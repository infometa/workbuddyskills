# tag.update 更新标签

> 工具 `tag.update` · 命令 `sensors tag update` · 类型 写入

## 用途

安全更新同一创建类型的标签定义：规则、显示名称、描述、调度、存储保留份数或可见性，先预览差异再用审批指纹执行。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
| --- | --- | --- | --- | --- | --- |
| `--name` | string | 是（或 `--schema`） | — | 标签定义机器名；不接受显示名称 | `user_tag_1` |
| `--entity-name` | string | 是（或 `--schema`） | — | 标签所属实体名，例如 `user` | `user` |
| `--input` | string | 是（或 `--schema`） | — | JSON 输入；`-` 从 stdin 读，也可传文件路径；包含 `expected_create_type` 和 `changes` | `-` |
| `--schema` | flag | 否 | 关 | 输出完整 JSON 输入 Schema，不读取配置、不访问网络 | `—` |
| `--dry-run` | flag | 否 | 关 | 读取当前标签并输出修改前后差异与审批指纹，不调用更新接口 | `—` |
| `--approved-fingerprint` | string | 执行时必填 | — | 必须与同一输入最近一次 `--dry-run` 输出的 64 位审批指纹一致 | `c569c9033cf91fadb6bdec9cd378e598bc7af5f1c44565b89345e24fed02d783` |

全局 flag：`--format json|pretty`（默认 json）、`--context`、`--project`、`--org-id`、`--timeout`（默认 300 秒）、`--ai-session-id`（预览与执行均必填）。

调用示例（先预览，确认后用指纹执行）：

```bash
sensors tag update --ai-session-id <ai_session_id> --name <标签机器名> --entity-name user --input update-input.json --dry-run --format json
sensors tag update --ai-session-id <ai_session_id> --name <标签机器名> --entity-name user --input update-input.json --approved-fingerprint <approval_fingerprint> --format json
```

## 输入 Schema

`--input` 顶层字段：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
| --- | --- | --- | --- | --- |
| `expected_create_type` | `TAG_EQL` \| `TAG_CUSTOMIZED_RULE` \| `TAG_GENERAL_RULE_DISTRIBUTION` \| `TAG_SQL` | 是 | 当前标签的创建类型，用于同类型校验（不是要改成的类型） | `TAG_CUSTOMIZED_RULE` |
| `changes` | object | 是 | 本次明确请求的变更，至少一个字段，未知字段被拒绝 | `{"display_name":"事件分析使用-更新预览"}` |

输入示例（多字段变更）：

```json
{
  "expected_create_type": "TAG_EQL",
  "changes": {
    "display_name": "新版高价值用户",
    "comment": "更新后的业务口径",
    "visible": false,
    "storage_settings": {"version_count": 10}
  }
}
```

`changes` 允许的字段：

| 用户语义 | 字段 | 约束 | 示例值 |
| --- | --- | --- | --- |
| 规则 | `rule_draft` | 结构化规则草稿，整体替换当前规则；`rule_draft.create_type` 必须与 `expected_create_type` 相同；结构见 [tag-rule-schema.md](tag-rule-schema.md) | `—` |
| 显示名称 | `display_name` | 新显示名称，不得为空白 | `事件分析使用-更新预览` |
| 描述 | `comment` | 新描述；空字符串表示清空；≤1024 字符 | `Agent 更新预览：验证 dry-run 差异输出` |
| 调度配置 | `trigger` | 调度变更：`CRON → CRON` 仅允许修改七字段 Quartz CRON 的秒、分、时，日、月、周、年必须与当前值完全相同；后端支持 `CRON → MANUAL`（CLI 自动把 `storage_settings.version_count` 置为 `1`）；`MANUAL → CRON` 不支持 | `—` |
| 保留份数 | `storage_settings.version_count` | 保留份数，`1..100`；当前为 `MANUAL` 时只能为 `1` | `3` |
| 可见性 | `visible` | 严格布尔值 | `false` |

告警配置和标签通知配置不在更新白名单内，写入会被未知字段校验拒绝。

以 `--schema` 实时输出为最终事实源。

## 构造流程

命令层固定步骤：读取当前定义 → 组装最小变更输入 → 预览差异与指纹 → 精确 `Approved` → 指纹执行。

1. 读取现状：用 `tag.get` 获取当前 `create_type`、`trigger`、`storage_settings` 等；`expected_create_type` 必须填当前实际类型。
2. 组装输入：只把本次明确变更的字段放进 `changes`；更新规则时 `rule_draft` 按当前类型对应章节构造（规则整体替换，不支持局部改条件）：

   | 当前标签 `create_type` | `rule_draft` 规则结构 |
   | --- | --- |
   | `TAG_EQL`（条件 / 布尔标签） | [tag-rule-schema.md](tag-rule-schema.md)「TAG_EQL」 |
   | `TAG_CUSTOMIZED_RULE`（分层标签） | [tag-rule-schema.md](tag-rule-schema.md)「TAG_CUSTOMIZED_RULE」 |
   | `TAG_GENERAL_RULE_DISTRIBUTION`（指标分桶标签） | [tag-rule-schema.md](tag-rule-schema.md)「TAG_GENERAL_RULE_DISTRIBUTION」 |
   | `TAG_SQL` | [tag-rule-schema.md](tag-rule-schema.md)「TAG_SQL」 |

3. 预览：`sensors tag update --dry-run --input update-input.json`，输出 `differences`、`update_mask`、`request`、`approval_fingerprint`。
4. 向调用方逐项展示全部 `field` / `before` / `after` 差异与指纹，等待精确 `Approved`（`approved`、`同意`、`Approved.` 等均不等价）。
5. 执行：同一输入 + `--approved-fingerprint <指纹>`；CLI 执行时重新读取当前定义并复核指纹，输入或当前状态变化后旧指纹自动失效，须重新 `--dry-run` 取新指纹。
6. 执行成功后用 `tag.get` 回读验证。

调度变更边界（CLI 校验事实，更新输入前逐条对照）：

- `CRON → CRON`：只允许改秒、分、时（均须明确整数，范围分别为 0..59 / 0..59 / 0..23）；日、月、周、年四字段必须与当前 `crontab_exp` 完全一致。新 CRON 还须为七字段 Quartz 且通过形态校验：月与年必须为 `*`，仅支持每日（`日=* 周=?`）、每周单日（`日=? 周=<星期>`）、每月单日（`日=<1..31> 周=?`）三种形态。
- `CRON → MANUAL`：支持，且仅当当前为 `CRON`；CLI 自动联动 `storage_settings.version_count=1` 并写入同一请求，无需另行提供保留份数（显式提供时也只能为 `1`）。
- `MANUAL → CRON`：不支持，CLI 直接报调度变更错误。
- 当前为 `MANUAL` 的标签，`storage_settings.version_count` 只能为 `1`。

示例：当前为每日 CRON `0 5 8 * * ? *`，只把执行时间改为每天 9:30：

```json
{
  "expected_create_type": "TAG_EQL",
  "changes": {
    "trigger": {
      "trigger_type": "CRON",
      "cron_trigger": {"crontab_exp": "0 30 9 * * ? *"}
    }
  }
}
```

该示例仅适用于当前同为每日周期；当前为每周或每月时，必须保留当前 CRON 的日、月、周、年字段，不得拿示例覆盖周期。不猜测当前 `crontab_exp`，先从 `tag.get` 读取真实值。

## 输出

`--dry-run` 输出预览：

```json
{
  "differences": [
    {"field": "display_name", "before": "高价值用户", "after": "新版高价值用户"}
  ],
  "update_mask": "display_name",
  "request": {
    "definition": {"name": "high_value", "entity_name": "user", "display_name": "新版高价值用户"},
    "update_mask": "display_name"
  },
  "approval_fingerprint": "<64 位十六进制指纹>"
}
```

结构性解读：

- `differences`：逐字段的修改前后值，必须逐项核对、不得概括为"将更新标签"；规则替换以 `field="rule"` 呈现，保留份数以 `field="storage_settings.version_count"` 呈现。
- `update_mask`：真实发送的最小字段集合；未出现在掩码中的字段不会被更新。
- `request`：将要（预览）或已经（执行）原样发送的最小更新请求。
- `approval_fingerprint`：绑定领域（tag）、目标当前状态快照（含 `update_time`、`rule_version`、`expression`、`trigger`、`storage_settings`、`visible` 等）与完整请求的 SHA-256 指纹；精确 `Approved` 只批准这一份预览。
- 真实执行输出同一份 `preview` 与服务端 `result`；执行时命令重新读取当前定义并复核指纹，输入或当前状态变化后旧指纹自动失效。

## 错误

| 错误 | 触发条件 | 修正方式 |
| --- | --- | --- |
| UsageError：`--dry-run` 与 `--approved-fingerprint` 互斥 | 两个同时提供 | 预览不带指纹；执行不带 `--dry-run` |
| UsageError：缺少 `--name` / `--entity-name` / `--input` | 未提供必要参数 | 补齐参数或先 `--schema` |
| UsageError：审批指纹无效或已失效 | 指纹不匹配（输入或当前状态已变化） | 重新执行 `--dry-run` 取新指纹 |
| 仅支持同类型更新 | `expected_create_type` 与当前 `create_type` 不一致，或 `rule_draft.create_type` 跨类型 | 先用 `tag.get` 读取当前 `create_type`，按同类型重写输入 |
| 调度变更不支持 | `MANUAL → CRON`、CRON 周期字段（日/月/周/年）变化、CRON 非七字段或非每日/每周/每月形态 | 保持原周期仅改秒/分/时，或使用受支持的 `CRON → MANUAL` |
| 无有效变更 | `changes` 为空或所有值与当前值相同 | 调整变更内容 |
| 写操作未开启 | 配置 `write_operations_enabled=false` | 停止执行，如实转达报错与开启指引，不绕过、不编造成功 |

## 使用约束

- 未执行 `--dry-run`、未展示全部差异或未收到精确 `Approved`，不得真实更新；确认编排见 SKILL.md「写操作安全联锁」。
- 不得复用另一份预览的 `approval_fingerprint`，不得在确认后修改输入再执行。
- 不跨创建类型更新规则：四种 `create_type` 之间不能互换。
- 执行成功后用 `tag.get` 回读验证；回读失败不得宣称最终状态已验证。
