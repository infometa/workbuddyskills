#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import email.utils
import hashlib
import hmac
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


OSS_ENDPOINT = "oss-cn-shenzhen.aliyuncs.com"
OSS_REGION = "cn-shenzhen"
OSS_BUCKET = "ly-open-assets"
DEFAULT_RELEASE_PREFIX = "mcp-gateway/releases"
DEFAULT_PUBLIC_BASE_URL = f"https://{OSS_BUCKET}.{OSS_ENDPOINT}"
RELEASE_VERSION_RE = re.compile(r"(?<![0-9])([0-9]+[.][0-9]+[.][0-9]+)(?![0-9])")
SEMVER_RE = re.compile(r"^[0-9]+[.][0-9]+[.][0-9]+(?:-[0-9A-Za-z.-]+)?$")
OSS_UPLOAD_ATTEMPTS = 3
OSS_UPLOAD_RETRY_DELAYS_SECONDS = (1, 3)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_version_from_filename(file_name: str) -> str:
    matches = RELEASE_VERSION_RE.findall(file_name)
    if not matches:
        raise SystemExit(f"cannot infer release version from filename: {file_name}")
    return matches[-1]


def build_release_channels(
    release_version: str,
    workbuddy_official_version: str = "",
) -> dict[str, dict[str, object]]:
    if not SEMVER_RE.fullmatch(release_version):
        raise ValueError(f"release version must be semantic version: {release_version}")
    official_version = workbuddy_official_version.strip()
    if official_version and not SEMVER_RE.fullmatch(official_version):
        raise ValueError(
            "workbuddy official version must be semantic version: "
            f"{official_version}"
        )
    return {
        "stable": {
            "version": release_version,
            "status": "available",
            "audience": "authenticated",
            "asset": "workbuddy",
        },
        "workbuddy_official": {
            "version": official_version,
            "status": "approved" if official_version else "manual_submission",
            "update_mode": "manual_zip_review",
        },
    }


def content_type_for(path: Path) -> str:
    if path.suffix == ".json":
        return "application/json; charset=utf-8"
    if path.suffix == ".md":
        return "text/markdown; charset=utf-8"
    if path.suffix == ".sha256":
        return "text/plain; charset=utf-8"
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def cache_control_for(key: str) -> str:
    if key.endswith("manifest.json") or key.endswith(".md") or key.endswith("-latest.tgz"):
        return "public, max-age=300"
    return "public, max-age=31536000, immutable"


def quote_key(key: str) -> str:
    return "/".join(urllib.parse.quote(part, safe="") for part in key.split("/"))


def sign_headers(
    *,
    method: str,
    bucket: str,
    key: str,
    content_type: str,
    access_key_id: str,
    access_key_secret: str,
    headers: dict[str, str],
) -> dict[str, str]:
    date = email.utils.formatdate(time.time(), usegmt=True)
    headers = {**headers, "Date": date, "Content-Type": content_type}
    oss_headers = {
        name.lower(): value.strip()
        for name, value in headers.items()
        if name.lower().startswith("x-oss-")
    }
    canonical_oss_headers = "".join(
        f"{name}:{oss_headers[name]}\n" for name in sorted(oss_headers)
    )
    canonical_resource = f"/{bucket}/{key}"
    string_to_sign = (
        f"{method}\n\n{content_type}\n{date}\n"
        f"{canonical_oss_headers}{canonical_resource}"
    )
    signature = base64.b64encode(
        hmac.new(
            access_key_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")
    headers["Authorization"] = f"OSS {access_key_id}:{signature}"
    return headers


def put_object(
    *,
    key: str,
    body: bytes,
    content_type: str,
    access_key_id: str,
    access_key_secret: str,
    public_read: bool,
) -> str:
    url = f"https://{OSS_BUCKET}.{OSS_ENDPOINT}/{quote_key(key)}"
    extra_headers: dict[str, str] = {
        "Cache-Control": cache_control_for(key),
    }
    if public_read:
        extra_headers["x-oss-object-acl"] = "public-read"
    for attempt in range(1, OSS_UPLOAD_ATTEMPTS + 1):
        headers = sign_headers(
            method="PUT",
            bucket=OSS_BUCKET,
            key=key,
            content_type=content_type,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            headers=extra_headers,
        )
        request = urllib.request.Request(url, data=body, headers=headers, method="PUT")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status not in (200, 201):
                    raise RuntimeError(f"PUT {key} returned HTTP {response.status}")
            break
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == OSS_UPLOAD_ATTEMPTS:
                detail = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"PUT {key} failed: HTTP {error.code} {detail}"
                ) from error
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == OSS_UPLOAD_ATTEMPTS:
                raise RuntimeError(
                    f"PUT {key} failed after {attempt} attempts: {error}"
                ) from error
        time.sleep(OSS_UPLOAD_RETRY_DELAYS_SECONDS[attempt - 1])
    return url


def upload_file(
    *,
    local_path: Path,
    object_key: str,
    access_key_id: str,
    access_key_secret: str,
    public_read: bool,
) -> dict[str, object]:
    body = local_path.read_bytes()
    url = put_object(
        key=object_key,
        body=body,
        content_type=content_type_for(local_path),
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        public_read=public_read,
    )
    digest = hashlib.sha256(body).hexdigest()
    return {
        "file": local_path.name,
        "key": object_key,
        "url": url,
        "sha256": digest,
        "size": len(body),
    }


def upload_prompt_doc(
    *,
    action: str,
    kind: str,
    body: str,
    prefix: str,
    public_base_url: str,
    access_key_id: str,
    access_key_secret: str,
    public_read: bool,
) -> dict[str, object]:
    file_name = f"{action}-{kind}.md"
    object_key = f"{prefix}/prompts/{file_name}"
    body_bytes = body.encode("utf-8")
    put_object(
        key=object_key,
        body=body_bytes,
        content_type="text/markdown; charset=utf-8",
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        public_read=public_read,
    )
    return {
        "file": file_name,
        "key": object_key,
        "url": f"{public_base_url}/{quote_key(object_key)}",
        "sha256": hashlib.sha256(body_bytes).hexdigest(),
        "size": len(body_bytes),
    }


def credential_note_for(kind: str) -> str:
    if kind == "workbuddy":
        return "WorkBuddy 使用单一 tongzhou-fin-research Connector 的浏览器 OAuth；不要复制、粘贴或本地保存 API Key。"
    return "Codex 使用单一 tongzhou-fin-research stdio OAuth proxy；不要复制、粘贴或本地保存 API Key。"


def build_workbuddy_npm_prompt_doc(
    *,
    action: str,
    manifest_url: str,
    gateway_url: str,
    asset: dict[str, object],
    npm_setup_command: str,
) -> str:
    action_text = "安装" if action == "install" else "升级"
    setup_command = npm_setup_command.strip() or "npx --yes tongzhou-fin-research-expert@latest setup"
    if not setup_command.endswith(" setup"):
        raise ValueError("npm setup command must end with ' setup'")
    runner = setup_command.removesuffix(" setup")
    workbuddy_command = f"{setup_command} --target workbuddy --yes"
    doctor_command = f"{runner} doctor --target workbuddy"
    return "\n".join(
        [
            f"# 同舟股市投研专家 WorkBuddy 本机版{action_text} Prompt",
            "",
            f"请帮我在当前电脑为 WorkBuddy {action_text}“同舟股市投研专家”。只处理安装、升级和连接校验，不回答投研问题。",
            "",
            "## 一条命令",
            "",
            "```bash",
            workbuddy_command,
            "```",
            "",
            "## Release",
            "",
            f"- Release Manifest: {manifest_url}",
            f"- Gateway: {gateway_url}",
            f"- 当前专家包: {asset.get('file')}",
            f"- 当前专家包 SHA256: {asset.get('sha256')}",
            "- WorkBuddy Connector: `assets.workbuddy_connector`（与专家包独立发布）",
            "",
            "## 执行要求",
            "",
            "1. 先重新读取本 Markdown 和 Release Manifest，不要使用旧快照或旧安装脚本。",
            f"2. 运行 `{workbuddy_command}`。安装器必须从同一 Manifest 读取 `assets.workbuddy` 和 `assets.workbuddy_connector`，分别校验 SHA256 后再写入本机。",
            "3. 已完整注册的 WorkBuddy 官方 Connector 不覆盖；缺失或注册不完整时才安装独立 Connector。标准专家 ZIP 仍不得包含 Connector 源码。",
            "4. 覆盖专家目录前保留时间戳备份；任一下载、校验、JSON 解析、Connector 注册或专家结构检查失败时停止，并回滚本次新增的 Connector。",
            f"5. 安装完成后运行 `{doctor_command}`，确认 `installed: true`、`config: true`，且 Connector 的 `installed`、`registered`、`ready` 均为 `true`。",
            "6. 重启 WorkBuddy，在专家中点击连接 `tongzhou-fin-research`；需要授权时由 WorkBuddy 打开浏览器 OAuth。不要要求用户复制或粘贴 API Key、access token、refresh token 或授权码。",
            "7. 浏览器授权完成后回到 WorkBuddy，只重试原请求一次。若用户拒绝授权或授权失败，停止调用实时行情、研报、图谱和同舟材料，不得回退到旧 API Key 桥接脚本。",
            "8. 最终只回复系统类型、专家安装目录、Connector 状态、版本和 SHA256 前 12 位，不输出 OAuth 凭证、配置文件全文或个人信息。",
            "",
        ]
    )


def build_install_prompt_doc(
    *,
    kind: str,
    manifest_url: str,
    gateway_url: str,
    asset: dict[str, object],
    npm_setup_command: str = "",
) -> str:
    if kind == "workbuddy":
        return build_workbuddy_npm_prompt_doc(
            action="install",
            manifest_url=manifest_url,
            gateway_url=gateway_url,
            asset=asset,
            npm_setup_command=npm_setup_command,
        )
    target_label = "Codex 插件"
    install_dir = (
        "macOS/Linux: ~/.codex/plugins/tongzhou-fin-research-expert\n"
        "Windows: %USERPROFILE%\\.codex\\plugins\\tongzhou-fin-research-expert"
    )
    structure_check = ".codex-plugin/plugin.json"
    credential_action = (
        "确认 `~/.agents/plugins/marketplace.json` 的 personal marketplace 包含 "
        "`tongzhou-fin-research-expert` 本地插件条目，`source.path` 指向 "
        "`./.codex/plugins/tongzhou-fin-research-expert`；确认 `~/.codex/config.toml` "
        "包含 `[plugins.\"tongzhou-fin-research-expert@personal\"]` 且 `enabled = true`；"
        "确认只注册一个 tongzhou-fin-research stdio OAuth proxy；Windows 使用对应用户目录。"
    )
    check_command = "重新打开 Codex 或启动新会话以加载插件；需要显式授权修复时运行 `npx --yes tongzhou-fin-research-expert@latest auth status`，不要运行本地业务桥接脚本"
    completion_rule = "插件结构、单一 MCP 注册和 OAuth 状态校验通过后告诉用户安装完成；最终回复只说明安装位置、版本、文件名和 SHA256 前 12 位，不要输出 OAuth 凭证或个人信息。"
    distribution_rule = "只修改当前用户的 Codex personal 插件目录，不修改其他客户端。"
    credential_note = credential_note_for(kind)
    return "\n".join(
        [
            f"# 同舟股市投研专家 {target_label}安装 Prompt",
            "",
            "请帮我在本机安装“同舟股市投研专家”最新稳定版。你只需要处理本机安装、校验和 Gateway OAuth 连接，不要回答投研问题。",
            "",
            "## Release",
            "",
            f"- Release Manifest: {manifest_url}",
            f"- Gateway: {gateway_url}",
            f"- 凭证说明: {credential_note}",
            f"- 当前发布文件: {asset.get('file')}",
            f"- 当前发布地址: {asset.get('url')}",
            f"- 当前发布 SHA256: {asset.get('sha256')}",
            "",
            "## 执行要求",
            "",
            "1. 执行时必须先重新读取本 Markdown 和 Release Manifest，不要只使用用户粘贴的旧快照。",
            f"2. 从 Manifest 的 `assets.{kind}` 读取最新 `file`、`url`、`sha256` 和 `sha256_url`。",
            "3. 下载最新 zip 到本机临时目录，并用 Manifest 返回的 `sha256` 校验；校验失败必须停止。",
            "4. 如果安装目录已存在，先备份旧目录再覆盖。",
            f"5. 安装目录：\n{install_dir}",
            f"6. 解压后确认 `{structure_check}` 存在；不存在说明 zip 结构不正确，必须停止。",
            f"7. {distribution_rule}",
            f"8. {credential_action}",
            f"9. Gateway 地址使用 `{gateway_url}`；按 OAuth 流程获取和续期凭证。{credential_note}",
            f"10. 安装后{check_command}。",
            f"11. {completion_rule}",
            "",
        ]
    )


def build_upgrade_prompt_doc(
    *,
    kind: str,
    manifest_url: str,
    gateway_url: str,
    asset: dict[str, object],
    npm_setup_command: str = "",
) -> str:
    if kind == "workbuddy":
        return build_workbuddy_npm_prompt_doc(
            action="upgrade",
            manifest_url=manifest_url,
            gateway_url=gateway_url,
            asset=asset,
            npm_setup_command=npm_setup_command,
        )
    target_label = "Codex 插件"
    install_dir = (
        "macOS/Linux: ~/.codex/plugins/tongzhou-fin-research-expert\n"
        "Windows: %USERPROFILE%\\.codex\\plugins\\tongzhou-fin-research-expert"
    )
    structure_check = ".codex-plugin/plugin.json"
    credential_action = (
        "确认 `~/.agents/plugins/marketplace.json` 的 personal marketplace 包含 "
        "`tongzhou-fin-research-expert` 本地插件条目，`source.path` 指向 "
        "`./.codex/plugins/tongzhou-fin-research-expert`；确认 `~/.codex/config.toml` "
        "包含 `[plugins.\"tongzhou-fin-research-expert@personal\"]` 且 `enabled = true`；"
        "保留单一 tongzhou-fin-research stdio OAuth proxy 和已有可续期会话；Windows 使用对应用户目录。"
    )
    check_command = "重新打开 Codex 或启动新会话以加载插件；需要显式授权修复时运行 `npx --yes tongzhou-fin-research-expert@latest auth status`，不要运行本地业务桥接脚本"
    completion_rule = "插件结构、单一 MCP 注册和 OAuth 状态校验通过后告诉用户升级完成；最终回复只说明安装位置、版本、文件名和 SHA256 前 12 位，不要输出 OAuth 凭证或个人信息。"
    rekey_rule = "不要要求用户提供 API Key 或 OAuth token；只有 OAuth 状态明确失效时才重新授权。"
    distribution_rule = "只修改当前用户的 Codex personal 插件目录，不修改其他客户端。"
    credential_note = credential_note_for(kind)
    return "\n".join(
        [
            f"# 同舟股市投研专家 {target_label}升级 Prompt",
            "",
            "请帮我把本机的“同舟股市投研专家”升级到 Release Manifest 标记的最新稳定版。你只需要处理本机升级、校验和保留已有 Gateway OAuth 会话，不要回答投研问题。",
            "",
            "## Release",
            "",
            f"- Release Manifest: {manifest_url}",
            f"- Gateway: {gateway_url}",
            f"- 凭证说明: {credential_note}",
            f"- 当前发布文件: {asset.get('file')}",
            f"- 当前发布地址: {asset.get('url')}",
            f"- 当前发布 SHA256: {asset.get('sha256')}",
            "",
            "## 执行要求",
            "",
            "1. 执行时必须先重新读取本 Markdown 和 Release Manifest，不要只使用用户粘贴的旧快照。",
            f"2. 从 Manifest 的 `assets.{kind}` 读取最新 `file`、`url`、`sha256` 和 `sha256_url`。",
            "3. 下载最新 zip 到本机临时目录，并用 Manifest 返回的 `sha256` 校验；校验失败必须停止，不要覆盖旧版本。",
            "4. 覆盖安装前先备份旧目录。",
            f"5. 安装目录：\n{install_dir}",
            f"6. 解压后确认 `{structure_check}` 存在；不存在说明 zip 结构不正确，必须停止。",
            f"7. {distribution_rule}",
            f"8. {credential_action}",
            f"9. {rekey_rule}{credential_note} 不要猜测、不要输出完整 API Key。",
            f"10. 升级后{check_command}。",
            f"11. {completion_rule}",
            "",
        ]
    )


def build_layer1_prompt_doc(
    *,
    action: str,
    manifest_url: str,
    asset: dict[str, object],
) -> str:
    action_text = "安装" if action == "install" else "升级"
    return "\n".join(
        [
            f"# 同舟金融研究 L1 Skill {action_text} Prompt",
            "",
            f"请帮我为当前 MCP 客户端{action_text}“同舟金融研究 L1 Skill”。先确认客户端支持的原生扩展形态；本任务复用 OAuth 单一研究连接，不读取任何本地凭证，也不回答投研问题。",
            "",
            "## Release",
            "",
            f"- Release Manifest: {manifest_url}",
            f"- 当前发布文件: {asset.get('file')}",
            f"- 当前发布地址: {asset.get('url')}",
            f"- 当前发布 SHA256: {asset.get('sha256')}",
            "",
            "## 执行要求",
            "",
            "1. 先识别当前 MCP 客户端是否有稳定、可验证的 Skill/Plugin/Extension 机制及其真实目录；如果不支持，停止安装并说明仍可只使用 MCP，不要猜测目录或改写成普通提示词。",
            "2. 重新读取本 Markdown 和 Release Manifest，从 `assets.layer1` 获取最新 `file`、`url`、`sha256` 和 `sha256_url`。",
            "3. 下载 zip 到本机临时目录并校验 SHA256；校验失败必须停止，不要覆盖已有 Skill。",
            "4. 解压后必须且只能看到 `layer1-doc-search`、`layer1-fin-data`、`layer1-fin-graph`、`layer1-same-boat` 四个顶层 Skill 目录，每个目录都必须包含 `SKILL.md`。",
            "5. 客户端路径规则：Claude Code 优先做本地 skills-directory plugin，安装到 `~/.claude/skills/tongzhou-fin-research-expert`（Windows 为 `%USERPROFILE%\\.claude\\skills\\tongzhou-fin-research-expert`），并生成 `.claude-plugin/plugin.json` + `skills/`；Gemini CLI 优先做 extension，安装到 `~/.gemini/extensions/tongzhou-fin-research-expert`（Windows 为 `%USERPROFILE%\\.gemini\\extensions\\tongzhou-fin-research-expert`），并生成 `gemini-extension.json` + `skills/`；Cursor、OpenCode、VS Code/GitHub Copilot、GitHub Copilot CLI、Cline、Windsurf 和 Hermes Agent 安装四个 Skill 到各自已确认的用户级 Skill 目录。MCP 连接统一由 npm 安装器按客户端能力写入单一 `tongzhou-fin-research`：支持远程 OAuth 的客户端使用 direct OAuth，其余客户端使用 stdio OAuth proxy；不要手工写认证头或本地凭证。",
            "6. 覆盖前先备份同名目录，不要安装到 MCP server 配置目录。保持目录名和 references 相对路径不变。该包只提供选工具、参数约束、实体解析顺序和失败降级规则，不替代单一研究连接。",
            "7. 安装后让客户端重新加载 Skills，并确认四个 Skill 都能被发现；再检查单一 `tongzhou-fin-research` 连接能列出 `fin_data__`、`doc_search__`、`fin_graph__`、`same_boat__` 命名空间。",
            "8. 不读取、移动或输出 API Key、OAuth access token、refresh token 或授权码；不要把 Key 写进 Skill 文件，也不要把任何凭证写进聊天、日志、截图或最终回复。",
            "9. 最终只回复客户端、安装形态（Skill/Claude plugin/Gemini extension）、安装目录、版本、文件名、SHA256 前 12 位、四个 Skill 和单一研究连接的检查结果。",
            "",
        ]
    )


def build_npm_commands(
    *,
    package_name: str,
    package_url: str,
    registry_published: bool,
) -> tuple[str, str]:
    if registry_published:
        runner = f"npx --yes {package_name}@latest"
    else:
        runner = f"npx --yes --package={package_url} tongzhou-fin-research"
    return f"{runner} setup", f"{runner} targets"


def build_agent_prompt_doc(
    *,
    action: str,
    package_name: str,
    version: str,
    setup_command: str = "",
) -> str:
    action_text = "安装" if action == "install" else "升级"
    command = setup_command or f"npx --yes {package_name}@latest setup"
    return "\n".join(
        [
            f"# 同舟金融研究专家主流 Agent {action_text} Prompt",
            "",
            f"请在当前电脑为受支持的 Agent {action_text}同舟金融研究能力。先识别当前客户端和操作系统，不要回答投研问题。",
            "",
            "## npm",
            "",
            f"- Package: {package_name}",
            f"- Release version: {version}",
            f"- Command: `{command}`",
            "",
            "## 执行要求",
            "",
            f"1. 运行 `{command}`；安装器会识别本机已有客户端，并按实际状态执行首次安装或升级。需要先确认识别结果时添加 `--dry-run`。",
            "2. macOS、Linux、WSL 和 Windows PowerShell 使用同一个 npx 命令；不得手工猜测用户目录，路径由安装器按系统解析。",
            "3. WorkBuddy 与 Codex 安装完整专家/插件包；WorkBuddy 若缺少 `tongzhou-fin-research` Connector，安装器会从同一 Manifest 下载独立 Connector 资产并注册，已完整注册的官方 Connector 不覆盖。Claude Code 安装本地 skills-directory plugin，Gemini CLI 安装 extension；Cursor、Windsurf、OpenCode、GitHub Copilot CLI、VS Code/GitHub Copilot、Cline 和 Hermes Agent 安装四个 L1 Skill。安装器按客户端能力写入单一 `tongzhou-fin-research`：WorkBuddy 使用原生 Connector OAuth，支持远程 OAuth 的客户端使用 direct OAuth，其余客户端使用 stdio OAuth proxy。",
            "4. 首次需要认证时，按浏览器或 Device Flow 页面完成 OAuth；不要要求用户提供 API Key、access token、refresh token 或授权码，也不要把任何凭证写进聊天、命令历史、配置说明或日志。",
            "5. 下载文件必须来自 Release Manifest 并通过 SHA256 校验；校验、JSON 解析或 Skill 结构检查失败时停止，不覆盖旧版本。",
            "6. 覆盖前保留时间戳备份，完成后运行同一包的 `doctor --target` 检查本机安装、OAuth 会话和单一 MCP 配置状态。",
            "7. 最终只回复目标客户端、系统类型、安装目录、版本和 SHA256 前 12 位，不输出 OAuth 凭证或配置文件全文。",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish WorkBuddy, Connector, Codex, and Layer 1 release zips to Aliyun OSS.")
    parser.add_argument("--workbuddy-zip", required=True, help="WorkBuddy expert release zip.")
    parser.add_argument("--workbuddy-connector-zip", required=True, help="Standalone WorkBuddy Connector release zip.")
    parser.add_argument("--codex-zip", required=True, help="Codex plugin release zip.")
    parser.add_argument("--layer1-zip", required=True, help="Approved Layer 1 skills release zip.")
    parser.add_argument("--npm-tgz", required=True, help="Packed cross-platform npm installer.")
    parser.add_argument("--npm-package", default="tongzhou-fin-research-expert")
    parser.add_argument("--npm-version")
    parser.add_argument("--release-version")
    parser.add_argument(
        "--workbuddy-official-version",
        default=os.environ.get("WORKBUDDY_OFFICIAL_VERSION", ""),
        help="Latest WorkBuddy-reviewed version; omitted while official updates remain manual.",
    )
    parser.add_argument("--prefix", default=os.environ.get("OSS_RELEASE_PREFIX", DEFAULT_RELEASE_PREFIX))
    parser.add_argument("--public-base-url", default=os.environ.get("OSS_PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL))
    parser.add_argument("--no-public-read", action="store_true", help="Do not set x-oss-object-acl: public-read.")
    args = parser.parse_args()

    access_key_id = (os.environ.get("OSS_ACCESS_KEY_ID") or os.environ.get("OssAccessKeyId") or "").strip()
    access_key_secret = (
        os.environ.get("OSS_ACCESS_KEY_SECRET") or os.environ.get("OssAccessKeySecret") or ""
    ).strip()
    if not access_key_id or not access_key_secret:
        raise SystemExit(
            "OSS_ACCESS_KEY_ID/OSS_ACCESS_KEY_SECRET are required "
            "(OssAccessKeyId/OssAccessKeySecret aliases are also supported)"
        )

    prefix = args.prefix.strip("/")
    public_base_url = args.public_base_url.rstrip("/")
    public_read = not args.no_public_read
    gateway_url = os.environ.get("GATEWAY_PUBLIC_BASE_URL", "https://mcp-gateway.textmind-gz.com").rstrip("/")
    workbuddy_zip = Path(args.workbuddy_zip).resolve()
    workbuddy_connector_zip = Path(args.workbuddy_connector_zip).resolve()
    codex_zip = Path(args.codex_zip).resolve()
    layer1_zip = Path(args.layer1_zip).resolve()
    npm_tgz = Path(args.npm_tgz).resolve()
    if not workbuddy_zip.is_file():
        raise SystemExit(f"missing WorkBuddy zip: {workbuddy_zip}")
    if not workbuddy_connector_zip.is_file():
        raise SystemExit(f"missing WorkBuddy Connector zip: {workbuddy_connector_zip}")
    if not codex_zip.is_file():
        raise SystemExit(f"missing Codex zip: {codex_zip}")
    if not layer1_zip.is_file():
        raise SystemExit(f"missing Layer 1 zip: {layer1_zip}")
    if not npm_tgz.is_file():
        raise SystemExit(f"missing npm package: {npm_tgz}")
    release_version = args.release_version or release_version_from_filename(workbuddy_zip.name)
    workbuddy_official_version = args.workbuddy_official_version.strip()
    try:
        channels = build_release_channels(release_version, workbuddy_official_version)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if args.npm_version and args.npm_version != release_version:
        raise SystemExit(
            f"npm version must match release version: {args.npm_version} != {release_version}"
        )

    assets: dict[str, dict[str, object]] = {}
    for kind, path in (
        ("workbuddy", workbuddy_zip),
        ("workbuddy_connector", workbuddy_connector_zip),
        ("codex", codex_zip),
        ("layer1", layer1_zip),
    ):
        asset_key = f"{prefix}/{kind}/{path.name}"
        sha_key = f"{asset_key}.sha256"
        asset = upload_file(
            local_path=path,
            object_key=asset_key,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            public_read=public_read,
        )
        sha_body = f"{asset['sha256']}  {path.name}\n".encode("utf-8")
        put_object(
            key=sha_key,
            body=sha_body,
            content_type="text/plain; charset=utf-8",
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            public_read=public_read,
        )
        asset["url"] = f"{public_base_url}/{quote_key(asset_key)}"
        asset["sha256_url"] = f"{public_base_url}/{quote_key(sha_key)}"
        asset["version"] = release_version
        assets[kind] = asset

    npm_key = f"{prefix}/npm/{npm_tgz.name}"
    npm_asset = upload_file(
        local_path=npm_tgz,
        object_key=npm_key,
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        public_read=public_read,
    )
    latest_npm_key = f"{prefix}/npm/{args.npm_package}-latest.tgz"
    latest_npm_body = npm_tgz.read_bytes()
    put_object(
        key=latest_npm_key,
        body=latest_npm_body,
        content_type="application/octet-stream",
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        public_read=public_read,
    )
    npm_asset["url"] = f"{public_base_url}/{quote_key(npm_key)}"
    npm_asset["latest_url"] = f"{public_base_url}/{quote_key(latest_npm_key)}"
    npm_asset["latest_key"] = latest_npm_key
    npm_asset["version"] = release_version
    assets["npm"] = npm_asset

    if args.npm_version:
        npm_source_type = "registry"
        registry_url: str | None = f"https://www.npmjs.com/package/{args.npm_package}"
    else:
        npm_source_type = "oss"
        registry_url = None
    npm_setup_command, npm_targets_command = build_npm_commands(
        package_name=args.npm_package,
        package_url=str(npm_asset["latest_url"]),
        registry_published=bool(args.npm_version),
    )

    manifest_key = f"{prefix}/manifest.json"
    manifest_url = f"{public_base_url}/{quote_key(manifest_key)}"
    prompts: dict[str, dict[str, dict[str, object]]] = {"install": {}, "upgrade": {}}
    for kind in ("workbuddy", "codex"):
        asset = assets[kind]
        prompts["install"][kind] = upload_prompt_doc(
            action="install",
            kind=kind,
            body=build_install_prompt_doc(
                kind=kind,
                manifest_url=manifest_url,
                gateway_url=gateway_url,
                asset=asset,
                npm_setup_command=npm_setup_command,
            ),
            prefix=prefix,
            public_base_url=public_base_url,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            public_read=public_read,
        )
        prompts["upgrade"][kind] = upload_prompt_doc(
            action="upgrade",
            kind=kind,
            body=build_upgrade_prompt_doc(
                kind=kind,
                manifest_url=manifest_url,
                gateway_url=gateway_url,
                asset=asset,
                npm_setup_command=npm_setup_command,
            ),
            prefix=prefix,
            public_base_url=public_base_url,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            public_read=public_read,
        )
    for action in ("install", "upgrade"):
        prompts[action]["layer1"] = upload_prompt_doc(
            action=action,
            kind="layer1",
            body=build_layer1_prompt_doc(
                action=action,
                manifest_url=manifest_url,
                asset=assets["layer1"],
            ),
            prefix=prefix,
            public_base_url=public_base_url,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            public_read=public_read,
        )
        prompts[action]["agent"] = upload_prompt_doc(
            action=action,
            kind="agent",
            body=build_agent_prompt_doc(
                action=action,
                package_name=args.npm_package,
                version=release_version,
                setup_command=npm_setup_command,
            ),
            prefix=prefix,
            public_base_url=public_base_url,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            public_read=public_read,
        )

    manifest = {
        "schema_version": 2,
        "generated_at": int(time.time()),
        "bucket": OSS_BUCKET,
        "endpoint": OSS_ENDPOINT,
        "region": OSS_REGION,
        "prefix": prefix,
        "manifest_url": manifest_url,
        "channels": channels,
        "assets": assets,
        "prompts": prompts,
    }
    manifest["npm"] = {
        "name": args.npm_package,
        "version": release_version,
        "source": npm_source_type,
        "package_url": npm_asset["latest_url"],
        "registry_url": registry_url,
        "setup_command": npm_setup_command,
        "install_command": npm_setup_command,
        "upgrade_command": npm_setup_command,
        "targets_command": npm_targets_command,
    }
    manifest_body = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    put_object(
        key=manifest_key,
        body=manifest_body,
        content_type="application/json; charset=utf-8",
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        public_read=public_read,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
