"""linkfox skill 输出路径与会话索引（所有 skill 共享）。

目录结构：
  <ACPX_WORKSPACES|cwd>/linkfox/
  ├── <YYYY-MM-DD>/
  │   └── <session-id>/
  │       ├── _meta.json                # 会话元信息
  │       ├── reports/<topic>-<ts>.<ext> # 最终交付（report-generator 等）
  │       ├── data/<skill>-<ts>.json     # 原始数据（普通 skill）
  │       └── media/<slug>-<ts>.<ext>    # 图片/视频/音频
  └── index.jsonl                        # 全局会话索引（按行追加）

环境变量：
  SESSION_ID       — 会话 ID；缺省自动生成 `HHMMSS-<6 hex>`
  LINKFOX_TOOL_GATEWAY  — tool-gateway 地址（缺省 https://tool-gateway.linkfox.com）
  LINKFOX_AGENT_API_KEY — API 鉴权 Token（TokenType.API 接口必需）

OSS 上传依赖 oss2（pip install oss2）。
"""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from typing import Optional


_SAFE_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_slug(slug: str, fallback: str = "linkfox") -> str:
    """把文件名 slug 收敛到 [A-Za-z0-9._-]，避免中文/空格/全角符号导致乱码。

    非法字符（含中文、空格、全角标点等）整段压成单个 '-'；首尾的 '-._' 去掉；
    截断到 80 字符；全部被过滤掉（如纯中文标题）时回退到 fallback。
    """
    s = _SAFE_SLUG_RE.sub("-", (slug or "").strip())
    s = s.strip("-._")[:80].rstrip("-._")
    return s or fallback


def get_api_base() -> str:
    """网关基础地址：env LINKFOX_TOOL_GATEWAY 优先，缺省回退正式地址。"""
    return (os.environ.get("LINKFOX_TOOL_GATEWAY") or "https://tool-gateway.linkfox.com").rstrip("/")


_SESSION_CACHE: dict[str, str] = {}


def _format_iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(ts))


def _session_id(ts: float) -> str:
    """优先 env SESSION_ID；缺省按 HHMMSS-<6 hex> 生成（同一进程内稳定）。"""
    env = os.environ.get("SESSION_ID")
    if env:
        return env.strip()
    if "_auto" not in _SESSION_CACHE:
        _SESSION_CACHE["_auto"] = (
            time.strftime("%H%M%S", time.localtime(ts)) + "-" + secrets.token_hex(3)
        )
    return _SESSION_CACHE["_auto"]


def _linkfox_root() -> str:
    """选择可写的 linkfox 根目录。

    优先级：
      1. $ACPX_WORKSPACES 第一个路径下的 linkfox/（真实的工作目录）
      2. 当前工作目录下的 linkfox/
      3. ~/linkfox/
      4. $TMPDIR/linkfox/

    当某路径只读（如 cwd 为 /tmp 或只读目录）时，自动回退到后序选项。
    选定结果在进程内缓存，保证同一次运行内所有落盘路径稳定一致。
    """
    cached = _SESSION_CACHE.get("_root")
    if cached:
        return cached
    candidates = []
    # 1. ACPX_WORKSPACES（真实的工作目录，优先级最高）
    acpx = (os.environ.get("ACPX_WORKSPACES") or "").strip()
    if acpx:
        acpx = acpx.split(os.pathsep)[0].strip()
        if acpx:
            candidates.append(os.path.join(acpx, "linkfox"))
    # 2. 当前工作目录
    candidates.append(os.path.join(os.getcwd(), "linkfox"))
    # 3. 家目录
    candidates.append(os.path.join(os.path.expanduser("~"), "linkfox"))
    # 4. 临时目录
    import tempfile
    candidates.append(os.path.join(tempfile.gettempdir(), "linkfox"))

    for root in candidates:
        try:
            os.makedirs(root, exist_ok=True)
            probe = os.path.join(root, ".write_probe")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("")
            os.remove(probe)
        except OSError:
            continue
        root = os.path.abspath(root)
        _SESSION_CACHE["_root"] = root
        return root
    fallback = os.path.abspath(candidates[-1])
    _SESSION_CACHE["_root"] = fallback
    return fallback


def _ensure_session(ts: float) -> tuple[str, str]:
    """返回 (linkfox_root, session_dir)；session_dir 一定存在。"""
    date_str = time.strftime("%Y-%m-%d", time.localtime(ts))
    sid = _session_id(ts)
    root = _linkfox_root()
    session_dir = os.path.join(root, date_str, sid)
    os.makedirs(session_dir, exist_ok=True)
    _ensure_meta(root, session_dir, date_str, sid, ts)
    return root, session_dir


def _timestamp_suffix(ts: float) -> str:
    """用于文件名的微秒级时间戳，避免同一秒内多次落盘互相覆盖。"""
    return str(int(ts * 1_000_000))


def _ensure_meta(root: str, session_dir: str, date_str: str, sid: str, ts: float) -> None:
    """会话首次出现时创建 _meta.json，并向 index.jsonl 追加一条。"""
    meta_path = os.path.join(session_dir, "_meta.json")
    if os.path.exists(meta_path):
        return
    meta = {
        "session_id": sid,
        "date": date_str,
        "started_at": _format_iso(ts),
        "skills_called": [],
        "deliverables": [],
        "data_files": [],
        "media_files": [],
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    try:
        with open(os.path.join(root, "index.jsonl"), "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "session_id": sid,
                        "date": date_str,
                        "path": os.path.relpath(session_dir, root),
                        "started_at": _format_iso(ts),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except OSError:
        pass


def _update_meta(session_dir: str, *, skill: str, kind: str, file_rel: str, ts: float) -> None:
    """把本次输出写入 _meta.json 的对应分类列表。kind ∈ {data, deliverable, media}。"""
    meta_path = os.path.join(session_dir, "_meta.json")
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if skill and skill not in meta.setdefault("skills_called", []):
        meta["skills_called"].append(skill)
    bucket = {"data": "data_files", "deliverable": "deliverables", "media": "media_files"}.get(
        kind, "data_files"
    )
    files = meta.setdefault(bucket, [])
    if file_rel not in files:  # 去重：并发或重复注册同一路径时不留重复条目
        files.append(file_rel)
    meta["last_used_at"] = _format_iso(ts)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def resolve_data_path(slug: str, ts: float, ext: str = "json") -> str:
    """普通 skill 的原始数据落到 <session>/data/<slug>-<ts>.<ext>。"""
    _, session_dir = _ensure_session(ts)
    sub = os.path.join(session_dir, "data")
    os.makedirs(sub, exist_ok=True)
    out = os.path.join(sub, f"{_safe_slug(slug)}-{int(ts * 1_000_000)}.{ext}")
    _update_meta(session_dir, skill=slug, kind="data", file_rel=os.path.relpath(out, session_dir), ts=ts)
    return out


def resolve_report_path(slug: str, ts: float, ext: str) -> str:
    """最终交付（report-generator）落到 <session>/reports/<slug>-<ts>.<ext>。"""
    _, session_dir = _ensure_session(ts)
    sub = os.path.join(session_dir, "reports")
    os.makedirs(sub, exist_ok=True)
    out = os.path.join(sub, f"{_safe_slug(slug, 'linkfox-report')}-{int(ts * 1_000_000)}.{ext}")
    _update_meta(session_dir, skill=slug, kind="deliverable", file_rel=os.path.relpath(out, session_dir), ts=ts)
    return out


def resolve_media_path(slug: str, ts: float, ext: str) -> str:
    """图片/视频/音频落到 <session>/media/<slug>-<ts>.<ext>。"""
    _, session_dir = _ensure_session(ts)
    sub = os.path.join(session_dir, "media")
    os.makedirs(sub, exist_ok=True)
    out = os.path.join(sub, f"{_safe_slug(slug)}-{int(ts * 1_000_000)}.{ext}")
    _update_meta(session_dir, skill=slug, kind="media", file_rel=os.path.relpath(out, session_dir), ts=ts)
    return out


def session_root(ts: Optional[float] = None) -> str:
    """返回当前 session 目录（其它脚本若需要自定义文件名时用）。"""
    if ts is None:
        ts = time.time()
    _, session_dir = _ensure_session(ts)
    return session_dir


def _get_agent_base() -> str:
    """tool-gateway 基础地址：LINKFOX_TOOL_GATEWAY 优先，缺省回退正式地址。"""
    return (os.environ.get("LINKFOX_TOOL_GATEWAY") or "https://tool-gateway.linkfox.com").rstrip("/")


def _parse_endpoint(endpoint: str) -> tuple[str, str]:
    """规范化 OSS endpoint，兼容带/不带 scheme 两种形式。

    Returns:
        (endpoint_url, endpoint_host)
        - endpoint_url:  带 scheme，供 oss2.Bucket 使用，如 'https://oss-cn-shenzhen.aliyuncs.com'
        - endpoint_host: 不带 scheme 的纯主机名，供 bucket-style URL 拼接，如 'oss-cn-shenzhen.aliyuncs.com'
    """
    ep = (endpoint or "").strip().rstrip("/")
    if ep.startswith("https://"):
        return ep, ep[len("https://"):]
    if ep.startswith("http://"):
        return ep, ep[len("http://"):]
    return f"https://{ep}", ep


def get_sts_voucher() -> dict:
    """调用 /oss/getStsVoucherByAPI 获取阿里云 OSS STS 临时上传凭证。

    后端响应（扁平结构）字段：
      - 凭证：accessKeyId、accessKeySecret、securityToken、expiration
      - OSS：endpoint（可能带 https:// 前缀）、bucketName、dir、region
      - 约束：supportedTypes（逗号分隔的扩展名）、maxFileSize（字节）、maxFileCount

    本函数做的归一化：
      - 兼容 {errcode, data} 信封与扁平响应。
      - maxFileSize/maxFileCount 若为数字字符串，转为 int。
      - errcode != 200 或返回 ErrorCode 字段时直接抛错。

    失败时抛出 RuntimeError（最多重试 3 次，指数退避 1s→2s→4s）。
    """
    import sys
    import urllib.error
    from urllib.request import urlopen, Request

    base = _get_agent_base()
    api_token = os.environ.get("LINKFOX_AGENT_API_KEY") or ""
    url = f"{base}/oss/getStsVoucherByAPI"

    last_exc: Exception = RuntimeError("未知错误")
    body: dict = {}
    for attempt in range(3):
        if attempt:
            time.sleep(1 << (attempt - 1))  # 1s, 2s
        req = Request(
            url,
            method="POST",
            data=b"{}",
            headers={"Content-Type": "application/json", "Authorization": api_token},
        )
        try:
            with urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode())
            break
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read().decode()[:300]
            last_exc = RuntimeError(f"getStsVoucherByAPI HTTP {status}: {raw}")
            if status not in (408, 429, 500, 502, 503, 504):
                raise last_exc
        except Exception as e:
            last_exc = RuntimeError(f"getStsVoucherByAPI 请求失败: {e}")
            print(f"[get_sts_voucher] attempt {attempt+1}/3 失败: {e}", file=sys.stderr)
    else:
        raise last_exc

    if not isinstance(body, dict):
        raise RuntimeError(f"getStsVoucherByAPI 响应格式异常: {body!r}")

    errcode = body.get("errcode")
    if errcode is not None and errcode != 200:
        raise RuntimeError(
            f"getStsVoucherByAPI 业务错误: errcode={errcode}, "
            f"msg={body.get('errmsg', body.get('message', ''))}"
        )

    raw_voucher = body.get("data") if isinstance(body.get("data"), dict) else body
    if not isinstance(raw_voucher, dict):
        raise RuntimeError(f"getStsVoucherByAPI 响应缺少凭证字段: {body!r}")

    if "ErrorCode" in raw_voucher:
        raise RuntimeError(
            f"STS 凭证获取失败: {raw_voucher['ErrorCode']} - {raw_voucher.get('ErrorMessage', '')}"
        )

    voucher = dict(raw_voucher)
    for key in ("maxFileSize", "maxFileCount"):
        val = voucher.get(key)
        if isinstance(val, str) and val.strip().isdigit():
            voucher[key] = int(val.strip())

    return voucher


def upload_file(
    local_path: str,
    *,
    slug: Optional[str] = None,
    ts: Optional[float] = None,
    voucher: Optional[dict] = None,
) -> dict:
    """上传本地文件到阿里云 OSS，注册到会话 _meta.json，返回文件信息 dict。

    Args:
        local_path: 本地文件路径。
        slug:       标识名，用于 _meta.json 记录（默认取文件名去扩展名）。
        ts:         时间戳，决定 OSS 路径中的年月（默认 time.time()）。
        voucher:    已有的 STS 凭证 dict；为 None 时自动调用 get_sts_voucher()。

    Returns:
        {
          "url":  str,   # 可公开访问的 HTTPS URL
          "path": str,   # OSS 对象键（如 tmp/2025/06/abc123.pdf）
          "name": str,   # 原始文件名
          "size": int,   # 文件大小（字节）
          "ext":  str,   # 扩展名（不含点）
        }

    Raises:
        RuntimeError: 缺少 oss2、凭证获取失败或上传失败。
    """
    try:
        import oss2
    except ImportError:
        raise RuntimeError("缺少 oss2 依赖，请运行: pip install oss2")

    import uuid as _uuid

    if ts is None:
        ts = time.time()
    if slug is None:
        slug = os.path.splitext(os.path.basename(local_path))[0]

    ext = os.path.splitext(local_path)[1].lstrip(".").lower()
    if not ext:
        ext = "bin"

    if voucher is None:
        voucher = get_sts_voucher()

    file_size = os.path.getsize(local_path)

    max_size = voucher.get("maxFileSize")
    if isinstance(max_size, int) and max_size > 0 and file_size > max_size:
        raise RuntimeError(
            f"文件大小 {file_size} 字节超过 OSS 上限 {max_size} 字节"
            f"（约 {max_size // (1024 * 1024)}MB）: {local_path}"
        )

    supported = voucher.get("supportedTypes")
    if isinstance(supported, str) and supported.strip():
        allowed = {t.strip().lower() for t in supported.split(",") if t.strip()}
        if allowed and ext not in allowed:
            raise RuntimeError(
                f"文件类型 .{ext} 不在 OSS 允许列表中：{sorted(allowed)}（{local_path}）"
            )

    dir_ = (voucher.get("dir") or "tmp").rstrip("/")
    date_prefix = time.strftime("%Y/%m", time.localtime(ts))
    object_key = f"{dir_}/{date_prefix}/{_uuid.uuid4().hex}.{ext}"

    endpoint_url, endpoint_host = _parse_endpoint(voucher["endpoint"])
    bucket_name = voucher["bucketName"]

    auth = oss2.StsAuth(
        voucher["accessKeyId"],
        voucher["accessKeySecret"],
        voucher["securityToken"],
    )
    bucket = oss2.Bucket(auth, endpoint_url, bucket_name)

    with open(local_path, "rb") as f:
        bucket.put_object(object_key, f)

    url = f"https://{bucket_name}.{endpoint_host}/{object_key}"

    _, session_dir = _ensure_session(ts)
    _update_meta(session_dir, skill=slug, kind="deliverable", file_rel=url, ts=ts)

    return {
        "url": url,
        "path": object_key,
        "name": os.path.basename(local_path),
        "size": file_size,
        "ext": ext,
    }


NL_PLACEHOLDER = "⏎"


def encode_nl(text: str) -> str:
    """把文本中的换行符压平为单字符占位符 ⏎（U+23CE），供链式调用安全传递。

    覆盖两种形态：
      1. 真实换行控制符：\r\n / \r / \n
      2. 字面量两字符转义序列：\\r\\n / \\n / \\r
    """
    if not isinstance(text, str):
        return text
    # 先处理字面量转义序列（两字符）
    text = text.replace("\\r\\n", NL_PLACEHOLDER)
    text = text.replace("\\n", NL_PLACEHOLDER)
    text = text.replace("\\r", NL_PLACEHOLDER)
    # 再处理真实换行控制符
    text = text.replace("\r\n", NL_PLACEHOLDER)
    text = text.replace("\r", NL_PLACEHOLDER)
    text = text.replace("\n", NL_PLACEHOLDER)
    return text


def decode_nl(text: str) -> str:
    """把占位符 ⏎ 还原为真实换行符 \\n。"""
    if not isinstance(text, str):
        return text
    return text.replace(NL_PLACEHOLDER, "\n")


def decode_nl_in_obj(obj):
    """递归遍历 dict/list，对所有 string 值执行 decode_nl。"""
    if isinstance(obj, str):
        return decode_nl(obj)
    if isinstance(obj, list):
        return [decode_nl_in_obj(item) for item in obj]
    if isinstance(obj, dict):
        return {k: decode_nl_in_obj(v) for k, v in obj.items()}
    return obj


def download_media(url: str, slug: str, ts: Optional[float] = None, ext: Optional[str] = None, timeout: int = 300) -> Optional[str]:
    """下载 URL 到 <session>/media/<slug>-<ts>.<ext>，返回本地路径；失败返回 None。

    健壮性保证：
    - ext 为 None 时从 URL 路径或 Content-Type 推断。
    - 仅支持 http/https URL，拒绝 file:// 等。
    - 先写临时文件，下载完成后 rename 为正式路径，再注册到 _meta.json。
      下载中断时自动清理临时文件，不会留下残缺产物。
    - 任何异常均返回 None，不抛出。
    - timeout 默认 300s（视频文件较大）。
    """
    import sys
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError
    import posixpath

    if not url or not isinstance(url, str):
        return None

    if not url.startswith("http://") and not url.startswith("https://"):
        print(f"[download_media] Unsupported URL scheme: {url[:80]}", file=sys.stderr)
        return None

    if ts is None:
        ts = time.time()

    # 从 URL 路径推断扩展名
    guessed_ext = ext
    if not guessed_ext:
        path_part = url.split("?")[0]
        candidate = posixpath.splitext(path_part)[1].lstrip(".")
        if candidate and len(candidate) <= 5 and candidate.isalnum():
            guessed_ext = candidate
        else:
            guessed_ext = "bin"

    # 准备临时文件路径（在 media/ 目录下，以 .tmp- 前缀标识）
    _, session_dir = _ensure_session(ts)
    media_dir = os.path.join(session_dir, "media")
    os.makedirs(media_dir, exist_ok=True)
    tmp_filename = f".tmp-{_safe_slug(slug)}-{int(ts * 1_000_000)}.download"
    tmp_path = os.path.join(media_dir, tmp_filename)

    req = Request(url, headers={"User-Agent": "LinkFox-Skill/2.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            # 从 Content-Type 进一步修正扩展名
            if guessed_ext == "bin":
                ct = resp.headers.get("Content-Type", "")
                if "mp4" in ct:
                    guessed_ext = "mp4"
                elif "webm" in ct:
                    guessed_ext = "webm"
                elif "png" in ct:
                    guessed_ext = "png"
                elif "jpeg" in ct or "jpg" in ct:
                    guessed_ext = "jpg"
                elif "webp" in ct:
                    guessed_ext = "webp"
                elif "gif" in ct:
                    guessed_ext = "gif"

            # 写入临时文件
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)

        # 下载完成：确定正式路径（微秒级避免碰撞），rename，然后注册到 _meta
        ts_us = int(ts * 1_000_000)
        final_path = os.path.join(media_dir, f"{_safe_slug(slug)}-{ts_us}.{guessed_ext}")
        os.replace(tmp_path, final_path)
        _update_meta(session_dir, skill=slug, kind="media", file_rel=os.path.relpath(final_path, session_dir), ts=ts)
        return final_path

    except Exception as e:
        print(f"[download_media] Failed to download {url}: {e}", file=sys.stderr)
        # 清理残缺的临时文件
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        return None
