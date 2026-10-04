---
name: dcs-cloud-terminal
description: 通过本机 dcs CLI 操作云端在线容器（OpenSandbox）并投递离线任务。路径均为容器内路径。默认镜像 stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0。
version: 1.1.0
---

# 云端在线容器（dcs CLI）

> 执行前确认已完成总览 [SKILL.md](../SKILL.md) 中的 **auth login + project switch**。

用 **本机已安装的 `dcs` CLI** 操作 DCS Cloud 在线容器（OpenSandbox）与离线 analysis 任务。路径均为**容器内**绝对路径，不是本机路径。

**默认镜像**（在线 terminal 与离线 `analysis run` 统一）：

`stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0`

任务详情里可能显示映射名如 `ubuntu:24.04-python3.12`，传参以 registry 路径为准。不要用展示名、随意 tag 或纯数字 ID。

## 前置

1. `dcs auth login`（必须 CLI 登录，网页登录不算）
2. `dcs project switch --id P...`（不要写 `<P...>` 尖括号）
3. 登录时自动写 `user_id`；`copilot_base_url` 随 `base_url` 推导，一般无需手设
4. `terminal` 需要数值型 `user_id`；若报 `83011`，重新 `dcs auth login` 或 `dcs config set user_id <id>`

## 命令对照（核心）

| 意图 | 命令 |
|------|------|
| 列容器规格 | `dcs terminal ls_resource --output json` |
| 打开容器 | `dcs terminal open [--resource_id <id>] --output json` |
| 关闭容器 | `dcs terminal close [--force]` |
| 容器内执行 | `dcs terminal exec -c '<cmd>'` 或 `dcs terminal exec -- <cmd>` |
| 读文本文件 | `dcs terminal read -p <abs>` |
| 写/覆盖文件 | `dcs terminal create -p <abs> -c '...'`（省略 `-c` 则创建空文件） |
| 本机→容器上传 | `dcs terminal upload -p <容器路径> -f <本机文件>` |
| 容器→本机下载 | `dcs terminal download -p <容器路径> -t <本机路径>` |
| 局部编辑 | `dcs terminal edit -p <abs> --old '...' --new '...'` |
| 投递离线任务 | `dcs analysis run -i '<cmd>' -l 'vf=Ng,num_proc=M' --image '<registry>'` |

## 路径约定

- 工作目录：`/work/{user_name}`（默认 exec cwd）
- 软件安装：`/home/{user_name}/software`
- 一律用**容器内绝对路径**；解释器用 `python3`（不要用 `python`）

## 推荐流程

1. `dcs terminal ls_resource` →（可选）`dcs terminal open --resource_id <id>`
2. **open 后等 3–5 秒**再 `exec`；若报 503/83007，确认 `workspace_status=Running` 后重试
3. 短命令 / 装依赖：`dcs terminal exec`
4. 读写改文件：
   - 文本内容：`read` / `create -c` / `edit`（`edit` 的 `--old` 须与 `read` 内容精确匹配）
   - 本机文件进容器：`terminal upload`
   - 容器文件到本机（含二进制）：`terminal download`
5. 用户明确要「离线 / DCS 队列」时：`dcs analysis run`（`-l` / `--image` 必填）
6. 结束：`dcs terminal close`（重复 close 幂等；无本地会话时可 `--force` 通过 Copilot 关闭）

需要装软件时，先在默认在线容器里装好并验证，再投离线，避免「终端里能跑、离线镜像里缺包」。

切换项目后：先 `dcs terminal close` 再 `dcs terminal open`，否则 exec/read 报 83012。

## 脚本与图片结果取回

**`terminal read` 仅适合文本**；PNG/PDF 等二进制会损坏，不要用 read 取图。

推荐（按场景）：

```bash
# 方式 A：容器直接下载到本机（最简单）
dcs terminal download -p /work/{user_name}/output/xxx.png -t ./xxx.png

# 方式 B：先入 Files 再 data download
dcs data push /work/{user_name}/output/xxx.png /Files/Result/Notebook/plots/xxx.png
dcs data download --type web --path /Files/Result/Notebook/plots/xxx.png --target .
```

详见 [dcs-data-manager.md](dcs-data-manager.md)。

## 离线投递要点

- 命令：**`dcs analysis run`**（无 `-t s`）
- `-l` / `--image` **必填**；镜像默认 `stereonote_hpc/dcs_claw_ubuntu_24_04:v1.0`
- `-l` 必须同时含 `vf` 与 `num_proc`，且匹配当前片区机型：
  - BGI-Center（st）：`vf=4g,num_proc=1`
  - DCS-North2（ve）：无 1c 4g，用当地机型如 `vf=8g,num_proc=4`
- 单条命令：`-i`；本机批处理：`-p <本机文件>`（每行一条命令）
- 容器内调试通过后，再在本机构 `-i` 投递（同一默认镜像）
- 投递前可 `terminal exec -c "python3 -c 'import …'"` 校验依赖
- `task consume`：本人任务可用；他人任务会「无权限」
- `task start`：调用的是 resume/重投；本人失败任务仍可能「重投失败」，先勿写成稳定可用流程

## 明确不做

- Streamlit / Dash / notebook 网关等需 Web 网关的能力（本 skill 只覆盖 CLI）
- 不用 `task run -t s`（实际无此 flag）
