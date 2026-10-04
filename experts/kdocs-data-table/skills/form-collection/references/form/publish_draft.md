# form.lite.publish_draft

## 1. form.lite.publish_draft

#### 功能说明

将智能表单草稿发布为正式表单。当前接口不读取业务字段，请求体建议传空对象。

#### 调用约束

- **前置检查**：form.lite.get_form_info 确认目标表单仍为 Draft
- **后置验证**：form.lite.get_form_info 确认 type 为 Release 且 sid 非空

**幂等性**：否 — 重试前先调用 form.lite.get_form_info；若已为 Release，可视为发布成功

> 发布动作会改变表单状态；发布前请确认题目列表已经最终确定。
> 发布成功后 `sid` 非空，可生成填写页面链接。

#### 调用示例

发布草稿：

```json
{
  "form_id": "f_xxxxx"
}
```

#### 参数说明

- `form_id` (string, 必填): 草稿表单 ID

#### 返回值说明

```json
{
  "form_id": "f_xxxxx",
  "type": "Release",
  "sid": "s_xxxxx",
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
| `type` | string | 表单状态，发布后为 Release |
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

发布成功后，使用响应中的 `form_id` 拼接管理页面，使用 `sid` 拼接填写页面。交付给用户时建议同时提供这两个链接。

**失败示例：**

```json
{
  "code": 11000,
  "result": "NotDraft"
}
```
