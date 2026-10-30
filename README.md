# Clasificación de Tweets Humanitarios en Situaciones de Desastre

## Integrantes
* Juan Esteban Trujillo Montes
* Andrés Pérez Quinchía
* David Alejandro Gutiérrez Leal
* Mariamny del Valle Ramírez Telles

## Contexto y Justificación
Durante un desastre natural (terremotos, huracanes, inundaciones o incendios forestales) las personas afectadas y los testigos publican miles de mensajes por minuto en redes sociales como Twitter. Entre ellos hay información crítica para los equipos de respuesta como personas que piden ayuda, daños en infraestructura, heridos, desaparecidos o necesidades urgentes. Pero se mezcla con mensajes de simpatía, opiniones y ruido que no aportan a la operación humanitaria y más en una situación tan crítica como un desastre en donde contar con información centralizada y de forma rápida es fundamental.

Revisar ese volumen a mano es inviable en la ventana de tiempo en la que la información es útil. Un clasificador automático de texto permite filtrar y priorizar los tweets según su categoría humanitaria, y reduce el tiempo entre que alguien reporta una necesidad y que un equipo de respuesta la ve.

## Dataset
Vamos a usar **HumAID** (Alam, Qazi, Imran y Ofli, *HumAID: Human-Annotated Disaster Incidents Data from Twitter*, ICWSM 2021).

* **Fuente:** [arXiv:2104.03090](https://arxiv.org/abs/2104.03090) y [HumAID en Hugging Face](https://huggingface.co/datasets/QCRI/HumAID-all). Es de acceso público.
* **Tamaño:** unos 77 mil tweets anotados manualmente (76.484 filas en la versión de Hugging Face), muestreados de cerca de 24 millones de tweets recolectados.
* **Eventos:** 19 desastres naturales ocurridos entre 2016 y 2019, de cuatro tipos: terremotos, huracanes, inundaciones e incendios forestales.
* **Idioma:** inglés.
* **Anotación:** manual, por crowdworkers en Amazon Mechanical Turk. Cada tweet tiene una sola etiqueta humanitaria.
* **Campos:** `tweet_text` (el texto del tweet) y `class_label` (la categoría).
* **Categorías (11 según la documentación oficial):**
  1. Caution and advice (precauciones y consejos)
  2. Displaced people and evacuations (desplazados y evacuaciones)
  3. Don't know, can't judge (no se puede juzgar)
  4. Infrastructure and utility damage (daños en infraestructura y servicios)
  5. Injured or dead people (heridos o muertos)
  6. Missing or found people (personas desaparecidas o encontradas)
  7. Not humanitarian (no humanitario)
  8. Other relevant information (otra información relevante)
  9. Requests or urgent needs (solicitudes o necesidades urgentes)
  10. Rescue, volunteering, or donation effort (rescate, voluntariado y donaciones)
  11. Sympathy and support (simpatía y apoyo)

## Extensión al Español y al Contexto Colombiano
HumAID está compuesto únicamente por tweets en inglés de desastres ocurridos en otros países, mientras que el contexto que nos interesa es el colombiano, donde la información se publica en español y con expresiones, nombres de lugares y formas de reportar propias de la región.

Como parte del proyecto queremos explorar si es posible que el modelo entrenado sobre HumAID llegue a entender tweets en español, y probarlo con tweets de desastres que han ocurrido en Colombia, como el último terremoto. Todavía no tenemos definida la manera de lograrlo pero es una idea que queremos investigar y que dependerá de lo que encontremos sobre los datos disponibles.

## Objetivo General:
Clasificar tweets publicados durante desastres naturales en las 11 categorías humanitarias del dataset HumAID, mediante el desarrollo y la comparación de un modelo BiLSTM y un modelo Transformer preentrenado, evaluando su capacidad de generalización sobre desastres no utilizados durante el entrenamiento, con el fin de apoyar la identificación rápida de información relevante para los equipos de respuesta a emergencias.

## Objetivos Específicos
* Preprocesar los tweets del dataset HumAID (limpieza de URLs, menciones, hashtags y caracteres especiales, y tokenización) y dividirlos en conjuntos de entrenamiento, validación y prueba, reservando desastres completos que el modelo no verá durante el entrenamiento para la evaluación externa.

* Implementar y entrenar un modelo BiLSTM desde cero como modelo base, y ajustar mediante fine-tuning un modelo Transformer preentrenado (BERTweet o DistilBERT) para la misma tarea de clasificación.

* Evaluar y comparar el desempeño de ambos modelos mediante la métrica F1-macro y matrices de confusión, tanto en el conjunto de prueba como en los desastres no vistos, identificando las categorías en las que cada modelo presenta mayores dificultades.