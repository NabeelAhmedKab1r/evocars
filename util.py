# util.py

import json
import os
from config import SAVE_DIR


def ensure_dirs():
    os.makedirs(SAVE_DIR, exist_ok=True)


def save_best_genome(track_name, genome):
    ensure_dirs()
    path = os.path.join(SAVE_DIR, f"{track_name}_best.json")
    with open(path, "w") as f:
        json.dump([float(w) for w in genome], f)
    print(f"Saved best genome for '{track_name}' → {path}")


def load_best_genome(track_name):
    path = os.path.join(SAVE_DIR, f"{track_name}_best.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    # Support both old tuple format and new flat float format
    if data and isinstance(data[0], list):
        print(f"Old genome format found for '{track_name}' — ignoring, starting fresh.")
        return None
    genome = [float(w) for w in data]
    print(f"Loaded best genome for '{track_name}' ← {path}")
    return genome
