---
name: safe-file-operations
description: "防止误删文件的安全操作规范。当涉及文件删除、批量移动、rm -rf、rd /s /q 等危险操作时使用此 Skill，避免灾难性误删事故。"
version: 1.0.0
---

# 🚨 安全文件操作规范（血泪教训版）

## 事故回顾

2026年4月19日，在 CodeBuddyPlugin 项目中，为了清理 `plugin/out/` 编译输出目录，
执行了 `rd /s /q` 命令，但由于 **PowerShell 与 cmd 语法混淆**，命令被错误解析，
导致 **整个项目目录被递归删除**，包括：

- `.git/` — 版本历史全部丢失
- `plugin/src/` — 所有 TypeScript 源码
- `server/` — 整个后端代码
- `package.json`、`tsconfig.json` — 项目配置
- `node_modules/` — 依赖
- `build.bat`、`install.bat` 等脚本
- `plugin/resources/icon.svg` — 刚刚精心制作的自定义图标

**整个项目从有到无，不可逆转。**

---

## 🔴 绝对禁止（NEVER DO）

### 1. 禁止使用 `rd /s /q`、`rm -rf`、`Remove-Item -Recurse -Force` 清理目录
- **永远不要**用这些命令来清理编译输出、临时文件
- 即使目标路径看起来正确，Shell 语法差异可能导致灾难
- PowerShell 中 `rd` 是 `Remove-Item` 的别名，行为与 cmd 的 `rd` **不完全相同**

### 2. 禁止在项目根目录附近执行任何递归删除命令
- 哪怕目标是子目录，一个路径解析错误就会删掉整个项目
- 尤其是包含空格、特殊字符、或使用变量拼接路径时

### 3. 禁止先删后建的文件操作模式
- 不要 `delete` + `write`，直接 `write_to_file` 覆盖即可
- `write_to_file` 本身就是覆盖语义，不需要先删除

---

## 🟢 正确做法（ALWAYS DO）

### 清理编译输出
```
# 正确：使用专用工具，不用终端命令
- 用 IDE 的 clean 命令
- 或手动删除 out/ 下的 .js 文件（不要删 out/ 目录本身）
- 如果必须用命令，先 `dir` / `ls` 确认目标内容
```

### 如果确实需要删除目录
1. **先 `ls` / `dir` 列出内容**，确认是预期的目标
2. **只删除文件，不删除目录结构**（用 `del /q out\*.js` 而非 `rd /s /q out`）
3. **使用 IDE 工具** (`delete_file`) 逐个删除，而非批量终端命令
4. **绝不在包含 .git 的目录层级使用递归删除**

### 文件修改
- 修改文件 → `replace_in_file`（精确替换）
- 重写文件 → `write_to_file`（自动覆盖）
- 新建文件 → `write_to_file`
- 删除文件 → `delete_file`（仅限确实要移除的文件）

---

## ⚠️ Shell 陷阱提醒

| 场景 | 危险 | 安全替代 |
|------|------|----------|
| 清理 out/ | `rd /s /q out` | `del /q out\*.js` 或 IDE 工具 |
| 清理 node_modules | `rd /s /q node_modules` | `npm ci`（会自动清理重装）|
| PowerShell 中用 cmd 语法 | 命令被错误解析 | 确认当前 Shell 类型再执行 |
| 路径含空格 | 未加引号导致截断 | 始终用引号包裹路径 |
| 变量拼接路径 | 变量为空则删根目录 | 先 echo 路径确认 |

---

## 🧠 核心原则

> **对破坏性操作保持极度偏执。**
> 
> 宁可多花 10 秒确认，也不要花 10 小时恢复。
> 
> 如果一个操作可能删除用户代码，就假设它**一定会**出错。
> 
> **能用 IDE 工具完成的事，绝不用终端命令。**

---

## 检查清单（执行危险操作前必须过一遍）

- [ ] 我确认了当前 Shell 是 PowerShell 还是 cmd？
- [ ] 我确认了目标路径是正确的（不是父目录）？
- [ ] 这个操作如果出错，最坏后果是什么？
- [ ] 有没有更安全的替代方案（IDE 工具）？
- [ ] 项目是否有 git 提交/远程备份可以恢复？
- [ ] 我是否可以用 `replace_in_file` 或 `write_to_file` 代替终端操作？
