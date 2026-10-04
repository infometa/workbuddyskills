#!/usr/bin/env python3
"""Single writer for the project status and exactly one recommended next step."""
from __future__ import annotations

import argparse
from pathlib import Path

from common import assert_project_root, iso_now, read_csv, safe_project_path, write_text_atomic
from source_registry import read_registry


def collect_state(root: Path) -> dict:
    sources = read_csv(safe_project_path(root, "02_素材账/source-ledger.csv"))
    people = read_csv(safe_project_path(root, "03_人物与关系/person-ledger.csv"))
    media = read_csv(safe_project_path(root, "05_媒体索引/media-index.csv"))
    questions = read_csv(safe_project_path(root, "07_问题与回答/question-ledger.csv"))
    chapters = read_csv(safe_project_path(root, "10_大纲与章节/chapter-ledger.csv"))
    consents = read_csv(safe_project_path(root, "11_隐私与授权/consent-ledger.csv"))
    quality = read_csv(safe_project_path(root, "02_素材账/质量问题.csv"))
    story_dir = safe_project_path(root, "08_故事卡")
    checkpoint_dir = safe_project_path(root, "12_版本与检查点")
    stories = list(story_dir.glob("STY-*.md")) if story_dir.exists() else []
    checkpoints = list(checkpoint_dir.glob("CPK-*.json")) if checkpoint_dir.exists() else []
    visible_sources = [row for row in sources if row.get("status") != "missing"]
    changed_sources = [row for row in visible_sources if row.get("status") == "modified" or row.get("needs_reanalysis") == "yes"]
    pending_people = [row for row in people if row.get("status") != "confirmed"]
    pending_media = [row for row in media if row.get("coverage_status") not in {"complete", "not_applicable"}]
    pending_consents = [row for row in consents if row.get("status") in {"pending", "disputed", "withdrawn"}]
    pending_quality = [row for row in quality if row.get("status") not in {"resolved", "ignored"}]
    roots = read_registry(root).get("roots", [])
    if not roots:
        next_step = "登记一个已授权的生活资料目录。"
    elif not sources:
        next_step = "对一个在线来源执行完整扫描、差异复核和提交。"
    elif changed_sources:
        next_step = "复核新增或变化资料，并只重分析标记变化的来源。"
    elif not people:
        next_step = "基于来源锚点确认一位人物候选。"
    elif not stories:
        next_step = "基于已确认来源生成一张真实故事卡。"
    elif pending_consents:
        next_step = "处理最严格的一项权限待确认或撤回状态。"
    elif pending_media:
        next_step = "继续一个尚未完成的媒体批次并写入时间码覆盖状态。"
    elif not questions:
        next_step = "根据已确认资料空白生成一组资料驱动追问。"
    elif not chapters:
        next_step = "把已确认故事卡编入一个可编辑章节草稿。"
    else:
        next_step = "冻结一个交付选择并运行对应的权限门。"
    return {
        "roots": roots,
        "sources": sources,
        "visible_sources": visible_sources,
        "changed_sources": changed_sources,
        "people": people,
        "pending_people": pending_people,
        "stories": stories,
        "media": media,
        "pending_media": pending_media,
        "questions": questions,
        "chapters": chapters,
        "consents": consents,
        "pending_consents": pending_consents,
        "pending_quality": pending_quality,
        "checkpoints": checkpoints,
        "next_step": next_step,
    }


def update_project_status(root: Path, status: str | None = None, note: str = "") -> dict:
    state = collect_state(root)
    current = status or ("待处理变化资料" if state["changed_sources"] else "进行中")
    lines = [
        "# 当前状态",
        "",
        f"状态：{current}",
        f"更新时间：{iso_now()}",
        f"来源根：{len(state['roots'])}",
        f"已盘点资料：{len(state['visible_sources'])}",
        f"新增或变化资料：{len(state['changed_sources'])}",
        f"人物待确认：{len(state['pending_people'])}",
        f"故事卡：{len(state['stories'])}",
        f"媒体待处理：{len(state['pending_media'])}",
        f"权限待确认：{len(state['pending_consents'])}",
        f"当前章节：{len(state['chapters'])}",
        f"质量问题：{len(state['pending_quality'])}",
        f"检查点：{len(state['checkpoints'])}",
        f"备注：{note}",
        "",
    ]
    write_text_atomic(safe_project_path(root, "00_项目看板/当前状态.md"), "\n".join(lines), project_root=root)
    write_text_atomic(
        safe_project_path(root, "00_项目看板/下一步.md"),
        f"# 下一步\n\n推荐动作：{state['next_step']}\n",
        project_root=root,
    )
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir")
    parser.add_argument("--status", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    root = assert_project_root(args.project_dir)
    update_project_status(root, args.status or None, args.note)
    print(f"project status updated: {root}")


if __name__ == "__main__":
    main()
