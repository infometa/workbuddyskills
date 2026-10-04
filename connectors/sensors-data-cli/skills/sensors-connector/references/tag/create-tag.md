# tag.create 创建标签

> 工具 `tag.create` · 命令 `sensors tag create` · 类型 写入

## 用途

创建标签定义，或先向服务端发送 `dry_run=true` 只校验不落库；真实创建同时完成 AI Agent 目录挂载。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--input` | string | 是（或 `--schema`） | — | JSON 输入；`-` 从 stdin 读，也可传文件路径；包含 `definition` 和可选 `rule_draft` | `-` |
| `--schema` | flag | 否 | 关 | 输出完整 JSON 输入 Schema，不读取配置、不访问网络 | `—` |
| `--dry-run` | flag | 否 | 关 | 向服务端发送 `dry_run=true`，只校验不落库 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` / `--schema` 豁免）。

调用示例（预览与执行变体）：

```bash
sensors tag create --ai-session-id <ai_session_id> --dry-run --input request.json --format json
sensors tag create --ai-session-id <ai_session_id> --input request.json --format json
```

## 输入 Schema

`--input` 顶层字段：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `definition` | object | 是 | 标签定义外壳：`name`（必填机器名）、`display_name`、`data_type`、`trigger`、`storage_settings` 等；规则条件不放这里 | `{"name":"user_tag_agent_demo_eql","display_name":"Agent演示EQL标签"}` |
| `rule_draft` | object | 二选一 | 结构化规则草稿，由 CLI Builder 转换最终 expression | `{"create_type":"TAG_EQL","value_expression":{"expression":"user.cname"}}` |
| `definition.expression` | object | 二选一 | 已完成转换的 Horizon 最终规则（完整 Definition 模式，须同时含 `entity_name`、`create_type`） | `{"tag_type":"EQL_BASED","eql_based_rule":{"value_expression":"user.cname"}}` |
| `dry_run` | bool | 否 | 请求服务端只校验不持久化；命令层 `--dry-run` flag 等效且优先 | `true` |
| `skip_rule_check` | bool | 否 | 跳过服务端规则校验；保持省略或 `false`，禁止设为 `true` | `—` |

`definition.name`（机器名）服务端命名契约：须匹配正则 `^[a-z][a-z\d_]{0,99}$`（小写字母开头，仅含小写字母 / 数字 / 下划线，总长 ≤100），且以按实体名派生的 `<实体名>_tag_` 前缀开头（实体 `user` 即 `user_tag_<名称>`）；历史兼容前缀 `user_tag_`、`tag_` 亦可。违反时服务端返回 code 131-1 参数错误（如 `tag definition name, not start with '<实体名>_tag_'`）。

规则来源二选一约束：`rule_draft` 与 `definition.expression` 必须恰好提供一个，同时提供或都不提供都会校验失败。

创建类型与输入形状对应（`rule_draft.create_type` 判别联合，当前 CLI 仅支持以下四种；导入标签等不支持通过本命令创建）：

| `create_type` | 语义 | `rule_draft` 输入形状 | 生成规则类型 |
| --- | --- | --- | --- |
| `TAG_EQL` | 单一标签值：值直接取表达式，或由条件树推出布尔/固定值 | `value_expression`（值表达式）或 `rule`（EQL 条件树）二选一；可选 `filter_expression` | `EQL_BASED` |
| `TAG_CUSTOMIZED_RULE` | 多个标签值分层，每层独立人群条件 | `layers[]` 标签值分层（唯一可组装形状；Schema 中的兼容字段 `rule` 会被 Builder 拒绝，不可使用） | `SEGMENT_BASED`（分层） |
| `TAG_GENERAL_RULE_DISTRIBUTION` | 按事件指标聚合结果分桶成多档标签值 | `rule` 为指标分布分桶（事件 + 聚合 + 分桶） | `BASIC_MEASURE_BASED` |
| `TAG_SQL` | 用显式提供的完整 SQL 产出标签值 | `rule.sql` 为用户显式提供的完整 SQL | `SQL_BASED` |

各类型规则对象的完整结构与 JSON 示例见 [tag-rule-schema.md](tag-rule-schema.md)。以 `--schema` 实时输出为最终事实源。

## 构造流程

命令层固定步骤：Rule Draft 组装 → 服务端 dry-run 预览 → 精确 `Approved` → 真实创建。

1. 判断输入来源：调用方已提供完整最终规则（含 `definition.expression`）走完整 Definition 模式；业务描述走 `rule_draft` 草稿模式，由 CLI Builder 转换最终 Horizon expression，不手写最终 expression。
2. 元数据绑定：规则引用的事件、属性、枚举值、已有标签和分群，先用对应查询命令确认准确名称与 `data_type` 后再写入规则；无法唯一确定时交由调用方消解，不猜测、不沿用示例名称。`$time`、`$day` 等契约明确的平台内置字段无需单独查询，但其所属事件必须真实存在并已确认。
3. 生成 JSON 输入（内联 / 文件 / stdin），只包含 `definition` 与二选一的规则来源；`definition` 至少提供稳定的机器名 `name`，按 `<实体名>_tag_` 派生前缀构造（实体 `user` 即 `user_tag_<名称>`），并满足「输入 Schema」命名契约的正则与长度约束。
4. 预览：`sensors tag create --ai-session-id <ai_session_id> --dry-run --input request.json --format json`，服务端只校验不落库。
5. 向调用方展示最终 Definition 与服务端校验结果，等待精确 `Approved`（`approved`、`同意`、`Approved.` 等均不等价）。
6. 执行：`sensors tag create --ai-session-id <ai_session_id> --input request.json --format json`，输入必须与 dry-run 完全相同；批准后不得改名、改规则或切换创建类型。
7. 真实创建内部完成定义创建与 AI Agent 目录挂载两步，结果解读见「输出」。
8. 创建成功后用 `tag.get` 回读验证；`trigger.trigger_type` 为 `MANUAL` 且需要立即出值时，用下方命令触发计算（是否执行由调用方决定，非手动触发标签不适用）。

```bash
sensors tag evaluate --ai-session-id <ai_session_id> --entity-name 'user' --input '[{"tag_definition_name":"<tag_name>"}]' --format json
```

失败处理（命令层事实，三分支）：

1. **规则或参数校验失败**：按服务端错误只修正受影响的字段后重跑 dry-run；修正上限一次，仍失败则停止并如实转达错误原文，不自动改名、不切换规则形态、不放宽条件。
2. **元数据对象不存在**（引用的事件 / 属性 / 枚举 / 标签 / 分群未找到）：停止构造，回到元数据解析协议确认对象后重试；不凭口头确认继续。
3. **写开关未开启**：停止并转达开启指引，不绕过。

名称、规则、时间范围、阈值或元数据变化后，旧输入的 dry-run 结果与 `Approved` 全部失效，必须重新预览并重新确认。

规则对象构造映射（业务输入 → 合法 JSON）：

| 业务输入形态 | 对应 `rule_draft` 写法 |
| --- | --- |
| 满足一组条件打一个固定/布尔值 | `TAG_EQL` + `rule` 条件树；布尔形态须 `definition.data_type="BOOL"` |
| 标签值直接取用户属性或简单表达式 | `TAG_EQL` + `value_expression.expression`（形如 `user.<属性名>`） |
| 多个命名层级、每层一组独立条件 | `TAG_CUSTOMIZED_RULE` + `layers[]`（`tag` 为层值、`segment` 为条件） |
| 指标按数值/百分位区间分桶成多档 | `TAG_GENERAL_RULE_DISTRIBUTION` + `rule`（`bucket_type` / `values` / `buckets`） |
| 调用方显式提供的完整 SQL | `TAG_SQL` + `rule.sql` |

标签值设计（字段层规则）：

- BOOL 标签：`definition.data_type` 必须显式声明 `"BOOL"`（遗漏会被解释为数值/字符串），且用 `rule` 条件树而非 `value_expression`；条件全部成立 → 标签值 `true`，任一不成立 → `false`；`value_expression` 与 BOOL 形态不兼容。
- 分层标签：`layers[].tag` 同一规则内唯一且非空，顺序即分层顺序；每层 `segment` 独立表达条件，不把不同标签值的条件合并。
- 分桶标签：`values` 顺序必须与 `buckets` 分桶顺序一致；`NUMBER` / `PERCENT` 要求 `values`、`buckets` 非空，`DISCRETE` 要求二者为空。

## 输出

```json
{
  "definition": { "…": "CLI 构建后的完整定义（含 create_type、规则 expression 与默认值）" },
  "result": { "…": "服务端创建或 dry-run 校验结果" },
  "catalog_binding": { "…": "真实创建时的 AI Agent 目录挂载结果" }
}
```

命令层事实：采用 `rule_draft` 时，CLI Builder 自动补全默认值（`entity_name=user`、`data_type=STRING`、`visible=true`、`status=TAG_ACTIVE`、来源类别 `TAG_AGENT` 等）并生成最终 expression；未提供 `trigger` 时默认 `MANUAL`。真实创建（非 dry-run）内部完成定义创建与 AI Agent 目录挂载两步：

- 返回含 `catalog_binding`：两步均成功，完整创建成功。
- `stage=catalog_binding`、`partial_success=true`：标签已创建，但目录挂载失败；保留创建结果与平台错误，不得重复执行创建（避免名称重复）。
- `stage=tag_creation`、`partial_success=false`：定义本身未创建成功，保留平台错误语义。

写开关（`write_operations_enabled`）关闭时命令直接拒绝执行，dry-run 与真实创建同样受限。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：必须提供 `--input` 或使用 `--schema` | 两者都未提供 | 提供输入或先查看 Schema |
| UsageError：`--input` 必须是 JSON 对象 | 输入不是对象 | 改为 JSON 对象（内联、文件或 stdin） |
| UsageError：输入校验失败 | 二选一约束、`create_type` 非法、未知字段、分桶/分层结构不匹配 | 按错误信息对照 `--schema` 修正输入；只改受影响字段后重跑 dry-run |
| 写操作未开启 | 配置 `write_operations_enabled=false` | 停止执行，如实转达 CLI 报错与开启指引，不绕过、不改配置、不编造结果 |
| 部分成功（目录挂载失败） | 标签已创建但绑定 AI Agent 目录失败 | 如实报告两阶段状态，不重复执行创建（避免名称重复） |
| 服务端命名校验失败（code 131-1，`tag definition name, not start with '<实体名>_tag_'` 等） | 机器名缺派生前缀、含大写或非法字符、总长超 100（不匹配 `^[a-z][a-z\d_]{0,99}$`） | 按派生前缀 `<实体名>_tag_`（实体 `user` 即 `user_tag_<名称>`）与正则重写机器名后重跑 dry-run |
| 服务端校验错误（dry-run 或真实创建） | 规则非法、名称重复、SQL 不合规、元数据不存在等 | 转达服务端错误原文；按错误修正后重试 dry-run，不改写为创建成功 |

## 使用约束

- 真实写入前按 SKILL.md「写操作安全联锁」完成读取现状、预览与确认；确认语为精确的 `Approved`（`approved`、`同意`、`Approved.` 等均不等价），输入或目标变化后确认失效。
- `--dry-run` 服务端校验通过不等于已创建；真实创建须使用与 dry-run 相同的输入。
- `TAG_SQL` 的 SQL 必须由调用方显式提供，CLI 不生成或改写 SQL；`skip_rule_check` 不设为 `true`。
- 创建成功后按目标能力用 `tag.get` 回读验证；回读失败不得宣称最终状态已验证。
