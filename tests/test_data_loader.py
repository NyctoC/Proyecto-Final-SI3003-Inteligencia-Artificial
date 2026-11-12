"""Tests de la Task 3: carga de datos (doble modo) y categorizacion ICA."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import data_loader as dl  # noqa: E402


# ----------------------- categorize_pm25 -----------------------

def test_categoria_buena_en_limite():
    assert dl.categorize_pm25(0) == "Buena"
    assert dl.categorize_pm25(12.0) == "Buena"


def test_categoria_moderada():
    assert dl.categorize_pm25(12.1) == "Moderada"
    assert dl.categorize_pm25(35.4) == "Moderada"


def test_categoria_danina_sensibles():
    assert dl.categorize_pm25(35.5) == "Dañina a grupos sensibles"
    assert dl.categorize_pm25(55.4) == "Dañina a grupos sensibles"


def test_categoria_danina():
    assert dl.categorize_pm25(55.5) == "Dañina"
    assert dl.categorize_pm25(150.4) == "Dañina"


def test_categoria_extremos():
    assert dl.categorize_pm25(200) == "Muy dañina"
    assert dl.categorize_pm25(300) == "Peligrosa"


def test_categoria_invalida():
    assert dl.categorize_pm25(-5) == "Desconocida"
    assert dl.categorize_pm25("abc") == "Desconocida"


# ----------------------- load_data -----------------------

def test_load_data_csv_por_defecto():
    df, fuente = dl.load_data()
    assert fuente == "csv"
    assert list(df.columns) == dl.COLUMNAS
    assert len(df) == 4380


def test_load_data_fallback_cuando_api_falla():
    # prefer_api=True pero la API devuelve None -> debe caer a CSV.
    with patch.object(dl.siata_api, "fetch_data", return_value=None):
        df, fuente = dl.load_data(prefer_api=True)
    assert fuente == "csv"
    assert len(df) == 4380


def test_load_data_usa_api_si_hay_datos():
    registros = [
        {
            "fecha": "2024-05-01",
            "estacion": "X",
            "pm25": 20.0,
            "temperatura": 22.0,
            "viento": 1.5,
            "precipitacion": 0.0,
            "lat": 6.2,
            "lon": -75.5,
        }
    ]
    with patch.object(dl.siata_api, "fetch_data", return_value=registros):
        df, fuente = dl.load_data(prefer_api=True)
    assert fuente == "api"
    assert len(df) == 1
    assert df.iloc[0]["estacion"] == "X"


# ----------------------- build_features -----------------------

def test_build_features_sin_nan_en_objetivo_y_features():
    df, _ = dl.load_data()
    feats = dl.build_features(df)
    assert len(feats) > 0
    for col in dl.FEATURES + ["objetivo"]:
        assert col in feats.columns
        assert feats[col].notna().all(), f"columna {col} tiene NaN"


def test_build_features_objetivo_es_categoria_del_dia_siguiente():
    # Serie controlada de una sola estacion.
    df = pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "estacion": ["E", "E", "E"],
            "pm25": [10.0, 40.0, 5.0],  # Buena, Dañina a sensibles, Buena
            "temperatura": [20.0, 21.0, 22.0],
            "viento": [1.0, 1.0, 1.0],
            "precipitacion": [0.0, 0.0, 0.0],
            "lat": [6.0, 6.0, 6.0],
            "lon": [-75.0, -75.0, -75.0],
        }
    )
    feats = dl.build_features(df)
    # Dia 1 (pm25=10, Buena) -> objetivo = categoria del dia 2 (pm25=40)
    fila1 = feats[feats["fecha"] == pd.Timestamp("2024-01-01")].iloc[0]
    assert fila1["categoria_hoy"] == "Buena"
    assert fila1["objetivo"] == "Dañina a grupos sensibles"
