"""
Conjunto fijo de preguntas de prueba para evaluar el agente (entregable 4).

Cada caso declara:
- pregunta: el texto que se le envia al agente.
- tool_esperada: la herramienta que deberia invocar (o None si no requiere ninguna).
- debe_citar: True si la respuesta deberia citar al menos una fuente del corpus.

Son 12 casos que cubren las tres herramientas, encadenamiento, manejo de errores
y preguntas puramente informativas.
"""
from __future__ import annotations

PREGUNTAS = [
    {
        "id": 1,
        "pregunta": "Cual es el PM2.5 actual en la estacion Medellin-Centro?",
        "tool_esperada": "get_pm25",
        "debe_citar": False,
    },
    {
        "id": 2,
        "pregunta": "Que categoria de calidad del aire se espera manana en Bello?",
        "tool_esperada": "predict_tomorrow",
        "debe_citar": False,
    },
    {
        "id": 3,
        "pregunta": "Que recomendaciones de salud hay cuando el aire es dañino para grupos sensibles?",
        "tool_esperada": "search_docs",
        "debe_citar": True,
    },
    {
        "id": 4,
        "pregunta": "Como esta el aire en Envigado y que deberia hacer hoy?",
        "tool_esperada": "get_pm25",
        "debe_citar": True,
    },
    {
        "id": 5,
        "pregunta": "En que consiste el protocolo de episodios criticos del Valle de Aburra?",
        "tool_esperada": "search_docs",
        "debe_citar": True,
    },
    {
        "id": 6,
        "pregunta": "Que significa que un dia este en categoria 'Moderada'?",
        "tool_esperada": "search_docs",
        "debe_citar": True,
    },
    {
        "id": 7,
        "pregunta": "Dame el PM2.5 de la estacion Caldas.",
        "tool_esperada": "get_pm25",
        "debe_citar": False,
    },
    {
        "id": 8,
        "pregunta": "Cual sera la calidad del aire manana en Itagui y por que importa para la salud?",
        "tool_esperada": "predict_tomorrow",
        "debe_citar": True,
    },
    {
        "id": 9,
        "pregunta": "Que es el PM2.5 y por que es peligroso?",
        "tool_esperada": "search_docs",
        "debe_citar": True,
    },
    {
        "id": 10,
        "pregunta": "Consulta el aire en la estacion 'EstacionQueNoExiste'.",
        "tool_esperada": "get_pm25",
        "debe_citar": False,
    },
    {
        "id": 11,
        "pregunta": "Quienes son los grupos sensibles a la contaminacion del aire?",
        "tool_esperada": "search_docs",
        "debe_citar": True,
    },
    {
        "id": 12,
        "pregunta": "Que PM2.5 tiene Sabaneta y que categoria es?",
        "tool_esperada": "get_pm25",
        "debe_citar": False,
    },
]
