---
title: AlertaNexo
emoji: 🆘
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
short_description: Clasificación de tweets humanitarios en situaciones de desastre
---

# AlertaNexo

Demo del proyecto final de Redes Neuronales y Aprendizaje Profundo (EAFIT): una red social donde se publica y un centro de información que clasifica cada publicación en tiempo real con los modelos entrenados sobre HumAID.

- `/demo`: red social y centro de información lado a lado.
- `/centro`: centro de información, con selector de modelo.
- `/resultados`: métricas, gráficas y comparaciones de las tres etapas.

El código viene de [JuanTrujilloM/final-project-NN-DL](https://github.com/JuanTrujilloM/final-project-NN-DL); los pesos de los Transformers se descargan al arrancar desde un repositorio privado del Hub, con el secreto `HF_TOKEN` del Space.

Las publicaciones viven en memoria: se pierden cuando el Space se reinicia.
