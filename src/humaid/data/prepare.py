import json
from pathlib import Path

from humaid.config import load_config
from humaid.data import download, splits


def main():
    cfg = load_config()
    raw = Path(cfg["paths"]["raw"])
    out_dir = Path(cfg["paths"]["processed"])
    res_dir = Path(cfg["paths"]["results"])
    threshold = cfg["dedup"]["near_duplicate_threshold"]

    print("1/4 Descargando datos...")
    download.download_humaid_events(cfg["humaid"]["repo"], raw / "humaid_events")
    if cfg["chile"]["enabled"]:
        download.download_crisisbench(cfg["chile"]["repo"], raw / "crisisbench")

    print("2/4 Construyendo HumAID (limpieza, split por desastre y deduplicación, ~35 s)...")
    df, report = splits.build_humaid(raw / "humaid_events", cfg["humaid"], threshold)
    (out_dir / "humaid_en").mkdir(parents=True, exist_ok=True)
    for old in (out_dir / "humaid_en").glob("*.csv"):
        old.unlink()
    for role, part in df.groupby("role"):
        part.to_csv(out_dir / "humaid_en" / f"{role}.csv", index=False)
    print("   Tweets por conjunto:", df["role"].value_counts().to_dict())
    print("   Eliminados:", json.dumps(report, ensure_ascii=False))
    if low := splits.check_class_coverage(df, cfg["humaid"]["min_per_class"]):
        print("   AVISO, clases por debajo del mínimo:", json.dumps(low, ensure_ascii=False))

    # Class counts per set, with a totals row.
    dist = splits.class_distribution(df)
    dist = dist[[c for c in ("train", "val", "test", "test_intra") if c in dist]]
    if cfg["chile"]["enabled"]:
        print("3/4 Construyendo Chile 2014 (español)...")
        chile, chile_report = splits.load_chile_test(raw / "crisisbench", cfg["chile"]["event"], threshold)
        (out_dir / "chile2014_es").mkdir(parents=True, exist_ok=True)
        chile.to_csv(out_dir / "chile2014_es" / "test.csv", index=False)
        print("   Chile 2014:", json.dumps(chile_report, ensure_ascii=False))
        dist["chile_2014"] = splits.class_distribution(chile)["external_chile"]

    # The Colombian set is annotated by hand and not in the repo: built only when some source has data.
    colombia_raw = Path(cfg["colombia"]["raw"])
    if any(colombia_raw.glob("*/*.csv")):
        print("4/4 Construyendo Colombia (español, todas las fuentes)...")
        colombia, colombia_report = splits.load_colombia_test(colombia_raw, threshold)
        (out_dir / cfg["colombia"]["output"]).mkdir(parents=True, exist_ok=True)
        colombia.to_csv(out_dir / cfg["colombia"]["output"] / "test.csv", index=False)
        print("   Colombia:", json.dumps(colombia_report, ensure_ascii=False))
        dist["colombia"] = splits.class_distribution(colombia)["external_colombia"]
    else:
        print(f"4/4 Colombia: no hay CSV en {colombia_raw}/<fuente>/, se omite")
    dist = dist.fillna(0).astype(int)
    dist.loc["TOTAL"] = dist.sum()
    dist.index.name = "categoria"
    dist.columns.name = None

    res_dir.mkdir(parents=True, exist_ok=True)
    dist.to_csv(res_dir / "distribucion_clases.csv")
    splits.event_class_table(df).to_csv(res_dir / "eventos_por_clase.csv")
    print(f"Listo. Datos en {out_dir} y tablas en {res_dir}")


if __name__ == "__main__":
    main()
