# 书签查询执行

> 工具 `dashboard.bookmark-query` · 命令 `sensors analytics bookmark-query` · 类型 查询

## 用途

按书签 ID 执行单个已保存书签的分析查询：先读取书签保存的查询配置，再调用对应分析接口并返回原始结果。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--bookmark-id` | int | 是 | — | 书签 ID（正整数），通过 `dashboard-get --id <id>` 获取 | `4` |
| `--dashboard-id` | int | 是 | — | 书签所属看板 ID（正整数），通过 `dashboard-list` 获取 | `7` |
| `--from-date` | string | 否 | 书签自身配置 | 覆盖书签开始日期；`yyyy-MM-dd` 或 `Nd`（如 `7d` 表示最近 7 个完整自然日，起止均以昨天为终点，即同时把结束日期覆盖为昨天） | `2026-09-20`（或 `7d`） |
| `--to-date` | string | 否 | — | 覆盖书签结束日期，格式 `yyyy-MM-dd`，不支持 `Nd`；仅在 `--from-date` 为标准日期时生效 | `2026-09-26` |
| `--dry-run` | flag | 否 | 关 | 打印书签基本信息（`bookmark_id` / `dashboard_id` / `type`），不执行分析查询；仍会拉取看板详情定位书签 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`、`--timeout`（默认 1800 秒）。

## 输入 Schema

本工具无复杂 JSON 输入，通过 flag 定位书签并可选覆盖时间范围。可覆盖的查询参数只有时间范围一项：书签保存的维度、过滤条件、指标、粒度等其余查询参数不可覆盖，一律按书签保存配置原样执行。

## 构造流程

从业务输入到合法命令参数的构造映射：

1. 定位书签：`--dashboard-id` 与 `--bookmark-id` 必须配套（看板 ID 来自 `dashboard-list`，书签 ID 与类型来自 `dashboard-get --id` 展开的 `bookmarks[]`）；书签与看板不匹配时命令直接报错。
2. 时间覆盖构造，按下表把业务时间诉求落成 flag：

| 业务时间诉求 | flag 构造 | 实际查询范围 |
|---|---|---|
| 按书签原配置执行 | 不传任何日期参数 | 书签保存的原始时间范围 |
| 最近 N 天 | `--from-date 7d` | 最近 7 个完整自然日（从昨天往前推 7 天至昨天，不含今天）；`to-date` 被自动覆盖为昨天，此时 `--to-date` 不生效 |
| 明确起止日期 | `--from-date 2026-06-01 --to-date 2026-06-25` | 指定起止；要求 from 不晚于 to |
| 只要结束日期 | 不支持 | `--to-date` 单独传（无 `--from-date`）直接报错 |

3. 批量执行整个看板：本命令单次只执行一个书签；批量时先 `dashboard-get` 拿 `bookmarks[]`，再对每个书签逐个调用本命令（可统一带上同一组时间覆盖 flag，也可逐书签不同）。
4. 需要预览时加 `--dry-run`：输出书签基本信息但不执行查询，确认对象与类型无误后去掉该 flag 真实执行。

示例变体：

```bash
# 按书签保存的原始时间范围执行
sensors analytics bookmark-query --ai-session-id <ai_session_id> --bookmark-id 5 --dashboard-id 101

# 覆盖为最近 7 个完整自然日（起止以昨天为终点）
sensors analytics bookmark-query --ai-session-id <ai_session_id> --bookmark-id 5 --dashboard-id 101 --from-date 7d

# 覆盖为明确起止日期
sensors analytics bookmark-query --ai-session-id <ai_session_id> --bookmark-id 5 --dashboard-id 101 \
  --from-date 2026-06-01 --to-date 2026-06-25

# 预览书签元信息，不执行真实查询
sensors analytics bookmark-query --ai-session-id <ai_session_id> --bookmark-id 5 --dashboard-id 101 --dry-run
```

## 输出

`--format json` 时输出（Envelope 包裹）：

```json
{
  "bookmark_id": 5,
  "bookmark_name": "周活漏斗",
  "type": "漏斗分析",
  "status": "success",
  "data": {"...": "对应分析接口的原始 response"}
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `bookmark_id` / `bookmark_name` | 书签 ID 与名称（展示名，不等于分析模型名） | `4` / `企业总数` |
| `type` | 分析类型中文名（如 事件分析 / 漏斗分析 / 留存分析），由平台原始类型转换而来 | `属性分析` |
| `status` | 执行状态：`success` / `error` / `unsupported` | `success` |
| `data` | 仅 `status=success` 时存在；对应分析模型的原始结果，结构随模型不同而不同 | `{"column_infos":[...],"detail_rows":[[126410.0]],"truncated":false}` |
| `error` | 仅 `status=error` 或 `unsupported` 时存在；说明失败原因 | `参数校验异常` |

三态结构解读：

| `status` | 含义 | 读取方式 |
|---|---|---|
| `success` | 书签执行成功 | `data` 是对应分析模型的原始 response，按 `type` 选择解释口径 |
| `error` | 执行出错 | 无 `data`；`error` 说明失败原因（常见为书签保存的查询参数与当前数据结构不兼容） |
| `unsupported` | 书签类型不在可执行列表 | 无 `data`；原样透传，不改写查询或用 SQL / HTTP 兜底 |

单书签 / 批量 / 混合的输出结构：

- 单书签：一次调用产出一个上述 Envelope 对象，`status` 三选一。
- 批量与混合：CLI 不提供整板聚合输出，调用方逐书签调用后得到一组独立 Envelope；汇总时按 `status` 分桶统计（成功 X 个 / 错误 Y 个 / 不支持 Z 个），再逐书签列出 `bookmark_name`、`type`、`status` 与关键结论或错误摘要。`error` 与 `unsupported` 属于结构事实，不得静默跳过。

可执行的书签类型（平台原始类型，输出为对应中文名，共 11 种）：`SEGMENTATION_MODEL`（事件分析）、`DISTRIBUTION_MODEL`（分布分析）、`FUNNEL_MODEL`（漏斗分析）、`RETENTION_MODEL`（留存分析）、`INTERVAL_MODEL`（间隔分析）、`ATTRIBUTION_MODEL`（归因分析）、`LTV_MODEL`（LTV 分析）、`SESSION_MODEL`（Session 分析）、`BEHAVIOR_PATH_MODEL`（路径分析）、`CUSTOM_SQL_MODEL`（自定义查询）、`USER_ANALYTICS_MODEL`（属性分析）；其余类型（如指标分析 `FANCY_METRIC_MODEL`）返回 `status: unsupported`。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `书签 ID X 在 Dashboard Y 中不存在` | 书签与看板不匹配，或书签已被删除 | 先 `dashboard-get --id <dashboard_id>` 复核书签列表 |
| `--to-date` 单独传报错 | 未同时提供 `--from-date` | 补传 `--from-date`，或改用 `Nd` 相对日期 |
| 日期格式 / 顺序错误 | 非 `yyyy-MM-dd` / `Nd`、非法日历日期、from 晚于 to | 按错误提示改用合法格式与顺序 |
| `status: error` | 书签保存的查询参数执行失败或与当前结构不兼容 | 原样返回 `error`；书签可能需要在平台侧更新 |
| `status: unsupported` | 书签类型不在可执行列表 | 原样返回，不改写查询或用 SQL / HTTP 兜底 |
| 结果与平台 UI 口径不一致 | 时间覆盖、采样或缓存差异 | 说明本次实际查询时间范围，保留结构事实由调用方判断 |

## 使用约束

- 单次只执行一个书签；执行整个看板的全部书签由调用方基于 `dashboard.get` 的 `bookmarks[]` 自行编排逐个调用。
- `error` 与 `unsupported` 必须原样透传，不得静默跳过或兜底改写查询。
- `data` 是原始分析结果，不做采样、截断修饰，业务解释由调用方完成。
- 本命令只执行已保存书签，不用于构造新的分析查询。
