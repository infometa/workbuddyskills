---
name: qinghu-ai-unified
display_name: 青虎AI
display_name_en: Qinghu AI
description: 青虎AI电商 SaaS 连接器，覆盖电商数据研究、选品与运营分析，以及 LinkPix 商品图、详情页、广告素材和短视频创作。适用于数据查询、达人与短视频研究、选品调研、生图、生视频、批量素材处理和视频本地化需求。
description_zh: 青虎AI电商 SaaS：数据研究、选品运营与 LinkPix 电商视觉创作。
description_en: Qinghu AI ecommerce SaaS for data research, product sourcing, operations analysis, and LinkPix visual creation.
version: 1.0.1
author: 广州青虎网络科技有限公司
user-invocable: true
---

# 青虎AI：电商数据与视觉创作

青虎AI在同一连接器中提供两条独立工作流：**电商数据研究**和 **LinkPix 电商视觉创作**。先按用户目标选择工作流，不能把创作产物表述为数据查询结果，也不能把分析建议表述为已经修改店铺或发布内容。

## 认证与素材

用户在 WorkBuddy 的连接器表单中填写 API 密钥和站点后，客户端自动注入鉴权请求头。不要让用户在对话中再次发送密钥。

- `prod` 为国内版 iqinghu.com；`intl` 为国际版 autoagc.com，账号和密钥不通用。
- 未配置时，引导用户在连接器设置中填写密钥；国内版可从 https://www.iqinghu.com/workbench/dashboard/api-keys 创建。
- MCP 运行在云端。图片、视频等附件只传可公开访问的 `http(s)` URL；不传用户电脑上的本地路径。

## 工作流 A：数据研究、选品与运营分析

适用：达人和短视频数据、选品调研、竞品比较、运营复盘，以及当前目录明确提供的商品、店铺、评论、热搜或货源数据应用。

1. 先用 `list_models(kind="workflow")` 查看当前真实开放的数据应用；产品截图或网页功能不等于已通过 MCP 开放。
2. 用 `model_options(kind="workflow", model_label=...)` 读取字段、支持平台和权限要求。
3. 用相同参数执行 `estimate_cost(kind="workflow", params=...)`，说明查询对象、范围、订阅权益和预计积分。
4. 得到用户确认后，才以 `confirmed=true` 调用 `run_workflow`；保存 `workflow_log_id` 并用 `task_status` 查询进度。
5. 结果交付时说明数据来源、查询对象、时间范围、样本量和缺失字段；明确区分实际统计、平台估算和分析推断。

没有目录或工具明确支持的细分平台数据时，说明当前连接器尚未接入，不编造应用 code、参数或数据。云设备、店铺写入、上货等操作，只有当前工具确实存在且用户明确授权范围后才执行。

## 工作流 B：LinkPix 电商视觉创作

适用：商品主图、详情页、场景图、广告素材、带货视频、批量图片处理、视频翻译与编辑、爆款内容研究、分镜、POD 和可用的 AI 工作流。下方的 LinkPix 操作手册给出精确的意图路由、报价、确认和轮询规则。

## 共同的提交和交付规则

- `account`、`list_models`、`model_options`、`estimate_cost`、`task_status` 为只读操作，可直接调用。
- 对任何会消耗积分、创建任务或写入外部系统的调用，必须先展示关键参数、素材、范围和 `estimate_cost` 返回的费用，并取得用户确认。
- 返回 `pending` 时按任务 ID 轮询；返回失败时按实际 `stage` 和 `message` 处理，避免重复提交和重复扣费。
- 输出时把“分析/创作建议”“待验证信息”和“已完成的实际结果”分开说明。

# LinkPix 电商视觉创作操作手册

# 青虎AI — 电商素材生成

本技能教你调用**已经连上的青虎 MCP 工具**。参数 schema 以工具定义为准，这里只写路由、硬规则和 WorkBuddy 上的注意点。

连接器连的是云端服务 `https://www.iqinghu.com/mcp`，不是本机 CLI。

## 1. 鉴权（不要再向用户要密钥）

用户在连接器表单里填过 API 密钥和站点（`prod` 国内版 / `intl` 国际版）后，WorkBuddy 会把它们注入请求头。之后：

- **不要**再让用户把密钥发到对话里，也不要让他们配 `Authorization`。
- 先发任务前可以跑一次 `account`。`configured=true` 即可继续。
- `account` 或任何工具返回 `stage="config"`：请用户打开连接器重新填写密钥，并确认站点与密钥所属站点一致（选错会 401）。两站账号、密钥互不通用。
- 用户还没有密钥：国内版先登录 https://www.iqinghu.com/workbench/login?urlCode=agentwb ，再到 https://www.iqinghu.com/workbench/dashboard/api-keys 创建；国际版把域名换成 `www.autoagc.com`。图文说明：https://xcnzsfe4uxrw.feishu.cn/wiki/KJ0Ywsyw8iAXmRkz5l4cddDbn6g

## 2. 素材必须是公网 URL

远端 MCP **读不到用户电脑上的路径**。`images` / `videos` / 工作流上传类字段只接受 `http(s)` URL。

- 用户给了可访问的链接：原样传入。
- 当前对话已经提供了附件的公网地址：用那个地址。
- 用户只给了本机路径（如 `C:\...`、`/Users/...`）：说明连接器在云端跑，读不到这台电脑，请他们改传公网链接或先把图传到可访问的位置。**不要**把本机路径传给任何工具，也不要调用 `upload_media` 去读本机文件。

图片有 **10MB** 硬上限。3MB 以上的图上传后可能带缩略提示（`notices`），那是提示不是错误。

## 3. 意图路由

| 用户想要 | 工具 | 产物 |
|---|---|---|
| 商品图 / 主图 / 一组营销图 | `generate_image`（套图模式） | 图片 |
| 按文字直出商业大图（可带参考图） | `generate_image`（智慧模型等） | 图片 |
| 详情页长图 | `generate_image`（电商详情图） | 图片 |
| 一批不同内容的图（多提示词 / 批量改 / 换产品 / 复刻主图 / 服装姿势 / 译图） | `generate_image_batch` | 图片 |
| 要控模型、画幅、参考图语义的带货/广告视频 | `generate_video` | 视频 |
| 「丢几张图出一条能投的片子」/ 把视频里的人换掉 | `generate_quick_video` | 视频 |
| 视频翻译（字幕 / 配音 / 对口型） | `translate_video` | 视频 |
| 去水印 / 去字幕 / 画质提升 | `edit_video` | 视频 |
| 拆爆款视频要可复用脚本 | `replicate_hot_video` | 脚本文本 |
| 爆款视频改写成图文 | `video_to_article` | 图文 |
| 分镜脚本 | `storyboard_script` | 文本（不扣生图积分） |
| 分镜图 | `generate_storyboard` | 图片 |
| 按投放模板出广告素材 | `generate_ad_material` | 视频或图片 |
| 印花提取 / 贴合 / 裂变 | `generate_pod_material` | 图片 |
| 工作台里的 AI 应用（仿拍、TVC、超清修复、数据引擎…） | `run_workflow` | 按应用而定 |
| 写一条生图提示词 | `polish_prompt` | 文本 |

先看产物是图、视频还是文本，再看输入是文字、图，还是已有视频/链接。表里没有的需求，先 `list_models(kind="workflow")`；仍然没有就明确说不支持，**不要硬套最接近的工具**。

音乐/MV、数字人口播、直播切片、长视频剪辑：当前不支持。

## 4. 标准流程

```
list_models(kind)
  → model_options(kind, model_label)
  → estimate_cost(kind, ...)
  → 向用户确认参数与积分
  → <提交工具> confirmed=true
  → task_status 轮询到 stage=done
```

只读工具可直接调用：`account` / `list_models` / `model_options` / `estimate_cost` / `task_status` / `polish_prompt` / `storyboard_script`。

`kind`：`image` / `video` / `image_batch` / `quick_video` / `video_translate` / `video_edit` / `hot_video` / `video_to_article` / `storyboard` / `ad` / `pod` / `workflow`。`list_models` 另外还有 `character`、`pod_product`。

`estimate_cost`：`kind=image` / `video` 时参数平铺；**其余 kind 把提交参数原样放进 `params`**。

## 5. 两条硬规则

**报价只能来自 `estimate_cost`。** `list_models` 的 `credits` 是目录单价，不含折扣、画质、张数和免费额度，不能报给用户。要把积分数字说出口，必须用**与提交完全相同的参数**跑 estimate，报它的 `credits`；`enough=false` 时先说余额不足。

没有报价接口的三个能力：`translate_video`、`replicate_hot_video`、`video_to_article`。estimate 会返回 `credits: null` —— 如实转述「以实际扣费为准」，不要换算、不要编数字。仍需用户明确同意后再带 `confirmed=true`。

**提交前必须确认。** 把模型/模式/模板/应用、数量、尺寸或时长画幅、语言、用到哪些素材、预计积分一次性列清，等明确同意。任务提交后不可取消。批量工具（`generate_image_batch` / `generate_ad_material` / `generate_pod_material`）要说清子任务数。未带 `confirmed=true` 会被 `stage="confirm"` 拒绝。

用户给了商品图就传入对应图片字段，不要只把图意转写成 prompt。

## 6. 选型与轮询

- 生图未指定模型：用「智慧模型」。一组风格统一的主图用「套图模式」（默认 9 张，必须把张数和积分说清楚）。详情页用「电商详情图」。尺寸表逐模型不同，用 `model_options` 查，标签必须逐字一致。
- 视频模型随线上目录变，先 `list_models(kind="video")`。省积分可看「全能电商2.0」；参考图是否必填以 `model_options` 为准。
- 工作流：列表 → `model_options` 查表现字段（线上随时变，禁止凭记忆填）→ 报价 → 确认 → `run_workflow`。
- 广告模板会覆盖模型，不要自己挑模型。

提交工具**立刻返回任务 ID**，必须自己轮询 `task_status`，按提交返回的那个 ID 字段传，一次只传一个：

| 提交返回 | 间隔 | 参考耗时 |
|---|---|---|
| `batch_task_id` | 15–30 秒 | 1–14 分钟 |
| `video_task_id` | 30–60 秒 | 最长 40 分钟，提前告知 |
| `inspire_task_id` | 15 秒 | 通常 1 分钟；超过 10 分钟仍在分析可视作失败 |
| `image_text_id` | 15 秒 | 1–3 分钟 |
| `pod_task_id` | 5–15 秒 | 1–14 分钟 |
| `workflow_log_id` | 15 秒 | 按应用 |

`stage=pending` 继续等；`done` 取产物；`completed` 但产物链接为空则继续轮询。停止轮询不影响后端继续跑，任务 ID 要留给用户。

## 7. 失败与交付

按返回的 `stage` 处理，不要盲着重试：

- `config`：重新连接连接器，见第 1 节
- `params`：按 message 改参数
- `confirm`：走完第 5 节再带 `confirmed=true`
- `upload` / `submit`：转述 message（积分不足、审核未过、模型维护、未订阅）
- `poll` / `timeout`：任务可能仍在跑，用任务 ID 再查
- `rate_limit`：按 message 等待，不要立刻重试

`run_workflow` 若带 `log_id_uncertain: true`，交付前请用户到青虎工作台核对。

产物从 `images` / `videos` / `primary_video` / `files` / `video_script` / `article` / `texts` / `script` 取。按当前对话环境的媒体约定发送，和「生成完成」写在同一轮，并告知实扣积分（工作流以返回的 `credits` 为准）。不要只甩一串裸 URL。
