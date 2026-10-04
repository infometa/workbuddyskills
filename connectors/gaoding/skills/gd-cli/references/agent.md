# Agent 创作

耗时较长的创作优先加 `--async`，提交一次后，使用返回的 `taskId` 执行 `gd-cli task get <taskId>`。running 时隔数秒查询同一 ID；completed 时读取 result。输出为空、查询超时、unknown 或宿主等待结束，都不能作为再次生成的依据。没有 ID 时用 task list 定位原任务。省略 --async 时命令仍同步等待，继续等待同一进程。状态处理见 [错误处理](errors.md)。

先读取输入规范。需要指定 Model 时，也先读取实时 Model detail：

```bash
gd-cli agent send --schema
gd-cli model list --tool <tool>
gd-cli model get <model>
gd-cli agent send --input request.json --async
gd-cli task get <taskId>
```

继续已有创作时，从上一条结果读取 `message.contextId`，原样填入下一次请求；同一创作的后续规划、生成和修改沿用该 Context。首次创作省略此字段。续聊示例：

```json
{
  "message": {
    "contextId": "<上一条结果的 message.contextId>",
    "parts": [{ "text": "<用户的后续要求>" }]
  }
}
```

将用户要求和已确认信息放在 Text Part，区分图片可见特征与材质、功能等推断。未核实信息标为待确认，必要时向用户澄清；上一轮模型描述按其事实来源判断，不自动视为用户确认。交付文案保持相同的事实边界，风格、客群和场景设想作为建议表达。

需要指定 Model、生成参数或首尾帧时，在组装请求前读取 [生成约束与媒体角色](generation-constraints.md)。

也可用 `--input -` 从 stdin 读取 JSON。同步输出（或异步任务 completed 时的 result）包含 `message` 和本次 `agent send` 调用的实际稿豆消耗 `usage`，不包含其他调用的消耗；将最终文本、资源、服务端续作标识和实际消耗交付给用户。报告多次调用的总消耗时，只汇总实际收到的不同调用的 `usage`；同一调用重复查询不重复计费。引用单次费用时说明对应调用，未取得的费用不猜测。

交付多个资源时，将每个 URL Part 的 `url`、`filename`、本地保存路径和展示名称作为一条记录一起处理；下载、重命名或调整顺序时保持对应，不按请求中的顺序重新配对。交付前核对每个最终链接的文件内容与名称一致；名称不足以辨认时查看资源内容。

每轮后续创作都会生成新的 taskId；续聊沿用 result.message.contextId。Agent 异步由本机临时后台进程继续执行，完成后退出；请在同一台机器查询。后台终止或电脑关机可能导致 unknown，按已有结果和快照说明情况，不自动重新生成。
