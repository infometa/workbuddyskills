# Ardot Design Generator

> Ardot 设计工具：在 Ardot 中生成高质量设计稿，包括移动端 UI、网站页面、Web 应用、幻灯片等。

## 简介

`ardot-design-generator` 是一个面向 Ardot 画布的 CodeBuddy 插件，通过 MCP（Model Context Protocol）对接 Ardot 本地服务，将自然语言或参考图片转化为可编辑的 `.ardot` 设计稿。插件内置多个专业 Skill，覆盖从零生成、图生 UI、图像理解到设计稿出码的全流程。

- **插件名称**：`ardot-design-generator`
- **版本**：`1.0.0`
- **作者**：Ardot Teams
- **主页**：https://ardot.tencent.com/
- **许可证**：MIT

## 功能特性

- 通过 Ardot MCP Server 直接操作画布节点，支持批量创建、修改、对齐、布局等原子操作
- 一键生成移动端界面、网站落地页、Web 应用、Dashboard、幻灯片等多种设计稿
- 支持图生 UI（Image to UI）：上传截图、线框图、草图 → 自动还原为可编辑设计稿
- 支持原生图像理解：Agent 直接分析截图，输出结构化 JSON（页面结构、设计风格、区域语义、差异对比）
- 支持从网站提取设计规范，生成设计系统（Design Tokens、组件库、排版、配色）
- 支持设计稿转前端代码（HTML / CSS / JS），实现 1:1 像素级还原

## 目录结构

```
ardot-design-generator/
├── .codebuddy-plugin/
│   └── plugin.json              # 插件元信息与 Skill 注册
├── .mcp.json                    # MCP Server 连接配置
├── rules/                       # 插件规则（可扩展）
├── skills/
│   ├── ardot-design-assistant/  # 核心设计助手（生成/修改/出码/幻灯片）
│   ├── image-to-ui/             # 图生 UI（四阶段流水线）
│   └── image-understanding-native/ # 原生图像结构化语义分析
└── README.md
```

## MCP 配置

插件通过本地 Ardot MCP Server 驱动所有设计操作，配置见 `.mcp.json`：

```json
{
  "mcpServers": {
    "ardot": {
      "url": "http://127.0.0.1:50501/api/v1/mcp"
    }
  }
}
```

请确保 Ardot 客户端已启动并监听 `127.0.0.1:50501`，否则插件无法访问画布。

## 内置 Skills

### 1. ardot-design-assistant

核心设计助手 Skill，适用于任何涉及创建、编辑、修改视觉设计、UI 界面、页面、布局、组件，以及将设计稿转换为前端代码的任务。

**典型触发词**：

- 生成页面 / 设计页面 / 创建界面
- 设计登录页 / 做一个 dashboard / 做一个落地页
- 修改设计稿 / 调整布局 / 修改样式
- 创建幻灯片 / 设计演示文稿
- 提取设计风格 / 生成设计指南
- 设计稿转代码 / 一比一还原 / 导出为网页

**参考文档**（按需加载）：

- `rules/design-rules.md`：Flexbox 布局、文本节点、组件、表格、图片、属性参考
- `references/ardot-workflow.md`：Ardot 生成/更新/分析工作流
- `references/slides-workflow.md`：幻灯片五阶段创作流程
- `references/extract-style-guide-from-web.md`：网站 → 设计指南提取流程
- `references/design-to-code-workflow.md`：设计稿 → 前端代码出码流程
- `rules/style-guide.md`：视觉风格指南与 Bento Grid 范式

### 2. image-to-ui

图生 UI Skill，将参考图片（截图、线框图、设计稿、手绘草图等）转化为可编辑的 Ardot 画布设计稿。

**核心流程**：图片 → 设计风格提取 → 结构化精细描述 → 反思校验 → 画布绘制

采用 4 阶段流水线，融合 Prompt Chaining、Reflection、Multi-Agent Collaboration 设计模式。Phase 1~3 为 Agent 内部思考，用户仅看到进度提示与 Phase 4 的最终画布结果。

**典型触发词**：把这张截图做成设计稿、还原这个界面、复刻这个页面、参照图片设计、图生 UI、截图转设计稿。

### 3. image-understanding-native

图片结构化语义分析 Skill，Agent 直接利用多模态能力，将 UI 截图转化为结构化 JSON，零外部依赖，不启动 MCP Server。

**四种分析任务**：

| 任务 | 输入 | 输出 | 何时使用 |
|------|------|------|---------|
| A. 全页面结构分析 | 截图 | `page_structure` | 分析截图、看布局 |
| B. 设计风格提取 | 截图 | `design_spec` | image-to-ui Phase 1、提取设计风格 |
| C. 区域语义描述 | 截图 + 区域 | `region_description` | 描述这个区域 |
| D. 对比差异分析 | 两张截图 | `comparison` | 对比差异、改了什么 |

## 使用方式

1. 安装并启用本插件后，确认本地 Ardot 客户端已运行
2. 在 CodeBuddy 对话中直接描述设计需求，例如：
   - "帮我设计一个 SaaS 产品的落地页"
   - "为这份设计稿生成对应的 HTML 代码"
   - "创建一套科技感的幻灯片，主题是 AI Agent 介绍"
3. 插件会自动匹配合适的 Skill，通过 Ardot MCP Server 在画布上生成/修改设计

## 相关链接

- Ardot 官网：https://ardot.tencent.com/
- MCP 协议规范：https://modelcontextprotocol.io/

## License

MIT © Ardot Teams
