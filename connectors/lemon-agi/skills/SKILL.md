---
name: lemon-agi
description: 乐檬零售 AGI 能力平台，用于查询乐檬零售生态的批发、仓储、零售等业务数据。当用户需要查询批发销售单、批发退货单、客户信息、批发价、库存、入库出库等业务数据时使用。
---

# 乐檬零售（Lemon AGI）

## 概述

乐檬 AGI 是乐檬（Nhsoft）的 AGI 能力平台，通过 MCP 暴露统一的「业务能力发现与调用」网关。本连接器提供两个 MCP 工具，用于发现并调用乐檬生态（批发 WHS、仓储 WMS、零售等）的业务能力。当前平台已发布 90+ 个能力，覆盖批发单据、批发基础资料、入库出库、库存、盘点、拣货等场景。

## 工作流程（重要）

乐檬零售 AGI 采用「发现能力 → 读取文档 → 调用接口」三步模式：

1. **搜索能力**：调用 `search_agi_abilities`，按关键词搜索需要的业务能力，拿到 `ability_code`。
2. **读取文档**：调用 `get_agi_ability_document`，读取该能力的完整 OpenAPI 3.0 文档，获得接口路径、请求参数、鉴权方式与返回结构。
3. **调用接口**：按 OpenAPI 文档中的 `servers[].url`（例如 `https://cloud.nhsoft.cn/agi/api`）与 `paths` 拼接完整 URL，携带 `Authorization: Bearer <Lemon Personal Token>` 请求头，按文档 `requestBody` schema 发起 HTTP 请求。

不要在 SKILL 中硬编码接口地址或参数；每次都应先读取对应能力的 OpenAPI 文档，以文档为准。

## MCP 工具

### search_agi_abilities

搜索 SkillHub 已发布的乐檬 AGI Ability。

参数：
- `keyword`（string，可选）：关键词，不区分大小写，匹配能力编码、接口路径、名称和摘要。
- `app_code`（string，可选）：应用编码精确筛选，如 `WHS`（批发）、`WMS`（仓储）。
- `method`（string，可选）：HTTP 方法精确筛选，如 `GET`、`POST`。
- `tag_path`（string，可选）：TAG 路径，包含其所有下级路径。
- `page`（integer，默认 1）：页码。
- `size`（integer，默认 5，最大 20）：每页数量。

返回：能力列表，含 `ability_code`、`name`、`summary`、`primary_tag`、`method`、`interface_path`、`app_code` 等。

### get_agi_ability_document

读取指定 AGI Ability 的完整 OpenAPI 文档。

参数：
- `ability_code`（string，必填）：能力编码，如 `nhsoft.whs.ai.wholesaleorder.find`。
- `version`（string，可选）：历史发布版本，不填时读取当前发布版本。

返回：完整 OpenAPI 3.0 文档，含 `paths`、`components.schemas`、`securitySchemes`、`servers`。

## 常见业务能力（示例）

- 批发销售单查询：`nhsoft.whs.ai.wholesaleorder.find`
- 批发订单查询：`nhsoft.whs.ai.wholesalebook.find`
- 批发退货单查询：`nhsoft.whs.ai.wholesalereturn.find`
- 批发客户信息：`nhsoft.whs.ai.client.find`
- 客户批发价：`nhsoft.whs.ai.storeitemclientspec.find`
- 入库单查询：`nhsoft.wms.ai.warehouseorder.find`
- 出库单查询：`nhsoft.wms.ai.outwarehouseorder.find`
- 库存（期效）查询：`nhsoft.wms.ai.stdinventoryln.find`

能力会持续更新，以上仅为示例；务必通过 `search_agi_abilities` 获取最新能力与准确编码。

## 鉴权

- 使用 Lemon Personal Token（`pt_` 开头），通过 `Authorization: Bearer <token>` 请求头传递。
- Token 绑定账套，业务数据以 Token 对应账套为准，请求中无需单独传账套号。
- 若返回 401，说明 Token 失效或权限不足，应引导用户重新生成并填写。

## 注意事项

- 日期时间参数使用 `yyyy-MM-dd HH:mm:ss` 格式（例如 `2026-08-12 00:00:00`）。
- 查询类接口支持分页（`limit` / `offset`），大批量数据应分页拉取，避免遗漏。
- 写操作类能力（如 `save`、`audit` 等）属于高风险操作，执行前必须向用户确认。
- 能力文档中标注 `format: date-time` 的字段，按上述日期格式传值。
