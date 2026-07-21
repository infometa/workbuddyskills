# End-to-End Deploy Example (Segmentation → Orchestration → Generation → Optimization → Deployment)

> Note: Outputs in this example are illustrated in English for clarity. Actual output language follows `references/data-contracts.md#language-resolution` (e.g., Chinese invocation → Chinese output).

## Input Payload (example)

```json
{
  "course_material": "Module transcript: observe metric drift, classify causes, apply one fix, review impact.",
  "generation_constraints": {
    "persona": "practical coach",
    "lesson_granularity": "short"
  },
  "course_profile": {
    "audience_level": "beginner",
    "lesson_duration_minutes": 10,
    "lesson_count_target": 3,
    "assessment_mode": "project"
  },
  "platform_region": "cn",
  "target_language": "zh-CN"
}
```

## Segmentation through Optimization (Author)

Produces optimized Teaching Prompts (see `pipeline-full.md` for detailed output).

## Deployment Output

### Step 1: Build Course Directory

```
my-course/
  README.md
  course-prompt.md
  structure.json
  lessons/
    lesson-01.md
    lesson-02.md
    lesson-03.md
```

### Step 2: Build Import File

```bash
python3 {skillDir}/scripts/shifu-cli.py build --course-dir ./my-course/ --title "Metric Drift Diagnosis"
```

Output: `my-course/shifu-import.json`

### Step 3: Import and Publish

```bash
python3 {skillDir}/scripts/shifu-cli.py import --new --json-file ./my-course/shifu-import.json
# Returns: shifu_bid = abc123-def456

python3 {skillDir}/scripts/shifu-cli.py publish abc123-def456
```

### Step 4: Verify

```bash
python3 {skillDir}/scripts/shifu-cli.py show abc123-def456
```

Platform URLs (copied verbatim from the `Verification URLs:` block printed by `publish` / `import` / `show` — do not reconstruct them; render each as Markdown link + bare URL + a Chinese-description line per `references/report-template.md`):

- [我的课程 - 后台管理](https://app.ai-shifu.cn/shifu/abc123-def456)
  https://app.ai-shifu.cn/shifu/abc123-def456
  课程的管理后台地址：需要管理课程的内容、设置小节是否隐藏、是否付费等，在这里操作。
- [我的课程 - 课程预览](https://app.ai-shifu.cn/c/abc123-def456?preview=true)
  https://app.ai-shifu.cn/c/abc123-def456?preview=true
  课程预览地址：仅课程作者本人可见，用于发布前后自测课程效果。
- [我的课程 - 已发布课程](https://app.ai-shifu.cn/c/abc123-def456)
  https://app.ai-shifu.cn/c/abc123-def456
  课程的公开学习地址：可以发送给学员使用。仅在课程已发布后生效。

## Acceptance Notes

- All pipeline stages executed end-to-end.
- Teaching Prompts (MarkdownFlow) written to course directory, built, imported, and published.
- Course is live and accessible via platform URL.
