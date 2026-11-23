---
name: dianleida-connector-basics
version: "1.0.0"
display_name: "店雷达连接基础"
display_name_en: "Dianleida Connector Basics"
description: "店雷达 MCP 的基础连接与通用调用规范。"
description_en: "Basic connection and general usage guidance for the Dianleida MCP."
---

# 店雷达连接基础

本 Skill 仅提供店雷达 MCP 的基础使用约定，不预置具体业务流程、工具参数或结果模板。可用能力、工具名称和参数以当前 MCP 服务实际返回的工具描述为准。

## 使用规则

1. 用户明确提出目标后，优先选择 MCP 服务实际暴露且描述匹配的工具。
2. 严格按照工具 schema 传参，不自行猜测字段、枚举值、分页方式或返回结构。
3. 需要图片、链接或其他输入时，先确认工具 schema 对输入格式的要求。
4. 结果只引用服务实际返回的数据，不补造商品、价格、销量、店铺或供应商信息。
5. 工具调用失败时，向用户说明实际错误；不要用无关工具反复探测或自动切换到其他服务。
6. 涉及批量查询时，复用已有结果，避免不必要的重复调用。

## 认证与连接

本连接器使用 MCP 标准 OAuth 流程。首次使用或授权失效时，按客户端提示完成登录授权；不要在 Skill、配置文件或消息中写入 Access Token、Refresh Token 或其他密钥。

## 输出要求

根据用户要求整理返回结果。缺失字段保持缺失，不把推测内容写成事实；如服务返回分页或继续查询信息，只有在用户需要时才继续请求。
