# Deployment and Course Management

## Deployment

Ship optimized Teaching Prompts to the AI-Shifu platform as live courses. Three distinct actions are involved and should not be conflated:

- **Deploy** — upload local course files to the platform via `build` + `import`. After this the course exists on the platform but is not yet visible to learners on a public URL.
- **Publish** — run `publish` on the platform, which pushes the current draft to the public student-facing URL. Only after this step does `<base>/c/<bid>` (no `preview=true`) work.
- **Sync** — keep a local course directory and the platform draft version-consistent; the platform draft is the single source of truth. Think `git pull` before `git push`. Mechanics: `cli/cli-reference.md#version-sync-pull--status`.

The standard end-to-end flow chains deploy + publish: build → import (deploy) → publish. When **editing an existing course**, use the sync loop instead: **`pull` → edit locally → `status` → `update-lesson` / `import` (push) → `publish`.**

### Prerequisites

- Python 3 with `requests` and `python-dotenv` packages installed.
- CLI script: `{skillDir}/scripts/shifu-cli.py`

### Authentication

Complete `authentication.md` first. Always use CLI commands; never make raw HTTP/API calls directly.

### Course Directory

Teaching Prompts must be organized in a course directory (one MarkdownFlow file per lesson under `lessons/`) before deployment. See `cli/course-directory-spec.md` for the full specification. When continuing from Optimization (Path A), write the optimized Teaching Prompts and Course Prompt into this structure automatically.

**Content vs attributes — the skill changes content, not attributes, by default.**
Content = lesson MarkdownFlow + course name/description/prompt; attributes = each
lesson's learning permission (`access` = 无需登录/试看/付费) and `hidden`, plus
course-level model/price/TTS/Ask/keywords/…. The skill pushes only content, and
the platform backend uses PATCH semantics (any field a write omits is left
unchanged), so iterating content never resets attributes. `pull` writes the
current attributes into `structure.json` and `course-config.json` as a
**read-only reference**. Change attributes only when the user explicitly asks —
`set-access` for a lesson's permission, `set-tts` for course Listen Mode (flags:
`cli/cli-reference.md#update-commands`); other course-level settings
are changed in the platform editor.

**Editing an existing course → use granular non-destructive commands**
(`pull → update-lesson / add-lesson / delete-lesson / reorder / set-access / set-tts`).
The destructive whole-course `import` recreates every outline (a recreated lesson
gets the platform-default permission), so reserve `import --new` for brand-new
courses — do not use it to iterate an existing one.

### CLI Commands

All commands documented in `cli/cli-reference.md` (deployment: `build` / `import` / `publish` / `show`; version sync: `pull` / `status`; management for Path D: `list` / `update-meta` / `update-lesson` / `rename-lesson` / `set-access` / `set-tts` / `reorder` / `delete-lesson` / `archive`). Import JSON schema: `cli/cli-reference.md#import-json-schema`.

### Deployment Workflow

**From pipeline (Path A continuation):**
1. Write Optimization outputs into the course directory: `lessons/lesson-*.md`, `README.md`, `course-description.md` (the generated SEO description; no author-side process notes), `course-prompt.md` (the Optimization `course_prompt` artifact, structured per `course-prompt.md#fillable-template`), and required `structure.json`.
2. Run `build --course-dir <dir>` to generate `shifu-import.json`.
3. **Deploy a new target**: Run `import --new --json-file <dir>/shifu-import.json`. If `course-target.md` resolved an existing target, do not run this command; use the Version Sync Workflow below.
4. **Publish**: Run `publish <shifu_bid>` to push the course to its public student-facing URL.
5. Verify via platform URL.

**Standalone deployment (Path C):**
1. Ensure the course directory is ready: Teaching Prompt files under `lessons/`, a `course-description.md` SEO summary, a `course-prompt.md` (author per `course-prompt.md#fillable-template` first if missing), and `structure.json` (create it if missing). Directories without `course-description.md` still build, but the platform description will be empty unless `--description` is provided.
2. New target: run `build` → `import --new` → `publish`. Existing target: use the Version Sync Workflow.

### Version Sync Workflow

The **front guard** that fixes the target (new-vs-edit, `find-title`,
pulling the existing course) is `course-target.md#resolve-the-course-target` — run it first. This section covers
what happens once the target is an existing course you have pulled: the
**pull → edit → push** loop that converges like `git pull` before `git push`.

1. **`pull <shifu_bid> --course-dir <dir>`** — download the cloud draft into the local dir and record revisions.
2. **Edit locally** — change lesson files / course description / course prompt in place.
3. **`status --course-dir <dir>`** — see what diverged (`behind` / `locally modified` / `new` / `deleted` on server).
4. **Push** with `--course-dir` so the recorded baseline is used: `update-lesson <bid> <ob> --teaching-prompt-file f.md --course-dir <dir>` for a single lesson, or `import <bid> --course-dir <dir>` for the whole course.
5. **`publish <bid>`** when ready for learners.

**Convergence loop on conflict.** A push checks whether the cloud advanced since
your last sync:

- **No newer version → push succeeds (exit 0) → done.** Proceed to `publish`.
- **Newer version → push reports a conflict (exit 2). Exit 2 means "retry", not
  "give up".** The CLI has **already** backed up your un-pushed change,
  auto-pulled the latest cloud copy over local, and printed who changed it and
  when. Then **loop**: re-read the freshly pulled files (the new baseline) →
  re-apply your intended change on top of it (you, the agent, do the merge — the
  CLI never auto-merges content) → run the same push again → **repeat until the
  push succeeds (exit 0)**. Never force the old content back — the cloud is
  authoritative.

Never hand-edit `.shifu-sync.json`, and always push with `--course-dir` —
without it a concurrent edit cannot be detected. Backup file locations and full
mechanics: `cli/cli-reference.md#version-sync-pull--status`.

### Verification

After any deployment or management operation, verify the result:
1. Show the user the verification URLs the script printed — admin console, course preview, and (when the script also printed it) the published public URL. Copy URLs verbatim from the script output and render each as three lines: a Markdown link, a bare URL on the next line for copy-friendliness, and the script's following Chinese `# ...` hint copied verbatim without the leading `#` (per `report-template.md` — Deployment → Verification URLs, plus the top-level Formatting Rules exception). Never reconstruct URLs from a template by hand. Lesson-level URLs are intentionally omitted to keep the report scannable; if the user later asks for a specific lesson link, use `show <shifu_bid>` to find the `outline_bid` and build it on demand.
2. Use `show <shifu_bid>` to get the lesson `outline_bid`, then check each lesson's Teaching Prompt, variable collection, and interaction logic.

### Validation

- Import completes without errors.
- Course is accessible via platform URL.
- Lesson count and structure match the source directory.
- Published course is reachable in preview mode.
