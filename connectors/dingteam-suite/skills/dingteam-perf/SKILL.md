---
name: dingteam-perf
description: Teach the AI how to use the DingTalk Performance connector for org queries, assessment plan creation, review progress tracking and process efficiency stats.
description_zh: 教 AI 使用钉钉绩效连接器查询组织架构与人员、创建绩效考核方案、跟踪考核进度与流程效率。
description_en: Teach the AI how to use the DingTalk Performance connector for org queries, assessment plan creation, review progress tracking and process efficiency stats.
version: 1.0.0
author: dingteam
---

# 钉钉绩效连接器使用说明

## 何时使用

用户提出以下请求时，优先调用本连接器的工具，不要凭经验猜测组织或考核数据：

- 查询组织架构、部门层级、部门下的成员名单
- 查询某个人的所属部门、汇报关系、岗位信息
- 创建 / 查看绩效考核方案、部门考核方案、评估计划
- 查询考核模板分类、可用模板、创建规则与创建状态
- 查询考核流程完成率、流程节点耗时、流程效率统计
- 评审组创建、评审链接获取
- 智能绩效内的 OKR 空间：周期、目标、任务、对齐关系查询
- 人力数据分析（HR analytics）相关查询

## 使用步骤

1. **先定位实体**：拿到姓名或部门名后，先调用组织查询工具解析出 ID（用户 → 部门 → 层级），再带上 ID 调用业务工具。不要用名称直接调用业务接口。
2. **确认周期**：涉及考核时必须先确认考核周期（如 2026 Q3）。用户没说时先调用考核周期列表工具，列出可选周期让用户确认。
3. **创建类操作二次确认**：创建考核方案、创建部门方案属写操作。调用前先向用户复述「考核周期 + 考核对象 + 模板」三要素并请其确认。
4. **统计类结果**：先给汇总数字（完成率、未提交人数），再按需展开明细，用 Markdown 表格呈现。
5. **图片类结果**：对齐图/关系图类工具返回图片，直接在回答中展示并附一句说明。

## 注意事项

- 首次使用需完成钉钉 OAuth 授权。工具返回 401 / 未授权时，引导用户到连接器授权入口重新登录，不要反复重试。
- 权限范围受钉钉侧应用可见范围限制，查不到数据时提示用户检查应用可见范围与管理员权限，不要臆造数据。
- 涉及他人绩效、薪酬等敏感信息时，仅返回用户权限范围内的结果。
