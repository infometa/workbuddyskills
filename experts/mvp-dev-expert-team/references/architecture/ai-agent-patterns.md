# AI Agent 工程化模式

> 基于 Excellent EvoMaster框架、SEO Agent、Harness Engineering实战蒸馏

## 一、Agent 自主进化：EvoMaster 框架

### 四层自主进化架构

```
┌─────────────────────────────────────┐
│     Evolution Controller 进化控制器   │
│  归因引擎 | 反思引擎 | Prompt进化 | 对抗验证  │
├─────────────────────────────────────┤
│     Execution Layer 执行层           │
│  工具调用 | 代码生成 | API请求 | 文件操作  │
├─────────────────────────────────────┤
│     Decision Layer 决策层            │
│  任务拆解 | 路由选择 | 策略切换 | 错误恢复  │
├─────────────────────────────────────┤
│     Perception Layer 感知层          │
│  输入解析 | 上下文理解 | 状态感知 | 反馈接收  │
└─────────────────────────────────────┘
```

### 四大引擎

| 引擎 | 功能 | 触发条件 |
|------|------|----------|
| 归因引擎 Attribution | 失败任务根因分析 | 任务失败时 |
| 反思引擎 Reflection | 成功/失败模式提取 | 每次任务完成后 |
| Prompt进化引擎 | 自动优化Prompt模板 | 积累足够数据后 |
| 对抗验证引擎 | 红队测试防漂移 | Prompt更新后 |

### SPAR 闭环

```
Sense(感知) → Plan(规划) → Act(执行) → Reflect(反思) → [循环]
```

- 任务成功率：87.3%（使用EvoMaster后）
- 每轮Reflect输出：改进建议 → 喂入下一轮Plan

## 二、多Agent协同模式

### SEO Agent 6角色系统

| 角色 | 职责 | 输入 | 输出 |
|------|------|------|------|
| Strategist | SEO策略 | 关键词数据 | 策略文档 |
| Writer | 内容撰写 | 策略文档 | 文章草稿 |
| Auditor | 质量审核 | 文章草稿 | 审核报告 |
| Pusher | 发布推送 | 审核通过的文章 | 发布确认 |
| Analyst | 数据分析 | 发布后数据 | 效果报告 |
| HomeOptimizer | 首页优化 | 效果报告 | 优化方案 |

**关键设计**：
- **48小时延迟反馈**：SEO效果需要时间观察，不能立即判断成败
- **Critic三轮挑战**：每篇文章经过3轮自我批判才发布
- **月度Supervisor评分**：长期效果评估和策略调整
- **三层安全防护**：内容安全/数据安全/操作安全

### 跨境电商5Agent系统

| Agent | 职责 |
|-------|------|
| 商品管理Agent | 商品CRUD、库存管理、价格同步 |
| 订单处理Agent | 订单流转、状态机、异常处理 |
| 物流跟踪Agent | 物流信息同步、异常预警 |
| 多语翻译Agent | 5语翻译、本地化适配 |
| 推荐引擎Agent | 7策略推荐、个性化排序 |

## 三、Harness Engineering 六层洋葱模型

| 层级 | 模块 | 核心能力 |
|------|------|----------|
| L1 | 上下文工程 | SESSION_BRIEF / workflow-state / 知识库索引 |
| L2 | 工具编排 | 统一接入矩阵 / 宿主Hooks运行时 |
| L3 | 指南与传感器 | 专家Playbook / 验证规则引擎 |
| L4 | 约束与权限 | 策略治理 / 权限感知Function Calling |
| L5 | 可观测性 | DORA度量 / ADR / 一致性检测 |
| 核心 | 模型能力 | 宿主提供，Harness不碰 |

**核心洞察**：同模型+同需求，没有Harness只有60%完成率，有Harness达98%完成率。

## 四、权限感知 Function Calling

```
用户请求
    ↓
RBAC权限过滤（在发送给LLM之前）
    ↓
LLM只能看到有权使用的工具
    ↓
生成工具调用
```

**关键原则**：LLM根本不知道被限制的工具存在，而非"知道但不能用"。

## 五、多模型路由策略

### 动态路由决策

```python
def route_model(task_type, priority, budget):
    if task_type == "code_generation":
        return ModelRoute(primary="claude", fallback=["gpt-4o", "deepseek"])
    elif task_type == "chinese_writing":
        return ModelRoute(primary="glm-5.1", fallback=["qwen", "gpt-4o"])
    elif task_type == "long_context":
        return ModelRoute(primary="gemini", fallback=["claude"])
    elif task_type == "fast_inference":
        return ModelRoute(primary="deepseek", fallback=["glm-5.1"])
    elif task_type == "multimodal":
        return ModelRoute(primary="gemini", fallback=["gpt-4o"])
```

### CircuitBreaker 熔断降级

```
主模型 → [失败] → 备选1 → [失败] → 备选2 → [失败] → 降级响应
     ↓ [连续3次失败] → 熔断10分钟
```

## 六、RAG 管道模式

### 自研三层漏斗

```
用户查询
    ↓
向量搜索 Top-50（pgvector HNSW）
    ↓
BM25 重排序（精准匹配加分）
    ↓
业务规则过滤（权限/时效/相关性）
    ↓
最终结果 Top-5
```

### 分块策略
- **滑动窗口**：固定大小+重叠区域
- **语义断点**：检测段落语义变化点作为切分依据
- **两者结合**：先语义断点粗切，再滑动窗口细切

### 双存储RAG
- 向量存储：语义搜索（"找相似"）
- 关系存储：结构化查询（"找精确"）
- 交叉验证：两种检索结果取交集，提高准确性

## 七、流式 Function Calling

### 增量累积模式
```
chunk1: tool_calls[0].function.name = "search"
chunk2: tool_calls[0].function.arguments += '{"qu'
chunk3: tool_calls[0].function.arguments += 'ery": "'
chunk4: tool_calls[0].function.arguments += 'ERP权限"}'
→ 完整调用：search(query="ERP权限")
```

### 递归调用
- _stream_with_tools 递归深度 max_depth=3
- 支持工具A调用→返回结果→工具B调用→返回结果→工具C调用

## 八、Agent 模式选型指南

| 需求场景 | 推荐模式 | 理由 |
|----------|----------|------|
| 单一任务自动化 | 单Agent + 工具链 | 简单高效 |
| 多步骤流水线 | 多Agent顺序协作 | 各阶段专业化 |
| 需要自我审查 | Agent + Critic | 内部质量保障 |
| 长期运行系统 | SPAR闭环 + 进化引擎 | 持续优化 |
| 企业级应用 | Harness + 权限感知 | 安全可控 |
| 高并发场景 | 多模型路由 + 熔断 | 可靠性保障 |
