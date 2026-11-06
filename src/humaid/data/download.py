import json
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download


def read_records(path):
    """Lee un .json que puede ser una lista JSON o JSON por líneas."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    return [data] if isinstance(data, dict) else data


def download_humaid_events(repo, dest):
    """HumAID por evento: una carpeta por desastre con train/dev/test."""
    snapshot_download(
        repo_id=repo,
        repo_type="dataset",
        local_dir=dest,
        allow_patterns=["*/train.json", "*/dev.json", "*/test.json", "README.md"],
    )


def download_crisisbench(repo, dest):
    """Subconjunto humanitario de CrisisBench (de aquí sale Chile 2014 en español)."""
    for split in ("train", "dev", "test"):
        hf_hub_download(
            repo_id=repo, repo_type="dataset", filename=f"humanitarian/{split}.json", local_dir=dest
        )
