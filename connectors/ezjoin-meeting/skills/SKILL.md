---
name: ezjoin-meeting-skill
description: EzyJoin 智慧会议操作技能 - 预约会议室、创建/取消会议、查询会议日程与 AI 纪要、企业知识库检索
version: "1.0.0"
author: "EzyJoin Team"
---

# EzyJoin 智慧会议 Skill

本 Skill 提供 EzyJoin 智慧会议平台的完整操作能力。所有操作通过 MCP Server 暴露的工具完成，无需拼接 URL 或设置请求头。

## 认证说明

- 用户需先完成 OAuth 授权（WorkBuddy 自动引导，浏览器登录 EzyJoin 账号后点击"允许"）
- 授权后 WorkBuddy 自动携带 access_token，MCP Server 自动识别当前用户身份
- access_token 有效期 1 小时，过期后 WorkBuddy 自动用 refresh_token 续期（30 天），无需用户干预
- 若 refresh_token 也过期，提示用户重新授权即可
- **不要要求用户提供 userId**：当前用户身份已由授权自动确定，userId 参数由服务端自动注入

## 可用工具

### teamMembers - 查询团队成员

查询当前用户加入的所有团队及成员清单。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| teamId | integer | - | 团队ID，不传则返回所有团队 |

**使用示例**：
- 用户问"我有哪些团队/同事"时调用，无需参数
- 用户提到某团队名称时，先调用本工具拿到 teamId

### meetingList - 查询会议列表

查询团队成员（含自己）权限范围内参与的所有会议，含各种审核状态（审批中/已通过/无需审核/已驳回）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| teamId | integer | - | 仅查指定团队的会议 |
| creatorUserId | integer | - | 仅查指定创建人的会议 |
| subject | string | - | 会议主题模糊搜索，最大100字符 |
| start_time | string | - | 开始时间 >= 该时间，格式 Y-m-d H:i:s |
| end_time | string | - | 开始时间 <= 该时间，格式 Y-m-d H:i:s（跨度最多30天） |
| page | integer | - | 页码，默认1 |
| pageSize | integer | - | 每页数量，默认20，最大100 |

**使用示例**：
- 用户问"我今天的会议"→ 传 start_time/end_time 为当天 00:00:00~23:59:59
- 用户问"本周/本月会议安排"→ 按时间范围过滤
- 返回的 auditStatus 可直接判断是否在审批中：1=无需审核、2=审批中、3=已通过、4=已驳回

### meetingDetail - 查询会议详情

查询指定会议的详细信息（主题、时间、会议室、参会人等）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| meetingId | integer | ✅ | 会议ID |

**使用示例**：
- 用户问"XX会议的详情"→ 先用 meetingList 找到 meetingId，再调用本工具

### meetingTranscription - 查询会议转写

查询指定会议的转写内容（语音转文字记录）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| meetingId | integer | ✅ | 会议ID |

### meetingMinutes - 查询会议 AI 纪要

查询指定会议的 AI 纪要内容。type=4 为全文纪要（默认），其他类型为分段纪要：1=会议议程、2=会议决议、3=会议任务。当前用户无纪要时自动回退到该会议最新一份纪要（管理员可查看成员纪要）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| meetingId | integer | ✅ | 会议ID |
| type | integer | - | 纪要类型：4=全文纪要(默认), 1=议程, 2=决议, 3=任务 |

**使用示例**：
- 用户问"XX会议的纪要/会议记录"→ 先 meetingList 找 meetingId，再调用本工具（默认全文纪要）
- 用户问"会议有什么决议/任务"→ 传 type=2 或 type=3
- 会议尚无纪要时返回 content=null，应如实告知用户纪要尚未生成

### companyUsers - 搜索公司用户

搜索公司用户（扁平列表），支持按姓名/手机/邮箱/拼音模糊搜索。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | - | 搜索关键词，不传返回全部 |
| pageSize | integer | - | 每页数量，默认20，最大100 |

### inviteUserList - 查询可邀请参会人

查询可邀请为参会人的用户列表（按部门分组），用于创建会议前查找参会人。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | - | 搜索关键词（部门名或用户姓名/手机/邮箱） |

### buildingRoomTree - 查询楼宇/会议室树

查询当前公司下所有楼宇、区域、会议室的三级树结构。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| 无 | - | - | 直接调用即可 |

**使用示例**：
- 用户问"有哪些会议室"或预约前先查会议室 → 调用本工具，返回楼宇(building)→区域(area)→会议室(meetingRoom)结构，取 meetingRoom 的 id/value 作为 meetingRoomId

### meetingRoomAvailability - 查询会议室占用情况

查询指定时间段内会议室的占用情况（空闲/已占用及冲突会议），用于预约前判断可用性。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startTime | string | ✅ | 开始时间，格式 Y-m-d H:i:s |
| endTime | string | ✅ | 结束时间，格式 Y-m-d H:i:s |
| meetingRoomId | integer | - | 会议室ID（可选，只查指定会议室） |
| buildingId | integer | - | 楼宇ID（可选，只查该楼宇下的会议室） |

**使用示例**：
- 预约前先调用本工具确认会议室空闲，若占用需如实告知用户并推荐其他可用会议室
- 用户说"帮我找明天下午空闲的会议室"→ 结合 buildingRoomTree + 本工具（不带 meetingRoomId）筛选

### meetingCreate - 创建会议

创建会议。type=1 线下日程（仅会议室），type=2 综合会议（会议室 + 线上视频会议）。支持周期会议（meetingType=1 + repeatType/repeatUntil）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| type | integer | - | 1=线下(默认), 2=综合会议 |
| meetingType | integer | - | 0=单次(默认), 1=周期会议 |
| repeatType | integer | 周期时必填 | 0=每天, 1=每周, 2=每月, 7=每个工作日 |
| repeatUntil | string | 周期时必填 | 重复截止时间，格式 Y-m-d H:i:s，最多向后1年 |
| repeatInterval | integer | - | 重复间隔，仅每周生效，默认1 |
| meetingRoomId | integer | ✅ | 会议室ID（从 buildingRoomTree 获取） |
| startTime | string | ✅ | 开始时间，格式 Y-m-d H:i:s |
| endTime | string | ✅ | 结束时间，格式 Y-m-d H:i:s |
| platform | integer | type=2 时必填 | 1=企微, 4=飞书, 5=腾讯会议 |
| password | string | - | 入会密码（最大20字符） |
| subject | string | - | 会议主题，最大50字，默认"未命名会议" |
| content | string | - | 会议描述/预约原因，最大500字 |
| inviteUserIds | integer[] | - | 参会人 userId 数组 |

**时间规则**（不满足会创建失败）：
- startTime 必须晚于当前时间
- endTime 必须晚于 startTime
- 时长不少于 5 分钟

**使用示例**：
- "帮我预约明天下午 3 点到 4 点的会议室" → 先 buildingRoomTree 选会议室 → meetingRoomAvailability 确认空闲 → meetingCreate
- **创建后必须检查返回结果**：isError=true 或 code!=200 表示失败，必须如实把失败原因（msg）告知用户，禁止谎报"预约成功"

### meetingEdit - 更新会议

更新当前用户自己创建的未开始会议。只传需修改的字段，未传的保持不变。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| meetingId | integer | ✅ | 会议ID |
| subject | string | - | 新主题，最大50字 |
| content | string | - | 新描述，最大500字 |
| startTime | string | - | 新开始时间，格式 Y-m-d H:i:s |
| endTime | string | - | 新结束时间，格式 Y-m-d H:i:s |
| inviteUserIds | integer[] | - | 参会人 userId 数组（传此字段时替换全部参会人） |

**注意事项**：
- 只能修改自己创建的、未开始的会议
- 时间规则同创建会议
- 更新后必须检查返回结果，失败时如实告知用户原因

### meetingCancel - 取消会议

取消当前用户自己创建的未开始会议。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| meetingId | integer | ✅ | 会议ID |

**使用示例**：
- 用户说"取消 XX 会议" → 先用 meetingList 确认会议存在且可取消，再调用
- 调用后必须检查返回结果，失败时如实告知原因

### sendWeworkMessage - 发送企业微信消息

向公司成员发送企业微信消息。支持 text 文本和 textcard 卡片消息。收件人必须是当前用户同公司的有效用户。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| recipientUserIds | integer[] | ✅ | 收件人 userId 数组（至少1个，需为本公司用户） |
| msgType | string | ✅ | text=文本, textcard=卡片 |
| content | string | ✅ | 消息内容，最大2000字符 |
| title | string | textcard 时必填 | 卡片标题，最大100字符 |
| url | string | - | 卡片跳转链接，最大500字符 |

**使用示例**：
- 用户说"给张三发条企微消息说下午开会" → 先 companyUsers 找到张三 userId → 调用本工具
- 用户说"发个会议通知卡片给参会人" → msgType=textcard，title 填"会议通知"，url 填会议链接

### sendEmail - 发送邮件

向公司成员发送邮件（通过企业微信邮箱发送）。收件人可通过 userId 或邮箱地址指定，至少需要一种。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| recipientUserIds | integer[] | - | 收件人 userId 数组（与 recipientEmails 至少填一个） |
| recipientEmails | string[] | - | 收件人邮箱地址数组（与 recipientUserIds 至少填一个） |
| ccUserIds | integer[] | - | 抄送人 userId 数组 |
| ccEmails | string[] | - | 抄送邮箱地址数组 |
| subject | string | ✅ | 邮件主题，最大200字符 |
| content | string | ✅ | 邮件正文，最大10000字符 |
| contentType | string | - | html 或 text（默认 text） |

**使用示例**：
- 用户说"给团队发封邮件" → 先 companyUsers/teamMembers 找到收件人 → 调用本工具
- 收件人指定：recipientUserIds 与 recipientEmails 至少填一种，否则工具会报错

### scheduledTaskCreate - 创建 AI 定时任务

创建一个 AI 助手定时任务，按指定频率自动执行提示词。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| title | string | ✅ | 任务标题，≤100字 |
| prompt | string | ✅ | 提示词，执行时发送给 AI 助手 |
| frequency | integer | ✅ | 1=每天 2=按间隔 3=单次 |
| executeTime | string | frequency=1 必填 | HH:MM |
| intervalHours | integer | frequency=2 必填 | 间隔小时数(1-24)，从每天0点起算 |
| weekdays | integer[] | - | 执行日 1-7（1=周一 7=周天），不传=每天 |
| executeDate | string | frequency=3 必填 | Y-m-d H:i:s |
| validStartDate | string | - | 生效开始日期 Y-m-d |
| validEndDate | string | - | 生效结束日期 Y-m-d |

### scheduledTaskList - 查询 AI 定时任务

列出当前用户的 AI 助手定时任务。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| frequency | integer | - | 按频率筛选：1=每天 2=按间隔 3=单次 |

### scheduledTaskUpdate - 修改 AI 定时任务

修改当前用户的 AI 助手定时任务（仅传需修改的字段）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| taskId | integer | ✅ | 任务ID |
| title | string | - | 新标题 |
| prompt | string | - | 新提示词 |
| frequency | integer | - | 1=每天 2=按间隔 3=单次 |
| executeTime | string | - | HH:MM |
| intervalHours | integer | - | 间隔小时数 |
| weekdays | integer[] | - | 执行日 1-7 |
| executeDate | string | - | Y-m-d H:i:s |
| validStartDate | string | - | Y-m-d |
| validEndDate | string | - | Y-m-d |

### scheduledTaskDelete - 删除 AI 定时任务

删除当前用户的 AI 助手定时任务。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| taskId | integer | ✅ | 任务ID |

### scheduledTaskPause - 暂停 AI 定时任务

暂停当前用户的 AI 助手定时任务，暂停后到点不再执行。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| taskId | integer | ✅ | 任务ID |

### scheduledTaskResume - 恢复 AI 定时任务

恢复当前用户已暂停的 AI 助手定时任务。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| taskId | integer | ✅ | 任务ID |

### knowledgeSearch - 搜索企业知识库

搜索企业知识库，返回文档标题和摘要。企业知识库文档（公司制度、流程规范、业务资料）始终包含在结果中。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| teamIds | integer[] | - | 团队ID数组，查这些团队下所有成员上传的文档 |
| meetingIds | integer[] | - | 会议ID数组，查这些会议的附件文档 |

**使用场景**：
- 用户询问公司制度、流程规范、业务资料、会议文档时使用
- 查询维度优先级：meetingIds > teamIds > 默认（只查当前用户自己的文档）

### knowledgeGet - 读取知识库文档全文

读取知识库中指定文档的原文全文。先调用 knowledgeSearch 拿到 docId 后再调用本工具。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| docId | integer | ✅ | 文档ID（从 knowledgeSearch 返回结果获取） |

## 通用注意事项

- **会议操作流程**：预约会议前先查会议室（buildingRoomTree）→ 查占用（meetingRoomAvailability）→ 创建（meetingCreate）；取消/改期先查列表（meetingList）确认 meetingId
- **如实反馈结果**：任何工具返回 isError=true 或 code!=200 时，必须把 msg 原样转达用户，禁止谎报成功
- **会议状态**：auditStatus=2 表示审批中，需等待审批通过；1=无需审核、3=已通过、4=已驳回
- **时间格式**：统一使用 Y-m-d H:i:s（如 2026-08-08 15:00:00）
- **权限边界**：只能操作当前用户自己创建或参与的会议；无权限时工具会返回明确错误
- **多租户**：每个用户只看到自己所属公司的数据，天然隔离
- **遇到 401/Token 过期**：提示用户重新授权，不要尝试绕过
