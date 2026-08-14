# Shell 命令最佳实践（所有阶段适用）

> 当模型将带 `{placeholder}` 的 shell 模板渲染为实际命令时，遵守以下规则
> 可避免引号转义、路径破坏、空输出等常见故障。

| 规则 | ❌ 错误做法 | ✅ 正确做法 | 原因 |
|------|------------|------------|------|
| **禁止 pipe + heredoc 组合** | `echo "$data" \| python3 << 'PYEOF'` | `echo "$data" \| python3 -c "..."` 或写临时 `.py` 文件后 `python3 /tmp/xxx.py` | heredoc 抢占 stdin，pipe 数据丢失，`json.load(sys.stdin)` 报 `JSONDecodeError` |
| 文件检测用 `test` 不用 `[ ]` | `[ -f "${DIR}/file" ]` | `test -f "${DIR}/file" && echo true \|\| echo false` | shell `[` 在嵌套 echo/command-sub 中比 `test` 更易触发引号转义 bug |
| 禁止 `\"` 内联转义 | `echo "$(python3 -c \"print('x')\")"` | 用 `python3 -c "..."` 且内部全用单引号 | `\"` 在 `"$(...)"` 中变成字面量反斜杠+引号 |
| 变量用 `${VAR}` 而非裸名 | `echo $DIR` | `echo "${DIR}"` | 路径含空格或特殊字符时不出错 |
| 长 JSON 用 python 构造 | 手拼 JSON 字符串 | `python3 -c "import json; print(json.dumps({...}))"` | 避免手动转义嵌套引号 |
| 多步骤检测合并为一次 `execute_command` | 分 3 次串行调用 | 一次命令内顺序执行，用 `echo '---TAG---'` 分隔输出 | 减少往返，加快执行 |

> **核心原则**：
> - **pipe 传入数据时用 `python3 -c "..."`**（不能用 heredoc，heredoc 会抢占 stdin）
> - **无 pipe 时用 heredoc**（代码更清晰，避免转义）
> - **复杂 Python 逻辑写临时 `.py` 文件**（register-agent.sh 已采用）

---

## Windows 环境注意事项

> Windows 用户通过 **Git Bash** 运行所有脚本（环境适配见 `references/win-adapter.md`）。适配完成后 GNU 工具、`/tmp/`、`~`、`/dev/null` 等均自动可用，无需额外处理。仅需注意：

| 注意事项 | 说明 |
|----------|------|
| **bash 显式调用** | 所有脚本调用统一用 `bash ${SKILL_DIR}/scripts/xxx.sh`，不依赖 shebang 直接执行 |
| **路径分隔符** | 传给脚本的路径用正斜杠 `/` 或 Git Bash 挂载路径 `/c/Users/...`，**禁止反斜杠 `\`** |
