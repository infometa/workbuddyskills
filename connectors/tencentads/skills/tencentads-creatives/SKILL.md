---
name: tencentads-creatives
description: 腾讯营销（原腾讯广告）展示广告管理 - 创意管理。用于管理动态创意(dynamic_creatives)和创意形式(creative_template)，以及素材标签（material_labels）。当用户需要创建或管理广告创意（含组件字段填写/审核详情）、或管理素材标签（素材标签查询、新建、更新和素材绑定）时使用此技能。排除搜索创意(search_dynamic_creatives)。
license: MIT. See LICENSE for full terms.
compatibility: any
metadata:
  author: DeliveryX Team
  version: "0.5.9"
  icon: megaphone
  category: tencent-ads
---

# 腾讯广告 - 创意管理

> **前置依赖**：需安装 `tencentads-cli`（Node.js ≥ 20）。执行 `npm install -g tencentads-cli@latest` 安装或升级；版本过低时 `tencentads` 会给出提示。

管理腾讯广告展示广告的动态创意（组件化创意）。

> **重要提示**: 本技能基于腾讯广告营销 API（api.e.qq.com）API **v3.0 展示广告**接口。
> - **以本文档和官方文档为准**: 字段名称、参数结构可能与旧版或其他广告平台不同，请勿依赖旧经验。
> - **串行执行约束**: 同一广告组下，创意的新建、更新和删除操作必须**串行执行**，不可并发。
> - **禁止修改用户意图**: 用户明确指定的参数值必须原样传递，严禁静默修改或忽略。若用户要求的参数值脚本不支持，必须**明确报错告知用户**，不得擅自使用默认值替代。

### ⚠️ 跨平台 JSON 参数传递规则（经实测验证）

脚本调用格式为 `node scripts/<脚本名>.mjs '<JSON参数>'`，但 **JSON 参数的引号包裹方式因操作系统/终端而异**，传递不当会导致 `JSON.parse` 报错（如 `Expected property name or '}' in JSON at position 1`）。

| 终端环境 | 正确写法 | 说明 |
|---------|---------|------|
| **Linux / macOS (Bash/Zsh)** | `node scripts/xxx.mjs '{"key":"value"}'` | ✅ 单引号包裹，内部双引号原样保留 |
| **Windows Git Bash** | `node scripts/xxx.mjs '{"key":"value"}'` | ✅ 同 Bash |
| **Windows CMD** | `node scripts/xxx.mjs "{\"key\":\"value\"}"` | ✅ 双引号包裹 + 反斜杠转义 |
| **Windows CMD (备选)** | `node scripts/xxx.mjs "{""key"":""value""}"` | ✅ 双引号包裹 + 双双引号转义 |
| **Windows PowerShell 5.x** | `node --% scripts/xxx.mjs "{\"key\":\"value\"}"` | ✅ 必须加 `--%` 停止解析符 |
| **Windows PowerShell 5.x (备选)** | `` node scripts/xxx.mjs "{\`"key\`":\`"value\`"}" `` | ✅ 反斜杠 + 反引号组合转义 |

> **⛔ PowerShell 5.x 是重灾区**：单引号 `'...'`、反引号 `` `" `` 、反斜杠 `\"` 三种常见写法**全部失败**（双引号会被吞掉）。必须使用 `--% ` 停止解析符或 `` \`" `` 组合转义。
> **⛔ Windows CMD 不支持单引号包裹字符串**，单引号会被当作普通字符传入脚本，导致 JSON 解析失败。

---

## 脚本列表

| 脚本 | 功能 | 必填参数 | 可选参数 |
|------|------|---------|---------|
| `scripts/create-creative.mjs` | 创建动态创意（自动校验必填字段及创意数量上限，须先调用 build-creative-params.mjs 完成参数预处理） | account_id, adgroup_id, creative_components | - |
| `scripts/update-creative.mjs` | 更新动态创意 | account_id, dynamic_creative_id | creative_components |
| `scripts/delete-creative.mjs` | 删除动态创意 | account_id, dynamic_creative_id | - |
| `scripts/get-component-list.mjs` | 按组件子类型查询账户下可用组件列表 | account_id, component_sub_types | - |
| `scripts/get-components.mjs` | 查询组件库（按类型拉取可用组件列表） | account_id, component_type | - |
| `scripts/get-creative-templates.mjs` | 查询可用创意形式，输出组件摘要 | account_id, adgroup_id | creative_template_id, dynamic_creative_type, delivery_mode, live_promoted_type |
| `scripts/get-creative-template-list.mjs` | 查询可用创意形式列表（含 live_promoted_type_list） | account_id | adgroup_id |
| `scripts/get-component-depends.mjs` | 查询组件字段联动约束，输出依赖摘要（含合法枚举值） | account_id, adgroup_id, component_type | creative_template_id, dynamic_creative_type, delivery_mode, live_promoted_type |
| `scripts/query-adgroup-context.mjs` | 查询广告组上下文（marketing_asset_outer_spec 等） | account_id, adgroup_id | - |
| `scripts/get-creative.mjs` | 查询动态创意详情（含 creative_components 完整结构） | account_id, dynamic_creative_id | fields |
| `scripts/build-creative-params.mjs` | 构建并校验创意请求参数（不发起创建，输出 params+warnings+errors） | account_id, adgroup_id, creative_components | adgroup_context, creative_template_id, live_promoted_type, impression_tracking_url, click_tracking_url |
| `scripts/get-playable-pages.mjs` | 查询小游戏试玩页列表，获取 `playable_page_path` | account_id, app_id | - |
| `scripts/get-project-assets.mjs` | 查询全店托管商品列表（获取 marketing_asset_id） | account_id, project_id（广告组ID） | - |
| `scripts/upload-image.mjs` | 上传图片到素材库（jpg/png/gif，≤10MB），返回 image_id | account_id, file_path | description, image_usage |
| `scripts/get-images.mjs` | 查询素材库图片列表（按 ID 确认素材存在/查详情） | account_id | filtering, page, page_size |
| `scripts/upload-video-svp.mjs` | 上传视频到素材库（SVP分片上传，支持大文件、断点续传） | account_id, file_path | description, concurrent, chunk_size, timeout |
| `scripts/get-videos.mjs` | 查询素材库视频列表（按 ID 确认/查转码状态 system_status） | account_id | filtering, page, page_size |
| `scripts/get-integrated-components.mjs` | 组件模式查询素材（含报表排序、起量潜力/首发/低质筛选） | account_id, component_sub_types | sort_field, sort_type, date_range, fuzzy_name, potential_status, first_publication_status, quality_status, generation_type, page, page_size, organization_id |
| `scripts/get-integrated-media.mjs` | 素材库模式查询单图/视频（含可用性过滤、报表排序、多维筛选） | account_id, type | sort, sort_type, date_range, create_range, ratios, ratio_valids, fuzzy_name, label_id, similarity_status, quality_status, first_publication_status, generation_type, duration, watermark, page, page_size, organization_id |
| `scripts/get-audios.mjs` | 查询妙思版权音频列表 | account_id | fields, page, page_size |
| `scripts/get-dc-review-result.mjs` | 查询动态创意审核详情（含组件/元素审核结果、驳回原因、组件组合审核信息） | account_id, dynamic_creative_id | need_return_has_violation_reason_interpretation |
| `scripts/dynamic-product-templates/get-dynamic-ad-image-templates.mjs` | 查询动态商品图片模版列表（MPA/DPA），返回可选模版 | account_id, product_catalog_id, product_mode, dynamic_ad_template_width, dynamic_ad_template_height | dynamic_ad_template_ownership_type, template_id_list, template_name |
| `scripts/dynamic-product-templates/generate-dynamic-ad-image.mjs` | 从商品图片模版生成图片，返回 image_id | account_id, product_catalog_id, product_mode, product_source, dynamic_ad_template_id, dynamic_ad_template_size | remove_template_id |
| `scripts/dynamic-product-templates/get-dynamic-ad-video-templates.mjs` | 查询动态商品视频模版列表（MPA/DPA），返回可选模版 | account_id, product_catalog_id, adcreative_template_id, product_mode | support_channel, template_id_list, template_name |
| `scripts/dynamic-product-templates/generate-dynamic-ad-video.mjs` | 从商品视频模版生成视频，返回 video_id | account_id, product_catalog_id, product_mode, product_source, dynamic_ad_template_id | - |
| `scripts/get-material-labels.mjs` | 查询账号下素材标签列表（图片/视频标签） | account_id 或 organization_id | label_id, label_name, business_scenario, page, page_size, need_count 等 |
| `scripts/add-material-labels.mjs` | 批量新建素材标签（一/二级类目、业务场景） | account_id 或 organization_id, labels | - |
| `scripts/update-material-labels.mjs` | 更新单个素材标签的名称或一/二级类目 | account_id 或 organization_id, label_id, label_name | first_label_level_name, second_label_level_name |
| `scripts/bind-material-labels.mjs` | 把图片/视频素材与标签建立绑定关系（覆盖/新增/解除） | account_id 或 organization_id, label_id_list, image_id_list 或 media_id_list 至少一个 | binding_type, business_scenario |

---

## 工作流零：素材准备（可选）

若用户**已有 `image_id` / `video_id` / `component_id`**，直接跳到工作流一。

当用户需要上传新素材或查找现有素材时，按以下方式操作。

### 上传新素材

```bash
# 上传图片
node scripts/upload-image.mjs '{"account_id":"123456789","file_path":"/tmp/banner.jpg"}'

# 上传视频
node scripts/upload-video-svp.mjs '{"account_id":"123456789","file_path":"/tmp/ad.mp4"}'
```

返回 `image_id` / `video_id`。**视频上传后需转码**，可用 `get-videos.mjs` 轮询 `system_status` 确认转码完成（`MEDIA_STATUS_VALID`）后再创建创意。

**文件格式限制**：图片 jpg/png/gif（≤10MB，GIF ≤5秒）；视频 mp4/mov/avi（≤100MB，微信广告需 Progressive 扫描）。

**详细接口规范**：[素材接口文档](references/materials/)

### 查询已有素材

提供两种查询方式，根据用户需求选择：

#### 方式一：素材库模式查询（推荐）

按素材粒度查询单图/视频，支持可用性过滤（比例+宽高+时长）、报表排序、标签/首发/相似度等筛选。

```bash
# 查询 16:9 可用视频，按消耗排序
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"VIDEO","sort":"cost","ratios":["16:9"],"ratio_valids":[{"ratio":"16:9","file_size_kb_limit":102400,"min_width":1280,"min_height":720,"min_duration":6,"max_duration":900}]}'

# 按名称模糊搜索图片
node scripts/get-integrated-media.mjs '{"account_id":"123456789","type":"IMAGE","fuzzy_name":"产品主图"}'
```

**详细参数说明**：[integrated-media-get.md](references/integrated-media-get.md)

#### 方式二：组件模式查询（用于选择已有组件）

按组件粒度查询，支持按消耗/曝光/ROI 排序，支持起量潜力/首发/低质等筛选。返回 `component_id` 可直接用于 `creative_components`。

```bash
# 查询视频组件，按消耗排序
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["VIDEO_16X9","VIDEO_9X16"],"sort_field":"report.cost","sort_type":"DESCENDING"}'

# 查询高潜图片组件
node scripts/get-integrated-components.mjs '{"account_id":"123456789","component_sub_types":["IMAGE_16X9"],"potential_status":["COMMON_POTENTIAL_STATUS_HIGH"]}'
```

**详细参数说明**：[integrated-components-get.md](references/integrated-components-get.md)

### 查询妙思版权音频

```bash
node scripts/get-audios.mjs '{"account_id":"123456789"}'
```

---

## 工作流零B：商品模版生成素材（可选）

当需要使用商品库素材时，可通过商品模版生成图片或视频。此流程是**独立的素材生产流程**，与广告组类型无关——只要账户有可用的 `product_catalog_id` 即可使用，生成的 `image_id` / `video_id` 是**通用素材资产**，可用于**任意广告组**的创意。

> **判断标识**：`get-creative-templates.mjs` 输出中若包含 `support_mpa_image_template: true`，则图片组件支持商品模版；`support_mpa_video_template: true`，则视频组件支持商品模版。

> **MPA 广告组约束**：若广告组为 MPA 模式（`mpa_spec` 非空），则该广告组的 image/video 组件**只能**通过商品模版生成，不支持本地上传素材。此约束仅适用于 MPA 广告组内部，不影响商品模版功能本身的使用范围。

### 参数来源

| 参数 | 来源 | 说明 |
|------|------|------|
| `product_catalog_id` | `adgroup.product_spec.product_catalog_id`（广告组字段）或用户已知的商品库 ID | 商品库ID |
| `product_source` | `mpa_spec.product_series_id`（优先）或 `marketing_asset_outer_spec.marketing_asset_outer_sub_id` | 商品系列/单品来源ID |
| `product_mode` | MPA 广告组（`mpa_spec` 非空）→ `MULTIPLE`；其他情况 → `SINGLE` | 动态广告模式 |
| `dynamic_ad_template_width/height` | `get-creative-templates` 输出中 image 组件的尺寸（如 sub_types 中的 width/height） | 图片尺寸要求 |
| `dynamic_ad_template_size` | 格式: `SIZE_{width}_{height}`（如 `SIZE_1280_720`） | 图片生成尺寸枚举 |

### 图片模版流程

1. 从 `get-creative-templates.mjs` 输出中确认 `support_mpa_image_template: true`，并获取 image 组件的尺寸要求
2. 查询可用图片模版：
   ```bash
   node scripts/dynamic-product-templates/get-dynamic-ad-image-templates.mjs '{"account_id":"123","product_catalog_id":456,"product_mode":"MULTIPLE","dynamic_ad_template_width":1280,"dynamic_ad_template_height":720}'
   ```
3. 展示模版列表供用户选择（或仅有一个时自动选中）
4. 用户选择模版后，生成图片：
   ```bash
   node scripts/dynamic-product-templates/generate-dynamic-ad-image.mjs '{"account_id":"123","product_catalog_id":456,"product_mode":"MULTIPLE","product_source":"789","dynamic_ad_template_id":12345,"dynamic_ad_template_size":"SIZE_1280_720"}'
   ```
5. 返回的 `image_id` 用于 `creative_components` 中 image/image_list 等组件

### 视频模版流程

1. 从 `get-creative-templates.mjs` 输出中确认 `support_mpa_video_template: true`
2. 查询可用视频模版（需传入创意形式 `template_id`）：
   ```bash
   node scripts/dynamic-product-templates/get-dynamic-ad-video-templates.mjs '{"account_id":"123","product_catalog_id":456,"adcreative_template_id":720,"product_mode":"MULTIPLE"}'
   ```
3. 展示模版列表供用户选择
4. 用户选择模版后，生成视频：
   ```bash
   node scripts/dynamic-product-templates/generate-dynamic-ad-video.mjs '{"account_id":"123","product_catalog_id":456,"product_mode":"MULTIPLE","product_source":"789","dynamic_ad_template_id":67890}'
   ```
5. 返回的 `video_id` 用于 `creative_components` 中 video 组件（`video_preview_image_id` 可作为 `cover_id`）

> **注意**：
> - 生成的 `image_id` / `video_id` 后续流程与普通素材完全一致——传入 `creative_components` 对应组件的 value 即可
> - 若 `product_source` 为空（`mpa_spec.product_series_id` 和 `marketing_asset_outer_sub_id` 均无值），需传 `0`

**详细接口规范**：[动态商品模版接口文档](references/dynamic-ad-templates.md)

---

## 工作流一：创建创意

### 第一步：确认 adgroup_id 并查询广告组上下文

`adgroup_id` 必须由用户提供，或在上下文中已知。

**每次创建创意前，必须先查询广告组上下文**，帮助理解广告组的信息：

```bash
node scripts/query-adgroup-context.mjs '{"account_id":"123456789","adgroup_id":987654321}'
```

### 第二步：查询创意形式及组件联动约束

**始终执行以下命令**获取可用创意形式列表（含 `live_promoted_type_list`）：

```bash
node scripts/get-creative-template-list.mjs '{"account_id":"123456789","adgroup_id":987654321}'
```

**live_promoted_type 填写规则**（`live_promoted_type_list` 来自上述命令输出）：

- 若 `live_promoted_type_list` 不为空 → 必须填写 `live_promoted_type`（顶层参数，与 `creative_components` 同级）：
  - 默认填 `LIVE_PROMOTED_TYPE_SHORT_VIDEO`（落地页为视频号直播间、视频号主页等均用此值）
  - 仅当用户**明确要求"直播实时画面"**（推广内容本身是直播流）时 → 填 `LIVE_PROMOTED_TYPE_NATIVE_VIDEO`
  - ⚠️ 注意：落地页类型是 `PAGE_TYPE_WECHAT_CHANNELS_WATCH_LIVE` **不代表** `NATIVE_VIDEO`，仍填 `SHORT_VIDEO`
- 若 `live_promoted_type_list` 为空/null → **不填此字段**

若用户指定了 `creative_template_id`，须确认该 ID 在上述返回列表中，不在则拦截并告知用户。若使用默认（`template_id=0`，不指定创意形式），则跳过此验证。

始终执行以下命令获取组件列表摘要（若用户未指定 `creative_template_id`，默认使用 `template_id=0`，不指定创意形式，`required=false` 的可选组件默认不加）：

> **⚠️ 可选组件规则**：`required=false` 的组件（如浮层 `floating_zone`/`floating_zone_list`、标签 `label`、社交互动 `social_skill`、数据外显 `show_data` 等）**未经用户许可禁止自行构建和添加**。仅在用户明确要求该组件时才加入。

```bash
node scripts/get-creative-templates.mjs '{"account_id":"123456789","adgroup_id":987654321}'
```

对结果中所有 `has_depend=true` 的组件，逐一调用以下命令查询联动约束：

```bash
node scripts/get-component-depends.mjs '{"account_id":"123456789","adgroup_id":987654321,"component_type":"WECHAT_CHANNELS"}'
```

若 `depends` 为空数组，说明该组件无联动约束，可直接填写。**若命令返回失败或 Mock not found，忽略该错误，直接跳到第三步继续。**

#### 监测链接（impression_tracking_url / click_tracking_url）

若 `get-creative-templates.mjs` 输出包含 `support_impression_tracking_url: true` 或 `support_click_tracking_url: true`，说明该创意形式支持第三方监测链接，用户提供时将其作为顶层参数传入后续脚本。详见 [dynamic-creatives-add.md](references/dynamic-creatives-add.md#监测链接)。

#### 小游戏落地页监测链接（mini_game_tracking_parameter）

**与上方顶层监测链接不同**，`mini_game_tracking_parameter` 是小游戏落地页（`PAGE_TYPE_WECHAT_MINI_GAME`）专属字段，位于 `wechat_mini_game_spec` 内部。用户描述落地页时若提供了"监测链接"（如 `?state=xxx`、`?gameplay_concept=1`），必须将其填入对应 jump_info 的 `page_spec.wechat_mini_game_spec.mini_game_tracking_parameter`。

- 适用组件：`main_jump_info`、`action_button`、`text_link`、`mini_card_link` 等所有包含小游戏落地页的 jump_info
- 同一广告下所有小游戏落地页的 `mini_game_tracking_parameter` 应保持一致（使用用户提供的值）

> **关键**：`component_depends/get` 响应中，`target_options[].support_options[].value` 是该字段**唯一合法的枚举值**，必须直接使用，不可凭经验填写其他枚举名。例如 `show_data.conversion_data_type` 的值只能取 `support_options` 中列出的（如 `CONVERSION_DATA_ADMETRIC`），而非 `CONVERSION_DATA_TYPE_CONVERSION` 等臆测值。

### 第三步：通过组件库获取 component_id

第二步的摘要输出中，每个组件包含 `sub_types` 字段（如 `["BRAND"]`、`["VIDEO_16X9","VIDEO_9X16",...]`）。如用户未提供 `component_id`，调用以下命令按组件子类型查询账户下可用组件：

```bash
node scripts/get-component-list.mjs '{"account_id":"123456789","component_sub_types":["BRAND"]}'
```

- `component_sub_types` 填对应组件的 `sub_types` 值，同类型有多个 sub_type 时**一次性全部传入**（如 `["BRAND","BRAND_WECHAT_CHANNEL"]`），**不要拆开多次调用**
- **list 为空时**：说明 `integrated_list` 无数据，改用 `get-components.mjs` fallback 查询：
  ```bash
  node scripts/get-components.mjs '{"account_id":"123456789","component_type":"BRAND"}'
  ```
  若仍为空，才告知用户该类型组件不存在。
- **查询失败时（返回错误或 Mock not found）**：**立即跳过，不重试，不换参数重试**。已成功获取其他组件的 component_id 时，直接用已有数据继续执行创意创建；若所有必填组件均无法获取，才告知用户。
- **严禁用 `0`、`null`、`-1` 等无效值占位 component_id**：查询失败的组件条目**整体省略**，不填虚假 ID。
- **video 组件查询失败时**：绝对不可生成 `[{}]`（空对象数组）——这会让 API 收到无效的空视频条目。查询失败时直接**整体省略** video，或告知用户提供视频 ID。
- **`image_showcase` / `video_showcase` 是复合展示位**，`value` 内嵌套 `image/video` + `image_list`，不能拆成独立组件分别传入。详见 [references/creative-components.md](references/creative-components.md#image_showcase--video_showcase-组件)

#### 通用选择规则（适用于所有组件类型）

获取到组件列表后，按以下规则决策，**严禁随机取第一个**：

1. **用户已明确指定**（提供了名称、ID 或描述）→ 从列表中匹配，使用用户指定的
2. **列表只有一个可用** → 直接使用，无需确认
3. **列表有多个，但用户意图可唯一确定**（如视频号场景下只有一个 `wechat_channels` 型 brand）→ 直接使用
4. **列表有多个，无法从上下文确定** → **询问用户**，列出名称（`component_custom_name`）让用户选择，**不可自行决定**

若用户提供了 `component_id` 但查询结果中不存在该 ID，应立即告知用户，不可继续使用该 ID 创建。

#### brand 组件的类型过滤

`get-component-list.mjs` 返回的 brand 条目含 `brand_type` 字段，是第3条"意图可唯一确定"判断的依据：

| brand_type | 含义 | 适用场景 |
|---|---|---|
| `common` | 普通品牌形象（brand_name + brand_image_id） | 小游戏、APP 等非视频号场景 |
| `wechat_channels` | 视频号品牌形象（含视频号 jump_info） | 视频号投放场景 |
| `h5_profile` | 品牌简介（H5 主页） | H5 场景 |
| `search_brand` | 搜一搜超级品专 | 搜索场景 |
| `wechat_official` | 公众号品牌形象 | 公众号场景 |
| `wecom` | 企业微信 | 企业微信场景 |

先按当前投放场景过滤出匹配 `brand_type` 的组件，再套用上方通用规则。过滤后为空时，告知用户当前场景下无对应类型品牌组件，询问如何处理。

#### wechat_channels 自动推断

`wechat_channels` 组件（视频号账号）**完全由脚本自动处理，禁止 Agent 在 `creative_components` 中传入 `wechat_channels` 键**。脚本会按以下路径自动推断：

1. **广告组上下文**（优先）：自动调用 `adgroups/get` 获取 `marketing_asset_outer_spec.marketing_asset_outer_id`（`v2_xxx@finder` 格式）；也可通过 `adgroup_context` 参数传入
2. **`brand` inline value**：若 brand 以 inline value 传入且 `jump_info.page_type == PAGE_TYPE_WECHAT_CHANNELS_PROFILE`，从 `wechat_channels_profile_spec.username` 提取
3. **`brand` 携带 `wechat_channels_username`** 临时字段：直接使用
4. 以上均无时，调用 `wechat_channels_accounts/get` 获取账号列表，自动选择（多账号时先结合 video_id 过滤，再结合名称匹配消歧）

> **多账号消歧**：当用户在品牌组件中指定了视频号名称（如"视频号profile页（视频号名称: A+肖像摄影门店）"），Agent 应在 brand 的 inline value 中携带 `wechat_channels_account_name` 临时字段，脚本会用它在多个可用账号中精确匹配。

> **⚠️ 禁止手动填写以下字段**（全部由脚本自动处理）：
> - `wechat_channels` 组件本身：❌ **不要在 `creative_components` 中包含 `wechat_channels` 键**，脚本自动生成
> - `wechat_channels_account_id`（`export/xxx` 格式）：脚本自动从 brand profile_spec 或 API 获取并补全
> - `finder_object_visibility`：脚本根据是否存在 `export/` 账号自动决定是否添加
> - `live_promoted_type`：顶层参数（与 `creative_components` 同级），❌ 禁止写入 `wechat_channels.value`

### 第四步A：构建参数并预校验

组装好 `creative_components` 后，先调用 `build-creative-params.mjs` 进行预处理和校验（**不发起创建**）：

```bash
node scripts/build-creative-params.mjs '{
  "account_id": "123456789",
  "adgroup_id": 987654321,
  "live_promoted_type": "LIVE_PROMOTED_TYPE_SHORT_VIDEO",
  "creative_components": {
    "video":         [{ "component_id": 1905866436402 }],
    "brand":         [{ "component_id": 1895897993168 }],
    "description":   [{ "value": { "content": "限时优惠，立即了解" } }],
    "action_button": [{ "value": { "button_text": "查看详情", "jump_info": { "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 3767098217 } } } } }],
    "main_jump_info":[{ "value": { "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 3767098217 } } } }]
  }
}'
```

**处理输出结果**：

- `errors` 非空 → 参数有问题，逐项修正后重调此脚本，不得直接进入创建步骤
- `warnings` 非空 → 向用户说明，确认后继续（如自动补全失败、cover_id 未查到等）
- `errors` 为空 → 继续第四步B，将 `params` 直接传给 `create-creative.mjs`

> **字段传递规则**：
>
> | 字段 | 用户未指定时 | 用户明确指定时 | 说明 |
> |------|-------------|---------------|------|
> | `delivery_mode` | 脚本默认 `DELIVERY_MODE_COMPONENT` | **必须传入用户指定的值**（如`DELIVERY_MODE_CUSTOMIZE`） | 用户说"自定义创意"→传`CUSTOMIZE`，"组件化创意"或不提→不传 |
> | `dynamic_creative_type` | 根据`creative_template_id`自动推断（0→`PROGRAM`，>0→`COMMON`） | **必须传入用户指定的值**（如`DYNAMIC_CREATIVE_TYPE_PROGRAM`） | 用户说"自动匹配"/"程序化"→传`PROGRAM`，"指定创意形式"→传`COMMON` |
> | `dynamic_creative_name` | 脚本自动生成 | 传入用户提供的名称 | 未提供时不传，由脚本生成 |
> | `wechat_channels` | 脚本自动推断 | **禁止 Agent 传入**，由脚本处理 | 无论从 brand 还是广告组上下文推断 |
> | `video.cover_id` | 自动查询补全 | 传入用户指定的 cover_id | 未提供时脚本自动查询 |
> | `impression_tracking_url` / `click_tracking_url` | 不传 | 原样透传用户提供的值 | 校验长度不超过 1024 字符 |
> | `smart_delivery_spec` | 脚本自动从广告组获取 | 传入用户选择的商品 ID | 全店托管场景必填 |
> | `configured_status` | 不传（由系统默认） | **必须传入用户指定的值** | 用户说"状态：有效"→传`AD_STATUS_NORMAL`，"状态：暂停"→传`AD_STATUS_SUSPEND` |
> | `auto_derived_program_creative_switch` | 不传 | 传入用户指定的开关值 | `true` 开启自动衍生 |
> | `program_creative_info` | 【不支持】 | 【当前不支持】**传入会报错** | 需根据素材动态生成，暂不支持用户传入 |
> | `site_set_validate_model` | 不传 | 传入用户指定的校验模式 | 如 `SITE_SET_VALIDATE_MODEL_STRICT` |
> | `page_track_url` | 不传 | 原样透传用户提供的值 | 校验长度不超过 1024 字符 |
>
> **关键原则**：用户明确指定了参数值（如"投放模式：自定义创意"、"动态创意类型：自动匹配"），Agent **必须**将该值传入 `build-creative-params.mjs`，不要依赖脚本默认值。

### 第四步B：发起创建

> **创意数量上限**：每个广告组下最多创建 **100** 个创意（仅自定义创意允许 1000）。`create-creative.mjs` 在发起创建前会自动查询已有创意数量，超限时拦截并返回错误，无需 Agent 额外处理。若用户遇到上限提示，应引导其先删除部分已有创意后重试。

将第四步A输出的 `params` 直接传入 `create-creative.mjs`：

```bash
node scripts/create-creative.mjs '<第四步A输出的 params JSON>'
```

> **⚠️ 文案含引号时**：改用 heredoc 方式（引号无需转义）：
>
> ```bash
> node scripts/create-creative.mjs <<'EOF'
> {
>   "account_id": "123456789",
>   "adgroup_id": 987654321,
>   "creative_components": {
>     "description": [{ "value": { "content": "别再夸"聪明"，要夸这一点" } }]
>   }
> }
> EOF
> ```

**组件 value 字段填写原则**：
- 内联 value 时，**严格按用户为该组件明确提供的信息填写**，不得从其他组件的参数推断/复制字段
- 只传用户明确指定的字段，多余字段即使看似合理也应省略
- 组件可用字段以 `get-creative-templates` 输出的 `fields` 为准，未在 `fields` 中列出的字段不得填写
- **中文名到字段名映射**：用户用中文描述组件（如"多卡轮播"、"卖点图"）时，在 [creative-components.md 的「常用组件类型」表格](references/creative-components.md#常用组件类型视频号投放) 中根据「中文名」查找对应的「组件类型」（即字段名）

**jump_info 嵌套结构说明**：

所有包含跳转链接的组件（`action_button`, `brand`, `mini_card_link` 等）的 `jump_info` 字段采用 `page_type` + `page_spec.<spec名>` 嵌套结构，**不能平铺**。

- ✅ 正确：`{ "page_type": "PAGE_TYPE_OFFICIAL", "page_spec": { "official_spec": { "page_id": 123 } } }`

`page_type → page_spec` 完整映射（含每种 page_type 的 page_spec 结构示例）见 [references/enums.md](references/enums.md)。

`creative_components` 格式规则及各组件详解见 [references/creative-components.md](references/creative-components.md)。

**dynamic_creative_name 命名规则**：
- 用户明确提供了创意名称 → 传入该名称
- 用户未提供 → **无需传入**，脚本自动生成含北京时间时间戳的默认名

**返回（成功）**: `{ "success": true, "dynamic_creative_id": 8362490722 }`

**接口详情见**: [references/dynamic-creatives-add.md](references/dynamic-creatives-add.md)

---

## 工作流二：更新创意

### 第一步：获取创意当前完整信息

`dynamic_creative_id` 必须由用户提供，或在上下文中已知。

**无论用户描述了哪些组件，都必须先调用以下命令查询创意当前状态**：

```bash
node scripts/get-creative.mjs '{"account_id":"123456789","dynamic_creative_id":111222333}'
```

返回的 `creative.creative_components` 即为当前完整结构，更新时须以此为基础修改（全量覆盖）。用户只描述了要改哪些组件，其余组件必须从此处获取后原样保留。

### 第二步：更新

> **注意**：`creative_components` 为**全量覆盖**，需基于第一步获取的完整结构修改，不可只传要变更的部分。

**如何从 GET 结果构造更新参数**：

GET 接口返回的每个组件格式为 `{ "component_id": xxx, "value": {...}, "is_deleted": false }`。

传给 update 接口时，规则如下：

1. **未更改的组件**：保留 `component_id` 和 `is_deleted` 字段，**去掉 `value`**，原样传入
2. **需要用组件库中已有组件替换的**：传 `{ "component_id": 新ID }`（无 `is_deleted`）
3. **需要用全新参数（inline value）更新的组件**：用 `{ "value": {...} }` 格式传入
4. **`jump_info` 字段**：GET 返回中可能包含 `jump_info` 顶层组件，**不要将其传入 update**，跳转信息已包含在 `main_jump_info` 中

```bash
node scripts/update-creative.mjs '{
  "account_id": "123456789",
  "dynamic_creative_id": 111222333,
  "creative_components": {
    "video":         [{ "component_id": 1905866436402 }],
    "brand":         [{ "component_id": 1895897993168 }],
    "description":   [{ "component_id": 1895897993169 }],
    "action_button": [{ "value": { "button_text": "立即咨询", "jump_info": { "page_type": "PAGE_TYPE_WECHAT_CONSULT", "page_spec": { "wechat_consult_spec": { "page_url": "https://work.weixin.qq.com/xxx" } } } } }],
    "main_jump_info": [{ "component_id": 1906127499786 }]
  }
}'
```

**返回（成功）**: `{ "success": true, "dynamic_creative_id": 111222333 }`

**接口详情见**: [references/dynamic-creatives-update.md](references/dynamic-creatives-update.md)

---

## 其他操作（删除）

### 删除创意

> **串行执行**：同一广告组下创意的新建、更新、删除不可并发。

```bash
node scripts/delete-creative.mjs '{
  "account_id": "123456789",
  "dynamic_creative_id": 111222333
}'
```

**接口详情见**: [references/dynamic-creatives-delete.md](references/dynamic-creatives-delete.md)

---

## 工作流三：素材标签管理

素材标签（material_labels）用于把一组图片/视频素材聚合成"标签包"，便于素材组织与检索。本 skill 提供 **查询 / 新建 / 更新 / 绑定** 4 个标签接口。

| 用户意图 | 推荐脚本 |
|---------|---------|
| 查询账号/业务单元下的素材标签列表（含每个标签的素材数量） | `scripts/get-material-labels.mjs` |
| 批量新建素材标签（可指定一/二级类目与业务场景） | `scripts/add-material-labels.mjs` |
| 修改单个标签的名称或一/二级类目 | `scripts/update-material-labels.mjs` |
| 把图片/视频素材绑定到标签上（覆盖 / 新增 / 解除三种 `binding_type`） | `scripts/bind-material-labels.mjs` |

> 调用示例、参数 schema、字段约束、枚举值、错误码处理详见 [references/material-labels.md](references/material-labels.md)。

---

## 接口文档索引

| 接口 | 文档 | 说明 |
|------|------|------|
| dynamic_creatives/add | [dynamic-creatives-add.md](references/dynamic-creatives-add.md) | 完整请求参数、枚举值 |
| dynamic_creatives/get | [dynamic-creatives-get.md](references/dynamic-creatives-get.md) | 查询创意详情（get-creative.mjs 使用） |
| creative_components 组件详解 | [creative-components.md](references/creative-components.md) | 格式规则及各组件字段说明 |
| 枚举值完整参考 | [enums.md](references/enums.md) | 创意组件枚举（delivery_mode/page_type/show_data/floating_zone/label 等）+ 素材枚举（source_type/system_status/image_usage/aigc_flag 等） |
| dynamic_creatives/update | [dynamic-creatives-update.md](references/dynamic-creatives-update.md) | 可更新字段、示例 |
| dynamic_creatives/delete | [dynamic-creatives-delete.md](references/dynamic-creatives-delete.md) | 必填参数 |
| creative_template/get | [creative-template-get.md](references/creative-template-get.md) | 查询可用创意形式及组件配置（get-creative-templates.mjs 使用） |
| creative_template_list/get | [creative-template-list-get.md](references/creative-template-list-get.md) | 验证用户指定的 creative_template_id 是否在可用列表中 |
| component_depends/get | [component-depends-get.md](references/component-depends-get.md) | 查询组件字段联动约束（get-component-depends.mjs 使用） |
| images/add | [materials/images-add.md](references/materials/images-add.md) | 上传图片（upload-image.mjs 使用） |
| images/get | [materials/images-get.md](references/materials/images-get.md) | 查询图片列表（get-images.mjs 使用） |
| videos/add | [materials/videos-add.md](references/materials/videos-add.md) | 上传视频（upload-video.mjs 使用） |
| videos/get | [materials/videos-get.md](references/materials/videos-get.md) | 查询视频列表（get-videos.mjs 使用） |
| integrated_list_multiaccount/get | [integrated-components-get.md](references/integrated-components-get.md) | 组件模式查询素材（get-integrated-components.mjs 使用），含报表排序、起量潜力/首发/低质筛选 |
| integrated_image_list/get & integrated_media_list/get | [integrated-media-get.md](references/integrated-media-get.md) | 素材库模式查询单图/视频（get-integrated-media.mjs 使用），含可用性过滤、报表排序 |
| muse_audios/get | [materials/muse-audios-get.md](references/materials/muse-audios-get.md) | 查询妙思版权音频（get-audios.mjs 使用） |
| dc_review_result/get | [dc-review-result-get.md](references/dc-review-result-get.md) | 查询动态创意审核详情（get-dc-review-result.mjs 使用），返回组件/元素的审核状态、驳回原因、组件组合审核信息 |
| dynamic_ad_image_templates/get | [dynamic-ad-templates.md](references/dynamic-ad-templates.md) | 查询商品图片模版列表（MPA/DPA，get-dynamic-ad-image-templates.mjs 使用） |
| dynamic_ad_images/add | [dynamic-ad-templates.md](references/dynamic-ad-templates.md) | 从商品模版生成图片（generate-dynamic-ad-image.mjs 使用） |
| dynamic_ad_video_templates/get | [dynamic-ad-templates.md](references/dynamic-ad-templates.md) | 查询商品视频模版列表（MPA/DPA，get-dynamic-ad-video-templates.mjs 使用） |
| dynamic_ad_video/add | [dynamic-ad-templates.md](references/dynamic-ad-templates.md) | 从商品模版生成视频（generate-dynamic-ad-video.mjs 使用） |
| material_labels/get·add·update·bind | [material-labels.md](references/material-labels.md) | 素材标签查询 / 新建 / 更新 / 绑定（get-material-labels / add-material-labels / update-material-labels / bind-material-labels 使用） |

---

## 相关技能

- **tencentads-adgroups** - 管理广告组（创意需关联到广告组，创建前先获取 `adgroup_id`）
