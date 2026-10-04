# 看板详情查询

> 工具 `dashboard.get` · 命令 `sensors analytics dashboard-get` · 类型 查询

## 用途

按看板 ID 精确获取单个看板的基本信息及其包含的全部书签（图表）列表，用于确定书签 ID 与书签分析类型。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--id` | int | 是 | — | 看板唯一 ID（整数），可通过 `dashboard-list` 命令获取 | `7` |
| `--dry-run` | flag | 否 | 关 | 打印将发送的请求参数 dict（`{"id": <id>}`），不发起真实 HTTP 请求 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填，`--dry-run` 豁免）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`（临时覆盖配置）、`--timeout`（analytics 命令默认 1800 秒）。

## 输入 Schema

本工具无复杂 JSON 输入，仅通过 `--id` 精确定位单个看板；无名称模糊查询能力，候选不唯一时先由调用方基于 `dashboard.list` 结果确认 ID。

## 构造流程

1. 已知看板 ID 时直接 `--id <dashboard_id>` 展开，不必先列看板候选。
2. 只有书签名 / 部分信息时：先 `dashboard-list` 拿看板候选，再逐个 `dashboard-get` 展开书签列表，在 `bookmarks[]` 中按名称匹配；多候选书签时把 `id` / `name` / `type` 交还调用方确认唯一目标。
3. 需要预览请求参数时加 `--dry-run`，确认后去掉该 flag 真实执行。

示例：

```bash
# 展开看板 101 的全部书签
sensors analytics dashboard-get --ai-session-id <ai_session_id> --id 101

# 预览将发送的请求参数，不发起真实请求
sensors analytics dashboard-get --ai-session-id <ai_session_id> --id 101 --dry-run
```

## 输出

`--format json` 时输出（Envelope 包裹）：

```json
{
  "id": 101,
  "name": "运营看板",
  "type": "PERSONAL",
  "bookmarks": [
    {"id": 5, "name": "周活漏斗", "type": "漏斗分析"}
  ]
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `id` / `name` | 看板唯一 ID 与名称 | `7` / `客户整体概览` |
| `type` | 看板类型字符串（如 PERSONAL / PUBLIC）；可能为 null | `PRIVATE` |
| `bookmarks[].id` | 书签唯一 ID，可作为 `bookmark-query --bookmark-id` 的入参 | `4` |
| `bookmarks[].name` | 书签名称（图表标题），是给用户看的展示名，不等于分析模型名 | `企业总数` |
| `bookmarks[].type` | 书签分析类型中文名，由平台原始类型转换而来，映射见下表 | `属性分析` |

定位与复用：`bookmarks[]` 中的 `id`（查询与写入的目标标识）、`name`（结果标题）、`type`（结果解释路由与可执行性判断）构成任务内的交接字段组——确认唯一书签后，同一任务内直接复用，不再重复展开看板。

书签类型转换表（未列出的平台原始类型原样返回）：

| 平台原始类型 | 输出 `type` |
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

- `bookmarks[]` 即看板内书签的全量清单（列表顺序以服务端返回为准），是执行书签查询（`bookmark-query` 逐个调用）、复制（`bookmark-copy` 选 ID）与移除（`bookmark-remove` 选 ID）的统一事实源。
- 书签的查询配置（`data`）与可视化配置（`config`）不在本输出中展开；执行查询时由 CLI 内部按书签保存内容还原，调用方无需读取。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `Invalid value for '--id'` / Missing option | `--id` 缺失或非整数 | 传入整数看板 ID |
| 看板不存在 / 无权限访问 | ID 不存在或不属于当前项目 | 先 `dashboard-list` 复核 ID |
| 认证 / 权限错误 | API Key 无效或无当前项目权限 | 先运行 `sensors doctor` 诊断配置 |
| `bookmarks: []` | 看板存在但未包含书签 | 空结果不是错误，原样返回 |

## 使用约束

- 只做单看板读取；书签候选不唯一时把候选（`id` / `name` / `type`）交还调用方确认，不自行选择。
- 输出中的中文 `type` 用于展示与后续执行路由判断；平台原始模型枚举以服务端返回为准。
