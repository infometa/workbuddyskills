# 异步运行时失败知识库（runtime_error_kb）

> 本文件供 SKILL 模型对照 `omics debug --run / --job` 输出做症状识别。
>
> CLI 端只负责"取证"——把 Status / Calls / stderr / PodEvents 一次性打包成结构化 JSON。
> 模型读这份知识库，对照下面的"症状信号 → 根因 → 修复方向"决定下一步行动。
>
> **使用方式**：拿到 `omics debug --run <uuid> -o json` 的输出后，按下面每个场景的
> "**判别信号**"逐条匹配 → 命中即输出对应"**用户话术**"。

## 0. 通用诊断流程

1. **先看 `Status.ErrorMessage`**：cromwell / NF runtime 抛的顶层错信，往往一句话点出大类（`return code 127` / `OOMKilled` / `Insufficient cpu` ...）。
2. **再看每个 `JobLogs[].Stderr` 末尾几十行**：90% 应用层错都在 stderr 末尾。
3. **没头绪时看 `JobLogs[].PodEvents`**：调度 / 挂载 / 镜像 / 资源类问题都在这。
4. **多个 call 同点失败** → 共性原因（应用 / 参数侧）；**分散失败** → 个性原因（环境 / 资源侧）。
5. **CLI 已自动钻最多 5 个失败 call**；剩余失败用 `omics debug --run <uuid> --job <jobId>` 单独钻。

## 1. 应用 / 命令层错（看 stderr）

### 1.1 退出码 127 — command not found

**判别信号**：
- `Status.ErrorMessage` 含 `exited with return code 127`
- `JobLogs[].Stderr` 末尾含 `command not found` / `: not found` / `No such file`

**根因**：
- WDL `command { ... }` 中命令拼写错 / 容器内没装该命令
- 或参数值含**未引号的空格**，shell 把空格后内容当下一条命令
- 或 docker 镜像与命令不匹配

**用户话术（SKILL 输出）**：
> ❌ Job 退出码 127（command not found）。可能原因：
> 1. 命令拼写错或容器内未安装该工具
> 2. 参数值含空格未加引号（如 `RunFastp.report_title = "fastp report"` 但 WDL 命令模板没用 `~{...}` 引号）
> 3. docker 镜像与命令不匹配
>
> 建议：
> - 用 `omics app file get --app <id> --path main.wdl -o raw` 取出 WDL，检查 `command { ... }` 块；
> - 检查 `omics app templates --app <id> --content <tpl-id> -o raw` 中的参数值是否含空格；
> - 修复后用 `omics run --app <id> --input <fixed.json>` 重跑（form C），不需要 `--update`。

### 1.2 退出码 1 / 2 — 应用代码错误（traceback）

**判别信号**：
- `Status.ErrorMessage` 含 `return code 1` 或 `return code 2`
- `JobLogs[].Stderr` 末尾含 `Traceback` / `error:` / `Segmentation fault` / `IndexError` / `KeyError` 等程序栈

**根因**：应用脚本或工具本身的运行时错误。

**用户话术**：
> ❌ Job 退出码 {1|2}：应用代码运行时错误。stderr 末尾的报错栈：
> ```
> {把 stderr 最后 ~40 行贴出来}
> ```
> 这是 WDL/NF 内调用的应用层问题，建议：
> 1. 看上面的 traceback / error，定位是脚本 bug 还是输入数据问题；
> 2. 若是脚本 bug → 改 `command { }` 块或镜像版本，用 `omics app file update` 精准 patch；
> 3. 若是输入数据问题 → 修 input JSON 后用 `omics run --app <id> --input <new.json>` 重跑。

### 1.3 No such file or directory（输入路径错）

**判别信号**：
- `Stderr` 末尾含 `No such file or directory: /xxx` / `cannot open ... for reading`
- 同时 `Status.Input` 或 user 给的 input JSON 中能看到对应路径

**根因**：input JSON 中的 cos:// 路径错 / 未授权 / 被删；或 task 之间 chain 断开（依赖的上游 output 没产出）。

**用户话术**：
> ❌ Job 报"文件不存在": `{贴 stderr 那一行}`。
>
> 检查：
> 1. 路径是否拼写正确（cos://bucket/key 各段）
> 2. 桶授权是否到位（用 `omics config show -o json` 确认 CosBucketName 是否绑定到当前环境）
> 3. 若是 task 间依赖断链 → 上一个 task 没产出该文件，先排查上游 task 的失败信号

## 2. 资源 / 调度类（看 PodEvents）

### 2.1 OOM 内存不足

**判别信号**：
- `JobLogs[].PodEvents[]` 含 `Reason=OOMKilled`
- 或 `Status.ErrorMessage` 含 `OOMKilled` / 退出码 137

**根因**：WDL `runtime { memory: ... }` 设置不足。

**用户话术**：
> ❌ Job 因内存不足被 K8s 杀掉（OOMKilled）。当前 runtime 配置：
> - memory: `{从 Calls[].Runtime 解析 memory 字段}`
>
> 建议把 `runtime.memory` 调大（例如从 `4G` 改为 `16G`）后用 `omics app file update --app <id> --path <主wdl>` 替换，再用 `omics run --app <id> --input <p>` 重跑。

### 2.2 调度失败 — 资源不足

**判别信号**：
- `PodEvents[]` 含 `Reason=FailedScheduling`，Message 含 `Insufficient cpu` 或 `Insufficient memory`

**根因**：当前环境的节点池剩余资源 < 任务申请；或 runtime 申请超过单节点上限。

**用户话术**：
> ❌ Job 调度失败：`Insufficient {cpu|memory}`。
>
> 当前 runtime 申请：cpu={...}, memory={...}。
>
> 建议：
> 1. 把 runtime.cpu / memory 调小到节点池单节点上限以内
> 2. 或联系平台扩节点池；查 `omics config show` 看当前 EnvironmentId

### 2.3 挂载失败 — `FailedMount`（重要：不要忽略）

**判别信号**：
- `PodEvents[]` 含 `Reason=FailedMount`，Message 通常含 `MountVolume.SetUp failed for volume "..."`

**根因**：CSI 驱动 / 数据卷异常 / 桶懒挂载未就绪。前端 UI 故意过滤这个 reason，但 AI 排障必须看。

**用户话术**：
> ❌ Job Pod 数据卷挂载失败（FailedMount）。事件信息：
> ```
> {贴最近一条 FailedMount 的 Message}
> ```
>
> 这通常是 CSI / 数据卷 / COS 桶懒挂载问题。建议：
> 1. 等 1~2 分钟后再次发起 `omics run --app <id>`（COS 桶懒挂载需要预热）
> 2. 仍失败则把上面 Message 反馈给平台运维（涉及 CSI 驱动）

### 2.4 镜像拉取失败 — `ImagePullBackOff` / `ErrImagePull`

**判别信号**：
- `PodEvents[]` 含 `Reason=Failed` 且 Message 含 `ImagePullBackOff` 或 `ErrImagePull`
- 或 `Stderr` 开头含 `Error response from daemon`

**根因**：runtime.docker 镜像名拼写错 / 镜像仓库网络问题 / tag 不存在。

**用户话术**：
> ❌ docker 镜像拉取失败：`{贴 Message}`。
>
> 当前 runtime.docker: `{从 Calls[].Runtime 解析}`。
>
> 建议：
> 1. 核对镜像名 / tag 拼写（如 `ccr.ccs.tencentyun.com/omics-public/fastp:0.23.2`）
> 2. 改用平台白名单内的镜像仓库（避免被网关拦截）
> 3. 修改后 `omics app file update --app <id> --path <主wdl>` 替换 WDL 中的 `runtime { docker }`

### 2.5 节点驱逐 — `Evicted`

**判别信号**：
- `PodEvents[]` 含 `Reason=Evicted` / `NodeNotReady` / `DiskPressure`

**根因**：节点磁盘 / 内存压力 / 节点不可达。

**用户话术**：
> ❌ Job 所在节点被驱逐（{Reason}）：`{Message}`。
>
> 这是节点级故障，重发一次任务通常能解决：`omics run --app <id> --input <p>`。
> 反复出现请把 EnvironmentId 反馈给平台运维。

## 3. 平台 / 提交期错（看 Run.Status / Status.ErrorMessage）

### 3.1 ApiSubmitError

**判别信号**：
- `Run.Status == ApiSubmitError`（在 `omics debug <rgId>` 段 1 输出能看到）
- `Run.ErrorMessage` 含 cromwell 提交期错信

**根因**：WDL Validate 通过但 cromwell 提交时报错（如 task 名重复 / outputs 引用错变量）。

**用户话术**：
> ❌ 任务在提交期失败（ApiSubmitError），未真正进入运行。错信：
> {ErrorMessage}
>
> 注意：此状态下 **不要再调 `omics debug --run <uuid>`**——没有 Pod / Job，取不到 stderr。
> 直接修 WDL 后用 `omics run --wdl ... --update <appId>` 重跑。

### 3.2 任务被终止 / Hold

**判别信号**：
- `Run.Status` 是 `Aborted` / `AbnormalAbort` / `OnHold`
- `Run.ErrorMessage` 通常为空或含 "user-terminate" / "on hold"

**用户话术**：
> ⚠️ 任务被终止 / 挂起。原因可能是：
> 1. 用户主动 `omics run` 后再终止（这边 CLI 没暴露 terminate 命令，通常是平台 UI 操作）
> 2. 平台风控触发挂起
>
> 不需要看 stderr，直接 `omics run --app <id>` 重发即可。

## 4. 兜底：模型自由分析

如果上面任一场景都不命中：

1. 把 `Status.ErrorMessage`、每个 `JobLogs[].Stderr` 的末尾 ~40 行、`PodEvents` 全列表整段贴给用户；
2. 不要瞎猜根因；
3. 提示用户："以上是完整失败现场，请检查命令是否合法 / 输入是否齐全 / 资源是否足够"；
4. 提示用户可以用 `omics debug --run <uuid> --job <plan-xxx>` 单独钻某个 Job 看更细节的现场。

## 5. 决策快速表

| 决定性信号 | 命中场景 |
|---|---|
| `return code 127` | 1.1 |
| `Traceback` / `error:` / SIGSEGV | 1.2 |
| `No such file or directory` | 1.3 |
| `OOMKilled` 或 退出码 137 | 2.1 |
| `FailedScheduling` + `Insufficient ...` | 2.2 |
| `FailedMount` | 2.3 |
| `ImagePullBackOff` / `ErrImagePull` | 2.4 |
| `Evicted` / `NodeNotReady` | 2.5 |
| `Status == ApiSubmitError` | 3.1 |
| `Status == Aborted` / `OnHold` | 3.2 |
| 其他 | 4 兜底 |
