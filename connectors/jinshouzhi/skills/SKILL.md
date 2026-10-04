---
name: jinshouzhi-skill
description: 金手指广告投放技能 - 查询项目数据、写回需求单与文案、生成投放主台深链、轻量调优
version: "1.0.50"
author: "Goldfinger Ad Agent"
---

# 金手指 Skill

本 Skill 提供金手指（腾讯广告投放执行台）的 MCP 操作能力。对话在 WorkBuddy，产物回写金手指平台；重操作（首次上线、上传素材、生成投手）需在页面完成。

## 使用前

1. 首次连接需完成 MCP OAuth 授权（WorkBuddy 会自动打开浏览器）。
2. 涉及具体项目时，**必须先调用 `list_projects`**，使用返回的 `id` 作为 `project_id`。
3. 不要传旧参数 `project`（项目名称）；仅接受 `project_id`（`projects.id`）。

## 可用工具

### validate_apikey - 校验腾讯广告凭证

校验 apiKey 与账户 ID 的连通性。项目已托管 Key 时传 `project_id` 即可。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | - | 金手指 `projects.id`，托管模式下传它即可 |
| accountId | string | - | 腾讯广告账户 ID；托管模式下可留空 |

### list_projects - 列出投放项目

列出当前用户名下所有投放项目及账户，供后续工具选择 `project_id`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| （无） | - | - | - |

### get_project_data - 查询投放数据

拉取近 N 天真实投放数据：消耗、曝光、点击、转化、付费金额、ROI。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | - | 金手指 `projects.id`；留空返回全部项目汇总 |
| days | number | - | 回溯天数，默认 7 |

### open_config - 生成投放主台深链

策略沟通完成后，把已确认策略打包为 session，返回金手指投放主台深链。用户点击后从「需求单确认」进入五步主台。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| strategy | object | ✅ | 已确认策略（offerName、预算、出价、定向等） |
| rawHtml | string | - | 策略 HTML 富文本（如《投放策略纪要》），用于精确预填 |
| project_id | string | - | 传入且属于当前用户时落需求单 |

### adjust_project - 轻量调整已上线项目

对已上线项目改日预算 / 改出价 / 暂停 / 恢复。**涉及花钱的操作需 `confirm=true` 才真正执行**。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| accountId | string | ✅ | 腾讯广告账户 ID |
| action | string | ✅ | `set_budget` / `set_bid` / `pause` / `resume` |
| project_id | string | - | 托管 Key 时用于取凭证 |
| adgroupId | string | - | 广告组 ID；执行时必填 |
| value | number | - | `set_budget` / `set_bid` 的目标值（元） |
| confirm | boolean | - | `false` 或未传时仅预览，不执行 |

### upsert_demand_brief - 写回需求单

把已确认的需求单/策略产物写回「需求单确认」步骤。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| payload | object | ✅ | 需求单结构化内容 |
| conversation_id | string | - | WorkBuddy 对话 ID |
| status | string | - | `draft` 或 `confirmed` |

### upsert_brand_assets - 品牌素材（落库）

写入品牌素材到 `brand_assets` 表；`storage_key` 为对象存储或外部引用键。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| items | array | ✅ | 素材项列表（title、storage_key、mime_type） |
| conversation_id | string | - | WorkBuddy 对话 ID |

### upsert_copy_asset - 写入投放文案

写入投放文案并落库。外层文案与首条评论可在页面修改；转化按钮文案只读。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| copy | string | - | 文案正文（兼容旧版） |
| outerCopy | string[] | - | 外层文案数组 |
| firstComments | string[] | - | 首条评论数组 |
| ctaCopy | object | - | 转化按钮文案 `{ primary, backup }`，只读 |
| conversation_id | string | - | WorkBuddy 对话 ID |

### bind_generated_creatives - 素材中转腾讯广告并落库

把产图或用户上传素材中转到腾讯广告（`fileBase64` 上传），并将 `image_id`/`video_id` 写入 `creative_assets` 表。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| items | array | ✅ | 素材项（title、fileBase64、mime_type、image_id、video_id、storage_key） |
| accountId | string | - | 腾讯广告账户 ID |
| conversation_id | string | - | WorkBuddy 对话 ID |

### upsert_review_intent - 写入复盘意图

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| payload | object | ✅ | 复盘意图内容 |
| conversation_id | string | - | WorkBuddy 对话 ID |

### upsert_review_schedule - 写入复盘定时

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| cron_expr | string | ✅ | Cron 表达式 |
| title | string | ✅ | 定时任务标题 |
| enabled | boolean | - | 是否启用 |
| conversation_id | string | - | WorkBuddy 对话 ID |

### upsert_review_artifact - 写入复盘材料

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |
| title | string | ✅ | 材料标题 |
| payload | object | ✅ | 复盘材料内容 |
| kind | string | - | 材料类型 |
| conversation_id | string | - | WorkBuddy 对话 ID |

### get_project_context - 读取项目五步产物

读取需求单、复盘材料等；平台范例见 `list_creative_examples`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| project_id | string | ✅ | 金手指 `projects.id` |

### list_creative_examples - 读取平台素材范例

全平台一份素材范例样式，素材经理出图前对照用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| （无） | - | - | - |

## 推荐调用顺序

1. `list_projects` → 获取 `project_id`
2. `get_project_data` / `get_project_context` → 了解现状
3. `upsert_demand_brief` / `upsert_copy_asset` 等 → 写回产物
4. `open_config` → 生成深链，引导用户进入页面完成重操作
5. 已上线后：`adjust_project`（先预览，确认后再 `confirm=true`）

## 认证说明

- 默认走 **MCP OAuth**：首次连接或 Token 过期时，WorkBuddy 会打开浏览器完成授权。
- 若收到 **401**，提示用户重新连接 Connector 并完成授权。
- access_token 有效期约 1 小时，WorkBuddy 会自动用 refresh_token 续期；续期失败需重新授权。

## 注意事项

- 项目标识统一用 `project_id`，不要用项目名称。
- `adjust_project` 单次预算上限 100,000 元、出价上限 5,000 元，超限会被拒绝。
- `open_config` 只负责预填与打开页面，不能替代首次上线或素材上传。
- 品牌素材与项目素材不落金手指平台，仅中转或写文案/需求单等结构化产物。
