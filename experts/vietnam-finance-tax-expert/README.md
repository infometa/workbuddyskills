# Vietnam Finance & Tax Expert

一句话描述：为中资企业赴越投资与经营提供越南税务、会计、银行、外汇、审计及财务合规咨询的 AI 专家。

## 类型

Agent 型（单个 AI 专家）

## 功能

- **税务咨询**：企业所得税（CIT）、增值税（VAT）、个人所得税（PIT）、外国承包商税（FCT）、特别消费税（SCT）、税收优惠与转让定价。
- **会计与审计**：越南会计准则（VAS）、财务报表编制、年度审计要求、电子发票制度。
- **银行与融资**：外资银行开户、资本金汇入、贸易融资、项目融资、跨境担保。
- **外汇管理**：SBV 外汇规定、利润汇回、外币借款登记、汇率风险应对。
- **支付与结算**：越南电子支付、跨境人民币结算、B2B 结算。
- **补贴与保险**：投资优惠、政府补贴、企业强制保险与商业保险方案。
- **财务合规**：AML、税务稽查应对、海关合规、关联交易披露、税务争议解决。

## 使用示例

- 越南企业所得税税率是多少？有哪些税收优惠政策？
- 外资企业在越南开立银行账户需要哪些流程？
- 越南外汇管理有哪些限制？利润汇回中国如何操作？

## 内置工具套件（v1.1.0 新增）

除语料问答外，专家包内置可运行的测算与查询工具（`references/tools/`），把定性建议升级为可复算的数字：

- `calculators.py` — CIT 估算、工资总成本（含 21.5% 社保 + 工会费 + PIT 代扣）、FCT 代扣 / gross-up
- `location_sim.py` — 选址成本模拟器（跨 8 省对比土地/厂房/工资/运营成本）
- `tariff.py` — 进口关税测算（关税 + VAT 10% + 特别消费税）
- `refs.py` — 越南合规日历 / 中资赴越 ODI 出境流程速查
- `search_corpus_semantic.py` — 可选语义检索升级（无模型时自动回退 TF-IDF）

结构化数据与模板位于 `references/data/`（成本库、合规日历、ODI清单、DTA税率、关税参考）与 `references/templates/`（董事会决议、IRC申请清单）。

**能力卡片（v1.2.0 新增）**：用户问"你能做什么 / 有什么功能"或开场寒暄时，专家会自动弹出可点击的能力卡片（`references/capability_card.html`），点一下即触发对应工具——无需记忆命令。

**交互式工具（v1.3.0 新增）**：专家包内置浏览器内实时交互卡（`references/widgets/`），用户可亲手输入/拖动、图表即时响应，每个卡均可一键导出可打印报告（HTML→PDF）：
- `payroll_calc.html` — 用工总成本计算器（改人数/月薪 → 月/年成本 + 构成环图实时变）
- `location_calc.html` — 选址成本对比卡（勾省份 + 调人数/面积 → 实时排名柱状图，最低成本高亮）
- `tariff_calc.html` — 进口环节税测算卡（输 CIF + 选品类 → 关税/特别消费税/VAT 实时拆解）

当用户提出对应问题时，专家优先弹出交互卡而非静态文字。

运行示例：

```bash
PY="python"                                 # 平台托管 Python 运行时（默认已配置；Windows 亦可用 python3）
TOOLS="<专家包根目录>/references/tools"       # <专家包根目录> 在执行时由运行环境解析为插件安装目录
"$PY" "$TOOLS/calculators.py" cit --revenue 50_000_000_000 --cost 38_000_000_000 --rate 10 --free 4 --half 9
"$PY" "$TOOLS/location_sim.py" --headcount 100 --factory_area 5000 --land_area 50000
```

## 头像

头像位于 `avatars/expert.png`：
- 格式：PNG
- 尺寸：512×512 px
- 大小：321 KB

## 安装

将专家包目录放到 WorkBuddy 专家目录下（`<WORKBUDDY_HOME>` 即用户主目录下的 `.workbuddy`，如 `C:\Users\<你的用户名>\.workbuddy` 或 `~/.workbuddy`）：

```
<WORKBUDDY_HOME>/plugins/marketplaces/my-experts/plugins/vietnam-finance-tax-expert/
```

## 依赖与运行环境

- **Python 运行时**：脚本由平台托管 Python 运行（命令中 `PY="python"` 即平台默认运行时；Windows 下如不可用可改 `python3`），无需另行安装 Python。
- **核心检索（默认路径，无额外依赖）**：`search_corpus.py` / `calculators.py` / `location_sim.py` / `tariff.py` / `refs.py` 仅依赖 Python 标准库，**开箱即用**。
- **语义检索（可选增强）**：`search_corpus_semantic.py` 在无模型时自动回退 TF-IDF，无需依赖；如需启用向量语义检索，可安装：
  ```bash
  pip install sentence-transformers
  ```
- **验证**：运行 `python references/tools/calculators.py cit --help` 能打印参数说明即环境正常。

## 打包分享

```bash
zip -r vietnam-finance-tax-expert.zip vietnam-finance-tax-expert/
```
