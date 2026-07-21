---
name: mastergo-vibe-mcp
description: "Connect to the MasterGo canvas to allow AI to design, modify, synchronize, and retrieve D2C code."
description_zh: "连接 MasterGo 画布，让 AI 进行设计、修改、同步和获取 D2C 代码。"
description_en: "Connect to the MasterGo canvas to allow AI to design, modify, synchronize, and retrieve D2C code."
version: "1.0.18"
---

# MasterGo 莫高设计 Skill

MasterGo Vibe MCP 连接器，通过 MCP 协议连接 MasterGo 画布，让 AI 能够进行设计创建、修改、同步和获取 D2C（Design to Code）代码。

## 功能能力

- **设计创建**：使用自然语言描述，AI 自动在 MasterGo 画布上生成设计稿
- **设计修改**：对当前选中的图层进行属性修改（颜色、尺寸、文字等）
- **组件库引用**：使用当前文件已订阅的团队组件库生成页面
- **代码生成**：获取当前选中图层的前端代码（D2C）
- **设计同步**：保持设计与代码的同步更新

## 调用原则

1. 确保 MasterGo 桌面端已启动并打开了目标文件
2. 需要在 MasterGo 中选中目标图层后执行修改/获取代码操作
3. 设计生成时尽量提供详细的需求描述，包括页面类型、布局、组件等
4. 修改属性时明确指定目标元素和属性值

## 典型流程

1. **设计生成**：描述需求 → AI 在画布生成设计稿 → 查看效果 → 迭代修改
2. **属性修改**：选中图层 → 描述修改需求 → AI 执行修改 → 确认结果
3. **代码获取**：选中图层 → 请求获取代码 → AI 返回前端代码

## 错误处理

- 若连接失败，检查 MasterGo 桌面端是否已启动
- 若无法获取选中图层，确认已在画布中选中目标元素
- 若组件库引用失败，检查当前文件是否已订阅所需团队组件库
