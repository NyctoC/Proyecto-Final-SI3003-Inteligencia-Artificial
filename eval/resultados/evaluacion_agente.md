# Evaluacion del agente

- Total de preguntas: **12**
- Herramienta correcta: **12/12** (100%)
- Citacion correcta (sobre 7 casos que debian citar): **6/7** (86%)

| # | Pregunta | Tool esperada | Tools usadas | Tool OK | Debe citar | Cito | Fuentes |
|---|----------|---------------|--------------|---------|-----------|------|---------|
| 1 | Cual es el PM2.5 actual en la estacion Medellin-Centro? | get_pm25 | get_pm25 | si | no | no |  |
| 2 | Que categoria de calidad del aire se espera manana en Bello? | predict_tomorrow | predict_tomorrow | si | no | no |  |
| 3 | Que recomendaciones de salud hay cuando el aire es dañino para grupos sensibles? | search_docs | search_docs | si | si | si | 02_recomendaciones_salud.md|04_preguntas_frecuentes_pm25.md |
| 4 | Como esta el aire en Envigado y que deberia hacer hoy? | get_pm25 | get_pm25 | si | si | no |  |
| 5 | En que consiste el protocolo de episodios criticos del Valle de Aburra? | search_docs | search_docs | si | si | si | 03_protocolo_episodios_criticos.md|04_preguntas_frecuentes_pm25.md |
| 6 | Que significa que un dia este en categoria 'Moderada'? | search_docs | search_docs | si | si | si | 02_recomendaciones_salud.md|03_protocolo_episodios_criticos.md|04_preguntas_frecuentes_pm25.md |
| 7 | Dame el PM2.5 de la estacion Caldas. | get_pm25 | get_pm25 | si | no | no |  |
| 8 | Cual sera la calidad del aire manana en Itagui y por que importa para la salud? | predict_tomorrow | predict_tomorrow|predict_tomorrow|search_docs | si | si | si | 02_recomendaciones_salud.md|04_preguntas_frecuentes_pm25.md |
| 9 | Que es el PM2.5 y por que es peligroso? | search_docs | search_docs | si | si | si | 01_categorias_ica_pm25.md|04_preguntas_frecuentes_pm25.md |
| 10 | Consulta el aire en la estacion 'EstacionQueNoExiste'. | get_pm25 | get_pm25 | si | no | no |  |
| 11 | Quienes son los grupos sensibles a la contaminacion del aire? | search_docs | search_docs | si | si | si | 02_recomendaciones_salud.md|03_protocolo_episodios_criticos.md|04_preguntas_frecuentes_pm25.md |
| 12 | Que PM2.5 tiene Sabaneta y que categoria es? | get_pm25 | get_pm25 | si | no | no |  |