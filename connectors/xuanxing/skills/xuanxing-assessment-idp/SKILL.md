---
name: xuanxing-assessment-idp
description: The current user's assessments and development plan on 绚星 (Xuanxing) - 测评 tasks and reports, the individual development plan (IDP) with its action items, periodic plan reviews, and talent calibration meetings. Use when the user asks 我还有哪些测评没做 / 测评结果 / 我的发展计划 / IDP / 我的行动计划 / 计划回顾 / 我要参加的盘点校准. Do not use for maps or certification - that is xuanxing-growth-map.
description_en: Assessments and development planning on Xuanxing - assessment tasks and reports, IDP with action items, plan reviews, and calibration meetings.
description_zh: 查询我在绚星的测评任务与报告、个人发展计划（IDP）及行动项、计划回顾和盘点校准会议。
allowed-tools:
disable: false
version: 1.0.2
author: 绚星
---

# 测评与发展计划

## 前置

先读 `xuanxing-shared`，确认连接与授权。

## 何时使用

- 「我还有哪些测评没做」「我的测评结果出来了吗」
- 「我的发展计划要做什么」「我的 IDP」「我的行动计划完成了吗」
- 「我的发展计划回顾得怎么样」「辅导人怎么评价我的」
- 「我要参加哪些盘点校准」

## 何时不要使用

| 用户想问 | 用哪个 |
|---|---|
| 岗位 / 层级地图、认证项目 | `xuanxing-growth-map` |
| 考试（不是测评） | `xuanxing-study-todo` / `xuanxing-study-progress` |
| **鉴定 / 待鉴定**（不是测评） | `xuanxing-teaching-todo` 的 `list_my_appraisals` |

⚠️ **「测评」不是「考试」，也不是「鉴定」。** 测评是能力/人格/问卷评估
（`list_my_assessments`）；鉴定是教学端对学员的评定审核任务
（`list_my_appraisals`，在 `xuanxing-teaching-todo` 里）。常见错误：用户问
「我还有哪些待鉴定的任务」，被当成测评去调 `list_my_assessments`，
返回的是测评数据，用户问的"鉴定"一条没答。
**看到"鉴定"字样一律转 `xuanxing-teaching-todo`，不要在本技能里找。**
用户说「考试」时同样不要用本技能。

## 调用流程

**测评** → `list_my_assessments`，不传参数。

**发展计划** → `get_my_development_plan`，不传参数。它会把计划信息和行动项一起取回。

⚠️ **用户问「以前的 / 历史的 / 往年的发展计划」要传 `include_history=True`。**
默认只返回**当前**计划（常常只有 1 个），而平台「历史 IDP」里可能有几十个。
不传就回答「你只有一个计划」= 拿一次没查过的东西替平台下结论。
返回里的 `history_plans` 为 `null` 是**没查**，空数组才是真的没有历史计划。

**计划回顾** →
1. **先**调 `get_my_development_plan` 拿到计划标识
2. **再**调 `get_my_plan_review`
3. 用户有多个计划时**问用户**是哪一个

**盘点校准** → `list_my_calibrations`，不传参数。
它只返回**我参与的**，不包含我组织的会议。

## 输出规范

- 测评按状态分组：待评估 / 已评估 / 未参与。⛔ **每项都要给名称、起止时间，
  并把测评名称做成指向 `entry_url` 的链接**——`entry_url` 是平台内的测评入口，
  **每条都有**（自评、评价别人、各种测评类型通用），一条都不许漏。
  `start_time`/`end_time` 有值就要写进回答（已完成的测评也一样有起止时间），
  不要漏。
  `url`（第三方直达答题链接）为 `null` 是正常的，**不要**因此说"这条没有进入链接"——
  入口看 `entry_url`。
- ⛔ **待评估（还没做）的清单不要放「报告」列。** 还没做完的测评不可能有报告，
  这一列只会是一排「—」。报告只在**已评估**的测评里说。
- ⚠️ **说"一共有多少个测评"时用 `meta.total_distinct_plans`，不要用 `meta.total`。**
  `total` 是任务条数（我要评的每个人算一条，一个测评方案可能摊成上百条）；
  `total_distinct_plans` 才是去重后的测评方案个数，只在 `status="all"` 时有值。
  其他 status（pending/done/not_joined）下 `total_distinct_plans` 是 null，
  这几档目前没有验证过的去重数字，只能报任务条数并说明单位
  （field_notes 里"总数"那条有完整措辞）。
- ⚠️ **进入链接的 `url_is_external` 为 true 时必须加一句提醒。**
  那是**第三方测评平台**的链接，不在本机构域名下，而且地址里**带着这个人专属的
  答题通行码**。给链接时同时说：这是你的个人专属答题入口、**不要转发给别人**，
  也不要贴到群里或文档里。
  ⛔⛔ **把 `url` 原样整段复制进回答，不要凭记忆重新打一遍。**
  通行码区分大小写又没有校验位，抄错一个字母肉眼看不出来，
  链接打开后第三方平台会直接登录失败。只有原样复制才保真。
- 已评估的测评：报告**已下发**的给报告链接；**未下发**的明确说「报告还没出来」，
  不要让用户以为是查询失败。
- 发展计划要给：计划名称、周期、辅导人、当前状态，然后逐条列行动项，
  每条给**是否达成**（`achieved`）。
  ⛔⛔ **`achieved` 为 `null` 只能说「还没有评价结论」（还没评价，或辅导人选的是
  「按计划进行中」），绝不能说成「未达成」。**
  这是本技能里**最容易答错的一条**，务必对照 `actions[].achieved`
  原始值回答，不要凭"没达成吧"这种直觉下结论。
  ⚠️ **得分不给分值，但要先看 `plans[].scoring_enabled` 再回答**：
  `false` → 说「这个计划的打分开关没有开启」（平台上就是「打分开关未开启」，
  **不要**说成「不对外显示」——那会让用户以为分数被藏起来了；也不要替平台断言
  「一定没有分数」）；
  `true` → 开了打分，`not_available.scores` 里写明分值属于合规限制，
  说「得分这边暂时不对外显示」；`null` → 说「打分是否开启这边没查到」，不要猜。
  ⚠️ 这个开关**不覆盖周期回顾**：回顾的打分开关另看 `reviews[].scoring_enabled`，
  同一个人可能计划没开、回顾开了，别拿一个回答另一个。
  无论哪种都**不要**说「需要另外查」
  （没有另一个地方能查到，说"另外查"等于让用户去找一个不存在的入口）。
- 回顾要先点出**回顾名称**（`reviews[].name`），再说流程走到
  哪一环（`flow_status`），以及**本人**（`my_review`）和**对方**（`mentor_comment`）
  分别写了什么。⚠️ **不要**因为回顾名称看起来像个编号就当成不重要略过，
  用户认的就是这个名称。
  ⚠️ **不要指望拿到第三份独立意见。**
  `roles_in_flow` 解出来可能是「员工/导师/辅导人」三个角色，但平台数据结构
  **只有两套意见字段**——`mentor_comment` 是「导师」和「辅导人」共用的那一个，
  没有单独的第三个字段。看到三个角色别去找一个不存在的第四个字段，
  也不要把 `mentor_comment` 的署名替用户猜成"导师"还是"辅导人"，照工具给的说。
  ⚠️ **「这次回顾达成了没有」这个结论给不了**（`not_available.achievement_result`）——
  `evaluate_status_raw` 等几个码值字段没拿到官方字典，**不许**翻译成
  "达成/未达成"。能说的是流程走到哪一环、双方写的文字意见原文，
  结论性的达成与否让用户自己去平台看。**打分功能是否开启**可以说
  （`scoring_enabled`），**具体分值不给**（同上，合规限制）。

### 已知限制（照实说，不要编）

> ⚠️ 本表是**预期管理**，不是本次调用的观察结果。
> 照实回答要以工具返回的 `not_available` 为准（见 `xuanxing-shared` 的硬规矩）。
> **没调过的工具，不要替它声明限制。**

| 用户可能会问 | 现状 | 你该怎么回答 |
|---|---|---|
| 测评报告在哪下载 | 报告链接多半只有人格类测评才有 | **看这一条返回里有没有报告链接**，有就给，没有就说这条没有可下载的报告 |
| 辅导人/导师具体写了什么评语 | **能给**——`mentor_comment` 就是这个，为 null 才是还没写 | 取到就原样引用；为 null 就说「对方还没写」，不要说成「没有评价」 |
| 这次回顾最终达成了没有 | **给不了**——相关码值字段没有官方字典，不确定怎么翻译 | 说「达成与否这边看不出来，只能给流程进度和双方的文字意见」，**不要猜一个答案** |

### 合规限制

- `get_my_development_plan` 底层接口会同时返回「我辅导的人」的计划。
  工具**只返回本人的**。用户问「我辅导的人计划怎么样」时，
  说明本技能只看自己的，让他到平台查。
- 回顾里其他角色的评价属于对**本人**的评价，可以展示；
  但**不要**展示其他被辅导人的任何数据。

- 能力评估等级、测评得分**不展示具体等级分值**，只说「已完成 / 未完成」和达成与否。

## 错误处理

按 `xuanxing-shared` 的错误码表。

- 没有进行中的 IDP 时返回空 —— 说「你当前没有进行中的发展计划」，不是错误。
