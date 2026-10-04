---
name: 企百科
name_en: qibook
description: 查询企业工商登记及相关尽调数据，涵盖主体识别、基本信息、股权与控制关系、变更、人员与组织、年报及上市信息。当用户提及企百科、qibook、工商查询、查企业、企业尽调、企业股东、企业法人、受益所有人、实际控制人、企业年报或上市公司信息时使用；不用于征信评分、司法涉诉或税务查询。
allowed-tools:
  - fuzzy_search
  - get_company_info
  - get_beneficial_owners
  - get_actual_controller
  - get_company_partner
  - get_pub_shareholder
  - get_self_disclose_share
  - get_company_changes
  - get_history_dynamic
  - get_company_contact
  - get_company_employee
  - get_branches
  - get_external_investments
  - get_annual_reports
  - get_listed_stock
  - get_pub_executive
  - get_listed_compinfo
  - get_head_company
  - scale_classification
  - get_company_introduction
source: qibook-mcp
type: mcp
auth_mode: gateway
---

# 企百科（qibook）企业工商数据查询连接器

## 1. 连接器定位

企百科用于查询企业工商登记及相关尽调数据，提供企业主体识别、工商基本信息、股权与控制关系、变更沿革、组织人员和上市信息等能力。本 Skill 定义工具选择、主体定位、异常处理和结果组织规则。

MCP 服务配置以连接器根目录的 `mcp.json` 为唯一准则，不在本文件中重复维护。

## 2. 适用场景与路由判断

当用户需要查询以下企业工商信息或相关尽调数据时使用：

- **企业身份识别**：按名称关键词模糊搜索企业 → `fuzzy_search`
- **工商基础信息**：注册资本、经营状态、法定代表人、成立日期、经营范围 → `get_company_info`
- **股权穿透**：股东、受益所有人(UBO)、实际控制人、自主公示股东、公开披露股东 → `get_company_partner` / `get_beneficial_owners` / `get_actual_controller` / `get_self_disclose_share` / `get_pub_shareholder`
- **变更沿革**：工商变更记录、历史工商动态 → `get_company_changes` / `get_history_dynamic`
- **组织与人员**：联系方式、主要人员(董监高)、分支机构、对外投资、总公司 → `get_company_contact` / `get_company_employee` / `get_branches` / `get_external_investments` / `get_head_company`
- **年报与简介**：企业年报、企业简介 → `get_annual_reports` / `get_company_introduction`
- **上市信息**：上市股票、公开披露股东、上市高管、上市公司基本信息 → `get_listed_stock` / `get_pub_shareholder` / `get_pub_executive` / `get_listed_compinfo`
- **规模划型**：企业规模及行业门类 → `scale_classification`

> 边界：本连接器仅查询工商登记/尽职调查数据，不处理企业征信评分、司法涉诉、税务等非工商数据；此类需求应转其他数据源。

## 3. 标准工作流

### 3.1 主体定位

- 用户只提供企业名称或关键词时，先调用 `fuzzy_search`，再使用返回的企业名称调用后续工具。
- 用户已提供下游工具所需的有效企业名称时，可跳过模糊搜索；参数名称和格式以工具 schema 为准。
- 搜索结果可以唯一确定主体时，继续查询；存在多个候选时，结合企业全称、统一社会信用代码、地区、经营状态等信息判断。仍无法唯一确定时，列出精简候选项请用户确认，不得自行猜测。
- 未搜索到匹配企业时，说明当前未找到匹配结果，并请用户补充更准确的企业名称或统一社会信用代码；不要继续调用深层查询工具。

### 3.2 按需求组合调用
主体确定后，根据用户问题从第 2 节选择工具。相互独立且使用同一已确认主体的查询可以并行；依赖前一工具结果的查询应按顺序执行。严格遵循工具 schema，不得猜测参数名、标识类型或必填值。

以下示例假设用户只提供企业名称：

- "查询 XX 的法人信息" → `fuzzy_search` → `get_company_info`（法定代表人字段）
- "查询 XX 的工商基本信息和股东" → `fuzzy_search` → 并行调用 `get_company_info`、`get_company_partner`
- "查询 XX 的对外投资以及高管信息" → `fuzzy_search` → 并行调用 `get_external_investments`、`get_company_employee`
- "XX 的上市股票、股东和高管" → `fuzzy_search` → 并行调用 `get_listed_stock`、`get_pub_shareholder`、`get_pub_executive`

### 3.3 结果组织
先直接回答用户问题，再提供必要明细。单一事实使用简短文本；多条同类记录或需要横向比较时使用表格。明确本次查询对应的企业主体，并保留工具返回的单位、日期、状态、数据口径和来源；工具未提供的信息不得补写或推断。

### 3.4 无数据与失败处理

- 区分"未查询到记录""字段未披露"和"工具调用失败"，不要将空值或调用失败表述为企业不存在或相关事项不存在。
- 工具调用失败时，可在不改变查询条件的情况下重试一次；仍失败则说明失败工具及未能获取的内容。
- 组合查询部分成功时，先返回已获得的结果，并单独列明失败或无数据的部分，不因单项失败丢弃全部结果。

## 4. 工具清单（allowed-tools）

| 工具名称 | 中文名称 | 功能描述 |
|---|---|---|
| `fuzzy_search` | 企业模糊搜索 | 根据企业名称关键词模糊搜索匹配企业 |
| `get_company_info` | 企业基本信息 | 企业名称、统一社会信用代码、法定代表人、注册资本、经营状态、成立日期等工商基本信息 |
| `get_beneficial_owners` | 受益所有人结果 | 查询企业受益所有人(UBO)信息，适用于反洗钱合规(AML)、尽职调查及穿透式监管分析 |
| `get_actual_controller` | 疑似实际控制人查询 | 查询在营企业的疑似实际控制人信息（名称、类型），适用于实控人判定、风险评估、KYC |
| `get_company_partner` | 企业股东信息 | 股东名称、股东类型、认缴出资额、出资比例等，适用于股权结构分析 |
| `get_pub_shareholder` | 公开披露股东名单 | 上市公司公开披露股东名单，适用于股东结构分析、大股东识别 |
| `get_self_disclose_share` | 自主公示股东 | 企业自主公示股东详情，含认缴/实缴出资、股东类型、出资合计 |
| `get_company_changes` | 变更信息 | 工商变更记录（变更日期、事项、变更前后内容） |
| `get_history_dynamic` | 历史工商动态信息 | 法定代表人、经营状态变更等动态记录，用于经营沿革核查 |
| `get_company_contact` | 企业联系方式 | 联系邮箱列表、联系电话列表 |
| `get_company_employee` | 主要人员信息 | 董监高信息（姓名、职位、最近任职日期） |
| `get_branches` | 分支机构 | 分支机构名称、成立日期、负责人、经营状态、省份 |
| `get_external_investments` | 对外投资 | 被投企业名称、类型、投资数额/比例、投资方式、是否上市 |
| `get_annual_reports` | 企业年报基本信息 | 年报年份、从业人数、经营状态、主营业务活动、是否有投资信息 |
| `get_listed_stock` | 上市股票信息 | 股票代码、证券简称、证券类型、总股本、上市日期/状态/市场/板块 |
| `get_pub_executive` | 上市高管信息 | 高管姓名、职位、职位类型、简历、当前状态、在职起始日期 |
| `get_listed_compinfo` | 上市公司基本信息 | 上市企业基础资料（名称、资质、人员、资本、地址、经营范围等） |
| `get_head_company` | 总公司信息 | 企业所属总公司信息 |
| `scale_classification` | 规模划型信息 | 企业规模结果及行业门类/大类/中类/小类 |
| `get_company_introduction` | 企业简介 | 企业简介文本，用于快速了解主营业务与发展概况 |

## 5. 调用约束

- 仅将本连接器用于合法合规的企业信息查询，并只呈现回答用户问题所需的数据；避免无关扩散联系方式或个人信息。
- 涉及实际控制人、受益所有人等敏感结论时，保留工具返回的"疑似"等限定词，区分数据事实与推断，不将结果表述为确定的法律、审计或合规结论。
- 查询结果反映工具在本次查询时返回的信息，可能存在更新延迟、字段缺失或覆盖范围限制；不得将其描述为完整、实时或穷尽性数据，除非工具结果明确说明。
- 对征信评分、司法涉诉、税务等超出能力边界的请求，明确说明本连接器无法查询该部分，不得用工商字段替代推断。
