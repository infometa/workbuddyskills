#!/usr/bin/env python3
"""
简历诊断确定性流水线 (resume_pipeline.py)

把简历诊断/评分中所有**确定性**逻辑代码化（规则说明见
references/analysis-resume-rules.md / diagnosis-categories.md / scoring-rubric.md /
diagnose-output-template.md）：

  1. prepare       : 前置合并（照片检测 idPhoto + 生成填写模板）。文本提取**不限定文件类型**，
                     默认由模型用 Read 工具直接读取原文；仅当 AI 读不了（如旧版 .doc 二进制）
                     时，才用 extract-text 兜底。
  2. extract-text  : 兜底文本提取（.docx 标准库解 XML / .doc 调 extract_spire、extract_doc_text），
                     仅当模型 Read 读不了时显式调用，不参与主流程的类型分支。
  3. emit-template : 按 resume-module-config.json 生成"逐字段填写模板"，
                     模型唯一的解析职责是把每个字段的值从原文抄进来。
  4. finalize      : 清洗（技能合并/教育前缀/学历枚举归一化/时间归一化）→
                     dataFieldStatus/moduleStatus 赋值（含空模块分支）→
                     模块 sort 重编号 → 可见字段过滤 →
                     NO_FILL / NO_DATA 候选 → DESCRIPTION_SUGGEST 目标清单 →
                     评分 LLM 输入串 → 5 个确定性维度评分。
  5. emit-llm-tasks: 把 finalize 结果中的 suggestTargets + scoreGptInput 组装成
                     「单次批量 LLM 任务单」（每个字段只附该字段用到的 Prompt 原文，
                     从 references/diagnose-prompts.json 机器读取，不再让模型整份加载），
                     模型一次推理产出全部 suggestions + score，替代逐字段多次 LLM 调用
                     的串行模拟。
  6. build-report  : 合并 LLM 建议 + 评分模块分 → 描述建议编号 →
                     按 sort/字段下标装配 reportDetails → score + beatPercent。

用法（路径参数传 `-` 表示走 stdin/stdout，不落盘）：
  python resume_pipeline.py emit-template --resume-type havingInternshipExperience --out skeleton.json
  python resume_pipeline.py finalize      --resume-type havingInternshipExperience --filled filled.json --out finalized.json
  python resume_pipeline.py finalize      --resume-type havingInternshipExperience --filled - --out - < filled.json
  python resume_pipeline.py extract-text  --resume-file "resume.doc" --out tmp/resume.txt   # 仅 AI Read 读不了时兜底
  python resume_pipeline.py build-report  --finalized finalized.json --suggestions suggestions.json \
                                          --gpt-score gpt_score.json --resume-id <id> --out report.json

零落盘流程（推荐）：build-report 的 suggestions / gpt-score 可直接内嵌在 --finalized 的
stdin 输入中（`_suggestions` / `_gptScore` 键），全程只走 stdin/stdout：
  python resume_pipeline.py build-report --finalized - --out - --resume-id <id> <<'JSON'
  { ...finalized 完整内容..., "_suggestions": {...}, "_gptScore": {...} }
  JSON
"""

import argparse
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODULE_CONFIG_PATH = BASE_DIR / "references" / "resume-module-config.json"
SCORE_CONFIG_PATH = BASE_DIR / "references" / "resume-score-config.json"
DIAGNOSE_PROMPTS_PATH = BASE_DIR / "references" / "diagnose-prompts.json"
SCORE_PROMPT_PATH = BASE_DIR / "references" / "resume-score-prompt.txt"

SHOW = 1
HIDDEN = 0

# ---------------------------------------------------------------------------
# 静态映射
# ---------------------------------------------------------------------------

# PROFESSION_MAP（学历入库值 -> qualificationScoreMap key）
PROFESSION_MAP = {
    "博士研究生": "doctor",
    "MBA": "mba",
    "硕士研究生": "master",
    "大学本科": "undergraduate",
    "大学专科": "specialist",
    "高中": "highSchool",
    "初中": "juniorHighSchool",   # qualificationScoreMap 中无此 key -> 0 分
    "小学": "primarySchool",      # qualificationScoreMap 中无此 key -> 0 分
}

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

# 各 resumeType 的 NO_DATA 检查模块组合
NO_DATA_MODULES = {
    "noInternshipExperience": ["practicalExperience", "professionalSkillsNonOnline"],
    "havingInternshipExperience": ["internshipExperience", "practicalExperience", "professionalSkillsNonOnline"],
    "onlineApplication": ["internshipExperience", "practicalExperience", "professionalSkills"],
    "havingWorkExperience": ["workExperience", "projectExperience", "professionalSkillsNonOnline"],
}

# computeProfessionalAbilityScore：三类命中字段
PROFESSIONAL_CATEGORIES = [
    ["languageClassify", "languageDesc", "languageSkill"],
    ["certificateName", "certificateDesc", "qualificationCertificate"],
    ["softwareName", "softwareDesc", "softwareOperation"],
]

# computeCreativeLeadershipScore：四类命中模块
CREATIVE_MODULES = ["projectExperience", "practicalExperience", "competitionExperience", "campusActivities"]

# cleanEducationExperience 前缀清洗正则（replaceFirst）
EDUCATION_PREFIX_RE = re.compile(r"专业课程:|专业课程：|专业课程")

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
# 时间归一化
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


def months_between(start: str, end: str):
    """结束月数 = (结束年-起始年)*12 + (结束月-起始月) + 1；解析失败返回 None。"""
    try:
        sy, sm = int(start[:4]), int(start[5:7])
        ey, em = int(end[:4]), int(end[5:7])
    except (ValueError, IndexError):
        return None
    return (ey - sy) * 12 + (em - sm) + 1


# ---------------------------------------------------------------------------
# prepare（照片检测 + 填写模板）与 extract-text（兜底文本提取）共用工具
# ---------------------------------------------------------------------------

def _count_embedded_images(data: bytes) -> int:
    """二进制魔数计数：JPEG / PNG / GIF 任一 >=1 即认为文档内嵌图片。"""
    return data.count(b"\xff\xd8\xff") + data.count(b"\x89PNG") + data.count(b"GIF8")


def _extract_docx(data: bytes) -> str:
    """纯标准库提取 .docx 文本（无 Spire 依赖时的首选路径）。"""
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:br[^>]*/>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


def _docx_has_media(data: bytes) -> bool:
    import io
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return any(n.startswith("word/media/") for n in zf.namelist())
    except zipfile.BadZipFile:
        return False


def _extract_doc_via_scripts(path: Path):
    """调 extract_spire.py（优先）/ extract_doc_text.py（兜底）提取 .doc 文本。"""
    for script in ("extract_spire.py", "extract_doc_text.py"):
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / script), str(path)],
            capture_output=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.decode("utf-8", "replace"), script
    return None, None


def _build_template(resume_type: str) -> dict:
    """emit-template 的复用内核（cmd_emit_template / cmd_prepare 共用）。"""
    cfg = load_json(MODULE_CONFIG_PATH)
    modules = cfg["moduleConfig"][resume_type]
    skeleton = {
        "_comment": "把简历原文的值逐字段抄进 records。经历类模块按原文条数增加 records 元素；"
                    "原文没有的字段保持空字符串。时间字段照抄原文（如 2023.09 / 至今），脚本会归一化。",
        "resumeType": resume_type,
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
    return skeleton


def cmd_prepare(args):
    """照片检测 + 填写模板。文本提取默认由模型用 Read 工具读取，脚本不限定文件类型。"""
    result = {"idPhotoDetected": False}

    if args.resume_file:
        path = Path(args.resume_file)
        if not path.exists():
            raise SystemExit(f"简历文件不存在: {path}")
        data = path.read_bytes()
        # 照片检测只读原始字节，不解析文件类型（.docx 额外查 word/media/ 目录）
        result["idPhotoDetected"] = (
            _docx_has_media(data) if path.suffix.lower() == ".docx" else False
        ) or _count_embedded_images(data) >= 1

    result["idPhoto"] = "<已上传证件照>" if result["idPhotoDetected"] else ""
    result["template"] = _build_template(args.resume_type)
    _write_json(args.out, result)
    _log(f"prepare 完成: idPhoto 检测={'含照片' if result['idPhotoDetected'] else '未检出/不适用'}"
         f"，模板 {len(result['template']['modules'])} 个模块")


def cmd_extract_text(args):
    """兜底文本提取：仅当模型 Read 工具读不了文件时显式调用，不参与主流程类型分支。"""
    path = Path(args.resume_file)
    if not path.exists():
        raise SystemExit(f"简历文件不存在: {path}")
    data = path.read_bytes()
    ext = path.suffix.lower()
    text = None
    source = None
    if ext == ".docx":
        text = _extract_docx(data)
        source = "docx-zipfile"
    elif ext == ".doc":
        text, source = _extract_doc_via_scripts(path)
    else:
        raise SystemExit(f"extract-text 不支持的格式 {ext or '(无扩展名)'}：请先用 Read 工具读取；"
                         "Read 读不了时请告知用户该格式暂不受支持")
    if not text or not text.strip():
        raise SystemExit("文本提取结果为空，请检查文件是否为有效文档")
    if args.out == "-":
        sys.stdout.buffer.write(text.encode("utf-8"))
    else:
        Path(args.out).write_text(text, encoding="utf-8")
    _log(f"extract-text 完成: {path} -> {args.out}（{source}，{len(text)} 字符）")


# ---------------------------------------------------------------------------
# emit-template
# ---------------------------------------------------------------------------

def cmd_emit_template(args):
    skeleton = _build_template(args.resume_type)
    _write_json(args.out, skeleton)
    _log(f"模板已生成: {args.out}（{len(skeleton['modules'])} 个模块）")


# ---------------------------------------------------------------------------
# finalize
# ---------------------------------------------------------------------------

def cmd_finalize(args):
    cfg = load_json(MODULE_CONFIG_PATH)
    score_cfg = load_json(SCORE_CONFIG_PATH)
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
                        if code == "educationExperience" and fc == "educationExperienceDesc":
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

    # ---- 可见字段过滤
    show_fields = []
    for m in show_mods:
        for rec in m["records"]:
            if rec["dataFieldStatus"] == SHOW:
                show_fields.append({**rec, "moduleCode": m["moduleCode"], "moduleName": m["moduleName"]})

    # ---- NO_FILL：按 moduleCode-dataFieldCode 分组，任一记录空白即记 1 条
    no_fill = []
    groups = {}
    for sf in show_fields:
        groups.setdefault((sf["moduleCode"], sf["dataFieldCode"]), []).append(sf)
    for (mc, fc), recs in groups.items():
        if any(is_blank(r["value"]) for r in recs):
            no_fill.append({
                "moduleCode": mc, "moduleName": recs[0]["moduleName"],
                "dataFieldCode": fc, "dataFieldName": recs[0]["dataFieldName"],
                "fieldIndex": recs[0]["fieldIndex"],
            })

    # ---- NO_DATA：组合内逐模块，可见字段全空白即记（空流 quirk 保留）
    no_data = []
    for mc in NO_DATA_MODULES[args.resume_type]:
        recs = [sf for sf in show_fields if sf["moduleCode"] == mc]
        if all(is_blank(r["value"]) for r in recs):
            mod = next((m for m in out_modules if m["moduleCode"] == mc), None)
            no_data.append({"moduleCode": mc, "moduleName": mod["moduleName"] if mod else mc})

    # ---- DESCRIPTION_SUGGEST 目标：值非空且命中 diagnosePromptMap
    prompt_fields = set(score_cfg["diagnosePromptMap"].keys())
    suggest_targets = [
        {"moduleCode": sf["moduleCode"], "moduleName": sf["moduleName"],
         "dataFieldCode": sf["dataFieldCode"], "dataId": sf["dataId"],
         "dataSort": sf["dataSort"], "value": sf["value"]}
        for sf in show_fields
        if not is_blank(sf["value"]) and sf["dataFieldCode"] in prompt_fields
    ]

    # ---- 评分 LLM 输入串（按 scoreGptConfig.fieldList 顺序，隐藏模块跳过）
    gpt_input_parts = []
    for fc in score_cfg["scoreGptConfig"]["fieldList"]:
        mc = fc["moduleCode"]
        mod = next((m for m in out_modules if m["moduleCode"] == mc), None)
        if not mod or mod["moduleStatus"] != SHOW:
            continue
        vals = sorted(
            [sf for sf in show_fields if sf["moduleCode"] == mc
             and sf["dataFieldCode"] == fc["dataFieldCode"] and not is_blank(sf["value"])],
            key=lambda r: r["dataSort"],
        )
        for i, sf in enumerate(vals, start=1):
            gpt_input_parts.append(f"{fc['moduleName']}{i}：\n{sf['value']}\n")
    gpt_input = "".join(gpt_input_parts)

    # ---- 确定性 5 维评分
    msm = score_cfg["moduleScoreMap"]
    total_fields = len(show_fields)
    filled_fields = sum(1 for sf in show_fields if not is_blank(sf["value"]))
    complete_score = filled_fields * msm["resumeComplete"] // total_fields if total_fields else 0

    qual_scores = []
    for sf in show_fields:
        if sf["dataFieldCode"] == "qualification" and not is_blank(sf["value"]):
            key = PROFESSION_MAP.get(sf["value"], "")
            qual_scores.append(score_cfg["qualificationScoreMap"].get(key, 0))
    learning_score = (max(qual_scores) * msm["learningAbility"] // 10) if qual_scores else 0

    prof_hits = 0
    for cat in PROFESSIONAL_CATEGORIES:
        if any(sf["dataFieldCode"] in cat and not is_blank(sf["value"]) for sf in show_fields):
            prof_hits += 1
    professional_score = int(score_cfg["professionalAbilityScoreMap"][str(prof_hits)]) * msm["professionalAbility"] // 10

    creative_hits = 0
    for mc in CREATIVE_MODULES:
        if any(sf["moduleCode"] == mc and not is_blank(sf["value"]) for sf in show_fields):
            creative_hits += 1
    creative_score = int(score_cfg["creativeLeadershipScoreMap"][str(creative_hits)]) * msm["creativeLeadership"] // 10

    career_months = 0
    for prefix in ("internship", "work"):
        starts = {}
        ends = {}
        for sf in show_fields:
            if sf["dataFieldCode"] == f"{prefix}StartTime" and not is_blank(sf["value"]):
                starts[sf["dataId"]] = sf["value"]
            elif sf["dataFieldCode"] == f"{prefix}EndTime" and not is_blank(sf["value"]):
                ends[sf["dataId"]] = sf["value"]
        for data_id, st in starts.items():
            en = ends.get(data_id)
            if not en:
                continue
            delta = months_between(st, en)
            if delta is not None:
                career_months += delta
    career_base = 0
    for rng, base in score_cfg["workPlaceScoreMap"].items():
        low, high = (int(x) for x in rng.split("--"))
        if career_months > low and career_months <= high:
            career_base = int(base)
            break
    career_score = career_base * msm["workplaceAbility"] // 10

    finalized = {
        "resumeType": args.resume_type,
        "modules": out_modules,
        "showFieldsCount": total_fields,
        "filledFieldsCount": filled_fields,
        "noFill": no_fill,
        "noData": no_data,
        "suggestTargets": suggest_targets,
        "scoreGptInput": gpt_input,
        "scores": {
            "completeScore": complete_score,
            "learningAbilityScore": learning_score,
            "professionalAbilityScore": professional_score,
            "creativeLeadershipScore": creative_score,
            "careerAbilityScore": career_score,
            "careerMonths": career_months,
        },
    }
    _write_json(args.out, finalized)
    _log(f"finalize 完成: {args.out}")
    _log(f"  showFields {filled_fields}/{total_fields}，NO_FILL {len(no_fill)} 条，NO_DATA {len(no_data)} 条，"
         f"建议目标 {len(suggest_targets)} 条，职场月数 {career_months}")
    _log(f"  确定性得分: 完整度{complete_score} 学习{learning_score} 专业{professional_score} "
         f"创新{creative_score} 职场{career_score}（经历描述分待 GPT）")


# ---------------------------------------------------------------------------
# emit-llm-tasks（单次批量 LLM 任务单）
# ---------------------------------------------------------------------------

def cmd_emit_llm_tasks(args):
    fin = _read_json(args.finalized)
    prompts = load_json(DIAGNOSE_PROMPTS_PATH)
    score_prompt = SCORE_PROMPT_PATH.read_text(encoding="utf-8").strip()

    targets = fin.get("suggestTargets") or []
    # 按字段分组：同字段多条共用一份 Prompt（原本是逐字段多次独立 LLM 调用，但每次的
    # system prompt 相同、user 消息只传字段值本身，条目间互不影响 -> 批量等价）
    groups = {}
    for t in targets:
        groups.setdefault(t["dataFieldCode"], []).append(t)

    L = []
    L.append("# 简历诊断 LLM 任务单（一次推理完成全部任务，不要分多次输出）")
    L.append("")
    L.append("> **判定纪律**：每个任务独立判定、互不影响。判「暂无修改建议」前必须逐条对照该任务的"
             " Rules，内部确认每条都明确满足；任何一条存疑/不满足都必须输出建议 JSON；"
             "内容与本字段无关时建议固定为「请认真完善哦～」。")
    L.append("> 全部任务完成后，只按文末《输出协议》输出**一个** JSON 对象，不要输出其他内容。")
    L.append("")

    L.append("## A. 诊断任务（DESCRIPTION_SUGGEST）")
    L.append("")
    if not groups:
        L.append("（无诊断任务，suggestions 输出空数组）")
        L.append("")
    task_no = 0
    for fc, items in groups.items():
        meta = prompts.get(fc)
        if meta is None:  # 防御：diagnosePromptMap 之外的字段不应出现在 suggestTargets
            _log(f"警告: 字段 {fc} 无对应 Prompt，已跳过")
            continue
        task_no += 1
        L.append(f"### 任务 A{task_no}：{meta['moduleName']}（fieldCode={fc}，共 {len(items)} 条）")
        L.append("")
        L.append("Prompt 原文（本任务所有条目共用，Role/Rules/OutputFormat/Addition 逐字生效）：")
        L.append("")
        L.append("```")
        L.append(meta["prompt"])
        L.append("```")
        L.append("")
        for t in sorted(items, key=lambda x: x.get("dataSort", 0)):
            L.append(f"**待诊断值**（moduleCode={t['moduleCode']} fieldCode={fc} dataSort={t['dataSort']}，"
                     "判定时只看下面的值本身，不拼字段名）：")
            L.append("")
            L.append(str(t["value"]))
            L.append("")

    L.append("## B. 经历描述评分任务")
    L.append("")
    L.append("Prompt 原文（逐字生效）：")
    L.append("")
    L.append("```")
    L.append(score_prompt)
    L.append("```")
    L.append("")
    gpt_input = fin.get("scoreGptInput") or ""
    if gpt_input.strip():
        L.append("**待评分输入**（模块名N：\\n值\\n 格式，由确定性脚本拼好，原样使用）：")
        L.append("")
        L.append(gpt_input)
    else:
        L.append("**待评分输入为空** -> 按 Prompt Addition：必须全 0 分。")
    L.append("")

    L.append("## 输出协议（唯一输出，单个 JSON 对象）")
    L.append("")
    L.append("```json")
    L.append(json.dumps({
        "suggestions": [
            {"moduleCode": "<任务标注的 moduleCode>", "fieldCode": "<任务标注的 fieldCode>",
             "dataSort": 1, "suggestion": "1.xxx\n2.xx"},
        ],
        "score": {"实习经历": 82, "自我评价": 70},
    }, ensure_ascii=False, indent=2))
    L.append("```")
    L.append("")
    L.append("- `suggestions`：只收录「输出建议 JSON」的任务（含与本字段无关的「请认真完善哦～」）；"
             "判「暂无修改建议」的任务**跳过不写**。同字段多条用不同 `dataSort` 区分，与任务标注一致。")
    L.append("- `score`：按评分 Prompt 的 OutputFormat，键用其中文模块名原样；无内容的模块给 0。")
    L.append("- `dataId` 不需要（报告装配只按 moduleCode+fieldCode 分组、dataSort 排序）。")

    text = "\n".join(L)
    if args.out == "-":
        sys.stdout.buffer.write(text.encode("utf-8"))
    else:
        Path(args.out).write_text(text, encoding="utf-8")
    _log(f"任务单已生成: {args.out}（诊断 {len(groups)} 个字段 / {len(targets)} 条 + 评分 1 次）")


# ---------------------------------------------------------------------------
# build-report
# ---------------------------------------------------------------------------

def cmd_build_report(args):
    fin = _read_json(args.finalized)
    score_cfg = load_json(SCORE_CONFIG_PATH)

    # ---- 无文件流：suggestions / gpt-score 可内嵌在 --finalized 输入中（_suggestions / _gptScore 键），
    #     显式传参时优先用文件，缺省时读内嵌键（零落盘流程只传一份 stdin）
    gpt_raw = None
    if args.gpt_score:
        gpt_raw = _read_json(args.gpt_score)
    elif "_gptScore" in fin:
        gpt_raw = fin["_gptScore"]

    sugg_raw = None
    if args.suggestions:
        sugg_raw = _read_json(args.suggestions)
    elif "_suggestions" in fin:
        sugg_raw = fin["_suggestions"]

    # ---- 经历描述分：{"score": {"模块名": int}} -> moduleName->moduleCode -> 仅 score>0 求均值
    description_score = 0
    if gpt_raw:
        name2code = {f["moduleName"]: f["moduleCode"] for f in score_cfg["scoreGptConfig"]["fieldList"]}
        valid = []
        for name, val in (gpt_raw.get("score") or {}).items():
            try:
                v = int(val)
            except (TypeError, ValueError):
                continue
            if name in name2code and v > 0:
                valid.append(v)
        if valid:
            avg = sum(valid) / len(valid)
            description_score = int(avg * score_cfg["moduleScoreMap"]["experienceDesc"] / 100)

    s = fin["scores"]
    total = (s["completeScore"] + description_score + s["learningAbilityScore"]
             + s["professionalAbilityScore"] + s["creativeLeadershipScore"] + s["careerAbilityScore"])

    # ---- beatPercent：scoreList 左闭右开首个命中
    beat_percent = None
    for row in score_cfg["scoreList"]:
        if row["min"] <= total < row["max"]:
            beat_percent = f"{row['beatPercent']}%"
            break

    # ---- DESCRIPTION_SUGGEST：描述建议分组编号
    suggestions = (sugg_raw or {}).get("suggestions", [])
    sugg_by_field = {}
    for sg in suggestions:
        if is_blank(sg.get("suggestion")):
            continue
        sugg_by_field.setdefault((sg["moduleCode"], sg["fieldCode"]), []).append(sg)
    suggest_texts = {}  # moduleCode -> [text]
    for (mc, _fc), items in sugg_by_field.items():
        items.sort(key=lambda x: x.get("dataSort", 0))
        texts = []
        if len(items) == 1:
            texts.append("描述建议：\n" + str(items[0]["suggestion"]).lstrip("\n"))
        else:
            for i, it in enumerate(items, start=1):
                texts.append(f"描述建议{i}：\n" + str(it["suggestion"]).lstrip("\n"))
        suggest_texts.setdefault(mc, []).extend(texts)

    # ---- reportDetails：按模块 sort 升序；模块内 NO_DATA -> NO_FILL(字段下标序) -> SUGGEST
    no_data_by_mod = {}
    for nd in fin["noData"]:
        no_data_by_mod.setdefault(nd["moduleCode"], nd["moduleName"])
    no_fill_by_mod = {}
    for nf in fin["noFill"]:
        no_fill_by_mod.setdefault(nf["moduleCode"], []).append(nf)

    report_details = []
    for m in sorted(fin["modules"], key=lambda x: x["sort"]):
        mc = m["moduleCode"]
        lines = []
        if mc in no_data_by_mod:
            lines.append(f"【{m['moduleName']}】可以为你加分哦，去完善")
        for nf in sorted(no_fill_by_mod.get(mc, []), key=lambda x: x["fieldIndex"]):
            lines.append(f"【{nf['dataFieldName']}】是简历中的重要信息，请完善")
        lines.extend(suggest_texts.get(mc, []))
        if not lines:
            continue
        report_details.append({
            "moduleCode": mc,
            "moduleName": m["moduleName"],
            "diagnoseNum": len(lines),
            "diagnoseList": lines,
        })

    report = {
        "resumeId": args.resume_id,
        "score": total,
        "beatPercent": beat_percent,
        "reportDetails": report_details,
    }
    _write_json(args.out, report)
    _log(f"报告已生成: {args.out}  score={total}  beatPercent={beat_percent}  模块数={len(report_details)}")


# ---------------------------------------------------------------------------

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="简历诊断确定性流水线")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare",
                       help="前置合并：照片检测 idPhoto + 生成填写模板（文本提取由模型 Read，不限定文件类型）")
    p.add_argument("--resume-type", required=True)
    p.add_argument("--resume-file", default=None, help="简历文件路径（仅用于照片检测，可省略）")
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_prepare)

    p = sub.add_parser("extract-text",
                       help="兜底文本提取：仅当模型 Read 读不了文件时调用（.docx/.doc）")
    p.add_argument("--resume-file", required=True, help="待提取文件路径")
    p.add_argument("--out", default="-", help="输出文本路径，传 - 走 stdout")
    p.set_defaults(fn=cmd_extract_text)

    p = sub.add_parser("emit-template")
    p.add_argument("--resume-type", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_emit_template)

    p = sub.add_parser("finalize")
    p.add_argument("--resume-type", required=True)
    p.add_argument("--filled", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_finalize)

    p = sub.add_parser("emit-llm-tasks",
                       help="组装单次批量 LLM 任务单（诊断 + 评分）")
    p.add_argument("--finalized", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_emit_llm_tasks)

    p = sub.add_parser("build-report")
    p.add_argument("--finalized", required=True)
    p.add_argument("--suggestions", default=None)
    p.add_argument("--gpt-score", default=None)
    p.add_argument("--resume-id", default="")
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_build_report)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
