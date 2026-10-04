# 目标查询与详情（okr-query）

只读 operation 清单：`okr.list`、`okr.get`、`okr.kr.list`、`okr.comment.list`、`okr.viewlink`、`okr.detail.link`。全部不需要确认，也不会写入数据。

## `okr.list` — 分页查询目标

标准版与 ebuilder 链路共用同一个 operation，入参一致，请求体按链路自动转换。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `query_scope` | `self` / `all` | `self`=本人对应周期（默认），`all`=按条件跨人检索 |
| `period_type` | `"1"`/`"2"`/`"3"`/`"4"` | 1-年度 2-季度 3-月度 4-自定义；`query_scope=self` 时必填 |
| `period_range` | string | 年度/季度为 `yyyy`，月度为 `yyyy-MM`，自定义为 `开始日期,结束日期` |
| `period_quarter` | `"1"`..`"4"` | `period_type=2` 时必填 |
| `name` | string | 目标名称关键字（**仅标准版链路**，模糊匹配） |
| `principalid` | 人员 ID | 责任人筛选（人员 ID 由 weaver-e10-hrm-connector 解析） |
| `status` | string | 状态码，英文逗号拼接（**仅标准版链路**） |
| `match` | `and` / `or` | 多条件关系，默认 `and`（仅标准版链路） |
| `page_no` / `page_size` | integer | 默认 1 / 10；`page_size` 最大 100 |

返回：

- `link`、`queryScope`、`period`、`page`（含 `total`/`hasNext`）、`count`。
- `goals[]`：统一结构的目标数组（`goalId`、`name`、`principalid`、`principalName`、`periodType`、`periodTypeLabel`、`periodRange`、`periodStart`、`periodEnd`、`status`、`statusLabel`、`progress`、`detailUrl` 等）。
- `table`：**固定四列**表格（目标名称、目标责任人名称、目标周期类型、目标周期范围），`table.markdown` 中的目标名称是可点击的**绝对地址**链接。

链路差异：

- **标准版**：`query_scope=self` 固定传 `condtype=1`/`subcondtype=1`/`status=1`；`query_scope=all` 传 `condtype=4`/`subcondtype=6`，支持 `name`/`principalid`/`status`。
- **ebuilder**：只传 `creator`（self 时）/`principalid` + 周期筛选字段；**不支持按名称或状态筛选**，传入 `name` 或 `status` 会返回 `validation/link_filter_unsupported`。

便捷入口：`weaver-work-cli --profile eteams okr list --period-type 3 --period-range 2026-09 --page-size 10`。

## `okr.get` — 目标详情

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | 目标 ID | 必填 |
| `include_comment_count` | boolean | 默认 `true`，仅标准版链路生效 |

返回 `link`、`goalId`、`goal`（统一结构）、`raw`（原始响应），以及标准版链路下的评论提示。

**评论规则**：标准版链路会额外查询评论总条数，但**详情绝不直接输出评论正文**：

- 总数 > 0 → 只返回 `commentSummary.totalCount` 与提示「该目标下共有 N 条评论，是否需要查看评论内容？」，正文必须由用户确认后再调 `okr.comment.list`。
- 总数 = 0 → 完全忽略评论模块，不输出任何评论相关文字。
- 评论接口不可用 → 记入 `meta.notes`（`comment_count_unavailable`）。
- ebuilder 链路 → 不查询评论接口，`meta.notes` 说明 `comment_api_unsupported_on_eb_link`。

## `okr.kr.list` — 关键成果列表（仅 ebuilder）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `object_id` | 目标 ID | 必填 |
| `page_no` / `page_size` | integer | 默认 1 / 10 |

标准版链路没有独立的关键成果分页接口，调用会返回 `policy/link_unsupported`；标准版请改用 `okr.get` 的 `goal.keyresultList` 或 `okr.list` 的 `goals[].keyresultList`。

## `okr.comment.list` — 目标评论（仅标准版）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `target_id` | 目标 ID | 必填 |
| `page_no` / `page_size` | integer | 默认 1 / 10 |

**只有在用户明确要求查看评论内容后才可调用**（`okr.get` 只给提示不给正文）。ebuilder 链路没有评论接口，调用会返回 `policy/link_unsupported`。

## `okr.viewlink` / `okr.detail.link` — 详情页链接

- `okr.viewlink`：`ids`（目标 ID 数组或英文逗号拼接字符串）必填，`anchor` 可选（链接展示文案）。逐条返回 `goalId`、`path`（站内相对路径）、`url`（绝对地址）、`anchor`。任一 id 链接不可用时整体返回 `status=VIEWLINK_UNAVAILABLE`、`available=false` 并给出 `warnings`。
- `okr.detail.link`：返回当前链路的地址模板（`pathTemplate` / `urlTemplate`）与 eb 表单 id 解析来源。

## 调用示例

标准版本人月度目标：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json okr run okr.list --input-json '{"query_scope":"self","period_type":"3","period_range":"2026-09","page_size":10}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"query_scope":"self","period_type":"3","period_range":"2026-09","page_size":10}' | weaver-work-cli --profile eteams --json okr run okr.list --input -
```

跨人检索（标准版）：

```text
weaver-work-cli --profile eteams --json okr run okr.list --input-json '{"query_scope":"all","name":"10月份","principalid":"<人员ID>"}'
```

查询详情：

```text
weaver-work-cli --profile eteams --json okr get --id <目标ID>
```

## 注意

- 返回的 `table.markdown` 可能较长，给用户只渲染表格与数量摘要，不要整段回贴 `raw`。
- `principalid`/`status` 等筛选字段传错类型会被 schema 直接拒绝，错误形状见 stderr JSON。
- 列表默认只查一页，需要更多数据时按 `page.hasNext` 递增 `page_no`，不要一次性把 `page_size` 调到 100 以上。
