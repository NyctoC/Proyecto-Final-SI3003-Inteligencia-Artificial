"""
Cliente de acceso a datos de calidad del aire del Valle de Aburra.

Contexto
--------
SIATA (https://siata.gov.co) publica datos de calidad del aire del Valle de
Aburra, pero NO expone una API REST publica, estable y documentada para
descarga programatica de series historicas: la informacion se difunde sobre
todo como graficas/PDF y tableros web. La via programatica mas estable para
estos mismos datos es OpenAQ, que agrega las mediciones de las estaciones de
Medellin.

Por eso, y como exige el enunciado (requisito 1: verificar el acceso en las
primeras 48 horas y tener plan B con historicos en CSV), este modulo:

1. Ofrece `check_access()` que prueba la conectividad al endpoint configurado y
   devuelve un reporte estructurado (exito/fallo, latencia, detalle), SIN lanzar
   excepciones que tumben el flujo.
2. Ofrece `fetch_data()` que intenta traer datos y normalizarlos al mismo
   esquema del CSV local; ante cualquier problema devuelve None para que la capa
   de carga (`data_loader`) use el plan B (CSV).

El endpoint es configurable por variable de entorno `SIATA_API_URL` para no
atar el codigo a una URL que puede cambiar.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any

import requests

# Esquema de columnas que el resto del proyecto espera (igual al CSV local).
ESQUEMA = ["fecha", "estacion", "pm25", "temperatura", "viento", "precipitacion", "lat", "lon"]

# Endpoint por defecto: API publica de OpenAQ (agrega estaciones de Medellin).
# Se puede sobrescribir con la variable de entorno SIATA_API_URL.
DEFAULT_API_URL = os.environ.get(
    "SIATA_API_URL",
    "https://api.openaq.org/v3/locations",
)

DEFAULT_TIMEOUT = 8  # segundos


@dataclass
class ReporteAcceso:
    """Resultado de verificar el acceso a la fuente de datos remota."""

    exito: bool
    url: str
    status_code: int | None = None
    latencia_ms: float | None = None
    detalle: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_access(url: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> ReporteAcceso:
    """Verifica la conectividad al endpoint de datos.

    No lanza excepciones: cualquier error de red se captura y se refleja en el
    reporte con `exito=False`. Esto permite documentar la verificacion de las
    primeras 48h sin arriesgar el flujo del proyecto.
    """
    url = url or DEFAULT_API_URL
    inicio = time.perf_counter()
    try:
        # Algunos endpoints (p.ej. OpenAQ v3) requieren API key; aun sin ella
        # la respuesta HTTP (200/401/403) sirve para confirmar conectividad.
        headers = {}
        api_key = os.environ.get("OPENAQ_API_KEY")
        if api_key:
            headers["X-API-Key"] = api_key

        resp = requests.get(url, params={"limit": 1}, headers=headers, timeout=timeout)
        latencia = (time.perf_counter() - inicio) * 1000.0
        alcanzable = resp.status_code < 500
        return ReporteAcceso(
            exito=alcanzable,
            url=url,
            status_code=resp.status_code,
            latencia_ms=round(latencia, 1),
            detalle=(
                "Endpoint alcanzable."
                if alcanzable
                else "El servidor respondio con error 5xx."
            ),
        )
    except requests.exceptions.Timeout:
        latencia = (time.perf_counter() - inicio) * 1000.0
        return ReporteAcceso(
            exito=False,
            url=url,
            latencia_ms=round(latencia, 1),
            detalle=f"Timeout tras {timeout}s.",
        )
    except requests.exceptions.RequestException as exc:
        return ReporteAcceso(
            exito=False,
            url=url,
            detalle=f"Error de red: {exc.__class__.__name__}: {exc}",
        )


def fetch_data(
    url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]] | None:
    """Intenta traer datos de la API y normalizarlos al esquema del proyecto.

    Devuelve una lista de registros (dicts con las claves de ESQUEMA) si logra
    datos utilizables, o None si debe usarse el plan B (CSV local).

    Nota: dada la ausencia de una API publica estable de SIATA con series
    historicas diarias listas para usar, esta funcion esta pensada para ser
    tolerante. Si el endpoint responde pero el formato no mapea al esquema,
    retorna None en lugar de inventar datos.
    """
    reporte = check_access(url=url, timeout=timeout)
    if not reporte.exito:
        return None

    try:
        headers = {}
        api_key = os.environ.get("OPENAQ_API_KEY")
        if api_key:
            headers["X-API-Key"] = api_key
        resp = requests.get(
            url or DEFAULT_API_URL,
            params={"limit": 100},
            headers=headers,
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        payload = resp.json()
    except (requests.exceptions.RequestException, ValueError):
        return None

    registros = _normalizar(payload)
    # Si no pudimos mapear nada al esquema, es mejor caer al plan B.
    return registros or None


def _normalizar(payload: Any) -> list[dict[str, Any]]:
    """Intenta mapear una respuesta JSON generica al esquema del proyecto.

    Es defensivo a proposito: distintos proveedores devuelven estructuras
    distintas. Solo conserva registros que tengan al menos estacion y pm25.
    """
    registros: list[dict[str, Any]] = []
    resultados = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(resultados, list):
        return registros

    for item in resultados:
        if not isinstance(item, dict):
            continue
        estacion = item.get("name") or item.get("location") or item.get("estacion")
        coords = item.get("coordinates") or {}
        lat = coords.get("latitude") if isinstance(coords, dict) else item.get("lat")
        lon = coords.get("longitude") if isinstance(coords, dict) else item.get("lon")
        pm25 = _extraer_pm25(item)
        if estacion is None or pm25 is None:
            continue
        registros.append(
            {
                "fecha": item.get("datetimeLast", {}).get("utc")
                if isinstance(item.get("datetimeLast"), dict)
                else item.get("fecha"),
                "estacion": str(estacion),
                "pm25": pm25,
                "temperatura": item.get("temperatura"),
                "viento": item.get("viento"),
                "precipitacion": item.get("precipitacion"),
                "lat": lat,
                "lon": lon,
            }
        )
    return registros


def _extraer_pm25(item: dict[str, Any]) -> float | None:
    """Busca un valor de PM2.5 en formatos comunes de respuesta."""
    # Formato OpenAQ v3: lista de 'sensors' o 'parameters'
    for clave in ("sensors", "parameters", "measurements"):
        lista = item.get(clave)
        if isinstance(lista, list):
            for medida in lista:
                if not isinstance(medida, dict):
                    continue
                param = medida.get("parameter")
                nombre = param.get("name") if isinstance(param, dict) else param
                if nombre in ("pm25", "pm2.5", "PM2.5"):
                    valor = medida.get("value") or medida.get("lastValue")
                    if valor is not None:
                        try:
                            return float(valor)
                        except (TypeError, ValueError):
                            return None
    valor = item.get("pm25")
    if valor is not None:
        try:
            return float(valor)
        except (TypeError, ValueError):
            return None
    return None
