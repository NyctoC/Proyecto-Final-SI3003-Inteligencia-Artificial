"""Smoke tests de la Task 1: el dataset de muestra existe y es legible."""
from __future__ import annotations

import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSV_MUESTRA = RAIZ / "data" / "raw" / "siata_sample.csv"

COLUMNAS_ESPERADAS = [
    "fecha",
    "estacion",
    "pm25",
    "temperatura",
    "viento",
    "precipitacion",
    "lat",
    "lon",
]


def test_csv_muestra_existe():
    assert CSV_MUESTRA.exists(), "Ejecuta: python scripts/generate_sample_data.py"


def test_csv_muestra_tiene_columnas_y_filas():
    with CSV_MUESTRA.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == COLUMNAS_ESPERADAS
        filas = list(reader)
    # 6 estaciones x 730 dias
    assert len(filas) == 4380
    # pm25 numerico y positivo en la primera fila
    assert float(filas[0]["pm25"]) > 0
