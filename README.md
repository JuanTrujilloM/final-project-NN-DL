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
* **Categorías (11 según la documentación oficial, pero los datos traen 10: `Don't know, can't judge` no aparece):**
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

## Primeros pasos
Usamos [`QCRI/HumAID-events`](https://huggingface.co/datasets/QCRI/HumAID-events) (los mismos tweets, separados por desastre) para poder reservar desastres completos. Protocolo, conjuntos y decisiones de limpieza en [`docs/protocolo-experimental.md`](docs/protocolo-experimental.md).

Desde la raíz del repo:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/prepare_data.py   # descarga y construye los conjuntos
```

### Entrenamiento (etapa 1)
Todo el entrenamiento está en [`notebooks/etapa1.ipynb`](notebooks/etapa1.ipynb). Está pensado para Kaggle (GPU e Internet activados): clona el repo, instala dependencias, prepara los datos y entrena:

- **Desde cero**: BiLSTM de 2 capas (atención + max pooling) con embeddings GloVe Twitter. Se hacen ablaciones con val y se entrena la configuración final.
- **Fine-tuning**: screening de 4 Transformers multilingües (XLM-R base, XLM-T, mDeBERTa-v3, XLM-R large) con la receta LP-FT y LLRD; se entrena el ganador. BERTweet queda como referencia solo en inglés.

Los hiperparámetros están en diccionarios dentro del notebook; con `LIMIT = 500` se hace una prueba rápida, y `RUN` permite repartir los bloques en varias sesiones.

Las corridas de selección (solo val) quedan en `results/etapa1/seleccion/`. Todo se entrena con la semilla 42. Cada modelo final guarda en `results/etapa1/<modelo>/` las curvas, el historial por época, métricas (F1-macro y ponderado) y matrices de confusión por conjunto, predicciones (sin el texto de los tweets) y un `resumen.json` con hiperparámetros, hardware y tiempo. La tabla comparativa es `results/etapa1/comparacion.csv` (una fila por modelo).

### Modelos entrenados
Los modelos finales de cada etapa se guardan en `models/etapa1/`, `models/etapa2/` y `models/etapa3/`, una carpeta por modelo, con lo necesario para clasificar textos nuevos sin los notebooks:

- **BiLSTM** (`bilstm_en`, `bilstm_bi`): `model.pt` (pesos), `vocab.json` y `config.json` (hiperparámetros y orden de las clases).
- **Transformer** (`<modelo>_en`, `<modelo>_bi`, `<modelo>_es`): `model.pt` (pesos del clasificador completo), `encoder/` (configuración del encoder), `tokenizer/` y `config.json`.

Kaggle los entrega en `modelos_etapa1.zip`, `modelos_etapa2.zip` y `modelos_etapa3.zip`. Los BiLSTM se suben al repositorio; los `model.pt` de los Transformers (~1 GB) superan el límite de GitHub y quedan fuera de git (`.gitignore`), así que se comparten aparte. Los checkpoints temporales del entrenamiento van a `models/checkpoints/`, que tampoco se sube.

### Etapa 3: modelos de Twitter en español
[`notebooks/etapa3.ipynb`](notebooks/etapa3.ipynb) entrena solo con HumAID traducido al español (`data/processed/humaid_es/`) y compara tres modelos preentrenados con tweets en español contra XLM-R large de las etapas 1 y 2 (que no se reentrena). Se corre en Kaggle con GPU, Internet activado y la traducción (`humaid_es.zip`) como input.

- **Candidatos**: BERTuit (`AIDA-UPM/BERTuit-base`), RoBERTuito (`pysentimiento/robertuito-base-uncased`, el modelo base y no el ajustado para sentimiento) y BERT colombiano (`johnatanebonilla/bert-colombiano-v1`).
- **Preprocesamiento**: cada modelo recibe los marcadores de su preentrenamiento (`adapt_text` en `src/humaid/data/preprocess.py`, que también usa la app): `<usr>`/`<url>` para BERTuit; `@usuario`/`url` y emojis como texto para RoBERTuito y BERT colombiano.
- **BERTuit** solo publica pesos de TensorFlow, que `transformers` 5 ya no carga; `scripts/convert_bertuit.py` los pasa a PyTorch sin TensorFlow y comprueba que el modelo convertido predice palabras enmascaradas.
- **Receta**: la de la etapa 1 (mean pooling, LP-FT, LLRD, pesos `sqrt`) con lr 2e-5, el de los modelos base; screening de 3 épocas y el ganador por F1-macro en val con hasta 10 épocas.

Screening (val, F1-macro): RoBERTuito 0,702, BERT colombiano 0,699 y BERTuit 0,695. La diferencia está dentro de lo esperable entre semillas; RoBERTuito fue el mejor en la fase lineal (0,598 frente a ~0,54), es decir, sus representaciones sin ajustar ya separan mejor las clases.

| F1-macro | RoBERTuito (etapa 3, español) | XLM-R large (etapa 2, bilingüe) | XLM-R large (etapa 1, inglés) |
|---|---|---|---|
| Chile 2014 | 0,405 | 0,431 | 0,412 |
| Chile 2014 (ponderado) | 0,557 | 0,570 | 0,554 |
| Inglés (`test_en` / `test`) | 0,639 | — | 0,740 |
| Parámetros | 109 M | 560 M | 560 M |
| Entrenamiento (T4) | 26 min | 143 min | 86 min |

En español nativo (Chile 2014), RoBERTuito no supera a XLM-R large: queda 0,026 por debajo del modelo bilingüe, que además se entrenó con el doble de datos (inglés y español), y prácticamente empata con el de la etapa 1. Lo logra con un modelo 5 veces más pequeño y más rápido de entrenar. Con tweets en inglés pierde unos 0,10 frente a XLM-R, pero no colapsa. Las clases que fallan en Chile (`missing_or_found_people`, `requests_or_urgent_needs`, `displaced_people_and_evacuations`) son las mismas en todos los modelos, lo que apunta a los datos (traducción automática de otros desastres) más que al modelo. Los resultados están en `results/etapa3/`; `val`, `test` y `test_intra` son en español y no se comparan directamente con las etapas anteriores.

## Extensión al Español y al Contexto Colombiano
HumAID está compuesto únicamente por tweets en inglés de desastres ocurridos en otros países, mientras que el contexto que nos interesa es el colombiano, donde la información se publica en español y con expresiones, nombres de lugares y formas de reportar propias de la región.

## Aplicación de demostración

La carpeta [`app/`](app) muestra cómo funcionaría el sistema durante un desastre, con dos plataformas conectadas en tiempo real:

- **Red social** (`/red`): un feed al estilo de X donde cualquier persona publica.
- **Centro de información** (`/centro`): cada publicación se limpia con `clean_tweet` (el mismo preprocesamiento del entrenamiento), la clasifica el modelo elegido y aparece al instante agrupada por frente de respuesta (Personas, Necesidades y ayuda, Infraestructura y avisos, Contexto) o por cada una de las 10 categorías.
- **Demo** (`/demo`): las dos plataformas lado a lado.

El backend (FastAPI, `app/backend/`) descubre los modelos guardados en `models/etapaX/<modelo>/` y deja elegir en el centro con cuál clasificar; solo mantiene en memoria el modelo activo. Las publicaciones nuevas llegan a todas las pantallas abiertas por Server-Sent Events. El frontend es React + Vite + Tailwind (`app/frontend/`).

Para desarrollo, desde la raíz del repositorio y en dos terminales:

```bash
.venv/bin/pip install -r app/requirements.txt
.venv/bin/python -m uvicorn app.backend.main:app --reload --reload-dir app/backend --timeout-graceful-shutdown 2 --port 8000
```

```bash
cd app/frontend && npm install && npm run dev
```

Después abre `http://localhost:5173/demo`. Para una sola terminal, compila el frontend una vez (`npm run build` en `app/frontend`) y abre `http://localhost:8000/demo`, que lo sirve FastAPI.

Los pesos de los Transformers no están en git (ver *Modelos entrenados*): copia su `model.pt` en la carpeta de cada modelo; los que no lo tienen aparecen deshabilitados en el selector.

## Objetivo General:
Clasificar tweets publicados durante desastres naturales en las 11 categorías humanitarias del dataset HumAID, mediante el desarrollo y la comparación de un modelo BiLSTM y un modelo Transformer preentrenado, evaluando su capacidad de generalización sobre desastres no utilizados durante el entrenamiento, con el fin de apoyar la identificación rápida de información relevante para los equipos de respuesta a emergencias.

## Objetivos Específicos
* Preprocesar los tweets del dataset HumAID (limpieza de URLs, menciones, hashtags y caracteres especiales, y tokenización) y dividirlos en conjuntos de entrenamiento, validación y prueba, reservando desastres completos que el modelo no verá durante el entrenamiento para la evaluación externa.

* Implementar y entrenar un modelo BiLSTM desde cero como modelo base, y ajustar mediante fine-tuning un modelo Transformer preentrenado (BERTweet o DistilBERT) para la misma tarea de clasificación.

* Evaluar y comparar el desempeño de ambos modelos mediante la métrica F1-macro y matrices de confusión, tanto en el conjunto de prueba como en los desastres no vistos, identificando las categorías en las que cada modelo presenta mayores dificultades.