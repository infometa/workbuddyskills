# Diff 模式策略

> 引用方：`commands/diff.md`

---

## 变更影响范围分析策略

diff 模式核心差异化能力。indexer 在 diff 模式下额外负责影响范围扩展。

### 执行策略

```
对每个变更代码文件：
  1. LSP documentSymbol -> 获取导出的公开方法/函数
  2. LSP findReferences -> 找到直接引用该文件导出符号的文件
  3. LSP incomingCalls -> 上游调用文件（<=2 层）
  4. LSP outgoingCalls -> 下游依赖文件（1 层）
  5. 标记为 relatedFiles，分类写入 stage1-context.json
```

### 关联文件分类

```
callerFiles[]  = 调用变更方法的上游文件（Controller/Handler/Service）
calleeFiles[]  = 被变更方法调用的下游文件（DAO/Repository/外部服务）
peerFiles[]    = 同层级兄弟文件（同包/同模块其他实现）
```

### 关联文件元数据

| 字段 | 说明 |
|------|------|
| `filePath` | 文件路径 |
| `relationType` | `"caller"` / `"callee"` / `"peer"` |
| `linkedSymbols` | 具体关联点（changedMethod, callSite） |
| `hasEntryPoint` | 是否含入口点 |
| `hasAuthAnnotation` | 是否含权限注解 |
| `hasSensitiveOp` | 是否含敏感操作 |

### 上限控制

关联文件总数不超过 `changedCodeFiles x 3`，超出按优先级裁剪：
1. 含入口点的 callerFiles（最高）
2. 含权限注解的文件
3. 含敏感操作的 calleeFiles
4. 其他 peerFiles（最低）

### 分析层次

| 层次 | 内容 | 适用场景 |
|------|------|---------|
| L1 调用点上下文 | +-30 行 | 所有关联文件 |
| L2 数据流追踪 | 入口到变更方法 | 含入口点的 callerFiles |
| L3 权限链完整性 | 权限保护验证 | 变更方法涉及敏感操作 |

---

## Agent 提示词注入模板

### vuln-scan

```
[扫描模式] diff-incremental
[变更文件] {changedCodeFiles}（全维度深度扫描）
[关联文件] stage1-context.json > relatedFiles[]
[关联文件扫描策略]
  - callerFiles：L1 + L2（验证输入校验完整性）
  - calleeFiles：L1（验证前置条件 + 检查变更是否暴露新的 Sink）
[关联文件预算上限] 25%
[优先级] 变更文件 > callerFiles（含入口点） > calleeFiles > 其他
```

### logic-scan

```
[扫描模式] diff-incremental
[变更文件] {changedCodeFiles}（全维度深度扫描）
[关联文件] stage1-context.json > relatedFiles[]
[关联文件扫描策略]
  - callerFiles：L1 + L2（验证权限链完整性）
  - calleeFiles：L1（检查变更是否破坏已有权限约束）
[关联文件预算上限] 25%
[优先级] 变更文件 > callerFiles（含权限注解） > calleeFiles > 其他
```

### red-team

```
[扫描模式] diff-incremental
[变更文件] {changedCodeFiles}（全维度深度扫描）
[关联文件] stage1-context.json > relatedFiles[]
[关联文件扫描策略]
  - callerFiles：L1 + L2（验证信任边界完整性）
  - calleeFiles：L1（组合攻击链候选）
  - peerFiles：L1 only（组合攻击链候选）
[关联文件预算上限] 25%
[优先级] 变更文件 > callerFiles（含入口点） > calleeFiles > 其他
[重点维度] Q3 信任穿越（变更可能破坏已有信任关系）+ Q2 异常路径（变更引入新的逻辑缺陷）
```

---

## 漏洞链检测重点（diff 特有）

变更可能在调用链某环引入新风险，与上下游已有风险组合形成完整攻击路径：
- **权限绕过链**：变更 Service -> Controller 缺权限检查 -> 未授权访问
- **注入传播链**：变更数据处理 -> 上游未校验 -> 注入到 Sink
- **提权链**：变更角色判断 -> 影响下游权限决策
