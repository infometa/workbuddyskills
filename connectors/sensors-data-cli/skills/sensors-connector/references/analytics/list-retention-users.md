# 留存用户明细

> 工具 `analysis.retention-users` · 命令 `sensors analytics retention-users` · 类型 查询

## 用途

查看留存分析中某个日期、某个留存周期的留存或流失用户列表：先由 `analysis.retention` 得到留存率结论，再用本工具下钻拿到具体用户（id、distinct_id、指定用户属性列），用于回访人群圈选或流失用户追踪。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（initial_event / return_event / date_range / unit / duration / user_filter / by_fields）与 `analysis.retention` 完全一致，见 [analyze-retention.md](analyze-retention.md)；注意 `user_filter` 仅 v2 接口支持（SA ≥ 3.0.4），v1 环境传入会报错。以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `wastage` | bool | 否 | 默认 `false` | `true` 查看流失用户（初始行为后未回访）；`false` 查看留存用户 | `false` |
| `slice_date` | string | 否 | `yyyy-MM-dd` | 查看哪一天（初始行为日）的用户；取值来自 `analysis.retention` 报表的日期列 | `2026-06-01` |
| `slice_interval` | int/string | 否 | 数字或数字字符串 | 查看第几个留存周期：`0` 表示当天（首日），`3` 表示第 3 个周期；不传表示全部周期 | `0` |
| `slice_by_value` | string | 否 | — | 按分组值下钻，取值来自 `by_fields` 分组字段的维度值 | `"北京"` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |
| `sort_by_field` | string | 否 | 无 | 排序字段（仅 v2 接口支持） | `user.$name` |
| `asc` | bool | 否 | 无 | 是否升序（仅 v2 接口支持） | `true` |

注意：`by_fields` 在明细命令中最多 1 个分组维度（接口限制）；明细命令不提供 `limit` 参数，返回量由 `page` / `page_size` 控制。

## 构造流程

### 第一步：复用留存口径

分析参数直接复用已验证过的 `analysis.retention` 查询体（初始/回访事件、日期范围、周期粒度与观测数）。

### 第二步：定位下钻单元格

| 业务表达 | 映射 |
|---|---|
| 「看看 6 月 1 日这批人的次日留存用户」 | `slice_date: "2026-06-01"` + `slice_interval: 1` + `wastage: false` |
| 「看看当天的留存用户」 | `slice_date` + `slice_interval: 0` |
| 「看看 6 月 1 日这批人的流失用户」 | `slice_date` + `wastage: true` |
| 「看看北京分组的留存用户」 | `by_fields: ["first.$country"]` + `slice_by_value: "北京"` |

`slice_interval` 与报表的留存周期列一致（0 = 首日，N = 第 N 个周期）；`slice_date` 是初始行为日期，来自报表日期列。

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看 6 月 1 日初始行为用户当天的留存用户：

```bash
sensors analytics retention-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "initial_event": { "event": "e2e_submit_order" },
  "return_event": { "event": "e2e_pay_order" },
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "slice_date": "2026-06-01",
  "slice_interval": 0,
  "page": 1,
  "page_size": 10,
  "profiles": ["user.$name"]
}
__SENSORS_QUERY__
```

查看流失用户：

```bash
sensors analytics retention-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "initial_event": { "event": "e2e_submit_order" },
  "return_event": { "event": "e2e_pay_order" },
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "wastage": true,
  "page_size": 10
}
__SENSORS_QUERY__
```

## 输出

保留用户分页专属结构（不走公共 `columns` / `rows`，见 [analytics-query-schema.md](analytics-query-schema.md) 公共输出一节）；结构与 [list-funnel-users.md](list-funnel-users.md) 输出一节一致：

```json
{
  "users": [
    { "id": "322340429274340974", "first_id": "e2e_user_0001", "second_id": "", "distinct_id": "", "profiles": { "$name": "张三" } }
  ],
  "page": { "current_page": 1, "page_count": 8, "total": 40 },
  "request_id": "..."
}
```

`users[].profiles` 键名为去掉 `user.` 前缀的属性名；`page.current_page` 从 1 起。`total: 0` 是合法空结果（该日期/周期无留存或流失用户），直接报告。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: ... 分组维度` | `by_fields` 传了超过 1 个维度 | 明细仅支持单分组维度；多维度分析用 `analysis.retention` 报表 |
| `参数校验失败: slice_interval ...` | 传入非数字（如 `day1`） | 传整数或数字字符串：`0`、`3`、`"7"` |
| 服务端「事件不存在或失效」 | 事件名未经元数据确认 | 先经 `metadata.events` 确认精确事件名 |
| 返回空但报表有数据 | `slice_date` / `slice_interval` 定位的单元格本身为空 | 对照报表确认该日期×周期的格子有人后再下钻 |

## 使用约束

- 分析参数必须与 `analysis.retention` 报表口径完全一致：先用报表确认日期列与周期列，再下钻。
- 版本路由：SA ≥ 3.0.4 走 v2 明细接口（支持 `user_filter` / `sort_by_field`），旧版本走 v1；CLI 统一 1-based page，分页字段自动适配。
- 已知服务端问题（部分版本如 SA 3.0.5.314 实测）：v2 明细翻页结果可能无稳定排序、`page.current_page` 回显差一；名单结论以 `total` 为准，翻页异常时如实上报 request_id，不反复重试。
- v1 环境不支持 `user_filter`（接口无该字段）：需要按用户属性筛人群时，先用 `analysis.retention` 报表确认，或将条件改写进事件过滤。
- `slice_date` + `slice_interval` 定位的单元格应先用报表确认有用户；`total: 0` 且无报错时是合法空结果，直接报告。
