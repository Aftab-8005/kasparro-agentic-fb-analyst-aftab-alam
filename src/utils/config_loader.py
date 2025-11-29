from pathlib import Path
import yaml
import random
import numpy as np


def load_config() -> dict:
    config_path = Path(__file__).resolve().parents[2] / "config" / "config.yaml"
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    seed = cfg.get("random_seed", 42)
    random.seed(seed)
    np.random.seed(seed)

    return cfg
