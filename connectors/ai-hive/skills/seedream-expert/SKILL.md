---
name: seedream-expert
display_name: Seedream 专家
display_name_en: Seedream Expert
description: "通过指导agent智能调度 Seedream 模型，针对\"手绘感、艺术插画、风格化视觉\"等场景深度优化 prompt 工程，覆盖水彩、油画、扁平插画、国风水墨、赛博朋克、像素艺术、蒸汽波、线描等多种艺术风格，输出高表现力创意视觉与品牌定制插画。"
description_zh: "通过指导agent智能调度 Seedream 模型，针对\"手绘感、艺术插画、风格化视觉\"等场景深度优化 prompt 工程，覆盖水彩、油画、扁平插画、国风水墨、赛博朋克、像素艺术、蒸汽波、线描等多种艺术风格，输出高表现力创意视觉与品牌定制插画。"
description_en: "Agent optimizes Seedream prompts for artistic illustration: watercolor, oil painting, flat, Chinese ink."
category: design
version: 1.0.0
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_image 与 get_generation_task
triggers:
- "Seedream"
- "艺术插画"
- "风格化"
- "水彩"
- "油画"
- "扁平插画"
- "国风"
- "水墨"
- "赛博朋克"
- "手绘感"
- "艺术感"
- "插画风格"
- "创意视觉"
- "illustration"
- "artistic"
---

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `kind`（可选，string）：资源类型 `image`
- `cursor`（可选，string）：分页游标

### `upload_media_from_path`
- `path`（必填，string）：用户授权的本地文件绝对路径
- `kind`（可选，string）：资源类型 `image`

### `generate_image`
- `model`（必填，object）：来自 `list_models(kind="image")` 的模型引用
- `prompt`（必填，string）：描述主体、构图、风格、光线与文字
- `count`（可选，integer）：候选数量（默认 1）
- `size`（可选，string）：像素尺寸（仅用支持的枚举值）
- `ratio`（可选，string）：画幅（仅用支持的枚举值）
- `referenceMediaIds`（可选，array）：通过 `upload_media_from_path` 得到的 mediaId 列表

### `get_generation_task`
- `taskId`（必填，string）：`generate_image` 真实返回的 taskId



> 所有工具的真实返回值以服务端响应为准；本章节参数表是客户端约束说明。

## 接入 AI-HIVE Connector

本 Skill 通过 AI-HIVE Connector 调用底层模型生成能力。CLI OAuth 模式接入流程：

1. **首次安装**：在 WorkBuddy 连接器列表中找到「AI-HIVE」，点击进入
2. **完成授权**：点击「连接」会弹出浏览器到 ai-hive.iclip.cn，在该网站登录 AI-HIVE 账户（无账户需先注册），点击授权
3. **回到 WorkBuddy**：授权完成后自动返回，Token 在本机保存（用户看不到）
4. **日常使用**：用户无需再次操作，直接调用本 Skill 即可
5. **连接过期/失败**：在 WorkBuddy 连接器列表中重新找到「AI-HIVE」，点击「重新连接」→ 完成浏览器 OAuth
6. **Token 安全**：如 Token 疑似泄露，到 ai-hive.iclip.cn → 账户设置 → 撤销所有 Token


## 能力范围

本 Skill 专注 Seedream 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_image 工具完成图片生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 image 列出当前可用模型及价格快照，从中筛选 Seedream 对应的 publicModelId。
- upload_media_from_path：上传本地参考图并返回 mediaId，用于风格迁移。
- generate_image：使用选定模型与 prompt 创建图片任务。
- get_generation_task：使用 taskId 查询任务状态与结果。

## 适用场景

- 用户明确表达使用本 Skill 对应的模型能力或场景需求
- 用户提供素材（图片/视频）需要在该模型擅长的领域生成结果
- 用户希望跨场景复用同一模型能力保持风格一致
- 用户对生成结果的某项特性（文字渲染/真实质感/艺术风格/运镜/动态表现）有明确要求

## 非适用场景

- 用户要求绕过积分、版权、安全审核或平台限制
- 用户素材涉及明显违法、侵权、欺诈、骚扰、色情、暴力、仇恨或其他敏感内容
- 用户未确认对素材拥有必要权利（第三方作品、商标、人物、肖像）
- 用户只询问创意建议而未要求实际创建任务，此时直接给文字建议，不调用付费工具
- 涉及真实人脸的素材（部分模型平台会拦截）—— 改用卡通/虚拟人物描述
- 涉及未成年人、裸露、暴力、仇恨内容的素材
- 用户希望免费获取结果——本 Skill 调用即按服务端计费，无免费预览


## Seedream 擅长什么

Seedream 的核心优势是艺术风格化与创意视觉，擅长把文字描述转化为有艺术感的画面，而非写实照片。

| 能力 | 说明 |
|---|---|
| 风格多样 | 水彩、油画、扁平插画、国风水墨、赛博朋克、像素艺术、蒸汽波 |
| 艺术构图 | 打破写实规则，做夸张、隐喻、超现实构图 |
| 色彩表现力 | 高饱和、低饱和、渐变、撞色等风格化调色 |
| 文字美化 | 画面中的文字作为视觉元素，艺术化变形而非精确可读 |
| 风格迁移 | 提供参考图，转换为目标艺术风格 |

## 风格库

按用户描述匹配风格关键词，prompt 中显式声明风格：

| 风格 | 关键词 | 适用场景 |
|---|---|---|
| 水彩 | 水彩、晕染、留白、纸张纹理 | 书籍插画、公众号配图、邀请函 |
| 油画 | 油画、厚涂、笔触感、画布纹理 | 艺术海报、展览视觉、高端品牌 |
| 扁平插画 | 扁平、矢量、几何色块、无渐变 | App 引导页、信息图、UI 配图 |
| 国风水墨 | 水墨、留白、毛笔笔触、宣纸 | 茶品牌、文化产品、节日海报 |
| 赛博朋克 | 霓虹、暗调、高对比、故障感 | 科技海报、游戏视觉、活动主视觉 |
| 像素艺术 | 像素、8-bit、马赛克 | 游戏素材、复古海报、社交表情 |
| 蒸汽波 | 粉紫渐变、复古网格、霓虹文字 | 音乐封面、潮流视觉、活动海报 |
| 线描 | 线描、单色、极简线条 | 图标、logo 草图、说明书配图 |
| 手绘 | 手绘、铅笔感、不完美线条 | 笔记配图、教育素材、故事板 |

## Prompt 原则：风格优先

Seedream 的 prompt 应把风格声明放在最前面，写实细节从简：艺术风格 + 主体 + 构图/色彩方向 + 情绪/氛围。

示例（水彩书籍插画）：风格水彩插画晕染技法纸张纹理，主体一只猫坐在窗台看雨，构图三分构图窗外留白，氛围安静温暖。

示例（扁平信息图）：风格扁平矢量插画几何色块无渐变，主体数据分析流程五个步骤图标，色彩蓝紫主色橙色强调，构图横向排列左到右流程。

## 风格迁移

用户提供参考图想转换风格时：upload_media_from_path 上传得到 mediaId；把 mediaId 放入 referenceMediaIds；prompt 说明目标风格（保持参考图的构图与主体，转换为水彩插画风格）。

## 调用流程

1. get_user_info 检查余额。
2. list_models(kind=image) 获取 Seedream 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 匹配风格关键词，组装艺术风格 prompt。
4. 如有参考图，upload_media_from_path 上传得到 mediaId。
5. generate_image 提交任务，get_generation_task 跟踪到 completed。

## 生成后建议

- 尝试不同艺术风格（从风格库中选择 2-3 种对比）
- 调整色彩方向（高饱和 / 低饱和 / 渐变 / 撞色）
- 添加参考图做风格迁移
- 调整构图方向（夸张 / 隐喻 / 超现实）

## 输入检查

- 明确目标风格（从风格库匹配；无匹配时询问用户）。
- 如果用户说"好看就行"，先推荐 2-3 种风格供选择，不自行决定。
- 画幅使用服务端支持的枚举值。
- 参考图仅使用用户主动选择的文件。

## 事实与合规边界

1. 只使用 list_models 真实返回的 publicModelId 与 pricingSnapshot。
2. 不虚构品牌信息、不制造虚假代言。
3. 不擅自改变参考图中人物的外观或身份特征。
4. 涉及真人时须确认用户拥有合法授权。
5. Token 只在 AI-HIVE Connector 凭证设置中填写。

## 费用授权

- generate_image 调用即按服务端计费扣费。
- 失败、被拒绝或余额不足时不重试扣费。
- 用户修改 prompt 或参考图后必须重新调用。

## 状态与错误处理

- pending / processing：返回工具真实状态，不自行估算。
- completed：返回所有可用图片链接。
- failed：保留可安全展示的 errorCode / errorCategory / retryable。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

## 调用示例

### 示例 1：典型办公场景

**用户表达**：用一张本地商品图，生成一张 1:1 的夏季促销海报，要求海报上写"夏季新品 5 折起"。

**AI 行为**：
1. 调用 `get_user_info` 检查余额与可用模型
2. 调用 `list_models(kind="image")` 获取本模型对应的 publicModelId 与 pricingSnapshot
3. 调用 `upload_media_from_path` 上传参考图，得到 mediaId
4. 调用 `generate_image`，prompt 包含场景描述与文字渲染要求
5. 调用 `get_generation_task(taskId)` 跟踪到 completed
6. 输出图片 URL + 参数摘要 + 后续建议

### 示例 2：批量对比场景

**用户表达**：用同一商品图，分别生成 3 张不同风格候选。

**AI 行为**：调用 `generate_image` 设置 `count: 3`，按 3 个候选分别输出，对比呈现。

### English Example

User: "Generate a 1:1 summer sale poster from my local product image with text 'Summer Sale 50% Off'."

AI flow: run `get_user_info` for balance, call `list_models(kind="image")` to fetch the model's `publicModelId` and `pricingSnapshot`, upload the reference image via `upload_media_from_path` to get `mediaId`, call `generate_image` with prompt describing scene + text rendering requirement, track with `get_generation_task(taskId)` until `completed`, return image URL + parameter summary + follow-up suggestions. Never ask the user to paste a Token into chat.


## 输出模板

### 成功：taskId + 模型与参数 + 图片 URL 列表 + 下一步建议
### 失败：错误码 + 错误分类 + 原因摘要 + 下一步建议
### 部分失败：成功图片完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
