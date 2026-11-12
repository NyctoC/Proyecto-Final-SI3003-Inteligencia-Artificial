"""Tests de la Task 9: las figuras del dashboard se construyen sin error.

No se levanta el servidor Streamlit; solo se validan las funciones de viz y los
helpers de tema.
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import data_loader as dl  # noqa: E402
from src import viz  # noqa: E402
from src.ui_theme import color_de, texto_de, COLOR_CATEGORIA  # noqa: E402


def test_mapa_estaciones_devuelve_figura():
    df, _ = dl.load_data()
    fig = viz.mapa_estaciones(df)
    assert isinstance(fig, go.Figure)
    # Debe tener al menos una traza (una por categoria presente).
    assert len(fig.data) >= 1


def test_serie_tiempo_devuelve_figura():
    df, _ = dl.load_data()
    est = df["estacion"].iloc[0]
    fig = viz.serie_tiempo(df, est)
    assert isinstance(fig, go.Figure)
    # La serie principal de PM2.5 debe existir.
    assert any(getattr(t, "name", None) == "PM2.5" for t in fig.data)


def test_colores_de_categoria_cubren_todas():
    for cat in COLOR_CATEGORIA:
        assert color_de(cat).startswith("#")
        assert texto_de(cat).startswith("#")


def test_color_categoria_desconocida_por_defecto():
    assert color_de("categoria que no existe") == COLOR_CATEGORIA["Desconocida"]
