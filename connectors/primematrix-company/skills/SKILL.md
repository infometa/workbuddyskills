---
name: primematrix-company
description: Query enterprise entity data through the Prime Matrix company MCP Server. Use for exact company matching, registration details, branches, company profiles, change records, shareholders and capital contributions, listing information, and direct external investments.
---

# 质数幻方企业主体数据

调用当前 Connector 暴露的 8 个企业主体工具获取公开企业数据。优先使用 MCP 返回的事实，不依赖模型内部知识补写企业信息。不代替用户作出开户、授信、合作、聘任或合规结论。

## 企业实体锚定

### 可直接作为 `ent_name` 查询

- 18 位统一社会信用代码。
- 以完整法定组织形式结尾的企业全称，包括有限公司、有限责任公司、股份有限公司、集团有限公司、合伙企业、个人独资企业、律师事务所、农民专业合作社及带完整母公司全名的分公司等。

### 必须先做精准匹配

简称、品牌名、股票简称、不完整企业名及需要补地名、括号或企业类型才能成为完整名称的输入，必须将用户原始字符串一字不改地传给 `get_company_precise_name`。禁止自行补全或猜测。

- 唯一匹配：使用返回的完整企业名称继续查询。
- 多个候选：完整展示候选名称、统一社会信用代码和登记状态，等待用户选择；禁止自动选择第一条。
- 未匹配：提示用户检查关键词或直接提供完整企业名称/统一社会信用代码。
- 下游工具提示未匹配时，立即用原始输入调用 `get_company_precise_name`，确认主体后再重试。

当前没有企业名称与统一社会信用代码二要素核验工具。用户同时提供两项时，可选择其中一项作为 `ent_name` 查询，但不要宣称已经完成二要素一致性核验。

## 工具目录

除 `get_company_precise_name` 外，其他工具的 `ent_name` 均为必填企业标识，只能传完整登记名称或 18 位统一社会信用代码。

| 工具 | 实际能力 | 参数与使用规则 |
| --- | --- | --- |
| `get_company_precise_name` | 按简称、关键词或品牌名模糊搜索企业主体 | `ent_name` 传用户原始模糊词。返回多个候选时必须让用户选择 |
| `get_registration_info` | 查询法定代表人、注册资本、成立日期、登记状态、经营范围、地址等核心登记信息 | 必填 `ent_name`；无额外筛选参数 |
| `get_branches` | 查询分支机构名称、负责人、地区、成立日期和登记状态 | 必填 `ent_name`；分公司不等于子公司或对外投资企业 |
| `get_company_profile` | 查询企业简介和主体概况 | 必填 `ent_name`；法定代表人、注册资本等结构化字段以 `get_registration_info` 为准 |
| `get_change_records` | 查询名称、地址、资本、经营范围、法定代表人、股东等工商变更前后内容及日期 | 必填 `ent_name`；这是工商沿革入口，不等于企业历史风险查询 |
| `get_shareholder_info` | 查询企业股东及出资信息；上市企业可返回十大股东 | 必填 `ent_name`；只返回一层直接股东和直接比例，不认定实控人或计算间接持股 |
| `get_listing_info` | 查询股票代码、上市日期、交易所、板块、总市值和股本等上市信息 | 必填 `ent_name`；只覆盖当前在市记录，数值原样引用 |
| `get_external_investments` | 查询企业作为投资方的一层对外投资、被投企业、经营状态、注册资本和持股比例 | 必填 `ent_name`；被投企业不必然是子公司，比例不得自行穿透或相乘 |

## 路由规则

- 企业基本画像：必要时先调用 `get_company_precise_name`，再调用 `get_registration_info` 和 `get_company_profile`，按需补充股东、分支、投资或上市信息。
- 工商历史沿革：调用 `get_change_records`，不要用当前登记信息猜测历史变化。
- 股权与投资：分别使用 `get_shareholder_info` 和 `get_external_investments`，只陈述一层直接关系。
- 关联方风险不属于本 Connector。需要继续查询股东、被投企业或分支机构的风险时，先取得用户明确同意，并要求连接风险信息 Connector；禁止自动逐家扫描。
- 当前不包含董监高个人风险模块。查询法定代表人或高管个人风险时，明确说明当前能力范围不支持。

## 输出与数据边界

- 使用 Markdown 表格呈现列表，并标注“数据来源：质数幻方企业数据 MCP”。
- 工具返回 0 条时写“未发现公开记录”，不得写“确定没有”。
- 字段缺失时写“未公示”或“未返回”；工具失败时明确说明调用失败，不用模型知识补答。
- 金额、市值、股本和比例原样引用，不自行换算、加总、估值或四舍五入。
- 区分事实数据和推理说明；跨来源冲突时提示以官方公示为准。
- 不承诺实时性；涉及数据更新时，以工具返回或质数幻方当前文档口径为准。

## 凭证异常

出现未授权、`invalid_token` 或 API Key 失效时，提示用户前往 `https://mcp.yidian.cn/dashboard/api-keys` 重新生成密钥，并在 WorkBuddy 中断开后重新连接。不要要求用户把 API Key 粘贴到聊天中。
