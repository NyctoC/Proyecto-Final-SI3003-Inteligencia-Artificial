# Informe — Agente de calidad del aire del Valle de Aburrá

SI3003 Inteligencia Artificial — Universidad EAFIT, 2026-1

## Integrantes del equipo

| Nombre | ID estudiante |
|--------|---------------|
| Cristian Cárdenas | 1000258211 |
|  |  |
|  |  |

## 1. Problema y datos

Los ciudadanos del Valle de Aburrá no comprenden qué significa el valor de PM2.5
del día ni qué acciones tomar. Este proyecto construye un MVP que comunica el
estado del aire y da recomendaciones apoyadas en documentos, combinando una
técnica clásica de IA con un agente LLM moderno.

**Datos.** Fuente: SIATA (Sistema de Alerta Temprana del Valle de Aburrá), con
datos abiertos del AMVA y datos.gov.co. Variables por estación y día: PM2.5
(µg/m³), temperatura, viento, precipitación y coordenadas.

**Verificación de acceso (requisito 1).** Se verificó el acceso en las primeras
horas (ver `docs/verificacion_acceso_datos.md`). SIATA no expone una API REST
pública y estable con series históricas diarias; la vía programática estable es
OpenAQ (agrega estaciones de Medellín) y requiere API key. Por reproducibilidad,
el sistema opera por defecto con **históricos en CSV (plan B)**, con un cliente
(`src/siata_api.py`) que verifica la API y cae automáticamente al CSV.

## 2. Parte 1 — Método clásico (implementado por el equipo)

Se implementó un **Naive Bayes Gaussiano** desde cero con numpy
(`src/naive_bayes.py`): el ajuste estima medias, varianzas y *priors* por clase,
y la predicción usa la log-verosimilitud gaussiana más el log-*prior*, con
suavizado de varianza. No se usó `sklearn.GaussianNB`.

**Tarea.** Predecir la categoría de calidad del aire del día siguiente a partir
de las condiciones del día actual (PM2.5, temperatura, viento, precipitación).
Las categorías siguen los puntos de corte tipo AQI/ICA de la EPA.

**Validación.** Split **temporal** 80/20 (sin fuga de información). Métricas:
accuracy y F1 macro, frente a dos líneas base: clase mayoritaria y persistencia
("mañana = hoy").

| Modelo                               | Accuracy | F1 macro |
|--------------------------------------|----------|----------|
| Naive Bayes (propio)                 | 0.903    | 0.600    |
| Clase mayoritaria                    | 0.831    | 0.303    |
| Persistencia (mañana = hoy)          | 0.900    | 0.599    |

La correctitud de la implementación se validó comparándola numéricamente contra
`sklearn.GaussianNB` en las pruebas (coincidencia exacta de predicciones).

## 3. Parte 2 — Agente LLM con RAG y herramientas

**Loop agéntico** (`src/agent.py`) sobre Groq (API compatible con OpenAI,
modelos GPT-OSS). Características: tope de iteraciones `T_max`, *tool calling*,
*fallback* de modelo, y los errores de herramientas se devuelven como observación
para que el agente reaccione en lugar de romperse.

**RAG** (`src/rag.py`): recuperación TF-IDF (scikit-learn) sobre un corpus de
cuatro documentos (categorías ICA, recomendaciones de salud, protocolo de
episodios críticos, FAQ). Es ligero, determinista y 100% offline.

**Herramientas** (`src/tools.py`): `get_pm25(estacion, fecha?)`,
`predict_tomorrow(estacion)` (usa el modelo de la Parte 1) y `search_docs(query)`
(RAG con citas). Cada una valida entradas y maneja errores sin lanzar excepciones.

## 4. Dashboard

Streamlit (`app.py`) con: tarjeta héroe del PM2.5 del día coloreada por categoría,
predicción de mañana, mapa de estaciones, serie de tiempo con bandas de umbral, y
chat con el agente que muestra las herramientas usadas y las fuentes citadas. El
diseño se apoyó en una guía de diseño frontend (color semántico = dato).

## 5. Resultados de la evaluación del agente

Conjunto fijo de 12 preguntas (`eval/preguntas.py`). Última corrida: **12/12**
de herramienta correcta y **6/7** de citación en los casos que debían citar. El
agente encadena herramientas (p. ej. `predict_tomorrow` + `search_docs`) y maneja
correctamente el caso de estación inexistente.

## 6. Limitaciones

- Clases desbalanceadas (predominan días buenos/moderados) reducen el F1 macro.
- El dataset incluido es sintético; para conclusiones reales hay que cargar
  históricos de SIATA.
- El agente ocasionalmente recomienda sin citar el corpus (1 de 7 casos).
- El sistema es informativo y **no constituye consejo médico, legal ni de
  seguridad**.
