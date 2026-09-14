"""ASE-driven, fixed-cell Quantum ESPRESSO relaxation and CI-NEB."""

import csv
import hashlib
import json
import shlex
import shutil
from pathlib import Path

import ase
import numpy as np
from ase.calculators.espresso import Espresso, EspressoProfile
from ase.io import read, write
from ase.mep import NEB
from ase.optimize import FIRE
from ase.vibrations import Vibrations

from .common import new_directory, save_json, sha256
from .structures import frozen_indices, validate_endpoints


def validate_config(config, atoms, require_files=True):
    if config.get("ensemble") != "fixed_charge":
        raise ValueError("This runner implements fixed-charge DFT only")
    data = config["input_data"]
    system = data["system"]
    if data["control"].get("calculation") != "scf" or not data["control"].get("tprnfor"):
        raise ValueError("ASE relaxation requires calculation=scf and tprnfor=true")
    if data["control"].get("restart_mode", "from_scratch") != "from_scratch":
        raise ValueError("Restart mode is not supported; create a new run from saved structures")
    if system.get("ibrav", 0) != 0:
        raise ValueError("Use ibrav=0 with explicit fixed cell")
    for key in ("ecutwfc", "ecutrho"):
        if not np.isfinite(system[key]) or system[key] <= 0:
            raise ValueError(f"Positive finite {key} required (Ry)")
    if system["ecutrho"] < system["ecutwfc"]:
        raise ValueError("ecutrho must be at least ecutwfc")
    kpts = config["kpts"]
    if len(kpts) != 3 or any(type(k) is not int or k < 1 for k in kpts):
        raise ValueError("kpts must contain three positive integers")
    charge = system.get("tot_charge", 0)
    if not np.isfinite(charge):
        raise ValueError("Nonfinite total cell charge")
    if charge != 0 and not config.get("charge_treatment", "").strip():
        raise ValueError("Charged slabs require an explicit, reviewed charge_treatment description")
    if not np.isfinite(config["fmax_ev_per_angstrom"]) or config["fmax_ev_per_angstrom"] <= 0:
        raise ValueError("Invalid force threshold")
    if type(config["max_steps"]) is not int or config["max_steps"] <= 0:
        raise ValueError("max_steps must be a positive integer")
    pseudo_dir = Path(config["pseudo_dir"]).expanduser().resolve()
    mapping = config["pseudopotentials"]
    for symbol in set(atoms.get_chemical_symbols()):
        if symbol not in mapping or Path(mapping[symbol]).name != mapping[symbol]:
            raise ValueError(f"Provide a pseudopotential basename for {symbol}")
        if require_files and not (pseudo_dir / mapping[symbol]).is_file():
            raise FileNotFoundError(f"Missing pseudopotential: {pseudo_dir / mapping[symbol]}")
    if require_files:
        command = shlex.split(config["command"])
        if not command or shutil.which(command[0]) is None:
            raise FileNotFoundError("QE command or MPI launcher is not installed/on PATH")
    frozen_indices(atoms)
    return pseudo_dir


def apply_magmoms(atoms, config):
    moments = config.get("initial_magnetic_moments")
    if moments is not None:
        if len(moments) != len(atoms) or not np.isfinite(moments).all():
            raise ValueError("Initial magnetic moments must match atom count")
        atoms.set_initial_magnetic_moments(moments)
    if config["input_data"]["system"].get("nspin", 1) == 2 and not np.any(
        atoms.get_initial_magnetic_moments()
    ):
        raise ValueError("Spin-polarized runs require nonzero initial moments in atoms or config")


def calculator(config, directory):
    return Espresso(
        profile=EspressoProfile(
            command=config["command"],
            pseudo_dir=str(Path(config["pseudo_dir"]).expanduser().resolve()),
        ),
        directory=str(directory),
        pseudopotentials=config["pseudopotentials"],
        input_data=config["input_data"],
        kpts=tuple(config["kpts"]),
    )


def provenance(config, inputs, atoms):
    pseudo_dir = Path(config["pseudo_dir"]).expanduser().resolve()
    hashes = {
        s: sha256(pseudo_dir / config["pseudopotentials"][s])
        for s in set(atoms.get_chemical_symbols())
    }
    # Include only scientific parameters in the compatibility fingerprint.
    method = {
        "input_data": config["input_data"],
        "kpts": config["kpts"],
        "pseudopotential_hashes": hashes,
        "charge_treatment": config.get("charge_treatment"),
        "ase_version": ase.__version__,
    }
    method_id = hashlib.sha256(json.dumps(method, sort_keys=True).encode()).hexdigest()
    return {
        "config": config,
        "input_hashes": {str(p): sha256(p) for p in inputs},
        "pseudopotential_hashes": hashes,
        "method_id": method_id,
        "ase_version": ase.__version__,
        "status": "running",
        "ensemble": "fixed_charge",
        "ts_verified": False,
        "note": "User must archive QE version/build, convergence studies and scientific review.",
    }


def write_qe_template(atoms_path, config, output):
    atoms = read(atoms_path)
    validate_config(config, atoms, require_files=False)
    apply_magmoms(atoms, config)
    output = new_directory(output)
    write(
        output / "pw.in",
        atoms,
        format="espresso-in",
        input_data=config["input_data"],
        pseudopotentials=config["pseudopotentials"],
        kpts=tuple(config["kpts"]),
    )
    save_json(
        output / "status.json",
        {
            "status": "input_template_only",
            "config": config,
            "structure_sha256": sha256(atoms_path),
            "pseudopotentials_verified": False,
        },
    )


def relax(atoms_path, config, output):
    atoms = read(atoms_path)
    validate_config(config, atoms)
    apply_magmoms(atoms, config)
    output = new_directory(output)
    manifest = provenance(config, [atoms_path], atoms)
    save_json(output / "run.json", manifest)
    atoms.calc = calculator(config, output / "qe")
    try:
        opt = FIRE(atoms, trajectory=str(output / "relax.traj"), logfile=str(output / "relax.log"))
        converged = bool(opt.run(fmax=config["fmax_ev_per_angstrom"], steps=config["max_steps"]))
        write(output / "final.traj", atoms)
        manifest.update(
            status="converged" if converged else "unconverged",
            converged=converged,
            energy_ev=atoms.get_potential_energy(),
            max_force_ev_per_angstrom=float(np.linalg.norm(atoms.get_forces(), axis=1).max()),
        )
        if not converged:
            raise RuntimeError(
                "Endpoint relaxation did not converge; inspect run.json and trajectory"
            )
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        save_json(output / "run.json", manifest)
    return manifest


def run_neb(images_path, config, output):
    images = read(images_path, index=":")
    if len(images) < 3:
        raise ValueError("At least three images required")
    for atoms in images:
        validate_config(config, atoms)
        apply_magmoms(atoms, config)
        validate_endpoints(images[0], atoms)
    output = new_directory(output)
    manifest = provenance(config, [images_path], images[0])
    save_json(output / "run.json", manifest)
    try:
        for i, atoms in enumerate(images):
            atoms.calc = calculator(config, output / f"image_{i:02d}")
        for endpoint in (images[0], images[-1]):
            if np.linalg.norm(endpoint.get_forces(), axis=1).max() > config["fmax_ev_per_angstrom"]:
                raise ValueError("Endpoints are not force-converged under this exact calculator")
        neb = NEB(images, method="improvedtangent", climb=False)
        FIRE(neb, logfile=str(output / "preclimb.log")).run(fmax=0.1, steps=config["max_steps"])
        neb.climb = True
        opt = FIRE(neb, logfile=str(output / "neb.log"), trajectory=str(output / "neb.traj"))
        converged = bool(opt.run(fmax=config["fmax_ev_per_angstrom"], steps=config["max_steps"]))
        energies = [a.get_potential_energy() for a in images]
        write(output / "final_images.traj", images)
        manifest.update(
            converged=converged,
            status="converged" if converged else "unconverged",
            n_images=len(images),
            final_images_sha256=sha256(output / "final_images.traj"),
        )
        if not converged:
            raise RuntimeError(
                "NEB did not converge; results must not be used as validated barriers"
            )
        rows = [
            {
                "run_id": output.name,
                "label": config["label"],
                "image": i,
                "energy_ev": energy,
                "status": "computed",
                "energy_kind": "electronic_energy",
                "ensemble": "fixed_charge",
                "composition": images[0].get_chemical_formula(),
                "charge": config["input_data"]["system"].get("tot_charge", 0),
                "method_id": manifest["method_id"],
            }
            for i, energy in enumerate(energies)
        ]
        with open(output / "energies.csv", "w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    except Exception as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        save_json(output / "run.json", manifest)
    return manifest


def vibrate(atoms_path, config, output, indices):
    atoms = read(atoms_path)
    validate_config(config, atoms)
    apply_magmoms(atoms, config)
    if (
        not indices
        or len(indices) != len(set(indices))
        or min(indices) < 0
        or max(indices) >= len(atoms)
    ):
        raise ValueError("Supply unique valid vibration indices")
    if set(indices) & set(frozen_indices(atoms)):
        raise ValueError("Vibration indices include frozen atoms")
    output = new_directory(output)
    atoms.calc = calculator(config, output / "qe")
    manifest = provenance(config, [atoms_path], atoms)
    save_json(output / "run.json", manifest)
    vib = Vibrations(atoms, indices=indices, name=str(output / "vib"), delta=0.01)
    vib.run()
    freqs = vib.get_frequencies()
    save_json(
        output / "frequencies.json",
        {
            "indices": indices,
            "frequencies_cm_inverse": [
                {"real": float(x.real), "imaginary": float(x.imag)} for x in freqs
            ],
            "status": "requires_mode_inspection",
            "note": "Partial Hessian if indices exclude mobile atoms. Inspect unstable mode and downhill connectivity; no automatic TS certificate.",
        },
    )
    manifest.update(status="completed_requires_mode_inspection")
    save_json(output / "run.json", manifest)
