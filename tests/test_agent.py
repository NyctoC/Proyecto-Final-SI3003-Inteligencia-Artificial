"""Tests de la Task 8: loop agentico con cliente Groq simulado (mock).

No se usa la red: se inyecta un cliente falso que devuelve tool_calls y luego
una respuesta final, para verificar el comportamiento del loop.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.agent import Agent  # noqa: E402


# -------- Infraestructura de mock del cliente Groq --------

def _tool_call(id_, nombre, args_json):
    return SimpleNamespace(
        id=id_,
        function=SimpleNamespace(name=nombre, arguments=args_json),
    )


def _completion(content=None, tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


class _FakeCompletions:
    def __init__(self, respuestas):
        self._respuestas = list(respuestas)
        self.llamadas = 0

    def create(self, **kwargs):
        resp = self._respuestas[self.llamadas]
        self.llamadas += 1
        return resp


class _FakeClient:
    def __init__(self, respuestas):
        self.chat = SimpleNamespace(completions=_FakeCompletions(respuestas))


def _agente_con(respuestas):
    ag = Agent(api_key="fake-key")
    ag._client = _FakeClient(respuestas)
    return ag


# -------- Tests --------

def test_respuesta_directa_sin_tools():
    ag = _agente_con([_completion(content="Hola, soy el asistente.")])
    resp = ag.run("hola")
    assert resp.texto == "Hola, soy el asistente."
    assert resp.herramientas_usadas == []
    assert resp.iteraciones == 1


def test_ejecuta_tool_y_incorpora_observacion():
    # 1er turno: el modelo pide get_pm25; 2do turno: responde con el dato.
    import json as _json
    from src import tools as _tools
    estacion = _tools.estaciones_disponibles()[0]
    respuestas = [
        _completion(tool_calls=[
            _tool_call("c1", "get_pm25", _json.dumps({"estacion": estacion}))
        ]),
        _completion(content="El PM2.5 esta disponible; categoria segun datos."),
    ]
    ag = _agente_con(respuestas)
    resp = ag.run("como esta el aire?")
    assert "get_pm25" in resp.herramientas_usadas
    assert resp.iteraciones == 2
    assert resp.texto.startswith("El PM2.5")
    # La traza debe contener la observacion real de la tool.
    assert resp.traza[0]["tool"] == "get_pm25"
    assert "error" not in resp.traza[0]["obs"]


def test_recolecta_fuentes_de_search_docs():
    respuestas = [
        _completion(tool_calls=[
            _tool_call("c1", "search_docs", '{"query": "recomendaciones salud"}')
        ]),
        _completion(content="Segun las fuentes, reduce la exposicion."),
    ]
    ag = _agente_con(respuestas)
    resp = ag.run("que hago si el aire esta malo?")
    assert "search_docs" in resp.herramientas_usadas
    assert len(resp.fuentes_citadas) >= 1
    assert all(f.endswith(".md") for f in resp.fuentes_citadas)


def test_corte_por_t_max():
    # El modelo pide tool indefinidamente -> debe cortar en t_max.
    siempre_tool = _completion(tool_calls=[
        _tool_call("c1", "get_pm25", '{"estacion": "Medellin-Centro"}')
    ])
    ag = Agent(t_max=3, api_key="fake-key")
    # Suministra suficientes respuestas identicas.
    ag._client = _FakeClient([siempre_tool] * 10)
    resp = ag.run("bucle")
    assert resp.iteraciones == 3
    assert "no pude completar" in resp.texto.lower()


def test_tool_desconocida_vuelve_como_observacion():
    respuestas = [
        _completion(tool_calls=[_tool_call("c1", "herramienta_inexistente", "{}")]),
        _completion(content="listo"),
    ]
    ag = _agente_con(respuestas)
    resp = ag.run("x")
    assert resp.traza[0]["obs"].get("error")


def test_argumentos_json_invalidos():
    respuestas = [
        _completion(tool_calls=[_tool_call("c1", "get_pm25", "{no-json}")]),
        _completion(content="listo"),
    ]
    ag = _agente_con(respuestas)
    resp = ag.run("x")
    assert "error" in resp.traza[0]["obs"]
