# 金数据表格专家（WorkBuddy Agent 型）

金数据（jinshuju.net）**数据表格**管理专家，通过金数据 MCP 用自然语言完成数据表搭建、列增删改、行数据增删改查与批量维护、账户查询，替代登录后台手动操作。

数据表格是金数据里以「列 + 行」组织的结构化数据表（类似多维表格 / 在线数据库），与用于对外收集的「在线表单」是不同产品。表单产品见同仓库的 `jinshuju-expert`。

## 目录结构

```
jinshuju-table-expert/
├── .codebuddy-plugin/plugin.json   # 专家配置与市场展示信息
├── avatars/
│   ├── expert.png                  # 专家头像（512×512）
│   └── jinshuju.svg                # 内置 MCP 引导卡片图标
├── agents/jinshuju-table-expert.md # Agent 定义（系统提示词）
├── skills/jinshuju-table/          # 内置金数据表格技能（工具参考与示例）
├── .mcp.json                       # 内置金数据 MCP 依赖声明（OAuth）
└── README.md
```

## 依赖

召唤本专家前，WorkBuddy 会引导用户连接**金数据 MCP**（`https://jinshuju.net/mcp`，OAuth 授权）。表单与表格共用同一 MCP 端点；**表格结构工具需账户开通「新版表格」**。授权范围决定可用工具集：`forms`（表结构）/ `read_entries` / `write_entries`（行数据）/ `user` / `billing_account`。

## 打包提交

```bash
cd workbuddy/expert
zip -r jinshuju-table-expert.zip jinshuju-table-expert/
```

> 提交前请确认 `plugin.json` 中的 `author.email` 为对外可用的官方邮箱。
> 专家头像 `avatars/expert.png` 为表格专属视觉；MCP 引导卡片图标 `avatars/jinshuju.svg` 复用金数据品牌图。
