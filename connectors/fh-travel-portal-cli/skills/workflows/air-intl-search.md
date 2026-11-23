# 国际机票查询、选舱与下单跳转（workflows/air-intl-search.md）

> 加载时机：进入国际机票（含港澳台）查询/预订流程时加载本文件。工具参数级契约见
> `references/tool-catalog.md`；连接与认证见 `references/cli-connection.md`。

## 快速通道（先抄命令，再读细节）

**本节目标：正常场景零探索完成查询到交付。禁止为了"了解脚本怎么用"去读脚本源码——
`--help` 和本节已覆盖全部用法。** 标准路径直接跑一条龙（自动发号）。交付读 `run_summary.json` 的 `html`。

### 首选：一条龙（单程/往返标准链路，1 次调用完成 S1→S3′）

```bash
# 中文城市名直接传入；日期兼容 2026-09-20 / 9.20（缺省当年）。
$PY -u scripts/air_intl_query.py --from 北京 --to 新加坡 --date 2026-09-20            # 单程
$PY -u scripts/air_intl_query.py --from 北京 --to 莫斯科 --date 2026-09-20 --return 2026-09-25   # 往返
#   内部自动完成：城市码 → 1 次 intl_shopping 组合查询（往返=同一 tripList 双段）→ 决策级摘要
#   → inline --scope best:5（默认）全量单页
#   页面结构：按推荐评分 Top5 精选内联舱位+免登下单链接；其余全部航班带「查舱位」按钮
#   （点击页内 fetch busi intlShop，头 infoCode；纯静态 HTML，无 server）
#   逐步计时并打印产物绝对路径；完成后 present_files 
#   可选: --scope best:N|direct   --rows N   --adults N   --skip-cabins(仅纯价格/时刻展示，不适用于预订意图)
#   失败时脚本打印出错步骤与降级命令，只重试该步骤，不要重跑整条链路
```

**展示：用 present_files 直接打开本地 HTML 文件。禁止启动任何本地 HTTP server**
（`python -m http.server`、cabin_query_server 等）。

### 分步版（一条龙失败后的降级，或需要拆步/补查时用）

```bash
PY=python3
# 分步才需要先 python -u scripts/portal_config.py 取号；标准路径 air_intl_query.py 已自动发号
RUNS=~/.fh-travel-workspace/fh-travel-runs/<run-id> 

# S1 城市码（本地缓存，秒回；exit 1 才调 air_city）
$PY scripts/air_intl_resolve_city.py 深圳 巴厘岛

# S2 查询（一条龙失败后的拆步重试；标准路径请用 air_intl_query.py）
$PY scripts/fh_travel.py tools/call '{"name":"intl_shopping","arguments":{
  "language":"cn","passengerType":"ADT","passengerCount":1,
  "tripList":[{"fromCity":"SZX","toCity":"DPS","flyDate":"2026-09-16","isFromCity":false,"isToCity":false}]}}' \
  > "$RUNS/raw_intl_shopping.json"

# S3 解析（stdout 摘要已含 行李/退改/中转机场+停留/同机场/廉价航/门到门——直接可决策，不要再 python -c 挖字段）
$PY scripts/air_intl_parse_shopping.py "$RUNS/raw_intl_shopping.json" --output "$RUNS/parsed.json" --rows 15

# S3′(S4+S6) 查舱位 + 渲染全量单页，二选一：
$PY scripts/air_intl_book.py inline --parsed "$RUNS/parsed.json" --out-dir "$RUNS/_inline" \
    --scope best:5 --title "深圳 → 巴厘岛 · 2026-09-16" --meta "1 成人 · 单程"
#   · best:N（推荐默认）＝精选评分：直飞>>单中转>多中转、同机场中转、门到门+价格、
#     非廉价航（IBELCC）、可退改/含托运加分；只对精选查舱位，但**渲染全量航班**：
#     精选内联舱位，其余带「查舱位」按钮（点击页内 fetch busi intlShop / infoCode；不可用只显示原因可重试，无复制降级）
#   · direct ＝仅直飞（有直飞且想全展示时用）；top:N ＝原始顺序前 N（不排序，不推荐）
#   · 完成后脚本自检并打印产物绝对路径；目录为空会报错，不要再去全盘 Glob 搜文件
```

**路径**：给脚本传 `--out-dir`/`--output`/文件路径时，用宿主操作系统的原生路径形式
（Windows 为盘符形式，如 `C:/...`；macOS/Linux 为 `/...`）；Windows 下不要用 Git Bash 的
`/c/...`（会被解析成错误盘符路径）。所有路径都从当前工作区推导，不要写死某台机器的绝对路径。
脚本只用 Python 标准库，认证由 fh CLI 自管（`~/.fh/credentials`）。
`air_intl_parse_shopping.py` 也能直接吃已解析的 `parsed.json`（顶层有 `flights[]`）重印摘要——
想再看行李/中转时重跑 parse 即可，禁止 `python -c` 手挖 JSON。

本篇覆盖工具：`air_city`（scope=INTERNATIONAL）、`intl_shopping`、`intl_multi_shopping`、
`intl_shopping_all_cab`、`intl_rule`。

**能力边界（先读）**：总入口见 `SKILL.md` 一。当前服务端只暴露只读查询。验价、政策/申请单、
乘机人证件、创单、支付、出票、退改签均未暴露——本流程**不到下单**，止于「选定舱位 → 拼下单页
跳转 URL」。未暴露能力见 `references/air-intl-capability-gap.md`，不得伪造调用。

## 阶段总链

```
S0 需求澄清（含行程模式判定） → S1 代码解析（按需） → S2 组合查询
  → S3 展示与选定（serialNumber + 查询 priceId）
  → S4 更多舱位（intl_shopping_all_cab，下单跳转的强制前置）
  → S5 [可选] 规则查询（intl_rule）
  → S6 拼下单页跳转 URL（portal 落单，流程结束）
```

回退原则：用户改城市/日期/人数/行程模式 → 回 S2 重查（serialNumber、priceId 全部作废，
以新查询为准）；改组合/运价 → 回 S3。

**下单跳转自动衔接（重要）**：凡是要落到「下单页跳转」的查询（用户表露下单/预订意图，
或宿主默认把国际查询当作可预订场景），S3 用户选定航班后**必须自动衔接** S4（查全部舱位）
→ 用户选舱 → S6 拼下单页 URL（`scripts/air_intl_build_order_jump_url.py`），不得停在 S3 等用户
再问。下单页跳转只需 `serialNumber + 舱位 priceId`（**不经过验价**）。两步字段来源铁律
与跳转契约见 [`references/air-intl-sso-forward.md`](../references/air-intl-sso-forward.md)。

标准查询走 `air_intl_query.py` 一条龙（内部 `fh_travel`），不要改用宿主侧
`mcp__…__intl_shopping` / ToolSearch。拆步补查时才直接调工具。每个查询、舱位/运价页
展示后停轮，等待用户选择；不要在同一用户轮连续替用户推进多个决策节点。

## 会话事实账本（内部，不对用户展示）

```text
requestGeneration, tripMode, tripList, language, passengerType, passengerCount, filters
serialNumber, selectedQueryPriceIdsByLeg, selectedCabPriceIdsByLeg, jumpUrl
```

任何新 shopping 都开启新 generation，并废弃旧 `serialNumber/priceId` 与旧跳转 URL。
改组合/舱位时清除对应舱位 priceId 与 jumpUrl。

---

## S0 需求澄清（不调工具）

核心槽位：**出发地、目的地、出发日期**；往返另需**返程日期**；多程需**每一段**的
城市与日期。人数默认 1，成人默认（儿童/婴儿须问清）。

**行程模式判定（查询前必须先定，互斥）**：

| 模式 | 判定 | 查询工具 |
|---|---|---|
| 单程 | 1 个航段，无返程含义 | `intl_shopping`，tripList 传 1 项 |
| 普通往返 | 2 个航段且第 2 段与第 1 段起终点互反 | **只调用 1 次** `intl_shopping`，同一 `tripList` 传 2 项（第 2 项起终点与第 1 项**互换**），返回 1 组往返组合结果 |
| 多程 / 逐程自由组合 | ≥2 个航段且**不是**普通往返（开口程、环游、用户明确「逐程/自己组合」） | `intl_multi_shopping`，tripList 传**全部**航段、按实际出行**原始顺序** |

- `intl_multi_shopping` **不是**普通往返的默认工具；禁止漏段、调序、重复航段。
- 普通往返**禁止**拆成两个单程 `intl_shopping` 请求；两次单程结果不能替代一次往返组合结果。
- 判定前必须扫描完整消息中的全部“出发地→目的地+日期”，不能读到第一段完整就默认单程；
  恰好两段只有方向互反才是普通往返，其余两段也属于多程。
- 当前服务端的 `intl_multi_shopping` 接受整组 `tripList`，没有逐腿卡片状态工具；必须按
  `tool-catalog` schema 一次提交全部航段，不得调用不存在的 `confirmTrip`、
  `intPolicy`、`intCheckApplication` 或 `waitSave`。
- 缺槽一次问齐；相对日期自行换算 `yyyy-MM-dd`。

## S1 代码解析（`air_city` 关键词检索，scope=INTERNATIONAL）

- **标准路径**：一条龙内部已调 `air_intl_resolve_city.py`——**缓存优先；未命中自动**
  `air_city`（`scope=INTERNATIONAL`，禁止 `AUTO`）并**合并回写**缓存。助手不要为补缓存去读
  脚本源码、不要手工 `--ingest`、不要并行多次入库。
- 分步自测：`python3 scripts/air_intl_resolve_city.py 北京 新加坡`（exit 0 即全部可用）。
- 从候选取 **`code`** 进 S2：`aggregate=true` 用城市聚合码且 `isFromCity/isToCity=true`；
  无聚合则用机场码、标志 false。不要调用已下线的 `intl_city`。
- 展示名/国家名可取本轮 `cityName`/`airPort`/`countryName`（缺失勿编造）。
- 仍未命中：换更短中文/英文关键词后重跑一条龙。**禁止凭模型记忆编造代码。**

## S2 组合查询（`intl_shopping` / `intl_multi_shopping`）

公共必填参数：

| 字段 | 取值 |
|---|---|
| `language` | `cn`=中文，`en`=英文 |
| `passengerType` | `ADT`=成人，`CHD`=儿童，`INF`=婴儿 |
| `tripList` | 每项：`fromCity`、`toCity`、`flyDate`（yyyy-MM-dd）、`isFromCity`、`isToCity`。**代码选城市聚合码时标志传 true，选具体机场码时传 false** |

公共可选参数：`passengerCount`（建议显式传，且与 S6 跳转 URL 的 `adultCount` **必须一致**）、
`cabClass`（列表：FIRST/PREMIUM_FIRST/BUSINESS/PREMIUM_BUSINESS/ECONOMY/
PREMIUM_ECONOMY）、`stopQuantity`（0=直飞，1=最多一次中转，2=最多两次中转）、
`onlyBigCustomerPrice`（只查大客户协议价）、`airIdList`（航司二字码列表）、
`showLcc`（含低成本航空，默认 false）、`clientId`（省略按登录态解析）。

仅 `intl_shopping` 有：`preferences`（只传实际需要的字段）——`transport`（交通偏好）、
`allianceCode`（航空联盟）、`changeable`（要求可改签）、`refundable`（要求可退）、
`upgradable`（要求可升舱）、`freeBaggageOnly`（仅含免费行李额运价）。
**`intl_multi_shopping` 没有 preferences，禁止虚构该字段。**

返回：`serialNumber`（查询会话标识）、`forwardCode`/`infoCode`（最外层短时效授权码）、`groupList`（航班组合）、`priceList`
（含**查询 priceId**）、`cityList/airwayList/baggageList`。

## S3 展示与选定

**标准路径**走 `air_intl_query.py`（内部 parse + `air_intl_book.py inline`），交付
`run_summary.json` 的 `html`。不要再对同一轮结果跑下面的 `parse --html` /
`--action select-flight`。以下是**拆步 / 多程定制**才用的解析与选航班页。

- `intl_shopping`：业务在 `structuredContent`（含 `serialNumber/groupList/priceList`）——
  **不要逐段阅读大响应**，交给 `air_intl_parse_shopping.py` 即可。读法见
  [`references/mcp-envelope.md`](../references/mcp-envelope.md)。宿主 Agent 按
  `references/air-intl-page.md` 从解析结果生成交互页。
- 结果超过宿主上下文限制并被保存为 `.txt/.json` 文件时，**优先一步完成**（解析 + 渲染）：
  `python3 scripts/air_intl_parse_shopping.py <结果文件> --json --html <输出.html> --title "<出发地> → <目的地> · <日期>" --meta "<人数>" --meta "<舱等/筛选条件>"`。
  `--html` 会内部调用 `air_intl_render_flight_options.py`，生成自包含 `.html` 与同目录页面外
  `.selection-map.json`（`generation` 一致）。
- 若需要只解析不渲染（如仅需结构化数据给下游流程），退回两步：
  `python3 scripts/air_intl_parse_shopping.py <结果文件> --json [--dest <最终到达机场码>]`，随后在同一轮
  **必须**执行
  `python3 scripts/air_intl_render_flight_options.py <parsed文件> --title "<出发地> → <目的地> · <日期>" --meta "<人数>" --meta "<舱等/筛选条件>"`。
  脚本会解封（读 `structuredContent`）取出真实
  `serialNumber/groupId/priceId`，并生成
  同目录 `parsed_<原文件名>.json`；渲染脚本生成自包含 `.html` 和页面外
  `.selection-map.json`。不要让模型重新手工解析大结果或临场手写页面。
  展示名称优先取服务端 `cityList/airwayList`，缺失时才读取 `references/air-intl-iata-codes.md` 回退；
  该映射禁止用于 API 入参。若解析结果无法恢复真实 `serialNumber`（text 块与
  flight-data 都缺失），只能展示、不得进入选舱与跳转；应重新执行本轮查询取得完整响应。
- `intl_multi_shopping`：解析本轮业务载荷（`structuredContent`），
  使用同一通用交互契约生成多程组合与运价页。
- 页面结果不得把本轮有效方案擅自收敛、把中转方案称为“噪音”，或给未被接口标记的方案
  添加“异常”结论。初始只显示前 20 条可以，但筛选、分页或“显示更多”必须能访问本轮全部
  有效方案。
- 结束本轮前检查：HTML 文件存在，并实际调用 `present_files` 打开本地 HTML 路径，禁止 `http.server`。
  **拆步 select-flight / select-cabin** 另需选择映射存在、与 HTML 同一 `generation`、记录数等于
  `flightCount`。任一项未完成，不得声称“已生成/已打开”。
- 用户选定组合与运价后，记下 **serialNumber + 该运价的查询 priceId**
  （取自 `priceList[].priceId`，**不是** groupId）。

## S3′ 脚本拆步

适用：一条龙失败需拆步补查。

S3 解析后默认走 `air_intl_book.py inline`：批量查舱位，精选航班内联舱位并带 HTTPS forward「去下单」链接；其余航班由页面内按钮打 busi `intlShop`（infoCode）查舱位并原地渲染。不要启动本地 HTTP server，也不要把复制指令发回对话框。展示用 `present_files` 打开本地 HTML。

```
S2  python3 scripts/fh_travel.py tools/call intl_shopping ...
        → air_intl_parse_shopping.py --json --output parsed.json

S3+S4+S6 一气呵成（推荐，0 直飞/中转多时用 best:N，有直飞可 direct 或 best:N）：
    python3 scripts/air_intl_book.py inline --parsed parsed.json \
        --scope best:8 --title "<出发地> → <目的地> · <日期>" --meta "<人数>"

仅当要看单班独立舱位页（如 inline 未覆盖某航班）才退回：
    python3 scripts/air_intl_book.py cabins --map <selection-map.json> --option F090

仅当要复用已有舱位 priceId 单独拼下单跳转链接才退回：
    python3 scripts/air_intl_book.py order --serial-number ... --price-id ... \
        --adult 1 --fly-type ONEWAY --pay-type 1 --forward-code <forwardCode>
        → 默认 HTTPS forward URL（query authCode=forwardCode）
```

**关键脚本职责（固化进源仓库，非临时拼凑）**：

- `mcp_proxy.py`：fh CLI 兼容层。接口仍是 `McpProxy(...).request("tools/call", ...)`，
  内部子进程调 `fh dev call <op>`；认证/刷新由 fh CLI 自行附加，Python 不再取 token、不携带。
- `fh_travel.py`：`tools/call` 通用入口（供各业务脚本以子进程方式调用），内部经
  `mcp_proxy.py` 走 fh CLI；认证由 fh CLI 自管，不再读本脚本自己的环境变量。
- `air_intl_book.py`：S4→S6 编排（v2.2.0 起推荐 `inline`）。
  - `inline` 子命令：批量调 `intl_shopping_all_cab` 聚合 `cabins_by_option.json`，调
    `air_intl_render_flight_options.py --action inline-cabins` 渲染内联舱位页（每舱位一个 HTTPS forward
    「去下单」`<a>` 链接，scope=direct|all|top:N 控制 batch 范围）。
  - `cabins` 子命令：取单航班全部舱位，调 `--action select-cabin` 渲染独立舱位页（仅当 inline
    未覆盖某航班时兜底）。
  - `order` 子命令：拼下单跳转 URL，**HTTPS forward（query authCode=forwardCode）**。
- `air_intl_render_flight_options.py`：v2.2.0 起**默认 inline-cabins**——舱位直接展开在航班行下，每舱位一个
  真 `<a href>` HTTPS `/oauth2/forward?authCode=<forwardCode>` 链接。**已彻底移除** replyBox/copyBtn/
  旧版 `选择 #Fxxx`/`查舱位 #Fxxx` 复制指令与自定义协议深链（这些在 web/预览沙箱里会弹 JS shell
  或“闪退无记录”）。  `select-cabin` 模式仍派发 `fh-travel-select` 事件/postMessage 供宿主原生
  场景使用，但不依赖该回传链路作为唯一路径。
- ~~`cabin_query_server.py`~~（v2.5.0 引入的本地补查服务器）：**v3.0.0 起已删除，全面禁止
  启动任何本地 HTTP server**（含 `python -m http.server`）。2026-09-04 实测翻车：莫斯科会话
  启 server 后预览报"无法加载该文件"，用户明确禁止。替代方案：无舱位/非精选
  航班卡片渲染「查舱位」按钮，**点击页内直调** busi `GET .../busi/air/intl/intlShop?type=allCab`
  （请求头 `X-Auth-Code: infoCode`），查到舱位原地渲染舱位表 +
  每舱位「去下单」forward 链接（JS 复刻 `build_order_route`/`build_forward_url`）。
  infoCode 过期/网络断时 JS 就地显示原因并允许重试。
  **v6.0.2 起按钮为三态**：查询成功后变「收起舱位」，再点收起、再点「展开舱位」恢复
  （结果缓存于页内 `CABIN_CACHE`，不重复打 intlShop）；点击时 `preventDefault` 拦下 summary
  的 details 默认 toggle。展示一律 present_files 直接打开本地 HTML。

**兜底链路的硬性约束（与宿主原生链路一致）**：下单跳转只需 serialNumber + 舱位 priceId，
不经过验价；inline 页 forward 链接带 `forwardCode`（本机本地页短时效，过期需重新生成）；选舱位报
「航班数据已过期」一律回 S2 重查。

## S4 更多舱位（`intl_shopping_all_cab`，下单跳转的强制前置）

- **下单跳转路径下为强制步骤**：要落到下单页 `#/bookingPricing` 时必须拿到舱位级
  `priceId`，不得拿 S3 组合查询的单值 priceId 拼单。
- **标准路径** `air_intl_query.py` / `air_intl_book.py inline` 内部已经批量调本工具，不要再逐航班手调。
  **拆步**才单独调；仅当 inline 未覆盖某航班、需看单班独立舱位页时才退回
  `air_intl_book.py cabins --option Fxxx`。
- 纯查询（不表露下单意图、也不要求跳转下单页）时才是可选的：仅当现有 priceList
  **不满足**用户需求（要看别的舱等/票价类型）时调用；不是重新查询航班。
- 参数：`serialNumber` + 查询 `priceId`（S3 同一对值，必须是**当次** shopping 的新鲜值，
  旧 serialNumber 会报「航班数据已过期」）；`internal` 普通场景 false。
- 调用成功后由宿主 Agent 基于原始结果重做运价页并停轮。用户改选新舱位 → 以新舱位
  priceId 拼单，旧选择作废。
- **下单页跳转注意**：本步骤产的舱位级 `priceId`（三段式 `x/y/n`）才是下单页
  `flightList[].priceId` 的合法值，不能拿 S3 组合查询的单值 priceId 直接拼单。跳转契约见
  [`references/air-intl-sso-forward.md`](../references/air-intl-sso-forward.md) 的「下单页（两步契约）」。

## S5 规则查询（`intl_rule`，用户问退改/行李时）

- 参数：`serialNumber` + 查询 `priceId`（与 S3 同一对值）；`pricingId` **省略不传**
  （验价能力未暴露，不存在真实 pricingId，禁止用查询 priceId 冒充）。
- 所有退/改/误机/舱位/行李规则**以接口返回为准**，不得按航司或舱等推断。

## S6 拼下单页跳转 URL（流程终点，不落单）

- 用 `scripts/air_intl_build_order_jump_url.py` 把 S4 产出的 `serialNumber + 舱位 priceId` 二元组
  拼成下单页 `#/bookingPricing` 路由；参数表与编码铁律见
  [`references/air-intl-sso-forward.md`](../references/air-intl-sso-forward.md)。页面按钮生成规范见
  `references/air-intl-page.md`。**授权码处理**：
  - 「去下单」走 HTTPS `/oauth2/forward?authCode=<forwardCode>`（本机本地页短时效）。
  - 页内「查舱位」走 busi `intlShop`，请求头 `X-Auth-Code` = `infoCode`。
  - 查询结果 HTML/JS 字段名只用 `infoCode` / `forwardCode`，不要写 `token`。
- 对用户如实表述：「点击跳转到飞鹤商旅完成下单与支付」。**禁止**声称已下单、已支付或
  已出票；portal 页面内的后续状态以 portal 为准，不要代答。
- 跳转 URL 生成后流程结束；用户改航班/舱位 → 回 S3/S4，改城市/日期/人数 → 回 S2。

---

## 失败与边界速查

| 场景 | 动作 |
|---|---|
| 城市代码被接口拒绝 | 回 S1 用 `air_city`（scope=INTERNATIONAL）关键词检索重新取码后重查 |
| 查询结果为空 | 如实告知，建议改日期/放宽中转或舱等；禁止编造航班 |
| 信封 `ok=false` 或业务错误 | 按 `mcp-envelope.md` / `error-handling.md` 分流；禁止把失败说成没有航班 |
| 选舱位报「航班数据已过期」 | serialNumber 失效，回 S2 重查后重走 S3→S4 |
| 用户要核价/政策/申请单/创单 | 读 `references/air-intl-capability-gap.md` 如实说明能力未暴露，引导去 portal 完成 |
| 用户要支付/出票/改签/退票/查订单 | 超边界：说明只能查询与跳转下单，引导去飞鹤 portal 或转人工 |
| 用户改订国内票 | 转 `workflows/air-domestic-search.md` |

若 S2 原始结果文件已落盘（排障/续跑），可用一条龙 `--raw` 只做出页，不要改成宿主手调：

```bash
$PY scripts/air_intl_query.py --raw "$RUNS/raw_intl_shopping.json" \
  --from 深圳 --to 首尔 --date 2026-09-08 --run-id <run-id>
```

预订、订票、去下单或“最便宜可订”意图不得使用 `--skip-cabins`，也不得直接把
`air_intl_parse_shopping.py --html` 的 `select-flight` 结果作为最终交付；最终交付必须是
`air_intl_book.py inline` 生成的 `flights_inline.html`。
