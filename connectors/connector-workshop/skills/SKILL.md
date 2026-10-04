---
name: connector-workshop
display_name: 连接器工坊
display_name_en: Connector Studio
description: Probe a remote MCP endpoint, draft and validate a WorkBuddy connector, and download it as a spec-compliant zip.
description_zh: 探测远程 MCP 端点能力，起草并校验 WorkBuddy 连接器配置，产出符合规范的连接器 zip 包。
description_en: Probe a remote MCP endpoint, draft and validate a WorkBuddy connector, and download it as a spec-compliant zip.
category: developer
version: 1.0.0
author: 智多心教育科技
---

# 连接器工坊 使用指南

## 触发场景

当用户需要 探测远程 MCP 端点能力，起草并校验 WorkBuddy 连接器配置，产出符合规范的连接器 zip 包 时，使用本技能。

典型说法：「帮我探测这个 MCP 端点有哪些能力」。

## 工具参考

共 4 个工具（由端点探测自动生成，请核对描述）：

| 工具 | 参数 | 用途 |
|---|---|---|
| `connector_studio_probe` | `url`（string，必填）：远程 MCP 端点完整 URL，如 https://example.com/mcp；`token`（string，可选）：可选 Bearer Token（服务需鉴权时提供，仅本次请求使用） | 对远程 MCP 端点做探测（initialize→tools/resources/prompts/list，零副作用，绝不调用任何工具）。返回服务信息、工具清单（含 inputSchema）、资源、Prompts、认证行为与耗时。参数 url 必须是 https://（仅本机 localhost/127.0.0.1 允许 http 调试）；私网/保留地址会被拒绝。token 可选——仅用于本次探测请求，不存储不记录。探测成功后建议用它组装 draft，再调 validate/generate_skill/build。 |
| `connector_studio_validate` | `draft`（unknown，必填）：连接器草稿：导出 JSON 字符串或 AppState 对象 | 对一份连接器草稿（draft）执行全部 14 条打包校验规则，返回逐项报告与自动推导的 minWorkbuddyVersion。draft 可以是向导导出的草稿 JSON 字符串、{schemaVersion,state} 对象、或 AppState 对象（缺字段自动补默认）。适合在 assemble 出 draft 后调用：hasError=true 时按 items 逐项修复后再生成。 |
| `connector_studio_generate_skill` | `draft`（unknown，必填）：连接器草稿：导出 JSON 字符串或 AppState 对象 | 基于草稿（draft）中的探测结果与基本信息，起草 SKILL.md 的 frontmatter 与正文骨架。返回 frontmatter、content 与拼好的完整 markdown。注意：这是「起点」——正式打包前请人工核对/改写内容。 |
| `connector_studio_build` | `draft`（unknown，必填）：连接器草稿：导出 JSON 字符串或 AppState 对象 | 把一份草稿（draft）打包成 WorkBuddy 连接器 zip（base64），同时返回 zip 内文件清单与校验报告。返回结构：{ filename, sizeBytes, base64, files[], validation:{hasError,errorCount,warningCount,items} }。请先跑 validate 确认 hasError=false 再 build；若仍有 Error，validation 字段会告诉你哪里不合规。 |

## 执行步骤

1. 根据用户请求从上表选择合适的工具（优先 `connector_studio_probe`）。
2. 组装参数并调用，返回结果转述给用户。
3. 工具返回错误时，把错误信息翻译成用户能理解的说法，并给出下一步建议。

## 认证与错误处理

- 本连接器无需认证，可直接调用。

- 参数错误（如缺少必填参数）时向用户澄清需求后再重试，不要盲目重试同一参数。

## 输出规范

- 结果默认用中文转述；保留工具返回的关键字段原文。
- 长列表先给摘要再给明细。

