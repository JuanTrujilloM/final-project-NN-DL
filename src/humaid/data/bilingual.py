import json
from pathlib import Path

import pandas as pd

from humaid.config import load_config
from humaid.data.splits import dedup_key

ROLES = ("train", "val", "test", "test_intra")
COLUMNS = ["tweet_id", "event", "role", "lang", "fuente", "label", "text_clean"]


def read_split(path):
    return pd.read_csv(path, dtype={"tweet_id": str})


# HumAID in English plus its translation, one row per text.
def load_humaid_pair(processed, roles):
    parts, report = [], {}
    for role in roles:
        en = read_split(processed / "humaid_en" / f"{role}.csv")
        es = read_split(processed / "humaid_es" / f"{role}.csv")
        if set(en["tweet_id"]) != set(es["tweet_id"]):
            raise ValueError(f"humaid_es/{role}.csv no corresponde a humaid_en: corre scripts/prepare_humaid_es.py")
        parts.append(en.assign(lang="en", fuente="humaid_en")[COLUMNS])
        parts.append(es.assign(lang="es", fuente="humaid_trad")[COLUMNS])
        report[role] = {"humaid_en": len(en), "humaid_trad": len(es)}
    return pd.concat(parts, ignore_index=True), report


# Two different English tweets can translate to the same Spanish text: drop it from train.
def drop_translated_collisions(corpus):
    trad = corpus["fuente"] == "humaid_trad"
    keys = corpus["text_clean"].map(dedup_key)
    eval_keys = set(keys[trad & (corpus["role"] != "train")])
    collide = trad & (corpus["role"] == "train") & keys.isin(eval_keys)
    return corpus[~collide].reset_index(drop=True), int(collide.sum())


# Hard checks: the script stops if any of them fails.
def check_no_leakage(corpus, chile):
    problems = []
    train = corpus[corpus["role"] == "train"]
    evaluation = corpus[corpus["role"] != "train"]
    if shared := set(train["tweet_id"]) & set(evaluation["tweet_id"]):
        problems.append(f"{len(shared)} tweet_id en train y en evaluación")
    if len(chile) and (shared := set(train["tweet_id"]) & set(chile["tweet_id"].astype(str))):
        problems.append(f"{len(shared)} tweet_id de Chile 2014 en train")
    if (split_roles := corpus.groupby("tweet_id")["role"].nunique()).gt(1).any():
        problems.append(f"{int(split_roles.gt(1).sum())} traducciones en otro conjunto que su original")
    if corpus["event"].str.contains("chile", case=False).any():
        problems.append("hay tweets de eventos de Chile en el corpus")
    if problems:
        raise ValueError("Fuga detectada: " + "; ".join(problems))


def main():
    cfg = load_config()
    processed = Path(cfg["paths"]["processed"])
    res_dir = Path(cfg["paths"]["results"])
    out_dir = Path(cfg["bilingual"]["output"])

    for name, script in (("humaid_en", "prepare_data.py"), ("humaid_es", "prepare_humaid_es.py")):
        if not (processed / name / "train.csv").exists():
            raise SystemExit(f"Falta data/processed/{name}: corre primero scripts/{script}")
    roles = [r for r in ROLES if (processed / "humaid_en" / f"{r}.csv").exists()]

    print("1/2 Uniendo HumAID en inglés y en español...")
    corpus, report_pair = load_humaid_pair(processed, roles)
    corpus, collisions = drop_translated_collisions(corpus)
    chile_path = processed / "chile2014_es" / "test.csv"
    chile = read_split(chile_path) if chile_path.exists() else pd.DataFrame(columns=COLUMNS)
    check_no_leakage(corpus, chile)

    print("2/2 Guardando...")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.csv"):
        old.unlink()
    for role in roles:
        corpus[corpus["role"] == role].to_csv(out_dir / f"{role}.csv", index=False)

    dist = corpus.pivot_table(index="label", columns=["role", "fuente"], values="text_clean",
                              aggfunc="count", fill_value=0)
    dist = dist.reindex(columns=[c for role in roles for c in dist.columns if c[0] == role])
    dist.loc["TOTAL"] = dist.sum()
    res_dir.mkdir(parents=True, exist_ok=True)
    dist.to_csv(res_dir / "bilingue_distribucion.csv")

    report = {
        "humaid_por_conjunto": report_pair,
        "traducciones_de_train_iguales_a_evaluacion": collisions,
        "tweets_por_conjunto_y_fuente": corpus.groupby(["role", "fuente"]).size().unstack(fill_value=0).to_dict(),
    }
    (res_dir / "bilingue_reporte.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=int))
    print("   Traducciones de train quitadas por coincidir con evaluación:", collisions)
    print(corpus.groupby(["role", "fuente"]).size().unstack(fill_value=0).to_string())
    print(f"Listo. Corpus en {out_dir} y tablas en {res_dir}")


if __name__ == "__main__":
    main()
