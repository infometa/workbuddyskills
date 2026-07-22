# Course Author Report Template

Use the section matching the executed phase. Omit sections for phases not run.

## Required References

- `language-policy.md`

## Formatting Rules

These rules apply to every report produced from this template and to any other user-visible chat output that includes URLs.

- **Report language.** Apply the required Language Policy to every human-readable report value and preserve its excluded literals.
- **Links must be Markdown, never bare URLs.** Whenever you show a URL to the user (admin console, course preview, contact page, etc.), wrap it in Markdown link syntax `[descriptive text](URL)`. Never emit a bare `https://...` on its own line.
- **Why:** the AI-Shifu chat client only treats Markdown links as clickable / copy-on-tap. A bare URL renders as plain text — the user cannot click it and cannot copy it cleanly on mobile.
- **Where this applies:** phase reports below, the opening introduction, contact mentions, and any ad-hoc message that surfaces a URL to the user.
- **Where this does NOT apply:** URLs inside Teaching Prompts (those follow MarkdownFlow image / link rules) and URLs shown inside fenced code blocks for reference.
- **Exception — deployment / management Verification URLs.** When transcribing a `Verification URLs:` block supplied by the active workflow, emit each URL as **three lines**:
  1. A Markdown link — `[<course name> - <localized purpose label>](<URL>)`
  2. The same URL again on its own line (intentionally bare), indented two spaces — so the user can long-press / select to copy it cleanly.
  3. The script's following Chinese `# ...` hint, copied verbatim without the leading `#`. The bare URL on line 2 is the only place a bare URL is allowed; it exists because copying out of a rendered Markdown link is unreliable on some clients. The script-owned Chinese hint on line 3 is a verbatim-output exception to the report-language rule; do not translate or rewrite it.

## Segmentation Report

- Source files:
- Processing mode: `standard|fallback`
- Total segments:
- Lesson candidates:
- Immutable blocks preserved:

Validation:

- Source span traceability: `pass|fail`
- Immutable block preservation: `pass|fail`
- One-core-question lesson check: `pass|fail`

Issues:

- Blocking issues:
- Non-blocking suggestions:

Next actions:

- Targeted reruns:
- Downstream handoff notes:

## Orchestration Report

- Input set:
- Execution mode: `standard|fallback`
- Constraints:
- Lesson files generated:
- Course index status:
- Variable table status:

Gate results:

- Preservation gate: `pass|fail`
- One-core-question gate: `pass|fail`
- Interaction safety gate: `pass|fail`
- Variable safety gate: `pass|fail`

Issues:

- Blocking issues:
- Suggestions:

Rerun plan:

- Lessons to rerun:
- Dependency-linked lessons:

## Generation Report

- Lesson id:
- Execution mode: `standard|fallback`
- Constraints:
- Teaching Prompt generated: `yes|no`
- Interaction count:
- Variables used:

Validation:

- Syntax validity: `pass|fail`
- Variable safety: `pass|fail`
- Visual-text coordination: `pass|fail`
- Teaching loop completeness: `pass|fail`

Issues:

- Blocking issues:
- Suggestions:

Follow-up:

- Rerun needed: `yes|no`
- Upstream dependency notes:

## Optimization Report

- Target Teaching Prompt(s):
- Target Course Prompt:
- Target course description:
- Source material set:
- Execution mode: `standard|fallback`
- Overall risk: `low|medium|high`

Issue breakdown:

- Coverage gaps:
- Meaning shifts:
- Interaction issues:
- Visual issues:
- Variable/syntax issues:

Changes applied:

- File references:
- Minimal-edit rationale:

Validation:

- Syntax check: `pass|fail`
- Variable safety check: `pass|fail`
- Interaction branching check: `pass|fail`
- Density preservation check: `pass|fail`
- Artifact envelope/schema check: `pass|fail|not-assessed`
- Checks not assessed:

## Deployment Report

- Course directory:
- Build result: `success|fail`
- Import result: `success|fail`
- Shifu BID:
- Lesson count imported:
- Publish result: `success|fail`

Validation:

- Import without errors: `pass|fail`
- Course accessible via URL: `pass|fail`
- Lesson count matches source: `pass|fail`
- Preview mode reachable: `pass|fail`

Verification URLs:

Use exactly the entries supplied by the active workflow's `Verification URLs:` block. Do not add, omit, reconstruct, or edit any URL. Render each supplied URL as three lines per the Formatting Rules exception; use the supplied purpose to choose the localized link label, and copy the following `# ...` hint without the leading `#` or surrounding indentation.

The fenced snippets below are illustrative templates only. In the generated report, emit their three content lines as ordinary Markdown without the surrounding fence so the first line remains clickable.

- `Admin console:`

  <!-- prettier-ignore -->
  ```md
  - [<course name> - <localized admin-console label>](<URL from script>)
    <URL from script>
    <Chinese hint copied verbatim from the script output, without "#">
  ```

- `Course preview:`

  <!-- prettier-ignore -->
  ```md
  - [<course name> - <localized course-preview label>](<URL from script>)
    <URL from script>
    <Chinese hint copied verbatim from the script output, without "#">
  ```

- `Published URL:`

  <!-- prettier-ignore -->
  ```md
  - [<course name> - <localized published-course label>](<URL from script>)
    <URL from script>
    <Chinese hint copied verbatim from the script output, without "#">
  ```

Omit every URL field that the workflow did not supply.
