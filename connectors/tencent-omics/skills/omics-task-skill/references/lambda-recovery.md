# Lambda 查询、恢复与重新运行

## 先读取同一个运行

保存完整 stdout、stderr 和退出码后再解析；错误 JSON、空响应或解析失败都不是完成回执。`omics whoami` 只输出文本，检查其登录结果，不加 `-o json`。命令版本仍以本机 `--help` 为准。

| 已有标识 | 命令与响应 |
| --- | --- |
| RunGroupId | `omics status <RunGroupId> --project <ProjectId> -o json` 返回数组；按 `RunUuid` 精确选记录，不取第一项当目标 |
| RunUuid | `omics debug --run <RunUuid> --project <ProjectId> --with-stdout -o json` 返回对象；运行状态在 `Status.Status`，步骤在 `Calls` |

客户端支持 `omics wait --help` 时优先用 `omics wait --run <RunUuid> --project <ProjectId> -o json`；批次用 `omics wait <RunGroupId> --project <ProjectId> -o json`。默认持续等服务端终态，自动跟踪步骤；`--timeout` 是本地等待期限，默认 `0`，只有用户明确要求才设正数。Ctrl-C 或等待超时只停止观察，不取消云任务；保留原标识后可继续等待。旧客户端不支持时按下述状态持续查询，不设固定次数或短窗口，不因临时查询失败自动重算。

只对非终态运行继续查询。查询失败或超时保留该标识和未知状态，不能据此再创建任务。多步出现上游失败、下游 `CANCELED` 时，先诊断首个失败 call。uploader 退出 124、发布超时或 receipt unavailable 说明发布/回执未完成，不能因计算日志结束就称整个步骤成功；不要把不存在的下游产物当成已完成。

## 按真实状态选择动作

先按 [运行预算与失败恢复](execution-budget.md) 核对失败阶段、累计尝试与下一步范围。计算已完成但发布失败时，先回收并验收真实已发布产物，查明发布条件；没有受支持的只发布/检查点入口时明确说明，不能把下表的 `retry` 当作只重传命令。修复原因前不重复全量计算。

| 情况 | 动作 |
| --- | --- |
| 提交响应丢失，是否创建未知 | 先恢复已有 RunUuid；确需恢复请求时，保持原参数和原 client token。返回原 RunUuid 是幂等回放，接着查它的当前状态 |
| 已明确失败终态，原定义不变且原因已处理 | 在现有授权范围用 `omics retry --run <原RunUuid> --project <ProjectId> -o json`。这是从冻结定义创建**新 Run**，不是恢复原 Pod 或断点续跑 |
| 输入、代码、资源或参数需改变 | 用 `omics run-definition --run <原RunUuid> --project <ProjectId> --format workflow-yaml` 导出多步定义（单 Task 用 `task-yaml`），在新文件修复、预览，再用新的 `omics run --lambda-file ...` 请求与新 client token 提交 |
| 部分上游已成功发布，只有失败步骤或后续分析需要执行 | 优先从冻结定义抽取所需步骤/子图，以实际发布 URL 替换子图外输入，只提交剩余部分；参见 [多步续跑](lambda-continuation.md)。无需复制维护每步独立模板，原 Run 整体失败不禁止复用已核验的上游 |

`retry` 自己也有幂等 token；它仅用于恢复那一次重跑请求，不复用原 `run` 的 token。需要区分两次明确授权的重跑时使用不同新 token。`retry` 不接受科学参数修改。默认环境盘输出按新 RunId 隔离；继承的是原 `--output-prefix` 请求或模板，基础前缀会追加新 RunId，`${runId}` 则展开为新值，不是复用旧运行目录。可用已授权的新 `--output-prefix` 更换基础前缀。定义里显式固定的 `outputs[].url` 仍按原地址写入，不由前缀覆盖；需保留该地址旧产物时，修改输出定义后发新请求。

每次重跑记录 `source_run_uuid`、新的 `RunUuid` / `RunGroupId`、实际项目/环境、定义与输入版本、失败原因及本次修改。新 RunUuid 必须不同于源 Run；受理成功只能报告“新运行已提交”，随后查询实际状态和发布产物再报告完成。`EXECUTOR_ERROR` 等终态不会因同 token 再投或命令退出 0 而自动变回运行中。

平台已发布产物按当前 `Artifacts[].DownloadCommand` 取回；`ExpectedOutputs` 只说明目标地址。部分文件存在但回执缺失时保留为未验收证据，不能据此承诺完整报告、注释或下游分析已经完成。

每个产物绑定真实源 RunUuid、步骤和输入/定义版本，必要时记录随机种子与校验和。不同重跑的部分文件不得按同名文件拼成一次成功运行；经过兼容性核验的独立分片或上游组合须另存组合清单，仍保留各源运行失败、未完成发布或未执行的状态。
