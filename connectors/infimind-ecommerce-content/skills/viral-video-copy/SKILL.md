---
name: viral-video-copy
description: 在用户要先拆解爆款参考视频，再为目标商品生成结构同类的新视频时，先预检估价，确认后直接或分步创建。
version: 1.0.0
author: 极睿科技（Infimind）
---

# 爆款视频复制

## 使用时机

用于拆解一条参考视频的结构、镜头和表达，再用 1～5 张目标商品图生成同类新视频。这不是动作换人、逐帧复制、原人物/品牌保留，也不是图片 `visual-migration`。

## 调用流程

1. 收集一条 HTTPS MP4 参考视频、1～5 张 HTTPS 目标商品图、复制模式和生成设置。
2. 先用 `create_viral_video_copy_task` 传 `dryRun=true`。预检只验证权限、素材、能力和包含拆解的整单估价，不建任务、不调供应商、不占积分。
3. 向用户展示 `estimatedCredits`、模式、时长、分辨率、比例和数量；用户未确认时不正式提交。
4. 直接生成：用完全相同的业务参数、`submissionMode=direct`、稳定 `idempotencyKey` 和用户确认的 `maxCredits` 正式创建。
5. 分步确认：只在用户明确要求先看策划时，用 `submissionMode=staged`、稳定 `idempotencyKey`、`maxCredits=0` 正式创建；查询到 `plan_ready` 后展示策划。
6. 用户要修改策划时，传当前 `planVersion` 调用 `update_viral_video_copy_plan`；不覆盖版本冲突。回读当前策划和估价，再经用户确认后传 `taskId`、最新 `planVersion`、新 `idempotencyKey` 和 `maxCredits` 调用 `confirm_viral_video_copy_task`。
7. 全程用精确 `taskId + taskType=viral_video_copy` 调用 `get_user_tasks`。completed 结果再用 `get_video_result_download_url`。

## 工具与参数

### `create_viral_video_copy_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `referenceVideo` | 是 | HTTPS MP4，最大 200 MB；2.0 为 5～15 秒，2.5 为 5～30 秒 |
| `productImages` | 是 | 1～5 张目标商品图 HTTPS URL |
| `copyMode` | 否 | `product_adaptive`（默认）/ `high_fidelity` |
| `productCategory` | 否 | 商品类目，最多 40 字符 |
| `additionalRequirements` | 否 | 补充要求，最多 2000 字符 |
| `submissionMode` | 是 | `direct` / `staged` |
| `model` | 是 | `seedance_2_0` / `seedance_2_5` |
| `durationSeconds` | 是 | 按模型支持的 5～30 秒档位 |
| `resolution` | 是 | `480p` / `720p` / `1080p` |
| `aspectRatio` | 是 | 公开固定比例或 `adaptive` |
| `outputCount` | 是 | 1～12 |
| `dryRun` | 是（预检） | 首次必须 true |
| `idempotencyKey` | 正式必填 | 网络重试复用同一值 |
| `maxCredits` | 正式必填 | direct 为确认整单上限；staged 创建时传 0 |

### `update_viral_video_copy_plan` / `confirm_viral_video_copy_task`

| 工具 | 关键参数 |
| --- | --- |
| `update_viral_video_copy_plan` | `taskId`、`planVersion`；可选 `viralFormula`、`style`、`script`、`sellingPoints`、`generatedPrompt`、`model`、`durationSeconds`、`resolution`、`aspectRatio`、`outputCount` |
| `confirm_viral_video_copy_task` | `taskId`、最新 `planVersion`、新 `idempotencyKey`、用户确认的 `maxCredits` |

### `get_user_tasks` / `get_video_result_download_url`

| 工具 | 参数 |
| --- | --- |
| `get_user_tasks` | 传 `taskId`、`taskType=viral_video_copy`；`status` 和 `limit` 仅作可选筛选 |
| `get_video_result_download_url` | completed 后传 `taskId`、`resultId`、`taskType=viral_video_copy` |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 绑定用户、空间和 operator，不索要 Token；创建、更新、确认、查看和下载均由服务端分别鉴权。
- 只传 HTTPS URL，禁止本地路径、base64、localhost、私网/保留地址、供应商 URL 或签名存储查询串。
- 参考视频只用于拆解，由服务端脱敏后才用于生成；不保留原人物身份、原品牌或未经商品图证实的事实。
- dryRun 的 `estimatedCredits` 为含拆解的整单估价；staged 创建不预留积分，确认 plan 时才以用户同意的上限创建 hold。
- 不自动修改 plan、增加输出、重新拆解或追加扣费；结果只从可信存储签发短时链接。

## 错误处理

只显示稳定公开 code/category 和可操作建议，不透传供应商错误、拆解原始负载、provider URL、存储 key 或提示词快照。`PROVIDER_CONTENT_SAFETY_REAL_PERSON` 要引导调整素材；`VIRAL_ANALYSIS_FAILED` 和 `VIRAL_REFERENCE_SANITIZATION_FAILED` 只能经用户同意、重验权限/素材/余额后新建任务，不自动重试或覆盖旧记录。
