---
name: godot-new
description: >
  仅当 godot-deploy 已完成（${WORKSPACE}/godot-editor 存在）且需要**新建
  一个游戏项目目录**时激活：用户说「再做一个 / 另一个游戏 / 新建游戏 /
  new game」，或被 godot-dev 在场景 1/2 让位过来。负责模板推断、复制
  templates/<...> → ${WORKSPACE}/<gameName>、注入 addons/godot_mcp、
  覆盖写 ${WORKSPACE}/active-game.json。
  用户首次说「做个 XX 游戏」请由 godot-dev 路由进来，不要直接激活本 Skill。
---

# 新建 Godot 游戏项目（Skill 自执行版）

> 严格遵循 [docs/需求文档/4.23.md](../../docs/需求文档/4.23.md) 场景 1 / 场景 2：
> **创建游戏 + 在工作区根目录写一个 JSON 说明当前操作的游戏文件夹。**

---

## 工作区目录契约（4.23.md 强制约定）

本 Skill 创建的项目**必须**作为 `${WORKSPACE}` 的一级子目录，与
`godot-editor/` 和 `active-game.json` 平铺同级（详见
[godot-dev/SKILL.md](../godot-dev/SKILL.md#工作区目录契约4-23-md-强制约定所有子-skill-必须遵守)）：

```
${WORKSPACE}/
├── godot-editor/        ← 由 godot-deploy 维护，本 Skill 不动
├── active-game.json     ← 本 Skill 覆盖写入
├── game1/               ← 第一次新建
└── game2/               ← 用户「再做一个」时新建
```

**严禁**：
- 把项目嵌套在 `godot-editor/` 内或其他子目录中
- 在工作区写除 `<projectName>/` 与 `active-game.json` 之外的根级别资产
- 修改 `${WORKSPACE}/godot-editor/`（那是 godot-deploy 的领地）

---

## 输入解析

从用户原话提取：

| 参数 | 默认 / 推断规则 |
|------|----------------|
| `projectName` | 优先用户显式给出；否则按下表推断；最后兜底 `my-game` |
| `template` | 优先用户显式指定；否则按下表推断；推不出来就 `empty`（4.23.md 要求）|

### 模板推断表（与 [templates/](../../templates/) 目录一致）

| 用户描述包含 | 模板 |
|-------------|------|
| 「平台跳跃 / 横版 / 2D 动作 / 马里奥 / platformer」 | `2d-platformer` |
| 「FPS / 第一人称 / 3D 射击 / first-person」 | `3d-fps` |
| 「弹幕 / 射击 / 塔防 / RPG / 棋牌 / 卡牌 / 益智 / 2D」等明确小类型 | `default`（带通用骨架） |
| 「空白 / 从零 / empty」 或 推不出 | `empty` |

### 项目名推断表

| 关键词 | 项目名 |
|--------|-------|
| 塔防 / tower defense | `tower-defense` |
| RPG | `my-rpg` |
| 平台跳跃 / platformer | `platformer-game` |
| 弹幕 / 射击 / FPS | `shooter-game` |
| 贪吃蛇 / snake | `snake-game` |
| 推不出 | `my-game` |

把推断结果**告诉用户**，例如：「将创建项目 `snake-game`，使用模板 `default`」，
**不要反问**。如果用户要求改名，再覆盖。

---

## 执行步骤（PowerShell，依次执行并把输出贴回对话）

```powershell
$ws       = "${WORKSPACE}"
$pluginRoot = "${env:CODEBUDDY_PLUGIN_ROOT}"
$projectName = "<上面推断>"
$template    = "<上面推断>"
$projectDir  = Join-Path $ws $projectName
$templateDir = Join-Path $pluginRoot "templates\$template"

if (-not (Test-Path $templateDir)) {
    Write-Host "[FAIL] 模板不存在: $templateDir"; return
}
if (Test-Path $projectDir) {
    Write-Host "[FAIL] 项目目录已存在: $projectDir，请换名或手动删除"; return
}
# 4.23.md 目录契约：projectName 不得与保留名冲突
if ($projectName -in @("godot-editor", "active-game.json", "addons", ".vscode")) {
    Write-Host "[FAIL] 项目名 '$projectName' 与工作区保留名冲突，请换名"; return
}

# 1) 复制模板
Copy-Item -Path $templateDir -Destination $projectDir -Recurse -Force
Write-Host "[OK] 已复制模板 $template → $projectDir"

# 2) 复制 MCP 插件（4.23.md 要求新项目立刻能被 MCP 操作）
$addonsSrc = Join-Path $pluginRoot "addons\godot_mcp"
$addonsDst = Join-Path $projectDir "addons\godot_mcp"
if (Test-Path $addonsSrc) {
    New-Item -ItemType Directory -Path (Split-Path $addonsDst) -Force | Out-Null
    Copy-Item -Path $addonsSrc -Destination $addonsDst -Recurse -Force
    Write-Host "[OK] 已植入 addons/godot_mcp/"
}

# 3) 更新 project.godot：写 config/name + 用本机 godot-editor 实际版本替换占位符
#    （模板里 config/features 用 "__GODOT_VERSION__" 占位，避免硬编码 4.6）
$pg = Join-Path $projectDir "project.godot"
$godotVersion = $null
$editorExe = Get-ChildItem -Path (Join-Path $ws "godot-editor") -Filter "Godot_v*.exe" `
                          -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($editorExe) {
    # 文件名形如 Godot_v4.6-stable_win64.exe → 取出 "4.6"
    if ($editorExe.Name -match 'Godot_v(\d+\.\d+)') { $godotVersion = $Matches[1] }
}
if (-not $godotVersion) {
    Write-Host "[WARN] 未能从 godot-editor 探测到版本，回退使用 4.6"
    $godotVersion = "4.6"
}
if (Test-Path $pg) {
    $content = Get-Content $pg -Raw
    $content = $content -replace 'config/name="[^"]*"', "config/name=`"$projectName`""
    $content = $content -replace '__GODOT_VERSION__', $godotVersion
    Set-Content $pg -Value $content -Encoding UTF8
    Write-Host "[OK] project.godot 已写入 config/name=$projectName, godot 版本=$godotVersion"
}

# 4) 标准目录骨架（与 docs/AI_GUIDE.md 一致；模板里没有的才补）
foreach ($d in @(
    "assets\audio","assets\fonts","assets\models","assets\textures","assets\ui",
    "data",
    "scenes\entities","scenes\levels","scenes\main","scenes\ui",
    "scripts\autoload","scripts\components","scripts\systems","scripts\ui"
)) {
    New-Item -ItemType Directory -Path (Join-Path $projectDir $d) -Force | Out-Null
}

# 5) 写入 / 覆盖 active-game.json （4.23.md 强制要求）
$activeJson = Join-Path $ws "active-game.json"
@{
    gameDir       = $projectDir
    projectName   = $projectName
    template      = $template
    godotVersion  = $godotVersion
    createdAt     = (Get-Date).ToString("o")
    pluginVersion = "2.0.0"
} | ConvertTo-Json -Depth 5 | Set-Content $activeJson -Encoding UTF8
Write-Host "[OK] active-game.json 已写入根目录: $activeJson"

# 6) 配置 godot-tools LSP（VSCode 扩展）
$vscodeDir = Join-Path $projectDir ".vscode"
New-Item -ItemType Directory -Path $vscodeDir -Force | Out-Null
$settings = @{ "godotTools.lsp.serverPort" = 6005; "godotTools.sceneFileConfig" = "open" }
$settings | ConvertTo-Json | Set-Content (Join-Path $vscodeDir "settings.json") -Encoding UTF8
Write-Host "[OK] .vscode/settings.json 已配置 LSP 端口 6005"

# 7) 自动拉起 Godot 编辑器并加载新项目（节省用户手动双击 + 导入）
#    --editor --path <projectDir> 是 Godot 官方支持的命令行参数，
#    会直接以编辑器模式打开该项目，首次会自动完成 import。
#    插件启用（Plugins 开关）仍然需要用户在 GUI 里勾一下。
$editorExeForLaunch = Get-ChildItem -Path (Join-Path $ws "godot-editor") -Filter "Godot_v*.exe" `
                                   -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($editorExeForLaunch) {
    try {
        Start-Process -FilePath $editorExeForLaunch.FullName `
                      -ArgumentList @("--editor", "--path", $projectDir) | Out-Null
        Write-Host "[OK] 已启动 Godot 编辑器并加载项目: $projectDir"
        $script:editorAutoLaunched = $true
    } catch {
        Write-Host "[WARN] 自动启动 Godot 编辑器失败：$($_.Exception.Message)。请手动打开。"
        $script:editorAutoLaunched = $false
    }
} else {
    Write-Host "[WARN] 在 ${ws}\godot-editor 下未找到 Godot_v*.exe，跳过自动启动。"
    $script:editorAutoLaunched = $false
}
```

---

## 完成后引导（**必须**输出）

根据步骤 7 是否成功拉起编辑器，二选一输出：

### A. 编辑器已自动启动（`$editorAutoLaunched -eq $true`）

```
╔═══════════════════════════════════════════════════════╗
║  ✓ 新游戏项目创建完成，Godot 编辑器已自动启动         ║
╠═══════════════════════════════════════════════════════╣
║  项目名: <projectName>                                ║
║  模板:   <template>                                   ║
║  路径:   <projectDir>                                 ║
║                                                       ║
║  你只需要在已打开的 Godot 编辑器里做一件事：          ║
║  Project → Project Settings → Plugins                 ║
║  把 GodotMCP 切到 Enabled，状态栏出现                 ║
║  "MCP: Listening on port 9080" 后告诉我即可。         ║
║                                                       ║
║  （首次打开时 Godot 会自动 import 资源，稍等几秒）    ║
╚═══════════════════════════════════════════════════════╝
```

### B. 自动启动失败（`$editorAutoLaunched -ne $true`）

```
╔═══════════════════════════════════════════════════════╗
║  ✓ 新游戏项目创建完成（编辑器需手动启动）            ║
╠═══════════════════════════════════════════════════════╣
║  项目名: <projectName>                                ║
║  模板:   <template>                                   ║
║  路径:   <projectDir>                                 ║
║                                                       ║
║  请手动完成以下步骤：                                  ║
║  1. 双击 <ws>\godot-editor\Godot_v*.exe              ║
║  2. Import / 加载 <projectDir>                        ║
║  3. Project → Project Settings → Plugins 启用 GodotMCP║
║  4. 状态栏出现 "MCP: Listening on port 9080" 告诉我   ║
║                                                       ║
║  active-game.json 已写入 <ws>，后续 godot-dev 会      ║
║  自动认得这个项目目录。                                ║
╚═══════════════════════════════════════════════════════╝
```

---

## 严禁行为

- ❌ **不要**调用任何 MCP 工具来建项目（`init_godot_project` 等已不存在）
- ❌ **不要**反问用户「项目名叫什么、用什么模板」——按推断表直接推断
- ❌ **不要**代用户点 Plugins 开关（必须用户在 GUI 手动启用 GodotMCP）
- ❌ **不要**写入除 `active-game.json` 之外的根级别文件
- ❌ **不要**在已有 `active-game.json` 而用户未明确说"新建"时执行本流程
  （那是 godot-dev 场景 3 的事）
