---
name: tencent-qidian-cs-skill
description: 腾讯企点客服（Tencent-Qidian-CS）Connector 的底层调用说明书。覆盖五大能力域——工单管理（新建/修改/查询工单，变更工单状态）、坐席查询（客服状态实时监控、会话监控、员工信息获取）、人工/机器人会话与消息记录查询（人工/大模型机器人/文本机器人会话和消息记录查询）、客服数据报表（满意度/时长/响应度分析、客服数据总览）。定义全部 MCP 工具的用途、参数、返回值、权限位映射、openId 与 cust_id 解析规则、时间戳规范、计数统计规范、分页完整性规范及调用链路。**只要会话涉及企点客服的工单、坐席、客户、人工/机器人会话记录或客服报表的查询/操作，无论用户是否点名"企点"或具体接口名，都加载本技能**——"看下今天工单情况""谁在线""客服在线情况""拉一下昨天的会话""客服满意度""帮我建个工单"这类需求都属于此范畴。
version: "7.3.0"
author: "Tencent-Qidian-CS"
---

# 腾讯企点客服（Tencent-Qidian-CS）Skill（五大能力域调用说明书）

本 Skill 是**腾讯企点客服**（产品代号 **Tencent-Qidian-CS**）Connector 的**底层调用说明书**，描述全部 MCP Tool 的用途、参数、**返回值**、权限位映射和调用链路。覆盖五大能力域：

- **工单管理**（新建/修改/查询工单，变更工单状态）—— `list_templates` / `list_tickets` / `get_ticket` / `list_statuses` / `create_ticket` / `update_ticket` / `assign_ticket`
- **坐席查询**（客服状态实时监控、会话监控、员工信息获取）—— `list_all_staff` / `get_staff_info` / `get_staff_openid` / `get_staff_monitor` / `get_message_alerts`
- **人工/机器人会话与消息记录查询**（人工/大模型机器人/文本机器人会话和消息记录查询）—— `get_monitored_sessions` / `get_staff_messages` / `list_robot_sessions` / `get_robot_messages` / `list_robots`（辅助查客户资料：`search_user` / `get_user` / `list_customers`）
- **客服数据报表**（满意度/时长/响应度分析、客服数据总览）—— `get_quality_report` / `get_service_report` / `get_staff_duration` / `get_staff_funnel`

落地调用接口时，按本说明书选择工具、组织参数、安排调用顺序、解析返回值。

---

## 欢迎语（首次与用户交互时主动使用）

用户首次提出企点相关请求时，先用类似下面的话开场（可口语化，但**敏感数据提示必须保留**——它关系到客户隐私和合规）：

> 你好，我是**腾讯企点客服**（Tencent-Qidian-CS）连接器助手，可以帮你处理工单、坐席、客户、会话记录、机器人记录和客服报表相关的查询与操作。
>
> ⚠️ 温馨提示：本连接器会访问**客户资料、聊天原文，以及企业全体员工**的工单与会话数据（数据范围覆盖全员，与你登录的账号无关）。我只在完成你需求所必需的范围内调取数据，也请你注意保护客户与同事的隐私，避免不必要的导出或外传。
>
> 需要我从哪里开始？

---

## 认证

### 基本说明

- 用户须先完成 **OAuth 授权**方可使用；任何业务调用前确认 MCP Server 已连接。
- "当前登录人自己"的 openId 由 **MCP Server 注入**；任何接口参数表中标为 `operator` 的，都是当前登录人 openId，由服务端注入——**不要手工填写，更不要让别人冒充自己**。

### Token 过期的识别与处理

- **过期信号**（任一即认为 Token 失效，立即停止业务调用、转走"重新授权"流程）：
  - HTTP 401 Unauthorized
  - 返回体中出现 `errcode=40001` / `40014` / `access_token expired` / `invalid_token` 等关键词
  - MCP Server 透传错误信息提及 "token expired" / "重新授权"
- **处理话术**（直接用，不要再向用户解释 token 是什么）：
  > 检测到企点登录已过期，请到连接器设置页找到 "腾讯企点客服 / Tencent-qidian-cs"，点击重新授权后再继续操作。
- **不要做的事**：
  - 不要在 token 失效时反复重试调用（每次都会 401，浪费 Token quota）
  - 不要尝试自行刷新 token（MCP Server 已负责，AI 没有刷新工具）

---

## 权限管控（由 MCP Server 错误码驱动）

权限校验在 **MCP Server 侧**完成。**不要尝试预先读取员工权限**——本 Connector 没有提供"查权限"工具，正常发起调用即可，再根据 MCP Server 返回的错误码处理：

- **完全无权限**（未勾选任何 AI 连接器权限位）：返回对应错误码时，回复——
  > 查询到权限不足，请联系管理员到企点客服账户中心（https://admin.qidian.qq.com/）中【企业管理】-【权限角色】-【AI连接器】模块中添加权限。（仅在线客服专业版、企业版套餐的企业可使用）

- **部分权限**（已开通某些权限位，但用户的需求落在未开通的位上）：回复——
  > 检测到缺少 **{缺失权限位名称}** 权限，无法执行最终操作。请联系管理员到企点客服账户中心（https://admin.qidian.qq.com/）中【企业管理】-【权限角色】-【AI连接器】模块中添加权限。（仅在线客服专业版、企业版套餐的企业可使用）

  `{缺失权限位名称}` 替换为下方映射表中对应的名称。

- **其他错误**：见《常见错误码速查表》。**不要编造结果或绕过**——伪造数据会让用户基于错误信息做决策。

### ⚠️ 数据范围（务必知悉）

当前所有接口覆盖企业**全体员工**数据，与登录账号无关：可以拉到所有员工的工单、所有坐席的会话。因此：

- 默认查询返回**全公司**数据；用户想看"我的 / 某人的"，要用 `ownerId` / `staffId` 等参数显式过滤。
- 涉及他人数据时审慎，不要超出用户需求去导出或展示。

---

## 常见错误码速查表

| 错误现象 | 可能原因 | 处理方式 |
|---------|---------|---------|
| HTTP 401 / `errcode=40001` / `invalid_token` | Token 失效或过期 | 走《认证 → Token 过期处理话术》引导用户重新授权，**不重试** |
| HTTP 403 / `permission denied` / `权限不足` | 该权限位未开通 | 走《权限管控》提示话术，按映射表填入缺失权限位名称 |
| HTTP 400 / `param invalid` / `参数错误` | 必填参数缺失 / 格式错 / 大整数被截断 | 检查是否漏传必填项；ID 字段是否字符串透传；时间格式是否 `YYYY-MM-DD`/微秒时间戳 |
| `工单不存在` / `模板不存在` / 末几位为 0 的 ID 报"找不到" | **大整数 ID 精度丢失**（被当 number 处理） | 用字符串保留原值重发；走《其他坑》大整数 ID 规则 |
| HTTP 429 / `rate limit` / `too many requests` | 限流 | 告知用户当前接口被限流，停止该轮批量操作，建议稍后或拆小批次再试 |
| HTTP 5xx / `server error` | 服务端异常 | **最多重试一次**；仍失败则如实告知用户，不要无限重试 |
| 客户姓名查询超时 / `timeout` | 客户库太大按名匹配慢 | 走《cust_id 解析规则》引导用户直接提供 cust_id |
| `next_page_token` 为空或缺失 | 已到末页 | 停止翻页 |
| 时间范围错误（结束 ≤ 开始） | 用户口误或跨天 | **不要自行推断**，向用户确认是否跨天或笔误 |

---

## openId 与 cust_id 解析规则（高频场景，常被用户隐式触发）

接口里大量参数（`ownerId` / `staffId` / `cuin`）需要的是系统 ID，但用户口头通常给的是姓名、社交账号、account 等。按下面规则解析；解析失败时**先澄清，不要猜**。

### 员工 openId 怎么拿

| 用户给的是… | 解析路径 |
|---|---|
| "我自己" / "我处理的" / `operator` | MCP Server 注入，无需 AI 查找 |
| 具名姓名（如 "张三"） | 调 `list_all_staff` 拿员工 openId 列表 → 对候选调 `get_staff_info` 取姓名 → 按姓名匹配 |
| account（组织架构里的英文工号，如 `anncui`） | 调 `get_staff_openid`，一步把 account 转 openId |
| 姓名匹配失败或员工太多导致很慢 | 引导用户提供 account："你能在企点【组织架构】里找到这位同事的 account（一串英文）发我吗？" 然后走 account 路径 |

为什么有 account 这条捷径：`list_all_staff` 只返回 openId 不返回姓名，要拿姓名得逐个调 `get_staff_info`，员工多时会很慢；让用户直接提供 account 是一次调用就搞定。

#### ⚠️ 反向：openId → 姓名的展示规范（强制）

**当查询结果中出现"处理人 / 受理人 / 坐席 / 创建人 / owner / staff / user / operator"等带 openId 的字段时，向用户展示时不能只输出原始 openId**——openId 是冷冰冰的字符串（如 `ouxxxxxxxxxxxxxxxxx`），用户看不出是谁。**必须自动调 `get_staff_info` 解析为姓名**，按 `openid（姓名）` 格式输出。

**强制流程**：

1. **批量收集**：扫描即将展示给用户的数据，收集所有 openId 值（去重），统一传入 `get_staff_info` 的 `openids` 数组一次性查询，避免 N+1 调用。
2. **构建映射表**：从返回值中得到 `{openid → name}` 的映射缓存（同一轮对话内可复用，下次再遇到相同 openId 直接查映射表，不重复调）。
3. **格式化展示**：在所有用户可见的输出中，把 openId 字段渲染为 `ouxxxxxx（张三）` 的形式。
   - 表格中：单独一列展示，或合并为"处理人"列内显示 `张三（ouxxxxxx）` 也可。
   - 自然语言：『工单 W-001 当前的处理人是 **张三**（openId: ouxxxxxx）』。
4. **解析失败兜底**：`get_staff_info` 返回为空（员工已离职/不存在）时，按 `ouxxxxxx（未找到员工）` 显示，不要让 openId 裸奔。
5. **本人识别**：如果 openId 等于"当前登录人 openId"（由 MCP Server 注入到 operator 的那个），可以显示为 `ouxxxxxx（我自己 / Ann）`，更友好。

**适用接口**：

| 接口 | 含 openId 的返回字段 |
|------|---------------------|
| `list_tickets` | `data[].ownerId`、`data[].createrId` |
| `get_ticket` | `data.ownerId`、`data.createrId`、`data.flowLogs[].operatorId` |
| `get_monitored_sessions` | `data[].staffId` |
| `get_staff_messages` | `data[].fromType` 内的坐席 |
| `get_staff_monitor` | `data.staffList[].openid` |
| 报表族（quality/service/duration/funnel） | `data.list[].userUin` |
| `get_robot_messages` | 转人工时的坐席 openId |

**反例（禁止）**：
- ❌ 『当前处理人 ID：ouAbCdEf123456』
- ❌ 『此工单由 ouxxxxxxx 处理』

**正例**：
- ✅ 『当前处理人：**张三**（ouAbCdEf123456）』
- ✅ 『此工单由 **张三**（ouxxxxxxx）处理』

### 客户 cust_id 怎么拿

| 用户给的是… | 解析路径 |
|---|---|
| **裸 QQ 号**（如 `379937263`）且未明确说是 cust_id | ⛔ **直接告知不支持**——见下方《⚠️ QQ 号查客户的强制规则》 |
| 社交账号（微信/电话/企微等，**QQ 除外**） | 调 `search_user` 反查 cust_id → 调 `get_user` 取详细资料 |
| 客户姓名 | 调 `list_customers` 翻页 + 对候选调 `get_user` 按姓名匹配 |
| cust_id 本身 | 直接 `get_user` |
| 手机号 | 调 `search_user`（type=22）反查 cust_id → 调 `get_user` |

#### ⚠️ QQ 号查客户的强制规则（不可绕过）

**当用户提供的输入是一串纯数字（5-12 位）、且语境是"查这个客户"而**没有**明确说"这是 cust_id"时，默认按 QQ 号处理**：本系统**不支持**用 QQ 号反查客户资料（业务限制，非接口能力问题）。

**强制响应模板**（直接用，不要尝试调 `search_user`）：

> 抱歉，目前不支持直接用 QQ 号（如 `{用户给的数字}`）查询客户资料。请提供以下任一信息：
> - **客户 ID（cust_id）**：在企点账户中心的【客户库】列表里能复制到
> - **手机号**：我会用手机号反查
> 你方便提供哪个？

**判别细则**：
- 5-12 位纯数字 + 上下文"查客户/客户信息" → **按 QQ 号拦截**，按上述话术回复，不要调 `search_user`
- 用户**明确**说"cust_id 是 379937263"或类似 → 按 cust_id 直接 `get_user`
- 数字 + "手机号是 13xxxxxxxxx" 等明示 → 走手机号路径（`search_user` type=22）
- 微信/小程序等其他社交账号 → 正常走 `search_user`（按通路类型选 type）

**为什么有这条规则**：实际业务中 QQ 号反查 cust_id 的成功率与匹配语义都不稳定，强行调用会拿到错的客户或空结果，进而误导后续 `get_user` / 工单创建。统一拦截在解析层更安全。

#### 客户库翻页慢的兜底

**客户库通常很大，按姓名匹配容易超时或报错。** 一旦发现查询时间过长、或接口返回错误，**立即停止重试**，引导用户：

> 客户库太大了，按姓名查找比较慢。麻烦你到企点账户中心的【客户库】列表里找到这位客户，复制 cust_id 发给我，我直接查就行。

拿到 cust_id 后走 `get_user` 即可。

---

## 通用约定

### 时间范围处理（⚠️ 强制规范，过往踩坑频次最高）

> **历史教训**：模型对"最近 30 天 / 本周 / 最近一周"等相对时间的换算，曾多次因**凭直觉拼时间戳**导致结果完全错误（例如把 2026 年 5 月查成了 2025 年 1 月）。本节规则强制执行，**违反任何一条都视为重大事故**。

#### 规则 A：当下时间 = 系统当下，**不能凭记忆/训练数据**

- 任何涉及"今天 / 现在 / 最近 X 天 / 本周 / 本月"的计算，**第一步必须**用 Bash 取真实当前时间：
  ```bash
  date "+%Y-%m-%d %H:%M:%S %Z"        # 人类可读
  date +%s                              # 秒级时间戳
  date +%s%6N                           # 微秒级时间戳（用于 ref_time 等）
  ```
- **禁止**根据训练截止日期、对话上下文推断"今天是 X 月 X 日"。模型的内部时间认知通常滞后真实时间数月到数年，**这是已知的事故源头**。

#### 规则 B：换算结果**必须先复述给用户确认**

把相对时间换算为绝对时间后，**先告诉用户具体日期范围**，等用户确认或修正，再带入接口参数。模板：

> 我换算的时间范围是：**{开始日期} ~ {结束日期}**（{相对说法}，共 {N} 天），对吗？

例如用户说"最近 30 天"，且 `date` 返回 `2026-05-27`，必须先回复：

> 我换算的时间范围是：**2026-04-28 ~ 2026-05-27**（最近 30 天，含今天，共 30 天），对吗？

确认后再继续。

#### 规则 C：时间戳单位**必须与接口匹配**

| 接口字段 | 单位 | 示例值（2026-05-27 00:00:00 +0800） |
|---------|-----|------|
| `list_tickets.startTime` / `endTime` | **毫秒**时间戳 | `1779638400000` |
| 报表族 `startTime[]`、会话记录 `startTime[]` | **秒**时间戳 | `1779638400` |
| 机器人会话 `StartTime[]` | **秒**时间戳 | `1779638400` |
| `get_staff_messages.ref_time` / `get_robot_messages.ref_time` | **微秒**时间戳（**string 透传**） | `1779638400000000` |

- 写入参数前**必须用 Bash 重新算一次**对应单位的时间戳，不要直接 ×1000 / ÷1000 拍脑袋。例如：
  ```bash
  date -j -f "%Y-%m-%d %H:%M:%S" "2026-04-28 00:00:00" +%s    # macOS BSD date
  # 输出 1777593600（秒）→ 毫秒需要 ×1000 = 1777593600000
  ```

#### 规则 D：相对时间的换算约定（团队内部统一）

| 相对说法 | 换算（基于"今天" T） | 备注 |
|---------|--------------------|------|
| "今天" | T 00:00:00 ~ T 23:59:59 | |
| "昨天" | T-1 00:00:00 ~ T-1 23:59:59 | |
| "最近 N 天" | T-(N-1) 00:00:00 ~ T 23:59:59 | **含今天**共 N 天 |
| "最近一周" / "最近 7 天" | T-6 00:00:00 ~ T 23:59:59 | 含今天共 7 天 |
| "本周" | 本周一 00:00:00 ~ 本周日 23:59:59 | 周一为周首 |
| "上周" | 上周一 00:00:00 ~ 上周日 23:59:59 | |
| "本月" | 当月 1 日 00:00:00 ~ 当月最后一天 23:59:59 | |
| "上月" | 上月 1 日 00:00:00 ~ 上月最后一天 23:59:59 | |
| "最近 30 天" | T-29 00:00:00 ~ T 23:59:59 | 含今天共 30 天 |

#### 规则 E：常规说明

- 报表、会话记录等接口需要起止时间。**用户没给明确的起止时间时，先追问**——即便用户给了相对时间，也要走规则 B 复述确认。
- 时区按企点后台所在地（**Asia/Shanghai / UTC+8**）理解；Bash `date` 命令默认就是本地时区，与企点一致。
- **时间逻辑校验**：若用户提供的结束时间 ≤ 开始时间（如"4 点到 3 点"），向用户确认是否跨天或笔误后再执行。
- **禁止行为汇总**：① 不查 Bash 直接给出"今天是 X 年 X 月 X 日"；② 不复述确认就直接把换算后的时间戳塞进工具参数；③ 不验证单位（秒/毫秒/微秒）就传值；④ 接口返回为空时不要立刻断言"无数据"——优先怀疑时间戳算错，重走规则 A→B→C。

### 分页与大批量操作

各接口分页约定不统一（见下表），调用前看清：

| 约定 | 起始 | 用在哪些接口 |
|---|---|---|
| `page` / `size` | 0 起 | 模板、状态、员工等 |
| `pageNo` / `pageSize` | 1 起 | 工单列表 |
| `count` / `index` | 1 起 | 会话记录 |
| `next_custid` 游标 | — | 客户列表 |
| `ref_time` 微秒时间戳 | — | 消息记录 |

**大批量拉取或写入前，先告知规模并取得用户同意**——例如"拉最近 30 天全部会话"可能跨很多页和很大数据量；批量建单可能一次创建几十张。先说"我预计要拉 N 页 / 创建 N 张工单，确认要继续吗？"再行动。

### 分页完整性强制规则（⚠️ 已知踩坑：只看第一页就下结论）

> **历史教训**：用户问"现在哪些客服在线"，模型调用 `get_staff_monitor`（默认每页 48 条）只看第一页就汇报"在线坐席共 3 人：钟意 sally、TestReply、smarthuang"。但实际企业有 68 个坐席分两页，第二页里还有 polite 在线（status=1），结果**漏报了一个在线坐席**。这种"分页未拉满就下结论"是和"计数错误"同源的懒人陷阱。

#### 规则 A：判断"是否需要翻完所有页"

| 场景 | 必须翻完所有页 | 可以只看第一页 |
|------|:------------:|:------------:|
| 用户问"全部 / 所有 / 一共多少 / 完整列表" | ✅ | |
| 用户问"现在谁在线 / 在线情况"（**全量筛选类**） | ✅（要从全量里筛出在线） | |
| 用户问"按某条件筛选"（如"在线的客服" / "未解决的工单"） | ✅（筛选必须基于全集） | |
| 用户问"看看大概情况 / 抽几个看看 / 前几条" | | ✅ |
| 用户已明确给出"第 N 页 / 前 N 条"的范围 | | ✅（按用户指定范围） |
| 用户问"汇总统计 / 总数"（且接口返回了 total 字段） | | ✅（直接用 total，不用拉全量明细） |

#### 规则 B：拉完所有页的标准流程

1. **第一页拉取**：调接口拿到第一页数据 + 总数（`total` / `count` / `maxLimitTotal`）。
2. **判断是否还有下一页**：
   - 若 `已拉条数 < total` → 继续拉下一页（自增 index 或 page）
   - 若 `data.next_page_token` / `next_custid` 非空 → 用游标拉下一页
   - 若用户明确说"够了 / 别拉太多"→ 停止并告知已拉条数 / 总数比例
3. **告知翻页规模**：若 total 较大（≥ 3 页或 ≥ 200 条），**先停下来告诉用户**：『总共 N 页 / N 条，预计要拉完才能给你完整答案，确认继续吗？』取得同意再翻。
4. **数据合并**：所有页数据合并到一个数组，**用 Bash/Python 程序化合并和筛选**，不要靠 LLM 拼接（会丢数据）：
   ```bash
   # 拉到的多页数据存成 page1.json / page2.json / ...
   python3 -c "import json,glob; all_data=[]; \
     [all_data.extend(json.load(open(f))['data']) for f in sorted(glob.glob('/tmp/page*.json'))]; \
     print(json.dumps(all_data, ensure_ascii=False))" > /tmp/all.json
   # 再做筛选/统计
   python3 -c "import json; d=json.load(open('/tmp/all.json')); \
     online=[x for x in d if x['status']==1]; print(len(online), [x['name'] for x in online])"
   ```

#### 规则 C：声明数据范围

**汇报结果时必须说明本次数据覆盖了多少**——让用户清楚地知道是"全量"还是"部分"：

✅ 正例：『**已拉取全部 68 个坐席**（共 2 页），其中在线 4 人：钟意 sally、TestReply、smarthuang、polite。』
✅ 正例：『当前只看了第一页（前 48 个坐席），如果需要看全部 68 个坐席的在线情况，我再拉一页。』
❌ 反例：『**在线坐席共 3 人**：钟意 sally、TestReply、smarthuang。』（隐藏了"只看了第一页"的事实）

#### 规则 D：常见易错点

- **`get_staff_monitor` 默认 count=48**：企业坐席多于 48 时必翻页。看用户问的是"全公司客服在线情况"还是"少数几个的接待情况"决定是否翻完。
- **`list_tickets` 默认 pageSize=15 或 20**：用户问"我所有的待处理工单"等"全集筛选"时必须翻到 `total` 满。
- **`list_all_staff` 一次最多 500**：超 500 必翻页；用户问"全公司多少员工"先看 total。
- **`list_customers` 游标分页**：`next_custid` 非空就还有下一页，直到为空才到末页。
- **`get_monitored_sessions` 30 天会话量**：按预估告知用户大概多少页，确认后再批量翻。
- **`list_robot_sessions`**：同上，机器人会话量大时必先报规模。

#### 规则 E：与"计数规范"的关系

分页完整性 + 计数程序化是配套的：**先翻完所有页拿到全集**（规则 B）→ **再用程序化方式数全集**（计数规范规则 A）。不要先拉一页数完就报数，否则数到的不是真实总量。

### 数据计数与统计规范（⚠️ 强制，过往踩坑频次第二高）

> **历史教训**：模型在汇总返回的 JSON 数组时，曾凭"目测/复述时数"得出错误数量（例如返回 12 个工单模板却汇报"共 11 个"，比对详情列表才发现少数了一个）。这种"靠直觉数数"是 LLM 已知短板，必须用程序化方式兜底。

#### 规则 A：用程序化方式数，**不要用眼睛数**

任何"共 N 条 / 总计 N 个 / 一共 N 张"的输出**必须满足以下任一条件**：

1. **优先取接口返回的 `total` / `count` / `maxLimitTotal` 字段**——这是服务端给出的权威计数，比模型自己数准。
2. 若返回结构没有 total 字段、必须从数组算长度时，**用 Bash/Python 计算**：
   ```bash
   echo '<JSON 字符串>' | python3 -c "import sys,json;print(len(json.load(sys.stdin)['data']))"
   # 或者保存到临时文件后
   python3 -c "import json;d=json.load(open('/tmp/r.json'));print(len(d['data']))"
   ```
3. 数组很短（≤ 5 条）且需要逐条展示时，先**编号列出每一项**，再以列表的最后一个编号作为总数（如 "12 项 → 编号 1 至 12 → 总数 12"）。

#### 规则 B：列表数 ≠ 概括数 时，**立即停止并重算**

输出格式如果同时包含两个数字（例如开头说"共 N 条"，下面又详细列了 M 条），**N 必须等于 M**。出现差值时：

1. 立即停止当前回复，**不要硬着头皮往下写**。
2. 用规则 A 的方式重新核对总数。
3. 修正后再发给用户。

#### 规则 C：用户反馈"数错了"时，**先承认再程序化重算**

如果用户指出"你说 N 个但列了 M 个"：

1. **直接承认**："你说得对，确实数错了。"——不要找借口。
2. 走规则 A 重新数（优先 total，其次 Bash 计算），不要再用眼睛数第二次。
3. 给出**经程序化验证**的最终数字。

#### 规则 D：常见易错点

- **JSON 数组中含 `null` 或重复对象**：肉眼扫容易跳过 → 必须用 `len()`。
- **多页返回时**：单次响应的 `data.length` ≠ 总数。要看 `total` / `next_page_token` 是否还有下一页。
- **嵌套数组**：例如 `data[].messages[]`，要明确"数的是哪一层"——是会话数还是消息数。
- **空数组 ≠ 0 条记录**：先确认请求成功（HTTP 200 + code=0）再确认 length=0。如果是 401/403 不要把它说成"0 条数据"。
- **分组聚合时**：例如"统计每个客服多少工单"，按 `ownerId` 分组的 dict 长度才是客服数，不是工单总数。

#### 规则 E：表达模板

数完之后输出格式建议：

> 共 **{N}** 条记录（来源：接口 `total` 字段 / 程序化计算）。

或者：

> 共 **{N}** 条记录（已逐条编号 1~{N}，与详情列表对齐）。

写明"来源"既能让用户知道你确实算过，也方便事后追溯。

### 会话 / 消息记录拉取的通路默认值规则（⚠️ 强制）

> **历史教训**：用户说"拉一下昨天的会话""看看那个客户的聊天记录"时通常没指定具体通路（QQ / 微信公众号 / 微信小程序 / 企微 / 微信客服 / webim / 电话 / APP 等）。模型若擅自只传一个默认通路（比如只传 type=0 或只传企微），会**漏掉其他通路上的会话**，结果给用户的是不完整的数据，误导分析。

#### 规则 A：用户没指定通路 → 默认拉所有通路

**触发场景**：用户说"拉聊天记录 / 看看会话 / 翻一下消息记录 / 这个客户最近聊了什么 / 这个机器人的对话"等，**没有任何"通过 QQ / 微信 / 企微 / 微信客服 / 公众号"等通路限定词**时：

- ✅ **默认行为**：通路参数（`subType` / `通路 type` / `Cid 类型` 等）**不传 / 传"全部 / 0 / 空"**，让接口返回所有通路的会话与消息。
- ❌ **禁止行为**：不要凭印象认定"应该是 QQ / 应该是企微"就只传一个通路；也不要先猜一个通路调一次拿到空再换一个通路。

#### 规则 B：拉回数据后按通路分组展示

为了让用户看清各通路的分布，**汇总时建议按通路分组统计**：

```
最近 7 天会话共 N 条：
- 微信公众号：X 条
- 企微：Y 条
- 微信小程序：Z 条
- 电话：M 条
- ...
```

让用户一眼看出哪些通路有会话、哪些通路是空的。

#### 规则 C：用户明确指定通路时严格按指定的来

用户**明确说**"只看微信的聊天 / 只看企微会话 / 只查 QQ 会话"等含通路限定的语句时，按指定通路的 type 值严格传入，不要扩大范围。

#### 规则 D：适用接口

| 接口 | 通路参数字段 | 默认行为 |
|------|------------|---------|
| `get_monitored_sessions` | 入参 `subType` / 筛选条件 | 不指定 → 拉全部通路的人工会话 |
| `get_staff_messages` | 由所属 sessionId 决定（继承会话通路） | 上一步 get_monitored_sessions 已拉全通路时，自动继承 |
| `list_robot_sessions` | 入参 `Cid 类型` 等筛选条件 | 不指定 → 拉全部通路的机器人会话 |
| `get_robot_messages` | 由所属 SessionID 决定 | 同上 |

#### 规则 E：与"分页完整性"配合

通路全拉 + 分页全翻是组合规则：先确保所有通路都覆盖（规则 A），再确保每个通路所有页都拉完（《分页完整性强制规则》），最后程序化合并 + 计数（《数据计数与统计规范》）。

> **典型反例**（禁止）：用户说"拉一下张三这周的客户会话"，AI **只调了** `get_monitored_sessions(staffId=ouXXX, subType=51 企微)`，结果只返回了企微通路的会话，漏掉了客户在微信公众号、QQ、电话等通路上和张三的对话。

> **正例**：同样的请求，AI **不传 subType**（或传"全部"），拿到所有通路的全集后按通路分组展示，让用户看到完整图景。

### 大整数 ID 字段处理（关键）

- **所有大整数 ID 字段一律以 string 传递**——`templateId` / `workorderId` / `customerId` / `statusId` / `robotId` / `ref_time` 等服务端定义为 long 的字段普遍超过 16 位（最长可达 19 位），而 **JavaScript Number 安全位数仅 15-16 位**（`Number.MAX_SAFE_INTEGER` ≈ 9×10¹⁵），按数字处理会精度丢失（末几位变 0 或漂移），导致接口报"工单不存在 / 模板不存在"等诡异错误。
- 即便文档标注为 long/integer，AI 也**必须用字符串保留原值透传**，不要做任何数值转换、计算或重新格式化。
- 从工具返回的 JSON 里拿到的 ID 字段也按字符串看待，复述给用户或传给下一跳工具时**原样透传**。

### 敏感数据

本连接器涉及客户 PII（姓名、电话、社交账号）、聊天原文、全员工单与会话数据。**仅在用户需求所必需的范围内**调取与展示，避免不必要的批量导出或转述。首次交互务必给出《欢迎语》中的敏感数据提示。

### 其他

- `list_customers` 的 `access_token` 由 MCP Server 处理，**不是**需要 AI 填写的参数。
- 报表 4 接口端点已更新到 `employeeSession` 族，**入参以最新文档地址为准**，下方参数表只列必要起止时间。

---

## 权限位 ↔ API 映射

> 共 9 个权限位（7 查询 + 2 编辑），24 个 API。下方均为 AI 连接器权限位。

### 工单管理（工单V2）

**[790] AI查询全部工单**（`ticket-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `list_templates` | 获取工单模板列表 | https://api.qidian.qq.com/wiki/doc/open/eynb5ft8gnsrqv17u05h |
| `list_tickets` | 工单列表查询（条件筛选） | https://api.qidian.qq.com/wiki/doc/open/esa3sklsvw0csvdlo2em |
| `get_ticket` | 工单详情查看 | https://api.qidian.qq.com/wiki/doc/open/ecse8s4sk4n28q0f1mhk |
| `list_statuses` | 获取工单状态列表 | https://api.qidian.qq.com/wiki/doc/open/eqod2tep8hlipt5pk14v |

**[791] AI新建工单**（`ticket-create`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `create_ticket` | 创建工单 | https://api.qidian.qq.com/wiki/doc/open/etczss4dko6p9xfs5g43 |

**[792] AI更新全部工单**（`ticket-update`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `update_ticket` | 工单信息更新（**改处理人 ownerId 用这个**） | https://api.qidian.qq.com/wiki/doc/open/e1ssbs7ou39981cmud5f |
| `assign_ticket` | 工单**状态变更**（名字虽是 assign，实为改状态） | https://api.qidian.qq.com/wiki/doc/open/e5bms5rryls1e37frhk1 |

### 坐席管理

**[793] AI查询全部坐席**（`agent-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `list_all_staff` | 批量拉取员工列表（**仅返回 openId**，要姓名需配合 get_staff_info） | https://api.qidian.qq.com/wiki/doc/open/enq3asm58qd30e5thznk |
| `get_staff_info` | 根据 openId 获取员工信息（含姓名） | https://api.qidian.qq.com/wiki/doc/open/emc2lsrxlpeyogp46h43 |
| `get_staff_openid` | 根据 account（组织架构里的英文工号）批量获取 openId | https://api.qidian.qq.com/wiki/doc/open/e1lvod8ftkgs44hupuu3 |
| `get_staff_monitor` | 客服实时监控数据（坐席级） | https://api.qidian.qq.com/wiki/doc/open/em7p5kar7co0f5htpr45 |

### 客户管理

**[794] AI查询全部客户**（`customer-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `get_user` | 客户资料查询（按 cust_id） | https://api.qidian.qq.com/wiki/doc/open/ebmlne6s3lpzplguht26 |
| `search_user` | 根据社交账号反查 cust_id | https://api.qidian.qq.com/wiki/doc/open/eal6s336lsl1czg5h569 |
| `list_customers` | 拉取客户列表（游标分页；客户多时慎用） | https://api.qidian.qq.com/wiki/doc/open/evblxstplyo4dpgm4ri6 |

### 会话记录

**[795] AI查询全部人工会话记录**（`session-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `get_monitored_sessions` | 人工接待会话记录拉取 | https://api.qidian.qq.com/wiki/doc/open/etlka4esonlgrv374h05 |
| `get_staff_messages` | 人工接待消息记录拉取（逐条聊天） | https://api.qidian.qq.com/wiki/doc/open/ed5e6foshrq8ol7k2ws4 |

**[796] AI查询全部客服会话监控**（`monitor-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `get_message_alerts` | 会话监控实时**大盘**（排队数、在线会话数、满意度等全局指标） | https://api.qidian.qq.com/wiki/doc/open/eamp842brgr7ni45n5s8 |

### 大模型机器人

**[797] AI查询机器人全部会话记录**（`AI-robot-session-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `list_robot_sessions` | 大模型机器人会话记录拉取 | https://api.qidian.qq.com/wiki/doc/open/flrka0xclflks9g9kiu8 |
| `get_robot_messages` | 大模型机器人消息记录拉取（问答对） | https://api.qidian.qq.com/wiki/doc/open/esarx13br5fnv2o0h103 |
| `list_robots` | 大模型机器人列表查询（先调它拿 robotId，再 list_robot_sessions 拉会话） | https://api.qidian.qq.com/wiki/doc/open/flk9laym9sbro1qdqfxi |

### 数据报表（已整体迁到 `employeeSession` 族）

**[798] AI查询全部客服报表**（`report-read`）

| action | 说明 | 文档地址 |
|--------|------|---------|
| `get_quality_report` | 会话客服分析-满意度分析 | https://api.qidian.qq.com/wiki/doc/open/e7btspmcwpxr9rd6ez5t |
| `get_service_report` | 会话客服分析-总览（客服维度） | https://api.qidian.qq.com/wiki/doc/open/evtnbs5pnd007fylwg60 |
| `get_staff_duration` | 会话客服分析-时长分析 | https://api.qidian.qq.com/wiki/doc/open/ezdlretsppwfplqix9m9 |
| `get_staff_funnel` | 会话客服分析-**响应度分析**（名字保留，含义已不是漏斗/转化） | https://api.qidian.qq.com/wiki/doc/open/eutbsc7lp6lf04k2h2ym |

### 权限位速查表

> 后台权限位中文名已统一为「AI + 动词 + 全部 + 对象」格式（如「AI查询全部工单」），强调授权范围是**全公司全员数据**。下表中文名与后台「账户中心 → AI 连接器」权限勾选页一致。

| ID | 权限位中文名（后台一致） | scope（英文 key） | 类型 | API 数量 |
|----|------|-------|------|---------|
| 790 | AI查询全部工单 | `ticket-read` | 查询 | 4 |
| 791 | AI新建工单 | `ticket-create` | 编辑 | 1 |
| 792 | AI更新全部工单 | `ticket-update` | 编辑 | 2 |
| 793 | AI查询全部坐席 | `agent-read` | 查询 | 4 |
| 794 | AI查询全部客户 | `customer-read` | 查询 | 3 |
| 795 | AI查询全部人工会话记录 | `session-read` | 查询 | 2 |
| 796 | AI查询全部客服会话监控 | `monitor-read` | 查询 | 1 |
| 797 | AI查询机器人全部会话记录 | `AI-robot-session-read` | 查询 | 3 |
| 798 | AI查询全部客服报表 | `report-read` | 查询 | 4 |
| — | **合计** | — | — | **24** |

---

## 工具详解

> **通用约定**
> - 参数表中的 `operator`（操作者 openId）已由 MCP Server 注入，下方表格不再重复列出。
> - 返回值仅列**业务关键字段**（用于解析展示或作为下一跳工具入参的字段）；完整字段以官方文档为准。
> - 凡是大整数 ID 字段（templateId / workorderId / customerId / statusId / robotId / cust_id / sessionId / ref_time 等），无论参数还是返回值，**一律按字符串透传**。

### 工单管理

> ### ⚠️ 工单写操作二次确认规则（强制，不可跳过）
>
> 工单的**增 / 改 / 状态变更**（`create_ticket` / `update_ticket` / `assign_ticket`）属于敏感写操作，**每次执行前都必须重新与用户逐项确认**，即便用户在本轮对话或上轮对话里已经提供过 `templateId`、`title`、`ownerId`、`statusId` 等参数。
>
> **必须遵守的流程**：
>
> 1. **完整展示即将提交的参数**——按"字段名：值（含可读名称）"逐项列出，例如：
>    - 模板：`templateId="614404267440304175"`（VIP 客户工单专用模板）
>    - 标题：xxx
>    - 处理人：`ownerId="ouxxxxxx"`（张三）
>    - 优先级：30（中）
> 2. **逐项询问是否使用 / 是否要替换**——尤其是 `templateId`、`ownerId`、`statusId` 这类引用其他对象的 ID 字段，明确问："要用这个模板 / 处理人 / 状态吗？还是换一个？"
> 3. **等待用户明确肯定回复**（"确认"、"是"、"OK"、"对"、"就这样"等）后再执行；用户犹豫、提出疑问或表达否定时，**立即停止**，按用户的最新意见调整后再次走确认流程。
> 4. **不得用"看起来都有了就直接提交"的判断越过确认**——即使所有必填项都已具备，也必须确认。
> 5. **批量场景**（如循环建单）必须先报"预计创建 N 张，第一张参数如下…"取得整体同意，再按批次执行；批次内任一条参数变化都要重新确认。
>
> **典型反例**（禁止）：用户半小时前提过"用 VIP 模板，处理人是张三"，现在又说"再帮我建一张同类的工单，标题叫 xxx"——AI **不能**直接用旧的 templateId/ownerId 调 `create_ticket`，必须先把完整参数列出来问一遍"用这些参数对吗？"

#### list_templates — 获取工单模板列表
查可用工单模板。创建工单前先调用让用户选模板。**权限位**：[790] AI查询全部工单（`ticket-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page | integer | 否 | 页码，0 起，默认 0 |
| size | integer | 否 | 每页条数，默认 15 |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].id` | string | **模板 ID（大整数，作 templateId 传给 create_ticket）** |
| `data[].name` | string | 模板名称（如 "VIP 客户工单"） |
| `data[].fields[]` | array | 该模板的必填/可选字段定义，用于检查 create_ticket 必填项 |

#### list_tickets — 工单列表查询
按条件筛选工单。**权限位**：[790] AI查询全部工单（`ticket-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| pageNo | integer | 否 | 页码，1 起，默认 1 |
| pageSize | integer | 否 | 每页条数，默认 20 |
| statusId | string | 否 | 工单状态 ID（大整数，字符串传递） |
| priorityId | integer | 否 | 优先级（40=低 30=中 20=高 10=紧急） |
| ownerId | string | 否 | 处理人 openId（看"某人/我的"工单时用它过滤） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].workorderId` | string | **工单 ID（大整数，作为 get_ticket / update_ticket / assign_ticket 的入参）** |
| `data[].title` | string | 工单标题 |
| `data[].statusId` | string | 当前状态 ID |
| `data[].priorityId` | integer | 优先级 |
| `data[].ownerId` | string | 处理人 openId |
| `data[].createTime` | string | 创建时间 |
| `total` | integer | 总条数 |

#### get_ticket — 工单详情
**权限位**：[790] AI查询全部工单（`ticket-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| workorderId | string | 是 | 工单 ID（大整数，字符串传递） |

**返回值（关键字段）**：完整工单对象，含 `workorderId` / `templateId` / `statusId` / `title` / `description` / `ownerId` / `customerId` / `priorityId` / `fields[]`（自定义字段值）/ `flowLogs[]`（流转记录）/ `attachments[]`。所有大整数 ID 字段均字符串透传。

#### list_statuses — 获取工单状态列表
变更状态前先用它取目标 statusId。**权限位**：[790] AI查询全部工单（`ticket-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| type | string | 否 | START / NORMAL / END，不填返回全部 |
| pageNumber | integer | 否 | 页码，0 起 |
| pageSize | integer | 否 | 每页条数，最大 30 |
| statusIds | string[] | 否 | 状态 ID 数组（每个 ID 都是大整数字符串） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].statusId` | string | **状态 ID（大整数，作 assign_ticket 入参）** |
| `data[].name` | string | 状态名称（如 "处理中" / "已解决"） |
| `data[].type` | string | START / NORMAL / END |

#### create_ticket — 创建工单
**写操作，执行前必须按《工单写操作二次确认规则》逐项确认。** 先 `list_templates` 取模板及必填字段；指定他人为处理人时按《openId 解析》先拿 ownerId。**权限位**：[791] AI新建工单（`ticket-create`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| title | string | 是 | 标题，0-128 字符 |
| templateId | string | 是 | 模板 ID（服务端为 64 位 long，**必须以字符串传递**） |
| description | string | 否 | 描述 |
| phone | string | 视模板 | 联系电话 |
| email | string | 视模板 | 邮箱 |
| priorityId | integer | 否 | 优先级 |
| ownerId | string | 否 | 处理人 openId |
| customerId | string | 否 | 客户 C 侧用户 ID（大整数同样字符串传递） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.workorderId` | string | **新创建工单的 ID（创建成功后通常需要复述给用户/继续后续操作）** |

#### update_ticket — 工单信息更新
更新标题、描述、优先级、**处理人**等。**改处理人就用这个接口的 ownerId。写操作，执行前必须按《工单写操作二次确认规则》逐项确认。** **权限位**：[792] AI更新全部工单（`ticket-update`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| workorderId | string | 是 | 工单 ID（大整数，字符串传递） |
| title | string | 否 | 新标题 |
| description | string | 否 | 新描述 |
| priorityId | integer | 否 | 新优先级 |
| ownerId | string | 否 | 新处理人 openId |

**返回值**：操作结果（成功 / 失败 + message）。

#### assign_ticket — 工单状态变更
变更工单流转状态。**注意：名字叫 assign，实为改状态；改处理人请用 update_ticket。写操作，执行前必须按《工单写操作二次确认规则》逐项确认。** **权限位**：[792] AI更新全部工单（`ticket-update`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| workorderId | string | 是 | 工单 ID（大整数，字符串传递） |
| statusId | string | 是 | 目标状态 ID（大整数，字符串传递；先用 list_statuses 取） |

**返回值**：操作结果（成功 / 失败 + message）。

### 坐席管理

#### list_all_staff — 批量拉取员工列表
拉组织架构下员工 openId 列表。**仅返回 openId**，要拿姓名得逐个调 `get_staff_info`，员工多时慢——优先引导用户提供 account（见《openId 解析》）。**权限位**：[793] AI查询全部坐席（`agent-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page_size | integer | 否 | 每页条数（一次最多 500） |
| page | integer | 否 | 页码 |
| id | string | 否 | 部门节点 ID |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].openid` | string | 员工 openId（**不含姓名**，要姓名调 get_staff_info） |
| `total` | integer | 总条数 |

#### get_staff_info — 根据 openId 获取员工信息
拿到员工 openId 后，调用它获取姓名等信息。**权限位**：[793] AI查询全部坐席（`agent-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| openids | string[] | 是 | 员工 openId 列表（一次可批量查多个） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].openid` | string | 员工 openId |
| `data[].name` | string | 员工姓名 |
| `data[].account` | string | 英文工号（如 anncui） |
| `data[].deptName` | string | 部门 |

#### get_staff_openid — 根据 account 批量获取 openId
account 是企点【组织架构】里能看到的一串英文工号。**这是姓名匹配慢/失败时的捷径**：让用户直接提供 account，一次调用搞定。**权限位**：[793] AI查询全部坐席（`agent-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| accounts | string[] | 是 | account（英文工号）列表 |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].account` | string | 英文工号 |
| `data[].openid` | string | 对应 openId |

#### get_staff_monitor — 客服实时监控数据（坐席级）
坐席级实时接待数据：在线/离线/忙碌人数、各坐席当前接待数与时长。**权限位**：[793] AI查询全部坐席（`agent-read`）

> **🎯 用户问"客服在线状态"/"谁在线"/"现在客服在干嘛"时的默认入口**
>
> 当用户提到下列任意意图，**不要追问"你想看什么"，直接调本接口**，再视情况补 `get_message_alerts`：
> - 客服在线状态 / 客服在线情况 / 现在客服在线吗 / 坐席在线
> - 谁在线 / 有几个客服在线 / 在线人数 / 在岗情况
> - 现在客服情况怎么样 / 客服接待情况 / 现在忙不忙
> - 排队多少 / 现在多少会话（这种需要再加 `get_message_alerts`）
>
> 本接口返回 `staffOnlineCount`（在线坐席数）、`staffBusyCount`（忙碌坐席数）、`staffList[]`（每个坐席的接待详情），已经能回答 80% 的"在线状态"类问题。**不要因为接口名带 monitor 就误以为是高级监控功能而跳过。**

> **⚠️ 分页完整性强制规则（已知踩坑）**
>
> 本接口**默认 count=48 单页拉取**，企业坐席数大于 48 时必然分多页。**用户问"全部坐席 / 哪些客服在线 / 在线情况"等"全集筛选类"问题时**，**必须翻完所有页**才能下结论：
>
> 1. 第一页（index=1）拉完后，**先看返回的 `total` 字段**——若企业有 N 个坐席而 N > 48，则需要翻 ⌈N / count⌉ 页。
> 2. 续翻页：`index=2, count=48` 拉第二页；如有更多页继续递增 index。
> 3. 所有页数据**用 Bash/Python 程序化合并**（不要靠 LLM 拼接），再做"在线状态 = 1"等筛选。
> 4. 汇报结果时**必须声明数据范围**：『已拉取全部 N 个坐席（共 M 页），其中在线 X 人：…』；不能只说"在线 X 人：…"隐藏只看第一页的事实。
>
> **真实事故案例**：用户问"现在哪些客服在线"，企业有 68 个坐席分 2 页（每页 48 条），模型只查第一页就汇报『在线坐席共 3 人：钟意 sally、TestReply、smarthuang』。但实际第二页有 polite（status=1）也在线，**漏报了一个**。正确做法：先看 total=68 → 知道分 2 页 → 翻完第二页 → 程序化筛选 status=1 → 完整汇报『在线 4 人：钟意 sally、TestReply、smarthuang、polite』。

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| index | integer | 是 | 页数（从 1 开始）。**用户问全集时必须翻完所有页** |
| count | integer | 是 | 每页拉取数据量，最大 48 |
| status | integer | 否 | 接待状态 0：全部状态 1：接待开启 2：接待关闭 3：PC未登录（未填写时拉全部状态数据） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.total` | integer | **总坐席数（用于判断是否还有下一页）** |
| `data.staffOnlineCount` | integer | 在线坐席数（**注意：这是当前页统计**，全公司在线数需要翻完所有页后程序化算） |
| `data.staffBusyCount` | integer | 忙碌坐席数（同上，当前页统计） |
| `data.staffList[]` | array | 当前页坐席接待明细（openid/姓名/当前接待数/接待时长/status 等） |
| `data.staffList[].openid` | string | 坐席 openId（展示给用户时按 `姓名（openid）` 格式，见《openId 显示规范》） |

> 两个"实时/监控"工具消歧：坐席级实时（含在线/忙碌坐席数）用 `get_staff_monitor`（793）；全局大盘（排队/在线会话）用 `get_message_alerts`（796）；历史统计用报表族（798）。

### 客户管理

#### get_user — 客户资料查询
按 cust_id 查客户详细资料（姓名、电话、备注、标签等）。**权限位**：[794] AI查询全部客户（`customer-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| cuin | string | 是 | 客户 cust_id |

**返回值（关键字段）**：完整客户对象，含 `cust_id` / `name` / `phone` / `email` / `tags[]` / `remark` 等。`cust_id` 始终字符串透传。

#### search_user — 根据社交账号反查 cust_id
**权限位**：[794] AI查询全部客户（`customer-read`）

> ⛔ **type=0（QQ 号）已禁用**：业务侧不支持 QQ 号反查客户资料。当用户提供裸 QQ 号时，**不要调本接口**，按《cust_id 解析规则 → QQ 号查客户的强制规则》直接拦截并引导用户提供 cust_id 或手机号。
>
> 可用 type：1=微信公众号、3=webim、9=微信小程序、22=电话、51=企微、53=微信客服、50=APP。

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| socialAccount | string | 是 | 社交账号 |
| type | integer | 是 | 账号类型（**禁用 0=QQ**；1=微信公众号, 3=webim, 9=微信小程序, 22=电话, 50=app, 51=企微, 53=微信客服） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.cust_id` | string | **查到的 cust_id（作下一跳 get_user 的入参）** |

#### list_customers — 拉取客户列表
游标分页。**客户库通常很大，按姓名匹配易超时——查询慢或报错时，按《cust_id 解析》引导用户去客户库复制 cust_id。** **权限位**：[794] AI查询全部客户（`customer-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| next_custid | string | 否 | 翻页游标；首次不传，后续传上一页返回的游标 |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.list[].cust_id` | string | 客户 cust_id（字符串透传） |
| `data.list[].name` | string | 客户姓名 |
| `data.next_custid` | string | 下一页游标，**为空表示末页** |

> `access_token` 由 MCP Server 处理，不需 AI 填写。

### 会话记录

#### get_monitored_sessions — 人工接待会话记录拉取
按时间段拉人工接待会话列表（客户名称、备注、标签、时长等）。**起止时间未给先追问；大批量前确认。** **权限位**：[795] AI查询全部人工会话记录（`session-read`）

> **⚠️ 通路默认全量规则**：用户说"拉会话 / 看聊天记录 / 这个客户聊了什么"等**未明确说通路**（QQ / 微信公众号 / 微信小程序 / 企微 / 微信客服 / webim / 电话 / APP）时，**不要传 `subType`**，让接口返回所有通路的会话。**禁止**凭印象只传一个通路（如默认企微）。返回后按通路分组展示，让用户看清各通路的分布。用户**明确**指定通路（"只看微信会话""只看 QQ"等）时再按指定 subType 传。

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | 是 | 开始日期 YYYY-MM-DD |
| endDate | string | 是 | 结束日期 YYYY-MM-DD |
| count | integer | 否 | 每页条数，最大 50 |
| index | integer | 否 | 页码，1 起 |
| staffId | string | 否 | 坐席 openId |
| socialAccount | string | 否 | 客户社交账号 |
| subType | integer | 否 | 通路类型（**用户未指定时不传，默认拉全部通路**：0=QQ / 1=微信公众号 / 3=webim / 9=微信小程序 / 22=电话 / 50=APP / 51=企微 / 53=微信客服）|
| convType | integer | 否 | 会话类型 |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].sessionId` | string | **会话 ID（大整数字符串，作 get_staff_messages 入参）** |
| `data[].staffId` | string | 坐席 openId |
| `data[].cust_id` | string | 客户 cust_id |
| `data[].startTime` / `data[].endTime` | string | 会话起止时间 |
| `data[].convRemarks` | string | 会话备注（用于业务意图识别） |
| `data[].customerTag` | string | 客户标签 |
| `total` | integer | 总条数 |

#### get_staff_messages — 人工接待消息记录拉取
按 session_id 拉某次人工会话的逐条聊天记录。**权限位**：[795] AI查询全部人工会话记录（`session-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| session_id | string | 是 | 会话 ID（来自 get_monitored_sessions） |
| ref_time | string | 否 | 翻页参考时间（微秒时间戳，**大整数字符串透传**，原值取自上一页响应不要自行计算或转 number） |
| paging_type | integer | 否 | 翻页方向（0=向后, 1=向前） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].msgTime` | string | 消息时间（微秒时间戳，大整数字符串） |
| `data[].fromType` | string/integer | 发送方（坐席 / 客户） |
| `data[].content` | string | 消息内容 |
| `data.has_more` | boolean | 是否还有下一页 |
| `data.next_ref_time` | string | 下一页 ref_time（字符串透传） |

### 监控

#### get_message_alerts — 会话监控实时大盘
全局实时指标：排队数、在线会话数、满意度等。**权限位**：[796] AI查询全部客服会话监控（`monitor-read`）

**入参**：无必填参数。

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.queueCount` | integer | 当前排队会话数 |
| `data.onlineSessionCount` | integer | 当前在线会话数 |
| `data.todaySatisfaction` | number | 今日满意度（百分比） |
| `data.todayResponseTime` | number | 今日平均响应时长（秒） |

### 大模型机器人

#### list_robots — 大模型机器人列表查询
拉企业已开通的大模型机器人列表（机器人名称、robotId 等），用于先拿到 robotId 后再调 `list_robot_sessions` 拉会话。**当用户给的是机器人名称（如"机器人演示-Ann"）而不是 robotId 时，必须先调本接口解析。** **权限位**：[797] AI查询机器人全部会话记录（`AI-robot-session-read`）

**入参**：参数以最新文档为准。

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].robotId` | string | **机器人 ID（大整数字符串，作 list_robot_sessions 入参）** |
| `data[].name` | string | 机器人名称（用于按名匹配） |

#### list_robot_sessions — 大模型机器人会话记录拉取
**起止时间未给先追问。** **权限位**：[797] AI查询机器人全部会话记录（`AI-robot-session-read`）

> **⚠️ 通路默认全量规则**：用户说"拉机器人会话 / 看机器人聊了什么 / 这个客户问机器人什么"等**未明确说通路**时，**不要传 `Cid 类型` 等通路过滤参数**，让接口返回所有通路的机器人会话。返回后按通路分组展示。用户明确指定通路时再严格按指定的 type 传入。

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| robotId | string | 是 | 机器人 ID（大整数，字符串传递） |
| startTime | string | 否 | 开始时间 |
| endTime | string | 否 | 结束时间 |
| page | integer | 否 | 页码 |
| pageSize | integer | 否 | 每页条数 |
| Cid 类型 | integer | 否 | 通路类型（**用户未指定时不传，默认拉全部通路**） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].SessionID` | string | **会话 ID（大整数字符串，作 get_robot_messages 入参）** |
| `data[].RobotID` | string | 机器人 ID |
| `data[].startTime` / `data[].endTime` | string | 起止时间 |
| `total` | integer | 总条数 |

#### get_robot_messages — 大模型机器人消息记录拉取
按会话 ID 取机器人会话的问答对。**权限位**：[797] AI查询机器人全部会话记录（`AI-robot-session-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| robotId | string | 是 | 机器人 ID（大整数，字符串传递） |
| sessionIds | string[] | 是 | 会话 ID 列表（来自 list_robot_sessions；每个 ID 均为大整数字符串） |

**返回值（关键字段）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[].sessionId` | string | 会话 ID |
| `data[].messages[].question` | string | 用户提问 |
| `data[].messages[].answer` | string | 机器人回答 |
| `data[].messages[].timestamp` | string | 时间戳 |

### 数据报表（端点已更新，参数以最新文档为准）

> 下列 4 个接口均为"会话客服分析"系列，起止时间为通用必填项；其余字段按各自文档地址核对。**起止时间未给先追问。** 返回值通常含 `data.metrics`（核心指标对象）+ `data.list[]`（按坐席/天/会话维度的明细），AI 解析时按用户问的维度展示即可。

#### get_quality_report — 满意度分析
**权限位**：[798] AI查询全部客服报表（`report-read`）

**入参**

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | 是 | YYYY-MM-DD |
| endDate | string | 是 | YYYY-MM-DD |

#### get_service_report — 总览（客服维度）
**权限位**：[798] AI查询全部客服报表（`report-read`）（参数同上）

#### get_staff_duration — 时长分析
**权限位**：[798] AI查询全部客服报表（`report-read`）（参数同上）

#### get_staff_funnel — 响应度分析
**权限位**：[798] AI查询全部客服报表（`report-read`）（参数同上）。名字保留为 `get_staff_funnel`，当前对应**响应度分析**，已不是"客户转化漏斗"。

---

## 常见调用链路（每个域至少一条示例）

### 【工单管理】创建工单
用户："帮我建个工单，VIP 模版，处理人是张三"

1. 解析处理人 openId：先 `list_all_staff` + `get_staff_info` 按姓名匹配；匹配慢/不准 → 引导用户给 account → `get_staff_openid` 一步到位。
2. `list_templates` 搜 "VIP" 取 templateId（**保持字符串原值不动**）及必填字段。
3. **按《工单写操作二次确认规则》逐项展示参数，请用户明确确认或调整**——即便用户上文已说过模板/处理人，也必须再问一次"用这些参数对吗？"。
4. 用户确认后调 `create_ticket`（所有大整数 ID 字段保持字符串透传）。

### 【工单管理】改状态 / 改处理人
- "把这个工单改为处理中" → `list_statuses` 取目标 statusId → **按二次确认规则确认 workorderId + statusId 后**调 `assign_ticket`。
- "把这个工单分给张三" → 解析张三 openId → **按二次确认规则确认 workorderId + 新 ownerId 后**调 `update_ticket`。

### 【坐席查询】客服在线状态 / 谁在线 / 现在客服情况怎么样
用户任意一种表达：「客服在线情况」「现在谁在线」「有几个客服在岗」「客服在忙吗」

1. **直接**调 `get_staff_monitor`（坐席级实时监控），无需追问"你想看什么"——本接口已含在线/忙碌/接待数据。
2. 如果用户的问题里还涉及"排队 / 在线会话总数 / 客户等待"，**再补**调 `get_message_alerts` 取全局大盘。
3. 汇总返回，重点字段：`staffOnlineCount`（在线坐席数）/`staffBusyCount`（忙碌）/`staffList[]`（各坐席详情）。

> ⚠️ 反例（禁止）：看到"客服在线状态"就追问"你是想查在线员工列表，还是接待情况？" —— 用户语义就是要看接待端的实时状态，直接 `get_staff_monitor` 比追问更专业。

### 【客户查询】用户给社交账号或客户 ID
- 用户给 **cust_id**（明确说"客户 ID 是 xxx"）→ 直接 `get_user`。
- 用户给 **微信/手机号/企微 ID 等**社交账号 → `search_user`（按通路选 type）→ `get_user`。
- 用户给 **纯数字串（5-12 位）查客户** → **拦截**，按《QQ 号查客户的强制规则》话术引导用户提供 cust_id 或手机号，**不要**调 `search_user` type=0。
- 用户给客户**姓名** → `list_customers` 翻页匹配；客户库大时超时立即停止，引导用户去客户库复制 cust_id。

### 【人工会话与消息记录】分析某段时间会话
用户："帮我看下昨天某个客户的聊天记录"

1. 起止时间不明先追问（"昨天"换算成具体日期再确认）。
2. 解析客户：给社交账号 → `search_user`；给姓名 → 按《cust_id 解析》，必要时引导提供 cust_id。
3. **通路默认全量**：用户没说"通过 QQ / 微信 / 企微"等具体通路时，调 `get_monitored_sessions` 时**不传 `subType`**，让接口返回所有通路的会话。
4. `get_monitored_sessions`（带 startDate/endDate + socialAccount 或 staffId 过滤）拉会话列表。大批量前先报规模并确认。
5. 对感兴趣的 `sessionId` 调 `get_staff_messages` 拉逐条聊天，AI 分析。
6. 汇总时**按通路分组**展示，让用户看清各通路的会话分布。

### 【大模型机器人记录】看机器人最近对话
用户："看看那个机器人这周聊了什么"

1. 起止时间不明先追问（"这周"换算成具体起止日期再确认）。
2. 解析 robotId：用户直接给 robotId 则用；用户给的是机器人名称（如"机器人演示-Ann"）→ 调 `list_robots` 按名称匹配拿 robotId（**保持字符串原值**）。
3. **通路默认全量**：用户没说"通过 QQ / 微信公众号 / 企微"等具体通路时，调 `list_robot_sessions` 时**不传 `Cid 类型`**等通路过滤参数，让接口返回所有通路的机器人会话。
4. `list_robot_sessions`（robotId + startTime + endTime）拉会话列表，分页全翻。
5. 对感兴趣的 sessionIds 调 `get_robot_messages` 拉问答对，AI 分析。
6. 汇总时**按通路分组**展示。

### 【客服数据报表】生成运营日报
用户："出一份今天的运营日报"

1. 确认"今天"的具体起止时间。
2. `get_message_alerts` 取实时大盘。
3. `get_quality_report` 满意度、`get_service_report` 客服总览、`get_staff_duration` 时长、`get_staff_funnel` 响应度。
4. `get_staff_monitor` 取坐席在线与实时接待数据。
5. AI 汇总成报告。

### 【会话分析 + 批量建单】综合示例
用户："拉最近 30 天会话，有购买意向的客户每个建一个工单"

1. 起止时间未给先确认；解析处理人 openId。
2. `get_monitored_sessions` 分页拉取（每页最多 50；**先报"预计 N 页"取得用户同意**）。
3. AI 分析 convRemarks + customerTag 识别购买意图。
4. `list_templates` 取模板。
5. **按《工单写操作二次确认规则》先告知"预计创建 N 张工单"并展示第一张完整参数（templateId/ownerId/title 等），取得整体同意**，再循环 `create_ticket`；批次内任一条参数与样本不一致都要重新确认。

---

## 注意事项速查

> 这一节是上面所有规则的精简提取，便于 AI 在执行中快速核对。详细规则见各对应章节。

- **认证**：Token 过期信号（401 / `errcode=40001`）→ 不重试，按《认证》话术引导重新授权。
- **权限**：权限错误（403）→ 按映射表填写缺失权限位名称，按话术回复。其他错误见《常见错误码速查表》。
- **员工 openId**：我自己 → MCP Server；具名姓名 → `list_all_staff` + `get_staff_info` 匹配；匹配慢/失败 → 引导提供 account → `get_staff_openid`。
- **⚠️ openId → 姓名展示规范**：所有展示给用户的处理人/坐席/操作者字段，**禁止裸输出 openId**——必须批量调 `get_staff_info` 解析为姓名，按 `openid（姓名）` 或 `姓名（openid）` 格式展示；同一轮对话内的映射可缓存复用；员工不存在时显示 `openid（未找到员工）`。
- **客户 cust_id**：手机/微信等社交账号 → `search_user`（type≠0）；姓名 → `list_customers` + `get_user`；**超时或报错时引导用户去客户库复制 cust_id**。
- **⛔ 裸 QQ 号查客户禁用**：5-12 位纯数字 + 上下文是"查客户"时，**直接拦截**，按《QQ 号查客户的强制规则》话术引导用户提供 cust_id 或手机号，**不要调 search_user type=0**。
- **operator**：所有接口的 `operator` 由 MCP Server 注入，不必手工填。
- **大整数 ID 全 string**：`templateId` / `workorderId` / `customerId` / `statusId` / `robotId` / `sessionId` / `ref_time` 等，参数与返回值**一律字符串透传**，不做任何数值转换。
- **写操作二次确认**：工单 create/update/assign 前即便参数齐全也必须逐项让用户确认或更换，不得直接执行；批量场景按批次确认。
- **assign_ticket 是改状态**；改处理人请用 `update_ticket` 的 ownerId。
- **客服在线状态 = `get_staff_monitor`**：用户问"谁在线 / 客服在线情况 / 现在客服情况怎么样"等，**直接**调本接口，无需追问；含排队/在线会话再补 `get_message_alerts`。
- **两类"监控"消歧**：`get_message_alerts` 全局大盘 / `get_staff_monitor` 坐席级实时（含在线/忙碌坐席数）/ 报表族（798）历史统计。
- **`get_staff_funnel` 现为响应度分析**，已不是漏斗/转化。
- **⚠️ 计数必须程序化**：任何"共 N 条 / 一共 N 个"的输出，**优先取接口返回的 total 字段**；没有 total 时用 Bash/Python `len()` 算，禁止靠肉眼数。"开头说 N 条 + 下面列 M 条"两数对不上时立刻停止重算。用户反馈数错时先承认再程序化重算。
- **⚠️ 分页完整性必检**：用户问"全部 / 所有 / 在线情况 / 筛选某条件"时，**必须翻完所有页才能下结论**——已知事故：`get_staff_monitor` 默认 count=48，企业 68 个坐席分两页时只看第一页会漏掉第二页的 polite 等在线坐席。第一页拉完后立刻看 `total`，若 `已拉条数 < total` 必须续翻，并先告知用户预计页数取得同意；汇报结果时必须声明数据范围（"已拉取全部 N 个坐席，共 M 页" vs "当前只看了第一页"）。
- **⚠️ 拉聊天记录通路默认全量**：用户说"拉聊天记录 / 看会话 / 这个客户最近聊了什么 / 这个机器人的对话"时，**只要没明确说"通过 QQ / 微信 / 企微 / 微信客服"等通路**，必须**默认拉全部通路**——`get_monitored_sessions` 不传 `subType`、`list_robot_sessions` 不传 `Cid 类型`，让接口返回所有通路的会话；汇总时按通路分组展示。**禁止**凭印象只传一个通路或先猜后换。用户明确指定通路时严格按指定的来。
- **⚠️ 时间戳强制规范**：① 任何"今天/最近 N 天/本周"先用 Bash `date` 取真实时间，不凭记忆推断；② 换算后**先复述给用户确认**再写入参数；③ 单位必须对（list_tickets=毫秒、报表/会话/机器人=秒、ref_time=微秒字符串）；④ 接口返回空时优先怀疑时间戳算错，不要立刻断言"无数据"。
- **起止时间未给先追问**；用户给相对时间（"上周/本月"）先按规则 D 换算并向用户复述确认。
- **大批量先报规模并取得用户同意**：会话拉取/批量建单等场景。
- **数据范围**：覆盖全员，与登录账号无关——默认全公司数据，按需用 ownerId/staffId 过滤；注意隐私。
