# 素材标签（material_package_id）参考

广告组创建时可通过 `material_package_id` 字段绑定一个素材标签（系统按平台规则从该标签关联的图/视频素材集合中挑选投放）。本文档聚焦 **如何取值** 与 **如何查询**，供 agent 在识别到用户提及"素材标签 / 素材包"时按需阅读。

> 广告组创建链路仅涉及 **素材标签查询** 与 **在广告组创建时把标签绑定到广告组（`material_package_id`）**。如需 **新建 / 更新素材标签**，或 **把图片 / 视频素材绑定到标签**（`material_labels/bind`），请改用 `tencentads-creatives` 技能。


# 素材标签查询能力（material_labels/get）+ 广告组绑定（material_package_id）

素材标签（material label）是用于聚合一组素材的"标签包"，一条广告组最多绑定**一个**标签，绑定后会从该标签关联的图片/视频集合中按平台规则选材投放。本片段仅包含 **素材标签查询** 与 **广告组创建时绑定字段** 两部分；**素材标签新建 / 更新 / 绑定关联关系** 等管理能力请使用 `tencentads-creatives` 技能。

> **关键映射**：查询接口返回的 `label_id` 等价于广告组创建接口的 `material_package_id`（integer），二者数值相同，仅字段名不同。

## 公共枚举

### BusinessScenario（业务场景）

| 枚举值 | 含义 |
|--------|------|
| `BUSINESS_SCENARIO_CREATIVE` | 素材库类型 |
| `BUSINESS_SCENARIO_DELIVERY` | 投放素材包类型 |

## 1. 查询素材标签列表 (material_labels/get)

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账户 ID（与 `organization_id` 二选一） |
| organization_id | integer | 业务单元 ID（与 `account_id` 二选一） |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| label_id | integer | 标签 ID，精确查询单个标签 |
| label_name | string | 标签名称（1-2048 字节，按名称过滤） |
| first_label_level_id_list | integer[] | 一级标签类目 ID 列表 |
| second_label_level_id_list | integer[] | 二级标签类目 ID 列表 |
| business_scenario | enum | 业务场景，枚举 `BusinessScenario` |
| ownership_type | enum | 素材归属类型，枚举 `OwnershipType` |
| need_count | boolean | 是否返回标签关联的图片/视频数量（脚本未传时默认 `true`） |
| order_by | struct[] | 排序字段数组（`sort_field` 默认 `CREATE_TIME`，1-12 项） |
| page | integer | 页码，默认 1 |
| page_size | integer | 每页数量，默认 10，最大 100 |

> **脚本层说明**：内置 `scripts/get-material-labels.mjs` 封装该接口，参数透传。常用调用：`node scripts/get-material-labels.mjs '{"account_id":"123456789","label_name":"618 大促"}'`。

### 响应核心字段

返回结构 `{ "list": [...], "page_info": {...} }`。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| list[].label_id | integer | **标签 ID（即广告组绑定时的 `material_package_id`）** |
| list[].label_name | string | 标签名称 |
| list[].first_label_level_id / _name | integer / string | 一级类目 ID 与名称 |
| list[].second_label_level_id / _name | integer / string | 二级类目 ID 与名称 |
| list[].label_source | enum | 标签来源（`MaterialLabelSource`） |
| list[].business_scenario_val | enum | 业务场景（`BusinessScenario`） |
| list[].relation_image_count | integer | 关联图片数（`need_count=true` 时返回） |
| list[].relation_media_count | integer | 关联视频数（`need_count=true` 时返回） |
| list[].create_time | string | 创建时间 |
| page_info.total_number | integer | 标签总数 |

## 2. 在广告组创建脚本中绑定 (material_package_id)

调用 `scripts/create-adgroup.mjs`（标准创建 / 智投创建均同名）时，在**入参 JSON 顶层**附加 `material_package_id` 即可绑定一个素材标签；脚本会原样透传到广告组创建接口 `POST /v3.0/adgroups/add` 的 adgroup 对象顶层字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| material_package_id | integer (uint64) | **素材标签 ID**，取自 `material_labels/get` 返回的 `label_id`。**单值**（每组最多一个标签），未提及则不传。 |

> ⛔ **限制**：智投（AIM+）与非智投常规广告均支持；**ADX 程序化广告不可填写**，强制传入会被拒绝。

**取值流程**（在调用 `create-adgroup.mjs` 之前完成）：
1. 用户给出 ID（如"素材包 ID 1234"）→ 直接 `material_package_id: 1234`，无需查询。
2. 用户给出名称/类目（如"618 大促主推标签"）→ 先 `node scripts/get-material-labels.mjs '{"account_id":"...","label_name":"618 大促"}'`，从返回的 `list[].label_id` 取值，再传给 `create-adgroup.mjs`。
3. 用户未提及 → **不传**该字段（保持广告组无素材标签绑定，默认行为）。

<!-- script get-material-labels → scripts/get-material-labels.mjs (injected at build time) -->
