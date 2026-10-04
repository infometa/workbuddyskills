# conference +search

> **前置条件：** 先阅读 [`../../ihr-shared/SKILL.md`](../../ihr-shared/SKILL.md) 了解共享运行规则、时间处理方式和 JSON 协议。

搜索历史面谈记录，支持按专项、文本、状态、预约时间范围、创建时间范围和首轮预览。面谈/会议、数字人面试和数字人陪练三类业务成功发起后都属于 conference 面谈会话，统一从本入口搜索。普通面谈、普通面试和会议属于同一类。该操作只读，不修改任何会议数据。

当前动作入口：

```bash
ihr-cli conference +search
```

## 典型触发表达

以下问题通常优先使用 `+search`：

- 最近开过哪些面谈
- 上周聊过预算评审的会
- 3 月已经结束的绩效面谈
- 最近 30 天和渠道拓展有关的面谈
- 先帮我找几条香港出海相关的历史面谈

## 命令

```bash
# 关键词搜索
ihr-cli conference +search --queryText "绩效面谈"

# 在指定专项内搜索；专项ID应先通过 +campaign-search 确认
ihr-cli conference +search --campaignId 35660 --queryText "绩效面谈"

# 按时间范围搜索
ihr-cli conference +search --startTimeFrom "2026-03-01 00:00:00" --startTimeTo "2026-03-31 23:59:59"

# 按创建时间范围搜索
ihr-cli conference +search --createdAtFrom "2026-03-01 00:00:00" --createdAtTo "2026-03-31 23:59:59"

# 关键词 + 状态 + 预览
ihr-cli conference +search --queryText "渠道拓展" --statuses "READY,STARTED,COMPLETED" --previewLimit 5

# 按面谈方式搜索
ihr-cli conference +search --interviewMode DIGITAL_AVATAR --previewLimit 5

# 时间范围 + 排序
ihr-cli conference +search --startTimeFrom "2026-03-01 00:00:00" --startTimeTo "2026-03-31 23:59:59" --sortField START_TIME --sortOrder DESC

# JSON 输入（调试用）
ihr-cli conference +search --json '{"campaignId":"1129621506616197123","queryText":"预算评审","previewLimit":3}'

# 写入输出文件
ihr-cli conference +search --queryText "香港出海" --output-file /tmp/ihr_conference_search.json
```

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--queryText <text>` | 否 | 搜索关键词 |
| `--campaignId <id>` | 否 | 专项 ID 文本；仅搜索该专项关联的面谈，并继续叠加当前用户数据权限。雪花 ID 必须按字符串传输，JSON 输入时需要保留引号 |
| `--statuses <values>` | 否 | 状态列表，逗号分隔，可选值：`CANCELLED`、`READY`、`STARTED`、`EXPIRED`、`COMPLETED` |
| `--interviewMode <mode>` | 否 | 面谈方式，取值：`ONLINE`、`OFFLINE`、`DIGITAL_AVATAR` |
| `--startTimeFrom <time>` | 否 | 普通面谈/会议预约开始时间、数字人会话允许进入时间的下界 |
| `--startTimeTo <time>` | 否 | 普通面谈/会议预约开始时间、数字人会话允许进入时间的上界 |
| `--endTimeFrom <time>` | 否 | 普通面谈/会议预约结束时间、数字人会话最晚结束时间的下界；不是实际结束时间 |
| `--endTimeTo <time>` | 否 | 普通面谈/会议预约结束时间、数字人会话最晚结束时间的上界；不是实际结束时间 |
| `--createdAtFrom <time>` | 否 | 创建时间下界 |
| `--createdAtTo <time>` | 否 | 创建时间上界 |
| `--sortField <field>` | 否 | 排序字段，取值：`START_TIME`、`END_TIME`；当存在 `queryText` 时，默认按相关性排序，显式指定时间字段后改为“先过相关性门槛，再按时间排序” |
| `--sortOrder <order>` | 否 | 排序方向，取值：`ASC`、`DESC`；仅在显式指定时间排序时影响最终结果顺序 |
| `--previewLimit <n>` | 否 | 预览数量，范围 `0-10` |
| `--json <json>` | 否 | 直接传入 JSON 字符串，调试用 |
| `--stdin` | 否 | 从标准输入读取 JSON 字符串，调试用 |
| `--output-file <file>` | 否 | 将结果额外写入文件 |

## 核心约束

### 1. 至少提供一个有效查询条件

必须至少提供一个有效查询条件，例如：

1. `queryText`
2. `campaignId`
3. `statuses`
4. `interviewMode`
5. 任一时间范围字段
6. 任一排序参数（`sortField` 或 `sortOrder`）
7. `previewLimit > 0`

### 2. 专项ID必须先确认

用户只提供专项名称时，先执行 `+campaign-search`。只有查询响应 `total=1` 时才可自动使用命中项的 `campaignId`；多条命中时必须展示候选并让用户确认。`campaignId` 固定按文本读取和传递，不得转换为浮点数。专项下没有关联面谈时返回空结果，不得退化为未限定专项的搜索。

### 3. 默认面向历史面谈

本动作的定位是历史记录检索，不应被用作未来日程或发起动作入口。

面谈/会议、数字人面试和数字人陪练三类业务不按发起流程拆分历史查询入口。模板准备和发起流程虽然不同，已经进入 conference 会话数据域的记录仍统一搜索。

### 4. 预览数量上限为 10

`previewLimit` 取值范围固定为 `0-10`。  
当结果很多时，应优先返回少量 `previewItems`，再决定是否继续进入 `+documents`。

### 5. 相对时间先换算

遇到“今天、上周、最近 30 天、最近两个月”之类表达，先换算成绝对日期，再传入命令。

搜索时间字段使用预约语义，并按会话方式解释：

| 会话方式 | `startTime` | `endTime` |
| --- | --- | --- |
| 普通面谈/会议 | 预约开始时间 | 预约结束时间 |
| 数字人面试/陪练 | 允许进入时间 | 最晚结束时间 |

这两个字段都不是实际执行时间。不要用它们回答“候选人实际几点进入、实际几点结束、实际进行了多久”；这类事实需要读取实际执行数据能力，当前 `+search` 预约时间筛选不能替代。

### 6. `queryText` 场景下的排序规则

当传入 `queryText` 时：

1. 默认按相关性排序。
2. 如果显式指定 `--sortField START_TIME` 或 `--sortField END_TIME`，则先过滤掉相关性不足的结果，再按时间排序。
3. `previewItems[].finalScore` 仍然表示 `0-1` 的相关性分数，可用于辅助判断结果质量。

### 7. `statuses` 使用搜索态，不是底层原始状态直出

`--statuses` 当前收敛为五种搜索态：

1. `CANCELLED`
2. `READY`
3. `STARTED`
4. `EXPIRED`
5. `COMPLETED`

补充说明：

1. `COMPLETED` 表示“面谈已完成且派生结果也已完成”，不是单纯底层会话结束。
2. `STARTED` 是搜索态，会归并多种进行中语义。
3. 未知或空白状态字面量会按当前兼容口径归一化为 `CANCELLED`。

### 8. `previewItems` 使用搜索过滤语义

当前 controller 会按当前用户权限过滤 `previewItems`：

1. 没有 `VIEW_BASIC_INFO` 时，整条 `previewItem` 不返回。
2. 有基础信息权限但缺少大纲、智能总结或转写权限时，对应内容字段返回 `null`。
3. 搜索结果不返回 `access` 对象；如需逐项判断四类内容访问状态，继续调用 `+documents`。

`returnedCount` 和 `conferenceSessionIds` 表达搜索命中结果，不能根据是否存在同位置的 `previewItem` 推断当前用户的具体内容权限。

### 9. 默认先搜索，再读文档

除非用户明确要求内容详情，否则不要在首轮搜索后自动对所有命中会话执行 `+documents`。

## 时间格式

推荐时间字符串格式：

| 格式 | 示例 |
|------|------|
| 日期时间 | `2026-03-10 14:00:00` |
| 仅日期 | `2026-03-10` |

## 输出结果

CLI 统一输出：

```json
{"success":true,"command":"queryConference","request":{},"response":{}}
```

业务字段从 `response.data` 读取，重点包括：

| 字段 | 说明 |
|------|------|
| `response.data.returnedCount` | 本次返回的候选会话数 |
| `response.data.truncated` | 是否可能还有更多结果未返回 |
| `response.data.previewLimit` | 预览上限 |
| `response.data.conferenceSessionIds[]` | 候选会话 ID 列表 |
| `response.data.previewItems[]` | 首轮预览项，受权限过滤影响 |
| `response.data.previewItems[].conferenceSessionId` | 会话 ID |
| `response.data.previewItems[].status` | 搜索态：`CANCELLED`、`READY`、`STARTED`、`EXPIRED`、`COMPLETED` |
| `response.data.previewItems[].startTime` | 普通会话为预约开始时间；数字人会话为允许进入时间 |
| `response.data.previewItems[].endTime` | 普通会话为预约结束时间；数字人会话为最晚结束时间；不是实际执行结束时间 |
| `response.data.previewItems[].createTime` | 创建时间 |
| `response.data.previewItems[].finalScore` | 相关性分数，范围 `0-1`，仅搜索预览中有 |
| `response.data.previewItems[].basicText` | 面谈基础信息文本 |
| `response.data.previewItems[].outlineText` | 面谈大纲文本 |
| `response.data.previewItems[].smartMinutesText` | 面谈智能纪要文本 |
| `response.data.previewItems[].topicText` | 面谈主题文本 |
| `response.data.previewItems[].summaryText` | 摘要文本 |
| `response.data.previewItems[].todoText` | 待办文本 |
| `response.data.previewItems[].transcriptSummaryText` | 转写摘要文本 |
| `response.data.previewItems[].currentQueryUserIdentity` | 当前查询用户在该会话中的身份信息；未解析到时可能为空 |
| `response.data.previewItems[].currentQueryUserIdentity.userId` | 当前发起搜索的用户 ID |
| `response.data.previewItems[].currentQueryUserIdentity.searchRole` | 搜索视角角色；当前固定为 `CURRENT_USER` |
| `response.data.previewItems[].currentQueryUserIdentity.participantNames` | 当前用户在该会话中的名称聚合，多个名称用 `|` 分隔 |
| `response.data.previewItems[].currentQueryUserIdentity.roleName` | 当前用户在该会话中的角色名称 |

补充说明：

1. 请求里的时间筛选字段使用 `yyyy-MM-dd` 或 `yyyy-MM-dd HH:mm:ss`。
2. 响应里的 `startTime`、`endTime`、`createTime` 来自服务端响应模型，格式为 ISO-8601 offset datetime；前两者按上面的会话方式解释为预约时间，不能表述为实际执行时间。
3. `queryText` 默认按相关性排序；若显式指定时间排序，则结果是在通过相关性门槛后，再按时间字段排序。
4. `previewItems` 使用搜索过滤语义：无基础信息权限时删除整条预览项，并且不返回 `access`。
5. 文本字段属于权限敏感输出；缺少对应内容权限时返回 `null`。`currentQueryUserIdentity` 只有在服务端成功解析“当前查询用户在该会话中的 participant 身份”时才返回，未解析到时可能为 `null`。

## 搜索结果中的下一步

当用户明确需要查看具体内容时，从 `response.data.conferenceSessionIds[]` 中选择目标会话，继续执行：

```bash
ihr-cli conference +documents --conferenceSessionIds "<conferenceSessionId>"
```

## 常见错误与排查

| 错误现象 | 根本原因 | 解决方案 |
|---------|---------|---------|
| 缺少输入参数 | 没有传任何有效条件 | 至少补一个查询条件 |
| `previewLimit 取值范围必须为 0-10` | 预览数量越界 | 改为 `0-10` |
| 无结果 | 条件过窄 | 先只保留关键词或缩小过滤条件 |
| 配置或登录错误 | CLI 返回 `CONFIG_ERROR` / `AUTH_REQUIRED` / `AUTH_EXPIRED` / `CREDENTIAL_MISSING` | 回到 [ihr-shared](../../ihr-shared/SKILL.md)，只解释结构化错误与一次恢复边界；本业务 reference 不维护安装、配置或登录命令 |
| 网络请求失败 | 服务不可达 | 检查服务地址与网络连通性 |

## 提示

- 默认优先输出少量 preview，而不是一开始就拉所有文档。
- `truncated=true` 时，应优先缩小查询范围，而不是盲目继续放大返回量。
- 调试输入结构时，优先使用 `--json` 或 `--stdin`。
