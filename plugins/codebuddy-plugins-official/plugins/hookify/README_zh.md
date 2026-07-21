```markdown
# Hookify Plugin

通过分析对话模式或根据明确指令,轻松创建自定义 Hook 以防止不良行为。

## 概述

hookify plugin 让创建 Hook 变得简单,无需编辑复杂的 `hooks.json` 文件。相反,你可以创建轻量级的 Markdown 配置文件来定义需要监视的模式以及匹配时显示的消息。

**核心功能:**
- 🎯 自动分析对话以发现不良行为
- 📝 使用 YAML frontmatter 的简单 Markdown 配置文件
- 🔍 支持强大的正则表达式模式匹配
- 🚀 无需编码 - 只需描述行为即可
- 🔄 轻松启用/禁用,无需重启

## 快速开始

### 1. 创建第一个规则

```bash
/hookify 当我使用 rm -rf 命令时警告我
```

这会分析你的请求并创建 `.codebuddy/hookify.warn-rm.local.md` 文件。

### 2. 立即测试

**无需重启!** 规则在下次工具使用时立即生效。

让 CodeBuddy 运行一个应该触发规则的命令:
```
Run rm -rf /tmp/test
```

你应该会立即看到警告消息!

## 使用方法

### 主命令: /hookify

**带参数:**
```
/hookify 不要在 TypeScript 文件中使用 console.log
```

根据你的明确指令创建规则。

**不带参数:**
```
/hookify
```

分析最近的对话,找出你纠正过的或感到困扰的行为。

### 辅助命令

**列出所有规则:**
```
/hookify:list
```

**交互式配置规则:**
```
/hookify:configure
```

通过交互界面启用/禁用现有规则。

**获取帮助:**
```
/hookify:help
```

## 规则配置格式

### 简单规则 (单一模式)

`.codebuddy/hookify.dangerous-rm.local.md`:
```markdown
---
name: block-dangerous-rm
enabled: true
event: bash
pattern: rm\s+-rf
action: block
---

⚠️ **检测到危险的 rm 命令!**

此命令可能删除重要文件。请:
- 验证路径是否正确
- 考虑使用更安全的方法
- 确保你有备份
```

**action 字段:**
- `warn`: 显示警告但允许操作 (默认)
- `block`: 阻止操作执行 (PreToolUse) 或停止会话 (Stop 事件)

### 高级规则 (多条件)

`.codebuddy/hookify.sensitive-files.local.md`:
```markdown
---
name: warn-sensitive-files
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.env$|credentials|secrets
  - field: new_text
    operator: contains
    pattern: KEY
---

🔐 **检测到敏感文件编辑!**

确保凭据未硬编码,且文件在 .gitignore 中。
```

**所有条件必须匹配** 才能触发规则。

## 事件类型

- **`bash`**: Bash 工具命令触发
- **`file`**: Edit、Write、MultiEdit 工具触发
- **`stop`**: CodeBuddy 想要停止时触发 (用于完成检查)
- **`prompt`**: 用户提交 prompt 时触发
- **`all`**: 所有事件触发

## 模式语法

使用 Python 正则表达式语法:

| 模式 | 匹配 | 示例 |
|---------|---------|---------|
| `rm\s+-rf` | rm -rf | rm -rf /tmp |
| `console\.log\(` | console.log( | console.log("test") |
| `(eval\|exec)\(` | eval( 或 exec( | eval("code") |
| `\.env$` | 以 .env 结尾的文件 | .env, .env.local |
| `chmod\s+777` | chmod 777 | chmod 777 file.txt |

**提示:**
- 使用 `\s` 表示空白字符
- 转义特殊字符: `\.` 表示字面量点号
- 使用 `|` 表示 OR: `(foo|bar)`
- 使用 `.*` 匹配任何内容
- 为危险操作设置 `action: block`
- 为信息性警告设置 `action: warn` (或省略)

## 示例

### 示例 1: 阻止危险命令

```markdown
---
name: block-destructive-ops
enabled: true
event: bash
pattern: rm\s+-rf|dd\s+if=|mkfs|format
action: block
---

🛑 **检测到破坏性操作!**

此命令可能导致数据丢失。为安全起见操作已被阻止。
请验证确切路径并使用更安全的方法。
```

**此规则会阻止操作** - CodeBuddy 将不允许执行这些命令。

### 示例 2: 警告调试代码

```markdown
---
name: warn-debug-code
enabled: true
event: file
pattern: console\.log\(|debugger;|print\(
action: warn
---

🐛 **检测到调试代码**

记得在提交前删除调试语句。
```

**此规则警告但允许** - CodeBuddy 会看到消息但仍可继续。

### 示例 3: 停止前要求运行测试

```markdown
---
name: require-tests-run
enabled: false
event: stop
action: block
conditions:
  - field: transcript
    operator: not_contains
    pattern: npm test|pytest|cargo test
---

**未在记录中检测到测试!**

在停止之前,请运行测试以验证你的更改正常工作。
```

**如果会话记录中没有出现测试命令,这将阻止 CodeBuddy 停止。** 仅在需要严格强制时启用。

## 高级用法

### 多条件

同时检查多个字段:

```markdown
---
name: api-key-in-typescript
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.tsx?$
  - field: new_text
    operator: regex_match
    pattern: (API_KEY|SECRET|TOKEN)\s*=\s*["']
---

🔐 **TypeScript 中检测到硬编码凭据!**

使用环境变量代替硬编码值。
```

### 运算符参考

- `regex_match`: 模式必须匹配 (最常见)
- `contains`: 字符串必须包含模式
- `equals`: 精确字符串匹配
- `not_contains`: 字符串必须不包含模式
- `starts_with`: 字符串以模式开头
- `ends_with`: 字符串以模式结尾

### 字段参考

**对于 bash 事件:**
- `command`: bash 命令字符串

**对于 file 事件:**
- `file_path`: 正在编辑的文件路径
- `new_text`: 正在添加的新内容 (Edit, Write)
- `old_text`: 正在替换的旧内容 (仅 Edit)
- `content`: 文件内容 (仅 Write)

**对于 prompt 事件:**
- `user_prompt`: 用户提交的 prompt 文本

**对于 stop 事件:**
- 在会话状态上进行通用匹配

## 管理

### 启用/禁用规则

**临时禁用:**
编辑 `.local.md` 文件并设置 `enabled: false`

**重新启用:**
设置 `enabled: true`

**或使用交互工具:**
```
/hookify:configure
```

### 删除规则

只需删除 `.local.md` 文件:
```bash
rm .codebuddy/hookify.my-rule.local.md
```

### 查看所有规则

```
/hookify:list
```

## 安装

此插件是 CodeBuddy Code Marketplace 的一部分。安装 marketplace 后应自动发现。

**手动测试:**
```bash
cc --plugin-dir /path/to/hookify
```

## 系统要求

- Python 3.7+
- 无外部依赖 (仅使用标准库)

## 故障排除

**规则未触发:**
1. 检查规则文件是否存在于 `.codebuddy/` 目录中 (在项目根目录,而非插件目录)
2. 验证 frontmatter 中 `enabled: true`
3. 单独测试正则表达式模式
4. 规则应立即生效 - 无需重启
5. 尝试 `/hookify:list` 查看规则是否已加载

**导入错误:**
- 确保可用 Python 3: `python3 --version`
- 检查 hookify 插件是否已安装

**模式不匹配:**
- 测试正则表达式: `python3 -c "import re; print(re.search(r'pattern', 'text'))"`
- 在 YAML 中使用不带引号的模式以避免转义问题
- 从简单开始,然后增加复杂性

**Hook 似乎很慢:**
- 保持模式简单 (避免复杂的正则表达式)
- 使用特定的事件类型 (bash, file) 而不是 "all"
- 限制活动规则的数量

## 贡献

发现了有用的规则模式? 考虑通过 PR 分享示例文件!

## 未来增强

- 严重性级别 (错误/警告/信息区分)
- 规则模板库
- 交互式模式构建器
- Hook 测试工具
- JSON 格式支持 (除 markdown 外)

## 许可证

MIT License
```
