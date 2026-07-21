---
name: godot-dev
description: >
  **Godot 游戏开发统一入口（4.23 三场景分流总 Skill）**。当用户用自然语言提出
  任何与「做游戏 / 开发游戏 / 加玩法 / 写 Godot 脚本 / 改场景 / 改节点 /
  做关卡 / 做 UI / 做角色 / 做敌人 / 做菜单 / 做 2D / 做 3D / 做 RPG /
  做平台跳跃 / 做贪吃蛇 / make a game / build a game / add gameplay /
  godot script / godot scene」相关的请求时激活。
  本 Skill **必须自己执行环境检测、意图判别、流程编排**（4.23.md 明确规定
  Skill 负责所有匹配/流程/资源/命令逻辑，不能甩给 MCP），并按照 4.23.md 的
  三个场景把控制权分别移交给 [godot-deploy](../godot-deploy/SKILL.md) /
  [godot-new](../godot-new/SKILL.md) 子流程，或直接用唯一的 MCP 编辑器单元
  工具 `build_godot_scene` 完成场景修改。
  ——
  仅当用户「只想部署 / 重连 MCP，不开发」时让位给 godot-deploy；
  仅当用户报告「运行报错 / 编译错误 / 崩溃」时让位给
  [godot-debug](../godot-debug/SKILL.md)。
  **不要**因为「工作区还没有 project.godot」就拒绝触发——本 Skill 自己会判断
  并切到场景 1 走部署 + 新建流程。
---

# Godot 开发统一入口（4.23 三场景分流）

> 严格遵循 [docs/需求文档/4.23.md](../../docs/需求文档/4.23.md)：
> **Skill 负责所有匹配逻辑、流程管理、资源下载、命令运行；
> MCP 只负责对 Godot 编辑器的单元操作。**
> 所以本文件里**必须**真实地跑 shell 命令、读文件、写 `active-game.json`，
> **不要**幻想存在某个 MCP 路由工具会替你判断（旧的 `godot_dev_router` 已删除）。

---

## 工作区目录契约（4.23.md 强制约定，所有子 Skill 必须遵守）

`${WORKSPACE}` 的最终结构 **永远** 是平铺的：

```
${WORKSPACE}/
├── godot-editor/          ← Godot 编辑器二进制（由 godot-deploy 下载/解压）
│   └── Godot_v4.6-stable_win64.exe
├── active-game.json       ← 全局唯一的「当前操作游戏目录」标记（由 godot-new 写入）
├── game1/                 ← 第 1 个游戏项目（由 godot-new 创建）
│   ├── project.godot
│   ├── addons/godot_mcp/
│   ├── scenes/  scripts/  assets/  data/  docs/
│   └── .vscode/
├── game2/                 ← 用户「再做一个」时由 godot-new 新建的第 2 个项目
│   └── ...
└── （用户可能存在的其他无关文件，本插件不动）
```

强约束：
- **`godot-editor/` 必须落在 `${WORKSPACE}/godot-editor/`**，不是插件目录、
  不是用户目录、不是嵌套在某个 game 里
- **`active-game.json` 必须放在 `${WORKSPACE}/active-game.json`**，与所有
  game 目录、godot-editor 平铺同级
- **每个游戏是 `${WORKSPACE}` 的一级子目录**，不嵌套、不带前缀
- 所有路径推断（gameDir / 编辑器可执行文件位置 / addons 注入位置）都基于
  此结构；任何子 Skill（godot-deploy / godot-new / godot-debug）都**不得**
  把这些资产放到其他位置

`active-game.json` 的字段：

```jsonc
{
  "gameDir":       "<absolute path, 例如 D:/work/${WORKSPACE}/game1>",
  "projectName":   "game1",
  "template":      "default" | "2d-platformer" | "3d-fps" | "empty",
  "createdAt":     "<ISO8601>",
  "pluginVersion": "2.0.0"
}
```

---

## 第 0 步：环境探测（每次激活的第一件事，必做，不可省略）

用一段 PowerShell 一次性收集 4 个标志位，**不要**反问用户。

```powershell
$ws = "${WORKSPACE}"   # Agent 已知的当前工作区绝对路径

# 0.1 active-game.json
$agJson = Join-Path $ws "active-game.json"
$active = $null
if (Test-Path $agJson) { $active = Get-Content $agJson -Raw | ConvertFrom-Json }
$hasActiveGame = [bool]$active

# 0.2 gameDir 与 project.godot
$gameDir = if ($hasActiveGame) { $active.gameDir } else { $null }
$hasProject = $false
if ($gameDir -and (Test-Path (Join-Path $gameDir "project.godot"))) {
    $hasProject = $true
} elseif (-not $hasActiveGame) {
    # fallback：扫一级子目录找任意 project.godot；只用于诊断展示，不自动写 active-game.json
    $cand = Get-ChildItem -Path $ws -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.FullName "project.godot") } |
            Select-Object -First 1
    if ($cand) { $gameDir = $cand.FullName; $hasProject = $true }
}

# 0.3 godot-editor 是否已下载到工作区
$editorDir = Join-Path $ws "godot-editor"
$hasEditor = (Test-Path $editorDir) -and `
             ((Get-ChildItem -Path $editorDir -Filter "Godot_v*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null)

# 0.4 9080 端口探测（Godot 插件是否启用）
$probe = Test-NetConnection -ComputerName 127.0.0.1 -Port 9080 `
         -InformationLevel Quiet -WarningAction SilentlyContinue
$editorListening = [bool]$probe

Write-Host "ENV: hasActiveGame=$hasActiveGame hasProject=$hasProject hasEditor=$hasEditor editorListening=$editorListening gameDir=$gameDir"
```

汇总四个标志位：

| 变量 | 含义 |
|------|------|
| `hasActiveGame` | `${WORKSPACE}/active-game.json` 是否存在 |
| `hasProject`    | active 游戏目录（或 fallback 子目录）下是否有 `project.godot` |
| `hasEditor`     | `${WORKSPACE}/godot-editor/` 下是否有 `Godot_v*.exe` |
| `editorListening` | 9080 是否在监听（即插件是否启用） |

---

## 第 1 步：意图判别（不要反问用户，按优先级直接判定）

把用户原话简单做关键词匹配：

| intent | 触发关键词 |
|--------|-----------|
| `new_game`     | 「再来一个 / 另一个 / 新游戏 / 再做一个 / 换一个游戏 / new game / another game」|
| `modify_game`  | 「加 / 改 / 删 / 优化 / 调整 / 修复 / 增加 / 替换」+ 节点/场景/脚本/UI/角色/敌人/关卡/菜单 |
| `make_game`    | 「做一个 X / 帮我做个 X / 想要个 X / make a X / build a X」（X 是游戏类型）|

按以下优先级直接判定（**禁止**反问用户）：

1. `hasProject == false`        → 一律 **场景 1 = make_game**
2. `hasProject == true` 且原话出现 `new_game` 关键词 → **场景 2 = new_game**
3. 其他                         → **场景 3 = modify_game**

---

## 第 2 步：按 4.23.md 三场景分流

### 🅐 场景 1 — `make_game`：空环境，全套部署 + 建项目

> 4.23.md：「环境为空或者只有无关文件，就按照旧的 deploy command 流程：
> 下载 godot 编辑器，创建游戏，**还需要在根目录添加一个 json 文件，
> 说明当前操作的游戏文件夹是哪个**」。

明确告诉用户：「正在按 4.23 场景 1 处理：先部署环境，再创建项目。」

执行顺序（**不要跳步**）：

1. **部署阶段**：执行
   [godot-deploy/SKILL.md](../godot-deploy/SKILL.md) 的 5 步流程
   （Node 检查、Server 构建、`.mcp.json` 注册、把 Godot 编辑器下载到
   `${WORKSPACE}/godot-editor/`、9080 探测）。
   - 步骤 5（9080 探测）通常会 `[WAIT]`，因为此时还没有项目可被编辑器打开。
     这是**正常**的——继续走步骤 2 创建项目，再让用户去打开编辑器即可。
2. **新建项目**：执行 [godot-new/SKILL.md](../godot-new/SKILL.md)：
   - 根据用户原话推断 `projectName` / `template`（推不出 → `empty`）
   - 复制模板 → `${WORKSPACE}/<projectName>`
   - 注入 `addons/godot_mcp/`
   - 写入 `${WORKSPACE}/active-game.json`
3. **引导用户**用 `${WORKSPACE}/godot-editor/` 下的 `Godot_v*.exe` 打开
   `${WORKSPACE}/<projectName>` 并启用 GodotMCP 插件。**不要**自动启动
   editor.exe（启用插件需要 GUI 操作）。
4. 用户回来再次说话时，会落到场景 3 走 `build_godot_scene` 完成首批游戏内容。

### 🅑 场景 2 — `new_game`：已有编辑器，仅新建另一个游戏

> 4.23.md：「当前环境已有 godot 编辑器，而且明确要一个新的游戏。则按照旧的
> new command 流程：仅新建游戏。如果用户的游戏需求明确，可以通过游戏推断出
> 哪个游戏模板合适，否则用空模板」。

明确告诉用户：「正在按 4.23 场景 2 处理：仅新建另一个游戏。」

1. **直接执行** [godot-new/SKILL.md](../godot-new/SKILL.md)：
   - 推断模板（推不出 → `empty`）
   - 复制模板到 `${WORKSPACE}/<projectName>`（与现有 game1/game2 平铺）
   - 注入 `addons/godot_mcp/`
   - **覆盖**写入 `active-game.json`，把 `gameDir` 切换到新项目
2. 引导用户在 Godot 编辑器中关闭旧项目、打开新项目目录、启用插件
3. **不要**重跑 godot-deploy（编辑器已就绪）；**不要**删除旧 game 目录

### 🅒 场景 3 — `modify_game`：修改当前游戏内容

> 4.23.md：「mcp 对项目的修改，所有场景的修改合并为一个工具，需要传递完整的
> 最终需要的场景树结构，然后内部用单元的方法实现。其他代码、策划案、表格，
> 以及图片、模型等资源，都直接在当前操作的游戏目录里修改」。

明确告诉用户：「正在按 4.23 场景 3 处理：修改 `<gameDir>` 内容。」

#### 前置条件检查

- `hasActiveGame == false` → 告诉用户先用「做一个 …」(场景 1) 或
  「再做一个 …」(场景 2) 创建项目；**不要**自己创建
- `hasProject == false`    → 同上
- `editorListening == false` → **让位给 godot-deploy** 把端口探起来后再说

#### 修改类型分流（基于 `gameDir = $active.gameDir`）

| 修改对象 | 处理方式 |
|----------|---------|
| **场景 / 节点 / 节点属性 / 节点附着的脚本** | 把"最终想要的场景树"完整地翻译成 `build_godot_scene` 的 root 树参数，**一次性调用 `build_godot_scene`**。**禁止**多次原子调用，**禁止**自己手写 `.tscn` |
| **独立 GDScript（autoload / 工具脚本，不挂节点）** | 直接用 Write/Edit 工具在 `${gameDir}/scripts/...` 里读写 `.gd` |
| **策划案 / 表格 / Markdown 文档** | 直接在 `${gameDir}/docs/`、`${gameDir}/data/` 里读写 |
| **图片 / 模型 / 音频等二进制资源** | `Copy-Item` / `Invoke-WebRequest` 到 `${gameDir}/assets/...`，由 Godot 编辑器自动 reimport |

#### `build_godot_scene` 调用约定

这是 4.23.md 场景 3 唯一允许的「场景修改」MCP 工具：

```
build_godot_scene({
  scenePath: "res://scenes/<场景名>.tscn",
  root: {
    name: "<根节点名>",
    type: "<Godot 节点类型，如 Node2D / CharacterBody2D / Control>",
    properties: { ... },          // Vector2 用 [x,y]；Color 用 [r,g,b,a] (0-1)；rotation 单位为弧度
    script: { path: "res://scripts/<x>.gd", content: "<完整 GDScript>" },
    children: [ ... ]             // 递归，每个子节点同样的结构
  },
  saveAfter:    true,             // 默认 true
  openInEditor: true              // 默认 true
})
```

把用户的开发需求**一次性**翻译成上面这个声明式 root 树，调一次
`build_godot_scene`，再把返回的 report **原样**展示给用户。

---

## Godot 4 路径与类型约定（写 `build_godot_scene` 参数时遵守）

| 类型 | 格式 | 示例 |
|------|------|------|
| 资源路径 | `res://...` | `res://scenes/main.tscn` |
| 节点类型 | Godot 4 类名 | `Node2D` / `CharacterBody2D` / `Control` / `Camera2D` |
| 脚本扩展名 | `.gd`（GDScript） | `res://scripts/player.gd` |
| 场景扩展名 | `.tscn`（文本格式） | `res://scenes/main.tscn` |
| Vector2 / Vector3 | 数组 | `[100, 200]` / `[1, 2, 3]` |
| Color | RGBA 数组 0–1 | `[1, 0.5, 0.5, 1]` |
| 旋转单位 | 弧度（radians） | `1.5708` |

---

## 严禁行为

- ❌ **不要**调用任何不在「`build_godot_scene` + 三个 debug 工具」之外的 MCP
  工具（旧的 `godot_deploy` / `godot_dev_router` / `init_godot_project` /
  `operate_node` / `operate_scene` / `operate_script` / `run_project` /
  `manage_project` / `scan_project_modules` / `get_project_info` /
  `list_templates` 等已经从 MCP 中**移除**，调用它们会失败）
- ❌ **不要**在 Skill 里写「我先调 router 让它告诉我下一步」——4.23.md 已经
  把路由职责放回 Skill，**这个文件本身就是路由**
- ❌ **不要**在没有 `active-game.json` 的情况下自己手写 `project.godot`
- ❌ **不要**为「修改场景」而做多次原子调用——必须一次 `build_godot_scene`
  传完整树
- ❌ **不要**做"自动 run_project → 自动再 debug"循环（本 MCP 已无 run_project）
- ❌ **不要**反复反问用户「你是要新建还是修改？」——按第 1 步优先级判定
- ❌ **不要**把 godot-editor 或 game 目录放到 `${WORKSPACE}` 之外或嵌套位置

---

## MCP 连接异常时的处理

调用 `build_godot_scene` / `get_debug_errors` / `get_script_errors` /
`get_editor_output` 时若收到 **「工具不存在 / 未注册 / connection refused /
ECONNREFUSED / WebSocket」** 类错误：

→ 立刻让位给 [godot-deploy](../godot-deploy/SKILL.md) 完成连接修复
（**不要**自己跑 npm / 改 `.mcp.json`），修复后让用户重新触发本 Skill。

---

## 输出格式

- **场景切换**：每次激活，第一行明确说「正在按 4.23 场景 X 处理：…」
- **MCP 工具结果**：原样展示返回的 report 文本，**不要复述、不要总结**
- **失败**：把错误信息和下一步建议简短给出，等待用户处理后重新触发
