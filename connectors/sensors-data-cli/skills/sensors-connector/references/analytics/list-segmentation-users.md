# 事件分析用户明细

> 工具 `analysis.segmentation-users` · 命令 `sensors analytics segmentation-users` · 类型 查询

## 用途

查看事件分析中触发某指标、落在某个分组值或某一天的用户列表：先由 `analysis.events` 得到指标结论，再用本工具下钻拿到具体用户（id、distinct_id、指定用户属性列）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 是 | 无 | JSON 输入；内联 JSON 对象、`-` 从 stdin 读取或文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 的分析参数（measures / date_range / unit / by_fields / filter）与 `analysis.events` 完全一致，见 [analyze-events.md](analyze-events.md)；以下为明细专有字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `slice_by_values` | string[] | 否 | 与 `by_fields` 对齐 | 按分组值下钻，取值来自 `analysis.events` 报表对应分组列的值 | `["北京"]` |
| `slice_date` | string | 否 | `yyyy-MM-dd` | 查看哪一天的用户；取值来自报表时间列 | `2026-06-08` |
| `page` | int | 否 | 默认 `1`，1 起 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，1~100 | 每页用户数 | `10` |
| `profiles` | string[] | 否 | 默认 `[]`（全部属性） | 返回的用户属性列，`user.<属性名>` 形式 | `["user.$name"]` |
| `detail` | bool | 否 | 默认 `true` | `true` 按 `profiles` 返回属性列；`false` 只返回 id 标识列 | `true` |

注意：明细命令不提供 `limit` 参数，返回量由 `page` / `page_size` 控制；时间类分组字段（如 `event.<事件>.$time`）在明细中不注入时间分桶参数，`slice_by_values` 的取值以报表返回的分组值为准。

## 构造流程

### 第一步：复用事件分析口径

分析参数（含公式指标）直接复用已验证过的 `analysis.events` 查询体。

### 第二步：定位下钻单元格

| 业务表达 | 映射 |
|---|---|
| 「看看触发过该指标的全部用户」 | 不传 `slice_by_values` / `slice_date` |
| 「看看 6 月 8 日触发该指标的用户」 | `slice_date: "2026-06-08"` |
| 「看看北京分组的用户」 | `by_fields` 含该维度 + `slice_by_values: ["北京"]` |

### 第三步：定返回列与分页

`profiles[]` 填 `user.<属性名>` 形式；`page` 从 1 起、`page_size` 1~100 默认 30。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

查看 6 月 8 日触发加购事件的用户：

```bash
sensors analytics segmentation-users --ai-session-id <ai_session_id> --input - <<'__SENSORS_QUERY__'
{
  "measures": [
    { "event": "e2e_add_to_cart", "aggregator": "general" }
  ],
  "date_range": { "from_date": "2026-05-19", "to_date": "2026-06-25" },
  "slice_date": "2026-06-08",
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

`total: 0` 是合法空结果（该指标/分组/日期无触发用户），直接报告。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: measures ...` | 指标列表为空或形态非法 | 复用 `analysis.events` 已验证的 measures |
| 服务端「事件不存在或失效」 | 事件名未经元数据确认 | 先经 `metadata.events` 确认精确事件名 |
| 返回空但报表有数据 | `slice_by_values` / `slice_date` 定位的单元格本身为空 | 对照报表确认单元格有人后再下钻 |

## 使用约束

- 分析参数必须与 `analysis.events` 报表口径完全一致；`slice_by_values` 取值必须来自报表对应分组列的真实值，不得猜测。
- `total: 0` 且无报错时是合法空结果，直接报告；不得自动放宽日期或去 filter 重试。
