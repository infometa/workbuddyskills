# 查询组件字段依赖 (component_depends/get)


## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID，不支持代理商ID |
| marketing_goal | enum | 营销目的类型 |
| marketing_target_type | enum | 推广产品类型 |
| marketing_carrier_type | enum | 营销载体类型 |
| delivery_mode | enum | 投放模式（`DELIVERY_MODE_COMPONENT` / `DELIVERY_MODE_CUSTOMIZE`） |

> **脚本层说明**：`get-component-depends.mjs` 脚本封装了该接口，传入 `adgroup_id` 后内部会自动获取广告组的四元组，无需手动传入。

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| adgroup_id | int64 | 广告组ID |
| marketing_sub_goal | enum | 二级营销目的 |
| automatic_site_enabled | boolean | 是否开启智能版位 |
| site_set | enum[] | 投放站点集合（1-32个元素） |
| dynamic_creative_type | enum | 动态创意类型 |
| creative_template_id | integer | 创意形式ID |
| component_type | enum | 创意组件类型（指定后只返回该组件的依赖） |

## 响应核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| data[].component_type | enum | 创意组件类型 |
| data[].component_name | string | 创意组件名称 |
| data[].component_depends[].target_path | string | 当前组件的字段路径 |
| data[].component_depends[].depend_paths | string[] | 该字段依赖的其他组件字段路径列表 |
| data[].component_depends[].target_options[].depends | object[] | 触发该选项的依赖条件（`path` + `value` 的组合） |
| data[].component_depends[].target_options[].support_options | object[] | 当满足 `depends` 条件时，该字段的**合法枚举值列表**（`value` + `desc`） |

> **重要**：`support_options[].value` 是唯一合法的枚举值来源，必须直接使用，不可替换为其他枚举名。
> 例如 `show_data.conversion_data_type` 的合法值可能是 `CONVERSION_DATA_ADMETRIC`，而非 `CONVERSION_DATA_TYPE_CONVERSION`。
