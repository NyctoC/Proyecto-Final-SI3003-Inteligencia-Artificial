"""
Verifica el acceso a la fuente de datos remota y deja constancia escrita.

Cumple el requisito 1 del enunciado: "Se verifica el acceso en las primeras
48 horas; si una API falla, se usan historicos descargados (plan B)".

Genera/actualiza docs/verificacion_acceso_datos.md con el resultado.

Uso:
    python scripts/verificar_acceso_datos.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.siata_api import check_access, DEFAULT_API_URL  # noqa: E402


def main() -> None:
    reporte = check_access()
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    estado = "ACCESIBLE" if reporte.exito else "NO ACCESIBLE (se usa plan B: CSV)"
    md = f"""# Verificacion de acceso a datos

> Generado automaticamente por `scripts/verificar_acceso_datos.py`.
> Requisito 1 del enunciado: verificar el acceso en las primeras 48 horas.

- **Fecha de verificacion:** {ahora}
- **Endpoint probado:** `{reporte.url}`
- **Resultado:** **{estado}**
- **Codigo HTTP:** {reporte.status_code}
- **Latencia:** {reporte.latencia_ms} ms
- **Detalle:** {reporte.detalle}

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
"""

    salida = RAIZ / "docs" / "verificacion_acceso_datos.md"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(md, encoding="utf-8")
    print(f"Resultado: {estado}")
    print(f"Reporte escrito en {salida}")


if __name__ == "__main__":
    main()
