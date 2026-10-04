---
name: picsetai-video-generate
displayName: Picset AI 商品带货视频生成
name_en: picsetai-video-generate
description: >
  用于 Picset AI 电商商品视频生成。适用于用户提供商品图，并希望生成有声或静音的商品带货视频、种草视频、口播视频、产品演示视频、开箱视频、痛点解决视频、品牌广告视频或其他电商短视频。支持 UGC 种草、产品口播、带货短剧、产品演示、开箱种草、痛点解决、TVC 品牌广告、参考音频、固定模特和多条视频生成。该 Skill 会智能规划并提供多个脚本大纲方向，用户确认后交由服务端生成完整脚本并按确认流程提交最终视频。声音生成默认开启，只有用户明确要求静音时关闭。
description_en: >
  Handle Picset AI ecommerce product video generation requests from product images and user creation requirements.
argument-hint: 商品图片、卖点、4-15 秒时长、比例、声音、语言、国家和可选视频类型
---

# Picset AI 商品视频生成

本子 Skill 负责商品视频生成流程。执行时必须使用共享协议：

- `../shared/handoff-protocol.md`
- `../shared/credit-confirmation-protocol.md`

从主 Skill 接收上下文后，只处理商品视频生成相关步骤，并将结果写回共享上下文。

## 输入规则

- 商品图必填。缺少商品图时，只询问并引导用户提供商品图，不追问其他生成信息。
- 若用户提供本地商品图路径或本地附件，先基于已收集素材意图和必要需求给出三个大纲方向，等待用户确认方向或大纲；用户确认方向或大纲后，若脚本工具需要远端素材引用，必须再向用户确认上传素材用于生成脚本。用户确认上传后进入生成脚本前素材准备，上传、登记并记录所有服务端需要的参考素材引用。不得在用户确认方向或大纲前请求上传确认；不得在用户确认上传素材前上传、登记或处理本地素材。不得使用 OSS SDK，不得使用 oss2，不得引入第三方上传依赖。
- 上传素材用于生成脚本不等于确认开始生成视频，不得跳过脚本确认、积分预估和最终生成确认。
- `project_id` 只内部保存和透传，不展示给用户；`create_video_script` 未传 `project_id` 时由服务端自动创建或恢复真实 `project_id` 并返回，收到后必须保存；未返回时保存 `script_id`。预估或生成前必须具备后端返回的有效 `project_id` 或可让后端恢复项目归属的 `script_id`。没有后端返回的 `project_id` 时，使用 `script_id` 或 `replica_script_id` 让后端恢复项目归属。不得传空字符串作为 `project_id`，不得臆造项目归属、不得用脚本任务 ID 冒充 `project_id`、不得用历史项目标识试探。不得围绕 `project_id` 要求用户提供、修正或查找。
- 两层 `video_type` 语义不同：调用 `create_video_script` 时，它是脚本创作风格，TVC 品牌广告传 `tvc`，其余电商类型传 `commerce`；调用 `estimate_video_generation` 和 `generate_video` 时，它是业务管线，商品视频传 `video_type=product`，并与 `mode=generate`、`script_id` 保持一致。不要把 commerce/tvc 传给最终生成，也不要把 product 传给商品脚本。
- `duration_sec` 必须是 4-15 整数秒；3、16、10.5 均为无效值，需要请用户改为 4 到 15 之间的整数秒。
- `generate_audio` 为可选布尔值，默认 `true`；只有用户明确要求静音时才传 `false`。`audio_refs` 是最多 3 个参考音频引用，与声音生成开关相互独立；提供参考音频不替代 `generate_audio`。
- 商品视频可使用用户明确提供的参考视频，写入 `video_refs`，去重后最多 3 个；商品视频不得使用 `target_video`。本地 MP4/MOV 必须调用 `video_get_reference_media_upload_token`、共享协议选择的上传执行器和 `video_register_reference_media`，使用登记返回的 `agent-media:` 引用；本地 MP3/WAV 同样登记后写入 `audio_refs`。参考媒体必须在脚本确认和积分预估前准备完成，预估与正式生成使用相同引用。媒体上传记录不绑定业务角色，同一视频可在不同任务中作为商品参考或复刻目标，但当前商品流程只能写入 `video_refs`。
- 普通真人出镜只写入 `requirements`。只有用户明确要求固定人物、一致人物或提供人物素材用于固定模特时，才进入 `picsetai-model-generate`。固定模特不是第三种 `video_type`。
- 只处理商品视频生成，不得执行场景图生成，不得宣称场景图生成。

## 大纲方向

在本地素材意图和必要需求齐备后，先给用户三个大纲方向。三个大纲方向只是创意方向摘要，不是完整脚本，不是最终 prompt，也不是逐镜头分镜。此阶段不得请求上传确认、不得上传、不得登记、不得调用 `create_video_script`。

用户选择方向后，脚本工具需要远端素材引用时，必须先向用户确认上传素材用于生成脚本；用户确认后，先按共享协议检查匹配的随包脚本；存在时直接使用，缺失且 Agent 具备本地 Python 能力时才生成受约束的临时上传器。商品图调用 `video_get_reference_image_upload_token`、选定上传执行器和 `video_register_reference_image`；本地参考视频或音频调用 `video_get_reference_media_upload_token`、选定上传执行器和 `video_register_reference_media`。将登记后的引用记录到 `VideoHandoffContext.assets`。若用户要求固定模特，必须先完成 `picsetai-model-generate`：已有合格合成三视图时展示并取得用户自然语言确认，普通人物照转换或无人物照生成时显式使用 `view_mode=three_view`，得到用户确认的 `model_image_ref` 后，才调用 `create_video_script`。大模型不得替用户确认人物三视图。再调用 `create_video_script` 让服务端生成完整脚本，并在固定模特场景传入已确认的同一 `model_image_ref`。若返回 `script_id` 且 `status` 不是 `success`，即使同时出现 `script_or_plan` 也不得当作完整脚本，必须保存 `script_id` 并调用状态查询工具直到取得 `status=success` 且完整 `script_or_plan` 后再展示给用户确认。完整脚本必须由服务端生成，不得把大纲方向、处理中占位文本、最终 prompt 或逐镜头分镜当作完整脚本。

## 生成顺序

内部执行顺序为：先给用户三个大纲方向 -> 用户确认方向或大纲 -> 用户确认上传素材用于生成脚本 -> 生成脚本前素材准备 -> 固定模特场景先生成或确认人物三视图 -> 生成脚本 -> 必要时查询完整脚本 -> 用户确认脚本 -> 预估积分 -> 用户确认开始生成视频 -> 提交最终生成 -> 查询生成进度。

脚本确认先于 `estimate_video_generation`：用户确认服务端生成的完整脚本前，不得预估积分。

预估前确定最终声音选择、商品参考视频和固定模特引用。调用 `estimate_video_generation` 时传 `video_type=product`、`mode=generate`、`script_id`、最多 3 个 `video_refs`、固定模特场景的 `model_image_ref` 以及 `generate_audio`；正式调用 `generate_video` 时必须复用相同字段和值，不得传 `target_video`。用户修改声音选择、参考音频、参考视频或其他生成输入后，旧预估和旧确认失效，必须重新预估并确认。

`estimate_video_generation` 返回具体积分后，必须用 `estimated_credits` 向用户确认具体积分消耗；确认具体积分先于 `generate_video`，用户确认预计消耗积分前，不得生成视频。

积分确认先于 `generate_video`：用户确认预计消耗积分前，不得生成视频。

生成脚本前素材准备只允许发生在用户明确确认上传素材用于生成脚本后、`create_video_script` 前：此时商品图才可通过 HTTP PUT 上传到 OSS 并调用 `video_register_reference_image`；本地 MP4/MOV/MP3/WAV 通过共享协议选定的 HTTP PUT 上传执行器上传后调用 `video_register_reference_media`，并把返回的 `agent-media:` 引用写入 `VideoHandoffContext.assets`。用户确认完整脚本后的积分预估阶段不得再次上传、登记或处理本地素材。

如果 `create_video_script`、`estimate_video_generation` 或其他工具 schema 看起来需要远端素材引用，仍不得绕过对应确认门；不得用空字符串、占位项目、历史项目、臆造项目标识或脚本任务 ID 试探 `project_id`。缺少服务端返回的有效项目归属且缺少可用于恢复项目归属的 `script_id`，或缺少可在当前阶段合法使用的素材引用时，停止后续工具调用，只向用户说明暂时无法继续处理。

用户明确确认预计积分后，才调用 `generate_video` 执行最终生成；用户确认预计积分前不得调用 `generate_video`。正式生成必须传 `video_type=product`、`mode=generate`、商品 `script_id` 和已确认的 `generate_audio`；有参考音频时传 `audio_refs`，有商品参考视频时传最多 3 个 `video_refs`，不得传 `target_video`。固定模特场景必须传与 `create_video_script` 和积分预估完全相同的 `model_image_ref`。用户更换人物三视图后，旧商品脚本、旧预估和旧积分确认失效；不得只替换最终生成参数，必须重新生成并确认商品脚本，再重新预估。`generate_video` 先于 `poll_video_status`，必须保存返回的 `task_id` 到 `VideoHandoffContext.service_state.generation_task_ids`。如果流程中断或需要重试，恢复 task_id 后继续调用 `poll_video_status`，不得重新生成。每次轮询 poll 状态都要保存或更新到 `VideoHandoffContext.results`，并只向用户展示可理解的生成状态和结果。

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
