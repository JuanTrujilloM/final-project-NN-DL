from pathlib import Path

import pandas as pd

from humaid.config import load_config

ROLES = ("train", "val", "test", "test_intra")


def read_split(path):
    return pd.read_csv(path, dtype={"tweet_id": str})


# Fails if the translation does not match its original one to one.
def check_translation(en, es, role):
    problems = []
    if es["text_es"].fillna("").str.strip().eq("").any():
        problems.append("hay traducciones vacías")
    if es["tweet_id"].duplicated().any():
        problems.append("hay tweet_id repetidos")
    missing, extra = set(en["tweet_id"]) - set(es["tweet_id"]), set(es["tweet_id"]) - set(en["tweet_id"])
    if missing or extra:
        problems.append(f"{len(missing)} originales sin traducir y {len(extra)} traducciones sin original")
    pair = en[["tweet_id", "event", "label", "role"]].merge(
        es[["tweet_id", "event", "label", "role"]], on="tweet_id", suffixes=("_en", "_es"))
    for col in ("event", "label", "role"):
        if (diff := int((pair[f"{col}_en"] != pair[f"{col}_es"]).sum())):
            problems.append(f"{diff} tweets con distinto {col}")
    if (en["role"] != role).any():
        problems.append(f"el archivo {role}.csv trae filas de otro conjunto")
    if problems:
        raise ValueError(f"La traducción de {role} no coincide con el original: " + "; ".join(problems))


# Same columns as humaid_en with the Spanish text in text_clean; text_raw keeps the English original.
def to_processed(en, es):
    out = en.drop(columns="text_clean").merge(es[["tweet_id", "text_es", "traductor"]], on="tweet_id",
                                              how="left", validate="one_to_one")
    return out.rename(columns={"text_es": "text_clean"})[list(en.columns) + ["traductor"]]


def main():
    cfg = load_config()
    processed = Path(cfg["paths"]["processed"])
    raw = Path(cfg["translation"]["raw"])
    out_dir = processed / "humaid_es"

    if not (processed / "humaid_en" / "train.csv").exists():
        raise SystemExit("Falta data/processed/humaid_en: corre primero scripts/prepare_data.py")
    if not (raw / "train.csv").exists():
        raise SystemExit(f"Falta la traducción en {raw}: descomprime ahí humaid_es.zip de Kaggle")
    roles = [r for r in ROLES if (processed / "humaid_en" / f"{r}.csv").exists()]

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.csv"):
        old.unlink()
    for role in roles:
        en = read_split(processed / "humaid_en" / f"{role}.csv")
        es = read_split(raw / f"{role}.csv")
        check_translation(en, es, role)
        to_processed(en, es).to_csv(out_dir / f"{role}.csv", index=False)
        print(f"   {role}: {len(es):,} tweets")
    print(f"Listo. HumAID en español en {out_dir}")


if __name__ == "__main__":
    main()
