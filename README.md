# Aire del Valle de Aburrá — Agente de calidad del aire

Proyecto Final — **SI3003 Inteligencia Artificial**, Universidad EAFIT (2026-1).

## Integrantes del equipo

| Nombre | ID estudiante |
|--------|---------------|
| Cristian Cárdenas | 1000258211 |
| Danna Carolina Mendoza Burgos |  |
|  |  |

Una solución que combina una técnica clásica de IA implementada por el equipo
(Parte 1) con un agente LLM moderno con RAG y herramientas (Parte 2), sobre datos
reales de calidad del aire del Valle de Aburrá, todo expuesto en un dashboard
interactivo con chat.

- **Problema.** Los ciudadanos no comprenden qué significa el PM2.5 del día ni
  qué hacer al respecto.
- **Parte 1 (clásica).** Clasificador **Naive Bayes Gaussiano implementado a
  mano** (sin usar `sklearn.GaussianNB`) que predice la categoría de calidad del
  aire del día siguiente, con métrica frente a dos líneas base.
- **Parte 2 (moderna).** Agente LLM (Groq) con **loop agéntico**, **RAG** sobre
  un corpus de salud/normativa y **tres herramientas** (`get_pm25`,
  `predict_tomorrow`, `search_docs`).
- **Dashboard.** Streamlit con dos visualizaciones (mapa de estaciones + serie de
  tiempo), selección de estación/fecha y chat con el agente.

> La información es orientativa y **no constituye consejo médico**.

## Arquitectura

```
Datos (API SIATA -> CSV, con fallback)         Parte 1 (clasica)
  src/siata_api.py  ->  src/data_loader.py  ->  src/naive_bayes.py + baselines
                             |                        |
                             v                        v
Parte 2 (agente)        src/tools.py  <----  modelo entrenado (models/)
  src/rag.py (TF-IDF)  ->  get_pm25 / predict_tomorrow / search_docs
  src/agent.py (loop Groq + T_max) ----------------^
                             |
                             v
Dashboard: app.py (Streamlit) + src/viz.py + src/ui_theme.py
```

## Requisitos

- Python 3.11 o superior (probado en 3.14).
- Una clave de API de **Groq** (gratuita): https://console.groq.com/keys

## Instalación

```bash
# 1. Crear y activar un entorno virtual
python -m venv .venv
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
# source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar la clave de Groq
# Copia .env.example a .env y coloca tu GROQ_API_KEY.
```

El archivo `.env` debe contener:

```
GROQ_API_KEY=tu_clave_de_groq
GROQ_MODEL=openai/gpt-oss-20b
GROQ_MODEL_FALLBACK=openai/gpt-oss-120b
```

> Nota: usa modelos a los que tu cuenta de Groq tenga acceso. Los `openai/gpt-oss-*`
> están disponibles en el tier gratuito y soportan *tool calling*.

## Cómo ejecutar

### 1. (Opcional) Verificar el acceso a datos
```bash
python scripts/verificar_acceso_datos.py
```
Genera `docs/verificacion_acceso_datos.md`. El sistema usa por defecto históricos
locales en CSV (plan B), así que **no requiere red para funcionar**.

### 2. Entrenar el modelo de la Parte 1
```bash
python -m src.train
```
Imprime las métricas (Naive Bayes vs líneas base) y guarda el modelo en `models/`.

### 3. Lanzar el dashboard
```bash
streamlit run app.py
```
Abre el navegador en la URL que indica Streamlit (por defecto
http://localhost:8501). Selecciona estación y día, explora el mapa y la serie, y
conversa con el asistente.

### 4. (Opcional) Evaluar el agente
```bash
python -m eval.agent_eval
```
Ejecuta las 12 preguntas de prueba y genera el reporte en
`eval/resultados/`.

### 5. (Opcional) Notebook de EDA y Parte 1
Abre `notebooks/01_eda_parte1.ipynb` en Jupyter.

## Datos

Fuente real: **SIATA** (Sistema de Alerta Temprana del Valle de Aburrá). Ver
`data/README.md` para el detalle de columnas, el plan B en CSV y cómo usar datos
reales descargados. El repositorio incluye `data/raw/siata_sample.csv`, un
dataset sintético y determinista que permite correr todo sin descargar nada.

## Pruebas

```bash
pytest -q
```
Cubren la categorización ICA, el cliente de datos con fallback, la correctitud
del Naive Bayes (comparado contra `sklearn.GaussianNB`), el RAG, las herramientas,
el loop del agente (con cliente simulado) y las figuras del dashboard.

## Resultados (Parte 1)

Sobre el dataset de muestra, con split temporal 80/20:

| Modelo                              | Accuracy | F1 macro |
|-------------------------------------|----------|----------|
| Naive Bayes (propio)                | 0.903    | 0.600    |
| Línea base: clase mayoritaria       | 0.831    | 0.303    |
| Línea base: persistencia (hoy=mañana)| 0.900   | 0.599    |

El Naive Bayes propio supera a ambas líneas base.

## Evaluación del agente

12 preguntas fijas (ver `eval/preguntas.py`). En la última corrida: **12/12** de
herramienta correcta y **6/7** de citación en los casos que debían citar. Reporte
completo en `eval/resultados/`.

## Limitaciones

- Las clases de calidad del aire están desbalanceadas (predominan días
  buenos/moderados), lo que reduce el F1 macro.
- El dataset incluido es sintético; para conclusiones reales deben cargarse
  históricos de SIATA.
- El agente a veces da recomendaciones sin consultar el corpus (ver la pregunta
  que falló la citación); es un área de mejora del *prompt*.
- **No es una herramienta clínica ni de consejo médico.**

## Estructura

```
app.py                      Dashboard Streamlit
src/                        Modulos (datos, modelo, RAG, agente, viz, tema)
corpus/                     Documentos para el RAG
data/                       CSV de muestra + instrucciones de datos
eval/                       Evaluacion del agente (preguntas + reporte)
notebooks/                  EDA y Parte 1
scripts/                    Utilidades (generar datos, verificar acceso, probar agente)
tests/                      Pruebas (pytest)
docs/                       Verificacion de acceso, informe, declaracion de IA
.kiro/skills/               Skill de diseño frontend usada para el dashboard
```

## Declaración de uso de IA generativa

Ver `docs/declaracion_uso_ia.md`.
