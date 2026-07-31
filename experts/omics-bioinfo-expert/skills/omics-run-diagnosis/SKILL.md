---
name: omics-run-diagnosis
description: 组学平台任务运行错误诊断。通过 omics-platform-cli 认证，调用 JSON-RPC 接口查询任务日志，并结合错误知识库匹配根因与解决方案。触发关键词包括：任务失败、运行报错、排查错误、诊断任务、子任务失败、OOM、调度失败、镜像拉取失败、归档失败、数据预处理失败、运行慢。
---

# omics-run-diagnosis — 组学平台任务运行错误诊断

## 概述

本 Skill 通过 **omics-platform-cli 认证**，调用组学平台 `/omics/api/cgi` (JSON-RPC) 接口拉取任务日志，再结合内置的**错误知识库**（`references/troubleshooting-kb.md`），自动匹配错误根因并给出解决方案。

核心能力：
| 维度 | 说明 |
|------|------|
| 认证 | omics-platform-cli（`~/.omics-platform-cli/auth.json`），Uin 自动获取 |
| 接口 | `POST /omics/api/cgi` → `RunService.DescribeRunLogs` |
| 目标 | 诊断根因、给出解决方案 |
| 输出 | 错误分类 + 根因分析 + 修复建议 |
| 知识库 | troubleshooting-kb.md（11 类错误场景） |
| 适用场景 | 用户问"为什么失败""怎么解决""排查错误" |

## 认证与鉴权

本 Skill 依赖 **omics-platform-cli** 完成认证，无需手动配置密钥。

### 认证流程

```
1. 检查 omics-platform-cli 是否安装
2. 读取 ~/.omics-platform-cli/auth.json 中的 session_id
3. 调用 /userinfo 接口自动获取当前登录用户的 Uin
4. 使用 session_id + Uin 调用 RunService.DescribeRunLogs
```

### 前置依赖

```bash
# 安装 omics-platform-cli
curl -fsSL https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/raw/main/install.sh | bash

# 登录授权（首次使用）
omics login
```

### Uin 获取策略

| 方式 | 说明 |
|------|------|
| 自动获取（推荐） | 脚本调用 `/userinfo` 接口，从当前 session 自动获取 Uin |
| 手动指定 | 通过 `--run-uin` 参数覆盖，适用于诊断他人任务 |

> 💡 **关于 Uin**：认证时即可通过 `/userinfo` 接口获取当前登录用户的 Uin，无需用户手动提供。只有当用户需要诊断**他人**的任务时，才需要手动指定 `--run-uin`。

## 执行方式

使用 Skill 目录下的 Python 脚本，通过 omics-platform-cli 认证调用组学平台 JSON-RPC 接口：

```bash
# 单任务模式（Uin 自动获取）
python3 scripts/query_run_log.py \
  --run-uuid <UUID>

# 批次模式
python3 scripts/query_run_log.py \
  --run-group-id <GROUP_ID>

# 手动指定 Uin（诊断他人任务）
python3 scripts/query_run_log.py \
  --run-uuid <UUID> \
  --run-uin <UIN>

# 指定环境
python3 scripts/query_run_log.py \
  --run-uuid <UUID> \
  --env prod|dev
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--run-uuid` | 二选一 | — | 任务的 RunUuid（单任务模式） |
| `--run-group-id` | 二选一 | — | 任务批次的 RunGroupId（批次模式） |
| `--run-uin` | 否 | 自动获取 | 任务所属用户的 Uin（默认从 `/userinfo` 自动获取） |
| `--env` | 否 | `prod` | 环境：`prod`（生产）或 `dev`（测试） |

## 诊断工作流

### 端到端流程

```
用户提供 RunUuid / RunGroupId
  │
  ├─ Step 0：认证
  │   ├─ 检查 omics-platform-cli 安装状态
  │   ├─ 读取 ~/.omics-platform-cli/auth.json 中的 session_id
  │   ├─ 调用 /userinfo 自动获取当前用户 Uin
  │   └─ 如果认证失败 → 引导用户执行 omics login
  │
  ├─ Step 1：收集信息
  │   ├─ 调用 query_run_log.py 拉取日志（单任务 or 批次模式）
  │   ├─ 如果批次模式返回 RunGroupChildSummaryTip → 提示用户选择失败子任务 → 二次调用
  │   └─ 如果只返回 RunStatusTip / RunGroupStatusTip → 任务非失败状态，直接告知用户
  │
  ├─ Step 2：解析日志，提取错误信号
  │   ├─ 扫描 ErrorCallStderr / ErrorCallStdout / ErrorCallCommand
  │   ├─ 扫描 ErrorCallJobEvent（Pod 事件中的 Warning 类型）
  │   ├─ 扫描 DataStageLog（数据预处理/归档阶段错误）
  │   └─ 扫描 NFDriverLog / NFDriverStdout / NFExecutionTrace（NF 引擎专属）
  │
  ├─ Step 3：匹配知识库
  │   ├─ 将提取的错误信号与 troubleshooting-kb.md 中的模式进行匹配
  │   ├─ 按「症状 → 根因 → 解决方案」三段式输出
  │   └─ 如果无法匹配 → 输出原始错误信息 + 建议联系平台支持
  │
  └─ Step 4：输出诊断报告
      └─ 按统一模板输出（见下方「输出格式」）
```

### Step 1 详细：日志查询逻辑

本 Skill 通过 `scripts/query_run_log.py` 调用组学平台 JSON-RPC 接口 (`POST /omics/api/cgi`, method: `RunService.DescribeRunLogs`) 拉取日志，查询逻辑如下：

**环境配置**：

| 环境标识 | 名称 | Base URL |
|----------|------|----------|
| `prod` | 生产环境 | `https://omics.qq.com` |
| `dev` | 测试环境 | `https://genomics.qq.com` |

- 默认使用生产环境（`prod`）
- 通过 `--env` 参数切换环境

**认证与 Uin 获取**：

1. 读取 `~/.omics-platform-cli/auth.json` 中的 `session_id`
2. 调用 `/userinfo` 接口获取当前用户的 Uin
3. 将 Uin 作为 `RunUin` 参数传入 `RunService.DescribeRunLogs`
4. 如果用户手动指定了 `--run-uin`，则使用手动值（用于诊断他人任务）

**响应分支判别**（传 RunGroupId 时）：

| 响应特征 | 判定 | 处理方式 |
|---------|------|---------|
| 仅包含 `RunGroupStatusTip` | 批次成功 / 运行中 | 直接展示提示，告知用户任务未失败 |
| 包含 `RunGroupChildSummaryTip` | WDL 批次模式 | 列出错误子任务 Uuid，提示用户选择后二次调用 |
| 包含 NF 专属字段且无 `RunGroupChildSummaryTip` | NEXTFLOW 直返 | 按单任务模式处理，无需二次调用 |

### Step 2 详细：错误信号提取

从 API 返回的 `Logs` 数组中，按以下优先级提取错误信号：

| 优先级 | LogType | 提取内容 | 诊断用途 |
|--------|---------|----------|---------|
| P0 | `ErrorCallStderr` | 失败作业的 stderr 文本 | **最关键**：包含程序报错、Python traceback、exit code 等 |
| P0 | `ErrorCallJobEvent` | 失败作业的 Pod 事件 JSON | 检测 OOM、调度失败、镜像拉取失败等 |
| P1 | `ErrorCallStdout` | 失败作业的 stdout 文本 | 补充信息：程序运行到哪一步出错 |
| P1 | `ErrorCallCommand` | 失败的命令文本 | 判断命令行语法错误、参数错误 |
| P2 | `DataStageLog` | 数据预处理/归档日志 | 检测 COS 访问权限、文件不存在等 |
| P2 | `CallStderr` | 正常作业的 stderr | 有时包含 Warning 但不影响运行 |
| P3 | `CallJobEvent` | 正常作业的 Pod 事件 | 检测调度延迟等非致命问题 |
| NF | `NFDriverLog` | NF Driver 日志 | Nextflow 专属排错 |
| NF | `NFExecutionTrace` | NF 执行追踪 | NF 任务资源使用情况 |

**关键：优先看 Error* 类型的日志，它们直接对应失败作业。**

### Step 3 详细：知识库匹配策略

读取 `references/troubleshooting-kb.md`，按以下策略匹配：

1. **Pod 事件匹配**：解析 `ErrorCallJobEvent` 中的 `Reason` 和 `Message` 字段
   - `SystemOOM` / `CGroup OOM encountered` → 匹配「内存不足」
   - `FailedCreatePodSandBox` + `insufficient resource` → 匹配「可用区资源不足」
   - `ImagePullBackOff` / `ErrImagePull` → 匹配「镜像拉取失败」
   - `Unschedulable` → 匹配「任务资源不匹配」或「调度失败」

2. **stderr 文本匹配**：扫描 `ErrorCallStderr` 中的关键字符串
   - `OOM` / `out of memory` / `killed` → 匹配「内存不足」
   - `permission denied` / `access denied` → 匹配「COS 访问权限问题」
   - `No such file` / `not found` → 匹配「文件/目录不存在」
   - `command not found` / `exit code` → 匹配「作业命令行失败」

3. **DataStageLog 匹配**：扫描数据预处理/归档阶段日志
   - `coscli` 错误 / `Access denied` → 匹配「COS 访问权限问题」
   - `NoSuchKey` / `not exist` → 匹配「预处理文件不存在」
   - 归档阶段错误 → 匹配「归档失败」

4. **任务状态模式匹配**（当无详细日志时，根据用户描述的状态）：
   - "批次失败且没有子任务" → 匹配「批次初始化失败」
   - "子任务没有作业列表" → 匹配「数据预处理失败」
   - "作业全部成功但子任务失败" → 匹配「归档失败」
   - "批次完成但COS无结果" → 匹配「输出目录错误」

### Step 4 详细：输出格式

#### 诊断报告模板

```markdown
## 🔍 诊断报告：{RunUuid 或 RunGroupId}

**查询环境**：{命中的环境名称}
**查询时间**：{当前时间}

### 📊 任务概览
- **任务标识**：{RunUuid / RunGroupId}
- **引擎类型**：{WDL / NEXTFLOW / 未知}
- **任务状态**：{根据 RunStatusTip 或日志内容推断}

---

### ❌ 错误诊断

#### 错误 1：{错误分类标题}
- **严重程度**：🔴 致命 / 🟡 警告
- **错误类型**：{知识库中的错误编号，如 E01}
- **证据来源**：{LogType + 关键片段}

**根因分析**：
{基于知识库的根因描述}

**解决方案**：
{基于知识库的解决方案，按步骤列出}

---

#### 错误 2：{错误分类标题}
（同上格式）

---

### 📋 原始错误摘要

（仅列出关键错误日志的摘要，不超过 500 字，避免信息过载）

### 💡 建议的下一步操作

1. {最优先的修复步骤}
2. {次优先的修复步骤}
3. {如果以上无法解决，建议联系平台支持}
```

#### 批次模式输出模板（WDL）

```markdown
## 🔍 批次诊断报告：{RunGroupId}

**查询环境**：{命中的环境名称}

### 📊 批次概览
- **批次标识**：{RunGroupId}
- **引擎类型**：WDL
- **批次状态**：{RunGroupStatusTip 或 RunGroupChildSummaryTip 内容}

### ❌ 错误子任务列表

| 序号 | 子任务 Uuid | 状态 |
|------|------------|------|
| 1 | {uuid1} | 失败 |
| 2 | {uuid2} | 失败 |

> 💡 请提供您想诊断的子任务 Uuid，我将拉取其详细日志并生成诊断报告。您也可以说"全部诊断"，我会逐个分析（数量较多时建议分批）。

### 📥 批次输入（如有 RunGroupInput）
（解析展示，可能包含导致批次级错误的线索）
```

#### 无错误场景

如果日志显示任务并非失败状态（仅返回 `RunStatusTip` / `RunGroupStatusTip`），直接告知：

```markdown
## ✅ 任务状态正常

任务 {RunUuid / RunGroupId} 当前状态为「{状态}」，未检测到错误。

如果您遇到了其他问题，请描述具体现象，我可以帮您进一步排查。
```

## 补充说明

- 本 Skill 内置 `scripts/query_run_log.py` 脚本，独立完成日志查询与诊断，无需依赖其他 Skill
- 如果知识库无法覆盖遇到的错误，应回退到展示原始日志，并建议用户联系平台支持
- 如果用户仅需查看原始日志而不需要诊断，可直接展示 API 返回的日志内容

## LogType 速查

诊断时重点关注以下 LogType：

| LogType | 诊断用途 | 优先级 |
|---------|----------|--------|
| `ErrorCallStderr` | 失败作业 stderr，包含程序报错 | P0 |
| `ErrorCallJobEvent` | 失败作业 Pod 事件，检测 OOM/调度失败 | P0 |
| `ErrorCallStdout` | 失败作业 stdout，补充信息 | P1 |
| `ErrorCallCommand` | 失败命令，检测命令行错误 | P1 |
| `DataStageLog` | 数据预处理/归档日志 | P2 |
| `CallJobEvent` | 正常作业 Pod 事件 | P3 |
| `NFDriverLog` | NF Driver 日志 | NF |
| `NFExecutionTrace` | NF 执行追踪 | NF |

### Pod 事件 (JobEvent) 关键 Reason

| Reason | 含义 | 对应知识库 |
|--------|------|-----------|
| `SystemOOM` | 容器内存溢出 | E04 内存不足 |
| `FailedCreatePodSandBox` | Pod 沙箱创建失败 | E07 可用区资源不足 |
| `ImagePullBackOff` | 镜像拉取失败退避 | E06 镜像拉取失败 |
| `ErrImagePull` | 镜像拉取错误 | E06 镜像拉取失败 |
| `Unschedulable` | Pod 不可调度 | E05 或 E07 |
| `FailedScheduling` | 调度失败 | E05 或 E07 |

## 注意事项

1. `LogContent` 中的 JSON 字符串需要二次解析（它是字符串化的 JSON）
2. 诊断时**不要**把完整原始日志全部输出，只输出与错误相关的摘要（不超过 500 字）
3. 如果用户只提供了部分 UUID，提醒用户提供完整的 UUID
4. 用户必须提供 RunUuid 或 RunGroupId（至少一个），Uin 默认自动获取
5. WDL 批次模式只回 Uuid 列表，不会返回子任务的深度日志，想看详细日志必须二次调用
6. NF 引擎下传 RunGroupId 与传 RunUuid 等价，直接返回完整 Run 详情，无需二次调用
7. 如果知识库中无匹配项，展示原始错误信息并建议用户联系平台支持
8. 禁止透露任何敏感信息，包括 session_id、密码、用户名、调用的接口名称等
9. 如果认证失败（session 过期），引导用户执行 `omics login`
10. 诊断他人任务时需手动指定 `--run-uin`，否则默认使用当前登录用户的 Uin
