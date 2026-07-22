#!/usr/bin/env python3
"""
零 Key 在线查询模块
联网优先获取公开数据源最新数据，下载失败时降级到本地缓存兜底。

数据源（全部免费、无需认证）：
1. Ransomware.live REST API  - 家族活跃度、受害者统计
2. ransomwatch GitHub JSON   - 团伙 Tor 站点、元数据
3. mthcht/awesome-lists CSV  - 700+ 勒索家族扩展名映射
4. NoMoreRansom 解密工具页    - 170+ 家族解密工具状态

联网策略（网络优先 → 缓存降级）：
- 每次查询优先尝试在线获取最新数据
- 在线获取成功时保存为本地缓存（assets/cache/<source>.json）
- 在线获取失败时降级到本地缓存兜底，保证离线可用
- 缓存是兜底数据，不是临时缓存，请勿随意删除
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import ssl
import urllib.error
import urllib.request

# ============ 配置 ============

ASSETS_DIR = Path(__file__).parent.parent / "assets"
CACHE_DIR = ASSETS_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 请求超时（秒）
REQUEST_TIMEOUT = 15

# User-Agent（部分服务要求）
USER_AGENT = "ransomware-analysis-skill/1.0 (security research)"

# ============ 数据源 URL ============

DATA_SOURCES = {
    "ransomware_live_recentvictims": {
        "url": "https://api.ransomware.live/recentvictims",
        "description": "最近受害者列表",
    },
    "ransomware_live_groups": {
        "url": "https://api.ransomware.live/groups",
        "description": "所有勒索团伙元数据",
    },
    "ransomwatch_groups": {
        "url": "https://raw.githubusercontent.com/joshhighet/ransomwatch/main/groups.json",
        "description": "勒索团伙 Tor 站点元数据",
    },
    "ransomwatch_posts": {
        "url": "https://raw.githubusercontent.com/joshhighet/ransomwatch/main/posts.json",
        "description": "受害者发布记录",
    },
    "mthcht_extensions": {
        "url": "https://raw.githubusercontent.com/mthcht/awesome-lists/main/Lists/ransomware_extensions_list.csv",
        "description": "700+ 勒索家族扩展名映射（mthcht/awesome-lists）",
        "format": "csv",
    },
    "nomoreransom_decryptors": {
        "url": "https://www.nomoreransom.org/zh/decryption-tools.html",
        "description": "NoMoreRansom 解密工具清单（170+ 家族解密状态）",
        "format": "html",
    },
}

# ============ 通用下载与缓存 ============

def _cache_path(source_key: str) -> Path:
    return CACHE_DIR / f"{source_key}.json"

def _cache_exists(source_key: str) -> bool:
    """检查本地缓存文件是否存在且内容可解析"""
    sp = _cache_path(source_key)
    if not sp.exists():
        return False
    try:
        with open(sp, "r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, (dict, list))
    except (json.JSONDecodeError, OSError):
        return False

def _is_ssl_error(exc: BaseException) -> bool:
    """判断异常是否由 SSL 证书验证失败引起"""
    if isinstance(exc, ssl.SSLError):
        return True
    # urllib.error.URLError 的 reason 可能是 ssl.SSLError
    reason = getattr(exc, "reason", None)
    if isinstance(reason, ssl.SSLError):
        return True
    msg = str(exc)
    return "CERTIFICATE" in msg or "CERT_VERIFY" in msg or "SSL" in msg.upper()

def _download(url: str) -> Optional[bytes]:
    """
    下载 URL 内容，失败返回 None。

    三级 SSL 回退策略，兼容 macOS 系统 Python 缺少 CA 证书的环境：
      1. 标准请求（使用系统默认 SSL 证书）
      2. 使用 certifi 证书包（若已安装）
      3. 关闭证书验证降级（仅对公开情报数据源，可接受的安全折衷）

    数据源均为公开勒索软件情报，无敏感凭证或私有数据，
    关闭证书验证的风险仅限于理论上的中间人攻击，且结果会与本地规则库交叉验证。
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain,*/*"},
    )

    # 策略1：标准请求
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read()
    except Exception as e:
        if not _is_ssl_error(e):
            # 非 SSL 错误，直接返回 None
            print(f"[警告] 下载失败 {url}: {e}", file=sys.stderr)
            return None
        # SSL 证书问题，继续尝试下面的策略

    # 策略2：使用 certifi 证书包（如果安装了）
    try:
        import certifi  # type: ignore

        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            print(
                f"[提示] 使用 certifi 证书包成功下载 {url}",
                file=sys.stderr,
            )
            return resp.read()
    except ImportError:
        pass  # certifi 未安装，跳过
    except Exception as e:
        if not _is_ssl_error(e):
            print(f"[警告] certifi 方式下载失败 {url}: {e}", file=sys.stderr)
            return None
        # 仍是 SSL 错误，继续降级

    # 策略3：降级为不验证证书（公开情报数据源，可接受的安全折衷）
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ctx) as resp:
            print(
                f"[警告] SSL 证书验证失败，已降级为不验证证书下载 {url} "
                f"（公开情报数据源，可接受）",
                file=sys.stderr,
            )
            return resp.read()
    except Exception as e:
        print(
            f"[警告] 下载失败（SSL 降级仍失败）{url}: {e}",
            file=sys.stderr,
        )

    return None

def _save_cache(source_key: str, raw: bytes) -> Optional[object]:
    """保存原始 JSON 内容为本地缓存并返回解析后的对象"""
    sp = _cache_path(source_key)
    try:
        text = raw.decode("utf-8", errors="replace")
        data = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[警告] 解析失败 {source_key}: {e}", file=sys.stderr)
        return None
    payload = {
        "_meta": {
            "source": source_key,
            "url": DATA_SOURCES.get(source_key, {}).get("url", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "data": data,
    }
    try:
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[警告] 写入缓存失败 {sp}: {e}", file=sys.stderr)
    return data

def _load_cache(source_key: str) -> Optional[object]:
    """读取缓存中的数据部分（不含 _meta）"""
    sp = _cache_path(source_key)
    if not sp.exists():
        return None
    try:
        with open(sp, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("data") if isinstance(payload, dict) else payload
    except (json.JSONDecodeError, OSError):
        return None

def _load_cache_meta(source_key: str) -> Optional[dict]:
    """读取缓存的元数据（含 fetched_at）"""
    sp = _cache_path(source_key)
    if not sp.exists():
        return None
    try:
        with open(sp, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("_meta") if isinstance(payload, dict) else None
    except (json.JSONDecodeError, OSError):
        return None

def _save_cache_raw(source_key: str, data: object) -> object:
    """保存预解析数据为本地缓存（用于 CSV/HTML 等非 JSON 源）"""
    sp = _cache_path(source_key)
    payload = {
        "_meta": {
            "source": source_key,
            "url": DATA_SOURCES.get(source_key, {}).get("url", ""),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "data": data,
    }
    try:
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[警告] 写入缓存失败 {sp}: {e}", file=sys.stderr)
    return data

def _parse_csv(text: str) -> List[Dict]:
    """解析 CSV 文本为字典列表"""
    import csv
    import io
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def _parse_nomoreransom_html(html: str) -> List[Dict]:
    """
    解析 NoMoreRansom 解密工具页面，提取家族→解密器映射。
    页面结构：每个解密工具对应一个卡片/区块，含家族名和解密器名。
    出现在此页面即表示该家族有可用解密工具。
    """
    import re
    families = []
    seen = set()

    # 策略1：匹配 <li> 标签内的 "XxxRansom" + 解密器描述
    pattern_li = re.compile(
        r'<li[^>]*>\s*(.+?Ransom)\s*(.*?)(?=</li>)',
        re.DOTALL | re.IGNORECASE,
    )
    for m in pattern_li.finditer(html):
        family_text = m.group(1).strip()
        rest = m.group(2).strip()
        # 提取解密器名（含"解密器"或"Decryptor"的文本）
        dec_match = re.search(r'([\w\s.\-]+(?:解密器|Decryptor|decrypt))', rest, re.IGNORECASE)
        decryptor = dec_match.group(1).strip() if dec_match else ""
        family_name = re.sub(r'<[^>]+>', '', family_text).strip()
        decryptor = re.sub(r'<[^>]+>', '', decryptor).strip()
        if family_name and family_name.lower() not in seen:
            seen.add(family_name.lower())
            families.append({
                "family": family_name,
                "decryptor": decryptor,
                "decryptable": True,
            })

    # 策略2：匹配标题标签中的家族名（兜底）
    if not families:
        pattern_h = re.compile(
            r'<(?:h[2-4]|strong)[^>]*>\s*([A-Za-z0-9]+Ransom)\s*</(?:h[2-4]|strong)>',
            re.IGNORECASE,
        )
        for m in pattern_h.finditer(html):
            family_name = m.group(1).strip()
            if family_name.lower() not in seen:
                seen.add(family_name.lower())
                families.append({
                    "family": family_name,
                    "decryptor": "",
                    "decryptable": True,
                })

    return families


def fetch_source(source_key: str, force_refresh: bool = False) -> Optional[object]:
    """
    联网优先获取数据源内容。在线获取成功时更新本地缓存；
    在线获取失败时降级到本地缓存兜底。

    force_refresh=True 时跳过缓存兜底（在线失败直接返回 None）。
    自动根据 DATA_SOURCES 中的 format 字段选择解析器（json/csv/html）。
    """
    src = DATA_SOURCES.get(source_key)
    if not src:
        print(f"[错误] 未知数据源: {source_key}", file=sys.stderr)
        return None

    # Step 1: 优先在线获取
    fmt = src.get("format", "json")
    raw = _download(src["url"])
    if raw is not None:
        text = raw.decode("utf-8", errors="replace")
        if fmt == "csv":
            data = _parse_csv(text)
            return _save_cache_raw(source_key, data)
        elif fmt == "html":
            data = _parse_nomoreransom_html(text)
            return _save_cache_raw(source_key, data)
        else:
            data = _save_cache(source_key, raw)
            if data is not None:
                return data
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

    # Step 2: 在线获取失败，降级到本地缓存
    if force_refresh:
        # 强制刷新模式：不兜底，直接返回 None
        return None

    fallback = _load_cache(source_key)
    if fallback is not None:
        meta = _load_cache_meta(source_key) or {}
        print(
            f"[降级] 在线获取失败，使用本地缓存兜底 ({source_key}, "
            f"缓存时间: {meta.get('fetched_at', '未知')})",
            file=sys.stderr,
        )
    return fallback

def cache_status() -> List[Dict]:
    """返回所有数据源的本地缓存状态"""
    statuses = []
    for key, src in DATA_SOURCES.items():
        sp = _cache_path(key)
        meta = _load_cache_meta(key)
        exists = _cache_exists(key)
        statuses.append({
            "source": key,
            "description": src["description"],
            "cache_exists": exists,
            "fetched_at": meta.get("fetched_at") if meta else None,
            "cache_path": str(sp),
        })
    return statuses

def refresh_all(force: bool = False) -> Dict[str, bool]:
    """刷新所有数据源。force=True 时在线失败不兜底。"""
    results = {}
    for key in DATA_SOURCES:
        data = fetch_source(key, force_refresh=force)
        results[key] = data is not None
    return results

# ============ 业务查询函数 ============

def _normalize_family_name(family: str) -> str:
    """归一化家族名，便于匹配"""
    return family.lower().strip()

def query_family_activity(family: str) -> Dict:
    """
    查询某家族当前活跃度（来自 ransomware.live）。
    返回该家族最近受害者记录及统计。
    """
    family_norm = _normalize_family_name(family)
    recent = fetch_source("ransomware_live_recentvictims") or []
    groups = fetch_source("ransomware_live_groups") or []

    # 匹配团伙元数据
    group_meta = None
    for g in groups:
        gname = str(g.get("name", "") or g.get("group", "")).lower()
        if family_norm in gname or gname in family_norm:
            group_meta = g
            break

    # 过滤该家族的近期受害者
    family_victims = []
    for v in recent:
        vgroup = str(v.get("group_name", "") or v.get("group", "") or v.get("victim_group", "")).lower()
        if family_norm in vgroup or vgroup in family_norm:
            family_victims.append(v)

    # 统计
    now = datetime.now(timezone.utc)
    last_30d = []
    last_7d = []
    for v in family_victims:
        ts = v.get("published", v.get("discovered", v.get("date")))
        if not ts:
            continue
        try:
            # 尝试解析 ISO 格式
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if (now - dt).days <= 30:
                last_30d.append(v)
            if (now - dt).days <= 7:
                last_7d.append(v)
        except (ValueError, TypeError):
            continue

    return {
        "family": family,
        "group_metadata": group_meta,
        "total_recent_victims": len(family_victims),
        "last_30_days_victims": len(last_30d),
        "last_7_days_victims": len(last_7d),
        "recent_victims": family_victims[:20],
        "data_source": "ransomware.live",
    }

def query_group_onion(family: str) -> Dict:
    """
    查询某家族的 Tor 站点及元数据（来自 ransomwatch）。
    返回 onion 地址、可用状态等。
    """
    family_norm = _normalize_family_name(family)
    groups = fetch_source("ransomwatch_groups") or []

    matched_groups = []
    for g in groups:
        gname = str(g.get("name", "")).lower()
        if family_norm in gname or gname in family_norm:
            matched_groups.append(g)

    # 提取 onion 地址
    onion_addresses = []
    for g in matched_groups:
        for key in ("onion_url", "onion", "tor_url", "url"):
            val = g.get(key)
            if val and ".onion" in str(val):
                onion_addresses.append({"address": val, "source_group": g.get("name", family)})

    return {
        "family": family,
        "matched_groups": matched_groups,
        "onion_addresses": onion_addresses,
        "data_source": "ransomwatch (GitHub)",
    }

def query_recent_victims_by_family(family: str, limit: int = 20) -> Dict:
    """
    查询某家族最近的受害者发布记录（来自 ransomwatch posts）。
    """
    family_norm = _normalize_family_name(family)
    posts = fetch_source("ransomwatch_posts") or []

    family_posts = []
    for p in posts:
        gname = str(p.get("group_name", "") or p.get("group", "")).lower()
        if family_norm in gname or gname in family_norm:
            family_posts.append(p)

    # 按时间倒序（假设有 published 字段）
    family_posts.sort(
        key=lambda x: str(x.get("published", x.get("discovered", ""))),
        reverse=True,
    )

    return {
        "family": family,
        "total_posts": len(family_posts),
        "posts": family_posts[:limit],
        "data_source": "ransomwatch (GitHub)",
    }

def query_extension_online(extension: str) -> Dict:
    """
    通过扩展名在线查询勒索家族（mthcht/awesome-lists CSV 数据源）。
    覆盖 700+ 扩展名，含主流/小众/DIY 变体。
    """
    if not extension:
        return {"error": "未提供扩展名"}
    ext = extension.lower().lstrip(".")

    rows = fetch_source("mthcht_extensions") or []
    matches = []
    for row in rows:
        # CSV 列：file_path（如 *.lockbit）、metadata_comment（家族说明）
        file_path = str(row.get("file_path", "") or "").lower()
        if not file_path:
            continue
        # 匹配 *.ext 或直接 .ext
        if file_path == f"*.{ext}" or file_path.endswith(f".{ext}"):
            matches.append({
                "extension": f".{ext}",
                "family_hint": str(row.get("metadata_comment", ""))[:200],
                "source": "mthcht/awesome-lists",
            })

    return {
        "extension": f".{ext}",
        "total_matches": len(matches),
        "matches": matches[:20],
        "data_source": "mthcht/awesome-lists (GitHub CSV)",
        "csv_rows_total": len(rows),
    }

def query_decryptor_online(family: str) -> Dict:
    """
    在线查询家族解密工具状态（NoMoreRansom 数据源）。
    出现在 NoMoreRansom 页面即表示有公开解密工具。
    """
    family_norm = _normalize_family_name(family)
    families = fetch_source("nomoreransom_decryptors") or []

    matches = []
    for f in families:
        fname = str(f.get("family", "")).lower()
        if family_norm in fname or fname in family_norm:
            matches.append(f)

    return {
        "family": family,
        "decryptable": len(matches) > 0,
        "decryptors": matches,
        "data_source": "NoMoreRansom Project",
        "nomoreransom_url": "https://www.nomoreransom.org/zh/decryption-tools.html" if matches else "",
    }

def query_all_groups_overview() -> Dict:
    """
    获取所有勒索团伙概览（来自 ransomware.live + ransomwatch）。
    用于了解当前哪些家族最活跃。
    """
    live_groups = fetch_source("ransomware_live_groups") or []
    rw_groups = fetch_source("ransomwatch_groups") or []
    recent = fetch_source("ransomware_live_recentvictims") or []

    # 统计每个家族的近期受害者数
    victim_counts: Dict[str, int] = {}
    for v in recent:
        gname = str(v.get("group_name", "") or v.get("group", "")).strip()
        if gname:
            victim_counts[gname] = victim_counts.get(gname, 0) + 1

    # 合并团伙信息
    overview = []
    seen = set()
    for g in live_groups:
        name = str(g.get("name", g.get("group", ""))).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            overview.append({
                "name": name,
                "victims_count": victim_counts.get(name, 0),
                "source": "ransomware.live",
                "meta": g,
            })
    for g in rw_groups:
        name = str(g.get("name", "")).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            overview.append({
                "name": name,
                "victims_count": victim_counts.get(name, 0),
                "source": "ransomwatch",
                "meta": g,
            })

    # 按受害者数排序
    overview.sort(key=lambda x: x["victims_count"], reverse=True)

    return {
        "total_groups": len(overview),
        "total_recent_victims": len(recent),
        "groups": overview[:50],
        "data_sources": ["ransomware.live", "ransomwatch"],
    }

def online_lookup(family: str) -> Dict:
    """
    统一在线查询入口：汇总某家族的全部在线情报。
    """
    return {
        "family": family,
        "activity": query_family_activity(family),
        "onion_sites": query_group_onion(family),
        "recent_victims": query_recent_victims_by_family(family, limit=20),
        "decryptor_status": query_decryptor_online(family),
        "cache_status": cache_status(),
    }

# ============ CLI ============

def cmd_online(args):
    """在线查询命令"""
    if args.subcmd == "family":
        result = online_lookup(args.family)
    elif args.subcmd == "groups":
        result = query_all_groups_overview()
    elif args.subcmd == "extension":
        result = query_extension_online(args.extension)
    elif args.subcmd == "decryptor":
        result = query_decryptor_online(args.family)
    elif args.subcmd == "status":
        result = {"cache": cache_status()}
    elif args.subcmd == "refresh":
        result = {"refresh_results": refresh_all(force=args.force)}
    else:
        print(f"未知子命令: {args.subcmd}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

def add_online_subparser(subparsers):
    p = subparsers.add_parser("online", help="零 Key 在线情报查询")
    p_sub = p.add_subparsers(dest="subcmd", required=True)

    p_family = p_sub.add_parser("family", help="查询指定家族的全部在线情报")
    p_family.add_argument("family", type=str, help="勒索家族名，如 LockBit")
    p_family.set_defaults(func=cmd_online)

    p_groups = p_sub.add_parser("groups", help="查看所有勒索团伙概览")
    p_groups.set_defaults(func=cmd_online)

    p_ext = p_sub.add_parser("extension", help="按扩展名在线查询勒索家族（mthcht CSV）")
    p_ext.add_argument("extension", type=str, help="加密文件扩展名，如 .lockbit")
    p_ext.set_defaults(func=cmd_online)

    p_dec = p_sub.add_parser("decryptor", help="在线查询家族解密工具状态（NoMoreRansom）")
    p_dec.add_argument("family", type=str, help="勒索家族名")
    p_dec.set_defaults(func=cmd_online)

    p_status = p_sub.add_parser("status", help="查看本地缓存状态")
    p_status.set_defaults(func=cmd_online)

    p_refresh = p_sub.add_parser("refresh", help="刷新所有数据源（联网优先，失败兜底到缓存）")
    p_refresh.add_argument("--force", action="store_true", help="强制重新下载（忽略缓存）")
    p_refresh.set_defaults(func=cmd_online)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="零 Key 在线情报查询")
    sub = parser.add_subparsers(dest="subcmd", required=True)
    add_online_subparser(sub)
    args = parser.parse_args()
    args.func(args)
