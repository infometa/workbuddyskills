#!/bin/bash
#SBATCH --job-name=my_job              # Job name
#SBATCH --partition=normal             # Partition (queue) name
# #SBATCH --account=<account>          # Charge account (uncomment if required)
#SBATCH --nodes=1                      # Number of nodes
#SBATCH --ntasks=1                     # Number of tasks (processes)
#SBATCH --cpus-per-task=1              # Number of CPU cores per task
#SBATCH --mem=4G                       # Memory per node
#SBATCH --time=01:00:00                # Time limit (hh:mm:ss)
#SBATCH --output=my_job_%j.out         # Standard output (%j = job ID)
#SBATCH --error=my_job_%j.err          # Standard error

set -euo pipefail

# Environment setup
# module load gcc
# source ~/miniconda3/etc/profile.d/conda.sh
# conda activate myenv

cd "${SLURM_SUBMIT_DIR:-$PWD}"

echo "Job started on $(date)"
echo "Running on node(s): $SLURM_JOB_NODELIST"

# Replace the line below with the actual workload command
# srun ./my_executable

echo "Job finished on $(date)"
