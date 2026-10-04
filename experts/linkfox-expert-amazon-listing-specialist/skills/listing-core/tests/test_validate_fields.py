#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
CORE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE_ROOT / "scripts"))
from build_spec import assemble_spec  # noqa: E402
from validate_fields import check_fields  # noqa: E402

KW = {"core": ["drawer organizer"], "scene": ["kitchen"], "pain": ["messy"]}
SPEC = assemble_spec("benchmark", ["Rocktone"], ["BrandX"], KW, [])

def draft(**over):
    d = {"title": "Drawer Organizer for Kitchen, Expandable 28-45cm",
         "bullets": ["EXPANDABLE DESIGN: fits kitchen drawers", "EASY CLEAN: smooth surface",
                     "FOOD-GRADE: safe material", "STACKABLE: saves space", "WARRANTY: friendly support"],
         "description": "An expandable drawer organizer.",
         "search_terms": "storage bin utensil tray"}
    d.update(over)
    return d

class TestValidateFields(unittest.TestCase):
    def test_pass_report_shape(self):
        r = check_fields(draft(), SPEC, facts_text="expandable 28-45cm kitchen drawer organizer")
        self.assertEqual(r["kind"], "listingCheckReport")
        self.assertEqual(r["fields"]["title"]["status"], "pass")

    def test_over_limit_only_flags_title(self):
        r = check_fields(draft(title="x" * 90), SPEC)
        self.assertEqual(r["fields"]["title"]["status"], "fail")
        self.assertEqual(r["fields"]["description"]["status"], "pass")  # 无级联

    def test_competitor_brand_flagged_owned_not(self):
        r = check_fields(draft(description="Better than BrandX. By Rocktone."), SPEC)
        codes = [i["code"] for i in r["fields"]["description"]["issues"]]
        self.assertIn("competitor_brand", codes)
        self.assertEqual(sum(1 for i in r["fields"]["description"]["issues"]
                             if i["code"] == "competitor_brand"), 1)

    def test_core_keyword_split_detected(self):
        r = check_fields(draft(title="Drawer Expandable Organizer for Kitchen"), SPEC)
        codes = [i["code"] for i in r["fields"]["title"]["issues"]]
        self.assertIn("core_kw_split", codes)

    def test_front_dup_and_unsupported_claim(self):
        r = check_fields(draft(search_terms="kitchen drawer organizer bin",
                               description="Holds 99 kg load."), SPEC, facts_text="expandable 28-45cm")
        self.assertTrue(r["coverage"]["search_terms_front_dup"])
        self.assertIn("99 kg", " ".join(r["fact_faithfulness"]["unsupported_claims"]))

    def test_decimal_version_followed_by_prose_is_not_a_fake_unit(self):
        for wording in (
            "Bluetooth 5.4 and multipoint connectivity.",
            "Bluetooth 5.4 with LE Audio.",
            "Bluetooth 5.4 supports compatible devices.",
        ):
            with self.subTest(wording=wording):
                result = check_fields(
                    draft(description=wording),
                    SPEC,
                    facts_text="Expandable 28-45cm; connectivity: Bluetooth 5.4, LE Audio",
                )
                self.assertEqual(result["fact_faithfulness"]["unsupported_claims"], [])

    def test_decimal_measurement_still_requires_fact_support(self):
        result = check_fields(
            draft(description="Wireless operation uses 5.4 GHz."),
            SPEC,
            facts_text="Expandable 28-45cm; connectivity details unavailable",
        )
        self.assertEqual(result["fact_faithfulness"]["unsupported_claims"], ["5.4 GHz"])

    def test_unit_fact_match_normalizes_hyphen_and_whitespace(self):
        result = check_fields(
            draft(
                title="Drawer Organizer for Kitchen",
                description="Provides 24 hours with the case.",
            ),
            SPEC,
            facts_text="Battery life: 24-hours   with case",
        )
        self.assertEqual(result["fact_faithfulness"]["unsupported_claims"], [])

    def test_front_dup_is_unicode_aware_for_localized_listing(self):
        r = check_fields(draft(
            title="Quiseen Whiskey Steine Set – 9 Kühlsteine aus Naturstein, Geschenk",
            item_highlights=["Coffret dégustation élégant"],
            bullets=[
                "KÜHLSTEINE: Kühlt Whiskey ohne Verwässern.",
                "Ideale Whisky Geschenkidee.",
                "Anders als Eiswürfel.",
                "Wiederverwendbar.",
                "Einfache Anwendung.",
            ],
            description="Accessoire pour boissons fraîches.",
            search_terms=(
                "frozen stones kühlwürfel gin zubehör whisky karaffe eis "
                "alkohol geschenkidee whiskyliebhaber dégustation fraîches"
            ),
        ), SPEC)
        self.assertEqual(
            r["coverage"]["search_terms_front_dup"],
            ["whisky", "geschenkidee"],
        )
        self.assertNotIn("k", r["coverage"]["search_terms_front_dup"])
        self.assertNotIn("rfel", r["coverage"]["search_terms_front_dup"])

    def test_banned_term_carries_library_replacement(self):
        r = check_fields(draft(description="This product may help cure your ailment."), SPEC)
        issues = r["fields"]["description"]["issues"]
        banned = [i for i in issues if i["code"] == "banned_term"]
        self.assertTrue(banned)
        self.assertEqual(
            banned[0]["replacement"],
            "Remove unsupported therapeutic wording or route to regulated-health review with evidence.",
        )

    def test_item_highlights_str_yields_type_error(self):
        r = check_fields(draft(item_highlights="not a list"), SPEC)
        ih = r["fields"]["item_highlights"]
        self.assertEqual(ih["status"], "fail")
        codes = [i["code"] for i in ih["issues"]]
        self.assertIn("type_error", codes)
        self.assertEqual(r["fields"]["title"]["status"], "pass")
        self.assertEqual(r["fields"]["description"]["status"], "pass")

    def test_item_highlights_must_be_one_line_single_field(self):
        multiple = check_fields(draft(item_highlights=["Material benefit", "Scene benefit"]), SPEC)
        line_break = check_fields(draft(item_highlights=["Material benefit\nScene benefit"]), SPEC)
        bullet = check_fields(draft(item_highlights=["1. Material benefit"]), SPEC)
        self.assertIn(
            "item_highlights_single_line",
            {issue["code"] for issue in multiple["fields"]["item_highlights"]["issues"]},
        )
        self.assertIn(
            "item_highlights_line_break",
            {issue["code"] for issue in line_break["fields"]["item_highlights"]["issues"]},
        )
        self.assertIn(
            "item_highlights_bullet_format",
            {issue["code"] for issue in bullet["fields"]["item_highlights"]["issues"]},
        )

    def test_missing_required_field_is_a_failure(self):
        value = draft()
        del value["description"]
        r = check_fields(value, SPEC)
        self.assertEqual(r["fields"]["description"]["status"], "fail")
        self.assertEqual(r["fields"]["description"]["issues"][0]["code"], "missing_field")

    def test_bullet_count_and_empty_item_are_failures(self):
        r = check_fields(draft(bullets=["one", "two", "", "four"]), SPEC)
        self.assertEqual(r["fields"]["bullets"]["status"], "fail")
        codes = {issue["code"] for issue in r["fields"]["bullets"]["issues"]}
        self.assertIn("bullet_count", codes)
        self.assertIn("empty_item", codes)

    def test_bullet_204_is_warning_not_failure(self):
        r = check_fields(draft(bullets=["x" * 204, "b", "c", "d", "e"]), SPEC)
        bullets = r["fields"]["bullets"]
        self.assertEqual(bullets["status"], "warn")
        self.assertIn("recommended_length", {i["code"] for i in bullets["issues"]})

    def test_bullet_over_255_is_failure(self):
        r = check_fields(draft(bullets=["x" * 256, "b", "c", "d", "e"]), SPEC)
        self.assertEqual(r["fields"]["bullets"]["status"], "fail")

    def test_bullet_total_over_1275_is_failure(self):
        r = check_fields(draft(bullets=["x" * 256] * 5), SPEC)
        bullets = r["fields"]["bullets"]
        self.assertEqual(bullets["status"], "fail")
        self.assertEqual(bullets["total_chars"], 1280)

    def test_bullet_total_1275_is_not_failure(self):
        r = check_fields(draft(bullets=["x" * 255] * 5), SPEC)
        self.assertEqual(r["fields"]["bullets"]["status"], "warn")

    def test_empty_required_fields_are_failures(self):
        r = check_fields(draft(title=" ", search_terms="", item_highlights=[]), SPEC)
        for field in ("title", "search_terms", "item_highlights"):
            self.assertEqual(r["fields"][field]["status"], "fail")
            self.assertIn("empty_field", {i["code"] for i in r["fields"][field]["issues"]})

    def test_verified_minimum_age_blocks_newborn_in_backend_fields(self):
        spec = dict(SPEC)
        spec["fact_constraints"] = {
            "age_months": {"min": 6, "max": 18, "source": "target_product_facts"},
        }
        result = check_fields(draft(search_terms="newborn sensory activity"), spec)

        self.assertEqual(result["fields"]["search_terms"]["status"], "fail")
        self.assertIn(
            "fact_conflict",
            {issue["code"] for issue in result["fields"]["search_terms"]["issues"]},
        )

if __name__ == "__main__":
    unittest.main()


class TestSubjectMatter(unittest.TestCase):
    """subject_matter 是可选后台字段：缺失不算 fail，给了就要过禁词/品牌安检。"""

    def test_absent_subject_matter_is_not_a_failure(self):
        r = check_fields(draft(), SPEC)
        self.assertNotIn("subject_matter", r["fields"])

    def test_clean_subject_matter_passes_without_char_limit(self):
        r = check_fields(draft(subject_matter=["kitchen storage", "drawer organizing"]), SPEC)
        self.assertEqual(r["fields"]["subject_matter"]["status"], "pass")
        self.assertIsNone(r["fields"]["subject_matter"]["limit"])

    def test_competitor_brand_in_subject_matter_fails(self):
        r = check_fields(draft(subject_matter=["kitchen storage", "BrandX organizer"]), SPEC)
        codes = [i["code"] for i in r["fields"]["subject_matter"]["issues"]]
        self.assertIn("competitor_brand", codes)
        self.assertEqual(r["fields"]["subject_matter"]["status"], "fail")

    def test_empty_item_flagged(self):
        r = check_fields(draft(subject_matter=["kitchen storage", "  "]), SPEC)
        codes = [i["code"] for i in r["fields"]["subject_matter"]["issues"]]
        self.assertIn("empty_item", codes)


class TestUserBannedTerms(unittest.TestCase):
    """卖家避讳词 / 词表禁用词：文档一直声称「等同违禁词」，实现里却没人扫。"""

    SPEC_BANNED = assemble_spec(
        "benchmark", ["Rocktone"], ["BrandX"], KW, [], banned_terms=["expandable"]
    )

    def test_user_banned_term_fails_the_field(self):
        r = check_fields(draft(), self.SPEC_BANNED)
        issues = r["fields"]["title"]["issues"]
        self.assertIn("banned_term", [i["code"] for i in issues])
        self.assertTrue(any("user_banned" in i["detail"] for i in issues))
        self.assertEqual(r["fields"]["title"]["status"], "fail")

    def test_user_banned_term_scans_every_field(self):
        r = check_fields(draft(), self.SPEC_BANNED)
        for field in ("title", "bullets", "description"):
            details = " ".join(i["detail"] for i in r["fields"][field]["issues"])
            self.assertIn("user_banned", details, field)

    def test_clean_draft_still_passes_without_banned_terms(self):
        r = check_fields(draft(), SPEC)
        self.assertEqual(r["fields"]["title"]["status"], "pass")


class TestUserBannedSuffixEscape(unittest.TestCase):
    """避讳词的复数/副词逃逸。

    整词匹配会让 `EGG` 拦不住 `EGGS`、`WIRELESS` 拦不住 `WIRELESSLY`——而
    CLAUDE.md 里 [卖家偏好] 的示例避讳词字面就是 `WIRELESS、EGG`，等于文档
    自带的例子就能被绕过。规则是词首对齐、允许后缀，但不允许词中出现。
    """

    def _spec(self, *terms):
        return assemble_spec("benchmark", ["Rocktone"], ["BrandX"], KW, [], banned_terms=list(terms))

    def _title_status(self, title, *terms):
        r = check_fields(draft(title=title), self._spec(*terms))
        return r["fields"]["title"]["status"]

    def test_plural_does_not_escape(self):
        self.assertEqual(self._title_status("Two EGGS included in the kit", "EGG"), "fail")

    def test_adverb_does_not_escape(self):
        self.assertEqual(self._title_status("Works WIRELESSLY indoors", "WIRELESS"), "fail")

    def test_compound_word_is_not_a_hit(self):
        """EGGSHELL 是颜色词，卖家避的是"鸡蛋"不是这个色号——只放行屈折后缀，不放行复合词。"""
        self.assertEqual(self._title_status("EGGSHELL white finish drawer", "EGG"), "pass")

    def test_short_term_does_not_over_fire(self):
        """短避讳词是词首对齐的死穴：pet 不能撞上 petite，clean 不能撞上 cleanser。"""
        self.assertEqual(self._title_status("Petite size drawer organizer", "pet"), "pass")
        self.assertEqual(self._title_status("A cleanser bottle holder", "clean"), "pass")
        self.assertEqual(self._title_status("Artificial leather drawer mat", "art"), "pass")

    def test_short_term_still_catches_inflections(self):
        """但短词的屈折形式仍要拦住——长度闸会把这几条一起放掉。"""
        self.assertEqual(self._title_status("Pet hair remover for drawers", "pet"), "fail")
        self.assertEqual(self._title_status("Two pets at home drawer set", "pet"), "fail")
        self.assertEqual(self._title_status("Cleaning cloth included here", "clean"), "fail")

    def test_term_inside_another_word_is_not_a_hit(self):
        """LEGGINGS 不该被 EGG 误伤——这正是当初放弃子串匹配的原因。"""
        self.assertEqual(self._title_status("Organic LEGGINGS for women", "EGG"), "pass")

    def test_suffix_rule_still_rejects_mid_word(self):
        self.assertEqual(self._title_status("A secure closure for drawers", "cure"), "pass")

    def test_obfuscated_spelling_still_hits(self):
        self.assertEqual(self._title_status("A c-u-r-e for messy drawers", "cure"), "fail")

    def test_multiword_banned_phrase_hits(self):
        self.assertEqual(self._title_status("Get free shipping on this drawer", "free shipping"), "fail")

    def test_hyphenated_compound_still_hits(self):
        """EGG-FREE 该拦（连字符断词，走屈折分支的词尾断言），EGGSHELL 不该拦。"""
        self.assertEqual(self._title_status("EGG-FREE recipe drawer label", "EGG"), "fail")

    def test_derivational_er_suffix_is_a_known_gap(self):
        """-er/-est 刻意不拦：加上它 pet→peter、cat→cater 会全部误报。

        这条测试是把「已知局限」钉住，不是描述期望的功能。要拦 cleaner 就把它
        写进避讳词表，不要改 _INFLECTION_SUFFIX。
        """
        self.assertEqual(self._title_status("A cleaner bottle for drawers", "clean"), "pass")
        self.assertEqual(self._title_status("The cleanest surface finish", "clean"), "pass")
        self.assertEqual(self._title_status("Peter piper drawer organizer", "pet"), "pass")
