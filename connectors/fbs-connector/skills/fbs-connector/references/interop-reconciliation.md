# 可选技术回执与业务对账

工具输出可带 interopReceipt；它是可选诊断子对象，不能当输入参数，也不是 member_service_receipt 或 profile_operation_receipt。缺失或探针未启用不意味着业务失败，不能为取得探针而重放一次写入。

关联编号不可互换：`episodeId`仅在本地把同一用户任务中的动作分组；`operationId`只标记一项写操作并在同载荷重试时保持不变；`attemptId`每次实际调用各异；`requestRef`只能从同一次服务响应的interopReceipt观察。工具schema不接受episodeId/attemptId时不发送它们；requestRef缺失就保留`not_observed`，不由时间、账号或operationId推算。

只读取服务实际返回的 schemaVersion、requestRef、可选 flowRef、flowCorrelation、correlationScope、probeEventSampled、completeBehaviorCoverage 和证据标志。已知 v1 的 same_oauth_authorization_flow 表示同一次 OAuth 授权链的短时服务关联；single_process_ttl 表示进程重启、过期或跨实例可能未观察。它不证明 WorkBuddy、专家或自然人在执行。

探针每流每工具/结果只记录首条；completeBehaviorCoverage=false。probeEventSampled=false 不能推断没有操作，不用记录条数计算用户数、偏好强度或成交。旧/未知 schema 保留为未解释数据，不补齐字段、不提升 trust，不因此阻塞已有业务结果。

三种结果分开核验：

1. 技术关联：requestRef/flowRef 可与服务日志、受控宿主证据汇合；静态头和客户端声明不补成宿主证明。
2. 业务结果：按工具 success/isError、serviceRequestAccepted、原 operationId/读取审计判断。HTTP 200 或 interopReceipt 存在不是成功。FBS_RESPONSE_LIMIT 且 serviceRequestAccepted=true 时业务可能已执行，先原号回读，不改号重做。
3. 本人选择：用途同意、事实确认、需求提交、联系许可各有自己的服务回执。探针、账号认证或专家推断不能自动生成这些确认。

用户看见简洁结果和下一步；仅在排障需要时展示安全 requestRef。flowRef 不作账号、设备、安装实例或长期画像主键。除用户本次允许保存诊断引用外，不为对账主动写长期记忆；不持久化令牌、授权码、Cookie、账号伪名、原始表单或聊天全文。
