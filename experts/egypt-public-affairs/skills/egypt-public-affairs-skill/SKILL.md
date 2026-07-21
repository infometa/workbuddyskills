---
name: egypt-public-affairs-skill
description: Egypt Public Affairs 的语料库引擎与数据使用指南。覆盖埃及政府关系、政策解读、监管沟通、行业协会、公共舆论、ESG、媒体关系、危机公关、利益相关方管理和政府采购。
agent_created: true
---

# Egypt Public Affairs — 埃及公共事务专家语料库引擎



## 📊 语料库统计

### Reference_Texts — 25 份，~95 KB，~95K 字符

| 文件 | 字符数 | 行数 | 用途 |
|------|--------|------|------|
| capmas_egypt_statistics.txt | 3,170 | 175 | 国家统计口径与宏观经济基础数据 |
| china_embassy_egypt_resources.txt | 3,526 | 170 | 中国驻埃及使领馆与经商处资源 |
| digital_2024_egypt.txt | 1,861 | 64 | 数字生态、社交媒体与互联网渗透率 |
| egypt_ad_regulations.txt | 2,129 | 139 | 广告法规与内容合规底线 |
| egypt_esg_csr_framework.txt | 3,522 | 205 | ESG/CSR 监管框架与披露要求 |
| egypt_esg_report_template.txt | 8,106 | 426 | ESG 报告模板与实操清单 |
| egypt_government_procurement.txt | 3,688 | 236 | 政府采购体系与电子招投标 |
| egypt_government_structure.txt | 4,847 | 171 | 政府架构与决策层级 |
| egypt_industry_associations.txt | 6,009 | 241 | 行业协会、商会与利益集团 |
| egypt_legislative_process.txt | 3,517 | 187 | 立法流程与政策制定机制 |
| egypt_marketing_strategy.txt | 3,704 | 187 | 市场营销策略与品牌传播 |
| egypt_media_landscape.txt | 5,640 | 227 | 媒体格局与舆情渠道 |
| egypt_procurement_cases.txt | 5,206 | 251 | 政府采购典型案例 |
| egypt_public_affairs_crisis_cases.txt | 3,912 | 266 | 公共事务危机案例库 |
| egypt_public_affairs_laws.txt | 5,015 | 223 | 公共事务相关法律框架 |
| egypt_public_opinion.txt | 2,312 | 116 | 民意调查与消费者心理 |
| egypt_stakeholder_mapping.txt | 5,893 | 206 | 利益相关方影响力矩阵 |
| egypt_vision_2030_governance.txt | 2,471 | 125 | Vision 2030 与政策治理框架 |
| gafi_investment_structure.txt | 4,153 | 244 | GAFI 投资与自由区管理架构 |
| hofstede_culture_egypt.txt | 1,938 | 90 | 霍夫斯泰德文化维度分析 |
| itida_ict_development.txt | 5,274 | 233 | ITIDA 与 ICT 产业发展 |
| pr_crisis_management.txt | 3,351 | 179 | 公关危机管理方法论 |
| egypt_ntra_regulatory_framework.txt | 1,847 | 82 | NTRA 电信监管与 ICT 牌照 |
| egypt_labor_law_and_unions.txt | 1,953 | 105 | 埃及劳动法与工会实践 |
| egypt_cultural_sensitivity_cases.txt | 1,952 | 95 | 宗教/文化敏感案例库 |

### DuckDB — 5 张表，~70 行

| 表名 | 行数 | 列数 | 用途 |
|------|------|------|------|
| corpus_metadata | 25 | 6 | 语料库文件元数据索引 |
| crisis_cases | 8 | 8 | 公共事务危机案例速查 |
| government_contacts | 6 | 9 | 政府部门关键联系人 |
| media_contacts | 9 | 9 | 媒体与舆情渠道联系人 |
| stakeholders | 14 | 7 | 利益相关方影响力与优先级 |

### 数据时效性

| 数据源 | 更新频率 | 典型滞后 | 注意事项 |
|--------|---------|---------|---------|
| DuckDB | 季度/年度 | 3-12 个月 | 参考各表注释 |
| Reference_Texts 法律/政策 | 修订后 | 即时 | 关注埃及官方法律门户 |
| Reference_Texts 报告 | 年度 | 6-12 个月 | 每年更新 |

---

## 🚨 语料库优先原则

任何回答必须优先从本地语料库提取信息。优先级：
1. Reference_Texts (.txt)
2. DuckDB (.duckdb)
3. site:xxx 定向搜索
4. **fetch_with_fallback 在线抓取** — 多层降级兜底（直连→Google缓存→CORS网关（可配置）），当 site:xxx 无法获取目标页面内容时触发
5. 通用 WebSearch

## 触发主题 — 强制读取表/文件

| 触发主题 | 必须读取的文件/表 | 示例问题 |
|---------|------------------|---------|
| 政府架构/部门职能 | egypt_government_structure.txt | 埃及投资主管部门是谁？ |
| 立法流程/政策制定 | egypt_legislative_process.txt | 一项法律从提案到生效要多久？ |
| 投资/自由区管理 | gafi_investment_structure.txt | GAFI 提供哪些一站式服务？ |
| 行业商会/协会 | egypt_industry_associations.txt | 埃及主要行业协会有哪些？ |
| 政府采购/招投标 | egypt_government_procurement.txt + egypt_procurement_cases.txt | 如何参与埃及政府招标？ |
| 公共舆论/消费者心理 | egypt_public_opinion.txt | 埃及消费者最关注什么？ |
| 媒体关系/传播 | egypt_media_landscape.txt + media_contacts | 埃及主流媒体有哪些？ |
| 数字营销/社交媒体 | digital_2024_egypt.txt + egypt_marketing_strategy.txt | 埃及社交媒体渗透率多少？ |
| 危机公关/舆情管理 | pr_crisis_management.txt + crisis_cases | 遇到负面舆情如何24小时响应？ |
| 利益相关方管理 | egypt_stakeholder_mapping.txt + stakeholders | 关键利益相关方有哪些？ |
| ESG/CSR 合规 | egypt_esg_csr_framework.txt + egypt_esg_report_template.txt | 埃及 ESG 披露要求是什么？ |
| 广告合规 | egypt_ad_regulations.txt | 埃及广告有哪些禁区？ |
| 使馆/经商处资源 | china_embassy_egypt_resources.txt + government_contacts | 中国企业如何在埃及找政府对接人？ |
| Vision 2030/政策治理 | egypt_vision_2030_governance.txt | 埃及 2030 愿景对公共事务意味着什么？ |
| ICT/电信监管沟通 | itida_ict_development.txt + egypt_ntra_regulatory_framework.txt | NTRA 牌照怎么申请？ |
| 劳动法/用工合规 | egypt_labor_law_and_unions.txt | 埃及解雇员工怎么补偿？ |
| 工会/利益相关方冲突 | egypt_labor_law_and_unions.txt + egypt_stakeholder_mapping.txt | 如何应对工会罢工？ |
| 文化敏感/宗教禁忌 | egypt_cultural_sensitivity_cases.txt + hofstede_culture_egypt.txt | 斋月期间营销要注意什么？ |
| 文化差异/沟通策略 | hofstede_culture_egypt.txt | 与埃及政府部门沟通要注意什么？ |

## 数据源定向触发矩阵

```
国家统计局: capmas.gov.eg → 人口 / 就业 / 产业数据
投资总局: gafi.gov.eg → FDI / 投资法规 / 激励政策 / 自由区
ICT 发展局: itida.gov.eg → 科技园区 / 数字政策 / 外包激励
工业联合会: fei.org.eg → 行业商会 / 雇主组织 / 政策游说
政府采购门户: eps-gags.gov.eg → 招标公告 / 电子采购
使馆经商处: eg.mofcom.gov.cn → 中资企业服务 / 政策解读
```

---

## 结构化引用格式

```
---
📚 来源引用：
1. [A/Reference_Texts] {file} — {section}
2. [B/site:{site}] {fact} — {url}

📊 来源占比：语料库 XX% | 定向搜索 XX% | fetch_with_fallback 在线抓取 XX% | 通用搜索 XX% | 推理 XX%
```

## 多层降级流程图

```
STEP 1: 语料库检索（P0 强制）
  → Reference_Texts → DuckDB
  → 命中 → 直接输出 + 标注来源
  → 未命中 → 降级至 STEP 2

STEP 2: site:xxx 定向搜索（B 级可信度）
  → CAPMAS / GAFI / ITIDA / FEI / 中国使馆经商处
  → 连续 3 次返回空 → 降级至 STEP 3

STEP 3: fetch_with_fallback 在线抓取
  → 调用 `python scripts/fetch_with_fallback.py <URL>`
  → 多层降级：直连 → Google缓存 → CORS网关（可配置）
  → 命中 → 输出并标注 "[C/fetch_with_fallback]"
  → 仍失败 → 降级至 STEP 4

STEP 4: 通用 WebSearch（C 级可信度，最后手段）
  → 必须标注 C 级可信度
  → 仍失败 → 输出 "⚠️ 数据获取链路全部失败，建议用户确认信息来源"
```

## 输出模式

- `详细模式` / `verbose` → 展开完整分析
- `简洁模式` / `concise` → 3-5 条核心结论
- `语料库测试` / `corpus test` → 每条数据标注来源

## 不确定性

- 非官方/单一来源必须标注 `⚠️ 不确定性`
- 禁止绝对化表述
- 涉及政治风险/汇率预测时附验证渠道建议