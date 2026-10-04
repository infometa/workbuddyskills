# 小元 MCP 工具参数参考

各工具完整参数表。意图路由与调用规范见上级 `SKILL.md`。

---

## 探测

### xiaoyuan_ping - 探测 MCP 连通

不调下游业务接口。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| message | string | - | 回显内容，默认 pong |

---

## 买家

### xiaoyuan_search_buyers - 多条件搜买家

按产品/国家/触达等搜买家。结果读 `data.page.records`、`hasNext`、`backendParam`，再拿 `companyCdpId` 查详情或联系人。翻页必须同时改 `page_num` 并回传上一轮 `backendParam`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tag_keyword | string | - | 产品/品牌关键词，英文优先，如 LED lighting |
| company_name | string | - | 公司名关键字 |
| profile_keyword | string | - | 公司简介关键字 |
| countries | string[] | - | 国家二字码，如 `["US","AE"]` |
| features | number[] | - | 5到展 7提单 20广交会 21报名 28推荐自选 |
| company_info | number[] | - | 公司触达：1官网 2座机 3邮箱 4手机 5 WhatsApp 6 FB 7 LinkedIn 8 Twitter |
| contact_info | number[] | - | 联系人触达，枚举同上 |
| company_attributes | string[] | - | 1生产商 2分销商 3零售商 4品牌 5商超 |
| staff_size_level | number[] | - | 人员：1=0-99 2=100-500 3=500-999 4=1000+ |
| trade_scale_level | number[] | - | 近3年贸易额美元：1&lt;5万 2=5-10万 3&gt;10万 |
| page_num | number | - | 页码，从 1；翻页时必须与 `backend_param` 一起改成目标页 |
| page_size | number | - | 默认 20，建议 ≤50 |
| sort_type | number | - | 0不排序 1 VIP到展 2综合（默认） |
| search_similarity | boolean | - | 精准结果后是否扩展相似搜索 |
| backend_param | string | - | 翻页游标：上一轮 `data.backendParam` 原样回传，同时把 `page_num` 改为下一页。只传其一不生效 |
| supplier_category_vo_list | object[] | - | 采购类目；先 `xiaoyuan_all_category`，路径 id 填 t1TagId~t4TagId |
| buyer_type_ids | string[] | - | 新买家类型 id（多值 OR）；先 `xiaoyuan_list_buyer_type` 取 id |

### xiaoyuan_list_buyer_type - 买家类型维度列表

查询 dim_buyer_type_2026。返回 `id` 填入 `xiaoyuan_search_buyers.buyer_type_ids`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| industry | string | - | 一级行业 |
| bussiness_area | string | - | 业务领域（历史拼写 bussiness） |
| buyer_type | string | - | 买家类型 |
| big_industry | string | - | 大行业 |

### xiaoyuan_search_buyers_by_name - 按公司名搜买家

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| company_name | string | ✅ | 公司名称 |

### xiaoyuan_get_buyer_detail - 买家详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| company_cdp_id | string | ✅ | 买家 companyCdpId |

### xiaoyuan_get_buyer_contacts - 买家联系人

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| company_cdp_ids | string[] | ✅ | 一个或多个 companyCdpId |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10 |

---

## 本企业 / 产品

### xiaoyuan_get_company_basic_info - 本企业基本信息

无参数。

### xiaoyuan_list_whatsapp_templates - 拉取可发送的 WhatsApp 模板

无参数。只返回当前发送号能发的已审核正文模板。发送前先调本工具。

结果每条读 `templateName`、`language`、`category`、`bodyText`、`bodyParamCount`。同名多语言各占一条。

### xiaoyuan_send_whatsapp_template - 发送 WhatsApp 模板消息

会真实发给收件人。须用户确认收件号、模板和填好的正文后再调。重复调用会再发一条。`template_name` 与 `language` 必须来自上一工具。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| to | string | 是 | 收件 WhatsApp 号码，可带或不带 `+` |
| template_name | string | 是 | 模板名 |
| language | string | - | 语言码，如 `en`、`zh_CN`；同名多语言时必填 |
| body_parameters | string[] | - | 正文变量，顺序对应 `{{1}}`、`{{2}}`；个数须等于 `bodyParamCount`，无变量不传 |

### xiaoyuan_get_notice_list - 收到的消息列表

结果读 `data.records`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10，最大 50 |
| msg_type | number | - | 不传=全部；1展会现场 2RFQ推荐 3买家到场 4系统 5物流 6工单 7参展指南 |
| read_state | number | - | 0未读 1已读；不传查全部 |

### xiaoyuan_list_goods - 本企业产品列表

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| name | string | - | 产品名模糊搜索 |
| goods_state | number | - | -1未提交 0未审核 1正常 2审核不通过 3违规 4冻结 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 20 |

---

## 一客一档 / 数据圈选

### xiaoyuan_get_customer_file - 一客一档

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tax_number | string | - | 企业税号 |
| company_name | string | - | 无税号时用此解析 |
| trade_country | string | - | 贸易国家二字码，空=全部 |

### xiaoyuan_search_exhibitors - 按公司名搜展商

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| company_name | string | ✅ | 公司名称 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10 |

### xiaoyuan_get_trade_records - 贸易记录

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tax_number | string | ✅ | 企业税号 |
| trade_country | string | - | 二字码，如 US |
| start_date | string | - | 开始年月 yyyymm |
| end_date | string | - | 结束年月 yyyymm |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10 |

### xiaoyuan_get_export_trend - 出口趋势

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tax_number | string | ✅ | 企业税号 |
| start_date | string | - | 开始年月 yyyymm |
| end_date | string | - | 结束年月 yyyymm |
| trade_country | string | - | 贸易国家二字码 |

### xiaoyuan_get_his_exhibition - 会刊参展历史

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tax_number | string | ✅ | 企业税号 |
| exhibition_type | string | - | 0国际 1国内；空则下游默认 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10 |

### xiaoyuan_get_product_tags - 企业产品标签

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tax_number | string | ✅ | 企业税号 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10 |

### xiaoyuan_search_exhibitions - 搜索展会库

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| exhibition_name | string | - | 展会名称 |
| exhibition_country | string | - | 展会国家 |
| exhibition_industry | string | - | 展会行业 |
| exhibition_date | string | - | 展会日期 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 10 |

### xiaoyuan_get_tag_collection - 关键词查类目 tagId

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | ✅ | 产品/类目关键词，英文优先 |
| hscode | string | - | 海关编码 |
| company_name | string | - | 公司中文名 |

---

## 同行

### xiaoyuan_get_colleague_categories - 查询同行 T4 类目

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tax_number | string | - | 税号；空则查当前登录供应商类目 |

### xiaoyuan_search_colleagues - 搜同行企业

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| t4_tag_ids | string[] | ✅ | T4 类目 ID |
| country | string | - | 出口国家二字码，如 US |
| search_type | number | - | 1精确 2推测，默认 1 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 20 |

### xiaoyuan_search_suppliers_by_category - 按类目查中国卖家

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tag_id | string | ✅ | 类目 tagId |
| country | string | - | 出口国家 |
| page_num | number | - | 页码，从 1 |
| page_size | number | - | 默认 20 |

---

## 参展服务（只查不改）

四工具共用分页：`page` 从 1，`limit` 默认 20；可用 `exhibition_id` / `exhibition_name` 过滤。

### xiaoyuan_get_exhibition_guide / logistics / build_applications

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page | number | - | 页码，从 1 |
| limit | number | - | 默认 20 |
| exhibition_id | string | - | 展会 ID |
| exhibition_name | string | - | 展会名称关键字 |

### xiaoyuan_get_exhibition_work_orders - 现场工单

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page | number | - | 页码，从 1 |
| limit | number | - | 默认 20 |
| exhibition_id | string | - | 展会 ID |
| exhibition_name | string | - | 展会名称关键字 |
| work_order_id | string | - | 工单号 |
| keyword | string | - | 问题关键词 |
| order_state | number | - | 1已提交 2解决中 3无法解决 4已解决 5已关闭 |

---

## 官方贸易数据

### xiaoyuan_comtrade_get - UN Comtrade 贸易流

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| reporter_code | string | ✅ | 报告国，如 156 或 CHN |
| period | string | ✅ | 年度 2023，月度 202301 |
| cmd_code | string | ✅ | HS，如 8703 |
| flow_code | string | - | M进口 / X出口，默认 M |
| partner_code | string | - | 伙伴国，0=世界 |
| type_code | string | - | C商品 / S服务，默认 C |
| freq_code | string | - | A年度 / M月度，默认 A |
| cl_code | string | - | HS / H2..H6，默认 HS |

### xiaoyuan_wits_tariff - WITS MFN/FTA 关税

数据停在 2023，答复时需说明。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| reporter | string | ✅ | 报告国 ISO3，如 CHN |
| product | string | ✅ | HS，如 8703 |
| partner | string | - | 伙伴国 ISO3，000=世界 |
| year | string | - | 默认 2023 |

### xiaoyuan_wto_eping - WTO ePing TBT/SPS 通报

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| member_codes | string[] | - | 通报成员，如 `["C156"]` |
| hs_codes | string[] | - | HS 列表，如 `["8703"]` |
| from_date | string | - | yyyy-MM-dd |
| to_date | string | - | yyyy-MM-dd |
| keyword | string | - | 关键词 |
| page | number | - | 从 **0** 开始 |
| page_size | number | - | 默认 20 |

### xiaoyuan_wto_qrs - WTO 数量限制

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| member | string | - | ISO3，如 CHN |
| hs6 | string | - | HS6，如 870321 |

### xiaoyuan_wto_tfad - WTO 通关便利化

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| member_iso3 | string | ✅ | 成员 ISO3，如 CHN |

---

## 提单买家

### xiaoyuan_get_lading_top_buyers - 提单 Top 买家

`hs_code` 与 `product` 至少一项。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| hs_code | string | - | HS 编码 |
| product | string | - | 产品描述 |
| country | string | - | 进口国 ISO2/ISO3，如 US |
| year | number | - | 年份，如 2024 |
| limit | number | - | 默认 10 |

### xiaoyuan_query_lading_buyers - 提单买家回填

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| company_name | string | - | 买家公司名 |
| buyer_id | string | - | 买家 ID |
| tax_number | string | - | 税号 |

---

## AroundDeal（海外画像）

### xiaoyuan_arounddeal_list_enums - 查数据字典（免费）

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| field | string | ✅ | job_level / function / employee_range / company_type / industry / industry_parent / country_code |
| search | string | - | 按名称或 ID 模糊搜 |
| suggest | string | - | 人话映射，如 CEO → CXO |

### xiaoyuan_arounddeal_enrich_company - 公司画像

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| linkedin_url | string | - | 公司 LinkedIn URL |
| website | string | - | 官网 |
| name | string | - | 公司名 |

### xiaoyuan_arounddeal_search_companies - 搜公司

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | - | 关键词 |
| country | string | - | ISO2，逗号分隔 |
| industry | string | - | 行业 ID，逗号分隔 |
| employee_range | string | - | 规模档 A~I，逗号分隔 |
| page | number | - | 页码，上限 1000 |
| size | number | - | 每页条数，上限 10 |

### xiaoyuan_arounddeal_search_people - 搜人

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| title | string | - | 职位关键词 |
| job_level | string | - | 职级，逗号分隔 |
| function | string | - | 职能 |
| country | string | - | 人所在国家 ISO2 |
| location | string | - | 地点 |
| industry | string | - | 行业 ID |
| employee_range | string | - | 公司规模档 A~I |
| company_hq_country | string | - | 总部国家 ISO2 |
| start | number | - | 起始下标 |
| limit | number | - | 上限 10 |

### xiaoyuan_arounddeal_find_contacts - 找公司联系人

按条计费，约 $0.50/人。`limit` 上限 5。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| linkedin_url | string | - | 公司 LinkedIn（强烈建议） |
| website | string | - | 官网 |
| name | string | - | 公司名 |
| preset | string | - | sourcing=采购决策人，brand=高管/品牌 |
| job_level | string | - | 职级，覆盖预设 |
| function | string | - | 职能，覆盖预设 |
| country | string | - | 联系人国家 ISO2 |
| limit | number | - | 1~5，默认 5 |
| require_business_email | boolean | - | 只要企业邮箱 |

### xiaoyuan_arounddeal_search_sourcing_contacts / search_brand_contacts

按条计费，`limit` 1~5。`linkedin_url` / `website` / `name` 至少一项。

### xiaoyuan_arounddeal_enrich_person - 人物富化

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| linkedin_url | string | - | 个人 LinkedIn |
| email | string | - | 邮箱 |
| name | string | - | 姓名（需同时给 company） |
| company | string | - | 公司名 |

### xiaoyuan_arounddeal_resume_enrichment - 人物履历

`linkedin_url` 或 `email` 至少一项。

### xiaoyuan_arounddeal_email_to_linkedin

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| email | string | ✅ | 工作邮箱 |

### xiaoyuan_arounddeal_verify_contact

email / phone 二选一。

### xiaoyuan_arounddeal_company_intel

`intel_type`：clients / suppliers / events / products / jobs / orgchart。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| intel_type | string | ✅ | 见上 |
| linkedin_url | string | - | 公司 LinkedIn |
| website | string | - | 官网 |
| name | string | - | 公司名 |

### xiaoyuan_arounddeal_check_relationship - 判断两家公司关系

至少 `name_a`+`name_b` 或 `website_a`+`website_b`。

---

## Hunter.io（邮箱）

`email_finder` 找不到不扣费。`discover` 免费。`domain` 优先于 `company`。

### xiaoyuan_hunter_email_finder

`domain` / `company` / `linkedin_handle` 至少一项；且须有 `first_name`+`last_name`、`full_name` 或 `linkedin_handle`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| domain | string | - | 公司域名 |
| company | string | - | 公司名 |
| linkedin_handle | string | - | LinkedIn 个人 handle |
| first_name | string | - | 名 |
| last_name | string | - | 姓 |
| full_name | string | - | 全名 |
| max_duration | number | - | 最长等待秒数 |

### xiaoyuan_hunter_domain_search

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| domain | string | - | 公司域名（与 company 至少一项） |
| company | string | - | 公司名 |
| limit | number | - | 默认 10 |
| offset | number | - | 偏移 |
| email_type | string | - | personal / generic |
| seniority | string | - | junior/senior/executive |
| department | string | - | executive/it/finance/sales/procurement 等 |
| decision_maker | boolean | - | 只取决策人 |

### xiaoyuan_hunter_email_verifier

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| email | string | ✅ | 邮箱 |

### xiaoyuan_hunter_people_find / companies_find / discover

详见各工具必填组合；`discover` 为免费搜公司。
