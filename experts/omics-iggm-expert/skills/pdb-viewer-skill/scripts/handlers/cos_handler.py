"""
handlers/cos_handler.py — COS 文件获取（双通道：omics 认证 + coscli 通用）
====================================================================

纯函数模块，无全局状态，可独立测试。

对外暴露：
  ── omics 通道（腾讯健康组学平台绑定桶）──
  - find_omics_cli() -> str | None
  - read_omics_session() -> tuple[str, bool]
  - read_omics_config() -> dict
  - parse_cos_uri(uri) -> tuple[str, str]
  - fetch_pdb_from_omics(uri) -> tuple[bytes, str]

  ── coscli 通道（通用 COS 桶，需用户自行配置）──
  - find_coscli() -> str | None
  - read_coscli_config() -> dict
  - get_coscli_buckets() -> list[str]
  - resolve_cos_route(uri) -> str          # 返回 "coscli" | "omics"
  - fetch_pdb_from_coscli(uri) -> tuple[bytes, str]
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ---------- omics 配置（正式环境）----------
OMICS_BASE_URL = "https://omics.qq.com"
OMICS_CGI_PATH = "/omics/api/cgi"
OMICS_AUTH_FILE = Path.home() / ".omics-platform-cli" / "auth.json"
OMICS_CONFIG_FILE = Path.home() / ".omics-platform-cli" / "omics_config.json"

# COS 地域白名单（用于区分 cos://bucket/region/key 与 cos://bucket/key）
COS_REGIONS = {
    "ap-beijing", "ap-shanghai", "ap-guangzhou", "ap-chengdu",
    "ap-chongqing", "ap-nanjing", "ap-hongkong", "ap-singapore",
    "ap-seoul", "ap-tokyo", "ap-bangkok", "ap-mumbai", "ap-jakarta",
    "na-toronto", "na-siliconvalley", "na-ashburn",
    "sa-saopaulo", "eu-frankfurt", "eu-moscow",
}


def find_omics_cli() -> str | None:
    """查找 omics-platform-cli 可执行文件。返回路径或 None。"""
    local_bin = Path.home() / ".local" / "bin" / "omics"
    if local_bin.is_file() and os.access(local_bin, os.X_OK):
        return str(local_bin)
    return shutil.which("omics")


def read_omics_session() -> tuple[str, bool]:
    """读取 omics 登录态。
    返回 (session_id, is_valid)：
      - session_id: 非空字符串（若已登录）
      - is_valid:   True 表示 session 存在且未过期
    """
    if not OMICS_AUTH_FILE.exists():
        return "", False
    try:
        auth = json.loads(OMICS_AUTH_FILE.read_text("utf-8"))
        session_id = auth.get("session_id", "")
        expires_at = auth.get("expires_at", 0)
        if not session_id:
            return "", False
        if expires_at > 0 and time.time() > expires_at:
            return session_id, False
        return session_id, True
    except (OSError, ValueError, KeyError):
        return "", False


def read_omics_config() -> dict[str, Any]:
    """读取 omics-platform-cli 配置（EnvironmentId 等）。"""
    try:
        if OMICS_CONFIG_FILE.is_file():
            data = json.loads(OMICS_CONFIG_FILE.read_text("utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def parse_cos_uri(uri: str) -> tuple[str, str]:
    """解析 cos:// URI，返回 (bucket, key)。region 段自动识别并丢弃。
    支持两种格式:
      cos://<bucket>/<region>/<key>  →  region 通过白名单识别，丢弃
      cos://<bucket>/<key>
    """
    if not uri.startswith("cos://"):
        return "", ""
    rest = uri[len("cos://"):]
    parts = rest.split("/", 2)
    if len(parts) < 2:
        return "", ""
    bucket = parts[0]
    if len(parts) == 3 and parts[1] in COS_REGIONS:
        key = parts[2]
    else:
        key = parts[1] if len(parts) == 2 else f"{parts[1]}/{parts[2]}"
    return bucket, key


def fetch_pdb_from_omics(uri: str) -> tuple[bytes, str]:
    """通过 omics-platform-cli 认证调用 CosBucketService.GetObjectData 读取 COS 上的 PDB 文件。

    完整流程:
      1. 检查 omics CLI 是否安装
      2. 读取 ~/.omics-platform-cli/auth.json 中的 session_id
      3. 读取 ~/.omics-platform-cli/omics_config.json 中的 EnvironmentId
      4. 解析 cos:// URI → bucket + key（region 丢弃）
      5. POST /omics/api/cgi (CosBucketService.GetObjectData)
      6. 返回 (raw_bytes, file_name)

    抛异常时包含友好的错误信息和操作引导。
    """
    # 1. 检查 CLI
    cli = find_omics_cli()
    if cli is None:
        raise RuntimeError(
            "omics-platform-cli 未安装。\n"
            "请从官方 Release 页面下载对应平台的二进制文件：\n"
            "  https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases\n"
            "安装后执行 omics login 完成登录授权。"
        )

    # 2. 登录态
    session_id, is_valid = read_omics_session()
    if not session_id:
        raise RuntimeError(
            "未检测到 omics 登录凭证 (~/.omics-platform-cli/auth.json)。\n"
            "请执行: omics login"
        )
    if not is_valid:
        raise RuntimeError(
            "omics 登录凭证已过期。\n"
            "请执行: omics login"
        )

    # 3. EnvironmentId
    config = read_omics_config()
    env_id = config.get("EnvironmentId", "")

    # 4. 解析 URI
    bucket, key = parse_cos_uri(uri)
    if not bucket or not key:
        raise ValueError(f"无效的 COS URI: {uri}，期望格式 cos://<bucket>/[<region>/]<key>")
    if not key.lower().endswith(".pdb"):
        raise ValueError(f"文件路径必须以 .pdb 结尾: {key}")
    file_name = key.rsplit("/", 1)[-1] if "/" in key else key

    # 5. 调用 API
    url = OMICS_BASE_URL + OMICS_CGI_PATH
    payload = {
        "id": str(int(time.time())),
        "jsonrpc": "2.0",
        "method": "CosBucketService.GetObjectData",
        "params": {
            "EnvironmentId": env_id,
            "Bucket": bucket,
            "Key": key,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Origin": OMICS_BASE_URL,
        "Referer": f"{OMICS_BASE_URL}/",
        "Cookie": f"omics_session={session_id}",
    }
    data = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, 'read') else ''
        raise RuntimeError(f"GetObjectData HTTP {exc.code}: {raw[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"网络请求失败: {exc.reason}") from exc

    if "error" in result:
        err = result["error"]
        err_msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        code = err.get("code", "") if isinstance(err, dict) else ""
        if any(kw in err_msg.lower() for kw in ("401", "403", "session", "unauthorized")):
            raise RuntimeError(
                f"omics 登录凭证已失效 [{code}]: {err_msg}\n"
                "请执行: omics login"
            )
        raise RuntimeError(f"GetObjectData 失败 [{code}]: {err_msg}")

    result_obj = result.get("result", {})
    b64_data = result_obj.get("Data", "")
    if not b64_data:
        raise RuntimeError(
            f"GetObjectData 返回空数据 (bucket={bucket}, key={key})\n"
            "可能原因: bucket/key 不存在、无访问权限、或 EnvironmentId 配置错误"
        )
    try:
        raw = base64.b64decode(b64_data)
    except Exception as exc:
        raise RuntimeError(f"GetObjectData 返回的 base64 数据解码失败: {exc}") from exc

    return raw, file_name


# ════════════════════════════════════════════════
#  coscli 通道（通用 COS 访问）
# ════════════════════════════════════════════════

# coscli 配置文件路径
COSCLI_CONFIG_FILE = Path.home() / ".cos.yaml"


def find_coscli() -> str | None:
    """查找 coscli 可执行文件。返回路径或 None。"""
    return shutil.which("coscli")


def read_coscli_config() -> dict[str, Any]:
    """读取 coscli 配置文件 (~/.cos.yaml)。

    返回解析后的字典，包含:
      - cos.base.secretid / secretkey（加密存储，仅作存在性检查）
      - cos.buckets: list[dict]，每项含 name / alias / region / endpoint

    文件不存在或解析失败时返回空字典。
    """
    if not COSCLI_CONFIG_FILE.exists():
        return {}
    try:
        import yaml
        raw = COSCLI_CONFIG_FILE.read_text("utf-8")
        data = yaml.safe_load(raw)
        if isinstance(data, dict):
            return data
    except ImportError:
        # 无 PyYAML，尝试手动解析 buckets 列表
        try:
            text = COSCLI_CONFIG_FILE.read_text("utf-8")
            # 简单提取 buckets 下的 name 字段
            buckets = []
            in_buckets = False
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("buckets:"):
                    in_buckets = True
                    continue
                if in_buckets:
                    if stripped.startswith("- name:") or stripped.startswith("- name :"):
                        name = stripped.split(":", 1)[1].strip()
                        buckets.append({"name": name})
                    elif stripped and not stripped.startswith("-") and not stripped.startswith(" "):
                        break
            return {"cos": {"buckets": buckets}} if buckets else {}
        except Exception:
            pass
    except Exception:
        pass
    return {}


def get_coscli_buckets() -> list[str]:
    """获取 coscli 已配置的 bucket 名称列表。

    返回格式: ["bucketname-1250000000", ...]
    来自 ~/.cos.yaml 中 cos.buckets[].name 字段。
    """
    cfg = read_coscli_config()
    buckets_cfg = cfg.get("cos", {}).get("buckets", [])
    if isinstance(buckets_cfg, list):
        return [b.get("name", "") for b in buckets_cfg if isinstance(b, dict) and b.get("name")]
    return []


def resolve_cos_route(uri: str) -> str:
    """判断 cos:// URI 应走哪条通道。

    路由策略:
      1. 解析 URI 提取 bucket 名称
      2. 检查该 bucket 是否在 coscli 已配置列表中
         → 是: 返回 "coscli"（用户显式配置了该桶）
         → 否: 返回 "omics"（尝试 omics 平台绑定桶）

    Args:
        uri: cos:// 格式的 URI

    Returns:
        "coscli" 或 "omics"
    """
    bucket, _key = parse_cos_uri(uri)
    if not bucket:
        return "omics"

    configured = get_coscli_buckets()
    # 精确匹配：用户可能输入带/不带 APPID 的名称
    if bucket in configured:
        return "coscli"
    # 模糊匹配：配置中是 "mybucket-123456789"，用户输入 "mybucket"
    for cb in configured:
        base_name = cb.rsplit("-", 1)[0] if "-" in cb else cb
        if bucket == base_name or bucket == cb:
            return "coscli"
    return "omics"


def fetch_pdb_from_coscli(uri: str) -> tuple[bytes, str]:
    """通过 coscli 命令行工具读取 COS 上的 PDB 文件。

    完整流程:
      1. 检查 coscli 是否安装
      2. 解析 cos:// URI → bucket + key
      3. 从 coscli 配置中查找 bucket 对应的 endpoint（如有）
      4. subprocess.run(["coscli", "cp", ...]) 下载到临时文件
      5. 读取临时文件内容 → (bytes, filename)
      6. 清理临时文件

    Args:
        uri: cos://<bucket>/[<region>/]<key.pdb>

    Returns:
        (raw_bytes, file_name)

    Raises:
        RuntimeError: coscli 未安装、配置缺失、下载失败等
    """
    import tempfile

    # 1. 检查 coscli
    cli = find_coscli()
    if cli is None:
        raise RuntimeError(
            "coscli 未安装。\n\n"
            "安装方式（macOS）：\n"
            "  # 方式 1: 直接下载（推荐）\n"
            "  wget https://cosbrowser.cloud.tencent.com/software/coscli/coscli-darwin-arm64\n"
            "  mv coscli-darwin-arm64 coscli && chmod +x coscli\n"
            "  sudo mv coscli /usr/local/bin/\n\n"
            "  # 方式 2: Homebrew（如有）\n"
            "  brew install coscli\n\n"
            "验证: coscli --version  # 应输出 v1.0.8+\n\n"
            "安装后请执行 cosli config init 完成配置。"
        )

    # 2. 解析 URI
    bucket, key = parse_cos_uri(uri)
    if not bucket or not key:
        raise ValueError(f"无效的 COS URI: {uri}，期望格式 cos://<bucket>/[<region>/]<key>")
    if not key.lower().endswith(".pdb"):
        raise ValueError(f"文件路径必须以 .pdb 结尾: {key}")
    file_name = key.rsplit("/", 1)[-1] if "/" in key else key

    # 3. 检查 coscli 配置是否存在
    if not COSCLI_CONFIG_FILE.exists():
        raise RuntimeError(
            f"coscli 配置文件不存在 ({COSCLI_CONFIG_FILE})。\n"
            "请执行: cosli config init\n"
            "按提示输入 SecretId、SecretKey、APPID、Bucket Name、Region 等信息。"
        )

    # 4. 从配置中查找该 bucket 的 endpoint（用于未配置别名的情况）
    cfg = read_coscli_config()
    buckets_cfg = cfg.get("cos", {}).get("buckets", [])
    endpoint = None
    region_hint = None
    if isinstance(buckets_cfg, list):
        for b in buckets_cfg:
            if not isinstance(b, dict):
                continue
            b_name = b.get("name", "")
            # 匹配全称或短名
            if b_name == bucket or b_name.rsplit("-", 1)[0] == bucket:
                endpoint = b.get("endpoint")
                region_hint = b.get("region")
                break

    # 5. 构建并执行 coscli cp 命令
    src_url = f"cos://{bucket}/{key}"

    # 使用 NamedTemporaryFile 确保唯一路径和自动清理
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdb", prefix="pdb_viewer_coscli_")
    os.close(tmp_fd)

    try:
        cmd = [cli, "cp", src_url, tmp_path]
        # 如果有显式 endpoint 且 bucket 不在已配置别名中，加上 --endpoint
        if endpoint:
            cmd.extend(["--endpoint", endpoint])

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=120,
            text=True,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else ""
            stdout = result.stdout.strip() if result.stdout else ""
            error_detail = stderr or stdout or f"退出码 {result.returncode}"
            raise RuntimeError(f"coscli cp 失败: {error_detail}")

        # 6. 读取下载的文件
        if not os.path.isfile(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise RuntimeError(f"coscli cp 完成但文件为空或不存在: {tmp_path}")

        with open(tmp_path, "rb") as f:
            raw_bytes = f.read()

        return raw_bytes, file_name

    finally:
        # 清理临时文件
        try:
            os.remove(tmp_path)
        except OSError:
            pass
