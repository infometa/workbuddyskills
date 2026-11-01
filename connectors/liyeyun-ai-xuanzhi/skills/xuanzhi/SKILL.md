---
name: liyeyun
description: 立业云AI选址 MCP 技能。通过 carrier_search 工具按必填省市 + 必填关键词 + 可选载体类型等条件搜索厂房、仓库、办公等产业载体，返回匹配载体列表与经纪人联系方式。当用户提到选址、找厂房、找仓库、找办公、找载体、招商、产业载体搜索或 carrier_search 时触发。
description_zh: "立业云AI选址助手，AI帮你智能查找厂房、仓库、办公等产业载体。"
description_en: "Liye Cloud AI site selection assistant: search factories, warehouses, and offices by region and carrier type."
version: 1.0.0
display_name: "立业云AI选址"
display_name_en: "Liye Cloud AI Site Selection"
visibility: "public"
---

# 立业云AI选址 (carrier_search)

通过立业云选址 MCP server 提供的 `carrier_search` 工具，按地区和载体类型搜索产业载体（厂房/仓库/办公），用于 AI 选址场景。

## 何时使用

- 用户想找某个地区的厂房 / 仓库 / 办公等产业载体
- 用户提到“选址”、“找厂房”、“找仓库”、“载体”、“招商”等需求
- 需要按省市、区县、街道、载体类型、关键词组合查询载体

## 前置条件

本技能依赖 agent 已通过 MCP 连接 `carrier_search` 工具。

若目标 agent 尚未配置该 MCP server，参考配置（Streamable HTTP）：

- **Server URL**: `https://lyy-mcp-platform-prod.liyeyun.com/mcp/lyy-pc-home-api-provider`
- **传输方式**: Streamable HTTP
- **协议版本**: MCP 2025-11-25
- **认证**: 需要 Authorization header（token 由平台提供）

配置到 `.mcp.json` 示例：

```json
{
  "mcpServers": {
    "立业云Ai选址": {
      "url": "https://lyy-mcp-platform-prod.liyeyun.com/mcp/lyy-pc-home-api-provider",
      "type": "streamable-http"
    }
  }
}
```

> 若该端口/URL 不可达，说明 MCP server 未启动或地址已变更，应先确认服务可用性。

## 参数规范

`carrier_search` 的参数：

| 参数          | 类型     | 必填   | 说明                                               |
| ------------- | -------- | ------ | -------------------------------------------------- |
| `province`    | string   | **是** | 省份，如 `河北`                                    |
| `city`        | string   | **是** | 城市，如 `廊坊`                                    |
| `carrierType` | string   | 否     | 载体类型，枚举：`厂房` / `仓库` / `办公`           |
| `query`       | string   | **是** | 搜索关键词（载体名称/位置/特征词等）               |
| `district`    | string   | 否     | 区/县                                              |
| `street`      | string   | 否     | 街道                                               |
| `excludeIds`  | string[] | 否     | 需排除的载体 ID 列表                               |
| `size`        | string   | **是** | 返回数量上限，**必须传字符串**（如 `"2"`），最多 2 |

### ⚠️ 关键约束

1. **`province`、`city`、`query` 均必填**。缺省市会触发服务端 `500 系统内部错误`；`query` 关键词也是必填项，缺失则无法定位搜索目标。
2. **`carrierType` 取中文枚举值，只有三个**：`厂房` / `仓库` / `办公`。不要传英文、编码或其他词。
3. 其余参数均为可选，按需提供。
4. **`size` 必填且类型是 `string`**：必须传字符串（如 `"2"`），传 number `2` 会直接报 `Parameter validation failed: /size: must be string`。取值 ≤ 2，建议默认传 `"2"`。

## 调用流程

1. **收集必填参数**：从用户需求中提取 `province`、`city`。若用户未明确，主动追问。
2. **提取关键词与可选参数**：`query` 关键词必填（从用户需求提取，如"独门独院"）；可选映射 `carrierType`（厂房/仓库/办公）、`district`/`street` 等。
3. **调用工具**：调用 `carrier_search`，传入上述参数，`size` 设为 `"2"`（**字符串**，最多返回 2 条）。
4. **解读返回**：见下节。
5. **呈现结果**：按「结果呈现规范」只提取核心信息呈现（图片/名称/核心信息/联系人）；宿主支持富渲染时优先用卡片式，否则降级为文本模板；若为空，提示无匹配并建议调整条件。

## 返回解读

返回是工具结果（`content[0].text` 中的 JSON 字符串），顶层结构：

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {
    "requestId": "85eddb05-...",
    "status": "SUCCESS | NO_MATCH",
    "queryMode": "MCP_LIGHT_SEARCH",
    "cardCount": 1,
    "cards": [ /* 载体卡片数组 */ ]
  }
}
```

| 字段             | 含义                                |
| ---------------- | ----------------------------------- |
| `code`           | 业务码，`200` 为成功                |
| `msg`            | 提示信息                            |
| `data.status`    | `SUCCESS` 有匹配；`NO_MATCH` 无匹配 |
| `data.cardCount` | 命中载体数量                        |
| `data.cards`     | 载体列表，每项为一张载体卡片        |
| `data.requestId` | 请求追踪 ID，排查问题时提供         |

- `code != 200` 或返回 `isError: true`：调用失败，展示 `msg` 并检查参数（尤其省市是否缺失）。
- `status: NO_MATCH` / `cardCount: 0`：调用成功但无数据，建议用户放宽条件（换关键词、扩大区域、改载体类型）。

### `cards[]` 核心字段

每张卡片字段很多，**只需提取以下核心字段呈现给用户**，其余（score、batchId、坐标、scoreBreakdown 等）无需展示：

| 呈现项     | 字段路径                              | 示例                                |
| ---------- | ------------------------------------- | ----------------------------------- |
| 载体名称   | `name`                                | 大厂-祁各庄-独门独院341             |
| 载体类型   | `carrierTypeName`                     | 厂房                                |
| 厂房图片   | `firstFiles[0].path`                  | https://oss-gtv...jpg               |
| 地址       | `address`                             | 河北省廊坊市大厂回族自治县...       |
| 面积(㎡)   | `totalArea` / `effectiveArea`         | 340.0                               |
| 租金       | `rentPriceMin` ~ `rentPriceMax`       | 0.06 ~ 0.1                          |
| 结构       | `structureNames`                      | 砖混结构                            |
| 层数/层高  | `totalNumber` / `maxFloorHeight`      | 1 层 / 3.6m                         |
| 特性标签   | `featureNames`（或 `specialTagName`） | 独栋,有燃气,带装修                  |
| 用途       | `purposeNames`                        | 加工,生产                           |
| 备注       | `remark`                              | 村里小院340平米，一年8000元，有燃气 |
| 联系人     | `broker.name`                         | 邓春伟                              |
| 联系电话   | `broker.phoneNumber`                  | 13717914273                         |
| 经纪人头像 | `broker.avatar`                       | https://...                         |
| 从业年限   | `broker.brokerProfessionalAge`        | 5                                   |

可选补充信息（`parkInfo`，若存在）：`parkIntroduce`（场地介绍）、`parkElectricityCapacity`（用电容量 kVA）、`parkElectricityPrice`（电价）、`supportingNames`（配套设施）、`parkWaterPrice`（水价）。

## 结果呈现规范

给用户的信息**精简为核心**，不堆砌全部字段。每条载体按以下结构呈现：

1. **图片**：展示 `firstFiles[0].path`（首图链接）
2. **名称**：`name` + `carrierTypeName`
3. **核心信息**：地址、面积、租金、结构/层高、特性标签、用途、备注（一句话）
4. **联系人**：经纪人姓名 + 电话 + 从业年限

呈现模板（单条）：

```
🏭 大厂-祁各庄-独门独院341（厂房）
📍 河北省廊坊市大厂回族自治县大厂镇西马庄村…
📐 340㎡   💰 0.06~0.1 元/㎡
🏗 砖混结构 · 1层 / 层高3.6m
🏷 独栋·有燃气·带装修   🎯 用途:加工/生产
💬 村里小院340平米，一年8000元，有燃气
👤 邓春伟 13717914273（从业5年）
🖼 图片: https://oss-gtv.liyeyun.com/...
```

- 每次最多呈现 **2 条**（对应 `size ≤ 2`）。
- 字段缺失时省略对应行，不要写「暂无」占位。
- 图片以链接形式给出，由宿主环境渲染；不支持渲染时保留链接。

### 卡片式呈现（WorkBuddy / 支持富渲染的宿主优先）

在 WorkBuddy 等能渲染内联组件的宿主里，**优先用卡片式呈现**，把同一份字段升维成卡片，信息密度与可读性都优于 emoji 文本模板。文本模板仅作为降级方案（不支持富渲染时）。

**两条交付通道，按场景选**：

| 通道                       | 做法                                                      | 版式与适用                                                                          |
| -------------------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **对话内卡片**（默认首选） | `build_cards.py --widget` 出片段 → `show_widget` 直接渲染 | `compact` 左图右文缩略图（176px WebP）；1–2 条结果的即时浏览，双卡片段约 1.8 万字符 |
| **HTML 文件**              | `build_cards.py` 完整模式出 HTML → `present_files`        | `hero` 2:1 大图、可高清；结果多 / 要留档时用                                        |

**首选直接调用内置生成脚本**（见下文「卡片模板与生成脚本」），样式与字段规则都已固化，不要手写 HTML。

**卡片字段映射**：

| 卡片区域   | 取字段                                                                                                                                                      |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 首图       | `firstFiles[0].path`。`hero` 版为 2:1 大图；`compact` 版为左上方形缩略图（显示框 104×104，**源图 176px** 即 1.7x 采样，`object-fit: cover`）                |
| 类型/角标  | `carrierTypeName`（如「厂房」）+ 从 `featureNames` 里挑 1–2 个强信号标签（如「国资·104地块」）。`hero` 版压在图上左右两角，`compact` 版为标题上方的两枚胶囊 |
| 标题       | `name`                                                                                                                                                      |
| 副标题     | `provinceName`+`cityName`+`regionName` +（`businessDistrictName` 或 `address`）                                                                             |
| 指标行 1   | 面积：`effectiveArea` / `totalArea`（为 0 时回退读 `remark` 里的亩数）                                                                                      |
| 指标行 2   | 租金：`rentPriceMin`~`rentPriceMax`（均为 0 时写「价格待议」）                                                                                              |
| 指标行 3   | 结构：`structureNames` · `totalNumber` 层 / `maxFloorHeight`                                                                                                |
| 标签 chips | `featureNames` 拆分，**「独门独院」等命中的关键词高亮**，其余弱化                                                                                           |
| 备注       | `remark`（截一句）                                                                                                                                          |
| 页脚联系人 | `broker.avatar`（头像）+ `broker.name` + `broker.phoneNumber` + `broker.brokerProfessionalAge`（**此区做视觉着重**，见下）                                  |

**渲染要点**：

- 用 `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; justify-items: center;` 自适应排布，一次最多 2 张。
- **卡片必须设 `max-width:400px`**：否则单条结果时卡片会撑满整行（760px），图片被放大数倍而发糊。
- **两种版式（脚本按通道自动选，不要手改）**：
  - `hero`（HTML 文件）：2:1 首图铺满卡宽，类型/角标压在图片左上/右上；图走 460px 高清。
  - `compact`（对话内卡片）：**左图右文**——左侧方形缩略图（**显示框 104px，源图取 176px**），右侧为「类型+角标胶囊 → 标题（最多 2 行）→ 地址」，其下才是指标行。关键：**源图必须比显示框大**（104 显示框配 104 源图在高分屏上会被放大一倍而发糊；176/104 = 1.7x 才清晰）。
- **配色以立业云品牌红为主**：品牌主色取自技能图标 `_icon.svg` 的 `#C0322B`（砖红），卡片整体走红色系，不要用蓝色/青色为主题色。推荐色板：
  - 主色 `#C0322B`、深色（文字压色）`#9E2823`、浅底 `#FBEAE8`、浅描边 `#E8A9A3`
  - 页面底 `#FAF7F6`、卡片底 `#FFFFFF`、指标块底 `#FBF4F3`、正文 `#1F1F1E`、次要 `#6B6A65`
  - 用法：右上角角标、联系人面板用**实心主色 + 白字**；命中关键词 chip 用 `#FBEAE8` 底 + `#9E2823` 字 + `#E8A9A3` 描边；普通 chip 保持中性灰。标题左侧加一条 4px 主色竖条作为品牌点缀。
  - 深色宿主主题下把主色面板换成 `#7A211C` 底，文字仍用白。
- 命中关键词（如用户搜的「独门独院」）用强调色 chip 突出，形成"搜什么亮什么"的呼应。
- 数字取整；单位（㎡ / 元/㎡ / 层 / kVA）跟在数值后并弱化。
- **联系人区做视觉着重（重要）**：这是用户最终要转化的动作位，不能做成分隔线下的弱化小字。做法：整块包成**品牌红实心圆角面板**（`#C0322B` 底、白字），头像 40px 用半透明白底（`rgba(255,255,255,.20)`）+ 白字，姓名 14px/500，从业年限降为 74% 白，**电话放大到 16–17px、白色、等宽数字（`font-variant-numeric: tabular-nums`）**，让整区成为全卡视觉重心。
  - **不要加「拨号」按钮，也不要包 `tel:` 链接**：WorkBuddy 是桌面端，不支持拨号，按钮点了没反应反而像坏了。电话以醒目纯文本呈现，用户自行抄录即可。
- 卡片下方配 1–2 句结论性文字（如哪条更适合规上企业落户），再给下一步筛选建议。
- **图片可点击 → 跳转立业云详情页**（脚本已自动处理，见下）：
  - URL 规则：`https://liyeyun.com/channel/{slug}/{card.id}.html`
  - 类型映射（`card.carrierTypeName` → slug），载体类型只有三种：`厂房→plant`、`仓库→warehouse`、`办公→office`
  - **类型不在映射表内、或 `card.id` 缺失时，不生成链接**（宁可图片不可点，也不给死链）；此时脚本会往 stderr 提示，可在 `TYPE_SLUG` 中补充映射。
  - 实现：图片外包 `<a class="imglink" href="..." target="_blank" rel="noopener">`；`.imglink` 铺满容器并 `cursor:pointer`，hover 时图片 `scale(1.05)` 做可点击反馈；压在 `hero` 大图上的类型/角标胶囊设 `pointer-events:none`，让点击穿透到底层链接。
  - 注意：桌面端**不支持 `tel:` 拨号**（别加拨号按钮），但 http(s) 外链以 `target="_blank"` 新窗口打开。

### ⚠️ 图片渲染规则（实测结论，务必注意）

**能用的**：`<img src="data:image/jpeg;base64,...">` 与 `data:image/webp;base64,...`（内联 data URI）在 `show_widget` 里**都确认可正常渲染**，不受 CSP 限制。**优先用 WebP**（同分辨率体积小 20%~25%）。

**不能用的**（都实测过，别重复踩）：

| 方式                                          | 结果   | 说明                                                                                                  |
| --------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `<img src="https://oss-gtv.liyeyun.com/...">` | ❌ 空白 | 内联组件 CSP 白名单只允许 cdnjs / esm.sh / jsdelivr / unpkg，第三方 OSS 外链被静默拦截                |
| 改 OSS URL 的 `x-oss-process` 要小图          | ❌ 403  | 该参数参与 V4 签名，一动就签名失效                                                                    |
| `src` 写 `{"type":"image_blob_ref",...}` 指针 | ❌ 空白 | blob 引用只是**工具输出方向**的显示层机制（大 base64 落盘到 `~/.workbuddy/blobs/`），渲染调用里不解析 |

**所以：对话内卡片必须走内联 base64。**

### ⚠️ 内联 base64 的体积是硬约束（决定清晰度的上限）

内联卡片里的 base64 **必须由模型重新完整写进渲染调用**（`show_widget` 的 `widget_code`），而且平台会**折叠过长的 base64**：

| 实测                                                 | 结果                                                      |
| ---------------------------------------------------- | --------------------------------------------------------- |
| 单段 base64 **15688 字符** / 片段总长 20391 字符     | ❌ 被折叠成 `image_blob_ref` 指针 → 卡片出来、**图片空白** |
| 单段 **3120 字符** / 片段总长 **13927 字符**（双卡） | ✅ 完整保留、正常渲染                                      |

而 **base64 体积 ∝ 像素面积**：要清晰就得够像素，够像素就必超预算，两者在对话内**不可兼得**。

> 算笔账：卡片显示宽 400px 的 2:1 大图 = 400×200 = 8 万像素 ≈ 1.6 万字符 base64 —— **必然踩线**。
> 所以"全宽高清大图 + 对话内卡片"这条路在数学上就不成立，**不要再试**。

**结论：对话内卡片用 `compact` 缩略图版式，源图取 176px（显示框 104px 的 1.7x 采样）；高清大图交给 HTML 文件模式。**

**用 WebP 换清晰度（关键）**：`compact` 模式默认输出 `data:image/webp`。同分辨率下 WebP 比 JPEG 小 20%~25%，正好用来把缩略图源图从 104px 提到 176px **而不超字节预算**。实测（双卡，含 1 张真人头像）：

| 方案               | 单段最长 base64 | 片段总长  | 结果                       |
| ------------------ | --------------- | --------- | -------------------------- |
| 104px JPEG q64     | 3120            | 13921     | ✅ 渲染，但高分屏发糊       |
| **176px WebP q74** | **5944**        | **17971** | ✅ **渲染正常（当前默认）** |
| 208px JPEG q64     | 9076            | —         | ⚠️ 单段越线                 |

| 通道           | 版式                        | 图片规格                                                        | 实测                             |
| -------------- | --------------------------- | --------------------------------------------------------------- | -------------------------------- |
| **对话内卡片** | `compact`（左图右文缩略图） | 源图 176px WebP q74（显示框 104px），单段约 4–6 千字符          | 双卡片段约 1.8 万字符 ✅ 正常渲染 |
| **HTML 文件**  | `hero`（2:1 大图）          | 大图 460px JPEG；图片**直写磁盘、不经过模型上下文**，可任意高清 | 不受体积限制                     |

读取内联片段时的两个坑：

- **`Read` 工具会截断超过 2000 字符的行** → base64 那行必被截，**不能用 Read 读内联片段，必须用 Bash `cat` 整读**。
- 安全线（脚本会自检并在越线时往 stderr 打警告）：**单段 base64 ≤ 8000 字符、片段总长 ≤ 19000 字符**。实测 18484 字符（176px WebP 双卡 + 详情页链接）可正常渲染。
- 再往上提清晰度（`--thumb-w 208/240`）虽用 WebP 也可能压住单段，但片段总长会逼近/超过 2 万字符的读取上限，**务必重新核对长度**；真要更大图就走 HTML 文件模式。

## 卡片模板与生成脚本（优先用法）

本技能已内置模板与生成脚本。**不要每次手写卡片 HTML**，直接调脚本，样式和字段规则都在里面。

```
~/.workbuddy/skills/liyeyun/
├── assets/
│   ├── page_template.html      # 页面骨架：全部样式 + 立业云品牌红配色
│   ├── card_block.html         # hero 版单卡（2:1 大图），<!--CARD--> ... <!--/CARD--> 包裹
│   ├── card_block_compact.html # compact 版单卡（左图右文缩略图），同上
│   └── sample_cards.json       # 真实 carrier_search 返回样例，改脚本后可自测
└── scripts/
    └── build_cards.py          # 一键生成（含图片下载与 base64 内联）
```

### 调用方式

1. 把 `carrier_search` 的返回原样存成 JSON（完整响应或直接是 `cards` 数组都可以）。
2. 执行脚本：

```bash
python scripts/build_cards.py \
  --input  cards.json \
  --out    cards.html \
  --query  "独门独院"
```

3. 交付：
   - `--widget` 片段 → 用 Bash `cat` 整读（**不要用 Read，会截断 base64 行**）→ 贴进 `show_widget` 直接渲染在对话里；
   - 完整 HTML → 用 `present_files` 交给宿主预览面板。

### 参数

| 参数        | 必填 | 说明                                                                             |
| ----------- | ---- | -------------------------------------------------------------------------------- |
| `--input`   | 是   | carrier_search 完整响应 JSON，或 `cards` 数组                                    |
| `--out`     | 是   | 输出 HTML 路径                                                                   |
| `--query`   | 否   | 用户搜索关键词；命中的 `featureNames` 会被高亮成红色 chip                        |
| `--title`   | 否   | 标题，默认按「城市 · 关键词」拼出                                                |
| `--widget`  | 否   | 输出内联组件片段（去掉 doctype/html/head/body），供 `show_widget`                |
| `--layout`  | 否   | 版式 `hero` / `compact`；默认 `hero`（文件模式）/ `compact`（`--widget`）        |
| `--img-w`   | 否   | **hero 版**大图宽度，默认 `460`（2:1 居中裁切）                                  |
| `--thumb-w` | 否   | **compact 版**缩略图源图边长，默认 `176`（正方形；显示框 104px，故为 1.7x 采样） |
| `--img-q`   | 否   | 图片质量；hero 默认 `58`（JPEG），compact 默认 `74`（WebP）                      |
| `--fmt`     | 否   | 内联图片格式 `auto\|jpeg\|webp`；`auto` = compact 用 webp、hero 用 jpeg          |

### 两条命令（照抄即可）

```bash
# 对话内卡片（compact 版式，176px WebP 缩略图；片段约 1.8 万字符，Bash cat 一次读全）
python scripts/build_cards.py --input cards.json --out /tmp/cards_w.html --query "独门独院" --widget

# HTML 文件（hero 版式，高清大图，present_files 交付）
python scripts/build_cards.py --input cards.json --out cards.html --query "独门独院"
```

### 脚本已代劳的判断（无需手工处理）

- **面积**：优先 `effectiveArea` → `totalArea`；为 0 时从 `remark` 正则兜底解析「7亩」「340平米」。
- **租金**：`rentPriceMin`/`rentPriceMax` 相等只显示一个值；都为 0 显示「价格待议」。
- **结构**：`structureNames` + `totalNumber` 层；仅当 `maxFloorHeight ≥ 2` 才追加层高（`1.0` 这类占位值不显示）。
- **角标**：从优先级标签里挑 2 个，自动避开已高亮的 chip，不出现重复。
- **头像**：取 `broker.avatar`，同样下载后**方形居中裁切并 base64 内联**（hero 版 80×80 / compact 版 72×72，显示框 40px 故为 1.8x 采样）；若字段为空、下载失败，或命中**平台默认头像**（URL 含 `avatar_mini` / `/static/` / `default_avatar`）则回退为姓氏首字圆形占位——默认头像不是真人照片，直接显示反而误导用户。
- **图片跳转链接**：按 `carrierTypeName` + `id` 自动生成详情页地址并填入 `{{LINK_OPEN}}/{{LINK_CLOSE}}` 槽位（见上文「图片可点击 → 跳转立业云详情页」）；无映射或 id 缺失时两槽位为空，图片保持不可点。
- **图片下载失败**：静默降级为透明占位，不中断渲染。
- **对话内片段会自动去掉给宿主 `body` 加 padding/背景的规则**，把字体/颜色基线挪到 `.wrap` 上，避免污染宿主页面。
- **空元素清理**：备注为空时不留空行、单位为空时不留空 `<em>`。

### 环境

脚本依赖 Pillow。优先用托管 Python 环境（已装 Pillow）：

```bash
"C:/Users/shen/.workbuddy/binaries/python/envs/default/Scripts/python.exe" scripts/build_cards.py ...
```

若该环境不存在：`python -m venv <env>` 后 `pip install pillow`。

## 示例

**示例 1 — 按省市+载体类型搜索**

用户：“帮我找廊坊的厂房”

```
carrier_search({
  province: "河北",
  city: "廊坊",
  query: "厂房",
  carrierType: "厂房",
  size: "2"
})
```

> 真实返回示例见配套 `assets/sample_cards.json`（可直接喂给 `scripts/build_cards.py` 自测）：命中「大厂-祁各庄-独门独院341」厂房载体。

**示例 2 — 精确关键词搜索**

用户：“在廊坊找个带‘独门独院’的厂房”

```
carrier_search({
  province: "河北",
  city: "廊坊",
  carrierType: "厂房",
  query: "独门独院",
  size: "2"
})
```

**示例 3 — 精确到区县 + 排除**

用户：“廊坊大厂回族自治县有哪些厂房？排除 ID 为 1979491700941574146 的”

```
carrier_search({
  province: "河北",
  city: "廊坊",
  district: "大厂回族自治县",
  query: "厂房",
  carrierType: "厂房",
  excludeIds: ["1979491700941574146"],
  size: "2"
})
```

## 注意事项

- 若调用返回 `{"code":500,"message":"系统内部错误"}`，**首先检查 `province`/`city`/`query` 是否都已填写**——这是最常见的触发原因。
- `carrierType` 必须是 `厂房`/`仓库`/`办公` 之一；传其他值可能不被识别。
- 省市名称用中文全称（如 `河北`、`廊坊`、`北京`），避免用简称或拼音。
- 结果为空不代表接口故障；先尝试调整查询条件再下结论。
