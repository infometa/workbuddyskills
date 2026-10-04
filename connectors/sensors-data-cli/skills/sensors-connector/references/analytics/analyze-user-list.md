# 用户列表
> 工具 `analysis.user-list` · 命令 `sensors analytics user-list` · 类型 查询

## 用途

查询用户明细列表（用户细查）：按用户 ID / 用户属性 / 固定分群筛选用户，并返回指定属性列。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | string | 否 | 无 | 支持内联 JSON 对象、`-` 从 stdin 读取或文件路径；JSON 输入；`-` 从 stdin 读取，或传文件路径 | `-` |
| `--dry-run` | flag | 否 | 关闭 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |
| `--ai-session-id` | string | 是 | 无 | 服务端链路追踪的会话 ID（公共参数；`--dry-run` 模式下豁免） | `—` |
| `--format` | enum | 否 | `json` | 输出格式 `json` / `pretty`（公共参数） | `—` |
| `--project` / `--context` / `--org-id` / `--timeout` | string/int | 否 | 配置值 | 临时覆盖项目、上下文、组织与超时（默认 1800s）（公共参数） | `—` |

## 输入 Schema

`--input` JSON 顶层字段：

| 字段 | 类型 | 必填 | 约束 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `filter` | object | 否 | 过滤树 | 用户筛选；按用户 ID 用 `field: "user.$id"`；按固定分群依赖项目内已物化的分群字段（形如 `user_segment_` 前缀的用户属性，每个分群一个，是否存在因项目而异），先用 `metadata.fields`（schema `users`）确认精确字段名、经 `metadata.values` 确认取值形态后再选 function；无可用字段时走规则人群替代路径（不支持临时分群） | `{"conditions":[{"field":"user.IncomeLevel","function":"isSet","params":[]}]}` |
| `profiles` | string[] | 否 | 默认 `[]`，元素须 `user.*` 形式 | 返回属性列，如 `user.$first_id`、`user.$update_time`；空数组走服务端默认口径 | `["user.$first_id","user.$second_id","user.$update_time","user.$latest_utm_campaign","user.IncomeLevel"]` |
| `page_index` | int | 否 | 默认 `1`，> 0 | 页码（从 1 开始） | `1` |
| `page_size` | int | 否 | 默认 `30`，> 0 且 ≤ `limit` | 每页条数 | `5` |
| `limit` | int | 否 | 默认 `10000` | 返回条数上限 | `10000` |
| `use_cache` | bool | 否 | 默认 `true` | 是否使用缓存 | `true` |
| `from_date` / `to_date` | string | 否 | `yyyy-MM-dd` | 日期范围 | `2026-09-20` / `2026-09-26` |

筛选字段三类写法（`filter` 叶子条件的 `field` 取值）：

| 场景 | 字段写法 | 规则 |
|---|---|---|
| 用户 ID 查询 | `user.$id` | 直接按神策用户 ID 筛选 |
| 用户属性查询 | `user.<属性名>` | 必须带 `user.` 前缀，属性名须已确认 |
| 固定分群查询 | `user.<已确认的分群字段>` | 依赖项目把分群物化为用户属性（形如 `user_segment_` 前缀字段，每个分群一个）：先用 `metadata.fields`（schema `users`）确认项目内是否存在可用分群字段，存在则用确认到的精确字段名构造条件，取值形态经 `metadata.values` 确认后再选 function；分群内部名先经 `segment.list` / `segment.get` 确认。项目无可用分群字段时本路径不可用，改走规则人群（`analysis.personas`）或用 `segment.get` 展开规则；不支持临时分群，不要写成 `user.<分群名>` 的字段路径 |

`profiles[]` 常见可直接复用的列：`user.$first_id`、`user.$second_id`、`user.$update_time`、`user.$first_utm_campaign`、`user.$first_utm_content`。

校验速记：`profiles[]` 须 `user.` 前缀（服务端要求裸属性名会被拒，CLI 本地不拦截）；`page_index` / `page_size` 必须 > 0；`page_size` 不得超过 `limit`；分群字段必须经 `metadata.fields` 确认存在后引用。

过滤树结构见 [analytics-query-schema.md](analytics-query-schema.md)；以 `--dry-run` 请求预览与实时 `--help` 为最终事实源。

## 构造流程

业务输入到合法 JSON 的步骤化映射，按序执行：

### 第一步：定查询对象（值映射）

| 业务表达 | 筛选字段 |
|---|---|
| 「查这个用户」「查 user_id 是多少的用户」 | `user.$id` |
| 「查某个用户属性满足条件的人」 | `user.<属性名>` |
| 「查某个固定分群里的用户」 | `user.<已确认的分群字段>`（先 `metadata.fields` 确认字段，function 按取值形态选） |

按固定分群查时，先用 `metadata.fields`（schema `users`）确认项目内是否已把该分群物化为用户属性（`user_segment_` 前缀字段，每个分群一个），存在则用确认到的精确字段名构造条件，取值形态经 `metadata.values` 确认后再选 function；分群内部名先经 `segment.list` / `segment.get` 确认。临时分群不支持；项目无可用分群字段时本路径不可用，改走规则人群路径（`analysis.personas`）或用 `segment.get` 展开分群规则自行构造过滤，由调用方决定。

### 第二步：定返回列

`profiles[]` 只填 `user.<属性名>` 形式；常见列直接复用 `user.$first_id`、`user.$second_id`、`user.$update_time`、`user.$first_utm_campaign`、`user.$first_utm_content`。

### 第三步：定分页

`page_index` 默认 `1`、`page_size` 默认 `30`、`limit` 默认 `10000`；「每页 30 / 50 条」映射到 `page_size`，「最多返回 10000 条」映射到 `limit`。

### 第四步：自检并执行

对照校验速记过一遍 → `--dry-run` → 执行。

### 调用示例

按用户 ID 查询并返回指定属性列：

```bash
sensors analytics user-list --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "filter": {
    "relation": "and",
    "conditions": [
      { "field": "user.$id", "function": "equal", "params": ["3203992394217473"] }
    ]
  },
  "profiles": [
    "user.$first_id",
    "user.$second_id",
    "user.$update_time",
    "user.$first_utm_campaign",
    "user.$first_utm_content"
  ],
  "page_index": 1,
  "page_size": 30,
  "limit": 10000,
  "use_cache": true
}
__SENSORS_QUERY__
```

按固定分群筛选（先经 `metadata.fields` 确认项目内已物化的分群字段、`metadata.values` 确认取值形态后构造）：

```bash
sensors analytics user-list --ai-session-id <ai_session_id> --input - --dry-run <<'__SENSORS_QUERY__'
{
  "filter": {
    "relation": "and",
    "conditions": [
      { "field": "<已确认的分群字段>", "function": "<按取值形态选定>", "params": [<与 function 匹配的取值>] }
    ]
  },
  "profiles": ["user.$first_id", "user.$second_id", "user.gender"],
  "page_index": 1,
  "page_size": 30,
  "limit": 10000,
  "use_cache": true
}
__SENSORS_QUERY__
```

分群字段形如 `user_segment_` 前缀的用户属性（每个分群一个）；取值形态先经 `metadata.values` 确认再选 function（如布尔形态用 `isTrue` + 空 `params`，枚举形态用 `equal` + 精确取值）。项目内无可用分群字段时本示例路径不可用，改走规则人群（`analysis.personas`）或 `segment.get` 展开规则。

## 输出

不走公共 `columns` / `rows` 结构（见 [analytics-query-schema.md](analytics-query-schema.md) 公共输出一节），保留专属结构：

```json
{
  "users": [
    {
      "id": "3203992394217473",
      "first_id": "7tpEmL7hMALkIinn",
      "second_id": "",
      "distinct_id": "",
      "column_names": ["$id", "vehicle_type"],
      "profiles": { "$id": "3203992394217473", "vehicle_type": "四门轿车" }
    }
  ],
  "page": { "current_page": 1, "page_count": 1, "total": 1 }
}
```

| 字段 | 含义 | 示例值 |
|---|---|---|
| `users[].id` | 神策用户 ID（字符串，可能为负值大数） | `"3203992394217473"` |
| `users[].first_id` / `second_id` / `distinct_id` | 平台返回的关联 ID，勿与筛选字段混淆 | `12345` / `""` / `""` |
| `users[].column_names` | 本次返回的属性列名（`profiles` 去掉 `user.` 前缀） | `["$first_id","$second_id","$update_time","$latest_utm_campaign","IncomeLevel"]` |
| `users[].profiles` | 明细属性字典，键名为 `user.<属性名>` 去掉前缀后的属性名 | `{"$first_id":"12345","IncomeLevel":"3000~5000"}` |
| `page.current_page` / `page_count` / `total` | 当前页（从 1 起）/ 总页数 / 总条数 | `1` / `1` / `1` |
| `request_id` | 请求追踪 ID | `16a80cfbe35346b2a2dcbdb62686ed6c` |

`total: 0` 是合法空结果：分群字段已确认正确且查询无 SQL 报错时，直接报告空结果即可（常见原因是分群尚在计算或分群确实无用户），不进入「为什么为空」的排查循环。

## 错误

| 错误 / 现象 | 触发条件 | 修正方式 |
|---|---|---|
| `参数校验失败: page_index: Input should be greater than 0`（本地校验，英文消息） | `page_index` / `page_size` 传 0 或负数 | CLI 本地直接拦截，改为 > 0 的整数（`page_index` 从 1 起，默认补 1） |
| 服务端校验失败（message：`page_size 参数取值只能在 1 ~ limit 参数之间`） | `page_size` 超过 `limit`（默认 10000） | 改为 ≤ `limit` 的正整数 |
| `profiles` 没返回预期列 | 没写 `user.` 前缀或属性不存在 | 用 `user.<属性名>` 重新构造 |
| 分群字段不存在或失效（message 提示 `{meta_data}` 不存在或失效） | 项目未把分群物化为用户属性，或分群字段名未经确认即引用（含误写成 `user.<分群名>` 的字段路径） | 先 `metadata.fields`（schema `users`）确认是否存在可用分群字段，用确认到的精确字段名重构；无可用字段时改用规则人群路径（`analysis.personas`）或 `segment.get` 展开分群规则自行构造过滤 |
| 临时分群查不到 | 本命令只支持固定分群 | 改用固定分群，或转其它查询链路 |
| 返回 `total: 0` | 筛选条件过严、字段名不精确，或分群确实无用户 | 分群字段已验证且无 SQL 报错时属合法空结果，直接报告，不反复排查 |

## 使用约束

- 分群内部名与分群字段不得猜测：分群内部名先经 `segment.list` / `segment.get` 确认，分群字段先经 `metadata.fields` 确认；多候选拿不准时交还调用方。
- 分群字段的存在性因项目而异（取决于项目是否把分群物化为用户属性），未经 `metadata` 确认不得引用。
- `total: 0` 是正常空结果（当前筛选无匹配用户），不是查询失败，不得进入循环排查或自动放宽条件重试。
- `truncated` / 分页信息原样传回，翻页由调用方决定。
