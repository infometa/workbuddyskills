---
name: product-main-image
display_name: 极睿商品主图生成
display_name_en: Infimind Product Main Image
description: 根据用户主动选择的商品素材与明确要求，生成一套电商商品主图。
description_zh: 根据用户主动选择的商品图片、类目、风格或参考图，生成 5–10 张电商商品主图，并跟踪任务结果。
description_en: Generate 5–10 e-commerce product main images from user-selected assets and explicit requirements, then track the task to completion.
category: design # 暂用；最终枚举待 WorkBuddy 团队确认
version: "1.0.1"
author: 极睿科技（Infimind）
permissions:
  provisional: true
  read:
    - "仅限当前对话中用户主动选择的图片"
  network:
    - "仅通过已启用的极睿电商生图 Connector 调用 create_product_main_image_task 与 get_user_tasks"
---

# 极睿商品主图生成

## 适用场景

当用户明确提出“商品主图”“电商主图”“白底主图”“主图套图”等生成需求时使用本 Skill。商品详情页长图应交给商品详情页 Skill，KOC 拼图应交给 KOC 种草 Skill。用户只是在咨询能力、参数、费用或方案时，不得创建任务；只有用户明确要求开始生成后才能执行。

## 事实与合规边界

只使用用户明确提供的信息和当前对话中主动选择的图片。不得虚构商品类目、材质、功能、功效、参数、认证、价格、促销信息或品牌背书；`coreSellingPoints` 与 `usageScenario` 只能传入用户明确提供的内容。不得擅自改变商品主体的颜色、结构、包装、标识或可见文字。涉及真人、AI 模特或参考图时，应确认用户拥有合法使用和生成授权；不得制造公众人物代言、虚假身份或容易造成身份混淆的内容。

本 Skill 只通过“极睿电商生图”Connector 调用 `create_product_main_image_task` 与 `get_user_tasks`。不得索取或要求用户在对话中粘贴 Token。

## 输入检查

创建任务前一次性检查并分组询问所有缺失或冲突信息：

- `productImages` 必须为用户主动选择的 1–5 张商品图；`referenceImages` 最多 5 张。附件不可访问或数量超限时，请用户重新选择，不得自行挑选或静默丢弃。
- `productCategory` 必填，必须由用户确认，不得从图片或商品名称擅自推断。
- `generationStyle` 与 `referenceImages` 至少提供一项。用户没有参考图时应确认文字风格；已有参考图时不得额外编造风格要求。
- `imageCount` 必须是 5–10 的整数，默认 5。记录本次确定的数量，后续用它判断全部子任务是否已经返回。
- 默认 `language` 为 `简体中文`、`aspectRatio` 为 `1:1`、`resolution` 为 `2k`、`model` 为 `gpt-image-2-edit`。`quality`、`coreSellingPoints`、`usageScenario`、`positionTypes`、`positionCopyModes` 和 `aiModelId` 仅在用户明确提供时传入。
- `positionCopyModes` 只能使用 `auto`、`with_copy`、`without_copy`。位置类型或文案模式最多各 10 项，不得超过本次 `imageCount`。
- `aspectRatio` 的合法值为 `1:1`、`3:4`、`4:3`、`16:9`、`9:16`、`2:3`、`3:2`、`4:5`、`5:4`、`21:9`；`resolution` 的合法值为 `1k`、`2k`、`3k`、`4k`；`quality` 的合法值为 `low`、`medium`、`high`；`model` 的合法值为 `nano-banana-2`、`nano-banana-pro`、`seedream-5.0-lite`、`gpt-image-2-edit`。
- `aiModelId` 仅在用户明确给出现有数字 ID 并确认拥有使用授权时传入；不得查询、猜测或自行选择。

## MCP 工具参数与返回值

### `create_product_main_image_task`

用途：创建一次商品主图父任务，由服务端继续生成策划方案和指定数量的主图。

| 参数 | 类型 | 必填 | 默认值或约束 |
| --- | --- | --- | --- |
| `productImages` | `string[]` | 是 | 1–5 个本地图片路径或公网 URL |
| `referenceImages` | `string[]` | 否 | 最多 5 个；与 `generationStyle` 至少提供一项 |
| `productCategory` | `string` | 是 | 用户确认的真实商品类目 |
| `generationStyle` | `string` | 否 | 与 `referenceImages` 至少提供一项 |
| `language` | `string` | 否 | 默认 `简体中文` |
| `coreSellingPoints` | `string` | 否 | 只传用户明确提供的核心卖点 |
| `usageScenario` | `string` | 否 | 只传用户明确提供的使用场景 |
| `imageCount` | `number` | 否 | 默认 `5`，允许 5–10 的整数 |
| `positionTypes` | `string[]` | 否 | 最多 10 项，且不得超过 `imageCount` |
| `positionCopyModes` | `string[]` | 否 | 最多 10 项；元素可选 `auto / with_copy / without_copy` |
| `aiModelId` | `number` | 否 | 仅传用户明确给出且获授权的数字 ID |
| `aspectRatio` | `string` | 否 | 默认 `1:1`；可选 `1:1 / 3:4 / 4:3 / 16:9 / 9:16 / 2:3 / 3:2 / 4:5 / 5:4 / 21:9` |
| `resolution` | `string` | 否 | 默认 `2k`；可选 `1k / 2k / 3k / 4k` |
| `quality` | `string` | 否 | 可选 `low / medium / high` |
| `model` | `string` | 否 | 默认 `gpt-image-2-edit`；可选 `nano-banana-2 / nano-banana-pro / seedream-5.0-lite / gpt-image-2-edit` |

创建成功返回的核心字段包括 `taskId`、`taskType`、`status`、`model`、`resolution`、`quality`、`detailUrl` 和 `message`。`taskId` 是后续查询的唯一任务编号。

### `get_user_tasks`

用途：查询当前 Token 创建的任务；本 Skill 只用它跟踪刚创建的商品主图父任务和子任务。

| 参数 | 类型 | 必填 | 默认值或约束 |
| --- | --- | --- | --- |
| `status` | `string` | 否 | 可选 `pending / processing / completed / failed`；本 Skill 轮询时省略，避免漏掉状态变化 |
| `taskId` | `number` | 否 | 本 Skill 必须传入创建返回的 `taskId` |
| `taskType` | `string` | 否 | 工具支持 `smart_refine / image_expand / koc_grid / detail_page / product_main_image / color_change / text_modify / outpainting / visual_migration / precision_edit`；本 Skill 固定传 `product_main_image` |
| `limit` | `number` | 否 | 工具默认 `10`；本 Skill 固定传 `11` |

查询返回根字段包括 `tasks`、`detailPageStats`、`detailPageStatsByParentTaskId`、`kocStats`、`kocStatsByParentTaskId`、`smartRefineStats`、`smartRefineStatsByTaskId`、`totalSuccessImageCount` 和 `successImageCount`。本 Skill 只读取与当前 `taskId`、`taskType: "product_main_image"` 匹配的 `tasks`。

## 创建任务

输入完整且用户明确要求生成后，仅调用一次 `create_product_main_image_task`。创建可能扣除积分，执行前应让用户清楚本次将正式生成。保存工具返回的数字 `taskId` 和本次确定的 `imageCount`；如果没有返回有效数字任务编号，应报告响应异常并停止，不能再次创建。

## 查询与收口

创建成功后，每隔 15–30 秒调用一次：

```json
{
  "taskId": 12345,
  "taskType": "product_main_image",
  "limit": 11
}
```

只处理根字段 `tasks` 中 `parentTaskId === taskId` 且 `taskType === "product_main_image"` 的记录：

1. 查询返回根 `tasks` 空数组，或尚未出现子任务而只有 `taskLevel === "parent"` 的父任务时，不得重新创建；父任务为 `failed` 时立即停止并报告工具返回的安全错误，其他情况继续用原 `taskId` 轮询。
2. 出现 `taskLevel === "child"` 的记录后，只按子任务判断结果。子任务数量少于本次 `imageCount`，或任一子任务仍为 `pending`、`processing` 时继续轮询。
3. 只有子任务数量等于本次 `imageCount`，且每个子任务状态都为 `completed` 或 `failed` 时，才能整体收口。数量超过预期、任务 ID 重复或字段缺失时，应报告响应异常，不得声称全部完成。
4. 成功图片只取 `status === "completed"` 且 `generatedImageUrl` 非空的子任务。部分失败时展示成功结果并明确说明成功数、失败数和结果缺失数；全部失败时如实说明，不得展示或编造结果。

累计等待达到 10 分钟时停止轮询，说明任务仍可能在后台处理，并保留 `taskId` 供用户后续查询。失败、异常或超时后不得自动重建或重试；只有用户了解可能重复扣费并再次明确确认后，才能创建新任务。

## 异常处理

- Token 无效、撤销或过期：提示用户打开 WorkBuddy Connector 凭证配置中的 Token 获取入口，登录本人极睿个人账户并进入 MCP Token 页面，撤销失效 Token，重新创建名为 `WorkBuddy` 的独立 Token，再返回 WorkBuddy 的 Connector 凭证配置中替换旧值；不得要求用户在对话中粘贴 Token。
- 会员权限不足：说明该能力仅对符合要求的专业版或企业版个人账户开放，并停止调用。
- 积分不足：说明任务未能创建或继续，提示用户先检查和补充本人账户积分。
- 附件不可访问：指出无法读取的附件，请用户重新选择或授权；修复前不得创建任务。
- 部分失败或结果缺失：返回可用的真实图片、实际数量和工具提供的原因，不自动补建任务。

## 示例

用户输入：

> 请用我选中的两张面霜商品图，为“护肤 / 面霜”类目生成 5 张 1:1 商品主图，风格是简约高端、干净浅色背景，现在开始生成。

以下图片占位只用于说明参数结构；调用前必须替换为 WorkBuddy 当前会话提供的实际本地路径或公网 URL，绝不能把占位文字原样传给工具：

```json
{
  "productImages": [
    "<用户选择的商品图 1>",
    "<用户选择的商品图 2>"
  ],
  "productCategory": "护肤 / 面霜",
  "generationStyle": "简约高端、干净浅色背景",
  "imageCount": 5,
  "language": "简体中文",
  "aspectRatio": "1:1",
  "resolution": "2k",
  "model": "gpt-image-2-edit"
}
```

调用一次 `create_product_main_image_task`。取得数字 `taskId` 后，按规定调用
`get_user_tasks({taskId, taskType: "product_main_image", limit: 11})`。
只有全部 5 个子任务进入终态后才能收口，并且只能展示工具真实返回的图片。
