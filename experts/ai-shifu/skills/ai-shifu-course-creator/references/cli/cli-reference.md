# CLI Reference

## Required References

None.

## Invocation

All commands use:

```bash
python3 {skillDir}/scripts/shifu-cli.py <command>
```

Authenticated commands accept `--token <jwt>` and otherwise read `SHIFU_TOKEN` from `{skillDir}/.env`. The CLI always uses `https://app.ai-shifu.cn`.

## Contents

- [Update Check](#update-check)
- [Authentication](#authentication)
- [Query Commands](#query-commands)
- [Analytics Query](#analytics-query)
- [Version Sync](#version-sync-pull--status)
- [Create Commands](#create-commands)
- [Update Commands](#update-commands)
- [Delete Commands](#delete-commands)
- [Bulk Import](#bulk-import)
- [Image Upload](#image-upload)
- [State Management](#state-management)
- [Exit Codes](#exit-codes)
- [CLI Output & Encoding](#cli-output--encoding)

## Update Check

```bash
check-update [--force] [--dev-manifest-url <loopback-url>]
```

`check-update` reads the public Skill-version manifest and prints a compact JSON result. `--force` bypasses the local TTL. `--dev-manifest-url` accepts only a localhost or loopback URL and exists for end-to-end development checks.

## Authentication

```bash
verify
login --phone 13800138000
login --phone 13800138000 --sms-code 1234
```

- `verify` exits `0` when the token is accepted, `1` when it is expired or invalid, and `2` when network, service, or response errors make its state unknown.
- `login --phone` sends an SMS code and exits without prompting.
- `login --phone --sms-code` verifies the code and writes `SHIFU_TOKEN=<jwt>` to `{skillDir}/.env`.
- A saved token is valid for seven days; successful authenticated API calls refresh that expiry.

Agent decisions about when to send or resend SMS are defined in `../authentication.md`; this section defines only CLI inputs and effects.

## Query Commands

```bash
list
show <shifu_bid>
show <shifu_bid> <outline_bid>
history <shifu_bid> <outline_bid>
export <shifu_bid> [-o file.json]
find-title <keyword>
```

- `list` prints all active courses visible to the authenticated creator.
- `show <shifu_bid>` prints course detail and the outline tree. `show <shifu_bid> <outline_bid>` prints one lesson's Teaching Prompt.
- `history` prints one lesson's Teaching Prompt revision history.
- `export` writes course JSON to stdout or the path passed with `-o`.
- `find-title` requires at least two non-whitespace characters, then matches the keyword case-insensitively after whitespace normalization against current draft and published titles. It does not match historical or renamed titles.

`show` without an outline BID prints a `Verification URLs:` block containing admin and preview URLs plus the published URL when available. `create`, `import`, `pull`, and `publish` also print command-appropriate verification URL blocks. Per-lesson preview URLs are not printed.

## Analytics Query

```bash
analytics-query <shifu_bid> --dsl '<json>'
analytics-query <shifu_bid> --dsl-file query.json

credit-detail <shifu_bid> \
  [--start 2026-05-01] [--end 2026-05-15] \
  [--scene 1202,1203] [--usage-type 1101,1102] \
  [--limit 200] [--offset 200]
```

`analytics-query` accepts exactly one of `--dsl` or `--dsl-file`. The positional Shifu BID is injected into the request; an existing `shifu_bid` in the JSON must match it. The complete JSON response is printed to stdout. Exit `0` means business code `0`; exit `1` covers transport, JSON, and nonzero business errors.

`credit-detail` returns JSON containing `summary` and paginated `rows` for the server-side credit detail join. Date bounds are inclusive. `--scene` accepts a comma-separated subset of `1201`, `1202`, and `1203`; `--usage-type` accepts a subset of `1101` and `1102`; `--limit` is `1..1000`; `--offset` defaults to `0`. The summary covers the full filtered set regardless of pagination. Validation, transport, or business errors exit `1`.

## Version Sync (pull / status)

```bash
pull <shifu_bid> --course-dir ./course-a/ [--force]
status --course-dir ./course-a/ [--exit-code]
```

`pull` writes the cloud draft into the course directory: `README.md`, `course-description.md`, `course-prompt.md`, `course-config.json`, lesson files, `structure.json`, and `.shifu-sync.json`. It records course and lesson revision baselines. Before overwriting a divergent local file, it writes `<file>.local-<timestamp>.bak`; `--force` disables these backups.

`status` reads `.shifu-sync.json`, compares it with cloud revisions and local hashes, and reports:

- course metadata behind;
- lesson behind;
- locally modified lesson or course description;
- new lesson on the server;
- lesson deleted on the server.

Without `--exit-code`, divergence is reported while the command exits normally. With `--exit-code`, any divergence exits `1`. A missing sync manifest also exits `1`.

`.shifu-sync.json` is auto-maintained by the CLI. Its schema is defined in `course-directory-spec.md#shifu-syncjson`.

## Create Commands

```bash
create --name "Title" [--description "Desc"]
add-chapter <shifu_bid> --name "Chapter Name"
add-lesson <shifu_bid> --name "Lesson Name" \
  [--teaching-prompt-file lesson.md] --parent-bid <chapter_bid>
```

- `create` creates an empty course and prints its BID and verification URLs.
- `add-chapter` creates one top-level chapter and prints its outline BID.
- `add-lesson` creates a lesson under the required parent chapter and, when a prompt file is provided, saves its MarkdownFlow content.

## Update Commands

```bash
update-meta <shifu_bid> [--name "..."] [--description "..."] \
  [--course-prompt-file prompt.md] [--course-dir ./course-a/]
update-lesson <shifu_bid> <outline_bid> \
  --teaching-prompt-file lesson.md [--course-dir ./course-a/]
rename-lesson <shifu_bid> <outline_bid> --name "New Name"
set-access <shifu_bid> <outline_bid> --access guest|trial|normal \
  [--hidden true|false] [--course-dir ./course-a/]
set-tts <shifu_bid> --enabled true|false [--speed <number>] \
  [--course-dir ./course-a/]
reorder <shifu_bid> --order bid1,bid2,bid3
```

### `update-lesson` and `rename-lesson`

`update-lesson` sends the prompt file as lesson content. With a matching `.shifu-sync.json`, it uses the recorded lesson revision as the optimistic-lock baseline and updates the manifest and local file after success. Without that baseline it uses the current cloud head, so concurrent-edit detection is degraded. On a conflict with `--course-dir`, the CLI saves the attempted content as `<file>.conflict`, pulls the cloud course over local, and exits `2`.

`rename-lesson` sends only the lesson name and preserves omitted lesson fields.

### `update-meta`

The command sends only provided `name`, `description`, and Course Prompt fields. With `--course-dir`, a local `course-description.md` that differs from the sync baseline is also sent. A successful description update refreshes the local file and the recorded course revision. Omitted platform attributes are preserved by backend PATCH semantics.

With a matching sync manifest, the CLI compares the recorded course revision before writing. On conflict it stores the intended metadata in `.shifu-meta.conflict.json`, pulls the cloud course over local, and exits `2`. Without any supplied or locally changed field it prints `Nothing to update` and exits normally.

### `set-access`

The command maps `guest`, `trial`, and `normal` to the platform learning-access value and sends only that value plus optional `is_hidden`. Other lesson fields are preserved. When `--course-dir` is present and the sync mapping exists, the CLI updates the matching entry in `structure.json` as a local side effect.

### `set-tts`

Disabling sends only `tts_enabled=false`. Enabling fetches platform TTS defaults and sends provider, model, voice, speed, normalized pitch `0`, and empty emotion; `--speed` overrides the default. Invalid or incomplete settings exit `1`.

With a matching sync manifest, the command checks the course revision before writing, then refreshes `course-config.json` and the manifest after success. On conflict it records the intended metadata, pulls the cloud course, and exits `2`.

### `reorder`

The command sends the comma-separated outline BID sequence and changes the course outline order.

## Delete Commands

```bash
delete-lesson <shifu_bid> <outline_bid>
```

`delete-lesson` deletes the named outline.

## Bulk Import

```bash
# Flat JSON import
import <shifu_bid> --json-file course.json
import --new --json-file course.json

# Build and import from a course directory
import <shifu_bid> --course-dir ./course-a/ \
  [--title "..."] [--description "..."] [--keywords "..."] [--chapter-name "..."]
import --new --course-dir ./course-a/ \
  [--title "..."] [--description "..."] [--keywords "..."] [--chapter-name "..."]

# Offline build only
build --course-dir ./course-a/ [-o shifu-import.json] \
  [--title "..."] [--description "..."] [--keywords "..."] [--chapter-name "..."]
```

`build` performs no network calls and writes the import JSON to `-o` or `<course-dir>/shifu-import.json`. File discovery, field precedence, directory schemas, and the generated import schema are defined in `course-directory-spec.md`.

`import --new` creates a new course. `import <shifu_bid>` targets an existing course. Both forms send content fields. Existing-course import leaves omitted platform attributes unchanged; new-course import uses platform defaults for omitted attributes.

Importing into an existing course deletes and recreates every outline, so all outline BIDs are regenerated and recreated lessons receive platform-default permissions. With `--course-dir` and a matching sync manifest, an existing-course import checks the course revision first. On conflict it backs up the local tree to `.conflict-backup-<timestamp>/`, pulls the cloud course over local, and exits `2`. After a successful existing-course import it runs an automatic pull to reseed the manifest.

## Image Upload

```bash
upload-image --file <local-path> [--course-dir <dir>] [--alt "<description>"]
upload-image --url <http-or-https-url> [--course-dir <dir>] [--alt "<description>"]
```

`--file` and `--url` are mutually exclusive and one is required.

- A local file is opened with Pillow, has EXIF orientation corrected, is downscaled to a maximum side of 2048 px, and is recompressed to at most 2 MB. Transparent images remain PNG; other accepted images are uploaded as JPEG. Invalid image input exits `1`.
- A remote URL is sent to the backend for validation and re-hosting.
- Stdout contains exactly the resulting `https://res.ai-shifu.cn/<uuid32>` URL; diagnostics and manifest messages go to stderr.
- With `--course-dir`, the CLI upserts an entry in `assets/image-manifest.json`, keyed by `local` or `source_url`.
- `--alt` is stored in the manifest.
- `--no-process` skips local preprocessing and is a debug-only flag.

The local preprocessing dependencies are `Pillow` and `pillow-heif`.

## State Management

```bash
publish <shifu_bid>
archive <shifu_bid>
unarchive <shifu_bid>
```

- `publish` publishes the current draft and prints admin, preview, and public verification URLs.
- `archive` archives the course.
- `unarchive` restores an archived course.

## Exit Codes

- `0`: command completed successfully.
- `1`: validation, transport, file, authentication, or platform business error; `status --exit-code` also uses `1` for divergence.
- `2`: `verify` could not determine token state, or a version-aware write found a conflict and auto-pulled the cloud baseline. Interpret the command context before handling this code.

Commands print platform business error payloads before exiting when available.

## CLI Output & Encoding

CLI JSON uses UTF-8 and `ensure_ascii=False`. If an agent subprocess renders Chinese stdout as mojibake, redirect output to a UTF-8 file and read that file. This changes only capture behavior, not command output.

```bash
python3 scripts/shifu-cli.py analytics-query <bid> --dsl '<json>' > /tmp/shifu-result.json
```

The saved token remains in `{skillDir}/.env`; authenticated commands load it automatically.
