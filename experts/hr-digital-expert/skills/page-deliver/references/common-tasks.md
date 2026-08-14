# 常见 Task 示例

> 编写 Plan 时的 Task 参考清单。非穷举，根据实际需求裁剪。

| Task | 做什么 | 验证方式 | 触发场景 |
|------|--------|----------|----------|
| 初始化项目 | 复制模板 + 替换占位符 + `echo '{"projectId":"<project_id>","projectDir":"<project_dir_abs>","projectName":"<project_name>"}' \| node "$PD" state init --input -` | 文件存在且内容正确，state 文件为标准 schemaVersion=2 | 每次执行开始时（`state init` 幂等：新建则创建，旧/异形结构则归一化） |
| 填充页面内容 | 写入业务 HTML/CSS/JS | 无 lint 错误 | 始终需要（核心交付物） |
| 填充数仓 SQL | 写入 queryDW 调用代码 + 配置查询参数 | MCP starrocks_query 验证 SQL 可执行 | `needs_dw=true` 时 |
| 填充 API 路由 | 写入 server.js 路由代码 + DB 连接/CRUD 逻辑 | curl 返回预期响应 | `needs_db=true` 时 |
| 迭代预览 | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" anydev full-deploy --input -` → 输出预览确认模板 → `ask_followup_question` 弹确认按钮 | full-deploy status: success 且 health-check 通过 | 始终需要（详见 writing-plans.md → 迭代循环） |
| 注册发布 | `echo '{"projectDir":"<project_dir_abs>"}' \| node "$PD" anydev publish --input -` → 输出部署输出模板 | status: success | 用户点击"确认发布"后 |

> 所有 `<project_dir_abs>` 都必须替换为项目目录绝对路径。`anydev full-deploy` / `anydev publish` 只接受 `projectDir`，不要添加 `skillDir`、`envInsId`、`ip`、`port` 等字段。
