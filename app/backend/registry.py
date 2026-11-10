import json
import threading
from pathlib import Path

from .classifiers import LoadedModel

FAMILY_NAMES = {
    "bilstm": "BiLSTM",
    "xlmr_large": "XLM-R large",
    "xlmr_base": "XLM-R base",
    "xlmt_base": "XLM-T",
    "mdeberta_base": "mDeBERTa-v3",
    "bertweet": "BERTweet",
}
LANGUAGE_NAMES = {"en": "solo inglés", "bi": "bilingüe"}


def describe(config_path):
    model_dir = config_path.parent
    config = json.loads(config_path.read_text())
    stage = model_dir.parent.name
    family, _, language = model_dir.name.rpartition("_")
    return {
        "id": f"{stage}/{model_dir.name}",
        "name": f"{FAMILY_NAMES.get(family, family)} · {LANGUAGE_NAMES.get(language, language)}",
        "stage": int(stage.removeprefix("etapa")) if stage.startswith("etapa") else None,
        "kind": config["tipo"],
        "val_f1_macro": config.get("mejor_val_f1_macro"),
        "available": (model_dir / "model.pt").is_file(),
        "path": str(model_dir),
    }


# Default order: bilingual stage first, transformer before BiLSTM.
def preference(model):
    return (-(model["stage"] or 0), model["kind"] != "transformer")


# Finds the exported models and keeps only the active one in memory (XLM-R large needs ~2 GB of RAM).
class ModelRegistry:
    def __init__(self, models_root):
        self.models_root = Path(models_root)
        self.lock = threading.Lock()
        self.loaded_id, self.loaded = None, None
        self.models = self.discover()
        available = sorted((m for m in self.models.values() if m["available"]), key=preference)
        self.active_id = available[0]["id"] if available else None

    def discover(self):
        found = [describe(path) for path in sorted(self.models_root.glob("*/*/config.json"))]
        return {model["id"]: model for model in found if "checkpoints" not in model["path"]}

    def public_models(self):
        return [{k: v for k, v in m.items() if k != "path"} for m in sorted(self.models.values(), key=preference)]

    def get(self, model_id):
        with self.lock:
            if self.loaded_id != model_id:
                self.loaded, self.loaded_id = None, None
                self.loaded = LoadedModel(self.models[model_id]["path"])
                self.loaded_id = model_id
            return self.loaded

    def set_active(self, model_id):
        model = self.models.get(model_id)
        if model is None or not model["available"]:
            raise KeyError(model_id)
        self.get(model_id)
        self.active_id = model_id

    def classify(self, texts, model_id=None):
        model_id = model_id or self.active_id
        if model_id is None:
            raise RuntimeError("No hay modelos con pesos en models/")
        model = self.get(model_id)
        with self.lock:
            return model_id, model.predict(texts)
