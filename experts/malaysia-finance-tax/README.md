# Malaysia Finance & Tax Expert

马来西亚财税金融专家 — 覆盖税务、会计、银行、融资、外汇、支付、审计、补贴、保险及财务合规的企业财税金融全栈情报专家。

## 能力范围

- **税务**：所得税、消费税(SST)、关税、转让定价、税务优惠
- **银行**：本地银行体系、企业开户、贷款产品、利率环境
- **融资**：股权/债务融资、PE/VC、政府补贴/激励
- **外汇**：汇率、外汇管制、跨境资金流动
- **支付**：FPX、DuitNow、PayNet、跨境支付合规
- **审计**：法定审计、MFRS、公司治理、反洗钱(AML)
- **保险**：强制保险、商业保险、ESG风险管理
- **财务合规**：公司注册、年报、信息披露、合规审查

## 语料库

- `Reference_Texts/` — 法律条文、政策文件、指南（56 份，~16.8M 字符）
- `Databases/` — DuckDB 结构化数据（33 张表，~28K 行，12 MB）
- `CSV_Datasets/` — 开放数据集（12 个，含 GDP、CPI、利率、汇率等）

## 数据源

- LHDN (lhdn.gov.my) — 税务
- BNM (bnm.gov.my) — 银行/外汇
- MOF (treasury.gov.my) — 财政/预算
- SSM (ssm.com.my) — 公司注册
- MIDA (mida.gov.my) — 投资激励
- SC (sc.com.my) — 证券监管
- Customs (customs.gov.my) — 关税
- Bursa Malaysia (bursamalaysia.com) — 上市规则
- data.gov.my — 开放数据

## 安装与依赖

```bash
pip install -r requirements.txt
```

主要依赖：`duckdb>=0.9.0`

可选依赖：`requests`（用于 fetch_with_fallback 在线抓取）

## 脚本工具

| 脚本 | 用途 |
|------|------|
| `scripts/fetch_with_fallback.py` | 四层降级在线抓取（直连→Google缓存→CORS网关→代理） |
| `Reference_Texts/scripts/build_duckdb.py` | 从 CSV 和 Reference_Texts 重建 DuckDB |
| `skills/malaysia-finance-tax/scripts/duckdb_query.py` | DuckDB 查询辅助 |
| `skills/malaysia-finance-tax/scripts/ref_text_search.py` | 语料库文本检索 |
| `skills/malaysia-finance-tax/scripts/data_verifier.py` | 数据完整性验证 |

## 版本

v1.0.0
