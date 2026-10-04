# 更新看板

> 工具 `dashboard.update` · 命令 `sensors analytics dashboard-update` · 类型 写入

## 用途

对一个已存在看板做全量更新：覆盖名称，并按提交顺序整体替换该看板的书签列表。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | JSON（`-` stdin / 文件路径） | 是 | — | 更新对象，需包含 `id` / `name` / `bookmarks`；`config` 可选；`bookmarks[].data` 必须是分析模型输入 schema JSON | `{"id":7,"name":"客户整体概览","bookmarks":[...]}` |
| `--dry-run` | flag | 否 | 关 | 仅输出转换后的 OpenAPI Request JSON，不发起真实写入（仍会做本地校验、版本检测与 data 转换） | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`、`--timeout`（默认 1800 秒）。本命令另需配置开启写操作开关，未开启时 CLI 在执行前直接拒绝（含 `--dry-run` 预览，同样要求写开关已开启）。

## 输入 Schema

| 字段 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `id` | int | 是 | — | 目标看板 ID | `7` |
| `name` | string | 是 | — | 看板名称（全量覆盖） | `客户整体概览` |
| `config` | string | 否 | null | 看板配置，序列化后的 JSON 字符串 | `{"oldConfig":"...","compatible":4674}` |
| `bookmarks` | array | 否 | `[]` | 书签全量列表，整体替换当前看板的书签，顺序即最终顺序；缺省空数组等效清空书签 | `[{"id":0,"type":"/custom-sql/",...}]` |

`bookmarks[]` 元素结构（写接口书签载荷）：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `id` | int | 否 | 保留已有书签时传原 ID；新书签传 0 | `4`（保留）/ `0`（新增） |
| `type` | string | 是 | 斜杠格式书签类型，见下方白名单 | `/custom-sql/` |
| `name` | string | 是 | 书签名称 | `每日启动人数` |
| `data` | string | 是 | 对应分析模型输入 schema 的 JSON 字符串；CLI 内部按 SA 版本转换为最终请求体 | `—`（JSON 字符串，超长） |
| `config` | string | 否 | 书签可视化配置，序列化后的 JSON 字符串；可为空 | `""` |
| `mode` | int | 是 | 书签模式：0 私有，1 公共 | `0` |

书签 `type` 白名单：`/segmentation/`（事件）、`/funnel/`、`/retention/`、`/addiction/`（分布）、`/ltv/`、`/behavior-path/`（路径）、`/interval/`、`/attribution/`（归因）、`/user_analytics/`（属性）、`/session/`、`/custom-sql/`（自定义 SQL）。`/custom-sql/` 的 `data` 至少包含非空 `sql`；`database` / `limit` 可选，不传由服务端按当前项目默认库与默认行数解析；复现已执行查询的书签应显式携带 `database`（默认库通常为 `horizon_default_1`），避免口径漂移。

以上字段以命令实时 `--help` / `--schema` 输出为最终事实源。

## 构造流程

全量替换语义的构造映射（`bookmarks` 漏掉已有书签 = 从看板移除）：

1. **读取现状**：`dashboard.get --id <id>` 取当前名称与书签全列表，作为合并基准。
2. **组装最终列表**：按目标最终顺序排列书签——保留的书签沿用原 `id` 与 `type`，只改需要变化的 `name` / `config` / `data` / `mode`；新增书签 `id` 传 `0` 并按 [add-bookmark.md](add-bookmark.md) 的构造规则填 `type` / `data`；要移除的书签直接不出现在列表中。
3. **填 `data`**：每条书签的 `data` 是对应分析模型命令的输入 schema JSON 字符串（先构造好该分析查询对象再序列化放入；`/custom-sql/` 至少含非空 `sql`）。
4. **预览**：`--dry-run` 输出已通过类型白名单校验与 SA 版本转换的最终请求体，即「提交后看板的完整最终状态」；向调用方展示替换后的完整书签列表，取得对本次全量替换的确认。
5. **执行与回读**：确认后去掉 `--dry-run` 提交同一份输入；`dashboard-get` 复核名称与书签顺序。

仅改名称（保留全部书签，需先从 `dashboard-get` 结果原样抄回列表）：

```bash
sensors analytics dashboard-update --ai-session-id <ai_session_id> --input - --dry-run <<'JSON'
{
  "id": 101,
  "name": "已更新看板",
  "bookmarks": [
    {"id": 9001, "type": "/segmentation/", "name": "日活趋势", "data": "{\"...\": \"原书签 data 原样保留\"}", "mode": 1},
    {"id": 0, "type": "/funnel/", "name": "新漏斗", "data": "{\"...\": \"本次新增书签的分析输入\"}", "mode": 1}
  ]
}
JSON
```

清空书签变体：`{"id": 101, "name": "空看板", "bookmarks": []}`。

## 输出

真实执行时输出 `request_id` 加服务端返回；成功时服务端通常返回空对象，判断成功以命令退出码与无错误信息为准，不以返回体内容为准。需要核对最终状态时，执行后用 `dashboard-get --id <id>` 复核看板名称与书签清单（书签顺序即本次提交 `bookmarks` 的顺序）。

`--dry-run` 输出完成类型白名单校验与 data 版本转换后的 OpenAPI Request JSON，字段解读：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `id` / `name` / `config` | 本次回写的看板 ID、名称与配置（全量覆盖语义） | `7` / `客户整体概览` / `{"oldConfig":"...","compatible":4674}` |
| `bookmarks[]` | 替换后的全量书签列表，顺序即回写后的最终顺序 | `—`（书签对象全量列表，超长） |
| `bookmarks[].id` | 保留的已有书签为原 ID，新书签为 `0` | `0` |
| `bookmarks[].type` | 斜杠格式书签类型（白名单校验已通过） | `/custom-sql/` |
| `bookmarks[].data` | 已按 SA 版本转换后的最终请求体 JSON 字符串，不是输入 schema 原文；可直接用于核对最终查询配置 | `—`（版本转换后的请求体 JSON，超长） |
| `bookmarks[].mode` | 0 私有 / 1 公共 | `0` |

dry-run 结果即可视为「提交后看板的完整最终状态」，可用于在真实写入前向调用方展示替换后的完整书签列表。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 写操作未开启 | 配置未启用写操作开关 | 按错误提示开启后重试，不得绕过 |
| 字段校验失败（UsageError） | 缺 `id` / `name`、`bookmarks[]` 结构非法 | 按错误信息修正输入 |
| 书签类型不支持 | `type` 不在白名单 | 错误信息会列出全部支持类型，据此替换 |
| `data` 与 `type` 不匹配 | `data` 不是对应分析模型的合法输入 | 改为该分析命令的输入 schema JSON |
| 看板不存在 / 无权限 | `id` 无效或不属于当前项目 | 先 `dashboard-list` / `dashboard-get` 复核 |

## 使用约束

- `bookmarks` 是全量替换语义：漏掉已有书签等效于从看板移除；仅追加或移除部分书签优先使用 `dashboard.bookmark-add` / `dashboard.bookmark-remove`。
- 可更新范围仅 `name` / `config` / `bookmarks`，不支持借本命令改其它结构。
- 真实写入前必须 `--dry-run` 预览并向调用方展示替换后的完整书签列表，按 SKILL.md「写操作安全联锁」取得确认后执行。
