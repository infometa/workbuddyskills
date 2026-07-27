# 鹅厂职业经纪人 埋点事件清单 Event List

| 事件名称 eventCode | 采集方式 collection | 上报时机 trigger | 设备标识 A2 | 用户标识 skill_user | Skill名称 skill_name | 运行平台 skill_platform | 操作系统 skill_os | Skill版本 skill_version | 私有参数 params |
|---------|:------------:|----------|-------|-------|-------|-------|-------|-------|-------|
| `skill_invoked` 经纪人调用 | Hook&track | 用户召唤职业经纪人 / 命中某能力路由时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID；`source` 调用来源；`capability` 命中能力（可选，枚举：profile画像/qa问答/assessment测评/coaching教练/liveflow活水/resume简历） |
| `task_completed` 任务完成 | Hook&track | 一次经纪人服务流程结束时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID；`status` 完成状态；`fail_reason` 失败归因（可选，枚举：skill_bug/llm_limitation/user_cancel/dependency_error/timeout） |
| `error_occurred` 异常发生 | track | 捕获到异常或错误时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `error_type` 错误类型；`error_message` 错误摘要（脱敏）；`phase` 发生阶段；`error_code` 错误码（可选） |
| `session_end` 会话结束 | Hook | 会话关闭时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID；`duration_seconds` 会话时长；`reason` 结束原因；`turn_count` 对话轮数（可选） |
| `liveflow_recommended` 活水推荐触发 | track | 活水机会推荐能力输出真实在招岗位列表时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID；`rec_count` 本次推荐岗位数 |
| `assessment_offered` 发起测评 | track | 打开职业DNA测评页时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID；`offer_source` 发起来源（可选，枚举：coaching教练/profile画像/user主动） |
| `assessment_completed` 测评完成 | track | 用户贴回职业DNA结果码时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID |
| `coaching_engaged` 教练对话深入 | track | 教练对话进入方向/卡点澄清等实质环节时 | 机器指纹 | whoami自动采集 | career-broker | 运行时自动检测 | 运行时自动检测 | 从配置自动读取 | `session_id` 会话ID；`turn_depth` 对话深度（可选，枚举：light轻聊/deep深入） |
