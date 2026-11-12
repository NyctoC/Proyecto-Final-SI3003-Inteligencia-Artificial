# Declaración de uso de IA generativa

Conforme al pacto pedagógico del curso SI3003, se declara el uso de herramientas
de IA generativa en el desarrollo de este proyecto.

## Herramientas utilizadas

- **Asistente de código con IA** (modelo de lenguaje tipo agente dentro del IDE):
  apoyo en la estructuración del proyecto, redacción de código base, pruebas y
  documentación.
- **Groq (modelos GPT-OSS)**: es un componente *funcional* del proyecto, no una
  herramienta de desarrollo. El agente del dashboard consulta este endpoint en
  tiempo de ejecución.

## Propósito y alcance del uso

La IA generativa se usó para:

1. Acelerar la escritura de código repetitivo (carga de datos, pruebas unitarias,
   estilos del dashboard).
2. Proponer la estructura del proyecto y el plan de trabajo por tareas.
3. Redactar borradores de documentación (README, corpus, este documento) que
   luego fueron revisados.
4. Depurar errores (por ejemplo, el descubrimiento de que la cuenta de Groq no
   tenía acceso a los modelos Llama y el ajuste a los modelos GPT-OSS).

## Comprensión y responsabilidad

El equipo comprende el funcionamiento de cada componente entregado:

- La implementación del Naive Bayes Gaussiano es propia y su correctitud se validó
  comparándola numéricamente contra `sklearn.GaussianNB` en las pruebas.
- El loop agéntico, las herramientas y el RAG fueron diseñados y revisados por el
  equipo; su comportamiento está cubierto por pruebas.
- Los datos, su categorización (puntos de corte ICA/AQI) y las limitaciones del
  sistema se documentan de forma explícita.

El uso de IA fue de **asistencia**, no de delegación total. Todo el código fue
revisado, probado y es comprendido por el equipo.

## Decisiones de diseño asistidas por el documento del profesor

Se siguieron las recomendaciones del enunciado: verificación temprana del acceso
a datos con plan B en CSV, construcción de una versión mínima de punta a punta
primero, `T_max` en el loop del agente, errores de herramientas devueltos como
observación, y evaluación del agente con un conjunto fijo de preguntas.
