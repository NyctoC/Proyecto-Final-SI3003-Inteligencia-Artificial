"""
Agente LLM con loop agentico manual sobre Groq (API compatible con OpenAI).

Cumple el requisito 3 y las recomendaciones del enunciado:
- Loop agentico con tope de iteraciones `T_max`.
- Tool calling con >= 2 herramientas (usa las 3 de src/tools.py).
- Los errores de las herramientas se devuelven como OBSERVACION (no rompen el
  loop): cada tool ya retorna {"error": ...} en vez de lanzar excepcion.
- RAG a traves de la herramienta search_docs; el system prompt obliga a citar.
- Fallback de modelo (70B -> 8B) ante fallos del modelo principal.

Uso programatico:
    from src.agent import Agent
    agente = Agent()
    resp = agente.run("Como esta el aire en Medellin-Centro y que hago?")
    print(resp.texto)
    print(resp.herramientas_usadas)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from src import tools

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")

MODELO_PRINCIPAL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
MODELO_FALLBACK = os.environ.get("GROQ_MODEL_FALLBACK", "openai/gpt-oss-120b")
T_MAX_DEFECTO = 6

SYSTEM_PROMPT = """\
Eres un asistente de calidad del aire del Valle de Aburra (Medellin y municipios
cercanos). Ayudas a ciudadanos a entender el PM2.5 del dia y que hacer.

Reglas:
- Usa las herramientas disponibles para obtener datos; NO inventes cifras.
  - get_pm25: concentracion y categoria actual de una estacion.
  - predict_tomorrow: categoria estimada para mañana.
  - search_docs: normativa, salud y protocolos; usala cuando des recomendaciones.
- Cuando des recomendaciones de salud o expliques categorias/protocolos, apoyate
  en search_docs y CITA la fuente (nombre del archivo) en tu respuesta.
- Si una herramienta devuelve un campo "error", explica el problema al usuario de
  forma clara (por ejemplo, listando las estaciones disponibles) en vez de inventar.
- Responde en espanol, claro y breve.
- Aclara que la informacion es orientativa y NO es consejo medico.
"""


@dataclass
class RespuestaAgente:
    texto: str
    herramientas_usadas: list[str] = field(default_factory=list)
    fuentes_citadas: list[str] = field(default_factory=list)
    iteraciones: int = 0
    modelo: str = ""
    traza: list[dict] = field(default_factory=list)


class Agent:
    def __init__(self, t_max: int = T_MAX_DEFECTO, api_key: str | None = None) -> None:
        self.t_max = t_max
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        self._client = None  # se crea perezosamente

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise RuntimeError(
                    "Falta GROQ_API_KEY. Copia .env.example a .env y coloca tu clave."
                )
            from groq import Groq  # import perezoso para no exigirlo en tests
            self._client = Groq(api_key=self._api_key)
        return self._client

    def _crear_completion(self, mensajes: list[dict]):
        """Llama al modelo principal; ante error intenta el modelo de fallback."""
        client = self._get_client()
        try:
            return client.chat.completions.create(
                model=MODELO_PRINCIPAL,
                messages=mensajes,
                tools=tools.TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
            ), MODELO_PRINCIPAL
        except Exception:  # noqa: BLE001  (fallback de robustez)
            return client.chat.completions.create(
                model=MODELO_FALLBACK,
                messages=mensajes,
                tools=tools.TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.2,
            ), MODELO_FALLBACK

    def run(self, pregunta: str) -> RespuestaAgente:
        mensajes = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pregunta},
        ]
        herramientas_usadas: list[str] = []
        fuentes: list[str] = []
        traza: list[dict] = []
        modelo_usado = ""

        for iteracion in range(1, self.t_max + 1):
            completion, modelo_usado = self._crear_completion(mensajes)
            msg = completion.choices[0].message

            tool_calls = getattr(msg, "tool_calls", None)
            if not tool_calls:
                # Respuesta final del modelo.
                return RespuestaAgente(
                    texto=msg.content or "",
                    herramientas_usadas=herramientas_usadas,
                    fuentes_citadas=sorted(set(fuentes)),
                    iteraciones=iteracion,
                    modelo=modelo_usado,
                    traza=traza,
                )

            # Registramos el turno del asistente con sus tool_calls.
            mensajes.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            # Ejecutamos cada herramienta y agregamos su observacion.
            for tc in tool_calls:
                nombre = tc.function.name
                herramientas_usadas.append(nombre)
                observacion = self._ejecutar_tool(nombre, tc.function.arguments)
                traza.append({"tool": nombre, "args": tc.function.arguments, "obs": observacion})

                # Recolecta fuentes citables si la tool fue search_docs.
                if nombre == "search_docs" and isinstance(observacion, dict):
                    for r in observacion.get("resultados", []):
                        if isinstance(r, dict) and r.get("fuente"):
                            fuentes.append(r["fuente"])

                mensajes.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": nombre,
                        "content": json.dumps(observacion, ensure_ascii=False),
                    }
                )

        # Se alcanzo T_max sin respuesta final.
        return RespuestaAgente(
            texto=(
                "No pude completar la consulta dentro del limite de pasos. "
                "Intenta reformular la pregunta o especificar la estacion."
            ),
            herramientas_usadas=herramientas_usadas,
            fuentes_citadas=sorted(set(fuentes)),
            iteraciones=self.t_max,
            modelo=modelo_usado,
            traza=traza,
        )

    @staticmethod
    def _ejecutar_tool(nombre: str, argumentos_json: str) -> dict:
        """Ejecuta una herramienta; cualquier problema vuelve como observacion."""
        func = tools.TOOL_FUNCS.get(nombre)
        if func is None:
            return {"error": f"Herramienta desconocida: {nombre}"}
        try:
            args = json.loads(argumentos_json) if argumentos_json else {}
        except json.JSONDecodeError:
            return {"error": f"Argumentos JSON invalidos para {nombre}: {argumentos_json!r}"}
        if not isinstance(args, dict):
            return {"error": f"Los argumentos de {nombre} deben ser un objeto JSON."}
        return func(**args)
