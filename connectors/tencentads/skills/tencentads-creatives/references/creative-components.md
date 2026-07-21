# creative_components 组件参考

本文档描述 `dynamic_creatives/add` 和 `dynamic_creatives/update` 接口中 `creative_components` 字段的格式规则与各组件详解。

---

## creative_components 格式规则

键名为组件类型，值**必须是数组**：

- 已有组件：`[{ "component_id": 123456 }]`
- 内联内容：`[{ "value": {内容字段} }]`（**必须用 value 包裹**）
- 多个同类：`[{ "component_id": A }, { "value": {...} }]`
- `component_id` 与 `value` 同时传入时，**以 `value` 为准**

```json
// ✅ 正确
"brand": [{ "component_id": 1895897993168 }]
"description": [{ "value": { "content": "广告文案" } }]

// ❌ 错误 - value 未包裹
"wechat_channels": [{ "username": "v2_xxx@finder" }]

// ❌ 错误 - 值不是数组
"brand": { "component_id": 1895897993168 }
```

### 常用组件类型（视频号投放）

实际可用组件以 `get-creative-templates.mjs` 输出为准。字段是否必填取决于具体创意形式配置，请查询 `get-creative-templates.mjs` 获取准确的字段要求。

| 组件类型 | 中文名 | 说明 |
|---------|--------|------|
| `video` | 视频 | 视频组件 |
| `image` | 单图 | 单图组件，每张图一个独立条目 |
| `image_list` | 多图轮播、图集 | 多图轮播组件，一个条目含多张图 |
| `image_showcase` | 图片展示位 | 橱窗图片（复合组件，含主图+图片列表） |
| `video_showcase` | 视频展示位 | 橱窗视频（复合组件，含视频+图片列表） |
| `description` | 描述、文案 | 描述文案组件 |
| `title` | 标题 | 标题组件 |
| `wechat_channels` | 视频号信息 | 视频号主页（视频号投放场景） |
| `video_channels_content` | 视频号主页视频 | 视频号主页视频组件 |
| `action_button` | 行动按钮 | 行动按钮组件 |
| `chosen_button` | 选择按钮 | 双选择按钮组件 |
| `main_jump_info` | 主跳转 | 主跳转落地页（常规组件化创意使用） |
| `jump_info` | 落地页 | 独立落地页组件（部分创意形式使用，如激励浏览） |
| `floating_zone` | 浮层卡片 | 浮层卡片组件 |
| `floating_zone_list` | 多卡轮播 | 浮层卡片列表（多卡轮播） |
| `brand` | 品牌形象 | 品牌形象组件 |
| `mini_card_link` | 图文链接 | 图文链接组件 |
| `show_data` | 数据外显 | 数据外显组件 |
| `social_skill` | 首评回复 | 首评回复组件 |
| `label` | 标签 | 标签组件 |
| `shop_image` | 卖点图、店铺图 | 卖点图组件 |
| `count_down` | 倒计时 | 倒计时组件 |
| `app_gift_pack_code` | 礼包码 | 礼包码组件 |
| `marketing_pendant` | 营销挂件 | 营销挂件组件 |
| `text_link` | 文字链 | 文字链组件 |
| `end_page` | 结束页 | 视频结束页组件 |
| `consult` | 咨询 | 咨询组件 |
| `phone` | 电话 | 电话组件 |
| `form` | 表单 | 表单组件 |
| `barrage` | 弹幕 | 弹幕组件 |
| `audio` | 音频 | 音频组件 |
| `short_video` | 短视频 | 短视频组件（视频号相关） |
| `element_story` | 集装箱创意组合 | 集装箱创意组合组件 |
| `wxgame_playable_page` | 试玩页 | 试玩页组件（小游戏） |
| `wxgame_direct_page` | 小游戏直玩 | 小游戏直玩组件 |
| `custom_barrage` | 自定义弹幕 | 自定义弹幕组件 |
| `living_desc` | 轮播文案 | 轮播文案组件（直播类） |
| `app_promotion_video` | OTT视频 | OTT视频组件（TV端） |

> **注**：
> - `jump_info` vs `main_jump_info`：**以 `get-creative-templates.mjs` 输出的组件名为准**，不可互换。激励浏览等特定创意形式使用 `jump_info` 作为独立组件键；常规组件化创意使用 `main_jump_info`。错误使用会导致 API 报 1000207 错误。
> - *`show_data` 的 `conversion_data_type`、`conversion_target_type` 枚举值**必须从 `component_depends/get` 返回的 `target_options[].support_options[].value` 中取**，不可自行猜测或使用旧经验中的枚举名。例如正确值为 `CONVERSION_DATA_ADMETRIC`，而非 `CONVERSION_DATA_TYPE_CONVERSION`。
> - *`username`：视频号主页链接，格式 `v2_xxxxx@finder`
> - **`live_promoted_type`：视频号直播投放时**强烈推荐**，但必须作为**顶层参数**（与 `creative_components` 同级）传入，❌ 禁止写入 `wechat_channels.value`。值：`LIVE_PROMOTED_TYPE_NATIVE_VIDEO` | `LIVE_PROMOTED_TYPE_SHORT_VIDEO` 等官方 enum
> - ⚠️ **官方 API 不支持以下字段**（即使在其他平台见过也不要填）：
>   - video 的 `width`、`height`、`sub_type`（只支持 `video_id` + 可选的 `cover_id`）
>   - 任何组件的 `image_id` 作为 cover（应用 `cover_id`）
> - `image` vs `image_list`：完全根据模板约束（`get-creative-templates.mjs` 输出的 `min`/`max`/`required`）和用户意图判断。若模板中只有 `image`（无 `image_list`），多个图片 ID 各自作为独立 `image` 条目；若两者都有，看用户提供的图片数量是否满足 `image_list` 的 `min_occurs`——不满足则只能用 `image`；满足时以用户意图为准（明确说"多图组件"用 `image_list`，否则用独立 `image` 条目）
> - `mini_card_link` 字段名是 `mini_card_link_description`/`mini_card_link_image`/`mini_card_link_button_text`，**不是** `card_description`/`card_image_id`/`card_button_text`
> - `show_data` 字段名是 `conversion_data_type`/`conversion_target_type`，**不是** `show_data_type`/`show_data_desc`

---

## image_showcase / video_showcase 组件

复合展示位，`value` 内嵌套两个子字段（`image`/`video` + `image_list`），**不能拆成独立的 `image`/`video` + `image_list` 分别传**。

```json
"image_showcase": [{
  "value": {
    "image": {
      "image_id": "35155852356",
      "jump_info": { "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 3767098217 } } }
    },
    "image_list": {
      "list": [{ "image_id": "35155852357" }, { "image_id": "35155852358" }],
      "jump_info": { "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 3767098217 } } }
    }
  }
}]

"video_showcase": [{
  "value": {
    "video": {
      "video_id": "35155852356",
      "cover_id": "35155852593",
      "jump_info": { "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 3767098217 } } }
    },
    "image_list": {
      "list": [{ "image_id": "35155852357" }, { "image_id": "35155852358" }],
      "jump_info": { "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 3767098217 } } }
    }
  }
}]

// 或通过 component_id 引用
"image_showcase": [{ "component_id": 1905866436402 }]
"video_showcase": [{ "component_id": 1905866436403 }]
```

- `image`/`video`（必填）：主图/主视频
- `image_list`（必填）：配图列表，`list[]` 每项含 `image_id`；`jump_info` 可选（配图共用跳转）

---

---

## Video 组件

```json
"video": [{ "value": { "video_id": "35155852356", "cover_id": "35155852593" } }]
```

**字段说明**：
- `video_id`（string，必填）：视频 ID
- `cover_id`（string，可选）：封面图片 ID，脚本会自动查询补全

---

## Image 组件

```json
"image": [{ "value": { "image_id": "35155852356" } }]
```

**字段说明**：
- `image_id`（string，必填）：图片 ID

---

## Image List 组件

```json
"image_list": [{
  "value": {
    "list": [
      { "image_id": "35155852356" },
      { "image_id": "35155852357" }
    ]
  }
}]
```

**字段说明**：
- `list`（array，必填）：图片列表，每项含 `image_id`

---

## Description 组件

```json
"description": [{ "value": { "content": "广告文案内容" } }]
```

**字段说明**：
- `content`（string，必填）：文案内容

---

## Brand 组件

`brand` 组件**不同投放场景格式完全不同**，**不可混用**：

### 1️⃣ 视频号投放场景
```json
{
  "value": {
    "jump_info": {
      "page_type": "PAGE_TYPE_WECHAT_CHANNELS_PROFILE",
      "page_spec": {
        "wechat_channels_profile_spec": {
          "username": "v2_060000...@finder"
        }
      }
    }
  }
}
```
**必填**: `jump_info` 包装 + `page_type` + `page_spec` + `wechat_channels_profile_spec`

### 2️⃣ 小游戏投放场景
```json
{
  "value": {
    "brand_name": "品牌名",
    "brand_image_id": "image_id"
  }
}
```
**必填**: `brand_name` + `brand_image_id`

### 3️⃣ H5 / 官方页投放场景
```json
{
  "value": {
    "jump_info": {
      "page_type": "PAGE_TYPE_H5_PROFILE",
      "page_spec": {
        "h5_profile_spec": {
          "page_id": 123456
        }
      }
    }
  }
}
```
**必填**: `jump_info` 包装 + `page_type` + `page_spec` + `h5_profile_spec`

---

## Action Button 组件（行动按钮）

`action_button` 组件定义广告的行动按钮，包含按钮文案和跳转落地页。

```json
"action_button": [{
  "value": {
    "button_text": "立即下载",
    "jump_info": {
      "page_type": "PAGE_TYPE_APP_MARKET",
      "page_spec": {
        "android_market_spec": { "app_id": "2000019090" }
      }
    }
  }
}]
```

**字段说明**：
- `button_text`（string，必填）：按钮文案
- `jump_info`（object，可选）：跳转落地页（`page_type` + `page_spec`），若省略则与 `main_jump_info` 共享落地页。`page_type → page_spec` 完整映射见 [enums.md](enums.md)

---

## Main Jump Info 组件（主跳转落地页）

`main_jump_info` 定义创意的主落地页跳转信息。value 结构直接是 jump_info 字段（不需要额外的 `jump_info` 包裹层）。

```json
"main_jump_info": [{
  "value": {
    "page_type": "PAGE_TYPE_OFFICIAL",
    "page_spec": {
      "official_spec": { "page_id": 3767098217 }
    }
  }
}]
```

**字段说明**：
- `page_type`（enum，必填）：落地页类型，如 `PAGE_TYPE_OFFICIAL`、`PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE`、`PAGE_TYPE_WECHAT_MINI_GAME` 等
- `page_spec`（object，必填）：与 `page_type` 对应的规格对象，完整映射见 [enums.md](enums.md)
- `mini_game_tracking_parameter`（string，可选）：仅小游戏落地页（`PAGE_TYPE_WECHAT_MINI_GAME`）时使用

---

## Wechat Channels 组件

`wechat_channels` 组件表示视频号账号，**视频号投放场景必填**。`username` 由脚本自动推断，无需手动填写。

### 基础格式
```json
{
  "value": {
    "username": "v2_060000231003b20faec8c4e...@finder"
  }
}
```

### 携带账号 ID（当 input 的 brand 字段中提供了 `wechat_channels_account_id` 时）
```json
{
  "value": {
    "username": "v2_060000231003b20faec8c4e...@finder",
    "wechat_channels_account_id": "export/UzFfAg...",
    "finder_object_visibility": false
  }
}
```

**字段说明**：
- `wechat_channels_account_id`：若 input 的 brand 字段中包含此字段，将其**原样复制**到 `wechat_channels` 的 value 中
- `finder_object_visibility`：仅在 `wechat_channels_account_id` 存在时附加，默认值为 `false`

### 视频号直播投放（含直播推广类型）
```json
{
  "value": {
    "username": "v2_060000231003b20faec8c4e...@finder",
    "live_promoted_type": "LIVE_PROMOTED_TYPE_SHORT_VIDEO"
  }
}
```

> ⚠️ `live_promoted_type` 应作为顶层参数（与 `creative_components` 同级）传入，❌ 禁止写入 `wechat_channels.value`。此处仅说明该字段的格式，实际传参位置在顶层。

**字段说明**：
- `username`：视频号账号，格式 `v2_xxxxx@finder`（完整字符串格式，不是数字ID）
- 官方可用 `live_promoted_type` 值：
  - `LIVE_PROMOTED_TYPE_NATIVE_VIDEO` - 原生视频直播推广
  - `LIVE_PROMOTED_TYPE_SHORT_VIDEO` - 短视频直播推广

---

## Social Skill 组件（首评回复）

`social_skill` 用于在广告投放后自动发布一条首条评论，提升广告互动效果。

```json
{
  "value": {
    "social_skill_first_comment_switch": true,
    "social_skill_first_comment": "限时体验，快来试试！"
  }
}
```

字段说明：
- `social_skill_first_comment_switch`（bool，必填）：是否开启首评，`true` 为开启
- `social_skill_first_comment`（string，可选）：首条评论文案，最多 30 字，支持最多 1 个 emoji；仅当 `switch=true` 时有意义

> 关闭首评时只需传 `social_skill_first_comment_switch: false`，无需传文案字段。

---

## Label 组件（标签）

`label` 组件的 `list` 字段是**对象数组**，每个元素必须包含 `content`（标签文案）和 `type`（标签类型枚举）：

```json
{
  "value": {
    "list": [
      { "content": "一站式检查", "type": "LABEL_TYPE_CUSTOMIZETEXT", "display_content": "显示内容" },
      { "content": "专家讲解", "type": "LABEL_TYPE_CUSTOMIZETEXT" }
    ]
  }
}
```

> ❌ 错误 — `list` 不能是字符串数组：
> ```json
> { "value": { "list": ["一站式检查", "专家讲解", "备孕指导"] } }
> ```

**字段说明**：
- `list`（array）：标签列表
  - `content`（string）：标签内容
  - `type`（enum）：标签类型，常用 `LABEL_TYPE_CUSTOMIZETEXT`（自定义文字）、`LABEL_TYPE_COMMON`（通用标签）
  - `display_content`（string）：标签显示内容，最大 100 字节

---

## Wxgame Playable Page 组件（小游戏试玩页）

`wxgame_playable_page` 组件用于小游戏投放场景，指定广告关联的试玩页。

```json
{
  "value": {
    "wxgame_playable_page_path": "playable@wx7a727ff7d940bb3f@CBgAA8J0ky4CRht8-5K6IzerReVCtw6k",
    "wxgame_playable_page_end_cover_img": "35640929877",
    "wxgame_playable_page_end_desc": "微信与 QQ 的共生支持"
  }
}
```

**字段说明**：
- `wxgame_playable_page_path`（string，必填）：试玩页路径标识，格式为 `playable@{appid}@{hash}`。取值来源于 `wx_game_playable_page/get` 接口返回的 `data.list[].playable_page_path`，**只能使用 `status = PLAYABLE_PAGE_STATUS_ONLINE` 的试玩页**。试玩页名称对应 `nick_name` 字段（非 `playable_page_name`）。
- `wxgame_playable_page_end_cover_img`（string，可选）：结束页封面图片 ID
- `wxgame_playable_page_end_desc`（string，可选）：结束页文案

**查询试玩页列表**：

```bash
node scripts/get-playable-pages.mjs '{"account_id":"78139785","app_id":"wx4bde5ea0aa8c8968"}'
```

- 取 `status = PLAYABLE_PAGE_STATUS_ONLINE` 的条目，使用其 `playable_page_path` 字段
- 试玩页游戏名称对应 `nick_name` 字段，页面名称对应 `playable_page_name` 字段
- 若用户未指定具体试玩页，默认取列表中第一个已上线的条目
- 若列表为空或无已上线条目，告知用户该小游戏暂无可用试玩页

---

## Show Data 组件（数据外显）

`show_data` 用于展示广告转化数据，`conversion_data_type` 和 `conversion_target_type` 的**合法枚举值由 `component_depends/get` 接口动态返回**，必须使用 `support_options[].value` 中的值，不可凭经验猜测。

```json
{
  "value": {
    "conversion_data_type": "CONVERSION_DATA_ADMETRIC",
    "conversion_target_type": "CONVERSION_TARGET_GET"
  }
}
```

**获取合法值的步骤**：
1. 调用 `get-component-depends.mjs`，传入 `component_type: "SHOW_DATA"`
2. 在返回的 `component_depends[].target_options[]` 中，找到与当前广告组其他组件值匹配的 `depends` 条件
3. 取对应的 `support_options[].value` 作为该字段的枚举值

---

## Floating Zone 组件（浮层卡片）

### 用 component_id（推荐）
```json
{ "component_id": 1895897993171 }
```

### 内联格式
```json
{
  "value": {
    "floating_zone_switch": true,
    "floating_zone_image_id": "image_id",
    "floating_zone_name": "卡片标题",
    "floating_zone_desc": "卡片描述",
    "floating_zone_button_text": "按钮文案",
    "floating_zone_type": "FLOATING_ZONE_TYPE_IMAGE_TEXT",
    "floating_zone_single_image_id": "image_id_2",
    "button_base_text": "基础文案"
  }
}
```
**必填**: `floating_zone_switch`（true/false，脚本层自动补全，AI 无需填写）

**字段说明**：
- `floating_zone_switch`（boolean）：浮层卡片开关
- `floating_zone_image_id`（string）：图片 ID，尺寸 512*512，不超过 50KB
- `floating_zone_name`（string）：文案一，最大 10 等宽字符
- `floating_zone_desc`（string）：文案二，最大 14 等宽字符
- `floating_zone_button_text`（string）：按钮文案，最大 10 等宽字符
- `floating_zone_type`（enum）：浮层卡片类型
- `floating_zone_single_image_id`（string）：单图 ID，尺寸 482*270
- `button_base_text`（string）：视频号基础态文案，最大 10 字节

---

## Floating Zone List 组件（多卡轮播）

`floating_zone_list` 是多卡轮播组件，与 `floating_zone` 互斥（两者只能选其一）。

### 用 component_id（推荐）
```json
{ "floating_zone_list": [{ "component_id": 1895897993172 }] }
```

### 内联格式
```json
{
  "floating_zone_list": [{
    "value": {
      "list": [
        {
          "floating_zone_image_id": "image_id_1",
          "floating_zone_name": "卡片标题1",
          "floating_zone_desc": "卡片描述1",
          "floating_zone_button_text": "按钮文案1"
        },
        {
          "floating_zone_image_id": "image_id_2",
          "floating_zone_name": "卡片标题2",
          "floating_zone_desc": "卡片描述2",
          "floating_zone_button_text": "按钮文案2"
        }
      ],
      "floating_zone_type": "FLOATING_ZONE_TYPE_SLIDER_CARD"
    }
  }]
}
```

---

## Video Channels Content 组件（视频号主页视频）

`video_channels_content` 用于展示视频号主页视频内容。

```json
{
  "video_channels_content": [{
    "value": {
      "video_id": "35155852356",
      "cover_id": "35155852593",
      "ad_export_id": "export/xxx",
      "wechat_channels_account_id": "v2_xxx@finder",
      "jump_info": {
        "page_type": "PAGE_TYPE_WECHAT_CHANNELS_PROFILE",
        "page_spec": {
          "wechat_channels_profile_spec": {
            "username": "v2_xxx@finder"
          }
        }
      }
    }
  }]
}
```

**字段说明**：
- `video_id`（string，必填）：视频 ID
- `cover_id`（string，可选）：封面图 ID
- `ad_export_id`（string，可选）：视频号推广对象 ID，脚本会自动补全
- `wechat_channels_account_id`（string，可选）：视频号账号 ID（v2_xxx@finder 格式，来自 wechat_channels_accounts/get）
- `mini_game_tracking_parameter`（string，可选）：小游戏监控参数
- `jump_info`（object，可选）：跳转信息

---

## Chosen Button 组件（选择按钮）

`chosen_button` 是双选择按钮组件，包含左右两个按钮。

```json
{
  "chosen_button": [{
    "value": {
      "left_button": {
        "text": "按钮A文案",
        "jump_info": {
          "page_type": "PAGE_TYPE_OFFICIAL",
          "page_spec": {
            "official_spec": { "page_id": 123456 }
          }
        }
      },
      "right_button": {
        "text": "按钮B文案",
        "jump_info": {
          "page_type": "PAGE_TYPE_OFFICIAL",
          "page_spec": {
            "official_spec": { "page_id": 123456 }
          }
        }
      }
    }
  }]
}
```

**字段说明**：
- `left_button`（object，必填）：左侧按钮配置
- `right_button`（object，必填）：右侧按钮配置
- 每个按钮包含 `text`（按钮文案）和 `jump_info`（跳转信息）

---

## Marketing Pendant 组件（营销挂件）

`marketing_pendant` 是营销挂件组件，可显示在广告创意上。

```json
{
  "marketing_pendant": [{
    "value": {
      "image_id": "35155852356",
      "jump_info": {
        "page_type": "PAGE_TYPE_OFFICIAL",
        "page_spec": {
          "official_spec": { "page_id": 123456 }
        }
      }
    }
  }]
}
```

**字段说明**：
- `image_id`（string，必填）：挂件图片 ID
- `jump_info`（object，可选）：挂件的跳转链接

---

## Short Video 组件（短视频）

`short_video` 是短视频组件，支持传入 1-2 个视频。

```json
{
  "short_video": [{
    "value": {
      "short_video1": "35155852356",
      "short_video2": "35155852357"
    }
  }]
}
```

**字段说明**：
- `short_video1`（string）：视频 ID，通过 videos 模块上传视频后获得
- `short_video2`（string）：视频 ID，可选

---

## Element Story 组件（集装箱创意组合）

`element_story` 是集装箱创意组合组件，包含图片、描述、标题、链接的组合列表。

```json
{
  "element_story": [{
    "value": {
      "list": [
        {
          "image": "35155852356",
          "image2": "35155852357",
          "description": "广告描述文案",
          "title": "广告标题",
          "url": "https://example.com/page1"
        },
        {
          "image": "35155852358",
          "description": "第二条广告描述",
          "title": "第二条标题",
          "url": "https://example.com/page2"
        }
      ]
    }
  }]
}
```

**字段说明**：
- `list`（array）：集装箱创意组合列表，最少 1 条，最多 14 条
- `list[].image`（string，必填）：图片 ID
- `list[].image2`（string）：第二张图片 ID，可选
- `list[].description`（string，必填）：广告描述
- `list[].title`（string，必填）：广告标题
- `list[].url`（string，必填）：跳转链接

---

## App Promotion Video 组件（OTT视频）

`app_promotion_video` 是 OTT 视频组件，用于 TV 端投放，支持二维码配置。

```json
{
  "app_promotion_video": [{
    "value": {
      "video": "35155852356",
      "video2": "35155852357",
      "video3": "35155852358",
      "allow_tv_qrcode": true,
      "qrcode_position": {
        "position_x": "100",
        "position_y": "200",
        "qrcode_width": 150
      }
    }
  }]
}
```

**字段说明**：
- `video` / `video2` / `video3`（string）：视频 ID，最多支持 3 个视频
- `allow_tv_qrcode`（boolean）：是否支持 TV 二维码
- `qrcode_position`（object）：二维码坐标信息
  - `position_x` / `position_y`（string）：X/Y 坐标
  - `qrcode_width`（integer）：二维码边长

---

## Title 组件（标题）

`title` 是标题组件，用于显示广告标题。

```json
{
  "title": [{ "value": { "content": "广告标题文案" } }]
}
```

**字段说明**：
- `content`（string）：标题文本，长度限制需通过创意形式详情接口获取

---

## Consult 组件（咨询）

`consult` 是咨询组件，用于配置咨询功能。

```json
{
  "consult": [{
    "value": {
      "id": 123456,
      "jump_info_list": [{
        "page_type": "PAGE_TYPE_OFFICIAL",
        "page_spec": { "official_spec": { "page_id": 123456 } }
      }]
    }
  }]
}
```

**字段说明**：
- `id`（integer）：咨询组件值
- `jump_info_list`（array）：兜底落地页内容列表

---

## Phone 组件（电话）

`phone` 是电话组件，用于配置电话拨打功能。

```json
{
  "phone": [{ "value": { "id": 123456 } }]
}
```

**字段说明**：
- `id`（integer）：电话组件值

---

## Form 组件（表单）

`form` 是表单组件，用于配置表单收集功能。

```json
{
  "form": [{ "value": { "id": 123456 } }]
}
```

**字段说明**：
- `id`（integer）：表单组件值

---

## Text Link 组件（文字链）

`text_link` 是文字链组件，用于显示可点击的文字链接。

```json
{
  "text_link": [{
    "value": {
      "link_name_type": "LINK_NAME_TYPE_DEFAULT",
      "link_name_text": "查看详情",
      "jump_info": {
        "page_type": "PAGE_TYPE_OFFICIAL",
        "page_spec": { "official_spec": { "page_id": 123456 } }
      }
    }
  }]
}
```

**字段说明**：
- `link_name_type`（enum）：链接名称类型
- `link_name_text`（string）：文字链文案
- `jump_info`（object）：落地页内容结构

---

## Barrage 组件（弹幕）

`barrage` 是弹幕组件，用于显示弹幕评论。

```json
{
  "barrage": [{
    "value": {
      "list": [
        { "id": "1", "text": "弹幕内容1" },
        { "id": "2", "text": "弹幕内容2" }
      ]
    }
  }]
}
```

**字段说明**：
- `list`（array）：弹幕列表
  - `id`（string）：弹幕 ID
  - `text`（string）：弹幕文本

---

## End Page 组件（结束页）

`end_page` 是视频结束页组件，用于配置视频播放结束后的展示内容。

```json
{
  "end_page": [{
    "value": {
      "end_page_type": "END_PAGE_TYPE_DEFAULT",
      "end_page_desc": "结束页描述文案"
    }
  }]
}
```

**字段说明**：
- `end_page_type`（enum）：结束页类型
- `end_page_desc`（string）：结束页描述

---

## Living Desc 组件（轮播文案）

`living_desc` 是轮播文案组件，用于直播类广告展示轮播文字。

```json
{
  "living_desc": [{
    "value": {
      "living_desc_switch": true,
      "desc_list": ["文案1", "文案2", "文案3"]
    }
  }]
}
```

**字段说明**：
- `living_desc_switch`（boolean）：轮播文案开关
- `desc_list`（array）：文案列表

---

## Wxgame Direct Page 组件（小游戏直玩）

`wxgame_direct_page` 是小游戏直玩组件，用于配置小游戏直玩功能。

```json
{
  "wxgame_direct_page": [{
    "value": {
      "wxgame_direct_page_description": "直玩页面描述"
    }
  }]
}
```

**字段说明**：
- `wxgame_direct_page_description`（string）：小游戏直玩页面描述

---

## Custom Barrage 组件（自定义弹幕）

`custom_barrage` 是自定义弹幕组件，用于配置自定义弹幕内容。

```json
{
  "custom_barrage": [{
    "value": {
      "text_list": ["自定义弹幕1", "自定义弹幕2"]
    }
  }]
}
```

**字段说明**：
- `text_list`（array）：自定义弹幕文本列表

---

## Audio 组件（音频）

`audio` 是音频组件，用于配置广告背景音乐。

```json
{
  "audio": [{ "value": { "audio_id": "audio_123456" } }]
}
```

**字段说明**：
- `audio_id`（string）：音频 ID

