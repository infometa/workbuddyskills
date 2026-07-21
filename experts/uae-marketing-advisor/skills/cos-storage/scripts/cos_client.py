"""
COS 存储桶客户端 - 零外部依赖，纯标准库实现。
基于 AWS Signature V4（COS 兼容 S3 协议），并支持 public-read manifest 免密访问。

用法：
  python cos_client.py list [prefix]       - 列出指定前缀下的文件
  python cos_client.py read <key>           - 读取并输出文件内容
  python cos_client.py search <keyword>     - 搜索文件名包含关键字的文件
  python cos_client.py exists <key>         - 检查文件是否存在
  python cos_client.py manifest             - 刷新/查看 manifest.json 摘要
"""

import sys
import os
import json
import hashlib
import hmac
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import quote
from xml.etree import ElementTree

# -- 配置：优先从同目录 config.py 读取，失败则用环境变量 --
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

try:
    from config import COS_CONFIG as _CFG
except ImportError:
    _CFG = None

COS_CONFIG = (
    _CFG if _CFG else
    {
        "secret_id": os.environ.get("COS_SECRET_ID", ""),
        "secret_key": os.environ.get("COS_SECRET_KEY", ""),
        "region": os.environ.get("COS_REGION", "ap-shanghai"),
        "bucket": os.environ.get("COS_BUCKET", "uae-marketing-1448789884"),
    }
)

_MANIFEST_CACHE = None
_MANIFEST_URL = None


def _public_url(key=""):
    """构造公开访问 URL（key 可为空，返回 manifest.json 根）"""
    bucket = COS_CONFIG["bucket"]
    region = COS_CONFIG["region"]
    host = f"https://{bucket}.cos.{region}.myqcloud.com"
    if not key:
        return f"{host}/manifest.json"
    key = key.lstrip("/")
    return f"{host}/{quote(key.encode('utf-8'), safe='/')}" if key else host + "/"


def _http_get(url, timeout=30):
    """发起简单 GET 请求，返回 response 对象"""
    req = Request(url, method="GET")
    req.add_header("User-Agent", "uae-cos-client/1.0")
    return urlopen(req, timeout=timeout)


def _load_manifest(force=False):
    """加载 public-read manifest.json；失败返回 None"""
    global _MANIFEST_CACHE, _MANIFEST_URL
    if not force and _MANIFEST_CACHE is not None:
        return _MANIFEST_CACHE
    url = _public_url("")
    try:
        resp = _http_get(url)
        data = json.loads(resp.read().decode("utf-8"))
        _MANIFEST_CACHE = data
        _MANIFEST_URL = url
        return data
    except Exception:
        return None


def _has_credentials():
    """检查是否配置了 COS 密钥"""
    return bool(COS_CONFIG.get("secret_id") and COS_CONFIG.get("secret_key"))


# ==========================================
#  AWS Signature V4（COS S3 兼容协议）
# ==========================================

def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(secret_key, date_stamp, region, service):
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _s3_request(method, path, params=None, body=None, headers_extra=None):
    """发送带 AWS SigV4 签名的 S3 兼容请求到 COS"""
    bucket = COS_CONFIG["bucket"]
    region = COS_CONFIG["region"]
    host = f"{bucket}.cos.{region}.myqcloud.com"
    service = "s3"

    params_items = sorted(params.items()) if params else []
    querystring = "&".join(
        f"{quote(k, safe='')}={quote(str(v), safe='')}" for k, v in params_items
    )

    t = datetime.now(timezone.utc)
    amzdate = t.strftime("%Y%m%dT%H%M%SZ")
    datestamp = t.strftime("%Y%m%d")

    payload = body if body else b""
    payload_hash = _sha256(payload)

    canonical_uri = f"/{quote(path.lstrip('/'), safe='/')}" if path and path != "/" else "/"
    canonical_querystring = querystring
    all_headers = {
        "host": host,
        "x-amz-date": amzdate,
        "x-amz-content-sha256": payload_hash,
    }
    if headers_extra:
        all_headers.update({k.strip(): str(v).strip() for k, v in headers_extra.items()})
    header_keys_lower = sorted(k.lower() for k in all_headers)
    signed_headers = ";".join(header_keys_lower)
    canonical_headers = "".join(f"{k}:{all_headers[k]}\n" for k in header_keys_lower)

    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amzdate}\n{credential_scope}\n"
        f"{_sha256(canonical_request.encode('utf-8'))}"
    )

    signing_key = _get_signature_key(COS_CONFIG["secret_key"], datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} Credential={COS_CONFIG['secret_id']}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    req_headers = {
        "Host": host,
        "X-Amz-Date": amzdate,
        "X-Amz-Content-SHA256": payload_hash,
        "Authorization": authorization,
    }
    if headers_extra:
        req_headers.update(headers_extra)

    url = f"https://{host}{canonical_uri}"
    if canonical_querystring:
        url += f"?{canonical_querystring}"

    req = Request(url, data=payload, headers=req_headers, method=method)
    return urlopen(req, timeout=30)


# ==========================================
#  API 封装
# ==========================================

def _manifest_to_objects(manifest, prefix=""):
    """把 manifest 中所有文件扁平化为对象列表"""
    objects = []
    for pfx_name, pfx_data in manifest.get("prefixes", {}).items():
        if not isinstance(pfx_data, dict):
            continue
        for f in pfx_data.get("files", []):
            key = f.get("key", "")
            if prefix and not key.startswith(prefix):
                continue
            objects.append({
                "key": key,
                "size": int(f.get("size_bytes", 0)),
                "size_kb": f.get("size_kb", 0),
                "last_modified": f.get("last_modified", ""),
                "url": f.get("url", ""),
                "mime": f.get("mime", ""),
            })
    for f in manifest.get("root_files", []):
        key = f.get("key", "")
        if prefix and not key.startswith(prefix):
            continue
        objects.append({
            "key": key,
            "size": int(f.get("size_bytes", 0)),
            "size_kb": f.get("size_kb", 0),
            "last_modified": f.get("last_modified", ""),
            "url": f.get("url", ""),
            "mime": f.get("mime", ""),
        })
    return objects


def list_objects(prefix=""):
    """列出 COS 存储桶中指定前缀下的文件；优先使用 public manifest"""
    manifest = _load_manifest()
    if manifest is not None:
        return _manifest_to_objects(manifest, prefix)

    if not _has_credentials():
        raise RuntimeError("无法读取 public manifest 且未配置 COS 密钥（COS_SECRET_ID / COS_SECRET_KEY）")

    params = {"max-keys": "1000"}
    if prefix:
        params["prefix"] = prefix

    objects = []
    marker = ""

    while True:
        if marker:
            params["marker"] = marker

        resp = _s3_request("GET", "/", params=params)
        xml_str = resp.read().decode("utf-8")

        root = ElementTree.fromstring(xml_str)
        ns = "http://s3.amazonaws.com/doc/2006-03-01/"

        for obj in root.findall(f"{{{ns}}}Contents"):
            key_el = obj.find(f"{{{ns}}}Key")
            size_el = obj.find(f"{{{ns}}}Size")
            lm_el = obj.find(f"{{{ns}}}LastModified")
            objects.append({
                "key": key_el.text,
                "size": int(size_el.text),
                "last_modified": lm_el.text if lm_el is not None else "",
            })

        is_truncated = root.find(f"{{{ns}}}IsTruncated")
        if is_truncated is None or is_truncated.text != "true":
            break

        next_marker = root.find(f"{{{ns}}}NextMarker")
        if next_marker is not None:
            marker = next_marker.text
        else:
            break

    return objects


def read_object(key):
    """读取 COS 存储桶中指定键的文件内容；优先 public URL"""
    url = _public_url(key)
    try:
        resp = _http_get(url)
        return resp.read()
    except Exception:
        pass

    if not _has_credentials():
        raise RuntimeError(f"公开读取失败且未配置 COS 密钥，无法读取 {key}")

    resp = _s3_request("GET", key)
    return resp.read()


def object_exists(key):
    """检查文件是否存在"""
    try:
        resp = _http_get(_public_url(key))
        return resp.status == 200
    except Exception:
        pass

    if not _has_credentials():
        return False

    try:
        resp = _s3_request("HEAD", key)
        return resp.status == 200
    except Exception:
        return False


def search_objects(keyword, prefix=""):
    """搜索文件名包含关键字的文件"""
    all_objs = list_objects(prefix)
    return [o for o in all_objs if keyword.lower() in o["key"].lower()]


def manifest_summary():
    """返回 manifest.json 摘要信息"""
    manifest = _load_manifest(force=True)
    if manifest is None:
        raise RuntimeError("无法加载 public manifest.json")
    return {
        "bucket": manifest.get("bucket"),
        "region": manifest.get("region"),
        "total_files": manifest.get("total_files"),
        "total_size_kb": manifest.get("total_size_kb"),
        "generated_at": manifest.get("generated_at"),
        "prefixes": list(manifest.get("prefixes", {}).keys()),
        "manifest_url": _MANIFEST_URL,
    }


# ==========================================
#  CLI
# ==========================================

def main():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    if len(sys.argv) < 2:
        print("Usage: python cos_client.py <command> [args]")
        print("Commands: list [prefix] | read <key> | search <keyword> [prefix] | exists <key> | manifest")
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "list":
            prefix = sys.argv[2] if len(sys.argv) > 2 else ""
            objects = list_objects(prefix)
            if not objects:
                print(f"(空) 前缀 '{prefix or '/'}' 下无文件")
            for obj in objects:
                print(f"{obj['key']}  ({obj['size']/1024:.1f} KB)  {obj['last_modified']}")

        elif cmd == "read":
            if len(sys.argv) < 3:
                print("请指定要读取的文件键名", file=sys.stderr); sys.exit(1)
            key = sys.argv[2]
            content = read_object(key)
            try:
                print(content.decode("utf-8"))
            except UnicodeDecodeError:
                print(f"[二进制文件，{len(content)} 字节]")

        elif cmd == "search":
            if len(sys.argv) < 3:
                print("请指定搜索关键字", file=sys.stderr); sys.exit(1)
            keyword = sys.argv[2]
            prefix = sys.argv[3] if len(sys.argv) > 3 else ""
            objects = search_objects(keyword, prefix)
            if not objects:
                print(f"未找到包含 '{keyword}' 的文件")
            for obj in objects:
                print(f"{obj['key']}  ({obj['size']/1024:.1f} KB)")

        elif cmd == "exists":
            if len(sys.argv) < 3:
                print("请指定文件键名", file=sys.stderr); sys.exit(1)
            print("存在" if object_exists(sys.argv[2]) else "不存在")

        elif cmd == "manifest":
            summary = manifest_summary()
            print(f"存储桶: {summary['bucket']}")
            print(f"区域:   {summary['region']}")
            print(f"文件数: {summary['total_files']}")
            print(f"总大小: {summary['total_size_kb'] / 1024:.1f} MB")
            print(f"生成时间: {summary['generated_at']}")
            print(f"目录前缀: {', '.join(summary['prefixes'])}")
            print(f"Manifest: {summary['manifest_url']}")

        else:
            print(f"未知命令: {cmd}", file=sys.stderr); sys.exit(1)

    except Exception as e:
        print(f"错误: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
