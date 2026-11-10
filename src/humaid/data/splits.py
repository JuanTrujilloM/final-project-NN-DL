# Event-level split: each disaster goes whole to train, val or test.

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from humaid.data.download import read_records
from humaid.data.preprocess import clean_tweet
from humaid.labels import CRISISBENCH_TO_HUMAID

ROLES = ("train", "val", "test")
EVENT_TYPES = {"wildfire": "fire", "earthquake": "earthquake", "flood": "flood", "hurricane": "hurricane",
               "cyclone": "hurricane"}
# Sets each role is checked against for duplicates.
LEAK_SOURCES = {"train": ["val", "test", "test_intra"], "val": ["test"]}

PLACEHOLDER_RE = re.compile(r"httpurl|@user")
NON_WORD_RE = re.compile(r"[^\w\s]")
SPACE_RE = re.compile(r"\s+")


def event_type(event):
    for key, kind in EVENT_TYPES.items():
        if key in event:
            return kind
    raise ValueError(f"Tipo de desastre desconocido: {event}")


def load_humaid_events(root):
    rows = []
    for event_dir in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        for split in ("train", "dev", "test"):
            path = event_dir / f"{split}.json"
            if not path.exists():
                continue
            for r in read_records(path):
                rows.append(
                    {
                        "event": event_dir.name,
                        "split": split,
                        "tweet_id": r.get("tweet_id"),
                        "text_raw": r["tweet_text"],
                        "label": r["class_label"],
                    }
                )
    df = pd.DataFrame(rows)
    df["text_clean"] = df["text_raw"].map(clean_tweet)
    return df


# Fails if an event is in two sets, is missing, or does not exist in the data.
def validate_assignment(assignment, events):
    seen = {}
    problems = []
    for role in ROLES:
        for event in assignment.get(role, []):
            if event in seen:
                problems.append(f"{event} está en {seen[event]} y en {role}")
            seen[event] = role
    if missing := sorted(set(events) - set(seen)):
        problems.append(f"eventos sin conjunto: {missing}")
    if unknown := sorted(set(seen) - set(events)):
        problems.append(f"eventos que no existen en los datos: {unknown}")
    if problems:
        raise ValueError("Reparto de eventos inválido: " + "; ".join(problems))
    return seen


def assign_roles(df, assignment, intra_event_reference=False):
    role_of = validate_assignment(assignment, df["event"].unique())
    out = df.copy()
    out["role"] = out["event"].map(role_of)
    if intra_event_reference:
        out.loc[(out["role"] == "train") & (out["split"] == "test"), "role"] = "test_intra"
    return out


# Normalized text used to find duplicates.
def dedup_key(text_clean):
    text = PLACEHOLDER_RE.sub(" ", text_clean.lower())
    return SPACE_RE.sub(" ", NON_WORD_RE.sub(" ", text)).strip()


# Flags query texts with TF-IDF cosine similarity >= threshold to any reference text.
def near_duplicate_mask(query, reference, threshold, chunk=500):
    query, reference = list(query), list(reference)
    mask = np.zeros(len(query), dtype=bool)
    if not query or not reference:
        return mask
    vectorizer = TfidfVectorizer(sublinear_tf=True).fit(query + reference)
    q, r = vectorizer.transform(query), vectorizer.transform(reference).T.tocsc()
    for start in range(0, q.shape[0], chunk):
        sims = q[start:start + chunk] @ r
        mask[start:start + chunk] = sims.max(axis=1).toarray().ravel() >= threshold
    return mask


# Removes empty texts, duplicates and train/val texts repeated in evaluation sets.
def remove_leakage(df, threshold=0.75):
    report = {}
    out = df.assign(key=df["text_clean"].map(dedup_key))
    keep = out["key"].str.len() > 0
    report["vacios"] = int((~keep).sum())
    out = out[keep]

    before = len(out)
    out = out.drop_duplicates(subset=["role", "key"], keep="first")
    report["duplicados_en_mismo_conjunto"] = before - len(out)

    for role, sources in LEAK_SOURCES.items():
        target = out["role"] == role
        ref = out.loc[out["role"].isin(sources), "key"]
        exact = target & out["key"].isin(set(ref))
        report[f"{role}_exactos_en_{'/'.join(sources)}"] = int(exact.sum())
        out = out[~exact]

        # Repeat, since removing texts changes the TF-IDF weights.
        removed = 0
        while True:
            target = out["role"] == role
            near = near_duplicate_mask(out.loc[target, "key"], out.loc[out["role"].isin(sources), "key"], threshold)
            if not near.any():
                break
            removed += int(near.sum())
            out = out.drop(index=out.loc[target].index[near])
        report[f"{role}_casi_duplicados_en_{'/'.join(sources)}"] = removed
    return out.drop(columns="key").reset_index(drop=True), report


# Returns the classes that fall below the minimum count in each set.
def check_class_coverage(df, min_per_class):
    counts = df.pivot_table(index="label", columns="role", values="text_clean", aggfunc="count", fill_value=0)
    labels = sorted(df["label"].unique())
    problems = {}
    for role, minimum in min_per_class.items():
        col = counts[role] if role in counts else pd.Series(0, index=counts.index)
        low = {label: int(col.get(label, 0)) for label in labels if col.get(label, 0) < minimum}
        if low:
            problems[role] = low
    return problems


def build_humaid(root, humaid_cfg, threshold):
    df = assign_roles(load_humaid_events(root), humaid_cfg["events"], humaid_cfg.get("intra_event_reference", False))
    return remove_leakage(df, threshold)


# Chile 2014 in Spanish, used whole as an external test.
def load_chile_test(crisisbench_root, event, threshold=0.75):
    rows = []
    for split in ("train", "dev", "test"):
        for r in read_records(Path(crisisbench_root) / "humanitarian" / f"{split}.json"):
            if r["event"] == event:
                rows.append(r)
    df = pd.DataFrame(rows).rename(columns={"id": "tweet_id"})
    report = {"total_evento": len(df)}
    df["label"] = df["class_label"].map(CRISISBENCH_TO_HUMAID)
    unmapped = df["label"].isna()
    report["sin_equivalente_descartados"] = int(unmapped.sum())
    report["etiquetas_descartadas"] = df.loc[unmapped, "class_label"].value_counts().to_dict()
    df = df[~unmapped].copy()
    df["text_raw"] = df["text"]
    df["text_clean"] = df["text_raw"].map(clean_tweet)
    df["role"] = "external_chile"
    df, leak = remove_leakage(df, threshold)
    report["duplicados_en_mismo_conjunto"] = leak["duplicados_en_mismo_conjunto"]
    report["final"] = len(df)
    cols = ["event", "role", "tweet_id", "text_raw", "text_clean", "label", "lang"]
    return df[[c for c in cols if c in df]], report


def class_distribution(df):
    return df.pivot_table(index="label", columns="role", values="text_clean", aggfunc="count", fill_value=0)


def event_class_table(df):
    table = df.pivot_table(index="event", columns="label", values="text_raw", aggfunc="count", fill_value=0)
    table.insert(0, "tipo", [event_type(e) for e in table.index])
    table["total"] = table.drop(columns="tipo").sum(axis=1)
    return table
