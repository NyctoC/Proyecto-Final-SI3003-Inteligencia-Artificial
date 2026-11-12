"""
Evaluacion del agente (entregable 4 del enunciado).

Ejecuta el conjunto fijo de preguntas y, para cada una, registra:
- si el agente llamo a la herramienta esperada,
- si cito al menos una fuente cuando se esperaba,
- las herramientas realmente usadas y las fuentes citadas.

Produce un reporte en Markdown y un CSV en eval/resultados/.

Uso:
    python -m eval.agent_eval
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from eval.preguntas import PREGUNTAS  # noqa: E402
from src.agent import Agent  # noqa: E402

DIR_RESULTADOS = RAIZ / "eval" / "resultados"


def evaluar(agente: Agent | None = None) -> list[dict]:
    agente = agente or Agent()
    filas = []
    for caso in PREGUNTAS:
        resp = agente.run(caso["pregunta"])
        tools = resp.herramientas_usadas
        tool_ok = caso["tool_esperada"] in tools if caso["tool_esperada"] else len(tools) == 0
        cito = len(resp.fuentes_citadas) > 0
        cita_ok = cito if caso["debe_citar"] else True
        filas.append(
            {
                "id": caso["id"],
                "pregunta": caso["pregunta"],
                "tool_esperada": caso["tool_esperada"] or "(ninguna)",
                "tools_usadas": "|".join(tools) if tools else "(ninguna)",
                "tool_correcta": tool_ok,
                "debe_citar": caso["debe_citar"],
                "cito_fuente": cito,
                "cita_ok": cita_ok,
                "fuentes": "|".join(resp.fuentes_citadas),
                "iteraciones": resp.iteraciones,
                "modelo": resp.modelo,
            }
        )
    return filas


def escribir_reportes(filas: list[dict]) -> tuple[Path, Path]:
    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)

    # CSV
    ruta_csv = DIR_RESULTADOS / "evaluacion_agente.csv"
    with ruta_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        writer.writeheader()
        writer.writerows(filas)

    # Metricas agregadas
    n = len(filas)
    tool_hits = sum(1 for f in filas if f["tool_correcta"])
    # Tasa de citas solo sobre los casos que debian citar.
    casos_cita = [f for f in filas if f["debe_citar"]]
    cita_hits = sum(1 for f in casos_cita if f["cito_fuente"])
    tasa_tool = tool_hits / n
    tasa_cita = (cita_hits / len(casos_cita)) if casos_cita else 1.0

    # Markdown
    md = [
        "# Evaluacion del agente",
        "",
        f"- Total de preguntas: **{n}**",
        f"- Herramienta correcta: **{tool_hits}/{n}** ({tasa_tool:.0%})",
        f"- Citacion correcta (sobre {len(casos_cita)} casos que debian citar): "
        f"**{cita_hits}/{len(casos_cita)}** ({tasa_cita:.0%})",
        "",
        "| # | Pregunta | Tool esperada | Tools usadas | Tool OK | Debe citar | Cito | Fuentes |",
        "|---|----------|---------------|--------------|---------|-----------|------|---------|",
    ]
    for f in filas:
        md.append(
            f"| {f['id']} | {f['pregunta']} | {f['tool_esperada']} | {f['tools_usadas']} "
            f"| {'si' if f['tool_correcta'] else 'NO'} | {'si' if f['debe_citar'] else 'no'} "
            f"| {'si' if f['cito_fuente'] else 'no'} | {f['fuentes']} |"
        )
    ruta_md = DIR_RESULTADOS / "evaluacion_agente.md"
    ruta_md.write_text("\n".join(md), encoding="utf-8")
    return ruta_md, ruta_csv


def main() -> None:
    filas = evaluar()
    ruta_md, ruta_csv = escribir_reportes(filas)
    n = len(filas)
    tool_hits = sum(1 for f in filas if f["tool_correcta"])
    print(f"Evaluacion completa: {tool_hits}/{n} herramientas correctas.")
    print(f"Reporte: {ruta_md}")
    print(f"CSV: {ruta_csv}")


if __name__ == "__main__":
    main()
