# 资产清单白名单

代码读取本文件来决定"导出/导入哪些资产"。修改本文件即可调整迁移范围，无需改代码。

格式约定：每一节顶部的 `<!-- machine: ... -->` 是机器可读的 JSON，代码会解析这段；正文是人读的说明。

## DB 表（必迁）

<!-- machine:db_tables
[
  {"name": "sessions", "has_deleted_at": true, "exclude_status": ["running", "Running", "in_progress", "InProgress", "active", "Active", "awaiting_input", "stopping"], "exclude_self_session": true},
  {"name": "automations", "has_deleted_at": true},
  {"name": "automation_runs", "has_deleted_at": false, "fk": {"col": "automation_id", "ref_table": "automations", "ref_col": "id"}},
  {"name": "automation_runtime_state", "has_deleted_at": false, "fk": {"col": "automation_id", "ref_table": "automations", "ref_col": "id"}},
  {"name": "workspaces", "has_deleted_at": false}
]
-->

- `sessions`：会话元数据。`user_id` 来自 `account.uid`。导出时过滤：
  - `deleted_at IS NULL`（必须未软删除）
  - `status NOT IN (running/Running/in_progress/InProgress/active/Active/awaiting_input/stopping)`：**只跳过正在执行中的**对话——这些在目标端会呈现为"中断、待确认、无法停止"的僵尸态
  - 注意 `pending/Pending` **不在跳过列表**里。pending 是"新建未发消息"或"用户输入中"的静态态，跨机器后正常可用
  - `Completed/Failed/Terminated/error/archived` 是终态，正常迁
  - 同时跳过执行本次迁移的 session：通过 `--exclude-session-id <id>` 或环境变量 `WORKBUDDY_CURRENT_SESSION_ID` / `CODEBUDDY_SESSION_ID` 传入
- `automations`：定时任务。同上
- `automation_runs`：执行历史。外键 `automation_id` 必须在 automations 表内，否则丢弃并 warn
- `automation_runtime_state`：调度器运行时状态。主键也是 `automation_id`
- `workspaces`：工作区路径足迹。主键是 `path`，跨机路径不同也不冲突

**不迁的表**（避免泄漏未列入清单的内容）：`session_usage`（缓存）、`migration_meta`（DB 自身的版本管理）、未来新增的所有表

## 文件资产（必迁）

<!-- machine:file_assets
[
  {"path": "skills", "type": "dir-of-dirs", "merge": "skip-if-exists", "skip_indices": ["agent-created-skills.json", "_bm_skillid_migration.json"]},
  {"path": "memory", "type": "dir-of-files", "pattern": "*_memory.md", "exclude_suffix": [".bak"], "merge": "append-with-separator"},
  {"path": "settings.json", "type": "json", "merge": "shallow-target-wins"},
  {"path": "mcp.json", "type": "json", "merge": "mcp-servers-by-name"},
  {"path": "models.json", "type": "json", "merge": "list-by-id", "list_field": "models", "id_field": "id"},
  {"path": "IDENTITY.md", "type": "file", "merge": "imported-suffix"},
  {"path": "SOUL.md", "type": "file", "merge": "imported-suffix"},
  {"path": "USER.md", "type": "file", "merge": "imported-suffix"},
  {"path": "plugins/known_marketplaces.json", "type": "json", "merge": "list-by-id", "list_field": "marketplaces", "id_field": "name"}
]
-->

合并策略说明：
- `skip-if-exists`：同名目录存在则跳过整个目录（除非 `--overwrite`）
- `append-with-separator`：文件存在时追加分隔符再 append 源内容，保留导入端原文在前
- `shallow-target-wins`：JSON 浅合并，导入端已有 key 保留
- `mcp-servers-by-name`：`mcpServers` 字典按 server name 合并，同名 skip
- `list-by-id`：数组类型，按指定 id 字段去重合并
- `imported-suffix`：目标已存在则写为 `<name>.imported<.md>`，避免人格污染

## 默认迁但加警告

<!-- machine:warned_assets
[
  {"path": "connectors", "type": "dir-of-userdirs", "warn": "OAuth refresh_token 可能跨机器/跨变体失效，建议导入后重新授权", "credentials_files": [".credentials.json"]}
]
-->

- `connectors/<uid>/`：包含 `mcp.json`、`connector-states.json`、`.credentials.json`
- `.credentials.json` 受 `--no-credentials` 门控（推荐跨机器时排除）

## Conversations（默认带，可选）

<!-- machine:conversations
{"path": "projects", "type": "session-keyed-jsonl", "filter": "by_sessions_table_id", "controlled_by": "--no-conversations"}
-->

- `projects/<projectFolder>/...jsonl`：消息体存档
- 导出时按 sessions 表的 `id` 集合过滤，只带和 session 关联的，孤儿 jsonl 不带
- 包体可能很大（GB 级），可用 `--no-conversations` 排除

## 严禁迁移

<!-- machine:never_migrate
[
  "logs/",
  "audit-log/",
  "usage-log.json",
  "binaries/",
  "git-bash/",
  "skills-marketplace/",
  "app/cache/",
  "session_usage (table)"
]
-->

- 认证 token 不在根目录下，在 `~/Library/Application Support/CodeBuddyExtension/Data/Public/auth/`，绑定机器和 authId，不迁
- 审计日志是哈希链结构，断了就废，不迁
- node binaries 和 git-bash 是平台相关二进制，目标机器自己构建
- skills-marketplace、app/cache 是缓存，目标端首次启动自动重建

## 路径重写目标（跨机时）

跨机迁移会重写下列位置里的本机绝对路径。规则由 `--path-map <src>=<dst>` 提供，按最长前缀匹配。

<!-- machine:path_rewrite
{
  "db_columns": [
    {"table": "sessions", "column": "cwd"},
    {"table": "workspaces", "column": "path", "pk": true},
    {"table": "automations", "column": "cwds", "type": "json_array"},
    {"table": "automation_runs", "column": "source_cwd"}
  ],
  "files": [
    {"path": "projects/*/*.meta.json", "json_path": "cwd"},
    {"path": "settings.json", "json_path": "defaultWorkspaceRoot"},
    {"path": "mcp.json", "json_pattern": "mcpServers.*.{command,cwd}"},
    {"path": "connectors/*/mcp.json", "json_pattern": "mcpServers.*.{command,cwd}"}
  ],
  "directory_renames": [
    {"base": "projects", "encode": "compressWorkspacePath"}
  ]
}
-->

- 注意：`projects/<projectId>/` 的目录名本身就是 `compressWorkspacePath(cwd) = re.sub(r'[/\\\\:]+', '-', cwd).strip('-')`。重写 sessions.cwd 后必须同步 rename 这个目录，否则对话点开是空白
- automations.cwds 是 JSON array，逐条 rewrite
- `mcp.json` 里 stdio MCP 的 `command`/`cwd` 字段可能含本机路径，重写时按 json_pattern 扫
- prompt / memory / markdown 正文里可能内嵌路径，**不动**，但在 import 报告 `suspicious_path_refs` 段列出可疑位置让用户人工改

## Workspace 内容（可选迁移，跨机才有意义）

<!-- machine:workspace_bundles
{
  "controlled_by": "--with-workspaces",
  "default": false,
  "source": "workspaces table (path column)",
  "exclude_patterns_file": "workspace_excludes.md",
  "size_warn_per_dir_bytes": 1073741824,
  "size_warn_total_bytes": 10737418240,
  "size_limit_per_dir_bytes": 5368709120,
  "default_destination": "~/wb-imported-workspaces/"
}
-->

- 默认不带（避免莫名打出几 G 的包）
- 同机迁移（manifest source 三元组 == 目标） → 即便加 `--with-workspaces` 也跳过，因为本机路径已可直接访问
- 跨机迁移 → 走第二个 zip 包 `<main>-workspaces.zip`
- 单 workspace 排除后超过 `size_limit_per_dir_bytes`（5GB）默认 skip + warn，用户须 `--workspace-include` 显式带上
- 超过 `size_warn_per_dir_bytes`（1GB）继续但 warn

## 重启感知

<!-- machine:restart_required
{
  "restart_after_any_of": [
    "db",
    "models.json",
    "settings.json",
    "plugins/known_marketplaces.json",
    "SOUL.md",
    "USER.md",
    "connectors/*/connector-states.json"
  ],
  "hot_reloaded": [
    "mcp.json",
    "connectors/*/mcp.json",
    "memory/*_memory.md",
    "IDENTITY.md",
    "skills/*"
  ]
}
-->

- 99% 的迁移场景都会动 DB → 导入完成后向用户提示"请重启 WorkBuddy 客户端使改动生效"
- mcp.json / IDENTITY.md / memory / skills 有 watcher 或每轮重读，不用重启
- 已打开的会话即便 skill 是热加载的，system prompt 已注入旧 skill 列表，**新会话**才能看到新 skill
