# WeStock Tool - 常见选股场景详解

> **定位**：本文档是 SKILL.md 的 **L3 层补充材料**，提供完整的选股场景示例和详细操作步骤。
>
> **使用方式**：AI 在遇到不确定的选股场景时按需加载本文档。命令列表和基本用法请参见
> [SKILL.md](../SKILL.md)，完整字段列表请参见 [fields-guide.md](./fields-guide.md)。

---

## 一、价值投资场景

### 场景 1：寻找低估值蓝筹

```
用户："帮我找PE低于15、ROE高于15%的白马股"
→ westock-tool filter "intersect([PE_TTM > 0, PE_TTM < 15, ROETTM > 15])" --date 2026-04-10 --orderby ROETTM --desc
→ 解读：PE为正说明盈利，低PE代表估值便宜，高ROE代表盈利能力强
→ 建议补充：查看行业分布，关注PE是否因周期低谷导致偏低
```

### 场景 2：高股息红利组合

```
用户："找股息率超过5%的高分红股票"
→ westock-tool filter "intersect([DividendRatioTTM > 5, PE_TTM > 0, PE_TTM < 20])" --limit 30
→ 解读：结合PE过滤掉异常值（如亏损或微利企业）
→ 进阶：使用预设 filterHighDividendLowValuation 同时叠加PB约束
```

### 场景 3：PEG成长股估值

```
用户："找PEG小于1的成长股"
→ westock-tool filter "intersect([PE_TTM > 0, PE_TTM < 40, NPParentCompanyYOY > 20, PE_TTM / NPParentCompanyYOY < 1])"
→ 解读：PEG<1意味着估值相对盈利增速便宜
→ 注意：需确保利润增长可持续，建议结合季报数据验证
```

---

## 二、技术面选股场景

### 场景 4：均线多头排列（趋势向上）

```
用户："找均线多头排列的强势股"
→ westock-tool filter "intersect([MA_5 > MA_10, MA_10 > MA_20, MA_20 > MA_60])" --limit 30
→ 解读：短期均线在上表明多头占优，适合趋势跟踪
→ 建议：叠加成交量放大 (TurnoverValue > 某阈值) 确认有效性
```

### 场景 5：MACD + KDJ 共振

```
用户："找MACD金叉且KDJ超卖反弹的股票"
→ westock-tool filter "intersect([DIF > DEA, MACD > 0, KDJ_J < 30])"
→ 解读：MACD金叉确认中期趋势转多，KDJ超卖区表明短期回调到位
→ 注意：此策略在沪深和港股有效，美股暂不支持技术指标筛选
```

### 场景 6：布林带突破 + RSI 确认

```
用户："找突破布林上轨且RSI没有严重超买的股票"
→ westock-tool filter "intersect([ClosePrice > BOLL_UPPER, RSI_6 < 80])"
→ 解读：突破上轨为强势信号，RSI<80排除极端超买
```

---

## 三、资金面选股场景

### 场景 7：主力资金大幅流入

```
用户："找今天主力资金净流入超过1亿的股票"
→ westock-tool filter "MainNetFlow > 100000000" --date 2026-04-10 --orderby MainNetFlow --desc
→ 解读：主力大额流入可能预示机构建仓
→ 注意：仅沪深市场支持，港股用 TotalNetFlow，美股不支持
```

### 场景 8：持续资金关注

```
用户："找近期持续有资金流入的股票"
→ westock-tool filter "intersect([MainNetFlow5D > 0, MainNetFlow10D > 0, MainNetFlow20D > 0])"
→ 解读：5日/10日/20日均为正流入，说明机构持续加仓
→ 注意：仅沪深市场支持此组合
```

---

## 四、港股/美股场景

### 场景 9：港股低估值高股息

```
用户："找港股中股息率高、估值低的央企"
→ westock-tool filter "intersect([PeTTM > 0, PeTTM < 10, DivTTM > 5])" --market hk --limit 30
→ 注意字段差异：港股用 PeTTM/PbLF/DivTTM，非 PE_TTM/PB/DividendRatioTTM
```

### 场景 10：美股大盘股筛选

```
用户："找美股中市值大于1000亿、PE低于30的科技股"
→ westock-tool filter "intersect([TotalMV > 100000000000, PeTTM > 0, PeTTM < 30])" --market us
→ 注意：美股不支持技术指标和资金流向筛选
```

---

## 五、策略选股场景

### 场景 11：使用预置策略

```
用户："用MACD金叉策略帮我选股"
→ westock-tool strategy macd_golden --date 2026-04-10
→ 返回当日满足 MACD 金叉条件的股票列表
```

### 场景 12：多策略对比

```
用户："对比价值投资和成长投资两种策略的选股结果"
→ westock-tool strategy value_invest --date 2026-04-10
→ westock-tool strategy growth_stock --date 2026-04-10
→ 对比两组结果中的重叠标的和差异
```

### 场景 13：策略回溯

```
用户："看看MACD金叉策略过去一周每天选了哪些股票"
→ westock-tool strategy macd_golden --start 2026-04-03 --end 2026-04-10
→ 返回区间内每天的策略选股结果
```

---

## 六、标签选股场景

### 场景 14：按股东属性筛选

```
用户："找央企控股的股票"
→ westock-tool label shareholder_central_state --date 2026-04-10
→ 返回央企控股标签下的股票列表
```

### 场景 15：财务特征标签

```
用户："找高ROE的公司"
→ westock-tool label fin_high_roettm --date 2026-04-10
→ 返回 ROE(TTM) 处于高位的股票列表
```

### 场景 16：多标签组合

```
用户："找央企中破净的股票"
→ westock-tool label shareholder_central_state,valuation_lowpb --date 2026-04-10
→ 同时满足央企 + 破净两个标签
```

---

## 七、排行选股场景（ranking）

### 场景 17：综合评分排行

```
用户："帮我找综合评分最高的10只股票"
→ westock-tool ranking CompScore --limit 10
→ 返回按综合评分降序排列的 TOP10 股票
→ 解读：综合评分综合了资金/基本面/风险/技术四个维度，高分代表综合表现好
→ 建议：结合行业分布，避免集中在单一行业
```

### 场景 18：评分变动追踪

```
用户："哪些股票评分周变动最大？"
→ westock-tool ranking CompScore --type weekly --limit 20
→ 返回评分周变动排行
→ 解读：评分大幅上升可能预示市场关注度提升
→ 进阶：用 westock-data score <code> 查看个股评分详细变动
```

### 场景 19：资金评分选股

```
用户："资金面评分最高的股票有哪些？"
→ westock-tool ranking CapScore --limit 20
→ 返回按资金评分排序的股票列表
→ 解读：资金评分高代表主力资金关注度高
→ 建议：结合 westock-data fundhold <code> 查看详细资金流向
```

### 场景 20：高评分筛选

```
用户："找综合评分70以上的优质股票"
→ westock-tool ranking CompScore --min-CompScore 70 --limit 20
→ 返回综合评分≥70的股票按综合评分降序排列
→ 解读：高评分代表综合表现好
→ 进阶：叠加 CapScore 等字段的阈值筛选，如 --min-CapScore 60
```

### 场景 21：估值排行

```
用户："A股估值最低的股票有哪些？"
→ westock-tool ranking fin_valuation --limit 20        # 默认升序（PE最低）
→ westock-tool ranking fin_valuation --asc             # 显式升序
→ 解读：估值排行按PE/PB/PS等指标排序
→ 建议：结合行业和基本面分析，避免单一维度判断
```

### 场景 22：成长指标选股

```
用户："成长能力最强的10只股票"
→ westock-tool ranking fin_growth --limit 10
→ 返回按营收增速降序排列的 TOP10
→ 解读：成长排行包含营收增速、利润增速等指标
→ 进阶：用 westock-data finance <code> summary 查看财务详情验证
```

### 场景 23：涨跌停排行

```
用户："连续涨停天数最多的股票？"
→ westock-tool ranking limitup_days --limit 20
→ 返回按连续涨停天数降序排列的股票
→ 解读：连板越多市场关注度越高
→ 风险：连板后可能面临炸板风险，需谨慎追高
```

### ⭐ 场景 24：范围限定（组合查询）

```
用户："央企里评分最高的10只"
→ westock-tool ranking CompScore --within-label shareholder_central_state --limit 10
→ 在央企股票里按综合评分排行

用户："MACD金叉的股票中估值最低的"
→ westock-tool ranking fin_valuation --within-strategy macd_golden --limit 10
→ 在 MACD 金叉信号股里按估值升序排行

用户："限售解禁股的评分排行"
→ westock-tool ranking CompScore --within-event shareunlock_next_90 --limit 10
→ 在限售解禁股中按综合评分排行

用户："半导体板块里估值最低的股票"
→ westock-tool ranking fin_valuation --universe 11010001 --limit 10
→ 在指定板块内按估值升序排行
```

### 场景 25：排行 + 阈值筛选组合

```
用户："资金评分高且综合评分≥70的股票"
→ westock-tool ranking CapScore --min-CompScore 70 --limit 20
→ 先筛综合评分≥70，再按资金评分降序
→ 解读：多维度综合筛选，选出"综合好 + 资金强"的标的
```

### 场景 26：两融加仓榜（margin 指标源）

```
用户："今天两融加仓最多的股票"
→ westock-tool ranking margin_chg_d --limit 20
→ 默认按 MChgD（两融余额日变动）降序，看加仓榜
→ 解读：MChgD > 0 = 加仓，融资盘看好；通过 --asc 切换到日减仓榜（看融资盘抛弃）

用户："近一周两融累计加仓最猛的股票"
→ westock-tool ranking margin_chg_w --limit 10
→ 按 MChgW（周变动）降序
→ 类似指标：margin_chg_m（月）/ margin_chg_q（季）/ margin_chg_y（年）
```

### 场景 27：两融连续扩大筛选

```
用户："两融余额连续扩大 5 天以上的股票（融资盘持续抢筹）"
→ westock-tool ranking margin_in_days --min-MtInDays 5 --limit 20
→ 按 MtInDays（连续扩大天数）降序，并设阈值 ≥5
→ 解读：连续多日两融扩大 = 融资盘持续看好，资金面强势信号
→ 反向指标：margin_out_days（连续缩小天数，融资盘持续撤离）
```

### 场景 28：主力资金净流入榜（capital 指标源）

```
用户："今天主力净流入最多的股票"
→ westock-tool ranking cap_main_net --limit 20
→ 默认按 MainNetIn 降序看主力净流入榜
→ 解读：通过 --asc 切换看主力净流出榜（被主力抛弃）；散户净流入榜首位通常对应主力净流出榜首位（资金流转零和性）

用户："近 5 个交易日主力累计净流入最多的股票"
→ westock-tool ranking cap_main_5d --limit 20
→ 按 MainSum5d（派生字段，= MainT0+T1+T2+T3+T4 的合计）降序
→ 不要直接看单日数据，5 日累计更能反映持续抢筹
```

### 场景 29：主力连续抢筹筛选

```
用户："主力连续净流入 3 天以上的股票（持续抢筹）"
→ westock-tool ranking cap_in_days --min-MainInDays 3 --limit 20
→ 按 MainInDays（连续净流入天数）降序，阈值 ≥3
→ 解读：连续多日主力净流入 = 主力持续抢筹；
→ 反向指标：cap_out_days（连续净流出天数，主力持续撤离）
```

### 场景 30：标签 × 资金交叉分析（ranking --within-label + capital）

```
用户："央企里近 5 天主力累计净流入最多的股票"
→ westock-tool ranking cap_main_5d --within-label shareholder_central_state --limit 10
→ 解读：先在央企标签内圈定股票池，再按主力 5 日累计净流入降序
→ 这是 ranking 命令的核心特色 — 范围限定 × 指标排序的二维交叉分析
→ 类似组合：板块×指标（--universe 11010001）/ 策略×指标（--within-strategy macd_golden）/ 事件×指标（--within-event shareunlock_next_90）
```

---

## 八、组合分析场景

### 场景 24：多维度综合选股

```
用户："帮我找基本面好、技术面向上、资金也在流入的股票"
→ 使用预设 filterTechFundamentalCombo：MACD金叉 + 均线多头 + ROE>10% + PE<30
→ 或自定义组合:
  westock-tool filter "intersect([DIF > DEA, MACD > 0, MA_5 > MA_10, ROEWeighted > 10, PE_TTM > 0, PE_TTM < 30, MainNetFlow > 0])"
```

### 场景 25：条件选股 + 数据查询联动

```
用户："帮我选出低估值高ROE的股票，并查看前3只的详细财务数据"
→ 步骤1: westock-tool filter "intersect([PE_TTM > 0, PE_TTM < 15, ROETTM > 20])" --limit 3
→ 步骤2: 取返回的3个股票代码
→ 步骤3: 使用 westock-data finance <code> summary 查看各股财务详情
→ 步骤4: 综合分析并给出推荐
```

---

## 九、注意事项

1. **市场字段差异**：沪深用 `PE_TTM`/`PB`/`DividendRatioTTM`，港美用 `PeTTM`/`PbLF`/`DivTTM`
2. **功能限制**：
   - 技术指标筛选（MACD/KDJ/RSI/BOLL）：沪深✅ 港股✅ 美股❌
   - 资金流向筛选（MainNetFlow等）：沪深✅ 港股部分✅ 美股❌
   - 神奇九转（NineTurn_Green9）：仅沪深
   - 策略选股、标签选股、事件选股、排行选股：仅沪深A股
3. **日期格式**：统一使用 `YYYY-MM-DD`，不传则默认当天
4. **数据时效**：选股数据基于收盘后更新，盘中查询可能使用前一交易日数据

---

## 十、ETF 选基场景

### 场景：高股息 ETF 主题筛选

```
用户："帮我找高股息的 ETF"
→ westock-tool label high_dividend --asset etf
→ 解读：返回的是符合"高股息"主题池的 ETF 名单
→ 进阶：可叠加规模筛选 → westock-tool label high_dividend,size_100 --asset etf
```

### 场景：千亿规模 ETF

```
用户："千亿规模以上的 ETF 都有哪些"
→ westock-tool label size_1000 --asset etf
→ 解读：直接命中 KYP 主题池中的"千亿规模"分类
```

### 场景：ETF 估值最低（PB 升序）

```
用户："PB 最低的 ETF 有哪些（找折价机会）"
→ westock-tool ranking valuation --asset etf --orderby PB --asc --limit 10
→ 解读：--orderby 切换排序字段为 PB，--asc 改为升序看最低
→ 注意：valuation 默认按 PE_TTM 升序；valuation_pct 看历史百分位（更适合判断"相对低估"）
```

### 场景：近 20 日涨幅最高的 ETF

```
用户："最近一个月涨幅最大的 ETF"
→ westock-tool ranking qt_chg_interval --asset etf --orderby ChgPct20D --limit 10
→ 解读：qt_chg_interval 提供 1D/5D/10D/20D/60D/250D 多档涨跌幅，通过 --orderby 选择
```

### 场景：ETF 选基 → 详情精查（联动）

```
用户："给我推荐一只规模大、估值低的科创 ETF"

AI 步骤：
1. 标签筛选：westock-tool label science_tech --asset etf --limit 20
   → 拿到候选 ETF 代码列表
2. 排行排序：westock-tool ranking size --asset etf --limit 20
   → 与候选列表取交集，挑出规模最大的几只
3. 估值校验：westock-tool ranking valuation --asset etf --orderby PE_TTM --asc --limit 50
   → 在候选中再筛低估值的
4. 精查详情：westock-data etf detail <code>
   → 看 classification（4 级分类）、managerHistory（经理稳定性）、费率、收益率、最大回撤等
5. 输出推荐结论
```

> ⚠️ **决策入口**：
> - 用户带"标签/主题"（如"高股息 / 千亿基金 / 科创板占比高"）→ `label --asset etf`
> - 用户带"排序/榜单"（如"规模最大 / 涨幅前 10 / 估值最低"）→ `ranking --asset etf`
> - 用户给具体 ETF 代码看详情 → `westock-data etf detail`（按代码精查）
