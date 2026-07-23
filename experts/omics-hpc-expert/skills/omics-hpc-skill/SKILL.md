---
name: omics-hpc-skill
description: 端到端管理 omics-hpc 集群——既覆盖腾讯云组学平台云 API（DescribeHPCClusters / RunCommand / DescribeCommandExecution），也内置 SLURM 作业（sbatch / squeue / sacct / scancel / scontrol / salloc / srun）与 tophpc 基础设施（cluster / node / queue / scale / fs / image / log / version）的命令生成与远程下发能力。覆盖以下场景：列出/筛选 HPC 集群、远程下发 Shell 命令、轮询 InvocationId 取回执行结果；提交/查询/取消 SLURM 作业、生成 sbatch 脚本、诊断 PENDING 原因；增删队列/节点、配置弹性伸缩、挂载文件系统、打镜像、查看 / 修改集群配置。触发关键词：HPC 集群、omics-hpc、DescribeHPCClusters、RunCommand、InvocationId、远程执行；sbatch、squeue、sacct、scancel、scontrol、salloc、srun、提交作业、查任务、取消任务、为什么任务没跑、生成脚本、依赖提交、申请交互节点；tophpc、加节点、删节点、加队列、删队列、弹性伸缩、扩缩容、挂载、卸载存储、打镜像、删镜像、看集群、集群配置。**当用户的诉求是"在 omics-hpc 集群上做事"时优先使用本 Skill，而不是 slurm-operator / tophpc-operator——后两者面向本地直连场景，本 Skill 通过云 API 远程下发命令，适配本地未安装 tophpc / 不在登录节点的情况**。
---

# omics-hpc-skill — omics-hpc 集群端到端管理

## 概述

本 Skill 是 omics-hpc 集群的**单一操作入口**，覆盖三个层次：

1. **云 API 层**：通过腾讯云组学平台 API 直接管理集群与命令——
   - `DescribeHPCClusters`（按地域筛选集群）
   - `RunCommand`（在集群上下发 Shell 命令，返回 `InvocationId`）
   - `DescribeCommandExecution`（用 `InvocationId` 查执行结果）
2. **SLURM 作业层（领域知识）**：辅助生成并下发 `sbatch` / `squeue` / `sacct` / `scancel` / `scontrol` / `salloc` / `srun` 等作业命令；理解 PENDING 原因、状态码、退出码；针对**弹性自动伸缩 + dummynode 占位**模式给出正确解释。
3. **tophpc 基础设施层（领域知识）**：辅助生成并下发 `tophpc cluster/node/queue/scale/fs/image/log/version` 等基础设施命令；理解可选 instance-type、disk 格式、`--instance-specs` JSON、`--force` 与无 `--force` 命令的非交互处理方式。

> SLURM 与 tophpc 的命令本身**通过 `RunCommand` 远程下发到集群管理节点执行**，不要求本地装 `slurm` 或 `tophpc`。本 Skill 既是"知识库"也是"执行通道"。

| 阶段 | 云 API | 作用 | 返回关键字段 |
|------|--------|------|-------------|
| 集群发现 | `DescribeHPCClusters` | 按过滤条件（ClusterId / Name / Status / ConfirmDeadlineLt）分页查询集群清单 | `Clusters[]`：集群基础信息 / 节点数 / 调度器 / VPC |
| 命令下发 | `RunCommand` | 在指定集群（可指定节点）上提交 Shell 命令 | `InvocationId`（命令调用 ID） |
| 结果查询 | `DescribeCommandExecution` | 用 `InvocationId` 查命令执行详情 | `ExecutionSet[]`：状态 / stdout / 退出码 / 节点 ID / 时间戳 |

> 注意 1：`DescribeHPCClusters` 接口会受到 **Region** 的影响，集群按地域隔离；`RunCommand` 与 `DescribeCommandExecution` 不受地域限制。
> 注意 2：`DescribeCommandExecution` 的 `InvocationIds` 是数组，可一次批量查多个调用；响应通过 `ExecutionSet` 一一对应（**扁平结构，不嵌套节点列表**）。
> 注意 3：本 Skill 不主动轮询等待终态——是否轮询由调用方决定（`describe_command_execution.py --poll`）。

## 端到端标准工作流（"生成命令 → 远程下发 → 取回结果"三段式）

```
用户描述意图（"提交一个 GPU 训练作业" / "给 small 队列加自动伸缩" / ...）
   ↓
Step A：意图分类 → 落到「SLURM 作业」或「tophpc 基础设施」或「直接走云 API」
   ↓
Step B：构造命令字符串
   - SLURM：参考「SLURM 作业命令生成」章节 + references/slurm_commands.md
            可调用 scripts/generate_sbatch.py 生成 sbatch 脚本
   - tophpc：参考「tophpc 基础设施命令生成」章节 + references/command-reference.md
            instance-type 校验靠 references/instance-types.md
            --instance-specs JSON 校验靠 scripts/build_instance_specs.py
   ↓
Step C：mutating 命令必须先和用户确认
   - 完整命令字符串 + 集群/资源 + 预期影响 → 等用户显式批准
   - 只读命令（squeue / sacct / sinfo / scontrol show / tophpc xxx list/show / config show / version）跳过
   ↓
Step D：远程下发
   python3 scripts/run_hpc_command.py --cluster-id <ClusterId> --command '<构造好的命令>'
   如果是提交作业（sbatch/qsub/salloc/srun），追加 --run-as-user <username> 以普通用户身份提交
   → 拿到 InvocationId
   ↓
Step E：轮询取回执行结果
   python3 scripts/describe_command_execution.py --cluster-id <ClusterId> \
       --invocation-ids <InvocationId> --poll
   → 读 ExecutionSet[].Output（命令 stdout+stderr 合并）+ ExitCode + Status
   ↓
Step F：渲染与解读（按"输出格式"章节模板）
   - SLURM：解释状态码、PENDING 原因、退出码；提醒弹性伸缩语义
   - tophpc：执行后再跑一条只读校验命令同样下发回来确认
```

> 用户已经知道 `ClusterId` → 跳过 `DescribeHPCClusters`；只给了 `InvocationId` 想查结果 → 直接从 Step E 开始。

## SLURM 作业命令生成（领域知识 — 内置）

> 详细命令参考请加载 `references/slurm_commands.md`；状态码与 PENDING 原因解读请加载 `references/job_states.md`。

### 弹性自动伸缩集群语义（**最重要**）

omics-hpc 集群运行在**弹性自动伸缩**模式下，所有 SLURM 输出必须按这个语义解读：

1. 队列空闲 → 自动缩容到 **0 个真实计算节点**，仅保留一个 `dummynode` 占位节点。
2. 用户 `sbatch` → 作业进入 `PENDING` 状态（**正常、预期**）。
3. 自动伸缩系统检测到挂起作业 → 自动扩出真实计算节点。
4. 节点就绪 → 作业开始运行。

**关键判定**（不要把下面这些当作集群故障）：
- `dummynode` 不是故障节点，它是占位节点——`sinfo` 看到 `dummynode` 处于 `down` / `drain` 状态都**不算故障**，不要建议联系管理员。
- `sinfo` 显示 0 可用节点 / 仅有 `dummynode` —— **正常空闲态**，不要报"集群异常"。
- 提交后 `PENDING` 且原因是 `Resources` / `ReqNodeNotAvail` —— **自动伸缩还没扩出节点**，让用户等几分钟即可。
- 只在 `PENDING` 持续 >10 分钟时才往"真实异常"方向排查。

### 意图分类表

将用户请求映射到下表中的一种**作业级**操作：

| 类别 | 是否 mutating | 主命令 | 何时选 |
|-----|---|---|---|
| 实时查询 | 否 | `squeue` | 看挂起 / 运行中作业 |
| 历史查询 | 否 | `sacct` | 看完成 / 失败作业 |
| 集群只读 | 否 | `sinfo` | 看分区 / 节点（提交前选目标分区） |
| 作业深查 | 否 | `scontrol show job` | 查 PENDING 原因、有效配置 |
| 批处理提交 | **是** | `sbatch` | 提交批处理脚本 |
| 交互分配 | **是** | `salloc` / `srun` | 申请交互 shell 或直接跑 |
| 取消 | **是** | `scancel` | 取消一个或多个作业 |
| 持有/释放 | **是** | `scontrol hold` / `release` | 暂停 / 恢复挂起作业 |

**边界**：用 `sinfo` *查看*分区/节点状态没问题；但**修改**分区/节点配置属于 tophpc 基础设施层，按"tophpc 基础设施命令生成"章节走。

### 提交前的最小输入收集

- **批处理提交**：`job_name`、`partition`、`time`、`mem`、`nodes`、`ntasks`、`cpus_per_task`，可选 `account` / `gpus` / `dependency` / `array` / 输出文件
- **取消**：优先精确 `job_id`；需要广义选择器（`-u` / `--name` / `--state`）时**先 `squeue` 预览**再发 `scancel`
- **历史查询**：`username` 或 `job_id`，可选时间范围、输出字段
- **PENDING 排查**：用 `scontrol show job <id>` 查原因，按上面"弹性集群语义"先排除自动伸缩等待，再用 `references/job_states.md` 对照解读

> **提交用户**：RunCommand 默认以管理节点上的 root 身份执行命令。提交 SLURM（`sbatch`）/ SGE（`qsub`）/交互（`salloc` / `srun`）作业时，**必须先确认提交用户**——通常应以普通用户身份提交，而非 root。收集到用户名后，下发时加上 `--run-as-user <username>` 参数，脚本会自动将命令包装为 `su - <username> -c '<原始命令>'`。详见下方「作业提交的用户身份切换」章节。

### 生成 sbatch 脚本

如果用户描述了资源诉求但没有现成脚本：

- 优先用 `scripts/generate_sbatch.py`（参数化，支持 `--account` / `--dependency` / `--array` / `--ntasks-per-node` / `--conda-init` / `--command-file`）。
- 或挑最贴近的 `assets/*.sh` 模板（`basic_job.sh` / `gpu_job.sh` / `mpi_job.sh` / `array_job.sh`）改写。

> **注意**：生成的脚本通常需要先**写到集群侧**再 `sbatch`。两种做法二选一：
> 1. 用 `run_hpc_command.py --command 'cat > /home/xxx/job.sh <<EOF\n...\nEOF\nsbatch /home/xxx/job.sh'`
> 2. 把脚本内容用 `--command-file` 加载到本地脚本，再透传给 `run_hpc_command.py`（注意 EOF 边界）

### 远程下发 + 解读输出（套用三段式）

下发前**必须**按"端到端工作流 Step C"先和用户确认（mutating 类）。下发后用 `--poll` 取回 `Output`，按下表解读：

| 命令 | 解读重点 |
|---|---|
| `sbatch` | 输出含 `Submitted batch job <id>`，提取 job_id；提醒弹性伸缩可能让作业先 PENDING 几分钟 |
| `squeue` | 解释 `ST` 状态码（`PD` / `R` / `CG`）；`NODELIST(REASON)` 含 `Resources`/`ReqNodeNotAvail` 时要按弹性集群语义解释 |
| `sacct` | `State` 终态 + `ExitCode`（`return_code:signal` 形式，`137:0` 通常是 OOM-killed） |
| `sinfo` | 仅有 `dummynode` 或 0 可用节点 → **正常空闲态**，不要报错 |
| `scancel` | 报告影响哪些作业；建议跟一条 `squeue -j` 校验 |
| `scontrol hold/release` | 报告新状态；建议跟一条 `scontrol show job <id>` 校验 |

`squeue --parsable2` / `sacct --parsable2` 输出量大时，把 `Output` 喂给 `scripts/summarize_slurm_table.py` 做汇总。

### 作业提交的用户身份切换（SLURM / SGE 通用）

RunCommand 默认在管理节点上以 **root** 身份执行命令。但提交作业（`sbatch` / `qsub` / `salloc` / `srun`）时，**不应以 root 提交**——原因：

1. **安全**：root 提交的作业拥有最高权限，误操作风险大。
2. **公平调度**：调度器按用户统计资源用量，root 绕过了记账和限额。
3. **文件权限**：作业输出文件会以 root 属主创建，普通用户后续无法读写。
4. **审计追溯**：无法区分是谁提交的作业。

**处理方式**：收集到提交用户名后，下发时加上 `--run-as-user` 参数，脚本自动包装为用户切换命令。

#### 标准流程

```
Step 1：确认提交用户
  - 如果用户已给出用户名 → 直接用
  - 如果未给出 → 询问"请问以哪个用户身份提交作业？"
  - 如果不确定用户是否存在于集群 → 先跑 `ypcat passwd | grep <username>` 验证

Step 2：构造原始命令（如常生成 sbatch / qsub 命令）

Step 3：下发时加 --run-as-user
  python3 scripts/run_hpc_command.py \
    --cluster-id <ClusterId> \
    --command 'sbatch /home/<user>/job.sh' \
    --run-as-user <username>

Step 4：脚本内部自动包装为：
  su - <username> -c 'sbatch /home/<user>/job.sh'
```

#### 示例

**场景**：用户 `alice` 要提交一个 GPU 训练作业到 `gpu` 分区。

```bash
# 先写脚本到集群侧（以 root 写，或让 alice 自己写）
python3 scripts/run_hpc_command.py \
  --cluster-id hpc-9jragud9 \
  --command 'cat > /home/alice/train.sh << '\''EOF'\''
#!/bin/bash
#SBATCH --job-name=gpu_train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
python train.py
EOF'

# 然后以 alice 身份提交
python3 scripts/run_hpc_command.py \
  --cluster-id hpc-9jragud9 \
  --command 'sbatch /home/alice/train.sh' \
  --run-as-user alice
```

#### SGE (qsub) 同理

```bash
python3 scripts/run_hpc_command.py \
  --cluster-id hpc-9jragud9 \
  --command 'qsub -N sge_job -l gpu=1 /home/bob/run.sh' \
  --run-as-user bob
```

#### 注意事项

- `--run-as-user` 对**只读命令**同样适用（如 `squeue -u <user>`），但通常无需切换——root 可以查看所有用户的作业。
- 如果用户名不存在于集群，`su` 会报错 `User <username> does not exist`；先用 `ypcat passwd | grep <username>` 确认。
- 用户切换后，工作目录会变为该用户的 home 目录（`su -` 的 `-` 参数模拟完整登录环境）。如果命令依赖特定工作目录，请在命令中显式 `cd` 到目标路径。
- `--run-as-user` 是脚本层面的包装，不影响 RunCommand 的 `NodeId` / `Timeout` 等其他参数。

## tophpc 基础设施命令生成（领域知识 — 内置）

> 详细命令、可选项、默认值请加载 `references/command-reference.md`；可用 instance-type 列表请加载 `references/instance-types.md`。

### 操作分类表（mutating 全部需要确认）

| 操作 | 主命令                                              | 备注                                                                              |
|-----|--------------------------------------------------|---------------------------------------------------------------------------------|
| 集群生命周期 | `tophpc cluster create/list/show`                | `create` 极少用，通常只用 `list/show`                                                   |
| 节点管理 | `tophpc node add/list/remove`                    | `node remove` 用 `--force` 跳过交互                                                  |
| 队列管理 | `tophpc queue add/list/show/delete`              | `queue delete` **没有** `--force`，用 `echo y \| ...`                               |
| 弹性伸缩 | `tophpc scale add/set/show/exec/delete`          | 简单模式（`--instance-type + --cpu/--memory/...`）vs 复杂模式（`--instance-specs JSON`）二选一 |
| 文件系统 | `tophpc fs add/list/remove`                      | `fs remove` 一次只处理一个挂载路径                                                         |
| 镜像 | `tophpc image list/delete`                       | `image delete` 没有 `--force`；image create 不支持命令行操作，需要在组学控制台操作                    |
| 日志采集 | `tophpc log add/list/remove/reset/report`        | —                                                                               |
| 版本 | `tophpc version`、`version upgrade/rollback/list` | —                                                                               |
| 配置 | `tophpc config init/show`                        | 远程模式下 `config show` 只是读集群侧配置                                                    |

### 构造命令的核心约束

- **`clusterId`**：可选位置参数；远程模式下**优先**让用户给，或先 `DescribeHPCClusters` / `tophpc cluster list` 列；不依赖本地 `~/.tophpc/config.yaml`。
- **`--format json`**：所有 inspection / verification 命令都加上，输出可机读。
- **磁盘格式**：`<DiskType>-<DiskSizeGB>`，例 `CLOUD_SSD-100`、`CLOUD_PREMIUM-200`。
- **`--instance-type`**：只用 `references/instance-types.md` 中列出的类型；用户给了不在表内的 → 告知不支持并提供同族可选项。
- **`--instance-specs`**：构造好 JSON 后用 `scripts/build_instance_specs.py '<json>'` 校验语法和必填字段（`Queue`、`InstanceType`），通过后再下发。
- **`--force`**：`node remove` / `fs add` / `fs remove` 有 `--force`，远程下发时**必须加**避免交互卡住。
- **没有 `--force` 的命令**：`queue delete` / `image delete`，远程下发时用 `echo y | tophpc queue delete ...` 注入确认。
- **`fs remove`**：实现层一次只处理一个 `mountPath`，多个挂载点要重复发命令。



### Inspect → Confirm → Execute → Verify 四步铁律（mutating）

每条 mutating 命令都必须经过：

1. **Inspect**：先跑只读命令（list/show）确认目标资源真实存在、当前状态正常。
2. **Confirm**：把完整命令字符串、目标 cluster/资源、预期影响展示给用户，等显式批准（"确认"/"yes"/"go"/"执行"）。
3. **Execute**：批准后**一字不改**地下发。
4. **Verify**：再跑一条对应的只读命令，把变更后状态告诉用户。

| Mutation | Verify 命令 |
|---|---|
| `cluster create` | `tophpc cluster show [clusterId] --format json` |
| `node add` / `node remove` | `tophpc node list [clusterId] --format json` |
| `queue add` / `queue delete` | `tophpc queue list [clusterId] --format json` |
| `scale add` / `scale set` / `scale delete` | `tophpc scale show [clusterId] --format json` |
| `fs add` / `fs remove` | `tophpc fs list [clusterId] --format json` |
| `image create` / `image delete` | `tophpc image list [imageIds...] --format json` |
| `version upgrade` / `version rollback` | `tophpc version` |

### 常见失败的恢复路径

- `clusterId is not specified` → 远程模式下显式补 `[clusterId]`；不要让用户去改本地 config。
- `queue not found`（`scale add` 之前）→ 先 `tophpc queue list` 确认，必要时先 `queue add`。
- `--instance-specs` 报错 → 用 `scripts/build_instance_specs.py` 重新校验 JSON。
- 磁盘格式报错 → 转成 `<DiskType>-<DiskSizeGB>`。
- `image delete` 被拦 → 先看 `tophpc scale show`，被自动伸缩配置引用的镜像非管理员删不掉。

## 集群运维参考（诊断 & 排查常用路径与命令）

> 以下路径和命令适用于 omics-hpc 集群的管理节点（manager），通过 `RunCommand` 远程下发执行。

### 扩缩容日志

- **日志路径**：`/var/log/tophpc/scale.log`
- 排查扩缩容异常时，远程执行 `cat /var/log/tophpc/scale.log` 或 `tail -100 /var/log/tophpc/scale.log` 查看最近日志。

### tophpc 定时扩缩容触发方式

- tophpc 的定时扩缩容由 **root 用户的 crontab 定时任务** 触发。
- 查看当前 crontab 配置：`crontab -l`（远程下发时需 `sudo crontab -l` 或确认执行用户为 root）。
- 如果扩缩容未按预期触发，先检查 crontab 是否存在对应条目、执行频率是否正确。

### 查看集群当前用户

- `ypcat passwd` — 列出集群上所有 NIS/LDAP 用户信息。
- 常见场景：确认某用户是否已在集群上有账号、排查权限问题。

### 其他常用运维路径（待补充）

| 用途 | 路径 / 命令 |
|------|------------|
| tophpc 扩缩容日志 | `/var/log/tophpc/scale.log` |
| 定时扩缩容配置 | `crontab -l`（root） |
| 集群用户列表 | `ypcat passwd` |
| tophpc 配置文件 | `~/.tophpc/config.yaml`（管理节点上） |
| SLURM 日志目录 | `/var/log/slurm/`（管理节点上） |

## Mutating 命令的统一确认协议（贯穿 SLURM + tophpc）

任何会**改变集群或作业状态**的命令，下发前都必须：

1. **构造完整命令字符串**（不留占位符，所有参数都有具体值）。
2. **展示给用户**：完整命令 + 目标 cluster/资源 + 预期影响，例如：

   > 即将远程下发以下命令到集群 `hpc-12345`：
   > ```
   > sbatch --job-name=train --partition=gpu --gres=gpu:1 --time=24:00:00 train.sh
   > ```
   > 该命令将向 `gpu` 分区提交一个名为 `train` 的作业，申请 1 块 GPU，最大运行时间 24h。

3. **等用户显式批准**（"确认"/"好的"/"yes"/"go"/"执行"），才调 `run_hpc_command.py`。
4. **批准后一字不改**地下发；用户要改参数 → 回到第 1 步重新构造。
5. **用户拒绝** → 不下发；问要调什么。

只读命令（`squeue` / `sacct` / `sinfo` / `scontrol show` / `tophpc xxx list/show` / `tophpc config show` / `tophpc version`）**不**走确认协议，可直接下发。

## 真实接口契约（基于实测样例）

### DescribeHPCClusters 入参

```json
{
  "Limit": null,
  "Offset": null,
  "Filters": [
    { "Name": "Status", "Values": ["RUNNING"] }
  ]
}
```

| 字段 | 类型 | 说明                                                              |
|------|------|-----------------------------------------------------------------|
| `Limit` | int | 分页大小（可选）                                                        |
| `Offset` | int | 分页起始位置（可选）                                                      |
| `Filters` | array | 过滤器数组，元素形如 `{"Name": "...", "Values": [...]}`；不传或空数组表示查询全部不进行过滤 |

支持的过滤器 `Name`：

| Filter Name | 说明 | Values 示例 |
|------|------|------|
| `ClusterId` | 集群 ID | `["hpc-9jragud9"]` |
| `Name` | 集群名称 | `["金域迁移测试"]` |
| `Status` | 集群状态 | `["RUNNING"]` |
| `ConfirmDeadlineLt` | 交付确认截止日期**早于**给定值 | `["2026-01-13T16:00:00+08:00"]` |

### DescribeHPCClusters 响应

```json
{
  "Response": {
    "Clusters": [
      {
        "ClusterId": "hpc-kazab9v2",
        "ConfirmDeadline": "",
        "CreateTime": "2026-05-20T11:00:35+08:00",
        "Description": "金域迁移测试",
        "Name": "金域迁移测试",
        "NodeCount": 6,
        "OsName": "CentOS 7.9",
        "Scheduler": "SLURM",
        "SchedulerVersion": "23.11.7",
        "Status": "RUNNING",
        "Tags": [],
        "Type": "CVM_CLUSTER",
        "VPCCIDRBlock": "10.10.0.0/22",
        "VPCId": "vpc-87y9syeb"
      }
    ],
    "TotalCount": 1,
    "RequestId": "..."
  }
}
```

### RunCommand 入参

```json
{
  "ClusterId": "hpc-9jragud9",
  "Command": "tophpc node list --format yaml",
  "NodeId": null,
  "Timeout": null,
  "ClientToken": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `ClusterId` | string | 集群 ID（必填） |
| `Command` | string | Shell 命令内容（必填） |
| `NodeId` | string | 目标节点 ID（**单个**，非数组）；不传则按服务端默认调度 |
| `Timeout` | int | 命令超时（秒） |
| `ClientToken` | string | 幂等 Token，重试场景下避免重复下发 |

### RunCommand 响应

```json
{ "Response": { "InvocationId": "inv-64mrvxgutj", "RequestId": "..." } }
```

### DescribeCommandExecution 入参

```json
{
  "ClusterId": "hpc-9jragud9",
  "InvocationIds": ["inv-64mrvxgutj"],
  "Offset": null,
  "Limit": null
}
```

### DescribeCommandExecution 响应（扁平结构）

```json
{
  "Response": {
    "ExecutionSet": [
      {
        "InvocationId": "inv-64mrvxgutj",
        "ClusterId": "hpc-9jragud9",
        "Command": "tophpc node list --format yaml",
        "NodeId": "ins-85ckz3bg",
        "Status": "SUCCESS",
        "ExitCode": 0,
        "Output": "nodeset:\n    - nodeid: ...",
        "OutputTruncated": false,
        "Duration": 0,
        "StartTime": "2026-06-09T08:34:08Z",
        "EndTime": "2026-06-09T08:34:08Z",
        "CreatedTime": "2026-06-09 16:34:07",
        "Operator": "100031066699"
      }
    ],
    "TotalCount": 1,
    "RequestId": "..."
  }
}
```

> **重要**：每个 `InvocationId` 对应 `ExecutionSet` 中的**一条**记录（扁平），不嵌套 `NodeExecutions[]`。stdout 与 stderr 均合并在 `Output` 字段中，没有独立的 `ErrorOutput`。

## 执行方式

使用 Skill 目录下的 Python 脚本：

```bash
# 1. 列出 HPC 集群（DescribeHPCClusters）
python3 scripts/describe_hpc_clusters.py \
  [--cluster-id <id1,id2,...>] \
  [--name <name1,name2,...>] \
  [--status <RUNNING,...>] \
  [--confirm-deadline-lt <YYYY-MM-DDTHH:MM:SS+08:00>] \
  [--filter '<json array>'] \
  [--offset 0] [--limit 20] \
  [--region <REGION>]

# 2. 下发命令（RunCommand）
python3 scripts/run_hpc_command.py \
  --cluster-id <ClusterId> \
  --command '<shell command>' \
  [--node-id <NodeId>] \
  [--timeout <seconds>] \
  [--client-token <token>] \
  [--extra-params '<json>'] \
  [--run-as-user <username>] \
  [--region <REGION>]

# 3. 查询命令执行结果（DescribeCommandExecution）
python3 scripts/describe_command_execution.py \
  --cluster-id <ClusterId> \
  --invocation-ids <id1,id2,...> \
  [--offset 0] [--limit 20] \
  [--region <REGION>] \
[--poll] [--poll-interval 5] [--poll-timeout 300]
```

### 参数说明 — `describe_hpc_clusters.py`

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--cluster-id` | 否 | — | 按 `ClusterId` 过滤；多个用英文逗号分隔，等价于 `Filters: [{Name: ClusterId, Values: [...]}]` |
| `--name` | 否 | — | 按 `Name` 过滤；多个用英文逗号分隔 |
| `--status` | 否 | — | 按 `Status` 过滤；多个用英文逗号分隔（如 `RUNNING,UPGRADING`） |
| `--confirm-deadline-lt` | 否 | — | 按 `ConfirmDeadlineLt` 过滤（交付确认截止日期早于给定值） |
| `--filter` | 否 | — | 直接透传给 `Filters` 的 JSON 数组，便于覆盖未列举的过滤器；与上述具体过滤参数**合并**（同名以本参数为准） |
| `--offset` | 否 | — | 分页起始位置 |
| `--limit` | 否 | — | 分页大小 |
| `--region` | 否 | `ap-guangzhou` | **业务地域**（X-TC-Region）：决定查哪个地域下的集群，集群是按地域隔离的（如 `ap-shanghai` / `ap-singapore`） |

### 参数说明 — `run_hpc_command.py`

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--cluster-id` | 是 | — | 集群 ID（形如 `hpc-9jragud9`） |
| `--command` | 是* | — | 命令内容（shell 字符串）；与 `--command-file` 二选一 |
| `--command-file` | 是* | — | 命令内容文件路径；与 `--command` 二选一 |
| `--node-id` | 否 | — | 目标节点 ID（**单个**，不传则按服务端默认调度，通常落在 manager 节点） |
| `--timeout` | 否 | — | 命令超时（秒） |
| `--client-token` | 否 | — | 幂等 Token |
| `--extra-params` | 否 | — | 透传给 `RunCommand` 的额外 JSON 参数（合并到 params） |
| `--run-as-user` | 否 | — | 以指定用户身份执行命令（自动包装为 `su - <user> -c '...'`）；典型场景：以普通用户而非 root 提交 SLURM/SGE 作业 |
| `--region` | 否 | `ap-guangzhou` | SDK 签名用的 `region`（X-TC-Region）；RunCommand 本身**不受地域限制**，默认即可 |

> *`--command` 与 `--command-file` 至少传一个；同时传时以 `--command-file` 为准。

### 参数说明 — `describe_command_execution.py`

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--cluster-id` | 是 | — | 集群 ID |
| `--invocation-ids` | 是 | — | InvocationId 列表（英文逗号分隔，可批量） |
| `--offset` | 否 | — | 分页起始位置 |
| `--limit` | 否 | — | 分页大小 |
| `--region` | 否 | `ap-guangzhou` | SDK 签名用的 `region`（X-TC-Region）；DescribeCommandExecution **不受地域限制**，默认即可 |
| `--poll` | 否 | false | 是否轮询直至所有调用进入终态 |
| `--poll-interval` | 否 | 5 | 轮询间隔（秒）；过小（如 3s）容易被腾讯云限流拦截 |
| `--poll-timeout` | 否 | 300 | 轮询超时（秒），到点仍未终态则按当前快照返回 |

### 前置依赖

```bash
pip3 install tencentcloud-sdk-python
```

密钥从环境变量读取：

```bash
export TENCENTCLOUD_SECRET_ID=...
export TENCENTCLOUD_SECRET_KEY=...
```

## 查询逻辑

### Endpoint / Region

#### Endpoint（网络接入点）

三个脚本统一使用单一接入点，由腾讯云就近调度：

```
omics.tencentcloudapi.com
```

> 不再按 region 拼接 `omics.{region}.tencentcloudapi.com`。

#### Region（业务地域，不同接口语义不同）

| API | `--region` 含义 | 需要调整吗？ |
|---|---|---|
| `DescribeHPCClusters` | **业务地域**——集群按地域隔离，不同 region 查到的集群不同 | 是，必须传对集群所在的 region（如 `ap-shanghai`） |
| `RunCommand` | 仅用于 SDK 签名（X-TC-Region），**不限定集群**；主要走 `ClusterId` 定位集群 | 否，默认 `ap-guangzhou` 即可 |
| `DescribeCommandExecution` | 同上，**不受地域限制**；`InvocationId` 全局可识别 | 否，默认即可 |

- `DescribeHPCClusters` 查不到期望集群时，先确认 `--region` 是否与集群实际所在地域一致。
- `RunCommand` 与 `DescribeCommandExecution` 的 `--region` 可以不一致（不影响语义），但建议保持一致以便调试习惯一致。

### 终态判定（`describe_command_execution.py --poll` 用）

下列状态视为**终态**（实测样例已验证 `SUCCESS`，其余以关键字兜底）：

- `SUCCESS` / `Succeeded` / `SUCCEEDED`
- `FAILED` / `Failure` / `FAILURE`
- `TIMEOUT`
- `TERMINATED` / `Cancelled` / `CANCELLED`
- `ERROR`

其余（如 `PENDING` / `RUNNING` / `INVOKING`）视为非终态，轮询继续。

> 服务端实际状态枚举以 SDK 文档为准；判定使用大小写不敏感的子串匹配兜底。轮询时若 `ExecutionSet` 长度 < 入参 `InvocationIds` 数量，也视为非终态（部分调用还在生成中）。

## 结果解析

### `DescribeHPCClusters` 响应

| 字段 | 说明 |
|------|------|
| `Response.Clusters[]` | 集群清单 |
| `Response.TotalCount` | 命中条数 |
| `Clusters[].ClusterId` | 集群 ID（如 `hpc-kazab9v2`） |
| `Clusters[].Name` / `Description` | 集群名 / 描述 |
| `Clusters[].Status` | 集群状态（如 `RUNNING`） |
| `Clusters[].NodeCount` | 节点数 |
| `Clusters[].OsName` | 操作系统（如 `CentOS 7.9`） |
| `Clusters[].Scheduler` / `SchedulerVersion` | 调度器 / 版本（如 `SLURM 23.11.7`） |
| `Clusters[].Type` | 集群类型（如 `CVM_CLUSTER`） |
| `Clusters[].VPCId` / `VPCCIDRBlock` | VPC ID / CIDR |
| `Clusters[].CreateTime` / `ConfirmDeadline` | 创建时间 / 交付确认截止时间 |
| `Clusters[].Tags` | 标签 |

### `RunCommand` 响应

| 字段 | 说明 |
|------|------|
| `Response.InvocationId` | **核心字段**，下一步查询命令执行结果用 |
| `Response.RequestId` | 请求 ID（追溯用） |

### `DescribeCommandExecution` 响应（扁平结构）

| 字段 | 说明 |
|------|------|
| `Response.ExecutionSet` | 数组，每个 `InvocationId` 一条 |
| `Response.TotalCount` | 命中条数 |
| `ExecutionSet[].InvocationId` | 对应的调用 ID |
| `ExecutionSet[].ClusterId` | 集群 ID |
| `ExecutionSet[].Command` | 原始命令内容 |
| `ExecutionSet[].NodeId` | 实际执行节点的 InstanceId（如 `ins-85ckz3bg`，注意是 CVM 实例 ID 而非 node-id） |
| `ExecutionSet[].Status` | 整体状态（参考终态判定） |
| `ExecutionSet[].ExitCode` | 退出码（0 = 正常） |
| `ExecutionSet[].Output` | 命令输出（stdout + stderr 合并；可能截断，看 `OutputTruncated`） |
| `ExecutionSet[].OutputTruncated` | 输出是否被截断的布尔位 |
| `ExecutionSet[].Duration` | 命令执行时长（秒） |
| `ExecutionSet[].StartTime` / `EndTime` | 执行起止时间（UTC） |
| `ExecutionSet[].CreatedTime` | 调用创建时间（北京时间） |
| `ExecutionSet[].Operator` | 操作者 Uin |

> 脚本透传服务端原始 Response，不做字段裁剪。

## 输出格式

### 集群列表（DescribeHPCClusters）

```markdown
## HPC 集群列表（{region}，共 {TotalCount} 个）

| ClusterId | Name | Status | Nodes | Scheduler | OS | VPC | CreateTime |
|---|---|---|---|---|---|---|---|
| `hpc-kazab9v2` | 金域迁移测试 | RUNNING | 6 | SLURM 23.11.7 | CentOS 7.9 | vpc-87y9syeb (10.10.0.0/22) | 2026-05-20 11:00:35 |
```

> 当 `TotalCount > limit`，提示用户用 `--offset/--limit` 翻页。

### 下发阶段（RunCommand）

```markdown
## 命令下发：{ClusterId}

**Region**：{region}
**InvocationId**：`{InvocationId}`  ← 下一步查询用
**RequestId**：{RequestId}

### 命令内容
```sh
{Command}
```

> 提示用户：如需查看执行结果，请运行
> `python3 scripts/describe_command_execution.py --cluster-id {ClusterId} --invocation-ids {InvocationId}`
> 或加 `--poll` 自动等到终态。
```

### 查询阶段（DescribeCommandExecution）

按 `ExecutionSet` 逐条渲染，每条一节：

```markdown
## 命令执行：{InvocationId}

**Region**：{region}
**集群**：{ClusterId}
**执行节点**：{NodeId}
**操作者**：{Operator}
**状态**：{Status}    **退出码**：{ExitCode}    **耗时**：{Duration}s
**创建时间**：{CreatedTime}
**起止**：{StartTime} ~ {EndTime}

### 命令
```sh
{Command}
```

### 输出（{OutputTruncated}）
```
{Output}
```
```

如果状态非终态（如 `RUNNING` / `PENDING`）且未启用 `--poll`，提示用户「命令仍在执行中，可加 `--poll` 自动等待，或稍后重试」。

`OutputTruncated=true` 时提醒用户：「输出被截断，建议改写命令为重定向到文件 + `cat 文件` 两步走」。

## 三段式工作流（指针）

云 API 三段式（`DescribeHPCClusters → RunCommand → DescribeCommandExecution`）已合并到本文顶部「端到端标准工作流」中作为通用骨架；当用户的诉求纯粹是"在某个集群上跑一条裸命令"时，把 Step A 的意图分类标记为"直接走云 API"，Step B 不进入 SLURM/tophpc 命令生成，直接把用户给的 shell 字符串送入 Step D 即可。其他步骤（确认协议、远程下发、轮询取回、按"输出格式"模板渲染）保持一致。

## 注意事项

1. 命令内容仅传**用户明确给定**的 shell 字符串，不要擅自加 `set -e`、`source ~/.bashrc` 等修改；如确有需要必须先与用户确认
2. 对涉及 `rm -rf`、覆盖系统文件、修改 `/etc`、`sudo` 等高危命令，下发前**必须**先回显完整命令并请用户显式确认（y/yes）
3. 如果命令含敏感信息（密钥、密码、token），提醒用户改用环境变量或文件方式注入
4. `--node-id` 不传时由服务端按集群默认策略调度；实测一般会落在 manager 节点（`role=1` 那台）
5. `Output` 字段服务端有大小限制，超长输出会被截断（看 `OutputTruncated`）；遇到截断改写为重定向到文件 + `cat 文件` 的两步
6. `RunCommand` 与 `DescribeCommandExecution` 是全局接口，**不受地域限制**；`InvocationId` 可以跨 region 查。`DescribeHPCClusters` 是地域接口，`--region` 传错会查不到集群。三个脚本统一走统一接入点 `omics.tencentcloudapi.com`，腾讯云会就近调度。
7. `ExecutionSet[].NodeId` 实测返回的是**CVM 实例 ID**（`ins-xxx`），不是 HPC 节点 ID（`node-xxx`）；如需对应 HPC 节点，请配合 `DescribeHPCNodes` 反查
8. `DescribeHPCClusters` 的过滤是**与**关系——多个 Filter 同时生效，单个 Filter 内部 `Values` 是**或**关系
9. 禁止透露任何敏感信息，包括密钥、密码、用户名、调用的接口名称等
