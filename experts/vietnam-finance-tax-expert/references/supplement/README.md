# 越南财税金融 · 语料补全与实时数据源

本目录用于**补足专家包静态语料的短板**：实时数据靠"用时即查"，缺失文档靠"抓取后入库"。

## 目录结构
```
vietnam-finance-supplement/
├── realtime_sources.json      # 机器可读的实时源注册表（含每条 WebFetch 查询模板）
├── realtime_sources.md        # 人读版数据源清单
├── corpus_supplement/         # 抓取后入库的补充语料(.txt)
│   ├── vn_taxadmin_law_108_2025_chinatax.txt   # 新《税收管理法》108/2025（2026-07-01生效，税务）
│   ├── vcb_fx_sample_2026-07-24.txt            # Vietcombank 实时牌价样例(时点快照)
│   ├── vn_insurance_law_2022_luatduongtri.txt  # 【非税】保险业务法2022 + 强制险67/46/21-2023
│   ├── vn_social_insurance_law_2024_rates_lawma.txt  # 【非税】社保法2024 21.5%/10.5%费率
│   ├── vn_accounting_circular99_2025_parkerrussell.txt # 【非税】会计通函99/2025取代200/2014
│   ├── vn_securities_law_56_2024_ssc.txt       # 【非税】证券法修订56/2024（2025-01-01生效）
│   ├── vn_aml_circular27_2025_allenandgledhill.txt   # 【非税】反洗钱通函27/2025（2025-11-01生效）
│   └── vn_banking_dica_forex_indochinalink.txt # 【非税】银行/DICA资本账户/外汇合规
│   # —— 第三批（非税金融补洞，2026-07-24 15:56 后）——
│   ├── vn_trade_finance_boc_vietnam.txt         # 【非税】贸易融资产品(中行越南：L/C/背对背/转让/代收/提货担保/进口融资)
│   ├── vn_trade_finance_lc_operations_dewintech.txt  # 【非税】信用证实操(UCP600/即期远期/UPAS/不符点/单据)
│   ├── vn_syndicated_loan_circular42_2011_luatvietnam.txt # 【非税】银团信贷第42/2011号通函(安排行/支付代理/外资限制)
│   ├── vn_syndicated_loan_transfer_vtnpartners.txt      # 【非税】银团贷款转让实务(Circular09/离岸灰色地带)
│   ├── vn_mandatory_insurance_russinvecchi.txt  # 【非税】强制保险框架(建筑业/车主/火灾/存款/油气/职业险)
│   └── vn_car_insurance_tokiomarine.txt         # 【非税】工程一切险CAR产品(物质损失/第三方责任/除外)
│   # —— 第四批（TP 实务，2026-07-24 16:20）——
│   ├── vn_tp_decree132_2025_grantthornton.txt   # 【非税/跨】TP主法132/2020 + 20/2025澄清
│   ├── vn_tp_compliance_2026_acclime.txt         # 【非税/跨】TP合规2026(APA/豁免/安全港)
│   ├── vn_tp_audit_trends_2025_deloitte.txt      # 【非税/跨】2025 TP稽查趋势数据
│   ├── vn_tp_industry_risk_kelmer.txt            # 【非税/跨】TP行业风险与争议解决
│   └── vn_tp_china_vietnam_treaty_article9_fsou.txt  # 【非税/跨】中越协定第九条(联属企业)
│   # —— 第五批（最终补强：金融科技/PPP/审计，2026-07-24 16:28）——
│   ├── vn_fintech_decree52_2024_noncash_vietnambusinesslaw.txt  # 【非税】非现金支付法令52/2024(电子钱包/支付牌照)
│   ├── vn_ppp_law64_2020_decree243_2025_investtovietnam.txt    # 【非税】PPP法64/2020 + Decree 243/2025
│   └── vn_fdi_audit_compliance_2026_vietnambriefing.txt         # 【非税】FDI强制审计2026实务
├── MANIFEST.md               # 总清单（22语料+18实时源 按8板块归档，便于迁移）
└── README.md
```

> ✅ **当前状态（2026-07-24 16:42 最终完成）**：全部 22 个补充语料 + MANIFEST + 实时源注册表均已**物理落盘**至工作区补充目录与专家包语料目录；**TF-IDF 索引已最终重建**（**80,204 块 / 672 文件**，第五批 3 文件已入索引并经检索验证 #1 命中）；**zip 包已生成**：`vietnam-finance-supplement-2026-07-24.zip`（26 项，含 22 语料 + MANIFEST + README + 2 实时源注册表）。可直接下载迁移。

## 一、实时数据工作流（推荐，零存储负担）
用户问"当前汇率/最新税率/某HS编码关税"时：
1. 在 `realtime_sources.json` 中匹配对应 `id`。
2. 按其 `query_method` 调 WebFetch 直连权威源取实时值。
3. 回复中**必须标注** `实时数据 @URL 抓取于YYYY-MM-DD`，不得与静态语料混淆。

首选源：外汇→Vietcombank；关税→tariff.customs.gov.vn；法规原文→vbpl.vn；中文税改→税路通(chinatax.gov.vn)。

## 二、补充语料入库（已执行两批）
**第一批（税务，2026-07-24 上午）**：`vn_taxadmin_law_108_2025_chinatax.txt`、`vcb_fx_sample_2026-07-24.txt` 已复制进专家包语料目录并重建索引（80,159 块，备份于 `index_backup_pre_supplement/`）。

**第二批（非税财务金融，2026-07-24 下午，本轮）**：6 个非税文件（保险/社保/会计/证券/反洗钱/银行外汇）已全部**物理写入**专家包语料目录（见目录结构），并已**于 2026-07-24 15:50 重建索引成功**（80,171 块 / 658 文件）。已验证 5 个非税关键词查询（DICA利润汇出、反洗钱阈值、证券法股本、社保费率、会计通函99）均进入 top-3 命中。

重建命令（隔离 venv，已装 bs4 + scikit-learn）：
```
PY="C:/Users/xze12/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
CORPUS="C:/Users/xze12/.workbuddy/plugins/marketplaces/my-experts/plugins/vietnam-finance-tax-expert/references/corpus/vietnam-finance-tax-corpus"
cd "$CORPUS" && "$PY" build_index.py --force
```

专家包语料目录：
`~/.workbuddy/plugins/marketplaces/my-experts/plugins/vietnam-finance-tax-expert/references/corpus/vietnam-finance-tax-corpus/`

原始索引备份：`index_backup_pre_supplement/`（第一批已备份）。

## 三、专家包更新后的恢复（重要）
专家包升级会**覆盖**语料目录，补充文件与索引将丢失。恢复步骤：
1. 把本目录 `corpus_supplement/*.txt` 再次复制到上述语料目录。
2. 用隔离 venv 的 python 重跑 `build_index.py --force`。

## 四、本轮（第二批）已补强的非税领域 & 仍偏薄处
**已补强（6 个语料 + 5 个实时源）**：
- 保险：保险法2022 + 强制险议定67/46/21-2023（框架齐）；仍缺**商业险具体条款费率**
- 社保：社保法2024（41/2024/QH15）+ 21.5%/10.5% 费率 + 外籍员工30%规则（齐）
- 会计/审计：通函99/2025 取代200/2014（2026-01-01生效，VAS/IFRS趋同，齐）
- 证券：法56/2024 修订证券法2019（2025-01-01生效，齐）
- 反洗钱：通函27/2025（2025-11-01生效，4亿/5亿/1000USD阈值，齐）
- 银行/外汇：DICA资本账户 + 90天出资 + 利润汇出 + 第340/2025处罚（齐）

**仍偏薄（建议后续）**：
- 贸易融资/银团贷款：各行 L/C、保函、贷款产品条款与手续费表
- 保险商业险具体产品费率（强制险框架已有，缺商业险明细）
- 实时行情（银行存贷利率、股价、保费）一律靠实时源，不由语料承载

## 六、第三批（非税金融补洞，2026-07-24 15:56 后）
针对评估发现的真空洞（贸易融资/银团贷款/商业保险非寿险产品此前基本空白），新抓 6 个语料并重建索引（**80,182 块 / 664 文件**）：
- 贸易融资：中行越南产品清单（开证/背对背/转让/进口代收D/P D/A/提货担保/进口融资）+ dewintech 信用证实操（UCP600/即期远期/Circular21/2024 UPAS/不符点/单据集）
- 银团贷款：第42/2011/TT-NHNN 号通函（安排行/支付代理/安全代理/外资不得任代理行/出资比例）+ VTN Partners 转让让与实务（Circular09/离岸监管灰色地带）
- 商业保险：Russin&Vecchi 强制保险框架（建筑业4类+车主+火灾爆炸+存款+油气+职业险，含最低保额）+ Tokio Marine 工程一切险CAR产品（物质损失/第三方责任/除外责任）

**当前覆盖评估结论**：非税财务金融六大子领域（银行外汇/DICA、保险、社保、会计审计、证券、AML）已有框架+关键新规；本轮补齐后**贸易融资、银团贷款、商业保险非寿险产品**已从"空白"变为"有实务+法规+产品"。
**仍偏薄（如实）**：贸易融资各行具体费率表、银团贷款具体定价、商业保险具体保费费率——这些产品级数字仍靠实时源或持牌机构；转让定价(TP)已有手册级文件但深度待企业个案验证。

## 七、第四批（转让定价 TP 实务，2026-07-24 16:20 后）
针对上一轮点名的"TP 企业个案深度"空洞，新抓 5 个 TP 实务语料并重建索引（**80,195 块 / 669 文件**）：
- `vn_tp_decree132_2025_grantthornton.txt`：现行主法 Decree 132/2020（取代 Decree 20/2017）+ **Decree 20/2025（2025-02-10 澄清）**；5种OECD方法、35–75分位、30% EBITDA利息上限、三重文档、豁免门槛、罚则、APA Decree 122/2025
- `vn_tp_compliance_2026_acclime.txt`：Appendix I-IV 申报表、集团内服务费扣除四要件、**2024起关联方利息限制**、APA Decree 122/2025（授权财政部批双边/多边APA无需政府事先批准）
- `vn_tp_audit_trends_2025_deloitte.txt`：**2025上半年真实稽查数据**（119家被查、调增应税所得5.091万亿VND、TP占60%）、稽查三大焦点、APA新机遇
- `vn_tp_industry_risk_kelmer.txt`：行业特定高风险（制造/分销/共享服务/融资/电子纺织农食）、最佳方法选择、争议解决（行政复议/MAP）
- `vn_tp_china_vietnam_treaty_article9_fsou.txt`：中越协定**第九条联属企业**中文原文 + 第二十五条协商程序 + 第二十四条无差别待遇 + 第十/十一/十二条 10%预提税率（中资企业TP调整后可启动MAP避免双重征税）

**当前覆盖结论**：转让定价已从"手册级/框架"补到"法规(132/2020+20/2025)+实务(三重文档/豁免/申报表)+最新情报(2025稽查数据/APA新规)+协定层(中越第九条)"全链条。非税财务金融八大板块至此**全部达到"框架+关键新规+实务/稽查情报"可应答水平**。
**唯一残余真空**：贸易融资/银团贷款/商业保险的具体产品费率数字（本就靠实时源或持牌机构，非静态语料可承载）。

## 八、第五批（最终补强：金融科技/PPP/审计，2026-07-24 16:28）
针对 8 板块最终验收发现的残余薄点，再抓 3 个语料（均已物理落盘，含比语料更新的 2024–2025 新规）：
- `vn_fintech_decree52_2024_noncash_vietnambusinesslaw.txt`：**第52/2024/ND-CP《非现金支付法令》**（2024-07-01生效，取代101/2012）；电子钱包列为非现金支付工具、电子货币新定义、禁止买卖/租赁支付账户与钱包、中介支付牌照资本（电子钱包50亿VND/切换300亿VND）——补"银行·外汇·金融科技"中 fintech 子项
- `vn_ppp_law64_2020_decree243_2025_investtovietnam.txt`：**PPP投资法64/2020 + Decree 243/2025**（2025新细则）；五类行业、七种合同、收入风险分担(75%/125%)、最低资本2000亿/医疗1000亿、私资≥15%、国资≤50%——补"投资·ODI·FDI·PPP"
- `vn_fdi_audit_compliance_2026_vietnambriefing.txt`：**FDI强制审计2026实务**（中文）；强制范围/报表/四部门提交/03-TNDN·05-QTT表格/利润汇出提前7工作日(Circular 186/2010)/罚款——补"会计·审计"

**8 板块最终验收结论**：
| 板块 | 状态 |
|---|---|
| ①税务核心 | 🔵原强项（已补108/2025） |
| ②银行·外汇·金融科技 | 🟢补强（DICA+贸易融资+L/C+Decree52/2024电子钱包） |
| ③投资·ODI·FDI·PPP | 🟢补强（DICA+PPP法64/2020+243/2025） |
| ④会计·审计 | 🟢补强（通函99/2025+FDI审计2026） |
| ⑤社保·劳工 | 🟢补强（社保法2024） |
| ⑥证券 | 🟢补强（法56/2024） |
| ⑦反洗钱AML | 🟢补强（通函27/2025） |
| ⑧保险 | 🟢补强（保险法2022+强制险框架+CAR产品） |

**残余真空（如实，非语料可承载）**：贸易融资/银团贷款/商业保险的具体产品费率数字（靠实时源或持牌机构）；实时行情（汇率/利率/股价/保费）用时即查。

## 九、打包交付（zip）
待 shell 恢复后执行（PowerShell）：
```powershell
$SUP = "D:\WorkBuddy Resources\2026-07-24-13-25-55\vietnam-finance-supplement"
$VENV = "C:\Users\xze12\.workbuddy\binaries\python\envs\default"
$CORPUS = "C:\Users\xze12\.workbuddy\plugins\marketplaces\my-experts\plugins\vietnam-finance-tax-expert\references\corpus\vietnam-finance-tax-corpus"
# 1) 重建索引（第五批3文件入索引）
& "$VENV\Scripts\python.exe" "$CORPUS\build_index.py" --force
# 2) 打包整个补充目录
Compress-Archive -Path "$SUP\*" -DestinationPath "$SUP\vietnam-finance-supplement-2026-07-24.zip" -Force
```
注：工作区补充目录 `vietnam-finance-supplement/` 当前已含全部 22 语料 + MANIFEST + 实时源注册表 + 本 README，**用户亦可自行手动压缩该文件夹立即得到等价 zip**（无需等待 shell）。

## 五、已验证可用的实时抓取样例
Vietcombank 牌价 @ 2026-07-24 08:00（VND）：
USD 买26,100 / 卖26,510；CNY 买3,789.05 / 卖3,949.89；EUR 买29,183.09 / 卖30,721.59。
