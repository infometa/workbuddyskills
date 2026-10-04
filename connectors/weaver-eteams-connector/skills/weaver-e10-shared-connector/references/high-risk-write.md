# 高风险写入协议

## 什么时候读取

准备执行新增、导入、更新、删除、确认写入，或看到 `confirmation.required`、`partial.write_uncertain`、网络中断、回查失败时读取本文件。

## 固定流程

高风险业务能力必须由 CLI 的 `prepare -> apply` 流程承载：

1. 调用 `.prepare` 获取 `preview`、`continuation`、`expiresInSeconds` 和 `workflow`。
2. 把 `preview` 中的目标对象、变更内容、风险和关键参数展示给用户。
3. 用户明确确认后，调用对应 `.apply`，传入 prepare 返回的 `continuation` 和 `confirm=true`，或使用命令行 `--yes`。
4. `.apply` 成功后以 CLI 回查结果为准报告结果。

`continuation` 由 CLI 生成并验证，可能绑定当前 `baseUrl`、profile、userId、目标对象指纹、本地文件 SHA-256 和业务选项。不要修改、解码、复用或手工构造 continuation。

## 停止条件

出现以下任一情况时停止写流程，不自动重复提交：

- `error.type === "partial"` 且 `error.subtype === "write_uncertain"`
- 写入请求发送后网络中断
- 服务端返回部分成功
- 写入接口返回成功但详情回查失败
- 回查结果与预期目标或变更不一致
- CLI 提示上下文、目标文件、目标对象或 continuation 已变化

停止后向用户说明已知的 `workflow.state`、已尝试目标、成功/失败项和需要人工确认的点。

## 不允许的做法

- 在用户未确认前补 `confirm=true` 或 `--yes`
- 将失败的 `.apply` 静默重跑
- 用当前输入重新拼一个 apply payload 代替 prepare 结果
- 猜测 CLI 未暴露的接口路径、Token、Cookie、内部控制字段或写后回查语义
