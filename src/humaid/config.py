import yaml


def load_config(path="configs/protocolo.yaml"):
    """Lee el protocolo. Las rutas del YAML son relativas a la raíz del repo, desde donde se corren los comandos."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
