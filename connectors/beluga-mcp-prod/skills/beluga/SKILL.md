---
name: beluga
description: 连接 Beluga 生产环境 MCP 网关（https://beluga-server-cn.heytapmobi.com/beluga-mcp/gateway）并通过自然语言调用其工具。当用户需要排查 Beluga 网关/上游存活（ping_upstream），或查询本人「全时记」录音摘要（recall_memory）与「随口记」短笔记（recall_note）时使用本 Skill；也包含 OAuth 接入方式与调用约定。
---

# Beluga MCP（生产）使用说明

本连接器通过 OAuth 2.1 授权连接 Beluga **生产环境** MCP 网关
（https://beluga-server-cn.heytapmobi.com/beluga-mcp/gateway）。
网关暴露的具体工具以实际连接后返回的工具列表为准。

## 接入方式

### 方式一（推荐）：WorkBuddy 原生授权 / 平台托管

本连接器已声明 `auth_mode: "server-side"`，凭据由 WorkBuddy 平台托管。
用户在「插件 → MCP 服务器」点击「信任/连接」即可自动拉起授权页完成登录，
令牌由平台自动携带与静默刷新，**桌面端与手机端行为一致**，无需手动配置。

> 使用新字段需 WorkBuddy ≥ 4.22.12（见 `connector-meta.json` 的
> `minWorkbuddyVersion`）。

### 方式二（仅调试备用）：一键接入脚本 connect.py

> 该方式把 Bearer Token 写入**本机** `~/.workbuddy/mcp.json`，仅在本地桌面端
> 有效、手机端无法复现，现已降级为调试/排障备用，不再作为常规接入方式。

在连接器包目录下运行（仅需 Python 3.9+，无第三方依赖）：

```bash
python connect.py            # 完整接入：自动拉起浏览器 → 登录授权 → 自动写入配置
python connect.py --check    # 验证现有令牌并列出可用工具
python connect.py --refresh  # access_token 过期后用 refresh_token 静默续期
```

脚本流程：发现 OAuth 元数据 → 动态注册客户端（http://localhost 回调）→
本地监听回调并自动打开浏览器 → 用户登录授权 → PKCE 换取令牌 →
把 `Authorization: Bearer` 写入 `~/.workbuddy/mcp.json` 的
`beluga-mcp-prod` 条目 → 自动验证并列出工具。

完成后回到 WorkBuddy「插件 → MCP 服务器」对 beluga-mcp-prod 点击
「信任/重连」即可。access_token 默认有效期 30 天，过期后运行
`--refresh` 续期即可，无需重新登录。

## 调用约定

- 调用工具前先向用户确认意图与必要参数，不要凭空编造参数值。
- 工具返回错误（网络错误 / 401 / 超时）时：如实告知用户，建议稍后重试或重新连接，
  不要伪造成功结果。401 时先尝试 `python connect.py --refresh`。
- 涉及创建、修改、删除类工具时，先向用户复述操作内容并取得确认后再执行。

## 工具清单（2026-09-08 实测）

网关当前暴露 3 个工具（以 `python connect.py --check` 实时结果为准）：

### ping_upstream
- 用途：探测上游 beluga-server Skill 存活（GET /beluga/skill/v1/ping）。
- 参数：无。
- 典型用途：接入排障、健康检查。

### recall_memory
- 用途：召回用户「全时记」——长时间被动录音生成的 Session 摘要
  （含会议/闲聊/日常等）。
- 典型调用：用户问"我上周开会说了什么/之前聊过什么"时，按时间范围或
  关键词检索召回。
- 注意：涉及个人录音数据，仅响应用户本人的查询请求，不要主动外发内容。

### recall_note
- 用途：召回用户「随口记」——主动触发的短笔记（灵感、口头指令、问答类
  短内容）。
- 典型调用：用户问"我之前记过什么/我说过要做什么"时检索。
- 注意：与 recall_memory 的区别在于数据来源（主动短记 vs 被动长录音），
  按用户语义选择，不确定时优先 recall_note，无结果再查 recall_memory。
