---
name: modao-ai
display_name: 墨刀AI
display_name_en: Modao AI
description: Generate PRDs, HTML prototypes, React/Vue apps and images with Modao AI, iterate on existing generation tasks, and read, import or export Modao prototype canvases. Use when the user asks for 墨刀/墨刀AI/Modao, a PRD, 原型/prototype, 高保真界面, React or Vue app scaffolding, or wants to look up, export or re-import an existing Modao prototype or task.
description_zh: 用墨刀AI在对话内生成 PRD、HTML 原型、React/Vue 应用与图片，继续迭代已有生成任务，并读取、导入、导出墨刀原型画布。
description_en: Generate PRDs, HTML prototypes, React/Vue apps and images with Modao AI, continue existing generation tasks, and read, import or export Modao prototype canvases.
category: 开发工具
version: 1.0.0
author: 墨刀
---

# 墨刀AI 连接器使用说明

墨刀AI 是「生成 + 沉淀」链路：本连接器在对话里创建内容，产物保存在用户的墨刀工作台空间。
**`generate*` 是付费生成操作**，消耗用户账号积分。未经用户明确需求，不得调用。

## 0. 所有调用的公共约定

- **每个工具都有可选参数 `client`，调用时填 `"WorkBuddy"`**。服务端用它做来源识别；不填会回退到 initialize 的 clientInfo.name。
- **失败即停。** 任何工具返回失败或异常时：**禁止**自动重试、**禁止**自动调用 `continue_task`、**禁止**改用 `generate` / `generate_*` 新建任务。必须把错误原文展示给用户，只有用户明确要求后才能再次调用。
- 所有路由都走令牌绑定的**墨刀工作台空间**，不能切换空间。接口文档与返回值里把它叫作「默认个人空间」，同一个东西。

## 1. 何时使用

使用：PRD / 需求文档、页面与高保真原型、React 或 Vue 应用、海报与配图、查看/继续/导出用户已有的墨刀任务与原型。

不要使用：纯概念咨询无产出、修改用户本地代码仓库、把 React / Vue 工程导入墨刀原型（不支持）。

## 2. 前置自检

首次连接或用户报异常时，先调 `get_account_status`（只读，不扣积分）确认账号、工作台空间、积分状态。
积分不足直接告知用户去 https://modao.cc/ai 查看，**不要重试生成**。

## 3. 工具与参数

> 参数均为可选除标注 ★。生成类工具的语义输入优先用 `query`（自然语言需求），需要结构化补充时用 `user_input`，参考素材用 `reference`。

### 3.1 内容生成（6，消耗积分）

| 工具 | 用途 | 参数 |
|---|---|---|
| `generate_prd` | PRD / 需求文档 / 功能说明 / 验收标准 | `query`、`user_input`、`reference`、`client` |
| `generate_html` | HTML 页面、静态页、高保真原型（未指定技术栈时用这个） | 同上 |
| `generate_react` | **仅**用户明确要 React 技术栈时 | 同上 |
| `generate_vue` | **仅**用户明确要 Vue / Vue3 时 | 同上 |
| `generate_image` | 海报、插图、配图、商品图；返回图片链接，不产出可交互页面 | 同上 |
| `generate` | 无法归入以上五类的需求 | 同上 |

选择原则：**能明确归类就用专用工具，不要图省事用 `generate`**。已有任务要改 → `continue_task`，不要重新 `generate_*`。

### 3.2 任务与交付（5）

| 工具 | 用途 | 参数 |
|---|---|---|
| `list_recent_tasks` | 查工作台空间最近 10 条（最多 20）任务，按名称筛选 | `limit`(int,默认10)、`keyword`、`client` |
| `get_task_result` | 按 ID 查状态、任务链接、预览链接、错误、产物（只读，可重复调） | `task_id`★、`client` |
| `continue_task` | 继续/修改/重试/恢复已有任务 | `task_id`★、`query`、`user_input`、`modification_context`、`client` |
| `paused_task` | 暂停或取消任务 | `task_id`★、`client` |
| `download_generated_content` | 取产物下载链接 | `task_id`★、`client` |

### 3.3 原型读取与导出（5）

| 工具 | 用途 | 参数 |
|---|---|---|
| `list_created_prototypes` | 查本人创建的 proto2 原型，按最近更新排序，默认 10 条最多 20 | `project_name`、`space_name`、`org_name`、`limit`(int,默认10)、`client` |
| `get_proto_details` | 读原型页面/画布目录；传 `target_key` 读布局、尺寸、文字、组件、交互（只读） | `project_cid`★、`target_key`、`client` |
| `import_to_proto` | 把 HTML 导入成可继续编辑的墨刀原型 | `task_id`、`task_url`、`html`、`html_list`、`page_name`、`client` |
| `export_proto_to_html` | 已有任务关联的原型 → HTML 下载链接 | `project_url`★（完整链接 `/proto/design/{project_id}`）、`client` |
| `export_proto_to_png` | 指定画布导出 PNG，返回链接及有效期 | `project_cid`★、`canvas_key`★、`client` |

### 3.4 账号

`get_account_status` — `client`。查账号、默认空间、积分。只读。

## 4. 标准调用链

**A. 生成 HTML 原型 → 导入为可编辑墨刀原型（最常用）**
`generate_html` → 拿 `task_id` → `get_task_result` 确认完成 → `import_to_proto`（传 `task_id`）→ 把返回的 `prototype_url` 交给用户。

**B. 生成 React / Vue 应用**
`generate_react` / `generate_vue` → `get_task_result` → 给预览链接与产物。
**不要**尝试 `import_to_proto`。若用户要求导入，说明限制并让用户决定，**不得自行 `generate_html` 转成 HTML**（那是付费操作，需用户明确同意）。

**C. 生成 PRD**
`generate_prd` → `get_task_result` → 返回文档内容与任务链接。

**D. 读取并导出已有原型**
`list_created_prototypes` 定位（**展示表格必须带更新时间列**）→ `get_proto_details` 取 `project_cid` 与目录 → 传 `target_key` 确认目标页面 → `export_proto_to_png`（`project_cid` + `canvas_key`）。
导出链接**有有效期**，必须把有效期一并告诉用户。

## 5. 异步任务处理（最容易出错）

`generate*` 单次调用最多等 **100 秒**：

- 返回 `running` + `task_id` → 任务**已创建**，只是还没生成完。
- **绝对不要**因为没拿到结果就重新 `generate_*`，会重复扣积分。
- 告知用户任务已创建，用 `get_task_result` 后续查询。同一轮对话最多再查 1–2 次，仍 `running` 就把 `task_id` 交给用户收尾。
- `continue_task` **不能**用于运行中的任务。用户要求立即改，先 `paused_task`，等状态变 `paused` 再 `continue_task`。
- `continue_task` 对**已完成**任务必须传 `query` 或 `user_input`，否则无修改内容。

## 6. 错误与恢复

| 现象 | 判断 | 处理 |
|---|---|---|
| 401 / Token 无效 | 令牌被删、撤销、复制不全、带空格 | 让用户去墨刀「令牌设置」重建，在连接器表单里重填 |
| 积分不足 | 账号权益问题，不是连接问题 | 引导用户去 https://modao.cc/ai，不重试生成 |
| 任务 `failed` | 生成失败 | 展示错误，经用户同意后 `continue_task` 重试 |
| 任务 `paused` | 已暂停 | 经用户确认后 `continue_task` 恢复 |
| 参数校验错误 | 参数名/类型不符 | 按 schema 修正重试一次，不盲重试 |
| 无可用任务 | 账号从没在墨刀AI 里生成过 | 提示用户先在墨刀AI 对话一次，再 `import_to_proto` |
| 找不到原型 | 只返回本人创建的项目 | 让用户提供项目链接或确认所属空间 |

## 7. 必须向用户确认的操作

- `paused_task`：**只有用户明确说"停/取消/别做了"** 才可调用，不得因任务太久自行暂停。
- `import_to_proto`、`continue_task`：写入用户工作台空间。用户没明确要求"导入""继续改"时不要调。
- `download_generated_content`、`export_proto_to_*`：链接**只交给用户**。客户端不得自行访问、验证、代下载或换其他方式取文件；链接需用户在已登录墨刀账号的浏览器打开。
- 批量生成（≥3 个任务）或明显消耗较多积分前，先说明范围再执行。

## 8. 已知边界

- `import_to_proto` 只吃 HTML 文本、`html_list=[{name, html}]` 或已完成任务的 HTML；**不支持** React / Vue 工程、外部 URL、指定其他空间。
- 所有调用归属令牌绑定的工作台空间。
- 产物保存在墨刀，本连接器不产出本地文件。

## 9. 输出规范

- 交付给三样：产物在哪（`task_id` / `prototype_url` / 任务链接）、能干什么（预览 / 继续改 / 导出）、一句下一步建议。
- 图片、PNG、HTML 导出给链接 + 有效期提醒。
- 默认给入口，不要把完整 HTML 源码或 PRD 全文糊进对话，除非用户明确要求。
- `list_created_prototypes` 的结果用表格展示时，必须包含更新时间列。
