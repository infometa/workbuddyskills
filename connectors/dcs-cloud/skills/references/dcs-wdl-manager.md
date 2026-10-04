---
name: dcs-wdl-manager
description: 通过本机 dcs CLI 选型、查参、投递 workflow（WDL）任务并查看进度。仅在用户明确要做 WDL/流程分析投递、填参或查任务时使用。
version: 1.2.0
---

# Workflow 流程（dcs CLI）

> 执行前确认已完成总览 [SKILL.md](../SKILL.md) 中的 **auth login + project switch**。

用 **本机 `dcs` CLI** 操作项目内与公共库 WDL workflow。不要调用 Hermes/`dcs_wdl_*` agent tool；以 `dcs workflow` 命令组为准。

## 标准流程（必须按序）

```
workflow ls →（可选 workflow plan）→ workflow check_parameter →（用户确认/补参）→ workflow run → workflow task_info
```

- 用户已声明「引用 WDL：XXX」时可跳过 `ls`，直接 `plan` / `check_parameter`。
- 多步流程用 `plan` 校验名称并按序投递；**前一步成功后再做下一步**。
- Agent 读结构化结果时加 `--output json`。

## 命令对照

| 意图 | 命令 |
|------|------|
| 列项目内流程 | `dcs workflow ls -a [--page-size N] [-n 关键字] --output json` |
| 列公共库官方流程 | `dcs workflow ls -a -p --output json` |
| 流程详情 | `dcs workflow info -n <name> [-v <version>] [-p 仅公共库]` |
| 多步规划校验 | `dcs workflow plan -n A -n B`（或 `dcs workflow plan A B`）`--output json` |
| 查参数规格 | `dcs workflow check_parameter -n <name> [-v <version>] --output json` |
| 投递任务 | `dcs workflow run -n <name> …`（见下方入参方式） |
| 列已投递 WDL 任务 | `dcs workflow tasks -u <user> [-a] [-i <id>] [-n <wf>] [-s <status>] --output json` |
| 查任务进度/详情 | `dcs workflow task_info <task-id> --output json` |
| 查步骤日志 | `dcs workflow task_log <task-id> [-n <step>] [--stdout\|--stderr\|--script]` |
| 启动 / 取消 / 删除 | `dcs workflow start\|cancel\|rm <task-id[,…]>` |

## 查库逻辑（agent 须知）

- **`workflow plan` / `check_parameter` / `info`（默认）**：先查项目内流程，找不到再查公共库
- **`workflow info -p`**：只查公共库
- **`workflow ls -p`**：只列公共库；不带 `-p` 列项目内流程
- 选型时项目内 + 公共库两份 `ls` 结果合并去重
- 流程名不存在时：`plan` 可能 exit=0 但 step 显示 `No such wdl`（软失败）

## 1. List / Plan

1. `dcs workflow ls -a --output json` 与 `dcs workflow ls -a -p --output json` 合并去重，按需求选候选。
2. 复杂筛选先看 `dcs workflow ls --help`（`-n` / `-u` / `-t` / 分页等）。
3. 多步：`dcs workflow plan -n Step1 -n Step2 --output json` 校验存在并展示计划。

## 2. Check：查参

```bash
dcs workflow check_parameter -n <WDL名> [--output json]
```

- 输出 `wdl_parameter`：参数名、类型、必填/选填、默认值、说明。
- **禁止**跳过 check 直接猜参数名。
- 需要简介/标签等元信息时再用 `dcs workflow info -n <name>`。

## 3. Run：填参并投递

本 CLI **没有**独立 fill 命令。根据 check 结果，用下列三种入参方式之一调用 `dcs workflow run`（`-j` / `-i` / `--table` 三选一）。

- 必须用 **`dcs workflow run`**，不要用 `dcs analysis run` 代替
- 投递会计费：向用户展示参数摘要并获得明确确认后再投（即使用户已同意过同名流程，本次仍须再确认）
- 不确定参数：`dcs workflow run --describe`

### 方式 A：单样本 `-i`（推荐简单场景）

简单流程（如 `echo_hello`）可用；**必须带 `-e/--entity`**（如 `-e 10010`）。不要只写会缺 Mem 的复杂示例当唯一用法。

```bash
dcs workflow run -n echo_hello -e 10010 [--output json]
```

```bash
dcs workflow run -n <WDL名> -e 001 \
  -i paramA='/Files/a.fastq' \
  -i paramB='value' \
  [-o <相对输出目录>] \
  [--output json]
```

- `-e/--entity` 必填（如 `10010`、`001`）
- `-i` 可重复；值为 JSON 字面量时可被解析（如 `["/a","/b"]`、`true`）
- `Array[File]` / `Array[String]`：**不要**用逗号拼成普通字符串，应传 JSON 数组文本

### 方式 B：多样本 / 复杂表 `--table`

本机 CSV/TSV/XLSX，首列实体 ID，其余列为参数名：

```text
EntityID,fastq,sample_name
001,/Files/a.fq,s1
002,/Files/b.fq,s2
```

```bash
dcs workflow run -n <WDL名> --table /path/to/params.csv [-o <相对输出目录>]
```

数组单元格写 JSON 数组文本，并由 CSV 正确引号转义。

### 方式 C：`-j` 任务 JSON 文件（本机路径）

实体 ID → 参数 map：

```json
{
  "001": { "fastq": "/Files/a.fq", "sample_name": "s1" },
  "002": { "fastq": "/Files/b.fq", "sample_name": "s2" }
}
```

```bash
dcs workflow run -n <WDL名> -j /path/to/params.json [-o <相对输出目录>]
```

注意：`run` 的 `-j` 是**任务入参文件**；全局 `--json` / `DCS_JSON_PARAM` 用于命令级参数（含 `name`/`entity` 等），二者不同。

### `output_path`（`-o`）

- 相对 `/work/{current_user}/`；不传则结果在 `/work/{user}/[taskId]`
- 传入时实际为 `/work/{user}/{o}/[taskId]`
- 向用户汇报路径时用返回的 `task_id(s)` 替换 `[taskId]`

### 投递成功

返回 `task_ids` / `task_id`（多个以逗号分隔）；若落库延迟可能只见 `batch_code`，用 `dcs workflow tasks -i <batch_or_id>` 再查。

## 4. Task info：查进度

```bash
dcs workflow task_info <task-id> --output json
dcs workflow tasks -u <user_name> -a          # 列表；务必加 -u，否则易混入他人任务
dcs workflow task_log <task-id>               # 需要步骤 stdout/stderr 时
```

- WDL 任务用 **`dcs workflow task_info` / `workflow tasks`**，不要用 `dcs analysis info`（那是个性化离线 shell 任务）
- 投递后可轮询 `task_info`；失败时看 `task_log`，再决定是否只重投失败样本
- 多样本部分失败：对照各 `task_id`，**只重投失败实体**；禁止不查日志整表重投或盲目进入下一步

## 路径与数据

- 流程输入文件路径遵循 DCS 规范（如 `/Files/...` 或 `/work/{user}/...`）
- `--table` / `-j` 文件路径是**本机路径**（CLI 本地读文件），不是云容器沙箱路径
- 若参数文件需先放到项目存储，走数据管理能力后再在表/JSON 里引用 `/Files/...`

## 常见错误

| 现象 | 处理 |
|------|------|
| 请先 ls 查询 / 41102 | 未选项目或流程名错；先 `project switch`，再 `workflow ls` 确认名称 |
| 未找到公共库工作流（错版本） | 指定 `-v` 时优先报「未找到工作流版本」；用 `workflow ls` 查可用版本 |
| JWT / 未登录 | 重新 `dcs auth login` |
| 必填参数 / 参数非法 | 回到 `check_parameter`，按参数名与类型重填后再 run |

## 明确不做

- Hermes 的 `dcs_wdl_*` tool、Plan/哨兵、`offline_task_recall` 自动续跑承诺
- 用 `terminal exec` 或 `dcs analysis run` 代替 `workflow run` 投递 WDL
- 跳过 `check_parameter` 瞎填参数名
- 未获用户确认就投递（计费操作）
