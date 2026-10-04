#!/usr/bin/env python3
"""Materialize validated MCP resume resources into one local directory."""
from __future__ import annotations

import argparse, hashlib, importlib.util, json, os, shutil, sys, uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
RENDERER = Path(__file__).resolve().parent / "render_resume_html.py"

def fail(message): raise SystemExit(message)
def read_json(path):
    try: return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc: fail(f"无法读取 MCP JSON 响应 {path}: {exc}")
def atomic_text(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="") as stream: stream.write(value)
    os.replace(temp, path)
def atomic_json(path, value): atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")
def digest(value): return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()
def runtime(path):
    root = Path(path).resolve()
    for child in ("raw", "prompts", "templates/source", "templates/converted"): (root / child).mkdir(parents=True, exist_ok=True)
    if not (root / "manifest.json").exists(): atomic_json(root / "manifest.json", {"schemaVersion": 1, "resources": {"prompts": {}, "templates": {}}})
    return root
def manifest(root):
    data = read_json(root / "manifest.json")
    if data.get("schemaVersion") != 1: fail(f"不支持的 manifest schemaVersion: {data.get('schemaVersion')}")
    data.setdefault("resources", {}).setdefault("prompts", {}); data["resources"].setdefault("templates", {})
    return data
def save_manifest(root, data):
    data["generatedAt"] = datetime.now(timezone.utc).isoformat(); atomic_json(root / "manifest.json", data)
def ensure_success(value):
    current = value
    for _ in range(6):
        if not isinstance(current, dict): return
        if current.get("isError") is True: fail("MCP 返回 isError=true，拒绝物化")
        if "error" in current and "jsonrpc" in current: fail(f"MCP JSON-RPC 返回错误: {current['error']}")
        if "jsonrpc" in current and isinstance(current.get("result"), dict): current = current["result"]
        else: return
def unwrap(value):
    current = value
    for _ in range(8):
        if not isinstance(current, dict): break
        keys = set(current)
        if "structuredContent" in current: current = current["structuredContent"]
        elif "jsonrpc" in current and "result" in current: current = current["result"]
        elif "result" in current and keys <= {"result", "status", "message", "requestId"}: current = current["result"]
        elif "data" in current and keys <= {"data", "status", "message", "requestId"}: current = current["data"]
        else: break
    return current
def copy_raw(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if Path(source).resolve() != target.resolve(): shutil.copyfile(source, target)
def convert(body, filename):
    spec = importlib.util.spec_from_file_location("resume_html_renderer", RENDERER); module = importlib.util.module_from_spec(spec)
    assert spec.loader; spec.loader.exec_module(module); return module.freemarker_to_jinja(body, filename)
def parse_ids(value):
    ids = [v.strip() for v in (value or "").split(",") if v.strip()]
    if any(not v.isdigit() for v in ids): fail(f"--prompt-ids 必须是逗号分隔的数字 ID: {value}")
    return list(dict.fromkeys(ids))

def validate_bundle(response, mode, requested):
    ensure_success(response); bundle = unwrap(response)
    if not isinstance(bundle, dict): fail("资源包 structuredContent 必须是对象")
    required = {"schemaVersion", "promptIndex", "prompts", "moduleConfig", "templates"}
    if required - set(bundle): fail("资源包缺少固定字段: " + ", ".join(sorted(required - set(bundle))))
    if bundle["schemaVersion"] != 1: fail(f"不支持的资源包 schemaVersion: {bundle['schemaVersion']}")
    if any(not isinstance(bundle[k], dict) for k in ("promptIndex", "prompts", "templates")): fail("promptIndex、prompts、templates 必须是对象")
    ids = list(bundle["prompts"])
    if set(bundle["promptIndex"]) != set(ids): fail("promptIndex 与 prompts 的 ID 集合不一致")
    if requested and set(ids) != set(requested): fail(f"Prompt ID 不匹配：请求 {requested}，响应 {ids}")
    if any(not isinstance(i, str) or not i.isdigit() for i in ids): fail("Prompt ID 必须是数字字符串")
    if any(not isinstance(v, str) or not v.strip() for v in bundle["prompts"].values()): fail("资源包包含空 Prompt 正文")
    if mode == "single":
        if not requested: fail("single 模式必须传 --prompt-ids")
        if bundle["moduleConfig"] is not None or bundle["templates"]: fail("single 模式不接受模块配置或模板")
    else:
        config = bundle["moduleConfig"]
        if not isinstance(config, dict) or not {"moduleConfig", "visibleModuleMap"} <= set(config): fail(f"{mode} 模式缺少有效 moduleConfig")
        if set(bundle["templates"]) != {"default"}: fail(f"{mode} 模式必须且只能包含 default 模板")
        if not isinstance(bundle["templates"]["default"], str) or not bundle["templates"]["default"].strip(): fail("default 模板正文为空")
        if mode == "full" and not ids: fail("full 模式必须包含 Prompt")
        if mode == "layout" and ids: fail("layout 模式不接受 Prompt")
    return bundle

def build_bundle(root, source, bundle):
    runtime(root); copy_raw(source, root / "raw/bundle-response.json")
    index = json.dumps(bundle["promptIndex"], ensure_ascii=False, indent=2) + "\n"; atomic_text(root / "prompts-index.json", index)
    resources = {"promptIndex": {"path": "prompts-index.json", "sha256": digest(index)}, "prompts": {}, "templates": {}}
    for pid, body in bundle["prompts"].items():
        atomic_text(root / f"prompts/prompt-{pid}.txt", body); resources["prompts"][pid] = {"path": f"prompts/prompt-{pid}.txt", "sha256": digest(body)}
    if bundle["moduleConfig"] is not None:
        body = json.dumps(bundle["moduleConfig"], ensure_ascii=False, indent=2) + "\n"; atomic_text(root / "resume-module-config.json", body)
        resources["moduleConfig"] = {"path": "resume-module-config.json", "sha256": digest(body)}
    for theme, body in bundle["templates"].items():
        name = f"personal_resume_onepage_{theme}.html"; rendered = convert(body, name)
        atomic_text(root / f"templates/source/{name}", body); atomic_text(root / f"templates/converted/{name}", rendered)
        resources["templates"][theme] = {"source": f"templates/source/{name}", "sourceSha256": digest(body), "converted": f"templates/converted/{name}", "convertedSha256": digest(rendered)}
    save_manifest(root, {"schemaVersion": 1, "resources": resources})

def verify(root, ids, require_layout):
    errors = []; data = manifest(root)
    if not (root / "prompts-index.json").is_file(): errors.append("缺少 prompts-index.json")
    for pid in ids:
        if not (root / f"prompts/prompt-{pid}.txt").is_file(): errors.append(f"缺少 prompts/prompt-{pid}.txt")
    if require_layout:
        if not (root / "resume-module-config.json").is_file(): errors.append("缺少 resume-module-config.json")
        if not (root / "templates/converted/personal_resume_onepage_default.html").is_file(): errors.append("缺少 converted default HTML 模板")
    entries = list(data["resources"].get("prompts", {}).values())
    entries += [v for v in data["resources"].get("templates", {}).values()]
    entries += [data["resources"][k] for k in ("promptIndex", "moduleConfig") if k in data["resources"]]
    for entry in entries:
        for path_key, hash_key in (("path", "sha256"), ("source", "sourceSha256"), ("converted", "convertedSha256")):
            if path_key in entry:
                target = root / entry[path_key]
                if not target.is_file(): errors.append(f"manifest 指向不存在文件: {entry[path_key]}")
                elif digest(target.read_bytes()) != entry.get(hash_key): errors.append(f"manifest hash 不一致: {entry[path_key]}")
    if errors: fail("资源校验失败：\n- " + "\n- ".join(errors))

def cmd_bundle(args):
    target, source, ids = Path(args.out_dir).resolve(), Path(args.input).resolve(), parse_ids(args.prompt_ids)
    bundle = validate_bundle(read_json(source), args.mode, ids)
    staging = target.with_name(target.name + ".staging-" + uuid.uuid4().hex); backup = target.with_name(target.name + ".backup-" + uuid.uuid4().hex)
    try:
        build_bundle(staging, source, bundle); verify(staging, list(bundle["prompts"]), args.mode in ("full", "layout")); existed = target.exists()
        if existed: os.replace(target, backup)
        try: os.replace(staging, target)
        except BaseException:
            if existed and backup.exists(): os.replace(backup, target)
            raise
        if backup.exists(): shutil.rmtree(backup)
    finally:
        if staging.exists(): shutil.rmtree(staging)
    print(json.dumps({"ok": True, "mode": args.mode, "outDir": str(target), "promptCount": len(bundle["prompts"])}, ensure_ascii=False))

# Old commands are retained for whole-task fallback only.
def cmd_init(args): print(json.dumps({"ok": True, "outDir": str(runtime(args.out_dir))}, ensure_ascii=False))
def cmd_index(args):
    root = runtime(args.out_dir); response = read_json(args.input); ensure_success(response); value = unwrap(response)
    index = value.get("prompts") if isinstance(value, dict) and isinstance(value.get("prompts"), dict) else value
    if not isinstance(index, dict): fail("无法识别 Prompt 索引响应")
    copy_raw(args.input, root / "raw/prompts-index.json"); body = json.dumps(index, ensure_ascii=False, indent=2) + "\n"; atomic_text(root / "prompts-index.json", body)
    data = manifest(root); data["resources"]["promptIndex"] = {"path": "prompts-index.json", "sha256": digest(body)}; save_manifest(root, data)
def cmd_prompt(args):
    root = runtime(args.out_dir); response = read_json(args.input); ensure_success(response); value = unwrap(response)
    if not isinstance(value, dict): fail("无法识别 Prompt 响应")
    actual = value.get("promptId", value.get("id")); body = next((value.get(k) for k in ("prompt", "systemRole", "content", "text") if isinstance(value.get(k), str)), None)
    if actual is not None and int(actual) != args.prompt_id: fail(f"promptId 不匹配：请求 {args.prompt_id}，响应 {actual}")
    if not body or not body.strip(): fail("Prompt 正文为空")
    copy_raw(args.input, root / f"raw/prompt-{args.prompt_id}.json"); atomic_text(root / f"prompts/prompt-{args.prompt_id}.txt", body)
    data = manifest(root); data["resources"]["prompts"][str(args.prompt_id)] = {"path": f"prompts/prompt-{args.prompt_id}.txt", "sha256": digest(body)}; save_manifest(root, data)
def cmd_module(args):
    root = runtime(args.out_dir); response = read_json(args.input); ensure_success(response); value = unwrap(response)
    if not isinstance(value, dict) or not {"moduleConfig", "visibleModuleMap"} <= set(value): fail("模块配置无效")
    copy_raw(args.input, root / "raw/resume-module-config.json"); body = json.dumps(value, ensure_ascii=False, indent=2) + "\n"; atomic_text(root / "resume-module-config.json", body)
    data = manifest(root); data["resources"]["moduleConfig"] = {"path": "resume-module-config.json", "sha256": digest(body)}; save_manifest(root, data)
def cmd_template(args):
    root = runtime(args.out_dir); response = read_json(args.input); ensure_success(response); value = unwrap(response)
    if not isinstance(value, dict): fail("模板响应无效")
    theme = value.get("theme", value.get("templateStyleCode")); body = next((value.get(k) for k in ("html", "template", "content", "text") if isinstance(value.get(k), str)), None)
    if theme is not None and str(theme) != args.theme: fail(f"模板 theme 不匹配：请求 {args.theme}，响应 {theme}")
    if not body or not body.strip(): fail("HTML 模板正文为空")
    name = f"personal_resume_onepage_{args.theme}.html"; rendered = convert(body, name); copy_raw(args.input, root / f"raw/template-{args.theme}.json")
    atomic_text(root / f"templates/source/{name}", body); atomic_text(root / f"templates/converted/{name}", rendered)
    data = manifest(root); data["resources"]["templates"][args.theme] = {"source": f"templates/source/{name}", "sourceSha256": digest(body), "converted": f"templates/converted/{name}", "convertedSha256": digest(rendered)}; save_manifest(root, data)
def cmd_verify(args):
    if args.layout_only and (args.prompt_ids or args.field_config): fail("--layout-only 与 --prompt-ids/--field-config 互斥")
    if args.prompt_ids and args.field_config: fail("--prompt-ids 与 --field-config 互斥")
    ids = parse_ids(args.prompt_ids)
    if args.field_config:
        for item in read_json(args.field_config).get("types", {}).values(): ids += [str(v) for v in (item.get("promptOneId"), item.get("promptTwoId")) if v is not None]
        ids = list(dict.fromkeys(ids))
    root = runtime(args.out_dir); verify(root, ids, bool(args.field_config) or args.layout_only)
    print(json.dumps({"ok": True, "outDir": str(root), "promptCount": len(ids)}, ensure_ascii=False))

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ingest-bundle"); p.add_argument("--input", required=True); p.add_argument("--out-dir", required=True); p.add_argument("--mode", choices=("single", "full", "layout"), required=True); p.add_argument("--prompt-ids"); p.set_defaults(func=cmd_bundle)
    p = sub.add_parser("init"); p.add_argument("--out-dir", required=True); p.set_defaults(func=cmd_init)
    for name, func in (("ingest-prompt-index", cmd_index), ("ingest-module-config", cmd_module)):
        p = sub.add_parser(name); p.add_argument("--input", required=True); p.add_argument("--out-dir", required=True); p.set_defaults(func=func)
    p = sub.add_parser("ingest-prompt"); p.add_argument("--input", required=True); p.add_argument("--prompt-id", type=int, required=True); p.add_argument("--out-dir", required=True); p.set_defaults(func=cmd_prompt)
    p = sub.add_parser("ingest-template"); p.add_argument("--input", required=True); p.add_argument("--theme", required=True); p.add_argument("--out-dir", required=True); p.set_defaults(func=cmd_template)
    p = sub.add_parser("verify"); p.add_argument("--out-dir", required=True); p.add_argument("--field-config"); p.add_argument("--prompt-ids"); p.add_argument("--layout-only", action="store_true"); p.set_defaults(func=cmd_verify)
    args = parser.parse_args(); args.func(args); return 0

if __name__ == "__main__": sys.exit(main())
