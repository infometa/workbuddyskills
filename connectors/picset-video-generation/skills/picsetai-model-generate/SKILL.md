---
name: picsetai-model-generate
displayName: Picset AI 人物三视图生成
name_en: picsetai-model-generate
description: >
  用于 Picset AI 独立生成人物正面、侧面、背面三视图，也用于商品视频或爆款复刻中的固定模特准备。有普通人物照时将已上传登记图片转换为统一三视图；没有人物照时根据人物要求直接生成三视图；已有合格合成三视图时由用户确认后直接复用。大模型只辅助检查，最终采用必须由用户自然语言确认。结果可单独交付，也可作为后续视频的 model_image_ref。
description_en: >
  Generate standalone person three-view images or prepare a user-confirmed fixed-model reference for product and replica video flows.
argument-hint: 人物照片、已有三视图、人物要求，或需要固定模特的视频任务上下文
---

# Picset AI 人物三视图生成

本子 Skill 同时负责独立人物三视图生成，以及视频固定模特流程中的三视图准备与确认。执行时必须使用共享协议：

- `../shared/handoff-protocol.md`
- `../shared/credit-confirmation-protocol.md`

用户可以只生成人物三视图而不生成视频；独立流程不得要求商品图、目标视频、视频脚本、时长或比例。视频流程中，人物三视图确认前不得进入需要固定模特的商品脚本或最终视频提交。

## 触发条件

- 用户直接要求生成正面、侧面、背面人物三视图时，进入独立三视图流程。
- 用户明确要求固定人物、同一人物或人物一致性，或者明确提供人物素材用于固定模特时，进入视频固定模特流程。
- 普通真人出镜、口播人物或目标视频中出现人物，不代表要求固定模特；只写入视频 `requirements`，不得自动生成三视图。
- 不新增 `video_type=model`；人物三视图是正交素材能力，不是视频业务管线。

## 判断标准与用户确认

固定模特的判断条件是“是否已有用户确认的合格人物三视图”，不是“是否有任意人物图片”。合格素材应是一张包含同一人物正面、侧面、背面的清晰合成图。

大模型只可辅助检查人物是否一致、三个视角是否齐全、是否清晰完整和无遮挡；大模型不得自行把图片判定为已确认。最终必须展示素材并取得用户自然语言确认，例如“确认使用”“就用这张”“三视图没问题”。只上传图片、询问效果或大模型自行判断都不构成确认。

根据用户素材分流：

1. **已有一张合格合成三视图**：上传登记并展示；用户确认后直接作为 `model_image_ref`，不调用三视图生成，不产生三视图生成任务。
2. **只有普通人物照**：按“尚无三视图”处理，询问是否转换；用户同意后使用 `mode=image_to_image`、`view_mode=three_view` 和 `input_image_refs`。
3. **有多张独立正面、侧面或背面人物照**：不能把多个引用直接写进单值 `model_image_ref`；使用全部已登记图片作为 `input_image_refs`，生成一张统一合成三视图。
4. **没有人物照**：收集人物要求，使用 `mode=text_to_image`、`view_mode=three_view` 直接生成三视图，不先生成单图再转换。
5. **用户拒绝生成或转换**：独立流程停止；视频流程取消固定模特保证，不能把普通人物照标记为已确认的 `model_image_ref`。

## 素材与项目规则

需要使用用户图片时，必须先取得用户对本次处理和上传的确认，再按服务端给出的直传地址通过 HTTP PUT 上传到 OSS，并登记素材引用。`image_to_image` 必须通过 `input_image_refs: [已登记的图片引用]` 传入；不能使用后端不读取的单值 `reference_image_ref`。不得使用 OSS SDK、oss2 或第三方上传依赖。

`project_id` 只内部保存和透传，不展示给用户。独立三视图调用可以省略 `project_id`，由服务端自动创建；收到返回的真实 `project_id` 后必须保存到 `VideoHandoffContext`。已有视频项目时可复用后端返回的项目归属。不得传空字符串、臆造项目、用脚本任务 ID 冒充项目 ID，或要求用户查找项目 ID。

没有明确人物要求时，默认人物要求为：中国模特、简体中文语境、中国电商短视频表达。用户补充的人物要求只保存可读摘要到 `VideoHandoffContext.drafts.model.person_requirements` 和 `person_summary`；不得生成、展示或保存最终模特 prompt。

## 预估与生成

人物三视图流程必须显式传 `view_mode=three_view`，不能依赖服务端兼容默认值 `single`。

素材和人物要求齐备后，必须先预估：调用 `generate_model_image`，传 `preflight_only=true`、`confirmed=false`。向用户展示 `estimated_credits` 和可理解的生成摘要，用户确认后才允许再次调用并传 `preflight_only=false`、`confirmed=true`。不得跳过预估、用户确认和正式生成顺序。

后端可配置人物三视图计费，默认可能返回 `estimated_credits=0`。无论是否为零，都要让用户确认开始生成；非零积分必须明确展示具体积分。用户未确认非零积分时不得进入生成。每次重新生成都是新的生成输入，必须重新预估并确认。

服务端生成最终模特 prompt；Skill 不得生成、展示或保存最终模特 prompt。同步返回时，把 `model_image_ref` 先保存为候选引用；异步返回时，把 `model_task_id` 保存到 `VideoHandoffContext.service_state.model_task_id`，再调用 `poll_model_status`。恢复、继续或重试时复用现有 `model_task_id`，不得重复调用 `generate_model_image`。

## 结果确认与回填

生成完成后展示人物三视图。用户确认前，候选引用只能写入 `candidate_model_image_ref`，不得作为已确认固定模特提交视频。用户自然语言确认后：

- 将素材以 `asset_role=model_image`、`confirmed=true` 写入 `VideoHandoffContext.assets`；
- 根据来源记录 `model_origin=existing_three_view | transformed_from_images | text_generated`；
- 写入 `confirmed_model_image_ref` 并回填视频流程使用的 `model_image_ref`；
- 独立流程直接交付三视图，保留该引用供未来视频任务重新展示、确认和复用。

用户拒绝结果或修改人物要求时，状态回到待确认或重新生成，丢弃旧候选引用。商品视频固定模特必须在 `create_video_script` 前确认三视图；脚本、积分预估和最终生成必须复用同一个 `model_image_ref`。更换三视图后，旧商品脚本、旧预估和旧积分确认失效，需要重新生成并确认商品脚本，再重新预估。

复刻方案分析当前不消费 `model_image_ref`。固定模特复刻可以在最终视频预估前确认三视图并传给最终生成，但不得宣称服务端复刻方案已经使用该人物素材；更换复刻人物三视图后需重新预估和确认最终视频。

## WorkBuddy 连接器补充规则

回复语言默认使用简体中文；用户明确使用英文时可用英文回复。解释工具字段、错误和确认信息时保持用户可理解，不展示内部任务 ID、完整密钥、敏感素材 URL 或 `project_id`。

`project_id` 只内部保存和透传，不展示给用户；脚本或方案工具未传 `project_id` 时由服务端自动创建或恢复真实 `project_id` 并返回，收到后必须保存；未返回时保存 `script_id` 或 `replica_script_id`。预估或生成前必须具备后端返回的有效 `project_id` 或可让后端恢复项目归属的脚本任务 ID。没有后端返回的 `project_id` 时，使用 `script_id` 或 `replica_script_id` 让后端恢复项目归属。不得传空字符串作为 `project_id`，不得臆造项目归属、不得用脚本任务 ID 冒充 `project_id`、不得用历史项目标识试探。不得围绕 `project_id` 要求用户提供、修正或查找。

## 用户回复规则

普通用户回复不得展示英文工具名、字段名、内部状态名、接口错误码或原始错误字段；工具名和字段名只可在内部执行或开发文档中使用。不得向用户说明底层上传实现细节、临时凭据、存储路径、内部素材引用或参数字段。向普通用户说明进度时，改用中文动作表达，例如：生成脚本、预估积分、可以上传、我会继续处理素材、素材已准备好、开始生成视频、查询生成进度。

不要说“我先确认某个内部方法在脚本阶段如何引用这张图”这类实现说明；应改说“我先根据这张图整理视频脚本，再给你确认”。

不要解释底层上传、存储、登记和参数传递细节；应改说“可以上传，我会继续处理素材”或“素材已准备好，现在继续生成”。

不得向用户说明内部执行动作、工具准备过程、服务端错误码或自动恢复细节。不说不会扣积分，只说正在预估积分；不说服务端项目错误或重试细节，只说我会继续处理；不说具体素材处理动作，只说素材已准备好。

预估失败时，只说暂时无法完成积分预估；状态说明只使用自然中文，不展示原始字段或状态值。

## WorkBuddy 内部执行规则

WorkBuddy streamableHttp 远程工具只声明服务端工具，不要求也不得调用本地 stdio 辅助工具。

远程工具：

- `video_get_reference_image_upload_token`
- `video_register_reference_image`
- `video_get_reference_media_upload_token`
- `video_register_reference_media`
- `estimate_video_generation`
- `create_video_script`
- `create_replica_script`
- `generate_model_image`
- `generate_video`
- `poll_video_status`
- `poll_model_status`
- `get_video_task_status`

模型：

- `Seedance 2.0`：默认模型。
- `Seedance 2.0 Fast`：快速模型。
- `Seedance 2.0 Mini`：轻量模型。

WorkBuddy 用户提供本地商品图或本地参考媒体时，必须先基于已收集素材意图和必要需求给出三个大纲方向，等待用户确认方向或大纲；不得在用户确认方向或大纲前请求上传确认、上传、登记或调用脚本/方案工具。用户确认方向或大纲后，若脚本或方案工具需要远端素材引用，必须再向用户确认上传素材用于生成脚本或方案；上传素材用于生成脚本不等于确认开始生成视频，不得跳过脚本或方案确认、积分预估和最终生成确认。用户确认上传素材后，才上传并登记本地素材；不得在用户确认上传素材前上传、登记或处理本地素材，不得把上传登记作为用户可见的独立步骤。生成脚本或方案前，必须先准备并记录所有服务端需要的参考素材引用。用户确认完整脚本或方案后的积分预估阶段不得再次上传、登记或处理本地素材。本地商品图的内部执行先检查 `scripts/picset_video_client.py` 是否真实存在：存在时调用远程工具 `video_get_reference_image_upload_token`，必须通过工具结果原文或临时文件原样传给上传脚本标准输入，执行 `python3 scripts/picset_video_client.py upload --file <本地图片路径>`；脚本缺失时按共享协议生成受约束的临时上传器，不得调用不存在的路径；不得把上传 token 写入 shell heredoc，不得手工改写、摘抄或重组 token JSON。脚本返回 `oss_path` 后再调用远程工具 `video_register_reference_image` 登记素材引用，并把登记后的素材引用写入后续服务端参数。

WorkBuddy 本地视频和音频只在对应方向或大纲确认、再确认上传素材后处理：先检查 `scripts/picset_video_client.py` 是否真实存在；存在时按真实文件类型调用远程工具 `video_get_reference_media_upload_token`，执行 `python3 scripts/picset_video_client.py upload --file <本地视频或音频路径>`；脚本缺失时按共享协议生成受约束的临时上传器。上传成功返回 `upload_id` 后调用 `video_register_reference_media`，只把登记返回的 `media_ref` 写入后续字段。本地 MP4/MOV 可作为商品 `video_refs` 或复刻唯一 `target_video`，本地 MP3/WAV 只写入 `audio_refs`；上传登记本身不永久绑定业务角色。复刻只允许唯一主目标视频并写入 `target_video`，不得传 `video_refs`；用户给出多个候选目标时必须先让用户选定一个，不能合并、排序或截断。商品视频才可使用去重后最多 3 个 `video_refs`，且不得传 `target_video`。预估和正式生成必须复用同一素材组合。用户未确认完整脚本或方案时不得调用 `estimate_video_generation`；用户未确认预计积分时，不得调用 `generate_video`。如果用户提供的是本地路径，不得把本地文件路径填入服务端 refs 字段，也不得把上传脚本返回的 `oss_path` 填入服务端 refs 字段。

WorkBuddy 支持不生成视频而直接生成人物三视图：有普通人物照时上传登记后使用 `mode=image_to_image`、`view_mode=three_view` 和 `input_image_refs`；无人物照时使用 `mode=text_to_image`、`view_mode=three_view`。独立调用可省略 `project_id` 并保存后端返回值。已有或新生成三视图都必须展示并由用户自然语言确认，大模型只能辅助检查。固定模特商品视频必须在生成脚本前确认三视图，并在脚本、预估和最终生成中复用同一个 `model_image_ref`。

调用 `estimate_video_generation` 和 `generate_video` 时，`duration_sec` 必须是 JSON 数字，例如 `"duration_sec": 4`，不得传字符串 `"duration_sec": "4"`。商品视频使用 `video_type=product`、`mode=generate` 和商品 `script_id`；复刻使用 `video_type=replica`、`mode=replica` 和 `replica_script_id`，不得混用。爆款复刻目标时长遵循网页版逻辑：优先读取本地目标视频媒体时长，四舍五入后限制在 4-15 秒作为 `duration_sec`；读取失败或目标视频不是本地文件时，再询问用户确认。比例默认 `9:16`，用户明确指定平台、比例或要求跟随参考视频比例时，按用户确认值传入；不得从复刻分析文本里抽取或猜测时长、比例。`generate_audio` 默认 `true`，只有用户明确要求静音时才传 `false`；`audio_refs` 是最多 3 个参考音频引用，与声音开关相互独立。预估和正式生成必须复用同一个 `generate_audio`。`product_image_refs` 必须是字符串数组，不得传对象 `"product_image_refs": { "item": "https://..." }`，也不得传字符串 `"product_image_refs": "https://..."`。

硬性停止条件：未收集到至少 1 张商品参考图或本地商品图意图时，不得预估或生成；用户确认具体积分后上传或登记失败时，不得继续调用 `generate_video`。脚本生成、复刻分析或预估失败时，不得继续调用后续步骤。用户修改脚本、方案、素材、时长、比例、数量、声音选择或参考素材后，必须重新 estimate 并重新请求明确确认。正式生成时生成稳定的 UUID 作为 `request_id`，同一次重试复用同一个 `request_id`。

状态恢复：`generate_video` 返回 `task_id` 后必须保存；如果流程中断或轮询超时，保留 `task_id` 并说明之后可继续查询，恢复后使用已有 `task_id` 调用状态查询，不得重复生成。
