import json
from pathlib import Path

import pandas as pd

from humaid.config import load_config
from humaid.data import download
from humaid.data.download import read_records
from humaid.data.preprocess import clean_tweet
from humaid.data.splits import dedup_key, near_duplicate_mask
from humaid.labels import CRISISBENCH_TO_HUMAID

ROLES = ("train", "val", "test", "test_intra")
COLUMNS = ["tweet_id", "event", "role", "lang", "fuente", "label", "text_clean"]


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


# HumAID in English plus its translation, one row per text.
def load_humaid_pair(processed, translated, roles):
    parts, report = [], {}
    for role in roles:
        en = read_split(processed / "humaid_en" / f"{role}.csv")
        es = read_split(translated / f"{role}.csv")
        check_translation(en, es, role)
        parts.append(en.assign(lang="en", fuente="humaid_en")[COLUMNS])
        parts.append(es.assign(lang="es", fuente="humaid_trad", text_clean=es["text_es"])[COLUMNS])
        report[role] = {"humaid_en": len(en), "humaid_trad": len(es)}
    return pd.concat(parts, ignore_index=True), report


# Native Spanish tweets from the chosen CrisisBench events; always train.
def load_native_spanish(crisisbench_root, events):
    if chile := [e for e in events if "chile" in e.lower()]:
        raise ValueError(f"Chile es evaluación externa y no puede entrar a train: {chile}")
    rows = [r for split in ("train", "dev", "test")
            for r in read_records(Path(crisisbench_root) / "humanitarian" / f"{split}.json")
            if r.get("lang") == "es" and r["event"] in events]
    df = pd.DataFrame(rows).rename(columns={"id": "tweet_id"})
    if missing := sorted(set(events) - set(df.get("event", []))):
        raise ValueError(f"Eventos sin tweets en español en CrisisBench: {missing}")

    report = {"total": len(df)}
    df["label"] = df["class_label"].map(CRISISBENCH_TO_HUMAID)
    unmapped = df["label"].isna()
    report["sin_equivalente_descartados"] = df.loc[unmapped, "class_label"].value_counts().to_dict()
    df = df[~unmapped].copy()
    df["text_clean"] = df["text"].map(clean_tweet)
    df = df.assign(tweet_id=df["tweet_id"].astype(str), role="train", lang="es", fuente="crisisbench_es")
    return df[COLUMNS], report


# Removes native texts that are empty, repeated, or (near-)duplicates of a Spanish evaluation text.
def dedup_native(native, reference_texts, threshold):
    report = {}
    out = native.assign(key=native["text_clean"].map(dedup_key))
    keep = out["key"].str.len() > 0
    report["vacios"] = int((~keep).sum())
    out = out[keep]

    before = len(out)
    out = out.drop_duplicates(subset="key", keep="first")
    report["duplicados_internos"] = before - len(out)

    ref_keys = reference_texts.map(dedup_key)
    exact = out["key"].isin(set(ref_keys))
    report["exactos_en_evaluacion"] = int(exact.sum())
    out = out[~exact]

    # Repeat, since removing texts changes the TF-IDF weights.
    removed = 0
    while True:
        near = near_duplicate_mask(out["key"], ref_keys, threshold)
        if not near.any():
            break
        removed += int(near.sum())
        out = out[~near]
    report["casi_duplicados_en_evaluacion"] = removed
    return out.drop(columns="key").reset_index(drop=True), report


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
    humaid = corpus[corpus["fuente"].isin(["humaid_en", "humaid_trad"])]
    if (split_roles := humaid.groupby("tweet_id")["role"].nunique()).gt(1).any():
        problems.append(f"{int(split_roles.gt(1).sum())} traducciones en otro conjunto que su original")
    if corpus.loc[corpus["fuente"] == "crisisbench_es", "role"].ne("train").any():
        problems.append("hay español nativo fuera de train")
    if corpus["event"].str.contains("chile", case=False).any():
        problems.append("hay tweets de eventos de Chile en el corpus")
    if problems:
        raise ValueError("Fuga detectada: " + "; ".join(problems))


def main():
    cfg = load_config()
    bcfg = cfg["bilingual"]
    processed = Path(cfg["paths"]["processed"])
    res_dir = Path(cfg["paths"]["results"])
    translated = Path(bcfg["translated"])
    out_dir = Path(bcfg["output"])
    crisisbench = Path(cfg["paths"]["raw"]) / "crisisbench"
    threshold = cfg["dedup"]["near_duplicate_threshold"]

    if not (processed / "humaid_en" / "train.csv").exists():
        raise SystemExit("Falta data/processed/humaid_en: corre primero scripts/prepare_data.py")
    if not (translated / "train.csv").exists():
        raise SystemExit(f"Falta la traducción en {translated}: descomprime ahí humaid_es.zip de Kaggle")
    roles = [r for r in ROLES if (processed / "humaid_en" / f"{r}.csv").exists()]

    print("1/4 HumAID en inglés y traducido...")
    corpus, report_pair = load_humaid_pair(processed, translated, roles)

    print("2/4 Español nativo de CrisisBench...")
    if not (crisisbench / "humanitarian" / "train.json").exists():
        download.download_crisisbench(cfg["chile"]["repo"], crisisbench)
    native, report_native = load_native_spanish(crisisbench, bcfg["crisisbench_es"]["events"])

    print("3/4 Deduplicación del español nativo contra val, test, test_intra y Chile 2014...")
    chile_path = processed / "chile2014_es" / "test.csv"
    chile = read_split(chile_path) if chile_path.exists() else pd.DataFrame(columns=COLUMNS)
    spanish_eval = pd.concat([corpus.loc[(corpus["lang"] == "es") & (corpus["role"] != "train"), "text_clean"],
                              chile["text_clean"]], ignore_index=True)
    native, report_native["deduplicacion"] = dedup_native(native, spanish_eval, threshold)
    report_native["final"] = len(native)

    corpus = pd.concat([corpus, native], ignore_index=True)
    corpus, collisions = drop_translated_collisions(corpus)
    check_no_leakage(corpus, chile)

    print("4/4 Guardando...")
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
        "crisisbench_es": {"eventos": bcfg["crisisbench_es"]["events"], **report_native},
        "traducciones_de_train_iguales_a_evaluacion": collisions,
        "tweets_por_conjunto_y_fuente": corpus.groupby(["role", "fuente"]).size().unstack(fill_value=0).to_dict(),
    }
    (res_dir / "bilingue_reporte.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=int))
    print("   Español nativo:", json.dumps(report["crisisbench_es"], ensure_ascii=False, default=int))
    print("   Traducciones de train quitadas por coincidir con evaluación:", collisions)
    print(corpus.groupby(["role", "fuente"]).size().unstack(fill_value=0).to_string())
    print(f"Listo. Corpus en {out_dir} y tablas en {res_dir}")


if __name__ == "__main__":
    main()