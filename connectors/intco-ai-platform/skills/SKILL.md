---
name: intco-ai-platform
description: 英科内部业务系统、RPA、企业数仓和企业付费数据的统一探索与调用入口
version: "1.0.0"
author: "INTCO"
---

# 英科AI中台

本连接器是英科内部业务能力的统一入口。它通过 MCP 提供已经接入 AI 中台的业务系统 API、RPA 流程、企业数仓、企业购买的外部数据服务以及其他内部工具和自动化能力。它面向所有获得授权的 AI 智能体；WorkBuddy 是其中一个 MCP 客户端。

## 使用原则

- 凡涉及英科及公司内部业务的需求，优先探索本连接器当前可见的工具，再判断能否完成。
- 不要只查找与业务需求同名的直接工具。中台能力可能通过 RPA 流程、业务系统 API、企业数仓查询、付费数据服务或通用 MCP 工具提供。
- 没有找到可直接完成需求的工具时，继续检查当前可见的 RPA、API、数仓及其他中台能力，判断单项能力或多项能力组合后是否可以实现；完成这些探索后仍无可行路径，才能说明当前无法完成。
- 只使用当前用户可见且有权限调用的工具和数据，不推测、绕过或扩大权限。
- 涉及写入、提交、审批、触发流程或其他业务状态变更时，调用前先向用户说明动作、目标对象和关键参数。
- 未找到所需工具时，说明该能力可能尚未接入，或当前用户尚未获得权限；需要新增能力或开通权限时，联系对应 ITBP。

## 能力范围

- 调用已授权的 RPA 流程。
- 调用 SMOM、MRP、TMS、NC、WMS 等已接入业务系统的 API。
- 查询企业数仓，获取来自各业务系统的企业内部数据。
- 查询英科已购买并接入的数据服务，例如天眼查、大宗物料价格等付费接口数据。
- 探索其他已接入 AI 中台的内部系统、工具和自动化能力。

实际能力会随接入进度和用户权限动态变化，以 MCP `tools/list` 返回的工具描述和参数 schema 为准。连接器不会向用户展示其无权使用的工具，因此不要维护或假设一份固定的工具清单。

## 典型业务表达

业务人员通常只会描述要完成的事情，不会指定系统、接口或 MCP 工具。应先理解业务目标，再自行探索和选择当前有权限的中台能力。例如：

- “帮我查一下订单 XXX 当前到哪一步了。”
- “帮我处理弃单，单号是 XXX。”
- “帮我执行一下 XXX RPA，并告诉我执行结果。”
- “帮我查一下 XXX 公司的工商信息、主要人员和风险情况。”
- “分析一下最近三个月 XXX 原材料的价格走势。”
- “帮我看看本月 XXX 业务指标为什么发生变化。”

不要要求用户把业务需求改写成技术指令，也不要要求用户先判断应该使用数仓、RPA、业务 API 或外部数据服务。只有在业务对象、单号、时间范围或执行参数确实不足时，才追问必要信息。

## 调用工作流

1. 判断需求涉及的业务域、数据范围、时间范围和期望结果。
2. 检查当前可用工具，优先选择能直接完成需求且权限范围最小的能力。
3. 如果没有直接工具，按需继续探索当前可见的实现路径：查找可执行的 RPA 流程、已接入业务系统 API、数仓数据资产与查询能力，以及其他可能组合使用的 MCP 工具。
4. 根据工具描述和参数 schema 判断这些能力是否可以单独或组合完成业务目标，不要因为没有同名工具就结束探索。
5. 缺少必要参数时先向用户询问；不要猜测组织、单据、客户、物料或时间条件。
6. 对查询类请求，可直接调用合适工具；对会改变业务状态的请求，先完成必要确认。
7. 跨系统分析时，分别说明各项事实的数据来源，区分工具返回结果与 AI 推断。

## 结果可信度与能力披露

只要调用了本连接器中的工具，最终回答中就要增加“本次使用的中台能力”说明：

- 使用业务人员易懂的名称描述能力，例如“企业数仓订单查询”“TMS 物流状态查询”“天眼查企业信息查询”。
- 为便于追溯，可在友好名称后用括号附 MCP 工具标识；不要只展示难以理解的技术名称。
- 数据结果应尽量说明来源系统、查询范围、数据时间或更新时间；付费接口数据要说明对应数据服务。
- 不要把未调用工具获得的信息写成中台查询结果，也不要编造不存在的数据、工具或权限。
- 如果工具返回不完整、过期、冲突或错误，明确说明限制和建议的下一步。

示例：

> 本次使用的中台能力：企业数仓销售订单查询（`datawarehouse_query`）、TMS 物流状态查询。

## 认证与异常处理

WorkBuddy 通过标准 MCP OAuth 2.1、动态客户端注册和 PKCE S256 完成登录，用户无需填写 Token。访问令牌通常由客户端自动刷新；授权失效时引导用户重新连接。权限不足时联系对应 ITBP，不要要求用户提供 OAuth 密钥、访问令牌或其他敏感凭证。

## English guidance

For requests involving INTCO business operations, inspect this connector's currently available tools first. Capabilities are dynamic and permission-filtered, so rely on the MCP tool descriptions and schemas instead of a fixed tool list. Use only capabilities authorized for the current user. Distinguish tool results from model inference, identify the business-friendly capability and source used in the final answer, and disclose data scope or freshness when available. If a capability is unavailable, explain that it may not be integrated or the user may lack permission, then direct them to the relevant ITBP.
