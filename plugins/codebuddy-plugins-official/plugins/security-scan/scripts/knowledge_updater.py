#!/usr/bin/env python3
"""
知识库更新工具 — 解决 Sink/Defense/Secret 模式的知识腐化问题

设计理念：
  检测模式不应该只是写死的静态文件。安全生态变化快，新框架、新 API、
  新攻击手法不断涌现。本工具提供三层防腐机制：
    1. 版本追踪 — 每个知识文件有 version + last_updated 元数据
    2. 过期检测 — check-freshness 检查哪些知识需要更新
    3. 候选生成 — suggest-updates 利用 WebSearch 生成候选更新（人工审核后合并）

子命令：
  1. check-freshness    — 检查所有知识文件的新鲜度，标记过期文件
  2. suggest-updates    — 为过期文件生成候选更新建议（输出到 pending-updates/）
  3. apply-update       — 将审核通过的候选更新合并到知识文件
  4. show-versions      — 显示所有知识文件的版本信息

工作流：
  # 1. 检查哪些知识过期了
  python3 knowledge_updater.py check-freshness --resource-dir resource/

  # 2. 为过期文件生成候选更新（需要编排器或人工触发 WebSearch）
  python3 knowledge_updater.py suggest-updates --resource-dir resource/ --output-dir pending-updates/

  # 3. 人工审核 pending-updates/*.yaml 后，合并到正式知识文件
  python3 knowledge_updater.py apply-update --update-file pending-updates/sink-patterns-update.yaml --target resource/scan-data/sink-patterns.yaml

跨平台：Python3 内置模块，零外部依赖。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ─── 配置 ─────────────────────────────────────────────────────

# 各类知识文件的最大有效期（天）
FRESHNESS_THRESHOLDS = {
    # 变化快的（新攻击手法）
    "secret-detection-patterns.yaml": 45,    # 新 API Key 格式经常变
    "supply-chain-patterns.yaml": 45,         # 新恶意包不断出现

    # 变化中等的
    "sink-patterns.yaml": 60,
    "defense-indicator-patterns.yaml": 60,
    "fast-exclusion-probes.yaml": 60,
    "config-baseline-patterns.yaml": 90,

    # 变化慢的（稳定的安全知识）
    "ghost-bits-truncation.yaml": 180,
    "session-cookie-patterns.yaml": 120,
    "password-security-patterns.yaml": 120,
    "dos-patterns.yaml": 120,
    "ssrf.yaml": 120,
    "auth-basic.yaml": 120,

    # 框架专属（跟框架版本走）
    "spring-security.yaml": 90,
    "mybatis-injection.yaml": 120,
    "actuator-exposure.yaml": 90,
    "nodejs-web.yaml": 60,
    "python-web.yaml": 60,
    "go-web.yaml": 90,

    # 默认
    "_default": 90,
}

# 知识更新搜索关键词模板（用于 WebSearch）
UPDATE_SEARCH_TEMPLATES = {
    "sink-patterns.yaml": [
        "{year} new code injection vulnerability pattern",
        "{year} new RCE vulnerability code pattern",
        "OWASP top 10 {year} new sink patterns",
    ],
    "secret-detection-patterns.yaml": [
        "new API key format {year}",
        "new cloud provider API key format {year}",
    ],
    "defense-indicator-patterns.yaml": [
        "security defense library {year}",
        "web application firewall framework {year}",
    ],
}


# ─── 工具函数 ─────────────────────────────────────────────────

def _parse_yaml_metadata(filepath):
    """从 YAML 文件的注释头中提取版本元数据"""
    metadata = {
        "version": "unknown",
        "last_updated": None,
        "update_strategy": "manual",
        "changelog": [],
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("#"):
                    break  # 遇到非注释行停止

                # 提取元数据字段
                m = re.match(r"#\s*version:\s*(.+)", line)
                if m:
                    metadata["version"] = m.group(1).strip()
                    continue

                m = re.match(r"#\s*last_updated:\s*[\"']?(\d{4}-\d{2}-\d{2})[\"']?", line)
                if m:
                    metadata["last_updated"] = m.group(1)
                    continue

                m = re.match(r"#\s*update_strategy:\s*(\w+)", line)
                if m:
                    metadata["update_strategy"] = m.group(1).strip()
                    continue

                m = re.match(r'#\s+-\s+"(.+)"', line)
                if m:
                    metadata["changelog"].append(m.group(1))

    except (IOError, UnicodeDecodeError):
        pass

    return metadata


def _calculate_freshness(last_updated_str, threshold_days):
    """计算知识文件的新鲜度"""
    if not last_updated_str:
        return {
            "status": "unknown",
            "days_since_update": None,
            "threshold_days": threshold_days,
            "message": "无 last_updated 元数据，无法判断新鲜度",
        }

    try:
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        now = datetime.now(timezone.utc)
        days_since = (now - last_updated).days

        if days_since <= threshold_days * 0.5:
            status = "fresh"
            message = f"最近更新于 {days_since} 天前，状态良好"
        elif days_since <= threshold_days:
            status = "aging"
            message = f"更新于 {days_since} 天前，接近过期阈值（{threshold_days} 天）"
        else:
            status = "stale"
            message = f"更新于 {days_since} 天前，已超过过期阈值（{threshold_days} 天），建议更新"

        return {
            "status": status,
            "days_since_update": days_since,
            "threshold_days": threshold_days,
            "message": message,
        }
    except ValueError:
        return {
            "status": "error",
            "days_since_update": None,
            "threshold_days": threshold_days,
            "message": f"last_updated 格式错误: {last_updated_str}",
        }


# ─── 命令: check-freshness ───────────────────────────────────

def cmd_check_freshness(args):
    """检查所有知识文件的新鲜度"""
    resource_dir = Path(args.resource_dir)
    results = []

    # 扫描 scan-data/ 和 knowledge/ 目录
    scan_dirs = [
        resource_dir / "scan-data",
        resource_dir / "knowledge",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue

        for yaml_file in sorted(scan_dir.glob("*.yaml")):
            if yaml_file.name == "_index.yaml":
                continue

            metadata = _parse_yaml_metadata(yaml_file)
            threshold = FRESHNESS_THRESHOLDS.get(
                yaml_file.name,
                FRESHNESS_THRESHOLDS["_default"]
            )
            freshness = _calculate_freshness(metadata["last_updated"], threshold)

            results.append({
                "file": str(yaml_file.relative_to(resource_dir)),
                "filename": yaml_file.name,
                "version": metadata["version"],
                "last_updated": metadata["last_updated"],
                "update_strategy": metadata["update_strategy"],
                "freshness": freshness,
            })

    # 统计
    stale_count = sum(1 for r in results if r["freshness"]["status"] == "stale")
    aging_count = sum(1 for r in results if r["freshness"]["status"] == "aging")
    fresh_count = sum(1 for r in results if r["freshness"]["status"] == "fresh")
    unknown_count = sum(1 for r in results if r["freshness"]["status"] == "unknown")

    output = {
        "status": "completed",
        "total_files": len(results),
        "summary": {
            "fresh": fresh_count,
            "aging": aging_count,
            "stale": stale_count,
            "unknown": unknown_count,
        },
        "stale_files": [r for r in results if r["freshness"]["status"] == "stale"],
        "aging_files": [r for r in results if r["freshness"]["status"] == "aging"],
        "all_files": results,
    }

    if stale_count > 0:
        output["recommendation"] = (
            f"发现 {stale_count} 个过期知识文件，建议执行: "
            f"python3 knowledge_updater.py suggest-updates --resource-dir {args.resource_dir}"
        )

    print(json.dumps(output, ensure_ascii=False, indent=2))


# ─── 命令: suggest-updates ───────────────────────────────────

def cmd_suggest_updates(args):
    """为过期/老化的知识文件生成候选更新建议"""
    resource_dir = Path(args.resource_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current_year = datetime.now().year

    scan_dirs = [resource_dir / "scan-data", resource_dir / "knowledge"]
    suggestions = []

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue

        for yaml_file in sorted(scan_dir.glob("*.yaml")):
            if yaml_file.name == "_index.yaml":
                continue

            metadata = _parse_yaml_metadata(yaml_file)
            threshold = FRESHNESS_THRESHOLDS.get(
                yaml_file.name, FRESHNESS_THRESHOLDS["_default"]
            )
            freshness = _calculate_freshness(metadata["last_updated"], threshold)

            if freshness["status"] not in ("stale", "aging"):
                continue

            # 生成搜索查询建议
            search_queries = []
            templates = UPDATE_SEARCH_TEMPLATES.get(yaml_file.name, [])
            for tmpl in templates:
                search_queries.append(tmpl.format(year=current_year))

            # 生成候选更新文件
            update_suggestion = {
                "target_file": str(yaml_file.relative_to(resource_dir)),
                "current_version": metadata["version"],
                "last_updated": metadata["last_updated"],
                "freshness_status": freshness["status"],
                "days_since_update": freshness["days_since_update"],
                "suggested_search_queries": search_queries,
                "update_instructions": _generate_update_instructions(yaml_file.name),
                "pending_patterns": [],  # 人工/WebSearch 填充
                "review_status": "pending",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            suggestion_file = output_dir / f"{yaml_file.stem}-update.json"
            with open(suggestion_file, "w", encoding="utf-8") as f:
                json.dump(update_suggestion, f, ensure_ascii=False, indent=2)

            suggestions.append({
                "file": yaml_file.name,
                "suggestion_file": str(suggestion_file),
                "search_queries": len(search_queries),
            })

    output = {
        "status": "completed",
        "suggestions_generated": len(suggestions),
        "output_dir": str(output_dir),
        "suggestions": suggestions,
        "next_steps": [
            "1. 检查 pending-updates/*.json 中的 suggested_search_queries",
            "2. 执行 WebSearch 或手动调研，将新发现的模式填入 pending_patterns[]",
            "3. 将 review_status 改为 'approved'",
            "4. 执行: python3 knowledge_updater.py apply-update --update-file <file> --target <target>",
        ],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def _generate_update_instructions(filename):
    """根据文件类型生成具体的更新指引"""
    instructions = {
        "sink-patterns.yaml": {
            "focus_areas": [
                "新的注入向量（如新的框架 API）",
                "新的不安全反序列化模式",
                "已知 CVE 对应的代码模式",
            ],
            "pattern_format": "每个新模式需包含: type、tech_stack、patterns[]、note",
            "validation": "新模式必须在真实代码库上测试，确认 Grep 命中率和误报率",
        },
        "secret-detection-patterns.yaml": {
            "focus_areas": [
                "现有提供商 Key 格式变更",
                "新的云服务商凭证格式",
            ],
            "pattern_format": "category + patterns[] 正则，需测试真实 Key 样本",
            "validation": "使用已知 Key 格式验证正则匹配率，确保不误报普通字符串",
        },
        "defense-indicator-patterns.yaml": {
            "focus_areas": [
                "新的安全库 API 变更",
                "新的 Web 安全防御框架",
                "新的输出净化库",
            ],
            "pattern_format": "type + tech_stack + patterns[] + note",
            "validation": "确认防御模式在目标框架的最新版本中仍然有效",
        },
    }

    return instructions.get(filename, {
        "focus_areas": ["检查该领域的最新安全公告和漏洞报告"],
        "pattern_format": "参照现有文件格式",
        "validation": "在真实代码库上测试",
    })


# ─── 命令: apply-update ──────────────────────────────────────

def cmd_apply_update(args):
    """将审核通过的候选更新合并到目标知识文件"""
    update_file = Path(args.update_file)
    target_file = Path(args.target)

    if not update_file.exists():
        print(json.dumps({"status": "error", "reason": f"更新文件不存在: {update_file}"}))
        sys.exit(1)

    if not target_file.exists():
        print(json.dumps({"status": "error", "reason": f"目标文件不存在: {target_file}"}))
        sys.exit(1)

    try:
        with open(update_file, "r", encoding="utf-8") as f:
            update_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(json.dumps({"status": "error", "reason": f"读取更新文件失败: {e}"}))
        sys.exit(1)

    # 检查审核状态
    if update_data.get("review_status") != "approved":
        print(json.dumps({
            "status": "blocked",
            "reason": f"更新文件审核状态为 '{update_data.get('review_status', 'unknown')}'，需要先审核通过（review_status: approved）",
        }))
        sys.exit(1)

    # 检查是否有待合并的模式
    pending = update_data.get("pending_patterns", [])
    if not pending:
        print(json.dumps({
            "status": "skipped",
            "reason": "pending_patterns 为空，无需合并",
        }))
        return

    # 读取目标文件
    with open(target_file, "r", encoding="utf-8") as f:
        target_content = f.read()

    # 更新版本元数据
    today = datetime.now().strftime("%Y-%m-%d")
    old_version = update_data.get("current_version", "1.0.0")
    new_version = _bump_version(old_version, "minor")

    # 更新 last_updated
    target_content = re.sub(
        r'(#\s*last_updated:\s*)["\']?\d{4}-\d{2}-\d{2}["\']?',
        f'\\g<1>"{today}"',
        target_content,
    )

    # 更新 version
    target_content = re.sub(
        r'(#\s*version:\s*)\S+',
        f'\\g<1>{new_version}',
        target_content,
    )

    # 追加 changelog
    changelog_entry = f'#   - "{new_version} ({today}): 知识更新 — {len(pending)} 个新模式"'
    # 在最后一条 changelog 后追加
    target_content = re.sub(
        r'(#\s+-\s+"[^"]+"\n)((?:#\s+-\s+"[^"]+"\n)*)',
        f'\\g<1>{changelog_entry}\n\\g<2>',
        target_content,
        count=1,
    )

    # 将 pending_patterns 追加到文件末尾（作为注释标记的待合并区域）
    append_section = "\n# ============================================================================\n"
    append_section += f"# 知识更新 {new_version} ({today}) — 以下模式由 knowledge_updater.py 合并\n"
    append_section += "# ============================================================================\n\n"

    for pattern in pending:
        # 将 JSON 格式的 pattern 转为 YAML 注释 + 内容
        if isinstance(pattern, dict):
            append_section += f"  # 新增模式: {pattern.get('description', 'N/A')}\n"
            if "yaml_content" in pattern:
                append_section += pattern["yaml_content"] + "\n\n"
            else:
                append_section += f"  # TODO: 手动将以下 JSON 转为 YAML 格式\n"
                append_section += f"  # {json.dumps(pattern, ensure_ascii=False)}\n\n"
        elif isinstance(pattern, str):
            append_section += pattern + "\n"

    target_content += append_section

    # 写回
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(target_content)

    # 标记更新文件为已合并
    update_data["review_status"] = "merged"
    update_data["merged_at"] = datetime.now(timezone.utc).isoformat()
    update_data["new_version"] = new_version
    with open(update_file, "w", encoding="utf-8") as f:
        json.dump(update_data, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "status": "completed",
        "target_file": str(target_file),
        "old_version": old_version,
        "new_version": new_version,
        "patterns_merged": len(pending),
        "message": f"成功合并 {len(pending)} 个新模式到 {target_file.name}",
    }, ensure_ascii=False))


def _bump_version(version, bump_type="minor"):
    """版本号递增"""
    try:
        parts = version.split(".")
        if len(parts) == 3:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            if bump_type == "major":
                return f"{major + 1}.0.0"
            elif bump_type == "minor":
                return f"{major}.{minor + 1}.0"
            else:
                return f"{major}.{minor}.{patch + 1}"
    except (ValueError, IndexError):
        pass
    return "1.0.0"


# ─── 命令: show-versions ─────────────────────────────────────

def cmd_show_versions(args):
    """显示所有知识文件的版本信息"""
    resource_dir = Path(args.resource_dir)
    results = []

    scan_dirs = [resource_dir / "scan-data", resource_dir / "knowledge"]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue

        for yaml_file in sorted(scan_dir.glob("*.yaml")):
            if yaml_file.name == "_index.yaml":
                continue

            metadata = _parse_yaml_metadata(yaml_file)
            file_size = yaml_file.stat().st_size

            # 统计文件行数
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
            except IOError:
                line_count = 0

            results.append({
                "file": str(yaml_file.relative_to(resource_dir)),
                "version": metadata["version"],
                "last_updated": metadata["last_updated"],
                "update_strategy": metadata["update_strategy"],
                "lines": line_count,
                "size_bytes": file_size,
                "changelog_entries": len(metadata["changelog"]),
            })

    output = {
        "status": "completed",
        "total_files": len(results),
        "files": results,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ─── CLI 入口 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="知识库更新工具 — 检测知识腐化，生成候选更新，增量合并",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查知识新鲜度
  %(prog)s check-freshness --resource-dir resource/

  # 为过期文件生成更新建议
  %(prog)s suggest-updates --resource-dir resource/ --output-dir pending-updates/

  # 合并审核通过的更新
  %(prog)s apply-update --update-file pending-updates/sink-patterns-update.json --target resource/scan-data/sink-patterns.yaml

  # 查看版本信息
  %(prog)s show-versions --resource-dir resource/
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # check-freshness
    p_fresh = subparsers.add_parser("check-freshness", help="检查知识文件新鲜度")
    p_fresh.add_argument("--resource-dir", required=True, help="资源目录路径")

    # suggest-updates
    p_suggest = subparsers.add_parser("suggest-updates", help="生成候选更新建议")
    p_suggest.add_argument("--resource-dir", required=True, help="资源目录路径")
    p_suggest.add_argument("--output-dir", default="pending-updates", help="输出目录")

    # apply-update
    p_apply = subparsers.add_parser("apply-update", help="合并审核通过的更新")
    p_apply.add_argument("--update-file", required=True, help="候选更新文件")
    p_apply.add_argument("--target", required=True, help="目标知识文件")

    # show-versions
    p_versions = subparsers.add_parser("show-versions", help="显示版本信息")
    p_versions.add_argument("--resource-dir", required=True, help="资源目录路径")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "check-freshness": cmd_check_freshness,
        "suggest-updates": cmd_suggest_updates,
        "apply-update": cmd_apply_update,
        "show-versions": cmd_show_versions,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
