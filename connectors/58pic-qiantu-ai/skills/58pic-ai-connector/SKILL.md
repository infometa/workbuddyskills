---
name: 58pic-ai-connector
description: Use the Qiantu AI connector for licensed asset search, image or video generation, credit checks, and editable creative workflows.
description_zh: 使用千图 AI 连接器完成正版素材检索、图片和视频生成、积分查询与可编辑工作流。
description_en: Use the Qiantu AI connector for licensed asset search, image and video generation, credit checks, and editable workflows.
version: 1.0.0
author: 千图AI
---

# 千图 AI 连接器使用规范

首次使用时按 MCP 客户端的浏览器 OAuth 引导完成授权；不要索取、展示或保存用户的 API Key。

## 工具边界

- 可直接调用：`list_models`、`list_catalog`、`search_images`、`get_model_capabilities`、`get_credits`、`get_generation_status`、`workflow_list`、`workflow_get`。
- 必须先告知影响并取得用户确认：`generate_image`、`generate_same_style`、`generate_video`、`get_download_info`、`workflow_create`、`workflow_save`、`workflow_run`。说明可能的积分消耗、写入或下载影响。
- 生成前先查模型能力；生成超时后查询原任务状态，禁止自动重复提交扣点任务。
- 编辑工作流必须先 `workflow_get` 获取完整画布，只改目标字段，再完整保存 nodes、edges、分组和父子关系。

## 异常恢复

授权失效时引导用户在 WorkBuddy 的连接器管理中重新连接。参数错误只解释可修正字段；积分不足、内容审核拒绝和扣点任务超时不得自动重试。
