import csv
import json
import math
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from .registry import display_name

ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = ROOT / "results"
FILES_URL = "/api/results/files"

router = APIRouter(prefix="/api/results")


def number(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return value
    if math.isnan(parsed):
        return None
    return int(parsed) if parsed.is_integer() and "." not in value else parsed


def read_csv(path):
    with path.open(encoding="utf-8") as f:
        return [{key: number(value) for key, value in row.items()} for row in csv.DictReader(f)]


def file_url(path):
    return f"{FILES_URL}/{path.relative_to(RESULTS_ROOT).as_posix()}"


def stage_number(stage_dir):
    return int(stage_dir.name.removeprefix("etapa"))


def model_summary(model_dir):
    summary = json.loads((model_dir / "resumen.json").read_text())
    resources = summary.get("recursos", {})
    sets = list(summary.get("resultados", {}))
    return {
        "id": f"{model_dir.parent.name}/{model_dir.name}",
        "family": model_dir.name,
        "name": display_name(model_dir.name),
        "kind": summary.get("tipo"),
        "base_model": summary.get("modelo"),
        "val_f1_macro": summary.get("mejor_val_f1_macro"),
        "epochs": summary.get("epocas_entrenadas"),
        "minutes": resources.get("tiempo_entrenamiento_min"),
        "gpu": resources.get("gpu"),
        "parameters": summary.get("parametros"),
        "results": summary.get("resultados", {}),
        "curves": file_url(model_dir / "curvas.png") if (model_dir / "curvas.png").exists() else None,
        "confusion": {name: file_url(model_dir / f"confusion_{name}.png") for name in sets
                      if (model_dir / f"confusion_{name}.png").exists()},
    }


def stage_summary(stage_dir):
    selection_dir = stage_dir / "seleccion"
    return {
        "id": stage_dir.name,
        "number": stage_number(stage_dir),
        "comparison": read_csv(stage_dir / "comparacion.csv") if (stage_dir / "comparacion.csv").exists() else [],
        "models": [model_summary(d) for d in sorted(stage_dir.iterdir()) if (d / "resumen.json").exists()],
        "selection": [{"name": f.stem, "rows": read_csv(f)} for f in sorted(selection_dir.glob("*.csv"))]
        if selection_dir.is_dir() else [],
    }


# Every stage with its comparison table, model summaries and selection tables, plus the data tables.
@router.get("")
def results_index():
    stages = sorted((d for d in RESULTS_ROOT.glob("etapa*") if d.is_dir()), key=stage_number)
    all_stages = [d / "comparacion_etapas.csv" for d in stages if (d / "comparacion_etapas.csv").exists()]
    data_dir = RESULTS_ROOT / "data"
    return {
        "stages": [stage_summary(d) for d in stages],
        "all_stages": read_csv(all_stages[-1]) if all_stages else [],
        "data": {f.stem: read_csv(f) for f in sorted(data_dir.glob("*.csv"))} if data_dir.is_dir() else {},
    }


# Per-class metrics of every evaluated set and the training history of one model.
@router.get("/model/{stage}/{family}")
def model_detail(stage: str, family: str):
    model_dir = (RESULTS_ROOT / stage / family).resolve()
    if RESULTS_ROOT not in model_dir.parents or not (model_dir / "resumen.json").exists():
        raise HTTPException(status_code=404, detail=f"Sin resultados para {stage}/{family}")
    summary = json.loads((model_dir / "resumen.json").read_text())
    per_class = {}
    for path in sorted(model_dir.glob("metricas_*.json")):
        report = json.loads(path.read_text())["por_clase"]
        per_class[path.stem.removeprefix("metricas_")] = {
            label: values for label, values in report.items() if label not in ("accuracy", "macro avg", "weighted avg")
        }
    history = model_dir / "history.csv"
    return {
        "per_class": per_class,
        "history": read_csv(history) if history.exists() else [],
        "hyperparameters": summary.get("hiperparametros", {}),
    }


# Only the images of results/; predictions and summaries go through the endpoints above.
@router.get("/files/{path:path}")
def result_file(path: str):
    target = (RESULTS_ROOT / path).resolve()
    if RESULTS_ROOT not in target.parents or target.suffix != ".png" or not target.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(target)
