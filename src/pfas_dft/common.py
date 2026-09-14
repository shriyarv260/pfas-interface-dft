import hashlib
import json
from pathlib import Path


def load_json(path):
    with open(path) as stream:
        return json.load(stream)


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path
