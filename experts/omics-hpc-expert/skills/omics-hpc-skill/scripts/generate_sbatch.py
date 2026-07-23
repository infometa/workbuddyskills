#!/usr/bin/env python3
"""Generate a SLURM sbatch script from structured arguments.

Supports CPU, GPU, MPI, and array job patterns as well as account,
dependency, conda, and module configuration.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a reusable SLURM sbatch script.")

    # Required
    p.add_argument("--output", required=True, help="Path to the generated script")

    # Core SBATCH directives
    p.add_argument("--job-name", default="my_job", help="SLURM job name")
    p.add_argument("--partition", default="normal", help="Partition / queue name")
    p.add_argument("--account", default=None, help="Charge account (-A)")
    p.add_argument("--nodes", type=int, default=1, help="Number of nodes")
    p.add_argument("--ntasks", type=int, default=1, help="Total number of tasks")
    p.add_argument(
        "--ntasks-per-node", type=int, default=None,
        help="Tasks per node (overrides --ntasks when set)",
    )
    p.add_argument("--cpus-per-task", type=int, default=1, help="CPUs per task")
    p.add_argument("--mem", default="4G", help="Memory per node, e.g. 4G")
    p.add_argument("--time", default="01:00:00", help="Walltime limit")
    p.add_argument("--gpus", type=int, default=0, help="GPU count (--gres=gpu:N)")
    p.add_argument(
        "--dependency", default=None,
        help="Dependency spec, e.g. afterok:12345",
    )
    p.add_argument(
        "--array", default=None,
        help="Array index range, e.g. 0-9 or 1-100%%10",
    )
    p.add_argument(
        "--stdout", default=None,
        help="Stdout path pattern, default <job_name>_%%j.out",
    )
    p.add_argument(
        "--stderr", default=None,
        help="Stderr path pattern, default <job_name>_%%j.err",
    )

    # Environment setup
    p.add_argument(
        "--module", action="append", default=[],
        help="Module to load (may be repeated)",
    )
    p.add_argument("--conda-env", default=None, help="Conda environment name")
    p.add_argument(
        "--conda-init", default=None,
        help="Path to conda init script (default: ~/miniconda3/etc/profile.d/conda.sh)",
    )

    # Workload
    p.add_argument(
        "--command", default=None,
        help="Main workload command (single line)",
    )
    p.add_argument(
        "--command-file", default=None,
        help="Read workload commands from this file (multi-line support)",
    )

    return p


def render_script(args: argparse.Namespace) -> str:
    # --- Output file patterns ---
    if args.array:
        stdout = args.stdout or f"{args.job_name}_%A_%a.out"
        stderr = args.stderr or f"{args.job_name}_%A_%a.err"
    else:
        stdout = args.stdout or f"{args.job_name}_%j.out"
        stderr = args.stderr or f"{args.job_name}_%j.err"

    # --- #SBATCH directives ---
    # IMPORTANT: All #SBATCH directives MUST come immediately after #!/bin/bash
    # and BEFORE any executable commands (including `set`). Slurm stops parsing
    # #SBATCH lines as soon as it encounters the first non-comment executable line.
    lines: list[str] = [
        "#!/bin/bash",
        f"#SBATCH --job-name={args.job_name}",
        f"#SBATCH --partition={args.partition}",
    ]

    if args.account:
        lines.append(f"#SBATCH --account={args.account}")
    else:
        lines.append("# #SBATCH --account=<account>  # uncomment if required")

    lines.append(f"#SBATCH --nodes={args.nodes}")

    if args.ntasks_per_node is not None:
        lines.append(f"#SBATCH --ntasks-per-node={args.ntasks_per_node}")
    else:
        lines.append(f"#SBATCH --ntasks={args.ntasks}")

    lines.extend([
        f"#SBATCH --cpus-per-task={args.cpus_per_task}",
        f"#SBATCH --mem={args.mem}",
        f"#SBATCH --time={args.time}",
        f"#SBATCH --output={stdout}",
        f"#SBATCH --error={stderr}",
    ])

    if args.gpus > 0:
        lines.append(f"#SBATCH --gres=gpu:{args.gpus}")

    if args.dependency:
        lines.append(f"#SBATCH --dependency={args.dependency}")

    if args.array:
        lines.append(f"#SBATCH --array={args.array}")

    # --- Shell options (MUST come after all #SBATCH directives) ---
    lines.extend(["", "set -euo pipefail"])

    # --- Environment setup ---
    lines.extend(["", "# Environment setup"])

    if args.module:
        for mod in args.module:
            lines.append(f"module load {mod}")
    else:
        lines.append("# module load <module_name>")

    conda_init = args.conda_init or "~/miniconda3/etc/profile.d/conda.sh"
    if args.conda_env:
        lines.extend([
            f"source {conda_init}",
            f"conda activate {args.conda_env}",
        ])
    else:
        lines.extend([
            f"# source {conda_init}",
            "# conda activate <env_name>",
        ])

    # --- Working directory and info ---
    lines.extend([
        "",
        'cd "${SLURM_SUBMIT_DIR:-$PWD}"',
        "",
        'echo "Job started on $(date)"',
        'echo "Running on node(s): $SLURM_JOB_NODELIST"',
        "",
    ])

    # --- Workload ---
    if args.command_file:
        command_text = Path(args.command_file).read_text(encoding="utf-8").rstrip("\n")
        lines.append(command_text)
    elif args.command:
        lines.append(args.command)
    else:
        lines.append("echo 'Replace this with the real workload command'")

    lines.extend([
        "",
        'echo "Job finished on $(date)"',
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_script(args), encoding="utf-8")
    output_path.chmod(0o755)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
