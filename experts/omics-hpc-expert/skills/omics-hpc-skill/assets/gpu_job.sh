#!/bin/bash
#SBATCH --job-name=gpu_job             # Job name
#SBATCH --partition=gpu                # GPU partition name
# #SBATCH --account=<account>          # Charge account (uncomment if required)
#SBATCH --nodes=1                      # Number of nodes
#SBATCH --ntasks=1                     # Number of tasks
#SBATCH --cpus-per-task=4              # CPUs per task
#SBATCH --mem=16G                      # Memory per node
#SBATCH --time=04:00:00                # Time limit
#SBATCH --gres=gpu:1                   # Number of GPUs
#SBATCH --output=gpu_job_%j.out        # Standard output
#SBATCH --error=gpu_job_%j.err         # Standard error

set -euo pipefail

# Environment setup
# module load cuda/12.2
# source ~/miniconda3/etc/profile.d/conda.sh
# conda activate myenv

cd "${SLURM_SUBMIT_DIR:-$PWD}"

echo "GPU job started on $(date)"
echo "Node list: $SLURM_JOB_NODELIST"

# Replace the line below with the actual workload command
# srun python train.py

echo "GPU job finished on $(date)"
