# MAI Lab并购专家包

English name: MAI Lab M&A Expert Pack

Version: 1.0.1

并购买卖，先问 MAI。

一笔并购，方向要理清，报告要搭好，数字要有出处，股权要对得上，公告不能漏。MAI Lab并购专家包帮你把关键步骤串起来：梳理任务、搭建报告、核验数据与股权表、监控港股公告。遇到估值、交易结构、控制权或监管等复杂判断时，专家包会生成分诊卡，转交 MAI 团队复核。

## 适合谁

- 投行、FA、并购顾问
- 企业战投、融资负责人、交易执行团队
- 需要把并购草稿、监控清单、股权表或交付材料先过一遍的人

## 它能帮什么

- 把并购任务拆成可执行的报告结构
- 检查关键数字有没有一手来源
- 用 `grounding_gate.py` 拦没有出处或来源层级不够的数字
- 用 `recon_gate.py` 检查持股表分母、重复披露和比例异常
- 用 `hkexnews_fetch.py` 盯港股公告并保留 URL
- 遇到估值、控制权、监管路径等高判断问题时，生成 `[ESCALATE]` 分诊卡

## 它不做什么

- 不包含 MAI 私有判断库、客户文件、项目档案或内部 know-how
- 不自动联系外部交易方
- 不处理报价、合同或商业成交安排
- 不把 AI 输出包装成投资建议、证券推荐或法律意见

## 安全演示

可用 `references/safe-demos.md` 展示三类低风险能力：

- 港股公告查询
- 持股表勾稽
- 复杂交易问题分诊

## 安装

通过 WorkBuddy / CodeBuddy 专家市场的安装流程导入本专家包。安装后 `bin/` 目录下的脚本会自动加入 PATH，可在 Agent 和 Skill 中直接调用。

## 本地校验

交付草稿前，可运行：

```bash
grounding_gate.py draft.md
recon_gate.py cap_table.xlsx
hkexnews_fetch.py 00700
```

任一 gate 返回退出码 `1`，都代表材料还不能直接交付。

## 依赖

需 Python 3.10 或更高版本。`.txt` 和 `.md` 文件只需要 Python 标准库。扫描 `.xlsx` 需安装 `openpyxl`；扫描 `.docx` 需安装 `python-docx`。

```bash
python -m pip install "openpyxl>=3.0" "python-docx>=1.0"
```

## 版本

v1.0.1 是 WorkBuddy 上架兼容性修复版。后续版本继续使用语义版本号，并保持 intake source 分版本记录：

`https://api.mai.deals/workbuddy/intake?source=mai-lab-ma-expert-pack-v1.0.1`

> 注意：以上 URL 指向 MAI 外部分诊服务（非 WorkBuddy 平台管控），`source` 参数中的版本号需随专家包版本同步更新。升级版本时请同时修改 `agents/mai-deal-advisor.md` 中 `[ESCALATE]` 卡片内的同一 URL。

## 免责声明

本专家包输出仅用于工作流支持和材料复核参考，不构成投资建议、证券推荐、法律意见或 MAI Deal Inc. 的交易承诺。用户应结合一手来源和人工专业复核后再决策。
