#!/bin/bash
#SBATCH --job-name=pfas-neb
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%j.out
set -euo pipefail
# Submit from repository root after site-specific account/partition/module setup.
# Configure your study JSON command as appropriate, e.g. "srun -n 16 pw.x".
# The Python NEB driver is serial over images; each QE call may use all allocated ranks.
: "${PFAS_CONFIG:?Set PFAS_CONFIG to the reviewed study JSON}"
: "${PFAS_IMAGES:?Set PFAS_IMAGES to the prepared images.traj}"
: "${PFAS_OUTPUT:?Set PFAS_OUTPUT to a new output directory}"
source .venv/bin/activate
export OMP_NUM_THREADS=1
pfas neb --input "$PFAS_IMAGES" --config "$PFAS_CONFIG" --output "$PFAS_OUTPUT"
