#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


EXPERT_MANAGER = Path("/Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/expert-manager")
APPROVED_ROUTES = {
    "layer2-stock-brief",
    "layer2-stock-narrative-valuation",
    "layer2-industry-brief",
    "layer2-announcement-brief",
    "layer2-research-digest",
    "layer2-policy-event-brief",
    "layer2-html-research-playbook",
    "layer2-evidence-ledger",
    "layer2-transmission-chain-builder",
    "layer2-research-red-team",
    "layer2-research-visuals",
}
APPROVED_CAPABILITIES = {"fin-data-query", "doc-search", "fin-graph", "same-boat"}
APPROVED_LAYER1_SKILLS = {
    "layer1-doc-search",
    "layer1-fin-data",
    "layer1-fin-graph",
    "layer1-same-boat",
}
APPROVED_LAYER3_SKILLS = {
    "layer3-event-interpretation",
    "layer3-industry-windvane",
}
CORE_LAYER1_SKILL_PATHS = [f"./skills/{skill}" for skill in sorted(APPROVED_LAYER1_SKILLS)]
CORE_LAYER2_SKILL_PATHS = [f"./skills/{route}" for route in sorted(APPROVED_ROUTES)]
CORE_LAYER3_SKILL_PATHS = [f"./skills/{skill}" for skill in sorted(APPROVED_LAYER3_SKILLS)]
EXPECTED_SKILL_PATHS = [
    "./skills/fin-mcp-gateway",
    *CORE_LAYER1_SKILL_PATHS,
    *CORE_LAYER2_SKILL_PATHS,
    *CORE_LAYER3_SKILL_PATHS,
]
FORBIDDEN_LAYER1_PREFIXES = ("layer1-sales-", "layer1-pa-")
FORBIDDEN_LAYER2_PREFIXES = ("layer2-sales-", "layer2-care-", "layer2-pa-")
FORBIDDEN_LAYER3_PREFIXES = ("layer3-sales-", "layer3-care-", "layer3-pa-")
SEMVER_RE = re.compile(r"^[0-9]+[.][0-9]+[.][0-9]+(?:[-.][0-9A-Za-z.-]+)?$")
WORKBUDDY_PLUGINS_DIR = Path.home() / ".workbuddy/plugins/marketplaces/my-experts/plugins"
EXCLUDED_DOC_ASSET_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".psd", ".sketch", ".webp"}
PACKAGED_PATH_EXCLUDED_PARTS = {
    ".git",
    ".gitea",
    ".mypy_cache",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "codex",
    "node_modules",
    "dist",
    "inspirations",
    "npm",
    "reference-materials",
    "tests",
}
EXPECTED_SPREADSHEET_CAPABILITY_STATUS = {
    ("同舟小程序", "行业要闻智能解读"): "launch",
    ("同舟小程序", "行业关键数据/指标一览"): "launch",
    ("同舟小程序", "金融资讯影响力评级"): "partial",
    ("同舟小程序", "机构研调观点脉络"): "partial",
    ("同舟小程序", "行业多空风向标与多维诊断"): "launch",
    ("同舟小程序", "轻量化行业报告"): "launch",
    ("同舟小程序", "行业异动归因"): "launch",
    ("同舟小程序", "板块重要新闻"): "launch",
    ("同舟小程序", "高度关联事件匹配"): "partial",
    ("同舟小程序", "相似事件列表"): "partial",
    ("同舟小程序", "行业逻辑推理"): "partial",
    ("同舟小程序", "行业异动真伪鉴定"): "partial",
    ("同舟小程序", "股票多空预期"): "partial",
    ("同舟小程序", "账户投资风格观察"): "future",
    ("同舟小程序", "个股风险透视"): "partial",
    ("同舟小程序", "账户投资优化建议"): "future",
    ("同舟小程序", "交易表现复盘"): "future",
    ("同舟小程序", "交易习惯回顾"): "future",
    ("同舟小程序", "交易心理偏差与引导"): "future",
    ("智能投顾", "通用金融问答"): "partial",
    ("智能投顾", "市场热点话题观察"): "partial",
    ("智能投顾", "事件解读分析"): "launch",
    ("智能投顾", "事件脉络追踪"): "partial",
    ("智能投顾", "事件波动预判"): "future",
    ("智能投顾", "事件回测结果"): "partial",
    ("智能投顾", "相似案例匹配"): "partial",
    ("智能投顾", "关联标的与上下游关系梳理"): "launch",
    ("智能投顾", "个股异动分析"): "launch",
    ("智能投顾", "市场复盘报告"): "future",
    ("智能投顾", "复盘风格个性化定制"): "future",
    ("智能投顾", "个股批判性分析"): "launch",
    ("智能投顾", "个股投资亮点"): "partial",
    ("智能投顾", "热门个股榜单"): "partial",
    ("智能投顾", "行业/板块批判性分析"): "launch",
    ("智能投顾", "行业/板块异动归因"): "launch",
    ("智能投顾", "报告核心要点提炼"): "launch",
    ("智能投顾", "报告智能对话"): "partial",
    ("研报数据平台", "报告核心要点提炼"): "launch",
    ("研报数据平台", "报告智能对话"): "partial",
    ("研报数据平台", "智能插入投研图表"): "launch",
    ("研报数据平台", "机构观点横向对比"): "partial",
    ("研报数据平台", "热门行业/个股机构要点萃取"): "launch",
}
REQUIRED_FILES = [
    ".mcp.json",
    ".codebuddy-plugin/plugin.json",
    "connectors/tongzhou-fin-research/connector-meta.json",
    "connectors/tongzhou-fin-research/icon.png",
    "connectors/tongzhou-fin-research/mcp.json",
    "connectors/tongzhou-fin-research/skills/SKILL.md",
    "agents/fin-research-expert.md",
    "avatars/expert.png",
    "avatars/expert-v2.png",
    "skills/fin-mcp-gateway/SKILL.md",
    "skills/fin-mcp-gateway/references/binding.md",
    "skills/fin-mcp-gateway/references/connector.md",
    "skills/fin-mcp-gateway/references/layered-capabilities.md",
    "skills/fin-mcp-gateway/references/playbook-style.md",
    "skills/fin-mcp-gateway/references/safety.md",
    "skills/layer1-doc-search/SKILL.md",
    "skills/layer1-doc-search/references/announcements-events.md",
    "skills/layer1-doc-search/references/document-detail.md",
    "skills/layer1-doc-search/references/examples.md",
    "skills/layer1-doc-search/references/limitations.md",
    "skills/layer1-doc-search/references/news.md",
    "skills/layer1-doc-search/references/research.md",
    "skills/layer1-fin-data/SKILL.md",
    "skills/layer1-fin-data/references/entity.md",
    "skills/layer1-fin-data/references/limitations.md",
    "skills/layer1-fin-data/references/macro_financial.md",
    "skills/layer1-fin-data/references/market.md",
    "skills/layer1-fin-data/references/screening.md",
    "skills/layer1-fin-graph/SKILL.md",
    "skills/layer1-fin-graph/references/identity.md",
    "skills/layer1-fin-graph/references/industry-chain-graph.md",
    "skills/layer1-fin-graph/references/industry-graph.md",
    "skills/layer1-fin-graph/references/limitations.md",
    "skills/layer1-fin-graph/references/market-signals.md",
    "skills/layer1-same-boat/SKILL.md",
    "skills/layer2-announcement-brief/SKILL.md",
    "skills/layer2-evidence-ledger/SKILL.md",
    "skills/layer2-html-research-playbook/SKILL.md",
    "skills/layer2-html-research-playbook/references/common.md",
    "skills/layer2-industry-brief/SKILL.md",
    "skills/layer2-policy-event-brief/SKILL.md",
    "skills/layer2-research-red-team/SKILL.md",
    "skills/layer2-research-digest/SKILL.md",
    "skills/layer2-research-visuals/SKILL.md",
    "skills/layer2-research-visuals/references/common.md",
    "skills/layer2-research-visuals/references/market-charts.md",
    "skills/layer2-research-visuals/references/report-images.md",
    "skills/layer2-research-visuals/references/widget-event-runtime.md",
    "skills/layer2-research-visuals/references/widget-kline-runtime.md",
    "skills/layer2-research-visuals/references/widget-svg-runtime.md",
    "skills/layer2-research-visuals/references/widget-trend-runtime.md",
    "skills/layer2-transmission-chain-builder/SKILL.md",
    "skills/layer2-stock-brief/SKILL.md",
    "skills/layer2-stock-narrative-valuation/SKILL.md",
    "skills/layer2-stock-narrative-valuation/scripts/dcf_implied.py",
    "skills/layer3-event-interpretation/SKILL.md",
    "skills/layer3-event-interpretation/references/playbook.md",
    "skills/layer3-industry-windvane/SKILL.md",
    "skills/layer3-industry-windvane/references/playbook.md",
    "README.md",
]
HTML_PLAYBOOK_SKILL_FILES = [
    "SKILL.md",
    "references/common.md",
]
LAYER3_SKILL_FILES = ["SKILL.md", "references/playbook.md"]
RESEARCH_VISUAL_SKILL_FILES = [
    "SKILL.md",
    "references/common.md",
    "references/market-charts.md",
    "references/report-images.md",
    "references/widget-event-runtime.md",
    "references/widget-kline-runtime.md",
    "references/widget-svg-runtime.md",
    "references/widget-trend-runtime.md",
]
PUBLISHED_PLAYBOOK_CASES = {
    "event-factor-impact-brief",
    "industry-long-short-signal",
}
EXPECTED_PLAYBOOK_TYPES = {
    "announcement-one-page-brief": "announcement-one-page",
    "event-factor-impact-brief": "event-factor-impact",
    "industry-long-short-signal": "industry-windvane",
    "policy-event-transmission-chain": "policy-transmission-chain",
    "research-consensus-divergence-map": "research-consensus-map",
    "stock-narrative-valuation-lens": "stock-narrative-valuation",
}
PUBLISHED_PLAYBOOK_TYPE_SKILLS = {
    "event-factor-impact": "layer3-event-interpretation",
    "industry-windvane": "layer3-industry-windvane",
}


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    ignored = {
        ".git",
        ".gitea",
        ".mypy_cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "node_modules",
        "playbooks",
        "dist",
        "tests",
        ".DS_Store",
        ".gitignore",
        ".npm_acc",
        ".sms_key",
    }
    ignored.update(name for name in names if name.startswith(".env"))
    if Path(_dir).name == "docs":
        ignored.update(name for name in names if Path(name).suffix.lower() in EXCLUDED_DOC_ASSET_SUFFIXES)
    if "reference-materials" in names:
        ignored.add("reference-materials")
    return ignored.intersection(names)


def _fail(message: str) -> None:
    raise SystemExit(message)


def _json(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(f"invalid json: {path}: {exc}")


def _rel(source: Path, rel_path: str) -> Path:
    return source / rel_path.removeprefix("./")


def _assert_only_core_skill_sources(source: Path) -> None:
    offenders: list[str] = []
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        if set(rel.parts) & PACKAGED_PATH_EXCLUDED_PARTS:
            continue
        layer_parts = [part for part in rel.parts if part.startswith(("layer1-", "layer2-", "layer3-"))]
        if not layer_parts:
            continue
        if rel.parts[:1] != ("skills",):
            offenders.append(rel.as_posix())
            continue
        for part in layer_parts:
            if part.startswith("layer1-") and (part.startswith(FORBIDDEN_LAYER1_PREFIXES) or part not in APPROVED_LAYER1_SKILLS):
                offenders.append(rel.as_posix())
                break
            if part.startswith("layer2-") and (part.startswith(FORBIDDEN_LAYER2_PREFIXES) or part not in APPROVED_ROUTES):
                offenders.append(rel.as_posix())
                break
            if part.startswith("layer3-") and (part.startswith(FORBIDDEN_LAYER3_PREFIXES) or part not in APPROVED_LAYER3_SKILLS):
                offenders.append(rel.as_posix())
                break
    if offenders:
        _fail("only approved public-market Layer 1/2/3 skills may be packaged: " + ", ".join(sorted(offenders)))


def _assert_layer2_dependencies_exist(source: Path) -> None:
    missing: list[str] = []
    for path in sorted((source / "skills").glob("layer2-*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        for skill in sorted(set(re.findall(r"layer1-[a-z0-9-]+", text))):
            if skill.startswith(FORBIDDEN_LAYER1_PREFIXES):
                missing.append(f"{path.relative_to(source).as_posix()} -> forbidden {skill}")
            elif skill not in APPROVED_LAYER1_SKILLS:
                missing.append(f"{path.relative_to(source).as_posix()} -> unsupported {skill}")
            elif not (source / "skills" / skill / "SKILL.md").exists():
                missing.append(f"{path.relative_to(source).as_posix()} -> missing {skill}")
    if missing:
        _fail("Layer 2 dependencies are not satisfied: " + ", ".join(missing))


def _assert_layer3_dependencies_exist(source: Path) -> None:
    missing: list[str] = []
    for path in sorted((source / "skills").glob("layer3-*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        for skill in sorted(set(re.findall(r"layer[12]-[a-z0-9-]+", text))):
            if skill.startswith("layer1-"):
                supported = skill in APPROVED_LAYER1_SKILLS
            else:
                supported = skill in APPROVED_ROUTES
            if not supported:
                missing.append(f"{path.relative_to(source).as_posix()} -> unsupported {skill}")
            elif not (source / "skills" / skill / "SKILL.md").exists():
                missing.append(f"{path.relative_to(source).as_posix()} -> missing {skill}")
    if missing:
        _fail("Layer 3 dependencies are not satisfied: " + ", ".join(missing))


def _assert_workbuddy_mcp_dependencies(source: Path, plugin: dict[str, object]) -> None:
    dependencies = plugin.get("dependencies")
    if not isinstance(dependencies, dict) or dependencies.get("connectors") != ["tongzhou-fin-research"]:
        _fail("plugin.json dependencies.connectors must declare only tongzhou-fin-research")

    connector_root = source / "connectors" / "tongzhou-fin-research"
    meta = _json(connector_root / "connector-meta.json")
    if meta.get("source") != "tongzhou-fin-research" or meta.get("minWorkbuddyVersion") != "5.0.0":
        _fail("tongzhou-fin-research connector metadata is invalid")
    mcp_config = _json(connector_root / "mcp.json")
    servers = mcp_config.get("mcpServers")
    if not isinstance(servers, dict) or set(servers) != {"tongzhou-fin-research"}:
        _fail("connector mcp.json must contain one tongzhou-fin-research server")
    server = servers["tongzhou-fin-research"]
    if server.get("type") != "streamableHttp":
        _fail("connector must use native streamableHttp transport")
    if server.get("url") != "https://mcp-gateway.textmind-gz.com/mcp/tongzhou-research":
        _fail("connector must use the canonical public OAuth MCP resource")
    if "headers" in server or "command" in server or "args" in server:
        _fail("connector must delegate credentials and OAuth to the WorkBuddy runtime")


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        _fail(f"avatar is not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _parse_spreadsheet_capability_rows(markdown: str) -> dict[tuple[str, str], dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    in_mapping = False
    section = ""
    for line in markdown.splitlines():
        if line == "## Spreadsheet Capability Mapping":
            in_mapping = True
            continue
        if in_mapping and line.startswith("## ") and not line.startswith("### "):
            break
        if in_mapping and line.startswith("### "):
            section = line.removeprefix("### ").strip()
            continue
        if section not in {"同舟小程序", "智能投顾", "研报数据平台"}:
            continue
        if not line.startswith("| ") or line.startswith("|---") or "Spreadsheet capability" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4:
            _fail(f"invalid spreadsheet capability row: {line}")
        rows[(section, cells[0])] = {"route": cells[1], "status": cells[2], "notes": cells[3]}
    return rows


def basic_validate(source: Path) -> None:
    _assert_only_core_skill_sources(source)
    _assert_layer2_dependencies_exist(source)
    _assert_layer3_dependencies_exist(source)
    plugin_path = source / ".codebuddy-plugin" / "plugin.json"
    if not plugin_path.exists():
        _fail(".codebuddy-plugin/plugin.json is missing")
    version_path = source / "VERSION"
    if not version_path.exists():
        _fail("VERSION is missing")
    expected_version = version_path.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.fullmatch(expected_version):
        _fail("VERSION must be SemVer")
    plugin = _json(plugin_path)
    missing_files = [path for path in REQUIRED_FILES if not (source / path).exists()]
    if missing_files:
        _fail(f"required files missing: {', '.join(missing_files)}")

    for field in ["name", "version", "expertType", "agentName", "categoryId"]:
        if not plugin.get(field):
            _fail(f"plugin.json missing {field}")
    if plugin.get("name") != "fin-research-expert":
        _fail("plugin.json name must be fin-research-expert")
    if plugin.get("version") != expected_version:
        _fail("plugin.json version must match VERSION")
    codex_plugin_path = source / "codex/plugins/tongzhou-fin-research-expert/.codex-plugin/plugin.json"
    if codex_plugin_path.exists():
        codex_plugin = _json(codex_plugin_path)
        if codex_plugin.get("version") != expected_version:
            _fail("Codex plugin version must match VERSION")
    display_name = plugin.get("displayName")
    if not isinstance(display_name, dict) or display_name.get("zh") != "同舟股市投研专家" or display_name.get("en") != "Tongzhou Equity Research Expert":
        _fail("plugin.json displayName must be 同舟股市投研专家 / Tongzhou Equity Research Expert")
    if plugin.get("expertType") != "agent":
        _fail("plugin.json expertType must be agent")
    if plugin.get("agents") != ["./agents/fin-research-expert.md"]:
        _fail("plugin.json agents must point to ./agents/fin-research-expert.md")
    if plugin.get("skills") != EXPECTED_SKILL_PATHS:
        _fail("plugin.json skills must include fin-mcp-gateway plus approved Layer 1, Layer 2, and Layer 3 skills")
    _assert_workbuddy_mcp_dependencies(source, plugin)

    tags = plugin.get("tags")
    quick_prompts = plugin.get("quickPrompts")
    if not isinstance(tags, list) or len(tags) != 3:
        _fail("plugin.json must declare exactly 3 tags")
    if not isinstance(quick_prompts, list) or len(quick_prompts) != 3:
        _fail("plugin.json must declare exactly 3 quickPrompts")
    if plugin.get("defaultInitPrompt") != quick_prompts[0]:
        _fail("defaultInitPrompt must match the first quick prompt")
    quick_prompt_text = json.dumps(quick_prompts, ensure_ascii=False)
    for phrase in ["事件因子解读", "因子", "产业链", "历史相似事件", "行业多空风向标", "短期", "中期", "长期"]:
        if phrase not in quick_prompt_text:
            _fail(f"quickPrompts missing expected entry point: {phrase}")
    plugin_text_forbidden_check = json.dumps(plugin, ensure_ascii=False)
    for phrase in ["账户投资风格观察", "账户投资优化建议", "交易表现复盘", "交易心理偏差"]:
        if phrase in plugin_text_forbidden_check:
            _fail(f"plugin metadata must not expose future account workflow: {phrase}")

    descriptions = plugin.get("displayDescription")
    if not isinstance(descriptions, dict):
        _fail("plugin.json displayDescription must be localized")
    zh_description = str(descriptions.get("zh", ""))
    if not 40 <= len(zh_description) <= 50:
        _fail("displayDescription.zh must be 40-50 Chinese characters")

    avatar = plugin.get("avatar")
    if avatar != "avatars/expert-v2.png":
        _fail("plugin.json avatar must be avatars/expert-v2.png")
    avatar_path = _rel(source, str(avatar))
    if avatar_path.stat().st_size > 500 * 1024:
        _fail("avatar must be <= 500KB")
    if _png_dimensions(avatar_path) != (512, 512):
        _fail("avatar must be 512x512 PNG")

    for rel_path in plugin.get("agents", []):
        if not _rel(source, str(rel_path)).exists():
            _fail(f"agent path missing: {rel_path}")
    for rel_path in plugin.get("skills", []):
        if not (_rel(source, str(rel_path)) / "SKILL.md").exists():
            _fail(f"skill path missing SKILL.md: {rel_path}")

    plugin_text = json.dumps(plugin, ensure_ascii=False)
    for forbidden in ["layer2-sales-", "layer2-care-", "layer2-pa-"]:
        if forbidden in plugin_text:
            _fail(f"plugin metadata must not advertise {forbidden}")

    agent = (source / "agents/fin-research-expert.md").read_text(encoding="utf-8")
    frontmatter = agent.split("---", 2)[1]
    if "tools:" in frontmatter:
        _fail("agent frontmatter must use skills, not tools")
    for phrase in ["激活边界", "必须遵守的执行顺序", "认证与工具闸门", "内部场景路由表", "能力状态处理", "证据合同", "状态处理", "个人买卖", "客户画像"]:
        if phrase not in agent:
            _fail(f"agent prompt missing required contract: {phrase}")
    for phrase in ["Expert", "Connector", "companion **Skill**", "Playbook", "不要把 `layer2-*` 路由名展示给用户"]:
        if phrase not in agent:
            _fail(f"agent prompt missing WorkBuddy ecosystem boundary: {phrase}")
    for phrase in ["同舟股市投研专家", "launch", "partial", "future/excluded"]:
        if phrase not in agent:
            _fail(f"agent prompt missing capability status behavior: {phrase}")
    for phrase in ["tongzhou-fin-research", "不要先运行 Shell", "mcp__fin-doc__*", "search_hot_news"]:
        if phrase not in agent:
            _fail(f"agent prompt missing credential bypass guard: {phrase}")
    for phrase in [
        "tongzhou-fin-research",
        "扫码/授权入口",
        "只重试原 Connector 调用一次",
        "新对话或 WorkBuddy 重启",
        "不要要求新用户",
    ]:
        if phrase not in agent:
            _fail(f"agent prompt missing customer binding flow: {phrase}")
    for phrase in ["上一轮结果", "缓存数据", "之前已经拉到", "WorkBuddy dependency Connector 成功业务调用"]:
        if phrase not in agent:
            _fail(f"agent prompt missing stale-evidence guard: {phrase}")
    for phrase in ["解析优先", "`subject`", "`basket_id`", "不要说“工程上没有解决”"]:
        if phrase not in agent:
            _fail(f"agent prompt missing resolver-before-call guard: {phrase}")

    skill = (source / "skills/fin-mcp-gateway/SKILL.md").read_text(encoding="utf-8")
    fin_data = (source / "skills/layer1-fin-data/SKILL.md").read_text(encoding="utf-8")
    fin_data_entity = (source / "skills/layer1-fin-data/references/entity.md").read_text(encoding="utf-8")
    doc_search = (source / "skills/layer1-doc-search/SKILL.md").read_text(encoding="utf-8")
    fin_graph_root = source / "skills/layer1-fin-graph"
    fin_graph = (fin_graph_root / "SKILL.md").read_text(encoding="utf-8")
    fin_graph_all = fin_graph + "\n" + "\n".join(
        (fin_graph_root / "references" / ref_name).read_text(encoding="utf-8")
        for ref_name in [
            "identity.md",
            "industry-chain-graph.md",
            "industry-graph.md",
            "limitations.md",
            "market-signals.md",
        ]
    )
    same_boat = (source / "skills/layer1-same-boat/SKILL.md").read_text(encoding="utf-8")
    binding = (source / "skills/fin-mcp-gateway/references/binding.md").read_text(encoding="utf-8")
    connector = (source / "skills/fin-mcp-gateway/references/connector.md").read_text(encoding="utf-8")
    playbook = (source / "skills/fin-mcp-gateway/references/playbook-style.md").read_text(encoding="utf-8")
    routes = (source / "skills/fin-mcp-gateway/references/layered-capabilities.md").read_text(encoding="utf-8")
    evidence_skill = (source / "skills/layer2-evidence-ledger/SKILL.md").read_text(encoding="utf-8")
    chain_skill = (source / "skills/layer2-transmission-chain-builder/SKILL.md").read_text(encoding="utf-8")
    red_team_skill = (source / "skills/layer2-research-red-team/SKILL.md").read_text(encoding="utf-8")
    narrative_skill = (source / "skills/layer2-stock-narrative-valuation/SKILL.md").read_text(encoding="utf-8")
    industry_skill = (source / "skills/layer2-industry-brief/SKILL.md").read_text(encoding="utf-8")
    research_visual_root = source / "skills/layer2-research-visuals"
    research_visual_all = "\n".join(
        (research_visual_root / rel_path).read_text(encoding="utf-8")
        for rel_path in RESEARCH_VISUAL_SKILL_FILES
    )
    html_playbook_root = source / "skills/layer2-html-research-playbook"
    html_skill = (html_playbook_root / "SKILL.md").read_text(encoding="utf-8")
    html_refs = {
        rel_path: (html_playbook_root / rel_path).read_text(encoding="utf-8")
        for rel_path in HTML_PLAYBOOK_SKILL_FILES
        if rel_path != "SKILL.md"
    }
    html_playbook_all = html_skill + "\n" + "\n".join(html_refs.values())
    actual_html_playbook_files = sorted(
        path.relative_to(html_playbook_root).as_posix()
        for path in html_playbook_root.rglob("*")
        if path.is_file()
    )
    if actual_html_playbook_files != HTML_PLAYBOOK_SKILL_FILES:
        _fail(
            "HTML research playbook skill must be router plus references: "
            + ", ".join(HTML_PLAYBOOK_SKILL_FILES)
        )
    codex_html_playbook_root = source / "codex/plugins/tongzhou-fin-research-expert/skills/layer2-html-research-playbook"
    if codex_html_playbook_root.exists():
        codex_html_playbook_files = sorted(
            path.relative_to(codex_html_playbook_root).as_posix()
            for path in codex_html_playbook_root.rglob("*")
            if path.is_file()
        )
        if codex_html_playbook_files != HTML_PLAYBOOK_SKILL_FILES:
            _fail("Codex HTML playbook skill files must mirror source skill files")
        for rel_path in HTML_PLAYBOOK_SKILL_FILES:
            if (codex_html_playbook_root / rel_path).read_text(encoding="utf-8") != (
                html_playbook_root / rel_path
            ).read_text(encoding="utf-8"):
                _fail(f"Codex HTML playbook skill differs from source skill: {rel_path}")
    layer3_all: dict[str, str] = {}
    for skill_name in sorted(APPROVED_LAYER3_SKILLS):
        layer3_root = source / "skills" / skill_name
        actual_layer3_files = sorted(
            path.relative_to(layer3_root).as_posix()
            for path in layer3_root.rglob("*")
            if path.is_file()
        )
        if actual_layer3_files != LAYER3_SKILL_FILES:
            _fail(f"{skill_name} must contain SKILL.md plus references/playbook.md")
        layer3_all[skill_name] = "\n".join(
            (layer3_root / rel_path).read_text(encoding="utf-8")
            for rel_path in LAYER3_SKILL_FILES
        )
        codex_layer3_root = source / "codex/plugins/tongzhou-fin-research-expert/skills" / skill_name
        if codex_layer3_root.exists():
            codex_layer3_files = sorted(
                path.relative_to(codex_layer3_root).as_posix()
                for path in codex_layer3_root.rglob("*")
                if path.is_file()
            )
            if codex_layer3_files != LAYER3_SKILL_FILES:
                _fail(f"Codex {skill_name} files must mirror source skill files")
            for rel_path in LAYER3_SKILL_FILES:
                if (codex_layer3_root / rel_path).read_text(encoding="utf-8") != (
                    layer3_root / rel_path
                ).read_text(encoding="utf-8"):
                    _fail(f"Codex {skill_name} differs from source skill: {rel_path}")
    actual_research_visual_files = sorted(
        path.relative_to(research_visual_root).as_posix()
        for path in research_visual_root.rglob("*")
        if path.is_file()
    )
    if actual_research_visual_files != RESEARCH_VISUAL_SKILL_FILES:
        _fail(
            "research visual skill must be router plus references: "
            + ", ".join(RESEARCH_VISUAL_SKILL_FILES)
        )
    codex_research_visual_root = source / "codex/plugins/tongzhou-fin-research-expert/skills/layer2-research-visuals"
    if codex_research_visual_root.exists():
        codex_research_visual_files = sorted(
            path.relative_to(codex_research_visual_root).as_posix()
            for path in codex_research_visual_root.rglob("*")
            if path.is_file()
        )
        if codex_research_visual_files != RESEARCH_VISUAL_SKILL_FILES:
            _fail("Codex research visual skill files must mirror source skill files")
        for rel_path in RESEARCH_VISUAL_SKILL_FILES:
            if (codex_research_visual_root / rel_path).read_text(encoding="utf-8") != (
                research_visual_root / rel_path
            ).read_text(encoding="utf-8"):
                _fail(f"Codex research visual skill differs from source skill: {rel_path}")
    for phrase in [
        "WorkBuddy Ecosystem Fit",
        "Mandatory Rules",
        "Internal Route Decision Table",
        "Route before calling",
        "No secret echo",
        "No bypass tools",
        "No local bridge",
        "Credential Check",
        "native OAuth",
        "Connector Operation Playbook",
        "Layer 1 Contract Preflight",
        "https://mcp-gateway.textmind-gz.com/login",
    ]:
        if phrase not in skill:
            _fail(f"skill runbook missing required section/rule: {phrase}")
    for phrase in ["Connector", "Skill", "Expert", "Playbook", "implementation labels"]:
        if phrase not in skill:
            _fail(f"skill missing WorkBuddy module mapping: {phrase}")
    for phrase in [
        "tongzhou-fin-research",
        "native OAuth",
        "renewable OAuth session",
        "retry the original Connector call once",
        "Never ask a new user to copy an API Key",
    ]:
        if phrase not in skill:
            _fail(f"skill runbook missing OAuth-first binding rule: {phrase}")
    for phrase in ["gateway_api.cjs", "missing local API Key", "mcp__fin-doc__*", "search_hot_news"]:
        if phrase not in skill and phrase not in binding:
            _fail(f"skill/binding missing no-bypass guard: {phrase}")
    for phrase in ["previously fetched results", "cached data", "prior-turn evidence", "`tongzhou-fin-research` is not connected"]:
        if phrase not in skill and phrase not in binding:
            _fail(f"skill/binding missing stale-evidence guard: {phrase}")
    for phrase in [
        "layer2-research-visuals",
        "WorkBuddy normal-answer visual polish",
        "`read_me`",
        "`show_widget`",
        "references/widget-svg-runtime.md",
        "chart-evidence/1",
        "workbuddy-kline-svg/1",
        "workbuddy-trend-svg/1",
        "workbuddy-event-svg/1",
        "do not use Bash, Write, Edit, Python, Node CLI",
        "table/text fallback",
    ]:
        if phrase not in skill:
            _fail(f"gateway skill missing normal-answer visual route: {phrase}")
    for phrase in ["Preferred WorkBuddy Native OAuth", "Codex Registered MCP OAuth", "No Local Credential Path"]:
        if phrase not in binding:
            _fail(f"binding reference missing OAuth guidance: {phrase}")
    for phrase in [
        "Preferred WorkBuddy Native OAuth",
        "browser authorization page",
        "Retry the original Connector call once",
    ]:
        if phrase not in binding and phrase not in connector:
            _fail(f"binding/connector missing WorkBuddy OAuth-first flow: {phrase}")
    for phrase in ["Tongzhou MCP Gateway is the WorkBuddy Connector", "companion instruction layer", "Do not surface internal labels", "INVALID_BROAD_TIME_RANGE"]:
        if phrase not in connector:
            _fail(f"connector reference missing WorkBuddy connector contract: {phrase}")
    for phrase in ["WorkBuddy Playbook", "做同款", "used capability badges", "layer3-industry-windvane", "layer3-event-interpretation"]:
        if phrase not in playbook:
            _fail(f"playbook reference missing Discover/Playbook contract: {phrase}")
    for phrase in ["Industry Windvane Visual Contract", "circular score rings", "waterfall score charts", "visible tool-failure chips"]:
        if phrase not in playbook:
            _fail(f"playbook reference missing industry windvane visual rule: {phrase}")
    for phrase in ["layer2-html-research-playbook", "shared presentation layer", "layer3-industry-windvane", "layer3-event-interpretation"]:
        if phrase not in playbook:
            _fail(f"playbook reference missing HTML playbook ownership: {phrase}")
    for phrase in ["layer2-evidence-ledger", "layer2-transmission-chain-builder", "layer2-research-red-team", "source audit", "impact chain", "falsification checks"]:
        if phrase not in playbook:
            _fail(f"playbook reference missing research assistant ownership: {phrase}")
    for phrase in ["证据台账", "支持、反对、背景、待验证或证据缺口", "不得新增事实", "不要把同舟观点写成券商研报"]:
        if phrase not in evidence_skill:
            _fail(f"evidence ledger skill missing boundary: {phrase}")
    for phrase in ["事件 -> 机制 -> 上中下游链路表", "受益/承压环节", "验证指标", "如果证据只覆盖 1-2 天"]:
        if phrase not in chain_skill:
            _fail(f"transmission chain skill missing boundary: {phrase}")
    for phrase in ["反方审查", "证伪信号", "叙事跳跃", "不要输出买入、卖出"]:
        if phrase not in red_team_skill:
            _fail(f"research red-team skill missing boundary: {phrase}")
    for phrase in ["调用任何业务工具前，必须先读取对应 Layer 1 契约", "工具调用失败不是用户结果"]:
        if phrase not in industry_skill:
            _fail(f"industry skill missing Layer 1/failure handling rule: {phrase}")
    for phrase in ["references/common.md", "layer3-industry-windvane", "layer3-event-interpretation", "does not own the user story"]:
        if phrase not in html_skill:
            _fail(f"HTML research playbook router missing reference route: {phrase}")
    for phrase in [
        "已取证",
        "必要交互内联",
        "不得新增事实",
        "来源类型",
        "非投资建议",
        "不能溢出",
        "工具调用失败",
    ]:
        if phrase not in html_playbook_all:
            _fail(f"HTML research playbook skill missing boundary: {phrase}")
    for phrase in [
        "Playbook type: industry-windvane",
        "resolve_research_identity",
        "canonical_id",
        "3d/5d/7d/20d",
        "Skip `60d`",
        "六维因子",
        "情景矩阵",
        "layer2-html-research-playbook",
    ]:
        if phrase not in layer3_all["layer3-industry-windvane"]:
            _fail(f"industry windvane Layer 3 skill missing contract: {phrase}")
    for phrase in [
        "Playbook type: event-factor-impact",
        "event title",
        "layer2-transmission-chain-builder",
        "3d/5d/7d/20d",
        "Treat `60d` as optional",
        "source-review entry",
        "layer2-html-research-playbook",
    ]:
        if phrase not in layer3_all["layer3-event-interpretation"]:
            _fail(f"event interpretation Layer 3 skill missing contract: {phrase}")
    for phrase in [
        "browser authorization page",
        "Retry the original Connector call once",
        "renewable session",
        "No Local Credential Path",
    ]:
        if phrase not in skill and phrase not in binding:
            _fail(f"skill/binding missing OAuth customer flow: {phrase}")
    for phrase in ["Resolver-before-call", "`subject`", "`basket_id`", "`sector_id`", "不要说工程上没有解决"]:
        if phrase not in skill:
            _fail(f"gateway skill missing resolver-before-call guard: {phrase}")
    for phrase in ["references/market.md", "references/entity.md", "Never generate or pass raw SQL"]:
        if phrase not in fin_data:
            _fail(f"fin data skill missing expected reference/rule: {phrase}")
    for phrase in ["basket resolution ledger", "resolved_basket_id", "query_sector_valuation", "search_baskets", "Do not say engineering has not solved this", "工程上没有解决"]:
        if phrase not in fin_data_entity:
            _fail(f"fin data entity reference missing resolver guard: {phrase}")
    for phrase in ["references/news.md", "references/research.md", "company", "ticker"]:
        if phrase not in doc_search:
            _fail(f"doc search skill missing expected reference/rule: {phrase}")
    for phrase in ["references/identity.md", "references/industry-chain-graph.md", "references/industry-graph.md", "references/market-signals.md"]:
        if phrase not in fin_graph:
            _fail(f"fin graph skill missing reference route: {phrase}")
    for phrase in ["list_industry_indices", "get_industry_views", "list_industry_anomalies", "Resolver-before-call guardrail", "subject resolution ledger", "resolved_subject", "list_supported_subjects", "不要说工程上没有解决"]:
        if phrase not in fin_graph_all:
            _fail(f"fin graph skill missing resolver guard: {phrase}")
    for phrase in ["search_research_sectors", "list_sector_viewpoints", "same-boat", "importance_score", "popularity_score", "sentiment_score", "radar"]:
        if phrase not in same_boat:
            _fail(f"same boat skill missing expected contract: {phrase}")
    for phrase in ["Same Boat `sector_id`", "Fin Data basket", "Fin Graph subject", "Shenwan valuation", "resolution ledger", "不要说工程上没有解决"]:
        if phrase not in industry_skill:
            _fail(f"industry skill missing resolver protocol: {phrase}")
    for phrase in [
        "WorkBuddy receives the native callback",
        "Reauthorization is required only after revoke",
        "do not echo, save, or use it",
    ]:
        if phrase not in binding:
            _fail(f"binding reference missing OAuth session rule: {phrase}")
    if "Layer 2 modules and Layer 3 user stories inherit" not in routes or "do not create additional data rights" not in routes:
        _fail("layered capability reference must state L2/L3 inheritance and no extra data rights")
    for phrase in ["WorkBuddy Ecosystem Alignment", "This file is an internal routing reference", "Do not split v1 into multiple same-brand experts", "Keep `layer1-*`, `layer2-*`"]:
        if phrase not in routes:
            _fail(f"layered capability reference missing WorkBuddy ecosystem alignment: {phrase}")
    for phrase in ["layer2-html-research-playbook", "Presentation-only artifact", "Approved Layer 3 User Stories", "layer3-industry-windvane", "layer3-event-interpretation"]:
        if phrase not in routes:
            _fail(f"layered capability reference missing HTML playbook route: {phrase}")
    for phrase in ["layer2-stock-narrative-valuation", "implied valuation", "DCF/no-DCF boundary"]:
        if phrase not in routes:
            _fail(f"layered capability reference missing stock narrative valuation route: {phrase}")
    for phrase in ["layer2-evidence-ledger", "layer2-transmission-chain-builder", "layer2-research-red-team", "falsification signals", "validation indicators"]:
        if phrase not in routes:
            _fail(f"layered capability reference missing research assistant route: {phrase}")
    for phrase in [
        "WorkBuddy inline visual gate",
        "Fallback first",
        "`read_me`",
        "`show_widget`",
        "#d92d20",
        "#079455",
        "height:340px",
        "host widget clips taller content",
        "No external assets",
        "Direct Widget path",
        "__TONGZHOU_CHART_PAYLOAD__",
        "chart-evidence/1",
        "data-tongzhou-kline",
        "data-tongzhou-trend",
        "data-tongzhou-event",
        "图表加载中，请同时参考数据表",
        "OHLCV validation",
        "sample_count",
        "missing_count",
        "stable HTTPS",
        "no fake link",
    ]:
        if phrase not in research_visual_all:
            _fail(f"research visual skill missing contract: {phrase}")
    for phrase in ["DCF 隐含终局利润反算", "scripts/dcf_implied.py", "E1/E2/E3", "不是目标价", "不是买卖建议", "支持当前叙事的证据"]:
        if phrase not in narrative_skill:
            _fail(f"stock narrative valuation skill missing boundary: {phrase}")
    rows = _parse_spreadsheet_capability_rows(routes)
    if set(rows) != set(EXPECTED_SPREADSHEET_CAPABILITY_STATUS):
        missing = sorted(set(EXPECTED_SPREADSHEET_CAPABILITY_STATUS) - set(rows))
        extra = sorted(set(rows) - set(EXPECTED_SPREADSHEET_CAPABILITY_STATUS))
        _fail(f"spreadsheet capability matrix mismatch; missing={missing}; extra={extra}")
    status_counts = Counter(row["status"] for row in rows.values())
    if status_counts != Counter({"launch": 16, "partial": 18, "future": 8}):
        _fail(f"spreadsheet capability status counts changed: {dict(status_counts)}")
    for key, expected_status in EXPECTED_SPREADSHEET_CAPABILITY_STATUS.items():
        row = rows[key]
        if row["status"] != expected_status:
            _fail(f"spreadsheet capability {key} status must be {expected_status}, got {row['status']}")
        if any(forbidden in row["route"] for forbidden in ["layer2-sales-", "layer2-care-", "layer2-pa-"]):
            _fail(f"spreadsheet capability {key} must not route to sales/care/PA")
        if row["status"] == "launch" and not any(
            route in row["route"] for route in APPROVED_ROUTES | APPROVED_LAYER3_SKILLS
        ):
            _fail(f"launch capability {key} must name an approved Layer 2 or Layer 3 route")
    for excluded in ["layer2-sales-*", "layer2-care-*", "layer2-pa-*"]:
        if f"| `{excluded}` | excluded |" not in routes:
            _fail(f"excluded capability family missing: {excluded}")
    for v2_alias in ["业务 V2 包装视图", "板块重要新闻", "相似事件列表", "事件回测结果"]:
        if v2_alias not in routes:
            _fail(f"business V2 capability boundary missing: {v2_alias}")

    playbook_root = source / "playbooks" / "cases"
    if playbook_root.exists():
        categories_payload = _json(source / "playbooks/categories.json")
        categories = {item["id"] for item in categories_payload.get("categories", []) if isinstance(item, dict)}
        case_dirs = sorted(playbook_root / case_id for case_id in PUBLISHED_PLAYBOOK_CASES)
        missing_published_cases = [path.name for path in case_dirs if not path.is_dir()]
        if missing_published_cases:
            _fail("published playbook cases missing: " + ", ".join(sorted(missing_published_cases)))
    else:
        case_dirs = []
        categories = set()
    for case_dir in case_dirs:
        case = _json(case_dir / "case.json")
        html = (case_dir / "output.html").read_text(encoding="utf-8")
        review = (case_dir / "review.md").read_text(encoding="utf-8")
        for field in [
            "id",
            "title",
            "title_en",
            "subtitle",
            "description",
            "categories",
            "tags",
            "artifact_type",
            "playbook_type",
            "cover_image",
            "preview",
            "prompt",
            "skills",
            "experts",
            "mcps",
            "creator",
            "quality_score",
            "source",
            "created_at",
            "updated_at",
        ]:
            if field not in case or case[field] in ("", None):
                _fail(f"{case_dir.name} case.json missing {field}")
        if case["id"] != case_dir.name:
            _fail(f"{case_dir.name} case id must match directory name")
        if case.get("artifact_type") != "html" or case.get("preview") != "output.html":
            _fail(f"{case_dir.name} must be an html case with output.html preview")
        expected_playbook_type = EXPECTED_PLAYBOOK_TYPES[case_dir.name]
        if case.get("playbook_type") != expected_playbook_type:
            _fail(f"{case_dir.name} playbook_type must be {expected_playbook_type}")
        owner_skill = PUBLISHED_PLAYBOOK_TYPE_SKILLS.get(expected_playbook_type)
        if owner_skill:
            playbook_reference = source / "skills" / owner_skill / "references/playbook.md"
        else:
            playbook_reference = case_dir / "playbook-reference.md"
        if not playbook_reference.exists():
            _fail(f"{case_dir.name} playbook_type reference is missing: {expected_playbook_type}")
        if not set(case.get("categories", [])) <= categories:
            _fail(f"{case_dir.name} uses unknown Playbook categories")
        if case.get("source_links_supported") is not True:
            _fail(f"{case_dir.name} must declare source_links_supported true")
        if not case.get("experts") or not case.get("mcps"):
            _fail(f"{case_dir.name} must link expert and MCP metadata")
        if case.get("skills") != []:
            _fail(f"{case_dir.name} must not list expert-embedded skills in skills[]")
        for expert in case.get("experts", []):
            if expert.get("expertType") in {"agent", "team"} and not expert.get("promptFileSnapshot"):
                _fail(f"{case_dir.name} agent/team expert must include promptFileSnapshot")
        if int(case.get("quality_score", 0)) < 80:
            _fail(f"{case_dir.name} quality_score must be >= 80")
        cover_mode = str(case.get("cover_mode", ""))
        expected_cover = (720, 1280) if cover_mode == "portrait" else (720, 400)
        cover = case_dir / str(case["cover_image"])
        if _png_dimensions(cover) != expected_cover:
            _fail(f"{case_dir.name} {case['cover_image']} must be {expected_cover[0]}x{expected_cover[1]}")
        fallback_cover = case_dir / "cover.png"
        if fallback_cover.exists() and _png_dimensions(fallback_cover) != (720, 400):
            _fail(f"{case_dir.name} fallback cover.png must be 720x400")
        lowered_html = html.lower()
        if "<html" not in lowered_html or "<style>" not in lowered_html:
            _fail(f"{case_dir.name} output.html must be a standalone HTML document")
        if re.search(r"<script[^>]+src=", lowered_html) or re.search(r"<link[^>]+href=", lowered_html) or re.search(r"<img[^>]+src=", lowered_html) or "@import" in lowered_html:
            _fail(f"{case_dir.name} output.html must not load external rendering assets")
        if 'href="#' in html or "javascript:" in lowered_html:
            _fail(f"{case_dir.name} output.html must not use hash anchors or javascript: links")
        if 'class="tabs"' not in html or "data-target=" not in html or "scrollIntoView" not in html:
            _fail(f"{case_dir.name} output.html must include button-based tab navigation")
        for phrase in ["源头复核", "非投资建议"]:
            if phrase not in html:
                _fail(f"{case_dir.name} output.html missing required phrase: {phrase}")
        for forbidden_phrase in ["未返回可跳转源头", "待回测"]:
            if forbidden_phrase in html:
                _fail(f"{case_dir.name} output.html must not expose diagnostic copy: {forbidden_phrase}")
        external_anchors = re.findall(r"<a\b[^>]*href=[\"']https?://[^\"']+[\"'][^>]*>", html, flags=re.I)
        if len(external_anchors) < 4:
            _fail(f"{case_dir.name} output.html must include source-review links")
        for anchor in external_anchors:
            if not re.search(r"target=[\"']_blank[\"']", anchor, flags=re.I):
                _fail(f"{case_dir.name} external source links must open in a new tab")
            rel_match = re.search(r"rel=[\"']([^\"']*)[\"']", anchor, flags=re.I)
            if not rel_match or "noopener" not in rel_match.group(1).lower().split():
                _fail(f"{case_dir.name} external source links must include rel noopener")
        if re.search(r"\.section\s*\{[^}]*display\s*:\s*none", html, flags=re.I | re.S):
            _fail(f"{case_dir.name} output.html sections must be visible without JS")
        if "score-circle" in html:
            _fail(f"{case_dir.name} output.html must not use circular score UI")
        if case.get("playbook_type") == "industry-windvane":
            for phrase in ["六维评分明细说明", "证据说明"]:
                if phrase not in html:
                    _fail(f"{case_dir.name} industry windvane radar must explain factor scores: {phrase}")
        for forbidden in ["mcp_live_", "短信验证码", "个人持仓", "交易历史", "raw JSON", "layer2-"]:
            if forbidden in html:
                _fail(f"{case_dir.name} output.html leaks forbidden content: {forbidden}")
        for phrase in ["源头复核", "没有文章级链接", "href=\"#section-id\""]:
            if phrase not in case["prompt"]:
                _fail(f"{case_dir.name} prompt must describe source links and no-hash navigation")
        for leaked_field in ["source_url", "pdf_url", "original_url", "document_url"]:
            if leaked_field in case["prompt"] or leaked_field in case.get("prompt_en", ""):
                _fail(f"{case_dir.name} prompt must not expose internal source field name: {leaked_field}")
        if "统计数据" not in case["prompt"]:
            _fail(f"{case_dir.name} prompt must describe how optional statistics are handled")
        if "##" not in review or "源头" not in review:
            _fail(f"{case_dir.name} review.md must document Playbook review and source behavior")


def workbuddy_validate(source: Path) -> int:
    validator = EXPERT_MANAGER / "scripts" / "validate_expert.py"
    if not validator.exists():
        raise SystemExit(f"WorkBuddy validator not found: {validator}")

    WORKBUDDY_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    temp_parent = Path(tempfile.mkdtemp(prefix=".validate-fin-research-expert-", dir=WORKBUDDY_PLUGINS_DIR))
    try:
        temp_expert = temp_parent / "fin-research-expert"
        shutil.copytree(source, temp_expert, ignore=_copy_ignore)
        return subprocess.call([sys.executable, str(validator), str(temp_expert)])
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Fin Research Expert package locally.")
    parser.add_argument("--source", default=".", help="Source expert directory.")
    parser.add_argument("--workbuddy", action="store_true", help="Also run WorkBuddy expert-manager validate_expert.py when available.")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    basic_validate(source)
    if args.workbuddy:
        return workbuddy_validate(source)
    print("local validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
