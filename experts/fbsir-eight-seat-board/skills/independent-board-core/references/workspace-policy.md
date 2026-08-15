# 专用工作空间策略

`local_managed` 用于本地独立审议的跨轮次恢复、正式产物与连续案卷。它不是对话内决策起手卡的前置条件，但用户确认开始建团后必须先初始化。

1. 目录必须由用户明确选择或授权创建；盘符根目录、用户主目录和非空未标记目录一律拒绝。
2. 初始化创建 `.fbsir-board/` 控制目录，以及 `tasks/`、`drafts/`、`results/`、`receipts/`、`failures/`、`deliverables/`。召集人把冻结计划写入 `.fbsir-board/plans/<runId>.json`，把只读 predecessor/legacy 摘要 receipt 写入新案卷 `.fbsir-board/predecessors/<runId>.json`，把已验证任务写入 `tasks/<agenda>/<seat>.task.r<revision>.json`，把成员只读认知资产短包写入 `tasks/<agenda>/<seat>.assets.r<revision>.json`；成员只能写自己的草稿、`results/<agenda>/<seat>.r<revision>.json` 和 `receipts/<agenda>/<seat>.r<revision>.send-message.json`，失败信封固定为 `failures/<agenda>/<seat>.r<revision>.json`，共享事件仍只允许召集人写。
3. 原始材料是否复制进入工作空间由用户另行决定；核心脚本不读取或复制原始材料。
4. 共享状态写入者固定为 `board-convener`。秘书和成员不得直接追加共享事件。
5. 工作空间 marker 绑定 Package ID 与完整 workspace/event release tuple，独立于包版本变量；`inspectWorkspace` 只读返回 `current_read_write`、`predecessor_read_only`、`legacy_read_only` 或 `unsupported`，`requireWritableWorkspace` 是全部写入口的统一门禁。前序案卷写入固定失败为 `WORKSPACE_PREDECESSOR_READ_ONLY`，legacy 写入固定失败为 `WORKSPACE_LEGACY_READ_ONLY`，未知或混合版本固定失败为 `WORKSPACE_VERSION_UNSUPPORTED`，禁止静默迁移。
6. predecessor/legacy 摘要只在合作式单写者/受信目录边界内提供稳定句柄捕获与可复算绑定；它不宣称跨文件原子快照，也不抵御具有同等文件系统权限的恶意并发目录替换。高保证续办必须由宿主先建立 ACL 独占窗口或提供原生相对目录句柄能力，并把该外部证明单独留痕。
7. `fbsir.case-resume-card/v1` 必须由调用方提供 exact receipt digest 后只读生成。current 先经完整工作空间事件验证器，只从重放事件链投影观察里程碑，不读取 digest 未绑定的材料记录；terminal run 不展示继续动作，其他 current 只能续同一 run。predecessor/legacy 只投影各自 `*_bound` 证据绑定并续到不同的新 26.8.10 run。digest 缺失、失配、不支持、源漂移或 inspect-only 展示均不得写入源/目标案卷、回显内容或发明责任状态；inspect-only 只隐藏本次 CTA，不构成全局动作撤销。
8. 删除、搬迁、云同步、共享或导出是独立动作，必须再次确认目标和隐私边界。
9. `.fbsir-board/events/*.jsonl` 只存操作元数据与哈希，不存正文、提示词、完整回应或身份凭据。
10. 工作空间 marker、计划、任务、资产包、结果、投递观察、失败信封和交付物目标及其已有路径段不得是符号链接或目录联接；路径越界、链接替换、冲突覆盖或摘要漂移均失败关闭。
11. 同一 `runId` 的冻结计划不可修改；起手卡、议题、模式、席位或已确认决策问题改变时必须使用新 `runId`。同一议案席位的新一轮任务必须增加 `revision`，旧修订的结果或失败不能填补新修订。
12. 新案卷只允许 exact `fbsir.board-workspace/v2@26.8.10` 且带合法随机 `workspaceInstanceId`；冻结前序案卷只允许 exact `fbsir.board-workspace/v2@26.8.1` 且保持同一 v2 keyset；冻结 legacy 案卷只允许 exact `fbsir.board-workspace/v1@26.7.20` 且 marker keyset 完整无扩展。`v1 + workspaceInstanceId`、混合 schema/release、额外或缺失关键字段一律 `unsupported`，不得使用 semver 范围或随机字段把只读案卷晋升为可写。

未创建工作空间时，只能交付决策起手卡，不得建团或承诺多人结果恢复与正式文件交付。
