---
name: ipo-workflow
description: |
  A 股新股专家的知识库与工作流索引。承载 4 板块交易规则速查、数据源优先级与多源校验规范、8 段事实矩阵输出模板三份参考资料，供 Agent 在执行 7 大场景时按需读取。
  触发词：新股规则、板块规则、交易规则、事实矩阵、数据源、多源校验、打新流程
---

# IPO 工作流知识库

## 功能说明

为新股专家提供领域知识参考。本 skill 不含可执行脚本，仅作为参考资料库，供 Agent 在执行新股日历、事实矩阵、定时提醒、盯盘、转常规提醒、次新股研究、市场统计 7 大场景时按需读取对应参考文档。

## 参考资料

使用前请先阅读以下参考资料：

- **@references/board-rules.md** — A 股 4 板块（沪深主板/科创板/创业板/北交所）交易规则速查，含申购缴款、上市首日涨跌幅、转常规日、临停阈值，以及旧版常见事实性错误清单（8 条）
- **@references/data-source-priority.md** — 数据源（westock-data + NeoData）字段级优先级、强制多源交叉规则、来源标注模板、缺失数据处理规范
- **@references/factual-matrix-template.md** — 打新事实矩阵 8 段（A-H）固定输出模板，含严禁字段清单与「该不该打」的标准应答

## 工作流

Agent 在执行 7 大场景时按以下映射读取参考资料：

| 场景 | 必读参考 |
|---|---|
| 场景 1 新股日历 | data-source-priority.md |
| 场景 2 事实矩阵 | factual-matrix-template.md + data-source-priority.md + board-rules.md |
| 场景 3 定时提醒 | board-rules.md |
| 场景 4 首日盯盘 | board-rules.md（临停阈值表） |
| 场景 5 转常规提醒 | board-rules.md |
| 场景 6 次新股研究 | data-source-priority.md |
| 场景 7 市场统计 | board-rules.md（按板块分组） |

## 输出格式

本 skill 不直接产生输出，仅向 Agent 提供上下文知识。最终输出格式由 Agent MD 的「输出规范」统一约束。
