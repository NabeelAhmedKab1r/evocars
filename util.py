# util.py

import json
import os
from config import SAVE_DIR


def ensure_dirs():
    if not os.path.isdir(SAVE_DIR):
        os.makedirs(SAVE_DIR, exist_ok=True)


def save_best_genome(track_name, genome):
    ensure_dirs()
    path = os.path.join(SAVE_DIR, f"{track_name}_best.json")
    serial = [[float(s), float(t)] for (s, t) in genome]
    with open(path, "w") as f:
        json.dump(serial, f)
    print(f"Saved best genome for '{track_name}' to {path}")


def load_best_genome(track_name):
    path = os.path.join(SAVE_DIR, f"{track_name}_best.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    genome = [(float(s), float(t)) for (s, t) in data]
    print(f"Loaded best genome for '{track_name}' from {path}")
    return genome
