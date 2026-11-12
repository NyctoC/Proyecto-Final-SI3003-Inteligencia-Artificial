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

## Datos reales — OpenAQ (fuente por defecto)

Los datos reales de PM2.5 diario provienen de **OpenAQ**, que agrega la red
oficial de calidad del aire de Medellín operada por SIATA. Se descargan con:

```bash
python scripts/descargar_datos_openaq.py   # crea data/raw/siata_real.csv
```

Requiere una API key gratuita de OpenAQ (https://explore.openaq.org/register)
en `.env` como `OPENAQ_API_KEY`. El archivo resultante `siata_real.csv` contiene
~31.457 registros de 24 estaciones del Valle de Aburrá (hasta ~5 años). OpenAQ
entrega PM2.5 pero no meteorología, por lo que esas columnas quedan vacías.

La verificación de acceso a datos (requisito 1) se documenta en
`docs/verificacion_acceso_datos.md`.

## Plan B — Dataset sintético

Para garantizar que la aplicación corra sin descargas ni red, el repositorio
incluye `data/raw/siata_sample.csv`. Si `siata_real.csv` no existe, el sistema
usa este dataset por defecto.

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
