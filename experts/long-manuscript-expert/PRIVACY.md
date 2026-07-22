# Privacy Notice / 隐私说明

## Default processing scope

默认处理范围仅限 `user-provided materials`：用户在当前对话或明确授权的任务中主动提供的提纲、笔记、访谈、草稿、成稿与修改要求。

专家包不会因为被安装就获得任意本地文件、账户或外部系统的访问权。任何工作区读取、写入或外部调用都需要宿主实际提供对应能力，并取得用户的 `explicit authorization`。

## Data minimization

`Data minimization` 是默认原则：只使用完成当前写作步骤所需的最小内容，只在必要时引用最小原文锚点，不为证明“记住了”而复制整篇文稿。

专家包不会主动收集、写入或输出：

- credential、Cookie、Token 或 password；
- stable user identifier 或可避免的账户标识；
- unnecessary full-manuscript copy；
- private local path 或与当前结果无关的设备信息。

如果用户材料中包含上述信息，专家应避免复述，建议删除或遮盖，并把相关内容视为待保护数据。

## Storage and telemetry boundary

This package defines `no hidden telemetry`, background collection, analytics upload, or stable-identifier tracking of its own.

The package `does not silently persist` manuscripts, conversation state, or a cross-session profile. 对话记录、文件保存、保留期限和删除能力由实际宿主或用户明确选择的存储表面控制，不由本专家包暗中扩展。

只有当前任务出现可见的成功写入回执时，专家才可以说明某个文件已保存；否则交付状态仅限当前对话中的可复制内容。

## Optional external capabilities

外部导入、事实查证、文件导出或归档仅是可选增强。调用前应说明目的与数据范围，确认能力可见、相关且获授权；失败时应披露失败并回退到对话内成果。专家包本身不承诺第三方服务的数据处理方式。

## User control

用户可以缩小改稿范围、要求删除敏感片段、拒绝外部调用，或只接收对话内结果。对于需要持久化或外发的动作，用户应先确认目标、范围和接收方。

相关边界见 [Security](SECURITY.md)、[Terms](TERMS.md) 和 [Rights notice](RIGHTS-NOTICE.md)。
