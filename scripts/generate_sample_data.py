"""
Genera un CSV de muestra reproducible que imita la estructura de los datos
diarios de calidad del aire (PM2.5) y meteorologia de SIATA para estaciones
del Valle de Aburra.

IMPORTANTE: estos datos son SINTETICOS, solo para que el proyecto corra de
punta a punta sin depender de la API. Los datos reales se obtienen de SIATA
(ver data/README.md). El generador es deterministico (semilla fija) para que
el dataset sea identico en cualquier maquina.

Uso:
    python scripts/generate_sample_data.py
"""
from __future__ import annotations

import csv
import math
from datetime import date, timedelta
from pathlib import Path

# Estaciones representativas del Valle de Aburra con coordenadas aproximadas
# reales de cada municipio/zona. (lat, lon)
ESTACIONES = {
    "Medellin-Centro": (6.2518, -75.5636),
    "Medellin-ITAGUI": (6.1719, -75.6060),
    "Bello": (6.3378, -75.5547),
    "Envigado": (6.1699, -75.5826),
    "Caldas": (6.0918, -75.6366),
    "Sabaneta": (6.1515, -75.6166),
}

# Rango de fechas: ~2 anios de datos diarios
FECHA_INICIO = date(2024, 1, 1)
N_DIAS = 730

# Parametros base por estacion (nivel medio de PM2.5 ug/m3).
# Estaciones del sur del valle (Itagui, Caldas) suelen tener PM2.5 mas alto.
NIVEL_BASE = {
    "Medellin-Centro": 24.0,
    "Medellin-ITAGUI": 30.0,
    "Bello": 26.0,
    "Envigado": 22.0,
    "Caldas": 28.0,
    "Sabaneta": 23.0,
}

SEED = 20260101


class _LCG:
    """Generador congruencial lineal simple y deterministico (sin numpy),
    para no depender de librerias externas al generar el CSV."""

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def random(self) -> float:
        # Parametros de Numerical Recipes
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state / 0xFFFFFFFF

    def normal(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        # Box-Muller
        u1 = max(self.random(), 1e-12)
        u2 = self.random()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + sigma * z


def _estacion_seca(dia_del_anio: int) -> float:
    """Factor estacional: las temporadas secas (dic-mar y jul-ago) en el
    Valle de Aburra concentran mas PM2.5. Devuelve un multiplicador ~[0.8, 1.4]."""
    # Dos picos al anio aproximando temporadas secas
    ang = 2 * math.pi * dia_del_anio / 365.0
    return 1.1 + 0.3 * math.cos(ang) + 0.1 * math.cos(2 * ang)


def generar_filas():
    rng = _LCG(SEED)
    filas = []
    for nombre, (lat, lon) in ESTACIONES.items():
        base = NIVEL_BASE[nombre]
        # Estado meteorologico con algo de memoria dia a dia
        pm_prev = base
        for i in range(N_DIAS):
            f = FECHA_INICIO + timedelta(days=i)
            doy = f.timetuple().tm_yday

            estacional = _estacion_seca(doy)

            # Meteorologia
            temperatura = 22.0 + 3.0 * math.sin(2 * math.pi * doy / 365.0) + rng.normal(0, 1.2)
            viento = max(0.2, 1.8 + rng.normal(0, 0.6))          # m/s
            lluvia = max(0.0, rng.normal(4.0, 6.0))              # mm; muchos ceros
            if rng.random() < 0.45:
                lluvia = 0.0

            # PM2.5: persistencia + estacionalidad - efecto limpiador de viento/lluvia
            objetivo = base * estacional
            pm = (
                0.55 * pm_prev
                + 0.45 * objetivo
                - 1.5 * (viento - 1.8)
                - 0.25 * lluvia
                + rng.normal(0, 3.0)
            )
            pm = max(3.0, pm)
            pm_prev = pm

            filas.append(
                {
                    "fecha": f.isoformat(),
                    "estacion": nombre,
                    "pm25": round(pm, 1),
                    "temperatura": round(temperatura, 1),
                    "viento": round(viento, 2),
                    "precipitacion": round(lluvia, 1),
                    "lat": lat,
                    "lon": lon,
                }
            )
    return filas


def main() -> None:
    filas = generar_filas()
    salida = Path(__file__).resolve().parents[1] / "data" / "raw" / "siata_sample.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    campos = ["fecha", "estacion", "pm25", "temperatura", "viento", "precipitacion", "lat", "lon"]
    with salida.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)
    print(f"Escritas {len(filas)} filas en {salida}")


if __name__ == "__main__":
    main()
