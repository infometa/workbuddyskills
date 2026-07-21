# 获取创意形式列表 (creative_template_list/get)


**使用场景**：当用户指定了 `creative_template_id` 时，须先调用此接口验证该 ID 是否在可用列表中。若不在列表中，应拦截并告知用户，不可继续使用该 ID 创建创意。

## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| marketing_goal | enum | 营销目的类型 |
| marketing_sub_goal | enum | 二级营销目的类型 |
| marketing_target_type | enum | 推广产品类型 |
| marketing_carrier_type | enum | 营销载体类型 |
| site_set | enum | 投放版位 |
| dynamic_ability_type | enum | 动态广告投放能力类型 |
| adgroup_id | int64 | 广告ID（填写后返回该广告适用的创意形式） |
| mpa_spec | struct | 动态商品广告属性 |
| support_site_set | enum[] | 可投放版位集合 |
| page | integer | 页码（默认1，最大99999） |
| page_size | integer | 每页条数（默认10，最大100） |

## 响应核心字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| data.list[].creative_template_id | integer | 创意形式ID |
| data.list[].creative_template_style | string | 创意形式类型 |
| data.list[].creative_template_appellation | string | 创意形式名称 |
| data.list[].creative_sample_image | string | 创意形式示意图链接 |
| data.list[].support_bid_mode_list | enum[] | 支持的出价方式 |
| data.page_info.total_number | integer | 总条数 |
| data.page_info.total_page | integer | 总页数 |
