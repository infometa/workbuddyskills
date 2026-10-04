---
name: tapnow-tools
description: TapNow 创意工作室工具总览与使用方法——资产检索（素材库/画布项目）、图片进出（上传/入库）与视觉制作（配图套件/电商组图/精品单图），含任务单轮询节奏与降级路径。
version: "0.1.0"
author: "TapNow"
---

# TapNow Creative Studio Skill

本 Skill 说明 TapNow Connector 提供的 MCP 工具与使用方法。制作类工具走**任务单模式**：提交秒回 `node_ids` + `project_id`，用 `get_production_result` 轮询取回成品。

## 工具总览

| 工具 | 类型 | 用途 |
| -- | -- | -- |
| `find_library_assets` / `find_library_folders` | 免费 | 检索用户素材库（个人/团队） |
| `list_visual_projects` | 免费 | 列出画布项目（`project_id` / 名称 / 更新时间），用于接续既有创作 |
| `upload_image` | 免费 | 公网 HTTPS 图片 URL → `image_id`；**用户给图的唯一入口** |
| `save_to_library` | 免费 | 把画布上的图存进个人素材库，供长期复用 |
| `create_hero_image` | 计费·任务单 | 单张高质量图；`model` 取 `fast`（默认）/`quality`/`artistic`，`aspect_ratio` 取 7 个比例之一 |
| `create_product_shots` | 计费·任务单 | 一张产品原图 → 白底/场景/多角度/细节全套商品图，按 `platform` 出画幅 |
| `create_deck_visuals` | 计费·任务单 | 大纲 → 整套风格统一配图；`purpose: deck`（章节配图）或 `b2b`（商务组图） |
| `get_production_result` | 免费 | 按 `node_ids` + `project_id` 轮询进度，完成后返回可渲染的 `image_url` |

## 使用规则

1. **路由**：单张 → `create_hero_image`；3 张以上同风格 → 成套工具（更统一、总价更省）；商品图 → `create_product_shots`。

2. **图片进来必须过 `upload_image`**：制作工具的参考图参数（`product_image_id` / `style_ref_image_id`）**只接受 `image_id`，不接受任何 URL**，包括素材库返回的 `source_url`。链路是 `URL → upload_image → image_id + project_id → 制作工具`。
   **`create_hero_image` 没有参考图参数**——用户要照着图出，走 `create_product_shots` 或 `create_deck_visuals`。

3. **任务单节奏**：制作工具返回的是任务单，成品尚未生成——**不要在提交成功时说"已生成"**，正确话术是"正在制作中，预计 X 秒"。每 15-30 秒轮询一次 `get_production_result`，**必须同时传 `node_ids` 和 `project_id`**（漏传会返回 `not_found`，成品取不回来）。`items[].status=done` 的条目才有 `image_url`（约 7 天有效）；已完成的先展示。

4. **`failed` 是终态**：顶层 `status=failed` 或 `failed_node_ids` 列出的条目不会再恢复，**立刻停止轮询**，如实转述并询问是否重做。`not_found` 同样不要继续轮询，先核对 `project_id`。

5. **产出去向**：成品沉淀在 TapNow 画布项目，**不进素材库**——不要用素材库检索找刚生成的图。用户要长期保留就调 `save_to_library(image_ids=node_ids, project_id=…)`。

6. **回流链接**：返回里带 `project_url` 时就给用户——`upload_image` 成功后给一次（让他确认图确实进了 TapNow）、制作工具提交后给一次（等待期可自行查看绘制过程）、全部完成后再给一次（引导回 TapNow 深度编辑）。该字段可能缺席，缺席时不要编造链接。

7. **返回值里没有的东西，不要编造**：没有 `job_id`（任务单号就是 `node_ids`）、没有进度百分比、没有实际消耗金额。

8. **素材库呈现**：以文字盘点为主——最多渲染 1-3 张代表性图片，其余用「名称（类型）+ 链接」逐条列出；视频/音频/文本一律给链接不渲染；超过 20 条只列前 10-15 条并提示可用关键词精确查找。

9. **降级**：素材库为空 → 引导用户直接给图片链接走 `upload_image`；余额不足（`status=blocked`）→ 告知差额，给"缩小范围"或"去 TapNow 充值"两个选项。

10. 授权失效（401）→ WorkBuddy 会自动刷新或重新拉起 TapNow 授权，提示用户在弹出的浏览器页面完成登录即可，不需要手填任何 Token。

## 交付约定

所有结果以文字 + 图片链接返回（链接在对话中直接渲染）。深度编辑需回 TapNow Creative OS，产出可在「我的项目」中找回。
