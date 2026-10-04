---
name: image-text-commerce
description: 在用户要生成封面、多张内容图和种草文案组成的图文带货笔记包时，默认直接创建，或按明确要求先选方案再提交。
version: 1.0.0
author: 极睿科技（Infimind）
---

# 图文带货

## 使用时机

用于根据商品图和商品信息，生成包含封面图、3～8 张内容图及笔记文案的笔记包。只要一张 KOC 拼图时使用 `koc-seeding`。

## 调用流程

### 默认直接创建

1. 收集 1～10 张商品图和商品名，建议补充类目、卖点、人群和使用场景。
2. 确认每个笔记包的内容图数、生成笔记包数和模型参数；仅传 HTTPS 素材 URL。
3. 说明当前 OAuth 空间和计费边界，调用 `create_koc_note_package_task`。

### 仅在用户明确要求查看/选择候选方案时

1. 调用 `prepare_koc_note_package_task`展示候选笔记方案，不代用户选择。
2. 用户选择 1～3 个方案后，用 prepare 返回的任务 ID 和 index 调用 `submit_koc_note_package_task`。

两种流程都用创建/prepare 返回的 `taskId` 和 `taskType=image_text_commerce` 调用 `get_user_tasks`。查询超时不得自动重建任务。

## 工具与参数

### `create_koc_note_package_task` / `prepare_koc_note_package_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `images` | 是 | 1～10 张商品图 HTTPS URL |
| `productName` | 是 | 商品名 |
| `productCategory` | 否 | 商品类目 |
| `sellingPoints` | 否 | 卖点、材质、功效和场景等已确认信息 |
| `targetAudience` | 否 | 目标人群 |
| `usageScenario` | 否 | 使用场景 |
| `modelDescription` | 否 | 人物描述；提供 `aiModelId` 时建议不同时填 |
| `aiModelId` | 否 | 已授权 AI 模特 ID |
| `noteImageCount` | 否 | 每个笔记包 3～8 张内容图，不含封面，默认 5 |
| `packageCount` | 仅 direct | 自动选择并生成 1～3 个笔记包 |
| `aspectRatio` | 否 | 默认 `3:4`；`auto` 仅 GPT Image 2 支持 |
| `resolution` | 否 | 公开分辨率，服务端按模型校验 |
| `quality` | 否 | `low` / `medium` / `high` |
| `model` | 否 | 当前公开图像模型 |

### `submit_koc_note_package_task`

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `taskId` | 是 | `prepare_koc_note_package_task` 返回的任务 ID |
| `selectedPlanIndexes` | 是 | 用户选择的 1～3 个笔记方案 index |

### `get_user_tasks`

| 参数 | 用法 |
| --- | --- |
| `taskId` | 直接创建或 prepare 返回的任务 ID |
| `taskType` | 固定为 `image_text_commerce` |
| `status` | 可选状态筛选 |
| `limit` | 精确查询时取最小值 |

## 权限、积分与安全边界

- OAuth 获取与刷新：首次连接时由 WorkBuddy 打开浏览器完成 OAuth；access token 到期后由客户端使用 refresh token 自动轮换；授权失效后重新连接。
- OAuth 绑定用户、空间和 operator，不索要 Token；任务、AI 模特和结果均由服务端重验权限。
- 只传 HTTPS URL，不传本地路径、base64、localhost、私网/保留地址或内部存储 URL。
- 创建与 submit 可能计费，余额、预留和结算以服务端业务表为准；不因客户端动画或文案判定已扣费。
- 不编造产品功效、价格、认证和人物身份；选择候选方案必须来自用户。

## 错误处理

仅展示稳定公开错误码和修正建议，不透传供应商错误、内部策划负载、存储 URL 或堆栈。权限、余额、素材或内容安全错误需先修正；不自动重试 submit 或重复创建。
