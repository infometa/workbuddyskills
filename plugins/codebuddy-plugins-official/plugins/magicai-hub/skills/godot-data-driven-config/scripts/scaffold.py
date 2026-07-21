#!/usr/bin/env python3
"""
godot-data-driven-config · scaffold.py

Reads a JSON field-spec (see ../schemas/field_spec.schema.json) and emits/updates:
  <project>/data/specs/<name>.spec.json       (copy of the spec — source of truth)
  <project>/data/resources/<name>_data.gd     (only if absent or --force-class)
  <project>/data/<name>s/default_<name>.tres  (only if absent or --force-tres)
  <project>/data/resources/data_manager.gd    (rebuilt from ALL specs on disk)
  <project>/tools/validate_data.gd            (rebuilt from ALL specs on disk)
  <project>/tools/validate_data.sh            (copied)
  <project>/project.godot                     (autoload patched idempotently)

The crucial design choice: specs are persisted under data/specs/*.spec.json.
Every invocation re-scans that directory to rebuild data_manager.gd and
validate_data.gd, so no category is ever "forgotten" and the default_id of a
previously-added category cannot be lost.

Usage:
  python3 scaffold.py --project-root /abs/path --spec path/to/weapon_spec.json
  python3 scaffold.py --project-root /abs/path --spec path/to/enemy_spec.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES = SKILL_DIR / "templates"

SAFE_WORDS = {"and", "or", "not", "true", "false", "null", "if", "else"}

# ---------------- helpers ----------------

def title_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))

def plural(name: str) -> str:
    if name.endswith("y") and not name.endswith(("ay", "ey", "iy", "oy", "uy")):
        return name[:-1] + "ies"
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    return name + "s"

def format_default(field: dict) -> str:
    t = field["type"]
    d = field.get("default")
    if d is None:
        return {
            "bool": "false", "int": "0", "float": "0.0",
            "String": '""', "StringName": '&""',
            "Vector2": "Vector2.ZERO", "Vector3": "Vector3.ZERO",
            "Color": "Color.WHITE", "NodePath": "NodePath()",
            "PackedScene": "null", "Texture2D": "null", "AudioStream": "null",
            "Resource": "null", "Array": "[]", "Dictionary": "{}",
        }.get(t, "null")
    return str(d)

def render_field(field: dict) -> str:
    lines: list[str] = []
    key = field["key"]
    t = field["type"]
    default = format_default(field)

    if field.get("doc"):
        lines.append(f"## {field['doc']}")

    attr = "@export"
    if t in ("float", "int") and "range" in field:
        rng = field["range"]
        step = rng[2] if len(rng) > 2 else (0.1 if t == "float" else 1)
        def fmt(v):  # keep integer-looking ints as ints, floats as floats
            return f"{v}"
        attr = f"@export_range({fmt(rng[0])}, {fmt(rng[1])}, {fmt(step)})"
    elif t == "String" and field.get("multiline"):
        attr = "@export_multiline"

    lines.append(f"{attr} var {key}: {t} = {default}")
    return "\n".join(lines)

def render_fields(fields: list[dict]) -> str:
    out: list[str] = []
    current_group: str | None = None
    for f in fields:
        g = f.get("group")
        if g != current_group:
            if g:
                out.append(f'\n@export_group("{g}")')
            current_group = g
        out.append(render_field(f))
    return "\n".join(out)

def render_tres_props(fields: list[dict]) -> str:
    return "\n".join(f"{f['key']} = {format_default(f)}" for f in fields)

def validator_func_body(name: str, validators: list[str]) -> str:
    """Generate a static-style function body returning a list of error strings."""
    if not validators:
        return f'\t\t"{name}":\n\t\t\treturn []'
    lines = [f'\t\t"{name}":', "\t\t\tvar errs: Array = []"]
    for v in validators:
        # Rewrite bare field names -> res.field_name access with null-safety via res.get().
        def rewrite(match: re.Match) -> str:
            word = match.group(1)
            if word in SAFE_WORDS:
                return word
            # Numeric literals
            if word[0].isdigit():
                return word
            return f'res.get("{word}")'
        # Be conservative: only rewrite identifiers, not numbers.
        expr = re.sub(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", rewrite, v)
        msg = v.replace('"', '\\"')
        lines.append(f'\t\t\tif not ({expr}):')
        lines.append(f'\t\t\t\terrs.append("{msg}")')
    lines.append("\t\t\treturn errs")
    return "\n".join(lines)

# ---------------- generators ----------------

def gen_data_class(spec: dict) -> str:
    tmpl = (TEMPLATES / "data_class.gd.tmpl").read_text()
    return (tmpl
            .replace("{{CLASS_NAME}}", f"{title_case(spec['name'])}Data")
            .replace("{{BASE_CLASS}}", spec.get("base_class", "Resource"))
            .replace("{{DISPLAY}}", spec.get("display", title_case(spec["name"])))
            .replace("{{FIELDS}}", render_fields(spec["fields"])))

def gen_tres(spec: dict) -> str:
    tmpl = (TEMPLATES / "data_resource.tres.tmpl").read_text()
    return (tmpl
            .replace("{{CLASS_NAME}}", f"{title_case(spec['name'])}Data")
            .replace("{{NAME}}", spec["name"])
            .replace("{{PROPS}}", render_tres_props(spec["fields"])))

def build_data_manager(specs: list[dict]) -> str:
    tmpl = (TEMPLATES / "data_manager.gd.tmpl").read_text()
    category_consts: list[str] = []
    category_dicts: list[str] = []
    default_ids: list[str] = []
    reload_body: list[str] = []
    getters: list[str] = []
    validate_body: list[str] = []
    summary_body: list[str] = []

    for spec in specs:
        name = spec["name"]
        class_name = f"{title_case(name)}Data"
        pl = plural(name)
        upper = pl.upper()
        default_id = spec.get("default_id", f"default_{name}")

        category_consts.append(f'const {upper}_DIR := "res://data/{pl}"')
        # Use untyped Dictionary so cold-start without class_cache still parses.
        category_dicts.append(f"var {pl}: Dictionary = {{}}   # StringName -> {class_name}")
        default_ids.append(f'var _default_{name}_id: StringName = &"{default_id}"')
        reload_body.append(f'\t{pl} = _scan_dir({upper}_DIR, "{class_name}")')
        getters.append(
            f"func get_{name}(id: StringName = &\"\") -> Resource:\n"
            f"\tif id == &\"\":\n"
            f"\t\tid = _default_{name}_id\n"
            f"\treturn {pl}.get(id, null)"
        )
        validate_body.append(
            f"\tif {pl}.is_empty():\n"
            f'\t\terrors.append("No {class_name} .tres found in %s" % {upper}_DIR)'
        )
        validate_body.append(
            f"\tif not {pl}.has(_default_{name}_id):\n"
            f'\t\terrors.append("Missing default {name} id: %s" % _default_{name}_id)'
        )
        summary_body.append(f'\tparts.append("{pl}=%d" % {pl}.size())')

    return (tmpl
            .replace("{{CATEGORY_CONSTS}}", "\n".join(category_consts))
            .replace("{{CATEGORY_DICTS}}", "\n".join(category_dicts))
            .replace("{{DEFAULT_IDS}}", "\n".join(default_ids))
            .replace("{{RELOAD_BODY}}", "\n".join(reload_body))
            .replace("{{GETTERS}}", "\n\n\n".join(getters))
            .replace("{{VALIDATE_BODY}}", "\n".join(validate_body))
            .replace("{{SUMMARY_BODY}}", "\n".join(summary_body)))

def build_validator(specs: list[dict]) -> str:
    tmpl = (TEMPLATES / "validate_data.gd.tmpl").read_text()
    cats: list[str] = []
    dispatch: list[str] = []
    for spec in specs:
        name = spec["name"]
        pl = plural(name)
        default_id = spec.get("default_id", f"default_{name}")
        cats.append(f'\t{{"name": "{name}", "dir": "res://data/{pl}", "default": "{default_id}"}},')
        dispatch.append(validator_func_body(name, spec.get("validators", [])))
    return (tmpl
            .replace("{{VALIDATOR_CATEGORIES}}", "\n".join(cats))
            .replace("{{VALIDATOR_CHECKS}}", "")
            .replace("{{VALIDATOR_DISPATCH}}", "\n".join(dispatch) if dispatch else '\t\t_:\n\t\t\treturn []'))

def install_validator_sh(project_root: Path) -> None:
    dst = project_root / "tools" / "validate_data.sh"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPLATES / "validate_data.sh.tmpl", dst)
    dst.chmod(0o755)

# ---------------- spec persistence ----------------

def persist_spec(project_root: Path, spec: dict) -> Path:
    specs_dir = project_root / "data" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    dst = specs_dir / f"{spec['name']}.spec.json"
    dst.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    return dst

def load_all_specs(project_root: Path) -> list[dict]:
    specs_dir = project_root / "data" / "specs"
    if not specs_dir.exists():
        return []
    result: list[dict] = []
    for f in sorted(specs_dir.glob("*.spec.json")):
        try:
            result.append(json.loads(f.read_text()))
        except Exception as e:  # noqa: BLE001
            print(f"[warn] skipping malformed spec {f}: {e}", file=sys.stderr)
    return result

# ---------------- project.godot ----------------

AUTOLOAD_LINE = 'DataManager="*res://data/resources/data_manager.gd"'

def patch_project_godot(project_root: Path) -> None:
    pf = project_root / "project.godot"
    if not pf.exists():
        print(f"[warn] {pf} missing, skipping autoload patch", file=sys.stderr)
        return
    text = pf.read_text()
    if AUTOLOAD_LINE in text:
        return
    if "[autoload]" in text:
        lines = text.splitlines(keepends=True)
        new_lines: list[str] = []
        in_autoload = False
        inserted = False
        for line in lines:
            if in_autoload and not inserted and line.startswith("["):
                new_lines.append(AUTOLOAD_LINE + "\n")
                inserted = True
                in_autoload = False
            new_lines.append(line)
            if line.strip() == "[autoload]":
                in_autoload = True
        if not inserted:
            if not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            new_lines.append(AUTOLOAD_LINE + "\n")
        pf.write_text("".join(new_lines))
    else:
        with pf.open("a") as fp:
            fp.write("\n[autoload]\n" + AUTOLOAD_LINE + "\n")

# ---------------- main ----------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold Godot data-driven config from a JSON spec.")
    ap.add_argument("--project-root", required=True, help="Absolute path to the Godot project root.")
    ap.add_argument("--spec", required=True, help="Path to field-spec JSON.")
    ap.add_argument("--force-tres", action="store_true", help="Overwrite default .tres even if present.")
    ap.add_argument("--force-class", action="store_true", help="Overwrite <name>_data.gd even if present.")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    spec_path = Path(args.spec).resolve()
    if not (project_root / "project.godot").exists():
        print(f"[error] {project_root} is not a Godot project (project.godot missing)", file=sys.stderr)
        return 2
    if not spec_path.exists():
        print(f"[error] spec file not found: {spec_path}", file=sys.stderr)
        return 2

    spec = json.loads(spec_path.read_text())
    if "name" not in spec or "fields" not in spec:
        print(f"[error] spec missing 'name' or 'fields'", file=sys.stderr)
        return 2

    name = spec["name"]
    pl = plural(name)
    default_id = spec.get("default_id", f"default_{name}")

    # 1. persist spec (source of truth)
    persist_spec(project_root, spec)
    print(f"[ok] persisted data/specs/{name}.spec.json")

    # 2. Resource class .gd
    data_class_path = project_root / "data" / "resources" / f"{name}_data.gd"
    data_class_path.parent.mkdir(parents=True, exist_ok=True)
    if args.force_class or not data_class_path.exists():
        data_class_path.write_text(gen_data_class(spec))
        print(f"[ok] wrote {data_class_path.relative_to(project_root)}")
    else:
        print(f"[skip] {data_class_path.relative_to(project_root)} exists (use --force-class to overwrite)")

    # 3. default .tres
    tres_path = project_root / "data" / pl / f"{default_id}.tres"
    tres_path.parent.mkdir(parents=True, exist_ok=True)
    if args.force_tres or not tres_path.exists():
        tres_path.write_text(gen_tres(spec))
        print(f"[ok] wrote {tres_path.relative_to(project_root)}")
    else:
        print(f"[skip] {tres_path.relative_to(project_root)} exists (use --force-tres to overwrite)")

    # 4. rebuild DataManager + validator from ALL specs
    all_specs = load_all_specs(project_root)
    dm_path = project_root / "data" / "resources" / "data_manager.gd"
    dm_path.parent.mkdir(parents=True, exist_ok=True)
    dm_path.write_text(build_data_manager(all_specs))
    print(f"[ok] wrote {dm_path.relative_to(project_root)} with {len(all_specs)} categor(y|ies)")

    val_path = project_root / "tools" / "validate_data.gd"
    val_path.parent.mkdir(parents=True, exist_ok=True)
    val_path.write_text(build_validator(all_specs))
    print(f"[ok] wrote {val_path.relative_to(project_root)}")

    install_validator_sh(project_root)
    print(f"[ok] wrote tools/validate_data.sh")

    # 5. autoload
    patch_project_godot(project_root)
    print("[ok] project.godot autoload confirmed")

    print("\nDone. Next steps:")
    print("  1. If this is a cold checkout:  godot --headless --editor --quit    # refresh class cache")
    print("  2. Validate:                    bash tools/validate_data.sh")
    print("  3. Migrate consumer .gd: add @export var <name>_data with DataManager fallback.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
