#!/usr/bin/env python3
"""
novel_writer 技能核心逻辑 (v3.0 - 优化版)
功能：辅助用户创作长篇小说，支持真实 LLM API 调用、记忆管理、大纲控制
优化点：
- Prompt 模块化
- 配置验证 (pydantic)
- 改进的中文摘要算法
- 批量生成、重写、导入导出
- 完整的类型注解
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 配置路径
WORK_DIR = Path(os.environ.get("WORKDIR", Path(__file__).parent.parent / "working"))
NOVELS_DIR = WORK_DIR / "novels"
SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "config.json"

NOVELS_DIR.mkdir(parents=True, exist_ok=True)

# 导入自定义模块
from prompts import (
    build_system_prompt,
    build_user_prompt,
    build_continue_prompt,
    build_regenerate_prompt
)
from config_models import NovelWriterConfig
from text_processor import ChineseTextProcessor, count_words, quick_summary, extract_last_hook

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(WORK_DIR / "novel_writer.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# OpenAI 客户端
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai library not installed. Run: pip install openai")


class NovelWriter:
    """小说创作助手"""

    def __init__(self, novel_title: str = "未命名小说", config_path: Optional[Path] = None):
        self.novel_title = novel_title
        self.config_path = config_path or CONFIG_FILE
        self.config = self._load_config()
        self.project_dir = NOVELS_DIR / novel_title
        self.context = self._load_context()
        self._init_project_dir()
        self._init_client()

    def _load_config(self) -> NovelWriterConfig:
        """加载配置"""
        try:
            return NovelWriterConfig.from_env()
        except Exception as e:
            logger.warning(f"Config validation failed, using defaults: {e}")
            return NovelWriterConfig()

    def _init_client(self):
        """初始化 LLM 客户端"""
        if OPENAI_AVAILABLE and self.config.validate_api_key():
            self.client = OpenAI(
                base_url=self.config.api.base_url,
                api_key=self.config.api.api_key
            )
            logger.info(f"LLM client initialized with model: {self.config.api.model}")
        else:
            self.client = None
            if not self.config.validate_api_key():
                logger.error("NOVEL_API_KEY not set. Please configure your API key.")

    def _load_context(self) -> dict:
        """加载记忆上下文"""
        context_file = self.project_dir / "meta" / "context.json"
        if context_file.exists():
            with open(context_file, 'r', encoding='utf-8') as f:
                ctx = json.load(f)
                logger.info(f"Loaded context for: {self.novel_title}")
                return ctx

        return {
            "novel_title": self.novel_title,
            "characters": {},
            "world": "",
            "outline": [],
            "chapters": [],
            "style": self.config.project.default_style,
            "word_count_total": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _save_context(self):
        """保存记忆上下文"""
        context_file = self.project_dir / "meta" / "context.json"
        context_file.parent.mkdir(parents=True, exist_ok=True)
        self.context["updated_at"] = datetime.now().isoformat()
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)
        logger.debug(f"Context saved for: {self.novel_title}")

    def _init_project_dir(self):
        """初始化项目目录"""
        dirs = ["characters", "world", "outline", "chapters", "meta"]
        for d in dirs:
            (self.project_dir / d).mkdir(parents=True, exist_ok=True)

        config_file = self.project_dir / "config.json"
        if not config_file.exists():
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "title": self.novel_title,
                    "style": self.context["style"],
                    "created_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

    # ========== 基础操作 ==========

    def set_character(self, name: str, profile: str) -> str:
        """设定人物"""
        self.context["characters"][name] = profile
        self._save_context()

        char_file = self.project_dir / "characters" / f"{name}.md"
        with open(char_file, 'w', encoding='utf-8') as f:
            f.write(f"# {name}\n\n{profile}\n\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

        logger.info(f"Character set: {name}")
        return f"Character '{name}' saved."

    def set_world(self, setting: str) -> str:
        """设定世界观"""
        self.context["world"] = setting
        self._save_context()

        world_file = self.project_dir / "world" / "main.md"
        with open(world_file, 'w', encoding='utf-8') as f:
            f.write(f"# World Setting\n\n{setting}\n\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

        logger.info("World setting updated")
        return "World setting saved."

    def set_style(self, style: str) -> str:
        """设定写作风格"""
        self.context["style"] = style
        self._save_context()
        logger.info(f"Style set to: {style}")
        return f"Style set to: {style}"

    # ========== 大纲操作 ==========

    def add_outline(self, chapter_num: int, title: str, summary: str, hooks: str = "") -> str:
        """添加大纲"""
        node = {
            "chapter": chapter_num,
            "title": title,
            "summary": summary,
            "status": "planned",
            "word_count": 0,
            "hooks": hooks.split(",") if hooks else []
        }

        # 更新或添加
        found = False
        for i, item in enumerate(self.context["outline"]):
            if item["chapter"] == chapter_num:
                self.context["outline"][i] = node
                found = True
                break

        if not found:
            self.context["outline"].append(node)

        self.context["outline"].sort(key=lambda x: x["chapter"])
        self._save_context()

        # 保存为 Markdown
        outline_file = self.project_dir / "outline" / f"ch{chapter_num:03d}_{title.replace(' ', '_')}.md"
        with open(outline_file, 'w', encoding='utf-8') as f:
            f.write(f"# Chapter {chapter_num}: {title}\n\n**Summary**: {summary}\n\n**Status**: Planned\n")

        logger.info(f"Outline added: Chapter {chapter_num} - {title}")
        return f"Chapter {chapter_num} outline updated: {title}"

    def import_outline(self, file_path: str) -> str:
        """从 JSON 文件导入大纲"""
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            outlines = data
        elif isinstance(data, dict) and "outline" in data:
            outlines = data["outline"]
        else:
            return "Error: Invalid outline format"

        count = 0
        for item in outlines:
            if "chapter" in item and "title" in item:
                self.add_outline(
                    item["chapter"],
                    item["title"],
                    item.get("summary", ""),
                    item.get("hooks", "")
                )
                count += 1

        logger.info(f"Imported {count} outline items")
        return f"Imported {count} outline items."

    def export_outline(self, file_path: str) -> str:
        """导出大纲到 JSON"""
        outline_data = {
            "novel_title": self.novel_title,
            "style": self.context["style"],
            "outline": self.context["outline"]
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(outline_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported outline to: {file_path}")
        return f"Outline exported to: {file_path}"

    # ========== 章节生成 ==========

    def generate_chapter(self, chapter_num: int, target_words: int = 2300) -> str:
        """生成章节"""
        if not self.client:
            return "Error: LLM client not initialized. Please set NOVEL_API_KEY."

        logger.info(f"Generating chapter {chapter_num} for '{self.novel_title}'")

        # 获取上下文
        prev_summary = ""
        last_hook = ""
        if chapter_num > 1 and self.context["chapters"]:
            # 获取上一章
            prev_ch = next((c for c in self.context["chapters"] if c["chapter"] == chapter_num - 1), None)
            if prev_ch:
                prev_summary = prev_ch.get("summary", "")
                last_hook = prev_ch.get("last_hook", "")

        # 获取大纲
        current_outline = next((o for o in self.context["outline"] if o["chapter"] == chapter_num), None)
        outline_text = current_outline["summary"] if current_outline else "无大纲"
        chapter_title = current_outline["title"] if current_outline else f"第 {chapter_num} 章"

        # 构建 Prompt
        system_prompt = build_system_prompt(
            novel_title=self.novel_title,
            chapter_num=chapter_num,
            style=self.context["style"],
            characters=self.context["characters"],
            world=self.context["world"],
            prev_summary=prev_summary,
            outline=outline_text,
            chapter_title=chapter_title
        )

        user_prompt = build_user_prompt(
            novel_title=self.novel_title,
            chapter_num=chapter_num,
            chapter_title=chapter_title
        )

        try:
            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.config.api.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.api.temperature,
                max_tokens=self.config.api.max_tokens
            )

            content = response.choices[0].message.content.strip()

            # 文本处理
            word_count = count_words(content)
            summary = quick_summary(content, max_length=200)
            last_hook = extract_last_hook(content) or ""

            # 字数检查
            min_words = self.config.project.min_word_count
            max_words = self.config.project.max_word_count

            if word_count < min_words:
                logger.warning(f"Chapter {chapter_num} word count ({word_count}) below minimum ({min_words})")
            elif word_count > max_words:
                logger.warning(f"Chapter {chapter_num} word count ({word_count}) exceeds maximum ({max_words})")

            # 保存章节
            chapter_file = self.project_dir / "chapters" / f"ch{chapter_num:03d}_{chapter_title.replace(' ', '_')}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"# {chapter_title}\n\n{content}")

            # 更新上下文
            chapter_data = {
                "chapter": chapter_num,
                "title": chapter_title,
                "content": content,
                "summary": summary,
                "word_count": word_count,
                "last_hook": last_hook,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }

            # 避免重复添加
            existing_idx = None
            for i, c in enumerate(self.context["chapters"]):
                if c["chapter"] == chapter_num:
                    existing_idx = i
                    break

            if existing_idx is not None:
                self.context["chapters"][existing_idx] = chapter_data
            else:
                self.context["chapters"].append(chapter_data)

            # 更新大纲状态
            if current_outline:
                current_outline["status"] = "done"
                current_outline["word_count"] = word_count

            # 更新总字数
            self.context["word_count_total"] = sum(
                c.get("word_count", 0) for c in self.context["chapters"]
            )

            self._save_context()

            logger.info(f"Chapter {chapter_num} generated: {word_count} words")
            return f"Chapter {chapter_num} saved.\nWords: {word_count}\nSummary: {summary[:100]}..."

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error: {str(e)}"

    def regenerate_chapter(self, chapter_num: int, problems: str = "") -> str:
        """重新生成章节"""
        if not self.client:
            return "Error: LLM client not initialized."

        # 获取大纲
        current_outline = next((o for o in self.context["outline"] if o["chapter"] == chapter_num), None)
        if not current_outline:
            return f"Error: Chapter {chapter_num} outline not found."

        outline_text = current_outline["summary"]
        chapter_title = current_outline["title"]

        # 获取已有内容的问题描述
        existing = next((c for c in self.context["chapters"] if c["chapter"] == chapter_num), None)
        if existing and not problems:
            problems = "情节平淡、爽点不足、描写不够细腻"

        system_prompt = build_regenerate_prompt(
            novel_title=self.novel_title,
            chapter_num=chapter_num,
            outline=outline_text,
            problems=problems
        )

        user_prompt = f"请重新创作第 {chapter_num} 章，标题：{chapter_title}"

        try:
            response = self.client.chat.completions.create(
                model=self.config.api.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.api.temperature + 0.1,  # 稍微提高创造性
                max_tokens=self.config.api.max_tokens
            )

            content = response.choices[0].message.content.strip()
            word_count = count_words(content)

            # 保存（覆盖旧版本）
            chapter_file = self.project_dir / "chapters" / f"ch{chapter_num:03d}_{chapter_title.replace(' ', '_')}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"# {chapter_title}\n\n{content}")

            # 更新上下文
            summary = quick_summary(content)
            chapter_data = {
                "chapter": chapter_num,
                "title": chapter_title,
                "content": content,
                "summary": summary,
                "word_count": word_count,
                "last_hook": extract_last_hook(content) or "",
                "timestamp": datetime.now().isoformat(),
                "status": "regenerated"
            }

            for i, c in enumerate(self.context["chapters"]):
                if c["chapter"] == chapter_num:
                    self.context["chapters"][i] = chapter_data
                    break

            self._save_context()

            logger.info(f"Chapter {chapter_num} regenerated: {word_count} words")
            return f"Chapter {chapter_num} regenerated.\nWords: {word_count}"

        except Exception as e:
            return f"Error: {str(e)}"

    def generate_batch(self, start_chapter: int, end_chapter: int, target_words: int = 2300) -> str:
        """批量生成章节"""
        results = []
        for ch in range(start_chapter, end_chapter + 1):
            print(f"Generating chapter {ch}...")
            result = self.generate_chapter(ch, target_words)
            results.append(f"Ch {ch}: {result}")

        return "\n".join(results)

    # ========== 统计和状态 ==========

    def get_status(self) -> str:
        """获取创作进度"""
        lines = [
            f"Novel: {self.novel_title}",
            f"Style: {self.context['style']}",
            f"Characters: {len(self.context['characters'])}",
            f"Outline: {len(self.context['outline'])} chapters",
            f"Written: {len(self.context['chapters'])} chapters",
            f"Total words: {self.context.get('word_count_total', 0):,}",
            "",
            "Outline preview:"
        ]

        for item in self.context["outline"][:5]:
            status_icon = "[OK]" if item["status"] == "done" else "[..]" if item["status"] == "writing" else "[--]"
            wc = f" ({item.get('word_count', 0)} words)" if item.get('word_count') else ""
            lines.append(f"  {status_icon} Ch{item['chapter']}: {item['title']}{wc}")

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """获取详细统计"""
        chapters = self.context["chapters"]
        if not chapters:
            return {"error": "No chapters written yet"}

        word_counts = [c.get("word_count", 0) for c in chapters]

        return {
            "novel_title": self.novel_title,
            "total_chapters": len(chapters),
            "total_words": sum(word_counts),
            "avg_words": sum(word_counts) // len(word_counts) if word_counts else 0,
            "min_words": min(word_counts) if word_counts else 0,
            "max_words": max(word_counts) if word_counts else 0,
            "word_count_per_chapter": {c["chapter"]: c.get("word_count", 0) for c in chapters}
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Novel Writer v3.0")
    parser.add_argument("--new", metavar="TITLE", help="Create new novel")
    parser.add_argument("--novel-title", metavar="TITLE", default="未命名小说", help="Novel title")
    parser.add_argument("--set-character", nargs=2, metavar=("NAME", "PROFILE"), help="Set character")
    parser.add_argument("--set-world", metavar="SETTING", help="Set world")
    parser.add_argument("--set-style", metavar="STYLE", help="Set style")
    parser.add_argument("--add-outline", nargs=3, metavar=("NUM", "TITLE", "SUMMARY"), help="Add outline")
    parser.add_argument("--import-outline", metavar="FILE", help="Import outline from JSON")
    parser.add_argument("--export-outline", metavar="FILE", help="Export outline to JSON")
    parser.add_argument("--generate", nargs=2, type=int, metavar=("NUM", "WORDS"), help="Generate chapter")
    parser.add_argument("--generate-batch", nargs=3, type=int, metavar=("START", "END", "WORDS"), help="Batch generate")
    parser.add_argument("--regenerate", type=int, metavar="NUM", help="Regenerate chapter")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--stats", action="store_true", help="Show detailed stats")

    args = parser.parse_args()

    # 处理 --new
    if args.new:
        novel = NovelWriter(args.new)
        print(f"Novel project '{args.new}' created")
        return

    novel = NovelWriter(args.novel_title)

    if args.set_character:
        name, profile = args.set_character
        print(novel.set_character(name, profile))
    elif args.set_world:
        print(novel.set_world(args.set_world))
    elif args.set_style:
        print(novel.set_style(args.set_style))
    elif args.add_outline:
        num, title, summary = args.add_outline
        print(novel.add_outline(int(num), title, summary))
    elif args.import_outline:
        print(novel.import_outline(args.import_outline))
    elif args.export_outline:
        print(novel.export_outline(args.export_outline))
    elif args.generate:
        num, words = args.generate
        print(novel.generate_chapter(num, words))
    elif args.generate_batch:
        start, end, words = args.generate_batch
        print(novel.generate_batch(start, end, words))
    elif args.regenerate:
        print(novel.regenerate_chapter(args.regenerate))
    elif args.status:
        print(novel.get_status())
    elif args.stats:
        import json
        print(json.dumps(novel.get_stats(), indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()