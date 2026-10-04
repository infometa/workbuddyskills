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

### 本技能 (gpt-image-expert)

- 本轮补充轮询策略（每 10–15s 查询 `get_generation_task`，仅关键状态变化时报一次，降低噪声）。
- 补充生成完成后再次调用 `get_user_info` 向用户报告准确剩余余额（含本次扣费）。
