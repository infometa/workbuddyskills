---
name: tuniu-cli
description: 途牛旅行统一助手（推荐优先使用）- 通过 tuniu CLI 统一调用国内/国际机票、酒店、门票、火车票、邮轮、度假产品、打包订等旅行服务。适用于用户询问国内和国际航班、酒店、景点门票、火车票、邮轮、跟团游/自助游/自驾游等度假产品，以及机酒/酒火等组合预订需求。【机票分流】涉及机票时必须先判断国内航线或国际航线，再分别调用 flight / intelflight。【度假/打包订】理解用户要买成品线路还是自由组合资源，再选 holiday 或 package-booking（二者非互斥，同一对话可先后使用）。【优先级说明】当同时安装了 tuniu-flight/tuniu-hotel/tuniu-ticket/tuniu-train/tuniu-cruise 等单独服务 skill 时，请优先使用本 skill，它整合了所有服务能力且调用方式更简洁。
version: 1.0.8
minCliVersion: 1.1.1
metadata: {"openclaw": {"emoji": "🧳", "category": "travel", "tags": ["途牛", "旅行", "机票", "国际机票", "酒店", "门票", "火车票", "邮轮", "预订", "度假", "打包订", "机酒"], "priority": 100, "requires": {"bins": ["node", "npm", "tuniu"], "node": ">=18.0.0"}}}
---

# 途牛旅行助手

当用户询问航班（含国际机票）、酒店、景点门票、火车票、邮轮、度假产品（跟团/自助/自驾/当地游等）、打包订（机酒/酒火/酒店+门票等组合预订）等旅行服务时，使用此 skill 通过 **tuniu CLI** 调用途牛服务。

机票/航班需求：**先看下方「机票国内 / 国际分流」再选 server**，不要默认调用 `flight`。

度假产品 vs 打包订：**先看下方「度假产品 / 打包订：意图识别」**。`holiday` 是买已上架成品线路；`package-booking` 是把机票/火车/酒店/门票中至少两类按需求自由组合。

## 运行环境要求

**运行环境必须安装 Node.js 18+ 与 tuniu-cli**，否则无法调用服务。

### 首次使用前自检

在第一次调用 `tuniu` 前，按顺序检查运行环境：

```bash
node --version
npm --version
tuniu --version
```

- 若 `node` 不存在，或版本低于 18：不要继续安装 `tuniu-cli`；告知用户需先安装或升级 Node.js 18+，否则 `npm install -g tuniu-cli@latest` 会失败。
- 若 `npm` 不存在：告知用户需安装 Node.js/npm 后再继续。
- 若 `tuniu` 不存在，但 Node.js 版本满足要求，自动执行 `npm install -g tuniu-cli@latest` 安装 CLI。
- 若 `tuniu` 已存在：检查版本是否满足本 skill 头部的 `minCliVersion`。低于该版本时，先更新 CLI，再继续业务调用。

### 安装 tuniu-cli

```bash
# npm 全局安装（推荐）
npm install -g tuniu-cli@latest

# 或使用 npx 临时调用
npx tuniu-cli --version
```

## 认证要求

WorkBuddy 仅支持 **daemon 模式 OAuth**。首次业务调用前先检查授权状态：

```bash
tuniu auth status --daemon
```

未授权或授权失效时，引导用户执行：

```bash
tuniu auth login --daemon
```

- 已授权：直接调用 `tuniu`，不要要求用户重复授权。
- 认证失败（如退出码 104、108、109、110、111、112）：先执行 `tuniu auth status --daemon` 确认状态；失效则重新执行 `tuniu auth login --daemon`。
- relay 授权链接默认有效 5 分钟；用户在浏览器中犹豫超过有效期后，需要重新执行 `tuniu auth login --daemon` 获取新链接。
- `tuniu auth status --daemon` 只输出 `TUNIU_AUTH_OK` 或 `TUNIU_AUTH_REQUIRED`。需要诊断 relay 超时或授权失败原因时，执行 `tuniu -d auth status --daemon`。

## 速查表

### 机票国内 / 国际分流（调用前必须执行）

收到机票/航班类需求时，**先按出发地、目的地判断航线类型，再选 MCP**，不要直接默认 `flight`：

| 航线类型 | 判断依据（以城市为准） | server | 首选工具 |
|----------|------------------------|--------|----------|
| **国内** | 出发地与目的地均为中国大陆城市（如北京→上海、广州→成都） | `flight` | `searchLowestPriceFlight` |
| **国际** | 出发地或目的地任一为境外（含港澳台，如北京→东京、上海→香港、深圳→台北） | `intelflight` | `list_intel_flights` |

**分流规则**：

1. **以出发地/目的地为准**；用户口头说「国内/国际/出国」仅作参考。若口头标签与城市判断冲突（如口称国际但两地均为大陆），按城市判断选 server。
2. 先解析出发城市、到达城市；无法判断时先向用户确认航线类型，**确认前不要调用任一机票 MCP**。
3. 国内只用 `flight`，国际只用 `intelflight`。两者工具名与参数体系不同（国内多为 camelCase，国际多为 snake_case），不可混用；同名工具（如 `getBookingRequiredInfo`）必须带对 server 前缀调用。
4. 若列表中尚无 `intelflight`，先执行 `tuniu discovery refresh && tuniu discovery list`；仍无则告知用户当前环境暂未开放国际机票服务。
5. **往返、多城按每一航段独立判断并选 server**（例如北京→东京→北京：去程、回程各调一次 `intelflight`；北京→上海→东京：第一段 `flight`、第二段 `intelflight`）。同一对话可交替使用两个服务，但单次 `tuniu call` 只能选一个 server。

### 度假产品 / 打包订：意图识别

`holiday` 与 `package-booking` 是两种商品形态（非互斥），同一对话可先后使用。先认清用户**当前这一步**要什么，再选工具。

| 能力 | 用户要什么 |
|------|------------|
| `holiday` | 买已上架的成品线路（产品、团期） |
| `package-booking` | 把机票/火车/酒店/门票中**至少两类**按需求自由组合成带报价的方案（可先看方案，确认后再下单） |
| 单品服务 | 只查/只订一类资源 |

| 用户表达 | 当前步骤 |
|----------|----------|
| “看看三亚跟团游”“查自由行产品/团期” | `holiday` |
| “帮我搭一套机酒方案看看价”“高铁+酒店先规划一下”“机票酒店门票一起订” | `package-booking` |
| “查三亚酒店” | `hotel` |
| “想去三亚玩”（未说明产品还是自选组合） | 先澄清，不要默认调 `holiday` 或 `package-booking` |

**判定顺序（按序，命中即停）**

1. 明确要产品/线路/跟团/团期/当地参团 → `holiday`（成品线路内部含不含机票酒店都无关）。
2. 明确要把机票/火车/酒店/门票中至少两类做成一套组合方案或一起订（2/3/4 类均可）→ `package_booking_create`；仅当用户确认清单与价格后才 `submit`。
3. 只涉及一类资源 → 对应单品服务。
4. 意图不清（仅目的地、“自由行/自助游”无上下文）→ 先问一句再调工具。
5. 调 `package-booking` 前若列表无该服务 → `tuniu discovery refresh && tuniu discovery list`。调用须有出发/目的城市，并显式传至少两类 `resourceSpecs`，不要依赖服务端默认补资源。

### 意图识别（用户说什么 → 用什么工具）

| 用户意图关键词 | server | 首选工具 | 必填参数 |
|---------------|--------|----------|----------|
| 航班/机票/飞机（两地均在中国大陆；分流见上表） | `flight` | `searchLowestPriceFlight` | `departureCityName`, `arrivalCityName`, `departureDate` |
| 航班/机票/飞机（含境外或港澳台；分流见上表） | `intelflight` | `list_intel_flights` | `departure_city`, `arrival_city`, `departure_date` |
| 酒店/住宿/民宿 | `hotel` | `tuniuHotelSearch` | `cityName` |
| 门票/景点门票 | `ticket` | `query_cheapest_tickets` | `scenic_name` |
| 火车票/高铁/动车 | `train` | `searchLowestPriceTrain` | `departureCityName`, `arrivalCityName`, `departureDate` |
| 邮轮/游轮 | `cruise` | `searchCruiseList` | `departsDateBegin`, `departsDateEnd` |
| 度假/跟团/自助游产品/自驾游产品/旅游线路/团期（成品线路，见上方意图识别） | `holiday` | `searchHolidayList` | 无单一必填（建议 `keyWord` 和/或结构化条件；若传出游日期则 `departsDateBegin` 与 `departsDateEnd` 需成对） |
| 打包订/组合预订/一起订/自由搭配（机票·火车·酒店·门票中至少两类，见上方意图识别） | `package-booking` | `package_booking_create` | `baseInfo.startCityName`, `baseInfo.destCityName`；建议显式传至少两类 `resourceSpecs` |

### 基本命令格式

```bash
tuniu call <server> <tool> -a '<JSON参数>'
```

| 参数 | 说明 |
|------|------|
| `server` | 服务名称：`ticket`、`hotel`、`flight`、`intelflight`、`train`、`cruise`、`holiday`、`package-booking` |
| `tool` | 工具名称，如 `query_cheapest_tickets`、`searchLowestPriceFlight`、`list_intel_flights` 等 |
| `--args` 或 `-a` | 工具输入参数，必须是合法的 JSON 字符串 |

**重要**：`--args` 的值必须是 JSON 格式，且用引号包裹。中文可直接写入，无需转义。无参数时用空对象：`-a '{}'`

### 服务工具链路

| 服务 | 完整流程（搜索→详情→下单） |
|------|---------------------------|
| `flight`（国内） | `searchLowestPriceFlight` → `multiCabinDetails` → `getBookingRequiredInfo` → `saveOrder` → `cancelOrder` |
| `intelflight`（国际） | `list_intel_flights` → `get_intel_flight_details` → `getBookingRequiredInfo` → `create_intel_flight_order` → `cancel_intel_flight_order` |
| `hotel` | `tuniuHotelSearch` → `tuniuHotelDetail` → `tuniuHotelCreateOrder` |
| `ticket` | `query_cheapest_tickets` → `create_ticket_order` |
| `train` | `searchLowestPriceTrain` → `queryTrainDetail` → `bookTrain` → `cancelOrder` |
| `cruise` | `searchCruiseList` → `getCruiseProductDetail` → `getCruiseCabinAndRoom` → `saveCruiseOrder` |
| `holiday` | `searchHolidayList` → `getHolidayProductDetail` → `getHolidayBookingRequiredInfo`（可选，预订说明）→ `saveHolidayOrder` |
| `package-booking` | `package_booking_create` →（展示清单并取得确认）→ `package_booking_submit` |

### 常用辅助命令

| 命令 | 用途 |
|------|------|
| `tuniu list` / `tuniu list <server>` | 列出服务/工具 |
| `tuniu help <server> <tool>` | 查看参数说明 |
| `tuniu schema --output json` | 获取完整 Schema |
| `tuniu discovery refresh && tuniu discovery list` | 检查新服务 |
| `tuniu call ... -d` | 调试模式 |
| `tuniu skill version` | 查看已安装 skill 版本 |
| `tuniu skill install [--agent/--dir]` | 安装/更新 skill 到指定 Agent 或目录 |

---

## 服务发现触发条件

当遇到以下情况时，**必须**先执行 `tuniu discovery refresh && tuniu discovery list`：

1. **用户需求不在已知服务列表中**（如签证、租车、度假套餐等）
2. **tuniu list 返回的服务不包含用户需要的功能**
3. **工具调用返回"工具不存在"错误（退出码 102）**
4. **首次使用 tuniu-cli 时**（确保获取最新服务列表）
5. **判断为国际航线但本地尚未发现 `intelflight` 服务时**
6. **用户要打包订/组合预订，但本地尚未发现 `package-booking` 服务时**

```bash
tuniu discovery refresh && tuniu discovery list
```

执行后重新检查服务列表，再决定下一步调用。若仍无法满足用户需求，才告知用户当前平台暂不支持该功能。

---

## Skill 版本与更新说明

`tuniu-cli` 提供 **skill** 子命令，用于维护本助手在各 AI Agent 目录下的安装与版本查看，与业务调用（`tuniu call`）相互独立。

### CLI 与 Skill 兼容性

本 skill 依赖 `tuniu-cli` 版本不低于头部声明的 `minCliVersion`。Agent 在使用本 skill 时必须遵循：

1. 若 `tuniu --version` 低于 `minCliVersion`，先执行 `npm install -g tuniu-cli@latest` 更新 CLI。
2. 更新 CLI 后执行 `tuniu --version` 确认版本，再执行 `tuniu skill install` 更新本地 skill。
3. 若全局 npm 安装无权限，先尝试提示用户授权或使用当前环境可用的安装方式；不要继续调用低版本 CLI 中不存在的命令。
4. 若更新失败，明确告知用户当前 CLI 版本与 skill 不兼容，部分操作可能失效。

**使用场景简述**

- **`tuniu skill version`**：在已配置多台 Agent（如 Cursor、Claude 等）时，检查各目录下已安装的 skill 版本、来源与安装时间；便于确认是否与文档站最新包一致。
- **`tuniu skill install`**：需要**安装或更新**本 skill 时使用。默认仅写入 `~/.agents/skills/tuniu-cli/`；通过 `--agent` 可指定单个、多个（逗号分隔）或 `all`（全部内置支持的 Agent）；`--dir` 可额外指定自定义 skills 根目录。
- **`npm install` / `npm ci`**：安装 `tuniu-cli` 时若启用脚本，**postinstall** 可能已根据本机存在的 Agent 父目录自动复制内置 skill；若需与线上一致或显式更新，仍建议执行 `tuniu skill install`。

更完整的参数与示例见：`tuniu skill install --help`。

---

## 隐私与个人信息（PII）说明

预订功能会将用户提供的**个人信息**（联系人姓名、手机号、乘客姓名、证件号等）通过 tuniu CLI 发送至途牛远端服务，以完成订单创建。使用本 skill 即表示用户知晓并同意上述 PII 被发送到外部服务。请勿在日志或回复中暴露用户个人信息。

## 适用场景

- 国内/国际机票搜索、舱位查询与预订（分流见速查表）
- 酒店搜索、详情查询、酒店预订
- 景点门票查询、门票预订
- 火车票车次查询、车次详情、火车票预订
- 邮轮产品搜索、团期查询、邮轮预订（兼容"游轮"说法）
- 度假产品搜索、团期价格日历、度假预订（兼容跟团、自助游、自驾游、当地游等表述；与打包订的区分见速查表意图识别）
- 打包订：多资源组合清单创建（可规划出方案/报价）与确认后的订单提交（机票/火车/酒店/门票中至少两类）
- **动态服务发现**：当用户旅行需求超出上述服务范围时，通过 discovery 功能检查是否有新服务上线

## 动态服务发现

途牛 CLI 支持动态发现新服务。**触发条件见上方 服务发现触发条件 章节**，满足条件时执行：

```bash
tuniu discovery refresh && tuniu discovery list
```

**服务发现默认开启**。如不确定，可先执行 `tuniu discovery status` 确认；若返回 `启用: 否`，手动开启：

```bash
export TUNIU_DISCOVERY_ENABLED=true
```

| 命令 | 用途 |
|------|------|
| `tuniu discovery status` | 查看启用状态、缓存状态、服务数量 |
| `tuniu discovery list` | 获取当前可用服务列表（失败时回退静态配置/缓存） |
| `tuniu discovery refresh` | 强制刷新缓存，获取最新服务列表 |

> 工具调用返回退出码 102 时，先执行 `tuniu discovery refresh && tuniu schema --output json`，再重试调用。

### 最佳实践

1. **初始化时**：执行 `tuniu discovery status` 确认服务发现状态（默认开启）
2. **遇到新需求时**：先执行 `tuniu discovery refresh` 刷新缓存，再 `tuniu discovery list` 查看最新服务
3. **获取新服务能力**：执行 `tuniu schema --output json` 获取最新工具定义
4. **降级处理**：如果 discovery 服务不可用，会自动回退到静态配置

## 各服务详细说明

### 1. 国内机票服务 (flight)

**触发词**：航班、机票、飞机；两地均在中国大陆（如北京到上海、广州到成都）

#### 1.1 航班搜索 (searchLowestPriceFlight)

**支持 6 种查询模式**：
- **默认低价查询**：不传 searchType
- **TIME 时间范围查询**：searchType="TIME"，按出发/到达时间筛选
- **PRICE 价格区间查询**：searchType="PRICE"，按价格区间筛选
- **NEAR_GO 周边出发**：searchType="NEAR_GO"，查询出发地周边机场
- **NEAR_BACK 周边到达**：searchType="NEAR_BACK"，查询目的地周边机场
- **TRANSFER 中转查询**：searchType="TRANSFER"，查询中转航班

**必填参数**：`departureCityName`、`arrivalCityName`、`departureDate`（YYYY-MM-DD）

**翻页**：传相同城市日期参数 + `pageNum`（2=第二页，3=第三页…）

```bash
# 默认低价查询
tuniu call flight searchLowestPriceFlight -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15"}'

# TIME 模式：早班机
tuniu call flight searchLowestPriceFlight -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15","searchType":"TIME","departureTime":"06:00-10:00"}'

# 翻页查询
tuniu call flight searchLowestPriceFlight -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15","pageNum":2}'
```

#### 1.2 舱位详情查询 (multiCabinDetails)

**必填参数**：`departureCityName`、`arrivalCityName`、`departureDate`（YYYY-MM-DD）、`flightNo`

**返回**：`cabinPriceId`（下单必需）

```bash
tuniu call flight multiCabinDetails -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15","flightNo":"MU5101"}'
```

#### 1.3 预订信息说明 (getBookingRequiredInfo)

**创建订单前必须先调用**（注意 server 为 `flight`，勿与 `intelflight getBookingRequiredInfo` 混淆）。无参数，返回纯文本预订字段说明。

```bash
tuniu call flight getBookingRequiredInfo -a '{}'
```

#### 1.4 创建订单 (saveOrder)

**前置条件**：必须先调用 `searchLowestPriceFlight`、`multiCabinDetails` 获取 `cabinPriceId`，并已调用 `getBookingRequiredInfo`

**必填参数**：`departureCityName`、`arrivalCityName`、`departureDate`、`flightNo`、`cabinPriceId`、`tourists`、`contactTourist`

```bash
tuniu call flight saveOrder -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15","flightNo":"MU5101","cabinPriceId":"xxx","tourists":[{"name":"张三","idType":"身份证","idNumber":"310101199001011234","mobile":"13800138000"}],"contactTourist":{"name":"张三","mobile":"13800138000"}}'
```

#### 1.5 取消订单 (cancelOrder)

```bash
tuniu call flight cancelOrder -a '{"orderId":"订单号"}'
```

---

### 2. 国际机票服务 (intelflight)

**触发词**：航班、机票、飞机；含境外或港澳台航线（如北京到东京、上海到香港、深圳到台北）

#### 2.1 国际航班搜索 (list_intel_flights)

**必填参数**：`departure_city`、`arrival_city`、`departure_date`（YYYY-MM-DD）

**可选参数**：`adult_count`（默认 2，单人须显式传 `1`）、`child_count`、`inf_count`、`page_num`

**返回**：顶层 `queryId`（后续下单必需，须与同一次搜索条件对应）、航班列表

**翻页**：保持除 `page_num` 外的查询条件不变。

```bash
# 单成人查询（务必显式传 adult_count=1，否则默认按 2 成人询价）
tuniu call intelflight list_intel_flights -a '{"departure_city":"北京","arrival_city":"东京","departure_date":"2026-08-15","adult_count":1}'

# 成人+儿童
tuniu call intelflight list_intel_flights -a '{"departure_city":"上海","arrival_city":"大阪","departure_date":"2026-08-20","adult_count":2,"child_count":1}'
```

#### 2.2 舱位详情 (get_intel_flight_details)

**前置条件**：建议先调用 `list_intel_flights`；城市与日期须与搜索一致。服务会按城市日期读取缓存的 `queryId`，未命中时自动重搜。

**必填参数**：`flight_no`（来自列表 `flightNumber`，多航段传完整组合如 `UO235-UO652`）、`departure_city`、`arrival_city`、`departure_date`

**返回**：`cabinInfo[].cabinCode`、`cabinInfo[].sourceId`（下单必需）

```bash
tuniu call intelflight get_intel_flight_details -a '{"flight_no":"UO235-UO652","departure_city":"北京","arrival_city":"东京","departure_date":"2026-08-15"}'
```

**下单字段提取**（同一航班同一舱位，不可混用）：

| 下单参数 | 取值来源 |
|----------|----------|
| `flight_nos` | `flightInfo[].flightNumber` |
| `cabin_codes` | `cabinInfo[].cabinCode` |
| `vendor_id` | `sourceId` 第一个 `-` 前的内容 |
| `expand_price_id` | `sourceId` 去掉 `vendor_id-` 后的内容 |

示例：`sourceId` 为 `95-UO235_T#UO652_T#` → `vendor_id=95`，`expand_price_id=UO235_T#UO652_T#`

#### 2.3 预订信息说明 (getBookingRequiredInfo)

**创建订单前必须先调用**（注意 server 为 `intelflight`，勿与 `flight getBookingRequiredInfo` 混淆）。无参数，返回纯文本预订字段说明（按文本展示，勿强行 JSON 解析）。

```bash
tuniu call intelflight getBookingRequiredInfo -a '{}'
```

#### 2.4 创建订单 (create_intel_flight_order)

**前置条件**：

1. 已调用 `list_intel_flights` 并保存顶层 `queryId`
2. 已调用 `get_intel_flight_details` 并选定舱位
3. 已调用 `getBookingRequiredInfo` 并向用户确认信息
4. 出发地、目的地、日期、乘客人数与搜索时一致
5. 当前版本仅支持护照（`pspt_type` 建议传 `2`）

**必填参数**：`query_id`、`flight_nos`、`cabin_codes`、`vendor_id`、`expand_price_id`、`tourists`、`contact`

`tourists` 关键字段：`surname`、`given_name`（建议证件英文姓名）、`pspt_type`、`pspt_id`、`sex`、`country`、`birthday`、`pspt_end_date`

`contact` 关键字段：`phone_area_code`、`phone`、`email`（`name` 可选）

```bash
tuniu call intelflight create_intel_flight_order -a '{"query_id":"Y2l0eUtleXM9QkpTLVRZTyxkZXBhcnR1cmVEYXRlPTIwMjYtMDgtMTU...","flight_nos":"UO235-UO652","cabin_codes":"T-T","vendor_id":95,"expand_price_id":"UO235_T#UO652_T#","category_code":"2000","tourists":[{"surname":"ZHANG","given_name":"SAN","pspt_type":2,"pspt_id":"E12345678","sex":"男","country":"中国","birthday":"1990-01-15","pspt_end_date":"2030-01-15"}],"contact":{"phone_area_code":"0086","phone":"13800138000","email":"zhangsan@example.com","name":"张三"}}'
```

下单成功后必须提醒用户点击返回的 `payment_url` 完成支付。

#### 2.5 取消订单 (cancel_intel_flight_order)

**仅在用户明确确认取消后调用**（未确认前不要执行）。

```bash
tuniu call intelflight cancel_intel_flight_order -a '{"order_id":"ORD20260815001","cancel_reason":"重选航程"}'
```

---

### 3. 酒店服务 (hotel)

**触发词**：酒店、住宿、民宿、某地酒店、入住、查酒店

#### 3.1 酒店搜索 (tuniuHotelSearch)

**必填参数**：`cityName`
**可选参数**：`checkIn`、`checkOut`（YYYY-MM-DD）、`keyword`、`prices`

**翻页**：传 `queryId`（首次搜索返回）和 `pageNum`

```bash
# 第一页
tuniu call hotel tuniuHotelSearch -a '{"cityName":"北京","checkIn":"2026-03-01","checkOut":"2026-03-03"}'

# 翻页（使用 queryId）
tuniu call hotel tuniuHotelSearch -a '{"queryId":"xxx","pageNum":2}'
```

#### 3.2 酒店详情 (tuniuHotelDetail)

**必填参数**：`hotelId` 或 `hotelName` 二选一

```bash
tuniu call hotel tuniuHotelDetail -a '{"hotelId":12345,"checkIn":"2026-03-01","checkOut":"2026-03-03"}'
```

#### 3.3 创建订单 (tuniuHotelCreateOrder)

**前置条件**：必须先调用 `tuniuHotelDetail` 获取 `preBookParam`

**必填参数**：`hotelId`、`roomId`、`preBookParam`、`checkInDate`、`checkOutDate`、`roomCount`、`roomGuests`、`contactName`、`contactPhone`

```bash
tuniu call hotel tuniuHotelCreateOrder -a '{"hotelId":"xxx","roomId":"xxx","preBookParam":"xxx","checkInDate":"2026-03-01","checkOutDate":"2026-03-03","roomCount":1,"roomGuests":[{"guests":[{"firstName":"三","lastName":"张"}]}],"contactName":"张三","contactPhone":"13800138000"}'
```

---

### 4. 门票服务 (ticket)

**触发词**：门票、景点门票、某景点门票、门票价格、门票多少钱

#### 4.1 门票查询 (query_cheapest_tickets)

**必填参数**：`scenic_name`（景点名称）

**返回**：`productId`、`resId`（下单必需）

```bash
tuniu call ticket query_cheapest_tickets -a '{"scenic_name":"中山陵"}'
```

#### 4.2 创建订单 (create_ticket_order)

**前置条件**：必须先调用 `query_cheapest_tickets` 获取 `productId` 和 `resId`

**必填参数**：`product_id`、`resource_id`、`depart_date`、`adult_num`、`contact_name`、`contact_mobile`、`tourist_1_name`、`tourist_1_mobile`、`tourist_1_cert_type`、`tourist_1_cert_no`

```bash
tuniu call ticket create_ticket_order -a '{"product_id":12345,"resource_id":"res001","depart_date":"2026-04-01","adult_num":1,"contact_name":"张三","contact_mobile":"13800138000","tourist_1_name":"张三","tourist_1_mobile":"13800138000","tourist_1_cert_type":"身份证","tourist_1_cert_no":"310101199001011234"}'
```

---

### 5. 火车票服务 (train)

**触发词**：火车票、火车、车次、某站到某站火车、高铁、动车

#### 5.1 查询车次列表 (searchLowestPriceTrain)

**必填参数**：`departureCityName`、`arrivalCityName`、`departureDate`（yyyy-MM-dd）
**可选参数**：`departureTime`、`arrivalTime`（时间范围，如"08:00-12:00"）、`searchType`（查询模式，默认值 `5`）

**searchType 取值说明**：
- `1`：按出发时间升序
- `2`：按出发时间降序
- `3`：按行程耗时升序
- `4`：按行程耗时降序
- `5`：按票价升序（默认）
- `6`：按票价降序

**翻页**：传首次查询返回的 `queryId` 和 `pageNum`

```bash
# 首次查询
tuniu call train searchLowestPriceTrain -a '{"departureCityName":"南京","arrivalCityName":"上海","departureDate":"2026-03-20","searchType":"5"}'

# 翻页
tuniu call train searchLowestPriceTrain -a '{"queryId":"xxx","pageNum":2}'
```

#### 5.2 查询车次详情 (queryTrainDetail)

**必填参数**：`departureStationName`、`arrivalStationName`、`departureDate`、`trainNum`

**返回**：`resId`、`price`、`departsDate`（下单必需）

```bash
tuniu call train queryTrainDetail -a '{"departureStationName":"南京南","arrivalStationName":"上海虹桥","departureDate":"2026-03-20","trainNum":"G203"}'
```

#### 5.3 预订下单 (bookTrain)

**前置条件**：必须先调用 `searchLowestPriceTrain` 和 `queryTrainDetail`

**必填参数**：`resources`、`adultTourists`、`contact`、`acceptStandingTicket`

```bash
tuniu call train bookTrain -a '{"acceptStandingTicket":false,"adultTourists":[{"name":"张三","psptId":"310101199001011234","psptType":1,"isStuDisabledArmyPolice":0,"tel":"13800138000"}],"contact":{"tel":"13800138000"},"resources":[{"resourceId":2121337089,"adultPrice":141.0,"departsDate":"2026-03-20"}]}'
```

#### 5.4 取消订单 (cancelOrder)

```bash
tuniu call train cancelOrder -a '{"orderId":"订单号"}'
```

---

### 6. 邮轮服务 (cruise)

**触发词**：邮轮、游轮、邮轮产品、游轮搜索、邮轮预订（兼容"游轮"说法）

#### 6.1 邮轮列表搜索 (searchCruiseList)

**必填参数**：`departsDateBegin`、`departsDateEnd`（YYYY-MM-DD）
**可选参数**：`cruiseLineName`（航线）、`cruiseBrand`（品牌）、`tourDay`（天数）、`pageNum`

**日期约束**：起始日期不得早于当天，结束日期不得早于起始日期

**筛选说明**：接口支持仅按日期查询；用户只给日期范围时直接查，不要为了补齐可选筛选而额外追问航线/品牌/天数。

**翻页说明**：用户说“还有吗/翻页/下一页”时，保持相同筛选条件，仅更新 `pageNum`（2/3/4...）。

**列表展示要求**：当前页 `data.rows` 需逐条展示，不应无说明地只列少量样例。

```bash
tuniu call cruise searchCruiseList -a '{"departsDateBegin":"2026-03-17","departsDateEnd":"2026-03-30"}'

# 按航线筛选
tuniu call cruise searchCruiseList -a '{"departsDateBegin":"2026-03-17","departsDateEnd":"2026-03-30","cruiseLineName":"长江三峡","cruiseBrand":"世纪邮轮"}'
```

#### 6.2 产品详情 (getCruiseProductDetail)

**所有参数必须从 searchCruiseList 返回结果中获取，且来自同一条 rows 记录**

**必填参数**：`productId`、`departsDateBegin`、`departsDateEnd`、`departCityCode`（数组格式，必须原样传递）、`classBrandParentId`、`proMode`

**团期规则**：必须展示 `productPriceCalendar` 中全部可售团期；若 `count=0` 或 `rows` 为空，明确告知无可售团期并停止后续下单链路。

```bash
tuniu call cruise getCruiseProductDetail -a '{"productId":"321648365","departsDateBegin":"2026-02-10","departsDateEnd":"2026-02-14","departCityCode":[1602],"classBrandParentId":12,"proMode":1}'
```

#### 6.3 邮轮基础信息（可选） (getCruiseBaseInfo)

**用途**：查询船只参数、餐饮娱乐、涵盖舱等说明；不替代可售房型查询。

```bash
tuniu call cruise getCruiseBaseInfo -a '{"productId":"321648365","traceId":"<可选traceId>"}'
```

#### 6.4 行程详情（可选） (getJourneyDetail)

**用途**：按天展开行程详情；与预订主链路解耦。

```bash
tuniu call cruise getJourneyDetail -a '{"productId":"321648365","traceId":"<可选traceId>"}'
```
#### 6.5 查询舱位房型 (getCruiseCabinAndRoom)

**必填参数**：`productId`、`departDate`（用户从团期列表选择的日期）

**参数来源约束**：`departDate` 必须来自 `getCruiseProductDetail.data.productPriceCalendar.rows[].departDate`。

**下单映射约束（关键）**：
- `journeyId` 必须来自本次返回的 `cabinList[].journeyId`
- `resourceId` 必须取用户所选房型 `priceRes` 中 `roomTypeResType=0` 条目的 `resId`
- `subResourceId`（可选）取同一 `priceRes` 中 `roomTypeResType=1` 条目的 `resId`
- 严禁把 `priceRes` 数组下标（0/1/2...）当作 `resourceId/subResourceId`
- 严禁复用历史对话中的 ID，必须以“最近一次”舱位查询结果为准

```bash
tuniu call cruise getCruiseCabinAndRoom -a '{"productId":"321648365","departDate":"2026-05-01"}'
```

#### 6.6 获取预订信息 (getCruiseBookingRequiredInfo)

**说明**：无参数，返回预订必填字段与合规提示文本。

```bash
tuniu call cruise getCruiseBookingRequiredInfo -a '{}'
```

#### 6.7 创建订单 (saveCruiseOrder)

**前置条件**：必须先调用 `getCruiseProductDetail`、`getCruiseCabinAndRoom`、`getCruiseBookingRequiredInfo`

**必填参数**：`productId`、`departureDate`、`departureCityName`、`duration`、`night`、`vendorId`、`selectRes`、`tourists`

**来源与校验要点**：
- `departureDate` 必须取 `getCruiseCabinAndRoom.data.base.beginDate`
- `selectRes[].journeyId/resourceId/subResourceId` 必须逐项回溯到最近一次 `getCruiseCabinAndRoom` 原始返回
- `resourceId/subResourceId` 必须是 `priceRes[].resId` 的真实值，不能是索引或推断值
- 建议透传 `getCruiseProductDetail` 的 `traceId` 到后续调用，便于排障

```bash
tuniu call cruise saveCruiseOrder -a '{"productId":"321648365","departureDate":"2026-05-01","departureCityName":"上海","duration":5,"night":4,"vendorId":73197,"selectRes":[{"journeyId":91808486,"resourceId":2121750804}],"tourists":[{"name":"张三","idType":"身份证","idNumber":"310101199001011234","mobile":"13800138000"}]}'
```

---

### 7. 度假产品服务 (holiday)

**触发词**：度假产品、跟团、自助游产品、自驾游产品、旅游线路、当地游、团期（与打包订/单品资源区分，见上方「度假产品 / 打包订：意图识别」）

#### 7.1 度假列表搜索 (searchHolidayList)

**参数规则**：无单一必填参数。建议至少提供 `keyWord` 和/或结构化条件（日期、出发城市、产品类型等）。
**可选参数**：`keyWord`、`departsDateBegin`、`departsDateEnd`（成对出现，yyyy-MM-dd）、`departCityName`、`tourDay`、`queryTypeName`（`自驾游` / `自助游` / `跟团`）、`brandTypeName`、`conditions`、`lowPrice`、`highPrice`、`pageNum`

**keyWord 实操要点**：
- `keyWord` 用于承接目的地/主题等检索语义，不要混入“第2页/下一页”等翻页词
- 避免将“推荐/热门/受欢迎”等排序词写入 `keyWord`
- 翻页时保持筛选条件不变，仅更新 `pageNum`

**列表价格展示**：`searchHolidayList` 返回的 `price`、`starPrice` 等价为**起步价**。向用户展示时必须标注「起」（如 `¥38起`），不得写成确定价，避免误导。

```bash
tuniu call holiday searchHolidayList -a '{"keyWord":"三亚","departsDateBegin":"2026-04-10","departsDateEnd":"2026-04-15"}'

# 指定上海出发、跟团
tuniu call holiday searchHolidayList -a '{"keyWord":"云南","departsDateBegin":"2026-04-10","departsDateEnd":"2026-04-20","departCityName":"上海","queryTypeName":"跟团"}'
```

#### 7.2 产品详情 (getHolidayProductDetail)

**前置条件**：必须先调用 `searchHolidayList`，**所有入参须从列表 `data.rows[]` 对应行原样取得**（含 `departCityCode` 数组、`classBrandId`→`classBrandParentId`、`proMode` 等）。

**必填参数**：`productId`、`departCityCode`（数组）、`classBrandParentId`、`proMode`；若列表行含 `departsDateBegin`/`departsDateEnd` 则需成对传入且与列表一致。

**展示约束**：
- 团期需展示 `productPriceCalendar.rows` 中全部可选日期与价格
- 若 `count=0` 或 `rows` 为空，明确告知暂无可售团期并停止下单链路
- 若返回 `journeySummary`，按天（第N天+标题+模块）组织展示

```bash
tuniu call holiday getHolidayProductDetail -a '{"productId":"321619424","departCityCode":[1602],"classBrandParentId":12,"proMode":1}'
```

#### 7.3 预订说明 (getHolidayBookingRequiredInfo)

无参数，返回预订需填信息的中文说明（纯文本，直接展示，不做 JSON.parse）。

```bash
tuniu call holiday getHolidayBookingRequiredInfo -a '{}'
```

#### 7.4 创建订单 (saveHolidayOrder)

**前置条件**：必须先调用 `getHolidayProductDetail`；`departDate` 须来自详情中 `productPriceCalendar.rows[].departDate`；建议传入详情返回的 `traceId`。

**必填参数**：`productId`、`departDate`、`departCityName`、`duration`、`tourists`；`night` 可选（半日游可能为 0 或空）。

**参数来源约束**：`departCityName` 必须取 `getHolidayProductDetail.data.departureCityName`。

```bash
tuniu call holiday saveHolidayOrder -a '{"productId":"321619424","departDate":"2026-05-01","departCityName":"南京","duration":5,"night":4,"traceId":"<详情返回的traceId>","tourists":[{"name":"张三","idType":"身份证","idNumber":"310101199001011234","mobile":"13800138000"}]}'
```

---

### 8. 打包订服务 (package-booking)

**适用意图**（见上方意图识别）：
- **出组合方案**：用户要把 `HOTEL` / `FLIGHT` / `TRAIN` / `TICKET` 中至少两类拼成带报价的组合清单（可只规划、暂不下单）→ `package_booking_create`
- **提交订单**：用户已确认多资源组合清单与价格 → `package_booking_submit`

若 `tuniu list` / discovery 中尚无本服务，先执行 `tuniu discovery refresh && tuniu discovery list`。

#### 8.1 创建打包订清单 (package_booking_create)

功能：根据城市、日期、人数和资源条件创建组合预订清单，返回顶层 `packageSessionId`、`data.resources`、`data.priceInfo`。**创建清单不会下单。**

**必填参数**：`baseInfo.startCityName`、`baseInfo.destCityName`

**建议参数**：
- `baseInfo.departDate` / `returnDate`（`YYYY-MM-DD`；`returnDate` 不得早于 `departDate`）
- `baseInfo.tripDays`、`adultCount`、`childCount`、`childAges`
- `resourceSpecs`：显式指定至少两类不同 `resourceType`（`HOTEL` / `FLIGHT` / `TRAIN` / `TICKET`）

**红线（Agent 必须遵守）**：
1. **至少两类资源意图**：用户未表达至少两类资源组合时，不要调用本工具；不要依赖服务端跨城默认 `HOTEL+TRAIN`、同城默认 `HOTEL`。
2. **不要空 `resourceSpecs` 碰运气**：组合预订应明确传入至少两类资源条件。
3. **不要同时放 `FLIGHT` 和 `TRAIN`**，除非用户明确要求两类交通都进同一个组合。
4. **create 是组合清单生成器，不是单品搜索器**：用户要「先出多资源组合方案/报价」时可直接 create；若具体航班/车次/酒店/门票尚需挑选，可先用单品服务查候选，再把条件写入 `resourceSpecs` 后 create。
5. **精确 ID**（`hotelId`/`roomId`/`ratePlanId`/`priceInfoId`/`vendorId`/`flightNo`/`trainNo` 等）应来自资源查询结果或用户明确指定；不要编造。
6. **创建成功后必须向用户展示资源与价格**，等待确认后再 submit；即使用户前文说“直接预订”，也不要在 create 成功同一轮自动 submit。
7. 创建与提交均为**非幂等**，失败或超时不要盲目重试；保留 `traceId` 核实。

```bash
tuniu call package-booking package_booking_create -a '{
  "baseInfo": {
    "startCityName": "南京",
    "destCityName": "北京",
    "departDate": "2026-09-10",
    "returnDate": "2026-09-13",
    "adultCount": 1,
    "childCount": 0
  },
  "resourceSpecs": [
    {
      "resourceType": "FLIGHT",
      "flight": {
        "startCityName": "南京",
        "destCityName": "北京",
        "journeyScope": "ROUND_TRIP",
        "cabinType": "ECONOMY",
        "internationalFlag": "DOMESTIC"
      }
    },
    {
      "resourceType": "HOTEL",
      "hotel": {
        "day": [1, 2, 3],
        "destCityName": "北京"
      }
    }
  ]
}'
```

**返回处理**：保存顶层 `packageSessionId`；展示 `data.resources` 与 `data.priceInfo`；核对资源类型不少于两类，以及交通方向、日期、人数、价格和币种。信息不完整时，不能自行判断为有库存、免费或已含在总价中。

#### 8.2 提交打包订订单 (package_booking_submit)

功能：补充联系人和出游人信息，对当前组合最终验价并提交订单。**可能直接创建真实订单。**

**前置条件**：
1. 使用本轮 create 返回的顶层 `packageSessionId`（不要用示例、日志或用户随口编号）
2. 已向用户展示并确认资源、日期、人数和当前价格
3. 已取得用户确认的联系人和出游人资料
4. 已告知用户本次操作可能创建真实订单，并取得明确确认

**必填参数**：`packageSessionId`、`confirmedByUser`（必须为 `true`）

**推荐传参**：`travelerCommitment`（`travelerIds` 与 `manualTravelers` 至少其一；可再传 `contactTravelerId` 或 `contactTourist`）

**互斥**：`travelerCommitment` 与 `commitment` 最多传一个。`commitment` 仅用于业务系统生成且经用户确认的完整下单信息，不要手工拼装或跨会话复用。

**变价**：仅当核验并展示新价格且用户明确接受后，传 `confirmedPriceChange=true`；否则不传。

```bash
tuniu call package-booking package_booking_submit -a '{
  "packageSessionId": "BS6NH32N31EUPS",
  "confirmedByUser": true,
  "travelerCommitment": {
    "manualTravelers": [
      {
        "name": "张三",
        "idType": "身份证",
        "idNumber": "310101199001011234",
        "mobile": "13800138000",
        "passengerType": "ADULT"
      }
    ],
    "contactTourist": {
      "name": "张三",
      "mobile": "13800138000"
    }
  }
}'
```

**订单结果判断**：
1. 存在 `data.orderResult.orderId`：订单已创建，**不再**调用提交工具；展示订单号与 `payUrl`（如有），提醒用户支付与跟进。
2. 无订单号但含 `MISSING_FIELDS`：按提示让用户补资料，重新展示清单并确认后再提交。
3. 返回 `UPSTREAM_BUSINESS_ERROR`：展示错误并停止自动提交；若详情带 `orderId`，先核实订单状态。
4. 无订单号且结果不明确：保留 `traceId`，提示用户联系客服通过订单记录或人工流程核实，**不要再次提交**。

**提交红线**：
- `confirmedByUser=true` 只表示用户确认当前组合进入真实提交，不是出游人资料承诺；不能只传 sessionId + `confirmedByUser`。
- 不要编造姓名、证件号、手机号。
- 用户改变日期、人数、资源或偏好后，应重新 create 并再次确认，不要复用旧 `packageSessionId`。
- 订单创建成功 ≠ 已支付/已出票/已履约。

---

## 响应处理

### 成功响应

stdout 输出 JSON 格式：

```json
{
  "success": true,
  "result": {...},
  "metadata": {...}
}
```

### 业务字段解析补充

- 通常 `tuniu call` 的 stdout 为统一 JSON 包装，业务结果在 `result` 内。
- 对于多数查询/下单工具，业务字段可按 JSON 对象读取。
- 对于 `getHolidayBookingRequiredInfo`、`getCruiseBookingRequiredInfo`，以及 `flight` / `intelflight` 各自的 `getBookingRequiredInfo`，返回内容为预订说明文本，应按纯文本展示，不要强行按业务 JSON 结构解析。调用时必须带正确的 server，禁止串服务。

### 错误响应

```json
{
  "success": false,
  "error": {
    "type": "ToolNotFoundError",
    "message": "工具不存在",
    "code": 102
  }
}
```

### 退出码含义

| 退出码 | 含义 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | 解析 stdout JSON |
| 101 | 连接失败 | 重试或检查网络 |
| 102 | 工具不存在 | 优先读取 `available_tools` 改用真实工具名；否则运行 `tuniu list <server> -o json` 校验 |
| 103 | 参数错误 | 运行 `tuniu help <server> <tool>` |
| 104 | 认证失败 | 优先执行 `tuniu auth status`；未授权或授权失效时执行 `tuniu auth login` |
| 105 | 超时 | 使用 `-t 60` 增加超时 |
| 106 | 服务器错误 | 联系服务提供方或稍后重试 |
| 107 | 配置错误 | 运行 `tuniu config show` 检查配置 |
| 108 | 未配置 API Key | 优先使用 OAuth：执行 `tuniu auth login`；无法浏览器授权时再提示配置 `TUNIU_API_KEY` |
| 109 | API Key 无效 | 更新 `TUNIU_API_KEY`；也可清除 API Key 后改用 `tuniu auth login` |
| 110 | 需要 OAuth 登录 | 执行 `tuniu auth login`，再用 `tuniu auth status` 确认 |
| 111 | OAuth 授权失败 | 检查 OAuth 配置/网络后重新执行 `tuniu auth login` |
| 112 | OAuth token 刷新失败 | 授权已失效，重新执行 `tuniu auth login` |
| 199 | 未知错误 | 使用 `-d` 调试模式 |

---

## 使用示例

以下示例中，所有参数均从**用户表述或上一轮结果**中解析并填入。

### 国内机票场景

**用户**：3月15号北京到上海的航班

**AI 判断**：出发/到达均为中国大陆 → `flight`

**AI 执行**：
```bash
tuniu call flight searchLowestPriceFlight -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15"}'
```

**用户**：看一下 MU5101 这个航班的舱位

**AI 执行**：
```bash
tuniu call flight multiCabinDetails -a '{"departureCityName":"北京","arrivalCityName":"上海","departureDate":"2026-03-15","flightNo":"MU5101"}'
```

### 国际机票场景

**用户**：8月15号北京到东京的机票，就我一个人

**AI 判断**：目的地为境外 → 按速查表选 `intelflight`；单人须显式传 `adult_count=1`

**AI 执行**（若列表无 `intelflight`，先 `tuniu discovery refresh && tuniu discovery list`）：
```bash
tuniu call intelflight list_intel_flights -a '{"departure_city":"北京","arrival_city":"东京","departure_date":"2026-08-15","adult_count":1}'
```

**用户**：看一下 UO235-UO652 的舱位

**AI 执行**：
```bash
tuniu call intelflight get_intel_flight_details -a '{"flight_no":"UO235-UO652","departure_city":"北京","arrival_city":"东京","departure_date":"2026-08-15"}'
```

### 酒店场景

**用户**：北京3月1号入住一晚，有什么酒店？

**AI 执行**：
```bash
tuniu call hotel tuniuHotelSearch -a '{"cityName":"北京","checkIn":"2026-03-01","checkOut":"2026-03-02"}'
```

### 门票场景

**用户**：中山陵门票多少钱？

**AI 执行**：
```bash
tuniu call ticket query_cheapest_tickets -a '{"scenic_name":"中山陵"}'
```

### 火车票场景

**用户**：3月20号南京到上海的火车票

**AI 执行**：
```bash
tuniu call train searchLowestPriceTrain -a '{"departureCityName":"南京","arrivalCityName":"上海","departureDate":"2026-03-20"}'

# 如果用户要求特定排序，例如“先看最便宜的”
tuniu call train searchLowestPriceTrain -a '{"departureCityName":"南京","arrivalCityName":"上海","departureDate":"2026-03-20","searchType":"5"}'
```

### 邮轮场景

**用户**：查一下3月17到3月30的邮轮

**AI 执行**：
```bash
tuniu call cruise searchCruiseList -a '{"departsDateBegin":"2026-03-17","departsDateEnd":"2026-03-30"}'
```

### 度假场景

**用户**：4月中旬想去三亚有什么度假线路？

**AI 判断**：明确要“度假线路” → `holiday`（不是打包订）

**AI 执行**：
```bash
tuniu call holiday searchHolidayList -a '{"keyWord":"三亚","departsDateBegin":"2026-04-10","departsDateEnd":"2026-04-20"}'
```

### 打包订场景

**用户**：南京到北京，9月10到13号，往返机票和酒店一起订

**AI 判断**：用户当前这一步明确要机酒组合 → `package-booking`；若列表无该服务，先 `tuniu discovery refresh && tuniu discovery list`

**AI 执行**：
```bash
tuniu call package-booking package_booking_create -a '{"baseInfo":{"startCityName":"南京","destCityName":"北京","departDate":"2026-09-10","returnDate":"2026-09-13","adultCount":1},"resourceSpecs":[{"resourceType":"FLIGHT","flight":{"startCityName":"南京","destCityName":"北京","journeyScope":"ROUND_TRIP","cabinType":"ECONOMY","internationalFlag":"DOMESTIC"}},{"resourceType":"HOTEL","hotel":{"day":[1,2,3],"destCityName":"北京"}}]}'
```

**AI 后续**：展示资源与总价 → 用户确认组合与出游人资料后，再调用 `package_booking_submit`（`confirmedByUser=true`）。

**信息不足示例**：用户只说“想去三亚玩” → 先澄清或做行程规划，不要默认调用 `holiday` 或 `package-booking`。

---

## 注意事项

1. **凭证安全**：绝对不要在回复或日志中暴露 OAuth token、refresh token 或 TUNIU_API_KEY
2. **PII 安全**：联系人姓名、手机号、乘客姓名、证件号仅在预订时发送至 MCP 服务，勿在日志或回复中暴露
3. **认证**：若遇认证错误（退出码 104、108、109、110、111、112），引导用户执行 `tuniu auth login --daemon`（WorkBuddy 仅支持 daemon 模式 OAuth）
4. **日期格式**：所有日期均为 `YYYY-MM-DD`
5. **参数验证**：下单前必须先调用搜索/详情接口获取必需参数（如 cabinPriceId、productId、resId、queryId、sourceId 等）
6. **翻页**：各服务翻页参数不同，注意区分
7. **支付提醒**：下单成功后必须提示用户点击支付链接完成支付
8. **调试模式**：遇到问题时使用 `-d` 参数查看详细请求/响应
9. **游轮兼容**：用户说"游轮"时等同于"邮轮"
10. **度假详情参数**：`getHolidayProductDetail` 的 `departCityCode` 等字段必须与 `searchHolidayList` 列表行一致，勿拆数组或自行拼参；`saveHolidayOrder` 的 `departDate` 必须来自详情团期日历中的可选日期
11. **邮轮下单 ID 映射**：`saveCruiseOrder.selectRes` 的 `journeyId/resourceId/subResourceId` 只能来自最近一次 `getCruiseCabinAndRoom` 返回（`resourceId/subResourceId` 必须取 `priceRes[].resId`，不能用数组下标或历史 ID）
12. **团期价格展示口径**：成人/儿童价格均需基于可售团期原始字段展示；儿童价为 0 时不展示儿童价，双 0 团期不展示
13. **订单结果提示**：下单成功后应明确展示 `orderId`/`order_id` 与支付或详情链接，并提醒用户在途牛 App/小程序跟进订单与出行通知
14. **102 处理规则**：若错误 JSON 含 `error.details.available_tools`，优先从中选择符合当前意图的真实工具名并重试；否则执行 `tuniu list <server> -o json` 获取工具名，再用 `tuniu help <server> <tool>` 或 `tuniu schema <server> -o json` 确认参数。禁止继续用错误工具名重试。
15. **国际机票下单约束**：仅支持护照；`adult_count` 默认 2，单人须显式传 `1`；`query_id`/`flight_nos`/`cabin_codes`/`vendor_id`/`expand_price_id` 必须来自同一次搜索与同一舱位方案；取消订单须用户明确确认后才调用 `cancel_intel_flight_order`
17. **打包订创建约束**：必须有出发/目的城市；显式传至少两类 `resourceSpecs`；不要依赖服务端默认组合；create 成功后不得同一轮自动 submit
18. **打包订提交约束**：`packageSessionId` 必须来自本轮 create；`confirmedByUser` 必须为 `true`；推荐 `travelerCommitment`；非幂等，超时或结果不明勿重试提交；仅当存在 `orderResult.orderId` 才视为下单成功
