---
name: godot-debug
description: >
  仅当用户明确报告 Godot 项目**已经出错**（报错 / 崩溃 / 编译失败 /
  脚本错误 / fix this error / 帮我看下这个 bug），或 build_godot_scene
  执行后返回了错误日志时激活。调用 get_debug_errors / get_script_errors /
  get_editor_output 三个 MCP 单元查询工具并美化呈现。
  用户在做新内容开发、部署、新建项目时**不要**激活本 Skill。
---

# Godot Debug 循环

> 严格遵循 [docs/需求文档/4.23.md](../../docs/需求文档/4.23.md)：
> 错误信息的扫描、行号定位、上下文提取属于「对 Godot 编辑器的单元查询」，
> 在 MCP 内部以**单元工具**形式实现；本 Skill 只做**调用 + 美化展示 + 引导**。

---

## 工作区目录契约（4.23.md 强制约定）

本 Skill 不创建任何文件，但所有「`script_path` 在哪个项目里」的判断都基于
工作区契约（详见 [godot-dev/SKILL.md](../godot-dev/SKILL.md#工作区目录契约4-23-md-强制约定所有子-skill-必须遵守)）：

```
${WORKSPACE}/
├── godot-editor/
├── active-game.json     ← 读这个文件取 gameDir，res:// 即指向该 gameDir
├── game1/  game2/  ...
```

调 `get_script_errors` 等工具时，`project` 参数（如使用）必须对应
`active-game.json` 里的 `projectName`；`script_path` 始终用 `res://` 形式
（指向 `${gameDir}/...`），**不要**写绝对路径，**不要**跨 game 目录读写。

---

## 唯一允许调用的三个 MCP 工具

| 工具 | 用途 | 何时调 |
|------|------|--------|
| `get_debug_errors` | 一次性扫描全项目，返回所有 GDScript 编译错误 + 编辑器日志中的错误 | **每次激活的第一步** |
| `get_script_errors` | 单个脚本的详细错误（行号、列号、代码片段、上下文、修复建议、完整脚本） | 拿到 `get_debug_errors` 结果后，对每个有问题的脚本各调一次 |
| `get_editor_output` | 读取 Godot 编辑器 Output 面板的原始日志（错误/警告/print 输出） | 仅当编译没问题但运行时崩溃，需要看运行时栈时调用 |

调用约定：

```
get_debug_errors({
  include_log_errors?: boolean,   // 默认 true
  directory?:          string,    // 默认 "res://"
  exclude_addons?:     boolean,   // 默认 true
  project?:            string     // 多项目场景下指定
})

get_script_errors({
  script_path:        string,     // 必填，例如 "res://scripts/player.gd"
  include_warnings?:  boolean,    // 默认 true
  project?:           string
})

get_editor_output({
  lines?:   number,                       // 1-1000，默认 100
  filter?:  "all" | "errors" | "warnings",// 默认 "all"
  project?: string
})
```

---

## 行为约束（只做这四件事）

1. **第一步永远是** `get_debug_errors()`，把返回文本原样展示给用户
2. 如果有错误，**对每个出错脚本**调一次 `get_script_errors(script_path=...)`，
   展示该脚本的详细报告（含 suggestion 和完整脚本内容）
3. 如果错误信息提示是运行时崩溃 / 找不到节点 / null instance 等动态错误，
   再补一次 `get_editor_output(filter="errors", lines=200)` 抓栈
4. 修复代码本身**不归本 Skill 管**：把详细的错误位置、suggestion、完整脚本
   内容展示给上层 Agent / 用户去改 —— 改完后用户重新触发本 Skill 即可看
   是否通过。代码修改本身遵循 4.23.md 场景 3 的分工：
   - 节点附着的脚本 → 用 `build_godot_scene` 整树重构（godot-dev）
   - 独立 GDScript / autoload → 在 `${active-game.json}.gameDir/scripts/...`
     里直接 Write/Edit 文件（godot-dev）

---

## 严禁行为

- ❌ **不要**自己用 Read/Edit 工具去读写 `.gd` 脚本来「分析错误」——所有定位与
  上下文提取都已由 `get_script_errors` 在 server 端完成
- ❌ **不要**调用任何不在上面表里的 MCP 工具（旧的 `validate_all_scripts` /
  `get_debug_output` / `start_debug_monitor` 等已不存在；新的 `godot_deploy`
  / `godot_dev_router` 也已被移除）
- ❌ **不要**做「自动改代码 → 自动 run_project → 自动再 debug」的循环。
  本 Skill 不调 `run_project`，也不写代码——它只产出诊断报告，循环由用户
  / 上层 Agent 显式驱动
- ❌ **不要**自己跑 shell 命令查日志文件，`get_editor_output` 已经处理好

---

## MCP 连接异常时的处理

调用任何上述工具时收到 **「工具不存在 / 未注册 / connection refused /
ECONNREFUSED」**：

→ 立刻让位给 [godot-deploy](../godot-deploy/SKILL.md) Skill 完成连接修复
（**不要**自己去查端口、改配置、跑 npm）。

---

## 输出格式

直接原样转发 MCP 工具返回的报告文本，**不要复述、不要总结、不要省略**。
报告里 `── Error N ──` 的分块、行号、suggestion、完整脚本块都要保留。

末尾追加一句简短引导，例如：
> 请按上面 suggestion 修改对应脚本后，再让我「检查一次错误」。
