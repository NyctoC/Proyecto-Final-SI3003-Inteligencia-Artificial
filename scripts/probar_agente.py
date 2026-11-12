"""
Prueba de humo del agente contra la API real de Groq.

Requiere un .env con GROQ_API_KEY. Escribe el resultado en un archivo para que
sea facil de inspeccionar.

Uso:
    python scripts/probar_agente.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.agent import Agent  # noqa: E402

PREGUNTAS = [
    "Como esta el PM2.5 en la estacion Medellin-Centro y que deberia hacer?",
    "Cual sera la categoria del aire manana en Bello?",
]


def main() -> None:
    salida = [f"Modelo principal configurado."]
    agente = Agent()
    for p in PREGUNTAS:
        salida.append("=" * 70)
        salida.append(f"PREGUNTA: {p}")
        try:
            resp = agente.run(p)
            salida.append(f"MODELO: {resp.modelo} | iteraciones: {resp.iteraciones}")
            salida.append(f"HERRAMIENTAS: {resp.herramientas_usadas}")
            salida.append(f"FUENTES: {resp.fuentes_citadas}")
            salida.append(f"RESPUESTA:\n{resp.texto}")
        except Exception as exc:  # noqa: BLE001
            salida.append(f"ERROR: {exc.__class__.__name__}: {exc}")
    (RAIZ / "scripts" / "_resultado_agente.txt").write_text(
        "\n".join(salida), encoding="utf-8"
    )
    print("listo")


if __name__ == "__main__":
    main()
