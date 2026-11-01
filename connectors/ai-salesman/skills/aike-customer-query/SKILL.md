---
name: aike-customer-query
display_name: 查客户
display_name_en: Customer Lookup
description: 客户查询与管理，支持按名称/关键词/联系人/国家/展会/跟进状态/意向等级搜索客户，支持 AI 画像筛选（活跃度/流失风险/购买潜力/AI 有更新）与创建/更新时间范围，查看客户详情（含 AI 画像）、修改客户信息（含行业/顾虑标签、主联系人、信任度等画像字段）、删除客户。当用户说"查一下 ABC 公司的信息""有哪些高流失风险的客户""修改这个客户的联系方式"时触发。
description_zh: 客户搜索（名称/关键词/联系人/国家/展会/跟进状态/意向等级/信息确认/AI 画像/时间范围）、详情查看（含 AI 画像）、信息修改（含画像人工字段）与删除。
description_en: Customer search with AI-profile filters, detail view, update and delete in GlobalSales Foreign Trade Salesman.
category: sales-commerce
version: 1.1.0
author: AI销客
---

# 查客户

面向「客户管理专家」的客户查询与维护技能（查 / 改 / 删，不含新增——新增见「新增客户」技能）。

## 功能描述

- 多维搜索客户列表：客户名 / 关键词（客户名称/国家/行业标签）/ 联系人名 / 国家区号 / 展会名 模糊匹配，按**跟进状态 / 意向等级 / 信息确认状态 / AI 画像（活跃度、流失风险、购买潜力、"AI 有更新"）/ 创建或更新时间范围**过滤
- 查看指定客户的完整详情（基础档案、AI 画像、全部联系人）
- 修改客户基础信息与 AI 画像人工字段（只传要改字段；联系人 / 关联展会 / 业务员 / 标签组为**整体替换**）
- 删除客户（两次确认，不可恢复）

## 触发场景（自然语言示例）

- "查一下 ABC 公司的信息"
- "看看 XYZ 客户的历史跟进"
- "有哪些高流失风险的客户？"
- "列出还没确认信息的新客户"
- "这个月新加了哪些客户？"
- "把 ABC 的联系人电话改一下"
- "删除这个重复的客户"

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`full` 开关**：读工具默认 `full=false`，返回精简字段（省 token）；显式 `full=true` 返回后端原始全量字段。
- **分页**：`page`（默认 1）、`pageSize`（默认 10，上限 50）；越界报参数错误。
- **`dry_run` 预演**：`update_customer` 支持 `dry_run=true`，仅回显载荷、**不落库**；默认 `false` 正式写入。
- **`confirm` 二次确认**：删除类（`delete_customer`）先不带 `confirm` 返回客户摘要；用户确认后带 `confirm=true` 才执行（不可恢复）。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:customers:ls:edit、pc:customers:ls:delete；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；删除客户忘记带 `confirm=true` 时会返回 `confirmRequired` 与删除摘要，向用户复述确认后再执行（删除不可恢复）。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `search_customers` | 搜索客户 | `pc:customers:ls:list` | ✅ 已开放 |
| `get_customer` | 获取客户详情 | `pc:customers:ls:list` | ✅ 已开放 |
| `update_customer` | 修改客户信息 | `pc:customers:ls:edit` | ✅ 已开放 |
| `delete_customer` | 删除客户 | `pc:customers:ls:delete` | ✅ 已开放 |

## 工具调用说明

### `search_customers`
- **用途**：搜索客户档案（多维过滤 + 分页）
- **入参**（参数名为驼峰，注意大小写）：
  - `customerName`（string，可选）：客户/企业名称，模糊匹配
  - `keyword`（string，可选）：搜索关键词，模糊匹配 客户名称 / 国家 / 行业标签
  - `contactName`（string，可选）：联系人姓名
  - `countryCode`（string，可选）：国家区号/代码
  - `exhibitionName`（string，可选）：展会名称
  - `followStatus`（enum，可选）：跟进状态，`pending_assign`（待分配）/ `following`（跟进中）/ `dealed`（已成交）/ `serving`（服务中）/ `lost`（已流失）
  - `intentionLevel`（enum，可选）：意向等级，`high` / `medium` / `low`
  - `infoConfirmed`（boolean，可选）：信息是否已确认准确完整
  - `activityLevel`（enum，可选）：客户活跃度（AI 画像），`high` / `medium` / `low`
  - `churnRisk`（enum，可选）：流失风险（AI 画像），`high` / `medium` / `low`
  - `purchasePotential`（enum，可选）：购买潜力（AI 画像），`high` / `medium_high` / `medium` / `low`
  - `aiHasUpdates`（boolean，可选）：`true`=仅看有 AI 待确认更新（"AI 有更新"角标）的客户
  - `createdAtFrom` / `createdAtTo`（string，可选）：创建时间范围（ISO 8601，如 `2026-09-01`；纯日期表示含当日全天/从当日 00:00 起）
  - `updatedAtFrom` / `updatedAtTo`（string，可选）：更新时间范围（口径同上）
  - `page`（int，可选，默认 1）
  - `pageSize`（int，可选，默认 10，上限 50）
  - `full`（boolean，可选，默认 `false`）
- **返回**：`{ total, page, pageSize, items[] }`；`items` 每项字段：
  - `id` / `customerName` / `countryName` / `countryCode`
  - `source`（客户来源）/ `ownerUserName`（创建人）
  - `followStatus`（跟进状态）/ `intentionLevel`（意向等级）
  - `activityLevel` / `churnRisk` / `purchasePotential`（AI 画像）
  - `hasPendingUpdates`（是否有 AI 待确认更新）
  - `createdAt` / `updatedAt`
  - `primaryContact`：首个联系人 `{ id, name, position, enterpriseName, email, phone, whatsapp }`
  - `latestFollow`：最近一条跟进 `{ type（audio/manual/marketing_email）, followTime, summary, name }`
- **注意**：`total` 即过滤后总数，可直接分页统计；"本月新增客户"用 `createdAtFrom`/`createdAtTo` 精确计数。

### `get_customer`
- **用途**：按 id 查详情（需先用 `search_customers` 拿到 id）
- **入参**：
  - `id`（string uuid，**必填**）
  - `full`（boolean，可选，默认 `false`）
- **返回**（精简口径）：
  - `id` / `customerName` / `countryName` / `countryCode` / `source` / `ownerUserName`
  - `scale` / `priceSensitivity` / `followStatus` / `intentionLevel` / `infoConfirmed`
  - `remark`（备注）/ `createdAt` / `updatedAt`
  - AI 画像块：`industryTags`（行业标签）/ `activityLevel(+activityLevelReason)`（活跃度）/ `churnRisk(+churnRiskReason)`（流失风险）/ `purchasePotential(+purchasePotentialReason)`（购买潜力）/ `opportunityPrediction`（机会预测）/ `predictionBasis`（预测依据）/ `suggestedNextStep`（建议下一步）/ `communicationPreference`（沟通偏好）/ `trustLevel`（信任度）/ `concernTags`（顾虑标签）/ `primaryContactName` / `primaryContactPosition`（主联系人）/ `hasPendingUpdates`（AI 待确认更新标记）/ `aiAnalyzedAt`（画像分析时间）
  - `contacts[]`：全部联系人 `{ id, name, position, enterpriseName, countryCode, email, emailValidations, phone, whatsapp, wechat, extraInfo }`
- **注意**：历史跟进时间线不在本工具返回内，需看客户动态时用仪表盘的 `customerUpdates` 或营销反馈；AI 待确认提案明细（`aiPendingUpdates`）传 `full=true` 获取。

### `update_customer`
- **用途**：修改客户档案；**只传需要修改的字段**，未传字段保持不变；一个字段都不传时报错「未提供任何要修改的字段」
- **入参**：
  - `id`（string uuid，**必填**）
  - `customer_name`（string，可选）：客户/企业名称
  - `country_code`（string，可选）：国家区号，如 +86 / ARG
  - `source`（enum，可选）：`online_channels` / `exhibitions` / `other_offline_channels` / `referrals` / `others`
  - `scale`（enum，可选）：规模 `large` / `medium` / `small`
  - `intention_level`（enum，可选）：`high` / `medium` / `low`
  - `price_sensitivity`（enum，可选）：`very_high` / `high` / `medium` / `low` / `very_low`
  - `follow_status`（enum，可选）：同 `followStatus` 枚举
  - `remark`（string，可选）
  - `product_tags`（string[]，可选）：产品偏好标签（整组替换）
  - `exhibition_ids`（uuid[]，可选）：关联展会，**整体替换**
  - `sales_user_ids`（uuid[]，可选）：所属业务员，**整体替换**
  - `industry_tags`（string[]，可选）：行业标签，**整组替换**，最多 50 个（2026-09 新增）
  - `concern_tags`（string[]，可选）：顾虑标签，**整组替换**，空数组=清空，最多 50 个（2026-09 新增）
  - `primary_contact_id`（string uuid | null，可选）：主联系人 ID，须属于该客户联系人列表；传 null 清除关联（2026-09 新增）
  - `communication_preference`（string，可选）：沟通偏好，自由文本 ≤255 字（2026-09 新增）
  - `trust_level`（enum，可选）：信任度 `low` / `medium` / `high`（2026-09 新增）
  - `interested_product_ids`（uuid[]，可选）：感兴趣商品 ID 列表（商品库选取，**整组替换**，空数组=清空，最多 100 个）（2026-09 新增）
  - `contacts`（object[]，可选）：联系人列表，**整体替换**；元素 `{ id?（更新已有联系人/设主联系人时传）, name（必填）, position?, enterprise_name?, country_code?, email?（多个用英文逗号分隔，可传空串清空）, phone?, wechat?, whatsapp?, extra_info?, card_ocr_record_id? }`
  - `dry_run`（boolean，可选，默认 `false`）：为 `true` 时返回 `{ dryRun: true, id, wouldUpdate: <载荷> }`
- **返回**：`{ id, message: '客户信息已更新' }`（不含更新后全量对象，需要时再 `get_customer`）
- **注意**：活跃度/流失风险/购买潜力等 **AI 画像值本身不可人工直改**（不在修改白名单，传入即被后端忽略）——画像更新走 AI 提案采纳链路；人工可维护的是上表 `industry_tags` / `concern_tags` / `primary_contact_id` / `communication_preference` / `trust_level` / `interested_product_ids`。

### `delete_customer`
- **用途**：删除客户（不可恢复）
- **入参与流程**：
  - 第一次不带 `confirm` → 返回 `{ confirmRequired: true, wouldDelete: <客户详情摘要，字段同 get_customer>，message }`，**不删除**
  - 用户确认后带 `confirm: true` → 执行删除，返回 `{ id, message: '客户已删除' }`
- **注意**：删除需用户角色含 `pc:customers:ls:delete` 权限码（连接器授权已包含，403 多为角色未配置）。

## 返回格式

- 搜索场景：列表含客户名 / 国家 / 跟进状态 / 意向等级 + 主联系人，标注总数与分页
- 详情场景：结构化档案卡（基础信息 + 全部联系人 + 备注）
- 修改 / 删除：返回操作结果；修改后如需展示最新档案再调 `get_customer`
