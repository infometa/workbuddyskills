---
description: "一键部署 Godot MCP（Node.js + Server 构建 + Godot 编辑器 + 9080 探测）"
argument-hint: "[skip-install]"
---

# /godot:deploy

显式触发 [godot-deploy](../skills/godot-deploy/SKILL.md) Skill 的 5 步部署流程。

> 4.23.md 的分工：**部署/构建/下载等所有「非编辑器单元操作」由 Skill 自己跑
> shell 完成**，MCP 不再持有任何部署相关工具。本 command 只是把 Skill 显式
> 拉起来；用户也可以直接用自然语言（如「帮我部署 godot mcp」）触发同一个
> Skill。

## 参数

- `skip-install`（可选）：步骤 2 跳过 `npm install`，仅跑 `npm run build`

## 行为

1. 读取本 command 的参数，转成 Skill 可见的提示
2. 全权委托给 `godot-deploy` Skill，按其 5 步流程执行：
   1. 检查 Node.js >= 18
   2. 检查 / 构建 `server/dist/index.js`
   3. 确认 `.mcp.json` 注册
   4. 确认 / 下载本地 Godot 编辑器
   5. TCP 探测 9080 + 引导用户启用插件
3. 把 Skill 的部署报告原样回显

## 失败处理

由 Skill 内置的失败对照表负责，本 command 不重复。
