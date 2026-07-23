# 组学平台任务运行错误知识库

> 本知识库用于 `omcs-run-diagnosis` Skill 的自动诊断匹配。
> 每条错误按「错误编号 → 症状 → 根因 → 日志特征 → 解决方案」结构化组织，便于程序化匹配。

---

## 错误分类总览

| 编号 | 错误分类 | 典型触发场景 |
|------|---------|-------------|
| E01 | 批次完成但 COS 无运行结果 | 任务跑完了但输出目录为空 |
| E02 | 批次初始化失败（无子任务） | 提交批次直接失败，没有生成任何子任务 |
| E03 | 子任务数据预处理失败 | 子任务没有作业列表，直接失败 |
| E04 | 内存不足（OOM） | 作业运行中被 OOM Kill |
| E05 | 作业命令行失败 | 作业执行的命令返回非零退出码 |
| E06 | 镜像拉取失败 | Pod 无法拉取容器镜像 |
| E07 | 调度失败/资源不足 | Pod 长时间 Pending 或调度失败 |
| E08 | 任务资源规格不匹配 | Pod 资源请求不符合容器平台要求 |
| E09 | 归档失败 | 作业全部成功但子任务/批次状态为失败 |
| E10 | COS 访问权限不足 | 数据预处理阶段无法访问 COS 桶 |
| E11 | 任务调度运行慢 | 任务排队时间长、执行慢 |

---

## E01 — 批次完成但 COS 无运行结果

### 症状
- 任务批次状态显示完成（COMPLETE），但 COS 输出目录中没有结果文件

### 根因
- 提交任务批次时，**输出目录选择错误**，结果写入了其他 COS 路径

### 日志特征
- `RunStatusTip` / `RunGroupStatusTip` 显示 COMPLETE
- `RunStatusOutput` 中的输出路径与用户期望的 COS 路径不一致

### 解决方案
1. 检查提交任务批次时选择的**任务输出目录**是否正确
2. 查看 `RunStatusOutput` 中的实际输出路径，到对应 COS 路径查找结果
3. 如果输出路径确实错误，需要重新提交任务并指定正确的输出目录

---

## E02 — 批次初始化失败（无子任务）

### 症状
- 任务批次提交后直接显示「已失败」
- 没有生成任何子任务
- RunGroupChildSummaryTip 中无子任务 Uuid

### 根因
1. **工作流或任务输入信息错误**：WDL/NF 脚本语法错误、输入参数缺失或格式不正确
2. **调度底层错误**：平台内部调度服务异常

### 日志特征
- API 返回的 Logs 为空或仅有 `RunGroupStatusTip`
- 无 `RunGroupChildSummaryTip`（没有子任务产生）
- 可能返回 `DataStageLog` 包含初始化阶段的错误信息

### 解决方案
1. **优先自查**：检查工作流代码和配置是否正确
   - WDL：检查 `input` 定义、`runtime` 块、`call` 语句
   - Nextflow：检查 `nextflow.config`、`params` 声明
2. **检查输入参数**：确认所有必填参数都已提供，类型和格式正确
3. **使用自助排查工具**：通过平台控制台的排障工具检查
4. 如果自查无果，**联系平台支持**，可能是调度底层错误

---

## E03 — 子任务数据预处理失败

### 症状
- 子任务创建后没有作业列表（无 Call/Job 记录）
- 子任务状态直接显示失败
- `ErrorCallStderr` / `DataStageLog` 中包含预处理阶段错误

### 根因
1. **数据预处理文件/目录在 COS 中不存在**：源文件路径错误或已被删除
2. **无 COS 访问权限**：运行环境未绑定对应的 COS 桶
3. **其他预处理错误**：数据格式不支持、文件损坏等

### 日志特征
- `DataStageLog` 中包含 `coscli` 相关错误（如 `NoSuchKey`、`not exist`）
- `DataStageLog` 中包含 `Access denied` / `permission denied`
- 无 `CallCommand` / `ErrorCallCommand`（预处理阶段就失败了，作业未启动）

### 解决方案
1. **检查 COS 源文件**：
   - 确认 COS 中源文件路径是否正确
   - 确认任务参数中引用的文件路径与实际一致
2. **检查 COS 访问权限**：
   - 进入平台「文件管理」，确认运行环境已绑定对应的 COS 桶
   - 如未绑定，在环境设置中添加 COS 桶绑定
3. **其他原因**：如以上均正常，联系平台支持

---

## E04 — 内存不足（OOM）

### 症状
- 作业运行过程中突然终止
- 作业详情 → 监控详情中，内存利用率达到 100%
- 作业详情 → 事件中出现 OOM 错误

### 根因
- 容器分配的内存不足以支撑作业运行，被 K8s OOM Killer 终止

### 日志特征（匹配优先级从高到低）
1. `ErrorCallJobEvent` 中：
   - `Reason: SystemOOM`
   - `Message: CGroup OOM encountered`
2. `ErrorCallStderr` 中：
   - `killed`
   - `OutOfMemoryError` / `out of memory`
   - `exit code 137`（OOM Kill 的标准退出码）
3. `CallJobEvent` 中（有时 OOM 事件也会出现在正常事件流中）

### 解决方案
1. **确认 OOM**：在作业详情 → 监控详情中查看内存利用率曲线，确认是否达到 100%
2. **增大内存**：
   - 修改工作流中对应 task/process 的内存配置
   - WDL：修改 `runtime { memory: "XX GB" }`
   - Nextflow：修改 `process { memory = 'XX GB' }`
3. **优化内存使用**：
   - 检查是否有内存泄漏
   - 分批处理大数据集
   - 使用流式处理代替全量加载
4. **重试策略**（Nextflow）：
   ```groovy
   process {
       memory        = { 8.GB * task.attempt }
       errorStrategy = { task.exitStatus == 137 ? 'retry' : 'terminate' }
       maxRetries    = 3
   }
   ```

---

## E05 — 作业命令行失败

### 症状
- 作业的命令行执行返回非零退出码
- stderr/stdout 中显示具体错误信息

### 根因
- 作业脚本中的某个命令执行失败（语法错误、参数错误、依赖缺失等）

### 日志特征
- `ErrorCallCommand`：失败的命令原文
- `ErrorCallStderr`：命令的错误输出，通常包含具体报错信息和退出码
- `ErrorCallStdout`：命令的标准输出，可能包含程序运行到哪一步的信息

### 解决方案
1. **查看 stderr**：作业详情 → 日志 → stderr，定位具体出错的命令和错误信息
2. **查看 stdout**：作业详情 → 日志 → stdout，了解命令执行到了哪一步
3. **结合 ErrorCallCommand**：确认实际执行的命令是否与预期一致
4. **常见修复**：
   - 命令语法错误 → 修正命令
   - 参数错误 → 检查输入参数
   - 依赖缺失 → 在 Dockerfile / 镜像中安装缺失依赖
   - 文件路径错误 → 检查工作流中的路径映射

---

## E06 — 镜像拉取失败

### 症状
- Pod 一直处于 `ImagePullBackOff` 或 `ErrImagePull` 状态
- 作业无法启动

### 根因
1. 使用了**非公共仓库**的镜像，但未配置镜像仓库访问凭证
2. **网络原因**：镜像仓库网络不通或速度过慢
3. **镜像过大**：拉取超时（>100G 的镜像）

### 日志特征
- `ErrorCallJobEvent` 中：
  - `Reason: ImagePullBackOff` 或 `ErrImagePull`
  - `Message` 包含 `Failed to pull image` / `pull access denied`
- `CallJobEvent` 中也可能包含拉取事件

### 解决方案
1. **检查镜像仓库类型**：
   - 如果使用公共仓库镜像 → 确认镜像名称和 tag 正确
   - 如果使用私有仓库 → 在腾讯健康组学平台控制台中为该运行环境添加**镜像仓库访问凭证**
2. **网络问题**：
   - 使用国内镜像仓库以提高拉取速度
   - 避免使用海外镜像源（如 Docker Hub）
3. **镜像过大**：
   - 优化、压缩镜像大小
   - 避免超大镜像（大于 100G）
   - 使用多阶段构建减小镜像体积
4. 已添加凭证但仍失败 → 可能是网络原因，重试或联系平台支持

---

## E07 — 调度失败 / 可用区资源不足

### 症状
- Pod 长时间处于 Pending 状态
- 事件中包含 `insufficient resource` 或 `FailedCreatePodSandBox`

### 根因
1. **可用区资源不足**：短时间提交大量任务，当前可用区资源被占满
2. **集群/环境配额不足**：Pod 数量、CPU、内存达到环境限额

### 日志特征
- `ErrorCallJobEvent` / `CallJobEvent` 中：
  - `Reason: FailedCreatePodSandBox`
  - `Message` 包含 `insufficient resource`
  - 示例：`Failed to create pod sandbox in underlay (will retry): pod:eks-xxxx, zone:ap-guangzhou-6, spec:8,32,1 insufficient resource`
- `Reason: Unschedulable` / `FailedScheduling`

### 解决方案
1. **短期大量任务场景**：
   - 通常等待一段时间后资源释放，任务会自动运行成功
   - 如果时效要求高，联系平台支持进行资源扩容
2. **环境配额不足**：
   - **标准环境**：检查 Pod 使用量是否达到单环境上限（100），达到则更换其他环境
   - **托管环境**：检查 Pod/CPU/内存是否达到环境配置限额，达到则提高环境额度
   - 环境限额查看：[腾讯云控制台 - 环境列表](https://console.cloud.tencent.com/omics/env/env-list)
3. **提高引擎并发**：
   - 如果配额未满但任务仍慢，可提高工作流引擎资源配额（增加同时执行的工作流数量）
4. **资源规格检查**：同时检查是否触发了 E08（资源规格不匹配）

---

## E08 — 任务资源规格不匹配

### 症状
- Pod 长时间处于调度状态，无法启动
- 事件中出现 `Unschedulable` 但不是因为资源不足

### 根因
- 工作流中定义的 Pod 资源规格不符合腾讯云容器平台的要求
- 例如：1核16G 这种非标准规格

### 日志特征
- `ErrorCallJobEvent` / `CallJobEvent` 中：
  - `Reason: Unschedulable` 或 `FailedScheduling`
  - `Message` 不包含 `insufficient resource`（区别于 E07）

### 解决方案
1. **调整资源规格**：参照腾讯云容器服务按量计费模式文档调整
   - 文档：https://cloud.tencent.com/document/product/457/74015
2. **使用标准规格**：避免使用非标准的 CPU/内存比（如 1核16G）
3. **常见标准规格**：
   - 2核4G、4核8G、8核16G、8核32G、16核32G、16核64G 等
4. 修改工作流中的 `runtime`（WDL）或 `process`（Nextflow）资源定义

---

## E09 — 归档失败

### 症状
- 子任务中所有作业都运行成功
- 但子任务/批次整体状态显示为失败

### 根因
- **归档阶段失败**：作业结果文件从运行环境回传到 COS 时出错

### 日志特征
- `DataStageLog` 中包含归档阶段的错误信息
- 所有 `Call*` 类型日志均正常（无 `Error*`）
- 失败发生在作业完成之后

### 解决方案
1. **查看 DataStageLog**：检查归档阶段的错误详情
2. **常见归档失败原因**：
   - COS 输出目录权限不足
   - COS 桶配额已满
   - 网络问题导致上传超时
3. 如果无法自行判断，使用平台排障工具查询，或**联系平台支持**

---

## E10 — COS 访问权限不足

### 症状
- 数据预处理阶段报错，作业无法启动
- 与 E03 类似，但更聚焦于权限问题

### 根因
- 运行环境未绑定任务所需的 COS 桶，或绑定的凭证已过期

### 日志特征
- `DataStageLog` 中包含：
  - `Access denied`
  - `permission denied`
  - `403 Forbidden`
  - `coscli` 命令返回权限错误

### 解决方案
1. 进入平台「文件管理」，确认运行环境已绑定对应的 COS 桶
2. 如未绑定，在环境设置中添加 COS 桶绑定
3. 检查 COS 桶的访问策略是否允许当前环境的服务角色访问
4. 确认 COS 桶所在地域与运行环境一致

---

## E11 — 任务调度运行速度慢

### 症状
- 任务提交后长时间处于排队/等待状态
- 并发任务数明显低于预期

### 根因
1. **环境配额达到上限**：Pod/CPU/内存达到限额
2. **引擎并发数不足**：工作流引擎同时执行的工作流数量过低
3. **可用区资源不足**：短时间大量任务导致资源紧张

### 日志特征
- `CallJobEvent` 中可能包含 `insufficient resource`（但任务最终能运行）
- 无致命错误，主要是调度延迟

### 解决方案
1. **检查环境资源**：
   - **标准环境**：Pod 使用量是否达到上限（100）？达到 → 更换环境
   - **托管环境**：Pod/CPU/内存是否达到限额？达到 → 提高额度
   - 限额查看：[腾讯云控制台 - 环境列表](https://console.cloud.tencent.com/omics/env/env-list)
2. **提高引擎并发**：如果配额未满，提高工作流引擎资源配额
3. **可用区资源不足**：
   - 短期大量任务场景，等待资源释放后自动恢复
   - 时效要求高 → 联系平台支持进行资源扩容
4. **错峰提交**：避免在高峰期提交大量任务

---

## 诊断匹配速查表

> Agent 在 Step 3 匹配时，可按此表快速定位错误编号。

| 关键字 / 正则模式 | 匹配错误编号 |
|------------------|-------------|
| `SystemOOM` / `CGroup OOM` / `exit code 137` / `OutOfMemory` | E04 |
| `ImagePullBackOff` / `ErrImagePull` / `Failed to pull image` | E06 |
| `FailedCreatePodSandBox` / `insufficient resource` | E07 |
| `Unschedulable` / `FailedScheduling`（无 insufficient resource） | E08 |
| `NoSuchKey` / `not exist` / `No such file` | E03 |
| `Access denied` / `permission denied` / `403` | E10 |
| `killed`（非 OOM 上下文） | E05 |
| DataStageLog 错误 + 所有 Call 正常 | E09 |
| 仅 RunGroupStatusTip（COMPLETE） + 用户报告无结果 | E01 |
| 无子任务 + 批次失败 | E02 |
| 子任务无作业列表 + 失败 | E03 |
| 长时间 Pending + 无 Warning 事件 | E11 |
