import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import snapshot_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from humaid.config import load_config
from humaid.labels import CRISISBENCH_TO_HUMAID


def read_any_json(path):
    try:
        return pd.read_json(path, lines=True, dtype={"id": str})
    except ValueError:
        return pd.read_json(path, dtype={"id": str})


def load_humanitarian(repo, local_dir):
    # Reuses the files already in data/raw if they are there.
    snapshot_download(repo, repo_type="dataset", allow_patterns=["humanitarian/*"], local_dir=local_dir)
    files = sorted(p for p in Path(local_dir, "humanitarian").rglob("*") if p.suffix in {".json", ".jsonl"})
    if not files:
        sys.exit(f"No hay archivos JSON en {local_dir}/humanitarian")
    parts = []
    for path in files:
        df = read_any_json(path)
        df["split_original"] = next((s for s in ("train", "dev", "test") if s in path.name), path.stem)
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


def main():
    cfg = load_config()
    raw = Path(cfg["paths"]["raw"]) / "crisisbench"
    res_dir = Path(cfg["paths"]["results"])
    chile_event = cfg["chile"]["event"]

    df = load_humanitarian(cfg["chile"]["repo"], raw)
    print(f"CrisisBench humanitarian: {len(df):,} tweets, {df['lang'].nunique()} idiomas")

    es = df[df["lang"] == "es"].copy()
    es["label"] = es["class_label"].map(CRISISBENCH_TO_HUMAID)
    es["es_chile"] = es["event"].str.contains("chile", case=False)
    conf = pd.to_numeric(es["lang_conf"], errors="coerce")
    print(f"En español: {len(es):,}")
    print(f"  confianza de idioma < 0,9 (API de Google): {int((conf < 0.9).sum()):,}")
    print(f"  sin equivalente en HumAID: {int(es['label'].isna().sum()):,}",
          es.loc[es["label"].isna(), "class_label"].value_counts().to_dict())
    print(f"  en eventos de Chile (se excluyen): {int(es['es_chile'].sum()):,}",
          es.loc[es["es_chile"], "event"].value_counts().to_dict())
    if chile_event not in set(es["event"]):
        print(f"  AVISO: {chile_event} no aparece con lang == 'es'")

    usable = es[~es["es_chile"] & es["label"].notna()]
    print(f"\nUtilizables para entrenar (antes de deduplicar): {len(usable):,}")

    by_event = (usable.groupby(["event", "source"]).size().rename("tweets")
                .reset_index().sort_values("tweets", ascending=False))
    print("\nPor evento:\n", by_event.to_string(index=False))

    by_class = usable["label"].value_counts().rename("tweets")
    print("\nPor clase:\n", by_class.to_string())

    res_dir.mkdir(parents=True, exist_ok=True)
    table = pd.crosstab(usable["event"], usable["label"], margins=True, margins_name="TOTAL")
    table.to_csv(res_dir / "crisisbench_es_eventos_por_clase.csv")
    print(f"\nTabla evento x clase en {res_dir / 'crisisbench_es_eventos_por_clase.csv'}")


if __name__ == "__main__":
    main()