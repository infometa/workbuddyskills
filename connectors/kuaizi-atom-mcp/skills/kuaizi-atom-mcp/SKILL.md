---
name: "kuaizi-atom-mcp"
display_name: "Kuaizi-Atom · 视频商业工具栈（MCP 连接器）"
display_name_en: "Kuaizi-Atom Video Commerce Toolstack (MCP Connector)"
description: "Call Kuaizi video commerce toolstack tools via the kmcp MCP gateway - products, IP, assets, cleaning, recall, covers, compose, publish, pullback, model gateway, wallet."
description_zh: "通过 kmcp MCP 网关调用视频商业工具栈（Kuaizi-Atom）：产品库、客户IP、素材、清洗、召回、封面、合成、发布、回捞、模型网关、钱包等 32 个能力 120 工具。"
description_en: "Invoke Kuaizi video commerce toolstack tools (32 capabilities / 120 tools) through the kmcp MCP gateway."
category: "productivity"
version: "1.0.1"
author: "筷子科技 FDE 团队"
---

# Kuaizi-Atom · 视频商业工具栈（MCP 连接器）

连接器安装后，本连接器的 MCP Server（kuaizi-atom）会把 120 个原子工具暴露给你。调用前先读
@./references/tool-index.md（32 能力 × 全量工具索引，含每个工具的参数说明）选工具。

## 鉴权方式（2026-11 起 OAuth 2.1）

- **WorkBuddy 内（本连接器）**：首次连接时自动跳转筷子授权页（atom.kuaizi.cn /#/authorize）——
  登录/留资 → 同意授权 → 自动返回，全程**无需手填 API Key**。token 过期由 WorkBuddy 自动续期。
- **其它 MCP 客户端（Cursor / Claude Code 等）**：仍可用 `Kz-Api-Key: <pk_ 开头 Key>` 头直连
  （Key 去筷子官网 atom.kuaizi.cn 留资注册获取）；网关同时兼容两种鉴权。

## 口径速记

1. 请求即 MCP `tools/call`，鉴权由连接器自动携带（OAuth Bearer / Kz-Api-Key）。
   payload 放 `arguments.payload`；可选 `arguments.ctx` 传 `{"app_id":"workbuddy"}`（计费归因，可省略）。
2. 返回 `{state, data, issues, meta}`：`succeeded` 取 data；`needs_input` 按 issues[].path/hint 补参重发（**不是报错**）；`failed` 看 issues。
   两种不该重试的情况：纯文本 `HELPER_UNAVAILABLE`（上游故障、不计费、原样稍后重发）、`INSUFFICIENT_BALANCE`（余额/限额不足，须充值或调额度）。
3. 异步工具返回 job_id/task_id → 调对应任务查询至终态（轮询对见下）。
4. 被拦截提示 kmcp_fee_confirm → 调 `kmcp_fee_confirm`（payload `{"agree":true}`）同意《计费协议》后重发原调用；免费工具不扣费，收费工具按规则扣点。
5. 模板写操作走个人模板库 `ref_personal_prompt_template_*`（归属跟账号走，无需场景头；全局模板 `ref_prompt_template_*` 只读）。
6. `publish_boost`（播放/点赞等增量）涉及目标平台反刷量规则，用户未明确要求并知悉风险时不要主动调用。

## 高频示例（可直接发送）

```json
{"name":"platform_balance_get","arguments":{"payload":{}}}
```

```json
{"name":"context_spu_ingest","arguments":{"payload":{
  "async": true,
  "sources":[{"kind":"text","text":"<商品资料文本>"}]}}}
```

```json
{"name":"token_generate_text","arguments":{"payload":{"model":"<先 token_models_list 取 model_id>","prompt":"用一句话介绍挂耳咖啡的卖点"}}}
```

```json
{"name":"composition_compose","arguments":{"payload":{
  "videos":[{"video_url":"https://<公网成片>.mp4","cover_url":"https://<封面>.png","duration":17.2}],
  "layout_id":"<从 effect_list kind=layout 拿>"}}}
```

## 轮询对

ingest/ip → context_job_get；nx_parse → nx_parse_job_get；token_* → token_job_get；
vproc_* → vproc_job_get；compose/tts → composition_job_get；cover_* → cover_job_get；
ref_matrix 生成类 → ref_matrix_job_get；qc_prepare* → qc_job_get；
publish_run → publish_run_status；publish_owned_run → publish_owned_run_status。
