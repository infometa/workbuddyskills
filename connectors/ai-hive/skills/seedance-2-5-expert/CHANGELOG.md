# 更新日志 (CHANGELOG)

> 本文件随 AI-HIVE Connector 包版本更新。Connector 包当前版本：**1.1.4**。
> 日期：2026-08-21

## 1.1.4 — 2026-08-21

- 对齐 MCP 0.2.5 的 MP3/WAV、15 MiB 与 `audioMediaIds` 契约，补充 Generate / Edit / Extend 的音频职责和非法组合处理。
- 双 PE 公平对照新增相同 `audioMediaIds` 值与顺序约束，继续只允许 Prompt 不同。

## [1.1.3] — 2026-08-20

### 本技能 (seedance-2-5-expert)

- 新增仅在用户明确要求时启用的双 PE 对照模式，使用“稳健基线版 / 优化增强版”，不声明未经验证的官方来源。
- 双 PE 默认只交付 Prompt；实际运行两版前明确提示会产生两个独立计费任务并取得确认。
- 公平对照固定相同模型、路由、价格快照、参数和媒体字段，仅允许 Prompt 策略不同。
- 时长、画幅、分辨率与输出格式从 Prompt 正文中分离，继续由当前模型配置允许的 `params` 承载。
- 时间戳改为按分镜、卡点、对白或关键事件边界按需使用，不再因视频较长自动切片。

## [1.1.2] — 2026-08-20

### 全技能通用修正（cross-cutting）
- `list_models` 只接收可选的 `modelType`（`TEXT` / `IMAGE` / `VIDEO`），不提供分页游标。
- `upload_media_from_path` 使用 `path`、可选 `filename` 与可选 `contentType`，不接收资源类型字段。
- 文本、图片和视频调用分别传入 `publicModelId`、`routingMode` 与 `pricingSnapshot`；模型专属参数放入 `params`。
- 图片参考使用 `imageMediaIds`；视频参考使用 `videoMediaIds`；首尾帧使用对应单值字段。
- 上传限制按当前 MCP 发布包执行：图片/文档 10MiB，视频 100MiB。
- 任务状态与失败信息改为服务端实际结构：`PENDING` / `SUBMITTED` / `PROCESSING` / `COMPLETED` / `FAILED`，失败详情读取 `failure.code` / `failure.summary` / `failure.suggestion`。

### 本技能 (seedance-2-5-expert)

- 既有工具参数统一对齐当前 MCP schema；图片与视频参考素材分开传入对应媒体数组。
