# Playbook｜从定稿 JD 发起职位发布草稿

适用于最终 JD 已生成且用户已确认标题的固定后续步骤。

1. 第 5 节最终 JD 出现后，确认当前会话实际暴露 `zhaopin-qiye-connector.generateJobRedirectLink`；Tool 不可用时，紧跟 JD 说明未生成链接的实际原因，不伪造链接。
2. 核对标题不超过 200 字符，最终 JD 正文为 10–10000 字符，且不含评分、待确认项、内部备注或模型推断。
3. 调用 Tool，输入仅为 `request.title` 和 `request.description`。
4. 仅展示 Tool 返回的 `url` 与 `expireAt`；不展示内部 `code`。
5. 明确告知：链接打开的是预填发布表单，用户需自行核对并确认发布；草稿链接不等于职位已创建、发布或审核通过。
6. Tool 失败、无 URL、链接过期、未认证或无权限时，如实说明，保留 JD 文本供用户使用；不重试写入，也不自动换链接。
