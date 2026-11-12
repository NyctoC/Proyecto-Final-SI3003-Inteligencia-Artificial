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
    assert len(df) > 0


def test_load_data_csv_sintetico_explicito():
    df, fuente = dl.load_data(path=dl.CSV_SINTETICO)
    assert fuente == "csv"
    # 6 estaciones x 730 dias (tras limpieza/agrupado se conserva).
    assert len(df) == 4380


def test_load_data_fallback_cuando_api_falla():
    # prefer_api=True pero la API devuelve None -> debe caer a CSV.
    with patch.object(dl.siata_api, "fetch_data", return_value=None):
        df, fuente = dl.load_data(prefer_api=True)
    assert fuente == "csv"
    assert len(df) > 0


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
    # Serie de 9 dias: media movil de 7 dias necesita 7 observaciones, y el
    # objetivo requiere el dia siguiente.
    fechas = pd.date_range("2024-01-01", periods=9, freq="D")
    # Dia 8 (indice 7) tiene pm25 bajo (Buena); dia 9 alto (Dañina a sensibles).
    pm = [8.0, 9.0, 10.0, 11.0, 12.0, 10.0, 9.0, 8.0, 40.0]
    df = pd.DataFrame(
        {
            "fecha": fechas,
            "estacion": ["E"] * 9,
            "pm25": pm,
            "temperatura": [20.0] * 9,
            "viento": [1.0] * 9,
            "precipitacion": [0.0] * 9,
            "lat": [6.0] * 9,
            "lon": [-75.0] * 9,
        }
    )
    feats = dl.build_features(df)
    fila8 = feats[feats["fecha"] == pd.Timestamp("2024-01-08")].iloc[0]
    assert fila8["categoria_hoy"] == "Buena"            # pm25=8 -> Buena
    assert fila8["objetivo"] == "Dañina a grupos sensibles"  # dia 9 pm25=40
    # media movil de 7 dias hasta el dia 8 = media de pm[1:8]
    esperado_media7 = sum(pm[1:8]) / 7
    assert abs(fila8["pm25_media7"] - esperado_media7) < 1e-9
