#!/usr/bin/env python3
"""简历 AI 帮你写：确定性渲染/解析脚本（1:1 对应服务端 prompt 装配逻辑）。

子命令：
  show      --type <dataFieldCode> [--prompts-dir <dir>]      查看类型配置（promptId/模型/变量映射）
  render    --type <dataFieldCode> --stage ask|opt --prompts-dir <dir>   渲染最终 systemPrompt + 固定 userContent
            [--fields-file fields.json] [--qa-file qa.json]
  parse-ask [--response-file response.json]                 校验追问输出，1:1 parseGenerateQuestionResponse
  parse-opt [--response-file response.json]                 校验优化输出，1:1 parseOptimizeResponse
  selfcheck --prompts-dir <dir>                             校验 field-config.json ↔ prompts 数据一致性

prompt 原文与索引不随包分发：调用方默认用 gaodun-job MCP 工具 resume_resource_bundle_get
（不传参=全量索引；传 prompt_id=原文+元数据）把所需内容物化到本地目录：
  <dir>/prompts-index.json        （索引整体落盘）
  <dir>/prompts/prompt-<id>.txt   （每个 prompt 原文一个文件）
脚本只读这个目录，自己不连任何 MCP 端点。

确定性规则（与 Java 一致，模型不得绕过脚本自行拼装）：
  - 变量值取 fields[请求字段]，空白 → "无"（buildCommonPromptParam）
  - 优化阶段追加 information = "1.{question}\\n答：{answer or 无}\\n" 逐条拼接；无问答 → "无"（buildQuestionParam）
  - user content 恒为 "开始，注意输出格式，注意输出格式"（简历正文走变量，不走 user message）
  - 追问输出要么 question1/2/3 全部非空（有追问），要么全部留空（无追问，直接进优化）；优化输出必须含非空 resume；否则判失败
"""
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "references" / "field-config.json"

DEFAULT_TEXT = "无"
VAR_RE = re.compile(r"\{\{\$(\w+)\}\}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_prompts_dir(raw: str):
    """物化目录 → (index, prompts_dir)；默认由 resume_resource_bundle_get 一次物化，旧工具仅作兜底。"""
    d = Path(raw)
    index_path = d / "prompts-index.json"
    prompts_dir = d / "prompts"
    if not index_path.is_file() or not prompts_dir.is_dir():
        fail(f"--prompts-dir 需包含 prompts-index.json 与 prompts/ 目录（内容来自 gaodun-job MCP "
             f"resume_resource_bundle_get（旧 resume_prompt_get 仅兜底；脚本不连 MCP）: {d}")
    return load_json(index_path), prompts_dir


def read_prompt(prompts_dir: Path, prompt_id) -> str:
    p = prompts_dir / f"prompt-{prompt_id}.txt"
    if not p.exists():
        fail(f"prompt 原文缺失: {p}（默认重新物化 resume_resource_bundle_get；旧 resume_prompt_get 仅兜底）")
    return p.read_text(encoding="utf-8")


def get_type(config: dict, data_field_code: str) -> dict:
    t = config["types"].get(data_field_code)
    if t is None:
        known = "、".join(sorted(config["types"]))
        fail(f"未知 dataFieldCode: {data_field_code}（已知：{known}）")
    return t


def fail(msg: str, code: int = 2):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def read_stdin() -> str:
    return sys.stdin.read()


def parse_json_arg(raw: str, what: str):
    try:
        return json.loads(raw)
    except Exception as e:  # noqa: BLE001
        fail(f"{what} 不是合法 JSON: {e}")


def build_variables(type_cfg: dict, fields: dict) -> dict:
    """1:1 buildCommonPromptParam：按 variableMappings 映射，空白填 无。"""
    variables = {}
    for req_field, prompt_var in type_cfg["variableMappings"].items():
        value = fields.get(req_field)
        if value is None or not str(value).strip():
            value = DEFAULT_TEXT
        variables[prompt_var] = str(value)
    return variables


def build_information(qa) -> str:
    """1:1 buildQuestionParam：'1.{question}\\n答：{answer or 无}\\n' 逐条；空 → 无。"""
    if not qa:
        return DEFAULT_TEXT
    parts = []
    for i, item in enumerate(qa):
        question = str(item.get("question") or "").strip()
        answer = str(item.get("answer") or "").strip() or DEFAULT_TEXT
        parts.append(f"{i + 1}.{question}\n答：{answer}\n")
    return "".join(parts)


def cmd_show(config: dict, index: dict | None, data_field_code: str):
    t = get_type(config, data_field_code)
    ask = (index or {}).get(str(t["promptOneId"]), {})
    opt = (index or {}).get(str(t["promptTwoId"]), {})
    out = {
        "dataFieldCode": data_field_code,
        "label": t.get("label"),
        "moduleCode": t["moduleCode"],
        "botId": config["botId"],
        "ask": {"promptId": t["promptOneId"], "name": ask.get("name"), "model": ask.get("model"), "updatedAt": ask.get("updatedAt")},
        "optimize": {"promptId": t["promptTwoId"], "name": opt.get("name"), "model": opt.get("model"), "updatedAt": opt.get("updatedAt")},
        "variableMappings": t["variableMappings"],
        "fixedUserContent": config["fixedUserContent"],
    }
    if t.get("modelException"):
        out["modelException"] = t["modelException"]
    if t.get("note"):
        out["note"] = t["note"]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_render(config: dict, index: dict, prompts_dir: Path, data_field_code: str, stage: str, fields_raw: str, qa_raw: str):
    t = get_type(config, data_field_code)
    fields = parse_json_arg(fields_raw, "--fields") if fields_raw else {}
    if not isinstance(fields, dict):
        fail("--fields 必须是 JSON object，如 '{\"position\":\"测试工程师\"}'")

    prompt_id = t["promptOneId"] if stage == "ask" else t["promptTwoId"]
    system_prompt = read_prompt(prompts_dir, prompt_id)

    variables = build_variables(t, fields)
    if stage == "opt":
        qa = parse_json_arg(qa_raw, "--qa") if qa_raw else None
        if qa is not None and not isinstance(qa, list):
            fail("--qa 必须是 JSON array，如 '[{\"question\":\"...\",\"answer\":\"...\"}]'")
        variables["information"] = build_information(qa)

    def sub(m):
        var = m.group(1)
        if var == "query":
            return m.group(0)  # query 是 user message 占位，不在 systemRole 渲染范围
        if var in variables:
            return variables[var]
        print(f"WARN: systemRole 中的变量 {var} 无映射，按 无 处理", file=sys.stderr)
        return DEFAULT_TEXT

    rendered = VAR_RE.sub(sub, system_prompt)
    meta = index.get(str(prompt_id), {})
    out = {
        "dataFieldCode": data_field_code,
        "stage": stage,
        "promptId": prompt_id,
        "promptName": meta.get("name"),
        "model": meta.get("model"),
        "temperature": meta.get("temperature"),
        "variables": variables,
        "systemPrompt": rendered,
        "userContent": config["fixedUserContent"],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def strict_parse(raw: str):
    """严格 JSON 解析（对齐 gson 首次解析；失败由模型修复一次后重试）。"""
    if not raw or not raw.strip():
        return None, "blank response"
    try:
        return json.loads(raw), None
    except Exception as e:  # noqa: BLE001
        return None, f"json parse error: {e}"


def cmd_parse_ask(raw=None):
    raw = read_stdin() if raw is None else raw
    data, err = strict_parse(raw)
    if err:
        print(json.dumps({"ok": False, "reason": err}, ensure_ascii=False))
        sys.exit(1)
    if not isinstance(data, dict):
        print(json.dumps({"ok": False, "reason": "追问响应必须是 JSON 对象"}, ensure_ascii=False))
        sys.exit(1)
    questions = [str(data.get(f"question{i}") or "").strip() for i in (1, 2, 3)]
    filled = [q for q in questions if q]
    if not filled:
        # 模型判断信息充分：无追问，调用方直接进优化（runner no-questions）
        print(json.dumps({"ok": True, "questions": []}, ensure_ascii=False))
        return
    if len(filled) != 3:
        print(json.dumps({"ok": False, "reason": "question1/2/3 必须全部非空（有追问）或全部留空（无追问），不允许残缺"}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps({"ok": True, "questions": questions}, ensure_ascii=False, indent=2))


def cmd_parse_opt(raw=None):
    raw = read_stdin() if raw is None else raw
    data, err = strict_parse(raw)
    if err:
        print(json.dumps({"ok": False, "reason": err}, ensure_ascii=False))
        sys.exit(1)
    resume = str(data.get("resume") or "").strip() if isinstance(data, dict) else ""
    if not resume:
        print(json.dumps({"ok": False, "reason": "resume 字段为空"}, ensure_ascii=False))
        sys.exit(1)
    out = {
        "ok": True,
        "resume": data["resume"],
        "responsibility": data.get("responsibility"),
        "suggestion": data.get("suggestion"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_selfcheck(config: dict, index: dict, prompts_dir: Path) -> int:
    problems = []
    warns = []
    for code, t in sorted(config["types"].items()):
        mapped = set(t["variableMappings"].values())
        for stage, pid in (("ask", t["promptOneId"]), ("opt", t["promptTwoId"])):
            sid = str(pid)
            meta = index.get(sid)
            if meta is None:
                problems.append(f"{code}/{stage} prompt-{pid}: 不在 prompts-index.json")
                continue
            txt = prompts_dir / f"prompt-{pid}.txt"
            if not txt.exists():
                problems.append(f"{code}/{stage} prompt-{pid}: 缺 {txt}")
                continue
            body = txt.read_text(encoding="utf-8")
            envs = set(meta.get("envs") or [])
            expect = mapped | ({"information"} if stage == "opt" else set())
            if envs != expect:
                problems.append(f"{code}/{stage} prompt-{pid}: envs={sorted(envs)} 与映射期望={sorted(expect)} 不一致")
            used = set(VAR_RE.findall(body)) - {"query"}
            if not used <= envs:
                problems.append(f"{code}/{stage} prompt-{pid}: systemRole 用了未声明变量 {sorted(used - envs)}")
            if envs - used:
                warns.append(f"{code}/{stage} prompt-{pid}: 声明但未在 systemRole 使用 {sorted(envs - used)}")
    for w in warns:
        print(f"WARN: {w}")
    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        print(f"selfcheck: {len(problems)} 个问题")
        return 1
    print(f"selfcheck PASS: {len(config['types'])} 类型 × 2 prompt 全部一致（{len(warns)} 条 WARN）")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    cmd, rest = args[0], args[1:]

    def opt_value(flag: str):
        if flag in rest:
            i = rest.index(flag)
            if i + 1 >= len(rest):
                fail(f"{flag} 缺参数")
            return rest[i + 1]
        return None

    def file_or_inline(file_flag: str, inline_flag: str):
        file_value = opt_value(file_flag)
        inline_value = opt_value(inline_flag)
        if file_value and inline_value:
            fail(f"{file_flag} 与 {inline_flag} 不能同时使用")
        if file_value:
            path = Path(file_value)
            if not path.is_file():
                fail(f"文件不存在: {path}")
            return path.read_text(encoding="utf-8-sig")
        return inline_value

    config = load_json(CONFIG_PATH)

    if cmd == "show":
        index = None
        if opt_value("--prompts-dir"):
            index, _ = load_prompts_dir(opt_value("--prompts-dir"))
        cmd_show(config, index, opt_value("--type") or fail("缺 --type"))
        return 0
    if cmd == "render":
        stage = opt_value("--stage") or fail("缺 --stage ask|opt")
        if stage not in ("ask", "opt"):
            fail("--stage 只支持 ask|opt")
        index, prompts_dir = load_prompts_dir(opt_value("--prompts-dir") or fail("缺 --prompts-dir"))
        cmd_render(
            config,
            index,
            prompts_dir,
            opt_value("--type") or fail("缺 --type"),
            stage,
            file_or_inline("--fields-file", "--fields"),
            file_or_inline("--qa-file", "--qa"),
        )
        return 0
    if cmd == "parse-ask":
        cmd_parse_ask(file_or_inline("--response-file", "--response"))
        return 0
    if cmd == "parse-opt":
        cmd_parse_opt(file_or_inline("--response-file", "--response"))
        return 0
    if cmd == "selfcheck":
        index, prompts_dir = load_prompts_dir(opt_value("--prompts-dir") or fail("缺 --prompts-dir"))
        return cmd_selfcheck(config, index, prompts_dir)
    fail(f"未知子命令: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
