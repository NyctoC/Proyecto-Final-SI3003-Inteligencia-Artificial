# Datos — Calidad del aire del Valle de Aburrá

## Fuente real: SIATA

Los datos reales de este proyecto provienen del **SIATA** (Sistema de Alerta
Temprana de Medellín y el Valle de Aburrá), operado por el Área Metropolitana
del Valle de Aburrá (AMVA).

- Portal SIATA: https://siata.gov.co/
- Datos abiertos del AMVA / datos.gov.co: https://www.datos.gov.co/

Variables usadas por estación y día:

| Columna         | Descripción                                   | Unidad |
|-----------------|-----------------------------------------------|--------|
| `fecha`         | Fecha del registro (diario)                   | ISO 8601 |
| `estacion`      | Nombre de la estación de monitoreo            | —      |
| `pm25`          | Concentración de material particulado PM2.5   | µg/m³  |
| `temperatura`   | Temperatura media del día                     | °C     |
| `viento`        | Velocidad media del viento                    | m/s    |
| `precipitacion` | Precipitación acumulada del día               | mm     |
| `lat`, `lon`    | Coordenadas de la estación                    | grados |

## Plan A — Acceso por API

El módulo `src/siata_api.py` intenta obtener datos desde SIATA y los normaliza
al esquema de la tabla anterior. La verificación de acceso a la API se ejecuta
en las primeras 48 horas del proyecto (requisito 1 del enunciado); su resultado
queda documentado en `docs/verificacion_acceso_datos.md`.

## Plan B — Históricos en CSV (modo por defecto)

Para garantizar que la aplicación corra de forma reproducible y sin depender de
la disponibilidad de la API durante la demostración, el sistema usa por defecto
archivos CSV locales en `data/raw/`.

### `siata_sample.csv` (incluido en el repositorio)

Dataset **sintético** y **determinista** (semilla fija) que imita la estructura
y la dinámica estacional del PM2.5 en el Valle de Aburrá. Permite ejecutar el
proyecto de punta a punta sin descargar nada. **No son mediciones reales** y no
deben interpretarse como tales.

Se regenera con:

```bash
python scripts/generate_sample_data.py
```

### Usar datos reales de SIATA

1. Descarga los históricos de PM2.5 y meteorología desde el portal SIATA o
   datos.gov.co para las estaciones de interés.
2. Normalízalos al esquema de columnas de la tabla de arriba.
3. Guárdalos como `data/raw/siata_real.csv`.
4. Indícalo al cargar los datos (ver `README.md` de la raíz).

> Nota ética: se usan únicamente datos agregados por estación. El proyecto es
> una herramienta informativa y **no constituye consejo médico**.
