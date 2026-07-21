# SaaS / B2B 工具 — 行业设计规范

## 行业特征
- 目标用户：企业决策者 + 一线使用者
- 核心诉求：提效、降本、可量化
- 决策链路长，需要 ROI 证明

## 设计风格
- **风格**：极简瑞士风 / 数据密集风
- **主色**：Slate Blue `#4F46E5` / Indigo `#6366F1`
- **对标品牌**：Linear、Notion、Stripe Dashboard、Vercel
- **字体**：Inter + Noto Sans SC，代码用 JetBrains Mono
- **氛围关键词**：专业、可靠、高效、克制

## 布局模式
- **左侧导航 + 右侧内容**：标准 SaaS 布局
- **顶部面包屑 + 操作栏**：层级导航
- **数据看板**：KPI 卡片 + 图表 + 趋势线
- **表格为主**：筛选栏 + 列表 + 分页
- **设置页**：Tab 切换 + 表单分组

## 核心页面清单
1. Dashboard（数据概览）
2. 列表页（CRUD + 筛选 + 搜索）
3. 详情页（信息分组 + 操作按钮）
4. 设置页（组织/权限/计费）
5. 空状态引导页
6. Onboarding 流程

## 交互规范
- 所有操作提供 undo 机制
- 删除操作二次确认
- 批量操作需选中态 + 批量操作栏
- 表格支持列排序、列筛选、列自定义
- 快捷键支持（Cmd+K 搜索等）

## 技术架构建议
- **前端**：Next.js 14+ / React 18+ / Vue 3
- **状态管理**：TanStack Query + Zustand / Pinia
- **UI 框架**：Tailwind CSS + Radix UI / Headless UI
- **后端**：FastAPI / Express + PostgreSQL
- **认证**：JWT + RBAC
- **部署**：Vercel / CloudBase + 云数据库

## 行业数据参考
- 用户留存率：30日 40-60%
- 付费转化率：5-15%（Freemium 模式）
- 平均客单价：$29-299/月
- NPS 基准线：30+
