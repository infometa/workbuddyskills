#!/usr/bin/env python3
"""Scaffold a ziniao-cli Skill + Runtime kit."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import textwrap
from pathlib import Path

SKILL_MAKER = Path(__file__).resolve().parent.parent
CLIENT_TEMPLATE = SKILL_MAKER / "scripts" / "runtime_client.template.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold ziniao Skill + Runtime kit")
    parser.add_argument("--name", required=True, help="Scenario slug, e.g. inventory-sync")
    parser.add_argument("--output", type=Path, required=True, help="Output root directory")
    parser.add_argument("--title", default="", help="Human title for SKILL.md")
    args = parser.parse_args()

    slug = args.name.strip().lower().replace("_", "-")
    if not slug.startswith("ziniao-"):
        slug = f"ziniao-{slug}"
    title = args.title or slug.replace("ziniao-", "").replace("-", " ").title()
    root = args.output / f"{slug}-kit"
    short = slug.replace("-", "_")

    write(
        root / "README.md",
        f"""
        # {title} Kit

        ```powershell
        cd {root.name}
        .\\run.ps1
        ```

        ```bash
        cd {root.name}
        ./run.sh
        ```

        规范见 `SKILL.md`。首次默认 **explore**；填好 `validated-reads.json` 后改 `phase=execute`。

        在 Kit 根目录执行 `./run.ps1` 或 `./run.sh`。浏览器场景在 `data/input.json` 的 `items[].storeId` 填写。
        """,
    )

    write(
        root / "run.ps1",
        f"""
        $ErrorActionPreference = "Stop"
        $Root = $PSScriptRoot
        Set-Location $Root
        $Out = Join-Path $Root "output"
        $InputJson = Join-Path $Root "data/input.json"
        $Runtime = Join-Path $Root "runtime/run_{short}.py"
        New-Item -ItemType Directory -Force -Path $Out | Out-Null

        ziniao-cli doctor

        Write-Host "==> read input"
        python "$Root/scripts/read_input.py" "$InputJson" --out "$Out/manifest.json"
        if ($LASTEXITCODE -ne 0) {{ throw "read_input failed" }}

        Write-Host "==> preflight"
        python "$Root/scripts/preflight_validate.py" "$Out/manifest.json" "$Root"
        if ($LASTEXITCODE -ne 0) {{ throw "preflight failed" }}

        Write-Host "==> run"
        python "$Runtime" --manifest "$Out/manifest.json"
        if ($LASTEXITCODE -ne 0) {{ throw "runtime failed" }}
        """,
    )

    run_sh = root / "run.sh"
    write(
        run_sh,
        f"""
        #!/usr/bin/env bash
        set -euo pipefail
        ROOT="$(cd "$(dirname "$0")" && pwd)"
        cd "$ROOT"
        OUT="$ROOT/output"
        mkdir -p "$OUT"
        PY="$(command -v python3 || true)"
        if [ -z "$PY" ]; then PY="$(command -v python || true)"; fi
        if [ -z "$PY" ]; then echo "python3/python not found" >&2; exit 1; fi

        ziniao-cli doctor
        echo "==> read input"
        "$PY" "$ROOT/scripts/read_input.py" "$ROOT/data/input.json" --out "$OUT/manifest.json"
        echo "==> preflight"
        "$PY" "$ROOT/scripts/preflight_validate.py" "$OUT/manifest.json" "$ROOT"
        echo "==> run"
        "$PY" "$ROOT/runtime/run_{short}.py" --manifest "$OUT/manifest.json"
        """,
    )
    os.chmod(run_sh, os.stat(run_sh).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    write(
        root / "SKILL.md",
        f"""
        ---
        name: {slug}
        version: 1.0.0
        description: "{title}。当用户需要用结构化输入重复执行该紫鸟浏览器/API 流程时使用。"
        metadata:
          requires:
            bins: ["ziniao-cli"]
        ---

        # {title}

        **CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../ziniao-shared/SKILL.md`](../ziniao-shared/SKILL.md)**

        ## 前置

        `ziniao-cli doctor` 通过。写入/保存/提交需用户确认。浏览器场景需要 `items[].storeId`（或 `--store-id`）。

        ## 流程

        1. `read_input.py` → manifest
        2. `preflight_validate.py`（失败即停）
        3. `python runtime/run_{short}.py --manifest ...`

        ## 阶段

        - **explore**（默认）：只采集 raw/截图，Agent 写 `validated-reads.json`
        - **execute**：解析 + `final_gate`；须 `meta.readyForExecute=true`

        ## 完成边界

        TODO: 定义业务完成信号（非 CLI exit 0）。

        ## Agent 仅处理

        规范未覆盖的新字段、异常分支、授权变更。
        """,
    )

    write(
        root / "references/input-contract.md",
        """
        # 输入契约

        | 键 | 类型 | 必填 | 说明 |
        |----|------|------|------|
        | tasks[].runMode | string | 是 | 仅填写 / 保存草稿 / 完整提交 / 只读 |
        | tasks[].allowSave | bool | 是 | |
        | tasks[].allowSubmit | bool | 是 | |
        | items[] | array | 视场景 | 业务主键与参数 |

        TODO: 补充本场景字段。
        """,
    )

    write(
        root / "references/submission-policy.md",
        """
        # 提交策略

        | runMode | allowSave | allowSubmit | 最终动作 |
        |---------|-----------|-------------|----------|
        | 只读 | false | false | 采集完成即停 |
        | 仅填写 | false | false | 停在完成态 |
        | 保存草稿 | true | false | 保存一次并验证 |
        | 完整提交 | true | true | 需用户明确授权 |
        """,
    )

    write(
        root / "references/failure-retrospective.md",
        """
        # 失败复盘

        | 区段 | 现象 | 根因 | 修复 |
        |------|------|------|------|
        | TODO | | | |
        | 等待 / 读取 | 区段耗时长、CLI 不多 | 固定 sleep 或 exec 长 loop | poll_until + 导航阶梯 |
        | 跨区段推断 | 主读法稳定空结果 | 异步组件 | validated-reads 声明 fallback_from_* |

        已知 selector 写进 `SKILL.md` 步骤；Path B 同步更新 `references/io-patterns.md`。等待策略见 skill-maker §原子 I/O 能力。
        """,
    )

    write(
        root / "references/io-patterns.md",
        """
        # I/O 模式（Kit 层组合，不含域判定）

        原子能力来自 `runtime/ziniao_client.py` 的 `poll_until`。本文件只记录**本 Kit** 如何组合。

        ## ready_predicate 登记

        | 区段 | read 来源 | ready 条件 | timeout_ms |
        |------|-----------|------------|------------|
        | TODO | | | |

        ## 导航阶梯

        | 级 | 动作 | 触发条件 |
        |----|------|----------|
        | 1 | visit 直达 | 默认 |
        | 2 | 中间页 + 交互 | 级 1 poll 超时 |
        | 3 | fallback / 人工 | 级 2 仍失败 |

        ## fallback 声明

        | 目标区段 | fallback 源区段 | validated-reads 键 |
        |----------|-----------------|-------------------|
        | TODO | | method=fallback_from_* |
        """,
    )

    write(
        root / "references/validated-reads.template.json",
        json.dumps(
            {
                "meta": {
                    "readyForExecute": False,
                    "notes": "Agent fills after explore runs",
                },
                "fields": {},
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    write(
        root / "scripts/read_input.py",
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path


        def main() -> int:
            parser = argparse.ArgumentParser()
            parser.add_argument("input_path", type=Path)
            parser.add_argument("--out", type=Path, required=True)
            args = parser.parse_args()

            raw = json.loads(args.input_path.read_text(encoding="utf-8-sig"))
            manifest = {
                "sourceFormat": "json",
                "tasks": raw.get("tasks", []),
                "items": raw.get("items", []),
                "assets": raw.get("assets", []),
                "options": raw.get("options", {}),
            }
            manifest.setdefault("options", {})
            manifest["options"].setdefault("phase", "explore")
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"ok": True, "out": str(args.out)}, ensure_ascii=False))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )

    write(
        root / "scripts/preflight_validate.py",
        """
        #!/usr/bin/env python3
        from __future__ import annotations

        import json
        import sys
        from pathlib import Path


        def validate(manifest: dict, kit_root: Path) -> list[dict]:
            errors = []
            tasks = manifest.get("tasks")
            if not isinstance(tasks, list) or not tasks:
                errors.append({"code": "TASKS_REQUIRED", "message": "tasks 必须是非空数组"})
            for task in tasks or []:
                mode = task.get("runMode", "")
                if mode == "仅填写" and (task.get("allowSave") or task.get("allowSubmit")):
                    errors.append({"code": "MODE_CONFLICT", "message": "仅填写 不允许 save/submit"})
            phase = (manifest.get("options") or {}).get("phase", "explore")
            if phase == "execute":
                vr = kit_root / "output" / "validated-reads.json"
                if not vr.is_file():
                    errors.append({"code": "VALIDATED_READS", "message": "execute 需要 output/validated-reads.json"})
                else:
                    data = json.loads(vr.read_text(encoding="utf-8-sig"))
                    if not (data.get("meta") or {}).get("readyForExecute"):
                        errors.append({"code": "NOT_READY", "message": "meta.readyForExecute 须为 true"})
            return errors


        def main() -> int:
            manifest_path = Path(sys.argv[1])
            kit_root = manifest_path.parent.parent
            if len(sys.argv) > 2:
                kit_root = Path(sys.argv[2])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            errors = validate(manifest, kit_root.resolve())
            result = {"ok": not errors, "errorCount": len(errors), "errors": errors, "warnings": []}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["ok"] else 1


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )

    write(
        root / f"runtime/run_{short}.py",
        f"""
        #!/usr/bin/env python3
        from __future__ import annotations

        from {short}_core import main


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )

    write(
        root / f"runtime/{short}_core.py",
        f"""
        #!/usr/bin/env python3
        from __future__ import annotations

        import argparse
        import json
        import sys
        import time
        from pathlib import Path
        from typing import Any

        from ziniao_client import ZiniaoClient, poll_until


        def final_gate(report: dict, validated: dict | None) -> list[str]:
            \"\"\"Return empty list if business success; non-empty = failed.\"\"\"
            phase = (report.get("meta") or {{}}).get("phase", "explore")
            if phase == "explore":
                return []
            if not validated or not (validated.get("meta") or {{}}).get("readyForExecute"):
                return ["validated-reads.meta.readyForExecute must be true"]
            # TODO: domain checks
            return []


        def validate_manifest(manifest: dict) -> None:
            if not manifest.get("tasks"):
                raise ValueError("manifest.tasks 不能为空")


        def phase(name: str, fn, log: dict) -> Any:
            started = time.perf_counter()
            result = fn()
            log["phaseDurationsMs"][name] = round((time.perf_counter() - started) * 1000)
            log["phasesCompleted"].append(name)
            return result


        def main(argv: list[str] | None = None) -> int:
            parser = argparse.ArgumentParser()
            parser.add_argument("--manifest", type=Path, required=True)
            parser.add_argument("--store-id", default="")
            args = parser.parse_args(argv)

            manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
            validate_manifest(manifest)
            options = manifest.get("options") or {{}}
            phase_name = options.get("phase", "explore")
            store_id = args.store_id or (manifest.get("items") or [{{}}])[0].get("storeId", "")
            client = ZiniaoClient(store_id) if store_id else None
            started = time.perf_counter()
            log: dict = {{
                "phase": phase_name,
                "phaseDurationsMs": {{}},
                "phasesCompleted": [],
                "cli": client.stats if client else {{}},
            }}

            if not store_id:
                log["warning"] = "missing items[].storeId or --store-id; page commands will fail"

            # TODO: phase("gate", ...), phase("section_a", ...), build report
            # 异步区块：visit/load 后 poll_until(read, ready)，禁止固定 sleep
            # poll 超时默认不 raise，须再判 ready 或 raise_on_timeout=True；条件写在 references/io-patterns.md
            report = {{"meta": {{"phase": phase_name}}}}

            validated = None
            vr = args.manifest.parent / "validated-reads.json"
            if vr.is_file():
                validated = json.loads(vr.read_text(encoding="utf-8-sig"))
            gate_errors = final_gate(report, validated)
            if gate_errors:
                raise RuntimeError("; ".join(gate_errors))

            log["elapsedMs"] = round((time.perf_counter() - started) * 1000)
            out = args.manifest.parent / "run-log.json"
            out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
            sys.stdout.buffer.write(
                json.dumps({{"ok": True, "log": log}}, ensure_ascii=False, indent=2).encode("utf-8") + b"\\n"
            )
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )

    shutil.copy2(CLIENT_TEMPLATE, root / "runtime" / "ziniao_client.py")
    (root / "runtime" / "ziniao_client.py").write_text(
        (root / "runtime" / "ziniao_client.py")
        .read_text(encoding="utf-8")
        .replace("copy into workflow-runtime or Kit domain code", "generated by ziniao-skill-maker scaffold"),
        encoding="utf-8",
    )

    for sub in ("data", "output"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (root / "data" / "input.json").write_text(
        json.dumps(
            {
                "tasks": [{"enabled": True, "taskId": "demo", "runMode": "只读", "allowSave": False, "allowSubmit": False}],
                "items": [{"storeId": ""}],
                "options": {"phase": "explore"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "root": str(root), "slug": slug}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
