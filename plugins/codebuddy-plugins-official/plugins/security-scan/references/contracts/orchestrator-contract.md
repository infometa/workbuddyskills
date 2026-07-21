# 编排器核心原则

> 引用方：commands/project.md、commands/diff.md

---

## 薄编排层定位

编排器为薄编排层——启动 Agent、等待返回、合并结果。不直接执行安全分析。

**上下文隔离**：编排器不得将任何 agent 的完整输出读入上下文。跨阶段数据通过脚本 stdout 摘要传递：
- `index_db.py query --preset summary` → 项目概况摘要
- Agent Task 返回 → findings 数量摘要
- `merge_findings.py stdout` → totalFindings、bySeverity

**禁止操作**：
- 禁止为安全分析而 Read 项目源文件
- 禁止为合并而 Read `agents/*.json`
- 禁止在 Agent 提示词中嵌入完整源代码
- 禁止 Agent 缺少落盘产物时手工接管扫描

**并行调度规则**（Deep 模式）：vuln-scan + logic-scan + red-team 三个 Agent 并行启动，verifier 在合并后顺序执行。

**子 Agent 权限模式**：所有 Task 启动必须设置 `mode: bypassPermissions`。原因：子 Agent 不继承编排器的白名单配置，`default` 模式下每次 Bash/Write 调用都会弹出授权确认，严重阻断自动化流程。`bypassPermissions` 跳过所有审批，安全性由以下机制保障：
- 子 Agent 的 `tools` 已在 agent 定义中受限（无 Edit/MultiEdit 外的危险工具）
- agent-rules.md 明确禁止列表（禁止 `rm`/`pip install`/网络请求等）
- permissions.deny 护栏仍生效（`rm -rf /`、`git push --force` 等被强制拦截）

---

## Agent 提示词模板

```
你是 {agent_name}，负责 {one-line task description}。

[插件根目录] CODEBUDDY_PLUGIN_ROOT={resolvedPluginRoot}
所有 Bash 调用插件脚本前必须先 export：export CODEBUDDY_PLUGIN_ROOT="{resolvedPluginRoot}"
[反幻觉契约] (1) filePath 必须通过 Read/Glob 验证 (2) riskCode 必须来自 Read 输出 (3) 确认漏洞前必须搜索防御措施 (4) 宁可漏报也不误报 (5) 安全分析必须使用工具层 Grep/Read/Glob/LSP，禁止通过 Bash grep/find/cat 执行安全分析。
[LSP 状态] {lspStatus}
[项目上下文] Read: .codebuddy/security-scan/runs/{batch}/stage1-context.json
[语义索引] .codebuddy/security-scan/runs/{batch}/project-index.db（通过 index_db.py query 按需查询）
[输出文件] agents/{agent-name}.json
[输出 Schema] 参见 {resolvedPluginRoot}/references/contracts/output-schemas.md > {agent-name}
```

提示词规则：
- **所有面向用户的输出必须使用简体中文**（JSON 字段名和技术标识符保持英文）
- `{resolvedPluginRoot}` 是编排器在 init-步骤0 解析出的插件根目录**绝对路径**，必须替换为实际值（如 `/Users/xxx/marketplace-yd-test/plugins/security-scan`），**禁止**传递 `${CODEBUDDY_PLUGIN_ROOT}` 变量名
- 提示词中的任务特定指令不得超过 2000 个字符
- 超出内容放入中间文件供 agent Read
- 使用文件路径引用，切勿将大量内容内联到提示词中
- Agent 完成后自然退出，输出数据写入 `[输出文件]` 指定的 JSON 文件即可

---

## max_turns 参考值

| Agent | max_turns |
|-------|-----------|
| indexer（deep） | 30 |
| indexer（light） | 20 |
| vuln-scan | 25 |
| logic-scan | 25 |
| red-team | 25 |
| verifier-vuln | 20 |
| verifier-logic | 20 |
| verifier-redteam | 20 |
