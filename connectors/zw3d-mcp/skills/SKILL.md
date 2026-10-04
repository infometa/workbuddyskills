---
name: zw3d-mcp-skill
description: ZW3D 三维建模技能 — 草图绘制、实体拉伸/旋转/扫掠/放样、工程特征、装配约束、钣金、外观材质、几何查询、安装目录发现与部署兜底
version: 1.2.1
author: ZW3D MCP Team
---

# ZW3D 建模 Skill

本 Skill 为 ZW3D CAD 提供建模全链路能力：草图 → 实体 → 特征 → 装配 → 外观 → 查询。

> **前置条件：用户本机必须已安装并启动 ZW3D 3200 及以上版本。**
> 若用户尚未安装 ZW3D（连接器报「No ZW3D installation detected」或连接失败），请先引导用户前往官方下载页安装：https://www.zwsoft.cn/product/zw3d
> 安装完成后需重新启动 ZW3D，并重新连接/添加 MCP 连接器。
> 若工具调用失败并提示连接错误，请先提示用户打开 ZW3D 应用程序。

---

## 启动前插件预检（强制执行）

> 目标：建模前确保「**正确的 ZW3D 已启动 + 插件 DLL 已就位**」，避免以无插件状态启动 ZW3D 导致
> 全部建模工具失败（表现：`no data returned from ZW3D` / `Failed to open event`）。

**三步走（按顺序）**：

1. **查路径**：调 `zw3d_status`（`resolve_remote: true`）→ 取 `zw3d_exe` / `zw3d_runtime_dir` / `remote_path`，
   并校验文件真实存在。
   - 查不到或路径无效 → **不要猜路径**，转「安装目录兜底」请用户提供目录。
2. **验 DLL**：确认 `<ZW3D目录>\apilibs\` 内 `ZW3D_MCP.dll`、`.env` 已存在，且与插件缓存
   `%LOCALAPPDATA%\ZWSOFT\ZW3D_MCP\plugins\v{版本}\node_modules\zw3d-mcp-plugin\bin\` 内容一致（大小 + SHA-1）。
   - 缺失/不一致 → **先部署再启动**：① 以管理员身份重连连接器（launcher 自动部署）；
     ② 或按「安装目录兜底」步骤 5 的管理员 PowerShell Copy-Item 命令手动复制。
3. **启 ZW3D**：ZW3D 未运行时，**用第 1 步拿到的 `zw3d_exe` 启动**（与 MCP 插件同源同版本，不另猜路径）；
   ZW3D 已在运行且步骤 2 做了新增部署 → 请用户**关闭后重开 ZW3D**（插件只在 ZW3D 启动瞬间加载）。

**自检收尾**：首个建模工具前先做 active root 查询；若返回 `no data returned from ZW3D` → 回到本预检或
「安装目录兜底」排查，不要盲目重试同一调用。

> 关闭/重启 ZW3D 一律先征得用户同意（见「进程管理约束」），优先引导用户自行操作，不代为强杀。

---

## 安装目录兜底：找不到或路径无效时（强制执行）

> **适用场景**：MCP 无法把正确的 ZW3D 路径交给 Agent——① `zw3d_status`（`resolve_remote: true`）
> 或 `zw3d://server/status` 查不到 `zw3d_exe` / `zw3d_runtime_dir` / `remote_path`；
> ② 返回的路径**经 Agent 文件系统校验不存在或不可用**（zw3d.exe、ZW3dRemote.exe 缺失，或启动即失败）；
> ③ 建模持续 `no data returned from ZW3D` / `Failed to open event` 且 apilibs 缺 DLL。
> 命中以上情况时**不要反复重试工具**，进入本兜底流程。

**为什么让用户提供目录是可靠路径**：注册表可能缺键/被清理，自定义或绿色安装不会注册；
此时用户给出安装目录 + Agent 在目录及子目录搜索，是最快恢复方式。

**步骤（按顺序执行）**：

1. **先自查并判定**：调 `zw3d_status`（`resolve_remote: true`），用文件系统校验返回的
   `zw3d_exe`、`remote_path` 是否真实存在；不存在或为空 → 判定"路径缺失/错误"，进入第 2 步。
2. **请用户提供目录**：询问"您的 ZW3D 装在哪个目录？"，提示典型位置
   （`C:\Program Files\ZWSOFT\ZW3D WuKong 2027`、`D:\...\ZWSOFT\...`），支持用户粘贴路径。
3. **搜索启动文件（用户目录 + 子目录）**：递归搜索（**限深 3 层**，避免全盘慢扫），目标：
   - 主程序：`zw3d.exe`
   - IPC 桥：`ZW3dRemote.exe`
   - 插件目录：名为 `apilibs` 的文件夹（内含 ZW3D_MCP.dll）
   - 参考命令（Agent 可用；把 `<用户目录>` 换成实际路径）：
     ```bash
     # Git Bash
     find "<用户目录>" -maxdepth 3 \( -iname 'zw3d.exe' -o -iname 'ZW3dRemote.exe' -o -iname 'apilibs' \) 2>/dev/null
     # PowerShell 等价：Get-ChildItem "<用户目录>" -Recurse -Depth 2 -Include zw3d.exe,ZW3dRemote.exe -ErrorAction SilentlyContinue
     ```
   - **多版本共存**：把命中的所有候选目录列给用户确认；也可用 `ZW3D_MCP_PREFERRED_VERSION`
     （如 3200）锁定目标版本。
4. **校验候选目录**：确认该目录同时含 `zw3d.exe` 与 `apilibs\`（或 `ZW3dRemote.exe`）；
   版本须为受支持的 **ZW3D 3200+**（注册表 `ProductVersion` 形如 `32.xx`）。
5. **部署 DLL + .env**：
   - 源：插件缓存 `%LOCALAPPDATA%\ZWSOFT\ZW3D_MCP\plugins\v{版本}\node_modules\zw3d-mcp-plugin\bin\`
     （内含 `ZW3D_MCP.dll`、`.env`；若缓存缺失，可重连连接器触发 launcher 下载）。
   - 目标：`<候选目录>\apilibs\`。
   - Agent **先尝试直接复制**并 SHA-1 校验一致性；
   - 若 `EPERM/EACCES`（写 `Program Files` 需管理员）→ 给用户一条代入真实路径的
     **管理员 PowerShell** 命令：
     ```powershell
     Copy-Item "$env:LOCALAPPDATA\ZWSOFT\ZW3D_MCP\plugins\v3200\node_modules\zw3d-mcp-plugin\bin\ZW3D_MCP.dll" "<候选目录>\apilibs\" -Force
     Copy-Item "$env:LOCALAPPDATA\ZWSOFT\ZW3D_MCP\plugins\v3200\node_modules\zw3d-mcp-plugin\bin\.env" "<候选目录>\apilibs\" -Force
     ```
   - 或提示"以管理员身份运行 WorkBuddy 后重连连接器"（launcher 会自动部署）。
6. **重启 ZW3D**：请用户**完全关闭并重新打开 ZW3D**（插件只在启动时加载）。重新打开时优先用
   `zw3d_status` 返回的 `zw3d_exe`（与插件同源），无效才用本流程搜到的目录。遵循「进程管理约束」：
   不代为强杀进程，先征得用户同意、优先引导用户自行关闭。
7. **自检收尾**：重连后调 `zw3d_status` 与 active root 查询确认链路打通；仍失败则回到本流程或
   「常见错误场景」排查，不要盲目重试建模工具。
8. **确未安装**：若用户目录内也搜不到 → 引导安装：官方下载 https://www.zwsoft.cn/product/zw3d
   （安装后重新启动 ZW3D，并重新连接/添加 MCP 连接器）。

> 目录含空格属正常（如 `ZW3D WuKong 2027`），搜索/复制命令一律加引号；给用户的命令中
> `<候选目录>` 需替换为实际路径，切忌原样粘贴。

---

## 工具发现机制（重要）

- ZW3D 的全部建模工具由 **MCP 服务动态提供**（`tools/list`）。工具的名称、参数、输入 schema 与使用说明，一律**以 MCP 服务返回的工具描述为准**。
- 建模前，请先查询相关工具的 description 与 input schema，再按其说明调用。
- 工具调用失败时，优先读取该工具返回的错误信息，并结合「常见错误场景」排查。

---

## 进程管理约束（必须遵守）

- **严禁自行强行关闭 ZW3D 进程**：未经用户同意，不得自行终止/结束 ZW3D 进程（包括但不限于调用结束进程、taskkill、强杀等任何方式）。
- **终止前必须提示并征得同意**：凡涉及需要终止或重启 ZW3D 进程的操作，都必须先明确提示用户、说明原因，并**得到用户明确同意后**才可执行。
- **优先引导用户自行关闭**：确需关闭 ZW3D 时，优先提示用户自行关闭，而非由 AI 代为强制结束。

---
## 工作流建议

1. **建模前**：用 active root 查询工具确认当前活动文档与文件类型。
2. **新建零件**：用空白零件/装配体创建命令（part 或 assembly）。
3. **画实体优先用复合命令**：草图+拉伸、草图+旋转、扫掠、放样等一步成型的复合命令。
4. **不要两步走**：不要先单独建草图再拉伸/旋转，复合命令内部会自动创建草图。
5. **特征顺序**：先完成主要几何特征，最后再添加倒圆角、倒角。
6. **查询 ID 再操作**：调用特征工具前，先用查询工具获取 face_id / edge_id / shape_id / feature_id。
7. **装配流程**：先创建装配体 → 插入零件 → 添加约束。
8. **外观流程**：搜索材质 → 应用材质。

---

## 常见错误场景

| 错误场景 | 表现 | 解决方案 |
|---------|------|---------|
| ZW3D 未启动 | 工具返回连接错误 | 先做「启动前插件预检」，再启动 ZW3D |
| 注册表查不到 ZW3D（自定义/绿色安装、键被清理） | `zw3d_status` 无 `zw3d_exe` / 返回 "No ZW3D installation detected" | 走「安装目录兜底」：请用户提供目录 → 搜索 zw3d.exe/apilibs → 部署 DLL |
| zw3d_exe 路径无效（Agent 校验不存在或启动即失败） | `zw3d_status` 有路径但文件不存在 / 启动秒退 | 路径错误→走「安装目录兜底」；路径正确→按预检部署 DLL 后重启 ZW3D |
| apilibs 缺 DLL/.env 或版本不一致 | `no data returned from ZW3D` / `Failed to open event` | 按「启动前插件预检」部署 DLL+.env 后**重启 ZW3D**，再重连连接器 |
| 部署被拒（非管理员） | `EPERM` / `EACCES`，连接被阻断（FATAL startup blocked） | 以管理员身份运行 WorkBuddy 重连，或在管理员 PowerShell 手动复制（见兜底步骤 5） |
| 实体 ID 无效 | 工具返回 "entity not found" | 用查询工具获取正确 ID |
| 布尔运算失败 | shape_id=0 | 检查目标实体是否存在 |
| 特征再生失败 | regen_status≠0 | 检查参数是否合理，面/边是否仍存在 |
| 草图轮廓不闭合 | 拉伸失败 | 确保 profile 首尾闭合 |
| 扫掠路径多段 | 返回错误 | 将多段路径合并为一条样条 |
| 重复插入组件 | 装配重影 | 删除多余组件 |
| 螺纹面非圆柱 | 标记螺纹报错 | 先确认目标面类型为圆柱 |

---

## 建模最佳实践

- **复合命令优先**：用「草图+拉伸」等复合命令，而非分开调用草图 + 拉伸。
- **ID 查询优先**：操作前用查询工具获取精确 ID，不要猜测。
- **特征顺序**：主要几何 → 孔/螺纹/筋/壳 → 最后倒圆角/倒角。
- **修改优先于重建**：用参数修改工具调整，避免删除重建。
- **嵌套不相交轮廓**：拉伸会被拆成多个实体，孔类特征用 remove 操作。
- **圆形阵列注意**：spacing_angle 是相邻实例间距角（如 24 个实例用 15°），非总角度。
- **装配基础件**：第一个插入的组件用 anchor=1 固定。
