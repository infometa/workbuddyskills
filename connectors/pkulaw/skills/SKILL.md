---
name: pkulaw
title: 法宝法律检索
description: 北大法宝官方法律检索 MCP Skill。涉及「法律」「法规」「法条」「司法解释」「判例」「类案」「案由」「合同审查」「合规清单」「裁判规则」「裁判依据」「争议焦点」「指导案例」「公报案例」「民法典」「公司法」「刑法」「量刑」「劳动争议」「劳动仲裁」「工伤」「离婚」「继承」「彩礼」「抚养」「民间借贷」「借条」「租赁」「买卖合同」「交通事故」「侵权」「行政处罚」「行政复议」「知识产权」「商标」「专利」「著作权」「电子证据」「数据合规」「个人信息保护」等法律咨询、检索、核实原文的场景时使用。提供 5 个工具：法条语义检索、法条精确查询、法规列表、案例语义检索、案例列表（含完整判决要素）。所有结果带 pkulaw.com 原文链接，可追溯、可复核；不构成法律意见。
description_zh: 北大法宝官方法律检索 MCP Skill。覆盖中国大陆法规与司法案例双库；适用于法规/法条/司法解释检索与核实、类案研判、合同审查、合规清单，及民商事、劳动、婚姻家庭、借贷、刑事、行政、知识产权等法律咨询。先检索后作答，禁止凭记忆答法条/案号；工具名以 tools/list 为准；不构成法律意见。
description_en: "PKULaw official legal search MCP Skill. Chinese statutes + judicial cases. Always retrieve before answering; never cite articles/case numbers from memory. Call tools by the names in tools/list. Not legal advice."
version: "2.1.0"
author: "北京北大英华科技有限公司（北大法宝）"
---

# 法宝法律检索（北大法宝MCP）

接入北大法宝（pkulaw.com）权威库，覆盖中国大陆宪法、法律、行政法规、地方性法规、部门规章、司法解释，及各级法院判决书 / 裁定书 / 调解书。连接与鉴权由所在客户端负责；本 Skill 只管拿到工具后怎么调、怎么读、怎么作答。

**所有法律结论必须落到工具返回结果，禁止凭模型记忆作答。**

> **启动时先读本会话 `tools/list`，按【用途/能力】匹配实际工具名**：下表工具名仅为对照快照，与实际不符时一律以 `tools/list` 暴露名为准（个别客户端把 `.` 显示成 `_`，如 `mcp-case.get_case_list` → `mcp-case_get_case_list`，以实际暴露名调用）；若出现本文未列出的新工具，读其 `description` 判断用途后按需使用，**不要因为本文没写就不调用**。
>
> **筛选参数名以本 Skill 第三节为准**：部分客户端 `tools/list` 广告的筛选参数名可能滞后（如 `province`/`department`/`type`/`date_start`），传这些会报 `Unexpected keyword argument`。请用本文列出的名字（`courthouse_province`/`issue_department`/`doc_type`/`decision_date_start` 等）；若仍被拒，**去掉该筛选、把条件并入 `text`** 即可，切勿因此放弃检索或改为凭记忆作答。`text` 主检索无筛选时永远可用。

## 一、何时使用 / 何时不用

**应使用**：查中国大陆现行/历史法规与司法解释原文；核实「《X 法》第 X 条」；检索类案、提取裁判规则；写意见书/合同审查/合规清单找依据。

**不应触发**：

| 用户请求 | 建议回复 |
|---|---|
| 境外法 / 港澳台法 | 本工具仅覆盖中国大陆法律，境外法请咨询涉外律师 |
| 个案结果预测（"我能赢吗"） | 无法预测具体走向，可检索类案供参考 |
| 征信 / 个人金融数据 | 非本工具范畴 |
| 律师推荐 / 案件代理 | 请通过律协或正规渠道选择执业律师 |
| 批量抽取判决/法规数据集 | 单次上限约 20 条，禁止用于训练或批量抽取 |

本 Skill **不含**：案号识别、法条识别、法宝超链、修正幻觉（均为独立服务）。

## 二、5 个工具与路由

> **"用途"列是稳定契约，工具名只是对照快照**——名字若变，按用途对齐 `tools/list` 实际暴露名即可。

| 工具（tools/list 全名，以实际暴露名为准） | 用途 | 优先选择条件 |
|---|---|---|
| `mcp-law-search-service.search_article` | 法条语义检索：自然语言 → 相关法条 | 描述事实/问题、未给出具体法名+条号 |
| `mcp-law-search-service.get_article` | 法条精确查询：法名 + 中文条号 → 单条原文 | 明确「《X 法》第 X 条」引用 |
| `mcp-law.get_law_list` | 法规列表：关键词 → 法规元数据（时效/效力/文号/机关） | 列一批法规、合规清单、立法追踪 |
| `mcp-case-search-service.search_case` | 案例语义检索：自然语言案情 → 类案（含查明/认为/结果） | 找类案、日常参考（可按法院/省/日期/文书类型筛） |
| `mcp-case.get_case_list` | 案例列表（深度）：关键词 → 判例 + 完整判决要素（29 字段） | 写意见书、深度研判、要争议焦点/裁判依据/案例级别 |

### 决策树

```
法规？
  ├─ 已给法名 + 条号 → get_article
  ├─ 描述问题找依据（自然语言）→ search_article
  └─ 列一批 / 合规清单 / 按效力位阶筛 → get_law_list
案例？
  ├─ 自然语言找类案、常规参考 → search_case
  └─ 深度研判 / 要争议焦点·裁判依据·案例级别 → get_case_list

复杂任务：先 search_article（或 get_law_list）定法 → 再 search_case（或 get_case_list）找案 → 必要时 get_article 补关键条文
```

## 三、跨工具坑速查（schema 里看不出来，务必遵守）

| 主题 | 语义类（search_article / search_case） | 列表类（get_law_list / get_case_list） |
|---|---|---|
| 返回体 | **裸数组** `[...]` | **包裹对象** `{"Message","Data":[...],"Total":N}` |
| 链接字段 | `url`，**纯链接**，直接可点 | `Url`，**markdown** `[北大法宝](...?way=mcp)`，展示取括号内裸链 |
| 时效入参 | **单字符串** `"现行有效"` | **数组** `["现行有效"]` |
| 日期入参 | **ISO** `2024-01-01` | **点号** `2024.1.1` |
| 案例法院字段 | `courthouse_name` | `Court` |

**分工具要点**：
- `search_article`：主参数 **`text`**（传 `query` 会失败）；可选 `lib`(中央/地方,单串)、`timeliness`(单串)、`issue_department`、`implement_date_start/end`(ISO)、`size`(1–20)。返回的 `lib` 是库代码(如 `chl`)，≠ 入参；`article` 偶为空可转 `get_article`。空结果形态是 `{"result":[]}`，有结果才是裸数组。
  - **`issue_department` 是完全精确匹配（非包含匹配）**：`国务院`/`交通运输部`/`全国人民代表大会` 等按常规名即可命中；**唯一例外是全国人大常委会——库里存简称 `全国人大常委会`，传官方全称 `全国人民代表大会常务委员会` 会 0 命中**。子串（如 `人大常委会`）也不命中。拿不准机关名时，优先把机关信息写进 `text` 或改用 `get_law_list` 的 `effectiveness` 筛，**勿因 `issue_department` 返回空就断言「无此法」**。
- `get_article`：`title` + `number`(**中文条号**如 `第一千零七十七条`，勿传 `1077`)。仅 `title/article/timeliness/url` 稳定有值，**空字段勿臆造**。
- `get_law_list`：`title`/`fulltext` **至少一个**；`timeliness`/`effectiveness` 是**数组**；日期 `startImplementDate/endImplementDate` 用**点号**。**无 `lib` 参数**（要「中央层级」靠 `EffectivenessDic`+`IssueDepartment` 判断）。返回 `TimelinessDic`/`EffectivenessDic` 为**中文数组**（非 `01/02` 编码）。空结果 `{"Message":"未找到数据","Data":[],"Total":0}`。
- `search_case`：主参数 `text`；筛选 `case_type`、`doc_type`(判决书/裁定书/决定书/调解书/其他文书)、`courthouse_name`(精确匹配，须库里存的法院全称如`浙江省金华市中级人民法院`)、`courthouse_province`(省简称如`浙江`即可)、`decision_date_start/end`(ISO)、`size` **均实测生效**。返回 12 字段含 `ascertain`/`identified`/`referee_result`。
- `get_case_list`：`title`/`fulltext` **至少一个**；`documentAttr`/`caseGrade` 是**数组**，`court` 是字符串，日期 `startLastInstanceDate/endLastInstanceDate` 用**点号**。返回 29 字段。
- **`Total` 是全库命中总数（可达千万级），不是本次返回条数**——禁止说「共找到 N 条」，说「本次返回约 N 条，命中量大可加条件缩小」。单次上限约 20 条，**禁止拼接多条全文成数据集**。

## 四、输出纪律（严格遵守）

1. **不凭记忆**答法条/案号/文号——即使"记得"也必须先调工具取真实原文。
2. **每条依据附链接**：列表类取 `Url` 裸链，语义/精确类用 `url`。
3. **时效强制标注**：`timeliness` 非「现行有效」，或 `TimelinessDic` 含「废止或失效/已被修改」等，必须显式提示「已废止/已修改，仅供参考」。
4. **效力级别排序**：法律 > 行政法规 > 部门规章 > 司法解释/其他；冲突以高位阶为准。
5. **新法优于旧法**：同级并存按 `IssueDate`/`ImplementDate` 取最新；引用旧法案例（裁判日期早于现行法生效日）须提示「适用旧法，参考价值有限」。
6. **特别法优于一般法**：如公司法 vs 民法典、劳动合同法 vs 民法典，涉该领域时特别法优先。
7. **案例力度**：指导性案例（应当参照）> 公报案例（高度参考）> 典型/参考案例 > 普通案例（仅供参考）。引用普通案例须附「最终以法院裁量为准」。
8. **裁判倾向**：多判例不一致时按 `courthouse_name`/`Court` + 日期标差异，给「主流倾向 + 少数观点」，不要只挑一个当唯一答案。
9. **空结果不编造**：返回空/未找到时如实说明；关键词 0 命中改语义检索，语义 0 命中让用户换表述。
10. **不替代律师**：资料检索与研究辅助，**不构成法律意见**；涉具体案件处理/对外文书，结尾必附「建议咨询执业律师」。

## 五、典型场景（正确调用）

### A. 法律咨询（法规 + 类案）
1. `search_article` → `{"text":"员工连续旷工三天公司能否解除劳动合同","timeliness":"现行有效","lib":"中央","size":5}`
2. `search_case` → `{"text":"员工连续旷工 公司解除劳动合同","size":5}`
3. 输出：结论 + 法条依据(链接) + 类案参考(案号/法院/链接) + 待复核点(规章公示、考勤证据等) + 律师建议

### B. 合同条款核查
1. `search_article` → `{"text":"单方解除合同不承担责任 格式条款"}`
2. `get_article` → `{"title":"民法典","number":"第四百九十六条"}`，必要时再取 `第四百九十七条`（无效情形）
3. 输出：风险等级 + 法条原文(链接) + 修改方向

### C. 精确取条
`get_article` → `{"title":"民法典","number":"第一千零七十七条"}` → 展示 `article`+`url`，空字段不臆造

### D. 合规清单
1. `get_law_list` → `{"title":"数据出境","timeliness":["现行有效"],"effectiveness":["法律","行政法规","部门规章"]}`
2. 按 `EffectivenessDic` 分组，附 `DocumentNO`/`IssueDepartment`/`ImplementDate`/裸 `Url`
3. 重点条文再 `get_article` 取原文

### E. 地域限定类案
`search_case` → `{"text":"房屋租赁押金返还纠纷","courthouse_province":"浙江","doc_type":"判决书","decision_date_start":"2023-01-01","size":5}`

### F. 深度类案研判（写意见书）
1. `get_case_list` → `{"fulltext":"押金","documentAttr":["判决书"],"caseGrade":["指导性案例","公报案例"],"court":"最高人民法院"}`
2. 按 `CaseGrade` 优先级排序，逐条展开 `Ascertain 查明 → ControversialFocus 焦点 → Identified 认为 → RefereeBasis 依据 → RefereeResult 结果`
3. 附 `CaseFlag`(案号)+`Court`+裸 `Url`；`Total` 大时提示「命中量大，已按条件取前若干条」

### G. 空结果防幻觉
`get_law_list({"title":"银河系劳动合同管理办法"})` → 返回「未找到数据」 → 如实告知，引导换关键词或改用 `search_article`；**禁止编造法规名/文号/条文**。

## 六、鉴权与错误码处置

连接与鉴权由所在客户端完成，**本 Skill 不处理、也不写入任何 Token/密钥**。服务按积分计费，账户有积分即可调用。调用失败先看返回错误码，**积分/配额/权限类错误属账户状态问题，禁止改词重试**：

| 码 | 含义 | 话术 / 处置 |
|---|---|---|
| `90001` | 积分用尽 | 「检索积分已用尽，请充值/续费后再试。」不重试 |
| `90002` | 成员用量达上限 | 「成员用量已达上限，请联系管理员提配额。」不重试 |
| `900908` | 无该服务权限 | 「未开通该服务，请在 mcp.pkulaw.com 确认订阅。」不重试 |
| `401` / `403` | 未授权 | 在客户端重新授权/连接，确认已订阅后再试 |

出现未列出的码：如实说「服务暂时不可用，建议稍后重试或联系服务方」，**不要编造检索结果**；不向用户暴露原始码/内部细节（除非追问）。

## 七、数据与免责

- **数据来源**：北大法宝（pkulaw.com），中国大陆法规 + 公开裁判文书；**不含港澳台与外国法**。
- **时效**：实时同步主库，废止/已修改在时效字段标注。
- **免责**：资料检索与研究辅助，**不构成法律意见**；请以 pkulaw.com 最新文本为准。
