"""Electronic energy profiles. No automatic free-energy or rate interpretation."""

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from .common import save_json

METADATA = ("label", "energy_kind", "ensemble", "composition", "charge", "method_id", "status")


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["run_id"]].append(row)
    if not groups:
        raise ValueError("No energy profiles supplied")
    results = []
    for run_id, group in groups.items():
        for field in METADATA:
            if len({str(r[field]) for r in group}) != 1 or not str(group[0][field]).strip():
                raise ValueError(f"{run_id}: inconsistent or missing {field}")
        ordered = sorted(group, key=lambda r: int(r["image"]))
        indices = [int(r["image"]) for r in ordered]
        if indices != list(range(len(ordered))) or len(indices) < 3:
            raise ValueError(f"{run_id}: require >=3 unique contiguous images starting at zero")
        energies = np.array([float(r["energy_ev"]) for r in ordered])
        if not np.isfinite(energies).all():
            raise ValueError("Nonfinite energies")
        peak = int(np.argmax(energies))
        result = dict(run_id=run_id, **{k: ordered[0][k] for k in METADATA})
        result.update(
            reaction_energy_ev=float(energies[-1] - energies[0]),
            sampled_forward_barrier_ev=float(energies.max() - energies[0]),
            sampled_reverse_barrier_ev=float(energies.max() - energies[-1]),
            peak_image=peak,
            interior_peak=0 < peak < len(energies) - 1,
            relative_energies_ev=(energies - energies[0]).tolist(),
            warning="Sampled NEB maximum; transition-state mode verification is separate.",
        )
        results.append(result)
    return results


def analyze_csv(path, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with open(path, newline="") as stream:
        result = summarize(list(csv.DictReader(stream)))
    save_json(output / "profiles.json", result)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    for profile in result:
        values = profile["relative_energies_ev"]
        ax.plot(np.linspace(0, 1, len(values)), values, "o-", label=profile["label"])
    ax.set(xlabel="Normalized image index (not path length)", ylabel="Relative energy (eV)")
    demo = any(p["status"] == "synthetic" for p in result)
    ax.set_title(
        "SYNTHETIC SOFTWARE DEMO — no PFAS predictions" if demo else "Electronic energy profiles"
    )
    ax.legend()
    fig.savefig(output / "landscape.png", dpi=180)
    plt.close(fig)
    return result
