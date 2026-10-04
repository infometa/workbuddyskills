# LTV 用户明细

> 工具 `analysis.ltv-users` · 命令 `sensors analytics ltv-users` · 类型 查询

## 用途

查看 LTV 分析中某个起始日期（cohort）的用户列表：先由 `analysis.ltv` 得到生命周期价值结论，再用本工具下钻拿到该 cohort 的具体用户（id、distinct_id、指定用户属性列）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（start_sign / measures / date_range / time_bucket / duration / by_fields / filter / subject_id）与 `analysis.ltv` 完全一致，见 [analyze-ltv.md](analyze-ltv.md)；以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `slice_date` | string | 否 | `yyyy-MM-dd` | 查看哪个起始日期（cohort）的用户；取值来自 `analysis.ltv` 报表的 cohort 日期列，不传表示全部日期 | `2026-06-09` |
| `slice_by_values` | string[] | 否 | 与 `by_fields` 对齐 | 按分组值下钻，取值来自报表对应分组列的值 | `["北京"]` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |
| `sort_by_field` | string | 否 | 无 | 排序字段（如 `user.$name`） | `user.$name` |

注意：明细命令不提供 `limit` 参数，返回量由 `page` / `page_size` 控制。

## 构造流程

### 第一步：复用 LTV 口径

分析参数直接复用已验证过的 `analysis.ltv` 查询体（起点定义、营收事件、周期粒度与观测数）。

### 第二步：定位 cohort

| 业务表达 | 映射 |
|---|---|
| 「看看全部起始日期的用户」 | 不传 `slice_date` |
| 「看看 6 月 9 日这批起始用户的名单」 | `slice_date: "2026-06-09"`（取自报表 cohort 日期列） |
| 「看看北京分组的起始用户」 | `by_fields` 含该维度 + `slice_by_values: ["北京"]` |

`slice_date` 是 cohort 起始日期（用户首次触发起点事件的日期），不是 LTV 周期列。

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看全部起始日期的用户名单：

```bash
sensors analytics ltv-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "start_sign": { "start_event": "e2e_submit_order" },
  "measures": [ { "event": "e2e_pay_order", "aggregator": "average" } ],
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "page": 1,
  "page_size": 10,
  "profiles": ["user.$name"]
}
__SENSORS_QUERY__
```

## 输出

保留用户分页专属结构（不走公共 `columns` / `rows`），结构与 [list-funnel-users.md](list-funnel-users.md) 输出一节一致：

```json
{
  "users": [
    { "id": "322340429274340974", "first_id": "e2e_user_0001", "second_id": "", "distinct_id": "", "profiles": { "$name": "张三" } }
  ],
  "page": { "current_page": 1, "page_count": 8, "total": 40 },
  "request_id": "..."
}
```

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: start_sign ...` | 起点未配置或同时配了事件与时间属性 | 复用 `analysis.ltv` 已验证的 start_sign（二选一） |
| 返回 `total: 0` 但报表有数据 | `slice_date` 不是报表 cohort 日期列的值 | 从报表结果的日期列取精确值（cohort 日期 ≠ 事件日期） |

## 使用约束

- 分析参数必须与 `analysis.ltv` 报表口径完全一致；`slice_date` 取自报表 cohort 日期列，不得猜测。
- `total: 0` 且无报错时是合法空结果，直接报告。
