---
name: godot-asset-path-surgery
description: Fix stale absolute paths baked inside Godot binary resources (.mesh / .material / .scn / .res / .tres) after a folder rename, migration, or Phase-3-style restructure. Use this skill whenever the user reports editor errors like "Cannot open file 'res://<old path>'", "Failed loading resource", "referenced non-existent resource at", or when they've just moved a folder and the editor console lights up red even though the files exist at the new location. Also use when they ask "how do I rename/move an asset folder in Godot without breaking references".
version: 1.0.0
---

# Godot Asset Path Surgery

> **When to invoke**: user is staring at red errors of the form
> `Cannot open file 'res://old/path/thing.material'` *while the file
> obviously exists at a new path*. This is almost always because a binary
> resource has the old path hard-coded in its payload (Godot bakes
> `ExtResource` paths into `.mesh` / `.material` / `.scn` / compressed
> `.tres` / `.res` at save time).

---

## Core insight

Godot resources carry **two kinds of path information**:

| Kind | Where | Update mechanism |
|---|---|---|
| **Discovery path** (how the editor finds the file) | `.godot/uid_cache.bin`, `<file>.uid` sidecar | Auto-updated by Godot when it sees the file move |
| **Internal ExtResource paths** (who this file references) | **Inside the binary payload** of the file | **Not auto-updated** — the file must be `load()` + `save()` again to rewrite them |

Phase-3-style folder migrations fix kind #1 for free but **silently break kind #2**. Symptom: editor reports broken refs; game often still runs because `load()` can still find the target via UID, but the error panel is polluted and hides real issues.

---

## Decision tree

```
Editor shows: "Cannot open file 'res://<old-path>'"
│
├─ Does the target file exist at the new path?
│  ├─ No  → you actually deleted it. Restore it or fix the reference.
│  └─ Yes → go to next check
│
├─ Is the error coming from a *binary* resource (.mesh/.material/.scn/.res)?
│  ├─ No  → it's a plain .tscn/.tres referencing the old path by text;
│  │       use sed/IDE search-replace on the text file and you're done.
│  └─ Yes → use the surgery pattern below (file's internal payload
│           carries the stale path as UTF-8 bytes).
│
├─ Does the affected binary ALSO depend on another resource that also moved?
│  ├─ No  → Pattern A (simple resave).
│  └─ Yes → Pattern B (shim + reassign + resave), because ResourceLoader
│           refuses to open a file whose ExtResource target is missing.
```

---

## Pattern A — Simple resave (self-contained binary)

**When**: a `.mesh` / `.material` / `.scn` carries a stale *self-path* header
or a stale external path, but the target of that external path still exists
(just at a new location accessible by UID).

```gdscript
# tools/resave_<thing>.gd  -- SceneTree-mode one-shot
extends SceneTree

const PATHS := [
    "res://art/models/<new>/thing.mesh",
    "res://art/models/<new>/thing.material",
]

func _initialize() -> void:
    var failed := 0
    for p in PATHS:
        var res := ResourceLoader.load(p, "", ResourceLoader.CACHE_MODE_IGNORE)
        if res == null:
            push_error("[resave] load failed: %s" % p)
            failed += 1
            continue
        # Force the in-memory resource_path to match the on-disk path so
        # ResourceSaver doesn't keep the stale path baked into the header.
        res.resource_path = p
        # FLAG_COMPRESS preserves the original RSCC compression; without it
        # binary resources (esp. .material) may bloat 3-5x.
        var err := ResourceSaver.save(res, p, ResourceSaver.FLAG_COMPRESS)
        if err != OK:
            push_error("[resave] save failed (%d): %s" % [err, p])
            failed += 1
            continue
        print("[resave] ok: ", p)
    quit(0 if failed == 0 else 1)
```

Run:
```bash
/Applications/Godot.app/Contents/MacOS/Godot --headless --quit \
    --path . --script tools/resave_<thing>.gd
```

---

## Pattern B — Shim + reassign (binary with broken ExtResource)

**When**: the binary resource internally references an `ExtResource` whose
*path* is stale, and Godot refuses to open the binary ("Can't load
dependency"). Pattern A won't work because `ResourceLoader.load()` fails
before you can rewrite the resource.

**Strategy**: temporarily place the dependency's current content at the
*old* path so the loader resolves, retarget the reference to the *new*
path in memory, save, clean up the shim.

```gdscript
# tools/resave_<thing>.gd  -- SceneTree-mode one-shot
extends SceneTree

const DEP_NEW := "res://art/models/<new>/material.material"
const DEP_OLD := "res://old/path/material.material"
const DEP_OLD_DIR := "res://old/path"

const BINARY := "res://art/models/<new>/mesh_with_dep.mesh"

func _initialize() -> void:
    # 1. Pre-load the dep from its real path (the one we want baked in).
    var dep := ResourceLoader.load(DEP_NEW, "", ResourceLoader.CACHE_MODE_REUSE)
    if dep == null:
        push_error("cannot load dep at %s" % DEP_NEW)
        quit(1)
        return

    # 2. Shim: copy dep to the old path so the binary's stale ExtResource resolves.
    var da := DirAccess.open("res://")
    var old_dir_rel := DEP_OLD_DIR.replace("res://", "")
    if not DirAccess.dir_exists_absolute(ProjectSettings.globalize_path(DEP_OLD_DIR)):
        da.make_dir_recursive(old_dir_rel)
    if da.copy(DEP_NEW, DEP_OLD) != OK:
        push_error("temp copy failed")
        quit(1)
        return

    # 3. Now the binary loads. Retarget its material(s) to the canonical
    #    instance whose resource_path is DEP_NEW, not the shim.
    var mesh := ResourceLoader.load(BINARY, "", ResourceLoader.CACHE_MODE_IGNORE) as ArrayMesh
    if mesh != null:
        for i in mesh.get_surface_count():
            mesh.surface_set_material(i, dep)
        mesh.resource_path = BINARY
        ResourceSaver.save(mesh, BINARY, ResourceSaver.FLAG_COMPRESS)
        print("[resave] ok: ", BINARY)

    # 4. Teardown: remove the shim + any dir tree we created.
    da.remove(DEP_OLD)
    _remove_empty_parents_up_to_res(DEP_OLD_DIR)
    quit(0)


func _remove_empty_parents_up_to_res(path: String) -> void:
    var da := DirAccess.open("res://")
    var cur := path
    while cur != "res://" and cur.begins_with("res://"):
        var d := DirAccess.open(cur)
        if d == null: break
        d.list_dir_begin()
        var has_child := false
        while true:
            var n := d.get_next()
            if n == "": break
            if n == "." or n == "..": continue
            has_child = true; break
        d.list_dir_end()
        if has_child: break
        if da.remove(cur) != OK: break
        cur = cur.get_base_dir()
```

Adapt the `surface_set_material()` line to whatever API the binary uses
(e.g. for a PackedScene you'd iterate nodes; for a ShaderMaterial you'd
reassign `shader` or texture params).

---

## Post-surgery verification checklist

Run all three:

1. **No more stale paths in binaries**:
   ```bash
   grep -rln '<old-path-fragment>' . --exclude-dir='.godot'
   ```
   Expected: only your maintenance script (which records the constant).

2. **Headless load smoke test** — drop this into `tools/_smoke.gd` and
   delete after:
   ```gdscript
   extends SceneTree
   func _initialize() -> void:
       var ps := load("res://scenes/.../affected_scene.tscn") as PackedScene
       if ps == null: push_error("FAIL"); quit(1); return
       var inst := ps.instantiate()
       print("OK children=", inst.get_child_count())
       inst.queue_free()
       quit(0)
   ```
   Run:
   ```bash
   /Applications/Godot.app/Contents/MacOS/Godot --headless \
       --path . --script tools/_smoke.gd 2>&1 | grep -E 'ERROR|OK:'
   ```
   Expected: no `ERROR` lines referencing old paths, one `OK children=N`.

3. **Editor visual check** — reopen the editor and watch the error panel.
   For best results: first clear stale caches (see the
   `godot-headless-verify` skill for the safe clean-cache recipe).

---

## Critical gotchas

### Length mismatch kills naive binary sed

```python
# DO NOT DO THIS — it corrupts the file
content = open(f, 'rb').read()
content = content.replace(b'level/textures/Material.material',
                          b'art/models/material.material')  # NEW is longer
open(f, 'wb').write(content)
```

Godot binary resources encode strings as length-prefixed (Pascal-style).
If new path length ≠ old path length, the length prefix still says "51
chars" but the string is now 55 chars — subsequent fields shift, parser
explodes. **Always go through `ResourceLoader`/`ResourceSaver`**, never
touch raw bytes.

### Forgetting `FLAG_COMPRESS`

Default `ResourceSaver.save(res, path)` writes **uncompressed** (`RSRC`
magic). If the original was `RSCC` (compressed), you'll see 3-5x file
bloat. Always pass `ResourceSaver.FLAG_COMPRESS` unless you have a
reason not to.

### `CACHE_MODE_REUSE` vs `CACHE_MODE_IGNORE`

- **IGNORE**: Force a fresh load from disk. Use for the resource you're
  about to mutate and save, so you don't accidentally mutate the editor's
  cached instance.
- **REUSE**: Share with the editor cache. Use for *dependencies* that
  you want other references to keep pointing at.

### `.uid` sidecar

Any new `.gd` file you drop in (like your one-shot `resave_*.gd`) needs a
`.uid` sidecar or the project-specific pre-commit hook will reject the
commit. Generate by running Godot once: `Godot --headless --import --path .`.

---

## Anti-patterns — don't do these

- ❌ **Binary sed**: length mismatch corrupts files (see above).
- ❌ **Duplicate assets at old + new paths**: tempting, but creates two
  copies that diverge. Violates `docs/ASSET_GUIDELINES.md §7`.
- ❌ **Leaving the surgery script in place without telling anyone**:
  mark it clearly as one-shot maintenance, add a header comment
  explaining what bug it fixed (with commit SHA if possible), keep it
  under `tools/` so `check_asset_structure.gd` accepts it.
- ❌ **Running the script without `--headless` first**: user may have the
  editor open, which will race-save stale state back over your fix.

---

## When to NOT use this skill

- **.tscn / .tres text resources**: they're text, do a plain sed or IDE
  global-replace.
- **User can just open-save in editor by hand**: if you're only dealing
  with 1-2 files and the user is comfortable in the editor, point them
  at "FileSystem dock → right-click → Reimport / Save". This skill is
  for 5+ files or when the user wants a reproducible, scripted fix.
- **UID-based references**: Godot 4 uses `uid://...` identifiers that are
  location-independent. If a `.tscn` references `uid://xyz` and the file
  has moved, Godot resolves it via UID cache — no surgery needed, just
  ensure `.godot/uid_cache.bin` is fresh (see `godot-headless-verify`).

---

## Reference: real fix done on TPS demo

Commit `7b94c7b` ("fix(art): rewrite core/*.mesh + Material_001.material
to drop stale Phase 3.6 paths"): after moving `level/textures/structure/Core/`
to `art/models/environment/arena/core/`, 5 binaries still baked the old
path. Script: [`tools/resave_core_meshes.gd`](../../../tools/resave_core_meshes.gd).
Result: 0 editor ERRORs + meshes shrunk 58% thanks to Godot 4.6's newer
compressor.
