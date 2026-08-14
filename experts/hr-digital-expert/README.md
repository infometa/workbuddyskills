# HR Digital Expert

覆盖HR数仓查询、页面设计开发、一键部署上线和知识库管理的**全链路HR数智专家**。

## 类型

单专家模式（Agent 型），通过意图路由自动加载对应 Skill 执行。

## 核心能力

| 能力域 | Skill | 说明 |
|--------|-------|------|
| 🔍 数据查询与分析 | `hr-data-sql-builder` | HR数仓 StarRocks SQL 生成与查询 |
| 🔐 权限排查 | `data-table-permission-checker` | 数据权限查询与脱敏排查 |
| 💻 前端API生成 | `data-warehouse-api-codegen` | 生成前端调用数仓接口的代码 |
| 🧩 组件开发 | `hr-vue-next` | Vue3+TDesign+HR-Vue-Next 组件库 |
| 🤖 LLM代理 | `hr-common-llm` | 前端页面调用混元大模型 |
| ✉️ 消息推送 | `hrclaw-message` | 邮件/企业微信Tips发送 |
| 🚀 应用部署 | `page-deliver` | AnyDev部署+Gateway注册一键上线 |

## MCP 服务依赖

| 服务 | 用途 |
|------|------|
| `hr_data_service_v1` | HR数仓查询（StarRocks SQL） |
| `hr-ai-knowledge` | HR知识语义检索（团队空间/HiHR/企微文档） |

## 使用示例

- "帮我查询我有HR数仓哪些权限"
- "帮我生成一个人员信息管理系统并部署到HRClaw"
- "帮我查一下公司的员工休假制度"

## 安装

将专家包目录放到 WorkBuddy 的专家目录下：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/<expert-name>/
```

重启 WorkBuddy 后在「专家」面板中即可看到。

## 打包分享

```bash
zip -r hr-digital-expert.zip hr-digital-expert/
```
