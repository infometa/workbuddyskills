# 用户路径用户明细

> 工具 `analysis.user-path-users` · 命令 `sensors analytics user-path-users` · 类型 查询

## 用途

查看路径分析中经过某个路径节点的用户列表：先由 `analysis.user-path` 得到路径图，再用本工具定位节点（事件 + 分组值 + 层数）下钻拿到具体用户（id、distinct_id、指定用户属性列）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（source_type / source_event / event_names / by_fields / col_limit / row_limit / from_date / to_date / filter / session_interval）与 `analysis.user-path` 一致，见 [analyze-user-path.md](analyze-user-path.md)；注意 `user_filter`（用户属性筛选）明细接口不支持，传入会被 CLI 拒绝。以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `slice_element_filters` | object[] | 否 | 每项 `{event, by_value?}` | 当前节点定位：`event` 为节点事件名，`by_value` 为按维度拆分时的分组值 | `[{"event":"e2e_add_to_cart"}]` |
| `next_slice_element_filters` | object[] | 否 | 同上 | 后续节点定位（查看流向下一节点的用户时使用） | `[{"event":"e2e_submit_order"}]` |
| `session_level` | int | 否 | ≥ 1 | 当前节点在路径中的层数（从 1 开始） | `1` |
| `edge_type` | string | 否 | `WASTAGE` / `RETENTION` / `ALL` | 节点统计口径：流失节点 / 后续事件统计 / 该节点合计人数 | `RETENTION` |
| `is_aggregate` | bool | 否 | 无 | 当前节点是否是聚合节点 | `false` |
| `is_next_aggregate` | bool | 否 | 无 | 下一节点是否是聚合节点 | `false` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |
| `sort_by_field` | string | 否 | 无 | 排序字段 | `user.$name` |

注意：明细命令不提供 `limit` 参数。

## 构造流程

### 第一步：先跑路径报表

`analysis.user-path` 报表必须先执行：从 `nodes`（分层节点：event_name、times）与 `links`（流向与流失）中确认要下钻的节点、层数与是否有后续。`session_interval`（Session 切割窗口）必须与报表一致，否则明细与报表节点对不上。

### 第二步：定位节点

| 业务表达 | 映射 |
|---|---|
| 「看看经过第 2 层『提交订单』节点的用户」 | `slice_element_filters: [{"event":"e2e_submit_order"}]` + `session_level: 2` |
| 「看看第 1 层节点的流失用户」 | `slice_element_filters: [{"event":"<该层事件>"}]` + `session_level: 1` + `edge_type: "WASTAGE"` |
| 「看看从节点 A 流向节点 B 的用户」 | `slice_element_filters: [A]` + `next_slice_element_filters: [B]` + 对应层数 |

`session_level` 与报表 `nodes` 的下标对应（第 1 层 = `nodes[0]`）。

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看经过第 2 层『提交订单』节点的用户：

```bash
sensors analytics user-path-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "source_type": "initial_event",
  "source_event": { "event_name": "e2e_add_to_cart" },
  "event_names": ["e2e_add_to_cart", "e2e_submit_order", "e2e_pay_order"],
  "col_limit": 3,
  "row_limit": 5,
  "from_date": "2026-05-19",
  "to_date": "2026-06-25",
  "session_interval": 2592000,
  "slice_element_filters": [{"event": "e2e_submit_order"}],
  "session_level": 2,
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

`total: 0` 可能为合法空结果：节点定位（层数/事件/edge 口径）与报表一致且无报错时，直接报告空结果并附报表节点口径。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: edge_type ...` | `edge_type` 不在 WASTAGE / RETENTION / ALL 内 | 按业务口径改为三者之一 |
| 返回 `total: 0` | 节点定位与报表不一致（层数、事件、`session_interval` 不同），或该节点本身无人 | 对照报表 `nodes` / `links` 重新定位；`session_interval` 与报表保持一致 |

## 使用约束

- 必须先运行 `analysis.user-path` 报表并以其 `nodes` / `links` 为定位依据；层数、事件名、Session 窗口（`session_interval`）都要与报表一致。
- 路径明细的节点定位依赖服务端路径计算，部分环境下明细可能返回空：定位值与报表一致且无报错时按合法空结果报告，不反复重试。
- `total: 0` 且无报错时直接报告，不自动调整层数或事件重试。
- `user_filter` 在明细中不可用（接口无该字段）：需要按用户属性筛人群时，先用 `analysis.user-path` 报表确认，或将条件改写进事件过滤。
