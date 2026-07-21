---
name: canva
description: "Use Canva's design capabilities: create and edit designs, manage assets and brand resources, search the asset library, export designs, and add comments."
description_zh: "让AI助手无缝调用Canva可画的设计能力，包括创建设计、编辑设计、管理素材和品牌资源、搜索资源库、导出设计以及添加评论等。"
description_en: "Access Canva's design capabilities: design creation and editing, asset and brand management, search, export, commenting, and more."
version: "1.0.0"
---

# Canva可画 Skill

通过 MCP 协议连接 Canva可画，让 AI 能够无缝调用设计能力，包括创建设计、编辑设计、管理素材和品牌资源、搜索资源库、导出设计以及添加评论等。

## 功能能力

- **创建设计**：使用自然语言描述，AI 自动在 Canva可画中创建设计稿
- **编辑设计**：对已有设计进行修改和调整
- **素材与品牌管理**：管理素材库和品牌资源
- **资源搜索**：搜索 Canva可画资源库中的模板和素材
- **导出设计**：将设计导出为图片或其他格式
- **评论管理**：为设计添加评论和反馈

## 调用原则

1. 确保 Canva可画 MCP 服务已正确配置并可访问
2. 创建设计时尽量提供详细的需求描述，包括设计类型、风格、尺寸等
3. 编辑设计时明确指定目标设计和修改内容
4. 导出设计时指定所需格式和尺寸

## 典型流程

1. **设计创建**：描述需求 → AI 在 Canva可画中创建设计 → 查看效果 → 迭代修改
2. **设计编辑**：指定设计 → 描述修改需求 → AI 执行修改 → 确认结果
3. **设计导出**：指定设计 → 选择导出格式 → AI 执行导出 → 获取结果

## 错误处理

- 若连接失败，检查 MCP 服务地址是否正确
- 若无法创建设计，确认设计参数是否完整
- 若导出失败，检查设计是否已完成且格式参数是否正确
