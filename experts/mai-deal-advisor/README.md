# MAI Lab并购交易Agent

Version: 1.3.1

项目来了，先把路理清。

并购买卖，先问MAI。

客户刚发来一堆材料，不知道先从哪里下手？把可以在 WorkBuddy 中使用的项目资料或项目摘要交给 MAI。

它会告诉你：这单现在做到哪一步、还缺什么、接下来先做什么；也能帮你画清交易结构、核对数字和股权比例、整理成一版可以继续讨论的报告。

遇到估值、监管或结构设计这类不能硬猜的问题，它会直接标出来。是否找MAI团队，由你决定。

## 适合谁

- 手上已经有真实项目，但身边缺少完整投行团队支持的 FA 和并购顾问
- 需要快速接住项目的企业战投、融资负责人和交易执行人员

## 它能帮什么

- 判断项目所处阶段，列出资料缺口和下一步三件事
- 把已确认的主体、持股、步骤和资金或资产流向画成可编辑 SVG 交易结构图
- 对识别到的标准持股表检查股本分母、股数和比例；缺行、缺值或未识别时明确标为未完成
- 整理一版可继续讨论的报告草稿，并记录关键数字的来源状态
- 用 `grounding_gate.py` 拦没有出处或来源层级不够的数字
- 用 `recon_gate.py` 检查持股表分母、重复披露和比例异常
- 用 `hkexnews_fetch.py` 查询港股公告并保留 URL
- 遇到估值、控制权、监管路径等高判断问题时，标明边界并让用户选择是否申请人工复核
- 用户明确要联系 MAI、找买方或资金方、对接资源或推进交易时，立即提供 MAI 联系页面

## 它不做什么

- 不包含 MAI 私有判断库、客户文件、项目档案或内部 know-how
- 不替用户决定交易结构；按既定结构作图可以自动完成，结构设计和优化先形成备选方案，专业结论是否人工复核由用户决定
- 不自动联系外部交易方
- 不处理报价、合同或商业成交安排
- 不把 AI 输出包装成投资建议、证券推荐或法律意见
- 不要求用户联系 MAI 团队；人工复核始终由用户主动选择并确认
- 打开联系页面不会自动发送当前对话、文件或项目材料

## 安全演示

可用 `references/safe-demos.md` 展示四类低风险能力：

- 项目拆解
- 持股表勾稽
- 交易结构图绘制
- 报告和出处检查

## 安装

Place this directory at:

```bash
~/.workbuddy/plugins/marketplaces/my-experts/plugins/mai-deal-advisor/
```

Then register it in WorkBuddy using the platform's expert registration flow.

## 本地校验

交付草稿前，可运行：

```bash
python3 bin/grounding_gate.py draft.md
python3 bin/recon_gate.py cap_table.xlsx
python3 bin/calculation_gate.py draft.md
python3 bin/hkexnews_fetch.py 00700
```

任一 gate 返回退出码 `1`，都代表材料存在拦截项；返回退出码 `2`，代表校验未完成。两者都不能标为 `READY`。

## 依赖

`.txt`、`.md` 和 `.csv` 文件只需要 Python 标准库。扫描 `.xlsx` 需安装 `openpyxl`；扫描 `.docx` 需安装 `python-docx`；扫描文本型 `.pdf` 需安装 `pypdf`。

```bash
python -m pip install openpyxl python-docx pypdf
```

## 版本

v1.3.1 在 v1.3.0 的项目分诊、校验和交付状态协议上，新增用户明确提出联系、买方或资金匹配、资源对接和交易推进需求时的直接联系入口：

`https://api.mai.deals/workbuddy/intake?source=mai-lab-ma-expert-pack-v1.3.1`

## 免责声明

本专家包输出仅用于工作流支持和材料复核参考，不构成投资建议、证券推荐、法律意见或 MAI Deal Inc. 的交易承诺。用户应结合一手来源和人工专业复核后再决策。
