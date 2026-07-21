#!/usr/bin/env python3
"""TeachAny Knowledge Layer utilities.

Subcommands:
- audit: inspect completeness/readiness of the knowledge layer
- lookup: return compact graph-first topic context for courseware generation
- find-node: find the best-matching tree node for a given node_id or name
- link: link a courseware to its tree node (update status + courses path)

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
NODE_INDEX_PATH = ROOT / "data" / "node-index.json"
MD_DIR = ROOT / "skill" / "data" / "kp-md"


# ═══════════════════════════════════════════════════════════════
#  v2 Lookup：基于 node-index.json + MD 的统一查询入口
#  方案 Y+ 起，excerpts 已并入 MD，这里是唯一真相源的对外接口。
# ═══════════════════════════════════════════════════════════════

def load_node_index_v2() -> Optional[Dict[str, Any]]:
    if not NODE_INDEX_PATH.exists():
        return None
    try:
        data = json.load(open(NODE_INDEX_PATH, encoding='utf-8'))
        if isinstance(data, dict) and isinstance(data.get("nodes"), dict):
            return data
    except Exception:
        pass
    return None


def lookup_v2(topic: str, subject: Optional[str] = None, top: int = 3) -> Optional[Dict[str, Any]]:
    """基于 node-index.json 的 lookup，返回与 v1 相似的 payload 结构"""
    idx = load_node_index_v2()
    if not idx:
        return None

    topic_norm = normalize_text(topic)
    subj_norm = (subject or "").strip().lower()

    scored = []
    for nid, node in idx["nodes"].items():
        if subj_norm:
            if (node.get("subject","").lower() != subj_norm
                and node.get("curriculum","").lower() != subj_norm):
                continue
        score = 0
        name_zh = node.get("name_zh", "")
        name_en = (node.get("name_en") or "").lower()
        if topic_norm == normalize_text(name_zh): score += 100
        elif topic_norm in normalize_text(name_zh): score += 40
        if topic.lower() == name_en: score += 80
        elif topic.lower() in name_en: score += 30
        if topic_norm in normalize_text(nid): score += 10
        if score > 0:
            scored.append((score, nid, node))

    scored.sort(key=lambda x: -x[0])
    matches = []
    for score, nid, node in scored[:top]:
        md_excerpt = ""
        md_sections = []
        md_path = node.get("md_path")
        if md_path:
            abs_md = ROOT / md_path
            if abs_md.exists():
                md_text = abs_md.read_text(encoding='utf-8')
                md_sections = re.findall(r'^##\s+([^\n]+)', md_text, re.M)
                # 提取「课标原文」部分作为 excerpt preview
                mm = re.search(
                    r'^##\s+课标原文[^\n]*\n(.*?)(?=^##\s|\Z)',
                    md_text, re.M | re.S
                )
                if mm:
                    md_excerpt = mm.group(1).strip()[:500]
        matches.append({
            "score": score,
            "node_id": nid,
            "name_zh": node.get("name_zh"),
            "name_en": node.get("name_en"),
            "subject": node.get("subject"),
            "stage": node.get("stage"),
            "curriculum": node.get("curriculum"),
            "domain": node.get("domain"),
            "grade": node.get("grade"),
            "md_path": md_path,
            "md_status": node.get("md_status"),
            "md_sections": md_sections,
            "md_curriculum_excerpt": md_excerpt,
            "hero_image": node.get("hero_image"),
            "prereq_ids": node.get("prereq_ids", []),
            "next_ids": node.get("next_ids", []),
            "courses": node.get("courses", []),
            "tree_path": node.get("tree_path"),
        })

    return {
        "topic": topic,
        "subject": subject,
        "match_count": len(scored),
        "matches": matches,
        "_source": "node-index-v2",
    }


def print_lookup_v2_human(payload: Dict[str, Any]) -> None:
    topic = payload.get("topic", "")
    print(f"# Knowledge Layer Lookup (v2): {topic}")
    print(f"# Source: {payload.get('_source')}, total_match={payload.get('match_count')}\n")
    matches = payload.get("matches", [])
    if not matches:
        print("No matches found.")
        return
    for i, m in enumerate(matches, 1):
        print(f"## Match {i}: {m['name_zh']}  ({m['subject']}/{m['stage']}/{m['curriculum']})")
        print(f"- node_id: {m['node_id']}")
        print(f"- domain:  {m.get('domain')}")
        if m.get("md_path"):
            print(f"- md:      {m['md_path']}  [{m.get('md_status')}]")
        if m.get("hero_image"):
            print(f"- hero:    {m['hero_image']}")
        if m.get("prereq_ids"):
            print(f"- 前驱:    {', '.join(m['prereq_ids'][:5])}")
        if m.get("next_ids"):
            print(f"- 后续:    {', '.join(m['next_ids'][:5])}")
        if m.get("md_curriculum_excerpt"):
            print("- 课标原文节选:")
            for line in m["md_curriculum_excerpt"].splitlines()[:8]:
                print(f"    {line}")
        print()


@dataclass
class DomainBundle:
    subject: str
    domain: str
    graph_path: Path
    graph: Dict[str, Any]
    errors_path: Optional[Path]
    errors: Optional[Dict[str, Any]]
    exercises_path: Optional[Path]
    exercises: Optional[Dict[str, Any]]


REQUIRED_NODE_FIELDS = [
    "id",
    "name",
    "name_en",
    "grade",
    "semester",
    "unit",
    "definition",
    "key_concepts",
    "prerequisites",
    "leads_to",
    "real_world",
    "memory_anchors",
    "bloom_verbs",
]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def coerce_item_list(payload: Optional[Any], key: str) -> List[Dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        value = payload.get(key, [])
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def iter_domain_dirs(data_dir: Path) -> Iterable[Tuple[str, Path]]:
    for subject_dir in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        for domain_dir in sorted(p for p in subject_dir.iterdir() if p.is_dir()):
            yield subject_dir.name, domain_dir


def load_bundles(data_dir: Path = DATA_DIR) -> List[DomainBundle]:
    bundles: List[DomainBundle] = []
    for subject, domain_dir in iter_domain_dirs(data_dir):
        graph_path = domain_dir / "_graph.json"
        if not graph_path.exists():
            continue
        errors_path = domain_dir / "_errors.json"
        exercises_path = domain_dir / "_exercises.json"
        graph = load_json(graph_path)
        errors = load_json(errors_path) if errors_path.exists() else None
        exercises = load_json(exercises_path) if exercises_path.exists() else None
        bundles.append(
            DomainBundle(
                subject=subject,
                domain=domain_dir.name,
                graph_path=graph_path,
                graph=graph,
                errors_path=errors_path if errors_path.exists() else None,
                errors=errors,
                exercises_path=exercises_path if exercises_path.exists() else None,
                exercises=exercises,
            )
        )
    return bundles


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


def subject_alias_map() -> Dict[str, str]:
    aliases = {
        "math": ["math", "数学"],
        "chinese": ["chinese", "语文", "中文"],
        "english": ["english", "英语"],
        "physics": ["physics", "物理"],
        "chemistry": ["chemistry", "化学"],
        "biology": ["biology", "bio", "生物", "生物学"],
        "science": ["science", "sci", "科学", "小学科学"],
        "geography": ["geography", "geo", "地理"],
        "history": ["history", "hist", "历史"],
        "info-tech": ["info-tech", "信息技术", "信息", "编程", "ai"],
    }
    result: Dict[str, str] = {}
    for canonical, names in aliases.items():
        for name in names:
            result[normalize_text(name)] = canonical
    return result


def resolve_subject(subject: Optional[str]) -> Optional[str]:
    if not subject:
        return None
    return subject_alias_map().get(normalize_text(subject), subject)


def build_global_indices(bundles: List[DomainBundle]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Tuple[str, str]]]:
    node_index: Dict[str, Dict[str, Any]] = {}
    node_home: Dict[str, Tuple[str, str]] = {}
    for bundle in bundles:
        for node in bundle.graph.get("nodes", []):
            node_id = node.get("id")
            if not node_id:
                continue
            node_index[node_id] = node
            node_home[node_id] = (bundle.subject, bundle.domain)
    return node_index, node_home


def compute_node_score(topic: str, bundle: DomainBundle, node: Dict[str, Any]) -> int:
    topic_n = normalize_text(topic)
    name = normalize_text(str(node.get("name", "")))
    name_en = normalize_text(str(node.get("name_en", "")))
    node_id = normalize_text(str(node.get("id", "")))
    domain = normalize_text(bundle.domain)
    score = 0
    if topic_n == name or topic_n == name_en or topic_n == node_id:
        score += 200
    if topic_n and topic_n in name:
        score += 120
    if topic_n and topic_n in name_en:
        score += 110
    if topic_n and topic_n in node_id:
        score += 100
    if topic_n and topic_n in domain:
        score += 60
    for concept in node.get("key_concepts", []):
        concept_n = normalize_text(str(concept))
        if topic_n and topic_n in concept_n:
            score += 15
    for text in node.get("real_world", []):
        text_n = normalize_text(str(text))
        if topic_n and topic_n in text_n:
            score += 10
    return score


def find_matches(bundles: List[DomainBundle], topic: str, subject: Optional[str] = None) -> List[Tuple[int, DomainBundle, Dict[str, Any]]]:
    subject = resolve_subject(subject)
    matches: List[Tuple[int, DomainBundle, Dict[str, Any]]] = []
    for bundle in bundles:
        if subject and bundle.subject != subject:
            continue
        for node in bundle.graph.get("nodes", []):
            score = compute_node_score(topic, bundle, node)
            if score > 0:
                matches.append((score, bundle, node))
    matches.sort(key=lambda item: (-item[0], item[1].subject, item[1].domain, item[2].get("name", "")))
    return matches


def summarize_refs(node_ids: List[str], node_index: Dict[str, Dict[str, Any]], node_home: Dict[str, Tuple[str, str]]) -> List[Dict[str, Any]]:
    output = []
    for node_id in node_ids:
        node = node_index.get(node_id)
        home = node_home.get(node_id)
        if node and home:
            output.append(
                {
                    "id": node_id,
                    "name": node.get("name"),
                    "subject": home[0],
                    "domain": home[1],
                    "grade": node.get("grade"),
                }
            )
        else:
            output.append({"id": node_id, "name": None, "subject": None, "domain": None, "grade": None})
    return output


def compact_node_summary(
    bundle: DomainBundle,
    node: Dict[str, Any],
    node_index: Dict[str, Dict[str, Any]],
    node_home: Dict[str, Tuple[str, str]],
    max_errors: int,
    max_exercises: int,
) -> Dict[str, Any]:
    node_id = node.get("id")
    error_items = []
    for item in coerce_item_list(bundle.errors, "errors"):
        if item.get("node_id") == node_id:
            error_items.append(
                {
                    "id": item.get("id"),
                    "type": item.get("type"),
                    "description": item.get("description"),
                    "diagnosis": item.get("diagnosis"),
                    "trigger": item.get("trigger"),
                    "frequency": item.get("frequency"),
                }
            )
    exercise_items = []
    for item in coerce_item_list(bundle.exercises, "exercises"):
        if item.get("node_id") == node_id:
            exercise_items.append(
                {
                    "id": item.get("id"),
                    "bloom_level": item.get("bloom_level"),
                    "difficulty": item.get("difficulty"),
                    "type": item.get("type"),
                    "stem": item.get("stem"),
                }
            )
    return {
        "subject": bundle.subject,
        "domain": bundle.domain,
        "curriculum": bundle.graph.get("curriculum"),
        "node": {
            "id": node.get("id"),
            "name": node.get("name"),
            "name_en": node.get("name_en"),
            "grade": node.get("grade"),
            "semester": node.get("semester"),
            "unit": node.get("unit"),
            "definition": node.get("definition"),
            "key_concepts": node.get("key_concepts", []),
            "prerequisites": summarize_refs(node.get("prerequisites", []), node_index, node_home),
            "leads_to": summarize_refs(node.get("leads_to", []), node_index, node_home),
            "real_world": node.get("real_world", []),
            "curriculum_standards": node.get("curriculum_standards", []),
            "memory_anchors": node.get("memory_anchors", []),
            "bloom_verbs": node.get("bloom_verbs", {}),
        },
        "error_count": len(error_items),
        "exercise_count": len(exercise_items),
        "errors": error_items[:max_errors],
        "exercises": exercise_items[:max_exercises],
        "source_files": {
            "graph": str(bundle.graph_path.relative_to(ROOT)),
            "errors": str(bundle.errors_path.relative_to(ROOT)) if bundle.errors_path else None,
            "exercises": str(bundle.exercises_path.relative_to(ROOT)) if bundle.exercises_path else None,
        },
    }


def domain_readiness_label(has_graph: bool, has_errors: bool, has_exercises: bool) -> str:
    if has_graph and has_errors and has_exercises:
        return "full"
    if has_graph and (has_errors or has_exercises):
        return "partial+"
    if has_graph:
        return "graph-only"
    return "missing"


def audit_bundles(bundles: List[DomainBundle], subject: Optional[str] = None) -> Dict[str, Any]:
    subject = resolve_subject(subject)
    filtered = [b for b in bundles if not subject or b.subject == subject]
    node_index, node_home = build_global_indices(filtered)
    issues: List[Dict[str, Any]] = []
    subject_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "domains": 0,
        "graph_domains": 0,
        "error_domains": 0,
        "exercise_domains": 0,
        "nodes": 0,
        "edges": 0,
    })
    global_node_counter: Counter[str] = Counter()

    for bundle in filtered:
        graph_nodes = bundle.graph.get("nodes", [])
        graph_edges = bundle.graph.get("edges", [])
        has_graph = True
        has_errors = bundle.errors is not None
        has_exercises = bundle.exercises is not None

        s = subject_stats[bundle.subject]
        s["domains"] += 1
        s["graph_domains"] += 1 if has_graph else 0
        s["error_domains"] += 1 if has_errors else 0
        s["exercise_domains"] += 1 if has_exercises else 0
        s["nodes"] += len(graph_nodes)
        s["edges"] += len(graph_edges)

        if not has_errors:
            issues.append({
                "severity": "medium",
                "subject": bundle.subject,
                "domain": bundle.domain,
                "type": "missing_errors",
                "message": "缺少 _errors.json，错因诊断与干扰项支持不足",
            })
        if not has_exercises:
            issues.append({
                "severity": "medium",
                "subject": bundle.subject,
                "domain": bundle.domain,
                "type": "missing_exercises",
                "message": "缺少 _exercises.json，分层练习与题库复用不足",
            })

        local_ids = set()
        for node in graph_nodes:
            node_id = node.get("id")
            if not node_id:
                issues.append({
                    "severity": "high",
                    "subject": bundle.subject,
                    "domain": bundle.domain,
                    "type": "missing_node_id",
                    "message": "存在缺少 id 的知识点节点",
                })
                continue
            global_node_counter[node_id] += 1
            if node_id in local_ids:
                issues.append({
                    "severity": "high",
                    "subject": bundle.subject,
                    "domain": bundle.domain,
                    "type": "duplicate_node_id_in_domain",
                    "message": f"节点 ID 重复：{node_id}",
                })
            local_ids.add(node_id)
            missing_fields = [field for field in REQUIRED_NODE_FIELDS if field not in node]
            if missing_fields:
                issues.append({
                    "severity": "high",
                    "subject": bundle.subject,
                    "domain": bundle.domain,
                    "type": "missing_required_fields",
                    "message": f"节点 {node_id} 缺少字段：{', '.join(missing_fields)}",
                })

        for node in graph_nodes:
            node_id = node.get("id", "<unknown>")
            for rel_field in ("prerequisites", "leads_to"):
                for ref in node.get(rel_field, []):
                    if ref not in node_index:
                        issues.append({
                            "severity": "high",
                            "subject": bundle.subject,
                            "domain": bundle.domain,
                            "type": "dangling_node_ref",
                            "message": f"节点 {node_id} 的 {rel_field} 引用了不存在的 ID：{ref}",
                        })

        for edge in graph_edges:
            frm = edge.get("from")
            to = edge.get("to")
            if frm not in node_index or to not in node_index:
                issues.append({
                    "severity": "high",
                    "subject": bundle.subject,
                    "domain": bundle.domain,
                    "type": "dangling_edge_ref",
                    "message": f"边 {frm} -> {to} 引用了不存在的节点",
                })

        if has_errors:
            for item in coerce_item_list(bundle.errors, "errors"):
                node_id = item.get("node_id")
                if node_id not in node_index:
                    issues.append({
                        "severity": "high",
                        "subject": bundle.subject,
                        "domain": bundle.domain,
                        "type": "error_node_missing",
                        "message": f"错误项 {item.get('id')} 引用了不存在的 node_id：{node_id}",
                    })

        if has_exercises:
            local_error_ids = {item.get("id") for item in coerce_item_list(bundle.errors, "errors")}
            for item in coerce_item_list(bundle.exercises, "exercises"):
                node_id = item.get("node_id")
                if node_id not in node_index:
                    issues.append({
                        "severity": "high",
                        "subject": bundle.subject,
                        "domain": bundle.domain,
                        "type": "exercise_node_missing",
                        "message": f"题目 {item.get('id')} 引用了不存在的 node_id：{node_id}",
                    })
                for option in item.get("options", []):
                    error_id = option.get("error_id")
                    if error_id and error_id not in local_error_ids:
                        issues.append({
                            "severity": "high",
                            "subject": bundle.subject,
                            "domain": bundle.domain,
                            "type": "exercise_error_missing",
                            "message": f"题目 {item.get('id')} 引用了不存在的 error_id：{error_id}",
                        })

    duplicates = [node_id for node_id, count in global_node_counter.items() if count > 1]
    for node_id in duplicates:
        issues.append({
            "severity": "high",
            "subject": None,
            "domain": None,
            "type": "duplicate_node_id_global",
            "message": f"全局节点 ID 重复：{node_id}",
        })

    total_domains = len(filtered)
    total_nodes = sum(len(bundle.graph.get("nodes", [])) for bundle in filtered)
    graph_domains = total_domains
    error_domains = sum(1 for bundle in filtered if bundle.errors is not None)
    exercise_domains = sum(1 for bundle in filtered if bundle.exercises is not None)
    full_domains = sum(1 for bundle in filtered if bundle.errors is not None and bundle.exercises is not None)
    partial_domains = sum(1 for bundle in filtered if (bundle.errors is not None) ^ (bundle.exercises is not None))

    graph_coverage = 1.0 if total_domains else 0.0
    assessment_coverage = full_domains / total_domains if total_domains else 0.0
    metadata_issues = sum(1 for item in issues if item["type"] in {"missing_required_fields", "missing_node_id", "duplicate_node_id_in_domain", "duplicate_node_id_global", "dangling_node_ref", "dangling_edge_ref"})
    consistency_score = max(0.0, 1.0 - (metadata_issues / max(1, total_nodes)))
    courseware_readiness_score = 0.5 * graph_coverage + 0.35 * assessment_coverage + 0.15 * consistency_score

    if courseware_readiness_score >= 0.85:
        readiness = "ready"
        readiness_desc = "可以直接作为课程制作主知识底座"
    elif courseware_readiness_score >= 0.65:
        readiness = "mostly-ready"
        readiness_desc = "图谱足以支撑大部分课程制作，但练习/错因层仍需补强"
    else:
        readiness = "partial"
        readiness_desc = "只能作为部分知识底座，尚不足以稳定支撑课程生成闭环"

    return {
        "scope": subject or "all",
        "summary": {
            "domains": total_domains,
            "nodes": total_nodes,
            "graph_domains": graph_domains,
            "error_domains": error_domains,
            "exercise_domains": exercise_domains,
            "full_domains": full_domains,
            "partial_domains": partial_domains,
            "graph_coverage_ratio": round(graph_coverage, 4),
            "assessment_coverage_ratio": round(assessment_coverage, 4),
            "consistency_score": round(consistency_score, 4),
            "courseware_readiness_score": round(courseware_readiness_score, 4),
            "courseware_readiness": readiness,
            "courseware_readiness_desc": readiness_desc,
        },
        "by_subject": dict(subject_stats),
        "issues": issues,
    }


def print_audit_human(report: Dict[str, Any]) -> None:
    summary = report["summary"]
    print("# TeachAny Knowledge Layer Audit")
    print(f"Scope: {report['scope']}")
    print()
    print("## Summary")
    print(f"- Domains: {summary['domains']}")
    print(f"- Nodes: {summary['nodes']}")
    print(f"- Graph coverage: {summary['graph_domains']}/{summary['domains']} ({summary['graph_coverage_ratio']:.0%})")
    print(f"- Error DB coverage: {summary['error_domains']}/{summary['domains']}")
    print(f"- Exercise DB coverage: {summary['exercise_domains']}/{summary['domains']}")
    print(f"- Full teaching bundles (_graph + _errors + _exercises): {summary['full_domains']}/{summary['domains']}")
    print(f"- Consistency score: {summary['consistency_score']:.0%}")
    print(f"- Courseware readiness: {summary['courseware_readiness']} ({summary['courseware_readiness_score']:.0%})")
    print(f"- Conclusion: {summary['courseware_readiness_desc']}")
    print()
    print("## By Subject")
    for subject, stats in sorted(report["by_subject"].items()):
        print(
            f"- {subject}: domains={stats['domains']}, nodes={stats['nodes']}, "
            f"errors={stats['error_domains']}, exercises={stats['exercise_domains']}"
        )
    high = [item for item in report["issues"] if item["severity"] == "high"]
    medium = [item for item in report["issues"] if item["severity"] == "medium"]
    print()
    print("## Issues")
    print(f"- High severity: {len(high)}")
    print(f"- Medium severity: {len(medium)}")
    preview = high[:10] + medium[:10]
    for item in preview:
        scope = f"{item['subject']}/{item['domain']}" if item["subject"] and item["domain"] else "global"
        print(f"  - [{item['severity']}] {scope}: {item['message']}")
    if len(report["issues"]) > len(preview):
        print(f"  - ... {len(report['issues']) - len(preview)} more issue(s)")


def print_lookup_human(matches: List[Dict[str, Any]], topic: str) -> None:
    print(f"# Knowledge Layer Lookup: {topic}")
    if not matches:
        print("No matches found.")
        return
    for idx, item in enumerate(matches, 1):
        node = item["node"]
        print()
        print(f"## Match {idx}: {node['name']} ({item['subject']}/{item['domain']})")
        print(f"- Grade/Semester: {node['grade']} / {node['semester']}")
        print(f"- Unit: {node['unit']}")
        print(f"- Definition: {node['definition']}")
        print(f"- Key concepts: {'；'.join(node['key_concepts'])}")
        if node["prerequisites"]:
            print("- Prerequisites: " + "；".join(
                ref["name"] or ref["id"] for ref in node["prerequisites"]
            ))
        if node["leads_to"]:
            print("- Leads to: " + "；".join(
                ref["name"] or ref["id"] for ref in node["leads_to"]
            ))
        if node["real_world"]:
            print("- Real-world anchors: " + "；".join(node["real_world"]))
        if node["memory_anchors"]:
            print("- Memory anchors: " + "；".join(node["memory_anchors"]))
        print(f"- Errors available: {item['error_count']}")
        print(f"- Exercises available: {item['exercise_count']}")
        if item["errors"]:
            print("- Error preview:")
            for err in item["errors"]:
                print(f"  - {err['description']}｜{err['diagnosis']}")
        if item["exercises"]:
            print("- Exercise preview:")
            for ex in item["exercises"]:
                print(f"  - [{ex['bloom_level']}] {ex['stem']}")
        print("- Source files:")
        print(f"  - graph: {item['source_files']['graph']}")
        if item['source_files']['errors']:
            print(f"  - errors: {item['source_files']['errors']}")
        if item['source_files']['exercises']:
            print(f"  - exercises: {item['source_files']['exercises']}")


# ═══════════════════════════════════════════════════════════════
#  知识树节点查找与课件关联
# ═══════════════════════════════════════════════════════════════

TREES_DIR = ROOT / "data" / "trees"
SKILLHUB_TREES_DIR = ROOT / "skillhub-package" / "references" / "data" / "trees"

# node_id 别名映射表：课件 manifest 中使用的 node_id → 知识树中对应的节点 ID
# 这个映射解决 _graph.json 中的 node_id 与 trees/*.json 中节点 ID 不一致的问题
NODE_ID_ALIASES: Dict[str, List[str]] = {
    "periodic-table": ["element-concept"],       # 元素周期表 → 元素与元素周期表
    "atomic-structure": ["atom-structure"],       # 原子结构 → 原子的构成
}


def load_all_trees(trees_dir: Path = TREES_DIR) -> List[Dict[str, Any]]:
    """加载所有知识树 JSON 文件"""
    trees = []
    if not trees_dir.exists():
        return trees
    for tree_file in sorted(trees_dir.rglob("*.json")):
        if tree_file.name.startswith("_"):
            continue
        try:
            tree = load_json(tree_file)
            if not isinstance(tree, dict) or "domains" not in tree:
                continue
            tree["_file_path"] = tree_file
            tree["_file_name"] = str(tree_file.relative_to(trees_dir))
            trees.append(tree)
        except (json.JSONDecodeError, OSError):
            continue
    return trees


def find_tree_node(
    trees: List[Dict[str, Any]],
    node_id: Optional[str] = None,
    name: Optional[str] = None,
    subject: Optional[str] = None,
    grade: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """在知识树中查找匹配的节点，返回带评分的匹配列表。

    支持三种匹配方式（按优先级）：
    1. 精确 node_id 匹配（含别名映射）
    2. 名称模糊匹配
    3. _graph.json 中的 node_id 与树节点 ID 交叉匹配
    """
    matches: List[Dict[str, Any]] = []
    subject = resolve_subject(subject)

    # 展开别名：如果 node_id 在别名表中，也搜索对应的树节点 ID
    search_ids = [node_id] if node_id else []
    if node_id and node_id in NODE_ID_ALIASES:
        search_ids.extend(NODE_ID_ALIASES[node_id])

    for tree in trees:
        tree_subject = tree.get("subject", "")
        tree_name = tree.get("name", "")
        tree_file = tree.get("_file_name", "")

        # 学科过滤
        if subject and resolve_subject(tree_subject) != subject:
            continue

        for domain in tree.get("domains", []):
            for node in domain.get("nodes", []):
                tree_node_id = node.get("id", "")
                node_name = node.get("name", "")
                score = 0

                # 1. 精确 node_id 匹配
                if node_id and tree_node_id in search_ids:
                    score += 500

                # 2. 别名反向匹配：树节点 ID 在别名映射的目标列表中
                if node_id:
                    for alias_key, alias_targets in NODE_ID_ALIASES.items():
                        if tree_node_id in alias_targets and alias_key == node_id:
                            score += 480

                # 3. 名称精确匹配
                if name and normalize_text(name) == normalize_text(node_name):
                    score += 300

                # 4. 名称模糊匹配
                if name:
                    name_n = normalize_text(name)
                    node_name_n = normalize_text(node_name)
                    if name_n and name_n in node_name_n:
                        score += 200
                    if node_name_n and node_name_n in name_n:
                        score += 150

                # 5. node_id 与名称交叉匹配（如 periodic-table 在 "元素周期表" 中）
                if node_id:
                    node_id_n = normalize_text(node_id)
                    node_name_n = normalize_text(node_name)
                    if node_id_n and node_id_n in node_name_n:
                        score += 100
                    # 反向：名称关键词在 node_id 中
                    for part in node_name_n.replace("与", " ").split():
                        if len(part) >= 2 and part in node_id_n:
                            score += 50

                # 6. 年级匹配加分
                if grade is not None and node.get("grade") == grade:
                    score += 30

                if score > 0:
                    matches.append({
                        "score": score,
                        "tree_file": tree_file,
                        "tree_subject": tree_subject,
                        "tree_name": tree_name,
                        "domain_id": domain.get("id", ""),
                        "domain_name": domain.get("name", ""),
                        "node_id": tree_node_id,
                        "node_name": node_name,
                        "node_grade": node.get("grade"),
                        "node_status": node.get("status", "gap"),
                        "node_courses": node.get("courses", []),
                        "file_path": str(tree.get("_file_path", "")),
                    })

    matches.sort(key=lambda m: (-m["score"], m["tree_file"], m["node_id"]))
    return matches


def link_courseware_to_tree(
    courseware_dir: str,
    trees_dirs: Optional[List[Path]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """将课件自动关联到知识树节点。

    读取课件的 manifest.json，通过 node_id/subject/grade/name 查找
    对应的知识树节点，将 status 改为 active 并添加 courses 路径。
    """
    courseware_path = Path(courseware_dir)
    if not courseware_path.exists():
        return {"error": f"课件目录不存在: {courseware_dir}"}

    manifest_path = courseware_path / "manifest.json"
    if not manifest_path.exists():
        return {"error": f"manifest.json 不存在: {manifest_path}"}

    manifest = load_json(manifest_path)
    node_id = manifest.get("node_id", "")
    subject = manifest.get("subject", "")
    grade = manifest.get("grade")
    name = manifest.get("name", "")

    # 课件相对路径（用于 courses 字段）
    try:
        course_rel = str(courseware_path.relative_to(ROOT))
    except ValueError:
        course_rel = courseware_dir

    # 搜索所有 trees 目录
    if trees_dirs is None:
        trees_dirs = [TREES_DIR, SKILLHUB_TREES_DIR]

    all_matches: List[Dict[str, Any]] = []
    for trees_dir in trees_dirs:
        if not trees_dir.exists():
            continue
        trees = load_all_trees(trees_dir)
        matches = find_tree_node(
            trees, node_id=node_id, name=name, subject=subject, grade=grade
        )
        for m in matches:
            m["trees_dir"] = str(trees_dir)
        all_matches.extend(matches)

    if not all_matches:
        return {
            "error": "未找到匹配的知识树节点",
            "search_params": {"node_id": node_id, "name": name, "subject": subject, "grade": grade},
            "hint": "检查 manifest.json 中的 node_id 或 name 是否与知识树中的节点对应",
        }

    # 取最佳匹配
    best = all_matches[0]
    results: List[Dict[str, Any]] = []

    # 更新所有匹配的树文件（同名文件在多个 trees_dir 中）
    for match in all_matches:
        if match["score"] < best["score"] * 0.5:
            continue  # 跳过分数过低的匹配

        tree_file = Path(match["file_path"])
        if not tree_file.exists():
            continue

        tree = load_json(tree_file)
        updated = False

        for domain in tree.get("domains", []):
            if domain.get("id") != match["domain_id"]:
                continue
            for node in domain.get("nodes", []):
                if node.get("id") != match["node_id"]:
                    continue

                old_status = node.get("status", "gap")
                old_courses = list(node.get("courses", []))

                # 添加课件路径（避免重复）
                if course_rel not in old_courses:
                    old_courses.append(course_rel)

                # 更新节点
                node["status"] = "active"
                node["courses"] = old_courses
                updated = True

                results.append({
                    "tree_file": str(tree_file),
                    "domain_id": match["domain_id"],
                    "node_id": match["node_id"],
                    "node_name": match["node_name"],
                    "old_status": old_status,
                    "new_status": "active",
                    "old_courses": match["node_courses"],
                    "new_courses": old_courses,
                    "score": match["score"],
                })
                break

        if updated and not dry_run:
            # 写回文件
            tree.pop("_file_path", None)
            tree.pop("_file_name", None)
            with tree_file.open("w", encoding="utf-8") as fh:
                json.dump(tree, fh, ensure_ascii=False, indent=2)
                fh.write("\n")

    return {
        "courseware": course_rel,
        "manifest": {"node_id": node_id, "name": name, "subject": subject, "grade": grade},
        "updated_nodes": results,
        "dry_run": dry_run,
    }


def print_find_node_human(matches: List[Dict[str, Any]], query: str) -> None:
    """人类可读的 find-node 输出"""
    print(f"# Tree Node Search: {query}")
    if not matches:
        print("No matching nodes found.")
        return
    for idx, m in enumerate(matches, 1):
        print()
        print(f"## Match {idx} (score: {m['score']})")
        print(f"- Tree: {m['tree_name']} ({m['tree_file']})")
        print(f"- Domain: {m['domain_name']} ({m['domain_id']})")
        print(f"- Node: {m['node_name']} (id={m['node_id']})")
        print(f"- Grade: {m['node_grade']}")
        print(f"- Status: {m['node_status']}")
        if m["node_courses"]:
            print(f"- Courses: {', '.join(m['node_courses'])}")
        print(f"- File: {m['file_path']}")


def print_link_human(result: Dict[str, Any]) -> None:
    """人类可读的 link 输出"""
    if "error" in result:
        print(f"❌ {result['error']}")
        if "hint" in result:
            print(f"💡 {result['hint']}")
        if "search_params" in result:
            sp = result["search_params"]
            print(f"   搜索参数: node_id={sp.get('node_id')}, name={sp.get('name')}, "
                  f"subject={sp.get('subject')}, grade={sp.get('grade')}")
        return

    print(f"# Link Courseware: {result['courseware']}")
    manifest = result["manifest"]
    print(f"  Manifest: node_id={manifest['node_id']}, name={manifest['name']}, "
          f"subject={manifest['subject']}, grade={manifest['grade']}")
    if result.get("dry_run"):
        print("  ⚠️ DRY RUN - no files modified")

    for idx, node in enumerate(result.get("updated_nodes", []), 1):
        print()
        print(f"  [{idx}] {node['node_name']} (id={node['node_id']})")
        print(f"      File: {node['tree_file']}")
        print(f"      Status: {node['old_status']} → {node['new_status']}")
        print(f"      Courses: {node['old_courses']} → {node['new_courses']}")
        print(f"      Score: {node['score']}")

    if not result.get("updated_nodes"):
        print("  No nodes were updated.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TeachAny Knowledge Layer utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="Audit completeness/readiness of the knowledge layer")
    audit.add_argument("--subject", help="Restrict to one subject, e.g. math / 数学")
    audit.add_argument("--json", action="store_true", help="Print JSON report")

    lookup = sub.add_parser("lookup", help="Lookup compact topic context from the knowledge layer")
    lookup.add_argument("--topic", required=True, help="Topic keyword, e.g. 一次函数 / photosynthesis")
    lookup.add_argument("--subject", help="Optional subject filter")
    lookup.add_argument("--top", type=int, default=3, help="Maximum number of matches to return")
    lookup.add_argument("--errors", type=int, default=3, help="Max error items per node")
    lookup.add_argument("--exercises", type=int, default=3, help="Max exercise items per node")
    lookup.add_argument("--json", action="store_true", help="Print JSON result")

    find_node = sub.add_parser("find-node", help="Find the best-matching tree node for a node_id or name")
    find_node.add_argument("--node-id", help="Node ID from manifest (e.g. periodic-table, linear-function)")
    find_node.add_argument("--name", help="Topic name in Chinese (e.g. 元素周期表, 一次函数)")
    find_node.add_argument("--subject", help="Subject filter (e.g. chemistry, math)")
    find_node.add_argument("--grade", type=int, help="Grade level filter (e.g. 9)")
    find_node.add_argument("--json", action="store_true", help="Print JSON result")

    link = sub.add_parser("link", help="Link a courseware to its tree node (update status + courses)")
    link.add_argument("courseware_dir", help="Path to the courseware directory (e.g. examples/chem-periodic-table)")
    link.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    link.add_argument("--json", action="store_true", help="Print JSON result")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    bundles = load_bundles(DATA_DIR)

    if args.command == "audit":
        report = audit_bundles(bundles, subject=args.subject)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_audit_human(report)
        return 0

    if args.command == "lookup":
        # 方案 Y+：优先使用基于 node-index.json + MD 的 v2 lookup
        v2 = lookup_v2(args.topic, subject=args.subject, top=args.top)
        if v2 and v2.get("match_count", 0) > 0:
            if args.json:
                print(json.dumps(v2, ensure_ascii=False, indent=2))
            else:
                print_lookup_v2_human(v2)
            return 0
        # v2 无结果时，回退到旧 bundles 路径（保留兼容）
        matches = find_matches(bundles, topic=args.topic, subject=args.subject)
        node_index, node_home = build_global_indices(bundles)
        compact = [
            compact_node_summary(bundle, node, node_index, node_home, args.errors, args.exercises)
            for _, bundle, node in matches[: args.top]
        ]
        payload = {
            "topic": args.topic,
            "subject": resolve_subject(args.subject) if args.subject else None,
            "match_count": len(matches),
            "matches": compact,
            "_source": "legacy-bundles",
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_lookup_human(compact, args.topic)
        return 0

    if args.command == "find-node":
        trees_dirs = [TREES_DIR, SKILLHUB_TREES_DIR]
        all_matches: List[Dict[str, Any]] = []
        for trees_dir in trees_dirs:
            if not trees_dir.exists():
                continue
            trees = load_all_trees(trees_dir)
            matches = find_tree_node(
                trees,
                node_id=args.node_id,
                name=args.name,
                subject=args.subject,
                grade=args.grade,
            )
            for m in matches:
                m["trees_dir"] = str(trees_dir)
            all_matches.extend(matches)

        # 去重：同一 tree_file + node_id 只保留最高分
        seen: Dict[str, Dict[str, Any]] = {}
        for m in all_matches:
            key = f"{m['tree_file']}:{m['node_id']}"
            if key not in seen or m["score"] > seen[key]["score"]:
                seen[key] = m
        deduped = sorted(seen.values(), key=lambda m: -m["score"])

        if args.json:
            print(json.dumps({"matches": deduped}, ensure_ascii=False, indent=2))
        else:
            query = args.node_id or args.name or ""
            print_find_node_human(deduped, query)
        return 0

    if args.command == "link":
        result = link_courseware_to_tree(
            args.courseware_dir,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_link_human(result)
        return 0

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
