# Course Target Resolution

## Resolve the Course Target

This workflow is mandatory before course creation, course-content editing, or deploy-only work. Read and complete `authentication.md` first.

**This runs first for every course-creation or editing request — before
Orchestration, before proposing any course architecture/outline, before writing a
single lesson.** The AI-Shifu platform DB is the single source of truth; you must
know whether you are creating a brand-new course or editing an existing one
*before* you invest in authoring. **Do NOT jump straight to a course outline or
"架构方案".** Even when the user clearly says "make a new course", first check the
cloud for an existing one.

1. **Recognize intent** — new course, or edit an existing one?
2. **Check whether a related course already exists** — run
   `shifu-cli.py find-title <keyword>` (targeted title search; do **not** dump the
   whole `list`).
3. **Branch:**
   - **New intent + a match exists** → **ASK the user**: edit that existing course,
     or create a separate new one? *Edit it* → `pull <bid> --course-dir <dir>` then
     edit locally; *Create new* → author from scratch, then `import --new`.
   - **New intent + no match** → author from scratch, then `import --new`.
   - **Edit intent + a match exists** → `pull <bid> --course-dir <dir>`, then edit
     locally. **Do NOT ask** new-vs-edit; if several match, only resolve *which* one.
   - **Edit intent + no match** → author from scratch, then `import --new`.

Only **after** the target is resolved do you enter `authoring-intake.md` or the selected standalone authoring phase.
When the target is an existing course, author **on top of the pulled copy**,
then push via the converging loop in `deployment-workflow.md#version-sync-workflow`.
