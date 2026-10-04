# 创建看板

> 工具 `dashboard.create` · 命令 `sensors analytics dashboard-create` · 类型 写入

## 用途

创建一个新的空看板（不接收初始书签），透传服务端创建结果并附 `request_id`。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | JSON（`-` stdin / 文件路径） | 是 | — | 创建看板的输入对象，需包含 `type` / `name`；`config` / `group_id` 可选；不接收初始 `bookmarks` | `{"type":"PRIVATE","name":"新看板"}` |
| `--dry-run` | flag | 否 | 关 | 仅输出转换后的 OpenAPI Request JSON，不发起真实请求 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填，`--dry-run` 豁免）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`、`--timeout`（默认 1800 秒）。本命令另需配置开启写操作开关，未开启时 CLI 在执行前直接拒绝（含 `--dry-run` 预览，同样要求写开关已开启）。

## 输入 Schema

| 字段 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `type` | `PRIVATE`\|`PUBLIC` | 是 | — | 看板类型：PRIVATE 个人看板，PUBLIC 公共看板 | `PRIVATE` |
| `name` | string | 是 | — | 看板名称 | `新看板` |
| `config` | string | 否 | null | 看板配置，序列化后的 JSON 字符串；可为空 | `"{}"` |
| `group_id` | int | 否 | 666666 | 目标看板分组 ID，缺省加入默认数据概览分组 | `666666` |

Schema 校验为封闭式（未知字段报错）；`request_id` 由 CLI 自动注入，无需传入。以上字段以命令实时 `--help` / `--schema` 输出为最终事实源。

## 构造流程

从业务输入到合法 `--input` JSON 的构造规则：

1. 确定看板类型：`type` 必填且只有 `PRIVATE`（个人看板，创建者视角）/ `PUBLIC`（公共看板，项目内共享）两档；CLI 不提供默认类型，业务输入未明确时由调用方确认后填入，不自行默认公共或私有。
2. 确定看板名称：`name` 必填；CLI 不提供默认名称，不自行补「新建看板」之类的占位名。
3. 可选字段按需追加：`config`（看板配置 JSON 字符串，无配置可省略或传空串）、`group_id`（要加入的看板分组 ID，不传落默认数据概览分组）。
4. 初始书签不在创建时传入：本命令只产出空看板壳；需要图表时创建成功后用 `dashboard.bookmark-add` 追加，不要在创建输入里夹带 `bookmarks`。

示例变体：

```bash
# 最简输入：只传必填的 type + name
sensors analytics dashboard-create --ai-session-id <ai_session_id> --input - <<'JSON'
{"type": "PRIVATE", "name": "新看板"}
JSON

# 全字段输入：显式指定配置与分组
sensors analytics dashboard-create --ai-session-id <ai_session_id> --input - <<'JSON'
{
  "type": "PUBLIC",
  "name": "运营周报看板",
  "config": "{}",
  "group_id": 666666
}
JSON

# 先预览转换后的 OpenAPI Request JSON，不发起真实请求
sensors analytics dashboard-create --ai-session-id <ai_session_id> --input - --dry-run <<'JSON'
{"type": "PRIVATE", "name": "新看板"}
JSON
```

## 输出

真实执行时透传服务端返回结果，并附加 `request_id` 便于追踪；成功响应中通常包含新看板 ID，后续 `dashboard-get --id` / `dashboard-bookmark-add --input` 都以该 ID 为目标。`--dry-run` 时输出转换后的 OpenAPI Request JSON（`bookmarks` 恒为空数组）。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 写操作未开启 | 配置未启用写操作开关 | 按错误提示在命令行开启后重试，不得绕过 |
| 字段校验失败（UsageError） | 缺 `type` / `name`、`type` 取值非法或含未知字段 | 按错误信息补齐或删除非法字段 |
| 服务端错误（含权限不足） | 服务端拒绝创建 | 原样返回错误与 `request_id`，由调用方处理 |

## 使用约束

- 只创建空看板壳；初始书签须在创建后通过 `dashboard.bookmark-add` 追加，本命令不接受 `bookmarks`。
- 名称与类型是显式输入：未提供时由调用方补齐，不自行填默认名称或默认类型。
- CLI 不提供删除看板的命令；不要把创建、更新、追加或移除书签当成删除看板。
- 真实写入前先用 `--dry-run` 预览最终请求体，并按 SKILL.md「写操作安全联锁」取得确认后执行。
