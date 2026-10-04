# 看板列表查询

> 工具 `dashboard.list` · 命令 `sensors analytics dashboard-list` · 类型 查询

## 用途

查询当前项目下可见的看板（Dashboard，平台 UI 内亦称「概览」）导航列表，每个看板附带真实书签数量，用于获取看板 ID 候选或浏览看板清单。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--type` | `PRIVATE`\|`PUBLIC` | 否 | 不传返回全部 | 按看板类型过滤：PRIVATE 个人看板，PUBLIC 公共看板；大小写敏感 | `PUBLIC` |
| `--dry-run` | flag | 否 | 关 | 打印将发送的 query params dict（如 `{"type": "PUBLIC"}`），不发起真实 HTTP 请求 | `—` |

公共 flag（analytics 命令共享）：`--ai-session-id`（真实请求必填，`--dry-run` 豁免）、`--format json|pretty`（默认 json）、`--project` / `--context` / `--org-id`（临时覆盖配置）、`--timeout`（analytics 命令默认 1800 秒）。

## 输入 Schema

本工具无复杂 JSON 输入，仅通过上表 flag 传参；过滤维度只有看板类型一项（PRIVATE / PUBLIC 两档），名称等模糊匹配在调用方对返回列表做。

## 构造流程

1. 明确过滤口径：只看个人看板传 `--type PRIVATE`，只看公共看板传 `--type PUBLIC`，浏览全部不传 `--type`。
2. 按名称定位看板时不在此命令过滤：先取列表结果，再在返回的 `dashboards[]` 上按 `name` 模糊匹配得到候选 ID；名称匹配无服务端模糊查询能力。
3. 需要预览请求参数时加 `--dry-run`，确认无误后去掉该 flag 再真实执行。

示例：

```bash
# 列出当前项目全部可见看板
sensors analytics dashboard-list --ai-session-id <ai_session_id>

# 仅列出个人看板 / 公共看板
sensors analytics dashboard-list --ai-session-id <ai_session_id> --type PRIVATE
sensors analytics dashboard-list --ai-session-id <ai_session_id> --type PUBLIC

# 预览将发送的 query params，不发起真实请求
sensors analytics dashboard-list --ai-session-id <ai_session_id> --type PUBLIC --dry-run
```

## 输出

`--format json` 时输出（Envelope 包裹）：

```json
{
  "dashboards": [
    {
      "id": 101,
      "name": "运营看板",
      "type": 0,
      "create_time": "2026-06-01 10:00:00",
      "user_name": "admin",
      "bookmark_count": 8
    }
  ],
  "total": 1
}
```

| 字段 | 说明 | 示例值 |
|---|---|---|
| `total` | 看板总数（当前过滤条件下的返回条数） | `72` |
| `dashboards[].id` | 看板唯一 ID，可作为 `dashboard-get --id` 的入参 | `7` |
| `dashboards[].name` | 看板名称；按名称定位看板时以此字段做调用方匹配 | `客户整体概览` |
| `dashboards[].type` | 看板类型整数编码（平台定义：0 个人 / 1 公共 / 2 分享等），不是 `--type` 的字符串值 | `0` |
| `dashboards[].create_time` | 创建时间，格式 yyyy-MM-dd HH:mm:ss；可能为 null | `2017-02-09 17:45:21` |
| `dashboards[].user_name` | 创建者用户名；可能为 null | `luhannong` |
| `dashboards[].bookmark_count` | 看板内真实书签数，口径为 dashboard.detail 返回的书签列表长度 | `6` |

结构性解读：

- 多候选看板时，把 `id` / `name` / `type` / `bookmark_count` 作为一组确认信息返回调用方，由调用方确认唯一目标；`bookmark_count` 同时可用于预估逐书签执行的成本（0 本书签的看板无需展开执行）。
- `bookmark_count` 由 CLI 逐看板调用一次详情接口统计，看板数量多时命令耗时相应增加。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `Invalid value for '--type'` | `--type` 非 PRIVATE/PUBLIC 或大小写不符 | 改为精确的 `PRIVATE` / `PUBLIC` |
| 认证 / 权限错误 | API Key 无效或无当前项目权限 | 先运行 `sensors doctor` 诊断配置 |
| 请求超时 | 网络异常或看板数量过大 | 提高 `--timeout` 后重试 |
| `dashboards: []` 且 `total: 0` | 当前项目无可见看板或过滤条件过窄 | 空结果不是错误，原样返回；可去掉 `--type` 放宽条件后重查（是否放宽由调用方决定） |

## 使用约束

- 空结果、多候选属于结构事实，原样返回调用方，不自行挑选目标看板、不自动换项目。
- 本工具只列看板概览，不展开单个看板的书签明细（使用 `dashboard.get`），也不执行任何书签查询。
