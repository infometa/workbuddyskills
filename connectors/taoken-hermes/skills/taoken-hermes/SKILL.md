---
name: taoken-hermes
description: 调用用户已授权的淘肯 Hermes 龙虾，提交任务、查询进度、查看历史与积分。
---

# 使用淘肯龙虾

先确认用户想交给自己的龙虾完成的具体任务。连接器只访问当前授权账号，不接收其他人的手机号、userId、ClawdToken 或机器名称。

1. 查看历史时调用 `hermes_list_sessions`，需要续聊时选择明确的 `sessionId`。
2. 用户要求执行任务后调用 `hermes_start_task`。`message` 保留用户明确的需求；`requestId` 使用本次消息唯一编号（字母、数字、下划线、短横线等，最多 200 字符）。同一次提交超时或重试，必须保持 requestId、sessionId 和 message 不变；新消息必须使用新 requestId。
3. 返回 queued/running 只表示任务已接收，不能声称已经完成或已经扣费成功。
4. 用 `hermes_get_task_progress` 获取结果，首次 afterSeq=0，后续使用返回的 nextSeq。单次等待不超过 15 秒。查询几次仍未完成，就告知用户任务编号并让进度面板继续刷新，避免无限轮询占用对话。
5. `terminal=true` 后停止查询。run.failed、run.cancelled 不是成功；不要编造结果。文件链接只使用后端真实返回的 HTTPS 链接。
6. 仅在用户明确要求停止时调用 `hermes_stop_task`。
7. 用 `hermes_get_balance` 读取淘肯积分余额；它不是 WorkBuddy 的积分或账单。

## 认证与边界

- OAuth 版通过浏览器进入淘肯授权页，使用已有账号手机号验证码登录，用户确认后才授权。此版本不负责新用户注册或重开 Profile。
- Token 测试版由用户在平台凭证表单填写自己的 ClawdToken；绝不让用户把凭证发到聊天里。
- 认证失败时提示重新连接，不要求用户提供原始 Token，不输出密钥、授权码或短信验证码。
- 此连接器只提供已列出的聊天和查询能力。商品图册、1688、报价等业务是否可执行取决于该用户龙虾已有的工具配置，不声称额外业务接口已经接通。
- MCP Apps 面板不可用时，使用文本工具查询仍可完成任务；不要把面板缺失误报为任务执行失败。
- 外部发送、付款、删除、客户群发等操作必须取得用户明确授权，不因工具具备执行能力而自动进行。
