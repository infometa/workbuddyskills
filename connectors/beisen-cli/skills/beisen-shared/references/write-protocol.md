# 高风险写操作门禁协议（exit 10）

> 本文档是 beisen-shared 的子参考，由 SKILL.md 引用。
>
> **说明**：beisen-cli 当前所有方法均为读操作，不触发写操作门禁。本文档所述 `exit 10` / `--yes` / `--dry-run` 协议为写方法上线后的预留设计，当前版本不会出现 exit 10。Agent 仍应了解该协议，以便写方法可用时正确处理。

---

## 写操作通用要求

- **危险操作必须先展示操作摘要**（操作类型、目标对象、影响范围），用户确认后才执行。
- **单次批量写入/删除不超过 50 条**；超过时拆批并逐批确认。

---

## 高风险操作门禁（exit 10）

beisen-cli 对高风险写操作有强制确认门禁。当 Agent 不带 `--yes` 调用高风险命令时，CLI 返回 exit code 10 + 结构化 JSON（exit code 10 即为确认信号，不需要判断 `ok`）：

```json
{
  "type": "confirmation",
  "subtype": "confirmation_required",
  "risk": "high-risk-write",
  "action": "<command>",
  "hint": "add --yes to confirm"
}
```

### Agent 遇到 exit 10 时必须

1. 识别 `type == "confirmation"` 和 `subtype == "confirmation_required"`
2. 向用户展示操作摘要（操作类型、目标对象、影响范围、风险等级）
3. 等待用户显式回复"确认 / 同意 / 执行"
4. 用户确认后，在原始命令末尾追加 `--yes` 重试
5. 用户拒绝 → 终止流程，不要擅自改写参数或跳过门禁

### 绝对不允许

- 看到 exit 10 就默认加 `--yes` 静默重试（等于禁用安全门禁）
- 把 `confirmation_required` 当作网络错误或权限错误处理
- 在用户未明确同意前追加 `--yes` 重试
