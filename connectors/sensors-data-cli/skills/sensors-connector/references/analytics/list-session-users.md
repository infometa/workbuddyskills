# Session 用户明细

> 工具 `analysis.session-users` · 命令 `sensors analytics session-users` · 类型 查询

## 用途

查看 Session 分析中满足 Session 指标的用户列表：先由 `analysis.session` 得到会话口径结论，再用本工具下钻拿到具体用户（id、distinct_id、指定用户属性列）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（event / date_range / session_name / by_fields / unit）与 `analysis.session` 完全一致，见 [analyze-session.md](analyze-session.md)；以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `slice_date` | string | 是 | `yyyy-MM-dd` | 查看哪一天的用户；取值来自 `analysis.session` 报表的时间列。服务端不传时按 `from_date` 过滤，通常应传有数据的日期 | `2026-06-08` |
| `slice_by_values` | string[] | 否 | 与 `by_fields` 对齐 | 按分组值下钻，取值来自报表对应分组列的值 | `["北京"]` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |

注意：`session_name` 必须是平台已有 Session 定义（`analysis.session-list` 查询）；明细命令不提供 `limit` 参数。

## 构造流程

### 第一步：确认 Session 定义

`session_name` 先经 `analysis.session-list` 确认存在；不存在时不可用（创建走 `analysis.session-create`，需写权限）。

### 第二步：从报表取日期

先运行 `analysis.session` 报表，从结果时间列取有数据的日期填入 `slice_date`（必填；服务端默认按 `from_date` 过滤，通常为空）。

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看 6 月 8 日 Session 内触发加购的用户：

```bash
sensors analytics session-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "event": { "event": "e2e_add_to_cart" },
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "session_name": "test",
  "slice_date": "2026-06-08",
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
| `参数校验失败: slice_date: Field required` | 未传日期 | 从 `analysis.session` 报表时间列取值填入 |
| 返回 `total: 0` 但报表有数据 | `slice_date` 不是报表时间列的值，或该日无 Session 数据 | 对照报表日期列重取精确值 |
| Session 名不存在 | `session_name` 未经确认 | 先 `analysis.session-list` 确认英文名 |

## 使用约束

- `session_name` 必须先经 `analysis.session-list` 确认，不得猜测。
- `slice_date` 必填且取自报表时间列；不传会被服务端按 `from_date` 过滤而返回空。
- `total: 0` 且无报错时是合法空结果，直接报告。
