import json
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
EXPERT_DIR = SKILL_DIR.parents[1]
PLUGIN_PATH = EXPERT_DIR / ".codebuddy-plugin" / "plugin.json"
AGENT_PATH = EXPERT_DIR / "agents" / "english-writing-coach.md"
REFERENCE_DIR = SKILL_DIR / "references"


class V13ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))
        cls.agent = AGENT_PATH.read_text(encoding="utf-8")
        cls.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_version_and_positioning(self):
        self.assertEqual(self.plugin["version"], "1.3.0")
        self.assertEqual(self.plugin["expertType"], "agent")
        self.assertEqual(self.plugin["profession"]["zh"], "大学英语学习教练")
        self.assertIn("College English Learning Coach", self.plugin["profession"]["en"])

    def test_display_fields_follow_constraints(self):
        description = self.plugin["displayDescription"]["zh"]
        self.assertGreaterEqual(len(description), 40)
        self.assertLessEqual(len(description), 50)
        self.assertEqual(len(self.plugin["tags"]), 3)
        self.assertEqual(len(self.plugin["quickPrompts"]), 3)
        self.assertEqual(self.plugin["defaultInitPrompt"], self.plugin["quickPrompts"][0])

    def test_intro_shows_scope_and_boundaries(self):
        for term in ("写作", "阅读理解", "语境词汇", "语法", "英汉互译", "CET-4", "不代写", "不做真实听力"):
            self.assertIn(term, self.agent)

    def test_required_references_exist(self):
        required = [
            "learning-foundation.md",
            "reading-comprehension.md",
            "vocabulary-learning.md",
            "grammar-training.md",
            "translation-training.md",
            "cet-text-training.md",
        ]
        for name in required:
            self.assertTrue((REFERENCE_DIR / name).exists(), name)
            self.assertIn(name, self.skill)

    def test_cet_scope_is_not_overclaimed(self):
        cet = (REFERENCE_DIR / "cet-text-training.md").read_text(encoding="utf-8")
        for term in ("写作", "阅读理解", "汉译英段落翻译", "当前不包括", "听力", "真实口语", "不推算官方总分"):
            self.assertIn(term, cet)

    def test_reading_requires_evidence_and_unique_answer(self):
        reading = (REFERENCE_DIR / "reading-comprehension.md").read_text(encoding="utf-8")
        self.assertIn("唯一答案检查", reading)
        self.assertIn("原文证据", reading)
        self.assertIn("原创练习", reading)
        self.assertIn("改为开放题", reading)

    def test_vocabulary_limits_batch_and_long_term_claims(self):
        vocabulary = (REFERENCE_DIR / "vocabulary-learning.md").read_text(encoding="utf-8")
        self.assertIn("不超过 8 个", vocabulary)
        self.assertIn("先回忆", vocabulary)
        self.assertIn("不承诺跨会话", vocabulary)

    def test_grammar_has_transfer_validation(self):
        grammar = (REFERENCE_DIR / "grammar-training.md").read_text(encoding="utf-8")
        for step in ("识别", "改错", "产出", "新语境验收"):
            self.assertIn(step, grammar)
        self.assertIn("不把个人偏好写成语法错误", grammar)

    def test_translation_separates_scenarios_and_reference_answer(self):
        translation = (REFERENCE_DIR / "translation-training.md").read_text(encoding="utf-8")
        for scenario in ("CET 汉译英", "考研英译中", "通用英译中 / 中译英"):
            self.assertIn(scenario, translation)
        self.assertIn("不是唯一答案", translation)
        self.assertIn("信息不增添", translation)

    def test_session_state_is_explicitly_non_persistent(self):
        foundation = (REFERENCE_DIR / "learning-foundation.md").read_text(encoding="utf-8")
        self.assertIn("当前会话", foundation)
        self.assertIn("不声称已跨会话保存", foundation)
        self.assertIn("不承诺间隔复习", foundation)

    def test_html_report_scope_remains_exam_writing_only(self):
        self.assertIn("当前脚本仅支持 CET/考研作文批改", self.skill)
        self.assertIn("不得套用 `exam_review`", self.skill)


if __name__ == "__main__":
    unittest.main()
