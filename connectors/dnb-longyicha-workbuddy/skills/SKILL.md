---
name: dnb-company-verification
description: 使用 D&B China Data（主题化中国数据 CDT）MCP 企业档案 Server（/v1/company）全部 14 个 Tool，对单一企业开展工商登记、简易注销、变更、股东与控股治理、主要人员、受益所有人、实际控制人、对外投资、分支机构、ICP 备案与企业年报的尽调式核验，输出结构化核查底稿与事实包。当用户要求做企业信息核验、工商底稿、主体真实性核查、股权与治理结构核查、UBO/实控人核验、年报与变更追溯、仅查企业档案不下钻风险/评分时触发此 skill。本 skill 只使用企业档案 Server，不输出评级与准入结论。
---

> 企业信息核验 SKILL · D&B China Data MCP（CDT 主题化中国数据）· v1.0.0
> 面向**单一主体工商与股权治理底稿**场景：输入企业名称或统一社会信用代码，锚定后并发调用**企业档案 Server 全部 14 个 Tool**（对齐《主题化中国数据-MCP 服务 0901》数据字典），输出可直接归档的**十二类核查模块底稿**。
>
> **Server 边界（硬性）**：本 SKILL **只能**调用**企业档案 Server**（MCP 基址 `https://mcp.dnbservice.com.cn/v1/company`）。**禁止**调用风险雷达、企业评分、商情洞察、知产智库、关联图谱或任何其他 Server——即使客户要求「顺便查风险 / 评级 / 诉讼 / 专利 / 两企业关联」，须说明超出本 SKILL 范围并转对应 SKILL。
>
> 核心能力：
>
> - **14 Tool 全覆盖（0901 字典 · 企业档案 Server 全集）**：`search_company` · `search_company_registration` · `search_simple_deregistration` · `search_company_changes` · `search_shareholders` · `search_controlling_shareholders` · `search_key_personnel` · `search_beneficial_owners` · `search_actual_controllers` · `search_company_investments` · `search_branches` · `search_branches_headquarters` · `search_icp_filing` · `search_annual_reports`——`--module all` 时**每个 Tool 各调用 1 次**，典型 **14 次**（无额外下钻）
> - **客商尽调工商子集**：覆盖 `dnb-counterparty-dd` 中企业档案域的**全部 14 Tool**，但不计分、不评级、不扩证司法/知产/跨境
> - **二要素硬闸**：名称与 USCC 不一致立即终止，不输出任何核查结论
> - **治理链完整呈现**：股东 → 控股股东 → 实控人 → 受益所有人 → 主要人员，逐表原值列示；`final_shareholding_ratio_percent` / `holding_path` **只引用接口字段**，**禁止**自行穿透相乘
>
> 适用场景：开户 / 准入前的工商底稿 · KYC 主体真实性核验 · 合同签约主体核查 · 供应商档案建档 · 投前工商与股权治理快核 · 年报与变更轨迹留档 · 仅购买企业档案模块的客户场景。
>
> 使用方式：
> `/dnb-company-verification 企业名称 [--uscc 18位] [--years 3] [--module all|registration|simple_dereg|changes|shareholders|controlling|personnel|ubo|controller|investments|branches|branches_hq|icp|annual] [--format md|json|html]`
>
> **⚠ 本 SKILL 是事实层工具**：只输出企业档案可核验字段与清单计数，**不输出** A/B/C/D 评级、红/橙/黄/绿分流、授信意见、准入否决或「空壳 / 高风险」等定性结论。发现异常事实时只能写「存在 X 记录，建议转 dnb-risk-screening / dnb-counterparty-dd 进一步评估」，并绑定具体字段证据。

**命令**：`/dnb-company-verification` · **MCP 工具集**：`企业档案 Server（唯一 · 14 Tool · https://mcp.dnbservice.com.cn/v1/company）`

---

## 数据原值纪律（全报告强制 · 对齐 BRD §7.2 · 0901 字段字典）

- 注册资本、持股比例（含 `shareholding_ratio` / `direct_holding_ratio` / `final_shareholding_ratio_percent` / `ratio`）、认缴/实缴金额、出资日期、年报财务字段等**一律逐字引用接口原始字符串**，保留全部小数位（`Decimal(32,6)` 字段含 6 位小数）。
- 同一指标在摘要、模块正文与事实包中重复出现时，**每一次复用同一原始字符串**。
- **禁止跨记录自行加总、相减、相乘、除法或估算**。「股东合计持股」「最终受益比例」等**只能引用** `final_shareholding_ratio_percent` / `holding_path` 等接口返回字段；禁止用 `ratio`（0~1）自行换算后再与 `shareholding_ratio` 混用。
- 接口未返回的字段写「未披露」；调用失败写「本次未核验」；成功返回 0 条写「本次未发现公开记录」。**三者严格区分**。
- `is_historical_filing` / `is_in_office` / `is_deleted` / `is_historical` 等状态字段按原文展示；**历史记录不得当作当前状态**。

## 实体锚定纪律（Entity Anchoring）

1. 先调 `search_company`（`searchType=1` 精准 → `=2` 模糊）；`searchKey` 支持企业名称（≥3 字）、USCC（≥8 位）、法人名称（≥2 字）、地址（≥6 字）、经营范围（≥6 字）等（见 0901 字典）。
2. 多条结果**必须向用户确认**；取 `unified_social_credit_code` 后，**后续 13 个 Tool 的 `searchKey` 一律传 USCC**。
3. 用户同时给出名称与 USCC 时执行**二要素一致性核验**；不一致 → **立即终止**。
4. 简称 / 品牌名不得直接进入流程，必须先完成锚定。
5. 集团场景须在首页说明：本次锚定主体、与总公司/分支机构关系（来自 `search_branches_headquarters`）；`relationshipType` 默认不传（字典默认 `1`）；若需同时查总公司方向，**额外**再调一次 `relationshipType=2`（计第 15 次调用，须向用户说明）。

---

## 🔍 取数方法论 · 锚定 → 十四 Tool 并发

### 步骤 0 · 主体锚定（Tool 1/14 · 必调）

| Tool | 规范名 | 关键入参 |
| --- | --- | --- |
| `search_company` | 企业检索 | `searchKey` · `searchType`（1 精准 / 2 模糊）· 可选 `pageNum` / `pageSize`（默认 1 / 50） |

### 步骤 1 · 十二类核查（Tool 2–14/14 · `--module all` 时全部并发）

| Tool | 规范名 | 核查模块 | 关键入参（0901） |
| --- | --- | --- | --- |
| `search_company_registration` | 企业工商信息 | 工商登记 | `searchKey`=USCC |
| `search_simple_deregistration` | 简易注销 | 简易注销 | `searchKey`=USCC |
| `search_company_changes` | 变更记录 | 变更 | `searchKey` · 可选 `pageNum` / `pageSize`（默认 50） |
| `search_shareholders` | 股东信息 | 股东 | `searchKey` |
| `search_controlling_shareholders` | 控股股东 | 控股股东 | `searchKey` · 可选 `pageNum` / `pageSize` |
| `search_key_personnel` | 主要人员信息 | 主要人员 | `searchKey` · 可选 `pageNum` / `pageSize` |
| `search_beneficial_owners` | 受益所有人 | 受益所有人 | `searchKey` · 可选 `pageNum` / `pageSize` |
| `search_actual_controllers` | 实际控制人 | 实际控制人 | `searchKey` |
| `search_company_investments` | 对外投资 | 对外投资 | `searchKey` · 可选 `pageNum` / `pageSize` |
| `search_branches` | 分支机构 | 分支机构清单 | `searchKey` |
| `search_branches_headquarters` | 分支机构与总公司 | 分支/总公司关系 | `searchKey` · 可选 `relationshipType`（1 分支 / 2 总公司，**默认 1**）· `pageNum` / `pageSize` |
| `search_icp_filing` | 企业网站 ICP 备案 | ICP 备案 | `searchKey` · 可选 `pageNum` / `pageSize` |
| `search_annual_reports` | 企业年报 | 年报 | `searchKey` · **`financialYear` 必传**（一次传 `--years` 个年度，最多 10 个，**禁止按年循环**） |

> **`--module` 非 `all` 时**：只调用对应 Tool，其余模块在报告中写「本次未调用」，**不得写「无记录」**。
> **`--module all` 纪律**：上述 13 个 Tool **各调用恰好 1 次**，与 `search_company` 合计 **14 次**，覆盖企业档案 Server 全集。

**调用预算**：`standard` = **14 次**（0901 企业档案 14 Tool 各 1 次）；集团双方向 `branches_headquarters` = **15 次**（额外 1 次，须声明）。

**并发纪律**：`search_company` 完成后，步骤 1 全部 Tool **同时发出**；失败不循环重试，该模块标「本次未核验」。

---

## 📖 企业档案 Server · 十四 Tool 全表（0901 字典 · 本 SKILL 唯一合法工具集）

| # | CDT MCP 工具 | 规范名 | 必传 `searchKey` | 主要输出字段（报告须覆盖） |
| --- | --- | --- | --- | --- |
| 1 | `search_company` | 企业检索 | 多类型关键词 | `unified_social_credit_code` · `company_chinese_name` · `company_status_chinese` · `match_score` |
| 2 | `search_company_registration` | 企业工商信息 | USCC/名称 | 登记状态 · 资本 · 期限 · 地址 · 经营范围 · 行业代码 · 联系方式 |
| 3 | `search_simple_deregistration` | 简易注销 | USCC/名称 | `announcement_period_start/end` · `review_result` · `deregistration_date` |
| 4 | `search_company_changes` | 变更记录 | USCC/名称 | `change_item` · `change_date` · 变更前后内容 |
| 5 | `search_shareholders` | 股东信息 | USCC/名称 | `shareholder_*` · `shareholding_ratio` · 认缴/实缴 |
| 6 | `search_controlling_shareholders` | 控股股东 | USCC/名称 | `result_status` · `control_category` · `direct_holding_ratio` · `final_shareholding_ratio_percent` · `holding_path` |
| 7 | `search_key_personnel` | 主要人员 | USCC/名称 | `key_person_*` · `position` · `is_legal_representative` · `is_in_office` |
| 8 | `search_beneficial_owners` | 受益所有人 | USCC/名称 | `beneficial_owner_name` · `bo_identification_mode/method` · `final_shareholding_ratio_percent` · `holding_path` · `identification_facts` |
| 9 | `search_actual_controllers` | 实际控制人 | USCC/名称 | `actual_controllers_name` · `actual_controllers_type` · `final_shareholding_ratio_percent` · `holding_path` |
| 10 | `search_company_investments` | 对外投资 | USCC/名称 | `invested_company_*` · `shareholding_ratio` · 认缴/实缴 · `contribution_date` |
| 11 | `search_branches` | 分支机构 | USCC/名称 | `branch_name` · `branch_credit_code` · `branch_status` · `is_historical` |
| 12 | `search_branches_headquarters` | 分支机构与总公司 | USCC/名称 | `relation_type` · 关联企业名称 · USCC · 负责人 |
| 13 | `search_icp_filing` | 企业网站 ICP 备案 | USCC/名称 | `website_name` · `domain_name` · `icp_filing_number` · `is_historical_filing` |
| 14 | `search_annual_reports` | 企业年报 | USCC/名称 + **`financialYear`** | `report_year` · 资产/负债/收入/利润 · 从业人数 · 股东出资摘要 |

> **禁止事项**：
> ❌ 不得调用上表以外的任何 CDT 工具——企业档案 Server **仅有以上 14 个 Tool**，本 SKILL 须**全部使用**（`--module all`）。
> ❌ 不得用其他 Server 工具「补充」本报告。
> ❌ **CDT 不提供批量查询**；多主体须循环本 SKILL，**N>5 时须报预估调用量**（约 `N×14` 次）。
> ❌ 不得输出评级、分流、准入结论或风险等级。

### 枚举速查（报告原值引用）

| 工具 | 枚举字段 | 常用值（0901） |
| --- | --- | --- |
| `search_beneficial_owners` | `bo_identification_mode` | STANDARD / SIMPLIFIED / ENHANCED / EXEMPTION |
| `search_beneficial_owners` | `bo_identification_method` | EQUITY / VOTING_CONTROL / ACTUAL_CONTROL / LEGAL_REPRESENTATIVE / … |
| `search_actual_controllers` | `actual_controllers_type` | AC_NATURAL_PERSON / AC_LEGAL_ENTITY / AC_OTHER / AC_NONE |
| `search_controlling_shareholders` | `result_status` | FOUND / NONE |
| `search_controlling_shareholders` | `control_category` | ABSOLUTE / RELATIVE / JOINT / NONE |
| `search_controlling_shareholders` | `shareholder_type` | NATURAL / LEGAL / PARTNERSHIP / OTHER / PASS_THROUGH |
| `search_branches_headquarters` | `relationshipType`（入参） | 1 查分支关联（默认）· 2 查总公司 |

---

# 企业信息核验 · D&B China Data MCP

## SKILL 定位

本 SKILL 回答：**这家企业在企业档案 Server 十四类公开记录中，登记、治理、投资、分支、备案与年报事实是什么。**

| 需求 | 使用 |
| --- | --- |
| 企业档案 14 Tool 全量底稿 | **本 SKILL** |
| 还要四维评估、司法、知产、D&B 评级 | → `dnb-counterparty-dd` |
| 还要准入红线与清单筛选 | → `dnb-risk-screening` |
| 还要两企业关联路径 | → `dnb-companies-relations` |

## MCP 依赖与配置

**唯一必选**

- `企业档案 Server` —— `https://mcp.dnbservice.com.cn/v1/company` · **14 Tool 全覆盖**

**降级策略**：单 Tool 失败 → 该模块写「本次未核验」；锚定失败 → **不输出任何核查结论**。

---

## 标准化输出契约（企业档案事实包）

```json
{
  "policy_version": "DNB_COMPANY_VERIFY_FACT_v1.0.0",
  "server": "企业档案",
  "tools_expected": 14,
  "entity": { "uscc": "<18位>", "name": "<登记名>", "anchor_match_score": "<原值|null>" },
  "coverage": {
    "modules_requested": ["registration","simple_deregistration","changes","shareholders","controlling_shareholders","key_personnel","beneficial_owners","actual_controllers","investments","branches","branches_headquarters","icp_filing","annual_reports"],
    "tools_called": [],
    "tools_failed": [],
    "tools_skipped": []
  },
  "summary": { "registration_status": "<原值>", "simple_dereg_review_result": "<原值|null>", "shareholder_count": 0, "ubo_count": 0, "icp_filing_count": 0, "annual_report_years": [] },
  "registration": {},
  "simple_deregistration": {},
  "changes": [],
  "shareholders": [],
  "controlling_shareholders": [],
  "key_personnel": [],
  "beneficial_owners": [],
  "actual_controllers": [],
  "investments": [],
  "branches": [],
  "branches_headquarters": [],
  "icp_filing": [],
  "annual_reports": [],
  "not_verified": [],
  "trace": [{ "tool": "search_company", "server": "企业档案", "request_id": "<id>", "timestamp": "ISO8601" }],
  "collected_at": "ISO8601"
}
```

**契约约束**：`tools_called.length` 在 `--module all` 成功时须为 **14**；不得出现 `grade` / `score` / `risk_level` / `decision`。

---

## 报告输出格式（严格填空骨架 · 模型只填值、不造结构）

> **使用约定**：以下是企业信息核验报告的**完整骨架**——标题层级、表头与列、章节顺序**全部固定**，模型只把 `{}` 占位替换为工具返回值，**禁止新增 / 删除章节、禁止改表列、禁止虚构接口未返回的字段**。报告正文用**业务语言**标注数据来源（如「邓白氏中国企业档案数据 · 工商登记」），**不写 MCP 工具代码名**（附录 A/B 除外）。**`--format html` 时章节与本骨架一致，见「HTML 交付规范」。**
>
> **核验逻辑顺序（市场惯例）**：主体锚定 → 工商登记与存续 → 治理链（股东→控股→实控→受益所有人→主要人员）→ 对外投资与分支网络 → 变更轨迹 → 年报披露 → 线上备案 → 跨模块互证 → 审计轨迹。
>
> **填写纪律**：① 数值逐字引用，禁自行加总 / 相乘穿透；② 已核验 / 未发现记录 / 未核验 三态严格区分；③ 互证矩阵只陈述可核对事实，**不下准入 / 风险 / 空壳等定性结论**；④ 各模块末尾「模块小结」仅复述本模块已填数据，不引入新数字。

```markdown
# 企业信息核验报告

## {企业完整登记名}

| 项目 | 内容 |
| --- | --- |
| **核验对象** | {完整登记名} |
| **统一社会信用代码** | {18 位 USCC} |
| **报告类型** | 企业档案全量核验（14 数据源） |
| **工商登记状态** | {company_status_chinese 原值} |
| **法定代表人** | {legal_rep_chinese_name 原值} |
| **集团内定位** | {独立主体 / 母公司 / 分公司 / 待厘清 · 依据分支关系模块} |
| **二要素一致性** | {一致 / 不一致 · 已终止} |
| **数据覆盖** | {14/14 已核验 / N/14 · 未核验模块逐项列名} |
| **报告生成时间** | YYYY-MM-DD HH:MM:SS |
| **审计留档编号** | COVF-{USCC}-{YYYYMMDD} |
| **事实版本** | DNB_COMPANY_VERIFY_FACT_v1.0.0 |

---

## 执行摘要

> **核验概述（1–2 句）：** {主体是否可锚定、登记状态、治理链是否完整取数、有无简易注销公告、年报覆盖年度、互证是否存在明显不一致 · 仅陈述事实}

### 关键指标一览

| 指标 | 取值 | 数据来源 | 核验状态 |
| --- | --- | --- | --- |
| 成立日期 | {establishment_date} | 工商登记 | {✓ / —} |
| 注册资本 | {registered_capital} {registered_capital_currency} | 工商登记 | {✓ / —} |
| 实缴资本 | {paid_in_capital} {paid_in_capital_currency} | 工商登记 | {✓ / —} |
| 股东数量 | {N 名 / 未发现} | 股东信息 | {✓ / ○ / —} |
| 控股股东 | {名称 · 控制类别原值 / 未识别} | 控股股东 | {✓ / ○ / —} |
| 实际控制人 | {名称 · 类型原值 / 未识别} | 实际控制人 | {✓ / ○ / —} |
| 受益所有人 | {N 名 / 未发现} | 受益所有人 | {✓ / ○ / —} |
| 主要人员（在任） | {N 名 / 未发现} | 主要人员 | {✓ / ○ / —} |
| 对外投资 | {N 家 / 未发现} | 对外投资 | {✓ / ○ / —} |
| 分支机构 | {N 家 · 含历史 N 家 / 未发现} | 分支机构 | {✓ / ○ / —} |
| 变更记录 | {近 36 个月 N 条 / 未发现} | 变更记录 | {✓ / ○ / —} |
| 简易注销 | {有公告 / 未发现} | 简易注销 | {✓ / ○ / —} |
| ICP 备案 | {N 条 · 有效 N 条 / 未发现} | ICP 备案 | {✓ / ○ / —} |
| 企业年报 | {YYYY、YYYY、YYYY / 部分年度未披露} | 企业年报 | {✓ / ○ / —} |

> **状态图例：** ✓ 已核验且有返回 · ○ 已核验但 0 条 · — 本次未核验

### 模块核验进度

| 序号 | 核验模块 | 记录概况 | 状态 |
| --- | --- | --- | --- |
| 1 | 主体锚定 | {match_score · 命中条数} | {✓ / —} |
| 2 | 工商登记信息 | {登记状态原值} | {✓ / —} |
| 3 | 简易注销 | {N 条 / 未发现} | {✓ / ○ / —} |
| 4 | 股东信息 | {N 名股东} | {✓ / ○ / —} |
| 5 | 控股股东 | {FOUND/NONE 等原值} | {✓ / ○ / —} |
| 6 | 实际控制人 | {N 名 / 未发现} | {✓ / ○ / —} |
| 7 | 受益所有人 | {N 名 / 未发现} | {✓ / ○ / —} |
| 8 | 主要人员 | {N 名 · 在任 N 名} | {✓ / ○ / —} |
| 9 | 对外投资 | {N 家} | {✓ / ○ / —} |
| 10 | 分支机构 | {N 家} | {✓ / ○ / —} |
| 11 | 分支/总公司关系 | {关系类型原值} | {✓ / ○ / —} |
| 12 | 变更记录 | {N 条} | {✓ / ○ / —} |
| 13 | 企业年报 | {N 个年度} | {✓ / ○ / —} |
| 14 | ICP 备案 | {N 条} | {✓ / ○ / —} |

**档案层观察（事实绑定 · 非定性结论）：** {仅列可核对事实，如「存在简易注销公告且 review_result 为…」「法定代表人于变更记录中出现 N 次变更」「年报披露从业人数与…不一致」等；禁止写「高风险 / 建议拒绝」}

**建议后续动作（事实触发 · 非准入结论）：** {如「简易注销公告存在 → 建议转 dnb-risk-screening 核查退出信号」「互证不一致项 → 建议人工核对客户申报材料」/ 无}

---

## 1 核验说明

### 1.1 核验范围与数据来源

| 数据域 | 业务来源 | 采集时间 | 时效说明 |
| --- | --- | --- | --- |
| 企业检索与工商登记 | 邓白氏中国企业档案数据 · 工商类 | YYYY-MM-DD | 一般 T+3 |
| 股权 / 治理 / 投资 / 分支 | 邓白氏中国企业档案数据 · 治理类 | YYYY-MM-DD | 一般 T+3 |
| 变更记录 | 邓白氏中国企业档案数据 · 变更类 | YYYY-MM-DD | 一般 T+3 |
| 简易注销 | 邓白氏中国企业档案数据 · 退出类 | YYYY-MM-DD | 一般 T+3 |
| 企业年报 | 邓白氏中国企业档案数据 · 年报类 | YYYY-MM-DD | 按 `--years` 年度 |
| ICP 备案 | 邓白氏中国企业档案数据 · 备案类 | YYYY-MM-DD | 一般 T+3 |

**本次未覆盖（须其他 SKILL）：** 司法 / 监管处罚 / 信用评级 / 知产 / 两主体关联路径 / 跨境事实 —— 本报告**不包含**上述数据域。

### 1.2 主体锚定与二要素核验

| 项目 | 内容 |
| --- | --- |
| 检索关键词 | {用户输入 / 锚定用 searchKey} |
| 检索方式 | {精准 / 模糊} |
| 命中主体数 | {N 条 · 已确认第 M 条 / 唯一命中} |
| 锚定 USCC | {18 位} |
| 锚定登记名 | {company_chinese_name} |
| 匹配度 | {match_score 原值} |
| 用户申报 USCC（如有） | {18 位 / 未提供} |
| 二要素比对 | {名称一致且 USCC 一致 / 不一致项：…} |
| 锚定结论 | {可继续核验 / 已终止} |

### 1.3 互证逻辑说明

本报告在数据取数完成后，对以下**可自动化核对项**做交叉比对（仅陈述一致 / 不一致 / 无法比对，不做风险评级）：

| 互证项 | 比对来源 A | 比对来源 B | 判定规则 |
| --- | --- | --- | --- |
| 企业名称 | 主体锚定 | 工商登记 | 字符串一致为「一致」 |
| 统一社会信用代码 | 用户申报 / 锚定 | 工商登记 | 18 位一致为「一致」 |
| 法定代表人 | 工商登记 | 主要人员（is_legal_representative=是 且在任） | 姓名一致为「一致」 |
| 法定代表人（年报） | 工商登记 | 最新年度年报 | 姓名一致为「一致」 |
| 注册地址 | 工商登记 | 最新年度年报通信地址 | 一致 / 不一致 / 年报未披露 |
| 企业电话 | 工商登记 | 最新年度年报 | 一致 / 不一致 / 任一侧未披露 |
| 股东 ↔ 控股股东 | 股东名册 | 控股股东模块 | 控股股东姓名出现在股东表为「可对应」 |
| 实控人 ↔ 受益所有人 | 实际控制人 | 受益所有人 | 姓名交集列示，不推断代持 |
| 年报「是否有投资」 | 最新年报 has_investment | 对外投资条数 | Y 且 N≥1 / Y 且 N=0 / N 等原值组合 |
| 年报「是否有网站」 | 最新年报 has_website_or_outlet | ICP 备案条数 | 同上 |

---

## 2 工商登记与存续状态

### 2.1 基础登记信息

| 字段 | 内容 |
| --- | --- |
| 企业名称（中文） | {company_chinese_name} |
| 企业名称（英文） | {company_english_name / 未披露} |
| 统一社会信用代码 | {unified_social_credit_code} |
| 注册号 | {registration_number / 未披露} |
| 组织机构代码 | {organization_code / 未披露} |
| 企业类型 | {company_type_chinese} |
| 登记状态 | {company_status_chinese} |
| 成立日期 | {establishment_date} |
| 核准日期 | {approval_date / 未披露} |
| 营业期限 | {business_term_start} 至 {business_term_end / 长期} |
| 注销日期 | {deregistration_date / 未披露} |
| 吊销日期 | {revocation_date / 未披露} |
| 登记机关 | {registration_authority_chinese} |
| 注册资本 | {registered_capital} {registered_capital_currency} |
| 认缴资本 | {subscribed_capital} {subscribed_capital_currency / 未披露} |
| 实缴资本 | {paid_in_capital} {paid_in_capital_currency / 未披露} |
| 国标行业代码 | {gb_industry_code / 未披露} |
| SIC 代码 | {sic_code / 未披露} |
| 数据更新时间 | {update_time / 未披露} |

### 2.2 地址与联系方式

| 字段 | 内容 |
| --- | --- |
| 注册地址 | {company_address_chinese} |
| 省 / 市 / 区 | {address_province_chinese} / {address_city_chinese} / {address_district_chinese} |
| 邮政编码 | {address_postal_code / 未披露} |
| 企业电话 | {company_phone / 未披露} |
| 企业网址 | {company_website / 未披露} |
| 企业邮箱 | {company_email / 未披露} |

### 2.3 经营范围

{完整引用 business_scope 原文，不截断}

### 2.4 简易注销核查

| 序号 | 公告期起 | 公告期止 | 审核结果 | 注销日期 | 登记机关 |
| --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} |

{0 条时整表替换为一句：「本次未发现简易注销公告记录。」}

**模块小结：** {仅复述登记状态 + 简易注销有无，不评价风险}

---

## 3 股权结构与治理链

> **阅读顺序：** 股东名册 → 控股股东 → 实际控制人 → 受益所有人 → 主要人员 → 治理链互证

### 3.1 股东名册（共 N 名）

| 序号 | 股东名称 | 股东类型 | 股东 USCC | 国籍/注册地 | 持股比例 | 认缴金额 | 实缴金额 | 出资方式 | 出资日期 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} | {} {} | {} {} | {} | {} |

{0 条：「本次未发现股东公开记录。」}

### 3.2 控股股东

| 序号 | 控股股东 | 股东类型 | 识别状态 | 控制类别 | 直接持股 | 总持股比例 | 识别路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} | {} | {} |

{result_status=NONE 或 0 条：「本次未识别到控股股东记录。」}

### 3.3 实际控制人

| 序号 | 实际控制人 | 类型 | 总持股比例 | 识别路径 |
| --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} |

{0 条：「本次未发现实际控制人公开记录。」}

### 3.4 受益所有人

| 序号 | 受益所有人 | 识别模式 | 识别方式 | 总持股比例 | 识别路径 | 识别事实 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} | {} |

{0 条：「本次未发现受益所有人公开记录。」}

> 总持股比例、识别路径**逐字引用接口** `final_shareholding_ratio_percent` / `holding_path`，禁止自行穿透相乘。

### 3.5 主要人员（共 N 名 · 在任 N 名）

| 序号 | 姓名 | 职务 | 是否法定代表人 | 是否在职 | 国籍 |
| --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} |

{0 条：「本次未发现主要人员公开记录。」}

### 3.6 治理链互证

| 互证项 | 结果 | 说明（逐字引用差异字段） |
| --- | --- | --- |
| 法定代表人：工商 vs 主要人员 | {一致 / 不一致 / 无法比对} | {} |
| 法定代表人：工商 vs 最新年报 | {一致 / 不一致 / 无法比对} | {} |
| 控股股东是否在股东名册 | {可对应 / 未出现 / 无法比对} | {} |
| 实控人与受益所有人姓名交集 | {列示姓名 / 无交集 / 无法比对} | {} |
| 主要人员与股东自然人重名 | {列示 / 无 / 无法比对} | {} |

**治理链小结：** {4–6 句业务语言，仅基于上表；如「控股股东为 X，总持股 Y%（接口原值）；受益所有人 N 名；法定代表人 Z 在主要人员表中在任」}

---

## 4 对外投资（共 N 家）

| 序号 | 被投资企业 | 被投 USCC | 持股比例 | 认缴出资 | 实缴出资 | 出资方式 | 出资日期 | 被投法人 | 被投状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} {} | {} {} | {} | {} | {} | {} |

{0 条：「本次未发现对外投资公开记录。」}

**模块小结：** {}

---

## 5 分支机构与集团关系

### 5.1 分支机构清单（共 N 家 · 当前 N 家 · 历史 N 家）

| 序号 | 分支机构名称 | 分支 USCC | 负责人 | 状态 | 成立日期 | 地址 | 是否历史 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} | {} | {} |

{0 条：「本次未发现分支机构公开记录。」}

### 5.2 与总公司 / 分支机构关系

| 序号 | 关系类型 | 关联企业名称 | 关联 USCC | 负责人 |
| --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} |

{0 条：「本次未发现分支/总公司关联记录。」}

**集团定位结论（事实）：** {本主体为独立主体 / 存在 N 家分支 / 存在总公司关联 · 名称原值}

---

## 6 变更记录

### 6.1 变更统计

| 统计项 | 数值 |
| --- | --- |
| 变更总条数 | {N / 0} |
| 近 12 个月 | {N 条} |
| 近 24 个月 | {N 条} |
| 近 36 个月 | {N 条} |
| 高频变更事项（Top 3） | {change_item · 次数} |

> 统计仅对**已返回变更条数**做计数排序，禁止推断未返回区间。

### 6.2 变更明细（按 change_date **降序**）

| 序号 | 变更日期 | 变更事项 | 变更前 | 变更后 |
| --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} |

{0 条：「本次未发现公开变更记录。」}

**模块小结：** {}

---

## 7 企业年报

### 7.1 年报披露概况

| 报告年度 | 披露状态 | 经营状态 | 从业人数 | 是否有投资 | 是否有网站 | 最新年报日期 |
| --- | --- | --- | --- | --- | --- | --- |
| {YYYY} | {已取数 / 未披露} | {} | {} | {} | {} | {} |
| {YYYY} | {} | {} | {} | {} | {} | {} |
| {YYYY} | {} | {} | {} | {} | {} | {} |

### 7.2 多期财务与规模对比

| 指标 | {YYYY} | {YYYY} | {YYYY} | 备注 |
| --- | --- | --- | --- | --- |
| 资产总额 | {} | {} | {} | 逐字引用 |
| 负债总额 | {} | {} | {} | 逐字引用 |
| 所有者权益合计 | {} | {} | {} | 逐字引用 |
| 营业总收入 | {} | {} | {} | 逐字引用 |
| 利润总额 | {} | {} | {} | 逐字引用 |
| 净利润 | {} | {} | {} | 逐字引用 |
| 从业人数 | {} | {} | {} | 逐字引用 |

{某年度无数据时该格写「未披露」，禁止用相邻年度插值}

### 7.3 各年度明细

#### {YYYY} 年度报告

**基本信息**

| 字段 | 内容 |
| --- | --- |
| 法定代表人 | {} |
| 通信地址 | {} |
| 主营业务 | {} |
| 控股类型 | {} |

**股东及出资信息**（来自 annual_report_capital_contribution · 有则列表，无则写未发现）

**股权变更信息**（来自 annual_report_equity_changes · 有则列表）

**年报修改记录**（来自 annual_report_change_records · 有则列表）

{每个 `--years` 年度重复 §7.3 小节}

### 7.4 年报互证

| 互证项 | 结果 | 说明 |
| --- | --- | --- |
| 年报从业人数 vs 工商登记 | {一致 / 不一致 / 无法比对} | {} |
| 年报 has_investment vs 对外投资条数 | {见 §1.3 规则} | {} |
| 年报 has_website vs ICP 条数 | {见 §1.3 规则} | {} |

**模块小结：** {}

---

## 8 企业网站 ICP 备案（共 N 条 · 有效 N 条 · 历史 N 条）

| 序号 | 网站名称 | 域名 | ICP 备案号 | 审核/备案日期 | 是否历史备案 |
| --- | --- | --- | --- | --- | --- |
| 1 | {} | {} | {} | {} | {} |

{0 条：「本次未发现 ICP 备案公开记录。」}

**模块小结：** {}

---

## 9 跨模块互证总表

| 序号 | 互证项 | 结果 | 涉及模块 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 二要素（名称 + USCC） | {} | 锚定 · 工商 | {} |
| 2 | 法定代表人三方比对 | {} | 工商 · 人员 · 年报 | {} |
| 3 | 注册地址 vs 年报地址 | {} | 工商 · 年报 | {} |
| 4 | 股东 ↔ 控股股东 | {} | 股东 · 控股 | {} |
| 5 | 实控人 ↔ 受益所有人 | {} | 实控 · 受益 | {} |
| 6 | 投资意愿 vs 投资事实 | {} | 年报 · 投资 | {} |
| 7 | 网站意愿 vs ICP 事实 | {} | 年报 · ICP | {} |
| 8 | 登记状态 vs 简易注销 | {} | 工商 · 简易注销 | {} |

**互证小结：** {一致 N 项 · 不一致 N 项 · 无法比对 N 项 — 仅计数已填行，不评级}

---

## 10 数据覆盖与核验轨迹

### 10.1 数据源调用清单

| 序号 | 数据域 | 规范名称 | 调用状态 | 返回条数 / 说明 |
| --- | --- | --- | --- | --- |
| 1 | 企业检索 | 企业检索 | {成功 / 失败 / 跳过} | {锚定} |
| 2 | 工商登记 | 企业工商信息 | {} | {} |
| 3 | 退出信号 | 简易注销 | {} | {} |
| 4 | 股东 | 股东信息 | {} | {} |
| 5 | 控股 | 控股股东 | {} | {} |
| 6 | 实控 | 实际控制人 | {} | {} |
| 7 | 受益 | 受益所有人 | {} | {} |
| 8 | 人员 | 主要人员信息 | {} | {} |
| 9 | 投资 | 对外投资 | {} | {} |
| 10 | 分支 | 分支机构 | {} | {} |
| 11 | 集团 | 分支机构与总公司 | {} | {} |
| 12 | 变更 | 变更记录 | {} | {} |
| 13 | 年报 | 企业年报 | {} | {} |
| 14 | 备案 | 企业网站 ICP 备案 | {} | {} |

### 10.2 审计轨迹

| 序号 | 数据域 | 请求标识 | 采集时间 |
| --- | --- | --- | --- |
| 1 | {} | {request_id} | {ISO8601} |

---

## 附录 A · 数据采集清单（技术留档）

| 序号 | MCP Tool | Server | 入参摘要 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | search_company | 企业档案 | searchKey={} · searchType={} | {} |
| 2–14 | {各 Tool 名} | 企业档案 | searchKey={USCC} · {其他入参} | {} |

## 附录 B · 机器可读事实包

{`--format json` 时输出完整 JSON；md/html 模式下嵌入或折叠输出 DNB_COMPANY_VERIFY_FACT_v1.0.0 事实包}

---

## 数据来源与免责声明

**数据来源：** D&B China Data · 企业档案 Server（0901 字典 · 14 Tool 全覆盖）。  
**报告性质：** 本报告为基于公开工商登记与企业档案数据的**事实核验材料**，不构成任何形式的准入审批、授信建议、投资意见或「无风险」保证。  
**局限说明：** 受益所有人与实际控制人识别基于公开股权信息；未披露的代持、协议控制、一致行动安排无法穿透。互证「不一致」仅表示数据源之间字段差异，需结合客户申报材料人工复核。  
**升级路径：** 需司法 / 监管 / 评级 / 关联路径 → 请使用 `dnb-risk-screening` · `dnb-counterparty-dd` · `dnb-companies-relations` 等决策层 SKILL。
```

---

## 参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--uscc <18 位>` | 二要素一致性核验 | 无 |
| `--years <N>` | `search_annual_reports.financialYear` 年度个数（≤10） | `3` |
| `--module` | `all` = 14 Tool 全调；或 `registration` · `simple_dereg` · `changes` · `shareholders` · `controlling` · `personnel` · `ubo` · `controller` · `investments` · `branches` · `branches_hq` · `icp` · `annual` | `all` |
| `--format <md\|json\|html>` | `json` 仅输出事实包 | `md` |

---

## HTML 交付规范（`--format html`）

通用规则见 `README-dnb-skills.md` §3.8。本 SKILL 补充：

1. **完整渲染**「企业信息核验报告」骨架：§ 执行摘要 → §10 数据覆盖，**14 行数据源清单不得省略**；附录 A/B 按需折叠。
2. **版式（自包含 CSS · 无外链）**：
   - **页眉区**：`<header class="report-header">` — 报告标题 + 企业名称 + USCC + 留档编号 + 生成时间，深蓝底 `#1a365d`、白字。
   - **摘要卡**：关键指标一览用 `<div class="metric-grid">` 四列卡片（成立 / 资本 / 治理 / 网络），每卡含指标名 + 数值 + 状态徽章。
   - **状态徽章**：`.badge-ok` 绿（✓ 已核验）· `.badge-empty` 灰（○ 未发现）· `.badge-skip` 橙（— 未核验）。
   - **表格**：全宽 `<table class="data-table">`，`<thead>` 浅灰底 `#f7fafc`，斑马纹偶数行 `#fafafa`，单元格 `padding: 8px 12px`，长文本 `word-break: break-all`。
   - **章节标题**：`<h2>` 左侧 4px 色条 `#3182ce`；`<h3>` 常规加粗。
   - **治理链**：§3 顶部可选 `<div class="chain-flow">` 横向步骤条（股东 → 控股 → 实控 → 受益 → 人员），仅展示模块名与条数，不手绘股权图。
   - **互证矩阵**：§9 中「不一致」行用 `.row-warn` 浅黄底 `#fffbeb` 高亮，**不得**写「高风险」字样。
   - **页脚**：免责声明 + 事实版本 + 页码（CSS `@page` 或 footer 固定）。
3. **`--format html` 与 `json` 互斥**；事实包见附录 B，默认不重复嵌入 HTML 正文。
4. HTML 与 md **同源同值**：不得因美化而省略 0 条模块、未核验行或互证「无法比对」行。

---

## 报告输出纪律（内部规则 · 严禁抄入报告）

1. **`--module all` 必须 14 Tool 各 1 次**，不得遗漏 ICP 备案 / 简易注销。
2. **一律业务语言**：正文不写 MCP 工具名 / Server 名 / 字段名；附录 A 为唯一工具名例外。
3. **禁止**调用企业档案以外 Tool；**禁止**评级、分流、准入、空壳认定等定性结论。
4. `final_shareholding_ratio_percent` / `holding_path` **只引原值**，禁止逐层相乘。
5. 未调用模块写「本次未核验」，成功 0 条写「本次未发现公开记录」，**二者不得混用**。
6. 互证矩阵只输出一致 / 不一致 / 无法比对，**不得**将不一致自动升级为风险等级。
7. 禁止过程独白（「我将调用…」「第一步…」），直接输出报告正文。
8. 本节及全部内部执行规则**严禁抄入报告**。

---

**SKILL 版本**：v1.0.0  
**所需 Server**：企业档案（唯一 · 14 Tool · `https://mcp.dnbservice.com.cn/v1/company`）  
**事实版本**：`DNB_COMPANY_VERIFY_FACT_v1.0.0`  
**对齐规范**：D&B China Data MCP Skills BRD v1.0 · 《主题化中国数据-MCP 服务 0901》企业档案 Server 全表
