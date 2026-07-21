# 更新创意 (dynamic_creatives/update)


## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID，不支持代理商ID |
| dynamic_creative_id | int64 | 要更新的创意ID |

### 可更新字段（至少填写一个）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dynamic_creative_name | string | 创意名称，同账号下不重复，最大60等宽字符（1个中文=1个等宽字符，1个英文=0.5个等宽字符） |
| creative_components | struct | 创意组件内容（**全量覆盖**，格式规则见 [creative-components.md](creative-components.md)） |

> **重要**：`creative_components` 为**全量覆盖**，缺失的组件将被清除。`component_id` 与 `value` 同时传入时，以 `value` 为准。各组件格式详见 [creative-components.md](creative-components.md)。

---

## 请求示例

```json
{
  "account_id": 123456789,
  "dynamic_creative_id": 111222333,
  "dynamic_creative_name": "更新后的创意名称_0324",
  "creative_components": {
    "video":           [{ "component_id": 1905866436402 }],
    "brand":           [{ "component_id": 1895897993168 }],
    "description":     [{ "value": { "content": "更新后的广告文案，点击了解更多" } }],
    "action_button":   [{ "component_id": 1895897993170 }],
    "main_jump_info":  [{ "component_id": 1906127499786 }],
    "wechat_channels": [{ "value": { "username": "v2_060000231003b2@finder" } }]
  }
}
```

## 响应参数

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 0 表示成功 |
| data.dynamic_creative_id | int64 | 被更新的创意ID |

## 常见错误

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| 40001 | 参数缺失或格式错误 | 检查 `creative_components` 结构是否完整 |
| 40006 | `dynamic_creative_id` 不存在 | 确认创意ID是否正确 |
| 45000 | 同广告组下有并发操作 | 等待上一操作完成后再重试（串行执行） |
| 45010 | 素材ID无效 | 检查 `image_id`/`video_id` 是否存在且属于当前账户 |
