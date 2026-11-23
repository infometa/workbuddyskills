---
name: cz-saas-cli
display_name: 驰在灵枢操作手册
display_name_en: Chizai LingShu Operation Guide
description: 用命令行 cz-saas 操作驰在灵枢 SaaS 的基础手册：怎么拿权威工具清单、三级风险（auto / confirm / strict）各该怎么处理、参数怎么传、退出码含义、常见报错的自愈路径、未授权时怎么引导商户重新授权、以及哪些能力刻意不提供。触发词：驰在灵枢、cz-saas、调用工具、工具清单、命令报错、退出码、未授权、重新授权、权限不足、SCOPE_DENIED、IDENTITY_NOT_FOUND、能做什么、做什么、做不到什么。
description_zh: 驰在灵枢 SaaS 所有能力的调用底座。讲怎么查工具、怎么传参、三级风险档怎么处理、报错怎么自愈、授权失效怎么办。
description_en: The base manual for operating Chizai LingShu via the cz-saas CLI — tool discovery, parameter passing, risk tiers, exit codes, and error recovery.
examples_zh:
  - "你能帮我做什么"
  - "这个命令报错了，帮我看看"
  - "提示未授权，怎么重新连接"
  - "列出所有能用的工具"
examples_en:
  - "What can you do for me?"
  - "This command failed — help me debug it"
  - "It says unauthorized, how do I reconnect?"
version: 1.0.0
author: "驰在科技"
---

# 驰在灵枢操作手册

商户的 AI 助手通过本技能操作驰在灵枢 SaaS。所有能力由本地 CLI `cz-saas` 提供。
本文件讲**怎么用**，不重复列工具清单 —— 清单只有一个来源，就是 CLI 自己。

**先看你在哪件事上**：页面装修 → `cz-saas-page-makeover`；导航配置 → `cz-saas-navigation-config`；
门店与继承 → `cz-saas-store-decoration`；内容能不能被 AI 答出 → `cz-saas-content-ai-readable`；
发布与撤回 → `cz-saas-publish-safety`。本文件是它们共用的底座。

---

## 一、开工前：先拿权威清单，不要凭记忆猜工具名

```bash
cz-saas tools --json      # 机器可读：name / title / description / risk / inputSchema
cz-saas tools             # 人类可读分组清单（共 42 个：只读 21 / 写草稿 12 / 对外生效 9）
```

> Windows 下命令名带 `.cmd`（`cz-saas.cmd`）。若报 command not found，先试 `.cmd` 版本。

`inputSchema` 是**契约本身**，不是文档。工具名、参数名、枚举值一律以它为准。
猜一个名字的代价是一次失败往返，还可能是错的业务动作。

## 二、调用语法

```bash
cz-saas call <tool> [--参数名 值 ...] [--json '{...}'] [--confirm]
```

- 参数用 `--参数名 值`，CLI 按 `inputSchema` 自动把字符串转成声明类型（数字 / 布尔 / 数组）。
  数组用英文逗号分隔，例如 `--types MP_NAVIGATION,USER_CENTER_MENU`。
- 参数多或含嵌套对象时改用 `--json`，整段入参：`--json '{"pageId":"123","blocks":[...]}'`。
- **ID 一律当字符串传**（雪花 ID 19 位，转 Number 会丢精度）。
- stdout 顺序固定：`[已完成] 标题` → 撤销/复核指引 → 警告 → 最后才是业务 JSON。
  **别只看最后那段 JSON** —— 「发布前必须处理的警告」在中间那几行。
- stderr 只出诊断（`[CODE] message` + 期望 + 下一步）。脚本化时判 `$?`。

### 退出码

| 码 | 含义 | 该怎么办 |
| --- | --- | --- |
| 0 | 成功 | 读 stdout 的 JSON |
| 1 | 业务或网络失败 | 看 stderr 的 `[CODE]` + `下一步` |
| 2 | 用法错 / 工具名不存在 | 按提示的近似候选改正，或重跑 `tools --json` |
| 3 | strict 动作缺 `--confirm` | **不是错误**。把后果讲给商户，同意后再加 `--confirm` |

## 三、三级风险：这是最重要的一段

**`auto`（21 个，只读）** —— 直接跑。列举、详情、聚合统计都属这档，不改变任何状态。
放心多查，不要凭印象作答。

**`confirm`（12 个，写草稿）** —— 直接跑，但**必须告诉商户「这还只是草稿」**。
草稿不对外生效，改错了随时能改，所以不需要事先征求同意；但绝不能让商户误以为已经上线。
典型：`decoration_add_block`、`decoration_update_block`、`campaign_save`、`coupon_save`。

**`strict`（9 个，对外生效 / 花算力）** —— **先问，再执行**。
不带 `--confirm` 时 CLI 打印具体后果（`PREVIEW`）并以退出码 3 结束。正确流程：

1. 跑一次不带 `--confirm`，读它打印的后果；
2. 用商户能听懂的话复述 —— 说「顾客马上会看到什么」「能不能撤回」；
3. 得到明确同意后，**原命令加 `--confirm`** 重跑。

**不要为了省事直接加 `--confirm`。**

## 四、开工前先确认授权状态

```bash
cz-saas auth status     # 以 "Logged in" 开头 = 已授权；"Not logged in" / "Session expired" = 需要重连
cz-saas doctor          # 一次跑完：凭据 → 令牌 → 权限 → 契约版本
```

`auth status` 非 0 退出 = 需要商户重新授权。此时**不要反复重试业务命令**，直接告诉商户：

```bash
cz-saas auth login      # 拉起浏览器，商户登录后点「同意」
```

商户看到的是驰在灵枢授权页：选应用、勾选授权范围、选门店，然后同意。
令牌存在本机加密文件里，**不需要商户复制任何密钥**。

**权限不足与未授权是两件事**：报 `FORBIDDEN` / `403` 说明已授权但该应用没拿到对应权限，
需要商户在 B 端提「权限申请」并由平台审核 —— 重跑 `auth login` 无用。

## 五、写操作的四条硬规矩

1. **先查后写。** 改之前先读。`decoration_get_page` 拿 `identities`，组件级操作用 `identity` 不用 `index`。
2. **只传要改的字段。** `decoration_update_page` 传整棵树时，**没传的组件等于被删掉**。
3. **发布前把该说的话说完。** 发布是 strict，服务端全量校验，不消耗配额 —— 别怕校验，怕的是没校验就发。
4. **回滚不是万能的。** 详见 `cz-saas-publish-safety`。

## 六、常见报错的自愈路径

| 报错 | 真因 | 怎么修 |
| --- | --- | --- |
| `NEED_REAUTH` | OAuth 令牌过期且无 secret 可换新 | `cz-saas auth login` |
| `401` / `Not logged in` | 没有凭据或凭据失效 | 同上；或 `auth status` 看原因 |
| `403 FORBIDDEN` | 应用没拿到该 scope | B 端提权限申请 → 审核 → `auth login` |
| `SCOPE_DENIED` | 授权时商户没勾这一项 | 重新 `auth login` 补勾 |
| `IDENTITY_NOT_FOUND` | identity 自编或已失效 | 重新 `decoration_get_page` |
| `VALIDATION_FAILED` | 内容门禁拦下 | stderr 会逐条列出哪个组件哪一项 |
| `429` | 触发限流 | 等一分钟，或合并请求 |
| `500` 且提到 `@DataScope` | 服务端 SQL 越权防护 | 不是商户能修的问题，如实上报，别重试 |

## 七、能力边界：这 6 类事做不到

`cz-saas doctor` 会打印「不提供」清单。涉及这些请求要**明确说做不到并给替代路径**，
不要含糊承诺，也不要自己拼一个近似的坏实现：

1. **删除页面 / 订单退款 / 改价 / 发放积分 / 直接发券给顾客 / 读顾客手机号** —— 涉及资金与个人信息，不开放。
2. **绕过发布直接改线上** —— 装修只有「改草稿 → 发布」一条路。
3. **跨商户操作** —— 令牌绑定单一商户，换商户要重新授权。

## 八、回答商户时的口径

- 报数字必带来源工具与时间口径（例：「本周」以 `insight_order_stats` 的 `startDate/endDate` 为准），
  **不要把两次不同区间的结果混着说**。
- 只读工具查不到的，就说「这次没查到」并给下一步（换关键词 / 缩短区间 / 去哪个页面看），
  **不要用常识补一个像样的数字**。商户拿这个做决策。
- 金额字段单位是**分**。`avgOrderAmountFen` 是「分/单」，展示成元要 ÷ 100 —— 漏掉这一步数字会放大 100 倍。
- 做完写操作，回一句「已存草稿，还没上线，需要发布告诉我」——比「已完成」有用得多。
