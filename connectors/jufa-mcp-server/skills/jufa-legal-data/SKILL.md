---
name: jufa-legal-data
description: 使用聚法法律数据智能服务检索司法案例、法律法规、检察文书、合同模板、招投标、企业信息及相关风险，并按结果标识读取详情。
version: 1.0.0
author: 聚法科技（长春）有限公司
---

# 聚法法律数据智能服务

## 适用场景

当用户需要查询中国司法案例、法律法规、检察文书、合同模板、招投标、企业工商信息、诉讼与执行风险、商标、专利、司法拍卖、开庭公告或行政处罚时使用本 Skill。

本 Connector 对外提供 36 个已上线工具。案例聚合、法规聚合和法规向量法条检索尚未上线，不得声称或尝试调用这些能力。

## 鉴权与费用

- 用户需先在 <https://www.jufaai.com/agent/profile> 获取聚法 API Key，并在 WorkBuddy Connector 配置页填写。
- API Key 失效或疑似泄露时，在聚法平台重新生成，回到 WorkBuddy 更新后断开并重新连接本 Connector。
- 工具调用可能消耗聚法账户积分。只在用户意图明确时调用，避免无意义的重复检索、深度翻页和批量详情读取。
- 不在回答、日志、文件或工具参数中复述 API Key。

## 通用调用规则

1. 优先调用搜索工具定位记录，再把搜索结果中的 `case_uuid`、`law_uuid`、`uuid`、`rowkey` 或 `company_id` 传给对应详情工具。
2. 默认从 `page=1` 开始，除非用户要求更多结果，否则使用较小的 `page_size`。
3. 日期范围的开始和结束参数应成对传入，日期格式使用 `YYYY-MM-DD`。
4. 不虚构筛选 ID。用户只给中文名称且工具支持名称参数时，优先使用名称参数；否则先做普通关键词检索。
5. 搜索结果属于候选。正式引用案例、法规或文书正文前，应读取详情并核对标题、案号、效力状态、发布日期和正文。
6. 返回空结果时，先放宽筛选或缩短关键词；不要自动进行大量相似调用。

## 工具清单

### 司法案例与法规

| 工具 | 用途与返回 | 参数 |
|---|---|---|
| `jufa_case_search_cases` | 搜索案例，返回列表、摘要及 `case_uuid` | 必填：`keyword`。可选：`page`、`page_size`、`court_name`、`court_id`、`court_level_id`、`case_type_id`、`case_level_id`、`reason_id`、`reason_name`、`region_id`、`region_name`、`year_id`、`judge_name`、`party_name`、`lawyer_name`、`lawoffice_name`、`judgement_id`、`judgement_timestamp_id`、`round_id`、`circuit_id`、`special_id`、`special_court_name`、`result_type_id`、`textlen_range_id`、`lxqj_id`、`ajtz_id`、`zyjd_id`、`typeKey`、`sign_type`、`sort_type`、`filters` |
| `jufa_case_get_case_detail` | 读取案例摘要、分段正文及引用法规 | `case_uuid`、`case_no`至少一个；可选`keyword`用于高亮 |
| `jufa_law_search_laws` | 搜索法规，返回列表、摘要及 `law_uuid` | 必填：`keyword`。可选：`page`、`page_size`、`area_id`、`area_name`、`xljb_id`、`xljb_name`、`lawxljb_id`、`unit_id`、`unit_name`、`sxx_id`、`year_id`、`publish_date_start`、`publish_date_end`、`effect_date_start`、`effect_date_end`、`typeKey`、`sign_type`、`sort_type`、`filters` |
| `jufa_law_get_law_detail` | 读取法规基础信息和分段法条正文 | `law_uuid`、`title`至少一个；可选`keyword`仅返回命中法条分段 |

### 检察文书

| 工具 | 用途与返回 | 参数 |
|---|---|---|
| `jufa_jcws_search_jcws` | 搜索检察文书，返回列表、摘要及 `case_uuid` | 必填：`keyword`。可选：`page`、`page_size`、`case_level_id`、`judgement_id`、`reason_id`、`year_id`、`typeKey`、`sign_type`、`sort_type`、`filters` |
| `jufa_jcws_get_jcws_detail` | 读取检察文书摘要、分段正文及引用法规 | 必填：`case_uuid`。可选：`keyword` |

### 合同模板与招投标

| 工具 | 用途与返回 | 参数 |
|---|---|---|
| `jufa_contract_search_contracts` | 搜索合同模板，返回摘要及 `uuid` | 必填：`keyword`。可选：`page`、`page_size`、`kind_id`、`parent_agg_id`、`is_gov`、`year_range_id`、`textlen_range_id`、`sort_type`、`filters` |
| `jufa_contract_get_contract_detail` | 读取合同模板基础信息和分段正文 | 必填：`uuid` |
| `jufa_tender_search_tenders` | 搜索招标信息，返回标题、采购人、代理机构及 `uuid` | 必填：`keyword`。可选：`page`、`page_size`、`province`、`city`、`main_type`、`notice_type_sub`、`publish_start_time`、`publish_end_time` |
| `jufa_tender_get_tender_detail` | 读取招标信息摘要和正文 | 必填：`uuid` |
| `jufa_tender_get_tender_related` | 按关键词扩展相关招标信息 | 必填：`keyword`。可选参数同招标搜索工具 |

### 企业信息与企业风险

企业详情类工具优先使用 `jufa_company_search_companies` 返回的加密 `company_id`。除搜索工具外，以下工具均支持以 `company_id` 或统一社会信用代码 `credit_code` 定位企业，二者至少提供一个。

| 工具 | 用途与返回 | 其他参数 |
|---|---|---|
| `jufa_company_search_companies` | 搜索企业并返回基础信息和 `company_id` | 必填：`keyword`；可选：`page`、`page_size`、`sort` |
| `jufa_company_get_company_profile` | 企业顶部名片、模块数量摘要及后续工具建议 | 无 |
| `jufa_company_get_company_registration` | 企业工商照面信息 | 无 |
| `jufa_company_get_company_staff` | 企业主要人员分页列表 | `history`、`page`、`page_size` |
| `jufa_company_get_company_changes` | 工商变更记录 | `history`、`page`、`page_size` |
| `jufa_company_get_company_equity` | 股东、对外投资或分支机构 | 必填：`type=shareholders|investments|branches`；可选：`history`、`page`、`page_size` |
| `jufa_company_get_company_annual_reports` | 年报基础、股东、网站、股权变更或社保信息 | 必填：`type=base|shareholders|websites|equity_changes|social_security`；可选：`page`、`page_size` |
| `jufa_company_get_company_litigation` | 裁判文书、开庭、法院公告、立案、送达或诉前调解 | 必填：`type=wenshu|open_notice|court_notice|create_case|delivery_notice|prelitigation_mediate`；可选：`history`、`page`、`page_size` |
| `jufa_company_get_company_execution_risks` | 失信、被执行、限消、终本、股权冻结、拍卖或破产重整 | 必填：`type=dishonest|executed|limit_consume|final_case|equity_freeze|judicial_auction|bankruptcy_reform`；可选：`history`、`page`、`page_size` |
| `jufa_company_get_company_business_risks` | 行政处罚、经营异常、股权出质、环保处罚、欠税等 | 必填：`type=administrative_penalty|abnormal_operation|equity_pledge|environmental_penalty|tax_arrears|chattel_mortgage|ip_pledge|equity_pawn|serious_illegality`；可选：`history`、`page`、`page_size` |
| `jufa_company_get_company_ip_assets` | 商标、专利、软著、作品著作权或ICP备案 | 必填：`type=trademark|patent|software_copyright|works_copyright|icp`；可选：`history`、`page`、`page_size` |
| `jufa_company_get_company_business_records` | 招投标、资质、招聘、许可、土地、采购、税务信用等 | 必填：`type=tendering|qualification_certificate|recruitment|import_export_credit|administrative_license|land_publicity|purchase_information|property_transaction|land_transfer|tax_credit|financing|double_random_inspection|spot_check|land_mortgage`；可选：`history`、`page`、`page_size` |
| `jufa_company_get_company_construction_info` | 建筑资质、建筑人员或建筑项目 | 必填：`type=qualification|staff|project`；可选：`page`、`page_size` |

### 商标、专利与公共风险

| 工具 | 用途与返回 | 参数 |
|---|---|---|
| `jufa_trademark_search_trademarks` | 搜索商标，返回注册号、分类、申请人及 `rowkey` | 必填：`keyword`。可选：`page`、`page_size`、`int_cls`、`status`、`filters` |
| `jufa_trademark_get_trademark_detail` | 读取商标详情 | 必填：`rowkey` |
| `jufa_patent_search_patents` | 搜索专利，返回申请号、公开号、申请人及 `rowkey` | 必填：`keyword`。可选：`page`、`page_size`、`pat_type`、`legal_status`、`filters` |
| `jufa_patent_get_patent_detail` | 读取专利详情 | 必填：`rowkey` |
| `jufa_dishonest_search_dishonesty` | 搜索失信被执行人，返回案号、执行法院和定位字段 | 必填：`keyword`。可选：`page`、`page_size`、`province`、`publish_year`、`type`、`filters` |
| `jufa_dishonest_get_dishonesty_detail` | 读取失信详情 | 优先传`rowkey`；或传`company_id`；自然人可传`card_num`和`name` |
| `jufa_auction_search_auctions` | 搜索司法拍卖，返回标的、价格、状态及 `rowkey` | 必填：`keyword`。可选：`page`、`page_size`、`auction_stage`、`auction_status`、`auction_type_two`、`filters` |
| `jufa_auction_get_auction_detail` | 读取拍卖详情及外链 | 必填：`rowkey` |
| `jufa_court_search_court_notices` | 搜索开庭公告，返回案号、案由、法院、时间及 `rowkey` | 必填：`keyword`。可选：`page`、`page_size`、`province`、`case_reason`、`sdata`、`edata`、`filters` |
| `jufa_court_get_court_notice_detail` | 读取开庭公告详情 | 必填：`rowkey` |
| `jufa_penalty_search_penalties` | 搜索行政处罚，返回相对人、处罚单位、日期、金额及 `rowkey` | 必填：`keyword`。可选：`page`、`page_size`、`province`、`decision_start_date`、`decision_end_date`、`publish_start_date`、`publish_end_date`、`punish_range`、`filters` |
| `jufa_penalty_get_penalty_detail` | 读取行政处罚详情 | 必填：`rowkey` |

## 推荐调用流程

### 案例研究

1. 用 `jufa_case_search_cases` 按关键词、法院、案由、年份等检索。
2. 从候选结果选择目标 `case_uuid`。
3. 用 `jufa_case_get_case_detail` 读取正文后再总结或引用。

### 法规核验

1. 用 `jufa_law_search_laws` 检索法规，并按 `sxx_id`、制定机关或效力位阶筛选。
2. 用 `jufa_law_get_law_detail` 读取目标法规；长法规可传 `keyword` 过滤相关法条。
3. 回答中区分法规标题、效力状态、公布/实施日期与具体条文。

### 企业尽调

1. 用 `jufa_company_search_companies` 定位准确主体并取得 `company_id`。
2. 用 `jufa_company_get_company_profile` 查看模块摘要。
3. 只按用户关心的风险类型调用诉讼、执行、经营风险、知识产权或经营信息工具。

## 错误与边界处理

- **鉴权失败（401/403）**：提示用户检查或重新生成 API Key，不要在回答中展示密钥。
- **余额或积分不足**：明确提示用户前往聚法平台查看账户与充值，不重复调用同一工具。
- **超时或连接关闭**：说明服务暂时不可用；可在用户同意后重试一次，不进行无限重试。
- **空结果**：说明当前条件未找到记录，并建议放宽关键词、日期或地域条件。
- **参数错误**：依据工具Schema修正；ID必须来自检索结果，不猜测UUID、rowkey或筛选ID。
- **正文引用**：工具结果是数据检索结果，不替代律师意见；涉及正式法律结论时应提醒用户核对最新有效原文和具体案件事实。
