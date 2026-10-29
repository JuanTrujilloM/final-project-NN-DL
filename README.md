# Clasificación de Tweets Humanitarios en Situaciones de Desastre

## Objetivo General:
Clasificar tweets publicados durante desastres naturales en las 11 categorías humanitarias del dataset HumAID, mediante el desarrollo y la comparación de un modelo BiLSTM y un modelo Transformer preentrenado, evaluando su capacidad de generalización sobre desastres no utilizados durante el entrenamiento, con el fin de apoyar la identificación rápida de información relevante para los equipos de respuesta a emergencias.

## Objetivos Específicos
* Preprocesar los tweets del dataset HumAID (limpieza de URLs, menciones, hashtags y caracteres especiales, y tokenización) y dividirlos en conjuntos de entrenamiento, validación y prueba, reservando desastres completos que el modelo no verá durante el entrenamiento para la evaluación externa.

* Implementar y entrenar un modelo BiLSTM desde cero como modelo base, y ajustar mediante fine-tuning un modelo Transformer preentrenado (BERTweet o DistilBERT) para la misma tarea de clasificación.

* Evaluar y comparar el desempeño de ambos modelos mediante la métrica F1-macro y matrices de confusión, tanto en el conjunto de prueba como en los desastres no vistos, identificando las categorías en las que cada modelo presenta mayores dificultades.