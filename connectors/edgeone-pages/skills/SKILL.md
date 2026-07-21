---
name: edgeone-makers
description_zh: "将项目部署到 EdgeOne Makers 并返回线上访问地址，支持全栈、云函数、AI Agent 等开发场景。"
description_en: "Deploy the project to EdgeOne Makers and return the live access URL. Supports full-stack development, cloud functions, AI Agent, and other development scenarios."
version: "1.0.0"
---

# EdgeOne Pages Skill

该 Skill 需要调用 `edgeone-makers-mcp-server` MCP Server。

## 概述

将项目部署到 EdgeOne Makers 并返回线上访问地址，支持全栈、云函数、AI Agent 等开发场景。

## 核心能力

- **全栈项目部署**：将全栈项目（React、Vue、Next.js、Nuxt、Vite 等）快速部署到 EdgeOne Makers
- **预览链接生成**：部署完成后自动生成预览链接，即时查看效果
- **框架自动识别**：自动检测项目框架类型并使用最佳构建配置
- **边缘加速**：利用 EdgeOne 全球边缘节点提供高性能访问
- **部署管理**：查看部署历史、回滚到指定版本、管理部署环境

## 使用原则

1. 部署前确认项目类型和构建配置
2. 优先使用框架自动识别功能，减少手动配置
3. 部署后通过生成的预览链接确认效果

## 典型工作流

1. **快速部署**：选择项目 → 自动识别框架 → 部署 → 获取预览链接
2. **更新部署**：修改代码 → 触发重新部署 → 通过预览链接确认
3. **版本回滚**：查看部署历史 → 选择目标版本 → 回滚部署