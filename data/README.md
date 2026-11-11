# Datos

Esta carpeta **no se sube a git** (ver `.gitignore`): las licencias de HumAID y CrisisBench son CC BY-NC-SA 4.0 y el repositorio es público. Se regenera con:

```bash
.venv/bin/python scripts/prepare_data.py
```

| Carpeta | Contenido |
|---|---|
| `raw/humaid_events/` | HumAID por desastre, tal como se descarga |
| `raw/crisisbench/` | Subconjunto humanitario de CrisisBench |
| `raw/humaid_events_translated/` | HumAID traducido al español (salida de `notebooks/traduccion.ipynb`): `train.csv`, `val.csv`, `test.csv`, `test_intra.csv` con las columnas de `humaid_en` más `text_es` y `traductor`; también `cache/`, que permite retomar la traducción si se cae la sesión |
| `raw/colombia/<fuente>/` | Posts de desastres colombianos anotados a mano, una subcarpeta por fuente (`x/`, `bluesky/`, `reddit/`, ...) y un CSV por evento (mismas columnas en todas: `event`, `tweet_id`, `text_raw`, `label`, ...). `text_raw` es el texto original. No se suben a git: tienen nombres de personas reales |
| `processed/humaid_en/` | `train.csv`, `val.csv`, `test.csv` (split por desastre completo) y `test_intra.csv` (referencia optimista). Columnas: `event`, `split` (split interno original de HumAID), `tweet_id`, `text_raw`, `label`, `text_clean`, `role` |
| `processed/chile2014_es/` | `test.csv` con Chile 2014 completo, en español, con etiquetas de HumAID |
| `processed/colombia_es/` | `test.csv` con todas las fuentes colombianas unidas (sin columna de fuente) y limpias con `clean_tweet`, mismas columnas que Chile 2014. Sale de `scripts/prepare_data.py` cuando hay CSV en `raw/colombia/<fuente>/` |
| `processed/humaid_es/` | La traducción con el mismo formato y los mismos conjuntos que `humaid_en`: el español va en `text_clean`, `text_raw` conserva el tweet original en inglés y se agrega `traductor` |
| `processed/bilingue/` | Corpus bilingüe de la etapa 2: `humaid_en` y `humaid_es` juntos en cada conjunto. Columnas: `tweet_id`, `event`, `role`, `lang`, `fuente`, `label`, `text_clean` |

## Traducción y corpus bilingüe (etapa 2)

La traducción se hace en Kaggle (GPU) y no se regenera localmente. Para tenerla en local, descomprimir el `humaid_es.zip` que genera el notebook de traducción y correr los dos pasos:

```bash
mkdir -p data/raw/humaid_events_translated
unzip ~/Downloads/humaid_es.zip -d data/raw/humaid_events_translated
.venv/bin/python scripts/prepare_humaid_es.py
.venv/bin/python scripts/prepare_bilingual.py
```

- `prepare_humaid_es.py` pasa la traducción a `processed/humaid_es/` y valida que cada traducción coincida uno a uno con su original (mismo `tweet_id`, evento, etiqueta y conjunto).
- `prepare_bilingual.py` une `humaid_en` y `humaid_es` en `processed/bilingue/`, quita de train las traducciones que quedaron iguales a una de evaluación y se detiene si detecta fuga (incluido Chile 2014, que es solo de prueba). El reporte de la traducción (sin texto de tweets) está en `results/traduccion/`.

El detalle de cada decisión está en [`docs/protocolo-experimental.md`](../docs/protocolo-experimental.md).
