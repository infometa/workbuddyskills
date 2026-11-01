# 服务端已知行为（实测记录）

> 标注"实测版本 + 待服务端修复项"。这些不是 bug，是当前服务端的设计行为。

## 2026-09-11 实测（mgvtraining test 环境）

| # | 行为 | 影响 | 状态 |
|---|---|---|---|
| 1 | GATE 文案 `"正在生成计划卡片，请稍等。"` | 中间生成状态，非 GATE 方案请求；agent 不应误判为需要用户确认 | 已知 |
| 2 | pro 非流式返回的 `data.content` 可能是 LangChain messages 转储 | MCP 层 `parseExaminerV2MegaviewContent` 已做解析+raw 降级 | 服务端优化项 |
| 3 | `CreateLearnerSingleCourse` 的 `CompleteTime` 必须非零 | MySQL 严格模式拒绝零时间；已设 `time.Now()` | 已修复 |
| 4 | `mgvproto 20260907` 版本删掉了 `PublishCourseRequest` 类型 | 与 main 的 gRPC publish 代码不兼容；已回退到 0904 | 部署依赖 |
| 5 | pro 刷新后 refresh_token 可能失效 | 需重新 OAuth 授权 | 已知 |
| 6 | 完成文案以「随时告诉我」结尾 | 旧版 gate-detection 关键词表会误报 GATE；已加「完成标志优先」短路规则（2026-09-14） | 已修复（skill 侧） |

## 待服务端修复/优化项

- GATE 停点轮的 response 是 LangChain messages 转储（非人类可读）——建议 pro 侧改为返回结构化确认状态
- mgvauth 原子功能点 `/webapi/training/course/manage` 待添加（当前用数据权限 scope 降级兜底）
- `mgvproto 0907` 版本缺 `PublishCourseRequest`——需 mgvproto 团队确认

## 2026-09-15 变更与规则

| # | 行为 | 影响 | 状态 |
|---|---|---|---|
| 7 | 学员系列课延迟到 chat done 后自动创建（内容达标才建，GATE 轮不建） | create 不再返回 seriesCourseId/learnUrl；done 的 update_status 响应携带 | 服务端已实现（skill 文档已同步） |
| 8 | create 后 agent 易提前宣告「课程创建成功」 | 用户误以为题目已生成；tool description 与 SKILL.md 硬性规则已加禁令：验题通过前只报中间态 | 已修复（skill 侧） |
| 9 | 学员路径 done 的 `learnUrl` 为相对路径（`/#/pages-sub/series-course-detail/index?id=129`，缺 H5 域名前缀） | 直接把 learnUrl 发给用户点击会打不开；根因是 H5 域名（Consul `url.h5_coach`）未配置，域名前缀为空。agent 交付前需拼上当前环境 H5 域名 | 待服务端配置（2026-09-15 实测） |
