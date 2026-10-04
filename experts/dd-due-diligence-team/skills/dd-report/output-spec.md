# 报告输出规范

> ⚠️ **本文件定义了落盘 JSON 的唯一合法格式。任何偏离本规范的字段名、字段值、结构都是错误的。**

## 输出 JSON Schema（强制校验）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["company_name", "reportName", "generatedAt", "chapters"],
  "properties": {
    "company_name": { "type": "string", "minLength": 1 },
    "reportName": { "type": "string", "minLength": 1 },
    "templateId": { "type": ["string", "null"] },
    "generatedAt": { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T" },
    "chapters": { "type": "array", "minItems": 1, "items": { "$ref": "#/$defs/chapter" } }
  },
  "$defs": {
    "chapter": {
      "type": "object",
      "required": ["id", "title", "order", "content"],
      "properties": {
        "id": { "type": "string", "pattern": "^c\\d+" },
        "title": { "type": "string", "minLength": 1 },
        "order": { "type": "integer", "minimum": 1 },
        "content": { "type": "string", "minLength": 1 },
        "children": { "type": "array", "items": { "$ref": "#/$defs/chapter" } }
      }
    }
  }
}
```

---

## 字段名强制约束（禁止偏离）

### ❌ 绝对禁止的写法

| 禁止写法                 | 正确写法                             | 说明                        |
| ------------------------ | ------------------------------------ | --------------------------- |
| 缺少 `company_name`      | 必须有 `"company_name": "XX公司"`    | 必填字段，不可省略          |
| `"company_name": ""`     | `"company_name": "华为技术有限公司"` | 不可为空字符串              |
| `"company_name": "华为"` | `"company_name": "华为技术有限公司"` | 必须是完整法定名称          |
| `"name": "报告标题"`     | `"reportName": "报告标题"`           | 字段名是 reportName（驼峰） |
| `"report_name": "..."`   | `"reportName": "..."`                | 不是下划线格式              |
| `"generated_at": "..."`  | `"generatedAt": "..."`               | 驼峰格式                    |
| `"template_id": "..."`   | `"templateId": "..."`                | 驼峰格式                    |
| `"content": ""`          | `"content": "章节正文..."`           | content 不可为空            |

### ✅ 字段值约束

| 字段                       | 要求                     | 示例                                         |
| -------------------------- | ------------------------ | -------------------------------------------- |
| `company_name`             | 完整法定名称             | `"华为技术有限公司"`                         |
| `reportName`               | 包含公司名 + 报告类型    | `"华为技术有限公司流动资金贷款尽职调查报告"` |
| `generatedAt`              | ISO 8601 UTC 时间        | `"2026-07-14T16:00:00Z"`                     |
| `chapters[].id`            | `c1`, `c2`, `c3`... 格式 | `"c1"`                                       |
| `chapters[].children[].id` | `c1-1`, `c1-2`... 格式   | `"c1-1"`                                     |
| `chapters[].content`       | Markdown 格式，不可为空  | `"## 项目概况\n\n..."`                       |

---

## 完整输出示例

以下是一个**完全合规**的输出 JSON：

```json
{
  "company_name": "华为技术有限公司",
  "reportName": "华为技术有限公司流动资金贷款尽职调查报告",
  "templateId": null,
  "generatedAt": "2026-07-14T16:00:00Z",
  "chapters": [
    {
      "id": "c1",
      "title": "项目概况",
      "order": 1,
      "content": "## 项目概况\n\n华为技术有限公司申请流动资金贷款5000万元，期限1年，用于补充日常经营周转资金。\n\n### 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| 申请人 | 华为技术有限公司 |\n| 贷款品种 | 流动资金贷款 |\n| 申请金额 | 5,000万元 |\n| 期限 | 12个月 |",
      "children": []
    },
    {
      "id": "c2",
      "title": "企业画像",
      "order": 2,
      "content": "## 企业画像\n\n华为技术有限公司成立于1987年，注册资本403.1亿元，是全球领先的ICT基础设施和智能终端提供商。",
      "children": [
        {
          "id": "c2-1",
          "title": "股权结构",
          "order": 1,
          "content": "### 股权结构\n\n华为投资控股有限公司持股100%，实际控制人为任正非。"
        }
      ]
    }
  ]
}
```

---

## 输出路径

```
/workspace/reports/{company_prefix}-report-{timestamp}.json
```

- `{company_prefix}` — 企业名称的简短英文标识（如 `huawei`、`byd`）
- `{timestamp}` — UTC 时间戳（去掉冒号和短横线），如 `20260714T160000`

示例：工作空间 reports/huawei-report-20260714T160000.json

> 如果只有一家企业，`{company_prefix}` 可省略。

---

## 落盘前校验清单

写入 JSON 文件前，**必须逐项确认**：

- [ ] `company_name` 不为空，且为完整法定名称（不是缩写）
- [ ] `reportName` 不为空，且包含公司名称
- [ ] `generatedAt` 为合法的 ISO 8601 时间字符串（含 `T` 和时区）
- [ ] `chapters` 为非空数组
- [ ] 每个章节都有 `id`（格式 `c1`/`c2`）、`title`（非空）、`order`（正整数）、`content`（非空 Markdown）
- [ ] 子章节 id 格式为 `c1-1`、`c1-2` 等
- [ ] 所有字段名为驼峰格式（`reportName`、`generatedAt`、`templateId`），不是下划线格式
- [ ] JSON 文件可被 `json.loads()` / `JSON.parse()` 正确解析
- [ ] 字符串中的双引号已转义为 `\"`，换行符为 `\n`

## 注意事项

1. 文件名中的时间戳使用 UTC 时间
2. 每次生成报告都创建新文件，不覆盖已有文件
3. content 字段使用 Markdown 格式，支持表格、列表、加粗等
4. 如果用户选择了模板，chapters 的结构应严格按照模板的章节定义
5. 如果未选择模板，模型可自由组织章节结构，但必须符合上述 JSON 格式
6. **`company_name` 是平台识别报告所属企业的唯一依据，缺失将导致报告无法正确归类**
