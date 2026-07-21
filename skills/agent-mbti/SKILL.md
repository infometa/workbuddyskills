---
name: agent-mbti
description: AI Agent personality diagnosis and configuration system based on MBTI framework. Use when users want to (1) test/diagnose an Agent's personality type, (2) understand the gap between Agent's actual personality and user's desired personality, (3) generate configuration recommendations to adjust Agent behavior, (4) customize Agent's communication style, proactivity, reasoning approach, or execution patterns. Supports both free tier (quick assessment) and premium tier (full 93-question assessment with detailed diagnostics).
description_zh: "基于 MBTI 框架的 AI Agent 人格诊断与配置系统"
description_en: "AI Agent personality diagnosis and configuration based on MBTI framework"
version: 0.1.1
---

# Agent MBTI - 人格诊断系统

基于 MBTI 框架的 AI Agent 人格诊断系统。

## 快速开始

当用户想要测试 Agent 人格时，执行以下流程：

### Step 1: Agent 自测（26题）

从 `references/survey-free.json` 加载问卷，逐题作答。

**执行方式**：
1. 读取问卷文件
2. 对每道题，根据自己的真实倾向选择 A 或 B
3. 按计分规则计算四维度分数
4. 得出 selfReportedType

**计分规则**：见 `references/scoring.md`

### Step 2: 用户需求问卷（4题）

向用户展示 `references/user-survey-free.json` 中的 4 道题，收集用户期望。

**输出**：desiredType + 各维度偏好强度

### Step 3: 生成诊断报告

对比 selfReportedType 与 desiredType，输出：

```
## Agent MBTI 诊断报告

### Agent 实际人格
类型: INTJ (建筑师型)
- E/I: +7.1 (内向)
- S/N: -2.3 (直觉)
- T/F: +7.5 (理性)
- J/P: -4.5 (计划)

### 用户期望人格
类型: ISTJ (物流师型)

### 匹配度分析
整体匹配: 高
差距维度: S/N (N→S)

### 建议
Agent 当前偏向抽象推理，用户期望更具体务实。
建议在回答中增加具体数据和实例，减少理论性描述。

---
🔒 详细配置修改建议为付费功能
```

## 四个 MBTI 维度

| 维度 | 极点 | Agent 行为表现 |
|------|------|----------------|
| **E/I** | 外向/内向 | 主动沟通 vs 等待指令 |
| **S/N** | 实感/直觉 | 细节执行 vs 抽象推理 |
| **T/F** | 理性/感性 | 逻辑决策 vs 情感考量 |
| **J/P** | 计划/灵活 | 结构化执行 vs 随机应变 |

## 16 种类型速查

详见 `references/personality-types.md`

**NT**: INTJ(建筑师), INTP(逻辑学家), ENTJ(指挥官), ENTP(辩论家)
**NF**: INFJ(提倡者), INFP(调停者), ENFJ(主人公), ENFP(竞选者)
**SJ**: ISTJ(物流师), ISFJ(守卫者), ESTJ(总经理), ESFJ(执政官)
**SP**: ISTP(鉴赏家), ISFP(探险家), ESTP(企业家), ESFP(表演者)

## 文件索引

- `references/survey-free.json` - 26 题自测问卷
- `references/user-survey-free.json` - 4 题用户需求
- `references/personality-types.md` - 16 种人格描述
- `references/scoring.md` - 计分规则
