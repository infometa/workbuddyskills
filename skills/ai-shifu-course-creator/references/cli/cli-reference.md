# CLI Reference

All commands use `{skillDir}/scripts/shifu-cli.py`. Prefix every call with:

```bash
python3 {skillDir}/scripts/shifu-cli.py <command>
```

## Authentication

Run login once — the token persists in `{skillDir}/.env` for subsequent commands:

```bash
# Step 1: Send SMS verification code
login --phone 13800138000

# Step 2: Complete login with the code
login --phone 13800138000 --sms-code 1234
```

The CLI always talks to `https://app.ai-shifu.cn`. To skip the SMS login, set `--token` / `SHIFU_TOKEN` directly.

### Agent Login Flow

When no valid token is available, guide the user through login. AI-Shifu's SMS login auto-creates an account on first use, so the same flow works for both new and returning users.

Fixed flow: preview + ask for phone → send code → ask for SMS code → complete. Run the steps in order.

Do not ask anything else. No status checks ("have you signed up / logged in before?"), no readiness or intent confirmations ("ready to start?", "I'll provide my phone"), no acknowledgment pauses, no recaps between steps. Each turn collects exactly the next value (phone, then SMS code), nothing else. The Step 1 flow preview is a one-shot heads-up, not a confirmation prompt — do not wait for the user to acknowledge it before asking for the phone.

Steps:

1. In a single turn, give the user a one-line preview of the full flow and then immediately ask for the phone number. Cover all of these in the preview: (a) SMS login, no password; (b) a 4-digit code will be sent to the phone; (c) the user replies with the code in the next turn; (d) on success the token is saved locally and login is complete; (e) new phone numbers auto-create an account on first use. Keep it brief — one or two sentences total — then ask for the phone in the same reply.
2. Send SMS code:
   `python3 {skillDir}/scripts/shifu-cli.py login --phone <phone>`
3. Ask the user for the 4-digit verification code they received.
4. Complete login:
   `python3 {skillDir}/scripts/shifu-cli.py login --phone <phone> --sms-code <4-digit-code>`
5. Token is automatically saved — proceed with the requested operation.

Always use CLI commands. Never make raw HTTP/API calls directly.

## Query Commands

```bash
list                                          # List all courses
show <shifu_bid>                              # Show course details + outline tree
show <shifu_bid> <outline_bid>                # Read a lesson's Teaching Prompt
history <shifu_bid> <outline_bid>             # Teaching Prompt revision history
export <shifu_bid> [-o file.json]             # Export course as JSON
```

`show` (without `outline_bid`), `create`, `import`, and `publish` all print a `Verification URLs:` block. Lines included depend on the command: `publish` and `show` add a `Published URL:` line (the public student-facing address — `<base>/c/<bid>` without `preview=true`); `create` and `import` omit it because the course is not yet published. Each URL is followed by a one-line `# ...` Chinese hint about its purpose. Per-lesson preview URLs are no longer printed — if you need one, use `show <shifu_bid>` to find the `outline_bid` and build `<base>/c/<bid>?preview=true&lessonid=<outline_bid>` on demand. Copy printed URLs as-is when reporting; never reconstruct them from a template.

## Analytics Query

```bash
analytics-query <shifu_bid> --dsl '<json>'        # Inline DSL body
analytics-query <shifu_bid> --dsl-file query.json # DSL body from a JSON file
```

Runs a DSL query against the creator-analytics endpoint and prints the full JSON response (success rows or business error code) to stdout. The CLI handles authentication headers automatically — never call the endpoint directly.

The `shifu_bid` positional argument is injected into the body; if the DSL JSON already carries a `shifu_bid`, it must match the positional argument.

Exit codes:
- `0` — API responded with `code == 0` (the response carries `data.columns` / `data.rows`).
- `1` — transport failure, JSON parse failure, or business error code (e.g. `11001` no access to course, `11002`-`11007` invalid DSL, `1001` / `1004` / `1005` token expired or missing).

The full response is always printed to stdout regardless of exit code, so the agent can read the error code and either fix the DSL or guide the user to re-login. The CLI deliberately does not exit before printing analytics business errors.

Use this command in conjunction with the analytics references in `references/analytics/` — never construct raw HTTP calls.

## Create Commands

```bash
create --name "Title" [--description "Desc"]
add-chapter <shifu_bid> --name "Chapter Name"
add-lesson <shifu_bid> --name "Name" --teaching-prompt-file lesson.md --parent-bid <chapter_bid>
```

## Update Commands

```bash
update-meta <shifu_bid> [--name "..."] [--description "..."] [--course-prompt-file prompt.md]
update-lesson <shifu_bid> <outline_bid> --teaching-prompt-file lesson.md   # Uses optimistic locking
rename-lesson <shifu_bid> <outline_bid> --name "New Name"
reorder <shifu_bid> --order bid1,bid2,bid3
```

`update-lesson` fetches the current revision before saving. If another user modified the lesson since you last read it, the server returns a conflict.

## Delete Commands

```bash
delete-lesson <shifu_bid> <outline_bid>
```

## Bulk Import

```bash
# Flat JSON import
import <shifu_bid> --json-file course.json
import --new --json-file course.json

# One-step build + import from course directory
import <shifu_bid> --course-dir ./course-a/ [--title "..."] [--chapter-name "..."]
import --new --course-dir ./course-a/ [--title "..."] [--chapter-name "..."]

# Local build only (offline, generates shifu-import.json)
build --course-dir ./course-a/ [-o shifu-import.json] [--title "..."] [--chapter-name "..."]
```

The `build` command works entirely offline — it reads the course directory's Teaching Prompts (one MarkdownFlow file per lesson under `lessons/`) and the Course Prompt, then produces `shifu-import.json` without any network calls. The `import --course-dir` option combines build + import in one step.

Build behavior:

- **Course title** resolution order: `--title` CLI arg -> first heading in `README.md` -> directory name
- **Chapter structure**: if `structure.json` exists, generates multi-chapter structure per its definition; otherwise creates a single chapter (named via `--chapter-name` or defaults to course title) containing all `lesson-*.md` files in sorted order
- **Lesson title** resolution order: `title` field in `structure.json` -> `lesson_title: ...` line in the Teaching Prompt -> filename derived (e.g., `lesson-01.md` -> "Lesson 01")

## Image Upload

```bash
# Local file: preprocessed locally (max side 2048 px, ≤ 2 MB, JPEG q=85 / PNG when alpha)
upload-image --file <local-path> [--course-dir <dir>] [--alt "<description>"]

# Remote URL: backend downloads and re-hosts; no local preprocessing
upload-image --url <http(s)-url> [--course-dir <dir>] [--alt "<description>"]
```

Stdout is **one line** — the resulting `https://resource.ai-shifu.cn/<uuid32>` URL. Diagnostic / manifest messages go to stderr, so a shell pipeline can capture the URL cleanly:

```bash
URL=$(python3 scripts/shifu-cli.py upload-image --file diagram.png --course-dir ./my-course/ --alt "Transformer 单层结构")
```

Behavior:

- `--file`: opens with Pillow (HEIC/HEIF via `pillow-heif`), corrects EXIF orientation, downscales to longest-side 2048 px, recompresses JPEG until ≤ 2 MB; transparent images output PNG. Non-image inputs (e.g. `.pdf`, `.txt`) raise an error in the preprocessing stage and exit with code 1.
- `--url`: posts directly to `/api/shifu/url-upfile`; the backend validates the response is `image/*` and re-hosts the file.
- `--course-dir`: when provided, an entry is upserted into `<course-dir>/assets/image-manifest.json` keyed by `local` (for file uploads) or `source_url` (for URL uploads). Re-uploading the same path updates the entry rather than appending.
- `--alt`: short description of what the image conveys; stored in the manifest for review and for later authoring of MarkdownFlow alt text. The LLM should still write a context-appropriate alt when embedding the image — `--alt` is the source of truth, not the final rendered text.
- `--no-process` (debug only): skip preprocessing and upload bytes as-is. Use only when investigating a backend issue; will fail for HEIC and oversize files.

Dependencies: `Pillow`, `pillow-heif`. First-run failures suggest `pip install -r scripts/requirements.txt`.

For the embedding rules once you have a URL, see `references/markdownflow.md#images`.

## State Management

```bash
publish <shifu_bid>       # Publish course (makes it live)
archive <shifu_bid>       # Archive course
unarchive <shifu_bid>     # Restore archived course
```

## CLI Output & Encoding

### Known issue: Chinese characters garbled in agent environments

When running CLI commands (especially `list` and `show`) from an agent's Bash tool, Chinese characters in stdout may appear garbled (mojibake) even with `PYTHONIOENCODING=utf-8` set. This is caused by the agent's subprocess pipe not inheriting the correct locale settings.

**Recommended workaround** — write JSON output to a UTF-8 file, then read it with the agent's file-reading tool:

```bash
# Instead of reading garbled stdout directly:
python3 scripts/shifu-cli.py analytics-query <bid> --dsl '<json>' > /tmp/shifu_result.json
# Then read /tmp/shifu_result.json with the agent's file reader
```

For `list` and `show`, which output formatted tables (not JSON), pipe through a JSON serialization helper or redirect to file:

```bash
python3 -c "
import subprocess, json, sys
result = subprocess.run(
    ['python3', 'scripts/shifu-cli.py', 'show', '<bid>'],
    capture_output=True, text=True, encoding='utf-8'
)
print(result.stdout)
" > /tmp/shifu_show.txt
```

### For analytics-query and credit-detail

These already output JSON via `json.dumps(ensure_ascii=False)`, so they work correctly when redirected to a file. The garbling only affects the pipe encoding — the JSON data itself is UTF-8.

### Token persistence

The token is saved to `{skillDir}/.env` after a successful login. Subsequent commands automatically read it. If the token expires (error codes `1001` / `1004` / `1005`), re-run the login flow — the token file is overwritten in place.
