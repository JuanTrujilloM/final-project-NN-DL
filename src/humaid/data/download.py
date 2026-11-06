import json
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download


# The source files are either a JSON list or JSON lines.
def read_records(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
    return [data] if isinstance(data, dict) else data


# HumAID with one folder per disaster.
def download_humaid_events(repo, dest):
    snapshot_download(
        repo_id=repo,
        repo_type="dataset",
        local_dir=dest,
        allow_patterns=["*/train.json", "*/dev.json", "*/test.json", "README.md"],
    )


# CrisisBench humanitarian subset (source of Chile 2014).
def download_crisisbench(repo, dest):
    for split in ("train", "dev", "test"):
        hf_hub_download(
            repo_id=repo, repo_type="dataset", filename=f"humanitarian/{split}.json", local_dir=dest
        )
