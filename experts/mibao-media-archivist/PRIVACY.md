# 秘宝 26.9.2 隐私说明

本说明适用于 `mibao-media-archivist` 26.9.2 的完整插件候选 ZIP 与 Agent 专家候选 ZIP。当前产品范围是 `execution_core_v1`，只包含 `inventory_build` 和 `inventory_search`。本说明描述候选包实际处理的数据与边界，不代表候选已通过活动宿主、企业上传、正式提审或上架。

## 两个分发通道

- Agent 专家候选不声明、安装或连接本地 MCP、连接器、localhost 服务或常驻进程。
- 完整插件候选保留一个独立研发用 stdio MCP `mibao_ping`；它只返回非敏感运行时状态，不读取媒体。完整插件的 MCP 证据不能回填为 Agent 专家能力。
- 两个候选都需要宿主提供可解析的 Python/SQLite 运行条件；运行时不在 ZIP 内。当前包不是自包含 Windows 运行时证明。

## 读取的数据

`inventory_build` 在用户明确确认的一个源目录内：

- 读取绝对源路径、相对文件名、文件大小、修改时间和文件系统身份；
- 有界读取文件头用于媒体类型识别；
- 读取文件全部字节以执行严格 SHA-256；
- 不移动、改名、覆盖、写回或删除源文件；
- 当前范围不解码媒体、不做人脸识别，不执行 OCR、ASR、视觉向量或内容语义识别。

`inventory_search` 只接受 `local-private` 项目，并在同一个已经审计且只读的 SQLite 快照事务上完成隐私门与 FTS 查询；结果显式返回 `privacyMode=local-private`。它不读取媒体文件，也不修改项目数据库。旧 `hybrid` 或 `deep-understanding` 项目会失败关闭；本版不提供原地隐私迁移，用户需新建或重建 `local-private` 项目后重新发起请求，也不会被静默扩大权限。

## 本地写入与保留

`inventory_build` 会在用户确认的项目目录持久化 `project.json`、SQLite 数据库、锁/恢复状态、FTS 索引和 HTML/CSV/JSONL/manifest 报告。数据库可包含绝对源根、相对文件名、大小、时间、文件身份、SHA-256、稳定 ID、重复关系和操作状态；报告包含相对路径、哈希、统计与异常。原始媒体不会被复制进项目。

WorkBuddy 会先把包含绝对源路径、项目路径、项目名或查询词的请求 JSON 写入当前会话 Workspace Folder 下 `.workbuddy/mibao/expert-request.json`。一次性入口要求宿主同时传入该绝对请求根与 `session-workspace` 固定作用域。包内入口由 WorkBuddy 在加载 `mibao` Skill 时解析的 `${CODEBUDDY_SKILL_DIR}` 固定定位，不读取环境变量或扫描 plugin root。对严格 schema-valid、无链接/重解析点且只有一个物理链接的请求，入口会在访问源目录或项目目录前将它原子 claim、复核同一内容并删除；即使后续项目操作失败，该有效请求也已消费。错误结果以 `requestDisposition` 和 `recovery` 区分未消费、已消费和可能残留。

无效请求、相对路径、错根路径、legacy 多硬链接或其他未通过所有权/完整性门的文件不保证自动清理；清理门失败时也可能残留内部 claim 文件。删除固定请求路径不等于介质安全擦除，也不能删除操作系统备份、同步副本或宿主日志。当前候选不自动删除项目数据，也尚未证明升级或卸载后的项目保留语义。

## 网络、模型与外发边界

秘宝候选 one-shot 子进程不包含网络客户端调用，不创建 `ExternalDisclosure`，不自动上传媒体、索引、报告、遥测或诊断数据。结果中的 `networkCallCount=0` 只描述候选 one-shot 子进程，不等同于 WorkBuddy 模型会话零网络，也不等同于整台电脑零网络。

用户提示、绝对路径、项目名、查询词、工具结果、相对文件名、统计或报告回读内容可能出现在 WorkBuddy 会话中，并由当前宿主/模型按其自身服务与隐私条款处理。秘宝当前执行范围禁止把原始图像或视频作为模型证据外发，但不能把候选子进程的零网络声明外推到 WorkBuddy 聊天传输、宿主工具、`present_files`、宿主遥测或系统管理的 session-local daily memory。专家不得主动创建长期 memory、Skill 或跨项目记录。

## 遥测与诊断

候选包没有秘宝自有的自动遥测、崩溃上传、广告跟踪或后台更新客户端。诊断包的自动上传尚未实现。WorkBuddy 宿主自身的网络、遥测、日志和模型处理不属于候选 one-shot 子进程，需按宿主条款和独立回执判断。

## 用户控制与未完成门禁

- 用户在执行前确认精确源目录、项目目录和只读/写入边界；秘宝不得自动扩大扫描范围。
- V1 不提供永久删除或覆盖原件接口。
- 完整的旧项目隐私迁移、ExternalDisclosure 账本、媒体脱敏、逐次模型外发许可、无效/清理失败请求的处置、升级/卸载数据保留和干净 Windows 验收仍是后续门禁。
- 本说明是工程隐私披露，不是法律意见。第一方商业分发、正式提审与上架仍需独立 owner 授权和平台回执。
