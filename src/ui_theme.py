"""
Tema visual del dashboard.

Diseno anclado al tema: aire del Valle de Aburra entre montanas. El color NO es
decorativo: codifica la categoria de calidad del aire (es el dato). Tipografia:
Fraunces (serif con caracter) para el numero heroe y titulares; Inter para UI y
datos. Paleta base en azules de aire de montana + neblina clara (no el cream
generico), con una escala semantica de calidad del aire.
"""
from __future__ import annotations

# Paleta base (derivada del tema del aire de montana, no defaults genericos).
CIELO_LIMPIO = "#2E6F95"   # azul-petroleo, color de marca
NEBLINA = "#EDF1F3"        # fondo gris-azulado claro (bruma del valle)
TINTA = "#16242B"          # texto casi-negro frio (derivado del azul base)
TINTA_SUAVE = "#52636B"    # texto secundario

# Escala semantica de calidad del aire por categoria (esto es DATO).
COLOR_CATEGORIA = {
    "Buena": "#3BA676",
    "Moderada": "#E0B23C",
    "Dañina a grupos sensibles": "#E67E3C",
    "Dañina": "#D1495B",
    "Muy dañina": "#8E44AD",
    "Peligrosa": "#6D214F",
    "Desconocida": "#9AA7AD",
}

# Texto legible (claro u oscuro) sobre cada color de categoria.
TEXTO_SOBRE_CATEGORIA = {
    "Buena": "#06301F",
    "Moderada": "#3D2E05",
    "Dañina a grupos sensibles": "#3A1A05",
    "Dañina": "#FFFFFF",
    "Muy dañina": "#FFFFFF",
    "Peligrosa": "#FFFFFF",
    "Desconocida": "#1B2429",
}


def color_de(categoria: str) -> str:
    return COLOR_CATEGORIA.get(categoria, COLOR_CATEGORIA["Desconocida"])


def texto_de(categoria: str) -> str:
    return TEXTO_SOBRE_CATEGORIA.get(categoria, "#1B2429")


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&family=Inter:wght@400;500;600&display=swap');

:root {{
  --cielo: {CIELO_LIMPIO};
  --neblina: {NEBLINA};
  --tinta: {TINTA};
  --tinta-suave: {TINTA_SUAVE};
}}

/* Fondo general y tipografia base */
.stApp {{
  background: var(--neblina);
  color: var(--tinta);
}}
html, body, [class*="st-"], .stMarkdown, p, span, div {{
  font-family: 'Inter', system-ui, sans-serif;
}}

/* Encabezado de la app */
.encabezado-aire {{
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  border-bottom: 2px solid var(--cielo);
  padding-bottom: 0.4rem;
  margin-bottom: 1.2rem;
}}
.encabezado-aire h1 {{
  font-family: 'Fraunces', serif;
  font-weight: 900;
  font-size: 1.9rem;
  letter-spacing: -0.01em;
  color: var(--tinta);
  margin: 0;
}}
.encabezado-aire .sub {{
  font-size: 0.95rem;
  color: var(--tinta-suave);
}}

/* Tarjeta heroe: el numero de PM2.5 del dia, con banda de color semantico */
.heroe {{
  border-radius: 18px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 10px 30px rgba(22, 36, 43, 0.08);
}}
.heroe .banda {{
  padding: 1.6rem 1.8rem;
}}
.heroe .valor {{
  font-family: 'Fraunces', serif;
  font-weight: 900;
  font-size: 4.6rem;
  line-height: 0.95;
  letter-spacing: -0.02em;
}}
.heroe .unidad {{
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 1rem;
  opacity: 0.85;
}}
.heroe .categoria {{
  font-family: 'Fraunces', serif;
  font-weight: 600;
  font-size: 1.5rem;
  margin-top: 0.2rem;
}}
.heroe .meta {{
  font-size: 0.9rem;
  opacity: 0.85;
  margin-top: 0.1rem;
}}
.heroe .pronostico {{
  padding: 0.9rem 1.8rem;
  background: #ffffff;
  color: var(--tinta);
  font-size: 0.98rem;
  border-top: 1px solid rgba(22,36,43,0.08);
}}
.heroe .pronostico b {{ font-weight: 600; }}

/* Titulos de seccion */
.titulo-seccion {{
  font-family: 'Fraunces', serif;
  font-weight: 600;
  font-size: 1.25rem;
  color: var(--tinta);
  margin: 0.4rem 0 0.6rem 0;
}}

/* Aviso */
.aviso {{
  font-size: 0.82rem;
  color: var(--tinta-suave);
  border-left: 3px solid var(--cielo);
  padding-left: 0.7rem;
  margin-top: 0.5rem;
}}

/* Fuentes citadas por el agente */
.fuente-chip {{
  display: inline-block;
  background: rgba(46, 111, 149, 0.12);
  color: var(--cielo);
  border-radius: 999px;
  padding: 0.12rem 0.65rem;
  font-size: 0.78rem;
  font-weight: 500;
  margin: 0.15rem 0.2rem 0 0;
}}
</style>
"""
