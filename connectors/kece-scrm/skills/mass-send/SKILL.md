---
name: mass-send
display_name: 企微群发
display_name_en: WeCom Mass Send
description: 创建企业微信客户群发任务，支持按标签/客层圈选人群、配置文案与附件、选择发送员工。触发词：群发、发消息、发通知、推送、触达、发送话术。
description_zh: 创建企业微信客户群发任务，支持按条件圈选人群、配置文案与附件、选择发送员工。
description_en: Create WeCom customer mass-send tasks with audience filters, message content, attachments, and sender selection.
version: 1.0.0
author: 网易云商
allowed-tools: get_customer_fields, search_customers, list_staff, list_segments, create_mass_send
examples_zh:
  - 给打了VIP标签的客户发一条春季回归活动通知，发送人用张三
  - 给这批沉默用户发一条促销消息，附上活动链接
  - 用 RPA 群发把这批客户的通知直接发出去
examples_en:
  - Send a spring comeback notice to VIP customers via Zhang San
  - Send a promo message with a link to this dormant audience
  - Use RPA send to deliver this notice automatically
---

# 企微群发

## 何时使用

用户要发消息给一批客户时使用。可接续「智能圈人」产出的人群条件；用户直接给条件时也可独立使用。

## 执行顺序

1. 确认人群：优先读取上文圈人环节给出的条件摘要与人数；没有的话询问用户发给谁，或引导先圈人。
2. 确认发送人：调用 `list_staff` 获取员工 accid，**严禁猜测 accid**。用户指定姓名时按姓名匹配；重名时请用户确认。
3. 确认群发要素：文案（必填）、附件（可选）、群发方式（普通 / RPA）、发送时间、发送间隔。
4. 展示完整预览并等待用户确认。
5. 用户确认后调用 `create_mass_send`，返回任务 ID 并说明后续动作。

## 工具与关键参数

### create_mass_send

| 参数 | 必填 | 说明 |
|---|---|---|
| `wxfollowers` | 是 | 发送人 accid 字符串数组，来自 `list_staff` |
| `type` | 否 | `0` 普通群发（需员工在企微确认）/ `4` RPA 群发（自动直发），默认 0 |
| `textContent` | 条件必填 | 文本内容，最长 4000 字符；与 `medias` 至少提供一个 |
| `medias` | 否 | 附件数组，每项 `{ sendType, picUrl?, linkUrl?, linkTitle?, linkContent? }`，`sendType`：1 链接 / 2 图片 / 3 小程序 |
| `filterType` | 是 | `quick` 快捷筛选 / `advanced` 高级筛选 / `segment` 按人群包 |
| `filterFields` | 条件必填 | `{ fieldId: string, filterType: number, filterValue: string }[]`，`quick`/`advanced` 时使用 |
| `segmentIds` | 条件必填 | 数字数组，`segment` 时使用 |
| `sendInterval` | 否 | 发送间隔（分钟） |
| `sendNumOnetime` | 否 | 每批发送人数，不小于 1000 |
| `allowAutoSend` | 否 | 是否自动发送，默认 false |

`filterFields[].filterType` 取值与圈人环节一致：1 满足/包含、2 不为空、3 包含所有、4 不包含、5 等于、6 不等于、7 介于、8 大于、9 小于。

### list_staff

查询企业员工列表，返回 `accid`、姓名、角色、部门。

## 规则

- **所有群发必须经用户确认后才可调用 `create_mass_send`。** 群发不可撤回。
- 确认预览必须包含：目标人群（条件摘要或人群包名称 + 人数）、发送人、群发方式、文案、附件、发送间隔。
- 选择 RPA 群发（`type=4`）时必须额外警告：将自动直发，不需要员工在企微确认。
- 严禁猜测 `wxfollowers`、`fieldId`、`segmentIds`。
- 文案最长 4000 字符；附件为图片/视频时注意 RPA 模式支持范围。
- 大批量群发建议分批，并提示用户预估耗时。
- 不要一次群发超过 50000 人。
