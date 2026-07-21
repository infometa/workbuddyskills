---
name: godot-headless-verify
description: Run Godot in headless mode to verify a project — quick load tests ("does this scene still instantiate?"), cache/UID cache repair ("editor shows red errors but game runs fine"), and batch resource operations. Use this skill when the user says things like "clear Godot cache", "editor shows referenced non-existent resource", "verify the project still loads", "run headless validation", "sanity-check after a refactor", or when they ask how to drive Godot from the command line without opening the UI.
version: 1.0.0
---

# Godot Headless Verify & Repair

> A pocket toolkit of **reproducible CLI recipes** for Godot 4 projects.
> Every recipe here is a copy-paste-ready one-liner (or short script) that
> exercises the engine without opening the editor. Use these instead of
> asking the user "can you open the editor and…" — that's slower and
> lossy.

---

## 0. The one-binary convention

Every recipe assumes you can reach Godot via either `$GODOT` env var or
its standard macOS location. Prefix every command with:

```bash
GODOT="${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}"
```

On Linux / Windows, set `$GODOT` to your binary. **Never** hard-code
`godot4` or `/opt/godot/...` in scripts — it breaks across machines.

---

## 1. Recipe: cache clean (safe)

**When**: editor shows `Cannot open file 'res://…'` or
`referenced non-existent resource` *even though the file exists*, typically
after a refactor / folder rename / branch swap.

**Why**: `.godot/imported/` and `.godot/uid_cache.bin` remember pre-move
paths. Godot doesn't self-heal until you force a rebuild.

```bash
# Requires: editor closed.
cd <project-root>

# Safe cache reset — preserves window layout + per-file folding state.
rm -rf .godot/imported \
       .godot/uid_cache.bin \
       .godot/global_script_class_cache.cfg \
       .godot/scene_groups_cache.cfg \
       .godot/editor/filesystem_cache* \
       .godot/editor/filesystem_update_* \
       .godot/editor/filesystem_update[0-9]*
# (zsh note: use `setopt NULL_GLOB` or run in bash if the * patterns
#  don't match anything and zsh complains)

# Rebuild cache headlessly (takes 30s-2min depending on project size).
"$GODOT" --headless --import --path .
```

**Keep these** (do NOT rm):
- `.godot/shader_cache/` — compiled shaders, expensive to rebuild
- `.godot/editor/*-folding-*.cfg` — per-file UI state
- `.godot/editor/editor_layout.cfg` — window layout

---

## 2. Recipe: scene-load smoke test

**When**: you just refactored something and want a 5-second "does it still
load?" answer before bothering with the full editor.

```bash
cat > /tmp/smoke.gd <<'EOF'
extends SceneTree

# Edit the paths you want to smoke-test:
const SCENES := [
    "res://scenes/boot/main.tscn",
    "res://scenes/levels/arena/arena.tscn",
    "res://scenes/levels/forest/forest.tscn",
]

func _initialize() -> void:
    var failed := 0
    for s in SCENES:
        var ps := load(s) as PackedScene
        if ps == null:
            push_error("FAIL load: %s" % s); failed += 1; continue
        var inst := ps.instantiate()
        if inst == null:
            push_error("FAIL instantiate: %s" % s); failed += 1; continue
        print("OK %s (children=%d)" % [s, inst.get_child_count()])
        inst.queue_free()
    quit(0 if failed == 0 else 1)
EOF

GODOT="${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}"
"$GODOT" --headless --path . --script /tmp/smoke.gd \
    2>&1 | grep -E 'ERROR|OK '

rm -f /tmp/smoke.gd
```

**Exit code** is 0 iff every scene loaded. Good for CI.

**Important**: `/tmp/smoke.gd` is outside the project, so Godot can't
resolve `res://` in its own script path. Always pass the full `/tmp/...`
filesystem path via `--script`. Don't put it inside `tools/` without the
matching `.uid` sidecar (pre-commit hook will otherwise complain).

---

## 3. Recipe: script-only parse check

**When**: you edited a bunch of `.gd` files and want to confirm they all
parse without opening the editor.

```bash
# --check-only runs the GDScript parser over all scripts the project
# touches; no scene is instantiated.
"$GODOT" --headless --quit --path . 2>&1 \
    | grep -iE 'SCRIPT ERROR|Parse Error' || echo "all scripts parse OK"
```

Note: `--quit` without a script exits after the engine's first idle frame,
which is enough to trigger script preloading.

---

## 4. Recipe: forced reimport of one folder

**When**: one specific asset got stuck with stale `.import` data but you
don't want a full project reimport.

```bash
# Delete just the .import files under the folder you care about.
# Godot will re-generate them on the next editor open OR headless --import.
find art/models/environment/arena -name '*.import' -delete

"$GODOT" --headless --import --path .
```

Pairs well with the `godot-asset-path-surgery` skill.

---

## 5. Recipe: run an arbitrary maintenance script

**When**: you want to batch-operate on resources (resave, audit, migrate).

Create the script under `tools/` so it's git-tracked and follows the
project's asset-structure rules. Template:

```gdscript
# tools/do_thing.gd
extends SceneTree

## One-shot maintenance: <what this does>.
## Usage:
##   /Applications/Godot.app/Contents/MacOS/Godot --headless --quit \
##       --path . --script tools/do_thing.gd

func _initialize() -> void:
    # ... your work here ...
    # Prefer idempotent ops: the script should be safe to re-run.
    quit(0)  # or quit(1) on failure
```

Checklist before committing:
- [ ] Has a header comment saying what it does and why
- [ ] Is idempotent (safe to re-run) — or prints a warning if not
- [ ] Uses `ResourceLoader.CACHE_MODE_IGNORE` when mutating
- [ ] Uses `ResourceSaver.FLAG_COMPRESS` when saving binaries (.mesh /
      .material / compressed .res) unless you have a reason otherwise
- [ ] Run it once, verify, then **don't delete it** — keep as living
      documentation of the maintenance event
- [ ] After creation, run Godot headless once to generate its `.uid`
      sidecar, then `git add` both files

---

## 6. Recipe: export / build validation

**When**: about to ship, want to confirm export presets still work.

```bash
# List presets defined in export_presets.cfg
grep '^\[preset\.' export_presets.cfg

# Dry-run export (v4.x):
mkdir -p /tmp/godot-export-test
"$GODOT" --headless --export-debug "<preset-name>" \
    /tmp/godot-export-test/game.pck --path .
# Check exit code; inspect .pck size sanity; `rm -rf /tmp/godot-export-test`
```

---

## 7. Common WARNING / ERROR noise (safe to ignore)

| Message | Source | Action |
|---|---|---|
| `ObjectDB instances leaked at exit` | Godot 4.6 cleanup order | Ignore for headless one-shots |
| `WARNING: [fbx] ...` | FBX SDK chatter | Ignore unless it mentions your file |
| `WARNING: Physics interpolation ... possibly benign` | Player runtime-spawned before physics tick | Log as tech debt, ignore at runtime |
| First-run `ERROR: failed loading resource` for every scene on an empty cache | Cache still rebuilding | Re-run after `--import` completes |

If you see an error that's **not** in this table and **not** trivial,
escalate — don't just swallow it.

---

## 8. CI / automation one-liner

The most common "I want to gate my PR on headless validity":

```bash
#!/usr/bin/env bash
set -euo pipefail
GODOT="${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}"
cd "$(dirname "$0")/.."

# 1. Structure check (project-specific).
bash tools/check_asset_structure.sh

# 2. Data-table validation (if using godot-data-driven-config skill).
[ -f tools/validate_data.sh ] && bash tools/validate_data.sh

# 3. Scene smoke test.
"$GODOT" --headless --path . --script tools/smoke.gd

# 4. No stale WARNING/ERROR on first-party code.
"$GODOT" --headless --quit --path . 2>&1 \
    | grep -iE 'SCRIPT ERROR|Parse Error' \
    && { echo "first-party script errors detected"; exit 1; } \
    || echo "clean"
```

---

## Anti-patterns — don't do these

- ❌ **Deleting all of `.godot/`**: wipes `shader_cache/` too → next
  editor open takes 10+ minutes rebuilding shaders.
- ❌ **Running maintenance scripts while the editor is open**: the
  editor will race-save stale in-memory state back over your change.
  Always close the editor first.
- ❌ **Assuming `--quit` waits for the filesystem scan**: it doesn't.
  Use `--import` when you need a complete rescan.
- ❌ **Hard-coding `/Applications/Godot.app/...` in committed scripts**:
  use `${GODOT:-<default>}` so the script works on other machines.
- ❌ **Treating smoke-test output as structured**: it's stderr-heavy,
  always pipe through `grep -E 'ERROR|OK'` before asserting.

---

## Integration with other skills

- **`godot-asset-path-surgery`** — after running surgery, verify with
  this skill's §2 smoke test, then clear cache via §1 before reopening
  the editor.
- **`godot-data-driven-config`** — the validator it generates
  (`tools/validate_data.sh`) is a domain-specific version of §8.
- **`gdscript-codegen`** — after generating new scripts, §3 parse-check
  catches syntax issues before the user opens Godot.
