# 看板详情查询

> 工具 `dashboard.get` · 命令 `sensors analytics dashboard-get` · 类型 查询

## 用途

按看板 ID 精确获取所属分组、文本便签及书签摘要。`items` 按概览配置中的 `notedata.order` 混排书签与便签，分别标记 `type=bookmark` / `type=note`。只读取元信息，不执行书签分析查询。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--id` | 正整数 | 是 | — | 看板唯一 ID，可通过 `dashboard-list` 命令获取 | `7` |
| `--dry-run` | flag | 否 | 关 | 仅打印详情请求参数 dict（`{"id": <id>}`），不发起 navigation 或 detail 请求 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填，`--dry-run` 豁免）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`（临时覆盖配置）、`--timeout`（analytics 命令默认 1800 秒）。

## 输入 Schema

本工具无复杂 JSON 输入，仅通过 `--id` 精确定位单个看板；无名称模糊查询能力，候选不唯一时先由调用方基于 `dashboard.list` 结果确认 ID。

## 构造流程

1. 已知看板 ID 时直接 `--id <dashboard_id>` 展开，不必先列看板候选；命令会分别查询 navigation 和 detail 各一次。
2. 只有书签名 / 部分信息时：先 `dashboard-list` 拿看板候选，再逐个 `dashboard-get` 展开 `items[]`，只在 `type=bookmark` 的项目中按名称匹配；多候选书签时把 `id` / `name` / `analysis_type` 交还调用方确认唯一目标。
3. 需要预览请求参数时加 `--dry-run`，确认后去掉该 flag 真实执行。

示例：

```bash
# 展开看板 101 的全部书签
sensors analytics dashboard-get --ai-session-id <ai_session_id> --id 101

# 预览将发送的请求参数，不发起真实请求
sensors analytics dashboard-get --ai-session-id <ai_session_id> --id 101 --dry-run
```

## 输出

`--format json` 时输出：

```json
{
  "id": 101,
  "name": "运营看板",
  "type": "PERSONAL",
  "groups": [{"id": 666666, "title": "运营概览"}],
  "notes": [
    {"id": "note-1", "text": "本周转化概况", "rich_text": "<p>本周转化概况</p>"}
  ],
  "bookmarks": [
    {
      "id": 5,
      "name": "周活漏斗",
      "analysis_type": "漏斗分析",
      "model_type": "FUNNEL_MODEL"
    }
  ],
  "items": [
    {
      "id": 5,
      "type": "bookmark",
      "name": "周活漏斗",
      "analysis_type": "漏斗分析",
      "model_type": "FUNNEL_MODEL"
    },
    {"id": "note-1", "type": "note", "text": "本周转化概况", "rich_text": "<p>本周转化概况</p>"}
  ],
  "request_id": "<本次命令生成的请求 ID>"
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `id` / `name` | 看板唯一 ID 与名称 | `7` / `客户整体概览` |
| `type` | 看板类型字符串（如 PERSONAL / PUBLIC）；可能为 null | `PRIVATE` |
| `groups[]` | 所属分组列表；按分组 ID 去重，未匹配时为空数组。每项包含 `id` 和 `title` | `[{"id":666666,"title":"运营概览"}]` |
| `notes[]` | 文本便签列表；每项包含 `id`、纯文本 `text`、原始 HTML `rich_text`；无便签时为空数组 | `[{"id":"note-1","text":"说明","rich_text":"<p>说明</p>"}]` |
| `bookmarks[]` | 书签列表；每项包含 `id`、`name`、`analysis_type`、`model_type`；无书签时为空数组 | `[{"id":5,"name":"周活漏斗"}]` |
| `items[]` | 书签与便签的混合列表，先按 `notedata.order` 排序，再补齐未列出的内容；没有内容时为空数组 | `[{"id":5,"type":"bookmark"},{"id":"note-1","type":"note"}]` |
| `items[].type` | 项目类型：`bookmark` 为书签，`note` 为文本便签 | `bookmark` |
| `items[].id` | 书签 ID 为整数，可用于 `bookmark-query --bookmark-id`；便签 ID 为字符串 | `5` |
| `items[].name` / `analysis_type` / `model_type` | 仅书签有：图表标题、中文分析类型、平台原始模型类型 | `周活漏斗` / `漏斗分析` / `FUNNEL_MODEL` |
| `items[].text` / `rich_text` | 仅便签有：提取后的纯文本和原始 HTML | `说明` / `<p>说明</p>` |
| `request_id` | 本次命令的请求追踪 ID | `...` |

定位与复用：只在 `items[]` 的 `type=bookmark` 项中寻找书签；其中的 `id`、`name`、`analysis_type` 用于确认唯一目标，确认后同一任务内直接复用。

书签类型转换表（未列出的平台原始类型原样返回）：

| 平台原始类型 | 输出 `analysis_type` |
|---|---|
| `SEGMENTATION_MODEL` | 事件分析 |
| `DISTRIBUTION_MODEL` / `ADDICTION_MODEL` | 分布分析 |
| `FUNNEL_MODEL` | 漏斗分析 |
| `RETENTION_MODEL` | 留存分析 |
| `INTERVAL_MODEL` | 间隔分析 |
| `ATTRIBUTION_MODEL` | 归因分析 |
| `LTV_MODEL` | LTV 分析 |
| `SESSION_MODEL` | Session 分析 |
| `BEHAVIOR_PATH_MODEL` | 路径分析 |
| `USER_ANALYTICS_MODEL` | 属性分析 |
| `FANCY_METRIC_MODEL` | 指标分析 |
| `CUSTOM_SQL_MODEL` | 自定义查询 |

结构性解读：

- `items[]` 是按页面顺序排列的完整内容；服务端 `widget` 映射为输出 `type=bookmark`，便签为 `type=note`。仅统计 `type=bookmark` 的项目作为书签总数。
- 便签的 `rich_text` 保留原文，`text` 用于直接阅读；书签只返回摘要，不包含保存的查询口径或展示配置，分析结果需另外调用 `dashboard.bookmark-query`。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `Invalid value for '--id'` / Missing option | `--id` 缺失或非整数 | 传入整数看板 ID |
| 看板不存在 / 无权限访问 | ID 不存在或不属于当前项目 | 先 `dashboard-list` 复核 ID |
| 认证 / 权限错误 | API Key 无效或无当前项目权限 | 先运行 `sensors doctor` 诊断配置 |
| `items: []` | 看板没有书签或便签 | 空结果不是错误，原样返回 |
| 概览配置不是合法 JSON 对象 | 服务端返回的概览配置损坏 | 根据错误中的概览 ID 排查服务端保存的数据 |

## 使用约束

- 只做单看板读取；书签候选不唯一时把候选（`id` / `name` / `type`）交还调用方确认，不自行选择。
- 书签的中文 `analysis_type` 用于展示；原始 `model_type` 以服务端返回为准，`items[].type` 仅区分书签和便签。
