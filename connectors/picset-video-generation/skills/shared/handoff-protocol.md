# 交接协议

主 Skill 与子 Skill 之间只通过 `VideoHandoffContext` 交接视频创作和人物三视图状态。主 Skill 负责创建、读取、合并和透传上下文；子 Skill 只更新自己负责的字段，并返回可继续执行的下一步。

```yaml
VideoHandoffContext:
  active_flow: generate | replica | model
  project:
    project_id:
  product:
    name:
    description:
    verified_facts: []
    uncertain_facts: []
    confirmed_selling_points: []
  requirements:
    country:
    language:
    video_count:
    video_type:
    duration_sec:
    aspect_ratio:
    generate_audio: true
    use_fixed_model:
    replica_requirements: []
  assets:
    - id:
      asset_type: image | video | audio
      asset_role: product_image | target_video | reference_video | reference_audio | model_image | scene_image
      source: uploaded | generated
      model_origin: existing_three_view | transformed_from_images | text_generated
      local_path:
      registered_ref:
      confirmed: false
  drafts:
    outline:
      status: 草稿、待选择、待确认、已确认或已失效
      directions: []
      selected_direction_id:
    service_script:
      mode: generate | replica
      visible_script_or_plan:
      duration_sec:
      aspect_ratio:
      model_image_ref:
      status: 无、待确认、已确认或已失效
    credit_confirmation:
      estimated_credits:
      status: 未就绪、待确认、已确认或已失效
    model:
      person_requirements: []
      person_summary:
      view_mode: three_view
      candidate_model_image_ref:
      confirmed_model_image_ref:
      estimated_credits: 0
      status: 无、待确认或已确认
  service_state:
    script_id:
    replica_script_id:
    model_task_id:
    model_prompt_id:
    generation_request_ids: []
    generation_task_ids: []
  results:
    - id:
      role: model_image | video
      status: 生成中、成功或失败
      artifact_ref:
```

`project_id` 只在内部保存和透传，用于项目归属、素材登记和生成历史关联，不得展示给用户。脚本、方案或人物三视图工具未传 `project_id` 时，服务端可以自动创建真实 `project_id` 并返回；收到后必须保存到 `VideoHandoffContext.project.project_id`。脚本或方案未返回项目时保存 `script_id` 或 `replica_script_id`，预估或生成时可用它恢复项目归属。独立人物三视图不要求事先存在视频、脚本或项目，不得为了满足字段而臆造、试探或要求用户提供 `project_id`。不得传空字符串，不得用脚本任务 ID 冒充项目 ID，不得用历史项目标识试探。

## 用户回复规则

普通用户回复不得展示英文工具名、字段名、内部状态名、接口错误码或原始错误字段；工具名和字段名只可在内部执行或开发文档中使用。不得向用户说明底层上传实现细节、临时凭据、存储路径、内部素材引用或参数字段。向普通用户说明进度时，改用中文动作表达，例如：生成脚本、生成三视图、预估积分、可以上传、素材已准备好、开始生成视频、查询生成进度。

不要说“我先确认某个内部方法在脚本阶段如何引用这张图”；应改说“我先根据这张人物三视图整理视频脚本，再给你确认”。不要解释底层上传、存储、登记和参数传递细节；应改说“可以上传，我会继续处理素材”或“素材已准备好，现在继续生成”。

不得向用户说明内部执行动作、工具准备过程、服务端错误码或自动恢复细节。不说不会扣积分，只说正在预估积分；不说服务端项目错误或重试细节，只说我会继续处理。预估失败时，只说暂时无法完成积分预估；状态说明只使用自然中文。

## 用户确认规则

大模型可以辅助检查人物素材是否包含同一人物的正面、侧面、背面，是否清晰、完整和无遮挡，但不能替用户确认。已有三视图和新生成三视图都必须展示给用户，只有用户以“确认使用”“就用这张”“三视图没问题”等自然语言明确表示采用后，才允许把 `confirmed` 置为 `true` 并写入 `confirmed_model_image_ref`。只上传图片、询问效果、让系统看看或大模型自行判断均不构成确认。

普通人物照、多张独立视角人物照和已合成三视图必须区分记录。只有用户确认的一张同一人物正面、侧面、背面合成图才能作为固定模特 `asset_role=model_image`；普通人物照不得直接冒充已确认三视图。

## 本地上传执行器选择

本地文件只有在用户已确认当前阶段允许上传后才能处理。图片必须调用图片上传凭证与登记工具；MP4、MOV、MP3、WAV 必须调用媒体上传凭证与登记工具，不得混用。

每次上传前必须先检查当前 Agent 或已安装 Skill 是否提供匹配的官方上传脚本，不得假设脚本一定存在：

1. 图片依次检查平台声明的图片上传器和通用 `scripts/picset_video_client.py`。
2. 视频或音频依次检查平台声明的媒体上传器和通用 `scripts/picset_video_client.py`。
3. 只有文件真实存在时才执行；存在时优先使用随包脚本，不得重复生成另一个上传器。
4. 脚本不存在但 Agent 具备本地文件写入和 Python 3 执行能力时，允许在系统临时目录生成一次性标准库上传器；不得写入已安装 Skill 目录，也不得把临时上传器当作长期资产。
5. Agent 不具备本地文件读取、临时文件写入或 Python 3 执行能力时立即停止，只说明当前环境无法处理本地素材；不得伪造上传、登记或素材引用。

临时上传器不是自由发挥的业务实现，必须严格满足以下固定契约：

- 只能使用 Python 标准库，不安装或导入 `oss2`、`requests` 或其他第三方依赖。
- 从标准输入读取上传凭证 JSON；凭证不得进入源码、命令行参数、shell 内联文档、日志或用户回复。
- 校验本地文件存在、真实字节数、服务端 `maxBytes` 和 `allowedMimeTypes`；图片与媒体按对应凭证处理。
- 图片凭证使用服务端 `pathPrefix` 生成单个对象路径；媒体凭证必须原样使用服务端唯一 `objectKey`，并保留 `uploadId`。
- 使用 OSS V1 HMAC-SHA1 签名执行单次 HTTPS PUT，保持 TLS 和主机名校验开启；不得使用 `--insecure` 或等价降级。
- 成功时只输出登记所需的 `oss_path`、`file_type`、`file_size`，媒体额外输出 `upload_id`；失败时输出稳定、脱敏的错误，不输出 STS 字段或签名。
- 上传完成或失败后删除本次生成的临时脚本；重新上传必须重新获取凭证，不得复用过期凭证。

上传脚本只负责减轻 Agent 的实现负担，不是流程前提。无论使用随包脚本还是临时上传器，上传后都必须调用对应登记工具；图片只使用登记返回的图片引用，视频或音频只使用登记返回的 `media_ref`，不得把本地路径或 `oss_path` 直接传入脚本、预估或生成工具。

## 内部交接规则

用户消息不得包含内部任务 ID、`project_id`、`script_id`、`replica_script_id`、`model_task_id`、`model_prompt_id`、`generation_request_ids` 或 `generation_task_ids`。上下文不保存 STS、OAuth、SK、最终 prompt、最终视频 prompt、最终模特 prompt、原始接口参数、调试信息或完整敏感 URL。

`asset_role` 只描述当前 `VideoHandoffContext` 中的业务用途，不会写入媒体上传准入记录，也不限制同一已登记视频在其他任务中的用途。`asset_role=target_video` 表示复刻唯一主目标视频，只能有 1 个；复刻流程不得使用 `asset_role=reference_video` 或 `video_refs`。`asset_role=reference_video` 只用于商品视频，去重后最多 3 个；商品视频不得使用 `target_video`。`asset_role=reference_audio` 表示最多 3 个参考音频；`asset_role=model_image` 表示已由用户确认的人物三视图。`asset_role=scene_image` 仅保留为未来扩展，本期不执行或宣称场景图生成。

`requirements.generate_audio` 默认 `true`，只有用户明确要求静音时才改为 `false`。它与参考音频素材相互独立；预估和正式生成必须复用同一个最终值。

固定模特商品视频必须在 `create_video_script` 前确认人物三视图，并在脚本、预估和最终生成中复用同一个 `model_image_ref`。更换三视图后，不删除历史数据，但必须把旧商品脚本和积分确认标记为已失效，重新生成并确认脚本，再重新预估。复刻方案分析当前不消费 `model_image_ref`；复刻更换三视图只使旧视频预估和确认失效，不得宣称复刻方案分析已使用人物三视图。
