---
name: pdb-viewer-skill
version: 1.0.0
description: 在 WorkBuddy 内置浏览器中以 3D 结构展示 PDB 文件，支持通过自然语言操控结构（高亮、隐藏链、测量距离等）。Mol* 5.9.0 本地自托管，支持本地文件和腾讯健康组学平台 COS 路径。
author: WorkBuddy
tags:
  [
    pdb,
    biology,
    3d,
    structure,
    mol*,
    viewer,
    omics,
    tencent-health,
    interactive,
    natural-language,
  ]
triggers:
  - 打开 pdb
  - 查看 pdb
  - 显示 pdb 结构
  - 可视化 pdb
  - 预览蛋白结构
  - 显示三维结构
  - 展示 3d 结构
  - pdb 浏览器
  - 蛋白结构
  - protein structure
  - pdb viewer
  - molstar
  - structure viewer
  - 3d protein
  - cos pdb
  - 腾讯健康组学平台 pdb
  - alphafold 结构
  - 蛋白质结构可视化
  - 查看 @*.pdb
  - 高亮残基
  - 隐藏链
  - 测量距离
  - 活性位点
  - 结合口袋
  - 突变位点
---

# pdb-viewer-skill

在 WorkBuddy 中以 **3D 交互式方式**展示 PDB/mmCIF 生物大分子结构文件，并支持通过**自然语言指令**实时操控场景。

底层使用 [Mol\* (molstar) 5.9.0](https://molstar.org/)，本地自托管（`templates/molstar.js` + `templates/molstar.css`）。COS 文件通过 **omics-platform-cli** 认证，调用 `CosBucketService.GetObjectData` 接口读取。

## 核心能力

| 类别           | 能力                         | 用户示例                          |
| -------------- | ---------------------------- | --------------------------------- |
| **数据加载**   | 本地 PDB / COS URI / RCSB ID | "打开 xxx.pdb"                    |
| **可视化控制** | 切换表示方式                 | "显示为球棍模型"                  |
|                | 着色方案                     | "按二级结构着色" / "全部设为蓝色" |
|                | 背景                         | "背景设为黑色"                    |
| **结构操作**   | 隐藏/显示链                  | "隐藏 B 链" / "显示所有链"        |
|                | 移除/恢复水分子              | "去掉水分子" / "显示水"           |
|                | 重置视图                     | "重置到默认状态"                  |
| **高亮标注**   | 区间高亮                     | "高亮 A 链 50-100 位残基"         |
|                | 离散残基高亮                 | "高亮突变位点 N501Y 的两个残基"   |
|                | 清除高亮                     | "清除所有高亮"                    |
| **测量分析**   | 距离测量                     | "测量 A 链 501 和 505 的 Cα 距离" |
|                | 清除测量                     | "删除所有测量线"                  |
| **动画与导出** | 自动旋转                     | "开始旋转" / "停止旋转"           |
|                | 截图                         | "截个图"                          |
|                | 保存 PDB                     | "保存当前结构"                    |
| **信息查询**   | 结构概要                     | "这个蛋白有什么信息"              |

## 架构

```
┌──────────────────────────────────────────────────────────────┐
│              WorkBuddy LLM (SKILL 编排层)                     │
│                                                              │
│  自然语言 → 命令映射 → HTTP POST /api/command                 │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│               serve_pdb.py (HTTP API + 静态文件服务)          │
│                                                              │
│  数据准备:  本地文件 /__file / COS /__cos → base64 JSON       │
│  命令路由:  POST /api/command → 入队 + SSE 推送               │
│  推送机制:  GET /api/events (SSE 实时推送到浏览器)             │
│  静态服务:  templates/viewer.html + molstar.js/css           │
│  心跳监控:  页面关闭 30s 后自动释放端口                        │
│  日志文件:  .pdb-viewer.log (SKILL_ROOT 绝对路径)             │
│              ★ [PUB-LOG-MARKER] 日志功能位置标记 ★            │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│   Mol* Viewer (WorkBuddy 内置浏览器)                          │
│                                                              │
│   Mol* 5.9.0（本地自托管，templates/molstar.js）              │
│   EventSource /api/events → 浏览器内 executeOp()             │
│   viewer.html                                                │
└──────────────────────────────────────────────────────────────┘
```

## 文件结构

```
pdb-viewer-skill/
├── SKILL.md                     # 本文件
├── templates/
│   ├── molstar.js              # Mol* 5.9.0 库（本地自托管）
│   ├── molstar.css             # Mol* 5.9.0 样式
│   ├── viewer.html             # ★ 唯一查看器（含完整 executeOp）
│   └── loading.html            # ★ 加载动画页（file:// 协议加载）
└── scripts/
    └── serve_pdb.py            # ★ HTTP 服务器（主入口）
                                #   ★ [PUB-LOG-MARKER] 日志代码位置 ★
```

## 前置依赖

### 必需：omics-platform-cli（仅 COS 场景）

本地 pdb 文件不需要 omics-platform-cli。只有访问 `cos://` 路径时才需要。

**安装方式**：

请前往 [omics-platform-cli 官方 Release 页面](https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases) 下载对应平台的二进制文件（`darwin-arm64` / `darwin-amd64` / `linux-amd64`），按页面说明完成安装。

**登录授权**：

```bash
omics login
# 自动打开浏览器完成平台授权（OAuth 流程）
# 登录态存储在 ~/.omics-platform-cli/auth.json
```

**验证**：

```bash
omics whoami
```

### 可选：Python 3

系统自带 Python 3 即可，`serve_pdb.py` 只用标准库（http.server / urllib / base64 / json 等），无需 pip 安装任何包。

## 使用方式

本 Skill 由 WorkBuddy (LLM) 自动调用，用户无需手动执行命令。

### 启动服务

```bash
# ★ SKILL_ROOT 必须使用实际安装路径，不能硬编码
# 获取方式（由 LLM 在运行时自动执行）：
#   - 用户级安装: <user-skill-dir>/pdb-viewer-skill
#   - 项目级安装: <project>/.workbuddy/skills/pdb-viewer-skill

# 方式 1: 后台启动（推荐，由 LLM 自动调用 run_in_background=true）
python3 {SKILL_ROOT}/scripts/serve_pdb.py \
  {SKILL_ROOT} \
  --pdb-file /abs/path/to/structure.pdb \
  --port 8789

# 方式 2: 仅启动服务（不指定默认 PDB，浏览器通过 ?pdb= 参数指定）
python3 {SKILL_ROOT}/scripts/serve_pdb.py \
  {SKILL_ROOT} \
  --port 8789
```

> **重要约束：`{SKILL_ROOT}` 是占位符，LLM 运行时必须替换为用户本机的实际安装路径。**

> **重要约束：只允许在 WorkBuddy 内置浏览器中打开，不允许主动打开用户本机浏览器。**

### 在 WorkBuddy 内置浏览器中打开

```python
present_files(files=["http://127.0.0.1:8789"])
# 或带 ?pdb= 参数
present_files(files=["http://127.0.0.1:8789?pdb=/abs/path/to/protein.pdb"])
```

### 通过 HTTP API 控制（自然语言操作）

服务启动后，通过 POST `/api/command` 发送命令，SSE 实时推送到浏览器执行：

```bash
# 高亮 A 链 50-100 位残基
curl -X POST http://localhost:8789/api/command \
  -H "Content-Type: application/json" \
  -d '{"op": "highlight_range", "params": {"chain": "A", "start": 50, "end": 100}}'

# 切换表示方式
curl -X POST http://localhost:8789/api/command \
  -H "Content-Type: application/json" \
  -d '{"op": "set_repr", "params": {"repr": "ball-and-stick"}}'

# 隐藏 B 链
curl -X POST http://localhost:8789/api/command \
  -H "Content-Type: application/json" \
  -d '{"op": "chain_visibility", "params": {"chain": "B", "visible": false}}'

# 获取结构信息
curl http://localhost:8789/api/status
```

## API 操作列表

### 数据加载

| `op`                         | 参数                          | 说明                                                       |
| ---------------------------- | ----------------------------- | ---------------------------------------------------------- |
| `get_pdb`                    | `id`/`pdb` (str), `url` (str) | 从 RCSB ID / URL / 本地路径加载 PDB                        |
| **[PUB-LOG-MARKER]** preload | `uri` (str)                   | **预加载 PDB 到服务端缓存（发布前删除此 API 和相关代码）** |

### 可视化控制

| `op`        | 参数             | 说明                                                                               |
| ----------- | ---------------- | ---------------------------------------------------------------------------------- |
| `set_repr`  | `repr` (str)     | cartoon / ball-and-stick / spacefill / gaussian-surface / putty                    |
| `set_color` | `theme` (str)    | chain-id / element-symbol / secondary-structure / b-factor / uniform (+ value hex) |
| `set_bg`    | `color` (str)    | CSS 颜色名或 hex                                                                   |
| `set_water` | `visible` (bool) | 水分子显隐                                                                         |

### 结构操作

| `op`               | 参数                            | 说明                         |
| ------------------ | ------------------------------- | ---------------------------- |
| `chain_visibility` | `chain` (str), `visible` (bool) | 链可见性                     |
| `focus_chain`      | `chain` (str)                   | 聚焦到链（当前为全结构重置） |
| `reset_view`       | —                               | 重置视角                     |

### 高亮与标注

| `op`               | 参数                                    | 说明         |
| ------------------ | --------------------------------------- | ------------ |
| `highlight_range`  | `chain`, `start`, `end`, `color`        | 区间高亮残基 |
| `highlight_list`   | `chain`, `residues`(list[int]), `color` | 离散残基高亮 |
| `clear_highlights` | —                                       | 清除所有高亮 |

### 测量

| `op`                 | 参数                               | 说明         |
| -------------------- | ---------------------------------- | ------------ |
| `measure_dist`       | `chain1`, `res1`, `chain2`, `res2` | Cα 距离测量  |
| `clear_measurements` | —                                  | 清除所有测量 |

### 动画与导出

| `op`           | 参数                                                              | 说明                                |
| -------------- | ----------------------------------------------------------------- | ----------------------------------- |
| `spin`         | `active` (bool), `speed` (number)                                 | 自动旋转 ON/OFF                     |
| `screenshot`   | —                                                                 | 浏览器下载 PNG                      |
| `record_video` | —                                                                 | 占位提示（引导使用 Mol\* 内置录制） |
| `save_pdb`     | `confirm_required` (bool), `confirmed` (bool), `path` (str, 可选) | 保存 PDB（需确认弹窗）              |

### 信息

| `op`       | 参数 | 说明                   |
| ---------- | ---- | ---------------------- |
| `get_info` | —    | 返回链数/残基数/原子数 |

### 日志相关 API（发布前删除）

| 路由              | 方法 | 说明                      | 删除标记             |
| ----------------- | ---- | ------------------------- | -------------------- |
| `/api/log`        | POST | 前端执行日志写入          | **[DEL-BEFORE-PUB]** |
| `/api/logs`       | GET  | 执行日志读取              | **[DEL-BEFORE-PUB]** |
| `.pdb-viewer.log` | 文件 | 日志文件存储位置          | **[DEL-BEFORE-PUB]** |
| `log_message()`   | 方法 | HTTP Handler 日志写入方法 | **[DEL-BEFORE-PUB]** |
| `_exec_logs`      | 变量 | 内存日志队列              | **[DEL-BEFORE-PUB]** |

## 腾讯健康组学平台 COS 支持

### 路径格式

```
cos://<bucket>/[<region>/]<key.pdb>
```

- region 可省略，脚本通过 region 白名单自动识别（非 region 字符串的路径段均视为 key 的一部分）
- key 必须以 `.pdb` 结尾（服务端校验）

### 完整工作流

```
viewer.html (?pdb=cos://...)
    ↓ fetch /__cos?uri=cos://bucket/[region/]key
serve_pdb.py /__cos 路由
    ↓ 1. 检查 omics CLI 是否安装 (~/.local/bin/omics)
    ↓ 2. 读取 ~/.omics-platform-cli/auth.json 中 session_id
    ↓ 3. 读取 ~/.omics-platform-cli/omics_config.json 中 EnvironmentId
    ↓ 4. 解析 cos:// URI → bucket + key (region 丢弃)
    ↓ 5. POST https://omics.qq.com/omics/api/cgi?method=CosBucketService.GetObjectData
         body: JSON-RPC 2.0 {jsonrpc, id, method, params: {EnvironmentId, Bucket, Key}}
         headers: Cookie: omics_session=<session_id>
    ↓ 6. 返回 JSON: {"data":"<base64>", "name":"xxx.pdb"}
viewer.html
    ↓ atob(data) → pdbText
    ↓ loadStructure(plugin, pdbText, 'pdb', name)
```

### 权限范围（严格限制）

pdb-viewer-skill 只调用以下一个接口，**不做其他任何操作**：

| 接口                                                     | 用途                                                                                                 |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `POST /omics/api/cgi` (`CosBucketService.GetObjectData`) | 读取指定 COS bucket/key 下的 pdb 文件内容，session_id 作为用户身份鉴权，EnvironmentId 指定环境上下文 |

**不允许通过此 SKILL 调用 omics-platform-cli 的其他命令**（如 run/status/debug 等）。

### 环境配置

环境 ID（`EnvironmentId`）从 `~/.omics-platform-cli/omics_config.json` 中的 `EnvironmentId` 字段读取，与 omics-platform-cli 的环境配置保持一致。

已连接**正式环境**（`https://omics.qq.com`）。

## LLM 行为约定（核心！）

### Step 1: 启动服务并拉起内置浏览器（file:// + http 两步法）

#### 1.1 端口策略

固定使用端口 **8789**（已验证代理可访问）。

#### 1.2 ★ WorkBuddy 内置浏览器面板行为规律（必读）

present_files 是否真正 GET，取决于**面板当前显示的协议**：

| 面板当前协议           | present_files 目标     | 行为                   |
| ---------------------- | ---------------------- | ---------------------- |
| `file://`（或空白）    | `http://127.0.0.1/...` | ✅ 真正 GET，完整加载  |
| `http://127.0.0.1/...` | `http://127.0.0.1/...` | ❌ 只发 HEAD，面板不动 |

> 面板一旦加载过 localhost URL，对后续所有 localhost URL 的 present_files 都只发 HEAD，**不管 URL 是否不同、服务是否重启**。唯一出路：先用 `file://` 协议切出来。

#### 1.3 ★ 核心流程：pdb_jump 直接触发协议切换

**每次打开新结构，统一走以下流程**（不杀旧服务，pdb_jump.html 同时承担协议切换 + 跳转两个角色）：

```
┌─ Step A: 启动服务（后台）────────────────────────────────────┐
│  python3 serve_pdb.py SKILL_ROOT --port 8789 --no-watchdog   │
│  等待 /__healthz 返回 session_id（最多轮询 10s）              │
└───────────────────────────────────────────────────────────────┘
         ↓
┌─ Step B: 预加载 PDB 数据到服务端缓存 ────────────────────────┐
│  POST /api/preload {"uri":"<pdb_path_or_cos_uri>"}           │
│  服务端提前读取 PDB 文件，浏览器打开时直接命中缓存             │
└───────────────────────────────────────────────────────────────┘
         ↓
┌─ Step C: 清理旧跳板 + present_files pdb_jump.html ───────────┐
│  rm -f /tmp/pdb_jump_*.html  （清理旧跳板文件）               │
│  生成含 <meta http-equiv="refresh" content="0;url=..."> 的 HTML │
│  present_files(["/tmp/pdb_jump_<ts>.html"])                  │
│  ★ 面板若在 http:// → 先切到 file://（加载 pdb_jump）        │
│  ★ meta-refresh 立刻触发 file:// → http:// 跳转              │
│  ★ 面板若在 file://（或空白）→ 同样直接跳转到 http://         │
│  服务端收到真正 GET，viewer.html 完整加载 ✅                  │
└───────────────────────────────────────────────────────────────┘
         ↓ Mol* 开始初始化（通常 5~10 秒）
┌─ Step D: 浏览器就绪后自动触发 get_pdb ───────────────────────┐
│  viewer.html SSE onopen / 轮询首次成功 时，自动 POST /api/ready │
│  服务端收到后，若有预加载缓存则立即推送 get_pdb 命令 ✅        │
│  ★ 无需 LLM sleep 等待，就绪即加载                           │
└───────────────────────────────────────────────────────────────┘
```

> ⚠️ **关键约束（已验证）**：
>
> - `present_files(本地文件)` 无论面板当前是 `http://` 还是 `file://`，都会真正导航到 `file://` ✅
> - 面板在 `http://` 时，`present_files(http://...)` 只发 HEAD 不导航 ❌ → 必须借助本地文件中转
> - 必须用 `<meta http-equiv="refresh">` 而非 JS `location.replace()`，meta-refresh 是浏览器级导航，不受 CSP 限制
> - **不再需要先杀旧服务**：新服务直接启动，旧服务会在端口冲突时自动失败或被替代
> - `loading.html` 已从默认流程移除；如需过渡动画，可手动在 Step B 之前插入

#### 1.4 完整流程代码

```python
import time
import os

# ── ★ 动态获取 SKILL_ROOT（必读）─────────────────────────────
# 优先级：用户级安装 > 项目级安装
_user_skill = os.path.expanduser("<user-skill-dir>/pdb-viewer-skill")
_project_skill = os.path.join(os.environ.get("PROJECT_ROOT", "."), ".workbuddy/skills/pdb-viewer-skill")

if os.path.isdir(_user_skill):
    SKILL_ROOT = _user_skill
elif os.path.isdir(_project_skill):
    SKILL_ROOT = os.path.abspath(_project_skill):
else:
    raise FileNotFoundError("找不到 pdb-viewer-skill 安装位置，请先安装该 Skill")
# ─────────────────────────────────────────────────────────────

PORT = 8789
pdb_path = "/abs/path/to/structure.pdb"

# ── Step A: 启动服务（不杀旧进程）──
# [Bash, run_in_background=true]:
#   python3 {SKILL_ROOT}/scripts/serve_pdb.py {SKILL_ROOT} --port {PORT} --no-watchdog

# 等待服务就绪（轮询 /__healthz，最多 10s）
# [Bash]:
#   for i in $(seq 1 20); do
#     result=$(no_proxy='*' curl -s http://127.0.0.1:8789/__healthz)
#     if echo "$result" | grep -q "session_id"; then echo "READY: $result"; break; fi
#     sleep 0.5
#   done

# ── Step B: 预加载 PDB 数据到服务端缓存 ────────────────────────
# [Bash]: no_proxy='*' curl -s -X POST http://127.0.0.1:{PORT}/api/preload \
#   -H "Content-Type: application/json" \
#   -d '{{"uri":"{pdb_path}"}}'

# ── Step C: 清理旧跳板文件 + 通过 meta-refresh 跳转到 http viewer ──
# ★ pdb_jump.html 同时承担两个角色：
#   1. 作为本地文件，把面板从 http:// 切到 file://（如面板已在 http:// 状态）
#   2. meta-refresh 立刻从 file:// 跳回 http://，服务端收到真正 GET ✅
# [Bash]: rm -f /tmp/pdb_jump_*.html
TS = int(time.time())
jump_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0;url=http://127.0.0.1:{PORT}/view/{TS}">
<title>正在打开...</title>
<style>body{{background:#1a1d24;color:#7fd97f;font-family:monospace;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}</style>
</head><body><p>正在打开 PDB 查看器...</p></body></html>"""
# [Write /tmp/pdb_jump_{TS}.html]: jump_html
# [present_files]: [f"/tmp/pdb_jump_{TS}.html"]
# 面板从任意状态 → file:// → 立刻跳转到 http://127.0.0.1:{PORT}/view/{TS} ✅

# ── Step D: 浏览器就绪后自动触发（无需 LLM 主动等待）──────────
# ★ viewer.html 在 SSE onopen / 轮询首次成功时，自动 POST /api/ready
# ★ 服务端收到 /api/ready 后，若有预加载缓存则立即推送 get_pdb 命令
# ★ LLM 无需再 sleep 30 等待，整个流程至此结束
```

#### 1.5 loading.html 的定位（备用）

`templates/loading.html` 已从默认流程中移除，文件保留备用。

- 默认流程中，`pdb_jump.html` 同时承担协议切换 + 跳转，用户感知到的是"瞬间切换"
- 如需在跳转前展示过渡动画，可在 Step B（preload）之前手动插入：
  ```
  present_files(["{SKILL_ROOT}/templates/loading.html"])
  sleep <N>   # 根据需要设置展示时长
  ```
- ⚠️ loading.html 内的 JS 轮询逻辑在 `file://` 下**会被 Electron CSP 阻止**，JS 不会执行，但动画仍正常展示

#### 1.6 空闲超时

服务默认 **600 秒（10 分钟）无任何 API 调用**后自动退出，释放端口。
可通过 `--idle-timeout=0` 禁用，或 `--idle-timeout=300` 调整为 5 分钟。

### Step 2: 映射自然语言 → API 操作

| 用户意图                  | `op`                   | 示例参数                                          |
| ------------------------- | ---------------------- | ------------------------------------------------- |
| "打开 X.pdb"              | `get_pdb`              | url=本地绝对路径 或 id=RCSB_ID                    |
| "从 RCSB 加载 Y"          | `get_pdb`              | id=Y (PDB ID)                                     |
| "隐藏 X 链"               | `chain_visibility`     | chain=X, visible=false                            |
| "只看 A 链"               | `chain_visibility` × N | 逐一隐藏其他链                                    |
| "去掉水"                  | `set_water`            | visible=false                                     |
| "高亮 X 链 N-M 位"        | `highlight_range`      | chain=X, start=N, end=M                           |
| "高亮这些残基 [N,M,K...]" | `highlight_list`       | residues=[N,M,K], chain=X                         |
| "设为球棍模型"            | `set_repr`             | repr=ball-and-stick                               |
| "设为表面模式"            | `set_repr`             | repr=gaussian-surface                             |
| "全部染成红色"            | `set_color`            | theme=uniform, value="#ff0000"                    |
| "按链着色"                | `set_color`            | theme=chain-id                                    |
| "测一下 X 和 Y 的距离"    | `measure_dist`         | 根据上下文推断 chain/residue                      |
| "清除测量线"              | `clear_measurements`   | —                                                 |
| "截个图"                  | `screenshot`           | —                                                 |
| "保存当前结构"            | `save_pdb`             | confirmed=true（先发 confirm_required=true 弹窗） |
| "这个结构有什么信息"      | `get_info`             | —                                                 |
| "重置"                    | `reset_view`           | —                                                 |

### Step 3: 执行操作并反馈

1. 发送 HTTP POST `/api/command` → `{ "op": "...", "params": {...} }`
2. 命令通过 **SSE 实时推送**到浏览器（无需轮询）
3. 浏览器端 `executeOp()` 执行并更新 UI
4. 向用户反馈执行结果

### Step 4: 处理多步骤请求

对于复合指令（如 "打开 X.pdb 并高亮活性位点，隐藏配体"），按以下顺序：

1. 先加载数据（`get_pdb`）
2. 再获取 `get_info`（了解链和残基）
3. 逐个发送操作命令（SSE 即时推送，每个命令自动刷新 UI）
4. 展示结果

### 重要约束

1. **必须先加载结构才能执行其他操作**
2. 使用 `get_info` 命令获取链信息后再做链级操作
3. 残基编号需要从 `get_info` 结果中确认
4. `set_repr` 的 repr 参数使用 kebab-case（如 `ball-and-stick`），不是 snake_case
5. 如果命令失败，向用户报告错误原因并建议修正
6. **只允许在 WorkBuddy 内置浏览器中打开，不允许主动打开用户本机浏览器**
7. **日志文件位置标记：搜索 `[DEL-BEFORE-PUB]` 可快速找到所有需删除的日志相关代码**
8. **浏览器页面默认不显示命令日志面板**；调试时在 URL 追加 `?debug=1` 可开启

### save_pdb 特殊说明

**save_pdb 操作支持两种模式：**

#### 模式 A: 覆盖已有文件（本地文件加载时）

```bash
# Step 1: 请求用户确认
POST /api/command {"op": "save_pdb", "params": {"confirm_required": true}}

# Step 2: 用户确认后执行（自动备份原文件为 .bak）
POST /api/command {"op": "save_pdb", "params": {"confirmed": true}}
```

#### 模式 B: 保存到指定路径（URL/COS 加载时，或另存为）

当从 RCSB URL 或 COS 加载 PDB 后，原始文件不在本地，需要用户提供保存路径：

```bash
# Step 1: 设置保存路径 + 请求确认
POST /api/command {
  "op": "save_pdb",
  "params": {
    "confirm_required": true,
    "path": "/tmp/my-structure.pdb"
  }
}

# Step 2: 用户确认后执行
POST /api/command {"op": "save_pdb", "params": {"confirmed": true}}
```

**LLM 行为规范：**

- 如果 PDB 是从**本地文件**加载的，直接执行两步确认即可
- 如果 PDB 是从 **URL/RCSB/COS** 加载的，**必须先询问用户要保存到哪里**，并将路径放入 `path` 参数

## 关键 API 陷阱

**molstar 5.x 必须用 `molstar.Viewer.create(...).then(viewer => {...})`，绝不能用 `new molstar.Viewer(...)`。**

详见注释。参考: <https://github.com/molstar/molstar/issues/631>

## 浏览器面板

- 通过 `present_files(files=["http://127.0.0.1:8789"])` 打开
- 鼠标操作：左键旋转、右键平移、滚轮缩放
- 左侧面板可切换 cartoon / ball-and-stick / surface 等表示
- 调试日志：URL 追加 `?debug=1` 显示命令执行面板

## 安全与隔离

- 服务器仅绑定 `127.0.0.1`，不暴露到局域网
- session_id 仅用于调用 `CosBucketService.GetObjectData`，不通过 HTTP 暴露给浏览器
- Mol\* 库本地自托管，无 CDN 依赖

## 发布前清理清单（重要！）

在将此 Skill 发布给其他用户前，**必须完成以下清理工作**：

### 日志功能删除（搜索 `[DEL-BEFORE-PUB]` 标记）

| 序号 | 文件           | 删除内容                                            | 标记位置           |
| ---- | -------------- | --------------------------------------------------- | ------------------ |
| 1    | `serve_pdb.py` | `LOG_FILE` 常量定义 (~line 70)                      | `[DEL-BEFORE-PUB]` |
| 2    | `serve_pdb.py` | `log_message()` 方法 (~line 312-321)                | `[DEL-BEFORE-PUB]` |
| 3    | `serve_pdb.py` | `_exec_logs` 变量及相关锁 (~line 120-122)           | `[DEL-BEFORE-PUB]` |
| 4    | `serve_pdb.py` | `/api/log` POST 路由处理 (~line 812-827)            | `[DEL-BEFORE-PUB]` |
| 5    | `serve_pdb.py` | `/api/logs` GET 路由处理 (~line 667-670)            | `[DEL-BEFORE-PUB]` |
| 6    | `serve_pdb.py` | `_preloaded_pdb` 相关代码（可选，preload 缓存机制） | `[PUB-LOG-MARKER]` |
| 7    | `SKILL.md`     | 本清单章节（发布后删除整个"发布前清理清单"章节）    | —                  |

### 清理验证

删除完成后：

1. 全局搜索 `DEL-BEFORE-PUB` 和 `PUB-LOG-MARKER`，确保无残留
2. 启动服务，确认无 `.pdb-viewer.log` 文件创建
3. 访问 `/api/log` 和 `/api/logs`，应返回 404
4. 功能测试：加载 PDB、执行命令等核心流程正常

## 常见问题

**Q: COS PDB 加载失败，提示 "omics-platform-cli 未安装"。**
A: 请前往 [omics-platform-cli 官方 Release 页面](https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/releases) 下载并安装对应平台的二进制文件，安装完成后重试。

**Q: COS PDB 加载失败，提示 "未检测到 omics 登录凭证" 或 "已过期"。**
A: 执行 `omics login` 完成登录授权，然后重试。

**Q: COS PDB 加载失败，提示 "GetObjectData 失败"。**
A: 可能原因：

1. bucket/key 不存在
2. 当前用户没有该 bucket 的访问权限
3. EnvironmentId 配置错误或未配置（执行 `omics config set` 检查）
4. 服务端尚未将 GetObjectData 开放到外部路由

**Q: 浏览器打开后显示 "未指定 PDB 文件"。**
A: 启动服务时未通过 `--pdb-file` 指定默认文件，也未在 URL 中带 `?pdb=` 参数。使用 `get_pdb` 命令加载文件，或重启服务时指定 `--pdb-file`。

**Q: 想换 Mol\* 版本怎么办？**
A: 下载新版 `molstar.js` 和 `molstar.css` 替换 `templates/` 下的文件，同时更新本 SKILL.md 版本号。

**Q: 如何确认 SKILL_ROOT 是否正确？**
A: 在运行时查看 LLM 日志，应该能看到类似输出：

```
[pdb-viewer] serving /Users/<user>/.workbuddy/skills/pdb-viewer-skill at http://127.0.0.1:8789
```

如果报错 `找不到 pdb-viewer-skill 安装位置`，说明 Skill 未正确安装到预期路径。
