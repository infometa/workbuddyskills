# 异步运行时失败知识库（runtime_error_kb · v6 · WDL/NF 分流）

> 本文件供 SKILL 模型对照 `omics debug --run / --job -o json` 输出做症状识别。
>
> CLI 端只负责"取证"——把 Status / Calls / JobLogs / NextflowLog（仅 NF）/ PodEvents 一次性打包成结构化 JSON。
> 模型读这份知识库，对照"症状信号 → 根因 → 修复方向"决定下一步行动。
>
> **使用方式**：拿到 `omics debug --run <uuid> -o json` 的输出后：
> 1. 先看 `AppType`：`WDL` / `WDL_GRAPH` 走 §1（WDL 通用症状）；`NEXTFLOW` 走 §2（NF 专属症状）
> 2. 共用症状（资源 / 调度 / 平台）走 §3、§4、§5
> 3. 都不命中走 §6 兜底

---

## 0. 通用诊断流程

1. **先确定 `AppType`**（来自 debug JSON 顶层 `AppType` 字段）：
   - `WDL` / `WDL_GRAPH` → 主战场是 `JobLogs[].Stderr` + `PodEvents`
   - `NEXTFLOW` → 主战场是 `NextflowLog` 末尾 + `JobLogs[].Stderr`
2. **看 `Status.ErrorMessage`**：cromwell / NF runtime 抛的顶层错信，往往一句话点出大类。
3. **(NF 专属)看 `NextflowLog` 末尾 ~80 行**：pipeline 编排级错误几乎都在这——参数缺失、process 找不到、channel 异常、引擎自身 stack。
4. **看每个 `JobLogs[].Stderr` 末尾几十行**：90% 应用层错都在 stderr 末尾。
5. **没头绪时看 `JobLogs[].PodEvents`**：调度 / 挂载 / 镜像 / 资源类问题都在这（不分 WDL/NF）。
6. **多个 call 同点失败** → 共性原因（应用 / 参数侧）；**分散失败** → 个性原因（环境 / 资源侧）。
7. **CLI 已自动钻最多 8 个失败 call**；剩余失败用 `omics debug --run <uuid> --job <jobId>` 单独钻。

---

## 1. WDL 通用症状（AppType = WDL / WDL_GRAPH）

> 主要看：`JobLogs[].Stderr` 末尾、`Status.ErrorMessage`、`JobLogs[].Runtime`。
> CLI v6 已清空 `Status.Command` / `Status.Meta`，不再消费这两个字段。

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
> 建议：检查 WDL `command { ... }` 块与 input JSON；修复后用 `omics run --wdl <整目录> --update <appId>` 重跑。

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
> 这是 WDL 内调用的应用层问题。建议：
> 1. 看上面的 traceback / error，定位是脚本 bug 还是输入数据问题；
> 2. 若是脚本 bug → 改 `command { }` 块或镜像版本，用 `omics run --wdl ... --update <appId>` 重跑；
> 3. 若是输入数据问题 → 修 input JSON 后用 `omics run --app <id> --input <new.json>` 重跑（无需 --update）。

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

### 1.4 ApiSubmitError — cromwell 提交期失败

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

---

## 2. NF 专属症状（AppType = NEXTFLOW）

> 主要看：`NextflowLog` 末尾、`Status.ErrorMessage`、`JobLogs[].Stderr`。
> CLI v6 已清空 `Status.Output`（NF 没 output 概念），保留了 `Status.Command`（NF 启动命令）。

### 2.1 NextflowLog 末尾 "Process X terminated with code N"

**判别信号**：
- `NextflowLog` 末尾含 `Process \`<name>\` terminated with .* code (\d+)`
- 通常伴随某个 `JobLogs[].Status == Failed`，stderr 与之对应

**根因**：NF 中具体 process 内部子进程退出非 0；本质等同 WDL §1 的应用层错，但需要先在 `NextflowLog` 中定位是哪个 process。

**话术**：
> ❌ NF process `<name>` 以退出码 N 失败。CLI 已自动钻取该 process 对应 Job 的 stderr：
> ```
> {贴 JobLogs[].Stderr 末尾 ~40 行}
> ```
> 若是参数问题 → 修 input JSON 后 `omics run --app <NF应用id> --nf-version <版本> --input <fixed.json>` 重跑（form C，复用应用）；
> 若是 NF 代码 bug → 修管道源码后**重新上传到 COS**，用 `omics run --nf <new-cos-path> --name xxx --nf-version <版本>` 新建任务（NF 不支持 --update）。

### 2.2 NextflowLog "Missing required input" / "No such variable"

**判别信号**：
- `NextflowLog` 末尾含 `Missing process or workflow name` / `No such variable: <name>` / `Required parameter <x> not specified`

**根因**：input JSON 缺必填字段，或 NF 配置 `params.x` 引用不存在。

**话术**：
> ❌ NF 引擎报参数缺失：`{贴关键行}`。
>
> 这是 input JSON 不完整或 NF 配置写错。建议：
> 1. 检查 `Status.Input` 字段，对照 NF 入口 `nextflow.config` / `main.nf` 中的 `params.*`；
> 2. 修复 input JSON 后用 `omics run --app <NF应用id> --nf-version <版本> --input <fixed.json>` 重跑（form C）。

### 2.3 NextflowLog "No such file or directory" / "publishDir cannot ..."

**判别信号**：
- `NextflowLog` 末尾含 `No such file or directory` / `publishDir cannot be created`

**根因**：COS 路径错 / publishDir 配置不可写 / NF 路径权限问题。

**话术**：
> ❌ NF 路径相关错误：`{贴关键行}`。
>
> 检查：
> 1. input JSON 中所有 `cos://` 路径拼写
> 2. nextflow.config 中 `publishDir` 是否指向有写权限的桶 / 路径
> 3. 必要时改 NF 配置后重新上传到 COS，用 `omics run --nf <new-cos-path> ...` 新建任务

### 2.4 NextflowLog "command not found" / 容器内工具缺失

**判别信号**：
- `NextflowLog` 或对应 `JobLogs[].Stderr` 含 `command not found` / `executable file not found in $PATH`

**根因**：NF process 的 `container` 指令镜像与命令不匹配；或 process 用了 `module` 而集群没装。

**话术**：
> ❌ NF process 内未找到命令 `{cmd}`。
>
> 大概率是 `container` 镜像选错或 tag 不对。建议改 NF 源码（`process { container '...' }`）后重新上传到 COS，
> 用 `omics run --nf <new-cos-path> --name xxx --nf-version <版本>` 新建任务。

### 2.5 NF 引擎自身 stack（NextflowLog 含 java traceback）

**判别信号**：
- `NextflowLog` 末尾含 `java.lang.*Exception` / `nextflow.exception.*` 长 stack

**根因**：NF 引擎版本不兼容 / 配置语法错 / 远程缓存损坏。

**话术**：
> ❌ NF 引擎自身抛异常（非业务错）：
> ```
> {贴 java stack 末尾 ~20 行}
> ```
> 优先尝试切引擎版本：把 `--nf-version` 切到 `23.10.3` / `24.04.3` 等较稳定的版本重跑。仍失败把上面 stack 反馈给平台。

---

## 3. 资源 / 调度类（WDL / NF 共用 · 看 PodEvents + Runtime）

### 3.1 OOM 内存不足

**判别信号**：
- `JobLogs[].PodEvents[]` 含 `Reason=OOMKilled`
- 或 `Status.ErrorMessage` / `NextflowLog` 含 `OOMKilled` / 退出码 137

**根因**：runtime memory（WDL）/ NF process `memory` 指令设置不足。

**话术**：
> ❌ Job 因内存不足被 K8s 杀掉（OOMKilled）。当前 runtime：
> - memory: `{从 JobLogs[].Runtime 解析 memory 字段}`
>
> 建议把 memory 调大（例如从 `4G` 改为 `16G`）：
> - WDL → 改 `runtime { memory: "16G" }` 后 `omics run --wdl <整目录> --update <appId>` 重跑
> - NF → 改 nextflow.config 中该 process 的 `memory '16 GB'` 后重新上传到 COS，`omics run --nf <new-cos-path> ...` 新建任务

### 3.2 调度失败 — 资源不足

**判别信号**：
- `PodEvents[]` 含 `Reason=FailedScheduling`，Message 含 `Insufficient cpu` 或 `Insufficient memory`

**根因**：当前环境的节点池剩余资源 < 任务申请；或 runtime 申请超过单节点上限。

**话术**：
> ❌ Job 调度失败：`Insufficient {cpu|memory}`。
>
> 当前 runtime 申请：cpu={...}, memory={...}（从 `JobLogs[].Runtime` 解析）。
>
> 建议：
> 1. 把 cpu / memory 调小到节点池单节点上限以内
> 2. 或联系平台扩节点池；查 `omics config show` 看当前 EnvironmentId

### 3.3 挂载失败 — `FailedMount`（重要：不要忽略）

**判别信号**：
- `PodEvents[]` 含 `Reason=FailedMount`，Message 通常含 `MountVolume.SetUp failed for volume "..."`

**根因**：CSI 驱动 / 数据卷异常 / 桶懒挂载未就绪。前端 UI 故意过滤这个 reason，但 AI 排障必须看。

**话术**：
> ❌ Job Pod 数据卷挂载失败（FailedMount）。事件信息：
> ```
> {贴最近一条 FailedMount 的 Message}
> ```
>
> 这通常是 CSI / 数据卷 / COS 桶懒挂载问题。建议：
> 1. 等 1~2 分钟后再次发起 `omics run --app <id>`（COS 桶懒挂载需要预热）
> 2. 仍失败则把上面 Message 反馈给平台运维（涉及 CSI 驱动）

### 3.4 镜像拉取失败 — `ImagePullBackOff` / `ErrImagePull`

**判别信号**：
- `PodEvents[]` 含 `Reason=Failed` 且 Message 含 `ImagePullBackOff` 或 `ErrImagePull`
- 或 `Stderr` 开头含 `Error response from daemon`

**根因**：runtime.docker / NF `process.container` 镜像名拼写错 / 仓库网络问题 / tag 不存在。

**话术**：
> ❌ docker 镜像拉取失败：`{贴 Message}`。
>
> 当前镜像: `{从 JobLogs[].Runtime 解析 docker 字段}`。
>
> 建议：
> 1. 核对镜像名 / tag 拼写（如 `ccr.ccs.tencentyun.com/omics-public/fastp:0.23.2`）
> 2. 改用平台白名单内的镜像仓库（避免被网关拦截）
> 3. WDL 改后走 `--update`；NF 改后**重新上传 COS** + `--nf <new-cos-path>` 新建

### 3.5 节点驱逐 — `Evicted`

**判别信号**：
- `PodEvents[]` 含 `Reason=Evicted` / `NodeNotReady` / `DiskPressure`

**根因**：节点磁盘 / 内存压力 / 节点不可达。

**话术**：
> ❌ Job 所在节点被驱逐（{Reason}）：`{Message}`。
>
> 这是节点级故障，重发一次任务通常能解决：`omics run --app <id> --input <p>`。
> 反复出现请把 EnvironmentId 反馈给平台运维。

---

## 4. 平台 / 提交期错（看 Run.Status / Status.ErrorMessage）

### 4.1 任务被终止 / Hold

**判别信号**：
- `Run.Status` 是 `Aborted` / `AbnormalAbort` / `OnHold`
- `Run.ErrorMessage` 通常为空或含 "user-terminate" / "on hold"

**话术**：
> ⚠️ 任务被终止 / 挂起。原因可能是：
> 1. 用户主动终止（CLI 不暴露 terminate 命令，通常是平台 UI 操作）
> 2. 平台风控触发挂起
>
> 不需要看 stderr，直接 `omics run --app <id>` 重发即可。

---

## 5. 兜底：模型自由分析

如果上面任一场景都不命中：

1. 把 `Status.ErrorMessage`、（NF）`NextflowLog` 末尾、每个 `JobLogs[].Stderr` 的末尾 ~40 行、`PodEvents` 全列表整段贴给用户；
2. 不要瞎猜根因；
3. 提示用户："以上是完整失败现场，请检查命令是否合法 / 输入是否齐全 / 资源是否足够"；
4. 提示用户可以用 `omics debug --run <uuid> --job <plan-xxx>` 单独钻某个 Job 看更细节的现场。

---

## 6. 决策快速表（v6）

| AppType | 决定性信号 | 命中场景 |
|---|---|---|
| WDL | `return code 127` | 1.1 |
| WDL | `Traceback` / `error:` / SIGSEGV | 1.2 |
| WDL | `No such file or directory`（stderr） | 1.3 |
| WDL | `Run.Status == ApiSubmitError` | 1.4 |
| NF  | `NextflowLog`: "Process X terminated with code N" | 2.1 |
| NF  | `NextflowLog`: "Missing required" / "No such variable" | 2.2 |
| NF  | `NextflowLog`: "No such file" / "publishDir" | 2.3 |
| NF  | `NextflowLog` / stderr: "command not found" | 2.4 |
| NF  | `NextflowLog` 含 java/nextflow exception stack | 2.5 |
| 共用 | `OOMKilled` 或 退出码 137 | 3.1 |
| 共用 | `FailedScheduling` + `Insufficient ...` | 3.2 |
| 共用 | `FailedMount` | 3.3 |
| 共用 | `ImagePullBackOff` / `ErrImagePull` | 3.4 |
| 共用 | `Evicted` / `NodeNotReady` | 3.5 |
| 共用 | `Status == Aborted` / `OnHold` | 4.1 |
| 其他 | — | 5 兜底 |

---

## 7. 重跑分流（按 AppType + 错因）

| 错因类别 | WDL 重跑 | NF 重跑 |
|---|---|---|
| 应用代码 / WDL/NF 源码 bug | `omics run --wdl <整目录> --update <appId> --input <p>` | `omics run --nf <new-cos-path> --name <n> --nf-version <版本>`（**新建**，NF 不支持 --update） |
| 输入参数错（input JSON） | `omics run --app <id> [--version <Ver>] --input <fixed.json>` | `omics run --app <NFappId> --nf-version <版本> --input <fixed.json>`（form C） |
| 资源不足（OOM / 调度） | 改 `runtime { memory/cpu }` 后走"应用代码"路径 | 改 nextflow.config 中 process resources 后走"NF 源码"路径 |
| 平台 / 节点级 | 直接 `omics run --app <id>` 重发 | 直接 `omics run --app <NFappId> --nf-version <版本> --input <p>` 重发 |
