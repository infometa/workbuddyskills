# 素材标签操作参考（查询 / 创建 / 更新 / 绑定）

本文档覆盖素材标签（material_labels）的四个核心接口：
- `material_labels/get`：查询账户/业务单元下的素材标签列表
- `material_labels/add`：新建一批素材标签
- `material_labels/update`：更新单个标签的名称或类目
- `material_labels/bind`：把图片/视频素材与标签建立绑定关系

广告查询的 filtering 中可以通过 `image.label_name` / `video.label_name` 字段，按素材中心的"素材标签"来筛选图片/视频素材；广告组创建时通过 `material_package_id` 绑定一个素材标签，二者数值与 `material_labels/get` 返回的 `label_id` 一致。

> **关键映射**：查询接口返回的 `label_id` 等价于广告组创建接口的 `material_package_id`（integer），二者数值相同，仅字段名不同。

## 公共枚举

以下枚举在多个标签接口中复用，统一在脚本入口处做白名单校验，传入未列出的值脚本会直接报错并附带可选值清单。

### BusinessScenario（业务场景）

| 枚举值 | 含义 |
|--------|------|
| `BUSINESS_SCENARIO_CREATIVE` | 素材库类型 |
| `BUSINESS_SCENARIO_DELIVERY` | 投放素材包类型 |

### BindingType（标签绑定类型，仅 bind 接口）

| 枚举值 | 含义 |
|--------|------|
| `LABEL_BINDING_TYPE_OVERWRITE` | 素材标签覆盖绑定（清空原绑定后重新绑定） |
| `LABEL_BINDING_TYPE_ADD` | 素材标签新增绑定（在原绑定基础上追加） |
| `LABEL_BINDING_TYPE_DELETE` | 素材标签删除绑定（解除指定素材与标签的关联关系） |

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

> **脚本层说明**：各创编 skill 内置 `scripts/get-material-labels.mjs` 封装该接口，参数透传。常用调用：`node scripts/get-material-labels.mjs '{"account_id":"123456789","label_name":"618 大促"}'`。

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

## 2. 创建素材标签 (material_labels/add)

POST 接口，在指定账户/业务单元下批量创建素材标签。

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账户 ID（与 `organization_id` 二选一） |
| organization_id | integer | 业务单元 ID（与 `account_id` 二选一） |
| labels | struct[] | 标签信息列表，每项至少含 `label_name` |

### labels[i] 字段

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| label_name | string | **是** | 标签名称（1-2048 字节） |
| first_label_level_name | string | 否 | 一级标签类目名称 |
| second_label_level_name | string | 否 | 二级标签类目名称 |
| business_scenario | enum | 否 | 业务场景，见上文 `BusinessScenario`；**脚本兜底**：未传时自动填 `BUSINESS_SCENARIO_DELIVERY`（投放素材包类型） |

### 响应

返回结构 `{ "success_label_list": [...], "fail_label_list": [...] }`，分别对应新增成功 / 失败的标签列表。

### 调用示例

```bash
node scripts/add-material-labels.mjs '{"account_id":"123456789","labels":[{"label_name":"618 大促主推","first_label_level_name":"大促","second_label_level_name":"618"},{"label_name":"夏装外套","business_scenario":"BUSINESS_SCENARIO_CREATIVE"}]}'
```

## 3. 更新素材标签 (material_labels/update)

POST 接口，更新单个素材标签的名称或类目归属。

### 必需参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | integer | 二选一 | 广告主账户 ID |
| organization_id | integer | 二选一 | 业务单元 ID |
| label_id | integer | **是** | 待更新的标签 ID |
| label_name | string | **是** | 新的标签名称（1-2048 字节）。**协议层面 label_name 始终必填**，如只想改类目而不改名称，请把原标签名再传一次 |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| first_label_level_name | string | 新的一级标签类目名称 |
| second_label_level_name | string | 新的二级标签类目名称 |

### 响应

返回结构 `{ "success_label_list": [...], "fail_label_list": [...] }`。

### 调用示例

```bash
node scripts/update-material-labels.mjs '{"account_id":"123456789","label_id":12345,"label_name":"618 大促主推（更新）","first_label_level_name":"大促","second_label_level_name":"618"}'
```

## 4. 绑定标签素材关联关系 (material_labels/bind)

POST 接口，管理图片/视频素材与素材标签的关联关系。支持三种模式：**覆盖绑定**、**新增绑定**、**解除绑定**（详见下文 `binding_type` 枚举）。

### 必需参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | integer | 二选一 | 广告主账户 ID |
| organization_id | integer | 二选一 | 业务单元 ID |
| label_id_list | integer[] | **是** | 目标标签 ID 列表 |
| image_id_list / media_id_list | string[] | **至少一个非空** | 图片 ID 列表与视频 ID 列表，二者可同时传，但**不能都为空**（脚本前置校验） |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| binding_type | enum | 标签绑定类型，见上文 `BindingType` |
| business_scenario | enum | 业务场景，见上文 `BusinessScenario` |

### 响应

返回结构 `{ "success_id_list": [...], "fail_id_list": [...], "fail_reason_list": [...] }`：
- `success_id_list` / `fail_id_list`：绑定成功 / 失败的素材 ID 列表
- `fail_reason_list[i]`：失败原因明细，含 `material_id` / `label_id` / `label_name` / `reason` / `relation_tid_list`（关联创意 ID）

### 调用示例

新增绑定（在原标签关联基础上追加图片）：

```bash
node scripts/bind-material-labels.mjs '{"account_id":"123456789","label_id_list":[1234,5678],"image_id_list":["img-aaa","img-bbb"],"binding_type":"LABEL_BINDING_TYPE_ADD"}'
```

覆盖绑定（清空标签原有的视频关联，重新设置）：

```bash
node scripts/bind-material-labels.mjs '{"account_id":"123456789","label_id_list":[1234],"media_id_list":["video-001"],"binding_type":"LABEL_BINDING_TYPE_OVERWRITE","business_scenario":"BUSINESS_SCENARIO_DELIVERY"}'
```

删除绑定（解除某些素材与标签的关联关系，不影响标签下的其它素材）：

```bash
node scripts/bind-material-labels.mjs '{"account_id":"123456789","label_id_list":[1234],"image_id_list":["img-bbb"],"binding_type":"LABEL_BINDING_TYPE_DELETE"}'
```

## 5. 在广告组创建脚本中绑定 (material_package_id)

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

<!-- script add-material-labels → scripts/add-material-labels.mjs (injected at build time) -->

<!-- script update-material-labels → scripts/update-material-labels.mjs (injected at build time) -->

<!-- script bind-material-labels → scripts/bind-material-labels.mjs (injected at build time) -->
