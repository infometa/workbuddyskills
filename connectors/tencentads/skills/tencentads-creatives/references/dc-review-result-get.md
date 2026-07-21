# 查询创意审核详情 (dc_review_result/get)

## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |
| dynamic_creative_id_list | int64[] | 动态创意ID列表 |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| need_return_has_violation_reason_interpretation | boolean | 是否返回违规原因解读入口标志，默认 true |

---

## 响应字段说明

### list 顶层字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `adgroup_id` | int64 | 广告组ID |
| `total_component_compose_count` | integer | 该创意下组件生成的组合总数 |
| `reject_component_compose_count` | integer | 因特殊审核场景驳回原因未打在具体组件上的组合数 |
| `is_all_component_compose_pending` | boolean | 该创意下组件组合是否全部待审中 |
| `delay_message_list` | string[] | 组件审核受阻提示信息列表 |
| `element_result_list` | struct[] | 组件元素审核结果列表，见下方说明 |
| `reject_component_compose_info_list` | struct[] | 组件组合驳回详情列表（特殊审核场景），见下方说明 |

### element_result_list 元素审核结果

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `element_id` | int64 | 元素ID |
| `element_name` | string | 元素名称 |
| `element_type` | enum | 元素类型，见下方枚举值 |
| `element_value` | string | 元素内容（文本/图片URL/视频URL等） |
| `element_fingerprint` | string | 元素指纹（唯一标识） |
| `review_status` | enum | 元素审核状态，见下方枚举值 |
| `component_info` | struct | 元素所属组件信息，若为创意级元素则为空 |
| `element_reject_detail_info` | struct[] | 元素驳回详情列表 |

### component_info 组件信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `component_id` | int64 | 组件ID（0 表示创意级元素，不属于具体组件） |
| `component_type` | string | 组件类型（如 `video`、`brand`、`description` 等） |
| `component_type_name` | string | 组件类型中文名称 |
| `review_status` | enum | 组件审核状态 |
| `creative_asset_id` | int64 | 创意资产ID（大于0时优先展示，否则展示 component_id） |

### element_reject_detail_info 元素驳回详情

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `reason` | string | 驳回原因文案 |
| `has_violation_reason_interpretation` | boolean | 是否支持违规原因解读 |
| `review_policy_id` | string | 审核策略ID |
| `site_set_list` | struct[] | 影响的版位列表，含 `site_set`（版位ID）和 `site_set_name`（版位名称） |
| `reject_info_location` | struct[] | 违规位置信息（图片/视频定位框），含 `x`、`y`、`width`、`height`、`img_url`、`time_second` |
| `video_asr_infos` | struct[] | 视频违规口播信息，含 `text`（口播文本）、`start_time`、`end_time`（秒） |
| `caption_infos` | struct[] | 视频违规段落信息，含 `start_time`、`end_time`（秒） |

### reject_component_compose_info_list 组件组合驳回详情

> 特殊审核场景下，驳回原因未能定位到具体组件，打在"不指定组件"上，此处列出对应的组合信息。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `reject_message` | string | 组合驳回原因文案 |
| `component_compose_element_list` | int64[] | 该组合包含的元素ID列表 |
