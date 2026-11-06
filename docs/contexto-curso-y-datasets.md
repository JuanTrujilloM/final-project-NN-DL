# Contexto del curso y datasets en español

Resumen de lo verificado el 2026-11-02 en el [repo del curso](https://github.com/jdmartinev/SI3014---Redes-Neuronales-y-Aprendizaje-Profundo) (`Project/README.md` y `Project/00. Projects.pdf`, publicados el 2026-10-23) y de la búsqueda de datasets en español.

## 1. Lineamientos oficiales del proyecto final

**Fechas**
- Título y objetivos (general + 2 a 3 específicos): jueves 29 de octubre (tabla) o viernes 30 de octubre (texto). El documento es inconsistente.
- Presentación e informe final: **miércoles 11 de noviembre de 2026**, por correo. No se aceptan versiones posteriores; no entregar equivale a 0.0.
- Sustentaciones: semanas 17 y 18 (el PDF dice 17, 18 y 19). 15 minutos de presentación y 5 de preguntas.

**Calificación:** 20 % del curso (15 % sustentación, 5 % informe). La nota es el promedio del profesor y de los estudiantes; si difieren en más de 0.5 hay penalización `0.3 + 0.5 * (diferencia - 0.5)`. La asistencia a todas las exposiciones es obligatoria (penalizaciones de 5 %, 10 % y 20 % por 6, 9 y 12 horas de inasistencia).

**La sustentación debe incluir**
1. Problema, justificación y objetivos formales.
2. Arquitectura del modelo. Si viene de la literatura: referencia y modificaciones realizadas. Hay que mostrar que se entiende y justificar por qué es adecuada.
3. Dataset (tamaño, clases, distribución), división train/val/test y preprocesamiento justificado.
4. Curvas de aprendizaje (loss y validación), hiperparámetros, función de pérdida, optimizador, análisis de sobreajuste o subajuste.
5. Recursos computacionales (CPU, GPU, RAM) y tiempo de entrenamiento.
6. Métricas y resultados cuantitativos.
7. **Evaluación con datos externos o no vistos:** ¿se mantiene el rendimiento?, ¿se degrada?, ¿por qué?
8. Conclusiones y limitaciones.

**Informe:** PDF de máximo 3 páginas con objetivos, base de datos, modelo, resultados (incluida la evaluación externa) y conclusiones.

**Lo que se valora:** la comprensión y la interpretación crítica, no solo la métrica. "Presentar una gráfica no equivale a analizarla."

## 2. Lo que NO está confirmado por escrito

La idea de "armar una arquitectura desde cero, hacer fine-tuning de un modelo preentrenado y compararlos" **no aparece en los documentos oficiales**. Lo que sí exigen es un modelo justificado (se permiten modelos de la literatura con referencia y modificaciones) y la evaluación externa. Nuestro plan del README (BiLSTM desde cero vs Transformer con fine-tuning) cumple la idea y es un diseño sólido, pero conviene confirmar con los profesores si fue indicación verbal en clase. Las mejoras adicionales (por ejemplo, datos en español) no están prohibidas por ningún documento revisado.

Contenido del curso relacionado: transfer learning (Taller 2), RNN/LSTM (Lecture 10), atención (Lecture 11 y 12) y el Taller 3 de SFT + LoRA con Qwen2.5-0.5B.

## 3. Datasets en español

| Dataset | Texto | Etiquetas | Español | Veredicto |
|---|---|---|---|---|
| [QCRI/CrisisBench-all-lang](https://huggingface.co/datasets/QCRI/CrisisBench-all-lang) | Sí | 16 clases humanitarias | 4.879 tweets (3.368 train, 485 dev, 1.026 test) | **El único utilizable.** CC BY-NC-SA 4.0 |
| Multi-Crisis (Sánchez et al., 2023) | No (solo IDs) | Binaria (relacionado o no) | 12.025 | Descartado |
| UrbangEnCy (Ecuador 2020) | No (solo IDs) | Tipo de emergencia urbana | 25.547 | Descartado |
| CREXWET (Zenodo) | No (solo IDs) | fire, flood o none (LLM) | ~91k | Descartado |

- El evento español principal es `2014_chile_earthquake_esp` (2.326 tweets en las tres particiones). El idioma lo asigna un detector automático.
- **Pendiente:** contar la distribución de clases en español (necesita descargar los archivos json de CrisisBench).
- **No existe un dataset público anotado de desastres en Colombia.** El set de prueba colombiano (200 a 300 tweets del sismo de Mw 7,4 del 10 de agosto de 2026 en Chocó) hay que armarlo y anotarlo a mano, por ejemplo con tweets de cuentas públicas como UNGRD o Cruz Roja Colombiana.

## 4. Plan sugerido

1. Entrenar con HumAID (inglés) más el español de CrisisBench, con un modelo multilingüe (XLM-R o mDeBERTa). BERTweet y DistilBERT son solo de inglés.
2. Reservar `2014_chile_earthquake_esp` completo como desastre en español no visto.
3. Usar el set colombiano anotado a mano como evaluación externa final.
4. Comparar contra el BiLSTM y contra el modelo entrenado solo en inglés, y analizar por qué baja el desempeño en cada caso.
