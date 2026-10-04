# workrally-canvas-organizer

WorkRally 无限画布自动整理工具。把凌乱的画布按素材类型（人物 / 场景 / 视频 / 散图等）分组到不同画板(artboard)，网格化排列。支持可选清理"散落的旧媒资节点"，**文字节点永远保留**。

> **MCP 版**：本 skill 全程使用 **WorkRally MCP 工具**，**不需要** `workrally` CLI、不需要 API Key。
> 本地脚本只做纯计算（分类 / 网格布局 / Y.js 解析），I/O 由 Agent 走 MCP 完成。

## 前置条件

- WorkBuddy 已连接 **WorkRally 连接器**（MCP server `workrally`）
- Python 3.8+（只用标准库）
- 画布必须已存在（skill 不会自动建画布）
- 画布 ID 来自链接 `https://workrally.qq.com/toolbox/canvas/<canvas_id>`

## 快速上手

### 常规整理（非破坏性）

```text
① Agent 拉素材（MCP）：
   asset_search(canvas_project_id=["<canvas_id>"],
                channel=["toolbox_canvas"],
                page_size=100, page=1)
   → 把返回原样落盘 /tmp/workrally/assets.json（超过 100 条要翻页合并）

② 本地生成布局：
   python3 scripts/organize_canvas.py \
     --canvas-id <canvas_id> \
     --assets /tmp/workrally/assets.json \
     --rules rules.example.json \
     --captions \
     --emit-args /tmp/workrally/build_args.json

③ Agent 写回画布（MCP，安全增量）：
   canvas_manage(action="build_draft",
                 canvas_id="<canvas_id>",
                 nodes=<build_args.json 里的 nodes>,
                 mode="merge")
```

### 整理后清理散落原节点（文字节点硬性保留）

```text
① Agent 取画布快照（MCP）：
   canvas_manage(action="get", canvas_id="<canvas_id>")
   → 把完整返回原样落盘 /tmp/workrally/canvas_snapshot.json

② 本地筛孤儿并出参数：
   python3 scripts/cleanup_orphans.py \
     --canvas /tmp/workrally/canvas_snapshot.json \
     --canvas-id <canvas_id> \
     --emit-delete-args /tmp/workrally/del_args.json

③ 目检清单后再由 Agent 执行（MCP）：
   canvas_manage(action="build_draft",
                 canvas_id="<canvas_id>",
                 delete_node_ids=<del_args.json 里的某一批>,
                 mode="merge")
```

## 🛡️ 安全保证（两条铁律）

1. **文字节点(text) 和画笔节点(freehand) 永远不会被删除** — `cleanup_orphans.py` 硬编码了白名单 `PROTECTED_TYPES = {'text', 'freehand', 'artboard', 'generator'}`，任何参数都无法绕过；执行前还有一次 defensive 检查，混入受保护类型立即中止。
2. **默认使用 merge 模式** — `canvas_manage(action="build_draft", mode="merge")` 增量合并，只新增/重排媒资素材到新画板中，不删除任何已有节点。

## 目录结构

```
workrally-canvas-organizer/
├── SKILL.md                         # Skill 主入口（Agent 读取）
├── README.md                        # 本文件
├── rules.example.json               # 规则示例
├── scripts/
│   ├── organize_canvas.py           # 纯本地：分类 + 网格布局 → 输出 build_draft 的 nodes
│   └── cleanup_orphans.py           # 纯本地：解析 draft_v1 → 输出待删 delete_node_ids
└── references/
    ├── classification-rules.md      # 分类规则详解
    └── layout-cheatsheet.md         # 布局尺寸速查
```

## 分类规则支持的匹配方式

- `asset_type` — 按素材类型（image/video/audio）
- `title_prefix` — 标题前缀
- `title_keywords` — 标题关键词
- `title_regex` — 正则匹配
- `and` / `or` — 组合条件
- `fallback` — 兜底组（必须放最后）

详见 [references/classification-rules.md](references/classification-rules.md)。

## 清理脚本工作原理

`cleanup_orphans.py` 通过以下步骤识别待清理的散落原媒资节点：

1. 读 Agent 用 MCP `canvas_manage(action="get")` 落盘的完整返回
2. 提取 `draft_v1` 字段（Y.js update 二进制，base64 编码）
3. 手写扫描器解析 Y.js 字段模式 `<name_len><name>\x01w<varint_len><value>`，提取所有节点的 id/type/parentId
4. 筛选 `type ∈ {image, video}` 且 `parentId` 为空的孤儿节点
5. **硬性排除** `type ∈ {text, freehand, artboard, generator}`
6. 分批（每批 ≤ 80）输出 `delete_node_ids`，交给 MCP `canvas_manage(action="build_draft")` 删除

删除前脚本会做一次 defensive 检查，若待删列表里混入了受保护类型则立即中止。

## 版本历史

- **v3.0.0（MCP 版）**：剥离全部 `workrally` CLI 调用，脚本改为纯本地计算（文件 in / 参数 out），I/O 由 Agent 通过 MCP `asset_search` / `canvas_manage` 完成。
- **v2.1.0**：新增 `cleanup_orphans.py`，支持整理后清理散落原节点，硬性保留所有文字/画笔节点。
- **v2.0.0**：初始版本，支持分类 + 网格布局 + merge 写入。
