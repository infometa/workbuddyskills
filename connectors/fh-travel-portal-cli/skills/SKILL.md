---
name: feihe-portal
display_name: 飞鹤商旅
display_name_en: Feihe Air Travel
description: 通过 fh CLI 查询、比较国内/国际机票，并跳转飞鹤商旅页面完成预订。适用于飞鹤商旅、国内机票、国际机票、航班查询、航班筛选、差旅预订等请求；命令行调用，宿主零 MCP 依赖，标准查询脚本出交互页面。使用前必须先登录：fh auth status 检查，无凭据先 fh auth login。
description_zh: 飞鹤企业差旅国内/国际机票查询助手（fh CLI 版），支持航班比选、舱位与退改规则查询，并跳转飞鹤商旅页面完成预订
description_en: Feihe corporate travel assistant for domestic/international flight search, cabin and fare-rule lookup, with SSO handoff to the Feihe portal for booking (invoked via the fh CLI; no host MCP required)
version: 1.0.2
metadata:
  openclaw:
    requires:
      bins:
        - python3
    category: travel
    emoji: "✈️"
---

# 飞鹤商旅 CLI 总入口

本 skill 全部业务能力通过 `fh` 命令行调用，**不依赖宿主 MCP 能力**。
本文件只负责连接、路由和跨流程安全约束。工具参数、业务细节和展示规范按需加载，
不要一次读取全部引用文件。

## ⚠️ 第零步：登录闸门（任何业务调用之前必做，不可跳过）

**本 skill 的一切业务命令（查询/城市码/出页）都要求已登录态。收到首个飞鹤商旅相关请求时，
必须先完成本闸门，再去跑任何脚本或 `fh` 业务命令。禁止跳过本闸门直接调用接口乱试。**

登录和查询都用 `node` 执行本技能目录下的 `cli/cli.js`。这是 JavaScript，不是 exe。PATH 上不必有名叫 `fh` 的命令。

```text
Windows：auth-status.cmd
macOS / Linux：sh auth-status.sh
```

分流：
- 输出显示凭据已设置且未过期 → **闸门通过**，直接进入查询，**不要重复登录**。
- 无凭据 / 已过期且刷新失败 / 退出码 3 → **助手在当前对话里前台执行登录**，等命令结束再继续
  （脚本会等浏览器回调，最长约 5 分钟，不要放到后台）：
  Windows 运行本 skill 目录下的 `auth-login.cmd`。
  macOS / Linux 运行同目录 `sh auth-login.sh`。
  两者都是 `node` 执行同目录 `cli/cli.js`，并带上 `auth login`。会打开浏览器，在本机等待回调。
  （WorkBuddy 连接器「连接」按钮会另外对 `https://crm.feiheair.com/download/fh-cli-0.1.4.tgz` 做 `npm install -g`，从而得到 PATH 上的 `fh`。凭据都在 `~/.fh/credentials`。助手登录用上面的脚本即可，不必先有 `fh`）。
  用户只在弹出的**系统默认浏览器**里完成图形码和短信，然后关闭页面，回到当前对话。
  不要让用户寻找技能安装目录，不要让用户双击 bat 或自己打开命令行。
  登录由脚本打开系统默认浏览器。不要把授权地址发到对话里供用户点击，也不要用宿主内置浏览器打开。
  桌面浏览器未弹出时：不要贴链接；助手可改跑 `auth-login.cmd --manual` 或 `sh auth-login.sh --manual`，并排查本机默认浏览器是否正常。
  登录命令结束后（无论退出码是否为 0）：先跑 `auth-status.cmd` 或 `sh auth-status.sh`。若 stderr 已出现「登录成功」，或 status 显示已有有效凭据，不要重复登录（进程收尾异常时退出码可能非 0，凭据仍可能已写入）。
  确认已登录后再开始查询。
- `node` 不存在，或同目录没有 `cli/cli.js` → 读脚本 stderr 的 `[fh]` 行。不要全盘搜索，不要让用户自己找目录或执行 `npm install`。
- **找不到命令时**（不要全盘搜索，不要让用户去翻安装目录）：
  本 `SKILL.md` 所在目录就是技能目录。`auth-login.cmd`、`auth-status.cmd`、`auth-login.sh`、`auth-status.sh` 和 `cli/cli.js` 都在这里。
  Windows 执行 `auth-login.cmd` / `auth-status.cmd`。macOS / Linux 执行 `sh auth-login.sh` / `sh auth-status.sh`。
  失败时读该命令的 **stderr**。不要把其中的网址发到对话里点击。退出码 3 是未登录，不是没找到文件。
  进程要前台等到自己退出，最长约 5 分钟；超时被掐掉则 localhost 回调失败。

细节见 [`references/cli-connection.md`](references/cli-connection.md)。凭据文件名以 skill
`config.json` 的 `credentialsFile` 为准（生产默认 `credentials`）。不得向用户索要或回显
access token、refresh token、密码或验证码。查询时 CLI 自己带认证头；服务端返回 401 或 403 时用 refresh token 静默续一次并重试，没有提前刷新。
日常查询无需反复过本闸门；只有续期失败、`auth status` 报失效或连续退出码 3 才重新登录。

## 运行前置（Python 依赖）

本地脚本通道（`scripts/*.py`）只用 Python 标准库，不需要第三方包，也不再创建 venv。
注意 shim 自己改变了 cwd 等 shell 易错的情况。Windows 下脚本路径用盘符（如 `C:/...`），不要用 Git Bash 的 `/c/...`。

## 安装与认证（fh CLI）

**新装后的第一件事是登录，不是查票**：先跑 `auth-status.cmd` 或 `sh auth-status.sh`，无凭据再跑对应的 `auth-login` 脚本，确认已登录后再跑任何查询脚本。
跳过登录直接调业务命令只会得到退出码 3。脚本已经带上
`--credentials-file`（与 `config.json` 的 `credentialsFile` 同一文件名）。
不要把登录说成用户自己去安装目录里操作，也不要为了得到 `fh` 这个名字去执行 `npm install -g`。

## 一.能力边界

**当前支持**：国内机票、国际机票的查询与结果筛选；筛选后在交互页点击「去下单 / 预订」，
经免登跳转到飞鹤 portal 继续操作。

**当前不支持**：上述范围之外的任何产品或动作（例如在对话里直接创单/支付/出票/改签/退票等）。
用户问起时**礼貌说明暂不支持**，并简要告知仅支持国内/国际机票查询与筛选，以及在界面上
点预订后的跳转；不要编造流程，不要调用本 skill 路由与 tool-catalog 未收录的工具。

关于 memory 记忆相关的更新（注意不是记忆读取和使用）：记忆的创建和更新，需要等查询完毕
**且已 `present_files` 展示 html** 之后再进行，不要中途去创建记忆目录和更新记忆。

## 二.路由

先判产品，再判地理。

- **国内**：出发地和目的地在中国大陆 → `domestic_*`
- **国际**：中国香港、中国澳门、中国台湾，以及外国 → `intl_*`

不确定时一句问清。`air_city` 必须带 `scope=DOMESTIC` 或 `INTERNATIONAL`，禁止凭记忆猜码，禁止传 AUTO。

日期直接使用宿主/harness 注入的当前日期，不额外启动脚本。将「今天/明天/后天/下周五」
换算成 `yyyy-MM-dd` 后再查询；宿主没有提供当前日期或用户表达确有歧义时，才向用户确认。

## 三.怎么执行

脚本只用 Python 标准库，不建 venv。用 `python -u` 加脚本**绝对路径**直接跑。
Windows 路径用盘符（如 `C:/Users/...`），**不要用 Git Bash**（PATH 会坏、路径会写烂）。`~` 换主目录。
python 用本 skill 目录下的绝对路径；skill 若不在
`~/.workbuddy/skills/fh-travel-portal-cli/`，把该前缀换成**本 skill 目录**。
不要 `cd` 进脚本目录。不要先单独跑 `portal_config.py` 取号。
一条龙失败：看 stderr，把**同一条一条龙命令**再跑一次。禁止改去单独跑城市脚本或其它拆步脚本。

0. **前置闸门**：本会话尚未确认登录态时，先过「⚠️ 第零步：登录闸门」（`fh auth status`，
   无凭据先 `fh auth login`）。未登录直接跑脚本只会失败（退出码 3）。已确认登录则跳过本步。

1. 查询

听懂用户要查什么，判断国内或国际；缺槽问一句。要查航班就跑一条龙（省略 `--run-id`，脚本自己发号）。

国内（详见「四.国内机票」）：

```text
python -u ~/.workbuddy/skills/fh-travel-portal-cli/scripts/air_domestic_query.py --from <城市> --to <城市> --date <yyyy-MM-dd> [--return <回程>]
```

国际（详见「五.国际机票」）：

```text
python -u ~/.workbuddy/skills/fh-travel-portal-cli/scripts/air_intl_query.py --from <城市> --to <城市> --date <yyyy-MM-dd> [--return <回程>]
```

2. 查询结果

`exit=0` 后：stdout 第一行是 `run-id`（后面可能还有日志），不要把整段日志当成 run-id。
用它拼 `fh-travel-runs/<run-id>/run_summary.json`。stdout 整段为空才读
`~/.fh-travel-workspace/fh-last-task-id.txt` 再拼 summary。

工作区默认 `~/.fh-travel-workspace`。产物都在这里，不要无故打开 `config.json`，不要全盘 Glob。
fh 凭据在 `~/.fh/`（与工作区分离），永不写入 skill 目录。

| 用途 | 工作区路径下的路径 |
|---|---|
| 本轮 id | `fh-last-task-id.txt` |
| 本轮产物 | `fh-travel-runs/<run-id>/` |
| 执行结果 | `fh-travel-runs/<run-id>/run_summary.json` |
| 交付页 | 国内 `…/page.html`；国际 `…/_inline/flights_inline.html` |

3. 展示

`run_summary.json` 的 `ok=true` 时，**必须调用 `present_files`**，传入 `html` 的**绝对路径**。
禁止只在回复里写路径、写「已打开」、附 Markdown 链接却不调工具。没调工具 = 没打开。
`present_files` 成功之后才可说「页面已打开」。`ok=false` 没有 html，按失败处理（读 `error`）。

stdout 空是常态，**不是失败**。禁止为 stdout 重跑、重定向、测通道。
一条龙已 `exit=0` 或本轮 `ok=true` → 不要重跑。用户改城市/日期/人数/往返才整段重跑（不要带旧 `--run-id`）。
`--raw` 续跑才把旧 `--run-id` 传回一条龙。分步排障才单独跑 `portal_config.py`。

退出码 3 / token 失败：先 `fh auth status`，稍后重跑一条龙，不要让用户重新授权；连续多次仍失败才读
[`references/cli-connection.md`](references/cli-connection.md)。
国际页内「查舱位」不是重复 shopping，不要被本纪律拦住。

## 四.国内机票

标准查询走一条龙，见「三.怎么执行」。拆步/口径见
[`workflows/air-domestic-search.md`](workflows/air-domestic-search.md)。

| 用户目标 | 按需读取 |
|---|---|
| **标准国内机票查询（单程/推荐往返，查完即交付）** | 见「三.怎么执行」。`--return` = 一次 `journeyType=1` 推荐往返。须 `official=true`、`sortBy=DEPARTURE_TIME`、`withCabinRules=true`、`needRefundChangeRule=false`（shopping 不带退改，页内点退改补查）。禁止宿主手调 `mcp__…__domestic_shopping`。拆步/定制再读下一行 |
| 查询、比较、出分析页（拆步/定制/补查） | [`workflows/air-domestic-search.md`](workflows/air-domestic-search.md) |
| 出页（对照能力摘要，不要打开 html） | [`references/air-domestic-oneway-page.md`](references/air-domestic-oneway-page.md)；脚本 `scripts/air_domestic_oneway_render_page.py` + 模板 `assets/air-domestic-oneway-page.html` |
| 推荐往返出页（journeyType=1） | [`references/air-domestic-roundtrip-page.md`](references/air-domestic-roundtrip-page.md)；脚本 `scripts/air_domestic_roundtrip_render_page.py` + 模板 `assets/air-domestic-roundtrip-page.html`。不要把往返结果丢给单程脚本，也不要降级为编号列表 |
| 国内下单页跳转字段 | [`references/air-domestic-sso-forward.md`](references/air-domestic-sso-forward.md)（`#/bookingPricing` 最外层 `serialNumber`/`flightId`/`cabId`，不要 `flightList`） |
| 购物返回字段对不上 | [`references/air-domestic-shopping-schema.md`](references/air-domestic-shopping-schema.md) |

查询出页对照能力摘要，不要打开 html 或 assets 模板判断能力。不要走创单工具。
城市码：`fh common city search --scope DOMESTIC` 或 `scripts/air_domestic_resolve_city.py`（未命中自动查并回写）。

## 五.国际机票

标准查询走一条龙，见「三.怎么执行」。拆步/定制见
[`workflows/air-intl-search.md`](workflows/air-intl-search.md)。
一条龙内部已批量 `intl_shopping_all_cab`（经 fh）；页内「查舱位」打 busi `intlShop`（`X-Auth-Code` = infoCode），不是再调 MCP。

| 用户目标 | 按需读取 |
|---|---|
| **标准国际机票查询（单程/往返，查完即交付）** | 见「三.怎么执行」。普通往返 `--return` **只发起 1 次** `intl_shopping`（同一 `tripList` 含去程和反向返程）；禁止拆成两次单程，也禁止用 `intl_multi_shopping` 代替普通往返。不要改走宿主手调 `mcp__…__intl_shopping` / ToolSearch |
| 国际机票多段/特殊舱位等复杂查询 | [`workflows/air-intl-search.md`](workflows/air-intl-search.md) |
| 国际城市/机场码解析 | `scripts/air_intl_resolve_city.py`（缓存优先；未命中自动 `air_city` scope=INTERNATIONAL 并合并回写）。从候选取 **`code`**；`aggregate=true` 则 `isFromCity/isToCity=true`。不要用已下线的 `intl_city`，不要手工并行 `--ingest` |
| 国际查询结果过大 | 本轮返回交给 `air_intl_parse_shopping.py` / `air_intl_render_flight_options.py`；下单链路用 `air_intl_book.py inline --scope best:N`。展示名回退 [`references/air-intl-iata-codes.md`](references/air-intl-iata-codes.md)。禁止 python -c 挖字段 |
| 国际出页契约 | [`references/air-intl-page.md`](references/air-intl-page.md) |
| 解封任意工具返回 | `scripts/unwrap_content.py`（契约见 [`references/mcp-envelope.md`](references/mcp-envelope.md)） |
| 用户要求国际核价、政策、申请单或创单（当前未暴露） | [`references/air-intl-capability-gap.md`](references/air-intl-capability-gap.md)，不得伪造调用 |
| 国际列表页/下单页字段 | [`references/air-intl-sso-forward.md`](references/air-intl-sso-forward.md) |

## 六.基建

| 用户目标 | 按需读取 |
|---|---|
| 解析工具返回 | [`references/mcp-envelope.md`](references/mcp-envelope.md)。业务只在 `structuredContent`。二次转义可用 `scripts/mcp_envelope.py --result` |
| 免登跳转编码 / `/oauth2/forward` / `forwardCode` | [`references/sso-forward.md`](references/sso-forward.md)，库 `scripts/sso_forward.py`。国内字段表 [`air-domestic-sso-forward.md`](references/air-domestic-sso-forward.md)，国际 [`air-intl-sso-forward.md`](references/air-intl-sso-forward.md) |
| 不确定工具、参数或写操作等级 | [`references/tool-catalog.md`](references/tool-catalog.md) |
| 命令错误、超时、业务拒绝 | [`references/error-handling.md`](references/error-handling.md) |
| CLI 安装/认证/配置/传输通道 | [`references/cli-connection.md`](references/cli-connection.md) |

## 七.连接

工具名与入参以 `fh dev tools` / [`references/tool-catalog.md`](references/tool-catalog.md)
为准（公共 1、国内机票 6、国际机票 5，共 12）；不在目录中的名字不要调用。
预订/下单只能走 portal 免登跳转。

```text
Windows：auth-status.cmd
macOS / Linux：sh auth-status.sh
无凭据再跑 auth-login.cmd 或 sh auth-login.sh
```

这些脚本用 `node` 执行同目录 `cli/cli.js`。WorkBuddy 连接器按钮仍可能另外安装 PATH 上的 `fh`，助手不必依赖它。

不得向用户索要或回显 access token、refresh token、密码或验证码。
认证只走 `fh auth login` 写入的 `~/.fh/<credentialsFile>`（文件名见 `config.json`）。无凭据或 401 先 `fh auth status`，
稍后重跑一条龙；连续多次仍失败则由助手前台重新登录：Windows 执行同目录 `auth-login.cmd`，macOS / Linux 执行同目录 `sh auth-login.sh`。
命令不存在时看 stderr 的 `[fh]` 提示，不要全盘搜索。不要让用户自己去安装目录或连接器菜单里找命令。修好后**重跑一条龙出错步骤**，不要改成宿主直调。

标准查询只走一条龙（见「三.怎么执行」）。脚本内部经 `fh_travel.py` → `mcp_proxy.py` 调
`fh dev call <op>`。**不要**用宿主侧 `tools/call` / ToolSearch / `mcp__…__domestic_shopping` /
`mcp__…__intl_shopping` 代替一条龙。

拆步/排障才手工：

```bash
fh <域> <对象> <动作> [旗标]
fh dev call <op> --args '{...}'           # 写操作需 --yes
fh dev tools --out tools.json
```

CLI 输出：stdout 只输出 JSON 信封；失败看退出码（0/1/2/3/4/5，见 error-handling.md）。
大结果 `--out <文件>.json` 落盘再交给产品脚本。业务只在 `structuredContent`（见 mcp-envelope.md）。
机票 shopping 很大，**不要整份读进大模型**。

## 八.目录约定

扁平面，不按产品再套子目录。文档/资源 kebab-case，脚本 snake_case。
命名 `{产品}-{地理}-{职责}`。国内出页再加行程：`oneway`（单程）/ `roundtrip`（往返）。
一条龙查询脚本不加行程（`air_domestic_query.py` / `air_intl_query.py` 覆盖单程和往返）。
后端 op 名（如 `domestic_shopping`）不跟文件改名。新开产品线只加前缀，不改现有文件名。

| 前缀 | 产品线 | 放哪 |
|---|---|---|
| `air-domestic-` / `air_domestic_` | 国内机票 | `workflows/` `scripts/` `assets/` `references/` |
| `air-intl-` / `air_intl_` | 国际机票（含港澳台） | 同上；国际出页目前单程往返同一套 |
| 无前缀 | 连接、信封、免登、错误、工具目录 | `cli-connection.md`、`mcp-envelope.md`、`sso-forward.md`、`error-handling.md`、`tool-catalog.md`、`scripts/query_run.py` |

| 角色 | 国内单程 | 国内往返 | 国际 |
|---|---|---|---|
| 能力摘要 | `air-domestic-oneway-page.md` | `air-domestic-roundtrip-page.md` | `air-intl-page.md` |
| 出页脚本 | `air_domestic_oneway_render_page.py` | `air_domestic_roundtrip_render_page.py` | `air_intl_render_flight_options.py` |
| HTML | `air-domestic-oneway-page.html` | `air-domestic-roundtrip-page.html` | 脚本内联 |
| 页内 busi | `air-domestic-page-busi.js`（单程/往返共用，出页时内联） | 同左 | — |
| 免登字段 | `air-domestic-sso-forward.md` | 同左 | `air-intl-sso-forward.md` |

免登编码：`sso-forward.md` / `sso_forward.py`。

## 九.跨流程硬约束

编号勿改（`air-intl-page.md` 按「第 N 条」引用）。

1. 城市码、航司码、`serialNumber`、`flightId`、`cabId`、`priceId` 只取当前登录态下的真实工具结果；
   禁止猜测、改写或国内/国际混用。解封见 [`references/mcp-envelope.md`](references/mcp-envelope.md)。
2. 新查询或城市、日期、人数、行程模式变化会产生新结果世代；旧页面选择和旧交易标识全部失效。
3. 当前服务端只暴露只读查询；下单、支付、出票、改签和退票只能在飞鹤 portal 完成。
4. 价格、库存、政策和规则只以真实工具结果为准；portal 内下单/支付/出票状态不得代答。
5. 需要用户比较/选择的列表结果：**必须先生成并 `present_files` 展示交互页再结束**，
   不得以 Markdown/JSON/「稍后补页面」代替。标准查询只跑一条龙（见「三.怎么执行」）。
   **禁止**宿主手调 shopping 代替一条龙。拆步：国内单程 `air_domestic_oneway_render_page.py`，
   推荐往返 `air_domestic_roundtrip_render_page.py`；国际 `air_intl_parse_shopping.py` 后立即
   `air_intl_render_flight_options.py`。页内补查：国际「查舱位」`fetch` busi `intlShop`（头 infoCode）；
   国内退或改文案缺一侧时 `fetch` busi `rule`（头 infoCode）；国内「更多」只展开本次 shopping
   已返回舱位，**不**直调 `domestic_shopping_by_flight_id`。除此 busi 外页面不调 MCP `tools/call`。
6. 完整证件、手机号、MCP token 不得进入 HTML、URL、DOM 或前端存储。查询结果只用
   `infoCode` / `forwardCode`。**唯一例外**：免登 `href` 的 query `authCode=forwardCode`。
7. 运行时缺少文档中列出的工具时，不得伪造调用。国际核价/创单降级见
   [`references/air-intl-capability-gap.md`](references/air-intl-capability-gap.md)。
8. 不得擅自丢弃、截断或把真实结果标成「噪音/异常」；筛选/分页后全部有效方案仍可访问。
9. 下单跳转按产品字段表：国际 [`air-intl-sso-forward.md`](references/air-intl-sso-forward.md)
   （`serialNumber + 舱位 priceId`，不经过核价）；国内
   [`air-domestic-sso-forward.md`](references/air-domestic-sso-forward.md)
   （最外层 `serialNumber`/`flightId`/`cabId`，不要 `flightList`）。国际表露预订意图时，
   选定航班后必须自动衔接选舱 → 拼下单 URL，不得停在选航班等用户再问。
10. **禁止**启动任何本地 HTTP server；**禁止**「复制指令发回对话框」降级。
    见 [`references/air-intl-page.md`](references/air-intl-page.md)。

## 十.降级策略

依赖飞鹤外部服务时，按类型处理（细节见 [`references/error-handling.md`](references/error-handling.md)、[`references/air-intl-capability-gap.md`](references/air-intl-capability-gap.md)）：

| 类型 | 适用场景 | 处理方式 |
|---|---|---|
| `degrade` | 工具调用失败/超时（可重试 1 次仍失败）；宿主无 `present_files` | 如实说明查询失败；或给出 `html` 绝对路径并打开该文件（打开方式不限）；不编造航班与价格 |
| `partial` | 只拿到部分可用结果；国际核价/创单等能力未暴露 | 说明缺失部分，返回已有查询结果，或引导用户在飞鹤 portal 完成后续 |
| `block` | 鉴权失败（退出码 3 / 需重新登录）；用户要求对话内创单、支付、出票 | 明确停止；提示先完成登录，或说明本 skill 不支持该写操作并引导 portal / 转人工 |

## 示例

**用户**：帮我查明天深圳飞北京的飞鹤商旅机票

**助手**：
1. 先执行 `auth-status`；未登录则前台跑 `auth-login`，等系统浏览器完成授权后再继续。
2. 确认登录后跑国内一条龙查询，并出交互页。
3. 用 `present_files` 展示 `html`（若无该工具则打开该 `html`，方式不限）；用户在页内点预订后跳转飞鹤商旅完成后续。
