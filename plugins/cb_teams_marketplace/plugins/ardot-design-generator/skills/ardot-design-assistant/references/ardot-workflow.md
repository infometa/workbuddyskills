# Ardot MCP Tool Usage Guide — Complete Reference

This document provides end-to-end workflow examples. For design rules, property constraints, troubleshooting, and the full **Tiered Validation / Convergence Threshold** spec, see `design-rules.md`.

> **Three reminders** before reading the examples:
> 1. **File-open gate** — `create_design` / `open_design` must complete and the ready context update must arrive **before** any other MCP call. Never bundle them with reads in the same message.
> 2. **Parallelize independent reads** — when a step contains multiple calls with no mutual data dependency, issue them in a single message as parallel tool calls; do not serialize them. The examples mark these with `(parallel, single message)`.
> 3. **Validation tiers** — `[T1]`/`[T3]`/`[T4]`/`[T5]` tags mark which validation tier applies to each `batch_edit`. Do **not** run full screenshot+layout after every batch. Cap corrective iterations at 2 per section.

## Ardot MCP Tool Usage Guide

## End-to-End Workflow Examples

### Example A: Creating a New Landing Page

```
Step 0 (message 1):
  create_design / open_design  ← WAIT for ready context update before next message.
  (Never bundle subsequent reads into this same message — the editor is not loaded yet.)

Step 1 — read existing state (skipped for fresh create_design):
  # Fresh file: empty canvas, root "0:1", no variables yet → nothing to read.
  # Opened existing file: call the following (parallel, single message):
  #   fetch_editor_state(includeSchema: false)
  #   fetch_variables

Step 2: Load references/guidelines-landing-page.md → learn landing page design rules
        Read ../../rules/style-guide-tags.md → pick 5–10 fitting tags for Step 4.

Steps 4–6 (parallel, single message):
  fetch_style_guide(tags: ["modern", "minimal", "website", ...])
  locate_available_space(width: 1440, height: 3000)
  # Do NOT call fetch_style_guide_tags — the tag list is static,
  # already read from ../../rules/style-guide-tags.md in Step 2.

Step 7: batch_edit → page frame + hero scaffold (structural)      [T1]
        → capture_layout(heroId, problemsOnly: true)              (skip screenshot)
Step 8: batch_edit → hero content + styling (visual)              [T3]
        → capture_screenshot(nodeIds: [heroId])                   (skip layout)
Step 9: batch_edit → features section scaffold + content + style  [T4, section complete]
        → capture_screenshot + capture_layout(problemsOnly: true) (once)
Step 10: batch_edit → footer + CTA sections                       [T4, section complete]
        → capture_screenshot + capture_layout(problemsOnly: true) (once)
Step 11: IF any real issues accumulated → ONE batch_edit fixing all of them
        → re-run only the tier that flagged them
        (Max 2 fix iterations per section; ignore ≤4px spacing noise.)
Step 12: capture_screenshot(full page)                            [T5, final]
```

Notes:
- For a freshly created file this whole flow is **2 read round-trips** (Step 2's local file read + Steps 4–6 parallel batch) before the first `batch_edit`.
- For an opened existing file it's **3 read round-trips** (Step 1 parallel + Step 2 local read + Steps 4–6 parallel).
- Do not screenshot between T2 (pure content) or consecutive T3 batches — defer to the section boundary.
- Skip Step 11 entirely if T4 checks came back clean.

### Example B: Modifying an Existing Design

```
Step 0: Ensure design file is open → skip if editor already has a file loaded
Step 1: fetch_editor_state(includeSchema: false) → check current state and selection
Step 2: batch_read(patterns: [{name: "Header"}]) → find target elements
Step 3: capture_layout(parentId: "headerId", maxDepth: 2) → inspect current layout
Step 4: capture_screenshot(nodeIds: ["headerId"]) → visually check current state
Step 5: batch_edit → apply modifications (≤25 ops)
Step 6: capture_screenshot(nodeIds: [...]) → verify changes (batch all target nodes in one call)
```

### Example C: Global Style Update

```
Step 0: Ensure design file is open → skip if editor already has a file loaded
Step 1: fetch_editor_state(includeSchema: false) → check current state
Step 2: scan_all_unique_properties(parentIds: ["rootFrame"]) → audit existing styles
Step 3: substitute_all_matching_properties → bulk update matching properties
Step 4: capture_screenshot → verify the global changes            [T3]
        (No capture_layout — substitutions don't change structure.)
```

### Example D: Setting Up Design Tokens

```
Step 0: Ensure design file is open → skip if editor already has a file loaded
Step 1: fetch_editor_state(includeSchema: false) → check current state
Step 2: fetch_variables → inspect existing variables
Step 3: apply_variables → create or update variable sets with Light/Dark modes
Step 4: batch_read(patterns: [{reusable: true}]) → find components to bind variables to
Step 5: batch_edit → bind variable references to component properties   [T2]
        (Token binding alone doesn't change visuals or structure — skip validation.
         If a subsequent visual batch follows, validate there instead.)
```

### Example E: Creating a Registration Form

```
Step 0: Ensure design file is open → create_design / open_design if needed, wait for ready
Step 1: fetch_editor_state(includeSchema: false) → get available components
Step 2: batch_edit → container frame + title + inputs in ONE batch   [T4 small form]
  container=I(document, {type: "frame", name: "Registration", layout: "vertical", width: 400, height: "hug_contents(600)"})
  title=I("containerId", {type: "text", name: "Title", content: "Create Account", fontSize: 28, fill: "#18191C"})
  input1=I("containerId", {type: "ref", ref: "InputComponentId"})
  U(input1+"/label", {content: "First Name"})
  ... (remaining fields, submit button, all in the same batch_edit)
Step 3: capture_screenshot + capture_layout(problemsOnly: true)      (once)
Step 4: IF issues → ONE batch_edit fixing all → re-run same tier (max 2 iterations)
```

Notes:
- Small self-contained UIs like a form should be built in **one** batch when ≤25 ops allow, then validated once — not scaffolded, content-filled, and styled in separate round-trips.

