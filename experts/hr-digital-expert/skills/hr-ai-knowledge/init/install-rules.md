# 安装 Rules

> **触发时机**：
> - **主动安装（唯一执行入口）**：用户运行 `/enable-hr-ai-knowledge` 命令时，按本流程覆盖拷贝 Rules 到当前工作目录。
> - **被动检测（不静默写盘）**：使用 skill 时若检测到当前工作目录未安装 Rules，**不自动写入用户目录**，仅作为**可选建议**提示用户运行 `/enable-hr-ai-knowledge`（并说明"不装也能用"）；用户同意后才走本流程。

## 核心原则

**Rules 安装到当前工作目录**（`{当前工作目录}/.codebuddy/rules/` + `{当前工作目录}/.workbuddy/rules/`）：

- 用户在哪个工作目录启用了本插件，就在哪个工作目录生效自动加载——**用户有选择权**，不会污染其他项目。
- HR 知识检索没有落地在工作目录的本地文件标志物，检索完全依赖远端 hr-ai-knowledge MCP，因此 Rules 仅安装到当前工作目录一处，不存在按本地目录位置区分安装路径的分支。

## 安装目标路径

| 触发时机 | Rules 安装路径 |
|---|---|
| **`/enable-hr-ai-knowledge`（或用户同意后）** | `{当前工作目录}/.codebuddy/rules/use-hr-ai-knowledge.mdc` + `{当前工作目录}/.workbuddy/rules/use-hr-ai-knowledge.mdc` |

## 目的

将 `use-hr-ai-knowledge.mdc` 安装到目标目录的 `.codebuddy/rules/` 和 `.workbuddy/rules/` 下，使 CodeBuddy / WorkBuddy 自动应用此规则，无需手动激活技能即可在 HR 意图出现时**主动**加载技能并先做连接预检。

## 涉及文件

| 文件 | 说明 |
|------|------|
| `init/rules/use-hr-ai-knowledge.mdc` | 插件中的 rule 模板（源） |
| `{目标目录}/.codebuddy/rules/use-hr-ai-knowledge.mdc` | 安装到 `.codebuddy` 目录的 rule（目标 1） |
| `{目标目录}/.workbuddy/rules/use-hr-ai-knowledge.mdc` | 安装到 `.workbuddy` 目录的 rule（目标 2） |

## 执行步骤

### 1. 确定安装目标目录

目标目录固定为**当前工作目录**（IDE 打开的工作区根目录，绝对路径）。

### 2. 覆盖拷贝 Rule 文件

将 `use-hr-ai-knowledge.mdc` **原样覆盖拷贝**到目标目录的 `.codebuddy/rules/` 和 `.workbuddy/rules/` 下：

```bash
mkdir -p {目标目录}/.codebuddy/rules
cp "$CODEBUDDY_PLUGIN_ROOT/skills/hr-ai-knowledge/init/rules/use-hr-ai-knowledge.mdc" {目标目录}/.codebuddy/rules/use-hr-ai-knowledge.mdc

mkdir -p {目标目录}/.workbuddy/rules
cp "$CODEBUDDY_PLUGIN_ROOT/skills/hr-ai-knowledge/init/rules/use-hr-ai-knowledge.mdc" {目标目录}/.workbuddy/rules/use-hr-ai-knowledge.mdc
```

> 使用 `execute_command` 执行上述命令。`$CODEBUDDY_PLUGIN_ROOT` 由 CodeBuddy 运行时注入，指向当前插件根目录。
>
> **Windows（PowerShell）等价命令：**
> ```powershell
> New-Item -ItemType Directory -Force -Path "{目标目录}\.codebuddy\rules" | Out-Null
> Copy-Item "$env:CODEBUDDY_PLUGIN_ROOT\skills\hr-ai-knowledge\init\rules\use-hr-ai-knowledge.mdc" "{目标目录}\.codebuddy\rules\use-hr-ai-knowledge.mdc" -Force
> New-Item -ItemType Directory -Force -Path "{目标目录}\.workbuddy\rules" | Out-Null
> Copy-Item "$env:CODEBUDDY_PLUGIN_ROOT\skills\hr-ai-knowledge\init\rules\use-hr-ai-knowledge.mdc" "{目标目录}\.workbuddy\rules\use-hr-ai-knowledge.mdc" -Force
> ```
>
> **重要**：仅执行 `cp` / `Copy-Item` 文件覆盖拷贝，**禁止读取、编辑或修改** rule 文件的任何内容。无论目标文件是否已存在，均直接用源文件完整覆盖。两个目标目录均需安装。

### 3. 用户通知

🤝 告知用户：

```
已完成 Rule 安装：
use-hr-ai-knowledge 规则已安装到：
  - {目标目录}/.codebuddy/rules/use-hr-ai-knowledge.mdc
  - {目标目录}/.workbuddy/rules/use-hr-ai-knowledge.mdc
CodeBuddy / WorkBuddy 将自动应用此规则：HR / 知识检索意图出现时主动加载技能并先做 hr-ai-knowledge 连接预检。
```

## Rule 内容说明

安装的 `use-hr-ai-knowledge.mdc` 为 CodeBuddy 的自定义指令（Custom Directive），配置为 `alwaysApply: true`，确保每次对话都生效：

| 字段 | 值 | 说明 |
|------|-----|------|
| `alwaysApply` | `true` | 所有会话自动加载，无需手动调用 |
| `enabled` | `true` | 默认启用 |
| 描述 | 使用 hr-ai-knowledge 技能 | HR 触发词出现时主动调用 `use_skill` 并先做连接预检 |

## Rules 版本检测

源文件 frontmatter 含 `version: <N>` 字段。`use_skill("hr-ai-knowledge")` 加载后**应执行版本检测**：

1. 读取目标目录已安装的 `use-hr-ai-knowledge.mdc`（如存在）
2. 比对其 `version` 字段与源文件 `version`：
   - 缺失 `version` 字段 → 视为旧版
   - 已安装版本 < 源版本 → 🤝 提示用户："检测到 Rules 版本过旧（v{已装}→v{源}），建议重装以获得新行为约束"，征得同意后执行覆盖拷贝
   - 已安装版本 >= 源版本 → 无需重装

| 当前源版本 | 关键变更 |
|---|---|
| `version: 1`（2026-07-23） | 初始版本：强制 `use_skill` + 连接预检前置，禁止"先执行后提醒" |

## 注意事项

- 使用 skill 时会检查当前工作目录的 Rules 是否已安装；未安装时**仅作为可选建议提示**用户运行 `/enable-hr-ai-knowledge`，**不静默写盘**
- 已安装但版本过旧时，🤝 提示用户重装（征得同意后覆盖拷贝）
- 实际执行覆盖拷贝的入口只有：用户运行 `/enable-hr-ai-knowledge` 命令，或用户明确同意重装
- **跨平台支持**：所有系统均可执行（macOS / Linux / Windows）
