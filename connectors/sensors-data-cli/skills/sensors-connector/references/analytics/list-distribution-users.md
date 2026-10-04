# 分布分析用户明细

> 工具 `analysis.distribution-users` · 命令 `sensors analytics distribution-users` · 类型 查询

## 用途

查看分布分析中分布值落入某个区间的用户列表：先由 `analysis.distribution` 得到区间分布结论，再用本工具下钻拿到具体用户（id、distinct_id、指定用户属性列）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（event / measure / date_range / by_field / filter / unit / measure_type）与 `analysis.distribution` 一致，见 [analyze-distribution.md](analyze-distribution.md)；注意 `user_filter`（用户属性筛选）明细接口不支持，传入会被 CLI 拒绝。以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `slice_by_value` | string | 是 | — | 定位报表单元格：未设置 `by_field` 时传报表 `by_value` 列的日期值（`yyyy-MM-dd`）；设置了 `by_field` 时传该维度的属性值。服务端按该值精确匹配，不传会返回空 | `"2026-06-08"` |
| `slice_freq` | int | 否 | — | 区间左端点，与报表分桶区间（`bucket_region_N` 列）对齐 | `1` |
| `slice_max_freq` | int | 否 | — | 区间右端点，与 `slice_freq` 配合表示 `[slice_freq, slice_max_freq)` 区间 | `3` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |

注意：明细命令不支持自定义分桶边界（`bucket_boundaries`），按服务端默认分桶下钻；不提供 `limit` 参数。

## 构造流程

### 第一步：复用分布分析口径

分析参数直接复用已验证过的 `analysis.distribution` 查询体（事件、分布对象、日期范围）。

### 第二步：从报表取定位值（关键）

先运行 `analysis.distribution` 报表，从结果中取两个定位值：

| 报表列 | 用途 | 映射 |
|---|---|---|
| `by_value` | 单元格定位 | 无 `by_field` 时是日期（如 `2026-06-08`）→ `slice_by_value`；有 `by_field` 时是维度值 → `slice_by_value` |
| `bucket_region_N` | 区间定位 | 如 `[1, 3)` → `slice_freq: 1` + `slice_max_freq: 3` |

`slice_by_value` 必填：不传或传错值时服务端按空值精确匹配，恒返回 0 用户。

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看 6 月 8 日加购次数落在 [1,3) 区间的用户：

```bash
sensors analytics distribution-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "event": "e2e_add_to_cart",
  "measure": { "event": "e2e_add_to_cart", "aggregator": "general" },
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "slice_by_value": "2026-06-08",
  "slice_freq": 1,
  "page": 1,
  "page_size": 10
}
__SENSORS_QUERY__
```

## 输出

保留用户分页专属结构（不走公共 `columns` / `rows`），结构与 [list-funnel-users.md](list-funnel-users.md) 输出一节一致：

```json
{
  "users": [
    { "id": "322340429274340974", "first_id": "e2e_user_0001", "second_id": "", "distinct_id": "", "profiles": {} }
  ],
  "page": { "current_page": 1, "page_count": 8, "total": 40 },
  "request_id": "..."
}
```

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: slice_by_value: Field required` | 未传单元格定位值 | 从 `analysis.distribution` 报表 `by_value` 列取值填入 |
| `参数校验失败: ... bucket_boundaries` | 明细输入带了自定义分桶边界 | 去掉 `bucket_boundaries`；区间用 `slice_freq` / `slice_max_freq` 定位 |
| 返回 `total: 0` | `slice_by_value` 与报表单元格不匹配，或该区间无人 | 对照报表 `by_value` 与 `bucket_region_N` 列重取定位值；确认匹配后 0 为合法空结果 |

## 使用约束

- `slice_by_value` 的取值必须来自报表 `by_value` 列（无 `by_field` 时是日期，有 `by_field` 时是维度值），不得猜测。
- 明细使用服务端默认分桶；要自定义分桶请用 `analysis.distribution` 报表命令。
- `total: 0` 且定位值已对照报表确认时是合法空结果，直接报告。
- `user_filter` 在明细中不可用（接口无该字段）：需要按用户属性筛人群时，先用 `analysis.distribution` 报表确认，或将条件改写进事件过滤。
