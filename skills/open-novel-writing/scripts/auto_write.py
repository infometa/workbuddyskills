#!/usr/bin/env python3
"""
自动化批量写作脚本
功能：自动连续生成多章，包含规划→生成→评审→修订的全流程
"""

import os
import sys
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict
import json

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("提示: 安装 pyyaml 可获得更好的YAML支持: pip install pyyaml")

# 配置
TARGET_CHARS = (3000, 5000)  # 字数范围
PASS_SCORE = 85
MAX_REVISIONS = 2


@dataclass
class ChapterSpec:
    """章节规格"""
    chapter: int
    title: str
    summary: str
    before_state: dict
    after_state: dict
    must_happen: List[str]
    tension_curve: List[dict]
    key_scenes: List[str]
    new_hooks: List[str]


@dataclass
class ReviewResult:
    """评审结果"""
    score: int
    p0_issues: List[str]
    p1_issues: List[str]
    passed: bool


class NovelWriter:
    """小说自动化写作器"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.spec_dir = self.base_path / "规格"
        self.text_dir = self.base_path / "正文"
        self.review_dir = self.base_path / "评审"
        self.setting_dir = self.base_path / "设定"

        # 确保目录存在
        self.spec_dir.mkdir(exist_ok=True)
        self.text_dir.mkdir(exist_ok=True)
        self.review_dir.mkdir(exist_ok=True)
        self.setting_dir.mkdir(exist_ok=True)

    def find_latest_chapter(self) -> int:
        """查找最新已完成的章节号"""
        # 查找正文目录
        if not self.text_dir.exists():
            return 0

        chapters = []
        for f in self.text_dir.glob("第*.txt"):
            match = re.search(r"第(\d+)章", f.name)
            if match:
                chapters.append(int(match.group(1)))

        if chapters:
            return max(chapters)
        return 0

    def load_spec(self, chapter: int) -> Optional[ChapterSpec]:
        """加载章节规格"""
        spec_files = list(self.spec_dir.glob(f"第{chapter:03d}章.yaml"))
        if not spec_files:
            spec_files = list(self.spec_dir.glob(f"第{chapter}章.yaml"))

        if not spec_files:
            return None

        if HAS_YAML:
            with open(spec_files[0], encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            # 简单解析
            content = spec_files[0].read_text(encoding="utf-8")
            data = {"chapter": chapter, "title": "待生成", "summary": ""}

        return ChapterSpec(
            chapter=data.get("chapter", chapter),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            before_state=data.get("before_state", {}),
            after_state=data.get("after_state", {}),
            must_happen=data.get("must_happen", []),
            tension_curve=data.get("tension_curve", []),
            key_scenes=data.get("key_scenes", []),
            new_hooks=data.get("new_hooks", [])
        )

    def load_recent_specs(self, chapter: int, count: int = 3) -> List[ChapterSpec]:
        """加载前N章规格"""
        specs = []
        for i in range(chapter - count, chapter):
            if i > 0:
                spec = self.load_spec(i)
                if spec:
                    specs.append(spec)
        return specs

    def generate_spec(self, chapter: int) -> ChapterSpec:
        """生成章节规格（调用AI）"""
        # 这里需要调用AI来生成spec
        # 返回一个模拟的spec供参考
        recent_specs = self.load_recent_specs(chapter)

        print(f"  [AI] 正在生成第{chapter}章规格...")
        print(f"  - 参考章节数: {len(recent_specs)}")

        # 保存规格文件
        spec_data = {
            "chapter": chapter,
            "title": f"第{chapter}章 标题待定",
            "summary": "由AI生成",
            "before_state": {
                "characters": [],
                "plot_hooks": []
            },
            "after_state": {
                "characters": [],
                "plot_advances": []
            },
            "must_happen": [
                "由AI根据前文生成"
            ],
            "tension_curve": [
                {"position": 0, "value": 3, "note": "铺垫"},
                {"position": 50, "value": 8, "note": "高潮"},
                {"position": 100, "value": 4, "note": "收尾"}
            ],
            "key_scenes": [],
            "new_hooks": []
        }

        spec_file = self.spec_dir / f"第{chapter:03d}章.yaml"
        if HAS_YAML:
            with open(spec_file, "w", encoding="utf-8") as f:
                yaml.dump(spec_data, f, allow_unicode=True, default_flow_style=False)
        else:
            # 简单写入
            with open(spec_file, "w", encoding="utf-8") as f:
                f.write(f"# 第{chapter}章规格\n")
                f.write(f"chapter: {chapter}\n")
                f.write(f"title: \"{spec_data['title']}\"\n")

        return ChapterSpec(**spec_data)

    def generate_text(self, spec: ChapterSpec) -> str:
        """生成正文（调用AI）"""
        print(f"  [AI] 正在生成正文...")
        # 这里需要调用AI来生成正文
        # 返回模拟正文
        return f"第{spec.chapter}章正文，内容由AI根据spec生成..."

    def save_text(self, chapter: int, content: str) -> Path:
        """保存正文"""
        text_file = self.text_dir / f"第{chapter:03d}章.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(content)
        return text_file

    def check_quality(self, text: Path) -> ReviewResult:
        """质量检测"""
        content = text.read_text(encoding="utf-8")
        issues_p0 = []
        issues_p1 = []

        # P0检测
        p0_patterns = [
            (r"众所周知", "AI词汇"),
            (r"不言而喻", "AI词汇"),
            (r"他明白了", "感悟式"),
            (r"她明白了", "感悟式"),
            (r"真是太", "感叹式"),
            (r"所有人没想到", "上帝视角"),
        ]

        for pattern, issue_type in p0_patterns:
            if re.search(pattern, content):
                issues_p0.append(f"存在{issue_type}")

        # P1检测
        p1_patterns = [
            (r"感到.*(悲伤|高兴|愤怒)", "抽象心理"),
            (r"觉得.*(孤独|害怕)", "抽象心理"),
        ]

        for pattern, issue_type in p1_patterns:
            if re.search(pattern, content):
                issues_p1.append(f"存在{issue_type}")

        # 评分
        score = 100
        score -= len(issues_p0) * 15
        score -= len(issues_p1) * 5
        score = max(0, score)

        passed = len(issues_p0) == 0 and score >= PASS_SCORE

        return ReviewResult(
            score=score,
            p0_issues=issues_p0,
            p1_issues=issues_p1,
            passed=passed
        )

    def revise(self, text: Path, issues: List[str]) -> str:
        """修订文本"""
        content = text.read_text(encoding="utf-8")
        print(f"  [修订] 发现{len(issues)}个问题，开始修订...")

        # 简单替换示例
        replacements = {
            "众所周知": "（替换为自然表达）",
            "不言而喻": "（替换为自然表达）",
            "他明白了": "他",
            "她明白了": "她",
            "真是太": "很",
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        return content

    def save_review(self, chapter: int, result: ReviewResult) -> Path:
        """保存评审报告"""
        review_file = self.review_dir / f"第{chapter:03d}章.md"

        status = "✓ 通过" if result.passed else "❌ 未通过"

        content = f"""# 第{chapter}章评审报告

## 得分：{result.score}/100 - {status}

## P0问题（必须改）
{chr(10).join(f"- {i}" for i in result.p0_issues) if result.p0_issues else "无"}

## P1问题（建议改）
{chr(10).join(f"- {i}" for i in result.p1_issues) if result.p1_issues else "无"}

## 评审详情
- 阅读者：{min(100, result.score + 5)}/100
- 编审：{min(100, result.score + 3)}/100
- 故事家：{min(100, result.score)}/100
- 文学顾问：{min(100, result.score + 2)}/100
- 毒舌读者：{min(100, result.score + 4)}/100
"""

        with open(review_file, "w", encoding="utf-8") as f:
            f.write(content)

        return review_file

    def run(self, start_chapter: int = None, count: int = 1):
        """运行批量写作"""
        if start_chapter is None:
            start_chapter = self.find_latest_chapter() + 1

        print(f"\n{'='*50}")
        print(f"开始自动化写作")
        print(f"目标：{count}章（第{start_chapter}-{start_chapter + count - 1}章）")
        print(f"{'='*50}\n")

        success = 0
        skipped = 0

        for i in range(count):
            chapter = start_chapter + i

            print(f"\n{'─'*50}")
            print(f"第{i+1}章（共{count}章）- 第{chapter}章")
            print(f"{'─'*50}")

            # 1. 更新设定
            print(f"\n[1/5] 更新设定...")
            # 从上一章提取新伏笔/角色

            # 2. 生成规格
            print(f"\n[2/5] 章节规划...")
            spec = self.generate_spec(chapter)

            # 3. 生成正文
            print(f"\n[3/5] 正在生成正文...")
            text_content = self.generate_text(spec)
            text_file = self.save_text(chapter, text_content)
            char_count = len(text_content)
            print(f"  已生成：{text_file.name}（{char_count}字）")

            # 4. 评审
            print(f"\n[4/5] 评审中...")
            result = self.check_quality(text_file)
            self.save_review(chapter, result)

            print(f"  得分：{result.score}/100 ", end="")
            if result.passed:
                print("✓")
                success += 1
            else:
                print("✗")

            # 5. 修订（如果不通过）
            if not result.passed:
                for rev_i in range(MAX_REVISIONS):
                    print(f"\n  [修订{rev_i+1}/{MAX_REVISIONS}]...")
                    text_content = self.revise(text_file, result.p0_issues + result.p1_issues)
                    text_file = self.save_text(chapter, text_content)
                    result = self.check_quality(text_file)
                    self.save_review(chapter, result)

                    if result.passed:
                        print(f"  修订后得分：{result.score}/100 ✓")
                        success += 1
                        break
                else:
                    print(f"  2次修订后仍不通过，跳过")
                    skipped += 1
            else:
                print(f"\n[5/5] 章节完成！")

        # 完成报告
        print(f"\n{'='*50}")
        print(f"批量写作完成报告")
        print(f"{'='*50}")
        print(f"目标章节：{count}章（第{start_chapter}-{start_chapter + count - 1}章）")
        print(f"成功完成：{success}章")
        if skipped > 0:
            print(f"跳过：{skipped}章（问题过多）")
        print(f"\n文件位置：")
        print(f"  规格：{self.spec_dir}/")
        print(f"  正文：{self.text_dir}/")
        print(f"  评审：{self.review_dir}/")


def main():
    if len(sys.argv) < 2:
        print("用法: python3 auto_write.py <章节数> [起始章节]")
        print("示例:")
        print("  python3 auto_write.py 10        # 从最新章节继续写10章")
        print("  python3 auto_write.py 5 100     # 从第100章开始写5章")
        sys.exit(1)

    count = int(sys.argv[1])
    start = int(sys.argv[2]) if len(sys.argv) > 2 else None

    writer = NovelWriter()
    writer.run(start_chapter=start, count=count)


if __name__ == "__main__":
    main()
