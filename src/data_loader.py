"""
Capa de carga de datos con doble modo (API -> CSV) y categorizacion de PM2.5.

Diseno
------
- `load_data()` intenta la API (si `prefer_api=True`) y, ante cualquier problema,
  cae automaticamente al CSV local (plan B). Por defecto `prefer_api=False` para
  que la demostracion sea 100% reproducible y no dependa de la red.
- `categorize_pm25()` asigna la categoria de calidad del aire segun los puntos
  de corte de PM2.5 (concentracion diaria, ug/m3) del indice tipo AQI/ICA,
  estandar de la EPA adoptado en Colombia.
- `build_features()` construye las variables para la Parte 1: rezagos (lag-1) de
  PM2.5 y meteorologia, mas la categoria del dia siguiente como objetivo.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from src import siata_api

RAIZ = Path(__file__).resolve().parents[1]
CSV_POR_DEFECTO = RAIZ / "data" / "raw" / "siata_sample.csv"

COLUMNAS = ["fecha", "estacion", "pm25", "temperatura", "viento", "precipitacion", "lat", "lon"]

# Categorias de calidad del aire por PM2.5 (promedio diario, ug/m3).
# Puntos de corte tipo AQI/ICA (EPA). (limite_superior_inclusive, etiqueta)
CATEGORIAS_PM25 = [
    (12.0, "Buena"),
    (35.4, "Moderada"),
    (55.4, "Dañina a grupos sensibles"),
    (150.4, "Dañina"),
    (250.4, "Muy dañina"),
    (float("inf"), "Peligrosa"),
]

ETIQUETAS = [etiqueta for _, etiqueta in CATEGORIAS_PM25]


def categorize_pm25(valor: float) -> str:
    """Devuelve la categoria de calidad del aire para un valor de PM2.5 (ug/m3).

    Usa los cortes estandar tipo AQI/ICA. Valores negativos o no numericos se
    consideran invalidos y devuelven 'Desconocida'.
    """
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "Desconocida"
    if v < 0 or pd.isna(v):
        return "Desconocida"
    for limite, etiqueta in CATEGORIAS_PM25:
        if v <= limite:
            return etiqueta
    return "Peligrosa"


def _cargar_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["fecha"])
    faltantes = [c for c in COLUMNAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"El CSV no tiene las columnas esperadas; faltan: {faltantes}")
    return df[COLUMNAS].copy()


def load_data(
    path: str | Path | None = None,
    prefer_api: bool = False,
) -> tuple[pd.DataFrame, Literal["api", "csv"]]:
    """Carga los datos de calidad del aire.

    Parametros
    ----------
    path : ruta al CSV del plan B. Por defecto `data/raw/siata_sample.csv`.
    prefer_api : si True, intenta primero la API; ante cualquier fallo usa el CSV.

    Devuelve
    --------
    (DataFrame, fuente) donde fuente es "api" o "csv" para dejar traza.
    """
    path = Path(path) if path is not None else CSV_POR_DEFECTO

    if prefer_api:
        registros = siata_api.fetch_data()
        if registros:
            df = pd.DataFrame(registros)
            # Asegura el esquema; columnas faltantes quedan como NaN.
            for col in COLUMNAS:
                if col not in df.columns:
                    df[col] = pd.NA
            df = df[COLUMNAS]
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            return df, "api"
        # Si la API no entrego datos utilizables, caemos al plan B.

    return _cargar_csv(path), "csv"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construye features para la Parte 1.

    Para cada estacion y en orden temporal:
    - lag-1 de pm25, temperatura, viento, precipitacion (condiciones de HOY).
    - `categoria_hoy`: categoria del dia actual.
    - `objetivo`: categoria del DIA SIGUIENTE (lo que el modelo debe predecir).

    Se eliminan las filas sin objetivo (ultimo dia de cada estacion) y las que
    queden sin features por el rezago (primer dia de cada estacion).
    """
    df = df.copy()
    df = df.sort_values(["estacion", "fecha"]).reset_index(drop=True)
    df["categoria_hoy"] = df["pm25"].apply(categorize_pm25)

    g = df.groupby("estacion", group_keys=False)
    # Features = condiciones de hoy (usadas para predecir la categoria de mañana).
    df["pm25_hoy"] = df["pm25"]
    df["temp_hoy"] = df["temperatura"]
    df["viento_hoy"] = df["viento"]
    df["precip_hoy"] = df["precipitacion"]
    # Objetivo = categoria del dia siguiente dentro de cada estacion.
    df["pm25_manana"] = g["pm25"].shift(-1)
    df["objetivo"] = df["pm25_manana"].apply(
        lambda v: categorize_pm25(v) if pd.notna(v) else None
    )

    columnas_feat = ["pm25_hoy", "temp_hoy", "viento_hoy", "precip_hoy"]
    resultado = df.dropna(subset=columnas_feat + ["objetivo"]).reset_index(drop=True)
    return resultado


FEATURES = ["pm25_hoy", "temp_hoy", "viento_hoy", "precip_hoy"]
