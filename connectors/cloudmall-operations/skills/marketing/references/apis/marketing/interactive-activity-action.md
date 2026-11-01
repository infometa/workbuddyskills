# 营销域 — 互动营销活动写操作契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/interactive-activity-flow.md`
> 互动活动为 draft/formal 双版本模型：同一活动 ID 恒有 draft（运营编辑）副本，发布后追加 formal（C 端运行）副本。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `interactive-activity-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：interactive-activity.create 创建互动活动 🟡 · interactive-activity.update 编辑互动活动 🟡 · interactive-activity.set-priority 设置互动活动优先级 🟡 · interactive-activity.save-relative-scenes 保存关联应用场景 🟢

---

## ✅ 创建活动 — `ops.marketing.interactive-activity.create`

- **风险**：🟡 可逆写（仅落草稿，未发布不生效）
- **前置**：开始时间不能早于当前时间，结束时间必须晚于开始时间；configInfo 必填且需含该活动类型"必需玩法桶"（见下表），桶内强类型规则键会逐项校验。

**活动类型 → 必需玩法桶**（configInfo 外层 key 缺一不可）：

| activityType | 必需桶 |
|--------------|--------|
| sudoku-lottery / dzp / newcomer-gift / open-screen-gift | COMMON、PROBABILITY |
| daily-checkin | SIGN |
| exchange-code | COMMON |
| share-gift | COMMON、SHARE、PROBABILITY |
| yqzl | COMMON、ASSIST、PROBABILITY |

玩法桶（configInfo 外层 key）：COMMON（通用配置）、PROBABILITY（概率抽奖）、SIGN（签到）、SHARE（分享）、INVITE（邀请）、ASSIST（助力）。

**configInfo 校验行为**（服务端 `InteractiveConfigInfoValidator` 三段式）：
- 外层 key 必须是玩法桶名（非 PlayType 枚举值直接报错）；必需桶缺失报「活动类型缺少必需的玩法配置桶」；
- 内层 key 未在协议表中的**未知键跳过校验**（允许扩展 KV，不报错）；
- 强类型规则键会反序列化后逐项校验，反序列化失败或注解校验失败**整单报错**（错误消息含 `configInfo[桶][键]` 定位）。发布时会对库中 configInfo 重新校验。

**⚠️ 已知环境限制**：部分环境对**新建**互动活动启用了「请选择适用人群」必填校验（code=5006），该字段未在本契约文档化、`userJoinRule` 配置后仍会被拦截；存量活动不受影响。**替代路径**：用 `interactive-activity.copy` 复制现有活动生成草稿再编辑（复制草稿不触发该校验，已验证可行）。若创建被此校验拒绝，不要反复尝试字段组合，如实告知用户改走复制路径或管理后台，并说明该限制待平台侧补文档。

**内层 key 协议表**（按桶分组；「—」为该桶不适用）：

| 桶 | 内层 key | 值结构与说明 |
|---|---|---|
| COMMON | activityTimeRule | `{startTime, endTime}`（**毫秒时间戳**，Long）；可选 `reserveTime`（毫秒）、`cycleType`（day/week/month/all）、`dayRange: ["09:00:00","21:00:00"]`（每日时段）、`weekRange`（每周几，1=周一..7=周日）、`dayRangeOfMonth: ["1","15"]`、`lastDaysOfMonth` |
| COMMON | userJoinRule | `{enable: Boolean, userType: blackList\|whiteList, allowJoin: Boolean}`（名单内用户能否参与） |
| COMMON | assistRule | `{assistCntForMasterPrize, assistCntForGuestPrize}`（每 N 次成功助力给主态/客态发奖；客态 0/null=不发；yqzl 用，分享有礼固定 master=1/guest=0） |
| COMMON | description / rules / activityLink / pageId / pageName / channelTypes | 字符串扩展键（channelTypes 为 string[] 投放渠道）；description 同时用于列表展示 |
| PROBABILITY | activityLimitRule | `{uid: {flag, default: {day, week, month, all}}}`（参与频次限制；day/week/month/all 为周期内累计次数整数；flag 2=不区分人群） |
| PROBABILITY | sendPrizeLimitRule | 结构同 activityLimitRule（发奖/中奖频次限制；奖品级发放限制在 prizeInfo 各奖品字段，不在此处） |
| PROBABILITY | rateLimitRule | `{enable: Boolean, ruleKey, timeWindow}`（接口限流；timeWindow 秒，0=不限） |
| PROBABILITY | prizeStrategy | 奖品策略数组（见下方 prizeStrategy 展开） |
| PROBABILITY | showPrizePool / noWinText | Boolean（是否展示奖品池）/ String（未中奖文案） |
| SIGN | signRule | `{type: sequential\|aggregate, startTime（毫秒时间戳）, period}`（sequential 连续签到 / aggregate 累计签到，仅此两值；period ≤0 不分周期；N=每 N 天一周期） |
| SIGN | prizeStrategy | 同上（签到按「第 N 天」逐条建策略） |
| SHARE | shareContentRule | `{pageId（≤64 字）, pageName（≤100 字）}`——分享卡片跳转的装修页；**share-gift 未配置分享页时保留空 SHARE 桶**（服务端豁免空桶校验） |
| ASSIST | prizeStrategy | 同上（yqzl 客态发奖策略） |
| INVITE | inviteRule | `{capacityDayLimit, expireType, expireValue, conditions}`——当前无活动类型绑定 INVITE 桶，无需构造 |
| 任意桶 | joinCondition / matchCondition / blockAndBlackRule / qualificationRule | 弱类型扩展点（引擎层解析、Validator 跳过），运营端不构造 |

**prizeStrategy（奖品策略）展开**（数组，每项）：

| 字段 | 类型 | 说明 |
|------|------|------|
| enable | Boolean | 策略启用开关，默认 false |
| priority | Integer | 优先级，数值越大越优先 |
| strategyId / strategyName | String | 策略 ID（前端生成 UUID）/ 策略名称 |
| conditions | Object | 匹配条件（弱类型；签到玩法用 `conditions.signCount.expression` 表达「第 N 天」） |
| prizePlans[] | Array | 奖品组：`{planId（UUID）, planName, conditions, sendModel, prizeList}` |
| prizePlans[].prizeList[] | Array | `{type, prizeTemplateId, prizeTemplateName, num}` + **`probality`（Integer，百万分制中奖概率——1000000=100%；按百分比口径录入时需 ×10000：5% = 50000、10% = 100000、0.1% = 1000、100% = 1000000；同一奖品组各奖品概率之和不得超过 1000000（超出时 C 端抽奖报错，创建时不拦截），剩余概率即未中奖、展示 noWinText）**；prizeTemplateId 须与 prizeInfo.prizeList[].templateId 对应，num 单次发放数量一般为 1 |

### 入参（顶层）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityName | String | ✅ | 活动名称，≤50 字 |
| activityType | String | ✅ | 活动类型 code（见上表） |
| startTime | String | ✅ | 开始时间（yyyy-MM-dd HH:mm:ss，须晚于当前） |
| endTime | String | ✅ | 结束时间（yyyy-MM-dd HH:mm:ss，须晚于开始） |
| configInfo | Object | ✅ | 双层 Map：`{ 玩法桶: { 规则名: 值 } }`（COMMON.description/rules 为字符串扩展键） |
| prizeInfo | Object | 否 | 奖品池配置（见下） |
| pageConfig | Object | 否 | 页面装修配置（弱类型）——**服务端不解析**（落库前仅剥离 COS URL 签名参数、回显时重签，其余原样存储并透传 C 端）；不同活动类型字段不同（九宫格 bgImage/gridImage/gridCells 等、大转盘 sectors 等），**从详情回显原值修改，不要自行构造** |

### prizeInfo 子结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is100Prize | Boolean | 否 | 抽奖必中托底，默认 false |
| prizeList[].templateId | String | 否 | 奖品模板 ID（奖品库选中后绑定） |
| prizeList[].prizeName | String | ✅ | 奖品名称 |
| prizeList[].imgUrl | String | 否 | 奖品图片 |
| prizeList[].prizeType | String | ✅ | points/coupon/physical |
| prizeList[].hasStock | Integer | 否 | 1=管理库存，0=不管理 |
| prizeList[].totalAmount | Integer | 否 | 活动期间总量（≥0；0/null 不限） |
| prizeList[].dailyAmount / weekAmount / monthAmount | Integer | 否 | 日/周/月发放总量（活动级，≥0） |
| prizeList[].dailyAmountPerUser / totalAmountPerUser | Integer | 否 | 单人单日/单人活动期总量（≥0） |
| prizeList[].alertAmount | Integer | 否 | 库存告警阈值（≥0） |
| onlyOneList.enable | Boolean | 否 | "每人最多中其中一个"互斥开关 |
| onlyOneList.value | String[] | 否 | 参与互斥的奖品模板 ID 列表 |

**prizeInfo 回显补充**：详情出参还可能含 `usedStock`（已发放数，服务端富化、写入忽略透传值）、`conditions`/`extraInfo`（弱类型扩展点）、`expireConfig`（`{expireType, expireValue}`——fixTime/fixTimePerDay 为毫秒时间戳，afterDay/afterHour/afterMin/afterSec 为数量值）、`recRemindConfig`（未领取提醒：remindType/remindValue/remindChannel=WX_MP/appId/msgTemplateId）、`published`/`assetTag`。**运营端创建只构造上表字段；中奖概率不在 PrizeItem 里，在 configInfo 的 prizeStrategy.prizePlans[].prizeList[].probality**。

### 出参（原始数据）

- **关键字段来源**：返回对象含 `activityId`（新活动业务 ID）→ 后续编辑/发布；`detailType` 恒为 draft。

### 调用示例

**对象层级**：`input` 必须为 JSON 对象，不是包含 JSON 的字符串；嵌套配置直接传对象/数组。`activityName/activityType/startTime/endTime/configInfo/prizeInfo/pageConfig` 均为顶层业务字段，`configInfo` 内只放玩法桶；奖品组字段为 `prizePlans`（不是 `planPlans`）。参数被拒时对照结构修正，不通过补括号、自动解包或更换执行器绕过校验。

下面示例的名称、时间、数量是示意值；时间须以本次用户指令及业务时区计算，奖品模板 ID/UUID 用查询结果或生成值替换。两项奖品模板已准备好时，九宫格草稿对象示例：

```json
{
  "capability": "ops.marketing.interactive-activity.create",
  "input": {
    "activityName": "九宫格福利草稿",
    "activityType": "sudoku-lottery",
    "startTime": "2026-11-01 00:00:00",
    "endTime": "2026-11-11 23:59:59",
    "configInfo": {
      "COMMON": {
        "activityTimeRule": {"startTime": 1793462400000, "endTime": 1794412799000},
        "description": "蓝牙耳机与优惠券抽奖"
      },
      "PROBABILITY": {
        "activityLimitRule": {"uid": {"flag": 2, "default": {"day": 1, "week": 0, "month": 0, "all": 0}}},
        "noWinText": "谢谢参与",
        "prizeStrategy": [{
          "strategyId": "9b53224c-37ad-42a7-a747-b60fc4af0c16",
          "strategyName": "默认策略",
          "enable": true,
          "priority": 1,
          "prizePlans": [{
            "planId": "9ff29728-dc2f-4f4f-9a74-058e5f00790f",
            "planName": "默认奖品组",
            "prizeList": [
              {"type": "physical", "prizeTemplateId": "5200000000000000001", "prizeTemplateName": "蓝牙耳机", "num": 1, "probality": 5000},
              {"type": "coupon", "prizeTemplateId": "5200000000000000002", "prizeTemplateName": "优惠券奖品", "num": 1, "probality": 50000}
            ]
          }]
        }]
      }
    },
    "prizeInfo": {"is100Prize": false, "prizeList": [
      {"templateId": "5200000000000000001", "prizeName": "蓝牙耳机", "prizeType": "physical", "hasStock": 1, "totalAmount": 1},
      {"templateId": "5200000000000000002", "prizeName": "优惠券奖品", "prizeType": "coupon", "hasStock": 1, "totalAmount": 50}
    ]}
  },
  "summary": "保存九宫格活动草稿，不发布"
}
```

**页面要求未完成的处理**：上例只展示活动与奖品规则，未构造 `pageConfig`。用户要求中间格「立即抽奖」、各格布局等时，必须核对可信页面配置；没有现值/受支持结构时不猜字段，不把 `noWinText` 当成格子布局。可保存规则草稿，但明确报告页面要求未完成、需要在运营端补齐；回读有页面配置且逐项核验后才宣称全部完成。

兑换码活动仅存草稿的最小对象如下；coupon 奖品模板的 `bizTemplateId` 须预先关联用户指定的促销券模板。草稿可保存不代表品牌码核验/领奖链路已实现，不能承诺上线即能兑换。

```json
{"capability":"ops.marketing.interactive-activity.create","input":{"activityName":"品牌联合兑换码草稿","activityType":"exchange-code","startTime":"2026-11-01 00:00:00","endTime":"2026-11-11 23:59:59","configInfo":{"COMMON":{"description":"品牌方兑换码联合福利","rules":"活动奖品共100份；兑换码核验链路待确认"}},"prizeInfo":{"is100Prize":false,"prizeList":[{"templateId":"5200000000000000002","prizeName":"优惠券奖品","prizeType":"coupon","hasStock":1,"totalAmount":100}]}},"summary":"保存品牌兑换码活动草稿，不发布"}
```

---

## ✅ 编辑活动 — `ops.marketing.interactive-activity.update`

- **风险**：🟡 可逆写（只改 draft，需再次发布才生效）
- **前置**：formal 未结束（TERMINATED/EXPIRED 不可编辑）。先读 draft 详情做基线，保留未改动字段。**已发布活动（存在 formal）的奖品总量只能增加不能减少**（防止超发），调小会报错。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |
| (其余字段) | - | ✅ | 结构同创建（activityName/activityType/startTime/endTime/configInfo/prizeInfo/pageConfig），整包覆盖 draft |

### 出参

- 无 data（成功即已保存）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.update","input":{"activityId":"1942000000000000001","activityName":"国庆到店兑换礼","activityType":"exchange-code","startTime":"2026-10-01 00:00:00","endTime":"2026-10-10 23:59:59","configInfo":{"COMMON":{"description":"到店出示兑换码参与活动","rules":"每人每日限参与一次，礼品数量有限先到先得"}}},"summary":"延长活动结束时间并保存草稿"}
```

---

## ✅ 设置优先级 — `ops.marketing.interactive-activity.set-priority`

- **风险**：🟡 可逆写
- **说明**：draft 与 formal（若存在）同步更新。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |
| priority | Integer | ✅ | 优先级（query 参数） |

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.set-priority","input":{"activityId":"1942000000000000001","priority":10},"summary":"提高活动展示优先级"}
```

---

## ✅ 保存关联应用场景 — `ops.marketing.interactive-activity.save-relative-scenes`

- **风险**：🟡 可逆写
- **说明**：全量覆盖式保存（未传的旧场景会被移除）；保存前先查当前场景做合并确认。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| activityId | String | ✅ | 活动业务 ID |
| scenes | Array | ✅ | 场景列表（至少存在，可为空数组=清空） |
| scenes[].sceneType | String | ✅ | mini_program_page / push / banner |
| scenes[].sceneValue | String | ✅ | 场景值（页面路径/推送 ID 等） |
| scenes[].sceneName | String | 否 | 场景名称 |

### 出参

- 无 data（成功即已保存）。

### 调用示例

```json
{"capability":"ops.marketing.interactive-activity.save-relative-scenes","input":{"activityId":"1942000000000000001","scenes":[{"sceneType":"mini_program_page","sceneValue":"/pages/index/index","sceneName":"小程序首页"}]},"summary":"把活动挂载到小程序首页场景"}
```

---
