---
name: workrally-game-art-flowchart-example
description: Use this when the user asks to turn an AI game art generation skill
  or workflow into a clear production flowchart and generate a WorkRally
  GPT-IMAGE-2 example image. Combines game asset pipeline extraction, visual
  flowchart design, image model discovery, image generation, download, and
  delivery. 全程通过 WorkRally MCP 工具完成，不依赖 workrally CLI。
description_zh: 游戏美术流程图与示例图
description_en: Game art flowchart and example
agent_created: true
version: 1.1.0
---

# WorkRally 游戏美术流程图与示例图

> **执行通道**：本 skill 全程使用 **WorkRally MCP 工具**（`mcp__workrally1__*`）。
> **不要**调用 `workrally` CLI，也不要依赖 `WORKRALLY_API_KEY` 环境变量——鉴权由 MCP 连接器托管。

## When to use

当用户要求：

- 根据游戏美术、资产生产、角色一致性、纹理生成等 skill 写出流程图。
- 同时要求使用 WorkRally / GPT2 / GPT-IMAGE-2 生成示例图。
- 需要把 AI 游戏美术流水线从文字规则转成可视化流程，并产出一张可交付的参考图。

## Steps

1. 先加载相关领域 skill，例如 `ai-game-art-generation-cn`，并阅读它要求引用的参考文件：`patterns.md`、`sharp_edges.md`、`validations.md`。
2. 提炼流程图主线，默认结构为：风格基准 → 结构控制 → 一致性控制 → 批量生成 → 后处理 → 质量审查 → 归档合规/引擎导入。
3. 在流程图中必须保留质量返工回路：质量审查不通过时回到风格基准、结构控制或一致性控制，不要直接导出。
4. 将关键风险写入流程图或说明：不记录 seed、跳过人工 QA、提示词形容词堆叠、角色漂移、解剖错误、纹理接缝、授权/Steam 披露遗漏。
5. 确认登录态：调用 **`who_am_i`**。
6. 动态查询生图模型：调用 **`canvas_image_model_list`**，从返回的 `models[]` 里选 `model_id` 对应 GPT-IMAGE-2 的那一项（按 `name` / `en_name` 认，**不要硬编码未验证的 model_id**）。同时读取该模型的 `aspect_ratios`、`resolution_options`、`infer_quality_options`、`kontext_config.max_input_images`，后续参数只能从这些返回值里取。
7. 编写示例图提示词。游戏资产默认使用聚焦提示词，不堆叠冲突形容词。建议包含：资产类型、统一角色、视图/姿势、风格、轮廓、色板、一致性、反向约束。
8. 提交生成任务（MCP 异步，本身即 fire-and-forget，**没有** `--poll` 这类阻塞参数）：

```text
canvas_generate_image(
  prompt       = "<prompt>",
  model        = "<从 canvas_image_model_list 取到的 model_id>",
  aspect_ratio = "1:1",
  count        = 1,
  task_name    = "<可读名称，如 game-art_example>",
  short_series_project_id = "<短番项目ID，来自 project_list；不传则只在「全部项目」可见>"
)
→ 返回 task_ids: ["<task_id>"]
```

9. 轮询任务：对每个 `task_id` 调 **`canvas_get_task`**（间隔约 3 秒）。
   `state` 枚举：**1=排队 2=运行 3=暂停 4=成功 5=失败 6=已取消**。只认 `4` 取产物、`5` 放弃重提、其余继续等。
   成功后产物在 `output_assets[]`，取 `asset_id`。
10. 取下载地址：用 **`asset_detail(asset_ids=[...])`** 拿带签名的 `asset_details.url` / `download_url`（签名约 10 小时有效），再本地 `curl` 落盘到工作区输出目录。
11. 如果下载文件没有扩展名，用文件类型检查后重命名为有意义的 `.png` 文件名。
12. 向用户交付：流程图、示例图文件、使用的模型、尺寸、提示词摘要和必要的 QA 注意事项。

## Prompt template

```text
game-ready 2D <asset type> asset reference sheet,
same <subject> in <views or poses>,
<costume/material details>,
<fixed accent color> accent color,
stylized hand-painted mobile game art,
clean silhouette, consistent face and costume across all views,
crisp outline, limited palette, orthographic presentation,
production asset sheet,
no text, no watermark, no logo,
avoid extra fingers, bad anatomy, blurry edges
```

## Pitfalls

- **不要使用 `workrally` CLI**：本 skill 的所有生成/查询/下载都走 MCP 工具。CLI 需要额外安装二进制与 API Key，换机后不可用。
- WorkRally 模型必须**动态获取**（`canvas_image_model_list`），不能凭记忆猜 `model_id`；不同环境可用模型不同。
- MCP 的 `task_ids` **不能直接用于下载** —— 要用 `canvas_get_task` 查状态，素材 URL 必须经 `asset_detail` 获取。
- `asset_detail` 返回的 URL 带签名、约 10 小时过期，过期后重新调用即可。
- 下载文件有时没有扩展名；下载后应检查文件类型并重命名。
- GPT-IMAGE-2 可能不真正输出透明 Alpha，即使提示词写了 transparent background；交付时不要承诺一定透明。
- 游戏资产示例图只是概念/参考级输出，进入项目前仍要人工 QA 和必要修图。
- 商业项目要记录模型、提示词、生成任务、授权等级；Steam 上架还要做 AI 内容披露。

## Verification

- 流程图包含生产主线、质量审查和返工回路。
- `canvas_get_task` 返回 `state=4`，且 `output_assets` 非空。
- 下载后的示例图可以被本地识别为 PNG/JPG 等图像格式。
- 示例图文件被放入工作区，并通过附件交付给用户。
