---
name: koc-seeding
description: 在用户要根据商品图和卖点生成 KOC 种草拼图时，默认直接创建，或按用户明确要求先准备候选方案再提交。
version: 1.0.0
author: 极睿科技（Infimind）
---

# KOC 种草拼图

## 使用时机

用于根据 1～10 张商品图、商品名和可选卖点/人群/场景生成一张 KOC 种草拼图。如用户需要封面加多张内容图及笔记文案，使用 `image-text-commerce`。

## 调用流程

### 默认直接创建

1. 收集商品图和商品名，可选收集类目、卖点、目标人群、场景和人物要求。
2. 确认版式和生成参数，仅传 HTTPS 素材 URL，说明当前 OAuth 空间和计费边界。
3. 调用 `create_koc_collage_task`。

### 仅在用户明确要求查看/选择候选方案时

1. 用同样输入调用 `prepare_koc_collage_task`，展示返回候选，不自行代替用户选择。
2. 用户选择 1～3 个方案后，用 prepare 返回的任务 ID 和 index 调用 `submit_koc_collage_task`。

两种流程最后都用创建/prepare 返回的 `taskId` 与 `taskType=koc_grid` 调用 `get_user_tasks`。超时或失败时不得自动重建任务。

## 工具与参数

### `create_koc_collage_task` / `prepare_koc_collage_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `images` | 是 | 1～10 张商品图 HTTPS URL |
| `productName` | 是 | 商品名 |
| `productCategory` | 否 | 商品类目 |
| `sellingPoints` | 否 | 卖点、材质、功效和价格等已确认信息 |
| `targetAudience` | 否 | 目标人群 |
| `usageScenario` | 否 | 使用场景 |
| `modelDescription` | 否 | 人物描述；提供 `aiModelId` 时建议不同时填 |
| `aiModelId` | 否 | 已授权 AI 模特 ID |
| `collageLayout` | 否 | `grid_5x2` / `grid_3x3` / `grid_2x2` |
| `promptCandidateCount` | 仅 prepare | 4 / 6 / 10，默认 6 |
| `aspectRatio` | 否 | 不填时由版式推导；`auto` 仅 GPT Image 2 支持 |
| `resolution` | 否 | `1k` / `2k` / `3k` / `4k`，服务端按模型校验 |
| `quality` | 否 | `low` / `medium` / `high` |
| `model` | 否 | 当前公开图像模型 |

### `submit_koc_collage_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `taskId` | 是 | `prepare_koc_collage_task` 返回的任务 ID |
| `selectedPlanIndexes` | 是 | 用户选择的 1～3 个候选 index |

### `get_user_tasks`

| 参数 | 用法 |
| --- | --- |
| `taskId` | 直接创建或 prepare 返回的任务 ID |
| `taskType` | 固定为 `koc_grid` |
| `status` | 可选状态筛选 |
| `limit` | 精确查询时取最小值 |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 绑定用户、空间和 operator，不索要 Token；只能创建、提交和查询有权限的任务。
- 仅传 HTTPS URL，不传本地路径、base64、localhost、私网/保留地址或存储内部 URL。
- 工具会在服务端重验素材、AI 模特、空间、能力和积分；客户端不替代业务事实。
- 不编造商品功效、价格、认证或人物身份，不代用户选择候选方案。

## 错误处理

仅返回稳定公开错误码和修正建议，不透传供应商错误、原始候选负载、存储 URL 或内部堆栈。权限、余额、素材或内容安全失败需先修正；不自动重试 submit 或创建。
