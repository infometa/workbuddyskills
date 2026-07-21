#!/usr/bin/env python3
"""LSP 环境检测与 setupSteps 生成脚本。

用途：检测项目语言、LSP 二进制可用性，生成结构化的 pendingActions（含 setupSteps）。
      供编排器在步骤 0.4 消费，替代编排器内联构造 pendingActions 的逻辑。

子命令：
  detect   检测项目语言和 LSP 二进制状态，输出 JSON
  steps    根据探活结果生成 pendingActions（含 setupSteps），输出 JSON

示例：
  python3 lsp_setup.py detect --project-path /path/to/project
  python3 lsp_setup.py steps --language Java --probe-status failed --binary-installed true
  python3 lsp_setup.py steps --language Java --probe-status failed --binary-installed false
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# LSP 插件清单
# Ref: ${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md
# ---------------------------------------------------------------------------

LSP_REGISTRY = {
    "Java": {
        "pluginName": "jdtls-lsp",
        "binary": "jdtls",
        "installCommand": "brew install jdtls",
        "markerFiles": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "extensions": [".java"],
    },
    # Kotlin 无可用 LSP（jdtls 不支持 Kotlin），不注册。
    # Kotlin 项目走 Grep+AST 降级路径，由 detect_language 识别后返回 unsupported。
    "JS/TS": {
        "pluginName": "typescript-lsp",
        "binary": "typescript-language-server",
        "installCommand": "npm i -g typescript-language-server typescript",
        "markerFiles": ["package.json", "tsconfig.json"],
        "extensions": [".ts", ".tsx", ".js", ".jsx", ".mts", ".cts", ".mjs", ".cjs"],
    },
    "Go": {
        "pluginName": "gopls-lsp",
        "binary": "gopls",
        "installCommand": "go install golang.org/x/tools/gopls@latest",
        "markerFiles": ["go.mod"],
        "extensions": [".go"],
    },
    "Python": {
        "pluginName": "pyright-lsp",
        "binary": "pyright-langserver",
        "installCommand": "pip install pyright",
        "markerFiles": ["requirements.txt", "pyproject.toml", "setup.py"],
        "extensions": [".py", ".pyi"],
    },
    "Rust": {
        "pluginName": "rust-analyzer-lsp",
        "binary": "rust-analyzer",
        "installCommand": "rustup component add rust-analyzer",
        "markerFiles": ["Cargo.toml"],
        "extensions": [".rs"],
    },
    "C#": {
        "pluginName": "csharp-lsp",
        "binary": "csharp-ls",
        "installCommand": "dotnet tool install --global csharp-ls",
        "markerFiles": ["*.sln", "*.csproj"],
        "extensions": [".cs"],
    },
    "Swift": {
        "pluginName": "swift-lsp",
        "binary": "sourcekit-lsp",
        "installCommand": "",  # Xcode 内置
        "markerFiles": ["Package.swift"],
        "extensions": [".swift"],
    },
    "C/C++": {
        "pluginName": "clangd-lsp",
        "binary": "clangd",
        "installCommand": "brew install llvm",
        "markerFiles": ["CMakeLists.txt"],
        "extensions": [".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
    },
    "PHP": {
        "pluginName": "php-lsp",
        "binary": "intelephense",
        "installCommand": "npm i -g intelephense",
        "markerFiles": ["composer.json"],
        "extensions": [".php"],
    },
    "Lua": {
        "pluginName": "lua-lsp",
        "binary": "lua-language-server",
        "installCommand": "brew install lua-language-server",
        "markerFiles": [],  # 无标准标记文件，通过 .lua 文件检测
        "extensions": [".lua"],
    },
}

MARKETPLACE = "codebuddy-plugins-official"


# ---------------------------------------------------------------------------
# detect: 检测项目语言 + LSP 二进制状态
# ---------------------------------------------------------------------------

def detect_language(project_path: str) -> dict:
    """检测项目语言和 LSP 二进制可用性。

    特殊处理：
      - Kotlin 无可用 LSP 服务器（jdtls 不支持 Kotlin）。
      - 纯 Kotlin 项目（只有 .kt/.kts 而无 .java 文件）返回 language="Kotlin", supported=False。
      - 混合项目（同时有 .java 和 .kt）识别为 Java，走 Java LSP 通道。

    Returns:
        JSON 结构：
        {
          "language": "Java" | "Kotlin" | ... | null,
          "binaryInstalled": true/false,
          "binary": ... | null,
          "pluginName": ... | null,
          "installCommand": ... | null,
          "pluginInstallCommand": ... | null,
          "supported": true/false
        }
    """
    project = Path(project_path)

    for lang, info in LSP_REGISTRY.items():
        # 检查标记文件
        found = False
        for marker in info["markerFiles"]:
            if "*" in marker:
                # glob 模式
                if list(project.glob(marker)):
                    found = True
                    break
            else:
                if (project / marker).exists():
                    found = True
                    break

        # Lua 回退：无标记文件时检查 .lua 文件
        if not found and lang == "Lua":
            if list(project.glob("**/*.lua"))[:1]:
                found = True

        if not found:
            continue

        # Java/Kotlin 区分：检测到 JVM 构建标记后，判断实际语言
        if lang == "Java":
            has_kt = bool(list(project.glob("**/*.kt"))[:1])
            has_java = bool(list(project.glob("**/*.java"))[:1])
            if has_kt and not has_java:
                # 纯 Kotlin 项目：无可用 LSP，直接返回 unsupported
                return {
                    "language": "Kotlin",
                    "binaryInstalled": False,
                    "binary": None,
                    "pluginName": None,
                    "installCommand": None,
                    "pluginInstallCommand": None,
                    "supported": False,
                }
            # 混合项目或纯 Java 项目：走 Java LSP 通道

        # 检测到语言，检查二进制
        binary = info["binary"]
        binary_installed = shutil.which(binary) is not None
        plugin_cmd = f"codebuddy plugin install {info['pluginName']}@{MARKETPLACE}"

        return {
            "language": lang,
            "binaryInstalled": binary_installed,
            "binary": binary,
            "pluginName": info["pluginName"],
            "installCommand": info["installCommand"],
            "pluginInstallCommand": plugin_cmd,
            "supported": True,
        }

    return {
        "language": None,
        "binaryInstalled": False,
        "binary": None,
        "pluginName": None,
        "installCommand": None,
        "pluginInstallCommand": None,
        "supported": False,
    }


# ---------------------------------------------------------------------------
# steps: 根据探活结果生成 pendingActions（含 setupSteps）
# ---------------------------------------------------------------------------

def generate_pending_actions(
    language: str,
    probe_status: str,
    binary_installed: bool,
) -> dict:
    """根据 LSP 探活结果生成 pendingActions。

    Args:
        language: 项目语言（如 "Java"）
        probe_status: 探活状态（"available" | "failed" | "unsupported"）
        binary_installed: LSP 二进制是否已安装

    Returns:
        JSON 结构：
        {
          "lspStatus": "available" | "failed" | "unsupported",
          "needsRestart": false | true,
          "pendingActions": [...]   // 空数组表示无需操作
        }
    """
    # 探活成功或不支持的语言，无需操作
    if probe_status == "available":
        return {
            "lspStatus": "available",
            "needsRestart": False,
            "pendingActions": [],
        }

    if probe_status == "unsupported" or language not in LSP_REGISTRY:
        return {
            "lspStatus": "unsupported",
            "needsRestart": False,
            "pendingActions": [],
        }

    info = LSP_REGISTRY[language]
    plugin_cmd = f"codebuddy plugin install {info['pluginName']}@{MARKETPLACE}"

    binary = info["binary"]
    install_cmd = info["installCommand"]

    if binary_installed:
        # 情景 A：二进制已装，仅需安装插件 + 重启
        setup_steps = [
            f"退出 CodeBuddy（输入 /quit 或按 Ctrl+C）",
            f"在终端执行插件安装：{plugin_cmd}",
            f"在项目目录重新运行 codebuddy 启动 CodeBuddy",
            f"重新执行扫描命令",
        ]
        action = {
            "type": "lsp-plugin",
            "description": f"安装 {language} LSP 插件（{info['pluginName']}）并重启 CodeBuddy",
            "binary": binary,
            "pluginInstallCommand": plugin_cmd,
            "needsRestart": True,
            "restartHint": "关闭当前 CodeBuddy 窗口，然后重新打开项目",
            "setupSteps": setup_steps,
            "degradeImpact": "回退到 Grep+Read，跨文件调用追踪精度下降",
        }
    else:
        # 情景 B：二进制未装，需先装二进制再装插件 + 重启
        setup_steps = [
            f"退出 CodeBuddy（输入 /quit 或按 Ctrl+C）",
        ]
        if install_cmd:
            setup_steps.append(f"在终端安装 {language} LSP 二进制（{binary}）：{install_cmd}")
        else:
            setup_steps.append(f"请手动安装 {language} LSP 二进制（{binary}）")
        setup_steps.extend([
            f"在终端执行插件安装：{plugin_cmd}",
            f"在项目目录重新运行 codebuddy 启动 CodeBuddy",
            f"重新执行扫描命令",
        ])
        action = {
            "type": "lsp",
            "description": f"{language} LSP 语言服务（{binary}）未安装，需手动安装后重启 CodeBuddy",
            "binary": binary,
            "installCommand": install_cmd,
            "pluginInstallCommand": plugin_cmd,
            "needsRestart": True,
            "restartHint": "关闭当前 CodeBuddy 窗口，然后重新打开项目",
            "setupSteps": setup_steps,
            "degradeImpact": "回退到 Grep+Read，跨文件调用追踪精度下降",
        }

    return {
        "lspStatus": "failed",
        "needsRestart": True,
        "pendingActions": [action],
    }


# ---------------------------------------------------------------------------
# format: 将 pendingActions 格式化为用户可读的文本
# ---------------------------------------------------------------------------

def format_user_guidance(pending_actions_result: dict) -> str:
    """将 pendingActions 格式化为用户可读的分步指引文本。

    Args:
        pending_actions_result: generate_pending_actions() 的返回值

    Returns:
        格式化的纯文本指引
    """
    actions = pending_actions_result.get("pendingActions", [])
    if not actions:
        return ""

    lines = []
    for action in actions:
        lines.append(f"**{action['description']}**\n")
        steps = action.get("setupSteps", [])
        for i, step in enumerate(steps, 1):
            lines.append(f"  {i}. {step}")
        lines.append("")

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="LSP 环境检测与 setupSteps 生成",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # detect 子命令
    detect_parser = subparsers.add_parser(
        "detect",
        help="检测项目语言和 LSP 二进制状态",
    )
    detect_parser.add_argument(
        "--project-path",
        default=".",
        help="项目根目录路径（默认：当前目录）",
    )

    # steps 子命令
    steps_parser = subparsers.add_parser(
        "steps",
        help="根据探活结果生成 pendingActions（含 setupSteps）",
    )
    steps_parser.add_argument(
        "--language",
        required=True,
        help="项目语言（如 Java、Go、Python）",
    )
    steps_parser.add_argument(
        "--probe-status",
        required=True,
        choices=["available", "failed", "unsupported"],
        help="LSP 探活状态",
    )
    steps_parser.add_argument(
        "--binary-installed",
        required=True,
        choices=["true", "false"],
        help="LSP 二进制是否已安装",
    )

    # format 子命令
    format_parser = subparsers.add_parser(
        "format",
        help="将 pendingActions JSON 格式化为用户可读文本",
    )
    format_parser.add_argument(
        "--input",
        default="-",
        help="输入 JSON 文件路径（默认：stdin）",
    )

    args = parser.parse_args()

    if args.command == "detect":
        result = detect_language(args.project_path)
        print(json.dumps(result, ensure_ascii=False))

    elif args.command == "steps":
        result = generate_pending_actions(
            language=args.language,
            probe_status=args.probe_status,
            binary_installed=(args.binary_installed == "true"),
        )
        print(json.dumps(result, ensure_ascii=False))

    elif args.command == "format":
        if args.input == "-":
            data = json.load(sys.stdin)
        else:
            with open(args.input, encoding="utf-8") as f:
                data = json.load(f)
        text = format_user_guidance(data)
        if text:
            print(text)


if __name__ == "__main__":
    main()
