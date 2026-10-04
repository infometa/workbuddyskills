# 考试批改 HTML 报告数据契约

HTML 仅用于 CET 与考研考试批改。一般写作修改和范文精读默认在对话中交付。

## 输入 JSON

```json
{
  "schema_version": "1.0",
  "report_type": "exam_review",
  "title": "CET-4 作文批改报告",
  "meta": {
    "task": "CET-4",
    "source": "CET-2016",
    "total_word_count": 145,
    "excluded_word_count": 3,
    "effective_word_count": 142,
    "generated_at": "2026-07-19 14:30"
  },
  "score": {
    "raw": 11,
    "deduction": 1,
    "final": 10,
    "maximum": 15,
    "band": "11档"
  },
  "summary": "整体判断",
  "evidence": [
    {
      "claim": "支持当前档",
      "quote": "作文原句",
      "reason": "判断说明"
    }
  ],
  "issues": [
    {
      "priority": "P1",
      "location": "P2",
      "original": "原句",
      "suggestion": "建议改法",
      "reason": "原因"
    }
  ],
  "actions": ["下一步动作一", "下一步动作二"]
}
```

## 必填规则

- `schema_version` 必须为 `1.0`。
- `report_type` 必须为 `exam_review`。
- `title`、`summary` 必须为非空字符串。
- `meta`、`score` 必须为对象。
- `evidence`、`issues`、`actions` 必须为数组。
- `score.raw`、`score.deduction`、`score.final`、`score.maximum` 必须为有限数值。
- `score.band` 必须为非空字符串。
- `score.raw` 在 0 与 `score.maximum` 之间。
- `score.deduction` 在 0 与 `score.raw` 之间。
- `score.final = max(0, score.raw - score.deduction)`。
- `evidence` 至少一项，每项的 `claim`、`quote`、`reason` 都是非空字符串。
- `issues` 可以为空；若有项目，`priority`、`location`、`original`、`suggestion`、`reason` 都是非空字符串。
- `actions` 至少一项，每项都是非空字符串。

## 评分字段使用规则

- 没有独立扣分时，`score.deduction` 使用 `0`。
- 只给档次区间且无法给稳定整数时，不生成当前数字型 HTML 报告；先在对话中交付定性结果。
- `meta.source` 建议填写 `CET-2016`、`PG-2008` 或用户提供的当年依据 ID。
- 有效字数无法可靠分离时，不伪造 `excluded_word_count` 与 `effective_word_count`；可仅保留 `total_word_count` 并在 `summary` 中说明限制。

## 文件规则

- 所有用户内容在渲染时进行 HTML 转义。
- 分数、扣分、最终分、证据和建议与对话输出一致。
- 报告不加载外部脚本、字体、图片或远程资源。
- 报告使用新文件名，不覆盖用户材料。
- 数据校验失败时停止生成并报告具体字段。
