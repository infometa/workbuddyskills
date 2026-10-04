# 图表模板库

## 目录

- [A. 时间轴图模板](#a-时间轴图模板)
- [B. 主体关系图模板](#b-主体关系图模板)
- [C. 证据关联图模板](#c-证据关联图模板)
- [D. 流程图模板](#d-流程图模板)
- [E. 争议链路图模板](#e-争议链路图模板)

---

## A. 时间轴图模板

### A.1 标准时间轴（单阶段）

```mermaid
timeline
    title {案件/项目标题}
    section {阶段名称}
        {YYYY-MM-DD} : {事件1描述}
        {YYYY-MM-DD} : {事件2描述}
        {YYYY-MM-DD} : {事件3描述}
```

### A.2 多阶段时间轴

```mermaid
timeline
    title {案件/项目标题}
    section {阶段一名称}
        {YYYY-MM-DD} : {事件A}
        {YYYY-MM-DD} : {事件B}
    section {阶段二名称}
        {YYYY-MM-DD} : {事件C}
        {YYYY-MM-DD} : {事件D}
    section {阶段三名称}
        {YYYY-MM-DD} : {事件E}
        {YYYY-MM-DD} : {事件F}
```

### A.3 含证据锚点的时间轴

```mermaid
timeline
    title {案件标题}事实时间轴
    section {签约履行}
        2023-01-15 : 签订{合同名称} [📄材料A/3/2]
        2023-02-20 : 支付首付款{金额} [📄材料A/8/1]
    section {争议发生}
        2023-04-01 : {违约事实} [⚠️材料B/12/1]
        2023-06-15 : 协商未果 [💾材料C/1-3/1]
    section 诉讼阶段
        2023-09-20 : 提起诉讼
```

### A.4 含断点标注的时间轴

```mermaid
timeline
    title {案件标题}事实时间轴
    section 合同签订
        2023-01-15 : 签订合同
        2023-02-20 : 支付首付款
    section 履行过程
        2023-03-01 : 部分交付
        2023-04~06 : ⚠️ 履行记录缺失
    section 争议阶段
        2023-07-01 : 发现违约
```

---

## B. 主体关系图模板

### B.1 基础主体关系图

```mermaid
flowchart LR
    subgraph "群体A名称"
        a["{主体A名称}"]
        b["{主体B名称}"]
    end
    subgraph "群体B名称"
        c["{主体C名称}"]
        d["{主体D名称}"]
    end

    a -->|"{关系标签1}"| b
    a -->|"{关系标签2}"| c
    b -.->|"{弱关系标签}"| d

    classDef key fill:#1d4ed8,color:#ffffff,stroke:#1e3a8a,stroke-width:2px
    classDef normal fill:#eff6ff,color:#1e3a8a,stroke:#60a5fa,stroke-width:1px
    classDef weak fill:#f9fafb,color:#6b7280,stroke:#d1d5db,stroke-width:1px,stroke-dasharray:5 5

    class a,b key
    class c normal
    class d weak
```

### B.2 股权控制关系图

```mermaid
flowchart LR
    p["自然人A"] -->|控股80%| c1["公司甲"]
    p -->|参股30%| c2["公司乙"]
    c1 -->|全资子公司| c3["公司丙"]
    c1 -.->|实际控制| c4["公司丁"]

    classDef person fill:#7c3aed,color:#fff,stroke:#5b21b6,stroke-width:2px
    classDef company fill:#1d4ed8,color:#fff,stroke:#1e3a8a,stroke-width:2px
    classDef sub fill:#eff6ff,color:#1e3a8a,stroke:#60a5fa,stroke-width:1px
    classDef ctrl fill:#fef3c7,color:#92400e,stroke:#fbbf24,stroke-width:1px,stroke-dasharray:5 5

    class p person
    class c1 company
    class c2,c3 sub
    class c4 ctrl
```

### B.3 交易关系图（含资金流向）

```mermaid
flowchart LR
    buyer["{买方A}"] -->|"买卖合同<br/>价款{金额}"| seller["{卖方B}"]
    buyer ==>|"支付{金额}"| seller
    seller -->|委托代收| agent["{代收方C}"]
    seller -.->|未按时交付| buyer

    classDef key fill:#0369a1,color:#fff,stroke:#075985,stroke-width:2px
    classDef normal fill:#e0f2fe,color:#0c4a6e,stroke:#38bdf8,stroke-width:1px
    classDef warn fill:#fee2e2,color:#991b1b,stroke:#dc2626,stroke-width:2px
    classDef flow fill:#dcfce7,color:#166534,stroke:#22c55e,stroke-width:2px

    class buyer,seller key
    class agent normal
```

---

## C. 证据关联图模板

### C.1 基础证据关联图

```mermaid
flowchart TB
    subgraph "待证事实"
        f1["事实主张1"]
        f2["事实主张2"]
        f3["事实主张3"]
    end
    subgraph "证据支撑"
        e1["证据1 🟢强"]
        e2["证据2 🟡中"]
        e3["证据3 🔴弱"]
    end

    e1 -->|直接证明| f1
    e2 -->|间接佐证| f2
    e3 -.->|关联| f2
    e1 -.->|关联| f3

    classDef fact fill:#fef3c7,stroke:#d97706,stroke-width:2px
    classDef evidence-strong fill:#dcfce7,stroke:#16a34a,stroke-width:2px
    classDef evidence-medium fill:#fef9c3,stroke:#ca8a04,stroke-width:1px
    classDef evidence-weak fill:#fee2e2,stroke:#dc2626,stroke-width:1px

    class f1,f2,f3 fact
    class e1 evidence-strong
    class e2 evidence-medium
    class e3 evidence-weak
```

### C.2 含证据缺口标注的证据关联图

```mermaid
flowchart TB
    subgraph "待证事实"
        f1["合同成立"]
        f2["违约事实"]
        f3["损失金额"]
    end
    subgraph "证据支撑"
        e1["合同原件 🟢"]
        e2["微信记录 🟡"]
        e3["待补充 🔴"]
    end

    e1 --> f1
    e2 --> f2
    e3 -.->|证据缺失| f3

    classDef fact fill:#fef3c7,stroke:#d97706,stroke-width:2px
    classDef gap fill:#fee2e2,stroke:#dc2626,stroke-width:2px,stroke-dasharray:5 5

    class f1,f2,f3 fact
    class e3 gap
```

---

## D. 流程图模板

### D.1 基础流程图（含分支）

```mermaid
flowchart TD
    start(["开始"]) --> step1["步骤1"]
    step1 --> step2["步骤2"]
    step2 --> decision1{{"判断条件?"}}
    decision1 -->|条件A| step3a["步骤3A"]
    decision1 -->|条件B| step3b["步骤3B"]
    step3a --> step4["步骤4"]
    step3b --> step4
    step4 --> e_end(["结束"])

    classDef startend fill:#0f766e,color:#fff,stroke:#115e59,stroke-width:2px
    classDef process fill:#eff6ff,color:#1e3a8a,stroke:#3b82f6,stroke-width:1px
    classDef decision fill:#fff7ed,color:#9a3412,stroke:#fdba74,stroke-width:2px

    class start,e_end startend
    class step1,step2,step3a,step3b,step4 process
    class decision1 decision
```

### D.2 含循环的流程图

```mermaid
flowchart TD
    start(["开始"]) --> review["审核材料"]
    review --> decision1{{"材料齐全?"}}
    decision1 -->|否| fix["补充材料"]
    fix --> review
    decision1 -->|是| process["处理审批"]
    process --> decision2{{"审批通过?"}}
    decision2 -->|否| modify["修改方案"]
    modify --> process
    decision2 -->|是| done(["出具结果"])
    done --> e_end(["结束"])

    classDef startend fill:#0f766e,color:#fff,stroke:#115e59,stroke-width:2px
    classDef process fill:#eff6ff,color:#1e3a8a,stroke:#3b82f6,stroke-width:1px
    classDef decision fill:#fff7ed,color:#9a3412,stroke:#fdba74,stroke-width:2px
    classDef loop fill:#f9fafb,color:#6b7280,stroke:#d1d5db,stroke-width:1px,stroke-dasharray:5 5

    class start,e_end,done startend
    class review,process process
    class decision1,decision2 decision
    class fix,modify loop
```

---

## E. 争议链路图模板

### E.1 基础争议链路图

```mermaid
flowchart LR
    d1["争议焦点1"] --> e1a["我方证据A"]
    d1 --> e1b["我方证据B"]
    d1 --> c1["对方抗辩"]
    d2["争议焦点2"] --> e2a["我方证据C"]
    d2 --> c2["对方抗辩"]
    d1 -.->|关联| d2

    classDef dispute fill:#fee2e2,color:#991b1b,stroke:#dc2626,stroke-width:2px
    classDef support fill:#dcfce7,color:#166534,stroke:#22c55e,stroke-width:1px
    classDef counter fill:#fef3c7,color:#92400e,stroke:#fbbf24,stroke-width:1px
    classDef link fill:#f9fafb,color:#6b7280,stroke:#d1d5db,stroke-width:1px,stroke-dasharray:5 5

    class d1,d2 dispute
    class e1a,e1b,e2a support
    class c1,c2 counter
```

### E.2 含风险标注的争议链路图

```mermaid
flowchart LR
    d1{违约认定} --> e1[合同条款-强]
    d1 --> e2[未交付证据-中]
    d1 --> c1[不可抗力抗辩]
    d2{损失赔偿} --> e3[损失计算-中]
    d2 --> e4[下游取消-弱]
    d1 --> d2

    classDef dispute fill:#fee2e2,color:#991b1b,stroke:#dc2626,stroke-width:2px
    classDef high_risk fill:#fee2e2,color:#991b1b,stroke:#dc2626,stroke-width:3px
    classDef support fill:#dcfce7,stroke:#16a34a,stroke-width:1px
    classDef counter fill:#fef3c7,stroke:#fbbf24,stroke-width:1px

    class d1,d2 dispute
    class e1,e2,e3 support
    class c1 counter
    class e4 high_risk
```

---

## F. 攻防矩阵图模板（Markdown 表格）

### F.1 标准攻防矩阵（5列完整版）

```markdown
### 攻防矩阵：{案件类型}

| 我方主张 | 对方可能抗辩 | 我方回应策略 | 支撑证据 | 风险等级 |
|---------|------------|------------|---------|---------|
| {主张1} | {抗辩1} | {回应策略1} | {证据1} | 🟢 低 |
| {主张2} | {抗辩2} | {回应策略2} | {证据2} | 🟡 中 |
| {主张3} | {抗辩3} | {回应策略3} | {证据3} | 🔴 高 |

**风险等级说明**：🟢 低 = 证据充分/法律明确；🟡 中 = 存在一定争议空间；🔴 高 = 证据薄弱/法律适用不明
```

### F.2 法官版攻防矩阵（4列精简版）

```markdown
### 攻防矩阵：{案件类型}（庭审版）

| 我方主张 | 我方回应策略 | 支撑证据 | 风险等级 |
|---------|------------|---------|---------|
| {主张1} | {回应策略1} | {证据1} | 🟢 |
| {主张2} | {回应策略2} | {证据2} | 🟡 |
| {主张3} | {回应策略3} | {证据3} | 🔴 |
```

### F.3 团队版攻防矩阵（6列扩展版）

```markdown
### 攻防矩阵：{案件类型}（团队工作版）

| 序号 | 我方主张 | 对方可能抗辩 | 我方回应策略 | 支撑证据 | 风险等级 | 备注 |
|------|---------|------------|------------|---------|---------|------|
| 1 | {主张1} | {抗辩1} | {回应策略1} | {证据1} | 🟢 | {备注1} |
| 2 | {主张2} | {抗辩2} | {回应策略2} | {证据2} | 🟡 | {备注2} |
| 3 | {主张3} | {抗辩3} | {回应策略3} | {证据3} | 🔴 | 需补强证据 |
```

---

## G. 数据结构化表模板（Markdown 表格）

### G.1 金额拆解表

```markdown
### {项目名称}金额构成表

| 项目 | 金额（元） | 占比 | 计算依据 | 证据 | 可视化 |
|------|-----------|------|---------|------|--------|
| {项目1} | {金额1} | {占比1}% | {依据1} | {证据1} | ▓▓▓▓▓▓░░░░ |
| {项目2} | {金额2} | {占比2}% | {依据2} | {证据2} | ▓▓▓▓░░░░░░ |
| **合计** | **{总金额}** | **100%** | — | — | ▓▓▓▓▓▓▓▓▓▓ |

> 计算校验：{项目1} + {项目2} = {总金额} ✅
```

### G.2 资金流水表

```markdown
### 资金流水明细表

| 日期 | 方向 | 对方账户 | 金额（元） | 用途/备注 | 证据 |
|------|------|---------|-----------|----------|------|
| {日期1} | 支出 | {账户1} | {金额1} | {用途1} | {证据1} |
| {日期2} | 收入 | {账户2} | {金额2} | {用途2} | {证据2} |
| **合计** | — | — | **{净额}** | — | — |
```

### G.3 损失构成表

```markdown
### 损失构成明细表

| 损失类型 | 直接损失 | 间接损失 | 计算方式 | 证据 | 风险 |
|---------|---------|---------|---------|------|------|
| {类型1} | {金额1} | {金额2} | {方式1} | {证据1} | 🟢 |
| {类型2} | {金额3} | {金额4} | {方式2} | {证据2} | 🟡 |
| **合计** | **{总额}** | **{总额}** | — | — | — |
```

### G.4 比例对比表

```markdown
### {对比主题}比例对比表

| 对比项 | 数值 | 占比 | 对比基准 | 差异 | 可视化 |
|--------|------|------|---------|------|--------|
| {项A} | {数值A} | {占比A}% | {基准} | {差异A} | ▓▓▓▓▓▓▓▓░░ |
| {项B} | {数值B} | {占比B}% | {基准} | {差异B} | ▓▓▓▓░░░░░░ |
```
