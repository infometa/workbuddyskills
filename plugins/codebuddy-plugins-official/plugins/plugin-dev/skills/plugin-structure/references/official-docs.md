# CodeBuddy Code 官方文档参考

本文档提供 CodeBuddy Code 插件开发相关的官方文档链接，作为插件开发的权威参考。

## 官方文档列表

### 1. 插件系统概述 (plugins.md)

**链接**: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/plugins.md

**内容概要**:
- 什么是 CodeBuddy Code 插件
- 插件的核心组件（Commands、Agents、Skills、Hooks、MCP Servers）
- 快速开始指南
- 插件安装和管理
- 团队配置和共享

**适用场景**: 初次了解插件系统、快速入门

---

### 2. 插件市场指南 (plugin-marketplaces.md)

**链接**: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/plugin-marketplaces.md

**内容概要**:
- 市场类型（Official、Community、Private）
- 如何添加插件市场
- 从市场安装插件
- 发布插件到市场
- marketplace.json 规范

**适用场景**: 发布插件到市场、管理私有市场

---

### 3. 插件参考手册 (plugins-reference.md)

**链接**: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/plugins-reference.md

**内容概要**:
- Commands 详细规范（YAML frontmatter、参数、工具限制）
- Agents 详细规范（description 格式、触发条件、工具配置）
- Skills 详细规范（SKILL.md 格式、资源组织）
- Hooks 详细规范（事件类型、配置格式、输出格式）
- MCP Servers 配置
- plugin.json 完整字段说明

**适用场景**: 开发具体组件时的 API 参考

---

## 与本插件文档的关系

| 本插件文档 | 对应官方文档 | 说明 |
|-----------|-------------|------|
| `SKILL.md` | plugins.md | 本插件提供实践指导，官方文档提供概念基础 |
| `manifest-reference.md` | plugins-reference.md | 本插件更详细，官方文档更权威 |
| `component-patterns.md` | plugins-reference.md | 本插件侧重模式，官方文档侧重规范 |

## 建议阅读顺序

1. **入门**: 先读官方 `plugins.md` 了解整体概念
2. **开发**: 使用本插件的 `SKILL.md` 和 `references/` 进行实际开发
3. **发布**: 参考官方 `plugin-marketplaces.md` 发布插件
4. **深入**: 遇到具体问题时查阅官方 `plugins-reference.md`

## 注意事项

- 官方文档会持续更新，本链接指向最新版本
- 如发现本插件文档与官方文档不一致，以官方文档为准
- 欢迎反馈文档差异，帮助改进本插件
