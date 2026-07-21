# 错误恢复手册

> 引用方：commands/project.md、commands/diff.md、agents/*.md

---

## 1. 编排器层异常

### StreamTimeout / MaxTurnsExceeded

```
1. Glob 检查 agents/{agent-name}.json 是否存在
2. 文件存在 且 writeCount>=1 -> 视为 partial 完成，不重试
3. 文件不存在或 writeCount=0 -> 重试 1 次
4. 重试仍失败 -> 按产物完整性规则处理
```

> 文件状态优先于 Task 返回；已有有效数据不因错误丢弃。

### Agent 产物完整性检查失败

仅允许重试缺失/损坏 agent **1 次**，重试仍失败则终止并输出：

```
**扫描过程中遇到异常**，部分分析结果未完成。
已保留的结果：**{readyAgents}**
未完成的分析：**{failedAgents}**
建议：重新运行扫描命令重试。
```

---

## 2. Agent 层异常

### 接近 max_turns 限制

立即写入已完成数据，设置 `status: "partial"`，记录 lastCheckpoint。

### LSP 不可用

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md > LSP 降级规则`（完整降级策略和错误处理表见该节）

自动降级为 Grep+Read 继续扫描，不询问用户；扫描完成后在报告或日志中提示用户安装 LSP 以获得更高置信度。

### 增量写入失败

重试 1 次 -> 写备用路径 -> 下个周期合并 -> 连续 3 次失败则停止。

---

## 3. 数据层异常

| 场景 | 处理 |
|------|------|
| JSON 解析失败 | 跳过该 Agent，使用其余结果 |
| merge_findings.py 失败 | 跳过损坏 agent 合并其余 |
| Agent 重启续做 | 从 lastCheckpoint 继续 |

---

## 4. 降级策略汇总

> LSP 降级完整规则（错误处理表 + 逐文件回退策略）见 `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/initialization.md > LSP 降级规则`。

| 异常场景 | 操作 | 数据影响 |
|---------|------|---------|
| LSP 不可用 | Grep+Read | 置信度降低 |
| Agent Timeout | 使用已落盘数据 | partial |
| 接近 max_turns | 立即写入并退出 | partial |
| 单 Agent 失败 | 跳过 | 覆盖率降低 |
| 产物完整性失败 | 重试 1 次 -> 终止 | 不伪造数据 |

核心原则：宁可 partial 也不伪造 completed。
