# 阶段六：输出分析报告（详细步骤）

报告使用中文，保存为 html 格式，文件名 `crash_report_TIME.html`，保存在 vmcore 所在目录。

## 🔴 步骤 6.0-pre：确认 TIME 变量

TIME 变量已在**阶段一**获取（`date '+%Y%m%d_%H%M'`），此处直接复用。

**🚫 禁止重新获取 TIME，必须使用阶段一的值。**

TIME 值**全程复用**：`crash_cmd_log_TIME.jsonl`、`crash_report_TIME.md`、`crash_report_TIME.html`。

## 🔴🔴🔴 报告生成方式（强制使用脚本，禁止直接输出 HTML）

**必须使用 [`crash_report_generator.py`](../scripts/crash_report_generator.py) 脚本生成。**

**🔴 绝对禁止：**
- 🚫 使用 `write_to_file` 直接写入 HTML 内容
- 🚫 在任何工具调用中直接输出 `<!DOCTYPE html>` 或 `<html` 开头的内容
- 🚫 绕过脚本自行设计 CSS 样式、HTML 布局

**✅ 合法方式：** 命令日志自动记录 → 撰写 Markdown → 写入 `.md` → 调用脚本生成 `.html`

## 步骤 6.0：命令日志（MCP 自动完成）

创建会话时通过 `cmd_log_path` 参数指定路径为 `<vmcore_dir>/crash_cmd_log_${TIME}.jsonl`，MCP 服务端自动记录所有命令。

- 🔴 创建会话时必须传入 `cmd_log_path`，不要使用默认的 `cmd_log.jsonl`
- 如需确认日志完整性，调用 `export_command_log`
- **回退方案**（MCP 不支持自动日志时）：
  ```bash
  python3 <skill_dir>/scripts/crash_report_generator.py --log-cmd <vmcore_dir>/crash_cmd_log_${TIME}.jsonl --cmd "<命令>" --cmd-output "<输出>"
  ```

## 步骤 6.1：前置自检

| 检查项 | 通过标准 |
|--------|---------|
| 是否使用 `crash_report_generator.py` 脚本生成？ | 必须"是" |
| 下一步是否撰写 Markdown？ | 必须"是" |
| 是否打算 `write_to_file` 直接写 HTML？ | 必须"否" |
| `crash_cmd_log_TIME.jsonl` 是否已由 MCP 自动生成？ | 必须"是" |

## 步骤 6.2：撰写 Markdown 报告

使用 `@cmd[]` 引用替代嵌入命令输出：

```markdown
### 3.1 基线收集
通过 `analyze_crash` 创建调试会话并收集基线诊断信息。
@cmd[sys]
从 `sys` 输出确认：256 核 KVM 虚拟机，1TB 内存...
@cmd[bt]
Panic CPU#172 当前正在 softirq 上下文处理网络包...
```

格式详情可查看：`python3 <skill_dir>/scripts/crash_report_generator.py --format-help`

## 步骤 6.3：写入 Markdown 文件

🔴 TIME 必须是**阶段一获取的值**，禁止重新获取。文件名必须为 `crash_report_TIME.md`。

## 步骤 6.4：调用脚本生成 HTML

```bash
python3 <skill_dir>/scripts/crash_report_generator.py -i <vmcore_dir>/crash_report_${TIME}.md -l <vmcore_dir>/crash_cmd_log_${TIME}.jsonl -o <vmcore_dir>/crash_report_${TIME}.html
```

## 步骤 6.5：后置验证

1. 确认脚本输出 `✅ 报告已生成: <path>`
2. 检查命令引用填充情况（"已填充 N, 未找到 M"中 M 尽可能为 0）
3. 有未找到的引用则检查日志
4. 脚本报错则修正 Markdown 后重新执行 6.3-6.4

## Markdown 报告扩展语法

**元数据块**（报告开头）：
```markdown
::: meta
report_time: 2026-03-19 17:22
vmcore_id: 16330271/ins-dehdympf
tool: crash + AiCrasher MCP
:::
```

**命令引用**：
- `@cmd[sys]` — 引用完整输出
- `@cmd[bt -a]{lines=50}` — 引用前 50 行
- `@cmd[]` 必须独占一行

**特殊块**：
- `::: alert{level=warning,title=标题}` ... `:::` — 提示框
- `::: highlight` ... `:::` — 高亮块
- `::: summary-box` ... `:::` — 摘要框
- `::: causal-chain` ... `:::` — 因果链

## 报告内容结构

1. **基本信息** — 系统环境（含 hypervisor）、内核版本、发行版、运行时长、Panic 时间和类型
2. **问题摘要** — 分析现象和结论简短摘要
3. **分析过程** — 关键分析步骤和详细推理逻辑（含命令输入输出、堆栈/反汇编/源码、变量提取过程）
4. **根因分析** — 根因结论（必须有证据）、完整因果链、排除的其他可能性
5. **建议与修复** — 社区修复 commit、官方知识库匹配、规避方案、进一步排查方向
