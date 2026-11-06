---
name: tuniu-cli
description: 途牛旅行统一助手（推荐优先使用）- 通过 tuniu CLI 调用国内/国际机票、酒店、门票、火车票、邮轮、度假产品、打包订等 C 端旅行服务。适用于查航班、订酒店、门票、火车票、邮轮、跟团/自助/自驾等度假产品，以及机酒/酒火等组合预订。机票、酒店、度假与打包订的分流与降级规则见正文「意图分流决策表」及 references/，调用前必须遵循。【优先级】若同时安装了 tuniu-flight/tuniu-hotel/tuniu-ticket 等单独服务 skill，请优先使用本 skill。
version: 1.1.2
minCliVersion: 1.1.4
metadata: {"openclaw": {"emoji": "🧳", "category": "travel", "tags": ["途牛", "旅行", "机票", "国际机票", "酒店", "门票", "火车票", "邮轮", "预订", "度假", "打包订", "机酒"], "priority": 100, "requires": {"bins": ["node", "npm", "tuniu"], "node": ">=18.0.0"}, "env": {"TUNIU_AUTH_SOURCE": {"type": "string", "description": "OAuth 接入源：tuniu-cli / workbuddy / doubao；平台注入时优先使用", "required": false}, "TUNIU_API_KEY": {"type": "string", "description": "普通服务 API Key 兜底凭证", "required": false}}}}
---

# 途牛旅行助手

> **首次调用任一服务前，必须先 Read `references/<server>.md` 确认工具名与参数，禁止凭记忆拼写工具名。** 下单/取消、参数不确定或工具报错时同样必须先读该 reference。若文件不存在，改用 `tuniu schema <server> -o json`，必要时再 `tuniu help <server> <tool>`。

当用户询问航班、酒店、门票、火车票、邮轮、度假产品、打包订等旅行服务时，通过 **tuniu CLI** 调用途牛服务。

## 意图分流决策表

### 酒店

酒店住宿需求使用 `hotel`（`references/hotel.md`），首选工具 `tuniuHotelSearch`。

### 机票国内 / 国际分流（调用前必须执行）

收到机票/航班类需求时，**先按出发地、目的地判断航线类型，再选 server**，不要直接默认 `flight`：

| 航线类型 | 判断依据（以城市为准） | server | 参考文件 | 首选工具 |
|----------|------------------------|--------|----------|----------|
| **国内** | 出发地与目的地均为中国大陆城市 | `flight` | `references/flight.md` | `searchLowestPriceFlight` |
| **国际** | 出发地或目的地任一为境外（含港澳台） | `intelflight` | `references/intelflight.md` | `list_intel_flights` |

**分流规则**：

1. **以出发地/目的地为准**；用户口头说「国内/国际/出国」仅作参考。冲突时按城市判断选 server。
2. 无法判断时先向用户确认航线类型，**确认前不要调用任一机票 MCP**。
3. 国内只用 `flight`，国际只用 `intelflight`；工具名与参数体系不同，不可混用。
4. 列表无 `intelflight` 时 → `tuniu discovery refresh && tuniu discovery list`。
5. **往返、多城按每一航段独立判断**；单次 `tuniu call` 只能选一个 server。

### 度假产品 / 打包订：意图识别

| 能力 | 用户要什么 | 参考文件 | 首选工具 |
|------|------------|----------|----------|
| `holiday` | 买已上架成品线路（产品、团期） | `references/holiday.md` | `searchHolidayList` |
| `package-booking` | 机票/火车/酒店/门票中**至少两类**自由组合 | `references/package-booking.md` | `package_booking_create` |
| 单品服务 | 只查/只订一类资源 | 对应 `references/<server>.md` | 见该服务 |

**判定顺序（命中即停）**：① 明确要产品/线路/团期 → `holiday`；② 明确至少两类资源组合 → `package-booking`，首调 `package_booking_create`（确认后才 `submit`）；③ 只一类资源 → 单品服务；④ 意图不清（如「想去三亚玩」）→ 先问一句，不要默认调 `holiday` 或 `package-booking`。

### 用户说什么 → 用什么服务

国内 / 国际机票、度假 / 打包订的分流与降级规则见上文对应章节。其余意图按下表：

| 用户意图 | server | 参考文件 | 首选工具 |
|----------|--------|----------|----------|
| 门票/景点门票 | `ticket` | `references/ticket.md` | `query_cheapest_tickets` |
| 火车票/高铁/动车 | `train` | `references/train.md` | `searchLowestPriceTrain` |
| 邮轮/游轮 | `cruise` | `references/cruise.md` | `searchCruiseList` |

## 环境自检

运行环境须 Node.js 18+ 与 tuniu-cli。首次调用前执行：

```bash
node --version    # 须 >= 18
npm --version
# 若 tuniu 未安装：npm install -g tuniu-cli@latest
tuniu --version   # 须 >= 头部 minCliVersion；不足则 tuniu update
```

## 认证与 API Key 安全

优先使用 OAuth；OAuth 不可用时可用 `TUNIU_API_KEY` 兜底。

### OAuth 接入源（source）

各宿主 OAuth token **互相隔离**；`auth` / `call` / `help` / `list` / `schema` / `health`等需凭证命令须同源，否则出现「已登录但仍提示未授权」。

本宿主自行判断 source：WorkBuddy→`workbuddy`，豆包→`doubao`，其他 Agent / 普通终端→`tuniu-cli`。CLI 解析优先级：`--source` > `TUNIU_AUTH_SOURCE` > `auth use` 持久化 > 默认 `tuniu-cli`。

**会话首次业务调用前必须、且只需执行一次**只读检查 `tuniu auth use --show`；对齐完成后不要每条命令重复检查。按 `resolved_source`（实际生效值）与 `source_resolution`（`env` / `config` / `default`）处理：

| `source_resolution` | 条件 | 动作 |
|---|---|---|
| 任意 | 已是本宿主 | 不写 `auth use`；后续可省略 `--source` |
| `config` | 指向其他宿主残留 | `tuniu auth use <本宿主source>` 修正一次即可；禁止每会话无条件写（会改整机默认） |
| `env` | 值非本宿主 | **不要** `auth use`（盖不过 env）；本会话全程显式 `--source` |
| `default` | 本宿主非 `tuniu-cli` | `auth use <本宿主source>`，或全程显式 `--source` |

修正后按当前 source 检查授权：`tuniu auth status --source <source>`；未授权则 `tuniu auth login --source <source>`（WorkBuddy 等会结束 auth 子进程的宿主必须加 `--daemon`，拿到授权 URL 后能打开浏览器则直接打开，不要只贴链接等用户复制）；业务调用保持同一 source。

### API Key 兜底

OAuth 不可用时可用 `TUNIU_API_KEY`：

```bash
export TUNIU_API_KEY=your_api_key
```

### 凭证安全约束

- 已配置凭证时直接调用，不要要求用户重复提供；认证失败（退出码 104、108–112）按退出码表处理：优先确认 source 并重新 OAuth 登录，API Key 兜底失败时提示更新 Key。
- **不要明文复述密钥**；确认时仅可用后四位等脱敏形式（如 `****abcd`）。
- 不要代替用户执行含完整密钥的命令；持久化由用户在本地终端自行设置。
- 配置文件 `~/.tuniu-mcp/config.json` 仅作最后兜底，须 `chmod 600`。

## 基本命令

### 业务调用

```bash
tuniu call <server> <tool> --source <source> -a '<JSON参数>'
tuniu list [server] --source <source>              # 列出服务/工具（列工具时需同源）
tuniu help <server> [<tool>] --source <source>     # 查看参数说明（调用前不确定参数时必用）
tuniu schema [server] --source <source>            # 导出工具 Schema（可加 -o json）；references 缺失时必用
tuniu health [server] --source <source>            # 健康检查
tuniu update                     # 一键更新 CLI（并刷新本机已安装的 skill）
tuniu discovery refresh && tuniu discovery list   # 刷新服务列表
```

`--args` / `-a` 必须是合法 JSON 字符串；无参数用 `-a '{}'`。中文可直接写入。

### 服务工具链路（概览）

| 服务 | 搜索 → 详情 → 下单 |
|------|-------------------|
| `flight` | `searchLowestPriceFlight` → `multiCabinDetails` → `getBookingRequiredInfo` → `saveOrder` |
| `intelflight` | `list_intel_flights` → `get_intel_flight_details` → `getBookingRequiredInfo` → `create_intel_flight_order` |
| `hotel` | `tuniuHotelSearch` → `tuniuHotelDetail` → `tuniuHotelCreateOrder` |
| `ticket` | `query_cheapest_tickets` → `create_ticket_order` |
| `train` | `searchLowestPriceTrain` → `queryTrainDetail` → `bookTrain` |
| `cruise` | `searchCruiseList` → `getCruiseProductDetail` → `getCruiseCabinAndRoom` → `saveCruiseOrder` |
| `holiday` | `searchHolidayList` → `getHolidayProductDetail` → `saveHolidayOrder` |
| `package-booking` | `package_booking_create` →（确认）→ `package_booking_submit` |

各服务调用模板、翻页规则、展示规范、场景示例见对应 `references/<server>.md`。

## 服务发现

以下情况须先 `tuniu discovery refresh && tuniu discovery list`：

- 用户需求不在已知服务列表中
- 工具不存在（退出码 102）
- 首次使用 / 无 `intelflight` / 无 `package-booking`

## 响应与退出码

成功时 stdout 为 JSON：`{"success": true, "result": {...}}`。`getBookingRequiredInfo`、`getHolidayBookingRequiredInfo`、`getCruiseBookingRequiredInfo` 返回纯文本，勿强行 JSON 解析。

| 退出码 | 含义 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | 解析 stdout JSON |
| 101 | 连接失败 | 重试或检查网络 |
| 102 | 工具不存在 | 优先读取 `error.details.available_tools` 改用真实工具名并重试；否则 `tuniu list <server> -o json`，再用 `tuniu help` 或 `tuniu schema <server> -o json` 确认。禁止继续用错误工具名重试 |
| 103 | 参数错误 | 运行 `tuniu help <server> <tool>` |
| 104 | 认证失败 | 检查 OAuth / `TUNIU_API_KEY` |
| 105 | 超时 | 使用 `-t 60` 增加超时 |
| 106 | 服务器错误 | 联系服务提供方或稍后重试 |
| 107 | 配置错误 | 运行 `tuniu config show` 检查配置 |
| 108 | 未配置 API Key | 优先 OAuth；必要时设置 `TUNIU_API_KEY` |
| 109 | API Key 无效 | 更新 `TUNIU_API_KEY`，或改用 OAuth |
| 110 | 需要 OAuth 登录 | 按当前 source 执行 `tuniu auth login --source <source>`（daemon 环境加 `--daemon`），再用 `tuniu auth status --source <source>` 确认 |
| 111 | OAuth 授权失败 | 检查 OAuth 配置/网络后，按同一 source 重新 `tuniu auth login --source <source>` |
| 112 | OAuth token 刷新失败 | 当前 source 授权已失效，重新执行 `tuniu auth login --source <source>` |
| 199 | 未知错误 | 使用 `-d` 调试模式 |

## 全局约束

1. **凭证与 PII 安全**：勿在回复或日志中暴露 OAuth token、refresh token、`TUNIU_API_KEY`；联系人姓名、手机号、乘客姓名、证件号仅在预订时发送至 MCP 服务。
2. **认证**：认证错误（退出码 104、108、109、110、111、112）先确认 source，再 `tuniu auth login/status --source <source>`。
3. **日期格式**：所有日期均为 `YYYY-MM-DD`。
4. **参数验证**：下单前必须先调用搜索/详情接口获取必需参数（如 `cabinPriceId`、`productId`、`resId`、`queryId`、`sourceId`、`preBookParam` 等）。
5. **翻页**：各服务翻页参数不同，注意区分（详见各 `references/<server>.md`）。
6. **下单结果**：下单成功后展示 `orderId`/`order_id` 与支付或详情链接，提醒用户完成支付，并在途牛 App/小程序跟进订单与出行通知。
7. **调试模式**：遇到问题时使用 `-d` 参数查看详细请求/响应。
8. **团期价格展示**：成人/儿童价格均需基于可售团期原始字段展示；儿童价为 0 时不展示儿童价，双 0 团期不展示。

## 其他命令

### 认证

```bash
tuniu auth status --source <source>          # 查看指定接入源授权状态
tuniu auth login --source <source>           # 登录授权（CLI 打开浏览器并阻塞至完成）
tuniu auth login --daemon --source <source>  # daemon 模式：输出授权 URL 后立即退出
tuniu auth use <source>                      # 持久化默认 source（写入 config.json）
tuniu auth use --show                        # 查看当前默认 source 与解析结果
tuniu auth use --clear                       # 清除持久化默认 source
tuniu auth logout --source <source>          # 清除当前 source 的本地 OAuth 授权
tuniu auth logout --all                      # 清除当前 profile 下全部 source
```

### CLI 更新

```bash
tuniu update                     # 检查并更新 CLI 到 npm latest，并刷新本机已安装的 skill
tuniu update --check             # 仅检查是否有新版本（不安装）
tuniu update --cli-only          # 只更新 CLI，不刷新 skill
tuniu update --to <version>      # 更新到指定版本
tuniu -V                         # 查看当前 CLI 版本
```

Agent 发现 CLI/Skill 过旧或能力缺失时，优先执行 `tuniu update`，不要手工卸载/清缓存再装。仅刷新 Skill 时用 `tuniu skill install`。

### Skill 管理

```bash
tuniu skill install              # 安装/更新 skill（默认 ~/.agents/skills/tuniu-cli/）
tuniu skill install --agent cursor,claude   # 指定 Agent
tuniu skill install --agent all             # 刷新本机已安装 tuniu-cli 的全部位置
tuniu skill install --dir <skills根目录>    # 自定义目录
tuniu skill version              # 查看已安装 skill 版本
```

安装产物含 `SKILL.md` + `references/`；优先从开放平台下载 zip，失败则用 CLI 内置 `skill/` 目录。

### 配置

```bash
tuniu config show                # 查看当前配置（退出码 107 时排查）
tuniu config init                # 初始化配置文件
tuniu config init -f             # 覆盖已有配置
tuniu config set <key> <value>   # 设置配置项
```

默认配置文件：`~/.tuniu-mcp/config.json`。

## Skill 版本

CLI 版本须 ≥ 头部 `minCliVersion`；不足时执行 `tuniu update`。查看版本：`tuniu -V` / `tuniu skill version`。
