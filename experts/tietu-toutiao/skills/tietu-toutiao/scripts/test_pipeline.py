#!/usr/bin/env python3
"""Regression tests for the Tietu Toutiao deterministic pipeline (v1 + v2 contract)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


validate = load("validate", SCRIPT_DIR / "validate_content_state.py")
layout = load("layout", SCRIPT_DIR / "layout_engine.py")
render = load("render", SCRIPT_DIR / "render_cover.py")
patcher = load("patcher", SCRIPT_DIR / "apply_patch.py")
versions = load("versions", SCRIPT_DIR / "version_manager.py")
build_covers = load("build_covers", SCRIPT_DIR / "build_covers.py")

TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
PKG_REFERENCES = SCRIPT_DIR.parent.parent.parent / "references"
SCHEMA_V1_PATH = PKG_REFERENCES / "content-state.v1.schema.json"
SCHEMA_V2_PATH = PKG_REFERENCES / "content-state.v2.schema.json"
CANVAS_W, CANVAS_H = 1080, 1920
KNOWN_LAYER_TYPES = {"text", "image", "rect", "line", "item_list"}
KNOWN_TOKENS = {"{masthead}", "{date}", "{headline}", "{sub_headline}", "{primary_photo_path}"}
TOKEN_RE = __import__("re").compile(r"\{[a-z_]+\}")


def lint_templates() -> None:
    """Templates are the single source of layout truth; lint them at CI time."""
    names = {path.stem for path in TEMPLATES_DIR.glob("*.json")}
    assert names == {"authoritative", "visual", "digest", "synthesis"}, f"unexpected template set: {names}"
    for template_path in sorted(TEMPLATES_DIR.glob("*.json")):
        template = json.loads(template_path.read_text(encoding="utf-8"))
        layers = template.get("layers")
        assert isinstance(layers, list) and layers, f"{template_path.name}: no layers"
        for index, layer in enumerate(layers):
            where = f"{template_path.name} layer[{index}]"
            layer_type = layer.get("type")
            assert layer_type in KNOWN_LAYER_TYPES, f"{where}: unknown type {layer_type!r}"
            if layer_type == "item_list":
                assert isinstance(layer.get("w"), int) and layer["w"] > 0, f"{where}: w must be a positive int"
                assert 0 <= layer.get("x", -1) and layer.get("x", 0) < CANVAS_W, f"{where}: x outside canvas"
                y = layer.get("y")
                if isinstance(y, str):
                    assert y.strip().startswith("="), f"{where}: string y must be an expression"
                else:
                    assert 0 <= y and y < CANVAS_H, f"{where}: y outside canvas"
                assert layer.get("item_max", 0) >= 1, f"{where}: item_max must allow at least one item"
                continue
            if layer_type in ("text", "rect"):
                assert 0 <= layer.get("x", -1) and layer.get("x", 0) < CANVAS_W, f"{where}: x outside canvas"
                assert 0 <= layer.get("y", -1) and layer.get("y", 0) < CANVAS_H, f"{where}: y outside canvas"
                if layer_type == "rect":
                    assert layer["x"] + layer["w"] <= CANVAS_W, f"{where}: rect exceeds width"
                    assert layer["y"] + layer["h"] <= CANVAS_H, f"{where}: rect exceeds height"
                if layer_type == "text":
                    assert layer.get("x", 0) + layer.get("max_width", 0) <= CANVAS_W, f"{where}: text exceeds width"
            if layer_type == "image":
                assert layer.get("x", 0) + layer["w"] <= CANVAS_W, f"{where}: image exceeds width"
                assert layer.get("y", 0) + layer["h"] <= CANVAS_H, f"{where}: image exceeds height"
            if layer_type == "line":
                assert max(layer["x1"], layer["x2"]) <= CANVAS_W, f"{where}: line exceeds width"
                assert max(layer["y1"], layer["y2"]) <= CANVAS_H, f"{where}: line exceeds height"
            # Every token used in the template must be resolvable by the layout engine.
            for key, value in layer.items():
                if isinstance(value, str):
                    for token in TOKEN_RE.findall(value):
                        assert token in KNOWN_TOKENS, f"{where}: unresolvable token {token} in {key!r}"
        # Each template must place masthead, headline and the primary photo.
        fields = {layer.get("field") for layer in layers}
        assert "masthead.text" in fields, f"{template_path.name}: missing masthead layer"
        assert "headline.original" in fields, f"{template_path.name}: missing headline layer"
        assert "primary_photo.path" in fields, f"{template_path.name}: missing primary photo layer"


def check_schema_parity() -> None:
    """The JSON schema documents and the hardcoded validator must not drift apart."""
    source = (SCRIPT_DIR / "validate_content_state.py").read_text(encoding="utf-8")
    for schema_path, const in ((SCHEMA_V1_PATH, "content-state.v1"), (SCHEMA_V2_PATH, "content-state.v2")):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for field in schema.get("required", []):
            assert f'"{field}"' in source, f"{schema_path.name}: validator misses required field: {field}"
        assert schema["properties"]["schema_version"]["const"] == const, f"{schema_path.name}: wrong const"


def assert_no_unresolved_tokens(value, where: str = "layout") -> None:
    if isinstance(value, str):
        assert not TOKEN_RE.search(value), f"{where}: unresolved token in {value!r}"
    elif isinstance(value, list):
        for item in value:
            assert_no_unresolved_tokens(item, where)
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_unresolved_tokens(item, f"{where}.{key}")


def make_image(path: Path, size: tuple[int, int], colors: tuple[str, str]) -> None:
    image = Image.new("RGB", size, colors[0])
    draw = ImageDraw.Draw(image)
    draw.rectangle([size[0] // 2, 0, size[0], size[1]], fill=colors[1])
    image.save(path, "PNG")


def make_v2_base(state: dict) -> dict:
    """Turn the v1 fixture into a valid v2 state (caller tweaks from there)."""
    v2 = json.loads(json.dumps(state, ensure_ascii=False))
    v2["schema_version"] = "content-state.v2"
    v2["source_manifest"] = {
        "sources": [
            {"file": "wKgNBmqQ5c2A.pdf", "sha256": "a" * 64, "pages_used": [1], "page_label": "08版"}
        ],
        "ingested_at": "2026-08-31T20:05:00+08:00",
        "ingest_method": "pdfplumber@150dpi",
    }
    v2["layout_analysis"] = {
        "masthead_bbox": {"x": 60, "y": 60, "width": 900, "height": 180, "confidence": 0.99},
        "photo_regions": [
            {"bbox": {"x": 676, "y": 1722, "width": 1268, "height": 797}, "kind": "news_photo",
             "subject": "疍家舞蹈群像", "confidence": 0.94}
        ],
        "analyzer": "multimodal-model",
        "confirmed": True,
    }
    v2["items"] = [
        {"id": "item-08-danjia", "type": "feature", "headline": "《潮起大湾》疍家人",
         "summary": "音乐剧重现东南沿海疍家人千年漂泊史", "source_page": "08版",
         "photo_region_ref": 0, "weight": 0.95,
         "scores": {"visual": 0.95, "relevance": 0.92}, "selected": True},
        {"id": "item-07-yimakan", "type": "feature", "headline": "《永不落幕的伊玛堪》",
         "summary": "赫哲族史诗与东北抗联精神的跨时空对话", "source_page": "07版",
         "weight": 0.88, "selected": True},
        {"id": "item-02-zuozongtang", "type": "news", "headline": "学术会议侧记",
         "summary": "弱视觉素材条目", "weight": 0.55, "selected": False},
    ]
    v2["editorial_log"] = {
        "narrative": "文化-历史-产业-国防 四维覆盖",
        "excluded": [{"id": "item-02-zuozongtang", "reason": "视觉素材弱"}],
        "model": "regression-fixture",
        "generated_at": "2026-08-31T20:10:00+08:00",
        "review": {
            "passed": True,
            "checks": [
                {"item": "标题忠于原文", "ok": True},
                {"item": "日期报头准确", "ok": True},
            ],
        },
    }
    return v2


def test_v2_contract(state: dict, state_path: Path, workspace: Path) -> None:
    """v2 contract: validation, item_list resolution, review gate, archival."""
    v2 = make_v2_base(state)
    assert validate.validate_state(v2, workspace, check_files=True) == []

    # Low-confidence key fields must not be confirmed.
    low = json.loads(json.dumps(v2, ensure_ascii=False))
    low["masthead"] = {"text": "?报", "confidence": 0.6, "confirmed": True}
    errors = validate.validate_state(low, workspace, check_files=False)
    assert any("must stay confirmed=false" in error for error in errors), errors

    # v2-only fields are rejected on a v1 document.
    mixed = json.loads(json.dumps(state, ensure_ascii=False))
    mixed["items"] = []
    errors = validate.validate_state(mixed, workspace, check_files=False)
    assert any("requires schema_version content-state.v2" in error for error in errors), errors

    # Duplicate item ids are rejected.
    dup = json.loads(json.dumps(v2, ensure_ascii=False))
    dup["items"].append(json.loads(json.dumps(dup["items"][0])))
    errors = validate.validate_state(dup, workspace, check_files=False)
    assert any("duplicates" in error for error in errors), errors

    # item_list resolution: selected+weight sorting, shrink, drop.
    items_layer = {"type": "item_list", "x": 40, "y": 1000, "w": 1000, "item_max": 4}
    four = layout._resolve_item_list(dict(items_layer), v2)
    assert [entry["headline"] for entry in four["items"]] == ["《潮起大湾》疍家人", "《永不落幕的伊玛堪》"]
    two = layout._resolve_item_list(dict(items_layer), {**v2, "items": v2["items"][:2]})
    assert len(two["items"]) == 2
    none_selected = layout._resolve_item_list(dict(items_layer), {**v2, "items": [v2["items"][2]]})
    assert none_selected is None
    assert layout._resolve_item_list(dict(items_layer), {}) is None

    # Coordinate expressions: happy path and hard failures.
    variables = {"canvas_w": 1080, "canvas_h": 1920, "photo_top": 400, "photo_bottom": 1020}
    assert layout._eval_expression("=photo_bottom + 40", variables, "t") == 1060
    assert layout._eval_expression("=canvas_h - 120", variables, "t") == 1800
    assert layout._eval_expression("=(photo_bottom - photo_top) / 2", variables, "t") == 310
    for bad in ("=secret_var + 1", "=__import__('os').getcwd()", "photo_bottom + 1"):
        try:
            layout._eval_expression(bad, variables, "t")
        except ValueError:
            pass
        else:
            raise AssertionError(f"expression was accepted: {bad!r}")

    # Full v2 e2e: all four templates render from one state, editorial log archived.
    v2_path = workspace / "content-state-v2.json"
    v2_path.write_text(json.dumps(v2, ensure_ascii=False, indent=2), encoding="utf-8")
    v2_dir = workspace / "oneshot_v2"
    rendered, errors = build_covers.build_all(v2_path, v2_dir)
    assert errors == [], errors
    assert len(rendered) == 4, rendered
    synthesis_layout = json.loads((v2_dir / "layout_synthesis.json").read_text(encoding="utf-8"))
    item_layers = [entry for entry in synthesis_layout["layers"] if entry.get("type") == "item_list"]
    assert len(item_layers) == 1 and item_layers[0]["y"] == 1060, item_layers
    archive = v2_dir / "editorial_log.jsonl"
    assert archive.is_file() and archive.read_text(encoding="utf-8").strip()

    # Self-review gate: a v2 state without a passed review must refuse to render.
    no_review = json.loads(json.dumps(v2, ensure_ascii=False))
    del no_review["editorial_log"]["review"]
    no_review["revision_id"] = "v2-noreview"
    no_review_path = workspace / "content-state-v2-noreview.json"
    no_review_path.write_text(json.dumps(no_review, ensure_ascii=False), encoding="utf-8")
    rendered_bad, bad_errors = build_covers.build_all(no_review_path, workspace / "oneshot_noreview")
    assert rendered_bad == [] and any("review" in error for error in bad_errors), bad_errors


def main() -> int:
    lint_templates()
    check_schema_parity()
    with tempfile.TemporaryDirectory(prefix="tietu_test_") as temp:
        workspace = Path(temp)
        source_path = workspace / "newspaper.png"
        photo_path = workspace / "photo.png"
        make_image(source_path, (2000, 1400), ("#eeeeee", "#bbbbbb"))
        make_image(photo_path, (1600, 400), ("#cc3333", "#3366cc"))
        state_path = workspace / "content-state.json"
        state = {
            "schema_version": "content-state.v1",
            "source_image": source_path.name,
            "masthead": {"text": "民族报", "confidence": 0.99, "confirmed": True},
            "date": {"text": "2026年8月31日", "confidence": 0.99, "confirmed": True},
            "headline": {"original": "全国民族团结进步表彰大会在京召开", "confidence": 0.98, "confirmed": True},
            "sub_headline": {"text": "这是结构化渲染回归测试", "confidence": 0.95, "confirmed": True},
            "primary_photo": {
                "path": photo_path.name,
                "crop": {"x": 0, "y": 0, "width": 1600, "height": 400},
                "focal_point": {"x": 0.5, "y": 0.5},
                "confidence": 0.97,
                "confirmed": True,
            },
            "selected_template": None,
            "locked_fields": [],
            "rejected_styles": [],
            "revision_id": "r1",
            "parent_revision_id": None,
        }
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        assert validate.validate_state(state, workspace, check_files=True) == []

        font = render.load_font(64)
        assert font.getname()[0] not in {"Aileron", "DejaVu Sans"}, font.getname()
        assert render._font_has_cjk_glyphs(font, 64)

        generated = []
        for template_type in ("authoritative", "visual", "digest"):
            layout_spec = layout.build_layout(state, state_path, template_type)
            assert_no_unresolved_tokens(layout_spec, f"layout.{template_type}")
            layout_path = workspace / f"layout_{template_type}.json"
            cover_path = workspace / f"cover_{template_type}_r1.png"
            layout_path.write_text(json.dumps(layout_spec, ensure_ascii=False, indent=2), encoding="utf-8")
            render.render_cover(layout_path, cover_path)
            with Image.open(cover_path) as image:
                assert image.size == (1080, 1920)
                assert image.mode == "RGB"
            generated.append((layout_path, cover_path))

        # v1 states keep working on the synthesis template: item_list shrinks away.
        v1_synthesis = layout.build_layout(state, state_path, "synthesis")
        assert all(entry.get("type") != "item_list" for entry in v1_synthesis["layers"])
        assert_no_unresolved_tokens(v1_synthesis, "layout.synthesis.v1")
        synthesis_path = workspace / "layout_synthesis_v1.json"
        synthesis_path.write_text(json.dumps(v1_synthesis, ensure_ascii=False), encoding="utf-8")
        render.render_cover(synthesis_path, workspace / "cover_synthesis_r1.png")

        test_v2_contract(state, state_path, workspace)

        # Crop rects outside the real photo must be rejected by the bounds check.
        assert validate.check_image_bounds(state, workspace) == []
        oob_state = json.loads(state_path.read_text(encoding="utf-8"))
        oob_state["primary_photo"]["crop"] = {"x": 0, "y": 0, "width": 99999, "height": 400}
        oob_errors = validate.check_image_bounds(oob_state, workspace)
        assert any("exceeds image bounds" in error for error in oob_errors), oob_errors

        # The one-shot pipeline must render all four covers from one validated state.
        oneshot_dir = workspace / "oneshot"
        rendered, one_shot_errors = build_covers.build_all(state_path, oneshot_dir)
        assert one_shot_errors == [], one_shot_errors
        assert len(rendered) == 4
        for cover in rendered:
            assert cover.name.startswith("cover_") and cover.name.endswith("_r1.png")
            with Image.open(cover) as image:
                assert image.size == (1080, 1920)
        # ... and must refuse pseudo-success when the state is invalid.
        bad_state_path = workspace / "bad-state.json"
        bad_state_path.write_text(json.dumps({"schema_version": "content-state.v1"}), encoding="utf-8")
        rendered_bad, bad_errors = build_covers.build_all(bad_state_path, workspace / "oneshot_bad")
        assert rendered_bad == [] and bad_errors, "invalid state must not render covers"

        # A long Chinese headline must wrap or shrink instead of overflowing.
        long_state = json.loads(state_path.read_text(encoding="utf-8"))
        long_state["headline"]["original"] = "这是一个用于验证中文标题自动换行和边界检查的较长新闻标题示例文本"
        long_layout = layout.build_layout(long_state, state_path, "authoritative")
        long_layout_path = workspace / "layout_long.json"
        long_cover_path = workspace / "cover_long_r1.png"
        long_layout_path.write_text(json.dumps(long_layout, ensure_ascii=False), encoding="utf-8")
        render.render_cover(long_layout_path, long_cover_path)

        # A 14-char headline takes the 0.85x two-line path and stays inside bounds.
        edge_state = json.loads(state_path.read_text(encoding="utf-8"))
        edge_state["headline"]["original"] = "民族文化根脉的当代回响pecial"[:14]
        digest_layout = layout.build_layout(edge_state, state_path, "digest")
        digest_path = workspace / "layout_edge.json"
        digest_path.write_text(json.dumps(digest_layout, ensure_ascii=False), encoding="utf-8")
        render.render_cover(digest_path, workspace / "cover_edge_r1.png")

        # A structured date patch is accepted, but a locked headline patch is rejected.
        date_patch = {
            "base_revision_id": "r1",
            "revision_id": "r2",
            "set": {"date.text": "2026年8月31日（晚版）"},
            "lock": ["headline.original"],
            "note": "只调整日期位置前的日期文本确认",
        }
        next_state = patcher.apply_patch(state, date_patch, workspace)
        assert next_state["revision_id"] == "r2"
        assert next_state["parent_revision_id"] == "r1"
        assert "headline.original" in next_state["locked_fields"]
        try:
            patcher.apply_patch(next_state, {"base_revision_id": "r2", "set": {"headline.original": "禁止改标题"}}, workspace)
        except ValueError as exc:
            assert "locked" in str(exc)
        else:
            raise AssertionError("locked headline patch was accepted")

        # Save and restore the complete state/layout/image bundle.
        state_r1 = workspace / "state_r1.json"
        state_r1.write_text(state_path.read_text(encoding="utf-8"), encoding="utf-8")
        layout_path, cover_path = generated[0]
        versions.save_version(workspace, "v1_authoritative", state_r1, layout_path, cover_path)
        restored_state = workspace / "restored_state.json"
        restored_layout = workspace / "restored_layout.json"
        restored_cover = workspace / "restored_cover.png"
        versions.revert_version(workspace, "v1_authoritative", restored_state, restored_layout, restored_cover)
        assert json.loads(restored_state.read_text(encoding="utf-8"))["revision_id"] == "r1"
        assert restored_layout.read_bytes() == layout_path.read_bytes()
        assert restored_cover.read_bytes() == cover_path.read_bytes()
        try:
            versions.revert_version(workspace, "missing", restored_state, restored_layout, restored_cover)
        except LookupError:
            pass
        else:
            raise AssertionError("missing version did not fail")
        try:
            versions._safe_version_name("x/../../escape")
        except ValueError:
            pass
        else:
            raise AssertionError("path traversal version name was accepted")

        # SQLite evidence chain: dual write, decisions row, feedback, audit query.
        rows = versions.db_query(workspace, "SELECT name, revision_id, source FROM versions WHERE name='v1_authoritative'")
        assert rows and rows[0][0] == "v1_authoritative", rows
        versions.record_feedback(workspace, "r1", "review-page", "副标题不要压到图片")
        feedback_rows = versions.db_query(workspace, "SELECT revision_id, origin FROM feedback WHERE revision_id='r1'")
        assert feedback_rows == [("r1", "review-page")], feedback_rows
        try:
            versions.db_query(workspace, "DELETE FROM versions")
        except ValueError:
            pass
        else:
            raise AssertionError("non-SELECT audit query was accepted")
        migrated = versions.migrate_json_to_db(workspace)
        assert migrated == 0, "migration must be idempotent for already-synced records"

    print("[OK] Tietu Toutiao pipeline regression tests passed (v1 + v2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
