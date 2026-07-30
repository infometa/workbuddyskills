# 磐石CRM跟进拜访助手（Panshi CRM Visit Assistant）

面向 CSIG 磐石场景的跟进拜访助手，覆盖跟进记录查询、拜访打卡记录查询，以及跟进记录搬运录入（写入磐石 CRM）。对应磐石 PC/小程序端"跟进拜访管理"入口。

## 类型

Agent 型（单专家）

## 核心能力

- crm-query-visit：跟进记录查询（文字性沟通内容、线下拜访明细）
- crm-query-check-in：拜访打卡记录查询（含位置与关联跟进状态）
- crm-visit-sync：跟进记录搬运录入——把 iWiki／腾讯文档／企微文档链接、粘贴文本（结构化纪要/对话流/纯文本）、企微聊天合并转发、图片截图 中已写好的跟进记录写入磐石 CRM（仅销售/售前架构师、客户/商机、15 天内）

## 使用示例

- 帮我查一下我上周的跟进记录
- 列一下我还没关联跟进的拜访打卡
- 把这个 iWiki（腾讯文档／企微文档）链接里的跟进记录搬运录入到磐石 CRM
- 把这段聊天记录 / 这张拜访纪要截图整理成跟进记录并写入磐石

## 依赖

- **omp-service**（必需）：跟进查询、拜访打卡查询、跟进记录写入等全部磐石业务接口统一经此连接器，完成授权后即可调用（见 `.mcp.json`）。
- **文档类内置连接器**（按需）：`crm-visit-sync` 处理文档链接（分支 A）时，依赖 WorkBuddy 内置连接器读取源文档——iWiki（`iwiki-woa`）、腾讯文档（`tencent-docs`）、企业微信（`wecom`）。这些为平台内置连接器，在「连接器管理」中授权即可，无需在 `.mcp.json` 里填写 URL/Token（见 `.mcp.json` 的 `x-workbuddy-connectors` 说明）。

## 目录说明

- `agents/`：专家主配置与系统提示（意图识别主路由）
- `skills/`：各业务技能与执行流程
  - `crm-query-visit-skill/`：跟进记录查询
  - `crm-query-check-in-skill/`：拜访打卡记录查询
  - `crm-visit-sync/`：跟进记录搬运录入（含 `shared/` 与 `samples/`）
- `avatars/`：专家头像与连接器图标资源
- `.codebuddy-plugin/plugin.json`：插件元数据
- `.mcp.json`：MCP 服务配置与文档类连接器依赖声明

## 头像资源

`plugin.json` 的 `avatar` 字段指向 `avatars/panshi-customer-visit-agent.png`（专家头像），`.mcp.json` 的 omp-service 图标指向 `avatars/omp-service.png`（连接器图标）。两个文件均已放入 `avatars/` 目录。

## 维护建议

- 新增技能时，同步更新 `plugin.json` 的 `skills` 列表、`agents/*.md` 的路由判定与本文档
- `crm-visit-sync` 的字段映射（重构后新字段）变更时，同步更新 `skills/crm-visit-sync/shared/FIELDS_MAPPING.md`
- 头像替换建议保持 512×512 尺寸、PNG/JPG 格式
