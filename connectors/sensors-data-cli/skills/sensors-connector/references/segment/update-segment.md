# segment.update 更新分群

> 工具 `segment.update` · 命令 `sensors segment update` · 类型 写入

## 用途

安全更新同一创建类型的分群定义：规则、显示名称、描述、调度、存储保留份数或可见性，先预览差异再用审批指纹执行。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--name` | string | 是（或 `--schema`） | — | 分群定义机器名；不接受显示名称 | `xiaofangdekehu` |
| `--entity-name` | string | 是（或 `--schema`） | — | 分群所属实体名，例如 `user` | `user` |
| `--input` | string | 是（或 `--schema`） | — | JSON 输入；`-` 从 stdin 读，也可传文件路径；包含 `expected_create_type` 和 `changes` | `update.json` |
| `--schema` | flag | 否 | 关 | 输出完整 JSON 输入 Schema，不读取配置、不访问网络 | `—` |
| `--dry-run` | flag | 否 | 关 | 读取当前分群并输出修改前后差异与审批指纹，不调用更新接口 | `—` |
| `--approved-fingerprint` | string | 执行时必填 | — | 必须与同一输入最近一次 `--dry-run` 输出的 64 位审批指纹一致 | `c711ec4056f5c1a77a241e13a7acc8f48999dfaf77e734e92359773c4cce663f` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（预览与执行均必填）。

## 输入 Schema

`--input` 顶层字段：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `expected_create_type` | `EQL` \| `CUSTOMIZED_RULE` | 是 | 当前分群的创建类型，用于同类型校验（不是要改成的类型） | `CUSTOMIZED_RULE` |
| `changes` | object | 是 | 本次明确请求的变更，至少一个字段，未知字段被拒绝 | `{"display_name":"晓芳的客户V2","comment":"dry-run 预览示例"}` |

输入示例（多字段变更）：

```json
{
  "expected_create_type": "EQL",
  "changes": {
    "display_name": "<新显示名>",
    "comment": "<新描述>",
    "visible": false,
    "storage_settings": {"version_count": 10}
  }
}
```

`changes` 允许的字段：

| 字段 | 约束 | 示例值 |
| --- | --- | --- |
| `rule_draft` | 结构化规则草稿，整体替换当前规则；`rule_draft.create_type` 必须与 `expected_create_type` 相同；结构见 [segment-rule-schema.md](segment-rule-schema.md)，行为序列见 [segment-event-sequence-schema.md](segment-event-sequence-schema.md) | `—` |
| `display_name` | 新显示名称，不得为空白 | `晓芳的客户V2` |
| `comment` | 新描述；空字符串表示清空；≤1024 字符 | `dry-run 预览示例` |
| `trigger` | 调度变更，形状见下方「调度变更」；分群不支持任何 `trigger_type` 切换（`MANUAL ↔ CRON` 均不支持）；`CRON → CRON` 仅允许修改七字段 Quartz CRON 的秒、分、时，日、月、周、年必须与当前值完全相同 | `—` |
| `storage_settings.version_count` | 保留份数，`1..100`；当前为 `MANUAL` 时固定为 `1` | `—` |
| `visible` | 严格布尔值 | `—` |

告警配置和分群通知配置不在更新白名单内，写入会被未知字段校验拒绝。

### 同类型规则替换

分群的创建类型只有 `EQL` 和 `CUSTOMIZED_RULE` 两种，与创建侧完全一致；普通条件、行为序列和同层混合都是 `CUSTOMIZED_RULE` 内的规则形态，不是独立类型。替换规则时按当前形态复用对应结构章节，只复用规则结构，不复用创建侧的命令与确认流程：

| 当前分群业务形态 | 复用结构 |
| --- | --- |
| 单一条件组合（EQL 形态） | [segment-rule-schema.md](segment-rule-schema.md)「条件树」+ `EQL` 输入形状 |
| 普通条件树（无行为顺序） | [segment-rule-schema.md](segment-rule-schema.md)「条件树」+ `CUSTOMIZED_RULE` 输入形状 |
| 行为序列 | [segment-event-sequence-schema.md](segment-event-sequence-schema.md) |
| 普通条件与行为序列混合 | [segment-event-sequence-schema.md](segment-event-sequence-schema.md)「组合约束」 |

`rule_draft` 整体替换当前规则：CLI 复用当前 `segment_rule_ref.segment_rule_name`，仅替换其 expression；规则形态变化也不得借机跨创建类型。当前定义缺少 `segment_rule_name` 时命令报错。

### 调度变更

`trigger` 变更只有两种形状：`{"trigger_type": "MANUAL"}`（分群侧不可用：当前为 `CRON` 时被切换禁令拒绝，当前已是 `MANUAL` 时无有效变更）与：

```json
{"trigger_type": "CRON", "cron_trigger": {"crontab_exp": "<新七字段 CRON>"}}
```

CLI 对更新侧 CRON 的形态校验（不满足即拒绝）：必须七字段；秒、分、时为明确整数（秒 / 分 0..59，时 0..23）；月、年必须为 `*`；日域只支持三种形态——每日（日 `*` + 周 `?`）、每周单日（日 `?` + 周 `MON`..`SUN`）、每月单日（日 `1..31` + 周 `?`）。

例如当前就是每日 CRON `0 5 8 * * ? *`，只把执行时间改为每天 9:30：`crontab_exp` 填 `"0 30 9 * * ? *"`。该示例仅适用于当前周期同为每日；当前为每周或每月时，必须保留当前 CRON 的日、月、周、年字段，不得拿示例覆盖周期。

以 `--schema` 实时输出为最终事实源。

## 构造流程

### 1. 读取现状

先用 `segment.get --name <机器名> --entity-name <实体名>` 读取当前 `create_type`、规则形态与 `trigger`，作为 `expected_create_type` 与调度边界的依据。

### 2. 组装输入

按「输入 Schema」组装 `expected_create_type` + `changes`，只写本次明确变更的字段。

### 3. 预览差异与指纹

```bash
sensors segment update --ai-session-id <ai_session_id> --name <分群机器名> --entity-name user --input update-input.json --dry-run --format json
```

### 4. 展示与确认

逐项展示 `differences` 中每个 `field` 的 `before` / `after`（不能只说"将更新分群"），连同 `update_mask` 与 `approval_fingerprint`，等待精确 `Approved`；确认只批准这一份预览。

### 5. 指纹执行

不带 `--dry-run`，携带预览返回的原始指纹执行；不得复用另一份预览的指纹，不得确认后修改输入：

```bash
sensors segment update --ai-session-id <ai_session_id> --name <分群机器名> --entity-name user --input update-input.json --approved-fingerprint <approval_fingerprint> --format json
```

### 6. 回读验证

执行成功后用 `segment.get` 回读验证；回读失败不得宣称最终状态已验证。

## 输出

`--dry-run` 输出预览：

```json
{
  "differences": [{ "field": "display_name", "before": "高价值用户", "after": "新版高价值用户" }],
  "update_mask": "display_name",
  "request": { "segment_definition": { "…": "最小更新请求" }, "update_mask": "display_name", "dry_run": false },
  "approval_fingerprint": "<64 位十六进制指纹>"
}
```

- `differences`：逐字段的修改前后值；规则替换显示为字段 `rule`，保留份数显示为 `storage_settings.version_count`。
- `update_mask`：真实发送的最小字段集合；未出现的字段不会主动更新。
- `approval_fingerprint`：SHA-256 指纹，输入材料为 `{domain: "segment", current: 当前状态快照, request: 完整更新请求}`；状态快照包含 `name`、`entity_name`、`create_type`、`update_time`、`rule_version`、`display_name`、`comment`、`segment_rule_ref`、`trigger`、`storage_settings`、`visible`。

真实执行输出同一份 `preview` 与服务端 `result`。执行时命令重新读取当前定义并复核指纹；输入或当前状态（含规则版本、更新时间）任一变化后旧指纹自动失效。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：`--dry-run` 与 `--approved-fingerprint` 互斥 | 两个同时提供 | 预览不带指纹；执行不带 `--dry-run` |
| UsageError：缺少 `--name` / `--entity-name` / `--input` | 未提供必要参数 | 补齐参数或先 `--schema` |
| UsageError：审批指纹无效或已失效 | 指纹不匹配（输入或当前状态已变化） | 重新执行 `--dry-run` 取新指纹 |
| 仅支持同类型更新 | `expected_create_type` 与当前 `create_type` 不一致，或 `rule_draft.create_type` 跨类型 | 先用 `segment.get` 读取当前 `create_type`，按同类型重写输入 |
| 调度变更不支持 | `trigger_type` 切换、CRON 周期字段（日/月/周/年）变化、当前 CRON 非七字段 | 保持原周期，仅改秒/分/时 |
| CRON 形态非法 | 非七字段；秒/分/时非整数或越界；月、年非 `*`；日域不是每日/每周单日/每月单日形态 | 按「调度变更」的形态规则重写 `crontab_exp` |
| 当前定义缺少规则名 | 规则替换时 `segment_rule_ref.segment_rule_name` 缺失 | 无法安全替换规则；核对目标后另寻处理方式 |
| 无有效变更 | `changes` 为空或所有值与当前值相同 | 调整变更内容 |
| 写操作未开启 | 配置 `write_operations_enabled=false` | 停止执行，转达开启指引 |

## 使用约束

- 未执行 `--dry-run`、未展示全部差异或未收到精确 `Approved`，不得真实更新；确认编排见 SKILL.md「写操作安全联锁」。
- 不得复用另一份预览的 `approval_fingerprint`，不得在确认后修改输入再执行。
- 不跨创建类型更新规则：`EQL` 与 `CUSTOMIZED_RULE` 之间不能互换。
- 不猜测 `crontab_exp`；不切换 `trigger_type`，不修改后端不支持的周期字段。
- 调整保留策略（`storage_settings.version_count`）可能需要单独权限；被拒绝时如实转达，不绕过。
- 执行成功后用 `segment.get` 回读验证；回读失败不得宣称最终状态已验证。
