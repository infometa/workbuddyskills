# Reference 索引

> 本文件为乐享知识库 MCP Skill 的参考文档索引。AI 根据意图路由表定位后，按需 Read 对应文件。

---

## 按功能域

| 你需要... | 读取文件 | 核心内容 |
|----------|---------|----------|
| 数据模型/URL 规则/安全规则/Block 结构/工具发现 | base.md | 完整基础知识 |
| 配置/认证/Token 管理/OAuth/故障排查 | setup.md | WorkBuddy OAuth、手动配置、续期流程 |
| 搜索文档/阅读内容/语义检索 | search.md | 实体召回、RAG 切片、目录浏览 |
| 创建文档/写入内容/导入/公众号收藏 | writer.md | import_content、create_entry、hyperlink |
| 编辑已有页面/Block 增删改移 | blocks.md | Block 操作、批量更新、Markdown 转 Block |
| 上传/下载文件（PDF/Word/图片等） | files.md | 三步上传流程、MIME 类型、更新文件 |
| 导入外部数据/腾讯会议 | connectors.md | 会议录制搜索/导入 |

---

## 按场景推荐加载顺序

| 场景 | 推荐读取顺序 |
|------|-------------|
| 首次使用 | setup.md → base.md |
| 搜索后写入 | search.md → writer.md |
| 读取后编辑 | search.md → blocks.md |
| 上传文件 | files.md |
| 会议导入 | connectors.md → writer.md |
| 排查错误 | common-errors.md |

---

## 补充参考文档

| 文档 | 说明 |
|------|------|
| block-schema.md | Block 类型完整字段定义 |
| mcp-examples.md | 复杂 Block 结构示例 |
| markdown-to-block.md | Markdown 转 Block 指南 |
| block-update.md | 批量更新 Block 方法 |
| content-reorganize.md | 文档结构重组方案 |
| folder-sync.md | 文件夹同步方案 |
| markdown-import.md | Markdown 导入详解 |
| common-errors.md | 常见错误排查（高频错误速查表） |
| doc-templates.md | 文档类型与大纲模板 |
| theme-config.md | 主题配色配置 |
| skill-maintenance.md | Skill 维护指南 |
