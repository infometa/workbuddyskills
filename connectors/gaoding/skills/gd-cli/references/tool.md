# Tool 创作

耗时较长的创作优先加 `--async`，提交一次后，使用返回的 `taskId` 执行 `gd-cli task get <taskId>`。running 时隔数秒查询同一 ID；completed 时读取 result。输出为空、查询超时、unknown 或宿主等待结束，都不能作为再次生成的依据。没有 ID 时用 task list 定位原任务。省略 --async 时命令仍同步等待，继续等待同一进程。状态处理见 [错误处理](errors.md)。

按顺序执行：

```bash
gd-cli tool list
gd-cli model list --tool <tool>
gd-cli model get <model>
gd-cli tool call <tool> --input request.json --async
gd-cli task get <taskId>
```

`tool list` 给出可用 Tool；`model list` 和 `model get` 给出当前可用 Model、说明、费用、预估耗时和结构化参数。`model get` 的 `parameters` 是所选 Model 的实际调用元数据：遵循 `required`、`type`、`description`，SELECT 参数使用 `options[].value`，required 参数带 `default` 时在用户未指定时显式传入默认值。`usageDescription` 描述跨字段规则，例如视频 mode 对首尾帧或素材字段的要求；这类组合不能只从单个字段推断。不要把列表值固化在提示或脚本中。

按所选 Model detail 构造 JSON：提供全部 required 字段；SELECT 参数使用 `options[].value`；required 字段带 default 且用户未指定时，在输入中显式使用该 default。存在 width、height、resolution 等专用字段时，将用户要求写入对应结构化参数，不要只写在 prompt 中。`tool call <tool> --schema` 返回整个 Tool 下所有 Model 的参数并集，只用于 Tool 级发现；选定 Model 后以 `model get` 的参数和 `usageDescription` 为准。

务必将 `model get <model>` 返回的 `model` 原样放在请求 JSON 的顶层 `model` 字段（即运行时的 `arguments.model`），与所选 Model 的参数字段并列；不要只复制 `parameters`。例如：

```json
{
  "model": "<model>",
  "prompt": "<required prompt>",
  "<parameter>": "<value>"
}
```

同步输出（或异步任务 completed 时的 result）包含 `content` 和 `usage`。`content` 是文本或资源链接；`usage` 包含所选模型及模型目录公布的稿豆价格区间，不表示实际扣费。

交付多个资源时，将每个资源链接、返回名称、本地保存路径和展示名称作为一条记录一起处理；下载、重命名或调整顺序时保持对应，不按请求中的顺序重新配对。交付前核对每个最终链接的文件内容与名称一致；名称不足以辨认时查看资源内容。
