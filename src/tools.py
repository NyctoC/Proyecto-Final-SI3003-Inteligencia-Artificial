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


# --------------------------------------------------------------------------
# Tool 1: get_pm25
# --------------------------------------------------------------------------
def get_pm25(estacion: str, fecha: str | None = None) -> dict[str, Any]:
    """Devuelve el PM2.5 y su categoria para una estacion.

    Si `fecha` es None, usa el ultimo dia disponible de esa estacion.
    """
    try:
        df = _datos()
        disponibles = estaciones_disponibles()
        if estacion not in disponibles:
            return {
                "error": f"Estacion '{estacion}' no encontrada.",
                "estaciones_disponibles": disponibles,
            }
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

    Usa las condiciones del ultimo dia disponible como features del Naive Bayes.
    """
    try:
        df = _datos()
        disponibles = estaciones_disponibles()
        if estacion not in disponibles:
            return {
                "error": f"Estacion '{estacion}' no encontrada.",
                "estaciones_disponibles": disponibles,
            }
        sub = df[df["estacion"] == estacion].sort_values("fecha")
        ultimo = sub.iloc[-1]

        X = np.array([[
            float(ultimo["pm25"]),
            float(ultimo["temperatura"]),
            float(ultimo["viento"]),
            float(ultimo["precipitacion"]),
        ]])
        modelo = _modelo()
        categoria = str(modelo.predict(X)[0])
        proba = modelo.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        confianza = float(proba[idx])

        return {
            "estacion": estacion,
            "fecha_base": str(pd.Timestamp(ultimo["fecha"]).date()),
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
