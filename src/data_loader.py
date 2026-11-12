"""
Capa de carga de datos con doble modo (API -> CSV) y categorizacion de PM2.5.

Diseno
------
- `load_data()` intenta la API (si `prefer_api=True`) y, ante cualquier problema,
  cae automaticamente al CSV local (plan B). Por defecto `prefer_api=False`.
- Fuente por defecto: `data/raw/siata_real.csv` (datos REALES de la red de SIATA,
  obtenidos vIa OpenAQ). Si no existe, cae a `siata_sample.csv` (sintetico).
- `categorize_pm25()` asigna la categoria tipo AQI/ICA (EPA) por PM2.5 diario.
- `build_features()` construye features para la Parte 1 a partir del PM2.5 real
  (la red de SIATA en OpenAQ no entrega meteorologia): PM2.5 de hoy, de ayer, su
  media movil de 3 dias, su variacion y el dia del anio (estacionalidad). El
  objetivo es la categoria del dia siguiente.
"""
from __future__ import annotations

import numpy as np
from pathlib import Path
from typing import Literal

import pandas as pd

from src import siata_api

RAIZ = Path(__file__).resolve().parents[1]
CSV_REAL = RAIZ / "data" / "raw" / "siata_real.csv"
CSV_SINTETICO = RAIZ / "data" / "raw" / "siata_sample.csv"

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

# Features de la Parte 1 (derivadas del PM2.5 real).
# Se eligen features POCO correlacionadas entre si: el supuesto "naive" de
# independencia condicional se degrada con variables colineales (p.ej. varias
# medias moviles). pm25_hoy (nivel), pm25_delta (dinamica), pm25_media7
# (tendencia) y el dia del anio (estacionalidad) aportan senales distintas.
FEATURES = ["pm25_hoy", "pm25_delta", "pm25_media7", "dia_anio"]


def _csv_por_defecto() -> Path:
    """Usa los datos reales si estan disponibles; si no, el sintetico."""
    return CSV_REAL if CSV_REAL.exists() else CSV_SINTETICO


def categorize_pm25(valor: float) -> str:
    """Devuelve la categoria de calidad del aire para un valor de PM2.5 (ug/m3).

    Valores negativos o no numericos devuelven 'Desconocida'.
    """
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "Desconocida"
    if pd.isna(v) or v < 0:
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
    df = df[COLUMNAS].copy()
    return _limpiar(df)


def _limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpieza: quita PM2.5 invalido, unifica sensores de una misma estacion
    por dia (promedio) y ordena."""
    df = df.copy()
    df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    df = df.dropna(subset=["pm25"])
    df = df[df["pm25"] >= 0]
    # Normaliza nombres de estaciones dadas de baja ("_OFF-...").
    df["estacion"] = df["estacion"].str.replace("_OFF-", "", regex=False).str.strip()
    # Si hay varios sensores por estacion/dia, promedia PM2.5 y toma coords/meteo.
    agg = {
        "pm25": "mean",
        "temperatura": "mean",
        "viento": "mean",
        "precipitacion": "mean",
        "lat": "first",
        "lon": "first",
    }
    df = df.groupby(["estacion", "fecha"], as_index=False).agg(agg)
    df = df[COLUMNAS]  # restaura el orden canonico de columnas
    return df.sort_values(["estacion", "fecha"]).reset_index(drop=True)


def load_data(
    path: str | Path | None = None,
    prefer_api: bool = False,
) -> tuple[pd.DataFrame, Literal["api", "csv"]]:
    """Carga los datos de calidad del aire.

    Parametros
    ----------
    path : ruta al CSV. Por defecto, datos reales si existen; si no, el sintetico.
    prefer_api : si True, intenta primero la API; ante cualquier fallo usa el CSV.

    Devuelve
    --------
    (DataFrame, fuente) donde fuente es "api" o "csv" para dejar traza.
    """
    path = Path(path) if path is not None else _csv_por_defecto()

    if prefer_api:
        registros = siata_api.fetch_data()
        if registros:
            df = pd.DataFrame(registros)
            for col in COLUMNAS:
                if col not in df.columns:
                    df[col] = pd.NA
            df = df[COLUMNAS]
            df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
            return _limpiar(df), "api"
        # Si la API no entrego datos utilizables, caemos al plan B.

    return _cargar_csv(path), "csv"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construye features para la Parte 1 a partir del PM2.5.

    Para cada estacion y en orden temporal (features poco correlacionadas):
    - `pm25_hoy`    : PM2.5 del dia actual (nivel).
    - `pm25_delta`  : cambio respecto a ayer (dinamica a corto plazo).
    - `pm25_media7` : media movil de 7 dias (tendencia).
    - `dia_anio`    : dia del anio (1-366), estacionalidad.
    - `categoria_hoy`: categoria del dia actual.
    - `objetivo`    : categoria del DIA SIGUIENTE (lo que se predice).

    Se eliminan las filas sin features (primeros 7 dias de cada estacion por el
    rezago) y sin objetivo (ultimo dia de cada estacion). La columna `pm25_ayer`
    se calcula de forma auxiliar para `pm25_delta`.
    """
    df = df.copy()
    df = df.sort_values(["estacion", "fecha"]).reset_index(drop=True)
    df["categoria_hoy"] = df["pm25"].apply(categorize_pm25)

    g = df.groupby("estacion", group_keys=False)
    df["pm25_hoy"] = df["pm25"]
    df["pm25_ayer"] = g["pm25"].shift(1)
    df["pm25_media7"] = g["pm25"].transform(lambda s: s.rolling(7, min_periods=7).mean())
    df["pm25_delta"] = df["pm25_hoy"] - df["pm25_ayer"]
    df["dia_anio"] = df["fecha"].dt.day_of_year.astype(float)
    df["pm25_manana"] = g["pm25"].shift(-1)
    df["objetivo"] = df["pm25_manana"].apply(
        lambda v: categorize_pm25(v) if pd.notna(v) else None
    )

    resultado = df.dropna(subset=FEATURES + ["objetivo"]).reset_index(drop=True)
    return resultado
