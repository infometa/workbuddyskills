#!/usr/bin/env python3
"""中文极限词库的内容测试。

中文没有词边界，扫描是子串匹配，所以这里的重点是**误报语料**：正常的规格、
步骤、材质描述必须扫不出东西。新增词条时先往 CLEAN_COPY 里加一条真实文案。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_SCRIPTS = ROOT.parent / "listing-core" / "scripts"
PRIVATE_DATA = ROOT.parent / "_listing-private-assets" / "data"
sys.path.insert(0, str(CORE_SCRIPTS))

from restricted_content_scan import scan  # noqa: E402

LIBRARY = json.loads((PRIVATE_DATA / "superlative-claims-zh-v1.json").read_text(encoding="utf-8"))
EN_LIBRARY = json.loads((PRIVATE_DATA / "superlative-claims-v1.json").read_text(encoding="utf-8"))

# 正常中文文案。任何一条扫出命中都是误报，除非在测试里显式说明为什么应该命中。
CLEAN_COPY = {
    "规格": "最大承重 20kg，最小尺寸 5cm，最高耐温 120°C，最低 -20°C",
    "安装步骤": "第一步：拧开盖子；第二步：加水至最上方刻度线；第三步：静置一分钟",
    "款式": "极简设计，一次性使用，适用于最新款手机，全场景适配",
    "清洁": "彻底清洁毛孔，深层去污，快速去除异味",
    "包装": "内含说明书一份，专利号 ZL2023XXXXXXX",
    "风格": "治愈系 ins 风设计，放在桌面很解压",
    "尺码": "第一次购买建议选大一码",
    "耐用": "304 不锈钢材质，耐用不生锈，经久耐用",
}


def terms_of(library):
    return {t for level in library["profiles"].values() for r in level for t in r["terms"]}


def hits_for(text):
    return scan({"description": text}, LIBRARY)


def severity_of(text):
    hits = hits_for(text)
    return hits[0]["severity"] if hits else None


class LibraryShapeTest(unittest.TestCase):
    def test_no_single_character_terms(self):
        """单字会大面积子串误命中——「最」撞「最大承重」，「一」撞「一次性」。"""
        for term in terms_of(LIBRARY):
            self.assertGreaterEqual(len(term), 2, f"{term} 是单字词条")

    def test_every_rule_carries_reason_and_replacement(self):
        for level in ("block", "review"):
            for rule in LIBRARY["profiles"][level]:
                self.assertTrue(rule["reason"], rule["category"])
                self.assertTrue(rule["replacement"], rule["category"])
                self.assertTrue(rule["terms"], rule["category"])

    def test_terms_are_unique(self):
        seen = set()
        for level in ("block", "review"):
            for rule in LIBRARY["profiles"][level]:
                for term in rule["terms"]:
                    self.assertNotIn(term, seen, f"{term} 重复收录")
                    seen.add(term)

    def test_does_not_overlap_the_english_library(self):
        self.assertEqual(terms_of(LIBRARY) & terms_of(EN_LIBRARY), set())

    def test_locale_is_declared(self):
        self.assertEqual(LIBRARY["locale"], "zh")

    def test_readme_term_count_matches_the_library(self):
        """README 里的条数必须跟库对得上——文档数字一旦落后就会被到处引用。"""
        readme = (PRIVATE_DATA.parent / "README.md").read_text(encoding="utf-8")
        rules = [r for level in LIBRARY["profiles"].values() for r in level]
        expected = f"{len(terms_of(LIBRARY))} 条 / {len(rules)} 类"
        self.assertIn(expected, readme, f"README 应写「{expected}」")

    def test_matching_note_records_the_counter_examples(self):
        """约束和反例必须钉在数据旁边，否则下一个人会去加裸「最大」。"""
        note = LIBRARY["matching_note"]
        for counter_example in ("第一步", "最大承重", "治愈系"):
            self.assertIn(counter_example, note)


class FalsePositiveCorpusTest(unittest.TestCase):
    def test_ordinary_chinese_copy_is_not_flagged(self):
        for name, text in CLEAN_COPY.items():
            with self.subTest(copy=name):
                self.assertEqual(hits_for(text), [], f"{name} 出现误报")

    def test_spec_superlatives_are_deliberately_excluded(self):
        """「最大／最小／最高／最低」在规格里是事实，不收进库。"""
        self.assertIsNone(severity_of("最大直径 8cm"))
        self.assertIsNone(severity_of("最低工作温度 -20°C"))

    def test_bare_ordinal_is_excluded_but_ranking_phrase_is_not(self):
        self.assertIsNone(severity_of("第一步先充电"))
        self.assertEqual(severity_of("销量第一的钛杯"), "block")


class SeverityPolicyTest(unittest.TestCase):
    def test_advertising_law_absolutes_block(self):
        """《广告法》第九条的绝对化用语，属实也不许写。"""
        for text in ("最好的选择", "顶级工艺", "独一无二的设计"):
            self.assertEqual(severity_of(text), "block", text)

    def test_authority_and_ranking_claims_block(self):
        for text in ("免检产品", "驰名商标", "全国第一", "特供渠道"):
            self.assertEqual(severity_of(text), "block", text)

    def test_promotional_claims_block(self):
        for text in ("限时抢购", "买一送一", "包邮到家", "免费赠送"):
            self.assertEqual(severity_of(text), "block", text)

    def test_evidence_backed_claims_only_review(self):
        """有证据即可保留的判复核，不判死。"""
        for text in ("食品级硅胶", "专利技术加持", "可降解材质", "抑菌处理"):
            self.assertEqual(severity_of(text), "review", text)

    def test_disease_outcome_claims_block_but_generic_effects_review(self):
        self.assertEqual(severity_of("可根治脚气"), "block")
        self.assertEqual(severity_of("缓解肩颈酸痛"), "review")


class CrossLanguageTest(unittest.TestCase):
    def test_mixed_draft_is_covered_by_both_libraries(self):
        """中文草稿里夹英文营销词时，两个库各管各的那一半。"""
        mixed = {"description": "全网最低价的 Best Titanium Cup with free shipping"}
        zh_terms = {hit["term"] for hit in scan(mixed, LIBRARY)}
        en_terms = {hit["term"] for hit in scan(mixed, EN_LIBRARY)}
        self.assertIn("全网最低", zh_terms)
        self.assertIn("Best", en_terms)
        self.assertIn("free shipping", en_terms)

    def test_chinese_library_finds_nothing_in_pure_english_copy(self):
        self.assertEqual(scan({"description": "Stainless steel travel mug, 350ml"}, LIBRARY), [])


if __name__ == "__main__":
    unittest.main()
