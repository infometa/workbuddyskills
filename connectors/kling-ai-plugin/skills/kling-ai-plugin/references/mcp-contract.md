# 生成请求结构

仅在构造生成工具的外层 payload 时读取。能力发现、选型与模块加载见[能力发现](capability-discovery.md)和[参数规则](model-parameters.md)；素材管理按自身工具 schema，查询与 UI 按任务结果流程执行。

- 外层请求结构与值的编码以当前工具 `inputSchema` 为准，模型能力以 `who_am_i` 为准。生成工具通常使用 `model`、`arguments[]`、`inputs[]`、`rationale`、`taskTraceId`；不按示例补未声明字段。
- `model` 是当前账号在该入口返回的规范名。`arguments[]` 为 `{name, value}`；当前工具要求所有 `value` 为字符串，包括数字、布尔值和 JSON 数组。每个参数名只出现一次。
- `inputs[]` 为 `{name, inputType, url}`，只传所选模型声明的槽位及真实资源引用；`inputType` 按实时工具 schema。没有输入时省略，不能省略必填素材。
- `rationale` 简述用户目标与选参理由，不代替用户提示词。提示词不用于绕过字段或枚举限制。
- 同一目标复用 UUIDv7 `taskTraceId`，无关目标才创建新值。它仅用于追踪，不是幂等键；不能据此自动重放收费请求。
- 工具输入结构与 `who_am_i` 所选模型的参数、条件约束同时成立。工具泛化描述或其他型号示例不覆盖当前模型的能力；结构冲突按能力发现流程刷新，仍不一致时停止。
- Element 支持及图片/视频主体类型以 `who_am_i` 中目标入口、所选模型的声明和条件限制为准，不能只看是否列有 `elements`，也不用工具描述或历史举例覆盖账号能力。

提交返回 `generationId` 只表示创建/受理，后续按[任务结果](task-results.md)处理；不因返回 `creditsConsumed` 就声称生成完成。
