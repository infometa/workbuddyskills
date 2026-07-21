---
name: egypt-strategic-advisory-skill
description: Egypt Strategic Advisory 的语料库引擎与数据使用指南。覆盖埃及宏观经济、产业趋势、竞争格局、投资选址、进入模式、风险评估、长期布局和决策建议。
agent_created: true
---

# Egypt Strategic Advisory — 埃及战略顾问语料库引擎



## 📊 语料库统计

### Reference_Texts — 35 份，~841 KB，~841K 字符

| 文件 | 字符数 | 行数 | 用途 |
|------|--------|------|------|
| egypt_macro_outlook.txt | 391,446 | 1,829 | IMF 宏观经济展望 / 财政政策 / 结构性改革 |
| egypt_national_narrative.txt | 301,669 | 7,961 | MPED 国家经济叙事 / 发展战略与部门优先 |
| egypt_trade_agreements.txt | 13,392 | 117 | 自由贸易协定与市场准入 |
| egypt_ebrd_transition_2025.txt | 9,879 | 164 | EBRD 转型报告国别评估 |
| egypt_wb_mpo.txt | 8,750 | 131 | 世界银行宏观贫困展望 |
| egypt_investment_law.txt | 10,247 | 156 | 埃及投资法 72/2017 / 激励与保障 |
| egypt_vision2030.txt | 7,435 | 152 | 埃及 2030 愿景 / 八大战略目标 |
| egypt_industry_analysis.txt | 5,677 | 129 | 重点行业综合分析 |
| egypt_fdi_analysis.txt | 5,614 | 147 | FDI 来源 / 行业 / 投资环境 |
| egypt_competition_landscape.txt | 6,040 | 142 | 外资与中资企业竞争格局 |
| egypt_suez_canal.txt | 4,358 | 118 | 苏伊士运河收入与经济影响 |
| egypt_site_selection_comparison.txt | 4,014 | 183 | 投资选址对比 |
| egypt_sczone_guide.txt | 3,575 | 111 | 苏伊士运河经济区投资指南 |
| egypt_entry_mode_matrix.txt | 3,598 | 148 | 市场进入模式矩阵 |
| egypt_labor_market.txt | 3,339 | 153 | 劳动力市场与用工成本 |
| egypt_financing_landscape.txt | 3,491 | 138 | 融资环境与金融工具 |
| egypt_local_competitors.txt | 3,045 | 114 | 本地竞争者分析 |
| egypt_fx_risk_and_capital_controls.txt | 3,152 | 139 | 汇率风险与资本管制 |
| egypt_tax_practice.txt | 2,840 | 140 | 税务实践与合规 |
| egypt_customs_guide.txt | 2,882 | 136 | 海关与进出口实务 |
| egypt_scenario_planning.txt | 3,271 | 146 | 情景规划与长期布局 |
| egypt_industry_automotive.txt | 4,058 | 172 | 汽车行业深度 |
| egypt_industry_textiles.txt | 4,085 | 172 | 纺织行业深度 |
| egypt_industry_chemicals.txt | 4,119 | 165 | 化工行业深度 |
| egypt_industry_renewable_energy.txt | 4,168 | 175 | 可再生能源行业深度 |
| egypt_industry_pharmaceuticals.txt | 4,071 | 173 | 制药行业深度 |
| egypt_industry_food_processing.txt | 4,012 | 171 | 食品加工行业深度 |
| egypt_political_risk.txt | 3,822 | 97 | 政治经济风险与主权评级 |
| hofstede_culture_egypt.txt | 1,938 | 90 | 霍夫斯泰德文化维度分析 |
| egypt_public_opinion.txt | 2,312 | 116 | 民意与消费者心理 |
| egypt_ad_regulations.txt | 2,129 | 139 | 广告法规与内容合规 |
| egypt_sovereign_wealth_funds.txt | 2,215 | 94 | 主权财富基金与国有资本布局 |
| egypt_real_estate_and_construction.txt | 2,209 | 109 | 房地产与建筑业投资指南 |
| egypt_tourism_investment.txt | 2,175 | 113 | 旅游业投资与运营指南 |
| egypt_chinese_investment_cases.txt | 2,291 | 137 | 中资企业成功案例拆解 |

### DuckDB — 11 张表，~77 行

| 表名 | 行数 | 列数 | 用途 |
|------|------|------|------|
| corpus_metadata | 35 | 5 | 语料库文件元数据索引 |
| egypt_macro_indicators | 10 | 4 | 核心宏观经济指标速查 |
| egypt_industry_sectors | 10 | 5 | 重点行业 GDP 占比/增速/就业 |
| industry_details | 11 | 8 | 细分行业关键指标与投资机会 |
| egypt_fdi_by_source | 10 | 5 | FDI 来源国/金额/占比 |
| egypt_trade_agreements | 10 | 6 | 埃及 FTA 清单及优惠条款 |
| egypt_sczone_sectors | 10 | 4 | SCZone 目标行业及优先等级 |
| egypt_mega_projects | 9 | 5 | 重大基建与战略项目汇总 |
| egypt_chinese_investment | 10 | 4 | 中资企业在埃投资明细 |
| scenario_planning | 4 | 8 | 宏观情景与应对策略 |
| site_options | 6 | 9 | 投资选址关键指标对比 |

### 数据时效性

| 数据源 | 更新频率 | 典型滞后 | 注意事项 |
|--------|---------|---------|---------|
| DuckDB | 年度/季度 | 3-12 个月 | 参考各表注释 |
| Reference_Texts 法律/政策 | 修订后 | 即时 | 关注埃及官方法律门户 |
| Reference_Texts 报告 | 年度 | 6-12 个月 | 每年更新 |

---

## 🚨 语料库优先原则

任何回答必须优先从本地语料库提取信息。优先级：
1. Reference_Texts (.txt)
2. DuckDB (.duckdb)
3. CSV_Datasets (.csv)
4. 官方 API（CBE / CAPMAS / GAFI / SCZone）
5. site:xxx 定向搜索
6. **fetch_with_fallback 在线抓取** — 四层降级兜底（直连→Google缓存→CORS网关→免费代理），当 site:xxx 和通用搜索均无法获取目标页面内容时触发
7. 通用 WebSearch

## 触发主题 — 强制读取表/文件

| 触发主题 | 必须读取的文件/表 | 示例问题 |
|---------|------------------|---------|
| 宏观经济/GDP/通胀 | egypt_macro_outlook.txt + egypt_wb_mpo.txt + egypt_macro_indicators | 埃及 GDP 增速预测多少？ |
| 货币政策/汇率 | egypt_macro_outlook.txt + egypt_fx_risk_and_capital_controls.txt | CBE 利率和 EGP 走势？ |
| 重点行业分析 | egypt_industry_analysis.txt + egypt_national_narrative.txt + industry_details | 埃及制造业投资机会？ |
| 行业深度（汽车/纺织/化工/可再生能源/制药/食品） | egypt_industry_{sector}.txt + industry_details | 埃及汽车行业现状如何？ |
| 投资激励/税收优惠 | egypt_investment_law.txt + egypt_tax_practice.txt | 外资有什么优惠政策？ |
| 苏伊士运河经济区 | egypt_sczone_guide.txt + egypt_suez_canal.txt + egypt_sczone_sectors | SCZone 怎么入驻？ |
| 政治风险/地缘局势 | egypt_political_risk.txt + egypt_macro_outlook.txt + scenario_planning | 埃及外汇管制风险？ |
| 埃及愿景 2030 | egypt_vision2030.txt + egypt_national_narrative.txt | 2030 愿景重点产业？ |
| 竞争格局 | egypt_competition_landscape.txt + egypt_local_competitors.txt + egypt_chinese_investment | 中资在埃主要对手？ |
| 贸易协定/关税 | egypt_trade_agreements.txt + egypt_trade_agreements + egypt_customs_guide.txt | 埃及有哪些 FTA？ |
| FDI 来源与趋势 | egypt_fdi_analysis.txt + egypt_fdi_by_source | 外资主要来源国？ |
| 国家发展战略 | egypt_national_narrative.txt + egypt_mega_projects | 埃及经济发展叙事？ |
| 投资选址 | egypt_site_selection_comparison.txt + site_options | 开罗 vs 亚历山大 vs SCZone？ |
| 市场进入模式 | egypt_entry_mode_matrix.txt | 应该合资还是绿地投资？ |
| 融资环境 | egypt_financing_landscape.txt | 埃及有哪些融资渠道？ |
| 劳动力/用工成本 | egypt_labor_market.txt | 埃及平均工资多少？ |
| 主权财富基金/国企混改 | egypt_sovereign_wealth_funds.txt | TSFE 有哪些投资机会？ |
| 房地产/建筑业 | egypt_real_estate_and_construction.txt | 新行政首都房地产怎么投？ |
| 旅游业 | egypt_tourism_investment.txt | 红海酒店投资前景如何？ |
| 中资企业经验 | egypt_chinese_investment_cases.txt | 中资企业在埃及有哪些成功案例？ |
| 情景规划 | egypt_scenario_planning.txt + scenario_planning | 最佳/基准/悲观情景是什么？ |

## 数据源定向触发矩阵

```
国家统计: capmas.gov.eg → 人口 / 就业 / 产业数据
中央银行: cbe.org.eg → 利率 / 汇率 / 外汇储备 / 通胀
投资总局: gafi.gov.eg → FDI / 投资法规 / 激励政策
苏伊士经济区: sczone.eg → 园区 / 物流 / 产业准入
财政部: mof.gov.eg → 财政预算 / 债务 / 补贴
国家信息: sis.gov.eg → 国家战略 / 政策文件
海关: customs.gov.eg → 关税 / HS Code / 进出口数据
计划部: mped.gov.eg → 国家叙事 / 发展规划
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

## 四层降级流程图

```
STEP 1: 语料库检索（P0 强制）
  → Reference_Texts → DuckDB → CSV_Datasets
  → 命中 → 直接输出 + 标注来源
  → 未命中 → 降级至 STEP 2

STEP 2: site:xxx 定向搜索（B 级可信度）
  → CBE / CAPMAS / GAFI / SCZone / SIS / MOF / MPED
  → 连续 3 次返回空 → 降级至 STEP 3

STEP 3: fetch_with_fallback 在线抓取
  → 调用 `python scripts/fetch_with_fallback.py <URL>`
  → 自动四层降级：直连 → Google缓存 → CORS网关 → 免费代理
  → 命中 → 输出并标注 "[C/fetch_with_fallback]"
  → 仍失败 → 降级至 STEP 4

STEP 4: 通用 WebSearch（C 级可信度，最后手段）
  → 必须标注 C 级可信度
  → 仍失败 → 输出 "⚠️ 数据获取链路全部失败，建议用户确认信息来源"
```

## 输出模式

- `详细模式` / `verbose` → 展开完整分析
- `简洁模式` / `concise` → 3-8 条核心结论（**默认模式**）
- `语料库测试` / `corpus test` → 每条数据标注来源

## 🎯 默认输出规范（强制）

除非用户明确要求详细回答，否则默认使用简洁模式：

- 回答限制在 **3-8 条核心信息** 以内
- 每条信息控制在 1-3 句话，附关键数据即可
- 不展开推导过程、不列举所有来源、不写长篇分析
- 若用户追问某条信息，再展开详细解释
- 示例：
  > ❌ 长篇分析（默认）→ ✅ "核心结论：1. ... 2. ... 3. ... 如需展开请告诉我"

## 数据冲突处理规则（新增）

语料库中不同来源可能存在数据不一致，遇到冲突时按以下规则处理：

1. **法律原文 > 官方指南 > 营销材料** — 如SCZone指南中"48小时注册"与entry_mode_matrix中"2-4周"冲突，应优先采信实际流程数据
2. **具体数据 > 笼统表述** — 如绿氢激励中"土地租金减免"与Law 2/2024原文"25%用益权费用减免"，应采信具体数字
3. **标注冲突**：回答中如涉及冲突数据，应注明"不同来源存在差异"并给出合理区间
4. **时效性优先**：较新的来源优先于较早的来源

## 不确定性

- 非官方/单一来源必须标注 `⚠️ 不确定性`
- 禁止绝对化表述
- 涉及政治风险/汇率预测时附验证渠道建议