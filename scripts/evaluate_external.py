import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from app.backend.classifiers import LoadedModel


# Same per-set outputs as the training notebooks: metrics, confusion matrix and predictions without tweet text.
def report(df, preds, labels, name, model_name, out_dir):
    y_true, y_pred = df["label"].tolist(), preds
    present = [label for label in labels if label in set(y_true)]
    metrics = {
        "f1_macro": f1_score(y_true, y_pred, labels=present, average="macro", zero_division=0),
        "f1_weighted": f1_score(y_true, y_pred, labels=present, average="weighted", zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "n": len(y_true),
    }
    metrics["por_clase"] = classification_report(y_true, y_pred, labels=present, output_dict=True, zero_division=0)
    (out_dir / f"metricas_{name}.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))

    cm = confusion_matrix(y_true, y_pred, labels=present)
    cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    fig, axes = plt.subplots(1, 2, figsize=(22, 9))
    for ax, data, fmt, title in zip(axes, [cm, cm_norm], ["d", ".2f"], ["Conteos absolutos", "Proporción por clase (recall)"]):
        sns.heatmap(data, annot=True, fmt=fmt, cmap="Blues", xticklabels=present, yticklabels=present, ax=ax)
        ax.set_xlabel("Predicción")
        ax.set_ylabel("Real")
        ax.set_title(f"{model_name} | {name}\n{title}")
    plt.tight_layout()
    fig.savefig(out_dir / f"confusion_{name}.png", dpi=120)
    plt.close(fig)

    pd.DataFrame({"tweet_id": df["tweet_id"], "event": df["event"], "lang": df["lang"],
                  "label": y_true, "pred": y_pred}).to_csv(out_dir / f"predicciones_{name}.csv", index=False)
    return {key: metrics[key] for key in ("f1_macro", "f1_weighted", "accuracy", "n")}


# Adds the new set as two columns (macro and weighted F1) to an existing comparison table.
def add_to_table(path, name, scores, stage=None):
    if not path.exists():
        return
    table = pd.read_csv(path)
    rows = table["etapa"] == stage if stage is not None and "etapa" in table else True
    for metric, column in (("f1_macro", f"F1 {name}"), ("f1_weighted", f"F1 ponderado {name}")):
        if column not in table:
            table[column] = np.nan
        for model, result in scores.items():
            table.loc[rows & (table["modelo"] == model), column] = round(result[metric], 4)
    table.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Evalúa los modelos guardados en models/ con un conjunto externo")
    parser.add_argument("--data", default="data/processed/colombia_es/test.csv")
    parser.add_argument("--name", default="colombia")
    args = parser.parse_args()

    df = pd.read_csv(ROOT / args.data, dtype={"tweet_id": str})
    print(f"{args.name}: {len(df)} tweets")
    scores_by_stage = {}
    for model_dir in sorted((ROOT / "models").glob("etapa*/*")):
        if not (model_dir / "model.pt").is_file():
            print(f"  {model_dir.parent.name}/{model_dir.name}: sin model.pt, se omite")
            continue
        stage, family = model_dir.parent.name, model_dir.name
        out_dir = ROOT / "results" / stage / family
        model = LoadedModel(model_dir)
        probabilities = model.predict(df["text_clean"].tolist())
        preds = [max(p, key=p.get) for p in probabilities]
        result = report(df, preds, model.labels, args.name, family, out_dir)
        summary_path = out_dir / "resumen.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text())
            summary.setdefault("resultados", {})[args.name] = result
            summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
        scores_by_stage.setdefault(stage, {})[family] = result
        print(f"  {stage}/{family}: F1-macro {result['f1_macro']:.4f} | F1 ponderado {result['f1_weighted']:.4f} | accuracy {result['accuracy']:.4f}")

    for stage, scores in scores_by_stage.items():
        add_to_table(ROOT / "results" / stage / "comparacion.csv", args.name, scores)
        # Each stage from 2 on keeps a table with its models and those of the previous stages.
        for table in sorted((ROOT / "results").glob("etapa*/comparacion_etapas.csv")):
            add_to_table(table, args.name, scores, stage=int(stage.removeprefix("etapa")))
    print("Listo. Resultados en results/etapaX/<modelo>/ y columnas nuevas en las tablas de comparación")


if __name__ == "__main__":
    main()
