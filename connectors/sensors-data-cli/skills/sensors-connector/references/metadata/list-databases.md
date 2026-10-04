# 数据库列表查询

> 工具 `metadata.databases` · 命令 `sensors metadata databases` · 类型 查询

## 用途

查询当前项目下的数据库列表，返回库名与归属信息，供 SQL 构造时确定 `database.table` 中的库名。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| （无命令级参数） | — | — | — | 项目由全局 `--project`（项目英文名）或当前上下文默认项目决定 | — |

全局 flag（`--ai-session-id` 真实请求必填、`--project`、`--format json|pretty`、`--timeout` 默认 300s 等）见 `sensors metadata databases --help`。本命令无 `--dry-run` 预览参数。

调用示例（来自 CLI 帮助）：

```bash
sensors metadata databases --project default --ai-session-id <ai_session_id> --format json
```

## 输入 Schema

无 `--input` 复杂输入，参数见上表。CLI 内部按项目英文名自动解析数字项目 ID（解析结果按平台地址缓存），调用方无需关心 `project_id`。

## 输出

`databases[]` 数组，每个元素：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `project_id` | 项目 ID | `3` |
| `name` | 数据库名，用于 SQL 中的 `database.table` | `horizon_production_3` |
| `created_by` | 数据库创建者 | `sensorsdata.horizon` |
| `workspace` | 工作空间 | `PUBLIC` |

- `created_by = sensorsdata.horizon` 的记录是当前项目默认库（SQL 执行始终落在该库），常见名为 `horizon_default_1`；跨项目库名形如 `horizon_{项目英文名}_{项目id}`。
- 顶层其余字段（如分页信息）按服务端返回原样透传；管理噪音字段（`access_info` 等）已裁剪。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 未配置项目英文名 | 当前上下文无默认项目且未传 `--project` | 通过 `--project <项目英文名>` 指定后重试 |
| 项目不存在 / 无权限 | 项目英文名无效或当前凭证无权限 | 停止执行，返回配置或权限修复提示，不换项目重试 |
| 缺少 `--ai-session-id` | 真实请求未携带会话 ID | 先执行 `context.session-start` 取得 `ai_session_id` 再调用 |

## 使用约束

- 每次查询一个项目的库列表；需要对照多个项目时通过 `--project` 按项目分别查询，不做跨项目合并推断。
- 库列表原样返回调用方；默认库的判定依据是 `created_by` 字段，不靠名称猜测。
