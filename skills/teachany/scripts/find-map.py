#!/usr/bin/env python3
"""
find-map.py · TeachAny 地图资源查询工具 v1.0
============================================

在制作课件前，优先查 skill 自带的地图库，而不是每次都生成新的。

用法：
  python3 find-map.py <关键词>                     # 模糊搜索
  python3 find-map.py --dynasty tang              # 查指定朝代
  python3 find-map.py --era 1492                  # 查指定年份的世界地图
  python3 find-map.py --region europe             # 按区域
  python3 find-map.py --base hillshade            # 查底图
  python3 find-map.py --boundary country          # 查国界/省界
  python3 find-map.py --list-all                  # 列出全部资源
  python3 find-map.py --copy <文件名> <目标目录>  # 把资源拷到课件

示例：
  python3 find-map.py 文艺复兴
  python3 find-map.py --era 1500 --region europe
  python3 find-map.py --copy global-hillshade-4k.jpg ./community/my-course/assets/maps/
"""

import argparse
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent  # skill root when script lives in skill/scripts/
REPO_ROOT = SKILL_ROOT.parent
LOCAL_MAP_ROOTS = [
    SKILL_ROOT / "assets" / "maps",
    REPO_ROOT / "assets" / "maps",
    SKILL_ROOT / "assets",
]
REMOTE_MAP_BASE = "https://raw.githubusercontent.com/weponusa/teachany/main/assets/maps"
MAPS_ROOT = next((p for p in LOCAL_MAP_ROOTS if (p / "MANIFEST.json").exists()), LOCAL_MAP_ROOTS[0])
MANIFEST = MAPS_ROOT / "MANIFEST.json"

# 关键词到资源的模糊映射表（中文/英文别名 → 库中文件 key）
KEYWORD_ALIASES = {
    # 中国朝代
    "秦": "qin-dynasty", "汉": "han-dynasty", "西汉": "west-han-dynasty", "东汉": "east-han-dynasty",
    "三国": "three-kingdoms", "西晋": "jin-west-dynasty", "东晋": "jin-east-dynasty",
    "南北朝": "northern-southern", "隋": "sui-dynasty", "唐": "tang-dynasty",
    "五代": "five-dynasties", "辽": "liao-dynasty", "北宋": "north-song-dynasty",
    "金": "jin-jurchen", "宋": "song-dynasty", "南宋": "south-song-dynasty",
    "元": "yuan-dynasty", "明": "ming-dynasty", "清": "qing-dynasty",
    # 世界时期
    "文艺复兴": "ce-1492-age-of-discovery", "宗教改革": "ce-1600",
    "大航海": "ce-1492-age-of-discovery", "哥伦布": "ce-1492-age-of-discovery",
    "亚历山大": "bce-323-alexander", "罗马": "bce-1", "蒙古": "ce-1300-mongol-peak",
    "一战": "ce-1914-wwi", "二战": "ce-1945-wwii",
    "维也纳": "ce-1815-vienna", "拿破仑": "ce-1815-vienna",
    "殖民": "ce-1880", "当代": "ce-2000",
}


def load_manifest():
    if MANIFEST.exists():
        with open(MANIFEST) as f:
            data = json.load(f)
        data["_source"] = str(MANIFEST)
        data["_remote"] = False
        return data
    url = REMOTE_MAP_BASE + "/MANIFEST.json"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        data["_source"] = url
        data["_remote"] = True
        return data
    except Exception as e:
        sys.exit(f"❌ 找不到本地地图 manifest，远端也加载失败：{e}")


def format_file(entry, show_full=False):
    """格式化一条资源显示"""
    cat = entry["category"]
    path = entry["path"]
    size_kb = entry["size_bytes"] / 1024
    size_str = f"{size_kb:.0f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"

    name = entry.get("name_zh") or entry.get("subtype") or ""
    year = ""
    if "year_start" in entry:
        y1, y2 = entry["year_start"], entry.get("year_end", "")
        year = f"[{y1}-{y2}]"
    elif "year" in entry:
        year = f"[{entry['year']}]"

    note = entry.get("note", "")
    if show_full:
        return f"  📍 {path}\n      {name} {year} · {size_str}\n      {note}"
    else:
        return f"  📍 {path:<55} {name:<15} {year:<12} {size_str:>7}"


def search_by_keyword(files, kw):
    """按关键词模糊搜索"""
    kw_lower = kw.lower()
    results = []

    # 先查中文别名
    alias_key = KEYWORD_ALIASES.get(kw)

    for f in files:
        path = f["path"].lower()
        key = f.get("key", "").lower()
        name = f.get("name_zh", "")
        note = f.get("note", "")

        if alias_key and alias_key == f.get("key"):
            results.append(f)
        elif kw_lower in path or kw_lower in key:
            results.append(f)
        elif kw in name or kw in note:
            results.append(f)

    return results


def search_by_era(files, year, region=None):
    """按年份查世界地图（最接近的）"""
    candidates = [f for f in files if f["category"] == "chrono-world"]
    if not candidates:
        return []
    # 找最接近的 year
    best = min(candidates, key=lambda f: abs(f.get("year", 0) - year))
    results = [best]
    # 也返回前后 1 个
    idx = candidates.index(best)
    if idx > 0:
        results.insert(0, candidates[idx - 1])
    if idx < len(candidates) - 1:
        results.append(candidates[idx + 1])
    return results


def search_by_dynasty(files, dynasty_key):
    """按朝代查中国地图"""
    dynasty_key = dynasty_key.lower()
    return [f for f in files if f["category"] == "chrono-cn" and
            (dynasty_key in f.get("key", "").lower() or dynasty_key in f.get("name_zh", ""))]


def search_base(files, base_type):
    """查底图类资源"""
    if base_type == "hillshade":
        return [f for f in files if f.get("subtype") == "hillshade"]
    elif base_type == "coastline":
        return [f for f in files if f.get("subtype") == "coastline"]
    elif base_type == "rivers":
        return [f for f in files if f.get("subtype") == "rivers"]
    elif base_type == "lakes":
        return [f for f in files if f.get("subtype") == "lakes"]
    elif base_type == "terrain-tiles":
        return [f for f in files if f.get("subtype") == "terrain-tiles"]
    return []


def search_boundary(files, boundary_type):
    """查行政边界"""
    if boundary_type in ("country", "countries", "world", "国界"):
        return [f for f in files if "countries" in f["path"].lower() or "admin_0" in f["path"].lower()]
    elif boundary_type in ("province", "provinces", "省界"):
        return [f for f in files if "provinces" in f["path"].lower() or "china-provinces" in f["path"].lower()]
    elif boundary_type in ("city", "cities", "市"):
        return [f for f in files if "cities" in f["path"].lower() or "china-cities" in f["path"].lower()]
    return []


def copy_resource(filename, dst_dir):
    """把一个或多个资源从本地库拷贝到课件目录；本地无资源时从远端下载。"""
    dst = Path(dst_dir).resolve()
    dst.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()
    matches = [f for f in manifest.get("files", []) if filename in f.get("path", "") or filename in f.get("key", "")]
    local_candidates = list(MAPS_ROOT.rglob(f"*{filename}*")) if MAPS_ROOT.exists() else []

    if len(local_candidates) > 1:
        print(f"⚠️  找到 {len(local_candidates)} 个本地匹配：")
        for c in local_candidates:
            print(f"   - {c.relative_to(MAPS_ROOT)}")
        print("\n请提供更精确的文件名")
        return 2

    if local_candidates:
        src = local_candidates[0]
        dst_file = dst / src.name
        shutil.copy2(src, dst_file)
        source_label = str(src)
    else:
        if not matches:
            print(f"❌ 在地图库 manifest 中没找到 {filename}")
            return 1
        if len(matches) > 1:
            print(f"⚠️  找到 {len(matches)} 个远端匹配：")
            for m in matches:
                print(f"   - {m.get('path')}")
            print("\n请提供更精确的文件名")
            return 2
        rel = matches[0]["path"]
        url = REMOTE_MAP_BASE + "/" + rel
        dst_file = dst / Path(rel).name
        try:
            urllib.request.urlretrieve(url, dst_file)
        except Exception as e:
            print(f"❌ 下载失败: {url}\n   {e}")
            return 1
        source_label = url

    size_kb = dst_file.stat().st_size / 1024
    size_str = f"{size_kb:.0f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
    print("✅ 已拷贝:")
    print(f"   源: {source_label}")
    print(f"   目标: {dst_file}")
    print(f"   大小: {size_str}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="TeachAny 地图资源查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("keyword", nargs="?", help="关键词模糊搜索（中文/英文）")
    parser.add_argument("--dynasty", help="查指定朝代（如 tang、qin、song）")
    parser.add_argument("--era", type=int, help="查指定年份的世界地图")
    parser.add_argument("--region", help="区域过滤（europe/asia/china/world）")
    parser.add_argument("--base", choices=["hillshade", "coastline", "rivers", "lakes", "terrain-tiles"],
                        help="查底图类资源")
    parser.add_argument("--boundary", help="查行政边界（country/province/city）")
    parser.add_argument("--list-all", action="store_true", help="列出全部资源")
    parser.add_argument("--copy", nargs=2, metavar=("FILE", "DST"),
                        help="把资源拷到课件: --copy <文件名> <目标目录>")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    # 特殊命令：复制
    if args.copy:
        sys.exit(copy_resource(args.copy[0], args.copy[1]))

    manifest = load_manifest()
    files = manifest["files"]

    # 筛选结果
    if args.list_all:
        results = files
    elif args.dynasty:
        results = search_by_dynasty(files, args.dynasty)
    elif args.era:
        results = search_by_era(files, args.era)
    elif args.base:
        results = search_base(files, args.base)
    elif args.boundary:
        results = search_boundary(files, args.boundary)
    elif args.keyword:
        results = search_by_keyword(files, args.keyword)
    else:
        # 默认：显示库的统计 + 分类提示
        print("🗺️  TeachAny 地图资源库")
        print(f"   位置: {manifest.get('_source', str(MANIFEST))}")
        stats = manifest["stats"]
        print(f"   总数: {stats['total_files']} 个文件 · {stats['total_size_mb']:.1f} MB")
        print()
        print("📂 分类:")
        for cat, info in stats["by_category"].items():
            desc = manifest["categories"].get(cat, "")
            print(f"   {cat:<15} {info['files']:>3} 个 · {info['size_mb']:>5.1f} MB · {desc}")
        print()
        print("💡 用法示例:")
        print("   python3 find-map.py 唐                           # 查唐朝地图")
        print("   python3 find-map.py --era 1500                  # 查 1500 年前后世界地图")
        print("   python3 find-map.py --base hillshade            # 查全球地形底图")
        print("   python3 find-map.py --boundary country          # 查世界国界")
        print("   python3 find-map.py --copy tang-dynasty ./assets/maps/")
        print()
        print("详情看 --help")
        return 0

    # 输出结果
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print(f"⚠️  没找到匹配的资源")
        print(f"   可以试试：python3 find-map.py --list-all")
        return 1

    print(f"🎯 找到 {len(results)} 个匹配资源：\n")
    for r in results:
        print(format_file(r, show_full=args.verbose))
    print()
    print(f"💡 使用: <img src=\"./assets/maps/<文件名>\"> 或用 --copy 把资源拷到课件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
