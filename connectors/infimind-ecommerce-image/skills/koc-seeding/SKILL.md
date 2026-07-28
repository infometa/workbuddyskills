---
name: koc-seeding
display_name: KOC 种草拼图
display_name_en: KOC Seeding Collage
description: "根据用户主动选择的商品图，生成 KOC 种草、买家秀或小红书风格的营销拼图。"
description_zh: "根据用户主动选择的商品图，生成 KOC 种草、买家秀或小红书风格的营销拼图。"
description_en: "Create KOC-style promotional collages from product images explicitly selected by the user."
category: design # 暂用；最终枚举待 WorkBuddy 团队确认
version: "1.0.1"
author: "极睿科技（Infimind）"
permissions:
  provisional: true
  read:
    - "仅限当前对话中用户主动选择的图片"
  network:
    - "仅通过已启用的极睿电商生图 Connector 调用 create_koc_collage_task 与 get_user_tasks"
---

# KOC 种草拼图

## 何时使用

当用户提出“KOC 种草图”“买家秀拼图”“小红书风格拼图”“商品种草九宫格”等需求时使用本技能。产出仅是营销风格的模拟内容，不代表真实买家、真实评价、真实使用经历或第三方背书。不得虚构商品名称、卖点、材质、价格、功效、适用人群、使用场景及其他事实；尤其不得把生成文案描述成真实消费者证言。

## 调用前检查

1. 只读取当前对话中用户主动选择的 1–10 张图片。附件不可访问时，先请用户重新选择可访问的图片，不要创建任务。
2. `productName` 必填，且必须来自用户明确提供的商品名称。缺少时先询问，不能用“商品”等占位名称代替。
3. 用户选择超过 10 张图片时，列出数量并请用户明确选择最多 10 张；不得自行挑选或静默丢弃。
4. `collageLayout` 只能是 `grid_5x2`、`grid_3x3`、`grid_2x2`。默认使用 `grid_5x2`；用户说“九宫格”时使用 `grid_3x3`，说“四宫格”时使用 `grid_2x2`。
5. 默认 `resolution` 为 `2k`，默认 `model` 为 `gpt-image-2-edit`。`productCategory`、`sellingPoints`、`targetAudience`、`usageScenario`、`modelDescription`、`aiModelId`、`aspectRatio`、`quality` 等可选信息，仅在用户明确提供时传入，不从图片或常识中推断。不得使用可识别真人或公众人物制造代言、买家证言或身份混淆；涉及真人时须确认用户拥有合法授权，否则改用非特定人物描述。

## MCP 工具参数与返回值

### `create_koc_collage_task`

用途：创建一次 KOC 种草拼图父任务，并自动生成拼图方案和结果图。

| 参数 | 类型 | 必填 | 默认值或约束 |
| --- | --- | --- | --- |
| `images` | `string[]` | 是 | 1–10 个本地图片路径或公网 URL |
| `productName` | `string` | 是 | 用户明确提供的真实商品名 |
| `productCategory` | `string` | 否 | 用户明确提供时才传 |
| `sellingPoints` | `string` | 否 | 用户明确提供时才传 |
| `targetAudience` | `string` | 否 | 用户明确提供时才传 |
| `usageScenario` | `string` | 否 | 用户明确提供时才传 |
| `modelDescription` | `string` | 否 | 仅描述获授权的非特定人物形象 |
| `aiModelId` | `number` | 否 | 仅传用户明确给出且获授权的数字 ID |
| `collageLayout` | `string` | 否 | 默认 `grid_5x2`；可选 `grid_5x2 / grid_3x3 / grid_2x2` |
| `aspectRatio` | `string` | 否 | 可选 `1:1 / 3:4 / 4:3 / 16:9 / 9:16 / 2:3 / 3:2 / 4:5 / 5:4 / 21:9`；省略时按版式决定 |
| `resolution` | `string` | 否 | 默认 `2k`；可选 `1k / 2k / 3k / 4k` |
| `quality` | `string` | 否 | 可选 `low / medium / high` |
| `model` | `string` | 否 | 默认 `gpt-image-2-edit`；可选 `nano-banana-2 / nano-banana-pro / seedream-5.0-lite / gpt-image-2-edit` |

创建成功返回的核心字段包括 `taskId`、`taskType`、`outputMode`、`status`、`collageLayout`、`detailUrl` 和 `message`。`taskId` 是后续查询的唯一任务编号。

### `get_user_tasks`

用途：查询当前 Token 创建的任务；本 Skill 只用它跟踪刚创建的 KOC 拼图父任务和子任务。

| 参数 | 类型 | 必填 | 默认值或约束 |
| --- | --- | --- | --- |
| `status` | `string` | 否 | 可选 `pending / processing / completed / failed`；本 Skill 轮询时省略，避免漏掉状态变化 |
| `taskId` | `number` | 否 | 本 Skill 必须传入创建返回的 `taskId` |
| `taskType` | `string` | 否 | 工具支持 `smart_refine / image_expand / koc_grid / detail_page / product_main_image / color_change / text_modify / outpainting / visual_migration / precision_edit`；本 Skill 固定传 `koc_grid` |
| `limit` | `number` | 否 | 工具默认 `10`；本 Skill 固定传 `10` |

查询返回根字段包括 `tasks`、`detailPageStats`、`detailPageStatsByParentTaskId`、`kocStats`、`kocStatsByParentTaskId`、`smartRefineStats`、`smartRefineStatsByTaskId`、`totalSuccessImageCount` 和 `successImageCount`。本 Skill 只读取与当前 `taskId`、`taskType: "koc_grid"` 匹配的 `tasks`、`kocStats`。

## 创建与查询

确认必填信息后，仅当用户明确要求执行生成时，才调用一次 `create_koc_collage_task`；能力咨询、参数比较或方案讨论不得创建任务。创建可能产生积分扣费，执行前应让用户清楚本次将正式生成。保存返回的数字 `taskId`；若没有得到数字任务编号，应报告创建响应异常并停止，不要再次创建。

随后每隔 15–30 秒调用一次：

```json
{
  "taskId": 12345,
  "taskType": "koc_grid",
  "limit": 10
}
```

查询工具必须是 `get_user_tasks`，参数必须包含当前任务的 `taskId`、`taskType: "koc_grid"` 和 `limit: 10`。每次查询后，在根字段 `kocStats` 中查找 `parentTaskId === taskId` 且 `taskType === "koc_grid"` 的统计项。统计项缺失、数组为空或 `pendingImages > 0` 时，在总等待时间未满的前提下继续轮询；只有 `pendingImages === 0` 且 `totalImages > 0` 时才能整体收口。

整体收口后，按统计项区分结果：`successImageCount === totalImages`、`completedImages === totalImages` 且 `failedImages === 0` 为全部成功；`successImageCount > 0`、`completedImages > 0` 且 `failedImages > 0` 为部分成功；`successImageCount === 0`、`completedImages === 0` 且 `failedImages === totalImages` 为全部失败。计数不符合上述任一情况时，应报告统计异常，不能声称完成。

真实结果图片只能从根字段 `tasks` 中筛选 `parentTaskId === taskId`、`taskType === "koc_grid"`、`taskLevel === "child"`、`status === "completed"` 的任务，并读取其非空 `generatedImageUrl`。不得因为任一子任务为 `completed` 就声称整体完成。全部成功时展示所有真实返回图；部分成功时展示成功结果并明确披露 `failedImages`；全部失败时说明失败，不展示虚构结果。累计等待达到 10 分钟时停止并告知用户任务仍未完成。失败或超时后不得自动重建或重试，只有用户了解可能重复扣费并明确确认后，才能创建新任务。

## 异常处理

- Token 无效、撤销或过期：提示用户打开 WorkBuddy Connector 凭证配置中的 Token 获取入口，登录本人极睿个人账户并进入 MCP Token 页面，撤销失效 Token，重新创建名为 `WorkBuddy` 的独立 Token，再返回 WorkBuddy 的 Connector 凭证配置中替换旧值；不得要求用户在对话中粘贴 Token。
- 会员权限不足：说明该能力仅对符合要求的专业版或企业版个人账户开放，并停止调用。
- 积分不足：说明任务未能创建或继续，并提示用户先补充积分。
- 附件不可访问：请用户重新选择图片，修复前不要创建任务。
- 部分失败：返回已成功的真实结果、失败数量及工具提供的原因；不要自动补建任务。

## 示例：输入 → 工具 → 输出

用户输入：“用我选中的 3 张图给‘便携咖啡机’做九宫格 KOC 种草拼图，卖点是 400 ml 水箱。”其中商品名和卖点均由用户明确提供。

调用一次 `create_koc_collage_task`。以下图片占位文字仅用于说明对应关系；调用前必须替换为 WorkBuddy 当前会话实际提供的本地图片路径或公网 URL，绝不能把占位文字原样传给工具：

```json
{
  "images": [
    "<用户选择的图片 1>",
    "<用户选择的图片 2>",
    "<用户选择的图片 3>"
  ],
  "productName": "便携咖啡机",
  "sellingPoints": "400 ml 水箱",
  "collageLayout": "grid_3x3",
  "resolution": "2k",
  "model": "gpt-image-2-edit"
}
```

创建返回示例：

```json
{
  "taskId": 12345,
  "status": "generating_prompts"
}
```

工具返回数字任务编号后，按上述固定参数轮询。只有父任务统计整体收口且存在成功结果时，最终输出才可包含真实状态和真实返回图片，例如：“任务已完成，以下为生成结果。该内容为营销风格模拟，不代表真实买家评价。”若整体失败或超时，则只报告对应状态，不展示虚构结果，也不自动重新创建。
