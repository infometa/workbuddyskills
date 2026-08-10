#!/usr/bin/env python3
"""
review.py — 专家包形状层确定性检查 + ai_actions 输出

用法：
  python review.py <expert_dir> [--output-file <json>]

退出码：0=结构层无 BLOCKER；1=有结构层 BLOCKER
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from review_utils import (  # noqa: E402
    write_output_file, read_text_safe, read_json_safe,
    build_ai_action, build_finding, parse_version_tuple,
)

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ── 规范常量（仅作为脚本内部参考，不作为规则文本） ─────

# CODEBUDDY.md §十一 — 13 个标准分类 ID
VALID_CATEGORY_IDS = {
    "01-ProductDesign", "02-Engineering", "03-GameSpatial", "04-DataAI",
    "05-MarketingGrowth", "06-ContentCreative", "07-SalesCommerce",
    "08-FinanceInvestment", "09-OperationsHR", "10-ProjectQuality",
    "11-SecurityCompliance", "12-IndustryConsultant", "13-TencentZone",
}

# 不允许作为 agentName 的通用名（§3.3 / §十三-1）
AGENT_NAME_BLACKLIST = {"team-lead", "lead", "team", "agent", "expert", "main", "default"}

# 头像规范（§十）
AVATAR_MAX_BYTES = 500 * 1024
AVATAR_REQUIRED_SIZE = (512, 512)
AVATAR_VALID_EXTS = {".png", ".jpg", ".jpeg"}

# 金融类启发式触发关键词（plugin name）
FINANCE_PLUGIN_KEYWORDS = {
    "stock", "trading", "trade", "finance", "financial", "fund",
    "invest", "investment", "equity", "portfolio",
}

# 配置目录候选（外部提交包可能使用 .workbuddy-plugin/ 或 .codebuddy-plugin/）
PLUGIN_CONFIG_DIRS = [".codebuddy-plugin", ".workbuddy-plugin"]

# 文本扫描范围（用于安全/质量上下文预提取）
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".mjs", ".cjs", ".sh", ".bash", ".ps1", ".sql", ".html",
    ".htm", ".css", ".go", ".java", ".rb", ".php",
}
SCAN_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".review-cache", ".cache", "dist", "build"}

# 安全启发式：脚本只做表面检测，语义判断交给 security-hygiene-review ai_action
INTRANET_DOMAIN_RE = re.compile(r"(?i)\b[\w.-]*\.(?:woa|oa)\.com\b")
PERSONAL_PATH_RE = re.compile(r"(?i)(?:[A-Z]:\\\\Users\\\\[^\\\\\s]+|/Users/[^/\s]+|/home/[^/\s]+)")
PLATFORM_PATH_RE = re.compile(r"(?i)(?:\.cursor/|\.vscode/|\.idea/)")
CDN_LATEST_RE = re.compile(r"(?i)https?://(?:cdn\.jsdelivr\.net|unpkg\.com)/[^\s'\")]+@latest\b")
DANGEROUS_SHELL_RE = re.compile(r"(?i)(?:rm\s+-rf\s+[/~$*]|curl\s+[^|;\n]+\|\s*(?:sh|bash)|wget\s+[^|;\n]+\|\s*(?:sh|bash)|sudo\s+)")
CREDENTIAL_RE = re.compile(
    r"(?i)\b(?:password|passwd|secret|api[_-]?key|token|access[_-]?key|private[_-]?key)\b"
    r"\s*[:=]\s*[\"'](?!\s*(?:<|your-|xxx|xxxx|replace|todo|\$\{))[^\"'\s]{8,}[\"']"
)
ENV_VAR_RE = re.compile(r"(?:\$|export\s+|setx?\s+|\$env:)([A-Z][A-Z0-9_]{2,})")
SECRET_ENV_RE = re.compile(r"\b([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|API_KEY))\b")



# ── 工具函数 ──────────────────────────────────────────

def find_plugin_json(expert_dir: Path) -> tuple[Path | None, str]:
    """返回 (plugin.json 路径, 配置目录名)。"""
    for cand in PLUGIN_CONFIG_DIRS:
        p = expert_dir / cand / "plugin.json"
        if p.exists():
            return p, cand
    return None, ""


def parse_md_frontmatter(text: str) -> tuple[dict, str]:
    """简单解析 markdown frontmatter，返回 (frontmatter dict, body)。

    仅解析顶层 key:value 与 key:（多行嵌套块以原始字符串保留）。
    复杂结构由 LLM 阶段处理。
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_block = text[4:end]
    body = text[end + 5:]

    fm: dict = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def commit():
        nonlocal current_key, current_lines
        if current_key is not None:
            val = "\n".join(current_lines).strip()
            fm[current_key] = val
        current_key = None
        current_lines = []

    for line in fm_block.split("\n"):
        if not line:
            current_lines.append(line)
            continue
        if line[0] not in (" ", "\t", "-") and ":" in line:
            commit()
            k, _, v = line.partition(":")
            current_key = k.strip()
            current_lines = [v.strip()] if v.strip() else []
        else:
            current_lines.append(line)
    commit()
    return fm, body


def get_avatar_info(path: Path) -> dict:
    """返回头像文件的 size_bytes / dimensions / format / valid。"""
    info = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return info
    info["size_bytes"] = path.stat().st_size
    info["ext"] = path.suffix.lower()
    if HAS_PIL:
        try:
            with Image.open(path) as img:
                info["width"] = img.width
                info["height"] = img.height
                info["format"] = img.format
        except Exception as e:
            info["error"] = str(e)
    return info


# ── 检查器：A 组 一致性硬性 ───────────────────────────

def check_a_group(expert_dir: Path, plugin_json_path: Path | None,
                  config_dir: str, plugin_data: dict | None,
                  findings: list, ctx: dict) -> None:
    """A 组：一致性硬性（脚本可确定的部分）。"""

    # A01: plugin.json 存在
    if not plugin_json_path:
        findings.append(build_finding(
            "STRUCT-A01", "blocker", "missing_plugin_json",
            "plugin.json 不存在",
            evidence=f"在 {' / '.join(PLUGIN_CONFIG_DIRS)} 下均未找到 plugin.json",
            reference_doc="CODEBUDDY.md §三 / WorkBuddy专家开发规范.md §2",
            fix_hint="在配置目录下创建 plugin.json",
        ))
        return

    if plugin_data is None:
        findings.append(build_finding(
            "STRUCT-A01-2", "blocker", "invalid_plugin_json",
            "plugin.json 无法解析（JSON 格式错误）",
            evidence=f"{plugin_json_path}",
            target_file=str(plugin_json_path.relative_to(expert_dir)),
            reference_doc="CODEBUDDY.md §三",
            fix_hint="检查 JSON 语法（缺逗号、多余引号等）",
        ))
        return

    # A02: name 命名格式
    name = plugin_data.get("name", "")
    if not isinstance(name, str) or not re.match(r"^[a-z][a-z0-9-]*$", name):
        findings.append(build_finding(
            "STRUCT-A02", "blocker", "invalid_plugin_name",
            f"plugin.json `name` 格式不合法: {name!r}",
            evidence=f"name={name!r}",
            target_file=f"{config_dir}/plugin.json",
            reference_doc="CODEBUDDY.md §3.1",
            fix_hint="使用小写字母+连字符，如 my-expert",
        ))
    ctx["plugin_name"] = name

    # A03: version 格式
    version = plugin_data.get("version", "")
    if not parse_version_tuple(str(version)):
        findings.append(build_finding(
            "STRUCT-A03", "blocker", "invalid_version",
            f"plugin.json `version` 不是合法 semver: {version!r}",
            evidence=f"version={version!r}",
            target_file=f"{config_dir}/plugin.json",
            reference_doc="CODEBUDDY.md §3.1",
            fix_hint="使用纯数字 semver，如 1.0.0",
        ))

    # A04: expertType
    et = plugin_data.get("expertType", "")
    if et not in ("agent", "team", "plugin"):
        findings.append(build_finding(
            "STRUCT-A04", "blocker", "invalid_expert_type",
            f"plugin.json `expertType` 必须是 agent/team/plugin: {et!r}",
            target_file=f"{config_dir}/plugin.json",
            reference_doc="CODEBUDDY.md §3.3",
        ))
    ctx["expert_type"] = et

    # A05: agentName = 文件名 = MD frontmatter name
    agent_name = plugin_data.get("agentName")
    if et in ("agent", "team") and not agent_name:
        findings.append(build_finding(
            "STRUCT-A05", "blocker", "missing_agent_name",
            "agent/team 类型必须有 agentName 字段",
            target_file=f"{config_dir}/plugin.json",
            reference_doc="CODEBUDDY.md §3.3 / §十三-1",
        ))
    elif agent_name:
        agents_dir = expert_dir / "agents"
        md_path = agents_dir / f"{agent_name}.md"
        if not md_path.exists():
            findings.append(build_finding(
                "STRUCT-A05-2", "blocker", "agent_file_not_found",
                f"agentName={agent_name!r} 但 agents/{agent_name}.md 不存在",
                target_file=f"agents/{agent_name}.md",
                reference_doc="CODEBUDDY.md §十三-1",
            ))
        else:
            md_text = read_text_safe(md_path)
            fm, _ = parse_md_frontmatter(md_text)
            md_name = (fm.get("name") or "").strip().strip("\"'")
            if md_name and md_name != agent_name:
                findings.append(build_finding(
                    "STRUCT-A05-3", "blocker", "agent_name_mismatch",
                    f"agentName={agent_name!r} ≠ MD frontmatter name={md_name!r}",
                    evidence=f"plugin.json agentName={agent_name!r}; agents/{agent_name}.md frontmatter name={md_name!r}",
                    target_file=f"agents/{agent_name}.md",
                    reference_doc="CODEBUDDY.md §十三-1",
                ))

    # A06: agentName 业务语义（关键词黑名单 — 启发，最终由 LLM 判断）
    if agent_name and agent_name in AGENT_NAME_BLACKLIST:
        findings.append(build_finding(
            "STRUCT-A06", "blocker", "agent_name_too_generic",
            f"agentName={agent_name!r} 属于通用名，缺少业务语义",
            target_file=f"{config_dir}/plugin.json",
            reference_doc="CODEBUDDY.md §3.3 / §十三-1",
            fix_hint="改为具备业务含义的名字，如 huashu-data-pro-team-lead",
        ))

    # A07-A09: Team 型 members 字段
    if et == "team":
        team_info = plugin_data.get("teamInfo", {}) or {}
        member_agents = team_info.get("memberAgents", []) or []
        members = plugin_data.get("members", []) or []

        # A08: members 包含主理人
        lead_count = sum(
            1 for m in members
            if isinstance(m, dict) and m.get("role") == "lead"
        )
        if lead_count == 0:
            findings.append(build_finding(
                "STRUCT-A08", "blocker", "lead_not_in_members",
                "Team 型 members[] 中缺少 role=\"lead\" 的主理人条目",
                evidence=f"members count={len(members)}, lead count=0",
                target_file=f"{config_dir}/plugin.json",
                reference_doc="CODEBUDDY.md §3.6 / §十七",
                fix_hint="在 members[] 中追加主理人条目（role 设为 \"lead\"）",
            ))
        elif lead_count > 1:
            findings.append(build_finding(
                "STRUCT-A08-2", "blocker", "multiple_leads",
                f"Team 型 members[] 中有 {lead_count} 个 role=\"lead\"，应只有一个",
                target_file=f"{config_dir}/plugin.json",
                reference_doc="CODEBUDDY.md §3.6",
            ))

        # A09: members[].role 必须是字符串
        for i, m in enumerate(members):
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            if role is not None and not isinstance(role, str):
                findings.append(build_finding(
                    f"STRUCT-A09-{i}", "blocker", "member_role_type_mismatch",
                    f"members[{i}].role 类型应为字符串，实际为 {type(role).__name__}",
                    evidence=f"members[{i}].role={role!r}",
                    target_file=f"{config_dir}/plugin.json",
                    reference_doc="CODEBUDDY.md §3.6",
                    fix_hint='将 role 改为 "lead" 或 "member" 字符串',
                ))
            elif role is not None and role not in ("lead", "member"):
                findings.append(build_finding(
                    f"STRUCT-A09-V-{i}", "blocker", "member_role_invalid_value",
                    f"members[{i}].role={role!r} 必须是 \"lead\" 或 \"member\"",
                    target_file=f"{config_dir}/plugin.json",
                    reference_doc="CODEBUDDY.md §3.6",
                ))

        # A07: teamInfo.memberAgents[] ID = members[].id = 文件名
        member_ids = [m.get("id") for m in members if isinstance(m, dict)]
        for mid in member_ids:
            if not mid:
                continue
            mp = expert_dir / "agents" / f"{mid}.md"
            if not mp.exists():
                findings.append(build_finding(
                    f"STRUCT-A07-{mid}", "blocker", "member_file_missing",
                    f"members[].id={mid!r} 对应的 agents/{mid}.md 不存在",
                    target_file=f"agents/{mid}.md",
                    reference_doc="CODEBUDDY.md §十三-2",
                ))
        for ma in member_agents:
            if isinstance(ma, str) and ma not in member_ids and ma != agent_name:
                findings.append(build_finding(
                    f"STRUCT-A07-MA-{ma}", "blocker", "memberAgents_not_in_members",
                    f"teamInfo.memberAgents 中的 {ma!r} 未出现在 members[] 中",
                    target_file=f"{config_dir}/plugin.json",
                    reference_doc="CODEBUDDY.md §十三-2",
                ))

        # A10: settings.json agent = agentName
        settings_path = expert_dir / "settings.json"
        if settings_path.exists():
            sd = read_json_safe(settings_path)
            if isinstance(sd, dict):
                sa = sd.get("agent")
                if sa and agent_name and sa != agent_name:
                    findings.append(build_finding(
                        "STRUCT-A10", "blocker", "settings_agent_mismatch",
                        f"settings.json agent={sa!r} ≠ plugin.json agentName={agent_name!r}",
                        target_file="settings.json",
                        reference_doc="CODEBUDDY.md §八 / §十三-4",
                    ))
        else:
            findings.append(build_finding(
                "STRUCT-A10-2", "blocker", "settings_missing",
                "Team 型必须有 settings.json 指定主理人",
                target_file="settings.json",
                reference_doc="CODEBUDDY.md §八",
            ))

    # A11: avatar 路径存在
    avatar = plugin_data.get("avatar", "")
    if avatar:
        avatar_path = expert_dir / avatar
        if not avatar_path.exists():
            findings.append(build_finding(
                "STRUCT-A11", "blocker", "avatar_not_found",
                f"plugin.json avatar={avatar!r} 指向的文件不存在",
                target_file=avatar,
                reference_doc="CODEBUDDY.md §十三-3",
            ))

    # A12: skills[] 路径下存在 SKILL.md
    skills = plugin_data.get("skills", []) or []
    for s in skills:
        if not isinstance(s, str):
            continue
        sp = expert_dir / s.lstrip("./")
        sm = sp / "SKILL.md"
        if not sm.exists():
            findings.append(build_finding(
                f"STRUCT-A12-{s}", "blocker", "skill_md_missing",
                f"skills[] 中的 {s!r} 路径下缺少 SKILL.md",
                target_file=str((sm).relative_to(expert_dir)) if sm.is_relative_to(expert_dir) else str(sm),
                reference_doc="CODEBUDDY.md §十三-5",
            ))

    # A14: agents/、skills/、avatars/ 在插件根目录（不在配置目录里）
    config_path = expert_dir / config_dir
    for sub in ("agents", "skills", "avatars"):
        if (config_path / sub).exists():
            findings.append(build_finding(
                f"STRUCT-A14-{sub}", "blocker", "subdir_in_config_dir",
                f"`{sub}/` 不应放在 {config_dir}/ 目录里，应放在插件根目录",
                target_file=f"{config_dir}/{sub}",
                reference_doc="CODEBUDDY.md §二 / §十七",
            ))

    # A15: agents/ 下只有 agent 定义文件（带 frontmatter 的 .md）
    agents_dir = expert_dir / "agents"
    if agents_dir.is_dir():
        for md in agents_dir.glob("*.md"):
            text = read_text_safe(md)
            if not text.startswith("---\n"):
                findings.append(build_finding(
                    f"STRUCT-A15-{md.stem}", "blocker", "agent_md_no_frontmatter",
                    f"agents/{md.name} 缺少 YAML frontmatter（不是 agent 定义文件）",
                    target_file=f"agents/{md.name}",
                    reference_doc="CODEBUDDY.md §十七",
                    fix_hint="如果是策略/规则/模板文档，应放到 references/ 而不是 agents/",
                ))

    # A16: 配置目录下只有 plugin.json
    if config_path.is_dir():
        for sub in config_path.iterdir():
            if sub.name != "plugin.json":
                findings.append(build_finding(
                    f"STRUCT-A16-{sub.name}", "blocker", "extra_file_in_config_dir",
                    f"{config_dir}/ 下不应有 {sub.name}（仅允许 plugin.json）",
                    target_file=f"{config_dir}/{sub.name}",
                    reference_doc="CODEBUDDY.md §十七",
                ))

    # A17: 所有 JSON 文件可解析（plugin.json 已检查；额外检查 settings.json）
    for json_path in [expert_dir / "settings.json"]:
        if json_path.exists() and read_json_safe(json_path) is None:
            findings.append(build_finding(
                f"STRUCT-A17-{json_path.name}", "blocker", "invalid_json",
                f"{json_path.name} 无法解析为 JSON",
                target_file=json_path.name,
                reference_doc="CODEBUDDY.md §十七",
            ))


# ── 检查器：C 组 展示字段 ─────────────────────────────

def check_c_group(plugin_data: dict, config_dir: str, expert_type: str,
                  findings: list, actions: list) -> None:
    """C 组：展示字段质量。"""

    # C01: displayName.zh / .en 必填
    dn = plugin_data.get("displayName") or {}
    if expert_type in ("agent", "team"):
        if not isinstance(dn, dict) or not dn.get("zh") or not dn.get("en"):
            findings.append(build_finding(
                "STRUCT-C01", "blocker", "missing_display_name",
                "agent/team 类型必须有 displayName.zh 和 displayName.en",
                target_file=f"{config_dir}/plugin.json",
                reference_doc="CODEBUDDY.md §3.5",
            ))

    # C04: categoryId 合法
    cid = plugin_data.get("categoryId", "")
    if expert_type in ("agent", "team"):
        if cid not in VALID_CATEGORY_IDS:
            findings.append(build_finding(
                "STRUCT-C04", "blocker", "invalid_category_id",
                f"categoryId={cid!r} 不在 §十一 标准分类中",
                target_file=f"{config_dir}/plugin.json",
                reference_doc="CODEBUDDY.md §十一",
                fix_hint=f"使用 13 个标准分类之一: {sorted(VALID_CATEGORY_IDS)}",

            ))

    # C02 / C03 / C05 / C07 → ai_actions（语义判断）
    actions.append(build_ai_action(
        "AI-C02", "display-text-quality",
        "请阅读 CODEBUDDY.md §3.5 与 WorkBuddy专家开发规范.md §3.3，校验："
        "(1) displayDescription.zh 字数是否在 40-50 之间；"
        "(2) defaultInitPrompt.zh 是否与 quickPrompts[0].zh 完全一致；"
        "(3) tags 数量是否在 3-5 之间。"
        "不通过项列入 SUGGESTION。",
        priority="recommended",
        target_file=f"{config_dir}/plugin.json",
        reference_doc="CODEBUDDY.md §3.5 / WorkBuddy §3.3",
        context={"plugin_data_subset": {
            "displayDescription": plugin_data.get("displayDescription"),
            "defaultInitPrompt": plugin_data.get("defaultInitPrompt"),
            "quickPrompts": plugin_data.get("quickPrompts"),
            "tags": plugin_data.get("tags"),
        }},
    ))

    # C08 → 平台能力真实性检查（BLOCKER 级）
    actions.append(build_ai_action(
        "AI-C08", "platform-claim-check",
        "检查 displayDescription、description（plugin.json 与 agent frontmatter）以及 agent prompt 正文中，"
        "是否包含与 CodeBuddy/WorkBuddy 平台实际运行方式不符的技术承诺。"
        "平台事实：模型推理通过云端进行，专家不具备纯本地离线运行能力。"
        "需检测的违规关键词/短语包括但不限于："
        "「本地AI」「本地模型」「本地推理」「全程不联网」「离线运行」「不上云」「零数据外传」"
        "「never uploaded」「local inference」「offline」「runs locally」等。"
        "对文件操作本身在本地进行的描述（如'直接操作本地文件'）是准确的，不算违规。"
        "发现违规项列入 BLOCKER，标注具体文件位置和修复建议。",
        priority="recommended",
        target_file=f"{config_dir}/plugin.json",
        reference_doc="平台事实：CodeBuddy/WorkBuddy 模型推理均通过云端进行",
        context={"plugin_data_subset": {
            "description": plugin_data.get("description"),
            "displayDescription": plugin_data.get("displayDescription"),
        }},
    ))




# ── 检查器：D 组 头像 ─────────────────────────────────

def check_d_group(expert_dir: Path, plugin_data: dict, expert_type: str,
                  findings: list) -> None:
    """D 组：头像规范。"""
    avatar = plugin_data.get("avatar", "")
    if not avatar:
        return
    avatar_path = expert_dir / avatar
    info = get_avatar_info(avatar_path)
    if not info.get("exists"):
        return  # 已在 A11 报告

    # D01 格式
    if info.get("ext") not in AVATAR_VALID_EXTS:
        findings.append(build_finding(
            "STRUCT-D01", "blocker", "avatar_format_invalid",
            f"头像格式 {info.get('ext')} 不被允许（仅 PNG/JPG）",
            target_file=avatar,
            reference_doc="CODEBUDDY.md §十",
        ))

    # D02 尺寸
    if HAS_PIL and "width" in info:
        if (info["width"], info["height"]) != AVATAR_REQUIRED_SIZE:
            findings.append(build_finding(
                "STRUCT-D02", "blocker", "avatar_size_invalid",
                f"头像尺寸 {info['width']}x{info['height']} 不是 512x512",
                target_file=avatar,
                reference_doc="CODEBUDDY.md §十",
            ))

    # D03 大小
    if info.get("size_bytes", 0) > AVATAR_MAX_BYTES:
        findings.append(build_finding(
            "STRUCT-D03", "blocker", "avatar_oversize",
            f"头像大小 {info['size_bytes']} bytes 超过 500KB 上限",
            target_file=avatar,
            reference_doc="CODEBUDDY.md §十",
        ))

    # D04 Team 型成员头像
    if expert_type == "team":
        members = plugin_data.get("members", []) or []
        for m in members:
            if not isinstance(m, dict):
                continue
            mav = m.get("avatar", "")
            if not mav:
                findings.append(build_finding(
                    f"STRUCT-D04-{m.get('id', '?')}", "blocker", "member_avatar_missing",
                    f"成员 {m.get('id', '?')} 缺少 avatar 字段",
                    target_file="plugin.json",
                    reference_doc="CODEBUDDY.md §十",
                ))
                continue
            mp = expert_dir / mav
            if not mp.exists():
                findings.append(build_finding(
                    f"STRUCT-D04-FILE-{m.get('id', '?')}", "blocker",
                    "member_avatar_file_not_found",
                    f"成员 {m.get('id', '?')} 头像 {mav!r} 文件不存在",
                    target_file=mav,
                    reference_doc="CODEBUDDY.md §十",
                ))


# ── 检查器：B 组 Team Prompt（输出 ai_actions） ─────────

def emit_team_actions(expert_dir: Path, plugin_data: dict, actions: list) -> None:
    """Team 型主理人/成员 prompt 检查 — 全部走 ai_actions（LLM 读规范判断）。"""
    if plugin_data.get("expertType") != "team":
        return

    agent_name = plugin_data.get("agentName", "")
    members = plugin_data.get("members", []) or []
    team_info = plugin_data.get("teamInfo", {}) or {}
    # 成员 ID 来源：优先 teamInfo.memberAgents（更稳定），回退到 members[role=member]
    # 即使 members[].role 字段类型/值不规范（已在 A08/A09 报 BLOCKER），仍能继续校验成员 prompt
    ma_list = team_info.get("memberAgents", []) or []
    if ma_list:
        member_ids = [x for x in ma_list if isinstance(x, str) and x != agent_name]
    else:
        member_ids = [
            m.get("id") for m in members
            if isinstance(m, dict) and m.get("id") and m.get("id") != agent_name
        ]

    if agent_name:
        actions.append(build_ai_action(
            "AI-B01", "team-rule-check",
            "请阅读 CODEBUDDY.md §4.4 与 WorkBuddy专家开发规范.md §5.2.1，"
            "对照 target_file 逐项判断主理人 prompt 是否包含："
            "(1) 团队协作机制（铁律）章节；"
            "(2) 4 条协作铁律（建立团队 / 调度成员 / 消息中转 / 成员结论为准）；"
            "(3) 5 条红线（禁跳 TeamCreate / 禁代写成员 / 禁跳阶段 / 禁直连 / 禁 spawn 自己）；"
            "(4) 协作规则（TeamCreate→Agent spawn→SendMessage 回传 流程，含 name 参数）。"
            "缺失任一项均列入 BLOCKER。",
            priority="required",
                target_file=f"agents/{agent_name}.md",
            reference_doc="CODEBUDDY.md §4.4 / WorkBuddy专家开发规范.md §5.2.1",
            context={"agent_name": agent_name, "team_size": len(members)},
        ))



    for mid in member_ids:
        if not mid:
            continue
        actions.append(build_ai_action(
            f"AI-B07-{mid}", "member-rule-check",
            "请阅读 CODEBUDDY.md §4.5.3 与 WorkBuddy §5.3，对照 target_file 判断成员 prompt 是否包含："
            "(1) 角色定义；"
            "(2) 擅长领域（3-5 个具体能力点）；"
            "(3) 分析框架；"
            "(4) 数据获取方式；"
            "(5) 结构化输出模板。"
            "前 5 项缺失列入 BLOCKER。"
            "(6) 通过 SendMessage 将结果回传给主理人的明确说明，缺失时列入 SUGGESTION。",
            priority="required",
                target_file=f"agents/{mid}.md",
            reference_doc="CODEBUDDY.md §4.5.3 / WorkBuddy §5.3",
            context={"member_id": mid},
        ))




# ── 检查器：金融类启发式 ──────────────────────────────

def detect_finance_flag(plugin_data: dict, plugin_name: str) -> bool:
    if plugin_data.get("categoryId") == "08-FinanceInvestment":
        return True
    name_lower = (plugin_name or "").lower()
    return any(kw in name_lower for kw in FINANCE_PLUGIN_KEYWORDS)


def emit_finance_actions(plugin_data: dict, plugin_name: str, expert_dir: Path,
                          actions: list) -> None:
    config_dir = ".codebuddy-plugin" if (expert_dir / ".codebuddy-plugin").exists() else ".workbuddy-plugin"
    actions.append(build_ai_action(
        "AI-E01", "finance-compliance",
        "本专家被启发式识别为金融类。请阅读 CODEBUDDY.md §十八 与 §17，逐项判断："
        "(1) defaultInitPrompt 是否含「能不能买/该买吗/推荐」等决策类措辞 → BLOCKER；"
        "(2) displayDescription、description 是否暗示投资建议/买卖信号/操作路线图 → BLOCKER；"
        "(3) 主理人/成员 prompt 是否要求输出末尾包含 4 要素免责声明（AI 生成 + 公开信息 + 不构成投资建议 + 不构成个股推荐）→ BLOCKER；"
        "(4) 引用行情/财务/资金时是否标注数据来源 → SUGGESTION。",
        priority="required",
        target_file=f"{config_dir}/plugin.json",
        reference_doc="CODEBUDDY.md §十八 / §17",
        context={"plugin_name": plugin_name},
    ))





# ── Agent MD frontmatter 完整性（C07） ────────────────

def emit_prompt_completeness(expert_dir: Path, plugin_data: dict,
                              actions: list) -> None:
    agents_dir = expert_dir / "agents"
    if not agents_dir.is_dir():
        return
    targets = []
    for md in agents_dir.glob("*.md"):
        text = read_text_safe(md)
        fm, _ = parse_md_frontmatter(text)
        targets.append({
            "file": f"agents/{md.name}",
            "has_displayName": "displayName" in fm,
            "has_profession": "profession" in fm,
            "name": fm.get("name"),
        })
    if targets:
        actions.append(build_ai_action(
            "AI-C07", "prompt-completeness",
            "请阅读 CODEBUDDY.md §4.1 与 WorkBuddy §4.2，逐个检查 context.targets 中每个 agent.md "
            "的 frontmatter 是否包含 displayName 和 profession 字段。"
            "缺失项列入 SUGGESTION。",
            priority="required",
                reference_doc="CODEBUDDY.md §4.1 / WorkBuddy专家开发规范.md §4.2",
            context={"targets": targets},
        ))


# ── G/Q 组：安全、依赖引导、深度质量上下文预提取 ───────

def iter_review_text_files(root: Path) -> list[Path]:
    """遍历专家包内可扫描的文本文件，跳过缓存和依赖目录。"""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCAN_SKIP_DIRS]
        base = Path(dirpath)
        for fn in filenames:
            p = base / fn
            if p.suffix.lower() in TEXT_SUFFIXES:
                out.append(p)
    return out


def is_doc_context(line: str) -> bool:
    """识别明显的文档/示例上下文，降低安全启发式误报。"""
    stripped = line.strip()
    lower = stripped.lower()
    if not stripped:
        return True
    if stripped.startswith((">", "|", "- ", "* ", "#", "```")):
        return True
    if any(ph in lower for ph in ["<token", "<secret", "<password", "your-", "xxx", "xxxx", "todo", "example", "示例", "占位"]):
        return True
    if "${" in stripped or "$ENV" in stripped:

        return True
    return False


def add_capped_sample(bucket: list, item: dict, limit: int = 20) -> None:
    if len(bucket) < limit:
        bucket.append(item)


def check_security_hygiene(expert_dir: Path, findings: list) -> dict:
    """安全与通用性启发式扫描：凭据硬编码直接阻断，其余交给 LLM 语义复核。"""
    context = {
        "text_files_scanned": 0,
        "credential_blockers": [],
        "intranet_domains": [],
        "personal_paths": [],
        "platform_path_residue": [],
        "cdn_latest": [],
        "dangerous_shell": [],
    }

    for fpath in iter_review_text_files(expert_dir):
        rel = str(fpath.relative_to(expert_dir)).replace("\\", "/")
        text = read_text_safe(fpath)
        context["text_files_scanned"] += 1
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if is_doc_context(stripped):
                continue
            sample = {"file": rel, "line": line_no, "content": stripped[:160]}

            if CREDENTIAL_RE.search(line):
                add_capped_sample(context["credential_blockers"], sample)
                findings.append(build_finding(
                    f"STRUCT-G01-{len(context['credential_blockers'])}", "blocker", "hardcoded_credential",
                    "检测到疑似硬编码凭据",
                    evidence=f"{rel}:{line_no} {stripped[:120]}",
                    target_file=rel,
                    reference_doc="安全规则：High-Priority Secure Coding Standards / CODEBUDDY.md §十七",
                    fix_hint="改为环境变量、配置占位符或运行时凭据注入；不要在专家包中提交真实密钥",
                ))
            if INTRANET_DOMAIN_RE.search(line):
                add_capped_sample(context["intranet_domains"], sample)
            if PERSONAL_PATH_RE.search(line):
                add_capped_sample(context["personal_paths"], sample)
            if PLATFORM_PATH_RE.search(line):
                add_capped_sample(context["platform_path_residue"], sample)
            if CDN_LATEST_RE.search(line):
                add_capped_sample(context["cdn_latest"], sample)
            if DANGEROUS_SHELL_RE.search(line):
                add_capped_sample(context["dangerous_shell"], sample)

    suggestion_specs = [
        ("STRUCT-G02", "intranet_domain", "检测到内网域名引用", "intranet_domains"),
        ("STRUCT-G03", "personal_path", "检测到开发者个人路径残留", "personal_paths"),
        ("STRUCT-G04", "platform_path", "检测到其他 IDE/平台路径残留", "platform_path_residue"),
        ("STRUCT-G05", "cdn_latest", "检测到 CDN @latest 未锁定版本", "cdn_latest"),
        ("STRUCT-G06", "dangerous_shell", "检测到高风险 shell 命令模式", "dangerous_shell"),
    ]
    for finding_id, finding_type, title, key in suggestion_specs:
        samples = context[key]
        if samples:
            first = samples[0]
            findings.append(build_finding(
                finding_id, "suggestion", finding_type, title,
                evidence=f"{first['file']}:{first['line']} {first['content']}",
                target_file=first["file"],
                reference_doc="安全规则：High-Priority Secure Coding Standards / CODEBUDDY.md §十七",
                fix_hint="由 LLM 执行 security-hygiene-review 复核语义：确认是否为必要依赖、是否需公网降级/版本锁定/相对路径/安全替代方案",
            ))
    return context


def extract_dependency_context(expert_dir: Path) -> dict:
    """预提取外部依赖与安装/配置引导上下文。"""
    bin_dir = expert_dir / "bin"
    scripts_dirs = [p for p in expert_dir.rglob("scripts") if p.is_dir() and all(part not in SCAN_SKIP_DIRS for part in p.relative_to(expert_dir).parts)]
    bin_files = [str(p.relative_to(expert_dir)).replace("\\", "/") for p in bin_dir.rglob("*") if p.is_file()] if bin_dir.is_dir() else []
    script_files = []
    for sd in scripts_dirs:
        for p in sd.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES:
                script_files.append(str(p.relative_to(expert_dir)).replace("\\", "/"))

    env_vars: set[str] = set()
    install_commands: set[str] = set()
    has_setup_section = False
    docs = []
    for fpath in iter_review_text_files(expert_dir):
        rel = str(fpath.relative_to(expert_dir)).replace("\\", "/")
        text = read_text_safe(fpath)
        if fpath.suffix.lower() == ".md":
            docs.append(rel)
            lower = text.lower()
            if any(k in lower for k in ["## 安装", "## install", "## setup", "## 环境配置", "## 前提条件", "## prerequisites", "api key", "环境变量"]):
                has_setup_section = True
        env_vars.update(ENV_VAR_RE.findall(text))
        env_vars.update(SECRET_ENV_RE.findall(text))
        for m in re.finditer(r"(?:pip|npm|pnpm|yarn|brew|apt|cargo|go)\s+install\s+[^\n`]+", text, re.IGNORECASE):
            install_commands.add(m.group(0).strip()[:160])

    needs_dependency_guide = bool(bin_files or script_files or env_vars)
    return {
        "bin_files": bin_files[:20],
        "script_files": script_files[:30],
        "mentioned_env_vars": sorted(env_vars)[:30],
        "install_commands": sorted(install_commands)[:20],
        "documentation_files": docs[:20],
        "has_setup_section": has_setup_section,
        "needs_dependency_guide": needs_dependency_guide,
    }


def extract_deep_review_context(expert_dir: Path, plugin_data: dict | None) -> dict:
    """为 11 维度深度质量评审预提取结构化上下文。"""
    file_tree = []
    md_files = []
    agent_files = []
    skill_dirs = []
    total_files = 0
    total_md_chars = 0

    for p in expert_dir.rglob("*"):
        if not p.is_file() or any(part in SCAN_SKIP_DIRS for part in p.relative_to(expert_dir).parts):
            continue
        total_files += 1
        rel = str(p.relative_to(expert_dir)).replace("\\", "/")
        size_kb = round(p.stat().st_size / 1024, 1)
        file_tree.append({"path": rel, "size_kb": size_kb})
        if p.suffix.lower() == ".md":
            text = read_text_safe(p)
            total_md_chars += len(text)
            headings = re.findall(r"^(#{1,4})\s+(.+)$", text, re.MULTILINE)
            md_files.append({
                "path": rel,
                "chars": len(text),
                "headings": [{"level": len(h[0]), "title": h[1].strip()} for h in headings[:20]],
            })
            if rel.startswith("agents/"):
                fm, body = parse_md_frontmatter(text)
                agent_files.append({
                    "path": rel,
                    "name": fm.get("name"),
                    "description_len": len(str(fm.get("description", ""))),
                    "body_chars": len(body),
                    "has_send_message": "SendMessage" in body or "send_message" in body,
                })
        if rel.startswith("skills/") and rel.endswith("/SKILL.md"):
            skill_dirs.append(str(Path(rel).parent).replace("\\", "/"))

    file_tree.sort(key=lambda x: x["size_kb"], reverse=True)
    md_files.sort(key=lambda x: x["chars"], reverse=True)
    plugin_summary = {}
    if isinstance(plugin_data, dict):
        plugin_summary = {
            "name": plugin_data.get("name"),
            "expertType": plugin_data.get("expertType"),
            "agentName": plugin_data.get("agentName"),
            "categoryId": plugin_data.get("categoryId"),
            "agents_count": len(plugin_data.get("agents") or []),
            "skills_count": len(plugin_data.get("skills") or []),
            "members_count": len(plugin_data.get("members") or []),
            "tags_count": len(plugin_data.get("tags") or []),
            "quickPrompts_count": len(plugin_data.get("quickPrompts") or []),
        }

    skip_deep_review = total_md_chars < 1024
    return {
        "total_files": total_files,
        "total_md_chars": total_md_chars,
        "file_tree_top": file_tree[:20],
        "md_files_top": md_files[:10],
        "agent_files": agent_files,
        "skill_dirs": sorted(set(skill_dirs))[:20],
        "plugin_summary": plugin_summary,
        "skip_deep_review": skip_deep_review,
        "skip_reason": f"Markdown 总量仅 {total_md_chars} 字符，内容过少，深度评审无意义" if skip_deep_review else "",
    }


def emit_quality_security_actions(expert_dir: Path, plugin_data: dict | None,
                                  findings: list, actions: list) -> dict:
    """参考 skill-reviewer v3.7：输出安全、依赖引导、深度质量评审 ai_actions。"""
    security_context = check_security_hygiene(expert_dir, findings)
    dependency_context = extract_dependency_context(expert_dir)
    deep_review_context = extract_deep_review_context(expert_dir, plugin_data)

    actions.append(build_ai_action(
        "AI-G01", "security-hygiene-review",
        "请基于 context 中的启发式扫描结果，并阅读相关 target 文件，复核专家包安全与通用性："
        "(1) 是否存在真实凭据/密钥硬编码；(2) scripts/bin 是否有越权读取、数据外传或危险命令；"
        "(3) 内网域名是否有公网降级或明确适用范围；(4) 个人路径、平台路径、CDN @latest 是否需要修复。"
        "真实凭据硬编码列 BLOCKER；其余按影响列 SUGGESTION，并给出可执行修复方案。",
        priority="recommended",
        reference_doc="安全规则：High-Priority Secure Coding Standards / CODEBUDDY.md §十七",
        context=security_context,
    ))

    if dependency_context["needs_dependency_guide"]:
        actions.append(build_ai_action(
            "AI-G02", "dependency-guide-check",
            "检测到 bin/scripts/环境变量等运行时依赖。请阅读 README.md、skills/*/SKILL.md、agents/*.md，"
            "判断是否说明了安装命令、版本要求、环境变量名、获取方式和验证命令。"
            "关键依赖完全没有引导时列 BLOCKER；部分缺失列 SUGGESTION。",
            priority="recommended",
                reference_doc="CODEBUDDY.md §五 / §六 / §十七",
            context=dependency_context,
        ))

    actions.append(build_ai_action(
        "AI-Q01", "deep-quality-review",
        "请执行专家包深度质量评审。若 context.skip_deep_review=true，仅在报告中说明跳过原因；"
        "否则必须阅读核心 agents/*.md、README.md 与 skills/*/SKILL.md，按 11 维度输出建议级结论："
        "AI 可执行性、路由/触发清晰度、上下文效率、容错降级、角色边界、团队编排、"
        "用户体验、受众适配、可移植性、领域准确性、可维护性。所有结论均为 SUGGESTION，不阻断。",
        priority="recommended",
        reference_doc="references/review-checklist.md §深度质量评审 / skill-reviewer v3.7.1 11 维度",
        context=deep_review_context,
    ))

    return {
        "security_hygiene": security_context,
        "dependency_context": dependency_context,
        "deep_review_context": deep_review_context,
    }


# ── 主入口 ────────────────────────────────────────────

def review_expert(expert_dir: Path) -> dict:
    findings: list = []
    actions: list = []
    ctx: dict = {}

    plugin_json_path, config_dir = find_plugin_json(expert_dir)
    plugin_data = read_json_safe(plugin_json_path) if plugin_json_path else None

    # ── 提取 author 信息，写入报告上下文 ──
    author_info: dict = {}
    if isinstance(plugin_data, dict):
        raw_author = plugin_data.get("author")
        if isinstance(raw_author, dict):
            author_info = {
                "name": raw_author.get("name", ""),
                "email": raw_author.get("email", ""),
            }
        elif isinstance(raw_author, str):
            author_info = {"name": raw_author, "email": ""}



    # A 组：一致性硬性
    check_a_group(expert_dir, plugin_json_path, config_dir, plugin_data, findings, ctx)

    # 后续检查依赖 plugin_data 可用
    if isinstance(plugin_data, dict):
        expert_type = plugin_data.get("expertType", "")
        plugin_name = plugin_data.get("name", expert_dir.name)

        # C 组：展示字段
        check_c_group(plugin_data, config_dir, expert_type, findings, actions)

        # D 组：头像
        check_d_group(expert_dir, plugin_data, expert_type, findings)

        # B 组（Team prompt）→ ai_actions
        emit_team_actions(expert_dir, plugin_data, actions)

        # C07：Agent MD frontmatter 完整性
        emit_prompt_completeness(expert_dir, plugin_data, actions)

        # 金融类启发式
        finance_flag = detect_finance_flag(plugin_data, plugin_name)
        if finance_flag:
            emit_finance_actions(plugin_data, plugin_name, expert_dir, actions)

    else:
        expert_type = ""
        plugin_name = expert_dir.name
        finance_flag = False

    # G/Q 组：安全、依赖引导、深度质量评审（参考 skill-reviewer v3.7）
    extended_context = emit_quality_security_actions(expert_dir, plugin_data, findings, actions)


    executable_actions = []
    for a in actions:
        a = dict(a)
        a["execute"] = True
        executable_actions.append(a)

    blocker_count = sum(1 for f in findings if f["severity"] == "blocker")

    # 报告骨架
    report_skeleton = build_report_skeleton(
        plugin_name, expert_type,
        findings, executable_actions, finance_flag,
    )

    return {
        "expert_dir": str(expert_dir),
        "plugin_name": plugin_name,
        "expert_type": expert_type,
        "author_info": author_info,
        "structure_findings": findings,
        "ai_actions": executable_actions,
        "finance_flag": finance_flag,
        "extended_review_context": extended_context,
        "summary": {
            "structure_blockers": blocker_count,
            "structure_total": len(findings),
            "ai_actions_total": len(executable_actions),
            "ai_actions_to_execute": len(executable_actions),
            "security_samples": sum(
                len(v) for v in extended_context.get("security_hygiene", {}).values()
                if isinstance(v, list)
            ),
            "dependency_guide_needed": extended_context.get("dependency_context", {}).get("needs_dependency_guide", False),
            "deep_review_skip": extended_context.get("deep_review_context", {}).get("skip_deep_review", False),
        },
        "report_skeleton": report_skeleton,

    }


def build_report_skeleton(plugin_name: str, expert_type: str,
                          findings: list, actions: list,
                          finance_flag: bool) -> str:
    """生成 Markdown 报告骨架（LLM 在最终阶段填充每条详情）。"""
    blockers = [f for f in findings if f["severity"] == "blocker"]
    suggestions = [f for f in findings if f["severity"] == "suggestion"]

    lines = []
    lines.append(f"# 专家包审查报告 - {plugin_name}\n")
    lines.append(f"> 专家类型：{expert_type}")
    if finance_flag:
        lines.append("> ⚠️ 金融类启发式已触发，需校验 §十八 合规要求")
    lines.append("\n---\n")
    lines.append("## 一、总体结论\n")
    lines.append(
        "**整体结论：<可上架 | 需修复后方可上架>**\n\n"
        f"- 结构层 BLOCKER：{len(blockers)} 个\n"
        f"- 结构层 SUGGESTION：{len(suggestions)} 个\n"
        f"- 待 LLM 校验的规范项（ai_actions）：{sum(1 for a in actions if a.get('execute'))} 项\n"
    )
    lines.append("\n## 二、阻断问题（BLOCKER）\n")
    lines.append("> LLM 填充：结构层 BLOCKER 已由脚本检测；规范层 BLOCKER 由 ai_actions 执行后追加\n")
    for f in blockers:
        lines.append(f"### {f['id']} ❌ {f['title']}\n")
        if f.get("evidence"):
            lines.append(f"- **现状**: {f['evidence']}")
        if f.get("target_file"):
            lines.append(f"- **位置**: `{f['target_file']}`")
        if f.get("reference_doc"):
            lines.append(f"- **规范依据**: {f['reference_doc']}")
        if f.get("fix_hint"):
            lines.append(f"- **修复方案**: {f['fix_hint']}")
        lines.append("")

    lines.append("## 三、建议改进项（SUGGESTION）\n")
    lines.append("> LLM 填充：包含结构层 SUGGESTION、security-hygiene-review、dependency-guide-check 等结论\n")

    lines.append("## 四、深度质量评审\n")
    lines.append("> LLM 填充：按 11 维度输出建议级评审；若 deep_review_context.skip_deep_review=true，说明跳过原因\n")

    lines.append("## 五、修复优先级表\n")
    lines.append("> LLM 填充表格\n")

    lines.append("## 六、亮点（可选）\n")
    lines.append("> LLM 填充\n")


    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="专家包审查（形状层确定性 + ai_actions 输出）")
    parser.add_argument("expert_dir", help="专家包目录路径")
    parser.add_argument("--output-file", help="输出 JSON 路径")
    parser.add_argument("--save-skeleton", help="可选：把 report_skeleton 单独保存为 .md 文件")
    args = parser.parse_args()

    expert_dir = Path(args.expert_dir).resolve()
    if not expert_dir.is_dir():
        print(f"[ERROR] expert_dir 不是有效目录: {expert_dir}", file=sys.stderr)
        sys.exit(2)

    result = review_expert(expert_dir)
    plugin_name = result["plugin_name"]

    if args.save_skeleton:
        Path(args.save_skeleton).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save_skeleton).write_text(result["report_skeleton"], encoding="utf-8")

    summary_str = (
        f"review {plugin_name}: "
        f"structure_blockers={result['summary']['structure_blockers']}, "
        f"ai_actions_to_execute={result['summary']['ai_actions_to_execute']}"
    )

    write_output_file(args.output_file, result, stdout_summary=summary_str)
    sys.exit(1 if result["summary"]["structure_blockers"] > 0 else 0)


if __name__ == "__main__":
    main()
