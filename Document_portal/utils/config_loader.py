from pathlib import Path
import yaml

def load_config(config_path: str | None = None):
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config
