"""Tests de la Task 10: la evaluacion corre y produce un reporte bien formado.

Se usa un agente simulado (no se consume la API de Groq).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from eval import agent_eval  # noqa: E402
from eval.preguntas import PREGUNTAS  # noqa: E402
from src.agent import RespuestaAgente  # noqa: E402


class _AgenteFake:
    """Devuelve la herramienta esperada de cada pregunta, segun el orden fijo."""

    def __init__(self):
        self._i = 0

    def run(self, pregunta):
        caso = PREGUNTAS[self._i]
        self._i += 1
        tool = caso["tool_esperada"]
        fuentes = ["02_recomendaciones_salud.md"] if caso["debe_citar"] else []
        return RespuestaAgente(
            texto="respuesta simulada",
            herramientas_usadas=[tool] if tool else [],
            fuentes_citadas=fuentes,
            iteraciones=2,
            modelo="fake",
        )


def test_cantidad_de_preguntas_en_rango():
    # El enunciado pide entre 10 y 15 preguntas.
    assert 10 <= len(PREGUNTAS) <= 15


def test_evaluar_produce_una_fila_por_pregunta():
    filas = agent_eval.evaluar(agente=_AgenteFake())
    assert len(filas) == len(PREGUNTAS)
    for f in filas:
        assert "tool_correcta" in f
        assert "cito_fuente" in f


def test_evaluar_marca_tool_correcta_con_agente_ideal():
    filas = agent_eval.evaluar(agente=_AgenteFake())
    # El agente fake siempre usa la tool esperada -> 100% correcto.
    assert all(f["tool_correcta"] for f in filas)


def test_escribir_reportes_crea_archivos(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_eval, "DIR_RESULTADOS", tmp_path)
    filas = agent_eval.evaluar(agente=_AgenteFake())
    ruta_md, ruta_csv = agent_eval.escribir_reportes(filas)
    assert ruta_md.exists()
    assert ruta_csv.exists()
    contenido = ruta_md.read_text(encoding="utf-8")
    assert "Evaluacion del agente" in contenido
    assert "Herramienta correcta" in contenido
