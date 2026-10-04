# 常见 Task 示例

> 编写 Plan 时的 Task 参考清单。非穷举，根据实际需求裁剪。

| Task | 做什么 | 验证方式 | 触发场景 |
|------|--------|----------|----------|
| 初始化项目 | 复制模板 + 替换占位符 + `echo '{"projectId":"<project_id>","projectDir":"<project_dir_abs>","projectName":"<project_name>"}' \| node "$PD" state init --input -` | 文件存在且内容正确，state 文件为标准 schemaVersion=2 | 每次执行开始时（`state init` 幂等：新建则创建，旧/异形结构则归一化） |
| 填充页面内容 | 写入业务 HTML/CSS/JS | 无 lint 错误 | 始终需要（核心交付物） |
| 填充数仓 SQL | 写入 queryDW 调用代码 + 配置查询参数 | MCP starrocks_query 验证 SQL 可执行 | `needs_dw=true` 时 |
| 填充 API 路由 | 写入普通业务 API 路由（不得使用 `/app-mcp/` 保留前缀）；如涉及持久化再接入 DB 连接/CRUD 逻辑 | curl 返回预期响应 | `needs_db=true` 或普通业务功能需要新增/修正业务 API 时 |
| 委托 enable-mcp | 通过宿主 skill 调用机制委托 `enable-mcp` 完成能力确认、路由与 `public/restful.json` 生成 | `enable-mcp` 自查通过，路由与描述一致 | MCP 意图路由命中时 |
| 迭代预览 | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" anydev full-deploy --input -` → 输出预览确认模板 → `ask_followup_question` 弹确认按钮 | full-deploy status: success 且 health-check 通过 | 始终需要（详见 writing-plans.md → 迭代循环） |
| Dockerfile 检查/生成 | 校验/生成 Dockerfile 与 `.dockerignore`，并把 `projectType` 写入 state | 文件存在且 `state update` 成功 | 用户点击"确认注册"后 |
| 注册发布 | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" anydev publish --input -` → 输出部署输出模板 | status: success | 用户点击"确认注册"且 Dockerfile task 完成后 |

> 所有 `<project_dir_abs>` 都必须替换为项目目录绝对路径。`anydev full-deploy` / `anydev publish` 只接受 `projectDir`，不要添加 `skillDir`、`envInsId`、`ip`、`port` 等字段。
