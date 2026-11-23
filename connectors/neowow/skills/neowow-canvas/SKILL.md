---
name: neowow-canvas
display_name: Neowow 创作画布
display_name_en: Neowow Canvas
description: 在 Neowow 画布上用 AI 生成图片、视频、配音和音乐，放置脚本文本、连线，样片转正式，并查询进度、积分与预估费用。触发词：Neowow、画布、生图、文生图、图生图、分镜图、分镜脚本、海报、图生视频、文生视频、短视频、配音、旁白、有声剧、音乐、歌曲、配乐、样片、转正式、文本节点、连线、积分余额、多少积分。
description_zh: 连接 Neowow 账号，在画布项目里批量生成图片、视频、配音和音乐，把脚本/分镜放成文本节点并连线，生成前试算积分，样片转正式，轮询生成进度，查询积分余额。
description_en: Connect your Neowow account to generate images, videos, voice-overs and music in canvas projects, estimate points before generating, convert draft videos to final, poll task progress and check your points balance.
version: 1.0.0
author: Neowow
examples_zh:
  - 新建项目「赛博长安」并生成 4 张 16:9 海报
  - 把这张图做成 5 秒竖屏视频
  - 给这段台词生成旁白配音
examples_en:
  - Create a project called "Cyber Chang'an" and generate four 16:9 posters
  - Turn this image into a 5-second vertical video
  - Generate a voice-over narration for this script
---

# Neowow 创作画布

当用户需要在 Neowow 上生成图片、视频、配音或音乐，或查看项目、生成进度、积分余额与预估费用时，按以下步骤执行。

## 一、前置条件

1. 需要 Neowow 账号。首次调用任何工具时，客户端会打开浏览器让用户登录 neowow.cn 并授权，授权完成后回到对话继续。
2. 生成会消耗账号积分，积分在 neowow.cn 充值。生成前可用 `get_points_balance` 查看余额。
3. 所有生成结果都落在某个画布项目里，必须先有 `project_id`。
4. 授权范围（scope `canvas`）：授权后，连接器可以查看和新建你的画布项目、在项目里添加节点和连线、提交图片/视频/音频/音乐生成和样片转正式（扣你的积分）、取消自己还在排队的任务（积分退回）、查询生成进度、节点生成历史、积分余额和预估费用、把参考素材上传到你的账号。它**不能**删除节点或连线、改动画布上已有的内容（只会把生成结果回填进自己提交的节点）、修改账号资料或密码、查看订单和支付，也不能访问你没有权限的项目。授权只对连接器有效，不能用来登录网页端。
5. 授权会过期：过期后连接器会提示「未认证，请重新连接 Neowow」，按第六节处理。用户在客户端里断开连接后，需要重新授权才能继续用。

## 二、标准流程

1. **选项目**：用户没指定项目时，调 `list_projects` 列出最近的项目让用户选；要新建就调 `create_project`。
2. **选模型**：调 `list_models`（`type` 为 `image` 或 `video`；要延长 / 编辑已有视频用 `video_extend` / `video_edit`），按用户需求推荐模型。尺寸、比例、分辨率、时长等取值都必须来自该模型的返回值，不要自己编。音频不需要选模型。
3. **（可选）上传参考素材**：用户提供本地图片/音频/视频作参考时，先调 `get_upload_url` 拿到上传地址，再用 `curl -X PUT` 上传（见第三节 `get_upload_url`），之后用返回的 `file_url` 作参考素材。
4. **试算积分**：用和正式提交**完全相同的参数**调 `estimate_points`（免费，不建节点、不扣分），拿到 `points`。视频带参考视频时返回里会有 `warning`，报价时必须告诉用户：**带参考视频试算可能不准，实际以扣除为准**。
5. **确认并提交**：按第五节复述参数和预估积分、取得用户明确同意后，调 `generate_image` / `generate_video` / `generate_audio` / `generate_music`。这些工具**只提交任务**，立即返回 `task_id` 和 `node_key`，不会等结果。提交后生成节点（显示「生成中」）、参考素材节点和它们之间的连线**立刻出现在画布上**，自动排在参考节点右侧、不和已有节点重叠。
6. **轮询结果**：用 `get_task_status` 查询 `task_id`。查到成功或失败时，结果会**自动存进对应节点**（返回 `saved_to_node: true`），用户打开网页就能看到。
   - 图片：每 10–15 秒查一次，最长 20 分钟；
   - 视频：每 30–60 秒查一次，最长 2 小时，等待时间长可以告诉用户「稍后再问我进度」；
   - 音频、音乐：每 15–30 秒查一次。
   - 用户改主意、不想等了：还在排队（`PENDING`）的图片或视频任务可以用 `cancel_task` 取消，积分退回。
7. **展示结果**：`status` 为 `SUCCESS` 时，用 Markdown 展示 `result_urls`（图片用 `![](url)`，视频/音频给链接），并附上项目的 `web_url`，方便用户去网页端继续编辑。
8. **接着用上一步的结果**：图生视频、拿生成的图再改、用生成的配音做视频时，把上一步返回的 `node_key` 放进下一次 `generate_*` 的 `reference_node_keys`，画布上会自动连线。被引用的节点必须已经生成成功。
9. **放脚本、补连线**：用户给了现成的脚本、分镜、文案时，用 `create_text_node` 放成文本节点（可顺手连到已有节点），之后生成时把它的 `node_key` 放进 `reference_node_keys`；两个已有节点之间漏了连线，用 `connect_nodes` 补上。这两个工具不扣积分，不用事先确认。
10. **样片转正式**：视频想先低价看效果时，用 `list_models` 里 `draft_model: true` 的样片模型生成；用户满意后，先 `estimate_points`（`type=draft_to_formal`）报价，同意后调 `convert_draft_to_formal` 出正式版。
11. **找回历史结果**：节点上只显示最近一次结果，用户想要之前某次生成的图/视频时，调 `get_node_history` 查。

## 三、工具说明

所有工具出错时都返回 `isError=true` 的文本结果，处理方式见第六节。

### list_projects — 列出我的项目

| 参数 | 类型 | 必填 | 默认 | 说明 |
|--|--|--|--|--|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 10 | 每页条数，1–20 |

返回：
```json
{"total": 12, "page": 1, "page_size": 10,
 "projects": [{"project_id": "2096…", "title": "赛博长安", "updated_at": "2026-10-31 15:00:00", "web_url": "https://neowow.cn/…"}]}
```

### create_project — 新建项目

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| title | string | 是 | 项目标题 |
| description | string | 否 | 项目描述 |

示例：`create_project({"title": "赛博长安"})` → `{"project_id": "2096…", "title": "赛博长安", "web_url": "…"}`

### get_canvas — 查看画布节点清单

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| project_id | string | 是 | 项目 ID |
| node_type | string | 否 | `image` / `video` / `text` / `audio` 过滤 |

返回：
```json
{"total": 12, "nodes": [{"node_key": "6f1c…", "type": "image", "label": "海报1 朱雀大街", "status": "SUCCESS",
  "result_url": "https://…/xx.png", "x": 520, "y": 100}]}
```
最多 50 个节点，新建的在前。按标题找节点时看 `label`；`node_key` 可以填进 `generate_*` 的 `reference_node_keys`。`status`：图片/视频 `PENDING` 生成中、`SUCCESS`、`FAILED`；音频 `running` 生成中、`SUCCESS`、`error`；上传素材节点为 `idle`。查看时会顺带把已出结果的生成中节点（自己提交的）存进节点。

### get_nodes — 查看节点详情

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| project_id | string | 是 | 项目 ID |
| node_keys | string[] | 是 | 1–10 个 nodeKey |

生成类节点的成品地址在 `generated_output_url`；`data` 里的 `inputImageUrls` 是当时的输入参考图，不是成品。

### create_text_node — 把脚本、分镜、文案放成文本节点

| 参数 | 类型 | 必填 | 默认 | 说明 |
|--|--|--|--|--|
| project_id | string | 是 | | 项目 ID |
| title | string | 否 | 文本 | 节点标题，如「第1集 分镜脚本」 |
| content | string | 是 | | 正文原文，最多 32000 字，超了拆成多个节点 |
| connect_to_node_keys | string[] | 否 | | 建好后把文本节点连到这些已有节点当提示词输入，最多 10 个；可连图片、视频、音频、文本节点，上传素材节点不能连。任一个不合法时整次报错、什么都不写 |

适用场景：
- 用户给了现成的脚本、分镜、文案或人物设定，想留在画布上：先放成文本节点，之后 `generate_image` / `generate_video` 把它的 `node_key` 放进 `reference_node_keys`，正文会自动拼在提示词前面，画布上也会连线。`generate_audio` 不拼，台词照常写进 `text_prompt`。
- 画布上已经有图片、视频节点，想把对应的分镜挂上去：传 `connect_to_node_keys`，文本节点放在这些节点左边一列并连好线，用户在网页上重新生成时会带上这段文字。

示例（先把分镜脚本放成文本节点，同时连到已有的图片节点）：
```json
{"project_id": "2096…", "title": "第1集 分镜脚本", "content": "镜头1：雨夜长街，远景，霓虹倒影\n镜头2：主角回头，近景", "connect_to_node_keys": ["6f1c…"]}
```
返回：`{"node_key": "a3d9…", "connected": ["6f1c…"]}`

### create_upload_node — 把上传的文件放上画布

先 `get_upload_url` + `curl -X PUT` 上传成功，再调它把文件建成画布上的上传素材节点（不扣积分，图片会做一次内容审核）。

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| project_id | string | 是 | 项目 ID |
| file_url | string | 是 | `get_upload_url` 返回的 `file_url`，必须已 PUT 成功 |
| title | string | 否 | 节点标题，默认取文件名 |
| media_type | string | 否 | `image` / `video` / `audio`，不传按扩展名判断；传了要和扩展名一致 |

适用场景：
- **用户本地的视频要延长或编辑**：`generate_video` 的 `source_node_key` 只收画布上的视频节点，本地视频要先建成上传节点（见 `generate_video` 的「本地视频延长 / 编辑」）。
- 一份素材要在多次生成里反复引用：建成节点后用 `reference_node_keys` 引用，画布上只有一个素材节点。

同一地址已经在画布上（之前上传过或就是某个生成结果）时直接返回那个节点，`created` 为 `false`，不会重复建。

示例：
```json
{"project_id": "2096…", "file_url": "https://…/neowow/…/clip.mp4", "title": "原片"}
```
返回：`{"node_key": "c71e…", "type": "video", "media_type": "video", "url": "https://…/clip.mp4", "title": "原片", "created": true, "project_id": "2096…"}`

### connect_nodes — 手动连线

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| project_id | string | 是 | 项目 ID |
| source_node_key | string | 是 | 上游节点（从它的输出口连出），如文本节点、已生成的图片节点 |
| target_node_key | string | 是 | 下游节点（连到它的输入口），如图片、视频、音频节点 |

连上后 target 会把 source 当输入：文本节点的正文进 target 的提示词，图片/视频/音频节点的成品进 target 的参考素材。成品取的是连线那一刻的，source 还在生成就等它成功后再连。只改连线和 target 的参考字段，不触发生成、不扣积分。

可连的方向：

| source | target |
|--|--|
| 文本 | 文本、图片、视频、音频 |
| 图片、视频 | 文本、图片、视频 |
| 音频 | 文本、视频、音频 |

以下情况会拒绝（返回「拒绝连接：…」）：source 和 target 是同一个节点；连上会让节点首尾相连成环；target 是上传素材节点；方向不在上表里（如音频连图片）。同一对节点之间已有连线时不会重复建（返回 `created: false`），但会重新把上游的结果刷给下游——上游后来才生成出结果时，再连一次即可。

示例（文本节点 `a3d9…` 已经在画布上，把它连到图片节点 `6f1c…`）：
```json
{"project_id": "2096…", "source_node_key": "a3d9…", "target_node_key": "6f1c…"}
```
返回：`{"edge_id": "e-a3d9…-6f1c…", "created": true, "source_handle": "text", "target_handle": "image"}`

### list_models — 可用模型

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| type | string | 是 | `image`、`video`、`video_extend`（视频延长模型）或 `video_edit`（视频编辑模型） |

图片返回 `model_name`、`display_name`、`description`、`points_per_image`（基础单价，实际扣费以平台为准）、`image_sizes`、`aspect_ratios`、`quality`、`max_reference_images`。
视频返回 `model_name`、`name`、`description`、`duration_range`（`min`/`max`/`step` 秒）、`generation_types[]`（该模型能用的生成方式，只会出现 `UNIVERSAL_TO_VIDEO`、`TEXT_TO_VIDEO`、`IMAGE_TO_VIDEO` 三种，每种下可用的 `resolution` 与 `aspect_ratios` 各不相同）、`max_reference`（参考图/视频/音频上限）；`draft_model: true` 的是样片模型（名字以 `-draft` 结尾，低价出样片，满意后用 `convert_draft_to_formal` 转正式）。
`video_extend` / `video_edit` 字段同视频，`generation_types` 只有一项 `VIDEO_EXTEND` / `VIDEO_TO_VIDEO`；比例一般只有 `auto`，分辨率可能是大写（如 `720P`），原样照抄。
`points_per_image` 只是基础价，报价以 `estimate_points` 为准（按尺寸/质量/参考图数和折扣算）。

### generate_image — 生成图片（1–4 张）

| 参数 | 类型 | 必填 | 默认 | 说明 |
|--|--|--|--|--|
| project_id | string | 是 | | 项目 ID |
| requests | object[] | 是 | | 1–4 项，每项生成 1 张，超过 4 项会被拒绝 |
| requests[].title | string | 是 | | 节点标题，如「分镜1 雨夜长街」 |
| requests[].model_name | string | 是 | | 来自 `list_models(type=image)` |
| requests[].prompt | string | 是 | | 提示词，建议英文 |
| requests[].aspect_ratio | string | 是 | | 如 `16:9`，须在模型 `aspect_ratios` 内 |
| requests[].image_size | string | 是 | | `1K` / `2K` / `4K`，须在模型 `image_sizes` 内 |
| requests[].quality | string | 否 | high | 仅 gpt-image 系：`low`/`medium`/`high`（2.5 另有 `xhigh`/`max`） |
| requests[].transparent_background | boolean | 否 | false | 透明底（抠图）：输出带透明通道的 PNG，只支持 `gpt-image-2.5-flare` / `gpt-image-2.5-sunburst`，其它模型传 true 会报错。用户要「透明背景」「抠图」「贴纸/图标/LOGO 去底」时用 |
| requests[].reference_node_keys | string[] | 否 | | 画布上已有节点的 `node_key`（≤10）：图片节点当参考图，文本节点的内容拼在提示词前面；自动连线 |
| requests[].image_urls | string[] | 否 | | 参考图 URL（≤10），只能是 `get_upload_url` 的 `file_url`（须已上传成功，会做图片审核）或本账号的生成结果 URL；会在画布上建成上传节点并连线（已在画布上的 URL 直接连那个节点） |

示例：
```json
{"project_id": "2096…", "requests": [
  {"title": "海报1 朱雀大街", "model_name": "<list_models 返回的 model_name>", "prompt": "Cyberpunk Tang-dynasty Chang'an avenue at night, neon lanterns, rain reflections, wide shot, cinematic lighting", "aspect_ratio": "16:9", "image_size": "2K"}
]}
```
返回：
```json
{"success": true, "items": [{"title": "海报1 朱雀大街", "node_key": "6f1c…", "task_id": "t_1a…"}],
 "web_url": "https://neowow.cn/…", "next": "已提交，用 get_task_status 传入 task_id 轮询结果"}
```
部分失败时 `success=false`，失败项带 `error`、没有 `task_id`（画布上的节点会标成失败并显示原因）；只轮询有 `task_id` 的项。

### generate_video — 生成视频（一次 1 条）

| 参数 | 类型 | 必填 | 默认 | 说明 |
|--|--|--|--|--|
| project_id | string | 是 | | 项目 ID |
| request | object | 是 | | 一条视频的参数 |
| request.title | string | 是 | | 节点标题 |
| request.model_name | string | 是 | | 来自 `list_models(type=video)`；延长 / 编辑来自 `list_models(type=video_extend / video_edit)` |
| request.prompt | string | 是 | | 视频提示词，中文即可；编辑时写要怎么改（换风格、替换元素等），延长时写接下来发生什么 |
| request.generation_type | string | 是 | UNIVERSAL_TO_VIDEO | 必须是该模型 `generation_types` 里有的：`UNIVERSAL_TO_VIDEO` 全能（文生/参考图/参考音频/参考视频，模型支持就优先用）；`TEXT_TO_VIDEO` 纯文生（不支持全能的模型用它，不能带图片/视频/音频参考，文本节点可以）；`IMAGE_TO_VIDEO` 首尾帧（用户明确要首尾帧，或模型不支持全能但要图生视频时用）；`VIDEO_EXTEND` 视频延长（已有视频接着往后生成）；`VIDEO_TO_VIDEO` 视频编辑（改已有视频的画面、换风格、替换元素）。传了模型不支持的方式会直接报错并告诉你可用的方式 |
| request.source_node_key | string | 延长/编辑必填 | | 仅 `VIDEO_EXTEND` / `VIDEO_TO_VIDEO`：画布上要延长或编辑的视频节点 `node_key`，须已生成成功；会自动连到新节点。不收 URL，只能是画布上的视频节点（生成的、网页端上传的，或用 `create_upload_node` 建的） |
| request.aspect_ratio | string | 是 | | `16:9`/`9:16`/`1:1`/`4:3`/`3:4`/`21:9`；Seedance 2.5 首尾帧模式传 `auto`；延长 / 编辑一般只有 `auto`（默认） |
| request.resolution | string | 是 | 720p | 须在模型该生成类型的 `resolutions` 内（原样照抄，可能是大写 `720P`）；用户没要求就用 720p；延长 / 编辑不传则用模型默认 |
| request.duration | integer | 是 | | 秒，须在模型 `duration_range` 内；`VIDEO_EXTEND` 是新增那一段的时长；`VIDEO_TO_VIDEO` 不用传，输出时长跟随原视频（服务端实测，传了也忽略） |
| request.reference_node_keys | string[] | 否 | | 画布上已有节点的 `node_key`，自动连线：图片节点当参考图（`IMAGE_TO_VIDEO` 下依次当首帧、尾帧），视频节点当参考视频，音频节点当参考音频，文本节点拼进提示词 |
| request.first_frame_image_url | string | 首尾帧需要首帧 | | 首帧图 URL；不传就用 `reference_node_keys` 里第一个图片节点 |
| request.last_frame_image_url | string | 否 | | 尾帧图 URL；不传就用 `reference_node_keys` 里下一个图片节点 |
| request.image_urls | string[] | 否 | | 参考图（全能模式） |
| request.audio_url | string[] | 否 | | 参考音频（字段名是单数，值是数组） |
| request.reference_video_urls | string[] | 否 | | 参考视频，仅 `max_reference.videos > 0` 的模型 |
| request.generate_audio | boolean | 否 | true | 用户明确要无声视频才传 false |

示例（图生视频，用上一步 `generate_image` 返回的图片节点）：
```json
{"project_id": "2096…", "request": {"title": "朱雀大街 推镜", "model_name": "<list_models 返回的 model_name>", "prompt": "镜头缓慢推进，霓虹灯笼随风摇晃，雨水反光，人群穿行", "generation_type": "UNIVERSAL_TO_VIDEO", "aspect_ratio": "9:16", "resolution": "720p", "duration": 5, "reference_node_keys": ["6f1c…"]}}
```
用户本地的图片先 `get_upload_url` 上传，再把 `file_url` 放进 `image_urls`。返回格式同 `generate_image`。

**本地视频延长 / 编辑**：`get_upload_url`（`file_name` 如 `clip.mp4`）→ `curl -X PUT` 上传、等 200 → `create_upload_node` 把 `file_url` 建成视频节点 → 用返回的 `node_key` 当 `source_node_key` 调 `generate_video`（`VIDEO_EXTEND` / `VIDEO_TO_VIDEO`）。编辑的输出时长由服务端实测原视频决定。

示例（把画布上已有的视频接着往后生成 5 秒；改画面就把 `generation_type` 换成 `VIDEO_TO_VIDEO`、模型换成 `video_edit` 列表里的，不传 `duration`）：
```json
{"project_id": "2096…", "request": {"title": "朱雀大街 延长", "model_name": "<list_models(type=video_extend) 返回的 model_name>", "prompt": "镜头继续推进，主角转身走入雨中", "generation_type": "VIDEO_EXTEND", "source_node_key": "9a2e…", "aspect_ratio": "auto", "resolution": "720p", "duration": 5}}
```
延长 / 编辑都按原视频的实际时长另外计费（编辑：只按原视频时长；延长：原视频时长 + 新增时长），提交前务必先 `estimate_points` 报价。

### generate_audio — 生成音频

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| project_id | string | 是 | 项目 ID |
| title | string | 是 | 节点标题，如「客栈夜话 配音」 |
| text_prompt | string | 是 | 声音剧本：按时间线写对白（保留原文）、音效、配乐。成片约 2 分钟上限，台词约 5 字/秒，控制在 500 字内，超了就拆段分次生成 |
| reference_node_keys | string[] | 否 | 画布上已有节点的 `node_key`：音频节点当参考音频（自动连线），图片节点当参考人物图（音频节点不接图片连线，记为节点上的手动引用） |
| audio_urls | string[] | 否 | 参考音频 URL，连同音频节点合计 ≤3 条，克隆音色；与参考图二选一 |
| image_url | string | 否 | 1 张人物图 URL，按形象定音色；与参考音频二选一 |

返回格式同 `generate_image`，`items[0]` 另有 `consume_points`（本次预扣积分，失败会退还）。

### get_task_status — 查询进度

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| task_ids | string[] | 是 | 1–20 个 `task_id` |

返回：
```json
{"tasks": [{"task_id": "t_1a…", "node_key": "6f1c…", "project_id": "2096…", "status": "SUCCESS", "result_urls": ["https://…/xx.png"],
  "ahead_count": 0, "saved_to_node": true}],
 "not_found": ["t_zz…"]}
```
`status`：`PENDING` 排队（`ahead_count` 为前面排队数）/ `PROCESSING` 生成中 / `SUCCESS` 成功 / `FAILED` 失败（看 `error`）。只能查自己提交的任务，其它 id 会出现在 `not_found`。
到 `SUCCESS` / `FAILED` 时结果自动存进节点，`saved_to_node: true`，重复查询不会重复写。`false` 表示没存进去（节点已删除、已被新的生成任务占用，或已没有该项目的编辑权限），不影响 `result_urls`。

### get_points_balance — 积分余额

无参数。返回 `{"balance": 870, "level_code": "PLUS", "level_name": "PLUS", "membership_expire_time": "2026-12-31 23:59:59"}`。

### get_upload_url — 上传参考素材

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| file_name | string | 是 | 原始文件名，只取扩展名，如 `ref.png`、`voice.mp3`、`clip.mp4`；只支持图片、视频、音频 |
| file_size | integer | 否 | 字节数，传了会预先检查存储空间 |

返回：
```json
{"upload_url": "https://…", "method": "PUT", "required_headers": {"Content-Type": "image/png"},
 "file_url": "https://…/neowow/…/xxx.png", "expires_in": 300}
```
上传（300 秒内完成，`required_headers` 里的每个头都必须原样带上）：
```bash
curl -X PUT -H "Content-Type: image/png" --data-binary @ref.png "<upload_url>"
```
HTTP 200 即成功，之后把 `file_url` 填进 `image_urls` / `first_frame_image_url` / `audio_urls` 等参考参数。一定要等 PUT 返回 200 再调 `generate_*`：服务端会检查文件是否已上传，图片还会做内容审核。每个参考 URL 数组和 `reference_node_keys` 最多 10 条。

### estimate_points — 积分试算（免费）

生成前报价用：传和正式提交**完全相同的参数**，不建节点、不提交、不扣分。

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| type | string | 是 | `image` / `video` / `audio` / `music` / `draft_to_formal` |
| project_id | string | 条件 | `type=draft_to_formal`，或参数里用了 `reference_node_keys` 时必填 |
| requests | object[] | image 时 | 与 `generate_image` 的 `requests` 相同 |
| request | object | video 时 | 与 `generate_video` 的 `request` 相同 |
| text_prompt | string | audio 时 | 与 `generate_audio` 的 `text_prompt` 相同 |
| node_key | string | draft_to_formal 时 | 样片视频节点 |
| task_id | string | 否 | `draft_to_formal`：指定历史里某次样片 |
| resolution | string | 否 | `draft_to_formal`：目标分辨率 `1080p` / `4k`，默认 `1080p` |

示例（图片）：`{"type": "image", "project_id": "2096…", "requests": [<和 generate_image 一样的一项>]}`

返回：
```json
{"type": "image", "points": 60, "items": [{"title": "海报1 朱雀大街", "model_name": "…", "points": 30}], "note": "预估，以实际扣费为准"}
```
视频 / 样片转正式另有 `original_points`（原价）和 `discount`（折扣），有折扣时才返回；音频另有 `billed_seconds`（计费秒数）、`exceeds_max`（超过 2 分钟按 2 分钟计）。视频带参考视频（含延长 / 编辑的原视频）时另有 `warning`：参考视频按服务端读到的实际时长计价，个别视频读不到时长时会有偏差。**有 `warning` 时必须原样告诉用户「带参考视频试算可能不准，实际以扣除为准」**，不能只报一个数字。

### generate_music — 生成音乐

| 参数 | 类型 | 必填 | 默认 | 说明 |
|--|--|--|--|--|
| project_id | string | 是 | | 项目 ID |
| title | string | 否 | 音乐 | 节点标题，如「片尾曲」 |
| prompt | string | 是 | | 曲风：风格、情绪、乐器、节奏、人声，如「国风电子，琵琶与合成器，女声，中速，热血」 |
| lyrics | string | 否 | | 歌词；不传由服务端自动作词 |
| instrumental | boolean | 否 | false | `true` = 纯音乐（无人声，歌词忽略） |

在画布上新建一个音频节点。返回格式同 `generate_image`，`items[0]` 另有 `consume_points`（本次扣的积分，生成失败会退还）。通常 1–3 分钟出结果。

### convert_draft_to_formal — 样片转正式

| 参数 | 类型 | 必填 | 默认 | 说明 |
|--|--|--|--|--|
| project_id | string | 是 | | 项目 ID |
| node_key | string | 是 | | 样片视频节点，须已生成成功 |
| resolution | string | 否 | 1080p | 目标分辨率：`1080p` / `4k`（Seedance 2.5 样片只能转这两档） |
| task_id | string | 否 | | 转该节点历史里的某次样片（`get_node_history` 里 `draft: true` 的 `task_id`），不传取节点当前那次 |
| title | string | 否 | 正式视频 | 新节点标题 |

在样片节点右侧新建一个「正式视频」节点并连线，继承样片的提示词、模式、比例、时长，换成目标分辨率和正式模型；样片节点不动。样片完成后 6 天内可转。返回格式同 `generate_video`，`items[0]` 另有 `source_task_id`、`resolution`。

### cancel_task — 取消排队中的任务

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| task_id | string | 是 | 自己提交的、还在排队（`PENDING`）的图片或视频任务 |

返回：`{"task_id": "t_1a…", "cancelled": true, "node_key": "6f1c…", "project_id": "2096…", "saved_to_node": true, "note": "积分已退回"}`。节点会标成失败（「已取消排队任务」）。已经开始生成（`PROCESSING`）或已结束的任务、音频/音乐任务不能取消。

### get_node_history — 节点生成历史

| 参数 | 类型 | 必填 | 说明 |
|--|--|--|--|
| project_id | string | 是 | 项目 ID |
| node_key | string | 是 | 节点 `node_key` |
| status | string | 否 | 按状态过滤：`SUCCESS` / `FAILED` / `PENDING` / `PROCESSING` / `CANCELLED` |

返回（新的在前，最多 20 条，`total` 为全部条数）：
```json
{"node_key": "6f1c…", "total": 3, "records": [
  {"task_id": "t_1a…", "status": "SUCCESS", "type": "video", "created_at": "2026-11-04 16:00:00", "model": "…",
   "result_urls": ["https://…/x.mp4"], "draft": true}]}
```
`draft: true` 表示样片，可以把它的 `task_id` 传给 `convert_draft_to_formal`。不扣积分。

## 四、提示词建议

- **图片**：一句话写清主体 + 动作，再补场景、时间与天气、风格（如电影感、水彩、3D 渲染）、光线、镜头（特写/全景/俯拍）。避免否定句，直接写想要的效果。需要画面里出现文字时，把文字用引号写出来。
- **多张一致**：同一角色或场景的多张图，在每条 prompt 里重复相同的外貌、服装、色调描述；有参考图时在 prompt 里说明「参考图1 为角色外貌」。
- **视频**：先写整体设定（场景、风格、画质），再按时间顺序写镜头和动作，例如「0–2 秒：……；2–5 秒：……」。一条视频只讲一个连贯动作，镜头运动写明（推、拉、摇、跟拍）。
- **音频**：按出场顺序写，台词用引号保留原文并标明角色和语气，音效和配乐单独一句描述（如「背景：雨声，远处有钟声」）。

## 五、高风险操作确认（必须遵守）

1. 每次调用 `generate_image` / `generate_video` / `generate_audio` / `generate_music` / `convert_draft_to_formal` 前，先用相同参数调 `estimate_points`，再向用户复述：项目、模型、数量、尺寸/比例（图片）或时长/分辨率/比例（视频）、曲风与是否纯音乐（音乐）、是否带参考素材、**预估积分**，并得到用户**明确同意**后再提交。视频带参考视频时，报价必须同时说明「带参考视频试算可能不准，实际以扣除为准」。用户只说「随便」「你定」也要先给出方案再确认。
2. 视频逐条确认：多条视频要逐条复述、逐条提交，不要一次确认后批量提交。视频延长 / 编辑要额外说明：会按原视频的实际时长计费（编辑按原视频时长；延长按原视频时长 + 新增时长）。
3. 单次最多 4 张图；用户要更多时分批，每批前再确认。
4. 生成失败不要擅自重试，先告诉用户原因并询问是否重新生成。
5. 提交成功后不要重复提交同一需求；结果没出来就继续轮询。

## 六、错误与恢复

| 现象 | 处理 |
|--|--|
| 「未认证，请重新连接 Neowow」 | 登录已失效，请用户在客户端的连接器/插件设置里断开并重新连接 Neowow |
| 积分不足（如「积分不足，请充值后重试」） | 调 `get_points_balance` 告诉用户余额，提示到 neowow.cn 充值 |
| 存储空间已满 | 提示用户到 neowow.cn 清理存储或升级套餐后再试 |
| 「参考素材须先用 get_upload_url 上传」 | 参考素材只能是本账号的文件：先 `get_upload_url` + `curl PUT` 上传，再用 `file_url`；别人的地址、自己拼的地址都会被拒 |
| 「参考素材还没上传成功，请先完成 PUT 上传」 | 拿到 `upload_url` 后还没 PUT，或 PUT 没返回 200：重新上传成功后再提交；超过 300 秒就重新 `get_upload_url` |
| 「图片审核不通过：…」 | 参考图没过内容审核：告诉用户原因，请用户换一张图，不要原图重试 |
| 「图片审核服务异常，请稍后重试」 | 审核服务临时故障：稍后重试一次 |
| 「只支持上传图片、视频、音频」 | `get_upload_url` 只收这三类文件；文档、表格等请先转成图片，或把文字内容放进 `create_text_node` |
| 「… 最多 10 个」 | 单次参考素材 / `reference_node_keys` 超过 10 条：精简参考，或分多次生成 |
| 「画布节点已达上限 N，请新建项目」 | 这个项目节点太多：`create_project` 新建项目后在新项目里继续 |
| 「请求过于频繁，请稍后再试」 | 调用太密（每个账号每秒有上限）：等几秒再调，不要连续重试；轮询 `get_task_status` 间隔至少 5 秒 |
| 「服务繁忙，请稍后再试」 | 服务端并发已满：等十几秒再试一次，不要连续重试 |
| 「参考节点 … 还没有生成结果」 | 被引用的节点还在生成或已失败：先 `get_task_status` 等它成功再引用 |
| 「reference_node_keys / source_node_key / target_node_key / connect_to_node_keys 里的节点不在该项目画布上」 | `node_key` 写错或不属于这个项目：用 `get_canvas` 查正确的 `node_key` |
| 「拒绝连接：audio → image 非法 …」 | 这类节点不能给这种生成当参考（如音频不能给图片当参考）；去掉该参考或换个节点连 |
| 「拒绝连接：会形成闭环 …」 | 这条线会让节点首尾相连；确认上下游方向，通常是 source、target 写反了 |
| 「拒绝连接：目标节点 … 是 upload 节点 …」 | 上传素材节点没有输入口，只能当 source |
| 「content 最多 32000 字 …」 | 把正文拆成几段，分别 `create_text_node` |
| 「无权在该项目使用Agent」或「会话不存在」 | 项目不属于当前账号，或是只读的协作/分享项目；换一个项目或新建项目 |
| 参数不合法（模型、尺寸、比例、时长不在范围内等） | 重新调 `list_models` 核对取值后修正 |
| 「模型 … 不支持 …，可用：…」 | 这个模型不支持所选的视频生成方式：从报错给出的可用方式里选（要参考素材又不支持全能时用 `IMAGE_TO_VIDEO`），或换一个支持全能的模型 |
| 「TEXT_TO_VIDEO 是纯文生，不能带图片/视频/音频参考 …」 | 去掉媒体参考，或改用 `UNIVERSAL_TO_VIDEO` / `IMAGE_TO_VIDEO` |
| 「VIDEO_EXTEND / VIDEO_TO_VIDEO 需要 source_node_key …」/「source_node_key 必须是已生成成功的视频节点」 | 用 `get_canvas` 找到要延长 / 编辑的视频节点（类型 video、有成品地址），把它的 `node_key` 填进 `source_node_key`；用户本地的视频先 `get_upload_url` 上传，再 `create_upload_node` 建成节点 |
| 「只支持图片、视频、音频，media_type 要和文件扩展名一致」（create_upload_node） | 去掉 `media_type` 让服务端按扩展名判断，或改成和扩展名一致的类型 |
| 「读不到待编辑视频的时长 …」 | 原视频时长暂时取不到：稍后重试；仍不行请用户到网页端操作 |
| 原视频时长不在 4–30 秒等编辑限制 | Seedance 编辑只接受 4–30 秒的原视频：告诉用户原因，换一段视频 |
| 「透明底只支持 gpt-image-2.5-flare、gpt-image-2.5-sunburst …」 | 换成这两个模型之一，或去掉 `transparent_background` |
| 「该节点没有已成功的样片（草稿）视频…」/「task_id … 不是该节点已成功的样片…」 | 这个节点不是样片或还没生成成功：用 `get_node_history` 找 `draft: true` 且 `SUCCESS` 的记录；普通视频不用转正式 |
| 「Seedance 2.5 样片仅支持转为 1080p 或 4K 正式视频」/「草稿任务已超过6天…」 | 换 `1080p` 或 `4k`；超过 6 天的样片不能再转，只能用正式模型重新生成 |
| 「只能取消排队中的任务」/「该任务类型不支持取消」 | 任务已开始生成或已结束，或是音频/音乐任务：不能取消，继续用 `get_task_status` 等结果 |
| 「任务不存在：…」（cancel_task） | `task_id` 写错，或不是你提交的任务 |
| `get_task_status` 返回 `CANCELLED` | 任务已被取消（可能在网页端取消的），积分已退回；需要的话重新生成 |
| `get_task_status` 返回 `FAILED` | 把 `error` 告诉用户，询问是否调整提示词或参数后重新生成 |
| 「服务异常，请稍后重试 (traceId=…)」 | 稍后重试一次；仍失败把 traceId 告诉用户便于反馈 |
| 生成工具超时或连接中断 | 任务可能已提交：先 `get_canvas` 看是否多了新节点，或稍后再查，不要直接重复提交 |

## 七、注意

- 用户在网页端同时打开同一个项目时，网页刷新会用旧的画布快照覆盖连接器刚写入的节点、连线和结果。请提醒用户：通过本连接器生成期间先关闭网页端的这个项目，或生成完成后刷新网页再编辑。
- 没人轮询时结果不会写进节点；不过节点里已记下任务，用户打开网页画布后，网页会接着查询并显示结果。

## 八、暂不支持

- 删除、修改节点，删除连线；
- 图片超分 / 扩图、去字幕等其它编辑类操作（请到网页端操作；抠图请用 `generate_image` 的 `transparent_background` 重新生成透明底图）；
- 音乐翻唱（用参考曲生成）。
