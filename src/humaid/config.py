import yaml


# YAML paths are relative to the repo root.
def load_config(path="configs/protocolo.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
