#!/usr/bin/env python3

import json
import re
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).parents[1]
EXPERT_ROOT = SKILL_ROOT.parents[1]


class WorkflowContractTests(unittest.TestCase):
    def test_manifest_references_exist(self):
        manifest = (SKILL_ROOT / "manifest.yaml").read_text(encoding="utf-8")
        paths = set(re.findall(r"references/[A-Za-z0-9._/-]+\.md", manifest))
        self.assertGreaterEqual(len(paths), 12)
        missing = [path for path in paths if not (SKILL_ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_foundation_templates_exist(self):
        required = {
            "00-scope.md",
            "01-research-canon.md",
            "02-evidence-table.md",
            "03-argument-map.md",
            "04-section-contracts.md",
            "05-terminology-ledger.md",
            "revision-brief.md",
            "journal-fit-matrix.md",
            "reviewer-response-tracker.md",
            "research-execution-card.md",
        }
        actual = {path.name for path in (SKILL_ROOT / "templates").glob("*.md")}
        self.assertTrue(required.issubset(actual))

    def test_required_capability_contracts_are_present(self):
        checks = {
            "references/manuscript-types-and-section-contracts.md": ["章节通用契约", "一句话主论点", "段落任务"],
            "references/academic-language-and-polishing.md": ["章节任务", "局部修订", "中译英"],
            "references/journal-selection-and-submission.md": ["官方", "核验日期", "不预测录用"],
            "references/reviewer-response.md": ["VERIFIED_DONE", "REPORTED_DONE_UNVERIFIED", "ready_to_submit"],
            "references/statistics-results-and-figures.md": ["独立分析单位", "多重比较", "AUTHOR_INPUT_NEEDED"],
        }
        for relative, terms in checks.items():
            content = (SKILL_ROOT / relative).read_text(encoding="utf-8")
            for term in terms:
                self.assertIn(term, content, f"{relative} missing {term}")

    def test_v14_routes_and_reference_checker_exist(self):
        required_references = {
            "references/proposal-writing.md",
            "references/search-query-templates.md",
            "references/similarity-report-review.md",
            "references/feedback-implementation.md",
        }
        for relative in required_references:
            self.assertTrue((SKILL_ROOT / relative).is_file(), relative)

        script = SKILL_ROOT / "scripts" / "ref_check.py"
        self.assertTrue(script.is_file())
        content = script.read_text(encoding="utf-8")
        for term in ("field_completeness", "punctuation_report", "duplicate_report", "utf-8-sig"):
            self.assertIn(term, content)

        manifest = (SKILL_ROOT / "manifest.yaml").read_text(encoding="utf-8")
        route_checks = {
            "proposal": "references/proposal-writing.md",
            "search-query": "references/search-query-templates.md",
            "similarity-review": "references/similarity-report-review.md",
            "feedback-implementation": "references/feedback-implementation.md",
        }
        for route, path in route_checks.items():
            self.assertRegex(manifest, rf"{re.escape(route)}:\s+{re.escape(path)}")

    def test_default_modes_are_explicit(self):
        content = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for term in (
            "局部任务默认快速成稿",
            "整章或全文默认深度审阅、先诊断后修改",
            "交付物任务默认分步指导",
            "开题报告",
            "答辩 PPT",
        ):
            self.assertIn(term, content)

    def test_all_23_capability_contracts_are_present(self):
        checks = [
            ("01 分库检索式", "references/search-query-templates.md", ("SU=", "PubMed", "Scopus")),
            ("02 回填材料批量解析", "references/literature-and-evidence.md", ("RIS、ENW/EndNote Tagged", "TY", "单批最多处理 50 条")),
            ("03 GB/T 7714 著录核对", "references/citation-and-formatting.md", ("GB/T 7714—2015", "期刊文章", "专利")),
            ("04 学校模板核对", "references/citation-and-formatting.md", ("学校模板核对工作流", "Word 操作路径")),
            ("05 开题报告写作", "references/proposal-writing.md", ("开题报告说明", "不承诺研究结论")),
            ("06 研究进度安排", "references/proposal-writing.md", ("进度表", "学校硬节点")),
            ("07 description 双句", "SKILL.md", ("论文写作", "Use when", "citation")),
            ("08 默认模式", "SKILL.md", ("局部任务默认快速成稿", "整章或全文默认深度审阅", "默认分步指导")),
            ("09 文献精读卡", "references/output-templates.md", ("文献精读卡", "结论边界", "原文定位")),
            ("10 高频格式错误", "references/citation-and-formatting.md", ("本科论文高频格式错误对照", "Word")),
            ("11 图表呈现自查", "references/methods-results-and-figures.md", ("图表呈现自查", "图题置于图下", "跨页表")),
            ("12 创新点提炼", "references/topic-and-research-question.md", ("创新点提炼", "对照依据")),
            ("13 技术路线", "references/proposal-writing.md", ("主线", "分支", "反馈环", "绘图软件")),
            ("14 开题输出模板", "references/output-templates.md", ("开题报告逐节模板", "学校开题表字段对接")),
            ("15 检索审计记录", "references/output-templates.md", ("检索审计记录", "命中数", "排除理由")),
            ("16 格式逐项操作卡", "references/output-templates.md", ("格式逐项操作卡", "Word 操作路径")),
            ("17 引用字段校验脚本", "scripts/ref_check.py", ("字段", "标点", "重复条目")),
            ("18 查重报告工作流", "references/similarity-report-review.md", ("正当的固定表达", "不当大段搬运", "不预测或保证复检重复率")),
            ("19 意见落实工作流", "references/feedback-implementation.md", ("落实表", "修改位置", "回复要点")),
            ("20 问卷访谈", "references/methods-results-and-figures.md", ("问卷设计规范", "半结构化访谈提纲", "避免诱导式问题")),
            ("21 AIGC 合规", "references/academic-integrity-and-source-policy.md", ("AIGC 合规披露", "AIGC 检测报告解读", "过程留痕")),
            ("22 文献管理工具", "references/literature-and-evidence.md", ("Zotero", "NoteExpress", "EndNote", "Word 插件基本路径")),
            ("23 LaTeX 降级", "references/citation-and-formatting.md", ("LaTeX 场景边界", "转交")),
        ]
        self.assertEqual(len(checks), 23)
        for label, relative, terms in checks:
            root = EXPERT_ROOT if relative == "README.md" else SKILL_ROOT
            content = (root / relative).read_text(encoding="utf-8")
            for term in terms:
                self.assertIn(term, content, f"{label}: {relative} missing {term}")

    def test_plugin_and_skill_identity(self):
        plugin = json.loads((EXPERT_ROOT / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["version"], "1.4.0")
        manifest = (SKILL_ROOT / "manifest.yaml").read_text(encoding="utf-8")
        self.assertRegex(manifest, r"(?m)^version:\s+1\.4\.0$")
        self.assertEqual(plugin["name"], "thesis-writing-mentor")
        self.assertEqual(plugin["agentName"], "thesis-writing-mentor")
        self.assertEqual(len(plugin["tags"]), 3)
        self.assertEqual(len(plugin["quickPrompts"]), 3)
        self.assertEqual(plugin["defaultInitPrompt"], plugin["quickPrompts"][0])

    def test_no_old_version(self):
        text_files = list(EXPERT_ROOT.rglob("*.md")) + list(EXPERT_ROOT.rglob("*.json")) + list(EXPERT_ROOT.rglob("*.yaml"))
        merged = "\n".join(path.read_text(encoding="utf-8") for path in text_files)
        self.assertNotIn("1.2.0", merged)

    def test_tags_and_quickprompts_cover_three_function_directions(self):
        plugin = json.loads((EXPERT_ROOT / ".codebuddy-plugin" / "plugin.json").read_text(encoding="utf-8"))
        tag_zh = [item["zh"] for item in plugin["tags"]]
        self.assertEqual(tag_zh, ["论文全流程", "文献与论证", "答辩与分享"])
        prompts = [item["zh"] for item in plugin["quickPrompts"]]
        self.assertEqual(len(prompts), 3)
        for keyword in ("题目", "文献", "答辩"):
            self.assertTrue(any(keyword in prompt for prompt in prompts), f"quickPrompts 未覆盖方向关键词: {keyword}")


if __name__ == "__main__":
    unittest.main()
