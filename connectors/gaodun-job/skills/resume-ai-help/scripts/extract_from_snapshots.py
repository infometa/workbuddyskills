#!/usr/bin/env python3
"""从 bot 平台 prompt 快照（prompt-<id>.json）重新生成 prompt 原文与索引。

用法：
    python scripts/extract_from_snapshots.py <snapshots_dir>

snapshots_dir 为存放 prompt-<id>.json 的目录（拉取方法见 references/pipeline.md §4/§5）。
对每个快照：
  - result.systemRole 原文逐字写入 references/prompts/prompt-<id>.txt
  - 元数据（名称/promptKey/模型/updatedAt/envs/temperature）汇总进 references/prompts-index.json

注意：prompt 原文与索引的**正式存放地是服务端资源包**（
由 resume_prompt_get 下发）。本脚本的输出只是中转产物——跑完后把 references/prompts/*.txt
与 prompts-index.json 复制进 dyson 仓库，不要提交回本 skill 包（体积门禁）。
幂等：重复运行产出相同文件。复制进 dyson 后跑 `python scripts/aihelp.py selfcheck --prompts-dir <物化目录>` 验证。
"""
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = SKILL_DIR / "references" / "prompts"
INDEX_PATH = SKILL_DIR / "references" / "prompts-index.json"

VAR_RE = re.compile(r"\{\{\$(\w+)\}\}")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    src = Path(sys.argv[1])
    snapshots = sorted(src.glob("prompt-*.json"), key=lambda p: int(p.stem.split("-")[1]))
    if not snapshots:
        print(f"FAIL: {src} 下没有 prompt-*.json")
        return 1

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    index = {}
    errors = []
    for snap in snapshots:
        prompt_id = snap.stem.split("-")[1]
        try:
            data = json.loads(snap.read_text(encoding="utf-8"))
            assert data.get("status") == 0, f"status={data.get('status')}"
            result = data["result"]
            system_role = result["systemRole"]
            assert system_role.strip(), "systemRole 为空"
        except Exception as e:  # noqa: BLE001
            errors.append(f"{snap.name}: {e}")
            continue

        (PROMPTS_DIR / f"prompt-{prompt_id}.txt").write_text(system_role, encoding="utf-8")
        envs = result.get("envs") or []
        index[prompt_id] = {
            "name": result.get("name"),
            "promptKey": result.get("promptKey"),
            "model": (result.get("modelType") or {}).get("modelName"),
            "temperature": result.get("temperature"),
            "updatedAt": result.get("updatedAt"),
            "envs": [e["envKey"] for e in envs if e.get("envType") == 1],
            "varsInSystemRole": sorted(set(VAR_RE.findall(system_role))),
        }

    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"extracted {len(index)} prompts -> {PROMPTS_DIR}")
    print(f"index -> {INDEX_PATH}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
