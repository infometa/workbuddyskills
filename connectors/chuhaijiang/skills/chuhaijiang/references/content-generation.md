# AI 内容生成 SOP

目标：用 ai_generate 生成带货视频、商品图、口播脚本、评论分析报告，并且生成出**能用的质量**。质量差距九成来自素材和 prompt，不是模型——把功夫花在提交之前。动笔前先把每个卖点翻译成一个可拍的画面（「续航 5000 次」→「充一次电拖完 120 平一周不充」）：**画面证明卖点，不靠口播说教**，没有对应画面的卖点就是断点。正经的多镜头创作项目（分镜画板、hook 变体、多条成片）建议走画布路径，方法论见 canvas-creation.md。

## 通用流程

1. **先看余额**：批量生成或视频生成前调 account_info，余额不足直接告诉用户去充值，不要提交任务
2. **备素材**：决定质量下限的一步，见「原则一」
3. **写 prompt**：按场景模板写，见「原则二」，展示给用户
4. **用户确认**：模型 + 关键参数 + 预估消耗一起给用户确认（见「原则三」）
5. **提交轮询**：ai_generate(type, params) → 返回 task_id → check_task 直到 completed / failed
6. **验收**：按「验收清单」检查，不合格先诊断再调整重试——重试同样计费，不要原样重发
7. **交付**：把结果 URL 给用户；failed 时把 error 翻译成用户能懂的原因

## 原则一：素材先行，图生优于文生

带货内容的命门是**商品一致性**——纯文字生成的商品和真品对不上，画面再美也不能用。

- 带货视频优先走图生视频：商品实拍图传入参考图参数（各模型的参数名以 ai_generate 工具说明为准）
- 商品图来源：get_detail(products) 的商品图、amazon(action="detail") 的 image_urls、用户自己的实拍图（本地文件先走 upload_file，见「注意」）
- 图的质量决定下限：主体清晰、无水印、分辨率足够；多角度图优于单图
- 完全没有商品图才走纯文生，且必须在 prompt 里锁死商品外观（颜色/材质/形状/logo 位置），交付时提醒用户核对商品一致性

## 原则二：prompt 按场景写，不要直译需求

一句话需求直译成 prompt = 廉价空镜头。用英文写、结构化描述，四类带货场景的骨架：

**产品展示（product showcase）**
[运镜] + [商品主体与材质细节] + [光线] + [背景/氛围]
> Slow orbit shot of a matte black insulated tumbler on a wet stone surface, water droplets on the lid, soft morning light from the left, shallow depth of field, cinematic product photography style

**使用场景（lifestyle / in-use）**
[人物+动作] + [商品在画面中的角色] + [场景] + [情绪/质感]
> A young woman in gym clothes grabs the tumbler from a car cup holder and takes a sip, golden hour sunlight, casual handheld camera feel, authentic UGC style

**开箱/细节特写（unboxing / close-up）**
[手部动作] + [细节特写顺序] + [质感关键词]
> Close-up of hands lifting the tumbler out of kraft packaging, macro shot of the engraved logo, fingers running over the silicone grip, crisp focus, satisfying tactile feel

**口播带货（talking head）**
先有脚本再生成：把脚本手动拆成分镜列表 → 每个分镜一条 prompt 逐段生成。不要把 30 秒口播塞进一次生成。（storyboard 工具的输入是 video_id，只能拆已有视频、不能拆文本脚本——可以对标杆视频跑它，参考其分镜节奏来拆你的脚本）

通用规则：

- 一条 prompt 只描述一个镜头、一个动作；多镜头用 storyboard 拆开分段生成
- 负向要求写成正向描述（不要写 "no watermark"，写 "clean background"）——多数视频模型没有负向 prompt 通道
- prompt 里的商品外观词必须和参考图一致，不要让文字和图打架
- 避免要求画面内出现文字（包装字、字幕）——生成文字极易乱码且不可修
- 用户给中文需求时先翻译成英文 prompt，连同中文含义一起展示给用户确认

## 原则三：场景化推荐模型，花钱决定权在用户

给带理由的推荐（不要把裸选项摊给用户——用户比你更不懂模型差异），但花费必须用户确认：

| 场景 | 首选 | 理由 | 备选 |
|---|---|---|---|
| 带货短视频（有商品图） | seedance，9:16 + 参考图 | 功能最全：支持参考图/视频/音频 | 预算紧或赶时间 → seedance_fast |
| 单图起手的图生视频 | wan26（必须传 image） | 图生视频专长 | grok |
| 真实感人物 / 口播画面 | veo3 | 人物真实感更强 | seedance |
| 商品主图/场景图 | gpt_image，function_type="product_image" + 原图 images | 产品图专用管线 | nanobanana |
| 拆爆款 / 分镜 / 评论分析 | script_breakdown / storyboard / review_analysis | 无模型可选，直接执行 | — |

各模型完整参数与单价以 ai_generate 工具说明和 account_info 为准。提交前把最终模型、参数、预估消耗展示一次；批量任务（>3 个）先给清单和总预估再动手。用户明确指定过模型/参数或说"你来定"时不必反复问。

## 验收清单（生成完必查，不合格别交付）

视频：

- 商品一致性：外观/颜色/logo 与实拍图一致？有无变形、穿模、多手指
- 画面文字：有无乱码（有 = 基本不可修，重写 prompt 规避画面文字）
- 动作完成度：时长内动作是否做完（没做完 = prompt 塞了太多内容）
- 比例：是否符合投放位（带货短视频通常 9:16 竖屏）

图片：主体一致性、边缘伪影、光影方向统一、留白够不够放文案。

常见失败 → 修正策略：

| 症状 | 修正 |
|---|---|
| 商品变形/细节错 | 换更清晰的主体参考图；删减商品之外的描述，让模型专注主体 |
| 画面空洞、廉价感 | prompt 缺光线和材质细节，按场景骨架补全 |
| 动作没做完 | 缩短动作描述，或加时长参数 |
| 人物假、表情僵 | 换 veo3，或 prompt 加 authentic UGC style / handheld camera |

先诊断再重试：原 prompt 直接重发大概率复现同样的问题，白花钱。

## 组合打法：爆款二创（完整链路）

1. 数据侧找爆款：search(videos) 或 get_related(products, id, "videos") 锁定高 GMV 视频
2. ai_generate(script_breakdown) 拆解口播结构和卖点节奏
3. 基于拆解结果 + 用户商品信息写新脚本（纯文本生成），用户确认
4. 拆分镜：可先 ai_generate(storyboard, video_id=爆款视频) 拿标杆的分镜节奏做参考，再把新脚本手动拆成分镜列表（storyboard 只接受 video_id，不能直接拆文本脚本）
5. 备商品图 → 按分镜逐段生成（原则一、二）→ 每段过验收清单
6. 需要发布 → 走 social-media.md 的发布流程

脚本素材加分项：amazon(action="reviews") 的用户原声（好评里的卖点、差评里的痛点）直接喂给脚本写作，比凭空编卖点可信。

## 注意

- 参考素材参数要的是公网可访问的 URL：用户给本地文件时，先 upload_file 拿预签名地址、PUT 上传，再把返回的访问 URL（cdn_url / signed_url）传进去
- 生成结果要发布到社媒时，走 social-media.md 的发布流程（结果 URL 不能直接发布，需要先下载再上传进出海匠存储）
- 视频生成耗时几分钟，提交后告诉用户预期等待时间，不要沉默轮询
- 每次生成（含失败重试）都消耗余额
- 本文的 prompt 骨架是通用视频/图片生成经验，未按各模型逐一实测校准；实际效果与骨架冲突时，以实测调整为准并沉淀回本文件
