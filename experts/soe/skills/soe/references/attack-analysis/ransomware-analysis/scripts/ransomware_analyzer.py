#!/usr/bin/env python3
"""
勒索病毒分析器 - 核心分析逻辑
基于多维度特征匹配识别勒索家族、分析入侵路径、评估数据恢复可能性
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# 资源文件路径
ASSETS_DIR = Path(__file__).parent.parent / "assets"


def load_yaml(filename: str) -> dict:
    """加载 YAML 资源文件"""
    filepath = ASSETS_DIR / filename
    if not filepath.exists():
        print(f"[警告] 资源文件不存在: {filepath}", file=sys.stderr)
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_families_db() -> dict:
    return load_yaml("ransomware_families.yaml")


def load_intrusion_vectors() -> dict:
    return load_yaml("intrusion_vectors.yaml")


def load_decryptors() -> dict:
    return load_yaml("decryptors.yaml")


# ============ 家族匹配 ============

def match_by_extension(extension: str, families: dict) -> List[Dict]:
    """扩展名匹配"""
    matches = []
    if not extension:
        return matches
    ext = extension.lower().lstrip(".")
    for fam in families.get("families", []):
        family_exts = [e.lower().lstrip(".") for e in fam.get("extensions", [])]
        if ext in family_exts:
            matches.append({
                "family": fam["name"],
                "confidence": "high",
                "matched_dimension": "extension",
                "matched_value": f".{ext}",
            })
    return matches


def match_by_note_filename(filename: str, families: dict) -> List[Dict]:
    """勒索信文件名匹配"""
    matches = []
    if not filename:
        return matches
    fname = filename.lower()
    for fam in families.get("families", []):
        for nf in fam.get("note_filenames", []):
            if nf.lower() in fname or fname in nf.lower():
                matches.append({
                    "family": fam["name"],
                    "confidence": "medium",
                    "matched_dimension": "note_filename",
                    "matched_value": nf,
                })
    return matches


def match_by_note_keywords(note: str, families: dict) -> List[Dict]:
    """勒索信关键词匹配"""
    matches = []
    if not note:
        return matches
    note_lower = note.lower()
    for fam in families.get("families", []):
        hit_keywords = []
        for kw in fam.get("note_keywords", []):
            if kw.lower() in note_lower:
                hit_keywords.append(kw)
        if hit_keywords:
            total_kw = len(fam.get("note_keywords", []))
            hit_ratio = len(hit_keywords) / total_kw if total_kw > 0 else 0
            confidence = "high" if hit_ratio >= 0.5 else ("medium" if hit_ratio >= 0.25 else "low")
            matches.append({
                "family": fam["name"],
                "confidence": confidence,
                "matched_dimension": "note_keywords",
                "matched_value": hit_keywords,
                "hit_ratio": f"{hit_ratio:.0%}",
            })
    return matches


def match_by_iocs(iocs: Dict, families: dict) -> List[Dict]:
    """IOC 匹配"""
    matches = []
    if not iocs:
        return matches
    for fam in families.get("families", []):
        known_iocs = fam.get("known_iocs", {})
        hit_iocs = []
        for ioc_type, values in iocs.items():
            known_values = [v.lower() for v in known_iocs.get(ioc_type, [])]
            for v in values:
                if v.lower() in known_values:
                    hit_iocs.append({"type": ioc_type, "value": v})
        if hit_iocs:
            matches.append({
                "family": fam["name"],
                "confidence": "high",
                "matched_dimension": "ioc",
                "matched_value": hit_iocs,
            })
    return matches


# ============ 置信度综合 ============

def aggregate_matches(all_matches: List[Dict]) -> Optional[Dict]:
    """综合所有维度匹配结果，计算最终置信度"""
    if not all_matches:
        return None

    family_scores = {}
    for m in all_matches:
        fam = m["family"]
        if fam not in family_scores:
            family_scores[fam] = {
                "family": fam,
                "dimensions": [],
                "max_confidence": "low",
            }
        family_scores[fam]["dimensions"].append({
            "dimension": m["matched_dimension"],
            "confidence": m["confidence"],
            "value": m["matched_value"],
        })
        conf_order = {"low": 1, "medium": 2, "high": 3}
        if conf_order.get(m["confidence"], 0) > conf_order.get(family_scores[fam]["max_confidence"], 0):
            family_scores[fam]["max_confidence"] = m["confidence"]

    for fam, score in family_scores.items():
        dim_count = len(score["dimensions"])
        if dim_count >= 3:
            score["final_confidence"] = "high"
        elif dim_count >= 2:
            score["final_confidence"] = "medium" if score["max_confidence"] != "high" else "high"
        else:
            score["final_confidence"] = score["max_confidence"]

    conf_order = {"low": 1, "medium": 2, "high": 3}
    sorted_families = sorted(
        family_scores.values(),
        key=lambda x: (conf_order.get(x["final_confidence"], 0), len(x["dimensions"])),
        reverse=True,
    )
    return sorted_families[0] if sorted_families else None


# ============ IOC 提取 ============

def extract_iocs_from_note(note: str) -> Dict:
    """从勒索信提取 IOC"""
    try:
        from ioc_extractor import extract_iocs
        return extract_iocs(note)
    except ImportError:
        import re
        patterns = {
            "btc_address": re.compile(r"\bbc1[ac-hj-np-z02-9]{6,87}\b|\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
            "tor_onion": re.compile(r"\b[a-z2-7]{16,56}\.onion\b", re.IGNORECASE),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "telegram": re.compile(r"(?:@|t\.me/)([A-Za-z0-9_]{5,32})", re.IGNORECASE),
        }
        iocs = {}
        for ioc_type, pattern in patterns.items():
            matches = pattern.findall(note)
            seen = set()
            unique = []
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if m not in seen:
                    seen.add(m)
                    unique.append(m)
            if unique:
                iocs[ioc_type] = unique
        return iocs


# ============ 入侵路径分析 ============

def analyze_intrusion(family: str, env: dict) -> Dict:
    """分析入侵路径"""
    vectors_db = load_intrusion_vectors()
    families_db = load_families_db()

    result = {
        "family": family,
        "known_vectors": [],
        "environment_matches": [],
        "likely_entry_point": None,
        "lateral_movement": [],
    }

    for fam in families_db.get("families", []):
        if fam["name"].lower() == family.lower():
            result["known_vectors"] = fam.get("intrusion_vectors", [])
            break

    for vector in vectors_db.get("vectors", []):
        indicators = vector.get("environment_indicators", [])
        for ind in indicators:
            env_key = ind.get("env_key")
            env_value = ind.get("env_value")
            if env_key and env.get(env_key) == env_value:
                result["environment_matches"].append({
                    "vector": vector["name"],
                    "description": vector.get("description", ""),
                    "matched_indicator": f"{env_key}={env_value}",
                })

    if result["environment_matches"]:
        result["likely_entry_point"] = result["environment_matches"][0]["vector"]
    elif result["known_vectors"]:
        result["likely_entry_point"] = result["known_vectors"][0]

    for fam in families_db.get("families", []):
        if fam["name"].lower() == family.lower():
            result["lateral_movement"] = fam.get("lateral_movement", [])
            break

    return result


# ============ 数据恢复评估 ============

def check_decryptor(family: str) -> Dict:
    """查询解密工具"""
    decryptors_db = load_decryptors()
    for dec in decryptors_db.get("decryptors", []):
        if family.lower() in [f.lower() for f in dec.get("families", [])]:
            return {
                "available": True,
                "tool_name": dec.get("name", ""),
                "source": dec.get("source", ""),
                "url": dec.get("url", ""),
                "notes": dec.get("notes", ""),
            }
    return {
        "available": False,
        "message": f"未找到 {family} 的已知解密工具。建议访问 NoMoreRansom 项目查询最新状态。",
        "nomoreransom_url": "https://www.nomoreransom.org/",
    }


# ============ 主分析流程 ============

def analyze(note: str = "", extension: str = "", note_filename: str = "") -> Dict:
    """完整分析流程"""
    families_db = load_families_db()
    all_matches = []

    if extension:
        all_matches.extend(match_by_extension(extension, families_db))

    if note_filename:
        all_matches.extend(match_by_note_filename(note_filename, families_db))

    if note:
        all_matches.extend(match_by_note_keywords(note, families_db))

    iocs = extract_iocs_from_note(note) if note else {}
    if iocs:
        all_matches.extend(match_by_iocs(iocs, families_db))

    best_match = aggregate_matches(all_matches)

    family_info = None
    if best_match:
        for fam in families_db.get("families", []):
            if fam["name"].lower() == best_match["family"].lower():
                family_info = fam
                break

    return {
        "best_match": best_match,
        "all_matches": all_matches,
        "extracted_iocs": iocs,
        "family_info": family_info,
    }


# ============ CLI ============

def cmd_analyze(args):
    """分析命令"""
    result = analyze(
        note=args.note or "",
        extension=args.extension or "",
        note_filename=args.note_filename or "",
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n" + "=" * 60)
        print("勒索病毒分析结果")
        print("=" * 60)

        if not result["best_match"]:
            print("\n[!] 未能识别勒索家族，请补充更多信息。")
        else:
            bm = result["best_match"]
            print(f"\n[+] 识别家族: {bm['family']}")
            print(f"    置信度:   {bm['final_confidence']}")
            print(f"    匹配维度: {len(bm['dimensions'])} 个")
            for d in bm["dimensions"]:
                print(f"      - {d['dimension']} ({d['confidence']}): {d['value']}")

        if result["extracted_iocs"]:
            print(f"\n[+] 提取到 IOC:")
            for ioc_type, values in result["extracted_iocs"].items():
                print(f"    {ioc_type}:")
                for v in values:
                    print(f"      - {v}")

        if result["family_info"]:
            fi = result["family_info"]
            print(f"\n[+] 家族信息:")
            print(f"    别名:     {', '.join(fi.get('aliases', []))}")
            print(f"    首次出现: {fi.get('first_seen', '未知')}")
            print(f"    活跃状态: {fi.get('status', '未知')}")
            print(f"    入侵向量: {', '.join(fi.get('intrusion_vectors', []))}")


def cmd_intrusion(args):
    """入侵路径分析命令"""
    env = json.loads(args.env) if args.env else {}
    result = analyze_intrusion(args.family, env)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_recovery(args):
    """数据恢复评估命令"""
    result = check_decryptor(args.family)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_online(args):
    """在线情报查询命令（委托给 online_query 模块）"""
    try:
        from online_query import (
            online_lookup,
            query_all_groups_overview,
            query_extension_online,
            query_decryptor_online,
            cache_status,
            refresh_all,
        )
    except ImportError:
        # 兼容作为模块导入的路径
        sys.path.insert(0, str(Path(__file__).parent))
        from online_query import (
            online_lookup,
            query_all_groups_overview,
            query_extension_online,
            query_decryptor_online,
            cache_status,
            refresh_all,
        )

    if args.online_cmd == "family":
        result = online_lookup(args.family)
    elif args.online_cmd == "groups":
        result = query_all_groups_overview()
    elif args.online_cmd == "extension":
        result = query_extension_online(args.extension)
    elif args.online_cmd == "decryptor":
        result = query_decryptor_online(args.family)
    elif args.online_cmd == "status":
        result = {"caches": cache_status()}
    elif args.online_cmd == "refresh":
        result = {"refresh_results": refresh_all(force=args.force)}
    else:
        print(f"未知子命令: {args.online_cmd}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="勒索病毒分析工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    p_analyze = subparsers.add_parser("analyze", help="多维度家族识别")
    p_analyze.add_argument("--note", type=str, help="勒索信内容")
    p_analyze.add_argument("--extension", type=str, help="加密文件扩展名")
    p_analyze.add_argument("--note-filename", type=str, help="勒索信文件名")
    p_analyze.add_argument("--json", action="store_true", help="JSON 输出")
    p_analyze.set_defaults(func=cmd_analyze)

    p_intrusion = subparsers.add_parser("intrusion", help="入侵路径分析")
    p_intrusion.add_argument("--family", type=str, required=True, help="勒索家族名")
    p_intrusion.add_argument("--env", type=str, help="环境信息 JSON")
    p_intrusion.set_defaults(func=cmd_intrusion)

    p_recovery = subparsers.add_parser("recovery", help="数据恢复评估")
    p_recovery.add_argument("--family", type=str, required=True, help="勒索家族名")
    p_recovery.set_defaults(func=cmd_recovery)

    p_online = subparsers.add_parser("online", help="零 Key 在线情报查询")
    p_online.add_argument("online_cmd",
                          choices=["family", "groups", "extension", "decryptor", "status", "refresh"],
                          help="family <家族名> | groups | extension <扩展名> | decryptor <家族名> | status | refresh [--force]")
    p_online.add_argument("--family", type=str, help="勒索家族名（family/decryptor 子命令必填）")
    p_online.add_argument("--extension", type=str, help="加密文件扩展名（extension 子命令必填）")
    p_online.add_argument("--force", action="store_true", help="强制刷新缓存（refresh 子命令）")
    p_online.set_defaults(func=cmd_online)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    if args.command == "online" and args.online_cmd == "family" and not args.family:
        print("[错误] online family 子命令需要 --family 参数", file=sys.stderr)
        sys.exit(1)
    if args.command == "online" and args.online_cmd == "decryptor" and not args.family:
        print("[错误] online decryptor 子命令需要 --family 参数", file=sys.stderr)
        sys.exit(1)
    if args.command == "online" and args.online_cmd == "extension" and not args.extension:
        print("[错误] online extension 子命令需要 --extension 参数", file=sys.stderr)
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
