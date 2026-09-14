"""Analytical double-well integration test. This potential describes no real species."""

import csv

import numpy as np
from ase import Atoms
from ase.calculators.calculator import Calculator, all_changes
from ase.io import write
from ase.mep import NEB
from ase.optimize import FIRE

from .analysis import analyze_csv
from .common import new_directory, save_json


class DoubleWell(Calculator):
    implemented_properties = ["energy", "forces"]

    def calculate(self, atoms=None, properties=("energy",), system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        x, y, z = self.atoms.positions[0]
        q = y - 0.4 * (1 - x * x)
        self.results = {
            "energy": float((1 - x * x) ** 2 + 2 * q * q + z * z),
            "forces": np.array([[4 * x * (1 - x * x) - 3.2 * x * q, -4 * q, -2 * z]]),
        }


def run_demo(output):
    output = new_directory(output)
    images = [
        Atoms("H", positions=[[x, 0, 0]], calculator=DoubleWell()) for x in np.linspace(-1, 1, 7)
    ]
    neb = NEB(images, climb=False, method="improvedtangent")
    opt = FIRE(neb, logfile=str(output / "neb.log"))
    preconverged = opt.run(fmax=0.03, steps=500)
    neb.climb = True
    converged = FIRE(neb, logfile=str(output / "climb.log")).run(fmax=0.005, steps=500)
    if not preconverged or not converged:
        raise RuntimeError("Analytical demo NEB did not converge")
    write(output / "final_images.traj", images)
    rows = [
        {
            "run_id": "analytical_double_well",
            "label": "Analytical double well (synthetic)",
            "image": i,
            "energy_ev": a.get_potential_energy(),
            "status": "synthetic",
            "energy_kind": "analytical_potential",
            "ensemble": "toy",
            "composition": "dummy_coordinate",
            "charge": "not_applicable",
            "method_id": "double-well-v1",
        }
        for i, a in enumerate(images)
    ]
    with open(output / "energies.csv", "w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = analyze_csv(output / "energies.csv", output)
    save_json(
        output / "demo_status.json",
        {
            "status": "synthetic",
            "neb_converged": bool(converged),
            "analytic_barrier_ev": 1.0,
            "computed_sampled_barrier_ev": report[0]["sampled_forward_barrier_ev"],
            "is_pfas_validation": False,
        },
    )
    return report
