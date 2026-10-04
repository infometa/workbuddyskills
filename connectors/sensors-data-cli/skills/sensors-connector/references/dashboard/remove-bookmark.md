# 移除书签

> 工具 `dashboard.bookmark-remove` · 命令 `sensors analytics dashboard-bookmark-remove` · 类型 写入

## 用途

从一个已存在看板中按书签 ID 移除一个或多个书签：CLI 先读取该看板当前书签，过滤掉目标 ID 后按剩余列表回写。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--dashboard-id` | int | 是 | — | 目标看板 ID | `7` |
| `--bookmark-ids` | string | 是 | — | 要移除的书签 ID 列表，逗号分隔（如 `1,2,3`），必须为正整数 | `5` |
| `--dry-run` | flag | 否 | 关 | 先读取当前看板书签并输出过滤后的 OpenAPI Request JSON，不发起真实写入 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`（临时覆盖配置）、`--timeout`（analytics 命令默认 1800 秒）。本命令另需配置开启写操作开关，未开启时 CLI 在执行前直接拒绝（含 `--dry-run` 预览，同样要求写开关已开启）。

## 输入 Schema

本工具无复杂 JSON 输入，通过 `--dashboard-id` + `--bookmark-ids` 定位移除目标。只按书签 ID 精确匹配，书签名称不参与匹配，同名书签不影响结果。

## 构造流程

从业务输入到合法命令参数的构造映射：

1. 定位看板：`--dashboard-id` 取目标看板 ID（可用 `dashboard-list` / `dashboard-get` 复核）。
2. 把移除目标换算成确切书签 ID：先 `dashboard-get --id <dashboard_id>` 展开书签列表，将业务侧的书签名 / 图表描述对应到 `bookmarks[].id`；同名书签只能靠 ID 区分，候选不唯一时交调用方按 ID 确认，不按名称猜测。
3. 构造 `--bookmark-ids`：正整数、逗号分隔（如 `3,5`）；任一 ID 不在该看板内时命令整体报错（CLI 不静默忽略不存在的 ID），执行前先复核列表。
4. 预览与执行：先 `--dry-run` 核对剩余书签列表，确认后去掉该 flag 真实执行。

示例：

```bash
# 移除看板 101 中的书签 3 和 5
sensors analytics dashboard-bookmark-remove --ai-session-id <ai_session_id> --dashboard-id 101 --bookmark-ids 3,5

# 先预览移除后的剩余书签列表，不发起真实写入
sensors analytics dashboard-bookmark-remove --ai-session-id <ai_session_id> \
  --dashboard-id 101 --bookmark-ids 3,5 --dry-run
```

## 输出

真实执行时透传服务端返回结果（`--format json` 时为 Envelope 包裹），并附加 `request_id` 便于追踪；成功时服务端通常返回空对象，判断成功以命令退出码与无错误信息为准，需要复核时用 `dashboard-get --id <dashboard_id>` 确认剩余书签。

`--dry-run` 输出过滤后剩余书签的完整 OpenAPI Request JSON：`id` / `name` / `config` 保持看板现状，`bookmarks` 为剔除目标 ID 后的剩余列表（顺序保持原顺序），可用于核对移除后的最终状态。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 写操作未开启 | 配置未启用写操作开关 | 按错误提示在命令行开启后重试，不得绕过 |
| `--bookmark-ids 不能为空` / 包含非整数 / 非正整数 | 列表为空、含空段或非正整数 | 改为 `1,2,3` 形式的正整数列表 |
| `概览 X 中不存在书签 ID: ...` | 某个 ID 不在该看板内（CLI 不静默忽略） | 先 `dashboard-get --id <dashboard_id>` 复核书签 ID |
| 看板不存在 / 无权限 | `--dashboard-id` 无效或不属于当前项目 | 先 `dashboard-list` / `dashboard-get` 复核 |
| 认证 / 网络错误 | API Key 无效或网络异常 | 原样返回错误与 `request_id`；可按 `sensors doctor` 诊断后有限重试 |

## 使用约束

- 只移除看板内的书签，不删除看板本身；CLI 不提供删除看板的命令。
- 移除目标必须唯一确定：候选书签不唯一时先交调用方按 ID 确认，不按名称猜测。
- 真实写入前用 `--dry-run` 核对剩余书签列表，并按 SKILL.md「写操作安全联锁」取得对目标看板与本次移除 ID 的确认。
- 跨看板迁移书签不使用本工具，使用 `dashboard.bookmark-copy` 的 `--remove-from-source` 语义。
