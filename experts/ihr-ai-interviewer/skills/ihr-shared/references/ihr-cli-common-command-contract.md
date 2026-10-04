# ihr-cli 共享命令契约

本文只记录当前源码和测试已经证明的跨命令可观察行为。它不是 Interface Meta、权限模型、业务命令契约或未来 Runtime 目标；具体命令仍需在所属 reference/help/schema 中说明自己的输入、分页、确认、错误与恢复边界。

## 命令族

当前 `ihr-cli` 至少包含以下命令族，它们不共享完全相同的输入和输出形态：

| 命令族 | 典型入口 | 当前契约来源 |
| --- | --- | --- |
| 框架命令 | `help`、`version`、`auth`、`config`、`schema`、`monitor` | 命令 help 与框架实现 |
| Shortcut | `ihr-cli <domain> +<action>` 或 resource-scoped `+` 命令 | 命令 help、所属 Domain reference 与 Shortcut 实现 |
| Metadata Command | `ihr-cli <domain> <resource> <action>` | `schema`、所属业务 reference 与 Metadata Runtime |
| Raw interface | `ihr-cli interface +get/+post/...` | `ihr-interface` Skill/reference 与 Raw Runtime |

不能因为多个命令都输出 JSON，就假设它们支持相同 flags、相同 envelope 或相同业务响应路径。

## stdout 与 stderr

- Shortcut、Metadata Command 和 Raw interface 的成功或失败 JSON envelope 当前都写入 stdout。
- `version`、部分 config/auth/status/monitor 等框架 JSON 命令也写入 stdout；help 和交互式 device login 可以输出人类可读文本。
- 根 help 只输出框架命令、业务领域和逐层发现入口；资源、动作、参数和示例继续通过对应层级的 `--help` 或 `schema` 按需获取。
- 框架初始化、monitor、登录等已实现 warning 写入 stderr。
- 当前不能承诺“所有诊断都进入 stderr”；脚本应先按所属命令族解析 stdout，再结合进程退出状态判断结果。

## 当前 JSON envelope

Shortcut、Metadata Command 和 Raw interface 使用 `success/command/request/response/error` 家族：

```json
{"success":true,"command":"staffSearch","request":{},"response":{}}
```

框架 JSON 命令使用 `ok/message/data/error.type` 家族：

```json
{"ok":true,"message":"version","data":{}}
```

本文不定义安装、就绪或登录流程，也不生成授权命令、session 或等待步骤；这些流程只能回到当前 Agent 的可信安装/授权入口。各业务接口的 `response` shape 由具体命令契约决定；不能全局假设业务数据一定位于 `data`。

## JSON 格式

- JSON 输出以换行结束。
- `Auto` 模式在交互式终端使用缩进 JSON，在管道、重定向或普通非终端 writer 中使用紧凑 JSON。
- Shortcut 显式支持 `--pretty` 时强制格式化；Metadata Command 当前没有公共 `--pretty` 承诺。

## 进程退出状态

退出状态是本地 `ihr-cli` 进程的状态，不是 HTTP status，也不是业务响应体中的 `code`。

- `0`：命令按声明完成，并成功写出该命令要求的最终输出。包括 help、version、schema 查询成功、业务执行成功和成功生成 dry-run 预览。
- `1`：命令已经被识别，但执行依赖或运行环境失败。包括配置、鉴权、metadata 加载、stdin/输入文件读取、网络、HTTP、业务响应、响应解析、输出文件或可检测的 stdout 写入失败。
- `2`：调用在进入真实业务执行前被拒绝，调用者必须修改命令或补足显式安全前置条件。包括未知命令/子命令/action/flag、参数缺失、格式或范围错误、参数冲突、非法 JSON，以及 `HIGH/CRITICAL` Metadata Command 在非 dry-run 执行时缺少 `--yes`。
- `--dry-run` 不要求 `--yes`；成功生成预览返回 `0`。
- stdin/输入文件本身无法读取属于运行或环境 I/O 失败，返回 `1`；已经读取的内容为空、JSON 非法或不满足本地字段合同属于执行前输入拒绝，返回 `2`。
- 顶层、auth/config/monitor、Shortcut 和 Raw 的未知入口统一返回 `2`；框架、Shortcut、Metadata 和 Raw 可检测的必要 stdout writer failure 统一返回 `1`。
- 调用者仍应读取结构化 error code 和命令特有契约，以区分重新登录、修正参数、缩小范围、重试或停止等恢复动作。
- shell 找不到 binary、信号终止、panic、broken pipe 等 OS/运行时状态不属于应用正常返回的 `0/1/2` 范围。

## 响应头

Metadata Command 与 Raw interface 默认不输出上游响应头。只有调用者显式传入 `--include` 时，Raw transport 才把上游响应头原样加入 stdout envelope；当前不做额外脱敏。

## 文件输出

| 命令族 | 参数 | 当前行为 |
| --- | --- | --- |
| Shortcut | `--output-file <file>` | 把最终 JSON envelope 额外写入私有权限文件，同时 stdout 仍输出结果 |
| Metadata Command / Raw interface | `--output <file>` | 把原始响应 body 写入私有权限文件，stdout envelope 返回 `bodyFile/bodyBytes`，不再内联 body |

两种文件参数语义不同，不能互换。

## 证据边界

本文发布的是应用正常返回路径的统一 `0/1/2` 第一层分类，不替代逐命令输入、分页、确认、错误和恢复契约。当前证据来自 CLI、Shortcut、Metadata 和 Raw 四族框架退出码矩阵；help/schema 只能证明声明存在，不能单独证明运行行为。
