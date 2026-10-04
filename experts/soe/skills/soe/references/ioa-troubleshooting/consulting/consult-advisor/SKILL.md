---
name: consult-advisor
description: Use when the user asks product capability or purchasing and renewal questions, suspects iOA conflicts with third-party software, requests process guidance, or the problem cannot be clearly matched to another capability.
---

# 咨询顾问能力

本能力负责咨询判断与兜底：产品能力、购买续费、流程事项、第三方软件冲突判责，以及无法明确归类问题的归属判断。本能力不读取服务级知识文件，必要时路由到其他技术能力。所有操作遵守公共响应与安全规范。

## 适用范围与排除项

- **适用**：产品能力与适用场景咨询、续费/采购影响、流程与升级路径、第三方软件是否与 iOA 冲突、多因素混合且暂时无法归类的问题。
- **排除**：已有明确模块证据的技术故障，直接读取对应技术子能力文档；本能力用于先判责、再加载技术参考，不替代技术排障。

## 意图分诊

| 现象 | 处理方式 |
|---|---|
| 安装 iOA 后第三方软件异常 | 咨询判责：不因时间先后归因 |
| 产品能力/版本功能咨询 | 按资料确认，资料不足如实说明 |
| 续费、采购、权益 | 解释影响边界，转正式商务渠道 |
| 流程、升级、工单 | 给出路径与非敏感信息清单 |
| 无法归类 | 候选归属 + 最小风险核实路径 |

## 工作流程

### 第三方软件冲突判责

1. 先拆意图：软件异常是技术问题，续费影响是商务问题，分开回答。
2. 不因“装了 iOA 之后才坏”直接判定是 iOA 导致；时间先后不等于因果。
3. 按低风险顺序给出判责路径：先查是否存在进程管控、实时防护或 DLP 命中记录，再查系统与应用自身错误；涉及停用模块的对比测试属于变更，必须说明风险、最小范围、回滚方式并等待明确批准，不能作为默认步骤。
4. 只有在获得具体模块命中证据后，才追加读取 `references/ioa-troubleshooting/policy-management/policy-control/SKILL.md` 或 `references/ioa-troubleshooting/security-protection/security-detect/SKILL.md` 做技术排查；未命中时如实说明“未发现关联证据”。
5. 技术分支完成后检查原始意图清单，继续回答商务/流程问题，不得遗漏。

### 能力与商务咨询

1. 产品能力只依据随包知识回答，注明适用版本/部署；资料未覆盖时不编造。
2. 价格、折扣、合同与权益承诺一律转正式产品或商务渠道，不自行报价。
3. 续费影响只说明功能与服务风险，不制造紧迫感。

### 未命中兜底

1. 给出候选归属（可并列多个），证据不足时明确“暂无法可靠排序”。
2. 给出最小风险、只读优先的核实路径，并列出非敏感补充信息清单。
3. 禁止编造服务、字段、错误码或产品能力。

## 服务文档路由

本能力无独立服务知识。需要技术证据时由同一 Agent 按现象追加读取：

- 管控/冲突类：`references/ioa-troubleshooting/policy-management/policy-control/SKILL.md` 及其服务文档
- 防护/拦截类：`references/ioa-troubleshooting/security-protection/security-detect/SKILL.md` 及其服务文档
- 接入与访问类：`references/ioa-troubleshooting/trusted-access/access-login/SKILL.md` 及其服务文档
- 终端状态类：`references/ioa-troubleshooting/endpoint-management/endpoint-asset/SKILL.md` 及其服务文档
- 平台/后台类：`references/ioa-troubleshooting/platform-operations/platform-ops/SKILL.md` 及其服务文档

## 跨能力联动

- 同一 Agent 保留原始意图清单与已核实证据，按需读取一个或多个技术子能力文档，再把技术结论与咨询结论合并为一份答复；每个意图都必须有结论或明确待核实分支。

## 输出验收

- 技术故障按四段式输出，纯咨询按“直接结论 → 条件与边界 → 待确认信息”精简模板输出。
- 复合意图逐项标记“已确认 / 待核实 / 已转分支”，不吞并、不遗漏。
- 不报价、不承诺权益、不因时间先后归因。
- 未命中兜底给出候选归属与核实路径，无证据不排序。
