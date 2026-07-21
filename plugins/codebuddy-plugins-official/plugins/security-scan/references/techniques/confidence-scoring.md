# 置信度评分规则

> 引用方：verifier（对抗审查后置信度参考）、verifier.py score（确定性自动评分）

> **确定性评分下沉**：置信度的三维度基础评分、traceMethod 上限、高置信度门控已下沉到 `verifier.py score` 脚本执行（零 LLM turns）。verifier Agent 在攻击链深度验证和对抗审查中产出 `verificationStatus`、`challengeVerdict`、`defenseSearchRecord` 等判定字段，评分由脚本自动完成。

---

## 评分公式

```
置信度 = 攻击链可达性分 + 防御措施分 + 数据源可控性分
```

总分 0-100，三维度独立评分后累加。

## 维度 1：攻击链可达性（满分 40）

| 等级 | 分值 | 判定条件 |
|------|------|---------|
| 高 | 36-40 | 完整可达：全链路代码验证 + LSP 确认 |
| 中高 | 25-35 | 部分可达：存在特定触发条件 |
| 中低 | 10-24 | 理论可达：含未确认环节或仅 Grep+Read 推断 |
| 低 | 0-9 | 未确认：链路严重不完整 |

步骤一/二影响：`verified + confirmed` -> 高分；`unverified` -> 上限 24；`not_verifiable` -> 上限 15。

## 维度 2：防御措施（满分 30）

分数越高表示防御越弱（风险越大）。

| 等级 | 分值 | 判定条件 |
|------|------|---------|
| 高（无防御） | 27-30 | 无防御或已确认无效 |
| 中高（可绕过） | 18-26 | 有防御但可绕过 |
| 中低（不确定） | 9-17 | 有防御但有效性不确定 |
| 低（有效防御） | 0-8 | 已确认有效防御 |

## 维度 3：数据源可控性（满分 30）

| 等级 | 分值 | 判定条件 |
|------|------|---------|
| 高（直接可控） | 27-30 | HTTP 参数/请求体/URL/上传文件 |
| 中高（间接可控） | 18-26 | 数据库中用户数据/消息队列/文件 |
| 中低（来源不明） | 9-17 | 来源不明或需复杂条件 |
| 低（不可控） | 0-8 | 内部生成/硬编码/环境变量 |

---

## 调整规则

### traceMethod 分级上限

| traceMethod | 上限 | 说明 |
|-------------|:---:|------|
| `LSP` | 100 | 无限制 |
| `Grep+AST` | 95 | LSP 不可用但有 tree-sitter AST 数据 |
| `Grep+Read` | 90 | LSP 不可用时的最高上限 |
| `unknown` | 50 | 链路严重不完整 |

### Grep+AST 说明

当 LSP 不可用但 tree-sitter AST 解析可用时（典型场景：Kotlin 等无 LSP 支持的语言），traceMethod 为 `Grep+AST`，置信度上限为 95。AST 提供比纯文本 Grep 更精确的函数/类定义和调用关系，但缺少 LSP 的跨文件类型推断和完整 call graph。

### Grep+Read 说明

当 LSP 不可用时，所有基于 Grep+Read 追踪的 finding 置信度上限为 90。
要达到 90 分仍需满足高置信度门控的全部 3 项条件。

### 步骤二调整

- `challengeVerdict = downgraded` -> -10
- `ahAction = downgrade` -> -20

---

## 高置信度门控（>=90）

需满足全部 3 项，任一未通过则上限设为 89：

> **注意**：此门控适用于所有 traceMethod。

1. `verificationStatus = verified` — 攻击链经代码级验证通过（蕴含：attackChain 完整、traceMethod 已明确、verifiabilityLevel 可验证、ahAction = pass）
2. `challengeVerdict = confirmed` 或 `escalated` — 确定性对抗审查后仍成立
3. `defenseSearchRecord` 非空 — 确实搜索过防御措施并记录结果

---

## 置信度等级

| 范围 | 操作 |
|------|------|
| >= 90 | 可自动修复 |
| 60-89 | 需人工审核 |
| < 60 | 仅供参考 |

---

## 外部影响叠加

- 扫描 Agent `confidenceCeiling` -> 最终置信度不超过此值
- LSP 补偿置信度 -> Ref: `techniques/lsp-compensation.md`
- 路径敏感分析 -> Ref: `techniques/lsp-compensation.md`

最终置信度 = min(traceMethod 上限, 门控上限, confidenceCeiling, 三维度评分)
