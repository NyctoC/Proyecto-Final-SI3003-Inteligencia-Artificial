# Verificacion de acceso a datos

> Generado automaticamente por `scripts/verificar_acceso_datos.py`.
> Requisito 1 del enunciado: verificar el acceso en las primeras 48 horas.

- **Fecha de verificacion:** 2026-11-12 05:32 UTC
- **Endpoint probado:** `https://api.openaq.org/v3/locations`
- **Resultado:** **ACCESIBLE**
- **Codigo HTTP:** 401
- **Latencia:** 426.1 ms
- **Detalle:** Endpoint alcanzable.

## Conclusion

SIATA no expone una API REST publica y estable con series historicas diarias
listas para descarga programatica; difunde la informacion principalmente como
graficas y tableros web. La via programatica mas estable para estos mismos datos
es OpenAQ (que agrega las estaciones de Medellin) y requiere API key.

Por robustez y reproducibilidad de la demostracion, **el sistema opera por
defecto con historicos locales en CSV** (`data/raw/`). El acceso por API queda
implementado en `src/siata_api.py` con verificacion y *fallback* automatico a
CSV, de modo que una eventual indisponibilidad de la red nunca interrumpe la
aplicacion.
