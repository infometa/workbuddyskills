---
name: detail-page
display_name: 极睿电商详情页生成
display_name_en: Infimind Product Detail Page
description: 根据用户提供的商品素材与真实要求，生成电商商品详情页长图。
description_zh: 根据用户主动选择的商品图片、类目与风格要求，生成电商商品详情页长图，并跟踪任务结果。
description_en: Generate e-commerce product detail-page images from user-selected assets and explicit requirements, then track the task to completion.
category: design # 暂用；最终枚举待 WorkBuddy 团队确认
version: 1.0.1
author: 极睿科技（Infimind）
permissions:
  provisional: true
  read:
    - "仅限当前对话中用户主动选择的图片"
  network:
    - "仅通过已启用的极睿电商生图 Connector 调用 create_detail_page_task 与 get_user_tasks"
---

# 极睿电商详情页生成

## 适用场景

当用户明确提出“电商详情页”“商品详情页”或“详情页长图”生成需求时使用本 Skill。仅在用户明确要求开始生成后创建任务；如果用户只是咨询能力、费用、输入要求或方案建议，只回答问题，不创建任务。

## 事实与合规边界

只使用用户明确提供的信息，不虚构商品类目、卖点、功效、参数、价格、认证、平台要求或促销承诺。`extraDescription` 只能整合用户明确给出的卖点、尺寸、指定文案和平台要求，不得自行推断或补写。`aiModelId` 仅当用户明确给出现有数字 ID 并确认授权时传入；否则省略，禁止查询或猜测。含真人的素材须先确认用户拥有合法使用与生成授权；不得制造公众人物代言、虚假身份或容易造成身份混淆的内容。

本 Skill 只读取当前对话中用户主动选择的图片，并且只通过“极睿电商生图”Connector 调用 `create_detail_page_task` 与 `get_user_tasks`。不得索取或要求用户在对话中粘贴 Token。

## 输入检查

创建任务前一次性检查并分组询问所有缺失或冲突信息：

- `productImages` 必须为 1–5 张；`referenceImages` 最多 5 张。超量时请用户选择，不得静默丢弃。
- `productCategory` 必填，必须由用户确认，不得从图片或商品名擅自推断。
- `generationStyle` 与 `referenceImages` 至少提供一项。
- `imageCount` 允许 5–10，默认 5。
- 默认 `language` 为 `简体中文`、`aspectRatio` 为 `3:4`、`resolution` 为 `2k`、`model` 为 `gpt-image-2-edit`。
- `aspectRatio` 的合法值仅为 `1:1`、`3:4`、`2:3`、`4:3`、`3:2`、`16:9`、`9:16`；`model` 的合法值仅为 `nano-banana-2`、`nano-banana-pro`、`seedream-5.0-lite`、`gpt-image-2-edit`。非默认值仅在用户明确要求时使用；字段不合法或要求互相冲突时，先请用户确认再执行。

## MCP 工具参数与返回值

### `create_detail_page_task`

用途：创建一次商品详情页父任务，由服务端继续生成策划方案和子图。

| 参数 | 类型 | 必填 | 默认值或约束 |
| --- | --- | --- | --- |
| `productImages` | `string[]` | 是 | 1–5 个本地图片路径或公网 URL |
| `referenceImages` | `string[]` | 否 | 最多 5 个；与 `generationStyle` 至少提供一项 |
| `productCategory` | `string` | 是 | 用户确认的真实商品类目 |
| `generationStyle` | `string` | 否 | 与 `referenceImages` 至少提供一项 |
| `language` | `string` | 否 | 默认 `简体中文` |
| `extraDescription` | `string` | 否 | 只传用户明确提供的补充要求 |
| `imageCount` | `number` | 否 | 默认 `5`，允许 5–10 的整数 |
| `aiModelId` | `number` | 否 | 仅传用户明确给出且获授权的数字 ID |
| `aspectRatio` | `string` | 否 | 默认 `3:4`；可选 `1:1 / 3:4 / 2:3 / 4:3 / 3:2 / 16:9 / 9:16` |
| `resolution` | `string` | 否 | 默认 `2k`；可选 `2k / 4k` |
| `model` | `string` | 否 | 默认 `gpt-image-2-edit`；可选 `nano-banana-2 / nano-banana-pro / seedream-5.0-lite / gpt-image-2-edit` |

创建成功返回的核心字段包括 `taskId`、`taskType`、`status`、`productCategory`、`generationStyle`、`language`、`imageCount`、`aspectRatio`、`resolution`、`model`、`quality` 和 `message`。`taskId` 是后续查询的唯一任务编号。

### `get_user_tasks`

用途：查询当前 Token 创建的任务；本 Skill 只用它跟踪刚创建的详情页父任务及统计。

| 参数 | 类型 | 必填 | 默认值或约束 |
| --- | --- | --- | --- |
| `status` | `string` | 否 | 可选 `pending / processing / completed / failed`；本 Skill 轮询时省略，避免漏掉状态变化 |
| `taskId` | `number` | 否 | 本 Skill 必须传入创建返回的 `taskId` |
| `taskType` | `string` | 否 | 工具支持 `smart_refine / image_expand / koc_grid / detail_page / product_main_image / color_change / text_modify / outpainting / visual_migration / precision_edit`；本 Skill 固定传 `detail_page` |
| `limit` | `number` | 否 | 工具默认 `10`；本 Skill 固定传 `11` |

查询返回根字段包括 `tasks`、`detailPageStats`、`detailPageStatsByParentTaskId`、`kocStats`、`kocStatsByParentTaskId`、`smartRefineStats`、`smartRefineStatsByTaskId`、`totalSuccessImageCount` 和 `successImageCount`。本 Skill 只读取与当前 `taskId`、`taskType: "detail_page"` 匹配的 `tasks`、`detailPageStats`。

## 执行与跟踪

信息完整且用户明确要求生成后，仅调用一次 `create_detail_page_task`，并记录返回的数字 `taskId`。不得自动重建或重复提交同一任务，以免重复扣费。

随后每 15–30 秒调用一次，并固定使用 `limit: 11`，以覆盖最多 10 个子任务和 1 个父任务，避免父记录被截断：

`get_user_tasks({taskId, taskType: "detail_page", limit: 11})`

查询工具文本中的响应根字段为 `tasks` 与 `detailPageStats`。只从 `tasks` 中查找同时满足 `id === taskId`、`parentTaskId === taskId`、`taskLevel === "parent"`、`taskType === "detail_page"` 的父任务，并在 `detailPageStats` 中查找 `parentTaskId === taskId` 且 `taskType === "detail_page"` 的同一任务统计。不得用任何单个子任务的 `completed` 状态判断整体完成。

父任务状态为 `failed` 时停止。只有父任务状态为 `completed`，并且匹配统计存在且其中 `pendingImages === 0` 时，才能停止轮询并称“生成完成”。查询返回空结果、找不到父任务、缺少匹配统计或 `pendingImages` 仍大于 0 时，均继续轮询至 10 分钟上限。结果图片只取自匹配统计的 `generatedImageUrls`；成功、失败、待处理数量分别取同一统计的 `completedImages`、`failedImages`、`pendingImages`。若只有部分图片成功，必须披露这些实际数量及可用图片，不得把部分成功描述为全部成功。

## 异常处理

- Token 无效、撤销或过期：提示用户打开 WorkBuddy Connector 凭证配置中的 Token 获取入口，登录本人极睿个人账户并进入 MCP Token 页面，撤销失效 Token，重新创建名为 `WorkBuddy` 的独立 Token，再返回 WorkBuddy 的 Connector 凭证配置中替换旧值；不得要求用户在对话中粘贴 Token。
- 非专业版、非企业版个人账户，或会员权限校验未通过：说明仅专业版/企业版个人账户符合调用条件，并停止创建或重试。
- 积分不足：说明任务未能继续，提示用户自行检查账户积分。
- 附件不可访问：指出具体无法读取的附件，请用户重新选择或授权，不猜测附件内容。
- 任务失败：返回工具提供的失败状态与可安全展示的原因，不自动重试。
- 轮询超时：说明任务仍可能在后台处理，保留 `taskId` 供后续查询，不创建新任务。

## 示例

用户输入：

> 请用我选中的两张面霜商品图，按“护肤 / 面霜”类目做一套简约高端的商品详情页，现在开始生成。需要 5 张，简体中文。

创建任务：

**重要：下例仅展示参数结构。调用前必须把常量式占位替换为 WorkBuddy 实际提供的附件本地路径或公网 URL，绝不能把占位文字原样传给工具。**

```text
create_detail_page_task({
  productImages: [
    WORKBUDDY_SELECTED_IMAGE_LOCAL_PATH_OR_PUBLIC_URL_1,
    WORKBUDDY_SELECTED_IMAGE_LOCAL_PATH_OR_PUBLIC_URL_2
  ],
  productCategory: "护肤 / 面霜",
  generationStyle: "简约高端",
  imageCount: 5,
  language: "简体中文",
  aspectRatio: "3:4",
  resolution: "2k",
  model: "gpt-image-2-edit"
})
```

工具输出：

```text
{ taskId: 12345, status: "pending" }
```

记录数字 `taskId` 后，按规定调用
`get_user_tasks({taskId: 12345, taskType: "detail_page", limit: 11})`。
从工具文本根字段 `tasks` 中匹配指定父任务，并从
`detailPageStats` 中匹配同一 `parentTaskId` 的统计。满足整体完成条件后，只展示该统计的 `generatedImageUrls`，并用同一统计的 `completedImages`、`failedImages`、`pendingImages` 报告成功、失败和待处理数量；若为失败、部分成功或超时，则按对应状态如实说明。
