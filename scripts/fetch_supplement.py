"""Fetch the one audited supplement; enforce immutable SHA-256 before saving."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="data/raw")
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    records = json.loads((root / "references/sources.json").read_text())
    for record in records:
        if "download_url" not in record:
            continue
        destination = Path(args.output) / record["file"]
        if destination.exists():
            content = destination.read_bytes()
        else:
            with urlopen(record["download_url"], timeout=60) as response:
                content = response.read(20_000_001)
        if len(content) > 20_000_000 or hashlib.sha256(content).hexdigest() != record["sha256"]:
            raise ValueError("Supplement checksum/size mismatch; no file was written")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        print(f"Verified {destination}; upstream license: {record['license']}")


if __name__ == "__main__":
    main()
