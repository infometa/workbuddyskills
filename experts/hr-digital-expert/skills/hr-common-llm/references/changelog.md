# 更新日志 (Changelog)

本文件记录 `hr-common-llm` Skill 的所有版本变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.1.0] - 2026-05-25

### 变更

- **可用模型调整**：
  - 移除 `HY-2.0-instruct-20251111`（非思考模型）
  - 移除 `HY-2.0-thinking-20251109`（思考模型）
  - 新增 `HY-3-Preview`（非思考模型），作为统一可用模型
- 同步更新 `SKILL.md` 中可用模型说明、代码生成工作流的模型选择规则、注意事项与示例代码
- 同步更新 `references/code_templates.md` 中所有代码模板的默认模型与 TypeScript 类型定义
- 移除「简单工具函数」章节中基于思考模型的 `think()` 工具函数

## [1.0.0] - 2025-04-13

### 新增

- 初始版本发布
- 支持混元模型调用：
  - `HY-2.0-instruct-20251111`（非思考模型，已于 1.1.0 移除）
  - `HY-2.0-thinking-20251109`（思考模型，已于 1.1.0 移除）
- 完整的 OpenAI 标准接口规范支持
- 非流式和流式（SSE）两种响应模式
- 代码模板支持：
  - JavaScript fetch（非流式/流式）
  - JavaScript axios
  - TypeScript（含类型定义）
  - React Hook 封装（非流式/流式）
  - Vue 3 Composable 封装
  - 简单工具函数

### 技术说明

- API 地址：`https://ntsgw.woa.com/api/sso/llm-proxy-service/api/v1/chat/completions`
- 无需手动处理 Authorization，前端 HTTP 链路层已自动携带 SSO 身份信息
- 仅限浏览器端调用，后端环境不可用

---

## 版本更新指南

### 需要更新的场景

1. **API 地址变更**：修改 `SKILL.md` 和 `references/code_templates.md` 中的 API_URL
2. **新增可用模型**：更新「可用模型」表格和代码模板中的类型定义
3. **接口参数变更**：更新请求体结构说明和代码模板
4. **新增错误码**：更新错误响应说明

### 更新步骤

1. 修改 `SKILL.md` 中的 `version` 字段（遵循语义化版本）
2. 同步更新相关内容
3. 在本文件添加新版本的变更记录
4. 测试验证代码模板可用性

### 版本号规则

- **主版本号（MAJOR）**：不兼容的 API 变更
- **次版本号（MINOR）**：向后兼容的新功能
- **修订号（PATCH）**：向后兼容的问题修正

---

## 维护者

- HR 基础组件研发组
- 联系方式：jacknie@tencent.com
