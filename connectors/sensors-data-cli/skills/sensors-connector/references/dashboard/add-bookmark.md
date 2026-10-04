# 追加书签

> 工具 `dashboard.bookmark-add` · 命令 `sensors analytics dashboard-bookmark-add` · 类型 写入

## 用途

向一个已存在看板追加一个或多个新书签：CLI 先读取该看板当前书签，再把输入书签追加到列表末尾后回写。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--input` | JSON（`-` stdin / 文件路径） | 是 | — | 追加对象，需包含 `id` / `name` / `bookmarks`；`config` 可选；`bookmarks[].data` 必须是分析模型输入 schema JSON | `{"id":7,"name":"客户整体概览","bookmarks":[...]}` |
| `--dry-run` | flag | 否 | 关 | 先读取当前看板书签并输出合并后的 OpenAPI Request JSON，不发起真实写入 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`、`--timeout`（默认 1800 秒）。本命令另需配置开启写操作开关，未开启时 CLI 在执行前直接拒绝（含 `--dry-run` 预览，同样要求写开关已开启）。

## 输入 Schema

| 字段 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `id` | int | 是 | — | 目标看板 ID | `7` |
| `name` | string | 是 | — | 目标看板名称 | `客户整体概览` |
| `config` | string | 否 | null | 看板配置，序列化后的 JSON 字符串；不传保留现状 | `—`（不传） |
| `bookmarks` | array | 否 | `[]` | 要追加的书签列表，元素必须是完整写接口载荷；`id` 必须统一为 `0` | `[{"id":0,"type":"/segmentation/",...}]` |

`bookmarks[]` 元素结构：

| 字段 | 类型 | 必填 | 说明 | 示例值 |
|---|---|---|---|---|
| `id` | int | 是 | 固定传 `0`，表示新增书签；非 0 直接校验报错 | `0` |
| `type` | string | 是 | 斜杠格式书签类型，见下方白名单 | `/segmentation/` |
| `name` | string | 是 | 书签名称 | `事件分析示例` |
| `data` | string | 是 | 对应分析模型输入 schema 的 JSON 字符串（与该分析命令的 `--input` 同构）；CLI 内部按 SA 版本转换为最终请求体 | `—`（JSON 字符串，超长） |
| `config` | string | 否 | 书签可视化配置，序列化后的 JSON 字符串；可为 null | `""` |
| `mode` | int | 是 | 书签模式：0 私有，1 公共 | `0` |

以上字段以命令实时 `--help` / `--schema` 输出为最终事实源。

## 构造流程

从业务输入到合法 `--input` JSON 的构造映射：

1. 目标看板基础信息：`id` / `name` 必填，均取看板现状值（`dashboard-get --id` 可复核）；`name` 会随回写覆盖看板名称，传错名称等效改名看板。输入对象只使用 `id` / `name` / `config` / `bookmarks` 四个字段，`type` / `group_id` 等多余字段不参与本命令，不要传入。
2. 书签 `type` 按分析模型选斜杠格式，映射关系：

| 分析模型 | 书签写入 `type` |
|---|---|
| 事件分析 | `/segmentation/` |
| 漏斗分析 | `/funnel/` |
| 留存分析 | `/retention/` |
| 分布分析 | `/addiction/` |
| LTV 分析 | `/ltv/` |
| 路径分析 | `/behavior-path/` |
| 间隔分析 | `/interval/` |
| 归因分析 | `/attribution/` |
| 属性分析 | `/user_analytics/` |
| Session 分析 | `/session/` |
| 自定义 SQL | `/custom-sql/` |

3. `data` 按书签来源分三种构造方式：
   - 新建分析书签：先真实执行一次对应分析命令（如 `sensors analytics funnel ...`）拿到输入 schema JSON，把该 JSON 直接作为 `data` 字符串。`data` 必须是分析模型输入 schema JSON，不是手工拼装的最终请求体（如 `funnel` / `funnel_define`），CLI 内部按 SA 版本自动转换。
   - 自定义 SQL 书签：`type` 用 `/custom-sql/`，`data` 至少包含非空 `sql`；`database` / `limit` 可选，不传由服务端按当前项目默认库与默认行数解析；`variables` 可省略。当书签用于复现一条已执行的查询时，应显式携带 `database`（取执行时实际使用的库名，默认库通常为 `horizon_default_1`），避免服务端默认库解析导致书签口径与原查询漂移。
   - 复制已有书签（同板重建或跨板复用）：直接复用 CLI 从看板详情读到的原始 `data`，不改写。
4. 其余字段：`id` 统一 `0`；`mode` 按可见性选 0 私有 / 1 公共；`config` 无可视化配置传 null。
5. 提交前用 `--dry-run` 核对：输出为「看板现状书签 + 本次输入」合并后的完整 Request JSON，追加的书签位于列表末尾。
6. 白名单之外的查询类型（如用户明细 / 用户细查类查询）没有对应书签写入 `type`，不能保存为书签，遇到此类保存需求直接说明不支持。

示例变体：

```bash
# 追加一个事件分析书签（data 为 segmentation 输入 schema JSON）
sensors analytics dashboard-bookmark-add --ai-session-id <ai_session_id> --input - <<'JSON'
{
  "id": 7,
  "name": "cli 测试看板",
  "bookmarks": [
    {
      "id": 0,
      "type": "/segmentation/",
      "name": "事件分析示例",
      "data": "{\"event\":\"Wishlist\",\"date_range\":{\"from_date\":\"2026-06-30\",\"to_date\":\"2026-06-30\"},\"metrics\":[\"total\"],\"unit\":\"day\"}",
      "config": null,
      "mode": 0
    }
  ]
}
JSON

# 追加一个自定义 SQL 书签（复现已执行查询时应显式携带 database；limit 可选，省略时由服务端按默认行数解析）
sensors analytics dashboard-bookmark-add --ai-session-id <ai_session_id> --input - <<'JSON'
{
  "id": 7,
  "name": "cli 测试看板",
  "bookmarks": [
    {
      "id": 0,
      "type": "/custom-sql/",
      "name": "每日启动人数",
      "data": "{\"sql\":\"SELECT date, COUNT(DISTINCT distinct_id) AS users FROM events WHERE event = '$AppStart' GROUP BY date ORDER BY date LIMIT 100\",\"database\":\"horizon_default_1\"}",
      "config": null,
      "mode": 0
    }
  ]
}
JSON
```

## 输出

真实执行时透传服务端返回结果，并附加 `request_id`；成功时服务端通常返回空对象，判断成功以命令退出码与无错误信息为准。`--dry-run` 输出「看板现状书签 + 本次输入」合并后的完整 OpenAPI Request JSON，可用于核对追加位置与最终列表（新增书签的 `data` 已是版本转换后的最终请求体 JSON）。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| 写操作未开启 | 配置未启用写操作开关 | 按错误提示开启后重试，不得绕过 |
| `bookmarks[].id 必须为 0` | 新增书签传了非 0 ID | 统一改传 `0` |
| `不允许更新已有书签` | 输入 ID 与看板内已有书签冲突 | 更新已有书签改走 `dashboard.update` 全量流程 |
| 书签类型不支持 | `type` 不在白名单 | 错误信息会列出全部支持类型 |
| `data` 与 `type` 不匹配 | `data` 不是对应分析模型的合法输入 | 改为该分析命令的输入 schema JSON |
| 看板不存在 / 无权限 | `id` 无效或不属于当前项目 | 先 `dashboard-list` / `dashboard-get` 复核 |

## 使用约束

- 只允许新增：读取现状、合并（追加到列表末尾）、回写均由 CLI 内部完成，调用方不拼全量 `bookmarks`，也不得绕过本工具直接用 `dashboard.update` 做追加。
- 新建分析书签的 `data` 必须是分析模型输入 schema JSON，不是手工拼装的最终请求体；复制已有书签时可直接复用 CLI 读到的原始 `data`。
- 真实写入前用 `--dry-run` 核对合并结果，并按 SKILL.md「写操作安全联锁」取得对目标看板与本次书签的确认。
