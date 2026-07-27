# 金数据表单专家（WorkBuddy Agent 型）

金数据（jinshuju.net）**表单**搭建与数据管理专家，通过金数据 MCP 用自然语言完成表单搭建、数据增删改查与批量维护、账户查询，替代登录后台手动操作。

数据表格（以「列 + 行」组织的结构化数据表）是另一个产品，见同仓库的 `jinshuju-table-expert`。

## 目录结构

```
jinshuju-form-expert/
├── .codebuddy-plugin/plugin.json   # 专家配置与市场展示信息
├── avatars/
│   ├── expert.png                  # 专家头像（512×512）
│   └── jinshuju.svg                # 内置 MCP 引导卡片图标
├── agents/jinshuju-form-expert.md  # Agent 定义（系统提示词）
├── skills/jinshuju-form/           # 内置金数据表单技能（工具参考与示例）
├── .mcp.json                       # 内置金数据 MCP 依赖声明（OAuth）
└── README.md
```

## 依赖

召唤本专家前，WorkBuddy 会引导用户连接**金数据 MCP**（`https://jinshuju.net/mcp`，OAuth 授权）。授权范围决定可用工具集：`forms` / `form_setting` / `read_entries` / `write_entries` / `user` / `billing_account`。

## 打包提交

```bash
cd workbuddy/expert
zip -r jinshuju-form-expert.zip jinshuju-form-expert/
```

> 提交前请确认 `plugin.json` 中的 `author.email` 为对外可用的官方邮箱。
