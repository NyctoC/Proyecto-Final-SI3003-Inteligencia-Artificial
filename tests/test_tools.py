"""Tests de la Task 7: herramientas del agente con manejo de errores."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import tools  # noqa: E402

# Usa una estacion real cualquiera del dataset activo (robusto a la fuente).
ESTACION = tools.estaciones_disponibles()[0]


def test_estaciones_disponibles():
    ests = tools.estaciones_disponibles()
    assert len(ests) >= 1
    assert all(isinstance(e, str) and e for e in ests)


# ---------------------- get_pm25 ----------------------

def test_get_pm25_ultimo_dia():
    r = tools.get_pm25(ESTACION)
    assert "error" not in r
    assert r["estacion"] == ESTACION
    assert r["pm25"] > 0
    assert r["categoria"]
    assert r["unidad"] == "ug/m3"


def test_get_pm25_estacion_inexistente_devuelve_error_controlado():
    r = tools.get_pm25("EstacionFantasma")
    assert "error" in r
    assert "estaciones_disponibles" in r
    # No debe lanzar excepcion: devuelve dict.
    assert isinstance(r, dict)


def test_get_pm25_fecha_invalida():
    r = tools.get_pm25(ESTACION, fecha="no-es-fecha")
    assert "error" in r


def test_get_pm25_fecha_sin_dato():
    r = tools.get_pm25(ESTACION, fecha="1990-01-01")
    assert "error" in r
    assert "rango_disponible" in r


# ---------------------- predict_tomorrow ----------------------

def test_predict_tomorrow_ok():
    r = tools.predict_tomorrow(ESTACION)
    assert "error" not in r
    assert r["categoria_predicha_manana"]
    assert 0.0 <= r["confianza"] <= 1.0


def test_predict_tomorrow_estacion_inexistente():
    r = tools.predict_tomorrow("EstacionFantasma")
    assert "error" in r


# ---------------------- search_docs ----------------------

def test_search_docs_ok():
    r = tools.search_docs("recomendaciones de salud para grupos sensibles")
    assert "error" not in r
    assert len(r["resultados"]) >= 1
    assert r["resultados"][0]["fuente"].endswith(".md")


def test_search_docs_query_vacia():
    r = tools.search_docs("   ")
    assert "error" in r


# ---------------------- schemas ----------------------

def test_schemas_coinciden_con_funciones():
    nombres_schema = {s["function"]["name"] for s in tools.TOOL_SCHEMAS}
    assert nombres_schema == set(tools.TOOL_FUNCS.keys())
