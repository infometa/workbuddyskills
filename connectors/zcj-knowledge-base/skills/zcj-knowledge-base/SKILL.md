---
name: zcj-knowledge-base
description: 需要检索「中城交智枢交通知识库」（平台公共库：交通运输法规、行业标准与业务资料）时使用。不包含企业知识库与个人知识库。
---

# 中城交知识库 Skill（Hub v1 · 中城交智枢交通知识库）

## 何时使用

- 用户询问交通运输法规、行业标准、公开业务资料
- 需要在智枢任务资料中的「中城交智枢交通知识库」做语义检索

## 工具

- **search**：唯一对外工具；服务端已锁定「中城交智枢交通知识库」（TongDa `public` / `ai-master-public`），无需也不应传 `user_id` / `scope` / `space_codes` / `doc_ids`

## 不要做

- 不要声称可查企业知识库子空间或个人上传文档
- 不要要求用户填写 user_id 或空间编码
- 不要编造未检索到的内容；无结果时如实说明并建议换关键词
- 用户缺少 API Key 时，引导其前往 https://www.zcjsh.com/contact 申请
