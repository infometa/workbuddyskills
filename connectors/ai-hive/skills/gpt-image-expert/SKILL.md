---
name: gpt-image-expert
display_name: GPT-Image 专家
display_name_en: GPT-Image Expert
description: "通过指导agent智能调度 GPT-image 模型，针对\"画面中需要清晰可读文字、复杂多元素布局、严格指令跟随\"等场景深度优化 prompt 工程，擅长海报、信息图、菜单字、电商详情页、复杂指令构图与多场景电商视觉，支持多元素指令跟随与文字渲染。"
description_zh: "通过指导agent智能调度 GPT-image 模型，针对\"画面中需要清晰可读文字、复杂多元素布局、严格指令跟随\"等场景深度优化 prompt 工程，擅长海报、信息图、菜单字、电商详情页、复杂指令构图与多场景电商视觉，支持多元素指令跟随与文字渲染。"
description_en: "Agent optimizes GPT-image prompts for precise text rendering, multi-element layouts, complex composition."
category: design
version: 1.1.4
author: 极睿科技（Infimind）/ AI-HIVE 团队
permissions:
  provisional: true
  read:
  - 仅限当前对话中用户主动选择的本地图片
  network:
  - 仅通过已启用的 AI-HIVE Connector 调用 get_user_info、list_models、upload_media_from_path、generate_image 与 get_generation_task
triggers:
- "GPT画图"
- "gpt-image"
- "海报文字"
- "信息图"
- "菜单字"
- "海报设计"
- "创意构图"
- "文字渲染"
- "指令跟随"
- "吉卜力"
- "Pixar"
- "乐高"
- "粘土"
- "盲盒"
---

## 工具参数

### `get_user_info`
- 不接收参数；返回账户与余额摘要

### `list_models`
- `modelType`（可选，string）：资源类型枚举 `TEXT` / `IMAGE` / `VIDEO`（本 Skill 用 `IMAGE`）

### `upload_media_from_path`
- `path`（必填，string）：用户授权的本地文件绝对路径
- `filename`（可选，string）：覆盖上传文件名
- `contentType`（可选，string）：覆盖 MIME 类型；不确定时省略并由客户端识别

### `generate_image`
> 上传图片单文件上限 10MiB。若要把刚生成的图作为参考图传入下一张，先压缩至 10MiB 内再上传。

- `publicModelId`（必填，string）：来自 `list_models(modelType="IMAGE")` 的当前模型 ID
- `routingMode`（必填，string）：选中模型实际返回的 `COST_FIRST` / `SPEED_FIRST` / `SUCCESS_FIRST`
- `prompt`（必填，string）：描述主体、构图、风格、光线与文字
- `batchSize`（可选，integer）：候选数量，1–10，默认 1
- `imageMediaIds`（可选，array）：参考图片的 mediaId 列表
- `params`（可选，object）：画幅、分辨率、质量等模型专属参数；键、类型和值以当前模型配置为准
- `pricingSnapshot`（必填，object）：选中模型与路由返回的价格快照，原样传入

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

本 Skill 专注 GPT-Image 模型的 prompt 工程与参数调优，通过 AI-HIVE Connector 的 generate_image 工具完成图片生成。本 Skill 使用以下工具：

- get_user_info：查询当前账户与余额；不接收参数。
- list_models：按 image 列出当前可用模型及价格快照，从中筛选 GPT-Image 对应的 publicModelId。
- upload_media_from_path：上传本地参考图并返回 mediaId，用于图生图保人保物。
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


## GPT-Image 擅长什么

GPT-Image 的核心优势是精确文字渲染与多元素严格指令跟随，是当前最擅长在画面中直接生成可读文字的模型。

| 能力 | 说明 |
|---|---|
| 文字渲染 | 海报标题、菜单价格、信息图标签、产品说明 -- 画面中的文字清晰可读，不变形 |
| 指令跟随 | 复杂多元素构图（如"左上角放产品，右下角放价格标签，背景用渐变蓝"）能严格执行 |
| 图生图保人保物 | 提供参考图时，保持人物与产品的一致性，适合产品换背景、换风格 |
| 风格化 | 吉卜力、Pixar、乐高、赛博朋克、粘土、盲盒等风格一键切换 |

## Campaign Style Lock（多图视觉一致性）

电商或多图任务场景下，多张图必须保持视觉一致，避免风格漂移。锁定要素：

| 锁定要素 | 说明 |
|---|---|
| 色板 | 选定主色 2-3 个 + 辅色，所有图统一 |
| 冷暖调 | 整体偏暖（黄/橙）或偏冷（蓝/青），全系列统一 |
| 字体 | 文字渲染时使用相同字体风格 |
| 背景 | 纯色背景 / 场景背景风格统一 |
| 光线 | 摄影光线方向、强度、色温统一 |
| 构图 | 主体位置（如居中/左对齐）、视角（俯拍/平视）统一 |

操作建议：先确认第一张图的视觉风格，后续所有 prompt 复用相同的色板、光线、构图关键词，避免每次重新描述。

## 转化驱动力诊断

电商场景下，先判断本次任务的驱动类型，针对性生成图片序列：

| 驱动类型 | 适用产品 | 视觉策略 |
|---|---|---|
| 视觉驱动型 | 美妆、服饰、设计类产品 | 突出外观、质感、设计细节、视觉效果震撼 |
| 痛点驱动型 | 工具、效率、清洁类产品 | 突出问题场景、使用前后对比、痛点可视化 |
| 情感价值驱动型 | 礼品、母婴、宠物类产品 | 突出情感场景、温馨氛围、人宠互动、礼物惊喜 |

诊断方法：询问用户产品类目与营销目标；类目已知则按上表默认；目标明确（如"突出设计"）则直接锁定对应驱动类型。

## 场景 Recipe 模板

常见内容场景的 prompt 起步模板：

| 场景 | 核心要点 |
|---|---|
| 产品发布 | 主视觉突出产品 + 3 张细节特写 + 1 张场景应用 |
| 营销推广 | 强 CTA 视觉 + 折扣/促销信息清晰 + 紧迫感配色 |
| 周报月报 | 信息图风格 + 数据可视化 + 简洁留白 |
| 课程课件 | 知识点配图 + 步骤分解 + 高可读性 |
| 答辩结题 | 学术风格 + 数据图表 + 严谨配色 |
| 读书分享 | 文艺风格 + 封面视觉 + 情绪氛围 |

使用方式：先与用户确认场景与页数/张数，再基于 recipe 扩展具体内容，不直接套用示例文案。

## Prompt 原则：简洁聚焦

GPT-Image 对简洁 prompt 效果最好。不要堆砌形容词，只保留核心要素：

主体 + 场景/背景 + 光线 + 构图 + 风格 + 文字内容

示例（海报）：主体为磨砂玻璃精华瓶白色磨砂盖，背景纯白，光线柔光棚拍，构图居中正面，风格商业电商摄影，右下角写"AI-HIVE"白色无衬线字体。

## 场景模板（25 类）

按用户意图匹配模板，只读匹配的那一个，不全量加载。无匹配时默认用主图模板。

| 触发词 | 模板 | 核心要点 |
|---|---|---|
| 白底图、主图、hero image | 主图 | 纯白背景、居中正面、突出产品质感 |
| 场景图、生活图、lifestyle | 生活场景 | 真实使用环境、人物互动、自然光 |
| 平铺图、flat lay、俯拍 | 平铺 | 俯拍、道具搭配、留白构图 |
| 细节图、微距、macro | 细节特写 | 极近距、材质纹理、浅景深 |
| 海报、poster、banner、促销 | 海报横幅 | 文字渲染、品牌色、CTA 标语 |
| 小红书、Instagram、TikTok | 社交媒体 | 竖版、生活感、贴纸文字 |
| UGC、买家秀、GRWM | UGC 风格 | 手机拍摄感、真实不完美 |
| 模特、人物展示 | 模特展示 | 人物 + 产品、肤色还原 |
| 对比、before after、前后 | 前后对比 | 分屏或时间线、标签说明 |
| 包装、礼盒 | 包装设计 | 3D 盒型、品牌标贴 |
| 信息图、A+、详情页 | 信息图 | 结构化信息、图标 + 文字、多区块 |
| 创意、概念、creative | 创意概念 | 超现实、隐喻、视觉冲击 |
| 尺寸、规格、使用步骤 | 尺寸规格 | 标注线、数据可视化 |
| 套装、组合、bundle | 多品组合 | 多产品排列、主次分明 |
| 直播、livestream | 直播场景 | 主播 + 产品 + 背景屏 |
| 试穿、融入、try on | 虚拟试穿 | 人物 + 服装融合 |
| 拆解图、爆炸图 | 拆解视图 | 分层展开、内部结构 |
| 隐形模特、ghost mannequin | 隐形模特 | 3D 服装立体感 |
| 多角度、网格、grid | 多角度网格 | 3-6 角度、统一背景 |
| 杂志、封面、editorial | 杂志编辑 | 大片感、排版感 |
| 季节、四季、campaign | 季节活动 | 节日元素、色彩主题 |
| 奢华、氛围、烟雾 | 奢华氛围 | 光影层次、烟雾粒子 |
| 设备模型、界面、mockup | 设备样机 | 屏幕 + UI + 场景 |
| 店铺、门面、实体店 | 店面空间 | 建筑外观、招牌 |
| 运动、健身、sports | 运动场景 | 动态抓拍、运动装备 |

## Anti-AI Tips（UGC / 直播 / 社交场景）

生成 UGC、直播或社交媒体内容时，以下规则至关重要：

- 指定具体手机型号：iPhone 14 Pro、iPhone 15 Pro
- 加入可见瑕疵：毛孔、轻微噪点、暖色偏、不完美构图
- 使用 candid 语言：NOT professional photography、NOT AI-generated look
- 展示真实环境：稍微凌乱、真实物件、水渍、用过的毛巾
- 参考胶片色调：Kodak Portra 400 color feel

这些技巧让 GPT-Image 生成的图片看起来不像 AI 生成，而是像真实用户拍摄。

## Prompt 结构化组装流程

从匹配的场景模板组装 prompt 时，按以下步骤：

1. 取 prompt_template 作为基础结构
2. 用用户提供的信息替换变量
3. 如用户指定了风格变体，应用该变体的 overrides
4. 如已知产品类目，应用该类目的 category_tips
5. 简化：只保留有值的核心字段，移除空字段
6. 输出简洁的对象，不要包含模板的完整元数据

核心原则：保持 prompt 简洁。只包含必要信息。GPT-Image 对简洁聚焦的 prompt 效果最好，而非过度复杂的 prompt。

## Prompt 骨架（通用模板）

逐场景组装时，按以下 8 字段结构化；缺省字段留空，不强行填充，保持 prompt 简洁：

| 字段 | 含义 | 示例 |
|---|---|---|
| 用途 | 这张图用在哪（海报 / 主图 / 头像 / 信息图） | 领英头像 |
| 主体 | 核心对象（产品 / 人物 / 场景） | 商务正装男性 |
| 场景构图 | 背景、机位、景深、画幅 | 浅景深、灰渐变背景、对称构图 |
| 视觉风格 | 写实 / 插画 / 风格化 | 照片级写实 |
| 光线色彩 | 光源方向与色温 | 自然窗光、冷调 |
| 必须文字 | 画面中需可读的文字（无则留空） | 姓名 + 职位 |
| 保留项 | 图生图时须保留的要素 | 参考图人物五官 |
| 输出规格 | 尺寸 / 比例 / 分辨率 | 1:1 / 1080px |

组装顺序：用途 → 主体 → 场景构图 → 视觉风格 → 光线色彩 → 必须文字 → 保留项 → 输出规格。仅保留有值的字段。

## 调用流程

1. get_user_info 检查余额。
2. list_models(modelType=IMAGE) 获取 GPT-Image 模型对象（含 publicModelId 与 pricingSnapshot）。
3. 按用户意图匹配场景模板，组装简洁 prompt。
4. 如有参考图，upload_media_from_path 上传得到 mediaId。
5. generate_image 提交任务，get_generation_task 跟踪到 `COMPLETED`。

## 图生图保人保物

用户提供参考图时：把 mediaId 放入 imageMediaIds；prompt 中说明保留意图（保持参考图中产品外观，仅更换背景为户外阳光场景）；不擅自改变产品颜色、形状、包装、标识或可见文字。

## 生成后建议

- 尝试不同风格变体（列出模板中的可用变体）
- 调整产品类目以获得更精准的结果
- 添加参考图以获得更好的产品一致性
- 尝试不同场景类型
- 对 UGC/社交场景应用 Anti-AI Tips
- 生成完成后建议再调一次 `get_user_info` 向用户报告准确剩余余额（含本次扣费）。

## 输入检查

- 明确场景类型（25 类之一）；无匹配时确认用主图模板。
- 文字内容必须由用户明确提供，不得编造标语或价格。
- 参考图仅使用用户主动选择的文件。
- 画幅使用服务端支持的枚举值；不确定时先查 list_models。

## 事实与合规边界

1. 只使用 list_models 真实返回的 publicModelId 与 pricingSnapshot，不编造或缓存。
2. 不虚构商品类目、材质、功能、功效、参数、认证、价格。
3. 不擅自改变产品主体的颜色、结构、包装、标识或可见文字。
4. 涉及真人或公众人物时须确认用户拥有合法授权。
5. 不制造虚假代言、买家证言或身份混淆内容。
6. Token 只在 AI-HIVE Connector 凭证设置中填写，不得在对话中粘贴。

## 费用授权

- generate_image 调用即按服务端计费扣费。
- 失败、被拒绝或余额不足时不重试扣费。
- 用户修改模型、prompt 或参考图后必须重新调用，不复用旧扣费配额。

## 状态与错误处理

### 余额不足 / 任务被拒

**AI-HIVE 官网**：https://ai-hive.iclip.cn

**充值路径**（账户已存在）：
1. 访问 https://ai-hive.iclip.cn → 登录 AI-HIVE 账户
2. 进入「账户中心」/「钱包」/「充值」页面
3. 选择充值套餐或自定义金额 → 完成支付
4. 充值成功后回到 WorkBuddy，无需重新连接 Connector，直接重试任务

**注册路径**（首次用户）：
1. 直接访问 https://ai-hive.iclip.cn/login，进入注册页面
2. 使用手机号完成注册
3. 登录 → 回到 WorkBuddy 重新连接 AI-HIVE Connector 即可

**价格透明**：
- 每次调用前可调 `get_user_info` 查看当前余额
- 调用后实际扣费以服务端 `pricingSnapshot` 为准
- 若工具明确提示余额不足，停止创建任务；任务进入 `FAILED` 时按 `failure` 安全字段展示
- 详细价格参考：https://ai-hive.iclip.cn/pricing

**常见扣费场景参考**（具体以服务端为准）：
- 文本生成：按 token 数计费
- 图片生成：按张数 + 分辨率计费
- 视频生成：按秒数 + 分辨率计费

**其他被拒原因**：
- 账户被风控：联系 AI-HIVE 客服（https://ai-hive.iclip.cn → 登录 → 设置 → 联系客服）
- 模型临时不可用：稍后重试或换模型
- 内容违规审核：调整 prompt 后重试（避免敏感内容）

- 轮询策略：每 10–15s 查询一次 `get_generation_task`；状态未变化时不必逐次播报，仅在 `PENDING` → `PROCESSING` → `COMPLETED` 等关键变化时报一次，减少噪声。
- `PENDING` / `PROCESSING`：返回工具真实状态，不自行估算完成时间。
- `COMPLETED`：返回所有可用图片链接与缩略图。
- `FAILED`：展示 `failure.code`、`failure.summary` 与 `failure.suggestion`（若返回），不暴露内部诊断。
- **上传失败 413**：文件超过约 10MiB 限制；压缩图片（转 JPEG / 降分辨率至 ≤2K）后重新 `upload_media_from_path`。
- 鉴权失败（401/403）：提示用户重新连接 AI-HIVE Connector。

## 调用示例

### 示例 1：典型办公场景

**用户表达**：用一张本地商品图，生成一张 1:1 的夏季促销海报，要求海报上写"夏季新品 5 折起"。

**AI 行为**：
1. 调用 `get_user_info` 检查余额与可用模型
2. 调用 `list_models(modelType="IMAGE")` 获取本模型对应的 publicModelId 与 pricingSnapshot
3. 调用 `upload_media_from_path` 上传参考图，得到 mediaId
4. 调用 `generate_image`，prompt 包含场景描述与文字渲染要求
5. 调用 `get_generation_task(taskId)` 跟踪到 `COMPLETED`
6. 输出图片 URL + 参数摘要 + 后续建议

### 示例 2：批量对比场景

**用户表达**：用同一商品图，分别生成 3 张不同风格候选。

**AI 行为**：调用 `generate_image` 设置 `batchSize: 3`，按 3 个候选分别输出，对比呈现。

### English Example

User: "Generate a 1:1 summer sale poster from my local product image with text 'Summer Sale 50% Off'."

AI flow: run `get_user_info` for balance, call `list_models(modelType="IMAGE")` to fetch the model's `publicModelId` and `pricingSnapshot`, upload the reference image via `upload_media_from_path` to get `mediaId`, call `generate_image` with prompt describing scene + text rendering requirement, track with `get_generation_task(taskId)` until `COMPLETED`, return image URL + parameter summary + follow-up suggestions. Never ask the user to paste a Token into chat.


## 输出模板

### 成功：taskId + 模型与参数 + 图片 URL 列表 + 下一步建议
### 失败：failure.code + failure.summary + 原因摘要 + 下一步建议（充值/改连/调prompt/换模型）
### 部分失败：成功图片完整呈现 + 失败子任务错误码与 prompt 概要 + 不补写
