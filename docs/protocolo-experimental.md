# Protocolo experimental

Reglas fijas para todas las etapas, para que las comparaciones entre modelos sean justas. Se configuran en [`configs/protocolo.yaml`](../configs/protocolo.yaml). Los números vienen de `scripts/prepare_data.py` (2026-11-05).

## Datos

| Fuente | Qué es | Tamaño |
|---|---|---|
| [QCRI/HumAID-events](https://huggingface.co/datasets/QCRI/HumAID-events) | HumAID separado por desastre: 19 eventos, cada uno con `train`, `dev` y `test` (columnas `tweet_id`, `tweet_text`, `class_label`) | 76.484 tweets, **10 clases** |
| [QCRI/CrisisBench-all-lang](https://huggingface.co/datasets/QCRI/CrisisBench-all-lang) | Solo el evento `2014_chile_earthquake_esp` (español nativo) | 2.326 tweets |

- **Son 10 clases, no 11.** La documentación de HumAID menciona 11, pero `dont_know_cant_judge` no aparece en los datos.
- `HumAID-all` tiene los mismos tweets, pero sin columna de evento, así que no permite partir por desastre.
- Licencia: CC BY-NC-SA 4.0. Los datos no se suben al repositorio (es público); se regeneran con el script.

## Por qué partir por desastre completo
HumAID hizo sus splits 70/10/20 **dentro de cada evento**. Si se juntan, tweets del mismo desastre quedan en train y en test, con los mismos hashtags, lugares y temas. Esa fuga de evento infla el resultado y no mide si el modelo generaliza a un desastre nuevo. Por eso **cada evento va entero a un solo conjunto**.

## Conjuntos

| Conjunto | Eventos | Tweets | Uso |
|---|---|---:|---|
| train | 13 eventos (`train` y `dev` internos) | 47.671 | Entrenar; también vocabulario, SentencePiece y pesos de clase |
| val | `cyclone_idai_2019`, `kaikoura_earthquake_2016` | 6.124 | Hiperparámetros y early stopping |
| test | `puebla_mexico_earthquake_2017`, `maryland_floods_2018`, `hurricane_florence_2018`, `greece_wildfires_2018` | 10.536 | Resultado final, una sola vez |
| test_intra | `test` interno de los 13 eventos de train | 11.855 | Referencia optimista (con fuga de evento), solo para comparar |
| external_chile | Chile 2014 completo, en español | 2.326 | Evaluación externa en español nativo |
| colombia | Set anotado a mano (pendiente, issue #2) | — | Evaluación externa final |

Eventos de train: `california_wildfires_2018`, `canada_wildfires_2016`, `ecuador_earthquake_2016`, `hurricane_dorian_2019`, `hurricane_harvey_2017`, `hurricane_irma_2017`, `hurricane_maria_2017`, `hurricane_matthew_2016`, `italy_earthquake_aug_2016`, `kerala_floods_2018`, `midwestern_us_floods_2019`, `pakistan_earthquake_2019`, `srilanka_floods_2017`.

Regla: val, test, Chile 2014 y el set colombiano nunca se usan para entrenar. La comparación entre `test_intra` y `test` muestra cuánto infla el resultado ver el mismo desastre.

### Cómo se eligió el reparto
Se probaron todas las combinaciones que cumplen estas reglas (73 son factibles) y se eligió la de mejor puntaje:

1. Ningún evento en dos conjuntos.
2. Test con exactamente un evento de cada tipo (terremoto, huracán o ciclón, inundación, incendio); train con al menos dos de cada tipo.
3. Los 6 eventos de más de 7.000 tweets (Kerala, Harvey, Irma, Maria, Dorian, California) solo en train.
4. Cada clase con al menos 30 tweets en test y 15 en val.
5. Test entre 12 % y 22 % del total, y val entre 6 % y 12 %.
6. Puntaje: distancia entre la distribución de clases de val/test y la de train, más la desviación respecto a 16 % (test) y 8 % (val).

El reparto elegido deja test en 13,8 % y val en 8,0 %, e incluye a Puebla 2017, el terremoto latinoamericano más cercano al caso colombiano. La segunda mejor opción cambia Puebla por Ecuador 2016 y Grecia por Canadá 2016 (test 14,1 %).

## Distribución por clase

| Clase | train | val | test | test_intra | Chile 2014 |
|---|---:|---:|---:|---:|---:|
| rescue_volunteering_or_donation_effort | 12.978 | 2.076 | 2.891 | 3.233 | 496 |
| other_relevant_information | 8.296 | 717 | 1.041 | 2.058 | 418 |
| infrastructure_and_utility_damage | 5.484 | 666 | 604 | 1.366 | 125 |
| sympathy_and_support | 5.363 | 911 | 1.271 | 1.338 | 518 |
| injured_or_dead_people | 4.508 | 538 | 1.102 | 1.120 | 377 |
| not_humanitarian | 3.801 | 304 | 1.249 | 939 | 149 |
| caution_and_advice | 2.693 | 582 | 1.441 | 669 | 116 |
| displaced_people_and_evacuations | 2.560 | 144 | 637 | 636 | 25 |
| requests_or_urgent_needs | 1.846 | 167 | 140 | 460 | 64 |
| missing_or_found_people | 142 | 19 | 160 | 36 | 38 |

La tabla por evento y clase está en `results/etapa1/eventos_por_clase.csv`.

El desbalance es fuerte: de 12.978 a 142 en train. Por eso la métrica principal es **F1-macro** y se usará pérdida ponderada por clase.

**Costo conocido:** `missing_or_found_people` solo aparece en 4 eventos (California 179, Maryland 140, Grecia 20 e Idai 19), y Maryland es el único evento de inundación que la tiene. Con este reparto, toda la clase en train sale de California: quedan 142. Si se desactiva `intra_event_reference`, train recupera 36 más (178). En Chile 2014, `displaced_people_and_evacuations` (25) y `missing_or_found_people` (38) tienen pocos ejemplos, así que su F1 es ruidoso.

## Anti-fuga
| Medida | Resultado |
|---|---|
| Duplicados exactos dentro de cada conjunto (tras normalizar) | 5 eliminados |
| Textos de train con duplicado exacto en val, test o test_intra | 11 eliminados de train |
| Textos de train con casi-duplicado (TF-IDF, coseno ≥ 0,75, el umbral del paper de HumAID) | 278 eliminados de train |
| Textos de val repetidos en test (exactos y casi-duplicados) | 1 y 3 eliminados de val |

- La normalización para comparar es: minúsculas, sin URLs, menciones ni puntuación, y sin el prefijo `RT @usuario:`.
- Test y val nunca se recortan para proteger a train: siempre se elimina de train (o de val frente a test).
- La eliminación de casi-duplicados se repite hasta que no quede ninguno, porque al quitar textos cambian los pesos TF-IDF.
- Revisé a mano los pares más cercanos al umbral: son el mismo mensaje con otra mención o fuente.
- El script se detiene si un evento está en dos conjuntos, falta o no existe, y avisa si una clase queda bajo el mínimo.

## Mapeo de etiquetas de CrisisBench a HumAID
Solo se usa para Chile 2014. Está en [`src/humaid/labels.py`](../src/humaid/labels.py). Las 10 clases de HumAID tienen equivalente directo. Las etiquetas de CrisisBench sin equivalente (`affected_individual`, `disease_related`, `response_efforts`, `personal_update`, `physical_landslide`, `terrorism_related`) se descartarían y se reportarían; en Chile 2014 no apareció ninguna.

| CrisisBench | HumAID |
|---|---|
| requests_or_needs | requests_or_urgent_needs |
| displaced_and_evacuations | displaced_people_and_evacuations |
| infrastructure_and_utilities_damage | infrastructure_and_utility_damage |
| donation_and_volunteering | rescue_volunteering_or_donation_effort |
| missing_and_found_people | missing_or_found_people |
| el resto | mismo nombre |

## Limpieza (justificación)

| Decisión | Motivo |
|---|---|
| URLs a `HTTPURL`, menciones a `@USER` | Convención de BERTweet; sirve igual a XLM-R y al BiLSTM. El contenido de una URL o usuario no aporta a la categoría. |
| Hashtags: se conserva la palabra y se separa el CamelCase | Suelen cargar el tema (`#HurricaneIrma` pasa a `Hurricane Irma`). |
| Se quita el prefijo `RT @usuario:` y se decodifican entidades HTML | Ruido sin información. |
| Emojis y mayúsculas se conservan | Cada modelo decide. El tokenizador del BiLSTM pasa a minúsculas; los Transformers usan su propio tokenizador. |
| Se repara el texto con doble codificación (`AtenciÃ³n` a `Atención`) | El 38,7 % de Chile 2014 lo traía corrupto (900 de 2.326 tweets). Tras la reparación queda 1. |
| Tokenización de Transformers | Cada modelo usa su propio tokenizador sobre el texto limpio. |

Se guardan `text_raw` y `text_clean`.

## Reglas para las siguientes etapas
- Todo lo que se "aprende" de los datos (vocabulario, SentencePiece, pesos de clase, estadísticas) se calcula **solo con train**.
- Hiperparámetros y early stopping con val. Test se usa una sola vez, al final.
- En la etapa 2, un tweet traducido queda siempre en el mismo conjunto que su original; val y test traducidos son solo para evaluar.

## Limitaciones
- No se puede garantizar fuga cero. HumAID no trae `user_id`, así que no se puede partir por usuario: un mismo usuario puede tener tweets en train y en test.
- Los modelos preentrenados (BERTweet, XLM-R) pudieron ver tweets de 2016 a 2019 durante su preentrenamiento. El sismo colombiano de 2026 queda fuera de ese preentrenamiento.
- La clase `missing_or_found_people` tiene muy pocos ejemplos en todos los conjuntos.

## Cómo reproducirlo
Desde la raíz del repo:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/prepare_data.py   # descarga (~67 MB en data/raw/) y construye data/processed/ y results/etapa1/
```

## Pendiente de decidir
- Confirmar el reparto de eventos antes de entrenar.
- Decidir si se mantiene `test_intra` (cuesta 11.855 tweets de train, 36 de ellos de `missing_or_found_people`).
- La traducción y el corpus bilingüe (issue #6) quedan para la etapa 2.
