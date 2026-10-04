---
name: dcs-cloud
display_name: DCS Cloud生命科学研究智能平台
display_name_en: DCS Cloud Intelligent Platform for Life-Science Research
description: Operate DCS Cloud via the dcs CLI — projects, offline analysis tasks, WDL workflows, billing groups, and data files. Use when the user mentions DCS Cloud, projects, tasks, workflows, billing, or data files.
description_zh: 通过 dcs CLI 操作 DCS Cloud：项目、离线分析任务、WDL 工作流、计费组、数据文件。用户提到 华大、DCS、云平台、项目、任务、workflow、计费、数据文件时使用。
category: bioinformatics
version: 2.0.0
author: DCS Genpilot
---

# DCS Cloud（dcs CLI 直连模式）

本连接器只提供 **1 个 MCP 工具 `dcs_setup`**，负责下载 dcs CLI 二进制（SHA256 校验 + 自动更新）并用 PAT 完成登录。之后所有操作由 AI **直接在终端执行 dcs CLI 命令**完成，登录态持久化在 `~/.dcs/config.yaml`，与任何同用户 dcs 进程共享。

## 启动流程（每次会话开始时）

1. 调用 MCP 工具 `dcs_setup`（无参数）。
2. 成功后返回 `bin_path`、`version`、`logged_in`。
3. 之后一律在终端直接执行：`<bin_path> <子命令> --output json --no-history`

**示例（Windows PowerShell，路径含空格必须加引号）：**

```powershell
& "C:\Users\xx\.workbuddy\connectors\dcs-cloud\bin\dcs.exe" project ls --output json --no-history
```

**macOS / Linux：**

```bash
~/.workbuddy/connectors/dcs-cloud/bin/dcs-darwin-arm64 project ls --output json --no-history
```

## 鉴权说明

- 用户在 [https://www.dcs.cloud/](https://www.dcs.cloud/) 个人资料页创建 PAT（`dcs_pat_` 开头），填入 WorkBuddy 连接器表单。
- MCP Server 启动时通过 `DCS_PAT` 环境变量接收 PAT 并完成 `dcs auth login`。**PAT 不会出现在任何命令行参数中**，AI 不应、无需在对话中接触 PAT。
- `dcs_setup` 报 `DCS_PAT is not set`：提示用户去 WorkBuddy 表单填写 PAT 后重试。

## 硬性约定

- **所有命令必须带 `--output json --no-history`**（末尾追加），保证输出可解析且不污染历史。
- **任务/项目 ID 直接传字符串**，不要带尖括号 `<...>`。
- **路径**：数据浏览用 `/Files/...` 容器内绝对路径；本机路径含空格必须加引号。
- **批量操作**：多个 ID 用英文逗号 `,` 分隔作为一个参数传入。
- **危险操作**（`analysis cancel`、`workflow cancel/rm/start`、`terminal close`、`terminal exec`）：先执行对应 `info`/`ls` 命令确认状态，再向用户确认后执行。`terminal exec` 会在云端容器执行任意 shell 命令，首次使用或涉及删除/安装类命令时必须先向用户确认。
- 不要执行 `dcs config *`（登录态由 MCP Server 管理）、`dcs history *`。

## 命令速查

### 项目

| 意图 | 命令 |
|------|------|
| 列出项目 | `dcs project ls` |
| 当前项目 | `dcs project current` |
| 切换项目 | `dcs project switch --id PRJ-123` 或 `--name <精确名>` |

### 个性化分析任务（`dcs analysis`，非 WDL）

| 意图 | 命令 |
|------|------|
| 列出任务 | `dcs analysis ls` |
| 任务详情 | `dcs analysis info <task_id>` |
| 运行日志 | `dcs analysis log <task_id>` |
| 取消任务（批量逗号分隔） | `dcs analysis cancel <task_id>` |
| 投递离线任务 | `dcs analysis run -i '<cmd>' -l 'vf=4g,num_proc=1' --image 'stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0'` |

### WDL 工作流（`dcs workflow`）

| 意图 | 命令 |
|------|------|
| 列出工作流 | `dcs workflow ls [--name x] [--public] [--all]` |
| 工作流详情 | `dcs workflow info --name <name> [--version v]` |
| 输入参数规格 | `dcs workflow check_parameter --name <name>` |
| 多步规划 | `dcs workflow plan --names a,b,c` |
| 投递任务 | `dcs workflow run --name <name> [-i k=v ...] [-j file.json] [--table file] [--entity id] [--output_path p]` |
| 任务列表 | `dcs workflow tasks [筛选]`（见 `dcs workflow tasks --help`） |
| 任务详情/日志 | `dcs workflow info <task_id>` / `dcs workflow log <task_id> [步骤参数]` |
| 启动/取消/删除 | `dcs workflow start <id>` / `cancel <id>` / `rm <id>`（批量逗号分隔） |

> 注意区分：`dcs analysis` 是**个性化分析 shell 任务**；`dcs workflow` 是 **WDL 工作流任务**。两类任务 ID 不通用。

### 计费组

| 意图 | 命令 |
|------|------|
| 列出计费组 | `dcs billing ls [--name 关键词]` |

### 数据文件

| 意图 | 命令 |
|------|------|
| 浏览目录 | `dcs data ls [path] [--long] [--page 1] [--page-size 20]` |
| 下载到本机 | `dcs data download --type web --path /Files/... --target <本机目录>` |
| 本地文件上传 | `dcs data upload --type web --path a.txt,b.txt --target /Files/RawData`（逗号分隔多个文件） |
| 集群文件上传 | `dcs data upload --cluster-mode other --path /path/file1,/path/file2 --target /Files/RawData`（**须在容器内执行**，路径为集群路径） |
| 批量导入表上传 | `dcs data upload --cluster-mode batch_import --path /home/user/fastqImport.xlsx --target /Files/RawData`（**须在容器内执行**，csv/xlsx/xls） |
| 容器文件入 Files | `dcs data push /work/{user}/out.png /Files/Result/xxx.png` |

> `data upload` 复杂参数（含 sample_id 等）可用 JSON 传参：`--json @params.json`（跨 shell 通用）；PowerShell 内联 JSON 需外层双引号 + 转义内部双引号，建议优先用 `@file` 方式。`--target` 必须以 `/Files` 开头。

### 在线容器（OpenSandbox）

详见 [dcs-cloud-terminal.md](references/dcs-cloud-terminal.md)：`dcs terminal ls_resource/open/close/exec/read/create/edit/upload/download`。

## 常见错误码

| 码 | 含义 | 处理 |
|----|------|------|
| 83002 / 70102 / 41104 | 未登录 | 重新调用 `dcs_setup`；仍失败则提示用户在 WorkBuddy 表单重填 PAT |
| 83003 / 41102 | 未选项目 | 先 `dcs project switch` |
| 83011 | `user_id` 无效/非数值 | 重新 `dcs_setup`（内部重新登录） |
| 83012 | 容器会话失效 | 切换项目后先 `terminal close` 再 `open` |
| 命令卡住/超时 | 网络问题 | 缩小查询范围（分页）或稍后重试 |

## 禁止

- 不要在命令行使用 `--token` 传 PAT（会泄漏到进程列表）；登录已由 `dcs_setup` 完成，直接用即可。
- 不要让用户把 PAT 粘贴到对话中，应通过 WorkBuddy 连接器表单配置。
- 不要执行未在本手册或 references 中列出的 `dcs config` / `dcs history` 子命令。
- 危险命令（cancel/rm/close/exec）未经确认不得执行。
- CLI 错误输出可能包含敏感信息（如带凭证的完整命令回显）：**不要把原始错误输出原样回显给用户**，先摘录与故障相关的关键行；发现疑似 PAT/token 内容时只提示「输出包含敏感信息，已略去」。

## 开发者参考

以下文档供查阅 dcs CLI 细节，按需加载：

- [数据管理细节](references/dcs-data-manager.md)
- [在线容器 + 离线 analysis 细节](references/dcs-cloud-terminal.md)
- [Workflow 流程细节](references/dcs-wdl-manager.md)
