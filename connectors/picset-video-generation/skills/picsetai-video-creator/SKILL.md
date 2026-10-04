---
name: picsetai-video-creator
displayName: Picset AI 视频创作
name_en: picsetai-video-creator
description: >
  用于 Picset AI 视频创作和独立人物三视图生成，包括商品带货视频生成、爆款视频复刻、有人物参考图或无人物参考图的正面/侧面/背面三视图生成。支持 UGC 种草、产品口播、带货短剧、产品演示、开箱种草、痛点解决、TVC 品牌广告等类型，并支持有声或静音视频、参考音频、固定模特和多条视频生成。该 Skill 会路由到生成视频、复刻视频或人物三视图子 Skill，根据用户提供的商品图、唯一主目标视频、人物素材和创作要求，完成用户确认、素材准备、异步生成、状态恢复与结果交付。
description_en: >
  Route Picset AI ecommerce video creation requests across product video generation, viral video recreation, and model image generation while preserving shared context.
argument-hint: 商品图片、唯一主目标视频、人物照片、人物三视图、4-15 秒时长、声音要求或创作目标
---

# Picset AI 视频创作与人物三视图

本 Skill 只负责意图识别、路由、上下文管理、素材引用管理和子任务结果合并，不替代子 Skill 执行具体生成业务。

根据用户目标选择子 Skill：

- 商品视频生成：`picsetai-video-generate`
- 唯一目标视频复刻：`picsetai-video-replica`
- 独立人物三视图生成，或视频固定模特准备：`picsetai-model-generate`

用户可以只要求生成人物正面、侧面、背面三视图，不需要同时生成视频、提供商品图或先创建视频脚本。普通真人出镜不触发固定模特；只有用户明确要求固定人物、同一人物、人物一致性，或明确提供人物素材用于固定模特时，才路由人物三视图流程。

视频素材字段必须先按业务场景隔离：商品视频使用 `video_type=product`、`mode=generate`，可使用最多 3 个 `video_refs`，不得使用 `target_video`；视频复刻使用 `video_type=replica`、`mode=replica`，只使用唯一 `target_video`，不得使用 `video_refs`。本地 MP4/MOV/MP3/WAV 必须先通过媒体上传凭证、共享协议选择的 HTTP PUT 上传执行器和媒体登记工具取得 `agent-media:` 引用；上传前先检查随包脚本，缺失时才按共享协议生成受约束的临时上传器；视频和音频共用上传工具，但使用时按字段校验真实媒体类型。`create_video_script.video_type=commerce|tvc` 仅表示脚本创作风格，不是最终视频业务管线。

固定模特商品视频必须先完成用户对人物三视图的自然语言确认，再生成完整商品脚本。大模型可以辅助检查三视图，但不能替用户确认。商品脚本、视频预估和最终生成必须复用同一个 `model_image_ref`；更换三视图后重新生成并确认商品脚本、重新预估和确认积分。

所有子流程共享同一份 `VideoHandoffContext`。若上下文不足，先补齐当前子流程必需的素材和确认信息，再继续路由。复刻方案分析当前不消费人物三视图，不得向用户宣称复刻方案已使用固定模特素材。

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
