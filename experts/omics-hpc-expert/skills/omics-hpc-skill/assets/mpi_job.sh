#!/bin/bash
#SBATCH --job-name=mpi_job             # Job name
#SBATCH --partition=compute            # Partition name
# #SBATCH --account=<account>          # Charge account (uncomment if required)
#SBATCH --nodes=2                      # Number of nodes
#SBATCH --ntasks-per-node=8            # MPI ranks per node
#SBATCH --cpus-per-task=1              # CPUs per MPI rank
#SBATCH --mem=8G                       # Memory per node
#SBATCH --time=02:00:00                # Time limit
#SBATCH --output=mpi_job_%j.out        # Standard output
#SBATCH --error=mpi_job_%j.err         # Standard error

set -euo pipefail

# Environment setup
# module load openmpi

cd "${SLURM_SUBMIT_DIR:-$PWD}"

echo "MPI job started on $(date)"
echo "Allocated nodes: $SLURM_JOB_NODELIST"

# Replace the line below with the actual workload command
# srun ./my_mpi_program

echo "MPI job finished on $(date)"
