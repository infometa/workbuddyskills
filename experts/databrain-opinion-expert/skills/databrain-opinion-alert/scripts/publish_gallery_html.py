#!/usr/bin/env python3
"""
publish_gallery_html.py — alert skill 专用 AI Gallery 发布脚本。

职责边界：
  1) 使用当前用户 token 上传告警 HTML 到 AI Gallery；
  2) 保持作品 visibility 为 self；
  3) 回读并输出可访问 URL；
  4) 为接口可行性验证提供 --set-self-only 模式。

外层 skill / send_alert.py 只需要调用本脚本并读取 stdout JSON，不需要感知 Gallery
底层 API 细节。
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import ssl
import sys
import threading
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote


EXIT_OK = 0
EXIT_BIZ_ERROR = 1
EXIT_USAGE = 2

# [Why] databrain.woa.com 在无 SSO Cookie 的脚本请求里会 302 到登录页；
#       personal token 直连接口用 intlgame，最终展示 URL 仍使用 woa 域名。
DEFAULT_HOST = "https://databrain.intlgame.com"
DEFAULT_DISPLAY_HOST = "https://databrain.woa.com"
DEFAULT_TAGS = '[{"id":1}]'
MAX_FILE_SIZE = 50 * 1024 * 1024
TIMEOUT_DEFAULT = 30
TIMEOUT_UPLOAD = 180
SAFE_URICOMP = "!*'()"

_FALLBACK_CAFILE_CANDIDATES = (
    "/etc/ssl/cert.pem",
    "/opt/homebrew/etc/ca-certificates/cert.pem",
    "/usr/local/etc/ca-certificates/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
)

_DEFAULT_SSL_CTX = ssl.create_default_context()
_FALLBACK_SSL_CTX: ssl.SSLContext | None = None
for _candidate in _FALLBACK_CAFILE_CANDIDATES:
    if Path(_candidate).is_file():
        try:
            _FALLBACK_SSL_CTX = ssl.create_default_context(cafile=_candidate)
        except Exception:
            _FALLBACK_SSL_CTX = None
        if _FALLBACK_SSL_CTX is not None:
            break

_SSL_FALLBACK_LOGGED = threading.Event()


def _load_dotenv() -> None:
    """[Why] 允许本地 .env 注入用户自己的 Databrain token；环境变量仍优先。"""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.is_file():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        return


_load_dotenv()


class GalleryError(Exception):
    def __init__(self, code: int, msg: str, errors: Any = None, detail: Any = None) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.errors = errors
        self.detail = detail

    def to_payload(self) -> dict:
        payload: dict = {"ok": False, "code": self.code, "msg": self.msg}
        if self.errors is not None:
            payload["errors"] = self.errors
        if self.detail is not None:
            payload["detail"] = self.detail
        return payload


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _success(payload: dict) -> int:
    out = {"ok": True}
    out.update(payload)
    _print_json(out)
    return EXIT_OK


def _failure(exit_code: int, code: int, msg: str, errors: Any = None, detail: Any = None) -> int:
    payload: dict = {"ok": False, "code": code, "msg": msg}
    if errors is not None:
        payload["errors"] = errors
    if detail is not None:
        payload["detail"] = detail
    _print_json(payload)
    return exit_code


def _host() -> str:
    return (os.environ.get("DATABRAIN_GALLERY_HOST") or DEFAULT_HOST).rstrip("/")


def _display_host() -> str:
    return (os.environ.get("DATABRAIN_GALLERY_DISPLAY_HOST") or DEFAULT_DISPLAY_HOST).rstrip("/")


def _token() -> str:
    token = (
        os.environ.get("DATABRAIN_GALLERY_TOKEN", "").strip()
        or os.environ.get("DATABRAIN_TOKEN", "").strip()
    )
    if not token:
        raise GalleryError(
            -2,
            "missing DATABRAIN_TOKEN for AI Gallery publishing",
        )
    return token


def _build_url(path: str) -> str:
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return _host() + path


def _encode_multipart(
    fields: dict[str, str],
    file: tuple[str, bytes, str] | None,
) -> tuple[bytes, str]:
    boundary = f"----AlertGalleryClient{uuid.uuid4().hex}"
    bnd = boundary.encode("ascii")
    crlf = b"\r\n"
    parts: list[bytes] = []

    for name, value in fields.items():
        parts.append(b"--" + bnd + crlf)
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8") + crlf)
        parts.append(b"Content-Type: text/plain; charset=utf-8" + crlf)
        parts.append(crlf)
        parts.append(str(value).encode("utf-8"))
        parts.append(crlf)

    if file is not None:
        filename, file_bytes, content_type = file
        parts.append(b"--" + bnd + crlf)
        parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8") + crlf
        )
        parts.append(f"Content-Type: {content_type}".encode("utf-8") + crlf)
        parts.append(crlf)
        parts.append(file_bytes)
        parts.append(crlf)

    parts.append(b"--" + bnd + b"--" + crlf)
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _decode_response(resp_bytes: bytes) -> Any:
    if not resp_bytes:
        raise GalleryError(-1, "empty response body")
    try:
        body = json.loads(resp_bytes.decode("utf-8", errors="replace"))
    except (json.JSONDecodeError, ValueError) as exc:
        raise GalleryError(-1, f"invalid json response: {exc}") from exc
    if not isinstance(body, dict):
        raise GalleryError(-1, f"unexpected response shape: {type(body).__name__}")

    code = body.get("code")
    if code is None:
        if "statusCode" in body and "message" in body:
            msg_raw = body["message"]
            if isinstance(msg_raw, list):
                msg = "; ".join(str(x) for x in msg_raw)
            else:
                msg = str(msg_raw)
            try:
                status_code = int(body.get("statusCode"))
            except (TypeError, ValueError):
                status_code = -1
            raise GalleryError(status_code, msg, detail=body.get("error"))
        raise GalleryError(-1, "response missing code field")

    if code != 0:
        try:
            code_int = int(code)
        except (TypeError, ValueError):
            code_int = -1
        raise GalleryError(
            code_int,
            str(body.get("message") or body.get("msg") or "biz error"),
            errors=body.get("errors"),
            detail=body.get("detail"),
        )
    return body.get("data") if "data" in body else body


def _open_request(req: urllib.request.Request, timeout: int) -> bytes:
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_DEFAULT_SSL_CTX) as resp:
            return resp.read()
    except ssl.SSLCertVerificationError as exc:
        if _FALLBACK_SSL_CTX is None:
            raise GalleryError(-1, f"ssl verify failed (no fallback CA): {exc}") from exc
        if not _SSL_FALLBACK_LOGGED.is_set():
            _SSL_FALLBACK_LOGGED.set()
            print(f"[publish_gallery_html] ssl fallback engaged for {req.full_url}", file=sys.stderr)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_FALLBACK_SSL_CTX) as resp:
                return resp.read()
        except Exception as exc2:
            raise GalleryError(-1, f"ssl fallback also failed: {exc2}") from exc2
    except urllib.error.HTTPError as exc:
        raw = exc.read() if exc.fp is not None else b""
        if raw:
            return raw
        raise GalleryError(-1, f"http error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise GalleryError(-1, f"network: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GalleryError(-1, f"timeout after {timeout}s") from exc


def _request_json(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    multipart_fields: dict[str, str] | None = None,
    multipart_file: tuple[str, bytes, str] | None = None,
    timeout: int = TIMEOUT_DEFAULT,
) -> Any:
    data: bytes | None = None
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Origin": _host(),
        "Accept": "application/json",
    }

    if multipart_fields is not None or multipart_file is not None:
        body, content_type = _encode_multipart(multipart_fields or {}, multipart_file)
        data = body
        headers["Content-Type"] = content_type
    elif json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(
        _build_url(path),
        data=data,
        method=method.upper(),
        headers=headers,
    )
    return _decode_response(_open_request(req, timeout))


def _normalize_tags(raw: str) -> str:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GalleryError(-2, f"tags is not valid JSON: {exc}") from exc
    if not isinstance(parsed, list) or not (1 <= len(parsed) <= 5):
        raise GalleryError(-2, "tags must be a JSON array with 1-5 items")

    out = []
    for i, item in enumerate(parsed):
        if not isinstance(item, dict) or "id" not in item:
            raise GalleryError(-2, f'tags[{i}] must be like {{"id":<int>}}')
        try:
            out.append({"id": int(item["id"])})
        except (TypeError, ValueError) as exc:
            raise GalleryError(-2, f"tags[{i}].id must be int") from exc
    return json.dumps(out, ensure_ascii=False)


def _tags_from_args(raw: str | None) -> str:
    # [Why] alert skill 不向外层暴露 Gallery tag 细节；默认归入“舆情”标签，必要时可用 env 覆盖。
    tags = raw or os.environ.get("DATABRAIN_GALLERY_TAGS", "") or DEFAULT_TAGS
    return _normalize_tags(tags)


def _guess_upload_mime(path: Path) -> str:
    lower = path.name.lower()
    if lower.endswith((".html", ".htm")):
        return "text/html"
    if lower.endswith(".zip"):
        return "application/zip"
    guessed = mimetypes.guess_type(path.name)[0]
    raise GalleryError(-2, f"unsupported file type: {guessed or path.suffix or '(none)'}")


def _validate_file(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_file():
        raise GalleryError(-2, f"file not found: {file_path}")
    size = path.stat().st_size
    if size <= 0:
        raise GalleryError(-2, "file is empty")
    if size > MAX_FILE_SIZE:
        raise GalleryError(-2, f"file too large: {size} bytes > {MAX_FILE_SIZE}")
    _guess_upload_mime(path)
    return path


def _dashboard_urls(data: dict, rule_key: str) -> dict:
    link = data.get("link")
    name_cn = data.get("name_cn")
    name_en = data.get("name_en")
    display_url = None
    legacy_url = None
    if isinstance(link, str) and link:
        display_name = name_en or name_cn or rule_key
        display_url = (
            f"{_display_host()}/aigallery/report"
            f"?path={quote(link, safe=SAFE_URICOMP)}"
            f"&name={quote(str(display_name), safe=SAFE_URICOMP)}"
        )
        legacy_url = f"{_display_host()}{link}"
    return {
        "rule_key": data.get("rule_key") or rule_key,
        "link": link,
        "display_url": display_url,
        "legacy_url": legacy_url,
    }


def _get_dashboard(rule_key: str) -> dict:
    data = _request_json("GET", f"/api/ai-gallery/dashboards/{rule_key}")
    if not isinstance(data, dict):
        raise GalleryError(-1, f"unexpected dashboard payload shape: {type(data).__name__}")
    return data


def _set_self(rule_key: str) -> None:
    if not rule_key.strip():
        raise GalleryError(-2, "rule-key cannot be empty")
    _request_json(
        "PUT",
        f"/api/ai-gallery/dashboards/{rule_key}",
        json_body={"visibility": "self"},
        timeout=TIMEOUT_DEFAULT,
    )


def _create_dashboard(
    file_path: Path,
    title: str,
    tags: str,
    name_cn: str | None,
    name_en: str | None,
    desc_cn: str | None,
    desc_en: str | None,
) -> str:
    title = (title or file_path.stem).strip()
    fields = {
        "name_cn": (name_cn or title)[:40],
        "name_en": (name_en or title)[:60],
        "source": "file",
        "visibility": "self",
        "tags": tags,
    }
    if desc_cn:
        fields["desc_cn"] = desc_cn[:200]
    if desc_en:
        fields["desc_en"] = desc_en[:300]

    data = _request_json(
        "POST",
        "/api/ai-gallery/dashboards",
        multipart_fields=fields,
        multipart_file=(file_path.name, file_path.read_bytes(), _guess_upload_mime(file_path)),
        timeout=TIMEOUT_UPLOAD,
    )
    if not isinstance(data, dict) or not data.get("rule_key"):
        raise GalleryError(-1, f"unexpected create payload: {data!r}")
    return str(data["rule_key"])


def publish_html(args: argparse.Namespace) -> dict:
    file_path = _validate_file(args.file)
    tags = _tags_from_args(args.tags)
    rule_key = _create_dashboard(
        file_path,
        args.title,
        tags,
        args.name_cn,
        args.name_en,
        args.desc_cn,
        args.desc_en,
    )
    _set_self(rule_key)
    urls = _dashboard_urls(_get_dashboard(rule_key), rule_key)
    return {
        **urls,
        "created": True,
        "visibility_updated": True,
        "visibility": "self",
    }


def set_self_only(rule_key: str) -> dict:
    _set_self(rule_key)
    dashboard = _get_dashboard(rule_key)
    return {
        **_dashboard_urls(dashboard, rule_key),
        "created": False,
        "visibility_updated": True,
        "visibility": "self",
    }


def self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        if ok:
            print(f"  OK {name}")
        else:
            print(f"  FAIL {name}: {detail}")
            failures.append(name)

    check("normalize tags", _normalize_tags('[{"id":"1"},{"id":2}]') == '[{"id": 1}, {"id": 2}]')
    try:
        _normalize_tags("[]")
        check("reject empty tags", False, "accepted []")
    except GalleryError:
        check("reject empty tags", True)

    urls = _dashboard_urls(
        {"rule_key": "g-x", "link": "/as/report/g-x/alert.html", "name_en": "Alert Detail"},
        "g-x",
    )
    check("display url generated", "/aigallery/report?path=%2Fas%2Freport%2Fg-x%2Falert.html" in urls["display_url"])
    check("legacy url generated", urls["legacy_url"].endswith("/as/report/g-x/alert.html"))

    try:
        _token()
        check("token present or skipped", True)
    except GalleryError as exc:
        check("missing token detected", exc.code == -2)

    if failures:
        print(f"FAIL: {len(failures)}")
        return EXIT_USAGE
    print("PASS: publish_gallery_html self test")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish alert HTML to AI Gallery and keep visibility=self.")
    parser.add_argument("--file", default="", help="HTML file to publish")
    parser.add_argument("--title", default="Databrain Alert Detail")
    parser.add_argument("--name-cn", default=None)
    parser.add_argument("--name-en", default=None)
    parser.add_argument("--desc-cn", default=None)
    parser.add_argument("--desc-en", default=None)
    parser.add_argument("--tags", default=None, help='JSON tags, e.g. [{"id":1}]')
    parser.add_argument("--set-self-only", action="store_true", help="Only update an existing dashboard to self visibility")
    parser.add_argument("--rule-key", default="", help="Existing dashboard rule_key for --set-self-only")
    parser.add_argument("--self_test", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    try:
        if args.set_self_only:
            if args.file:
                raise GalleryError(-2, "--file cannot be used with --set-self-only")
            payload = set_self_only(args.rule_key.strip())
        else:
            if not args.file:
                raise GalleryError(-2, "missing --file")
            payload = publish_html(args)
    except GalleryError as exc:
        return _failure(EXIT_USAGE if exc.code == -2 else EXIT_BIZ_ERROR, exc.code, exc.msg, exc.errors, exc.detail)
    except Exception as exc:
        return _failure(EXIT_BIZ_ERROR, -1, f"{type(exc).__name__}: {exc}")

    return _success(payload)


if __name__ == "__main__":
    sys.exit(main())
