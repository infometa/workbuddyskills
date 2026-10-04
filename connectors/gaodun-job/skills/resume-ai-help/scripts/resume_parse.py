#!/usr/bin/env python3
"""
简历解析确定性脚本 (resume_parse.py) —— 1:1 还原服务端简历解析的解析/清洗/归一化。

**本文件直接复制自用户级 skill `resume-diagnosis` 的 `scripts/resume_pipeline.py` 的解析部分**
（两个 skill 的简历解析完全相同，采用复制而非引用，各自自包含）。与诊断相关的部分
（NO_FILL / NO_DATA / 6 维评分 / 报告装配 / resume-score-config.json 依赖）属于
resume-diagnosis 的业务方向，本 skill 不含，已剔除。

服务端解析逻辑（简历模块配置）变更时，
必须同步更新本文件与服务端资源包中的模块配置 /
`references/analysis-resume-rules.md`，并同步 resume-diagnosis 侧的对应文件。

子命令（路径参数传 `-` 表示走 stdin/stdout，不落盘）：
  emit-template  按模块配置生成"逐字段填写模板"，
                 模型唯一的解析职责是把每个字段的值从原文抄进来。
  finalize       清洗（技能合并/教育前缀/学历枚举归一化/时间归一化）→
                 dataFieldStatus/moduleStatus 赋值（含空模块分支）→ 模块 sort 重编号。
                 输出解析后的结构化简历（与线上入库数据同构）。
  extract-fields 从 finalize 结果提取 AI 帮你写 `--fields` 入参：
                 目标模块第 N 条记录的全部字段 + `--with` 指定的跨模块字段（如 position）。

模块配置（moduleConfig + visibleModuleMap）由调用方经 gaodun-job MCP 工具
`resume_resource_bundle_get` 一次物化后通过 `--module-config` 传入；旧工具仅兜底，本脚本不连任何 MCP 端点。

用法：
  python resume_parse.py emit-template --resume-type havingWorkExperience \
      --module-config <物化目录>/resume-module-config.json --out -
  python resume_parse.py finalize      --resume-type havingWorkExperience \
      --module-config <物化目录>/resume-module-config.json --filled - --out - < filled.json
  python resume_parse.py extract-fields --finalized - --module workExperience --data-sort 1 \
                                        --with position --out - < finalized.json
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SHOW = 1
HIDDEN = 0

# ---------------------------------------------------------------------------
# 静态映射（1:1 还原 Java 常量，与 resume-diagnosis 一致）
# ---------------------------------------------------------------------------

# 解析侧学历枚举归一化（analysis-resume-rules.md §2.1）：自由文本 -> 标准入库值
QUALIFICATION_NORMALIZE = {
    "本科": "大学本科", "学士": "大学本科", "大学本科": "大学本科",
    "硕士": "硕士研究生", "研究生": "硕士研究生", "硕士研究生": "硕士研究生",
    "博士": "博士研究生", "博士研究生": "博士研究生",
    "MBA": "MBA", "工商管理硕士": "MBA",
    "大专": "大学专科", "专科": "大学专科", "大学专科": "大学专科",
    "高中": "高中", "中专": "高中",
    "初中": "初中", "小学": "小学",
}

# cleanEducationExperience 前缀清洗正则（replaceFirst）
EDUCATION_PREFIX_RE = re.compile(r"专业课程:|专业课程：|成绩排名:|成绩排名：|专业课程|成绩排名")

# 技能合并规则：{moduleCode: (顿号拼接字段, 换行拼接字段)}
SKILL_MERGE = {
    "professionalSkills": (["languageClassify", "certificateName", "softwareName"],
                           ["languageDesc", "certificateDesc", "softwareDesc"]),
    "professionalSkillsNonOnline": (["languageSkill", "softwareOperation"],
                                    ["qualificationCertificate"]),
}


def load_json(path: Path):
    raw = path.read_text(encoding="utf-8-sig")
    return json.loads(raw if raw.lstrip().startswith("{") else "{" + raw + "}")


def _read_json(path_or_dash: str):
    """读 JSON：传 '-' 时从 stdin 读（用户/模型可直接管道传入内容，不落盘）。"""
    if path_or_dash == "-":
        # Windows 下 stdin 默认按系统代码页（GBK）解码会产生 lone surrogate，强制 UTF-8
        return json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    return load_json(Path(path_or_dash))


def _write_json(path_or_dash: str, obj):
    """写 JSON：传 '-' 时写到 stdout。"""
    if path_or_dash == "-":
        sys.stdout.buffer.write((json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return
    Path(path_or_dash).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _log(msg: str):
    """进度信息一律走 stderr，避免污染 --out - 的 stdout JSON。"""
    print(msg, file=sys.stderr)


def is_blank(v) -> bool:
    return v is None or str(v).strip() == ""


# ---------------------------------------------------------------------------
# 时间归一化（getStartEndTime / getFieldValue 1:1）
# ---------------------------------------------------------------------------

def normalize_month(raw: str, start_year: str = "") -> str:
    """归一化为 yyyy-MM；失败返回 ''。至今 -> 当前月；长度<=2 -> 拼 start 年份。"""
    if is_blank(raw):
        return ""
    s = str(raw).strip()
    if s in ("至今", "今", "现在", "present", "Present", "至今 "):
        return datetime.now().strftime("%Y-%m")
    if len(s) <= 2 and s.isdigit() and start_year:
        s = f"{start_year}-{s}"
    m = re.match(r"^(\d{4})\s*[年\-./]?\s*(\d{1,2})\s*月?$", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return ""


# ---------------------------------------------------------------------------
# emit-template（与 resume-diagnosis 完全一致）
# ---------------------------------------------------------------------------

def cmd_emit_template(args):
    cfg = load_json(Path(args.module_config))
    modules = cfg["moduleConfig"][args.resume_type]
    skeleton = {
        "_comment": "把简历原文的值逐字段抄进 records。经历类模块按原文条数增加 records 元素；"
                    "原文没有的字段保持空字符串。时间字段照抄原文（如 2023.09 / 至今），脚本会归一化。",
        "resumeType": args.resume_type,
        "modules": [],
    }
    for m in modules:
        record = {f["dataFieldCode"]: "" for f in m["dataFieldList"]}
        skeleton["modules"].append({
            "moduleCode": m["moduleCode"],
            "moduleName": m["moduleName"],
            "_hidden": bool(m.get("hidden")),
            "records": [record],
            "_fields": {f["dataFieldCode"]: f["dataFieldName"] for f in m["dataFieldList"]},
        })
    _write_json(args.out, skeleton)
    _log(f"模板已生成: {args.out}（{len(skeleton['modules'])} 个模块）")


# ---------------------------------------------------------------------------
# finalize（解析子集：清洗/归一化/状态/排序；诊断输出已剔除）
# ---------------------------------------------------------------------------

def cmd_finalize(args):
    cfg = load_json(Path(args.module_config))
    module_cfg = cfg["moduleConfig"][args.resume_type]
    visible_modules = set(cfg["visibleModuleMap"][args.resume_type])
    filled = _read_json(args.filled)
    filled_by_code = {m["moduleCode"]: m for m in filled.get("modules", [])}

    data_id_seq = [0]

    def new_data_id():
        data_id_seq[0] += 1
        return f"d{data_id_seq[0]:04d}"

    out_modules = []

    for m_cfg in module_cfg:
        code = m_cfg["moduleCode"]
        field_cfgs = m_cfg["dataFieldList"]
        hidden_cfg = bool(m_cfg.get("hidden"))
        all_can_hidden = all(bool(f.get("canHidden")) for f in field_cfgs)
        raw_records = [r for r in (filled_by_code.get(code, {}).get("records") or []) if isinstance(r, dict)]

        # ---- 清洗：技能模块多条合并为 1 条（clearProfessionalSkills / 4SinglePage）
        if code in SKILL_MERGE and len(raw_records) > 1:
            comma_fields, newline_fields = SKILL_MERGE[code]
            merged = {}
            for f in field_cfgs:
                fc = f["dataFieldCode"]
                vals = [str(r.get(fc, "")).replace("\n", "").strip() for r in raw_records if not is_blank(r.get(fc))]
                if fc in comma_fields:
                    merged[fc] = "、".join(vals)
                elif fc in newline_fields:
                    merged[fc] = "\n".join(str(r.get(fc, "")).strip() for r in raw_records if not is_blank(r.get(fc)))
                else:
                    merged[fc] = next((str(r.get(fc, "")) for r in raw_records if not is_blank(r.get(fc))), "")
            raw_records = [merged]

        has_content = any(
            not is_blank(r.get(f["dataFieldCode"])) for r in raw_records for f in field_cfgs
        )

        records_out = []  # [{dataFieldCode, dataFieldName, fieldIndex, value, dataId, dataSort, dataFieldStatus}]

        if not has_content:
            # ---- 空模块分支（analysis-resume-rules.md §3）：showOnPage==true 字段各生成 1 条空记录
            data_id = new_data_id()
            for idx, f in enumerate(field_cfgs):
                if f.get("showOnPage") is not True:
                    continue
                records_out.append({
                    "dataFieldCode": f["dataFieldCode"],
                    "dataFieldName": f["dataFieldName"],
                    "fieldIndex": idx,
                    "value": "",
                    "dataId": data_id,
                    "dataSort": 1,
                    "dataFieldStatus": SHOW if not f.get("canHidden") else HIDDEN,
                })
            module_status = HIDDEN if (hidden_cfg or all_can_hidden) else SHOW
        else:
            # ---- 有内容分支（§4）：不过滤 showOnPage，逐记录逐字段生成
            for sort_i, r in enumerate(raw_records, start=1):
                data_id = new_data_id()
                start_time = ""
                # 先归一化起止时间（end 长度<=2 需借 start 年份）
                time_values = {}
                for f in field_cfgs:
                    fc = f["dataFieldCode"]
                    if "StartTime" in fc:
                        start_time = normalize_month(r.get(fc, ""))
                        time_values[fc] = start_time
                    elif "EndTime" in fc:
                        raw_end = r.get(fc, "")
                        sv = ""
                        sy_m = re.match(r"^(\d{4})", str(r.get(fc.replace("EndTime", "StartTime"), "")))
                        if sy_m:
                            sv = sy_m.group(1)
                        time_values[fc] = normalize_month(raw_end, sv)
                for idx, f in enumerate(field_cfgs):
                    fc = f["dataFieldCode"]
                    if fc in time_values:
                        value = time_values[fc]
                    else:
                        value = "" if is_blank(r.get(fc)) else str(r.get(fc)).strip()
                        # 教育前缀清洗（cleanEducationExperience）
                        if code == "educationExperience" and fc in ("educationExperienceDesc", "classRank"):
                            value = EDUCATION_PREFIX_RE.sub("", value, count=1).strip()
                        # 学历枚举归一化（§2.1）
                        if fc == "qualification":
                            value = QUALIFICATION_NORMALIZE.get(value, value)
                    status = SHOW if (not is_blank(value) or not f.get("canHidden")) else HIDDEN
                    records_out.append({
                        "dataFieldCode": fc,
                        "dataFieldName": f["dataFieldName"],
                        "fieldIndex": idx,
                        "value": value,
                        "dataId": data_id,
                        "dataSort": sort_i,
                        "dataFieldStatus": status,
                    })
            any_value = any(not is_blank(rec["value"]) for rec in records_out)
            if code not in visible_modules:
                module_status = HIDDEN
            elif any_value or (not hidden_cfg and not all_can_hidden):
                module_status = SHOW
            else:
                module_status = HIDDEN

        out_modules.append({
            "moduleCode": code,
            "moduleName": m_cfg["moduleName"],
            "moduleStatus": module_status,
            "configHidden": hidden_cfg,
            "records": records_out,
        })

    # ---- 模块 sort：显示模块在前（配置数组序）+ 隐藏模块在后，重编号 1..N
    show_mods = [m for m in out_modules if m["moduleStatus"] == SHOW]
    hidden_mods = [m for m in out_modules if m["moduleStatus"] != SHOW]
    for i, m in enumerate(show_mods + hidden_mods, start=1):
        m["sort"] = i

    parsed = {
        "resumeType": args.resume_type,
        "modules": out_modules,
    }
    _write_json(args.out, parsed)
    filled_count = sum(1 for m in out_modules for r in m["records"] if not is_blank(r["value"]))
    _log(f"finalize 完成: {args.out}（{len(out_modules)} 个模块，{filled_count} 个字段有值）")


# ---------------------------------------------------------------------------
# extract-fields（AI 帮你写专用：解析结果 -> aihelp.py render 的 --fields 入参）
# ---------------------------------------------------------------------------

def cmd_extract_fields(args):
    fin = _read_json(args.finalized)
    with_codes = [c.strip() for c in (args.with_fields or "").split(",") if c.strip()]

    out = {}
    # ---- 目标模块第 dataSort 条记录的全部字段（含空白，空白由 aihelp 填「无」）
    mod = next((m for m in fin["modules"] if m["moduleCode"] == args.module), None)
    if mod is None:
        _log(f"WARN: 模块 {args.module} 不在解析结果中（resumeType={fin.get('resumeType')}）")
    else:
        recs = [r for r in mod["records"] if r["dataSort"] == args.data_sort]
        if not recs:
            _log(f"WARN: 模块 {args.module} 没有 dataSort={args.data_sort} 的记录")
        for r in recs:
            out[r["dataFieldCode"]] = r["value"]

    # ---- --with 跨模块字段（如 position 求职意向）：取全模块第一条非空值
    for code in with_codes:
        value = ""
        for m in fin["modules"]:
            for r in sorted(m["records"], key=lambda x: (x["dataSort"], x["fieldIndex"])):
                if r["dataFieldCode"] == code and not is_blank(r["value"]):
                    value = r["value"]
                    break
            if value:
                break
        out[code] = value

    _write_json(args.out, out)
    _log(f"extract-fields 完成: {args.out}（{sum(1 for v in out.values() if not is_blank(v))}/{len(out)} 个字段有值）")


# ---------------------------------------------------------------------------

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="简历解析确定性脚本（AI 帮你写侧，复制自 resume-diagnosis 解析部分）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("emit-template")
    p.add_argument("--resume-type", required=True)
    p.add_argument("--module-config", required=True,
                   help="模块配置 JSON（默认由 resume_resource_bundle_get 一次物化）")
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_emit_template)

    p = sub.add_parser("finalize")
    p.add_argument("--resume-type", required=True)
    p.add_argument("--module-config", required=True,
                   help="模块配置 JSON（默认由 resume_resource_bundle_get 一次物化）")
    p.add_argument("--filled", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_finalize)

    p = sub.add_parser("extract-fields")
    p.add_argument("--finalized", required=True)
    p.add_argument("--module", required=True)
    p.add_argument("--data-sort", type=int, default=1)
    p.add_argument("--with", dest="with_fields", default="")
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_extract_fields)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
