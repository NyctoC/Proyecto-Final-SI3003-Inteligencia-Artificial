"""
Construccion de las visualizaciones del dashboard (Plotly).

Separado de app.py para poder probar que las figuras se construyen sin levantar
Streamlit. Dos visualizaciones significativas:
- mapa de estaciones coloreado por PM2.5 (categoria),
- serie de tiempo de PM2.5 de una estacion con bandas de categoria.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src import data_loader as dl
from src.ui_theme import COLOR_CATEGORIA, CIELO_LIMPIO, TINTA, TINTA_SUAVE


def mapa_estaciones(df: pd.DataFrame, fecha: pd.Timestamp | None = None) -> go.Figure:
    """Mapa de las estaciones; color = categoria de PM2.5 del dia seleccionado
    (o el ultimo disponible por estacion si no se da fecha)."""
    if fecha is not None:
        snap = df[df["fecha"] == fecha]
    else:
        snap = df.sort_values("fecha").groupby("estacion", as_index=False).tail(1)

    if snap.empty:
        snap = df.sort_values("fecha").groupby("estacion", as_index=False).tail(1)

    snap = snap.copy()
    snap["categoria"] = snap["pm25"].apply(dl.categorize_pm25)
    snap["color"] = snap["categoria"].map(COLOR_CATEGORIA)

    fig = go.Figure()
    for categoria, grupo in snap.groupby("categoria"):
        fig.add_trace(
            go.Scattermap(
                lat=grupo["lat"],
                lon=grupo["lon"],
                mode="markers",
                marker=dict(size=22, color=COLOR_CATEGORIA.get(categoria, "#9AA7AD")),
                name=categoria,
                text=[
                    f"{r.estacion}<br>PM2.5: {r.pm25:.1f} ug/m3<br>{r.categoria}"
                    for r in grupo.itertuples()
                ],
                hoverinfo="text",
            )
        )

    centro_lat = float(snap["lat"].mean())
    centro_lon = float(snap["lon"].mean())
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=centro_lat, lon=centro_lon), zoom=10.3),
        margin=dict(l=0, r=0, t=0, b=0),
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.8)", font=dict(size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def serie_tiempo(df: pd.DataFrame, estacion: str, dias: int = 120) -> go.Figure:
    """Serie de tiempo de PM2.5 de una estacion, con los umbrales de categoria
    como bandas de fondo para leer el contexto de salud."""
    sub = df[df["estacion"] == estacion].sort_values("fecha").tail(dias)

    fig = go.Figure()

    # Bandas de umbral (dato: limites de categoria).
    umbrales = [
        (0, 12.0, COLOR_CATEGORIA["Buena"]),
        (12.0, 35.4, COLOR_CATEGORIA["Moderada"]),
        (35.4, 55.4, COLOR_CATEGORIA["Dañina a grupos sensibles"]),
        (55.4, 150.4, COLOR_CATEGORIA["Dañina"]),
    ]
    pm_max = float(sub["pm25"].max()) if not sub.empty else 60
    for lo, hi, color in umbrales:
        if lo > pm_max + 10:
            continue
        fig.add_hrect(y0=lo, y1=hi, fillcolor=color, opacity=0.08, line_width=0)

    fig.add_trace(
        go.Scatter(
            x=sub["fecha"],
            y=sub["pm25"],
            mode="lines",
            line=dict(color=CIELO_LIMPIO, width=2.2),
            name="PM2.5",
            hovertemplate="%{x|%d %b %Y}<br>PM2.5: %{y:.1f} ug/m3<extra></extra>",
        )
    )

    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.6)",
        font=dict(color=TINTA, family="Inter"),
        xaxis=dict(title=None, gridcolor="rgba(22,36,43,0.06)"),
        yaxis=dict(title="PM2.5 (ug/m3)", gridcolor="rgba(22,36,43,0.06)",
                   title_font=dict(color=TINTA_SUAVE)),
        showlegend=False,
    )
    return fig
