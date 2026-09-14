"""Generate reproducible starting conformers; no DFT or literature geometry claim."""

import hashlib
import json
from pathlib import Path

from ase import Atoms
from ase.io import write
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, rdMolDescriptors

ROOT = Path(__file__).resolve().parents[1]
SPECIES = {
    "pfoa_acid": "O=C(O)" + "C(F)(F)" * 6 + "C(F)(F)F",
    "pfoa_anion": "O=C([O-])" + "C(F)(F)" * 6 + "C(F)(F)F",
    "pfos_acid": "OS(=O)(=O)" + "C(F)(F)" * 7 + "C(F)(F)F",
    "pfos_anion": "[O-]S(=O)(=O)" + "C(F)(F)" * 7 + "C(F)(F)F",
}


def main():
    records = []
    output = ROOT / "data/structures"
    output.mkdir(parents=True, exist_ok=True)
    for name, smiles in SPECIES.items():
        mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
        params = AllChem.ETKDGv3()
        params.randomSeed = 202605
        if AllChem.EmbedMolecule(mol, params) != 0:
            raise RuntimeError(f"Embedding failed: {name}")
        status = AllChem.UFFOptimizeMolecule(mol, maxIters=2000)
        if status != 0:
            raise RuntimeError(f"UFF optimization failed: {name}")
        atoms = Atoms(
            [a.GetSymbol() for a in mol.GetAtoms()], positions=mol.GetConformer().GetPositions()
        )
        atoms.info.update(
            status="starting_conformer_not_DFT", formal_charge=Chem.GetFormalCharge(mol)
        )
        target = output / f"{name}.xyz"
        write(target, atoms, format="extxyz")
        # Bond map uses zero-based XYZ order for choosing C-F, headgroup C-C and C-S endpoints.
        records.append(
            {
                "name": name,
                "smiles": smiles,
                "formula": rdMolDescriptors.CalcMolFormula(mol),
                "formal_charge": Chem.GetFormalCharge(mol),
                "rdkit_version": rdBase.rdkitVersion,
                "method": "ETKDGv3 + UFF; seed 202605; not DFT",
                "file": target.name,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "atoms": [{"index": a.GetIdx(), "element": a.GetSymbol()} for a in mol.GetAtoms()],
                "bonds": [
                    [b.GetBeginAtomIdx(), b.GetEndAtomIdx(), str(b.GetBondType())]
                    for b in mol.GetBonds()
                ],
            }
        )
    (output / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
