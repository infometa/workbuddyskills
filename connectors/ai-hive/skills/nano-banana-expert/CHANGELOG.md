# 更新日志 (CHANGELOG)

> 本文件随 AI-HIVE Connector 包版本更新。Connector 包当前版本：**1.2.1**。
> 日期：2026-09-14

## 1.2.1 — 2026-09-14

- 修复 2026-09-09 平台审核驳回：`cli.json` 补齐 `init` 三平台安装命令，解决干净 Windows 环境安装步骤读取 `cliConfig.init` 崩溃（`Cannot read properties of undefined (reading 'win32')`）；技能内容不变。

## 1.2.0 — 2026-09-09

- 对齐 `@infimind-next/ai-hive-mcp@0.3.0`：新增 `get_model` 模型契约查询；`generate_image` / `generate_video` 新增 `dryRun` 只读预检与 `clientRequestId` 幂等键，`chat_text` 新增 `clientRequestId`；`pricingSnapshot` 来源扩展为 `list_models(detail="full")`、`get_model` 或 dry-run，付费调用原样回传。

## [1.1.2] — 2026-08-20

### 全技能通用修正（cross-cutting）
- `list_models` 只接收可选的 `modelType`（`TEXT` / `IMAGE` / `VIDEO`），不提供分页游标。
- `upload_media_from_path` 使用 `path`、可选 `filename` 与可选 `contentType`，不接收资源类型字段。
- 文本、图片和视频调用分别传入 `publicModelId`、`routingMode` 与 `pricingSnapshot`；模型专属参数放入 `params`。
- 图片参考使用 `imageMediaIds`；视频参考使用 `videoMediaIds`；首尾帧使用对应单值字段。
- 上传限制按当前 MCP 发布包执行：图片/文档 10MiB，视频 100MiB。
- 任务状态与失败信息改为服务端实际结构：`PENDING` / `SUBMITTED` / `PROCESSING` / `COMPLETED` / `FAILED`，失败详情读取 `failure.code` / `failure.summary` / `failure.suggestion`。

### 本技能 (nano-banana-expert)

- 新增肖像场景触发词：写真 / 头像 / 商务人像 / 简历照 / 职业照 / portrait / headshot / LinkedIn avatar。
- 既有 10MiB 上传上限说明与 413 错误处理；轮询策略与生成后余额复核已落地。
