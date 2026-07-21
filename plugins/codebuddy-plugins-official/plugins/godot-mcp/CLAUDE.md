# CLAUDE.md - Godot MCP Project Guidelines

## ⚠️ Workflow Guardrails（最高优先级，必读）

当用户请求**做任何 Godot 游戏**（贪吃蛇、平台跳跃、FPS、RPG、2D/3D、任意题材）时，
**必须按以下顺序执行，禁止跳步**：

### 第一步：环境检查（不可跳过）

使用**文件系统**检查当前工作区根目录，**不要仅依赖 `manage_project(action="list")`**
（注册表中的项目可能是历史残留，实际文件可能不存在）：
- 工作区是否存在 `project.godot`？
- 工作区是否存在 `godot-editor/Godot*.exe`？

### 第二步：环境不全 → 立即调 init_godot_project（不要启动策划！）

任何一个不存在，**第一个动作必须是：**
```
init_godot_project(workspace="<工作区路径>", template="<推断模板>")
```

**绝对禁止的行为**（违反必需立即停下重来）：
- ❌ 在环境未装配前启动 `game-planning` / `game-dev-workflow` / `interaction-design` /
  `gameplay-design` / `level-design` / `numerical-design` 任一策划技能
- ❌ 在环境未装配前生成任何策划文档（如 docs/planning/*.md）
- ❌ 在环境未装配前手写 `project.godot` / `.tscn` / `.gd` 文件（模板会自动生成）
- ❌ 在环境未装配前调用 `operate_node` / `operate_scene` / `operate_script` / `run_project`
  （需 Godot 进程连接，一定失败）
- ❌ 看到 `manage_project(action="list")` 返回“已注册但未连接”就认为环境 OK —— 必须额外核对文件系统

### 第三步：模板自动推断（不必问用户）

| 用户描述关键词 | template |
|---|---|
| 2D / 横版 / 平台 / 像素 / 跑酷 / **贪吃蛇** / **俄罗斯方块** / 俯视 / 打砖块 | `2d-platformer` |
| 3D / FPS / 射击 / 第一人称 | `3d-fps` |
| 空白 / 最小 / blank | `empty` |
| 其它 | `default` |

### 第四步：环境就绪后才进入后续阶段

1. （可选）进入 `game-planning` 生成策划文档
2. 进入 `godot-dev` 调用 `scan_project_modules` / `operate_scene` / `operate_script` / `operate_node` 开发游戏
3. `run_project(action="run")` 后报错 → `godot-debug` 自动循环

### 错误示例 vs 正确示例

**❌ 错误**（实际发生过）：
```
用户：做个贪吃蛇
AI → manage_project(action="list") → 看到一条记录 → “项目已注册” → 进入策划阶段生成文档
AI → 用 Write/Edit 手写 project.godot / scene.tscn / *.gd……
```

**✅ 正确**：
```
用户：做个贪吃蛇
AI → 读工作区根目录 → 看到没有 project.godot
     → init_godot_project(workspace="<cwd>", template="2d-platformer") → 下载编辑器 + 拷模板
     → 环境就绪后再进入策划或开发
```

## Build & Run Commands

### Development
- **Server Build**: `cd server && npm run build`
- **Server Start**: `cd server && npm run start`
- **Server Dev Mode**: `cd server && npm run dev` (auto-rebuild on changes)

### Deployment
- **One-Click Deploy**: `cd server && npm run deploy`
- **Dry Run**: `cd server && npm run deploy -- --dry-run`
- **With Godot Project**: `cd server && npm run deploy -- --godot-project "path/to/project"`

### Testing & Status
- **Run Tests**: `cd server && npm run test`
- **Check Status**: `cd server && npm run status`
- **Diagnose Issues**: `cd server && npm run status:diagnose`
- **Uninstall**: `cd server && npm run uninstall`

### Godot
- **Run Godot Project**: Open project.godot in Godot Editor
- **Enable Plugin**: Project > Project Settings > Plugins > Enable "Godot MCP"

## Project Structure

```
server/
├── src/                    # TypeScript source code
│   ├── index.ts           # MCP server entry point
│   ├── tools/             # MCP tool implementations
│   ├── resources/         # MCP resource implementations
│   └── utils/             # Shared utilities
├── scripts/               # Deployment and utility scripts
│   ├── deploy.js          # One-click deployment
│   ├── deployment_status.js # Status management
│   └── path_utils.js      # Cross-platform path utilities
├── test/                  # Test scripts
│   └── test_commands.js   # Interface regression tests
└── dist/                  # Compiled JavaScript (generated)

addons/godot_mcp/          # Godot plugin
├── plugin.cfg             # Plugin configuration
├── mcp_server.gd          # Main plugin entry
├── websocket_server.gd    # WebSocket server
├── command_handler.gd     # Command router
├── commands/              # Command implementations
│   ├── node_commands.gd
│   ├── scene_commands.gd
│   ├── script_commands.gd
│   ├── project_commands.gd
│   └── editor_commands.gd
└── ui/                    # UI components
```

## Code Style Guidelines

### TypeScript (Server)
- Use camelCase for variables, methods, and function names
- Use PascalCase for classes/interfaces
- Strong typing: avoid `any` type
- Prefer async/await over Promise chains
- Import structure: Node modules first, then local modules

### GDScript (Godot)
- Use snake_case for variables, methods, and function names
- Use PascalCase for classes
- Use type hints where possible: `var player: Player`
- Follow Godot singleton conventions (e.g., `Engine`, `OS`)
- Prefer signals for communication between nodes

### General
- Use descriptive names
- Keep functions small and focused
- Add comments for complex logic
- Error handling: prefer try/catch in TS, use assertions in GDScript

## Interface Contract

### Command Naming Convention
- MCP Tools use snake_case: `init_godot_project`, `operate_node`, `operate_scene`, `operate_script`, `run_project`
- Aggregated tools take an `action` parameter (e.g. `operate_node(action="create"|"delete"|"update"|"get"|"list")`)
- Resource URIs use forward slash: `godot/script`, `godot/scene/current`

### Adding New Commands
1. Add tool definition in `server/src/tools/*.ts`
2. Add command handler in `addons/godot_mcp/commands/*.gd`
3. Register handler in `command_handler.gd`
4. Update `docs/command-reference.md`
5. Add test case in `server/test/test_commands.js`
