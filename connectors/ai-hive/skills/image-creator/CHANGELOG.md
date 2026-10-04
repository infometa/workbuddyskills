# 更新日志 (CHANGELOG)

> 本文件随 AI-HIVE Connector 包版本更新。Connector 包当前版本：**1.1.4**。
> 日期：2026-08-20

## [1.1.2] — 2026-08-20

### 全技能通用修正（cross-cutting）
- `list_models` 只接收可选的 `modelType`（`TEXT` / `IMAGE` / `VIDEO`），不提供分页游标。
- `upload_media_from_path` 使用 `path`、可选 `filename` 与可选 `contentType`，不接收资源类型字段。
- 文本、图片和视频调用分别传入 `publicModelId`、`routingMode` 与 `pricingSnapshot`；模型专属参数放入 `params`。
- 图片参考使用 `imageMediaIds`；视频参考使用 `videoMediaIds`；首尾帧使用对应单值字段。
- 上传限制按当前 MCP 发布包执行：图片/文档 10MiB，视频 100MiB。
- 任务状态与失败信息改为服务端实际结构：`PENDING` / `SUBMITTED` / `PROCESSING` / `COMPLETED` / `FAILED`，失败详情读取 `failure.code` / `failure.summary` / `failure.suggestion`。

### 本技能 (image-creator)

- 新增风格分发指引：写实人像 / 写真 / 商务职业照 → Nano-Banana；国风 / 汉服 / 艺术插画 → Seedream；需清晰可读文字 / 海报 → GPT-Image。
- 既有 10MiB 上传上限说明与 413 错误处理；轮询策略与生成后余额复核已落地。
