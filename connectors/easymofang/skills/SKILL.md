---
name: easymofang
display_name: 易智魔方
display_name_en: EasyMofang
description: "商品文案/图片商标侵权检测，以及电商套图生成与重绘（白底图、场景图、功能图、对比图、尺寸图、普通A+、普通A+裁剪版、高级A+；平台 Amazon/亚马逊、AliExpress/速卖通、OZON、Walmart/沃尔玛、TEMU、Allegro、TikTok、Mercado Libre、Shopee/虾皮、eBay、Wayfair）"
description_zh: "商品文案/图片商标侵权检测，以及电商套图生成与重绘（白底图、场景图、功能图、对比图、尺寸图、普通A+、普通A+裁剪版、高级A+；平台 Amazon/亚马逊、AliExpress/速卖通、OZON、Walmart/沃尔玛、TEMU、Allegro、TikTok、Mercado Libre、Shopee/虾皮、eBay、Wayfair）"
description_en: "Product Copy/Image Trademark Infringement Detection, plus E-commerce Image Set Generation & Redrawing (white-background images, lifestyle/scene images, feature images, comparison images, size/dimension images, Standard A+, Standard A+ Cropped, Premium A+; platforms: Amazon, AliExpress, OZON, Walmart, TEMU, Allegro, TikTok, Mercado Libre, Shopee, eBay, Wayfair)"
version: "1.0.2"
author: "易佰网络"
---

# 易智魔方

通过 MCP 调用易智魔方能力：侵权检测（文案 / 图片）、图片上传、电商套图生成（白底图、场景图、功能图、对比图、尺寸图、普通A+、普通A+裁剪版、高级A+；平台 Amazon/亚马逊、AliExpress/速卖通、OZON、Walmart/沃尔玛、TEMU、Allegro、TikTok、Mercado Libre、Shopee/虾皮、eBay、Wayfair）。

## 认证

- 标准 MCP OAuth：首次使用会自动打开浏览器，登录易智魔方并点「允许」即完成连接，**不需要手填 API Key**。
- 访问令牌与刷新令牌由 WorkBuddy 保管并自动续期，工具调用时无需关心，**不要**向用户索要 Key 或 Token。
- 本机图片上传走 `get_image_upload_url` 签发的短时地址，同样**不需要** API Key。
- 令牌只能访问本 Skill 涉及的易智魔方接口，不等于完整登录态。

## 错误处置

工具失败时返回的文案已按类别归一，**直接转述给用户即可，不要改写成自己的猜测**。按下表判断后续动作：

| 返回文案开头 | 含义 | 该做什么 |
|---|---|---|
| 账户魔豆余额不足 | 账户余额不够支付本次操作 | 让用户去易智魔方**充值**。文案括号里带了当前余额与本次所需，可一并转述 |
| 未获取到用户身份 / HTTP 401 | 授权已过期或被撤销 | 让用户**重新授权**（在连接器里断开后重新连接，会再次打开浏览器） |
| 无权访问该接口 / HTTP 403 | 本次调用超出了授权范围 | 这是能力边界，不要重试；告知用户该操作需到易智魔方网站完成 |
| 请求过于频繁 / 上一次请求还在处理中 | 限流或并发冲突 | 稍等几秒后**可以重试**，不必改参数 |
| 内容未通过审核 | 文案或素材含违规内容 | 让用户调整文案或更换素材，括号里说明了被拦的字段 |
| 易智魔方服务暂时不可用 | 服务端异常 | 稍后重试；连续失败则建议用户联系客服 |

其余文案（如「参数 xxx 不能为空」「仅支持 jpg/jpeg/png/webp 格式」）是**入参问题**，按提示修正参数后重试，不要向用户报错。

余额类错误发生在扣费之前，**不会产生消耗**，用户充值后可直接重试同样的请求。

## 关键约束（必读）

1. **套图调用顺序**：① 本机图先 `get_image_upload_url` 再 multipart 直传到返回的 `uploadUrl`（或公网图用 `upload_image`）拿 `objectKey` → ② `product_image_series_image_settings` 取 `taskType` / `quality` / `ratio` → ③ `product_image_series_brand_config` 取品牌风格枚举 → ④ 可选 `product_image_series_generate_title` 生成 `productInfo` → ⑤ `product_image_series_submit`。枚举值由服务端配置驱动，**不要凭猜测填写**。
2. **objectKey 与 URL 不能混用**：套图的 `productImages` / `referenceImage` 只认上传返回的 `objectKey`（含 `://` 的值会被拒绝）；`image_compliance_*` 只认公网 `imageUrl`，已有公网地址时不必先上传。
3. **异步与轮询（必须遵守停表规则）**：`product_image_series_submit` / `product_image_series_redraw` 只返回任务标识（`waterNo` / `taskId`）。产物用 `product_image_series_query_tasks` 轮询，**必须带 `waterNo`，只看 `items[0]`**。主任务成功值是 `COMPLETED`，**没有 `SUCCESS`**。`items[0].status`：`PENDING` / `SUBMITTED` → 等 5～8 秒再查；**`COMPLETED` 且 `success=true` → 立刻停止轮询**，把 `subtasks[].result`（OBS key，没有 `https://` 也算成功）展示给用户；**`COMPLETED` 且 `success=false` → 立刻停止**并说明失败。子任务全部为 `SUCCESS` / `FAILED` 也是终态。最多查 20 次，超时让用户去易智魔方查看，禁止无限轮询。
4. **计费**：`text_compliance_check`、`image_compliance_check`、`product_image_series_submit`、`product_image_series_redraw` 扣魔豆；其余工具不计费。
5. **上传限制**：禁止把图片编成 base64 塞进 MCP（请求体过大会被拒）。本机图片：`get_image_upload_url` → curl 到返回的 `uploadUrl`；已有公网地址用 `upload_image(imageUrl)`。仅 jpg/jpeg/png/webp，10MB 以内。

支持的上架国家代码（侵权检测 `country`）：`US` / `UK` / `DE` / `JP` / `CA` / `AU` / `FR` / `IT` / `ES` / `NL` / `SE` / `PL` / `IN` / `SG` / `AE` / `SA` / `IE` / `BR` / `MX` / `TR` / `BE` / `EG` / `ZA`。

---

## 一、图片上传

### 本机图片：先申请上传地址再 multipart 直传

MCP 入参是 JSON，不能传文件；OAuth 令牌由 WorkBuddy 保管，也不能用于 curl。本机图片请：

1. 调用 `get_image_upload_url`（无入参），拿到 `uploadUrl`（约 5 分钟有效、一次性）
2. 对本机文件直传（**不要**带 `Authorization`，**不要**要用户提供 API Key）：

```bash
curl -X POST "$uploadUrl" \
  -F "file=@/path/to/product.jpg"
```

- 成功：返回 JSON，取 `objectKey` 填套图的 `productImages` / `referenceImage`
- 失败：HTTP 401 表示票无效/已用/过期，重新调 `get_image_upload_url`；HTTP 400 + 纯文本原因（如「审核未通过」「仅支持 jpg/jpeg/png/webp 格式」）
- 限制：jpg/jpeg/png/webp，10MB 以内；表单字段名必须是 `file`（与返回的 `formField` 一致）
- **不要**把图片编成 base64 塞进 MCP 工具参数（请求体过大，WorkBuddy 会拒绝）

### get_image_upload_url - 申请本机上传地址

无入参。返回 `uploadUrl` / `expiresIn` / `formField`。不计费。同一账号未消费票上限 3 张。

### upload_image - 按公网 URL 上传到 OBS

仅当图片已有公网可访问地址时使用。返回 `objectKey`（给套图）与 `objectUrl`。不计费。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| imageUrl | string | ✅ | 公网可访问图片地址，服务端下载后上传 |

---

## 二、侵权检测

### text_compliance_parse_amazon_link - 解析亚马逊链接

抓取 ASIN、站点国家、标题与描述，用于填充 `text_compliance_check`。不计费。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| url | string | ✅ | 亚马逊商品详情页链接，需包含 ASIN |

### text_compliance_check - 文案商标侵权检测

同步返回风险词清单。每次调用扣除魔豆。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| title | string | ✅ | 产品标题 |
| country | string | ✅ | 上架国家代码，见上文列表 |
| description | string | - | 产品描述或五点描述 |
| sku | string | - | SKU，仅归档 |
| productLink | string | - | 商品链接，仅归档 |
| asin | string | - | ASIN，仅归档 |

### text_compliance_recent - 最近文案检测记录

不计费。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| size | integer | - | 返回条数，默认 20，上限 50 |

### image_compliance_ocr - 图片 OCR

识别图片文字，结果可作为 `image_compliance_check` 的 `ocrText`。不计费。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| imageUrl | string | ✅ | 图片公网 URL |

### image_compliance_check - 图片商标侵权检测

同步返回风险词。每次调用扣除魔豆。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| imageUrl | string | ✅ | 图片公网 URL |
| country | string | ✅ | 上架国家代码 |
| ocrText | string | - | 图片文字；留空则服务端自动 OCR |
| sku | string | - | SKU，仅归档 |

### image_compliance_recent - 最近图片检测记录

不计费。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| size | integer | - | 返回条数，默认 20，上限 50 |

---

## 三、电商套图

### product_image_series_brand_config - 品牌风格可选值

无入参。返回销售国家/地区、生成图片语言、发布平台、品牌主色、智能字体风格。提交前先调。不计费。

发布平台 `publishPlatforms`（`submit` 的 `publishPlatform`，填英文值）：

| 取值 | 中文名 |
|------|--------|
| Amazon | 亚马逊 |
| AliExpress | 速卖通 |
| OZON | — |
| Walmart | 沃尔玛 |
| TEMU | — |
| Allegro | — |
| TikTok | — |
| Mercado Libre | — |
| Shopee | 虾皮 |
| eBay | — |
| Wayfair | — |

### product_image_series_image_settings - 图片设置可选值

无入参。返回图位类型（imageTypes）、A+ 类型（aPlusTypes）、画质（qualities）、比例（ratios）。`submit` 的 `tasks[].taskType`、`quality`、`ratio` 必须取自本工具或下列枚举。不计费。

图位类型 `imageTypes`（`tasks[].taskType`）：

| taskType | 名称 | 支持模板 |
|----------|------|:--------:|
| WHITE_BG_IMAGE | 白底图 | 否 |
| PRODUCT_IMAGE | 场景图 | 是 |
| FEATURE_IMAGE | 功能图 | 是 |
| COMPARISON_IMAGE | 对比图 | 是 |
| SIZE_IMAGE | 尺寸图 | 是 |

A+ 类型 `aplusTypes`（同样填入 `tasks[].taskType`）：

| taskType | 名称 | 支持模板 | 说明 |
|----------|------|:--------:|------|
| A_PLUS_CROP_IMAGE | 普通A+（裁剪版） | 是 | beta |
| A_PLUS_IMAGE | 普通A+ | 是 | |
| A_PLUS_ADVANCED_IMAGE | 高级A+ | 是 | 可同时出手机 A+（`generateMobileAPlus`） |

画质 `qualities`：`1K` / `2K` / `4K`。

比例 `ratios`：`1:1` / `2:3` / `3:2` / `3:4` / `4:3` / `4:5` / `5:4` / `9:16` / `16:9` / `21:9`。

### product_image_series_generate_title - 生成/润色标题与卖点

同步返回，结果可作为 `submit` 的 `productInfo`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| productImages | string[] | ✅ | 商品图 OBS objectKey 列表（来自 upload_image），至少一张 |
| title | string | - | 已有标题则润色，否则由图片生成 |
| sellingPoints | string | - | 已有卖点则润色，否则由图片生成 |

### product_image_series_submit - 提交套图任务

异步：立即返回 `waterNo` / `taskId`，产物用 `product_image_series_query_tasks(waterNo)` 轮询。主任务完成是 `COMPLETED`（不是 `SUCCESS`），见到即停，规则见关键约束第 3 条。按生成张数扣魔豆。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| productImages | string[] | ✅ | 商品图 OBS objectKey 列表 |
| tasks | object[] | ✅ | 图位配置，至少一项，见下表 |
| quality | string | ✅ | 画质：`1K` / `2K` / `4K` |
| ratio | string | ✅ | 比例：`1:1` / `2:3` / `3:2` / `3:4` / `4:3` / `4:5` / `5:4` / `9:16` / `16:9` / `21:9` |
| productInfo | string | - | 产品信息（标题+卖点+品牌）；带文案的图位依赖它 |
| sku | string | - | SKU，表单回显 |
| brandMainColor | string | - | 品牌主色，取值见 brand_config |
| intelligentFontStyle | string | - | 智能字体风格，取值见 brand_config |
| salesCountry | string | - | 销售国家/地区，取值见 brand_config |
| generatedImageLanguage | string | - | 生成图片语言，取值见 brand_config |
| publishPlatform | string | - | 发布平台：`Amazon`（亚马逊）/ `AliExpress`（速卖通）/ `OZON` / `Walmart`（沃尔玛）/ `TEMU` / `Allegro` / `TikTok` / `Mercado Libre` / `Shopee`（虾皮）/ `eBay` / `Wayfair` |
| customSettings | string | - | 自定义设置 |

`tasks[]` 字段：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| taskType | string | ✅ | 图位类型：`WHITE_BG_IMAGE`（白底图）/ `PRODUCT_IMAGE`（场景图）/ `FEATURE_IMAGE`（功能图）/ `COMPARISON_IMAGE`（对比图）/ `SIZE_IMAGE`（尺寸图）/ `A_PLUS_CROP_IMAGE`（普通A+裁剪版）/ `A_PLUS_IMAGE`（普通A+）/ `A_PLUS_ADVANCED_IMAGE`（高级A+） |
| count | integer | ✅ | 该图位生成张数，正整数 |
| baseOnProductInformation | boolean | - | 是否在图上带产品文案，默认 false |
| describe | string | - | 该图位补充描述 |
| referenceImage | string | - | 参考图 OBS objectKey |
| generateMobileAPlus | boolean | - | 仅 `A_PLUS_ADVANCED_IMAGE` 生效，是否同时出手机 A+ |
| templateId | string | - | 模板 ID，A+ 裁剪图用 |

### product_image_series_redraw - 单张重绘

异步：结果用 `product_image_series_query_tasks(waterNo)` 轮询。见到 `COMPLETED` 立刻停止。按张扣魔豆。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| subtaskId | string | ✅ | 子任务 ID，来自 query_tasks |
| describe | string | - | 新描述/提示词；留空则复用原子任务 |

### product_image_series_query_tasks - 查询套图任务

分页查询任务与产物，用于轮询 submit / redraw。不计费。轮询时**必须传 `waterNo`**，只解读 `items[0]`，不要扫整页其它历史任务。

返回是分页结构：`{ current, size, total, items[] }`。看 `items[0]`：

| 字段 | 取值 | 该做什么 |
|------|------|----------|
| status | `PENDING` / `SUBMITTED` | 未完成。等 5～8 秒后再查一次 |
| status + success | `COMPLETED` 且 `success=true` | **立刻停止轮询**。把 `subtasks[].result` 展示给用户 |
| status + success | `COMPLETED` 且 `success=false` | **立刻停止轮询**。告知失败 |
| subtasks[].status | `SUCCESS` / `FAILED` | 该子任务已终态。全部子任务都是二者之一也可停 |
| subtasks[].result | OBS key 数组，如 `["xxx.png"]` | 这就是产物。**不是 URL**，没有 `https://` 也算成功，不要继续查 |

主任务**没有** `SUCCESS` 这个状态，完成就是 `COMPLETED`。最多轮询 20 次。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page | integer | - | 页码，从 1 开始，默认 1 |
| size | integer | - | 每页条数，默认 5 |
| waterNo | string | - | 任务流水号，来自 submit 返回；轮询时必传 |

---

## 使用示例

- 文案检测：可先 `text_compliance_parse_amazon_link`，再把标题/描述/国家填入 `text_compliance_check`。
- 图片检测：已有公网图直接 `image_compliance_check`；可选先 `image_compliance_ocr`。
- 套图：按「关键约束」中的顺序调用；提交后用 `waterNo` 查 `product_image_series_query_tasks`。看到 `items[0].status=COMPLETED` 立即停止（`success=true` 展示 `subtasks[].result`，`success=false` 说明失败）。
- 某张图不满意：用返回的 `subtaskId` 调 `product_image_series_redraw`，再用同一 `waterNo` 轮询，同样在 `COMPLETED` 时停止。
