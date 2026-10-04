# iHR CLI 共享命令契约

本文记录 WorkBuddy Connector Skills 使用的跨命令可观察行为。具体业务输入、分页、确认、错误与恢复边界以所属 Domain reference/help/schema 为准。

## Connector 可用命令族

| 命令族 | 典型入口 | 当前契约来源 |
| --- | --- | --- |
| Shortcut | `ihr-cli <domain> +<action>` 或 resource-scoped `+` 命令 | 命令 help、所属 Domain reference 与 Shortcut 实现 |
| Metadata Command | `ihr-cli <domain> <resource> <action>` | `schema`、所属业务 reference 与 Metadata Runtime |

Connector Skills 不使用未打包 Domain、raw 网关命令、自写 HTTP client 或其他方式扩大能力面。

## stdout 与 stderr

- Shortcut 和 Metadata Command 的成功或失败 JSON envelope 写入 stdout。
- 根 help 只输出领域和逐层发现入口；资源、动作、参数和示例通过对应层级的 `--help` 或 `schema` 按需获取。
- warning 可以写入 stderr。不能假设所有诊断都只在 stderr；先按所属命令解析 stdout，再结合进程退出状态判断结果。

## JSON envelope

业务命令使用 `success/command/request/response/error` 家族：

```json
{"success":true,"command":"staffSearch","request":{},"response":{}}
```

不同命令的 `response` shape 由具体业务契约决定，不能全局假设业务数据位于固定字段。

## 进程退出状态

- `0`：命令按声明完成，并成功写出最终结果或 dry-run 预览。
- `1`：命令已识别，但配置、鉴权、网络、业务响应、响应解析、文件或输出失败。
- `2`：真实业务执行前因未知命令/flag、参数缺失或冲突、非法 JSON、缺少显式确认等原因被拒绝。
- shell 找不到 binary、信号终止、panic 或 broken pipe 不属于应用正常返回的 `0/1/2` 范围。

调用者仍须读取结构化 error code 和逐命令契约，以区分交还 WorkBuddy Connector 重连、修正参数、缩小范围、重试或停止。

## 文件输出

- Shortcut 的 `--output-file <file>` 把最终 JSON envelope 写入私有权限文件，同时 stdout 仍输出结果。
- Metadata Command 的 `--output <file>` 把原始响应 body 写入私有权限文件，stdout envelope 返回文件信息。

两种文件参数语义不同，不能互换。任何本地文件写入都遵循对应 Domain Skill 的确认要求。
