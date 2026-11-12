"""
Herramientas (tools) que el agente LLM puede invocar.

Cumple el requisito 3 del enunciado: el agente debe tener al menos dos
herramientas. Aqui hay tres:

1. get_pm25(estacion, fecha?)   -> consulta datos reales/historicos de PM2.5.
2. predict_tomorrow(estacion)   -> usa el Naive Bayes propio (Parte 1) para
                                   predecir la categoria del dia siguiente.
3. search_docs(query)           -> recupera documentos del corpus via RAG.

Principio de diseno (recomendacion del enunciado): ninguna herramienta lanza
excepciones hacia el loop del agente. Ante un error devuelven un dict con la
clave "error", de modo que el agente lo reciba como una OBSERVACION y pueda
reaccionar (reintentar, pedir aclaracion, etc.).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

from src import data_loader as dl
from src import train
from src.rag import get_retriever


@lru_cache(maxsize=1)
def _datos() -> pd.DataFrame:
    df, _ = dl.load_data()
    return df


@lru_cache(maxsize=1)
def _modelo():
    """Carga el modelo Naive Bayes entrenado; si no existe, lo entrena al vuelo."""
    try:
        return train.cargar_modelo()
    except FileNotFoundError:
        salida = train.entrenar_y_evaluar()
        train.guardar_modelo(salida["modelo"], {"entrenado_al_vuelo": True})
        return salida["modelo"]


def estaciones_disponibles() -> list[str]:
    return sorted(_datos()["estacion"].unique().tolist())


def _norm(s: str) -> str:
    """Normaliza para comparar: minusculas y sin acentos."""
    s = s.lower().strip()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u")):
        s = s.replace(a, b)
    return s


def resolver_estacion(consulta: str) -> str | None:
    """Resuelve el nombre de estacion que el usuario/agente escribe.

    Acepta coincidencia exacta o parcial (p.ej. 'Bello' -> 'BEL-FEVE - Bello -
    I.E. Fernando Velez'). Devuelve el nombre canonico o None si no hay match
    unico claro.
    """
    disponibles = estaciones_disponibles()
    if consulta in disponibles:
        return consulta
    q = _norm(consulta)
    # Coincidencia por subcadena (nombre de municipio o codigo).
    candidatos = [e for e in disponibles if q in _norm(e)]
    if len(candidatos) >= 1:
        return candidatos[0]
    return None


# --------------------------------------------------------------------------
# Tool 1: get_pm25
# --------------------------------------------------------------------------
def get_pm25(estacion: str, fecha: str | None = None) -> dict[str, Any]:
    """Devuelve el PM2.5 y su categoria para una estacion.

    Si `fecha` es None, usa el ultimo dia disponible de esa estacion.
    """
    try:
        df = _datos()
        resuelta = resolver_estacion(estacion)
        if resuelta is None:
            return {
                "error": f"Estacion '{estacion}' no encontrada.",
                "estaciones_disponibles": estaciones_disponibles(),
            }
        estacion = resuelta
        sub = df[df["estacion"] == estacion].sort_values("fecha")

        if fecha is not None:
            try:
                f = pd.to_datetime(fecha)
            except (ValueError, TypeError):
                return {"error": f"Fecha invalida: '{fecha}'. Usa formato YYYY-MM-DD."}
            fila = sub[sub["fecha"] == f]
            if fila.empty:
                return {
                    "error": f"No hay dato para '{estacion}' en {fecha}.",
                    "rango_disponible": [
                        str(sub["fecha"].min().date()),
                        str(sub["fecha"].max().date()),
                    ],
                }
            fila = fila.iloc[0]
        else:
            fila = sub.iloc[-1]

        pm = float(fila["pm25"])
        return {
            "estacion": estacion,
            "fecha": str(pd.Timestamp(fila["fecha"]).date()),
            "pm25": round(pm, 1),
            "unidad": "ug/m3",
            "categoria": dl.categorize_pm25(pm),
        }
    except Exception as exc:  # noqa: BLE001  (defensivo: el loop recibe la obs)
        return {"error": f"Fallo inesperado en get_pm25: {exc}"}


# --------------------------------------------------------------------------
# Tool 2: predict_tomorrow
# --------------------------------------------------------------------------
def predict_tomorrow(estacion: str) -> dict[str, Any]:
    """Predice la categoria de calidad del aire de mañana para una estacion.

    Construye las features del PM2.5 (hoy, ayer, media movil, variacion y dia del
    anio) a partir del historico reciente de la estacion y las pasa al Naive
    Bayes.
    """
    try:
        df = _datos()
        resuelta = resolver_estacion(estacion)
        if resuelta is None:
            return {
                "error": f"Estacion '{estacion}' no encontrada.",
                "estaciones_disponibles": estaciones_disponibles(),
            }
        estacion = resuelta
        sub = df[df["estacion"] == estacion].sort_values("fecha").copy()
        if len(sub) < 7:
            return {"error": f"Datos insuficientes para '{estacion}' (se requieren 7 dias)."}

        # Features del ultimo dia disponible (mismas que build_features):
        # pm25_hoy, pm25_delta, pm25_media7, dia_anio.
        ult7 = sub.tail(7)["pm25"].to_numpy(dtype=float)
        ultimo = sub.iloc[-1]
        pm25_hoy = float(ult7[-1])
        pm25_ayer = float(ult7[-2])
        pm25_media7 = float(ult7.mean())
        pm25_delta = pm25_hoy - pm25_ayer
        fecha_ts = pd.Timestamp(ultimo["fecha"])
        dia_anio = float(fecha_ts.day_of_year)

        X = np.array([[pm25_hoy, pm25_delta, pm25_media7, dia_anio]])
        modelo = _modelo()
        categoria = str(modelo.predict(X)[0])
        proba = modelo.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        confianza = float(proba[idx])

        return {
            "estacion": estacion,
            "fecha_base": str(pd.Timestamp(ultimo["fecha"]).date()),
            "pm25_hoy": round(pm25_hoy, 1),
            "categoria_predicha_manana": categoria,
            "confianza": round(confianza, 3),
            "nota": "Prediccion estadistica orientativa, no es una certeza.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Fallo inesperado en predict_tomorrow: {exc}"}


# --------------------------------------------------------------------------
# Tool 3: search_docs
# --------------------------------------------------------------------------
def search_docs(query: str, k: int = 3) -> dict[str, Any]:
    """Busca en el corpus (normativa, salud, episodios) y devuelve fragmentos
    con su fuente para que el agente pueda citar."""
    try:
        if not query or not query.strip():
            return {"error": "La consulta esta vacia."}
        resultados = get_retriever().search(query, k=k)
        if not resultados:
            return {"resultados": [], "nota": "Sin coincidencias en el corpus."}
        return {
            "resultados": [
                {"fuente": r.fuente, "score": r.score, "texto": r.texto}
                for r in resultados
            ]
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Fallo inesperado en search_docs: {exc}"}


# --------------------------------------------------------------------------
# Registro de herramientas: nombre -> (funcion, JSON schema para Groq)
# --------------------------------------------------------------------------
TOOL_FUNCS = {
    "get_pm25": get_pm25,
    "predict_tomorrow": predict_tomorrow,
    "search_docs": search_docs,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_pm25",
            "description": (
                "Consulta la concentracion de PM2.5 (ug/m3) y su categoria de "
                "calidad del aire para una estacion del Valle de Aburra. Si no "
                "se da fecha, devuelve el ultimo dia disponible."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "estacion": {
                        "type": "string",
                        "description": "Nombre de la estacion (ej. 'Medellin-Centro').",
                    },
                    "fecha": {
                        "type": "string",
                        "description": "Fecha opcional en formato YYYY-MM-DD.",
                    },
                },
                "required": ["estacion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_tomorrow",
            "description": (
                "Predice la categoria de calidad del aire del dia siguiente para "
                "una estacion, usando el modelo Naive Bayes del proyecto."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "estacion": {
                        "type": "string",
                        "description": "Nombre de la estacion.",
                    },
                },
                "required": ["estacion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": (
                "Busca en el corpus de documentos (categorias ICA, "
                "recomendaciones de salud, protocolo de episodios criticos, FAQ) "
                "y devuelve fragmentos relevantes con su fuente para citar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta en lenguaje natural.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
