# conference +launch

> **前置条件：** 先阅读 [`../../ihr-shared/SKILL.md`](../../ihr-shared/SKILL.md) 了解共享运行规则、时间处理方式和 JSON 协议。涉及人员时，先阅读 [`../../ihr-base/references/ihr-base-select-staffs.md`](../../ihr-base/references/ihr-base-select-staffs.md)。

带参创建并发起面谈。该动作有真实副作用，会创建会话、发起三方会议，并可能触发通知；只有用户明确要求创建、预约、安排或发起时才调用。

当前动作入口：

```bash
ihr-cli conference +launch
```

## 典型触发表达

以下问题通常应进入 `+launch`，但前提是人员和时间都已确认：

- 明天下午三点帮我安排张三的周期绩效复盘
- 给李经理和王五创建一个周度 1-on-1
- 预约一个新员工融入 Check-in 面谈
- 发起一次项目复盘会议

以下表达不要直接发起：

- 帮我准备一下面谈参数
- 帮我拟一个绩效面谈安排
- 搜一下张三能不能作为面谈对象

## 标准流程

如果用户只给了人名，先用通用选人能力确认人员 ID：

```bash
ihr-cli base +selectStaffs --searchKeyword "张三" --pageNo 1 --pageSize 10
```

确认 `response.data.dataList[].id` 后，再把该值写入 `+launch` 的参与人 `staffId`。

## 命令

```bash
# 分项参数，适合简单场景
ihr-cli conference +launch \
  --title "张三周期绩效复盘" \
  --purposeId purpose_004 \
  --startTime "2026-05-28T15:00:00+08:00" \
  --duration 30 \
  --interviewMode ONLINE \
  --interviewers '[{"staffId":"staff-001","name":"李经理"}]' \
  --interviewees '[{"staffId":"staff-002","name":"张三"}]' \
  --outlineMdText "## 面谈目标
- 复盘 Q2 目标达成
- 确认下阶段支持事项
- ..."

# JSON 输入，适合参与人较多或字段较复杂的场景
ihr-cli conference +launch --json '{
  "title": "张三周期绩效复盘",
  "purposeId": "purpose_004",
  "templateId": "template_004",
  "startTime": "2026-05-28T15:00:00+08:00",
  "duration": 30,
  "interviewMode": "ONLINE",
  "interviewers": [{"staffId":"staff-001","name":"李经理"}],
  "interviewees": [{"staffId":"staff-002","name":"张三"}],
  "outline": {
    "mdText": "## 面谈目标\n- 复盘 Q2 目标达成\n- 确认下阶段支持事项\n ..."
  },
  "referenceInfo": "重点聊 Q2 目标达成、关键项目复盘和下季度改进计划。"
}'

# 发起前检查请求体
ihr-cli conference +launch \
  --title "张三周期绩效复盘" \
  --purposeId purpose_004 \
  --startTime "2026-05-28T15:00:00+08:00" \
  --interviewMode ONLINE \
  --interviewers '[{"staffId":"staff-001","name":"李经理"}]' \
  --interviewees '[{"staffId":"staff-002","name":"张三"}]' \
  --dry-run

# 数字人面谈，interviewCode 是数字人面试模板 ID，独立于 conference templateId。
# 如果还没有 interviewCode，先用 +search-avatar-template 查询，必要时用 +create-avatar-template 创建。
ihr-cli conference +launch \
  --title "候选人A数字人初面" \
  --purposeId purpose_002 \
  --startTime "2026-05-28T15:00:00+08:00" \
  --thirdPartyPlatform DIGITAL_AVATAR \
  --interviewCode "avatar-template-001" \
  --interviewers '[{"staffId":"1","name":"数字人面谈官","sourceType":"DIGITAL_HUMAN"}]' \
  --interviewees '[{"name":"候选人A","sourceType":"EXTERNAL","phone":"13800000000","email":"candidate@example.com"}]' \
  --dry-run
```

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--campaignId <id>` | 否 | 预留字段；当前版本不支持绑定所属专项，传入会报错 |
| `--title <text>` | 是 | 面谈主题 |
| `--purposeId <id>` | 否 | 面谈目的 ID，不传默认 `purpose_001` |
| `--templateId <id>` | 否 | 模板业务 ID，不传按 `purposeId` 默认模板 |
| `--startTime <time>` | 是 | ISO-8601 offset datetime，例如 `2026-05-28T15:00:00+08:00` |
| `--duration <n>` | 否 | 面谈时长分钟，默认 `30`，必须大于 `0` |
| `--interviewMode <mode>` | 否 | `ONLINE`、`OFFLINE` 或 `DIGITAL_AVATAR`；不传时按 `thirdPartyPlatform` 推导，两者都不传时默认 `ONLINE` |
| `--thirdPartyPlatform <platform>` | 否 | `TENCENT_MEETING`、`OFFLINE_MEETING` 或 `DIGITAL_AVATAR`；不传时按 `interviewMode` 推导，两者都不传时默认 `TENCENT_MEETING` |
| `--digitalAvatarConfig <json>` | 数字人面谈可选 | 数字人面谈配置 JSON 对象，仅 `DIGITAL_AVATAR` 可传；不能和下面的分项数字人配置参数混用 |
| `--interviewCode <code>` | 数字人面谈必填 | 数字人面试模板 ID，写入 `digitalAvatarConfig.interviewCode`，独立于 `templateId` |
| `--allowObserverIntervention` | 否 | 数字人面谈是否允许一个真人监考官介入 |
| `--roundNumber <n>` | 否 | 数字人面谈轮次，写入 `digitalAvatarConfig.roundNumber` |
| `--resumeJSON <json>` | 否 | 数字人候选人简历 JSON，写入 `digitalAvatarConfig.resume` |
| `--skipVerification` | 否 | 数字人面谈是否跳过候选人验证页 |
| `--interviewers <json>` | 普通面谈必填 | 面谈官 JSON 数组；数字人面谈可省略，省略时默认补 `sourceType=DIGITAL_HUMAN, staffId=1` |
| `--interviewees <json>` | 是 | 面谈对象 JSON 数组；数字人面谈必须且只能有一个候选人 |
| `--others <json>` | 否 | 其他参与人 JSON 数组；数字人面谈不支持非空 `others` |
| `--outlineMdText <markdown>` | 否 | Markdown 格式面谈大纲，最终写入请求体 `outline.mdText`，如果不填写则由服务端生成，最多 `20000` 字符 |
| `--referenceInfo <text>` | 否 | 其他参考信息 |
| `--json <json>` | 否 | 直接传入 JSON 字符串，调试用，不能和分项参数混用 |
| `--stdin` | 否 | 从标准输入读取 JSON 字符串，调试用，不能和分项参数混用 |
| `--output-file <file>` | 否 | 将最终 JSON 结果额外写入文件 |
| `--dry-run` | 否 | 只打印请求信息，不真正执行 |

## 面谈大纲

`+launch` 支持传入 Markdown 格式面谈大纲。分项参数使用 `--outlineMdText`；JSON/STDIN 输入使用嵌套字段：

```json
{
  "outline": {
    "mdText": "## 面谈目标\n- 复盘 Q2 目标达成\n- 确认下阶段支持事项\n ..."
  }
}
```

规则：

1. `outline.mdText` 非空时，服务端会直接保存该 Markdown 大纲，不再触发后台自动生成面谈大纲。
2. 不传 `outline`、不传 `outline.mdText` 或内容为空白时，服务端按模板后台生成面谈大纲。
3. `outline.mdText` 最多 `20000` 字符。
4. Markdown 正文可以包含标题、列表、编号列表等标准 Markdown 内容；命令行多行文本需要整体作为同一个参数传入，复杂内容优先使用 `--json` 或 `--stdin`。

## 静态目的与模板

| purposeId | 目的名称 | templateId | 模板名称 |
|-----------|----------|------------|----------|
| `purpose_001` | 通用会议 | `template_001` | 通用会议 |
| `purpose_002` | 面试记录 | `template_002` | 面试记录 |
| `purpose_003` | 新员工融入Check-in | `template_003` | 新员工融入Check-in |
| `purpose_004` | 周期绩效复盘 | `template_004` | 周期绩效复盘 |
| `purpose_005` | 绩效辅导与提升 | `template_005` | 绩效辅导与提升 |
| `purpose_006` | 个人发展（IDP）面谈 | `template_006` | 个人发展（IDP）面谈 |
| `purpose_007` | 周度1-on-1 | `template_007` | 周度1-on-1 |
| `purpose_008` | 项目复盘 | `template_008` | 项目复盘 |
| `purpose_009` | 离职复盘与洞察 | `template_009` | 离职复盘与洞察 |

规则：

1. 用户明确说“绩效复盘”，使用 `purpose_004` / `template_004`。
2. 用户明确说“绩效辅导”，使用 `purpose_005` / `template_005`。
3. 用户没有表达具体目的时，默认 `purpose_001` / `template_001`，并告知按通用会议创建。
4. 不要传 `templateItemId`；服务端会按 `templateId` 或 `purposeId` 解析最新可用模板项。

## 参与人对象

`interviewers`、`interviewees`、`others` 的每个元素结构：

```json
{
  "staffId": "staff-001",
  "name": "李经理"
}
```

字段规则：

| 字段 | 必填 | 说明 |
|------|------|------|
| `staffId` | 内部人员必填 | 来自 `base +selectStaffs` 的 `dataList[].id`；内部人员不能只传姓名 |
| `name` | 外部人员必填，内部人员建议 | 展示用姓名；外部人员没有 `staffId` 时必须提供 |
| `sourceType` | 否 | 未传时，有 `staffId` 的人员按当前产品补 `IHR360/WORK100`，没有 `staffId` 的人员补 `EXTERNAL`；数字人面谈官使用 `DIGITAL_HUMAN` |
| `phone` / `email` | 外部人员建议，数字人候选人至少一个 | 外部人员联系方式；数字人面谈候选人必须至少提供一个 |

LLM 规则：

1. 如果用户只给人员姓名，优先按内部人员处理，必须先调用 `ihr-cli base +selectStaffs`，不能把姓名直接当作 `staffId`。
2. `total=0` 时告诉用户没找到。
3. `total=1` 且姓名高度一致时，可以采用该 `id`。
4. `total>1` 时必须展示候选并让用户确认，不能自动选第一个。
5. 只有用户明确说明是外部人员，或内部人员查找无匹配且用户确认按外部人员处理时，外部人员才可以没有 `staffId`，但必须提供 `name`，并尽量补充 `phone` 或 `email`；此时 CLI 会将缺省 `sourceType` 补为 `EXTERNAL`。数字人候选人必须有 `phone` 或 `email`。

## 数字人面谈

数字人面谈仍走 `conference +launch`，不会暴露后端 `DA_*` 或 `REGULAR_*` 角色码。CLI 只传参与人业务字段，后端根据 `thirdPartyPlatform=DIGITAL_AVATAR` 或 `interviewMode=DIGITAL_AVATAR`、`digitalAvatarConfig` 和参与人 `sourceType` 推导角色。

关键规则：

1. 必须通过 `thirdPartyPlatform=DIGITAL_AVATAR` 或 `interviewMode=DIGITAL_AVATAR` 表达数字人面谈。
2. 必须传 `digitalAvatarConfig.interviewCode`，分项参数可用 `--interviewCode`；它是数字人面试模板 ID，不是 conference `templateId`。如果用户没有提供，可以先用 `ihr-cli conference +search-avatar-template` 搜索已有模板；没有合适模板时再用 `ihr-cli conference +create-avatar-template` 创建，并把返回的 `templateId` 作为 `interviewCode`。
3. 数字人面谈官使用 `interviewers[].sourceType=DIGITAL_HUMAN`，`staffId` 是数字人配置 ID；不传数字人面谈官或唯一数字人面谈官的 `staffId` 为空时，会默认补 `staffId=1`。如果显式传非空 `staffId`，必须是数字字符串。
4. 候选人必须是唯一 `interviewees[0]`，需要 `name` 和 `phone` 或 `email`，可以不传 `staffId`。
5. 真人监考官是非 `DIGITAL_HUMAN` 的 `interviewers[]`，只有 `allowObserverIntervention=true` 时允许，且必须且只能有一个；未开启时不能传真人监考官。
6. 数字人面谈不支持 `others`。
7. 不要传 `roleCode`、`DA_INTERVIEWER`、`DA_CANDIDATE`、`REGULAR_*` 等后端内部角色值。

## 时间规则

`startTime` 必须使用 ISO-8601 offset datetime：

```text
2026-05-28T15:00:00+08:00
```

遇到“明天下午三点”“下周一上午十点”这类相对时间时，先基于当前系统日期换算成绝对时间。默认时区按 `Asia/Shanghai`，即 `+08:00`。

## 核心约束

### 1. 真实副作用

`+launch` 会真实创建并发起面谈。用户意图不明确时，先追问或使用 `--dry-run`。

### 2. 人员 ID 不能猜

拿到姓名时优先查找内部人员。内部人员的 `staffId` 必须来自选人能力或用户明确提供的确认结果，不能把姓名直接当作 `staffId`。只有用户明确说明是外部人员，或内部人员查找无匹配且用户确认按外部人员处理时，外部人员才可以没有 `staffId`，但必须有姓名、手机号、邮箱等可识别信息。

### 3. 所属专项暂不支持绑定

如果用户提到专项，可以把专项文本放入 `referenceInfo`；不要传 `campaignId`。当前传入 `campaignId` 会返回错误。

### 4. 缺少关键字段先追问

缺少以下任一关键字段时不要发起：

1. `title`
2. `startTime`
3. `interviewers`
4. `interviewees`

普通线上面谈可以省略 `interviewMode` 和 `thirdPartyPlatform`，服务端会默认按 `ONLINE/TENCENT_MEETING` 解析。数字人面谈的关键字段略有不同：可以不传 `interviewers`，但必须通过 `thirdPartyPlatform=DIGITAL_AVATAR` 或 `interviewMode=DIGITAL_AVATAR` 表达数字人面谈，并传 `interviewCode`、唯一候选人及候选人联系方式。

## 输出结果

CLI 统一输出：

```json
{"success":true,"command":"launchConference","request":{},"response":{}}
```

业务字段从 `response.data` 读取，重点包括：

| 字段 | 说明 |
|------|------|
| `response.data.conferenceSessionId` | 面谈会话 ID |
| `response.data.conferenceStatus` | 面谈状态，成功发起后通常为 `READY` |
| `response.data.title` | 面谈主题 |
| `response.data.startTime` | 开始时间 |
| `response.data.duration` | 面谈时长 |
| `response.data.meetingInfo` | 三方会议相关信息，结构由服务端返回 |
| `response.data.participants[]` | 参与人列表 |

## 常见错误与排查

| 错误现象 | 根本原因 | 解决方案 |
|---------|---------|---------|
| `title 不能为空` | 缺少面谈主题 | 先补充主题 |
| `startTime 不能为空` | 缺少开始时间 | 先确认绝对时间 |
| `startTime 必须是 ISO-8601 offset datetime` | 时间格式不对 | 使用 `2026-05-28T15:00:00+08:00` |
| `interviewers 不能为空` | 缺少面谈官 | 先通过 `base +selectStaffs` 确认人员 |
| `interviewees 不能为空` | 缺少面谈对象 | 先通过 `base +selectStaffs` 确认人员 |
| `staffId 和 name 不能同时为空` | 参与人缺少可识别信息 | 内部人员先选人拿 `staffId`；外部人员至少传 `name`，并尽量补充 `phone` 或 `email` |
| `templateId ... 与 purposeId ... 不匹配` | 模板和目的不一致 | 使用静态表中的同一行组合 |
| `当前版本不支持绑定所属专项` | 传入了 `campaignId` | 暂把专项说明放入 `referenceInfo` |
| `digitalAvatarConfig.interviewCode 不能为空` | 数字人面谈缺少数字人面试模板 ID | 传 `--interviewCode` 或 JSON 中的 `digitalAvatarConfig.interviewCode` |
| `数字人面试候选人 phone/email 至少传一个` | 数字人候选人没有联系方式 | 给唯一候选人补 `phone` 或 `email` |
| `数字人面试暂不支持其他参与人` | 数字人面谈传了 `others` | 移除 `others`，如需真人监考官用 `interviewers` 加 `allowObserverIntervention=true` |
| `数字人面谈官 staffId 必须是 digitalHumanId` | 数字人面谈官显式传了非数字配置 ID | 不传该字段使用默认 `1`，或传数字人配置 ID，例如 `1`、`123456` |
| `允许真人监考官介入时必须且只能有一个真人面谈官` | 开启真人介入但未传或传了多个真人监考官 | 在 `interviewers` 中保留一个非 `DIGITAL_HUMAN` 真人监考官 |

## 提示

- 简单发起可以用分项参数；参与人多时优先使用 `--json` 或 `--stdin`。
- 发起前不确定时，先用 `--dry-run` 查看最终请求体。
