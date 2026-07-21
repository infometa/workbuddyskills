# Course Directory Specification

## Directory Structure

```
<course>/
  README.md            # Course metadata (title from first heading)
  course-prompt.md     # Course-level prompt (AI role and teaching style)
  shifu-import.json    # Generated import file (output of build)
  structure.json       # Chapter structure (optional, for multi-chapter courses)
  lessons/
    lesson-01.md       # Teaching Prompt (MarkdownFlow)
    lesson-02.md
    ...
  assets/              # Image assets (optional)
    image-manifest.json  # Auto-maintained by upload-image: local → remote → alt
    raw/                 # Recommended location for the author's original images
```

## assets/

The `assets/` directory is created and maintained by `shifu-cli.py upload-image --course-dir <dir>`. It exists to give the course a stable record of which images have been uploaded, what they convey, and what their `resource.ai-shifu.cn` URLs are.

`image-manifest.json` schema:

```json
{
  "images": [
    {
      "local": "assets/raw/gradient-descent.heic",
      "remote": "https://resource.ai-shifu.cn/abcd…",
      "alt": "梯度下降三步示意",
      "uploaded_at": "2026-05-23T08:42:31Z",
      "bytes": 612345,
      "original_bytes": 4521000,
      "mime": "image/jpeg",
      "filename": "gradient-descent-1a2b3c4d.jpg"
    },
    {
      "source_url": "https://example.com/diagram.png",
      "remote": "https://resource.ai-shifu.cn/efgh…",
      "alt": "Transformer 注意力计算流程",
      "uploaded_at": "2026-05-23T08:45:02Z"
    }
  ]
}
```

Field reference:

- `local` (file uploads): path relative to `<course-dir>` when possible, otherwise absolute. Acts as the dedup key — uploading the same path again updates the entry rather than appending.
- `source_url` (URL uploads): the original remote URL provided to `--url`. Acts as the dedup key for URL-based uploads.
- `remote`: the platform OSS URL produced by upload. This is the value that should appear in Teaching Prompts.
- `alt`: description supplied via `--alt`. Not auto-rendered into MarkdownFlow — the authoring LLM still writes a contextual alt.
- `uploaded_at`: UTC ISO 8601 timestamp.
- `bytes` / `original_bytes` / `mime` / `filename` (file uploads only): book-keeping for the preprocessed payload that was actually sent.

`assets/raw/` is a recommendation, not enforced: store originals there so the manifest's `local` paths are stable across machines. The `build` command ignores `assets/` entirely.

## Lesson Files

When `structure.json` is not present, `build` auto-discovers only `lesson-*.md` files (e.g., `lesson-01.md`, `lesson-02.md`) and ignores other filenames. When `structure.json` is present, lesson files are taken from `chapters[].lessons[].file` and any filename is accepted as long as it exists.

## course-prompt.md

Defines the AI engine's role, teaching style, and interaction rules at the course level. The `build` command reads this file and populates `shifu.course_prompt` in the import JSON automatically (which the CLI maps to the platform API field `system_prompt` on import).

Authoring rules and a fillable template live in `../course-prompt.md`.

Note: MarkdownFlow files do not support HTML comments (`<!-- -->`). The parser discards them entirely, so the AI engine never sees them. Write instructions as plain text directly in the Course Prompt content.

## structure.json

Defines multi-chapter course structure. If this file exists, `build` uses it to organize lessons into chapters; otherwise all lessons are placed under a single auto-generated chapter.

Schema:

```json
{
  "chapters": [
    {
      "title": "Chapter Title",
      "lessons": [
        {"file": "lesson-01.md", "title": "Lesson Title"},
        {"file": "lesson-02.md"}
      ]
    }
  ]
}
```

Field reference:

- `chapters[].title` (required): Chapter display name
- `chapters[].lessons[]` (required): Array of lesson objects
- `chapters[].lessons[].file` (required): Filename in the `lessons/` directory (must exist)
- `chapters[].lessons[].title` (optional): Lesson display name. If omitted, auto-extracted from the Teaching Prompt (`lesson_title: ...` line in the MarkdownFlow content) or derived from filename
