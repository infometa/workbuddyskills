---
description: "查看插件内置的 Skill 列表与各自职责"
argument-hint: "[skill-name]"
---

# /godot:skill

列出当前插件按 [4.23.md](../docs/需求文档/4.23.md) 重构后的 Skill 与 MCP 工具
分工。所有 Skill 随插件自动加载，无需手动部署。

## 当前 Skill 列表（4.23 重构版）

| Skill | 职责 | 触发关键词 |
|-------|------|-----------|
| [godot-dev](../skills/godot-dev/SKILL.md)       | 统一开发入口；执行环境检测 + 三场景分流（make/new/modify）| 做游戏 / 改场景 / 加玩法 / make a game |
| [godot-deploy](../skills/godot-deploy/SKILL.md) | 自执行 5 步部署：Node 检查、Server 构建、Godot 编辑器下载、9080 探测 | 部署 / 一键部署 / setup mcp / 连不上 |
| [godot-new](../skills/godot-new/SKILL.md)       | 新建另一个游戏项目：推断模板、复制模板+addons、写 `active-game.json`  | 再做一个 / 新游戏 / new game |
| [godot-debug](../skills/godot-debug/SKILL.md)   | 调用 3 个 debug MCP 单元查询工具，展示错误报告 | 报错 / debug / 修 bug |

## 当前 MCP 工具列表（4.23 重构版）

> 4.23.md：**MCP 只暴露对 Godot 编辑器的单元操作。**
> 旧的 `godot_deploy` / `godot_dev_router` / `init_godot_project` /
> `operate_node` 等已从 MCP 中**移除**——它们的逻辑回归到了 Skill。

| 工具 | 类别 | 说明 |
|------|------|------|
| `build_godot_scene` | 场景修改门面 | 接收完整声明式场景树，server 端拆解为 create_node / update_node_property / create_script / save_scene 等单元命令逐一执行 |
| `get_debug_errors`  | 单元查询 | 一次性扫描全项目的编译错误 + 编辑器日志错误 |
| `get_script_errors` | 单元查询 | 单个脚本的详细错误 + 完整内容 |
| `get_editor_output` | 单元查询 | Godot 编辑器 Output 面板原始日志 |

外加若干 read-only 资源（场景列表 / 脚本列表 / 项目结构 / 编辑器状态等）。

## 工作区目录契约（4.23.md 强制约定）

```
${WORKSPACE}/
├── godot-editor/        ← 由 godot-deploy 下载
├── active-game.json     ← 由 godot-new 写入
├── game1/  game2/  ...  ← 由 godot-new 创建
```

详见 [godot-dev/SKILL.md](../skills/godot-dev/SKILL.md#工作区目录契约4-23-md-强制约定所有子-skill-必须遵守)。
所有子 Skill **必须**遵守此结构。

## 用法

```
/godot:skill              # 列出
/godot:skill godot-dev    # 直接打开某 Skill 的 SKILL.md
```

## 与三大场景的对应关系（参见 [4.23.md](../docs/需求文档/4.23.md)）

| 场景 | 触发条件 | 涉及 Skill | 调用的 MCP 工具 |
|------|---------|-----------|----------------|
| 1. 空环境 + 做游戏 | 工作区无 `project.godot` 且用户想做游戏 | godot-dev → godot-deploy → godot-new | （无；建项目本身不调 MCP） |
| 2. 已部署 + 新游戏 | 已有 `active-game.json` 但用户说「再做一个」 | godot-dev → godot-new | （无） |
| 3. 修改游戏内容 | 已有 `active-game.json` 且用户说改/加/删 | godot-dev | `build_godot_scene` 或直接文件 Write/Edit |
