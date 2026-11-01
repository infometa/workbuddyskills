# 固定执行循环

按 1 → 2 → 3 执行。需要用户回答走 4；机器仍在生成走 5；异常走 6。每次提交答案后回到 2，不结束任务。

## 宿主后台工具

启动或读取后台进程前读取 [宿主工具](host-tools.md) 的后台进程小节；云端命令通过 [执行包装](background-execution.md) 提交。

## 1. 启动一次命令

- create/send/reply/select/test/review 只提交一次；支持等待的命令带 `--timeout 600`。
- 保存返回的原进程句柄或后台 task_id，以及工具返回的输出文件路径（如有）。
- 默认通过 [包内运行脚本](commands.md#长任务的默认启动方式) 提交；stdout 是最终业务结果，stderr 包含已过滤的进度及原样保留的检查消息和提醒事件；按 [质量检查](quality-checks.md) 及时展示后两类事件，它们不代表完成。保存原任务句柄，不定时读日志代替结果接收。
- 不写 `sleep 150; tail ...`，不只保存 stderr，不重复 create/send。

## 2. 读取这条命令的结果

- 使用 `TaskOutput` 按上述宿主后台工具契约读取原调用的完整结果；句柄型工具传原 task_id，文件型 Read 传原输出文件的 file_path。不能把 task_id 当文件路径，也不能读取后续 sleep/tail 命令的结果。
- 已返回完整 stdout JSON：立即进入 3。
- 原任务仍在运行：有已确认的宿主完成通知时等待通知，否则通过原句柄的结果工具有限等待，单次不超过 60 秒。不循环忙查，不启动 sleep，不重启 CLI。
- 收到完成通知：马上取完整 stdout，进入 3。
- 已过本次 CLI 的 600 秒窗口仍没拿到结果：核对一次原任务状态并读取 stdout。已结束但结果丢失时，用已知 sessionId 查询一次 state，再进入 3；仍无法确定则进入 6。不要再盲等一轮。

**stderr 没变化 ≠ CLI 还在运行。stderr 写着“进行中” ≠ 最新业务状态。**

## 3. 只按最新 JSON 分支


从上到下，命中一项就执行：

| 条件 | 下一步 |
|---|---|
| `ok=false`、未知状态或状态与交互矛盾 | 进入 6 |
| 带 `agentFriendly` 或 `securityReview` | 按 [扩展能力](extend.md) 处理；这里的 `NEEDS_SELECTION` 是选接入方式，不当作风格候选 |
| `NEEDS_INPUT` + `stylePlanning` + 唯一 `APPROVE_ARCHITECTURE_PLAN` 且允许 APPROVE | 进入 5，由 CLI 静默确认，不在宿主弹审批或提交 APPROVE；其他业务问题不适用 |
| `NEEDS_INPUT` / `NEEDS_SELECTION` | 立即进入 4；不再等日志、不再调用 wait |
| `PAUSED` / `INTERRUPTED` / `CANCELLED` / `FAILED` | 报告实际状态，停止自动推进，保留标识 |
| 有 `stylePlanning` | 进入 5，等待自动衔接，不追加查看演示/开始研发/规划确认 |
| `ACCEPTED` / `QUEUED` / `RUNNING` | 进入 5 |
| `COMPLETED` 且有 `autoTest` / `codeReview` | 先按 [质量检查](quality-checks.md) 核对报告与条件，不套用普通研发完成菜单 |
| `COMPLETED` | 按 [阶段规则](creation-flow.md) 交付本轮结果；不把风格、列表或 stop 的完成当成应用完成 |
| 认证或配置结果 | 回到 [认证流程](authentication.md) 的下一步，不当成创作完成 |

进度卡的 completed、activeCount、complete 不参与上表判断。

## 4. 提问 → 收答 → 提交 → 回到 2

1. 取当前 interactionId、问题、选项和 answerSchema。需要比较页面时，先打开本批 previewUrl。
2. 按 [展示规则](host-presentation.md) 调用本渠道的原生提问工具。当前宿主保留完整问题和标识直接收答；原生工具不可用时降级文本，不把超时或默认项当成用户选择。
3. **等用户回答。此时不调用 Bash sleep、CLI wait 或 state 轮询。** 没有回答就保持未决，不代选、不设答题截止时间。
4. 只答一部分：保留已答内容，只问剩余项。推荐、预选、取消和异步工具返回都不是用户答案。
5. 答齐后，由原执行者按 [交互回复](interactions.md) 提交一次；CLI 会核对交互是否仍有效。普通问卷用 reply，风格按当前 select 入口；不把用户答案当作新建需求。
6. 保存这次命令的句柄，**回到 2 读取结果**。新结果有新题就再走 4；仍在生成就走 5。

`NEEDS_INPUT` 如果同时带 development.previewUrl（或兼容旧快照），先按 nextActions 和 [全部端入口](project-links.md) 展示成果与 development.routing 的完整端入口，不重复询问已选过的首次功能清单。发布完成同样使用 publish.routing 逐端交付，不能因 state 已完成而跳过展示。

## 5. 只等待机器，不重发写操作

先确认上一条 CLI 已返回。未返回就回到 2，不并发启动新命令。

| 当前操作 | 执行一次，然后回到 2 |
|---|---|
| 普通创作、研发、运营对话、stylePlanning、自动测试/审查及报告后续修复 | `superun-ai chat wait <sessionId> --timeout 600` |
| 风格批次仍生成 | 先打开新就绪页面；按下面的自适应补查查询原批次 style list；不用 chat wait 忙循环 |
| 发布或插件仍运行 | 按当前目标版本/插件的状态命令低频查询，不用 chat wait 代替 |

只有命令已经返回、服务端仍在生成且没有完成通知/可持续等待入口时，才补查。间隔按配置 `[60,120,300]` 秒从第一项开始，连续无实质变化就进入下一档，到末档保持；发现步骤、阶段、预览或 warnings 变化就回到第一档。使用宿主延后执行能力，不把长间隔实现成阻塞 Bash sleep。它是备用查询节奏，不是进度汇报频率；原任务完成、问卷、失败和用户消息不等这个计时器。

有 progressRevision 时给 wait/state/style list 带 `--progress-revision`，没有就省略。使用最新 sessionId/messageId/分支标识。`waitTimedOut=true` 只表示本次本地窗口结束，重新走 3，不重发需求。

没有可用的等待/继续执行能力：说明任务仍在运行并保留恢复标识，不假称已安排后台续查。

## 6. 异常只做一次恢复，不自行试错

- 原结果丢失、OUTCOME_UNKNOWN、LOCAL_WAIT_TIMEOUT、STALE_INTERACTION：用已有标识查询一次对应状态。取得有效结果就回到 3；仍不明确就报告错误与标识，停止自动重试。不能重发 create/send。
- AMBIGUOUS_INTERACTION：查询一次；仍有歧义则报告，不猜交互 ID。
- 用户中断、取消：保留停止意图，不自动重启。
- 更新、认证、权限错误：报告具体缺口，按对应指引处理；不跳过门禁、不直连后端。
- `PROTOCOL_ERROR` 或其他未知错误：原样报告错误代码与操作，停止自动写入；本地 CONFIGURED、只读查询成功或列表中未找到项目，都不能证明写入未发生或只是瞬时网络问题。不得据此重试 create/send，也不切换 --no-wait、绕过运行脚本或直接导入 CLI 内部模块再次尝试写入。排障需要另行限定范围，不能把建站任务自动转成源码调试。
- 没有 sessionId 且创建结果不明：只查一次 session list；不能唯一确定项目就报告，不再 create。

保留：原任务句柄、当前操作、sessionId、最新 messageId、progressRevision、分支/choiceId、未决 interactionId、用户已答内容和授权。检查及修复保留 autoTest/codeReview 的 phase、sourceMessageId、当前与前一份报告以及用户范围，旧来源失效先查当前状态，不重发检查；发布/插件保留各自目标标识。不要记录密钥。
