# 新加坡财税金融专家 (sg-finance-tax)

面向中国企业、跨境贸易公司、投资机构及在新加坡运营企业的 AI 财税金融合规咨询专家。

## 安装

将专家包解压到插件目录后在 WorkBuddy 中注册：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/sg-finance-tax/
```

SingStat MCP 已内置在 `.codebuddy-plugin/plugin.json` 中，注册后自动随专家加载。首次使用需在 WorkBuddy 连接器管理页面点击 "singstat" 的 "Trust"，之后对话中输入 `@sg-finance-tax` 即可使用。

## 类型

Agent 型（单个 AI 专家）

## 核心能力

| 领域 | 覆盖 |
|------|------|
| 税务 | IRAS CIT/GST/WHT/DTA/MLI/中新DTA/FTC/TP/VCC/S13W/印花税/个税/财产税 |
| 会计 | SFRS(I)/FRS/SFRS for SE/XBRL Taxonomy 2026/FRS 116/非S$功能货币 |
| 审计 | ISCA SSAs/ACRA PMP/Hot Review/审计豁免3选2/审计轮换PIE |
| 银行 | MAS Banking Act/Full Bank/QFB/Wholesale/中资银行FID速查/Notice 626-637-649/开户实务 |
| 融资 | EnterpriseSG EFS 7类贷款/EDG/MRA/PSG/Startup SG |
| 支付 | PS Act 2019/SPI/MPI/MC/PSN01-02/PayNow/eGIRO/FAST/SGQR |
| 外汇 | S$NEER basket-band-crawl/MAS Notice 755-757/CIPS/ODI监管链 |
| 合规 | RORC/PDPA/CDSA/TSFA/CG Code 2018/AML-CFT/CDD-EDD/PEP/STR |
| 劳动法 | MOM EP/COMPASS/S Pass/WP/Employment Act/CPF 费率表 |
| 保险 | Insurance Act/Insurer Types/WICA/Notice 133-126-314 |

## 使用示例

- "新加坡公司企业所得税怎么算？新公司有什么优惠？"
- "中国母公司向新加坡子公司收技术服务费，WHT 怎么处理？"
- "EP 月薪多少能申请？COMPASS 怎么打分？"
- "新加坡公司开户要什么材料？中国 UBO 会不会加难度？"
- "小公司审计豁免条件是什么？"
- "EDG 和 MRA 补贴有什么区别？"
- "中新 DTA 股息/利息/特许权使用费的优惠税率是多少？"
- "中国公司 ODI 备案要走哪些步骤？"

## 数据源

基于 300+ 官方公开页面，全部可在中国网络环境（不开启 VPN）下访问。

## 文件结构

```
sg-finance-tax/
  agents/sg-finance-tax.md           # 主 Agent 语料库（3000+ 行）
  avatars/expert.png                 # 专家头像（512×512px）
  .codebuddy-plugin/plugin.json      # 注册元数据（含 SingStat MCP）
  README.md                          # 本文件
```
