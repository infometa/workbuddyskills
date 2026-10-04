# form.lite.get_form_info

## 1. form.lite.get_form_info

#### 功能说明

获取智能表单信息，仅返回当前转换器支持的题型。适合在更新或发布前后核对表单状态、标题与题目结构。

> 若表单包含当前转换器不支持的题型，返回的题目范围可能受限。
> 交付表单时优先调用本工具确认 `type` 和 `sid`，再拼接页面地址。

#### 调用示例

获取表单信息：

```json
{
  "form_id": "f_xxxxx"
}
```

#### 参数说明

- `form_id` (string, 必填): 表单 ID

#### 返回值说明

```json
{
  "form_id": "f_xxxxx",
  "type": "Release",
  "sid": "s_xxxxx",
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
| `type` | string | 表单状态，如 Draft 或 Release |
| `sid` | string | 发布后的收集 ID |
| `title` | string | 表单标题 |
| `questions[].question_id` | string | 题目 ID |
| `questions[].question` | string | 题目标题 |
| `questions[].type` | string | 题目类型 |
| `questions[].selects` | array | 选择题选项 |

**页面地址：**

| 页面 | 地址 |
|------|------|
| 管理页面 | `https://f.wps.cn/ksform/m/result/{form_id}` |
| 填写页面 | `https://f.wps.cn/g/{sid}` |

查询结果中 `form_id` 可用于拼接管理页面；当 `type` 为 `Release` 且 `sid` 非空时，可用 `sid` 拼接填写页面。若 `sid` 为空，说明当前结果不足以生成填写链接。

**失败示例：**

```json
{
  "code": 10009,
  "result": "无权访问"
}
```
