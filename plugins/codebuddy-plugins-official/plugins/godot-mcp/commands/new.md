---
description: "新建一个 Godot 游戏项目（推断模板 → 复制模板 → 注入 addons → 写 active-game.json）"
argument-hint: "[project-name] [template]"
---

# /godot:new

显式触发 [godot-new](../skills/godot-new/SKILL.md) Skill。

> 4.23.md 场景 2：**已有部署环境时仅新建游戏**。
> 模板由 Skill 自动推断，推不出就用 `empty`；项目名同理，默认 `my-game`。

## 参数

- `project-name`（可选）：项目目录名，默认按用户原话推断 / `my-game`
- `template`（可选）：`default` | `2d-platformer` | `3d-fps` | `empty`，
  默认按用户原话推断 / `empty`

## 行为

把参数转成提示交给 `godot-new` Skill：

1. 模板推断（用户显式 > 关键词推断 > `empty`）
2. 复制 [templates/<template>/](../templates/) → `${WORKSPACE}/<projectName>`
3. 注入 [addons/godot_mcp/](../addons/godot_mcp/) 到新项目
4. 创建标准目录骨架（assets / data / scenes / scripts）
5. **覆盖**写入 `${WORKSPACE}/active-game.json`，把 `gameDir` 切到新项目
6. 写 `.vscode/settings.json` 配置 godot-tools LSP 端口
7. 引导用户在 Godot 编辑器手动打开新项目并启用 GodotMCP 插件

## 注意

- 不会自动启动 Godot 编辑器
- 不会调用任何 MCP 工具（`init_godot_project` 已经从 MCP 移除）
- 如果 `active-game.json` 已存在，本 command 会覆盖它，把当前操作目标
  切换到新项目；旧项目的文件不会被删除
