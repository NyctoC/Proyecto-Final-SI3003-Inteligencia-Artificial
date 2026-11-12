# Informe — Agente de calidad del aire del Valle de Aburrá

SI3003 Inteligencia Artificial — Universidad EAFIT, 2026-1

## Integrantes del equipo

| Nombre | ID estudiante |
|--------|---------------|
| Cristian Cárdenas | 1000258211 |
| Danna Carolina Mendoza Burgos | 1000258194 |
|  |  |

## 1. Problema y datos

Los ciudadanos del Valle de Aburrá no comprenden qué significa el valor de PM2.5
del día ni qué acciones tomar. Este proyecto construye un MVP que comunica el
estado del aire y da recomendaciones apoyadas en documentos, combinando una
técnica clásica de IA con un agente LLM moderno.

**Datos.** Fuente: SIATA (Sistema de Alerta Temprana del Valle de Aburrá). Se
usan **datos reales** de PM2.5 diario descargados vía **OpenAQ** (que agrega la
red oficial de calidad del aire de Medellín): **24 estaciones** del Valle de
Aburrá (Medellín, Bello, Envigado, Itagüí, Sabaneta, Caldas, Copacabana,
Girardota, La Estrella) con hasta ~5 años de historia, **31.457 registros**
diarios en total (`data/raw/siata_real.csv`, generado con
`scripts/descargar_datos_openaq.py`).

**Verificación de acceso (requisito 1).** Se verificó el acceso en las primeras
horas (ver `docs/verificacion_acceso_datos.md`). SIATA no expone una API REST
pública y estable con series históricas diarias listas para descarga; la vía
programática estable es OpenAQ (requiere API key gratuita). OpenAQ entrega PM2.5
pero no meteorología para estas estaciones. El sistema trae un cliente
(`src/siata_api.py`) que verifica la API y cae automáticamente a CSV, y como plan
B incluye un dataset sintético reproducible.

## 2. Parte 1 — Método clásico (implementado por el equipo)

Se implementó un **Naive Bayes Gaussiano** desde cero con numpy
(`src/naive_bayes.py`): el ajuste estima medias, varianzas y *priors* por clase,
y la predicción usa la log-verosimilitud gaussiana más el log-*prior*, con
suavizado de varianza. No se usó `sklearn.GaussianNB`.

**Tarea.** Predecir la categoría de calidad del aire del día siguiente. Como los
datos reales de OpenAQ solo traen PM2.5 (sin meteorología), las features se
derivan de la propia serie de PM2.5: nivel de hoy (`pm25_hoy`), variación
respecto a ayer (`pm25_delta`), media móvil de 7 días (`pm25_media7`, tendencia)
y día del año (`dia_anio`, estacionalidad). Se eligieron features poco
correlacionadas para no violar el supuesto de independencia del modelo. Las
categorías siguen los cortes tipo AQI/ICA de la EPA.

**Validación.** Split **temporal** 80/20 (sin fuga de información) sobre 31.457
registros reales. Métricas frente a dos líneas base: clase mayoritaria y
persistencia ("mañana = hoy").

| Modelo                               | Accuracy | F1 macro |
|--------------------------------------|----------|----------|
| Naive Bayes (propio)                 | 0.749    | **0.572** |
| Clase mayoritaria                    | 0.787    | 0.220    |
| Persistencia (mañana = hoy)          | 0.794    | 0.488    |

**Lectura de los resultados.** Las clases están muy desbalanceadas (dominan los
días "Buena"/"Moderada"), por lo que las líneas base logran *accuracy* alta
simplemente acertando la clase frecuente. La métrica relevante para salud pública
es el **F1 macro** (pondera todas las clases por igual, incluidos los días malos):
ahí el Naive Bayes **supera claramente a ambas líneas base** (0.572 vs 0.488 y
0.220), es decir, detecta mejor los episodios de mala calidad del aire. En
*accuracy* queda por debajo de la persistencia, una línea base fuerte en series
temporales. La correctitud de la implementación se validó comparándola
numéricamente contra `sklearn.GaussianNB` en las pruebas.

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

- Clases desbalanceadas (predominan días buenos/moderados); el modelo se evalúa
  con F1 macro justo por esto.
- Los datos reales de OpenAQ no incluyen meteorología (temperatura, viento,
  lluvia), que mejoraría la predicción; el modelo usa solo señales derivadas del
  PM2.5. Combinar con datos de IDEAM es trabajo futuro.
- El Naive Bayes no supera a la persistencia en *accuracy* (sí en F1 macro): la
  persistencia es una línea base fuerte en series de calidad del aire.
- El agente ocasionalmente recomienda sin citar el corpus (1 de 7 casos).
- El sistema es informativo y **no constituye consejo médico, legal ni de
  seguridad**.
