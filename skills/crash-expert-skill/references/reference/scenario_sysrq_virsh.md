# 场景分析：SysRq 触发 / virsh dump

### 分析步骤

1. 确认是否因机器宕机无响应而触发的 SysRq/virsh dump
2. 如果是无响应，按照以下优先级分析：
   - 检查是否存在 soft/hard lockup（参考 `reference/scenario_lockup.md`）
   - 检查是否存在 hung task（参考 `reference/scenario_hung_task.md`）
   - 检查内存状态
   - 检查各 CPU 上的进程状态：`bt -a`、`runq`
