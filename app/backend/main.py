"""API de demostración para clasificar publicaciones humanitarias."""

from pathlib import Path
import re
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .model_service import (
    ModelArtifactError,
    ModelNotReadyError,
    ModelService,
    default_model_dir,
)

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "app" / "frontend"

LABELS = {
    "caution_and_advice": "Precauciones y consejos",
    "displaced_people_and_evacuations": "Desplazados y evacuaciones",
    "infrastructure_and_utility_damage": "Daños en infraestructura",
    "injured_or_dead_people": "Heridos o muertos",
    "missing_or_found_people": "Personas desaparecidas",
    "not_humanitarian": "No humanitario",
    "other_relevant_information": "Otra información relevante",
    "requests_or_urgent_needs": "Solicitudes o necesidades urgentes",
    "rescue_volunteering_or_donation_effort": "Rescate, voluntariado o donaciones",
    "sympathy_and_support": "Simpatía y apoyo",
}

MODELS = [
    {
        "id": "simulador-humaid",
        "name": "Simulador HumAID",
        "description": "Predicción demostrativa basada en palabras clave.",
        "status": "demo",
    },
    {
        "id": "bilstm-base",
        "name": "BiLSTM base",
        "description": "Espacio reservado para el modelo entrenado del proyecto.",
        "status": "planned",
    },
    {
        "id": "transformer-es",
        "name": "Transformer en español",
        "description": "Espacio reservado para el modelo Transformer ajustado.",
        "status": "planned",
    },
]

KEYWORDS = {
    "requests_or_urgent_needs": (
        "ayuda", "agua", "comida", "necesito", "urgente", "rescate", "medicina",
    ),
    "infrastructure_and_utility_damage": (
        "puente", "carretera", "daño", "derrumb", "sin luz", "inundad", "vía",
    ),
    "injured_or_dead_people": (
        "herido", "herida", "muerto", "falleció", "ambulancia", "lesionado",
    ),
    "displaced_people_and_evacuations": (
        "evac", "desplaz", "refugio", "albergue", "desalojo",
    ),
    "rescue_volunteering_or_donation_effort": (
        "donar", "donación", "voluntario", "rescate", "brigada",
    ),
    "caution_and_advice": (
        "alerta", "precaución", "recomend", "evite", "información oficial",
    ),
    "missing_or_found_people": (
        "desaparecid", "buscamos", "encontrad", "perdido",
    ),
    "sympathy_and_support": (
        "fuerza", "solidaridad", "ánimo", "acompañamos",
    ),
}

model_service = ModelService(LABELS, default_model_dir(ROOT))
app = FastAPI(title="AlertaNexo API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    model: str = Field(default="simulador-humaid")


class PredictionResponse(BaseModel):
    model: str
    label: str
    label_name: str
    confidence: float
    probabilities: Dict[str, float]


def _tokenize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def predict(text: str) -> PredictionResponse:
    normalized = _tokenize(text)
    scores = {label: 0.05 for label in LABELS}
    for label, words in KEYWORDS.items():
        scores[label] += sum(0.35 for word in words if word in normalized)
    total = sum(scores.values())
    probabilities = {label: round(score / total, 4) for label, score in scores.items()}
    predicted = max(probabilities, key=probabilities.get)
    confidence = probabilities[predicted]
    return PredictionResponse(
        model="simulador-humaid",
        label=predicted,
        label_name=LABELS[predicted],
        confidence=confidence,
        probabilities=probabilities,
    )


def predict_with_model(model_id: str, text: str) -> PredictionResponse:
    label, probabilities = model_service.predict(model_id, text)
    return PredictionResponse(
        model=model_id,
        label=label,
        label_name=LABELS[label],
        confidence=probabilities[label],
        probabilities=probabilities,
    )


@app.get("/models")
def list_models() -> List[dict]:
    return [
        {
            **model,
            "available": model["id"] == "simulador-humaid"
            or model_service.is_available(model["id"]),
        }
        for model in MODELS
    ]


@app.post("/predict", response_model=PredictionResponse)
def classify(request: PredictionRequest) -> PredictionResponse:
    if request.model not in {model["id"] for model in MODELS}:
        raise HTTPException(status_code=400, detail=f"Modelo no disponible: {request.model}")
    if request.model == "simulador-humaid":
        return predict(request.text)
    try:
        return predict_with_model(request.model, request.text)
    except ModelNotReadyError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ModelArtifactError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


@app.get("/{asset_path:path}")
def frontend_assets(asset_path: str) -> FileResponse:
    asset = (FRONTEND / asset_path).resolve()
    if FRONTEND not in asset.parents or not asset.is_file():
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return FileResponse(asset)
