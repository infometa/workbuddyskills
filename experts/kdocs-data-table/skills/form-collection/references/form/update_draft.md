# form.lite.update_draft

## 1. form.lite.update_draft

#### 功能说明

更新智能表单草稿的标题或题目列表。`questions` 传入时会按完整题目列表覆盖原有题目，不传则保持不变。

#### 调用约束

- **前置检查**：form.lite.get_form_info 确认目标仍为 Draft，并确认当前题目列表
- **后置验证**：form.lite.get_form_info 确认标题和题目列表已按预期更新

**幂等性**：否 — 若 questions 中未固定 question_id/select_id，重试前需先 get_form_info 确认当前草稿结构

> `questions` 是完整覆盖语义；只想改标题时不要传 `questions`。
> 如需稳定重试，建议显式提供 `question_id` 和 `select_id`。

#### 调用示例

更新标题：

```json
{
  "form_id": "f_xxxxx",
  "title": "客户回访表（新版）"
}
```

覆盖题目列表：

```json
{
  "form_id": "f_xxxxx",
  "questions": [
    {
      "question_id": "q_name",
      "question": "姓名",
      "type": "input"
    },
    {
      "question_id": "q_score",
      "question": "满意度",
      "type": "select",
      "selects": [
        {
          "select_id": "sel_1",
          "value": "非常满意"
        },
        {
          "select_id": "sel_2",
          "value": "满意"
        },
        {
          "select_id": "sel_3",
          "value": "一般"
        }
      ]
    }
  ]
}
```

#### 参数说明

- `form_id` (string, 必填): 草稿表单 ID
- `title` (string, 可选): 更新后的表单标题，不传则保持不变
- `questions` (array, 可选): 更新后的完整题目列表，不传则保持不变

**questions 每项字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question_id` | string | 否 | 题目 ID，不传时服务端自动生成 6 位随机 ID |
| `question` | string | 是 | 题目标题，去空格后不能为空 |
| `type` | string | 是 | 题目类型，支持 `input`、`telphone`、`email`、`idcard`、`numberInput`、`decimal`、`select`、`multiSelect`、`dropdown`、`date`、`dateTime`、`month`、`time`、`address` |
| `selects` | array | 否 | 选择题选项，仅 `select`、`multiSelect`、`dropdown` 使用 |
| `address` | boolean | 否 | 地址题是否需要详细地址，仅 `address` 使用，默认 `false` |
| `location_type` | string | 否 | 地址题精确层级，仅 `address` 使用，默认 `city`；可选 `province`、`city`、`district`、`town`、`village` |

**selects 每项字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `select_id` | string | 否 | 选项 ID，不传时服务端自动生成 |
| `value` | string | 是 | 选项内容，去空格后不能为空 |

#### 返回值说明

```json
{
  "form_id": "f_xxxxx",
  "type": "Draft",
  "sid": "",
  "title": "客户回访表（新版）",
  "questions": [
    {
      "question_id": "q_name",
      "question": "姓名",
      "type": "input"
    },
    {
      "question_id": "q_score",
      "question": "满意度",
      "type": "select",
      "selects": [
        { "select_id": "sel_1", "value": "非常满意" },
        { "select_id": "sel_2", "value": "满意" },
        { "select_id": "sel_3", "value": "一般" },
        { "select_id": "sel_4", "value": "不满意" }
      ]
    }
  ]
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `form_id` | string | 表单 ID |
| `type` | string | 表单状态，草稿为 Draft |
| `sid` | string | 发布后的收集 ID，草稿阶段通常为空 |
| `title` | string | 表单标题 |
| `questions[].question_id` | string | 题目 ID |
| `questions[].question` | string | 题目标题 |
| `questions[].type` | string | 题目类型 |
| `questions[].selects` | array | 选择题选项 |

**失败示例：**

```json
{
  "code": 11000,
  "result": "NotDraft"
}
```
