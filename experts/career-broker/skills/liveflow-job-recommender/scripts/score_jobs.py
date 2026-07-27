#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_jobs.py — 加权打分 + 客户端过滤

用法：
    cat candidates.json | python score_jobs.py \
      --user-level P5 \
      --user-location-id 1 \
      --user-position "产品策划" \
      --user-department-id 26832 \
      --tags-json '{"skill_tags":[{"tag":"产品策划","weight":0.95}, ...]}' \
      --top 7

输入（stdin）：list of jobs，每条含 _llm_position / _llm_tier / _matched_kw 字段
输出（stdout）：top N 排序后的列表 + 每条的 _score / _filtered_reason
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from typing import Optional


# ============= 职级过滤（详见 skills/liveflow-job-recommender/references/level-range-rules.md） =============

def parse_level(level_str: str) -> Optional[tuple]:
    if not level_str:
        return None
    s = str(level_str).strip().upper()
    m = re.match(r'^([PTSML]+)(\d+)', s)
    if not m:
        return None
    return m.group(1), int(m.group(2))


def parse_job_levels(level_field: str) -> list:
    if not level_field:
        return []
    out = []
    for part in str(level_field).split(','):
        parsed = parse_level(part.strip())
        if parsed:
            out.append(parsed)
    return out


def level_within_range(job_level_field, user_level_str: str, tolerance: int = 1) -> bool:
    user = parse_level(user_level_str)
    if not user or user[0] == 'S':
        return True
    user_prefix, user_num = user
    candidates = parse_job_levels(job_level_field)
    if not candidates:
        return True
    for _, num in candidates:
        if abs(num - user_num) <= tolerance:
            return True
    return False


def is_management_job(job: dict) -> bool:
    return bool(job.get('initMrgPositionLevelName'))


# ============= 评分 =============

def keyword_match_score(job_title: str, profile_tags: list) -> float:
    """命中标签数 / 总标签数（按 weight 加权）"""
    if not job_title or not profile_tags:
        return 0.0
    title = str(job_title)
    hit_weight = 0.0
    total_weight = 0.0
    for t in profile_tags:
        tag = t.get('tag') if isinstance(t, dict) else str(t)
        weight = t.get('weight', 1.0) if isinstance(t, dict) else 1.0
        total_weight += weight
        # 任意子串命中（拆开 4 字以上的标签）
        keywords = [tag] + ([tag[:4]] if len(tag) > 4 else [])
        if any(k and k in title for k in keywords):
            hit_weight += weight
    return hit_weight / total_weight if total_weight > 0 else 0.0


def cluster_fit_score(llm_position: str, job_cluster: str) -> float:
    """LLM 选的职位 vs 实际岗位的族——简单包含匹配。"""
    if not llm_position or not job_cluster:
        return 0.5
    return 1.0 if llm_position in str(job_cluster) or str(job_cluster) in llm_position else 0.5


def tier_weight(tier: str) -> float:
    return {'primary': 1.0, 'stretch': 0.8, 'explore': 0.6}.get(tier, 0.5)


def same_location_bonus(job: dict, user_location_id: str = '', user_location_name: str = '') -> float:
    if user_location_id and str(job.get('recruitLocationId') or '') == str(user_location_id):
        return 1.0
    if user_location_name and str(job.get('recruitLocationName') or '') == str(user_location_name):
        return 1.0
    return 0.0


def same_position_bonus(job: dict, user_position: str = '') -> float:
    if not user_position:
        return 0.0
    pos = str(user_position)
    for field in ('mappingInnerPostName', 'recruitPostName', '_llm_position'):
        val = str(job.get(field) or '')
        if val and (pos in val or val in pos):
            return 1.0
    return 0.0


def is_current_department(job: dict, user_department_id: str = '', user_department_name: str = '') -> bool:
    if user_department_id and str(job.get('departmentId') or '') == str(user_department_id):
        return True
    if user_department_name and str(job.get('departmentName') or '') == str(user_department_name):
        return True
    return False


def score_job(job: dict, profile_tags: list, user_location_id: str = '', user_location_name: str = '', user_position: str = '') -> float:
    return round(
        0.30 * keyword_match_score(job.get('recruitPostName', ''), profile_tags)
        + 0.25 * cluster_fit_score(job.get('_llm_position', ''), job.get('clusterName', ''))
        + 0.20 * tier_weight(job.get('_llm_tier', ''))
        + 0.15 * same_location_bonus(job, user_location_id, user_location_name)
        + 0.10 * same_position_bonus(job, user_position),
        4,
    )


# ============= 主流程 =============

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user-level', default='', help='用户当前职级，如 P5/T7/S3 或留空')
    ap.add_argument('--user-location-id', default='', help='用户当前工作地 ID，来自 profile.basic.work_location_id')
    ap.add_argument('--user-location-name', default='', help='用户当前工作地名称，来自 profile.basic.work_location')
    ap.add_argument('--user-position', default='', help='用户当前职位，来自 profile.basic.position_name/position')
    ap.add_argument('--user-department-id', default='', help='用户当前部门 ID；用于屏蔽当前部门岗位')
    ap.add_argument('--user-department-name', default='', help='用户当前部门名称；用于屏蔽当前部门岗位')
    ap.add_argument('--tags-json', required=True, help='profile_compact 的 skill_tags + domain_tags 合并 JSON')
    ap.add_argument('--top', type=int, default=7)
    ap.add_argument('--input', default='-', help='候选 JSON 文件，- 表示 stdin')
    args = ap.parse_args()

    # 读输入
    if args.input == '-':
        candidates = json.load(sys.stdin)
    else:
        candidates = json.load(open(args.input, encoding='utf-8'))

    # 读标签
    tags_dict = json.loads(args.tags_json)
    profile_tags = tags_dict.get('skill_tags', []) + tags_dict.get('domain_tags', [])

    # 过滤
    survivors = []
    dropped = {'state': 0, 'mgmt': 0, 'level': 0, 'current_department': 0}
    for job in candidates:
        if job.get('state') != 1:
            dropped['state'] += 1
            continue
        if is_management_job(job):
            dropped['mgmt'] += 1
            continue
        if is_current_department(job, args.user_department_id, args.user_department_name):
            dropped['current_department'] += 1
            continue
        if not level_within_range(job.get('estimatePassLevelName'), args.user_level):
            dropped['level'] += 1
            continue
        survivors.append(job)

    # 评分
    for job in survivors:
        job['_score'] = score_job(job, profile_tags, args.user_location_id, args.user_location_name, args.user_position)
        job['_same_location'] = bool(same_location_bonus(job, args.user_location_id, args.user_location_name))
        job['_same_position'] = bool(same_position_bonus(job, args.user_position))

    # 排序
    survivors.sort(key=lambda x: -x['_score'])
    top = survivors[:args.top]

    # 兜底放宽
    if len(top) < 3 and args.user_level:
        relaxed = []
        for job in candidates:
            if job.get('state') != 1 or is_management_job(job):
                continue
            if is_current_department(job, args.user_department_id, args.user_department_name):
                continue
            if level_within_range(job.get('estimatePassLevelName'), args.user_level, tolerance=2):
                if job not in survivors:
                    job['_score'] = score_job(job, profile_tags, args.user_location_id, args.user_location_name, args.user_position)
                    job['_same_location'] = bool(same_location_bonus(job, args.user_location_id, args.user_location_name))
                    job['_same_position'] = bool(same_position_bonus(job, args.user_position))
                    job['_relaxed'] = True
                    relaxed.append(job)
        relaxed.sort(key=lambda x: -x['_score'])
        top = (top + relaxed)[:args.top]

    print(json.dumps({
        'total_candidates': len(candidates),
        'dropped': dropped,
        'survivors': len(survivors),
        'top': top,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
