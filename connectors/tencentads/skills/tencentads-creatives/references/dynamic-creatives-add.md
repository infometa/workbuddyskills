# 创建创意 (dynamic_creatives/add)


## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID，不支持代理商ID |
| adgroup_id | int64 | 广告组ID |
| dynamic_creative_name | string | 创意名称，同账号下不重复，最大60等宽字符（1个中文=1个等宽字符，1个英文=0.5个等宽字符） |
| creative_components | struct | 创意组件内容（见下方说明） |

### 可选参数（创意类型）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| dynamic_creative_type | enum | 指定创意形式 → `DYNAMIC_CREATIVE_TYPE_COMMON`；不指定（程序化）→ `DYNAMIC_CREATIVE_TYPE_PROGRAM` |
| creative_template_id | integer | 指定创意形式时填对应 ID；不指定时填 `0` |

> **联动规则**：两个字段必须配套填写，勿省略。

### 可选参数（状态控制）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| configured_status | enum | 客户设置的广告状态。可选值：`AD_STATUS_NORMAL`（有效）、`AD_STATUS_SUSPEND`（暂停） |

> **用户明确指定状态时**：如用户说"客户设置状态：有效"或"状态：暂停"，必须将对应枚举值传入 `configured_status` 字段。

### 可选参数（程序化创意）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| auto_derived_program_creative_switch | boolean | 自动衍生程序化创意开关，`true` 表示开启自动衍生 |
| program_creative_info | struct | 【当前不支持】程序化创意信息，需根据当前选中的素材动态生成 |

> **注意**：`program_creative_info` 需要根据当前选中的素材动态生成，目前暂不支持此功能。如需使用程序化创意，请先开启 `auto_derived_program_creative_switch`，`program_creative_info` 将由系统自动处理。

### 可选参数（版位与跟踪）

| 参数名 | 类型 | 说明 |
|--------|------|------|
| site_set_validate_model | enum | 版位校验模式，可选值：`SITE_SET_VALIDATE_MODEL_STRICT`（严格模式） |
| page_track_url | string | 页面级转化跟踪 URL，用于整页级的转化数据跟踪 |

> **注意**：`page_track_url` 长度上限 **1024 字符**（超出时 `build-creative-params.mjs` 会在 `errors` 中报错）。

---

## creative_components 格式规则与组件详解

见 [creative-components.md](creative-components.md)。

---

## 监测链接

`impression_tracking_url` 和 `click_tracking_url` 是顶层参数（与 `creative_components` 同级），用于接入第三方监测平台。

**是否可用**：由 `creative_template/get` 返回的 `creative_permissions` 字段决定：
- `support_impression_tracking_url: true` — 该创意形式支持曝光监测链接
- `support_click_tracking_url: true` — 该创意形式支持点击监测链接

`get-creative-templates.mjs` 仅在值为 `true` 时输出对应字段，未出现则不支持。

**处理规则**：
- 模板支持且用户提供了链接 → 作为顶层参数传入 `build-creative-params.mjs` 和 `create-creative.mjs`
- 用户未提供或模板不支持 → **不填此字段**（传空字符串或省略均可）
- 链接长度上限：**1024 字符**（超出时 `build-creative-params.mjs` 会在 `errors` 中报错）

**示例**（含监测链接的请求参数）：

```json
{
  "account_id": 123456789,
  "adgroup_id": 987654321,
  "impression_tracking_url": "https://example.miaozhen.com/r/k=xxx&t=imp",
  "click_tracking_url": "https://example.miaozhen.com/r/k=xxx&t=clk",
  "creative_components": {
    "video": [{ "component_id": 1905866436402 }]
  }
}
```

---

## 请求示例

```json
{
  "account_id": 123456789,
  "adgroup_id": 987654321,
  "dynamic_creative_name": "创意_视频号_0324",
  "creative_components": {
    "video":           [{ "component_id": 1905866436402 }],
    "brand":           [{ "component_id": 1895897993168 }],
    "description":     [
      { "component_id": 1905249050464 },
      { "value": { "content": "限时优惠，立即了解" } }
    ],
    "action_button":   [{ "component_id": 1895897993170 }],
    "main_jump_info":  [{ "component_id": 1906127499786 }],
    "wechat_channels": [{ "value": { "username": "v2_060000231003b2@finder" } }],
    "floating_zone":   [{ "component_id": 1895897993171 }]
  }
}
```

## 响应参数

| 字段名 | 类型 | 说明 |
|--------|------|------|
| code | integer | 0 表示成功 |
| data.dynamic_creative_id | int64 | 新创建的创意ID |

## 常见错误

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| 40001 | 参数缺失或格式错误 | 检查 `creative_components` 结构是否完整 |
| 40006 | `adgroup_id` 不存在 | 确认广告组ID是否正确 |
| 45000 | 同广告组下有并发操作 | 等待上一操作完成后再重试 |
| 45010 | 素材ID无效 | 检查 `image_id`/`video_id` 是否存在且属于当前账户 |
