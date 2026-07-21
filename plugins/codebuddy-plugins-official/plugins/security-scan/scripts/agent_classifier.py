from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover - py3.10 fallback
    tomllib = None  # type: ignore[assignment]


PROJECT_TYPE_WEB = "Web类项目"
PROJECT_TYPE_AI_AGENT = "AI Agent类项目"
PROJECT_TYPE_BACKEND = "后端服务类项目"
PROJECT_TYPE_MOBILE = "移动客户端类项目"
PROJECT_TYPE_DESKTOP = "桌面客户端类项目"
PROJECT_TYPE_MINI_PROGRAM = "小程序类项目"
PROJECT_TYPE_BROWSER_EXTENSION = "浏览器插件类项目"
PROJECT_TYPE_CLI = "命令行/工具类项目"
PROJECT_TYPE_SDK = "SDK/库类项目"
PROJECT_TYPE_CLOUD_NATIVE = "云原生/基础设施类项目"
PROJECT_TYPE_DATA_ML = "数据/算法类项目"
PROJECT_TYPE_GAME = "游戏类项目"
PROJECT_TYPE_UNKNOWN = "未知类目"

PRODUCT_CATEGORY_CODES = {
    PROJECT_TYPE_WEB: "web",
    PROJECT_TYPE_AI_AGENT: "ai_agent",
    PROJECT_TYPE_BACKEND: "backend",
    PROJECT_TYPE_MOBILE: "mobile",
    PROJECT_TYPE_DESKTOP: "desktop",
    PROJECT_TYPE_MINI_PROGRAM: "mini_program",
    PROJECT_TYPE_BROWSER_EXTENSION: "browser_extension",
    PROJECT_TYPE_CLI: "cli_tool",
    PROJECT_TYPE_SDK: "sdk_library",
    PROJECT_TYPE_CLOUD_NATIVE: "cloud_native",
    PROJECT_TYPE_DATA_ML: "data_ml",
    PROJECT_TYPE_GAME: "game",
    PROJECT_TYPE_UNKNOWN: "unknown",
}

AGENT_SUBTYPE_DISPLAY = {
    "coding-agent": "编码智能体",
    "browser-agent": "浏览器智能体",
    "mcp-agent": "MCP/工具智能体",
    "multi-agent-framework": "多智能体编排",
    "self-improving-agent": "自进化智能体",
    "memory-agent": "记忆型智能体",
    "rag-agent": "RAG/知识库智能体",
    "tool-agent": "工具调用智能体",
    "chat-agent": "对话智能体",
    "agent-framework": "通用智能体",
    "skill-agent": "技能型智能体",
    "autonomous-agent": "自主任务智能体",
    "personal-agent": "个人助理智能体",
    "unknown": "未知",
}

PRODUCT_TYPE_META = {
    "web_frontend": (PROJECT_TYPE_WEB, "前端应用"),
    "web_fullstack": (PROJECT_TYPE_WEB, "全栈应用"),
    "backend_api": (PROJECT_TYPE_BACKEND, "Web API服务"),
    "backend_rpc": (PROJECT_TYPE_BACKEND, "RPC/微服务"),
    "mobile_flutter": (PROJECT_TYPE_MOBILE, "Flutter客户端"),
    "mobile_react_native": (PROJECT_TYPE_MOBILE, "React Native客户端"),
    "mobile_android": (PROJECT_TYPE_MOBILE, "Android客户端"),
    "mobile_ios": (PROJECT_TYPE_MOBILE, "iOS客户端"),
    "desktop_electron": (PROJECT_TYPE_DESKTOP, "Electron客户端"),
    "desktop_tauri": (PROJECT_TYPE_DESKTOP, "Tauri客户端"),
    "desktop_native": (PROJECT_TYPE_DESKTOP, "原生桌面客户端"),
    "mini_wechat": (PROJECT_TYPE_MINI_PROGRAM, "微信小程序"),
    "mini_cross": (PROJECT_TYPE_MINI_PROGRAM, "跨端小程序"),
    "browser_extension": (PROJECT_TYPE_BROWSER_EXTENSION, "浏览器扩展"),
    "cli_tool": (PROJECT_TYPE_CLI, "命令行工具"),
    "sdk_library": (PROJECT_TYPE_SDK, "SDK/通用库"),
    "cloud_native": (PROJECT_TYPE_CLOUD_NATIVE, "容器/Kubernetes/Serverless"),
    "infra_iac": (PROJECT_TYPE_CLOUD_NATIVE, "IaC基础设施编排"),
    "data_ml": (PROJECT_TYPE_DATA_ML, "数据处理/机器学习"),
    "game_unity": (PROJECT_TYPE_GAME, "Unity游戏"),
    "game_unreal": (PROJECT_TYPE_GAME, "Unreal游戏"),
    "game_web": (PROJECT_TYPE_GAME, "Web游戏"),
}

DEPENDENCY_PRODUCT_HINTS = {
    # Web 前端 / 全栈
    "react": ("web_frontend", 18), "vue": ("web_frontend", 18), "@angular/core": ("web_frontend", 18),
    "svelte": ("web_frontend", 18), "vite": ("web_frontend", 10), "webpack": ("web_frontend", 8),
    "next": ("web_fullstack", 22), "next.js": ("web_fullstack", 22), "nuxt": ("web_fullstack", 22),
    "@remix-run/react": ("web_fullstack", 18),
    # 后端服务
    "express": ("backend_api", 20), "koa": ("backend_api", 18), "fastify": ("backend_api", 18),
    "@nestjs/core": ("backend_api", 22), "django": ("backend_api", 22), "flask": ("backend_api", 20),
    "fastapi": ("backend_api", 22), "starlette": ("backend_api", 16), "spring-boot-starter-web": ("backend_api", 22),
    "gin-gonic/gin": ("backend_api", 20), "labstack/echo": ("backend_api", 18), "gofiber/fiber": ("backend_api", 18),
    "grpc": ("backend_rpc", 16), "@grpc/grpc-js": ("backend_rpc", 16), "google.golang.org/grpc": ("backend_rpc", 18),
    # 客户端
    "react-native": ("mobile_react_native", 28), "expo": ("mobile_react_native", 24), "flutter": ("mobile_flutter", 28),
    "@capacitor/core": ("mobile_react_native", 16), "cordova": ("mobile_react_native", 14),
    "electron": ("desktop_electron", 28), "@tauri-apps/api": ("desktop_tauri", 28), "tauri": ("desktop_tauri", 24),
    # 小程序 / 扩展
    "@tarojs/taro": ("mini_cross", 24), "uni-app": ("mini_cross", 22), "miniprogram-api-typings": ("mini_wechat", 22),
    "webextension-polyfill": ("browser_extension", 24),
    # CLI / SDK
    "commander": ("cli_tool", 18), "yargs": ("cli_tool", 16), "clipanion": ("cli_tool", 14),
    "click": ("cli_tool", 18), "typer": ("cli_tool", 18), "cobra": ("cli_tool", 18), "urfave/cli": ("cli_tool", 16),
    # 数据算法
    "pandas": ("data_ml", 14), "numpy": ("data_ml", 10), "scikit-learn": ("data_ml", 18),
    "torch": ("data_ml", 18), "tensorflow": ("data_ml", 18), "xgboost": ("data_ml", 16),
    # 游戏
    "phaser": ("game_web", 22), "pixi.js": ("game_web", 18), "cocos": ("game_web", 20),
}

PATH_PRODUCT_HINTS = (
    ("mobile_flutter", 30, ("pubspec.yaml", "lib/main.dart"), (r"flutter:", r"package:flutter")),
    ("mobile_android", 28, ("AndroidManifest.xml", "app/build.gradle", "build.gradle"), (r"com\.android\.application", r"androidx\.")),
    ("mobile_ios", 28, ("Info.plist", "Podfile", ".xcodeproj/"), (r"UIApplication", r"SwiftUI", r"UIKit")),
    ("mini_wechat", 28, ("project.config.json", "app.json", ".wxml"), (r"miniprogram", r"微信小程序", r"wx\.")),
    ("browser_extension", 28, ("manifest.json",), (r"manifest_version", r"content_scripts", r"background")),
    ("cloud_native", 22, ("Dockerfile", "docker-compose.yml", "Chart.yaml", "kustomization.yaml"), (r"apiVersion:\s*apps/", r"kind:\s*(Deployment|Service|Ingress)")),
    ("infra_iac", 24, (".tf", "serverless.yml", "pulumi.yaml"), (r"resource\s+\"", r"provider\s+\"", r"service:")),
    ("game_unity", 30, ("ProjectSettings/ProjectVersion.txt", "Assets/"), (r"m_EditorVersion", r"UnityEngine")),
    ("game_unreal", 30, (".uproject", "Source/"), (r"Unreal Engine", r"ModuleRules")),
    ("sdk_library", 12, ("setup.py", "setup.cfg"), (r"from setuptools import setup",)),
)

KNOWN_AGENT_FAMILIES: dict[str, dict[str, Any]] = {
    "openclaw": {
        "display": "OpenClaw",
        "patterns": [
            r"\bopenclaw\b",
            r"openclaw[_-]?agent",
        ],
        "types": ["personal-agent", "browser-agent", "coding-agent"],
    },
    "hermes": {
        "display": "Hermes Agent",
        "patterns": [
            r"\bhermes[_ -]?agent\b",
            r"nous[_ -]?research.*hermes",
        ],
        "types": ["self-improving-agent", "memory-agent", "coding-agent"],
    },
    "claude-code": {
        "display": "Claude Code",
        "patterns": [r"\bclaude code\b", r"claude_code", r"CLAUDE\.md"],
        "types": ["coding-agent"],
    },
    "codex-cli": {
        "display": "Codex CLI",
        "patterns": [r"\bcodex cli\b", r"\.codex/", r"AGENTS\.md"],
        "types": ["coding-agent"],
    },
    "cline": {
        "display": "Cline",
        "patterns": [r"\bcline\b", r"\.clinerules"],
        "types": ["coding-agent"],
    },
    "cursor": {
        "display": "Cursor",
        "patterns": [r"\bcursor\b", r"\.cursorrules", r"\.cursor/"],
        "types": ["coding-agent"],
    },
    "openhands": {
        "display": "OpenHands",
        "patterns": [r"\bopenhands\b", r"software-agent-sdk"],
        "types": ["coding-agent"],
    },
    "swe-agent": {
        "display": "SWE-agent",
        "patterns": [r"\bswe-agent\b", r"\bswe_agent\b"],
        "types": ["coding-agent"],
    },
    "browser-use": {
        "display": "browser-use",
        "patterns": [r"\bbrowser-use\b", r"\bbrowser_use\b"],
        "types": ["browser-agent"],
    },
    "crewai": {
        "display": "CrewAI",
        "patterns": [r"\bcrewai\b", r"from crewai import", r"Crew\s*\("],
        "types": ["multi-agent-framework"],
    },
    "autogen": {
        "display": "AutoGen",
        "patterns": [r"\bautogen\b", r"\bautogen_agentchat\b", r"AssistantAgent\s*\("],
        "types": ["multi-agent-framework"],
    },
    "langchain": {
        "display": "LangChain Agent",
        "patterns": [r"\blangchain\b", r"create_(?:openai_)?tools_agent", r"AgentExecutor", r"bind_tools\s*\("],
        "types": ["agent-framework", "tool-agent"],
    },
    "llamaindex": {
        "display": "LlamaIndex Agent",
        "patterns": [r"\bllama[-_]?index\b", r"llama_index", r"ReActAgent"],
        "types": ["rag-agent", "agent-framework"],
    },
    "semantic-kernel": {
        "display": "Semantic Kernel",
        "patterns": [r"semantic[-_ ]kernel", r"KernelFunction", r"@kernel_function"],
        "types": ["agent-framework", "tool-agent"],
    },
    "openai-agents": {
        "display": "OpenAI Agents SDK",
        "patterns": [r"openai[-_ ]agents", r"from agents import Agent", r"Agent\s*\(.*tools\s="],
        "types": ["agent-framework", "tool-agent"],
    },
}

LLM_PROVIDER_PATTERNS = {
    "openai": r"\b(openai|OpenAI|chat\.completions\.create|responses\.create|OPENAI_API_KEY)\b",
    "anthropic": r"\b(anthropic|Anthropic|messages\.create|claude-|ANTHROPIC_API_KEY)\b",
    "gemini": r"\b(gemini|google\.generativeai|genai\.|GenerativeModel|GOOGLE_API_KEY|GEMINI_API_KEY)\b",
    "openrouter": r"\b(openrouter|openrouter\.ai|OPENROUTER_API_KEY)\b",
    "ollama": r"\b(ollama|OLLAMA_HOST)\b",
    "litellm": r"\b(litellm|completion\()\b",
    "vllm": r"\b(vllm|VLLM)\b",
    "bedrock": r"\b(bedrock|boto3\.client\(['\"]bedrock)\b",
    "cohere": r"\b(cohere|Cohere)\b",
    "mistral": r"\b(mistral|Mistral)\b",
    "azure-openai": r"\b(AzureOpenAI|AZURE_OPENAI|azure[-_]?openai)\b",
}

DEPENDENCY_FAMILY_HINTS = {
    "crewai": "crewai",
    "autogen": "autogen",
    "pyautogen": "autogen",
    "langchain": "langchain",
    "llama-index": "llamaindex",
    "llama_index": "llamaindex",
    "semantic-kernel": "semantic-kernel",
    "openai-agents": "openai-agents",
    "browser-use": "browser-use",
    "browser_use": "browser-use",
    "openhands": "openhands",
    "swe-agent": "swe-agent",
}

AGENT_FRAMEWORK_DEPENDENCIES = {
    "crewai",
    "autogen",
    "pyautogen",
    "langchain",
    "llama-index",
    "llama_index",
    "semantic-kernel",
    "haystack-ai",
    "openai-agents",
    "smolagents",
    "agno",
    "browser-use",
    "mcp",
}

TOOL_PATTERNS = [
    r"\btool_calls?\b",
    r"\bfunction_call\b",
    r"@(?:mcp\.)?tool",
    r"@kernel_function",
    r"\btools\s*=",
    r"\bbind_tools\s*\(",
    r"\btool_choice\s*=",
    r"\bcreate_(?:openai_)?tools_agent\s*\(",
    r"\bcreate_react_agent\s*\(",
    r"\bAgentExecutor\b",
    r"\bMCP\b|\bmcpServers\b",
]

CONVERSATION_PATTERNS = [
    r"\bmessages\s*=",
    r"\bconversation",
    r"\bchat_history\b",
    r"\brole\s*[:=]\s*['\"](?:system|user|assistant|tool)['\"]",
    r"\bsystem[_ -]?prompt\b",
    r"\bassistant\b.{0,40}\buser\b",
]

MEMORY_PATTERNS = [
    r"\bmemory\b",
    r"\blong[-_ ]?term[-_ ]?memory\b",
    r"\bvectorstore\b",
    r"\bvector_store\b",
    r"\bembedding(?:s)?\b",
    r"\bchroma(?:db)?\b",
    r"\bfaiss\b",
    r"\bqdrant\b",
    r"\bpinecone\b",
    r"\bweaviate\b",
    r"\badd_documents\b",
]

AUTONOMY_PATTERNS = [
    r"\bplan\b.{0,80}\bact\b",
    r"\bobserve\b",
    r"\btask_loop\b",
    r"\bwhile\s+True\b",
    r"\bmax_iterations\b",
    r"\bAgentExecutor\b",
    r"\bautonomous\b",
    r"\bscheduler\b",
]

TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rs", ".rb", ".php",
    ".cs", ".cpp", ".c", ".h", ".hpp", ".swift", ".scala", ".vue", ".svelte", ".dart", ".xml", ".plist",
    ".tf", ".uproject", ".ipynb", ".md", ".mdx", ".txt", ".json", ".jsonc", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".env", ".sh", ".bash", ".zsh",
}
MANIFEST_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "poetry.lock", "pipfile",
    "go.mod", "pom.xml", "build.gradle", "settings.gradle", "cargo.toml", "gemfile", "composer.json",
    "pubspec.yaml", "project.config.json", "app.json", "manifest.json", "pages.json", "Dockerfile", "Chart.yaml",
    "CLAUDE.md", "AGENTS.md", ".cursorrules", ".clinerules",
}
SKIP_DIR_NAMES = {
    ".git", ".hg", ".svn", ".codebuddy", "node_modules", "vendor", "dist", "build", "target", "coverage",
    "__pycache__", ".venv", "venv", "env", ".next", ".nuxt", ".cache", ".pytest_cache",
}
SKIP_GLOBS = ("*.min.js", "*.bundle.js", "*.map", "*.lock")

CODE_SIGNAL_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".go", ".rs", ".rb", ".php",
    ".cs", ".cpp", ".c", ".h", ".hpp", ".swift", ".scala", ".vue", ".svelte", ".dart",
}
PRODUCT_CONTENT_SUFFIXES = CODE_SIGNAL_SUFFIXES | {".xml", ".plist", ".tf", ".uproject"}
LOW_CONFIDENCE_CONTEXT_PREFIXES = (
    "docs/", "doc/", "references/", "reference/", "resource/", "resources/", "test/", "tests/", "example/", "examples/",
)
WEB_SERVICE_PRODUCT_CATEGORIES = {PROJECT_TYPE_WEB, PROJECT_TYPE_BACKEND}
DEV_ASSISTANT_FAMILIES = {"claude-code", "codex-cli", "cline", "cursor"}
DEV_ASSISTANT_MANIFEST_NAMES = {"CLAUDE.md", "AGENTS.md", ".cursorrules", ".clinerules"}


@dataclass
class FileContext:
    path: Path
    relative_path: str
    text: str

    @property
    def name(self) -> str:
        return self.path.name


class AgentProjectClassifier:
    """Classify whether a repository is an AI Agent project and why."""

    def __init__(self, contexts: list[FileContext]) -> None:
        self.contexts = contexts

    def classify(self) -> dict[str, Any]:
        signals: list[dict[str, Any]] = []
        product_signals: list[dict[str, Any]] = []
        model_providers: set[str] = set()
        known_families: dict[str, dict[str, Any]] = {}
        agent_types: set[str] = set()
        counters: dict[str, int] = defaultdict(int)
        product_scores: dict[str, int] = defaultdict(int)
        product_frameworks: dict[str, set[str]] = defaultdict(set)

        for ctx in self.contexts:
            text = ctx.text
            lowered_path = ctx.relative_path.lower()
            data = parse_structured(ctx)
            trusted_agent_context = _is_agent_signal_context(ctx)
            if isinstance(data, dict):
                if trusted_agent_context:
                    for signal in _manifest_signals(ctx, data):
                        _append_signal(signals, counters, signal, agent_types)
                for product_signal in _manifest_product_signals(ctx, data):
                    _append_product_signal(product_signals, product_scores, product_frameworks, product_signal)

            dep_names = _dependency_names(ctx, data if isinstance(data, dict) else {})
            for dep_name in dep_names:
                dep_lower = dep_name.lower()
                if dep_lower in AGENT_FRAMEWORK_DEPENDENCIES:
                    _append_signal(
                        signals,
                        counters,
                        _signal("agent-framework", ctx, f"Agent framework dependency `{dep_name}`", 22, agent_type="agent-framework"),
                        agent_types,
                    )
                family_key = DEPENDENCY_FAMILY_HINTS.get(dep_lower)
                if family_key:
                    _add_family(known_families, family_key, ctx.relative_path, f"dependency `{dep_name}`")
                product_hint = DEPENDENCY_PRODUCT_HINTS.get(dep_lower)
                if product_hint:
                    product_key, weight = product_hint
                    _append_product_signal(
                        product_signals,
                        product_scores,
                        product_frameworks,
                        _product_signal(product_key, ctx, f"dependency `{dep_name}`", weight, framework=dep_name),
                    )

            for product_signal in _path_product_signals(ctx):
                _append_product_signal(product_signals, product_scores, product_frameworks, product_signal)

            if trusted_agent_context:
                for provider, pattern in LLM_PROVIDER_PATTERNS.items():
                    if re.search(pattern, text, re.IGNORECASE):
                        model_providers.add(provider)
                        _append_signal(
                            signals,
                            counters,
                            _signal("model-provider", ctx, f"LLM provider signal `{provider}`", 20),
                            agent_types,
                        )

                for category, patterns, weight, agent_type in (
                    ("conversation", CONVERSATION_PATTERNS, 12, "chat-agent"),
                    ("tool-use", TOOL_PATTERNS, 22, "tool-agent"),
                    ("memory-rag", MEMORY_PATTERNS, 10, "rag-agent"),
                    ("autonomy", AUTONOMY_PATTERNS, 12, "autonomous-agent"),
                ):
                    matched = _first_pattern(text, patterns)
                    if matched:
                        _append_signal(signals, counters, _signal(category, ctx, matched, weight, agent_type=agent_type), agent_types)

                for family_key, meta in KNOWN_AGENT_FAMILIES.items():
                    if family_key in DEV_ASSISTANT_FAMILIES:
                        continue
                    for pattern in meta["patterns"]:
                        if re.search(pattern, text, re.IGNORECASE) or re.search(pattern, lowered_path, re.IGNORECASE):
                            _add_family(known_families, family_key, ctx.relative_path, f"matched `{pattern}`")
                            _append_signal(
                                signals,
                                counters,
                                _signal("known-agent-family", ctx, f"{meta['display']} fingerprint", 28, agent_type=meta["types"][0]),
                                agent_types,
                            )
                            agent_types.update(meta["types"])
                            break

        product_profile = _product_profile(product_scores, product_frameworks, product_signals)
        if _is_web_service_profile(product_profile):
            agent_types, known_families = _drop_coding_agent_for_web_service(agent_types, known_families)
        deduped = _dedupe_signals(signals)
        score = min(100, sum(int(signal["weight"]) for signal in deduped))
        llm_capability = _has_llm_capability(counters, model_providers)
        tool_execution_capability = _has_tool_execution_capability(counters)
        confidence = _confidence(score, counters, llm_capability, tool_execution_capability)
        is_agent = bool(agent_types) and llm_capability and tool_execution_capability and confidence in {"high", "medium"}
        primary_type = _primary_agent_type(agent_types, counters)
        evidence = _top_evidence(signals)
        agent_subtype = _agent_subtype(primary_type, agent_types, known_families)
        if is_agent:
            project_type = PROJECT_TYPE_AI_AGENT
            project_type_code = _product_category_code(PROJECT_TYPE_AI_AGENT)
            product_category = PROJECT_TYPE_AI_AGENT
            product_subtype = agent_subtype
            product_shape = product_category
            product_shape_evidence_chain = _agent_product_evidence_chain(
                product_shape=product_shape,
                confidence=confidence,
                score=score,
                evidence=evidence,
                llm_capability=llm_capability,
                tool_execution_capability=tool_execution_capability,
                model_providers=model_providers,
                primary_type=primary_type,
            )
            product_shape_decision = product_shape_evidence_chain["decision"]
        else:
            project_type = product_profile["project_type"]
            project_type_code = product_profile["project_type_code"]
            product_category = product_profile["product_category"]
            product_subtype = product_profile["product_subtype"]
            product_shape = product_profile["product_shape"]
            product_shape_decision = product_profile["product_shape_decision"]
            product_shape_evidence_chain = product_profile["product_shape_evidence_chain"]

        return {
            "schema": "agentsecscan.agent_profile.v1",
            "project_type": project_type,
            "project_type_code": project_type_code,
            "product_category": product_category,
            "product_subtype": product_subtype,
            "product_shape": product_shape,
            "product_shape_decision": product_shape_decision,
            "product_shape_evidence_chain": product_shape_evidence_chain,
            "product_frameworks": product_profile.get("frameworks", []),
            "product_shape_candidates": product_profile.get("candidates", []),
            "is_agent_project": is_agent,
            "agent_confidence": confidence,
            "agent_score": score,
            "agent_type": primary_type,
            "agent_subtype": agent_subtype if is_agent else "",
            "agent_types": sorted(agent_types),
            "capabilities": {
                "llm_call": llm_capability,
                "tool_execution": tool_execution_capability,
                "classification_standard": "同时发现 LLM 调用能力与工具执行/注册能力才判定为 AI Agent 类项目",
            },
            "known_agent_families": sorted(known_families.values(), key=lambda item: item["name"]),
            "model_providers": sorted(model_providers),
            "signal_counts": dict(sorted(counters.items())),
            "evidence": evidence,
            "decision_reason": _decision_reason(is_agent, confidence, primary_type, evidence, llm_capability, tool_execution_capability),
        }


def classify_agent_project(contexts: list[FileContext]) -> dict[str, Any]:
    return AgentProjectClassifier(contexts).classify()


def classify_project_path(project_path: str | Path, *, max_files: int = 1000, max_bytes_per_file: int = 256 * 1024) -> dict[str, Any]:
    root = Path(project_path).resolve()
    contexts = collect_file_contexts(root, max_files=max_files, max_bytes_per_file=max_bytes_per_file)
    profile = classify_agent_project(contexts)
    profile["project_path"] = str(root)
    profile["scanned_files"] = len(contexts)
    return profile


def collect_file_contexts(root: Path, *, max_files: int = 1000, max_bytes_per_file: int = 256 * 1024) -> list[FileContext]:
    contexts: list[FileContext] = []
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for name in files:
            if len(contexts) >= max_files:
                return contexts
            path = Path(current_root) / name
            rel = path.relative_to(root).as_posix()
            if not _should_scan_file(path, rel):
                continue
            try:
                if path.stat().st_size > max_bytes_per_file:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeError):
                continue
            contexts.append(FileContext(path=path, relative_path=rel, text=text))
    return contexts


def parse_structured(ctx: FileContext) -> Any:
    if ctx.name == "package.json" or ctx.path.suffix.lower() == ".json":
        try:
            return json.loads(ctx.text)
        except json.JSONDecodeError:
            return None
    if ctx.name in {"pyproject.toml", "cargo.toml"} or ctx.path.suffix.lower() == ".toml":
        if tomllib is None:
            return None
        try:
            return tomllib.loads(ctx.text)
        except Exception:
            return None
    return None


def write_detection_result(profile: dict[str, Any], batch_dir: str | Path | None = None, output: str | Path | None = None) -> None:
    targets: list[Path] = []
    if output:
        targets.append(Path(output))
    if batch_dir:
        targets.append(Path(batch_dir) / "project-type.json")
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    if batch_dir:
        _merge_project_type_into_batch_plan(Path(batch_dir), profile)


def _merge_project_type_into_batch_plan(batch_dir: Path, profile: dict[str, Any]) -> None:
    batch_plan_file = batch_dir / "batch-plan.json"
    if not batch_plan_file.exists():
        return
    try:
        with batch_plan_file.open("r", encoding="utf-8") as f:
            batch_plan = json.load(f)
        if not isinstance(batch_plan, dict):
            return
        batch_plan["project_type"] = profile.get("project_type", PROJECT_TYPE_UNKNOWN)
        batch_plan["project_type_code"] = profile.get("project_type_code", "unknown")
        batch_plan["product_category"] = profile.get("product_category", PROJECT_TYPE_UNKNOWN)
        batch_plan["product_subtype"] = profile.get("product_subtype", "通用代码")
        batch_plan["product_shape"] = profile.get("product_shape", "")
        batch_plan["product_shape_decision"] = profile.get("product_shape_decision", "")
        batch_plan["product_shape_evidence_chain"] = profile.get("product_shape_evidence_chain", {})
        batch_plan["agent_profile"] = profile
        with batch_plan_file.open("w", encoding="utf-8") as f:
            json.dump(batch_plan, f, ensure_ascii=False, indent=2)
    except Exception:
        return


def _should_scan_file(path: Path, rel: str) -> bool:
    if path.name in MANIFEST_NAMES:
        return True
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES:
        return False
    return not any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in SKIP_GLOBS)


def _normalized_rel_path(ctx: FileContext) -> str:
    return ctx.relative_path.replace("\\", "/")


def _is_low_confidence_context(ctx: FileContext) -> bool:
    rel = _normalized_rel_path(ctx).lower()
    return rel.endswith("scripts/agent_classifier.py") or any(rel.startswith(prefix) or f"/{prefix}" in rel for prefix in LOW_CONFIDENCE_CONTEXT_PREFIXES)


def _is_agent_signal_context(ctx: FileContext) -> bool:
    if _is_low_confidence_context(ctx) or ctx.name in DEV_ASSISTANT_MANIFEST_NAMES:
        return False
    suffix = ctx.path.suffix.lower()
    return suffix in CODE_SIGNAL_SUFFIXES or ctx.name in MANIFEST_NAMES


def _is_product_content_context(ctx: FileContext) -> bool:
    if _is_low_confidence_context(ctx):
        return False
    return ctx.path.suffix.lower() in PRODUCT_CONTENT_SUFFIXES


def _is_web_service_profile(product_profile: dict[str, Any]) -> bool:
    return product_profile.get("product_category") in WEB_SERVICE_PRODUCT_CATEGORIES


def _drop_coding_agent_for_web_service(
    agent_types: set[str],
    known_families: dict[str, dict[str, Any]],
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    filtered_types = {agent_type for agent_type in agent_types if agent_type != "coding-agent"}
    filtered_families = {
        key: value
        for key, value in known_families.items()
        if "coding-agent" not in value.get("agent_types", [])
    }
    return filtered_types, filtered_families


def _product_signal(product_key: str, ctx: FileContext, reason: str, weight: int, *, framework: str = "") -> dict[str, Any]:
    return {
        "product_key": product_key,
        "path": ctx.relative_path,
        "reason": reason,
        "weight": weight,
        "framework": framework,
    }


def _append_product_signal(
    signals: list[dict[str, Any]],
    scores: dict[str, int],
    frameworks: dict[str, set[str]],
    signal: dict[str, Any],
) -> None:
    signals.append(signal)
    product_key = signal["product_key"]
    scores[product_key] += int(signal.get("weight", 0))
    framework = signal.get("framework")
    if framework:
        frameworks[product_key].add(str(framework))


def _manifest_product_signals(ctx: FileContext, data: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if ctx.name == "package.json":
        if isinstance(data.get("bin"), (dict, str)):
            signals.append(_product_signal("cli_tool", ctx, "package.json bin entry", 24, framework="npm-bin"))
        if isinstance(data.get("exports"), (dict, str)) or data.get("types") or data.get("typings"):
            signals.append(_product_signal("sdk_library", ctx, "package exports/types entry", 12, framework="npm-library"))
        scripts = data.get("scripts", {})
        if isinstance(scripts, dict):
            script_text = " ".join(str(v) for v in scripts.values()).lower()
            if "next" in script_text:
                signals.append(_product_signal("web_fullstack", ctx, "package scripts use next", 18, framework="next"))
            if "vite" in script_text:
                signals.append(_product_signal("web_frontend", ctx, "package scripts use vite", 12, framework="vite"))
            if "electron" in script_text:
                signals.append(_product_signal("desktop_electron", ctx, "package scripts use electron", 24, framework="electron"))
    if ctx.name == "pyproject.toml":
        project = data.get("project", {})
        if isinstance(project, dict) and isinstance(project.get("scripts"), dict):
            signals.append(_product_signal("cli_tool", ctx, "pyproject project.scripts", 24, framework="python-entrypoint"))
        if isinstance(project, dict) and project.get("name"):
            signals.append(_product_signal("sdk_library", ctx, "pyproject project.name", 8, framework="python-package"))
    if ctx.name == "manifest.json" and data.get("manifest_version"):
        signals.append(_product_signal("browser_extension", ctx, "browser extension manifest", 30, framework="webextension"))
    if ctx.name == "project.config.json" and (data.get("appid") or data.get("miniprogramRoot")):
        signals.append(_product_signal("mini_wechat", ctx, "WeChat miniprogram project config", 30, framework="wechat-miniprogram"))
    return signals


def _path_product_signals(ctx: FileContext) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    rel = _normalized_rel_path(ctx)
    lowered = rel.lower()
    allow_content_signal = _is_product_content_context(ctx)
    for product_key, weight, path_markers, content_patterns in PATH_PRODUCT_HINTS:
        path_hit = any(_path_marker_matches(lowered, marker.lower()) for marker in path_markers)
        content_hit = allow_content_signal and any(re.search(pattern, ctx.text, re.IGNORECASE) for pattern in content_patterns)
        if product_key == "browser_extension":
            matched = path_hit and content_hit
        else:
            matched = path_hit or content_hit
        if matched:
            reason = "path/content product marker" if content_hit else "path product marker"
            signals.append(_product_signal(product_key, ctx, reason, weight, framework=PRODUCT_TYPE_META[product_key][1]))
    if ctx.path.suffix.lower() == ".ipynb":
        signals.append(_product_signal("data_ml", ctx, "Jupyter notebook", 18, framework="jupyter"))
    return signals


def _path_marker_matches(path: str, marker: str) -> bool:
    marker = marker.replace("\\", "/")
    if marker.startswith("."):
        return path.endswith(marker)
    if marker.endswith("/"):
        return path.startswith(marker) or f"/{marker}" in path
    if "/" in marker:
        return path == marker or path.endswith(f"/{marker}") or f"/{marker}/" in path
    return path == marker or path.endswith(f"/{marker}") or f"/{marker}/" in path


def _agent_subtype(primary_type: str, agent_types: set[str], known_families: dict[str, dict[str, Any]]) -> str:
    coding_families = {"claude-code", "codex-cli", "cline", "cursor", "openhands", "swe-agent", "openclaw"}
    if any(key in known_families for key in coding_families):
        return "编码智能体"
    if "browser-agent" in agent_types:
        return "浏览器智能体"
    if "mcp-agent" in agent_types or "tool-agent" in agent_types:
        return "MCP/工具智能体"
    if "rag-agent" in agent_types or "memory-agent" in agent_types:
        return "RAG/知识库智能体"
    return AGENT_SUBTYPE_DISPLAY.get(primary_type, "通用智能体")


def _product_category_code(category: str) -> str:
    return PRODUCT_CATEGORY_CODES.get(category, "unknown")


def _product_profile(
    scores: dict[str, int],
    frameworks: dict[str, set[str]],
    signals: list[dict[str, Any]],
) -> dict[str, Any]:
    adjusted = dict(scores)
    if adjusted.get("web_frontend", 0) and adjusted.get("backend_api", 0):
        adjusted["web_fullstack"] = max(adjusted.get("web_fullstack", 0), adjusted["web_frontend"] + adjusted["backend_api"] // 2)
        frameworks["web_fullstack"].update(frameworks.get("web_frontend", set()))
        frameworks["web_fullstack"].update(frameworks.get("backend_api", set()))
    if not adjusted:
        conclusion = PROJECT_TYPE_UNKNOWN
        decision = "未知类目：score=0；未命中依赖、Manifest、路径或内容标记。"
        return {
            "project_type": PROJECT_TYPE_UNKNOWN,
            "project_type_code": "unknown",
            "product_category": PROJECT_TYPE_UNKNOWN,
            "product_subtype": "通用代码",
            "product_shape": conclusion,
            "product_shape_decision": decision,
            "product_shape_evidence_chain": {
                "conclusion": conclusion,
                "decision": decision,
                "standard": "依赖、Manifest、路径/内容信号加权评分，取最高分一级类目。",
                "score": 0,
                "basis": ["score=0; evidence=none"],
                "evidence": [],
                "competingCandidates": [],
            },
            "frameworks": [],
            "candidates": [],
        }
    ranked = sorted(adjusted.items(), key=lambda item: (-item[1], item[0]))
    best_key, best_score = ranked[0]
    category, subtype = PRODUCT_TYPE_META.get(best_key, (PROJECT_TYPE_UNKNOWN, "通用代码"))
    candidates = []
    for key, score in ranked[:5]:
        cand_category, _ = PRODUCT_TYPE_META.get(key, (PROJECT_TYPE_UNKNOWN, "通用代码"))
        candidates.append({
            "code": key,
            "project_type": cand_category,
            "product_shape": cand_category,
            "score": score,
            "frameworks": sorted(frameworks.get(key, set())),
            "evidence": _top_product_evidence(signals, key),
        })
    conclusion = category if best_score > 0 else PROJECT_TYPE_UNKNOWN
    evidence_chain = _product_evidence_chain(
        conclusion=conclusion,
        category=category,
        best_score=best_score,
        ranked=ranked,
        frameworks=frameworks,
        signals=signals,
        best_key=best_key,
    )
    return {
        "project_type": category if best_score > 0 else PROJECT_TYPE_UNKNOWN,
        "project_type_code": _product_category_code(category) if best_score > 0 else "unknown",
        "product_category": category,
        "product_subtype": subtype,
        "product_shape": conclusion,
        "product_shape_decision": evidence_chain["decision"],
        "product_shape_evidence_chain": evidence_chain,
        "frameworks": sorted(frameworks.get(best_key, set())),
        "candidates": candidates,
    }


def _top_product_evidence(signals: list[dict[str, Any]], product_key: str) -> list[dict[str, Any]]:
    related = [signal for signal in signals if signal.get("product_key") == product_key]
    related.sort(key=lambda item: (-int(item.get("weight", 0)), item.get("path", "")))
    return [
        {key: value for key, value in signal.items() if key != "weight" and value}
        for signal in related[:5]
    ]


def _product_evidence_chain(
    *,
    conclusion: str,
    category: str,
    best_score: int,
    ranked: list[tuple[str, int]],
    frameworks: dict[str, set[str]],
    signals: list[dict[str, Any]],
    best_key: str,
) -> dict[str, Any]:
    top_evidence = _top_product_evidence_with_weight(signals, best_key)
    competing = []
    for key, score in ranked[:5]:
        cand_category, _ = PRODUCT_TYPE_META.get(key, (PROJECT_TYPE_UNKNOWN, "通用代码"))
        competing.append({
            "code": key,
            "product_shape": cand_category,
            "score": score,
        })
    framework_text = ",".join(sorted(frameworks.get(best_key, set()))) or "none"
    evidence_summary = _compact_evidence_summary(top_evidence)
    runner_up = "none"
    if len(competing) > 1:
        runner_up = f"{competing[1]['product_shape']}:{competing[1]['score']}"
    decision = (
        f"{conclusion}：score={best_score}; frameworks={framework_text}; "
        f"evidence={evidence_summary}; runner_up={runner_up}。"
    )
    return {
        "conclusion": conclusion,
        "category": category,
        "decision": decision,
        "standard": "依赖、Manifest、路径/内容信号加权评分，取最高分一级类目。",
        "score": best_score,
        "basis": [
            f"winner={conclusion}; score={best_score}",
            f"frameworks={framework_text}",
            f"runner_up={runner_up}",
        ],
        "evidence": top_evidence,
        "competingCandidates": competing,
    }


def _top_product_evidence_with_weight(signals: list[dict[str, Any]], product_key: str) -> list[dict[str, Any]]:
    related = [signal for signal in signals if signal.get("product_key") == product_key]
    related.sort(key=lambda item: (-int(item.get("weight", 0)), item.get("path", "")))
    return [
        _format_product_evidence(signal, index + 1)
        for index, signal in enumerate(related[:8])
    ]


def _format_product_evidence(signal: dict[str, Any], step: int) -> dict[str, Any]:
    reason = str(signal.get("reason") or "")
    item = {
        "rank": step,
        "source": _product_signal_source(reason),
        "path": signal.get("path", ""),
        "signal": _product_signal_reason_zh(reason),
        "weight": int(signal.get("weight", 0)),
    }
    framework = signal.get("framework")
    if framework:
        item["framework"] = framework
    return item


def _compact_evidence_summary(evidence: list[dict[str, Any]], limit: int = 3) -> str:
    parts = []
    for item in evidence[:limit]:
        path = item.get("path") or "<unknown>"
        signal = item.get("signal") or item.get("reason") or item.get("category") or "signal"
        weight = item.get("weight", item.get("score", ""))
        suffix = f"(+{weight})" if weight != "" else ""
        parts.append(f"{path}:{signal}{suffix}")
    return "; ".join(parts) if parts else "none"


def _product_signal_source(reason: str) -> str:
    if reason.startswith("dependency"):
        return "依赖"
    if "package" in reason or "pyproject" in reason or "manifest" in reason or "project config" in reason:
        return "Manifest"
    if "path/content" in reason:
        return "路径/内容"
    if "path" in reason:
        return "路径"
    if "Jupyter" in reason:
        return "Notebook"
    return "代码/配置"


def _product_signal_reason_zh(reason: str) -> str:
    if reason.startswith("dependency `"):
        return reason.replace("dependency `", "dep:", 1).rstrip("`")
    mapping = {
        "package.json bin entry": "pkg.bin",
        "package exports/types entry": "pkg.exports/types",
        "package scripts use next": "script:next",
        "package scripts use vite": "script:vite",
        "package scripts use electron": "script:electron",
        "pyproject project.scripts": "pyproject.scripts",
        "pyproject project.name": "pyproject.name",
        "browser extension manifest": "manifest_version",
        "WeChat miniprogram project config": "wechat.project.config",
        "path/content product marker": "path/content-marker",
        "path product marker": "path-marker",
        "Jupyter notebook": "jupyter-notebook",
    }
    return mapping.get(reason, reason)


def _manifest_signals(ctx: FileContext, data: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if isinstance(data.get("mcpServers"), dict) or isinstance(data.get("servers"), dict):
        signals.append(_signal("mcp", ctx, "MCP server configuration", 28, agent_type="mcp-agent"))
    if isinstance(data.get("tools"), list) or isinstance(data.get("tool"), dict):
        signals.append(_signal("tool-use", ctx, "Tool schema or tool list in manifest", 22, agent_type="tool-agent"))
    if isinstance(data.get("permissions"), list) or isinstance(data.get("capabilities"), list):
        signals.append(_signal("skill-manifest", ctx, "Skill/Agent manifest permissions or capabilities", 18, agent_type="skill-agent"))
    return signals


def _dependency_names(ctx: FileContext, data: dict[str, Any]) -> list[str]:
    if ctx.name == "package.json":
        names: list[str] = []
        for bucket in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            values = data.get(bucket)
            if isinstance(values, dict):
                names.extend(str(name) for name in values)
        return names
    if ctx.name == "pyproject.toml":
        project = data.get("project", {})
        deps = project.get("dependencies") if isinstance(project, dict) else None
        names = [_dependency_name_from_spec(str(dep)) for dep in deps] if isinstance(deps, list) else []
        tool = data.get("tool", {})
        poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
        poetry_deps = poetry.get("dependencies", {}) if isinstance(poetry, dict) else {}
        if isinstance(poetry_deps, dict):
            names.extend(str(name).lower() for name in poetry_deps if name.lower() != "python")
        return names
    if ctx.name in {"requirements.txt", "requirements-dev.txt"}:
        return [_dependency_name_from_spec(line) for line in ctx.text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if ctx.name == "go.mod":
        return [_dependency_name_from_spec(line.replace("require", "").strip()) for line in ctx.text.splitlines() if line.strip().startswith("require")]
    return []


def _dependency_name_from_spec(spec: str) -> str:
    return re.split(r"\s|==|>=|<=|~=|>|<|;|@", spec.strip(), maxsplit=1)[0].strip().lower().strip('"\'')


def _first_pattern(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return f"matched `{pattern}`"
    return None


def _append_signal(signals: list[dict[str, Any]], counters: dict[str, int], signal: dict[str, Any], agent_types: set[str]) -> None:
    signals.append(signal)
    counters[signal["category"]] += 1
    if signal.get("agent_type"):
        agent_types.add(signal["agent_type"])


def _signal(category: str, ctx: FileContext, reason: str, weight: int, *, agent_type: str | None = None) -> dict[str, Any]:
    return {
        "category": category,
        "path": ctx.relative_path,
        "reason": reason,
        "weight": weight,
        "agent_type": agent_type,
    }


def _add_family(families: dict[str, dict[str, Any]], key: str, path: str, reason: str) -> None:
    meta = KNOWN_AGENT_FAMILIES[key]
    entry = families.setdefault(
        key,
        {
            "id": key,
            "name": meta["display"],
            "agent_types": list(meta["types"]),
            "evidence": [],
        },
    )
    if len(entry["evidence"]) < 5:
        entry["evidence"].append({"path": path, "reason": reason})


def _dedupe_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for signal in signals:
        key = (signal["category"], signal["path"], signal["reason"])
        if key in seen:
            continue
        seen.add(key)
        result.append(signal)
    return result


def _top_evidence(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in signal.items() if key != "weight" and value}
        for signal in sorted(_dedupe_signals(signals), key=lambda item: (-int(item["weight"]), item["path"], item["category"]))[:12]
    ]


def _has_llm_capability(counters: dict[str, int], model_providers: set[str]) -> bool:
    return bool(model_providers or counters.get("agent-framework") or counters.get("known-agent-family"))


def _has_tool_execution_capability(counters: dict[str, int]) -> bool:
    return bool(counters.get("tool-use") or counters.get("mcp") or counters.get("agent-framework") or counters.get("known-agent-family"))


def _confidence(score: int, counters: dict[str, int], llm_capability: bool, tool_execution_capability: bool) -> str:
    strong_categories = sum(
        1
        for key in ("model-provider", "tool-use", "mcp", "agent-framework", "known-agent-family")
        if counters.get(key, 0)
    )
    if llm_capability and tool_execution_capability and (counters.get("known-agent-family") or score >= 55 or strong_categories >= 2):
        return "high"
    if llm_capability and tool_execution_capability and score >= 32:
        return "medium"
    if score >= 16:
        return "low"
    return "none"


def _primary_agent_type(agent_types: set[str], counters: dict[str, int]) -> str:
    if not agent_types:
        return "unknown"
    priority = [
        "coding-agent",
        "browser-agent",
        "mcp-agent",
        "multi-agent-framework",
        "self-improving-agent",
        "memory-agent",
        "rag-agent",
        "tool-agent",
        "chat-agent",
        "agent-framework",
        "skill-agent",
        "autonomous-agent",
        "personal-agent",
    ]
    for item in priority:
        if item in agent_types:
            return item
    return sorted(agent_types)[0]


def _agent_product_evidence_chain(
    *,
    product_shape: str,
    confidence: str,
    score: int,
    evidence: list[dict[str, Any]],
    llm_capability: bool,
    tool_execution_capability: bool,
    model_providers: set[str],
    primary_type: str,
) -> dict[str, Any]:
    top_evidence = []
    for index, item in enumerate(evidence[:8], start=1):
        top_evidence.append({
            "rank": index,
            "source": item.get("category", "Agent能力信号"),
            "path": item.get("path", ""),
            "signal": item.get("reason", ""),
            "agent_type": item.get("agent_type", ""),
        })
    provider_text = ",".join(sorted(model_providers)) or "unknown"
    evidence_summary = _compact_evidence_summary(top_evidence)
    decision = (
        f"{product_shape}：confidence={confidence}; score={score}; "
        f"llm={str(llm_capability).lower()}({provider_text}); "
        f"tool={str(tool_execution_capability).lower()}; evidence={evidence_summary}。"
    )
    return {
        "conclusion": product_shape,
        "category": PROJECT_TYPE_AI_AGENT,
        "decision": decision,
        "standard": "LLM 调用能力 + 工具执行/注册能力 + 中/高置信度 => AI Agent 一级类目。",
        "score": score,
        "confidence": confidence,
        "basis": [
            f"llm={str(llm_capability).lower()}; providers={provider_text}",
            f"tool_execution={str(tool_execution_capability).lower()}",
            f"agent_type={primary_type}",
        ],
        "evidence": top_evidence,
        "competingCandidates": [],
    }


def _decision_reason(
    is_agent: bool,
    confidence: str,
    primary_type: str,
    evidence: list[dict[str, Any]],
    llm_capability: bool,
    tool_execution_capability: bool,
) -> str:
    if not is_agent:
        missing = []
        if not llm_capability:
            missing.append("LLM 调用能力")
        if not tool_execution_capability:
            missing.append("工具执行/注册能力")
        if missing:
            return f"未同时满足 AI Agent 判定标准，缺少：{'、'.join(missing)}；按产品形态信号进一步分类。"
        return "AI Agent 信号置信度不足，按产品形态信号进一步分类。"
    top = "; ".join(f"{item.get('category')}@{item.get('path')}" for item in evidence[:3])
    return f"判定为 {primary_type}，置信度 {confidence}；已同时发现 LLM 调用与工具执行/注册能力；主要依据：{top}。"


def agent_profile_to_json(profile: dict[str, Any]) -> str:
    return json.dumps(profile, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="识别项目产品形态，并细分 AI Agent 子类型")
    parser.add_argument("command", nargs="?", choices=["detect", "classify"], default="detect")
    parser.add_argument("--project-path", default=".", help="项目根目录")
    parser.add_argument("--batch-dir", help="扫描批次目录；指定后写入 project-type.json，并同步 batch-plan.json（若存在）")
    parser.add_argument("--output", help="额外输出 JSON 文件路径")
    parser.add_argument("--max-files", type=int, default=1000, help="最多扫描的文本文件数")
    parser.add_argument("--max-bytes-per-file", type=int, default=256 * 1024, help="单文件最大读取字节数")
    args = parser.parse_args()

    profile = classify_project_path(
        args.project_path,
        max_files=args.max_files,
        max_bytes_per_file=args.max_bytes_per_file,
    )
    write_detection_result(profile, batch_dir=args.batch_dir, output=args.output)
    print(agent_profile_to_json(profile))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
