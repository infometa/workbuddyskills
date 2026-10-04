# 标准工作流

## 新建画布工作流

1. 调用 `canvas_get_node_catalog` 获取节点和端口约束。
2. 调用 `material_list` 查找用户素材；公开 URL 素材先调用 `material_import_url`。
3. 使用 `canvas_create_workflow` 一次写入节点、素材引用、连线、分组和布局。
4. 调用 `canvas_validate`，确认画布有效。
5. 返回画布 `open_url`，不要再创建空白画布后逐次拼接。

## 修改已有画布

1. 调用 `canvas_get_project` 读取最新内容和 `revision`。
2. 根据用户要求构造最小操作集合。
3. 调用 `canvas_apply_operations`，传入最新 `base_revision` 和唯一幂等键。
4. 调用 `canvas_validate` 验证修改结果。
5. 如果发生 revision 冲突，重新读取并重新构造操作。

## 运行画布节点

1. 调用 `canvas_get_project` 确认目标节点、参数和前置连线。
2. 调用 `canvas_estimate_node`。
3. 展示预计积分并等待用户明确确认。
4. 使用确认令牌调用 `canvas_run_node`。
5. 保存任务 ID，按能力对应的间隔轮询 `generation_get_task`。
6. 成功后确认 `writeback_status`，并返回素材与画布入口。

## 直接生成媒体

1. 调用 `studio_get_balance` 和 `studio_get_generation_catalog`。
2. 使用 `material_list` 获取当前账号参考素材 ID。
3. 以正式生成工具名和完整参数调用 `generation_estimate`。
4. 展示预计积分并等待用户明确确认。
5. 把确认令牌加入完全相同的参数，调用图片、视频、音频或视频处理工具。
6. 保存任务 ID并持续查询 `generation_get_task`，直到终态或达到等待上限。
7. 成功后使用 `online_url` 向用户提供外部访问地址；`access_path` 仅用于站内打开。

## 查询和恢复任务

1. 已知任务 ID 时直接调用 `generation_get_task`。
2. 不知道任务 ID 时调用 `generation_list_tasks`，按类型、状态或时间定位。
3. 对仍在运行的任务继续查询，不重新提交。
4. 对失败任务先查看 `retryable` 和退款状态；只有用户要求重试时才重新预估。
5. 本地下载或展示失败但平台任务成功时，重新查询任务获取有效地址，不重新生成。
