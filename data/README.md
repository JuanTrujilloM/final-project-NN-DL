# Datos

Esta carpeta **no se sube a git** (ver `.gitignore`): las licencias de HumAID y CrisisBench son CC BY-NC-SA 4.0 y el repositorio es público. Se regenera con:

```bash
.venv/bin/python scripts/prepare_data.py
```

| Carpeta | Contenido |
|---|---|
| `raw/humaid_events/` | HumAID por desastre, tal como se descarga |
| `raw/crisisbench/` | Subconjunto humanitario de CrisisBench |
| `processed/humaid_en/` | `train.csv`, `val.csv`, `test.csv` (split por desastre completo) y `test_intra.csv` (referencia optimista). Columnas: `event`, `split` (split interno original de HumAID), `tweet_id`, `text_raw`, `label`, `text_clean`, `role` |
| `processed/chile2014_es/` | `test.csv` con Chile 2014 completo, en español, con etiquetas de HumAID |
| `colombia/` | Set colombiano anotado a mano. Antes de guardar texto de tweets, revisar privacidad y términos de uso de X |

El detalle de cada decisión está en [`docs/protocolo-experimental.md`](../docs/protocolo-experimental.md).
