# form.lite.create_draft

## 1. form.lite.create_draft

#### 功能说明

创建一个智能表单草稿。可传入题目列表直接生成完整草稿，也可传空数组创建空草稿后再更新。

#### 调用约束

- **后置验证**：使用返回的 form_id 调用 form.lite.get_form_info 验证草稿可访问

**幂等性**：否 — 重试前先确认是否已创建草稿，避免产生重复表单

> 需要空草稿时，`questions` 传 `[]`，不要省略该字段。

#### 调用示例

创建空草稿：

```json
{
  "title": "客户回访表",
  "questions": []
}
```

创建带题目的草稿：

```json
{
  "title": "客户回访表",
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
        }
      ]
    }
  ]
}
```

#### 参数说明

- `title` (string, 必填): 表单标题
- `questions` (array, 必填): 题目列表，可传空数组创建空草稿

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
  "title": "客户回访表",
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
        { "select_id": "sel_2", "value": "满意" }
      ]
    },
    {
      "question_id": "q_city",
      "question": "所在城市",
      "type": "address",
      "address": true,
      "location_type": "city"
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
| `questions[].address` | boolean | 是否需要详细地址 |
| `questions[].location_type` | string | 地址题精确层级 |

**失败示例：**

```json
{
  "code": 4,
  "result": "参数错误"
}
```
