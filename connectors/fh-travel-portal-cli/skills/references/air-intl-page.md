# 国际机票交互页契约

> 加载时机：国际航班、舱位、运价需要交互展示时。只覆盖国际。

服务端（经 `fh`）提供业务事实和真实标识；宿主把事实做成可操作的页。页面不得验价、改政策、创单、支付、出票、改签或退票。

「查舱位」页内 `fetch` busi `intlShop`（请求头 `infoCode`）。直调失败就地显示原因，禁止复制指令降级。
交互页是纯静态 HTML，禁止本地 HTTP server（`SKILL.md` 硬约束第 10 条）；用 `present_files` 打开本地文件。

数据源：本轮 `structuredContent`（[`mcp-envelope.md`](mcp-envelope.md)）→ 本轮其它文本 JSON → `script#flight-data` → 真实文本摘要。
不要逐段读大响应；`scripts/air_intl_parse_shopping.py` / `unwrap_content.py` 会解封。
不得从渲染后的 DOM 或文案猜交易字段。

## 执行链

结果很大时不要临场手写 HTML。

**标准查询**跑 `air_intl_query.py`（内部 parse + inline），交付 `run_summary.json` 的 `html`。

**拆步**（stdin 可用 `-`）：

```bash
python3 scripts/air_intl_parse_shopping.py - --json --html <输出.html> --dest <最终目的机场码> \
  --title "<出发地> → <目的地> · <日期>" --meta "<人数>" --meta "<舱等/筛选条件>"
```

一次两个文件：

- `*_航班方案.html`：展示事实、结果世代、`F001` 短键；
- `*.selection-map.json`：`generation + optionKey → serialNumber/groupId/priceId/rank`，只留工作目录，不给用户。

收到 `fh-travel-select` 或用户回复「选择 #F001」后，读映射并同时校验 `generation` 和 `optionKey`；禁止凭聊天记忆重建交易标识。

## 页面要求

- 单文件自包含；CSS/JS 内联；不加载第三方脚本/字体/图。
- 服务端字符串按纯文本转义，不拼进不受控 `innerHTML`。
- 写清本次城市、日期、人数、筛选和数据时间。
- 大结果分页或折叠，不能静默截断；筛排作用于本轮完整集合。
- 证件、手机、MCP token、订单快照、乘机人原文不得进 HTML/DOM/URL/存储/日志。页内只写 `infoCode` / `forwardCode`。

## 免登跳转

「去下单」用 `scripts/air_intl_build_jump_url.py`（列表）或 `scripts/air_intl_build_order_jump_url.py`（下单页），
禁止写死城市/日期/机场/token。字段见 [`air-intl-sso-forward.md`](air-intl-sso-forward.md)，编码见 [`sso-forward.md`](sso-forward.md)。

- 「去下单」：`/oauth2/forward?authCode=<forwardCode>`。
- 「查舱位」：`fetch` busi `intlShop`，头 `X-Auth-Code` = `infoCode`。
- 授权码明文不进日志、对话、远端。
- 标准 inline 页：精选舱位直接展开，「查舱位」页内 busi。拆步才由宿主事件桥循环，页面只回传选择。

## 选择事件

页面只回传无业务含义的引用：

```json
{
  "event": "fh-travel-select",
  "generation": "本次结果世代",
  "optionKey": "本页稳定短键",
  "action": "select-flight | select-cabin"
}
```

`select-cabin` 由 `air_intl_render_flight_options.py --action select-cabin` 生成。映射放宿主受控存储，不进 DOM。
旧世代点击必须拒绝。无事件桥时用户回复页面编号，仍只解析到本代映射。

## 页面类型

国际组合/运价映射到 `{serialNumber, priceId}`；`priceId` 必须来自同一次 shopping。

- 共享航班：`operatingFlightId` → 「共享·实际承运 XX」+ 逐段明细。
- 费用：只显示税/服务费；票价并入含税总价，附加费不展示。
- 特殊价（`specialRate=1`）→「特殊价」+ 限制标识；大客户协议价读 `bigCustomerPrice` 布尔（旧 `customersId`/`selfBigCustomersId` 兜底），只显示文案，不展示协议码。
- `source` / `allowTicket` 留在 parsed.json，不上页面。
- 可见区不展示 `serialNumber`。中转展开区固定逐段时刻/航站楼/机型/共享；时长为门到门。

## 降级

能写文件并能预览 HTML 时不得降级。无事件桥仍出页，改用回复短编号。只有不能写/预览或脚本报错，才出精简编号列表并说明原因。不得编造字段。

## 交付闸门

声称「页面已打开」之前：

**标准查询**（`air_intl_query.py` inline）：

1. `run_summary.json` 的 `ok=true`，`html` 文件真实存在且非空；
2. 已调用 `present_files`（绝对路径）。只写路径或 Markdown 链接不算打开。禁止 `http.server`；
3. 用户未要求删减时，全部有效结果仍可通过分页/筛选访问。

inline 会写 `flights_inline.selection-map.json`，那是内部产物，不是用户交付闸。

**拆步**另加：选择映射真实存在，条数与 `flightCount` 一致；HTML 与映射同一 `generation`。

## WorkBuddy 预览

把本地 HTML 绝对路径交给 `present_files`。禁止自起 HTTP server（硬约束第 10 条）。
HTML 自包含；页内「查舱位」在预览面板和外部浏览器均可工作。

## 面向用户的回复

说明已生成/展示、多少个方案、如何选择。`parsed_*.json` 和 `.selection-map.json` 用户未要求时不要当主交付物。
闸门没过就说哪步没完成，不能先说「预览已打开」。
