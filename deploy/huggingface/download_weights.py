import os
from pathlib import Path

from huggingface_hub import snapshot_download

# The model repo mirrors models/: etapaX/<model>/model.pt; configs and tokenizers already come from git.
repo = os.environ["HUMAID_WEIGHTS_REPO"]
target = Path("models")
snapshot_download(repo_id=repo, local_dir=target, allow_patterns=["etapa*/*/model.pt"], token=os.environ.get("HF_TOKEN"))
for path in sorted(target.glob("etapa*/*/model.pt")):
    print(f"{path}: {path.stat().st_size / 1e6:.0f} MB")
