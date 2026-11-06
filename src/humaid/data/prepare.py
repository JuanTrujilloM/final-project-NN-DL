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

    print("1/3 Descargando datos...")
    download.download_humaid_events(cfg["humaid"]["repo"], raw / "humaid_events")
    if cfg["chile"]["enabled"]:
        download.download_crisisbench(cfg["chile"]["repo"], raw / "crisisbench")

    print("2/3 Construyendo HumAID (limpieza, split por desastre y deduplicación, ~35 s)...")
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
        print("3/3 Construyendo Chile 2014 (español)...")
        chile, chile_report = splits.load_chile_test(raw / "crisisbench", cfg["chile"]["event"], threshold)
        (out_dir / "chile2014_es").mkdir(parents=True, exist_ok=True)
        chile.to_csv(out_dir / "chile2014_es" / "test.csv", index=False)
        print("   Chile 2014:", json.dumps(chile_report, ensure_ascii=False))
        dist["chile_2014"] = splits.class_distribution(chile)["external_chile"]
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
