---
name: scnet-command-executor
description: 执行 SCNet 业务命令的规则，以及`scnet_remote_shell_execute`工具的规则。当需要执行 SCNet 计算命令、远程业务命令时必须先调用。
disable: true
---

# scnet-command-executor | SCNet 命令执行器

## 何时调用该技能

当任意技能要求执行 SCNet 计算业务命令时调用本技能。例如：

```bash
cd {work_dir} && /public/software/VersionHub/...
```

## 命令执行规则

计算过程中的前处理、后处理、slurm相关命令，以及目标文件与操作在**当前工作目录之外**的命令，都可以认为是计算业务命令，必须使用工具`scnet_remote_shell_execute`执行。

执行要求：

- 工具 `scnet_remote_shell_execute` 的命令必须保持 `command` 的业务语义不变。
- 工具 `scnet_remote_shell_execute` 返回的退出码、标准输出、标准错误均视为本次业务命令的执行结果。

## 执行约束

1. 若命令执行失败，必须将失败作为当前业务命令失败处理，并返回给调用方技能继续按其错误处理规则执行。
2. 如果工具`scnet_remote_shell_execute`不可用，立刻停止计算流程，告知用户业务工具不可用，请寻求客服帮助。
3. 如果 MCP 工具 `scnet_remote_shell_exec` 遇到 HTTP 400、网络错误、TaskGroup 相关错误或同等的远程执行失败，禁止自动重试。如果当前存在活动计划，先调用 `mark_task_error` 将会话状态更新为错误。随后立即停止后续执行并将控制权交还用户：清晰说明当前错误，询问用户希望如何处理，并询问是否需要再次尝试执行。
4. 禁止在顶层目录或超大目录上执行 `find` 等大范围递归搜索，尤其禁止通过 `scnet_remote_shell_execute` 进行此类搜索。禁止在 `/public/software` 下进行此类搜索，否则可能导致超时和资源过度消耗。如确需递归搜索，必须先根据已知软件名称、版本或当前工作目录，将搜索范围缩小到明确的多级子目录；只有在当前会话工作目录等小型、任务专属目录中，才允许进行大范围遍历。
