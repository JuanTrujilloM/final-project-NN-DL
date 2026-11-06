"""Carga y ejecución de clasificadores conectables a la API."""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, Protocol, Sequence


class TextClassifier(Protocol):
    """Contrato mínimo para un modelo entrenado que se conecte al backend.

    El objeto serializado debe implementar ``predict_proba(texts)`` y devolver
    una matriz con una fila por texto y una columna por etiqueta.
    """

    classes_: Sequence[str]

    def predict_proba(self, texts: Iterable[str]) -> Any:
        ...


class ModelNotReadyError(RuntimeError):
    """Indica que el artefacto solicitado aún no está instalado."""


class ModelArtifactError(RuntimeError):
    """Indica que un artefacto no cumple el contrato del backend."""


class ModelService:
    """Administra modelos reales instalados en ``models/``."""

    def __init__(self, labels: Dict[str, str], model_dir: Path) -> None:
        self.labels = labels
        self.model_dir = model_dir
        self._loaded: Dict[str, TextClassifier] = {}

    def artifact_path(self, model_id: str) -> Path:
        return self.model_dir / f"{model_id}.pkl"

    def is_available(self, model_id: str) -> bool:
        return self.artifact_path(model_id).is_file()

    def load(self, model_id: str) -> TextClassifier:
        if model_id in self._loaded:
            return self._loaded[model_id]

        path = self.artifact_path(model_id)
        if not path.is_file():
            raise ModelNotReadyError(
                f"No existe el artefacto para '{model_id}'. "
                f"Colócalo en {path}."
            )
        try:
            with path.open("rb") as artifact:
                model = pickle.load(artifact)
        except (
            OSError,
            EOFError,
            pickle.PickleError,
            AttributeError,
            ImportError,
            ModuleNotFoundError,
        ) as error:
            raise ModelArtifactError(f"No se pudo cargar {path}: {error}") from error

        if not callable(getattr(model, "predict_proba", None)):
            raise ModelArtifactError(
                f"El modelo {path} debe implementar predict_proba(texts)."
            )
        classes = getattr(model, "classes_", None)
        if classes is None or not set(classes).issubset(self.labels):
            raise ModelArtifactError(
                f"El modelo {path} debe incluir classes_ con IDs de LABELS."
            )
        self._loaded[model_id] = model
        return model

    def predict(self, model_id: str, text: str) -> tuple[str, Dict[str, float]]:
        model = self.load(model_id)
        try:
            raw_probabilities = model.predict_proba([text])[0]
            probabilities = {
                label: round(float(probability), 4)
                for label, probability in zip(model.classes_, raw_probabilities)
            }
        except (IndexError, TypeError, ValueError) as error:
            raise ModelArtifactError(
                f"El modelo '{model_id}' devolvió probabilidades inválidas: {error}"
            ) from error

        if not probabilities or abs(sum(probabilities.values()) - 1) > 0.02:
            raise ModelArtifactError(
                f"El modelo '{model_id}' debe devolver probabilidades que sumen 1."
            )
        predicted = max(probabilities, key=probabilities.get)
        return predicted, probabilities


def default_model_dir(root: Path) -> Path:
    """Obtiene la carpeta de artefactos, configurable con HUMAID_MODEL_DIR."""

    configured = os.environ.get("HUMAID_MODEL_DIR")
    return Path(configured) if configured else root / "models"
