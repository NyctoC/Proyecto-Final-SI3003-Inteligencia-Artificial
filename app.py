"""
Dashboard ciudadano de calidad del aire del Valle de Aburra.

Integra las dos partes del proyecto:
- Parte 1 (Naive Bayes): prediccion de la categoria de mañana.
- Parte 2 (agente LLM + RAG): chat que consulta datos, predice y cita fuentes.

Visualizaciones: mapa de estaciones + serie de tiempo de PM2.5.
Interaccion: seleccion de estacion y fecha, y conversacion con el agente.

Ejecutar:
    streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src import data_loader as dl
from src import viz
from src.tools import estaciones_disponibles, get_pm25, predict_tomorrow
from src.ui_theme import CSS, color_de, texto_de

st.set_page_config(
    page_title="Aire del Valle de Aburra",
    page_icon="🌫️",
    layout="wide",
)
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cargar_datos() -> pd.DataFrame:
    df, _ = dl.load_data()
    return df


@st.cache_resource(show_spinner=False)
def crear_agente():
    # Import perezoso: solo al abrir el chat, para no exigir la API al arrancar.
    from src.agent import Agent
    return Agent()


df = cargar_datos()
estaciones = estaciones_disponibles()

# ----------------------------- Encabezado -----------------------------
st.markdown(
    """
    <div class="encabezado-aire">
      <h1>Aire del Valle de Aburra</h1>
      <span class="sub">Que respiras hoy y que puedes hacer al respecto</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Controles -----------------------------
col_e, col_f, _ = st.columns([1.2, 1.2, 2.6])
with col_e:
    estacion = st.selectbox("Estacion", estaciones, index=0)

sub = df[df["estacion"] == estacion].sort_values("fecha")
fechas = sub["fecha"].dt.date.tolist()
with col_f:
    fecha_sel = st.selectbox(
        "Dia", fechas, index=len(fechas) - 1,
        format_func=lambda d: d.strftime("%d %b %Y"),
    )

fecha_ts = pd.Timestamp(fecha_sel)

# ----------------------------- Tarjeta heroe -----------------------------
dato = get_pm25(estacion, fecha=str(fecha_sel))
pred = predict_tomorrow(estacion)

if "error" in dato:
    st.error(f"No pude leer el dato de esa estacion y dia: {dato['error']}")
else:
    cat = dato["categoria"]
    bg = color_de(cat)
    fg = texto_de(cat)

    if "error" in pred:
        pron_html = f"<div class='pronostico'>No hay prediccion disponible: {pred['error']}</div>"
    else:
        pron_html = (
            f"<div class='pronostico'>Mañana, estimado: "
            f"<b>{pred['categoria_predicha_manana']}</b> "
            f"(confianza {pred['confianza']:.0%}). "
            f"Prediccion orientativa del modelo, no una certeza.</div>"
        )

    st.markdown(
        f"""
        <div class="heroe">
          <div class="banda" style="background:{bg}; color:{fg};">
            <div class="valor">{dato['pm25']:.1f}<span class="unidad"> ug/m3 PM2.5</span></div>
            <div class="categoria">{cat}</div>
            <div class="meta">{estacion} &middot; {fecha_ts.strftime('%d %b %Y')}</div>
          </div>
          {pron_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------- Visualizaciones -----------------------------
st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
col_mapa, col_serie = st.columns(2)

with col_mapa:
    st.markdown("<div class='titulo-seccion'>Estaciones del valle</div>", unsafe_allow_html=True)
    st.plotly_chart(viz.mapa_estaciones(df, fecha_ts), use_container_width=True)

with col_serie:
    st.markdown(
        f"<div class='titulo-seccion'>Historia reciente en {estacion}</div>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(viz.serie_tiempo(df, estacion), use_container_width=True)

# ----------------------------- Chat con el agente -----------------------------
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
st.markdown(
    "<div class='titulo-seccion'>Preguntale al asistente del aire</div>",
    unsafe_allow_html=True,
)
st.caption(
    "Puede consultar el PM2.5, estimar la categoria de mañana y citar guias de "
    "salud. La informacion es orientativa y no es consejo medico."
)

if "chat" not in st.session_state:
    st.session_state.chat = []

for turno in st.session_state.chat:
    with st.chat_message(turno["rol"]):
        st.markdown(turno["texto"])
        if turno.get("fuentes"):
            chips = "".join(f"<span class='fuente-chip'>{f}</span>" for f in turno["fuentes"])
            st.markdown(chips, unsafe_allow_html=True)
        if turno.get("tools"):
            st.caption("Herramientas usadas: " + ", ".join(turno["tools"]))

pregunta = st.chat_input(f"Ej: como esta el aire en {estacion} y que hago?")
if pregunta:
    st.session_state.chat.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando datos y guias..."):
            try:
                agente = crear_agente()
                resp = agente.run(pregunta)
                st.markdown(resp.texto)
                if resp.fuentes_citadas:
                    chips = "".join(
                        f"<span class='fuente-chip'>{f}</span>" for f in resp.fuentes_citadas
                    )
                    st.markdown(chips, unsafe_allow_html=True)
                if resp.herramientas_usadas:
                    st.caption("Herramientas usadas: " + ", ".join(resp.herramientas_usadas))
                st.session_state.chat.append(
                    {
                        "rol": "assistant",
                        "texto": resp.texto,
                        "fuentes": resp.fuentes_citadas,
                        "tools": resp.herramientas_usadas,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                msg = (
                    "No pude responder ahora mismo. Revisa que GROQ_API_KEY este "
                    f"configurada en el archivo .env. Detalle: {exc}"
                )
                st.error(msg)
                st.session_state.chat.append({"rol": "assistant", "texto": msg})
