# 模型擅长场景速查表（references/model-scenarios.md）

适用版本：AI-HIVE Connector 1.0.0
更新日期：2026-07-31

> 本表帮助 agent 在调用 `list_models` 后，结合用户任务特点快速匹配擅长模型。
> 实际可用模型与价格以 `list_models` 返回为准；本表仅作场景速查，不替代服务端返回值。

## routingMode 三档计费说明

`list_models` 返回每个模型的 `pricingSnapshot`，含以下三档：

| routingMode | 含义 | 适用场景 |
|---|---|---|
| `COST_FIRST` | 成本优先 | 批量任务、草稿、对效果要求不高的场景 |
| `SPEED_FIRST` | 速度优先 | 实时交互、快速预览、紧急交付 |
| `SUCCESS_FIRST` | 成功率优先 | 高价值任务、最终交付、对稳定性要求高的场景 |

推荐模型时同时给出推荐 `routingMode`，让用户理解效果与成本的取舍。

## 文本模型（kind="text"）

| 模型 | 擅长场景 | 推荐 routingMode |
|---|---|---|
| deepseek-r1 | 深度推理、数学证明、代码生成；性能比肩 O1 | SUCCESS_FIRST（复杂推理） |
| deepseek-v3.1-fast | 中文写作兼顾速度与深度 | SPEED_FIRST（快速写作） |
| deepseek-v3-1-250821 | 混合推理，思考与非思考双模式 | COST_FIRST（通用写作） |
| kimi-k2.6 | 长程代码、指令遵循、自我纠错；支持图文视频输入 | SUCCESS_FIRST（长文任务） |
| kimi-k2 | MoE 架构，通用知识推理、编程、Agent | COST_FIRST（通用任务） |
| gpt-5.1 | 对话指令、自然交互，最常用型号 | SPEED_FIRST（日常对话） |
| gpt-5 | 跨领域编码、推理和智能体任务旗舰 | SUCCESS_FIRST（复杂任务） |
| claude-opus-4-5 | 编码、代理、计算机使用、企业工作流 | SUCCESS_FIRST（企业场景） |
| gemini-2.5-pro | 编码和复杂提示，深度思考，多模态输入 | SUCCESS_FIRST（复杂推理） |
| glm-5.1 | 长程任务，自主规划执行长达 8 小时 | SUCCESS_FIRST（长程任务） |
| qwen3-max-preview | 中英文通用、复杂指令、多语言、工具调用 | COST_FIRST（多语言） |
| doubao-seed-1-8 | 多模态理解、Agent 能力 | COST_FIRST（通用） |

### 选派逻辑

- **长文摘要 / 周报纪要**：kimi-k2.6（长程）或 deepseek-v3.1-fast（快速）
- **深度推理 / 数学 / 代码**：deepseek-r1 或 gpt-5
- **日常对话 / 邮件拟稿**：gpt-5.1（SPEED_FIRST）
- **合同要点 / 企业工作流**：claude-opus-4-5 或 gemini-2.5-pro
- **多语言翻译**：qwen3-max-preview 或 kimi-k2.6

## 图片模型（kind="image"）

| 模型 | 擅长场景 | 推荐 routingMode |
|---|---|---|
| gpt-image-2 | 最先进的图像生成与编辑，灵活参数 | SUCCESS_FIRST（高质量交付） |
| gpt-image-1.5 | 指令跟踪与提示遵循 | COST_FIRST（通用生图） |
| gemini-3.1-flash-image-preview（Nano Banana 2） | 低价高质量，对话式多轮编辑 | SPEED_FIRST（快速编辑） |
| gemini-3-pro-image-preview（Nano Banana pro） | 2K/4K 原生输出，文字渲染、物理推理 | SUCCESS_FIRST（高分辨率） |
| google/imagen-4 | 旗舰画图 | SUCCESS_FIRST（最高质量） |
| google/imagen-4-ultra | 质量最高，成本也最高 | SUCCESS_FIRST（极致画质） |
| doubao-seedream-4-5 | 多图融合，主体一致性 | SUCCESS_FIRST（参考图融合） |
| doubao-seedream-5-0 | 精准解析复杂指令 | COST_FIRST（通用生图） |
| flux-pro-1.1-ultra | 高分辨率快速生成 | SPEED_FIRST（快速高分辨率） |
| flux-pro | 效果堪比 Midjourney | COST_FIRST（风格化生图） |

### 选派逻辑

- **PPT 配图 / 信息图**：gpt-image-2（文字渲染好）或 Nano Banana pro（4K）
- **营销海报 / 广告图**：google/imagen-4 或 gpt-image-2
- **快速草图 / 预览**：Nano Banana 2（SPEED_FIRST）或 flux-pro-1.1-ultra
- **参考图风格迁移**：doubao-seedream-4-5（多图融合）
- **需要文字的创意图**：gpt-image-2 或 Nano Banana pro（文字渲染强）

## 视频模型（kind="video"）

| 模型 | 擅长场景 | 推荐 routingMode |
|---|---|---|
| doubao-seedance-1-0-pro-fast-251015 | 质量速度价格平衡 | COST_FIRST（通用视频） |
| doubao-seedance-1-0-lite-i2v-250428 | 图生运镜强（环绕/航拍/变焦/平移/跟随/手持），多主体动作 | SPEED_FIRST（图生运镜） |
| doubao-seedance-1-0-pro-250528 | 多镜头叙事，影视级 1080P | SUCCESS_FIRST（影视级） |
| doubao-seedance-1-5-pro-251215 | 首尾帧音画 | SUCCESS_FIRST（首尾帧） |
| happyhorse-1.0-t2v | 文生视频，动态画面 | COST_FIRST（文生视频） |
| happyhorse-1.0-i2v | 图生视频 | SPEED_FIRST（图生视频） |
| happyhorse-1.0-r2v | 参考生视频，9 图参考，主体场景稳定 | SUCCESS_FIRST（参考生视频） |
| veo3 | 带声音视频生成 | SUCCESS_FIRST（音画同步） |
| veo3.1-pro | 高质量模式，首尾帧+音画 | SUCCESS_FIRST（高质量音画） |
| sora-2 | 物理精准，同步对话音效 | SUCCESS_FIRST（物理精准） |
| minimax/video-01 | 高清节奏稳定 | SPEED_FIRST（快速生成） |

### 选派逻辑

- **产品讲解 / 培训录屏**：seedance-1-0-pro-fast（通用）或 seedance-1-0-pro（影视级）
- **文生视频**：happyhorse-1.0-t2v 或 seedance-1-0-lite-t2v
- **图生视频 / 单图动起来**：happyhorse-1.0-i2v 或 seedance-1-0-lite-i2v
- **首尾帧过渡**：seedance-1-5-pro 或 seedance-1-0-pro
- **多图参考保持一致**：happyhorse-1.0-r2v（最多 9 张参考）
- **需要声音 / 音画同步**：veo3 或 sora-2
- **快速预览**：seedance-1-0-pro-fast 或 minimax/video-01

## 注意事项

1. 本表为静态速查，**不代表当前一定可用**；必须以 `list_models` 返回的实时清单为准。
2. 模型可能临时下线或新增，推荐时只使用 `list_models` 实际返回的 `publicModelId`。
3. `pricingSnapshot` 中的价格可能随服务端调整变化，推荐时引用服务端实时值，不写固定价格。
4. 若用户指定的模型不在 `list_models` 返回中，提示该模型当前不可用，推荐替代方案。
