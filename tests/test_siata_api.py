"""Tests de la Task 2: verificacion de acceso y cliente con fallback.

Se mockea `requests` para no depender de la red real.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src import siata_api  # noqa: E402


class _RespFake:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"results": []}

    def json(self):
        return self._payload


def test_check_access_ok():
    with patch.object(siata_api.requests, "get", return_value=_RespFake(200)):
        rep = siata_api.check_access(url="http://fake")
    assert rep.exito is True
    assert rep.status_code == 200
    assert rep.latencia_ms is not None


def test_check_access_server_error_no_exito():
    with patch.object(siata_api.requests, "get", return_value=_RespFake(503)):
        rep = siata_api.check_access(url="http://fake")
    assert rep.exito is False
    assert rep.status_code == 503


def test_check_access_timeout_controlado():
    with patch.object(siata_api.requests, "get", side_effect=requests.exceptions.Timeout()):
        rep = siata_api.check_access(url="http://fake", timeout=1)
    # No debe lanzar excepcion; debe reportar fallo controlado.
    assert rep.exito is False
    assert "Timeout" in rep.detalle


def test_check_access_error_red_controlado():
    with patch.object(
        siata_api.requests, "get", side_effect=requests.exceptions.ConnectionError("boom")
    ):
        rep = siata_api.check_access(url="http://fake")
    assert rep.exito is False
    assert "Error de red" in rep.detalle


def test_fetch_data_api_caida_devuelve_none():
    with patch.object(
        siata_api.requests, "get", side_effect=requests.exceptions.ConnectionError("boom")
    ):
        datos = siata_api.fetch_data(url="http://fake")
    assert datos is None


def test_fetch_data_normaliza_payload_openaq():
    payload = {
        "results": [
            {
                "name": "Medellin-Centro",
                "coordinates": {"latitude": 6.25, "longitude": -75.56},
                "sensors": [
                    {"parameter": {"name": "pm25"}, "value": 31.2},
                ],
            },
            {
                # Registro sin pm25: debe descartarse.
                "name": "SinDatos",
                "coordinates": {"latitude": 6.1, "longitude": -75.6},
                "sensors": [],
            },
        ]
    }
    with patch.object(siata_api.requests, "get", return_value=_RespFake(200, payload)):
        datos = siata_api.fetch_data(url="http://fake")
    assert datos is not None
    assert len(datos) == 1
    reg = datos[0]
    assert reg["estacion"] == "Medellin-Centro"
    assert reg["pm25"] == 31.2
    assert reg["lat"] == 6.25


def test_fetch_data_payload_vacio_devuelve_none():
    with patch.object(siata_api.requests, "get", return_value=_RespFake(200, {"results": []})):
        datos = siata_api.fetch_data(url="http://fake")
    assert datos is None
