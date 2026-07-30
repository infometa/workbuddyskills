# Course Directory Specification

## Required References

None.

## Directory Layout

```text
<course>/
  README.md
  course-description.md
  course-prompt.md
  course-config.json
  structure.json
  shifu-import.json
  .shifu-sync.json
  lessons/
    lesson-01.md
    lesson-02.md
  assets/
    image-manifest.json
    raw/
```

| Path | Producer | Consumer | Required |
| --- | --- | --- | --- |
| `README.md` | author or `pull` | `build` title resolution | No; directory name is the fallback title. |
| `course-description.md` | author, `pull`, or `update-meta` | `build`, directory import, `status`, `update-meta` | No; missing means an empty description unless a CLI flag supplies one. |
| `course-prompt.md` | author or `pull` | `build` and directory import | No; missing means an empty Course Prompt. |
| `course-config.json` | `pull` or `set-tts --course-dir` | reference only; `build` and `import` ignore it | No. |
| `structure.json` | author, `pull`, or `set-access --course-dir` | `build` chapter and lesson mapping | No; missing selects single-chapter discovery. |
| `shifu-import.json` | `build` | JSON import | Generated output. |
| `.shifu-sync.json` | `pull` and version-aware writes | `status` and version-aware writes | Required only for full conflict protection. |
| `lessons/*` | author or `pull` | `build` and lesson update commands | Yes; at least one discoverable lesson is required by `build`. |
| `assets/image-manifest.json` | `upload-image --course-dir` | asset lookup | No. |
| `assets/raw/` | user | no direct build consumer | No; conventional storage only. |

The directory contract above is the complete set of recognized and managed course-directory paths. An author-only run writes only the relevant author-owned inputs; it must not synthesize CLI-managed outputs. Do not add an `authoring-manifest.json` or another root-level file to persist Segmentation or Orchestration handoffs; retain that phase data in the active handoff or report instead. New directory artifacts require an explicit CLI specification update.

## Build Precedence

`build --course-dir <dir>` resolves fields in this order:

1. Course title: `--title` → the first line of `README.md` when it is a Markdown heading → course-directory basename.
2. Course description: `--description` → `course-description.md` → empty string.
3. Course keywords: `--keywords` → empty string.
4. Course Prompt: `course-prompt.md` → empty string.
5. Chapter structure:
   - a non-empty `structure.json#chapters` list defines chapters and lesson files;
   - otherwise one chapter contains sorted `lessons/lesson-*.md` files, and its title is `--chapter-name` → resolved course title.
6. Lesson title: `structure.json` lesson `title` → filename stem with hyphens converted to spaces and title-cased.
7. Output path: `-o` → `<course-dir>/shifu-import.json`.

When `structure.json` is absent or has no chapters, only files matching `lesson-*.md` are discovered. When it has chapters, every `chapters[].lessons[].file` is resolved inside `lessons/`; other filenames are accepted when explicitly listed.

`build` ignores `course-config.json`, `assets/`, `.shifu-sync.json`, and the `access` and `hidden` reference fields in `structure.json`.

## README.md

Only the first line is inspected. If it begins with one or more `#` characters, the remaining trimmed text is the course title. Other README content is not mapped into the import payload. New authoring workflows should write only that title heading; do not duplicate the author, description, audience, or design controls here because their owners and consumers are elsewhere.

## Lesson Files

Each discovered lesson file is UTF-8 MarkdownFlow content. `build` copies the complete file into the corresponding lesson `outline_items[].content` field.

## course-description.md

This UTF-8 text file maps to `shifu.description`. `pull` writes the current cloud description. `update-meta --course-dir` compares it with the description recorded in `.shifu-sync.json`, sends it when locally changed, and refreshes it after a successful explicit description update.

## course-prompt.md

This UTF-8 text file maps to `shifu.course_prompt` in `shifu-import.json`; the import API maps that value to the platform `system_prompt` field. `pull` writes the current cloud system prompt back to this file.

## structure.json

Schema:

```json
{
  "chapters": [
    {
      "title": "Chapter Title",
      "lessons": [
        {
          "file": "lesson-01.md",
          "title": "Lesson Title",
          "access": "guest",
          "hidden": false
        }
      ]
    }
  ]
}
```

Fields:

- `chapters[].title` (required): chapter title.
- `chapters[].lessons[]` (required): lesson definitions in output order.
- `chapters[].lessons[].file` (required): file path relative to `lessons/`; the resolved path must remain inside that directory.
- `chapters[].lessons[].title` (required): lesson title. For compatibility, the builder derives a title from the filename when this field is absent or empty.
- `chapters[].lessons[].access` (optional reference): `guest`, `trial`, or `normal`, written by `pull` and optionally refreshed by `set-access`.
- `chapters[].lessons[].hidden` (optional boolean reference): lesson visibility, written by `pull` and optionally refreshed by `set-access`.

`build` and `import` do not send `access` or `hidden`; recreated lessons use platform defaults.

## course-config.json

`pull` writes this read-only snapshot of course-level attributes:

```json
{
  "model": "",
  "temperature": 0.3,
  "price": 0,
  "keywords": [],
  "avatar": "",
  "use_learner_language": false,
  "tts_enabled": false,
  "tts_provider": "",
  "tts_model": "",
  "tts_voice_id": "",
  "tts_speed": 1.0,
  "tts_pitch": 0,
  "tts_emotion": "",
  "ask_enabled_status": 5101,
  "ask_model": "",
  "ask_temperature": 0.0,
  "ask_system_prompt": "",
  "ask_provider_config": {}
}
```

`model`, `llm`, `ask_model`, `ask_llm`, and their related keys are stable machine-facing fields for the underlying models and settings used by the Teaching Agent. Keep those keys unchanged in files and payloads; human-facing explanations identify AI-Shifu ownership on the first Teaching Agent mention and use Teaching Agent thereafter for both course delivery and learner follow-up answers.

`build` and `import` do not read or send this file. `set-tts --course-dir` refreshes it after a successful Listen Mode update.

## .shifu-sync.json

This file is auto-maintained; its abridged schema is:

```json
{
  "schema_version": 1,
  "shifu_bid": "a1b2c3",
  "base_url": "https://app.ai-shifu.cn",
  "course": {
    "revision": 42,
    "name": "Course Title",
    "description": "Course description",
    "updated_at": "2026-01-01T00:00:00Z",
    "updated_user_bid": "user_bid"
  },
  "lessons": [
    {
      "file": "lessons/lesson-01.md",
      "outline_bid": "lesson_bid",
      "name": "Lesson Title",
      "parent_bid": "chapter_bid",
      "revision": 1187,
      "is_chapter": false,
      "content_sha256": "sha256"
    },
    {
      "file": null,
      "outline_bid": "chapter_bid",
      "name": "Chapter Title",
      "parent_bid": "",
      "revision": null,
      "is_chapter": true
    }
  ],
  "last_pull_at": "2026-01-01T00:00:00Z",
  "last_push_at": "2026-01-01T00:00:00Z"
}
```

The course and lesson revisions are cloud baselines. `content_sha256` is the last synchronized local-content hash. The CLI writes this file atomically; manual edits are unsupported.

## assets/

`assets/image-manifest.json` schema:

```json
{
  "images": [
    {
      "local": "assets/raw/gradient-descent.heic",
      "remote": "https://res.ai-shifu.cn/abcd",
      "alt": "Image description",
      "uploaded_at": "2026-05-23T08:42:31Z",
      "bytes": 612345,
      "original_bytes": 4521000,
      "mime": "image/jpeg",
      "filename": "gradient-descent-1a2b3c4d.jpg"
    },
    {
      "source_url": "https://example.com/diagram.png",
      "remote": "https://res.ai-shifu.cn/efgh",
      "alt": "Image description",
      "uploaded_at": "2026-05-23T08:45:02Z"
    }
  ]
}
```

- `local` is the source path for file uploads and their upsert key. It is relative to the course directory when possible, otherwise absolute.
- `source_url` is the source and upsert key for URL uploads.
- `remote` is the platform-hosted URL returned by the CLI.
- `alt` is the value supplied through `--alt`.
- `uploaded_at` is a UTC ISO 8601 timestamp.
- `bytes`, `original_bytes`, `mime`, and `filename` describe locally processed uploads and are absent from URL-upload entries.

`build` ignores the entire `assets/` directory.

## shifu-import.json

`build` generates this shape (abridged to stable contract fields):

```json
{
  "version": "1.0",
  "exported_at": "2026-01-01T00:00:00Z",
  "shifu": {
    "shifu_bid": "generated_uuid",
    "title": "Course Title",
    "keywords": "keyword-a,keyword-b",
    "description": "Course description",
    "avatar_res_bid": "",
    "llm": "",
    "llm_temperature": 0,
    "course_prompt": "Course Prompt content",
    "ask_enabled_status": 5101,
    "ask_llm": "",
    "ask_llm_temperature": 0.0,
    "ask_llm_system_prompt": ""
  },
  "outline_items": [
    {
      "outline_item_bid": "generated_uuid",
      "title": "Chapter or Lesson Title",
      "type": 401,
      "hidden": 0,
      "parent_bid": "",
      "position": "0",
      "content": ""
    }
  ],
  "structure": {
    "bid": "generated_uuid",
    "id": 0,
    "type": "shifu",
    "children": [],
    "child_count": 0
  }
}
```

Every top-level chapter has an empty `parent_bid` and empty `content`. Every lesson has its chapter BID as `parent_bid`, its file contents in `content`, and the resolved Course Prompt in its `course_prompt` field. Generated BIDs contain UUID characters without hyphens. Positions are zero-based strings.
