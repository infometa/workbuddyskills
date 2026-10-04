#!/usr/bin/env python3
"""Deterministic state machine for whole-resume AI-help orchestration.

The runner does not call an LLM.  It emits exactly one next action and the
fully rendered prompt for that action, then persists progress after the caller
records the decision, answers, or optimized result.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "references" / "field-config.json"
AIHELP_PATH = Path(__file__).with_name("aihelp.py")
HTML_PATH = Path(__file__).with_name("render_resume_html.py")
# prompt 原文、HTML 模板与模块配置默认由调用方经 gaodun-job MCP
# resume_resource_bundle_get 一次物化到本地（旧的三个工具仅整任务兜底），init 时以
# --prompts-dir/--templates-dir/--module-config 传入；runner 只读这些文件，自己不连任何 MCP 端点。


def read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, target)


def blank(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def first_field(finalized: dict, code: str) -> str:
    candidates = []
    for module in finalized.get("modules", []):
        for record in module.get("records", []):
            if record.get("dataFieldCode") == code and not blank(record.get("value")):
                candidates.append(record)
    candidates.sort(key=lambda x: (x.get("dataSort", 1), x.get("fieldIndex", 0)))
    return candidates[0]["value"] if candidates else ""


def build_items(finalized: dict, config: dict) -> list[dict]:
    modules = {m.get("moduleCode"): m for m in finalized.get("modules", [])}
    position = first_field(finalized, "position")
    items = []
    # JSON insertion order is the authoritative whole-resume optimization order.
    for field_code, type_cfg in config["types"].items():
        module = modules.get(type_cfg["moduleCode"])
        if not module or module.get("configHidden") or module.get("moduleStatus") == 0:
            continue
        records = module.get("records", [])
        sorts = sorted(
            {
                int(r.get("dataSort", 1))
                for r in records
                if r.get("dataFieldCode") == field_code
                and r.get("dataFieldStatus", 1) != 0
                and not blank(r.get("value"))
            }
        )
        for data_sort in sorts:
            fields = {
                r["dataFieldCode"]: r.get("value", "")
                for r in sorted(records, key=lambda x: x.get("fieldIndex", 0))
                if int(r.get("dataSort", 1)) == data_sort
            }
            fields["position"] = position
            items.append(
                {
                    "moduleCode": type_cfg["moduleCode"],
                    "dataFieldCode": field_code,
                    "dataSort": data_sort,
                    "label": type_cfg["label"],
                    "promptOneId": type_cfg["promptOneId"],
                    "promptTwoId": type_cfg["promptTwoId"],
                    "fields": fields,
                    "status": "awaiting_follow_up",
                    "qa": None,
                }
            )
    return items


def render_prompt(item: dict, stage: str, prompts_dir: str) -> dict:
    import importlib.util

    spec = importlib.util.spec_from_file_location("resume_aihelp", AIHELP_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    config = module.load_json(module.CONFIG_PATH)
    index, prompts_path = module.load_prompts_dir(prompts_dir)
    output = io.StringIO()
    qa = json.dumps(item.get("qa"), ensure_ascii=False) if item.get("qa") is not None else None
    with contextlib.redirect_stdout(output):
        module.cmd_render(
            config,
            index,
            prompts_path,
            item["dataFieldCode"],
            stage,
            json.dumps(item["fields"], ensure_ascii=False),
            qa,
        )
    return json.loads(output.getvalue())


def load_state(path: str | Path) -> dict:
    state = read_json(path)
    if state.get("version") != 1:
        raise SystemExit("不支持的 runner state 版本")
    return state


def current_item(state: dict) -> dict | None:
    index = state["currentIndex"]
    return state["items"][index] if index < len(state["items"]) else None


def save_state(args, state: dict) -> None:
    write_json(args.state, state)


def renderer_preflight(prompts_dir: str, templates_dir: str, manifest_path: str | None = None) -> dict[str, str]:
    try:
        import jinja2  # noqa: F401
    except ImportError as exc:
        raise SystemExit("初始化失败：缺少 HTML 渲染依赖 jinja2，请先安装项目依赖") from exc
    pd = Path(prompts_dir)
    if not (pd / "prompts-index.json").is_file() or not (pd / "prompts").is_dir():
        raise SystemExit(f"初始化失败：--prompts-dir 需含 prompts-index.json 与 prompts/（gaodun-job MCP 物化产物）: {pd}")
    td = Path(templates_dir)
    if not td.is_dir() or not any(td.glob("personal_resume_onepage_*.html")):
        raise SystemExit(f"初始化失败：--templates-dir 下未找到 HTML 模板（gaodun-job MCP 物化产物）: {td}")
    result = {"jinja2": "ok", "prompts": "ok", "templates": "ok"}
    if manifest_path:
        manifest = Path(manifest_path)
        if not manifest.is_file():
            raise SystemExit(f"初始化失败：资源目录缺少 manifest.json: {manifest}")
        if read_json(manifest).get("schemaVersion") != 1:
            raise SystemExit(f"初始化失败：不支持的资源 manifest schemaVersion: {manifest}")
        result["manifest"] = "ok"
    return result


def cmd_init(args):
    if args.resources_dir:
        resources_dir = Path(args.resources_dir).resolve()
        prompts_dir = str(resources_dir)
        templates_dir = str(resources_dir / "templates" / "converted")
        module_config = str(resources_dir / "resume-module-config.json")
        manifest_path = str(resources_dir / "manifest.json")
    else:
        if not args.prompts_dir or not args.templates_dir or not args.module_config:
            raise SystemExit("初始化失败：优先传 --resources-dir；诊断覆盖时需同时传 --prompts-dir/--templates-dir/--module-config")
        prompts_dir = args.prompts_dir
        templates_dir = args.templates_dir
        module_config = args.module_config
        manifest_path = None
    preflight = renderer_preflight(prompts_dir, templates_dir, manifest_path)
    module_config_path = Path(module_config).resolve()
    if not module_config_path.is_file():
        raise SystemExit(f"初始化失败：--module-config 文件不存在（默认由 resume_resource_bundle_get 一次物化）: {module_config_path}")
    finalized_path = Path(args.finalized).resolve()
    finalized = read_json(finalized_path)
    config = read_json(CONFIG_PATH)
    overrides_path = Path(args.overrides).resolve() if args.overrides else Path(args.state).resolve().with_name("overrides.json")
    state = {
        "version": 1,
        "finalized": str(finalized_path),
        "overrides": str(overrides_path),
        "promptsDir": str(Path(prompts_dir).resolve()),
        "templatesDir": str(Path(templates_dir).resolve()),
        "moduleConfig": str(module_config_path),
        "currentIndex": 0,
        "position": first_field(finalized, "position"),
        "positionAsked": bool(first_field(finalized, "position")),
        "items": build_items(finalized, config),
    }
    write_json(overrides_path, [])
    save_state(args, state)
    print(
        json.dumps(
            {
                "itemCount": len(state["items"]),
                "state": str(Path(args.state).resolve()),
                "preflight": preflight,
                "position": state["position"],
                "positionMissing": not state["positionAsked"],
                "requiredPromptIds": sorted(
                    {pid for item in state["items"] for pid in (item["promptOneId"], item["promptTwoId"])}
                ),
            },
            ensure_ascii=False,
        )
    )


def cmd_set_position(args):
    state = load_state(args.state)
    if state.get("positionAsked"):
        raise SystemExit("意向岗位已确认过，不得重复询问；如需修正请直接改 state 的 position")
    if args.skip and args.position:
        raise SystemExit("--skip 与 --position 互斥")
    if not args.skip and blank(args.position):
        raise SystemExit("请提供 --position '<目标岗位>'；用户表示不填/按通用方向时用 --skip")
    position = "" if args.skip else args.position.strip()
    state["position"] = position
    state["positionAsked"] = True
    for item in state["items"]:
        item.setdefault("fields", {})["position"] = position
    save_state(args, state)
    print(json.dumps({"position": position, "backfilled": len(state["items"])}, ensure_ascii=False))


def cmd_status(args):
    """队列进度概览：供查看用，不改变状态（避免自造 dump_*.py 直读 state）。"""
    state = load_state(args.state)
    print(
        json.dumps(
            {
                "currentIndex": state["currentIndex"],
                "itemCount": len(state["items"]),
                "position": state.get("position"),
                "positionAsked": state.get("positionAsked"),
                "items": [
                    {
                        "dataFieldCode": item["dataFieldCode"],
                        "label": item["label"],
                        "dataSort": item["dataSort"],
                        "status": item["status"],
                    }
                    for item in state["items"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_next(args):
    state = load_state(args.state)
    if not state.get("positionAsked"):
        raise SystemExit(
            "意向岗位未确认：先单独向用户询问一次目标岗位（不得混入字段追问），"
            "然后执行 set-position --position '<目标岗位>'；用户明确不填/按通用方向时执行 set-position --skip"
        )
    item = current_item(state)
    if item is None:
        print(json.dumps({"action": "render_html", "completed": len(state["items"]), "overrides": state["overrides"]}, ensure_ascii=False))
        return
    public_item = {k: v for k, v in item.items() if k not in {"status", "qa"}}
    status = item["status"]
    if status == "awaiting_follow_up":
        prompt = render_prompt(item, "ask", state["promptsDir"])
        result = {
            "action": "ask",
            "requiresUserInput": True,
            "stopAfterDisplay": True,
            "allowedTransitions": ["answers --qa", "skip-questions --confirmed-by-user", "no-questions（追问响应零问题时）"],
            "item": public_item,
            **prompt,
        }
    elif status == "awaiting_optimize":
        prompt = render_prompt(item, "opt", state["promptsDir"])
        result = {"action": "optimize", "item": public_item, **prompt}
    else:
        raise SystemExit(f"非法当前状态: {status}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_answers(args):
    state = load_state(args.state)
    item = current_item(state)
    if not item or item["status"] != "awaiting_follow_up":
        raise SystemExit("answers 仅允许用于当前追问项目")
    qa = read_json(args.qa_file) if args.qa_file else json.loads(args.qa)
    if not isinstance(qa, list):
        raise SystemExit("--qa 必须是 JSON 数组")
    if not any(isinstance(row, dict) and not blank(row.get("answer")) for row in qa):
        raise SystemExit("answers 至少需要一个用户答案；全部跳过请使用 skip-questions --confirmed-by-user")
    item["qa"] = qa
    item["status"] = "awaiting_optimize"
    save_state(args, state)


def cmd_skip_questions(args):
    state = load_state(args.state)
    item = current_item(state)
    if not item or item["status"] != "awaiting_follow_up":
        raise SystemExit("skip-questions 仅允许用于当前追问项目")
    if not args.confirmed_by_user:
        raise SystemExit("只有用户明确跳过追问后才允许推进")
    item["qa"] = None
    item["status"] = "awaiting_optimize"
    save_state(args, state)


def cmd_no_questions(args):
    """追问 prompt 返回零问题（parse-ask questions=[]）的系统路径：无需用户确认，直接进优化。"""
    state = load_state(args.state)
    item = current_item(state)
    if not item or item["status"] != "awaiting_follow_up":
        raise SystemExit("no-questions 仅允许用于当前追问项目")
    item["qa"] = None
    item["status"] = "awaiting_optimize"
    save_state(args, state)


def cmd_complete(args):
    state = load_state(args.state)
    item = current_item(state)
    if not item or item["status"] != "awaiting_optimize":
        raise SystemExit("complete 仅允许在当前项目进入优化阶段后执行")
    response_path = Path(args.response_file)
    if not response_path.is_file():
        raise SystemExit(f"优化响应文件不存在: {response_path}")
    parsed = subprocess.run(
        [sys.executable, str(AIHELP_PATH), "parse-opt"],
        input=response_path.read_bytes(),
        capture_output=True,
    )
    if parsed.returncode:
        reason = parsed.stdout.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"优化响应未通过 parse-opt 校验: {reason}")
    result = json.loads(parsed.stdout.decode("utf-8"))
    resume = result["resume"].strip()
    if "\\n" in resume or "\\r" in resume:
        raise SystemExit("优化结果含字面量 \\n/\\r；请将 LLM 原始 JSON 直接落盘，禁止经 shell 参数转写")
    overrides = read_json(state["overrides"])
    overrides.append(
        {
            "moduleCode": item["moduleCode"],
            "dataFieldCode": item["dataFieldCode"],
            "dataSort": item["dataSort"],
            "value": resume,
        }
    )
    write_json(state["overrides"], overrides)
    item["status"] = "completed"
    state["currentIndex"] += 1
    save_state(args, state)


def cmd_skip_item(args):
    state = load_state(args.state)
    item = current_item(state)
    if not item:
        raise SystemExit("没有可跳过的当前项目")
    item["status"] = "skipped"
    state["currentIndex"] += 1
    save_state(args, state)


def cmd_render_html(args):
    state = load_state(args.state)
    if current_item(state) is not None:
        raise SystemExit("仍有未处理项目，禁止提前生成 HTML")
    command = [
        sys.executable,
        str(HTML_PATH),
        "render",
        "--finalized",
        state["finalized"],
    ]
    if read_json(state["overrides"]):
        command.extend(["--overrides", state["overrides"]])
        module_config = state.get("moduleConfig")
        if module_config:
            command.extend(["--module-config", module_config])
    template_file = Path(state["templatesDir"]) / f"personal_resume_onepage_{args.template_code}.html"
    command.extend(
        [
            "--template-file",
            str(template_file),
            "--resume-name",
            args.resume_name,
            "--out",
            args.out,
        ]
    )
    result = subprocess.run(command, capture_output=True)
    for stream, target in ((result.stdout, sys.stdout), (result.stderr, sys.stderr)):
        if stream:
            try:
                target.write(stream.decode("utf-8"))
            except UnicodeDecodeError:
                target.write(stream.decode("gbk", errors="replace"))
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="整份简历逐项 Prompt 确定性编排器")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init")
    p.add_argument("--finalized", required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--overrides")
    p.add_argument("--resources-dir", help="materialize_resources.py 生成的统一资源目录（推荐）")
    p.add_argument("--prompts-dir",
                   help="含 prompts-index.json + prompts/ 的目录（默认由 resume_resource_bundle_get 一次物化）")
    p.add_argument("--templates-dir",
                   help="含 personal_resume_onepage_<code>.html 的目录（默认由 resume_resource_bundle_get 一次物化）")
    p.add_argument("--module-config",
                   help="resume-module-config.json 路径（默认由 resume_resource_bundle_get 一次物化）")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("set-position")
    p.add_argument("--state", required=True)
    p.add_argument("--position", help="用户明确给出的目标岗位")
    p.add_argument("--skip", action="store_true", help="用户明确不填/按通用方向")
    p.set_defaults(func=cmd_set_position)

    p = sub.add_parser("next")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("status")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("answers")
    p.add_argument("--state", required=True)
    qa_group = p.add_mutually_exclusive_group(required=True)
    qa_group.add_argument("--qa-file")
    qa_group.add_argument("--qa")
    p.set_defaults(func=cmd_answers)

    p = sub.add_parser("skip-questions")
    p.add_argument("--state", required=True)
    p.add_argument("--confirmed-by-user", action="store_true", required=True)
    p.set_defaults(func=cmd_skip_questions)

    p = sub.add_parser("no-questions")
    p.add_argument("--state", required=True)
    p.set_defaults(func=cmd_no_questions)

    p = sub.add_parser("complete")
    p.add_argument("--state", required=True)
    p.add_argument("--response-file", required=True)
    p.set_defaults(func=cmd_complete)

    p = sub.add_parser("skip-item")
    p.add_argument("--state", required=True)
    p.add_argument("--confirmed-by-user", action="store_true", required=True)
    p.set_defaults(func=cmd_skip_item)

    p = sub.add_parser("render-html")
    p.add_argument("--state", required=True)
    p.add_argument("--resume-name", required=True)
    p.add_argument("--template-code", default="default")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_render_html)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
