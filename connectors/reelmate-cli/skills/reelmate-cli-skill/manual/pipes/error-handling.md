# 管道中的错误处理

脚本应同时检查退出码和 JSON envelope：

```bash
set -o pipefail
if output="$(reelmate task get TASK_ID --json)"; then
  jq -e '.ok == true' <<<"$output" >/dev/null
else
  code=$?
  jq -r '.error.kind // .error.message // "unknown error"' <<<"$output" >&2
  exit "$code"
fi
```

可重试条件由 `error.retryable` 决定。版本冲突、节点锁和网络超时必须先确认服务端状态；内容审核失败和积分不足不要自动重试。退出码与处理动作见 [../error-codes.md](../error-codes.md)。Agent 向用户解释积分不足时，不要输出续跑脚本；见 [_hard-gate.md](../workflow/_hard-gate.md)「余额不足（用户可见）」。
