---
name: zwcad-mcp-skill
description: ZWCAD 2D 平台与中望机械 — 绘制、查询、标注、块/图层/样式管理、图框/标题栏/BOM/球标等机械能力
version: "0.1.0"
author: "ZWCAD 2D MCP Team"
---

# ZWCAD 2D 建模与制图 Skill

本 Skill 让 AI 通过自然语言操作中望 CAD（ZWCAD）二维图纸与中望机械扩展：绘制实体、查询图面、标注尺寸、管理图层/块/样式，以及机械图框、标题栏、BOM 明细表等。

---

## 环境前提检查（任务开始前必须先做）

本 MCP 经 **Windows COM** 连接本机正在运行的 ZWCAD。每次任务前按 ①②③ 检查，任一不满足则按对应话术告知用户并停止调用工具。

### ① Windows 系统

`os.name != 'nt'` / `sys.platform != 'win32'` 即不满足，直接告知：

> 本 MCP 只支持 Windows 环境，当前系统无法使用。请更换到 Windows 电脑，安装 ZWCAD 后再试。

### ② 已安装中望 CAD（或中望机械 CAD）

检测 `zwcad_get_capabilities(probe_cad=true)` / `zwcad_get_app_info(scope="cad")`；返回 `platform.available=false`、`Connection closed` 或 COM 错误 `-2147221008` 即不满足。

- **未安装**：

> 当前电脑没有安装 ZWCAD，本 MCP 无法使用。请先到这里下载并安装：https://www.zwsoft.cn/product/zwcad
> 装好后：① 打开 ZWCAD 并新建/打开一张 DWG；② 在连接器管理页重连「中望CAD MCP」；③ 回来让我继续。

- **已装未启动**：提示启动 ZWCAD 并打开/新建 DWG，重连后继续。

### ③ 运行依赖 uvx（默认 `uvx zwcad-mcp` 启动）

`uvx --version` 报错**不等于没装**——官方安装器默认落在 `%USERPROFILE%\.local\bin\`，该目录常不在 PATH：

| 检测 | 处置 |
|---|---|
| `uvx --version` 返回版本号 | 就绪 |
| 报错，但常见路径下有 `uvx.exe` | **A｜补 PATH** |
| 命令和常见路径都找不到 `uvx.exe` | **B｜安装 uv** |
| `~/.workbuddy/mcp.json` 有 `zwcad-2d`/`zwcadmech` 等服务（即使 `disabled: true`）且 venv 完整 | **C｜启用本地服务**（最快，不碰 uvx） |

uvx 常见路径：`%USERPROFILE%\.local\bin\uvx.exe`（默认）、`%LOCALAPPDATA%\Programs\uv\uvx.exe`、`C:\Program Files\uv\bin\uvx.exe`。检测：`Test-Path "$env:USERPROFILE\.local\bin\uvx.exe"`

**A｜补 PATH**：先用 `$env:PATH = "<目录>;$env:PATH"; uvx zwcad-mcp` 临时验证，确认后 `[Environment]::SetEnvironmentVariable("Path", $env:Path + ";<目录>", "User")` 永久修复；改完**重启终端与 WorkBuddy**，`where.exe uvx` 返回路径即生效。

**B｜安装 uv**（自带 uvx）：`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` 或 `winget install --id=astral.sh.uv`；装完重启终端 → 连接器断开重连 → 首次自动拉依赖。启动标志依次：`Installed N packages in Xs` → `INFO: ZWCAD-2D MCP Server 启动中...` → `Starting MCP server ... with transport 'stdio'`；卡 `Resolved` 行多为下载慢，配 `UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple`（连接器 `env` 默认已配）。

**C｜启用本地服务**：`cat ~/.workbuddy/mcp.json` 查看，在连接器管理页启用即可。

> 非 `uvx` 启动（如已 pip 装到某 Python 环境）跳过 ③，仅查 ①②。

---

## 工具发现机制（重要）

- 全部工具由 **MCP 服务动态提供**（`tools/list`），当前版本 39 个（平台 26 + 机械 11 + 诊断 2），随版本演进可能增减。工具名称、参数与输入 schema 一律**以 MCP 服务返回为准**，本文档不再重复罗列。
- 调用前先查目标工具的 description 与 input schema，再按其说明传参（角度单位为弧度）。
- 工具调用失败时优先读取返回的 `error` / `code` / `hint` 字段，并结合「常见错误场景」排查。

> **参考信息源**：本 Skill 涉及的工具详细说明、类型库加载机制与重要说明，以 `zwcad-mcp` 包随附的 README 为准。本连接器默认通过 `uvx` 启动，此时 `README.md` 位于 uv 缓存目录中（路径含随机哈希、不固定，无需手工查找）；若改用 `pip` 安装，则位于对应 Python 环境的 `site-packages` 目录下。README 内容与同版本 `dist-info\METADATA` 中的描述一致，任何安装方式下均可这样读取全文：
>
> ```bash
> python -c "import importlib.metadata as m; print(m.metadata('zwcad-mcp')['Description'])"
> ```
>
> 下文中的「README」均指此文档。

---

## 进程与文档安全约束（必须遵守）

- **严禁自行强行关闭 ZWCAD 进程**：未经用户同意，不得以任何方式终止 ZWCAD 进程。
- **破坏性操作必须先确认**：删除实体、覆盖保存、关闭文档、替换插件、修改系统变量等写操作会直接改变当前 DWG，**执行前必须向用户说明并征得同意**，必要时提示先备份图纸。
- **单活动实例**：同一时间只操作一个 ZWCAD 系列实例。多开后 COM 可能连接非预期窗口，操作前先调用 `zwcad_get_capabilities(probe_cad=true)` 确认活动产品与图纸。

---

## 工作流原则（按序执行）

1. **环境与开画前探测**：先按上文「环境前提检查」确认 ①Windows 平台、②已安装 ZWCAD 且打开 DWG、③uvx 可用；再调用 `zwcad_get_capabilities(probe_cad=true)` 确认活动产品、图纸、已挂载工具组；`zwcad_get_app_info(scope="cad")` 验证平台 COM。
2. **先查询后操作**：绘图、标注、变换、样式管理等操作前，先用对应查询工具确认目标实体、名称与参数，避免盲目调用；同批绘制用 `zwcad_draw_batch` 一次提交，减少交互轮次。
3. **机械流程**：机械诊断 → 初始化标准 → 建图框 → 填标题栏 → 球标/BOM，按此顺序执行。
4. **排障**：`zwcad_diagnose(probe_cad=true)` 获取平台/机械连接状态与修复建议。

> 绘图/标注/变换/样式管理等工具的名称、参数与枚举值不再在此罗列；调用前通过 `tools/list` 及目标工具的 description 与 input schema 获取最新定义，亦可查阅 README「工具详细说明」。

---

## 常见错误场景

| 错误场景           | 表现                                                                                            | 解决方案                                                                                                                                    |
| ------------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 非 Windows 系统    | 运行环境为 macOS/Linux，工具全部不可用                                                          | 直接告知用户"本 MCP 只支持 Windows"并停止操作，详见「环境前提检查 ①」                                                                     |
| 未安装 ZWCAD       | 探测不到 CAD 实例：`platform.available=false` / `Connection closed`                            | 直接告知用户下载安装 ZWCAD：https://www.zwsoft.cn/product/zwcad ，装好打开 DWG 后再重连，详见「环境前提检查 ②」                            |
| uvx 不在 PATH      | `uvx --version` 报错，但常见路径下能找到 `uvx.exe`                                                | **不要重装**，补 PATH 后重启终端与 WorkBuddy，见「③ A」                                                                                |
| uv 未安装          | 命令和常见路径都找不到 `uvx.exe`                                                                  | 一键装 uv（自带 uvx）后重连，见「③ B」                                                                                                   |
| 已有本地 MCP 服务  | `~/.workbuddy/mcp.json` 中服务已配置但 `disabled: true`，venv 完整                                | 连接器管理页启用即可绕开 uvx，见「③ C」                                                                                                  |
| 未启动/未打开图纸  | `Connection closed`、COM 初始化错误（-2147221008）                                              | 启动 ZWCAD 并打开 DWG，重启 MCP                                                                                                             |
| 机械工具失败       | `MECHANICAL_NOT_AVAILABLE` / `TYPELIB_NOT_LOADED`                                               | 调用 `zwcad_mech_diagnose` 获取逐项探测结果与修复建议；类型库加载机制与 `PYZWCADMECH_TLB_PATH` 配置详见 README「ZwmToolKit 类型库加载机制」 |
| 机械类型库解析失败 | `TYPELIB_NOT_LOADED`，`typelib_error` 含 `-2147312566`（`0x80029C4A`）「加载类型库/DLL 时出错」 | 按下方「机械类型库加载失败（-2147312566）的处置」分步处理，多数情况在第 1~3 步内解决                                                        |
| 首次拉取依赖失败   | `uvx` 下载慢、超时或网络错误                                                                    | 配置 `UV_DEFAULT_INDEX` 指向国内镜像（如 `https://pypi.tuna.tsinghua.edu.cn/simple`）后重启客户端                                           |
| 中文乱码           | `mbcs codec can't decode bytes`                                                                 | 确认使用本项目 server（`PYTHONUTF8=1`）并完全重启 WorkBuddy                                                                                 |
| 操作错窗口         | 多开时改到非预期图纸                                                                            | 关闭其他 ZWCAD 实例，仅保留目标产品后重连（单活动实例策略详见 README「重要说明」及上文「安全约束」）                                        |
| 实体找不到         | 返回空结果                                                                                      | 先用 `zwcad_get_objects_in_model` 确认真实 object_type/handle，再过滤                                                                       |
| 参数不匹配         | `缺少参数` 错误                                                                                 | 对照工具 description 补全必填字段；角度用弧度                                                                                               |
| 机械样式缺失       | 图框/标题栏操作报 XML 解析错误                                                                  | 用 `zwcad_get_app_info(scope="mech_style_path")` 查询本机实际样式路径并确认存在对应标准（GB 等）；路径与版本对应关系详见 README「重要说明」 |

> 工具返回的 `error` / `code` / `hint` 三字段是排障的权威信息；表中未覆盖的错误码同样按这三字段排查，并以工具 description 为准。

### 机械类型库加载失败的处置

**场景**：机械工具（图框/标题栏/明细表等）返回 `TYPELIB_NOT_LOADED`；`zwcad_mech_diagnose` 显示 `typelib_loaded: false`、`typelib_error` 含 `-2147312566`（`0x80029C4A`）「加载类型库/DLL 时出错」。按顺序处置：

1. **确认产品环境（多数在此解决）**：已装与 ZWCAD 版本匹配的中望机械、已完整启动并打开至少一张 DWG；近期卸载/升级/移动过组件的，以管理员身份执行**修复安装**，确保 `ZwmToolKit` 正确注册。
2. **核对类型库路径**：依赖 `ZwmToolKit.tlb`，默认在 `C:\Program Files\ZWSOFT\ZWCAD Mechanical <版本> Chs\Zwcadm\ZwmToolKit.tlb`；自动定位失败则把实际路径设为 `PYZWCADMECH_TLB_PATH` 并**完全重启 MCP 连接器**（须重建服务进程，仅重开客户端无效）。
3. **诊断与验证**：`zwcad_mech_diagnose` 复查 `typelib_loaded` / `typelib_source` / `typelib_error`。
4. **解析器容错（前 3 步仍失败时）**：comtypes 默认"一错即弃"——遇到个别无法从当前环境解析的引用就中止整份类型库加载，与产品功能无关：
   - **定位环境**：`wmic process` / 任务管理器确认 MCP **实际加载的 Python 环境路径**；`uvx` 启动时缓存目录可能并存**多个同名虚拟环境**，补丁与清缓存都必须落在 MCP 实际加载的那个，否则"改完重启仍失败"。
   - **打补丁**：该环境 `comtypes/tools/tlbparser.py` 中，把 `ParseInterface` / `ParseCoClass` 内读取基类类型的调用（`GetRefTypeOfImplType` / `GetRefTypeInfo`）包进 try/except，失败则告警跳过（**改前先备份**）。
   - **清缓存**：删除 `comtypes/gen` 下残留的 `_*.py` / `_*.pyc`，否则旧缓存被再次导入。若重生成时报 `mbcs codec can't decode bytes`，把同环境 `comtypes/tools/codegenerator/codegenerator.py` 生成文件头的编码声明由 `mbcs` 改为 `utf-8` 后重试。
   - **彻底重连**：断开→重连 MCP 重建进程。服务端会缓存首次加载失败状态，仅刷新客户端或重开应用不生效。
   - 此为运行环境级临时规避，升级 comtypes / 重装环境 / 换机后需重新应用。

---

## 最佳实践

- **修改优先于重建**：能用 `zwcad_transform_entity` / `zwcad_modify_entity` 就不删了重画。
- **单位与弧度**：坐标沿用当前图纸单位；角度一律弧度。
- **样式走 XML**：标准/标题栏/BOM/图框样式名来自本机 `styles/*.xml`，可用 `zwcad_mech_manage_*` 查询后使用。

> 探测先行、先查询后操作、写入需确认等约定已并入「工作流原则」与「进程与文档安全约束」，不再重复罗列；工具能力细节见 README「工具详细说明」。
