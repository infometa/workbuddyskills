#!/bin/bash
#SBATCH --job-name=array_job           # Job name
#SBATCH --partition=normal             # Partition name
# #SBATCH --account=<account>          # Charge account (uncomment if required)
#SBATCH --nodes=1                      # Number of nodes per task
#SBATCH --ntasks=1                     # Number of tasks per array element
#SBATCH --cpus-per-task=1              # CPUs per task
#SBATCH --mem=2G                       # Memory per task
#SBATCH --time=00:30:00                # Time limit
#SBATCH --array=0-9                    # Array index range (adjust as needed)
#SBATCH --output=array_%A_%a.out       # Standard output (%A=array job ID, %a=index)
#SBATCH --error=array_%A_%a.err        # Standard error

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:-$PWD}"

echo "Array task ${SLURM_ARRAY_TASK_ID} started on $(date)"

# Example: process one input item per array index
# INPUT_FILE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" input_list.txt)
# srun python process.py --input "$INPUT_FILE"

echo "Array task ${SLURM_ARRAY_TASK_ID} finished on $(date)"
