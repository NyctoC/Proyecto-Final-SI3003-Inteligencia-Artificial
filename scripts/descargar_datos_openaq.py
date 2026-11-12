"""
Descarga datos REALES de calidad del aire de Medellin / Valle de Aburra desde
OpenAQ (que agrega la red oficial de SIATA) y los guarda en el esquema del
proyecto como data/raw/siata_real.csv.

OpenAQ v3 requiere una API key gratuita. Obtenla en
https://explore.openaq.org/register y colocala en .env como:

    OPENAQ_API_KEY=tu_clave

Flujo:
  1. Lista estaciones (locations) de Colombia que midan PM2.5 cerca del Valle
     de Aburra.
  2. Para cada sensor de PM2.5, descarga agregados DIARIOS.
  3. Normaliza al esquema: fecha, estacion, pm25, temperatura, viento,
     precipitacion, lat, lon. (temp/viento/precip pueden quedar vacios si la
     estacion no los reporta; el modelo tolera NaN al imputar.)

Uso:
    python scripts/descargar_datos_openaq.py
"""
from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from dotenv import load_dotenv  # noqa: E402
load_dotenv(RAIZ / ".env")

API = "https://api.openaq.org/v3"
KEY = os.environ.get("OPENAQ_API_KEY")
SALIDA = RAIZ / "data" / "raw" / "siata_real.csv"

# Coordenadas del centro del Valle de Aburra (Medellin) para el radio de busqueda.
LAT_CENTRO, LON_CENTRO = 6.2442, -75.5812
RADIO_M = 25000  # 25 km cubre el valle metropolitano

CAMPOS = ["fecha", "estacion", "pm25", "temperatura", "viento", "precipitacion", "lat", "lon"]


def _headers():
    if not KEY:
        print("ERROR: falta OPENAQ_API_KEY en .env. Registrate en "
              "https://explore.openaq.org/register")
        sys.exit(1)
    return {"X-API-Key": KEY}


def _get(path, params=None):
    for intento in range(3):
        resp = requests.get(f"{API}{path}", headers=_headers(), params=params or {}, timeout=20)
        if resp.status_code == 429:  # rate limit
            time.sleep(2 * (intento + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def listar_sensores_pm25():
    """Devuelve lista de (location_name, lat, lon, sensor_id) para PM2.5."""
    data = _get("/locations", {
        "coordinates": f"{LAT_CENTRO},{LON_CENTRO}",
        "radius": RADIO_M,
        "limit": 100,
    })
    sensores = []
    for loc in data.get("results", []):
        nombre = loc.get("name", f"loc-{loc.get('id')}")
        coords = loc.get("coordinates") or {}
        lat = coords.get("latitude")
        lon = coords.get("longitude")
        for s in loc.get("sensors", []):
            param = s.get("parameter", {})
            if param.get("name") in ("pm25", "pm2.5"):
                sensores.append((nombre, lat, lon, s.get("id")))
    return sensores


def descargar_diarios(sensor_id, dias=730):
    """Agregados diarios de un sensor. Devuelve lista de (fecha_iso, valor)."""
    filas = []
    pagina = 1
    while True:
        data = _get(f"/sensors/{sensor_id}/days", {"limit": 1000, "page": pagina})
        resultados = data.get("results", [])
        if not resultados:
            break
        for r in resultados:
            periodo = r.get("period", {})
            inicio = (periodo.get("datetimeFrom") or {})
            fecha = inicio.get("local") or inicio.get("utc")
            valor = r.get("value")
            if fecha and valor is not None:
                filas.append((fecha[:10], float(valor)))
        if len(resultados) < 1000:
            break
        pagina += 1
    return filas


def main():
    sensores = listar_sensores_pm25()
    print(f"Estaciones con PM2.5 encontradas: {len(sensores)}")
    if not sensores:
        print("No se encontraron estaciones de PM2.5 en el radio. Revisa la API key.")
        sys.exit(1)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with SALIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        for nombre, lat, lon, sid in sensores:
            try:
                diarios = descargar_diarios(sid)
            except requests.HTTPError as e:
                print(f"  {nombre}: error {e}; se omite")
                continue
            for fecha, valor in diarios:
                w.writerow({
                    "fecha": fecha,
                    "estacion": nombre,
                    "pm25": round(valor, 1),
                    "temperatura": "",
                    "viento": "",
                    "precipitacion": "",
                    "lat": lat,
                    "lon": lon,
                })
                total += 1
            print(f"  {nombre}: {len(diarios)} dias")
            time.sleep(0.3)  # respeta el rate limit

    print(f"\nListo. {total} filas escritas en {SALIDA}")


if __name__ == "__main__":
    main()
