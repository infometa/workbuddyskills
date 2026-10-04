# 漏斗用户明细

> 工具 `analysis.funnel-users` · 命令 `sensors analytics funnel-users` · 类型 查询

## 用途

查看漏斗分析中完成或流失在某个步骤的用户列表：先由 `analysis.funnel` 得到转化/流失结论，再用本工具下钻拿到具体用户（id、distinct_id、指定用户属性列），用于分群圈选、名单导出或个案追踪。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（steps / date_range / conversion_window / time_bucket / filter / by_fields / count_mode / subject）与 `analysis.funnel` 完全一致，见 [analyze-funnel.md](analyze-funnel.md)；以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `slice_step` | int | 否 | ≥ 0，默认最后一步 | 查看第几步的用户（0 表示第一步）；与 `analysis.funnel` 输出的步骤下标对应 | `1` |
| `wastage` | bool | 否 | 默认 `false` | `true` 查看在 `slice_step` 步流失的用户（未进入下一步）；`false` 查看完成该步的转化用户 | `true` |
| `slice_by_values` | string[] | 否 | 与 `by_fields` 对齐 | 按分组值下钻，取值来自 `analysis.funnel` 报表对应分组列的值 | `["北京"]` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始；v2 接口的 0 基分页由 CLI 自动适配） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |
| `sort_by_field` | string | 否 | 无 | 排序字段（仅 v2 接口支持（SA ≥ 3.0.4）；v1 环境忽略） | `user.$name` |
| `asc` | bool | 否 | 无 | 是否升序（仅 v2 接口支持） | `true` |

注意：明细命令不提供 `limit` 参数（服务端对明细设正数 `limit` 会破坏翻页确定性），返回量由 `page` / `page_size` 控制。

## 构造流程

### 第一步：复用漏斗口径

分析参数直接复用已验证过的 `analysis.funnel` 查询体（事件步骤、日期范围、转化窗口、分组维度），不得另造口径。

### 第二步：定位下钻单元格

| 业务表达 | 映射 |
|---|---|
| 「看看完成全部转化的用户」 | 不传 `slice_step`（默认最后一步）+ `wastage: false` |
| 「看看卡在第一步没走到第二步的用户」 | `slice_step: 0` + `wastage: true` |
| 「看看第二步的转化用户」 | `slice_step: 1` + `wastage: false` |
| 「看看北京分组里的转化用户」 | `by_fields` 含该维度 + `slice_by_values: ["北京"]` |

`slice_step` 与报表输出的步骤下标一致（0 起）；漏斗共 N 步时取值 0 ~ N-1。

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式（空为全部属性）；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看完成全部转化的用户（默认最后一步、每页 10 条、返回姓名属性）：

```bash
sensors analytics funnel-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "steps": [
    { "event": "e2e_add_to_cart" },
    { "event": "e2e_submit_order" }
  ],
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "page": 1,
  "page_size": 10,
  "profiles": ["user.$name"]
}
__SENSORS_QUERY__
```

查看第一步流失用户：

```bash
sensors analytics funnel-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "steps": [
    { "event": "e2e_add_to_cart" },
    { "event": "e2e_submit_order" }
  ],
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "slice_step": 0,
  "wastage": true,
  "page_size": 10
}
__SENSORS_QUERY__
```

## 输出

保留用户分页专属结构（不走公共 `columns` / `rows`，见 [analytics-query-schema.md](analytics-query-schema.md) 公共输出一节）：

```json
{
  "users": [
    {
      "id": "322340429274340974",
      "first_id": "e2e_user_0001",
      "second_id": "",
      "distinct_id": "",
      "profiles": { "$name": "张三" }
    }
  ],
  "page": { "current_page": 1, "page_count": 8, "total": 40 },
  "request_id": "dace272dd6414eda..."
}
```

| 字段 | 含义 | 示例值 |
|---|---|---|
| `users[].id` | 神策用户 ID（字符串） | `"322340429274340974"` |
| `users[].first_id` / `second_id` / `distinct_id` | 关联 ID 标识列 | `"e2e_user_0001"` / `""` / `""` |
| `users[].profiles` | 明细属性字典，键名为去掉 `user.` 前缀的属性名 | `{"$name":"张三"}` |
| `page.current_page` / `page_count` / `total` | 当前页（1 起）/ 总页数 / 总用户数 | `1` / `8` / `40` |
| `request_id` | 请求追踪 ID | `—` |

`total: 0` 是合法空结果（该步骤无转化/流失用户），直接报告，不进入排查循环。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: slice_step ...` | `slice_step` 超出步骤范围（> 步骤数-1） | 改为 0 ~ N-1；N 为 steps 数量 |
| `参数校验失败: steps ...` | 步骤少于 2 个或事件名为空 | 复用 `analysis.funnel` 已验证的 steps |
| 服务端「事件不存在或失效」 | 事件名未经元数据确认 | 先经 `metadata.events` 确认精确事件名 |
| 翻页结果与第一页重复/错乱 | 使用了错误的分页基（自造脚本绕过 CLI） | 始终用本命令的 `page`（1 起）；v2 的 0 基分页由 CLI 自动适配 |

## 使用约束

- 分析参数必须与 `analysis.funnel` 报表口径完全一致：先用报表确认步骤下标与分组值，再下钻；不得凭记忆构造步骤。
- `slice_by_values` 的取值必须来自报表对应分组列的真实值，不得猜测。
- 返回量大时按 `page` 翻页；`page_count` / `total` 为服务端口径，v2 接口在返回全部页时 `page_count` 可能为 0，以 `total` 为准。
- `total: 0` 且无报错时是合法空结果，直接报告；不得自动放宽日期或去 filter 重试。
