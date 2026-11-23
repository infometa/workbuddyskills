# 项目工作流

选择项目制或继续已有项目时阅读。把创作目标、参考素材、约束和反馈交给 Flova Agent，由其负责项目内的规划、制作与资产协调。

## 1. 选择项目并读取上下文

已有项目继续在原项目中工作。需要查找时使用 `creation_project_list`，分页保持相同 `scope` 并沿用返回的 `next_cursor`，不混用页码与游标。

按返回的 `api_version` 选择匹配工具；版本未知时使用 `creation_project_runtime`。不从 ID 推断版本，不隐式迁移。无法读取旧项目时说明限制，由用户决定是否迁移；不要套用 V3 参数调用旧工具。

新项目确有必要且目标清楚后，调用 `creation_project_create`，给出简洁名称；除非用户另有选择，保留默认 `permission_mode`。

V3 先读取 `creation_project_info`。使用 `creation_project_graph` 或 `creation_project_search` 定位内容，`creation_project_nodes` 查看节点；使用 `creation_document_search` 和 `creation_project_document` 读取文档，`creation_asset_resources` 查看素材候选，`creation_composition_get` 查看成片时间线。文档以实际 `node_id` 选择，不假定固定的 `final_video_spec` 入口。

遵循分页，保留 epoch、节点和内容版本；局部读取不作为完整替换载荷，遇到冲突先重读权威状态。

项目可有多个讨论历史独立、共享文档与资产的对话。使用 `creation_conversation_list` 选择对话，需要独立讨论时才创建新对话。保留 `conversation_id`，运行、查询及待处理操作在原对话中继续。

## 2. 委托创作与修改

通过 `creation_run` 提交首次创作和普通修改意见，传入项目、对话、`content` 或结构化 `parts`，以及已上传的 `files`。

说明创作目标、素材用途、保留项、修改项及约定的评审节点。不要在外部 Agent 另建一套与项目竞争的制作状态。同一次提交重试使用原请求 ID；超时先查询原运行。

分阶段项目按任务需要推进分镜、关键元素与视觉参考、关键帧、视频镜头及音频、时间线和导出，在约定节点评审；用户要求一次完成时，让 Flova Agent 在授权范围内编排，不自行增加默认停顿。

用户指定服务端创作 Skill 时，先按[线上 Skill 指引](server-skills.md)核对真实 ID、分享码或工具查询结果，传入 `skill_id` 或 `skill_share_code`，不同时传两者。名称有歧义时请用户选择，不静默换成相似 Skill。普通续作保留原绑定；未指定时不强制寻找服务端 Skill。已确认的标识通过工具参数传递，不把服务端 Skill 名称、ID 或分享码写入自然语言创作消息。

## 3. 跟踪同一次运行

`creation_run` 或 `creation_run_resume` 返回 `stream_chat_id` 后持续跟踪原运行。

1. 首次调用 `creation_run_status` 传项目、对话和运行标识，不传 `from_message_id`。V3 不使用旧版事件、预览或资源链接开关。
2. 保存返回的 `next_event_id`；后续将它作为 `from_message_id`，并更新游标。
3. 按实际状态、`terminal` 和建议间隔查询。进度安静或增量为空，不代表完成，也不是重新提交的理由。
4. 对已观察的未完成媒体任务独立使用 `creation_resource_status`，每次最多 100 个任务 ID；通过 `creation_resource_info` 读取单项详情和可用链接，不只依赖事件增量判断媒体状态。
5. 第一个资源成功后即可按宿主规则展示，继续跟踪后续任务，保留交付去重和失败待补交状态。
6. 运行暂停或终止时调用 `creation_run_result`，读取结果、错误和待处理操作；需要时用 `creation_chat_pending_actions` 核实当前决定。不能因返回中缺少 `blocking` 字段而忽略需要用户决定的操作。

中断后保留项目、对话、运行、游标、媒体任务和已交付状态，恢复原工作。部分资源成功不能代替整轮状态核对。

## 4. 提交用户答复与审批

服务提出问题时，取得用户答复后，用 `creation_run_resume` 提交准确 `action_id` 及受支持的 `option_id`、`free_text` 或有序 `answers`。有序答案使用 `selected_values` 和／或 `free_text`，不与单答案字段混用。

服务审批使用 `creation_interaction_submit`，传入真实 `interaction_id`、用户答复和稳定请求 ID。普通修改通过 `creation_run` 发送，不冒用问题恢复或审批接口。

## 5. 项目媒体展示

通过状态与资源工具取得成功媒体，以 `creation_resource_info` 等实际可用读取工具获取可访问链接，按[入口 Skill 的媒体展示规则](../SKILL.md)及时交付。需要项目入口时读取原项目信息。展示不能代替运行状态、任务状态和待决事项核对。

## 6. 时间线、导出与交付

按约定节点评审，通过原项目中的 `creation_run` 提交修改。素材完成后，由 Flova Agent 按需求组装或调整时间线；通过 `creation_composition_get` 查看轨道、片段、设置与诊断。Sequence 排序不能代替最终成片时间线。

运行成功、待决事项已解决且导出属于用户授权目标时，对目标 Composition 调用 `creation_export_readiness`。仅在 `ready=true` 后，将准确的 `composition_node_id`、`expected_node_revision` 和稳定请求 ID 传给 `creation_export_video`。

保存导出任务 ID，通过 `creation_export_status` 跟踪至终态。同一导出重试保留原版本和请求 ID；丢失响应时用任务 ID 或请求 ID 恢复查询，不同时传两者。受理不等于成片完成。

用户要求项目资源归档时，使用 `creation_download_all` 和 `creation_download_status`；归档不替代成片导出，单项素材交付也不要求导出。

导出或归档返回 `status="done"` 且提供输出 URL 后，直接交付实际下载链接；展示或取回链接时使用原任务，不重新发起导出或归档。

需要项目入口时，交付服务返回的项目链接；缺少时读取原项目信息，不自行构造 URL。说明用户现在可评审、修改、继续制作还是下载。

## 7. 取消、恢复和分支

用户要求取消时，使用 `creation_run_cancel` 操作准确运行并跟踪至终态；取消不撤销完成的工作或实际消耗。

用户要求恢复时，确定历史消息和恢复模式，使用 `creation_project_restore_preview` 说明影响；取得确认后，以匹配的 `preview_token` 调用 `creation_project_restore`。预览过期或项目改变时重新预览。

`creation_project_branch` 创建新项目，`creation_conversation_branch` 在原项目中创建新对话；按用户意图选择，不自动创建分支。
