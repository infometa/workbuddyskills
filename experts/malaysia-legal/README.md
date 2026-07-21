# 马来西亚法务法规专家

马来西亚法务法规合规专家，覆盖公司注册、知识产权、数据保护、诉讼争议、行业准入与公司合规。

## 类型

Agent 型（单个 AI 专家）

## 功能

- **法律条款咨询**：Companies Act / PDPA / Contracts Act / Employment Act 等法条查询与解读
- **公司注册与尽调**：SSM 公司注册信息查询、外资持股分析、董事股东结构核实
- **知识产权查册**：MyIPO 商标/专利/工业设计查询，IP 保护评估
- **数据保护合规**：PDPA 2010 合规分析、跨境数据传输、数据用户注册
- **诉讼与争议分析**：e-Kehakiman 涉诉记录查询、清盘风险分析、判决结果解读
- **行业准入与许可**：外资行业准入、NPRA 药品/化妆品许可、JAKIM 清真认证、CIDB 建筑资质
- **法律尽职调查**：企业法律尽调，涵盖公司注册、IP、诉讼、合规、监管许可

## 语料库

| 模块 | 内容 |
|------|------|
| Reference_Texts | 45 份法律/合规文献（Companies Act / Contracts Act / PDPA / Employment Act / Land Code 等） |
| DuckDB | 15 张法务合规表（574K 行），涵盖 NPRA 药品监管、法律援助、犯罪统计 |
| 引擎脚本 | duckdb_query.py / ref_text_search.py / data_verifier.py（离线验证） |
| API 模块 | SSM e-Info / e-Kehakiman / MyIPO 搜索指南 |

## 使用示例

- "外资在马来西亚注册公司需要什么文件？能不能100%持股？"
- "马来西亚 PDPA 2010 的数据保护合规主要有哪些要求？"
- "如何在马来西亚通过 MyIPO 查询商标？注册流程是怎样的？"
- "帮我查一下这家公司有没有涉诉记录"
- "马来西亚劳动合同的核心条款有哪些？"
- "Contracts Act 1950 对违约赔偿怎么规定？"
- "在马来西亚开设餐馆需要什么许可证？"

## 数据源

| 数据源 | 类型 | 站点 |
|--------|------|------|
| SSM e-Info | 公司注册 | site:ssm.com.my |
| e-Kehakiman | 诉讼查询 | site:ehakiman.kehakiman.gov.my |
| MyIPO | 知识产权 | site:myipo.gov.my |
| NPRA | 药品/化妆品监管 | DuckDB 离线数据 |
| JAKIM | 清真认证 | site:halal.gov.my |
| CIDB | 建筑资质 | site:cidb.gov.my |
| LHDN | 税务合规 | site:lhdn.gov.my |

## 安装

将 `malaysia-legal/` 整个目录放到 WorkBuddy 专家市场插件目录下即可。在 WorkBuddy 中使用「管理专家」功能刷新后可见。

## 打包分享

```bash
zip -r malaysia-legal.zip malaysia-legal/
```
