---
name: qc-manage
display_name: 质检服务连接器
display_name_en: Quality Inspection Connector
description: 质检服务 MCP 连接器（OAuth 2.1 授权）。把标准落成规则或 SOP，提交会话或录音到已绑定任务做正式质检，并查询分数、命中和客户高频问。
description_zh: 质检服务 MCP 连接器。通过 OAuth 登录后配置规则与 SOP、提交正式质检，并解读分数、命中和客户高频问。
description_en: Quality inspection MCP connector. After OAuth sign-in, land rules and SOPs, submit formal inspections, and explain scores, hits, and frequent customer questions.
category: automotive
version: 1.1.0
author: Tencent Automotive Industry
---

# 质检服务 MCP

本连接器对接质检 MCP（服务名 `qc-manage`）。使用 **MCP Streamable HTTP + OAuth 2.1** 登录。租户由连接配置里的 `X-Tenant-Id` 带上，不写进工具入参。

## 使用流程

1. **首次使用**：在连接器管理页点击「连接」。浏览器打开 VCam 登录页；已经登过则直接完成。页面出现「连接成功」后回到 WorkBuddy。Token 保存在本机。
2. **日常使用**：不必重复登录，直接调用工具。
3. **授权过期**：调用返回 `401` 时，在连接器管理页重新连接。不要改工具入参，也不要自己拼登录地址。
4. **不要配置固定 Key**：本连接器走登录，不在 `mcp.json` 里写 `X-API-Key`。

## 鉴权说明

- **Connector 类型**：MCP Streamable HTTP。认证类型由服务端 401 发现，不在包内写 `client_id` / `client_secret`
- **MCP 地址**：`https://iautomark.sdm.qq.com/qc-manage-mcp/mcp`
- **发现文档**：`https://iautomark.sdm.qq.com/qc-manage-mcp/.well-known/oauth-protected-resource` 与 `/.well-known/oauth-authorization-server`
- 按 RFC 8414 路径插入的域名根别名是 `https://iautomark.sdm.qq.com/.well-known/oauth-*/qc-manage-mcp`，由网关转发到同一服务
- 服务端返回 `401` 时带 `WWW-Authenticate`，由 WorkBuddy 打开登录页

## 工具清单

工具名和参数以连上之后 `tools/list` 的说明为准，不要靠记忆编参数。

| 工具 | 用途 |
| --- | --- |
| `qc_catalog_get` | 看当前数据源、规则、SOP 和质检任务 |
| `qc_rule_draft` / `qc_rule_commit` | 起草规则；写入前先预览，确认后再落库 |
| `qc_sop_draft` / `qc_sop_commit` | 起草 SOP；同样先预览再写入 |
| `qc_operator_commit` | 读或写算子 |
| `qc_datasource_commit` | 读或写数据源 |
| `qc_outbound_import` | 把会话 JSON 导入当前任务做正式质检 |
| `qc_media_ingest` | 接入录音 |
| `qc_media_transcript` | 按材料取转写 |
| `qc_job_get` | 查录音或作业状态 |
| `qc_result_query` / `qc_result_search` / `qc_result_detail` | 查分数、命中和明细 |
| `qc_hfq_query` | 查客户高频问 |
| `qc_report_get` / `qc_report_save` | 读取或保存报告 |
| `qc_review_commit` | 复核写入 |

当前规则和 SOP 看任务详情里的 `groupRuleList`、`groupSopList`。正式质检走导入或录音接入，不调用 `qc_trial_run`。

## 关键约束

1. 租户只来自请求头，工具入参不要传 `tenantId`
2. 写规则、SOP、算子、数据源时，默认只预览；用户确认后才把确认标记打开
3. 分数、命中、高频问只引用工具返回，不编造
4. 该渠道有多条质检任务时，先问改哪一条，不猜

## 错误与边界

| 场景 | 处理 |
| --- | --- |
| `401` | 重新连接。不要改工具参数 |
| 缺 `X-Tenant-Id` | 连接配置问题，停止并说明，不要把租户写进工具 |
| 上游失败 | 把返回原文告诉用户 |
| 空结果 | 先核对材料编号、任务和时间范围，不编数据 |
