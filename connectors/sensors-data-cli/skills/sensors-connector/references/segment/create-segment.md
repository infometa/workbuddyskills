# segment.create 创建分群

> 工具 `segment.create` · 命令 `sensors segment create` · 类型 写入

## 用途

创建分群定义，或先向服务端发送 `dry_run=true` 只校验不落库。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--input` | string | 是（或 `--schema`） | — | JSON 输入；`-` 从 stdin 读，也可传文件路径；包含 `segment_definition` 和可选 `rule_draft` | `request.json` |
| `--schema` | flag | 否 | 关 | 输出完整 JSON 输入 Schema，不读取配置、不访问网络 | `—` |
| `--dry-run` | flag | 否 | 关 | 向服务端发送 `dry_run=true`，只校验不落库 | `—` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（真实请求必填；`--dry-run` / `--schema` 豁免）。

## 输入 Schema

`--input` 顶层字段：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `segment_definition` | object | 是 | 分群定义外壳：`name`（必填机器名）、`display_name`、`trigger`、`storage_settings` 等 | `{"name":"user_segment_agent_dryrun_eql_demo","display_name":"dry-run EQL 示例"}` |
| `rule_draft` | object | 二选一 | 结构化规则草稿，由 CLI Builder 转换最终 expression | `{"create_type":"EQL","rule":{…}}` |
| `segment_definition.segment_rule_ref.expression` | object | 二选一 | 已完成转换的 Horizon 最终规则（完整 Definition 模式；该模式下 `name`、`entity_name`、`create_type`、`expression` 四者必填） | `—` |
| `dry_run` | bool | 否 | 请求服务端只校验不持久化；命令层 `--dry-run` flag 等效且优先 | `true` |
| `skip_rule_check` | bool | 否 | 跳过服务端规则校验；保持省略或 `false` | `—` |

`segment_definition.name`（机器名）服务端命名契约：须匹配正则 `^[a-z][a-z\d_]{0,99}$`（小写字母开头，仅含小写字母 / 数字 / 下划线，总长 ≤100），且以按实体名派生的 `<实体名>_segment_` 前缀开头（实体 `user` 即 `user_segment_<名称>`）；历史兼容前缀 `user_group_`、`segment_` 亦可。违反时服务端返回 code 131-1 参数错误（如 `segment definition name, not start with '<实体名>_segment_'`）。

规则来源二选一约束：`rule_draft` 与 `segment_rule_ref.expression` 必须恰好提供一个，同时提供或都不提供都会校验失败。

创建类型与输入形状对应（`rule_draft.create_type` 判别联合）：

| `create_type` | `rule_draft` 输入形状 | 适用业务输入 |
| --- | --- | --- |
| `EQL` | `rule` 为可转 EQL 的条件树（不含 `event_sequence`） | 普通用户属性、事件、标签或分群条件，无行为先后顺序 |
| `CUSTOMIZED_RULE` | `rule` 为可扩展条件树，支持普通条件、标签/分群过滤与 `event_sequence` 行为序列 | 多组规则、复杂组合、行为先后顺序（先 A 再 B） |

类型判定要点：不因规则校验失败自动切换 `create_type`；形态有歧义时按业务差异（是否包含行为先后顺序）确认后再定。完整判定规则与字段结构见 [segment-rule-schema.md](segment-rule-schema.md)。

当前 CLI 仅支持以上两种创建类型；SQL 分群、导入分群等不支持通过本命令创建。

条件树、过滤、`time_range`、调度字段（`trigger` / `storage_settings`）的规则对象结构见 [segment-rule-schema.md](segment-rule-schema.md)；行为序列条件结构见 [segment-event-sequence-schema.md](segment-event-sequence-schema.md)。

以 `--schema` 实时输出为最终事实源。

## 构造流程

从业务输入到创建执行的命令层步骤：

### 1. 确定规则来源

判断输入是完整 Definition（调用方已提供最终 `expression`）还是业务规则（组装 `rule_draft`）。业务规则按 [segment-rule-schema.md](segment-rule-schema.md) 组装，事件、属性、标签、分群等标识符必须已经元数据查询确认。

### 2. 业务输入映射为 Rule Draft

| 已确认的业务输入 | 映射目标 |
| --- | --- |
| 分群机器名 / 显示名 | `segment_definition.name` / `display_name`；机器名按 `<实体名>_segment_` 派生前缀构造（实体 `user` 即 `user_segment_<名称>`），并满足「输入 Schema」命名契约的正则与长度约束 |
| 调度意图（手动 / 每天 N 点 + 保留份数） | `trigger.trigger_type` / `cron_trigger.crontab_exp` / `storage_settings.version_count` |
| 用户属性条件（属性、类型、操作符、阈值） | `type=user_attribute` 的 `field` / `data_type` / `operator` / `value` |
| 做过 / 没做过某事件 | `event_occurrence` / `event_absence` + `time_range` |
| 次数 / 去重天数 / 聚合指标阈值 | `event_count` / `event_day_distribution` / `event_metric` |
| 标签值条件 | `tag_filter`（`tag` 填准确标签名） |
| 属于 / 不属于某分群 | `segment_filter`（`INCLUDE` / `EXCLUDE`，`segment` 填分群内部 `name`） |
| 先 A 后 B、N 天内 | `event_sequence.steps` + `window`（仅 `CUSTOMIZED_RULE`） |
| 近 N 天 / 固定区间 / 全部历史 | `time_range`：`relative` / `static` / `all_time` |
| 且 / 或 / 非 | 条件组 `relation`（AND / OR / NOT，NOT 只能含一个条件）与嵌套组 |

### 3. 生成输入并 dry-run

生成只含 `segment_definition` 与二选一规则来源的 JSON（文件或 stdin payload），执行服务端校验：

```bash
sensors segment create --ai-session-id <ai_session_id> --dry-run --input request.json --format json
```

预览输出怎么读：`segment_definition` 是 CLI Builder 构建后的完整定义（含补全默认值、`create_type` 与最终 expression），`result` 是服务端校验结果；向调用方原样展示这两个对象。dry-run 成功仅代表校验通过，不代表已创建。

### 4. 确认后执行

收到精确 `Approved` 后，用与 dry-run 完全相同的输入真实创建（不得改名、改规则或切换创建类型）：

```bash
sensors segment create --ai-session-id <ai_session_id> --input request.json --format json
```

### 5. 回读验证

创建成功后用 `segment.get` 回读验证。`trigger_type=MANUAL` 的分群创建后不会自动计算，首个计算结果需通过 `segment evaluate` 触发（见 [evaluate-segment.md](evaluate-segment.md)）。

调用示例变体（EQL / CUSTOMIZED_RULE 普通 / 事件序列 / 同层混合四种完整 JSON payload）见 [segment-rule-schema.md](segment-rule-schema.md)「完整示例」。

## 输出

```json
{
  "segment_definition": { "…": "CLI 构建后的完整定义（含 create_type、规则 expression 与默认值）" },
  "result": { "…": "服务端创建或 dry-run 校验结果" }
}
```

命令层事实：采用 `rule_draft` 时，CLI Builder 自动补全默认值（`entity_name=user`、`visible=true`、`status=ACTIVE`、来源类别 `SEGMENT_AGENT` 等）并生成最终 expression；未提供 `trigger` 时默认 `MANUAL`。真实创建（非 dry-run）前，命令自动注册定义来源；写开关（`write_operations_enabled`）关闭时命令直接拒绝执行。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：必须提供 `--input` 或使用 `--schema` | 两者都未提供 | 提供输入或先查看 Schema |
| UsageError：`--input` 必须是 JSON 对象 | 输入不是对象 | 改为 JSON 对象（内联、文件或 stdin） |
| UsageError：输入校验失败 | 二选一约束、`create_type` 非法、未知字段、结构不匹配 | 按错误信息对照 `--schema` 修正输入 |
| 写操作未开启 | 配置 `write_operations_enabled=false` | 停止执行，转达开启指引，不绕过 |
| 服务端校验错误（dry-run 或真实创建） | 见下方分类 | 按错误性质修正；修正后最多重试 1 次 dry-run |

服务端校验错误的分类处理（字段级修正指引）：

| 错误性质 | 典型表现 | 修正方式 |
| --- | --- | --- |
| 规则 / 参数校验错误 | "请求的参数转换错误"、HTTP 5xx、枚举 / 结构非法 | 对照 [segment-rule-schema.md](segment-rule-schema.md) 核对 `rule_draft` 契约字段：`filters` 的 `operator` 与 `data_type` 兼容性、`value` 类型是否匹配、`IS_NULL` / `IS_NOT_NULL` 是否误传 `value`、step 过滤是否用了 8 个支持操作符之外的操作符、`event_sequence` 是否被放入嵌套条件组 |
| 机器名命名校验失败 | code 131-1 参数错误，如 `segment definition name, not start with '<实体名>_segment_'`；触发：机器名缺派生前缀、含大写或非法字符、总长超 100 | 按派生前缀 `<实体名>_segment_`（实体 `user` 即 `user_segment_<名称>`）与正则 `^[a-z][a-z\d_]{0,99}$` 重写机器名后重试 dry-run |
| 元数据对象不存在 | `DATA_NOT_FOUND`、事件 / 属性 / 枚举未找到 | 该对象未经元数据查询验证时，停止规则构造，交由调用方确认对象；不得凭口头描述继续或套用近似名称 |
| 修正 1 次后仍失败，或不属于上述两类 | — | 如实转达服务端错误原文，说明 `rule_draft` 已构造完成但校验未通过，停止当前流程等待指示；不反复尝试不同参数、不把失败改写成成功 |

无论错误性质如何，未收到精确 `Approved` 前不真实创建；名称重复、权限不足等转达服务端原文，不自动改名。

## 使用约束

- 真实写入前按 SKILL.md「写操作安全联锁」完成读取现状、预览与确认；确认语为精确的 `Approved`（`approved`、`同意`、`Approved.` 等均不等价），输入或目标变化后确认失效。
- `--dry-run` 服务端校验通过不等于已创建；真实创建须使用与 dry-run 相同的输入。
- 规则交给 CLI Builder 转换，不手写最终 Horizon expression；`skip_rule_check` 不设为 `true`。
- 创建成功后按目标能力用 `segment.get` 回读验证；回读失败不得宣称最终状态已验证。
