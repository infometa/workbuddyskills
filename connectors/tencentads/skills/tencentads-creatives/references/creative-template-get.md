# 获取创意形式详情 (creative_template/get)


## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID，不支持代理商ID |
| marketing_goal | enum | 营销目的类型 |
| marketing_target_type | enum | 推广产品类型 |
| marketing_carrier_type | enum | 营销载体类型 |
| delivery_mode | enum | 投放模式（`DELIVERY_MODE_COMPONENT` / `DELIVERY_MODE_CUSTOMIZE`） |

> **脚本层说明**：`get-creative-templates.mjs` 脚本封装了该接口，传入 `adgroup_id` 后内部会自动获取广告组的四元组，无需手动传入。

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| adgroup_id | int64 | 广告组ID |
| marketing_sub_goal | enum | 二级营销目的 |
| automatic_site_enabled | boolean | 是否开启智能版位 |
| site_set | enum[] | 投放站点集合（1-32个元素） |
| dynamic_creative_type | enum | 动态创意类型 |
| creative_template_id | integer | 指定创意形式ID（填写时返回该形式的详细配置） |
| use_new_version | boolean | 是否使用新版本（影响响应中 `creative_permissions` 字段是否返回） |
| adgroup_type | enum | 广告类型 |

## 响应核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| data.list[].creative_template_id | integer | 创意形式ID |
| data.list[].creative_components[] | struct[] | 该创意形式下的组件列表及填写规范 |
| data.list[].creative_components[].component_type | enum | 组件类型 |
| data.list[].creative_components[].required | boolean | 是否必填 |
| data.list[].creative_components[].has_depend | boolean | 是否有字段联动约束，`true` 时需调用 `component_depends/get` |
| data.list[].creative_permissions | struct | 创意权限详情（新版本返回） |
