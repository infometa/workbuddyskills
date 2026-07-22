# 专用工作空间策略

`local_managed` 用于本地独立审议的跨轮次恢复、正式产物与连续案卷。它不是对话内决策起手卡的前置条件，但用户确认开始建团后必须先初始化。

1. 目录必须由用户明确选择或授权创建；盘符根目录、用户主目录和非空未标记目录一律拒绝。
2. 初始化创建 `.fbsir-board/` 控制目录，以及 `tasks/`、`drafts/`、`results/`、`receipts/`、`failures/`、`deliverables/`。召集人把冻结计划写入 `.fbsir-board/plans/<runId>.json`，把已验证任务写入 `tasks/<agenda>/<seat>.task.r<revision>.json`，把成员只读认知资产短包写入 `tasks/<agenda>/<seat>.assets.r<revision>.json`；成员只能写自己的草稿、`results/<agenda>/<seat>.r<revision>.json` 和 `receipts/<agenda>/<seat>.r<revision>.send-message.json`，失败信封固定为 `failures/<agenda>/<seat>.r<revision>.json`，共享事件仍只允许召集人写。
3. 原始材料是否复制进入工作空间由用户另行决定；核心脚本不读取或复制原始材料。
4. 共享状态写入者固定为 `board-convener`。秘书和成员不得直接追加共享事件。
5. 工作空间 marker 绑定 Package ID 与产品版本；不匹配时停止，禁止静默迁移。
6. 删除、搬迁、云同步、共享或导出是独立动作，必须再次确认目标和隐私边界。
7. `.fbsir-board/events/*.jsonl` 只存操作元数据与哈希，不存正文、提示词、完整回应或身份凭据。
8. 工作空间 marker、计划、任务、资产包、结果、投递观察、失败信封和交付物目标及其已有路径段不得是符号链接或目录联接；路径越界、链接替换、冲突覆盖或摘要漂移均失败关闭。
9. 同一 `runId` 的冻结计划不可修改；起手卡、议题、模式、席位或已确认决策问题改变时必须使用新 `runId`。同一议案席位的新一轮任务必须增加 `revision`，旧修订的结果或失败不能填补新修订。

未创建工作空间时，只能交付决策起手卡，不得建团或承诺多人结果恢复与正式文件交付。
