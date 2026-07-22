# Image Authoring

Understand, upload, compose, embed, and validate image assets used by Teaching Prompts. Load this file only for tasks that actually use image assets.

## Required References

- `language-policy.md`
- `pedagogy.md#visual-text-coordination`
- `markdownflow.md#deterministic-blocks`
- `markdownflow.md#images`
- `cli/cli-reference.md#image-upload`
- `cli/course-directory-spec.md#assets`

## Conditional References

- When an image URL, alt, caption, or ordering was selected as immutable source content: `source-preservation.md`

## Asset Intake

Understand every image before choosing its lesson, position, or alt text:

- If the image is visible, identify in one sentence the concept, relation, or example it conveys.
- If only an opaque path or URL is available, ask the author for a one-sentence description or a semantically meaningful filename. Do not guess from an opaque filename.

When the selected route permits platform access, upload local or remote assets with `shifu-cli.py upload-image`, always passing `--course-dir` and an informative `--alt`. Use the returned `https://res.ai-shifu.cn/<uuid32>` URL and the stored manifest record as the authoritative asset identity.

For explicitly local artifact-only work where upload is excluded, do not call `upload-image`. Use the authoritative URL and metadata supplied by the source record instead. Stop when that record lacks the remote URL, informative alt, or another field required by the selected image form; never invent a missing value from a filename.

## Image Composition

Raw SVG, HTML drawings, Mermaid, PlantUML, and Graphviz source are not image-embedding forms by default. Include raw graphic source only when the author explicitly requests it.

Choose one form after the visual intent is known:

| Authoring intent | Form |
| --- | --- |
| Display the uploaded image without layout customization | `===![informative alt](url)===` on its own line |
| Control width, alignment, caption, or multi-image layout | A natural-language HTML-view instruction |

For fixed display, write informative alt text. When an alt was selected as immutable source content, load `source-preservation.md` and retain it exactly. The deterministic line bypasses the Teaching Agent.

For HTML-view, keep the instruction outside deterministic markers and include position, exact URL, image content for semantic alt, caption, layout, ordering, and aspect-ratio behavior. Keep each URL on its own labeled line. Describe responsive layout in natural language rather than fixed pixel values. The preservation wording constrains the Teaching Agent but is not parser-level locking.

Use this compact shape when authored output language is Simplified Chinese; localize it under `language-policy.md` for other languages:

```markdown
必须在此处以 HTML-view 方式插入一张带图注的图片，不得省略，并使用 HTML <figure>/<figcaption> 结构。

- URL（必须原样保留）：https://res.ai-shifu.cn/<uuid32>
- 图片内容（必须用于生成语义化 alt，不得省略）：图片传达的具体概念或关系
- 图注文字（必须原样输出，不要改写）：图注原文
- 展示方式：居中，宽度不超过容器 70%，保持原始宽高比
```

## Image Output Validation

1. Build an expected-image record from `assets/image-manifest.json`, adding the selected form, caption, position, layout constraints, and ordering. For explicitly local artifact-only work where upload is excluded, use the authoritative source record instead.
2. Stop before generation when the authoritative record lacks `remote`, informative `alt`, or a field required by the selected form.
3. Compare the generated Teaching Prompt with every expected record. Verify URL, description or alt, caption, position, layout constraints, ordering, and form.
4. Regenerate only the affected image instruction or lesson when a field is missing, changed, duplicated, or reordered.
5. If the second comparison still fails, stop that lesson and report the mismatched fields as blocking. Do not finalize or hand off the Teaching Prompt.
