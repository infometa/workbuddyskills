# 复制书签

> 工具 `dashboard.bookmark-copy` · 命令 `sensors analytics dashboard-bookmark-copy` · 类型 写入

## 用途

把源看板中的一个或多个已有书签复制到目标看板；可选在复制成功后从源看板移除这些书签（迁移语义）。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--source-dashboard-id` | int | 是 | — | 源看板 ID | `7` |
| `--bookmark-ids` | string | 是 | — | 要复制 / 迁移的书签 ID 列表，逗号分隔（如 `1,2,3`），必须为正整数且不允许重复 | `4` |
| `--target-dashboard-id` | int | 是 | — | 目标看板 ID | `8` |
| `--remove-from-source` | flag | 否 | 关 | 复制成功后从源看板移除真正复制成功的书签；因目标已存在而跳过的书签仍保留在源看板 | `—` |
| `--dry-run` | flag | 否 | 关 | 输出复制后的目标看板更新请求 JSON（含 copied / skipped / removed 三个 ID 列表），不发起真实写入 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`、`--timeout`（默认 1800 秒）。本命令另需配置开启写操作开关，未开启时 CLI 在执行前直接拒绝（含 `--dry-run` 预览，同样要求写开关已开启）。

## 输入 Schema

本工具无复杂 JSON 输入，通过三个 ID flag 定位源看板、书签与目标看板，调用方无需读取或拼接书签载荷。

## 构造流程

从业务输入到合法命令参数的构造映射：

1. 三要素缺一不可：`--source-dashboard-id`（书签从哪来）、`--bookmark-ids`（复制哪些）、`--target-dashboard-id`（复制到哪去）。看板 ID 不清楚时先 `dashboard-list`（可按 `--type PRIVATE` / `--type PUBLIC` 收窄）拿候选，书签 ID 用 `dashboard-get --id` 展开复核。
2. `--bookmark-ids` 构造：换算成确切的正整数书签 ID，逗号分隔（如 `11,12`），先去重（重复 ID 直接校验报错）；只按 ID 精确挑选，书签名称不参与匹配。
3. 语义选择：默认复制（源看板保留原书签）；仅当业务意图明确是「迁移」时加 `--remove-from-source`，且执行前须向调用方明示「复制成功后会从源看板移除这些书签」。
4. CLI 内部处理（调用方不参与）：依次读取源、目标看板详情 → 从源按 ID 精确挑选书签（ID 不在源看板内直接报错）→ 跳过目标已存在的 ID → 其余书签原样追加到目标书签列表末尾并回写；迁移模式额外对源看板按 copied 列表过滤回写一次。
5. 提交前用 `--dry-run` 预览 copied / skipped / removed 三个 ID 列表与目标看板更新请求 JSON。

示例变体：

```bash
# 复制：源看板 201 的书签 11、12 追加到目标看板 202，源看板不变
sensors analytics dashboard-bookmark-copy --ai-session-id <ai_session_id> \
  --source-dashboard-id 201 --bookmark-ids 11,12 --target-dashboard-id 202

# 迁移：复制成功后从源看板移除真正复制成功的书签
sensors analytics dashboard-bookmark-copy --ai-session-id <ai_session_id> \
  --source-dashboard-id 201 --bookmark-ids 11,12 --target-dashboard-id 202 --remove-from-source

# 预览 copied / skipped / removed 三个列表，不发起真实写入
sensors analytics dashboard-bookmark-copy --ai-session-id <ai_session_id> \
  --source-dashboard-id 201 --bookmark-ids 11,12 --target-dashboard-id 202 --dry-run
```

## 输出

`--format json` 时输出（Envelope 包裹）：

```json
{
  "id": 202,
  "name": "目标看板",
  "config": "{}",
  "bookmarks": ["...复制完成后目标看板的全量书签列表..."],
  "copied_bookmark_ids": [11, 12],
  "skipped_existing_bookmark_ids": [],
  "removed_from_source_bookmark_ids": [],
  "request_id": "..."
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `id` / `name` / `config` | 目标看板 ID、名称与配置 | `8` / `某企业使用情况` / `{"compatible":4674}` |
| `bookmarks` | 复制完成后目标看板的全量书签列表（原有书签在前，新复制书签追加在末尾） | `—`（书签对象全量列表，超长） |
| `copied_bookmark_ids` | 本次真正追加到目标看板的书签 ID 列表 | `[4]` |
| `skipped_existing_bookmark_ids` | 目标看板已存在而被跳过的书签 ID 列表（不报错、不重复追加） | `[]` |
| `removed_from_source_bookmark_ids` | 迁移模式下从源看板移除的书签 ID 列表；非迁移模式为空数组 | `[]` |
| `request_id` | 本次请求追踪 ID | `8ab374dbee73485188c5dcde716302df` |

结构性解读：先读三个 ID 列表判定本次行为（复制了谁 / 跳过了谁 / 迁移模式下移除了谁），再用 `bookmarks` 复核目标看板最终全量清单。跳过不是失败：`skipped_existing_bookmark_ids` 说明这些书签在目标看板已存在、内容保持原样；迁移模式下被跳过的书签仍保留在源看板（只有 copied 的才被移除）。向调用方总结时优先按「已复制 / 因已存在跳过 / 已迁移并从源移除」表述，仅在追问技术细节时展开底层字段名。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 写操作未开启 | 配置未启用写操作开关 | 按错误提示开启后重试，不得绕过 |
| `--bookmark-ids` 格式错误 | 为空、含非整数、非正整数或存在重复 ID | 改为去重后的 `1,2,3` 形式 |
| `源概览 X 中不存在书签 ID: ...` | 某个书签 ID 不在源看板内 | 先 `dashboard-get --id <source_dashboard_id>` 复核 |
| 源 / 目标看板不存在或无权限 | 看板 ID 无效或不属于当前项目 | 先 `dashboard-list` / `dashboard-get` 复核 |

## 使用约束

- 目标已存在的书签自动跳过且不视为失败；跳过结果通过 `skipped_existing_bookmark_ids` 原样透传。
- `--remove-from-source` 是迁移语义，会对源看板额外发起一次写请求；使用前必须向调用方明示「复制成功后会从源看板移除」并取得确认。
- 真实写入前用 `--dry-run` 预览 copied / skipped / removed 三个列表，并按 SKILL.md「写操作安全联锁」取得对源、书签、目标三要素的确认。
- 本工具只做已有书签的整体复制，不修改书签的 `data` / `config` / `mode`；新建分析书签走 `dashboard.bookmark-add`。
