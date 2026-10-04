#!/usr/bin/env python3
"""
简历 HTML 本地渲染脚本 (render_resume_html.py) —— finalized.json (+ AI 优化覆盖) → 简历 HTML。

**不调 export 服务、不传任何数据出本机**：模板原始件不随包分发——调用方先用
gaodun-job MCP 工具 `resume_resource_bundle_get`（旧 `resume_template_get` 仅兜底）
把模板落盘为本地文件，再以 `--template-file` 传入；脚本做机械 Freemarker→Jinja2
转换后本地渲染，DOM/CSS 与线上导出文件一致。

数据模型组装 1:1 按服务端设计文档 §8.2/§8.3：
- basicInfo：baseInformation 模块第 1 条记录同名字段直填 + basicInfoCommFieldList
  （fieldTypeMap 过滤、注入 dataFieldIcon/dataFieldDefaultValue）。
- moduleInfoList：SHOW 模块按 sort 序；每条记录生成 filedList：bind 子字段跳过、
  fieldTypeMap 外丢弃、主字段带 bindFieldCode 且绑定值非空 → `值~绑定值`、
  值 HTML 转义后 \\r\\n/\\n → <br>、注入 defaultValue。
- lineHeight 默认 onepageConfig.defaultLineHeight(28)；一页纸行高压缩（design.md
  §8.3 第 7 步）一期不实现，需要时用 --line-height 显式指定。

design.md 未覆盖、按产品行为补的两条假设（Java 侧若不同以 Java 为准并更新此处）：
- dataFieldStatus=HIDDEN（canHidden 且空值）的字段不渲染——避免红字占位符出现在成品上；
- moduleStatus!=SHOW 的模块不渲染。

用法（路径传 `-` 表示 stdin/stdout）：
  python render_resume_html.py render --finalized finalized.json \\
      --template-file personal_resume_onepage_default.html \\
      [--overrides overrides.json --module-config resume-module-config.json] \\
      [--resume-name 张三的简历] \\
      [--line-height 28] [--out resume.html] [--dump-model model.json]
  python render_resume_html.py convert-check --templates-dir <dir>   # 校验全部模板可机械转换（自检用）

overrides.json 格式（AI 优化结果覆盖，dataSort 省略默认 1）：
  [{"moduleCode": "workExperience", "dataFieldCode": "workExperienceDesc",
    "dataSort": 1, "value": "优化后内容"}]

依赖：jinja2（pip install jinja2）；其余 stdlib。
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FIELDTYPE_CONFIG_PATH = BASE_DIR / "references" / "resume-fieldtype.config.json"
# 模板 HTML / 模块配置默认由调用方经 gaodun-job MCP resume_resource_bundle_get
# 一次物化后传入；旧工具仅兜底，本地不存副本、不连 MCP

SHOW = 1
HIDDEN = 0

TEMPLATE_CODES = ["default", "simplicity", "violet", "strong", "darkGreen", "azure"]
TEMPLATE_FILE = "personal_resume_onepage_{code}.html"


def read_template(path_or_dash: str) -> str:
    if path_or_dash == "-":
        return sys.stdin.buffer.read().decode("utf-8-sig")
    p = Path(path_or_dash)
    if not p.is_file():
        raise SystemExit(f"模板文件不存在: {p}（默认重新物化 resume_resource_bundle_get；旧模板工具仅兜底）")
    return p.read_text(encoding="utf-8-sig")


def _read_json(path_or_dash: str):
    if path_or_dash == "-":
        return json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    raw = Path(path_or_dash).read_text(encoding="utf-8-sig")
    return json.loads(raw)


def _write_text(path_or_dash: str, text: str):
    if path_or_dash == "-":
        sys.stdout.buffer.write(text.encode("utf-8"))
        return
    Path(path_or_dash).write_text(text, encoding="utf-8")


def _log(msg: str):
    print(msg, file=sys.stderr)


def is_blank(v) -> bool:
    return v is None or str(v).strip() == ""


# ---------------------------------------------------------------------------
# Freemarker → Jinja2 机械转换（仅覆盖 6 套模板用到的语法；转换后有残留即报错）
# ---------------------------------------------------------------------------

def freemarker_to_jinja(text: str, template_name: str) -> str:
    t = text
    t = re.sub(r"\$\{([A-Za-z0-9_.]+)!\}", r"{{ \1 }}", t)
    t = re.sub(r"<#list\s+([A-Za-z0-9_.]+)\s+as\s+([A-Za-z0-9_]+)\s*>", r"{% for \2 in \1 %}", t)
    t = re.sub(r"<#if\s+([A-Za-z0-9_.]+)\?has_content\s*>", r"{% if \1 %}", t)
    t = re.sub(r"<#elseif\s+(.+?)\s*>", r"{% elif \1 %}", t)
    t = re.sub(r"<#if\s+(.+?)\s*>", r"{% if \1 %}", t)
    t = re.sub(r"<#else\s*>", "{% else %}", t)
    t = t.replace("</#if>", "{% endif %}").replace("</#list>", "{% endfor %}")
    # 模块图标原走公司 OSS PNG（模板已中性化为相对路径 icons/<moduleCode>.png）。
    # 渲染时改用内联 SVG 占位，不依赖外网，审扫无内部 URL；保留 class="icon" 与 alt 不塌版式。
    t = re.sub(
        r'<img class="icon" src="icons/[^"]*" alt="" />',
        '<img class="icon" alt="" '
        'src="data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'20\' height=\'20\'><rect width=\'20\' height=\'20\' rx=\'3\' fill=\'%23c8c8c8\'/></svg>" />',
        t,
    )
    leftover = re.findall(r"<#|\$\{", t)
    if leftover:
        raise SystemExit(f"模板 {template_name} 转换后仍有 Freemarker 残留（{len(leftover)} 处），"
                         f"说明模板用了转换器未覆盖的语法，需先扩展 freemarker_to_jinja")
    return t


# ---------------------------------------------------------------------------
# overrides（AI 优化结果覆盖）
# ---------------------------------------------------------------------------

def apply_overrides(fin: dict, overrides: list, module_order: list) -> dict:
    """把优化后内容写进 finalized 结构；值非空时把字段/模块翻成 SHOW 并按配置序重排 sort。"""
    by_module = {m["moduleCode"]: m for m in fin["modules"]}
    for i, ov in enumerate(overrides):
        code, field_code = ov.get("moduleCode"), ov.get("dataFieldCode")
        value = ov.get("value", "")
        sort_want = ov.get("dataSort", 1)
        module = by_module.get(code)
        if module is None:
            raise SystemExit(f"overrides[{i}]：finalized 中无模块 {code}")
        targets = [r for r in module["records"]
                   if r.get("dataSort") == sort_want and r.get("dataFieldCode") == field_code]
        if not targets:
            raise SystemExit(f"overrides[{i}]：模块 {code} 第 {sort_want} 条记录中无字段 {field_code}")
        targets[0]["value"] = "" if value is None else str(value)
        if not is_blank(value):
            targets[0]["dataFieldStatus"] = SHOW
    # 模块状态翻转：任一字段有值 → SHOW；随后按配置序重排（SHOW 在前，与 finalize 同规则）
    for m in fin["modules"]:
        if m["moduleStatus"] != SHOW and any(not is_blank(r["value"]) for r in m["records"]):
            m["moduleStatus"] = SHOW
    order_idx = {c: i for i, c in enumerate(module_order)}
    show_mods = sorted((m for m in fin["modules"] if m["moduleStatus"] == SHOW),
                       key=lambda m: order_idx.get(m["moduleCode"], 999))
    hidden_mods = sorted((m for m in fin["modules"] if m["moduleStatus"] != SHOW),
                         key=lambda m: order_idx.get(m["moduleCode"], 999))
    for i, m in enumerate(show_mods + hidden_mods, start=1):
        m["sort"] = i
    return fin


# ---------------------------------------------------------------------------
# 模型组装（design.md §8.2/§8.3）
# ---------------------------------------------------------------------------

def relax_placeholder_important(out_html: str) -> str:
    """去掉 .placeholder 规则里的 !important：红色仅作未填写提示，交付后用户在编辑器里
    改字体颜色（内联 style）应能覆盖；!important 会让内联颜色永远不生效。"""
    return re.sub(r"(\.placeholder\s*\{[^}]*?)\s*!important", r"\1", out_html)


def fmt_value(value: str) -> str:
    """HTML 转义后 \\r\\n/\\n → <br>（§8.3 第 6 步）。"""
    return re.sub(r"\r\n|\n", "<br>", html.escape(value, quote=True))


def build_model(fin: dict, ftcfg: dict, resume_name: str, line_height) -> dict:
    field_type_map = {f["dataFieldCode"]: f for f in ftcfg["fieldTypeList"]}
    bind_targets = {f["bindFieldCode"] for f in ftcfg["fieldTypeList"] if f.get("bindFieldCode")}

    modules = sorted(fin["modules"], key=lambda m: m.get("sort", 999))

    # ---- basicInfo（§8.2：第 1 条记录同名直填 + commFieldList 按 fieldTypeMap 过滤）
    basic_info, comm_list = {}, []
    base = next((m for m in modules if m["moduleCode"] == "baseInformation"), None)
    if base:
        rec0 = sorted((r for r in base["records"] if r.get("dataSort") == 1),
                      key=lambda r: r.get("fieldIndex", 0))
        for r in rec0:
            basic_info[r["dataFieldCode"]] = fmt_value(r["value"])
        for r in rec0:
            ft = field_type_map.get(r["dataFieldCode"])
            if ft is None or r.get("dataFieldStatus") == HIDDEN:
                continue
            comm_list.append({
                "dataFieldIcon": ft.get("dataFieldIcon") or "",
                "dataFieldValue": fmt_value(r["value"]),
                "defaultValue": ft.get("dataFieldDefaultValue") or "",
            })
    basic_info["basicInfoCommFieldList"] = comm_list

    # ---- moduleInfoList（§8.3 parseResume）
    module_info_list = []
    for m in modules:
        if m["moduleCode"] == "baseInformation" or m.get("moduleStatus") != SHOW:
            continue
        groups = {}
        for r in m["records"]:
            groups.setdefault((r.get("dataSort", 1), r.get("dataId")), []).append(r)
        module_data = []
        for (sort_no, _data_id) in sorted(groups):
            fields = sorted(groups[(sort_no, _data_id)], key=lambda r: r.get("fieldIndex", 0))
            group_values = {r["dataFieldCode"]: r["value"] for r in fields}
            filed_list = []
            for r in fields:
                code = r["dataFieldCode"]
                if code in bind_targets:            # §8.3-2：bind 子字段整条跳过
                    continue
                ft = field_type_map.get(code)
                if ft is None:                      # §8.3-3：fieldTypeMap 外丢弃
                    continue
                if r.get("dataFieldStatus") == HIDDEN:  # 见文件头假设 1
                    continue
                value = r["value"]
                bind_code = ft.get("bindFieldCode")
                if bind_code and not is_blank(group_values.get(bind_code)):
                    value = f"{value}~{group_values[bind_code]}"   # §8.3-4：值~绑定值
                filed_list.append({
                    "dataFieldType": ft.get("dataFieldType") or "",
                    "dataFieldName": r.get("dataFieldName") or "",
                    "dataFieldValue": fmt_value(value),
                    "defaultValue": ft.get("dataFieldDefaultValue") or "",
                })
            if filed_list:
                module_data.append({"filedList": filed_list})
        if module_data:
            module_info_list.append({
                "moduleCode": m["moduleCode"],
                "moduleName": m["moduleName"],
                "moduleData": module_data,
            })

    if is_blank(resume_name):
        name = basic_info.get("personalName", "")
        resume_name = f"{name}的简历" if name else "个人简历"
    return {
        "resumeName": resume_name,
        "lineHeight": line_height,
        "basicInfo": basic_info,
        "moduleInfoList": module_info_list,
    }


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------

def cmd_render(args):
    try:
        from jinja2 import Template
    except ImportError:
        raise SystemExit("缺少依赖 jinja2，请先 pip install jinja2")

    fin = _read_json(args.finalized)
    ftcfg = _read_json(str(FIELDTYPE_CONFIG_PATH))
    if args.overrides:
        overrides = _read_json(args.overrides)
        if not isinstance(overrides, list):
            raise SystemExit("overrides.json 必须是 JSON 数组（格式见文件头说明）")
        mcfg = _read_json(args.module_config) if args.module_config else None
        if mcfg is None:
            raise SystemExit("使用 --overrides 时必须同时传 --module-config"
                             "（默认由 resume_resource_bundle_get 一次物化），用于模块排序定位")
        module_order = [m["moduleCode"] for m in mcfg["moduleConfig"][fin["resumeType"]]]
        fin = apply_overrides(fin, overrides, module_order)

    line_height = args.line_height
    if line_height is None:
        line_height = ftcfg["onepageConfig"]["defaultLineHeight"]

    model = build_model(fin, ftcfg, args.resume_name, line_height)
    if args.dump_model:
        _write_text(args.dump_model, json.dumps(model, ensure_ascii=False, indent=2) + "\n")

    tpl_name = Path(args.template_file).name if args.template_file != "-" else "stdin"
    jinja_src = freemarker_to_jinja(read_template(args.template_file), tpl_name)
    out_html = relax_placeholder_important(Template(jinja_src).render(**model))
    _write_text(args.out, out_html)
    _log(f"渲染完成: {args.out}（模板 {tpl_name}，"
         f"{len(model['moduleInfoList'])} 个模块，lineHeight={line_height}）")


def cmd_convert_check(args):
    d = Path(args.templates_dir)
    if not d.is_dir():
        raise SystemExit(f"--templates-dir 不存在: {d}（默认用 resume_resource_bundle_get 物化所选模板）")
    ok = True
    for code in TEMPLATE_CODES:
        tpl_path = d / TEMPLATE_FILE.format(code=code)
        if not tpl_path.exists():
            _log(f"MISS  {code}: {tpl_path} 不存在")
            ok = False
            continue
        try:
            freemarker_to_jinja(tpl_path.read_text(encoding="utf-8-sig"), tpl_path.name)
            _log(f"OK    {code}")
        except SystemExit as e:
            _log(f"FAIL  {code}: {e}")
            ok = False
    if not ok:
        raise SystemExit("convert-check FAILED")
    _log("convert-check PASS（6 套模板均可机械转换）")


def main():
    ap = argparse.ArgumentParser(description="finalized.json (+优化覆盖) → 简历 HTML（本地渲染，不调接口）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("render", help="渲染简历 HTML")
    p.add_argument("--finalized", required=True, help="resume_parse.py finalize 产物（路径或 -）")
    p.add_argument("--overrides", help="AI 优化结果覆盖 JSON 数组（路径或 -，可选）")
    p.add_argument("--module-config",
                   help="模块配置 JSON（默认由 resume_resource_bundle_get 一次物化）；使用 --overrides 时必传")
    p.add_argument("--template-file", required=True,
                   help="模板 HTML 文件（路径或 -；默认来自 resume_resource_bundle_get）")
    p.add_argument("--resume-name", default="", help="默认用「姓名+的简历」")
    p.add_argument("--line-height", type=int, default=None,
                   help="默认取 onepageConfig.defaultLineHeight(28)；一页纸压缩一期不实现")
    p.add_argument("--out", default="resume.html", help="输出 HTML 路径（或 -）")
    p.add_argument("--dump-model", help="可选：把组装后的模型 JSON 落盘便于排查")
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("convert-check", help="自检：6 套模板均可机械转换")
    p.add_argument("--templates-dir", required=True,
                   help="含 6 套 personal_resume_onepage_<code>.html 的目录（MCP 物化产物）")
    p.set_defaults(fn=cmd_convert_check)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
