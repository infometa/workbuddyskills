# 国际机票免登跳转（字段表）

> 加载时机：国际机票要给方案页加「下单/去飞鹤」或拼列表/下单跳转时。
> 编码、`/oauth2/forward`、`forwardCode`/`infoCode` 见 [`sso-forward.md`](sso-forward.md)，不要在本文件
> 再抄一套。

## 两种跳转目标

| 目标 | 页面路由 | 拼接脚本 | 适用 |
|---|---|---|---|
| 航班列表页（重新搜索） | `#/?<搜索参数>` | `air_intl_build_jump_url.py` | 只带查询条件，让用户在前端自己重查 |
| 下单页（已选好航班/舱位） | `#/bookingPricing?flightList=[...]` | `air_intl_build_order_jump_url.py` | 两步走完后，带二元组直接落下单页 |

前端入口固定 `/VuePage/international/index.html`。城市/日期/机场禁止写死，全部来自本轮查询。

## 列表页字段

```bash
python3 scripts/air_intl_build_jump_url.py \
  --from 深圳 --from-code SZX --from-en Shenzhen \
  --from-airport 宝安机场 --from-airport-en "Baoan Airport" \
  --from-country 中国 --from-country-en China \
  --to 巴厘岛 --to-code DPS --to-en "Bali Island" \
  --to-airport 努拉莱伊机场 --to-airport-en "Nuralei Airport" \
  --to-country 印度尼西亚 --to-country-en Indonesia \
  --date 2026-09-02 --adult 1 --fee-type 公费出行 \
  --forward-code <当次 intl_shopping 的 forwardCode>
```

城市名/机场名/国家名/英文名优先取 `air_city`（`scope=INTERNATIONAL`）返回的原始字段
（`cityName`/`airPort` 等）。缓存或响应缺英文名/国家名时不要编造，省略该字段。

输出形态见 [`sso-forward.md`](sso-forward.md)（HTTPS `/oauth2/forward?authCode=forwardCode`）。

## 下单页（两步契约）

下单页不是「重新搜索」，而是把「选航班 → 选舱位」两步产出的标识一次性带过去。
与 `workflows/air-intl-search.md` 的 S3→S4 对应，**不经过核价**。

**强制衔接**：国际查询若表露下单/预订意图、或宿主默认按可预订场景处理，S3 选定航班后
必须自动衔接选舱位 → 拼下单页 URL，不得停在选航班等用户再问。

| 步 | 动作 | 工具 | 产出标识 |
|---|---|---|---|
| ① 选航班 | 用户从查询结果选一个组合 | `intl_shopping` | `serialNumber` + 查询 `priceId` |
| ② 选舱位 | 看该组合的全部舱位并选一个 | `intl_shopping_all_cab` | 舱位级 `priceId`（三段式 `x/y/n`） |

下单页 URL 里的 `priceId` 是 `intl_shopping_all_cab` 返回的舱位级三段式 priceId
（如 `36056399531212808/100000/6`），不是查询单值 priceId。

`flightList` 每项是**二元组 `{serialNumber, priceId}`**，**不含 pricingId**。

```bash
python3 scripts/air_intl_build_order_jump_url.py \
  --serial-number 260902162025A0000001 \
  --price-id "36056399531212808/100000/6" \
  --adult 1 --pay-type 1 --fly-type 1 \
  --forward-code <forwardCode>

python3 scripts/air_intl_build_order_jump_url.py \
  --flight '{"serialNumber":"A","priceId":"x/y/1"}' \
  --flight '{"serialNumber":"B","priceId":"m/n/2"}' \
  --adult 1 --fly-type 2 \
  --forward-code <forwardCode>
```

| 字段 | 必填 | 取值/来源 |
|---|---|---|
| `flightList` | ✅ | `[{serialNumber, priceId}]`，priceId 取选舱结果，往返/多程按出行原始顺序 |
| `flyType` | ✅ | 1=单程，2=往返，3=多程 |
| `adultCount` | ✅ | 查询时的同行人数 |
| `payType` | ✅ | 1=公费（因公挂账），0=自费 |
| `agent` | ✅ | 固定 `1`（agent 内置环境） |
| `applicationId` | – | 出差单 id（可选，有值才带） |
| `dh` | – | 出差单号（可选，有值才带） |

`flightList` 整体编码，`,` 与 `/` 保持裸字符（`sso_forward.encode_json_param`）：

```
#/bookingPricing?flightList=%5B%7B%22serialNumber%22%3A%22...%22,%22priceId%22%3A%22.../.../...%22%7D%5D&flyType=1&adultCount=1&payType=1&agent=1
```

## 标准出页 vs 拆步

**标准查询**走 `air_intl_query.py` → `air_intl_book.py inline`：精选航班内联舱位，「去下单」href 已是
`/oauth2/forward?authCode=<forwardCode>`；其余航班页内 `fetch` busi `intlShop`（头 `infoCode`）。
查询结果 HTML/JS 只内嵌 `infoCode` / `forwardCode`，跳转 query 名是服务端约定的 `authCode`。

**拆步 / 宿主事件桥**才用 `air_intl_render_flight_options.py --action`：

1. `--action select-flight`：选航班页，回传 `fh-travel-select`（action=select-flight）。
2. 宿主从 selection-map 反查 `serialNumber + 查询 priceId` → `intl_shopping_all_cab`（经 `fh`）→
   `--action select-cabin`。
3. 反查 `serialNumber + 舱位 priceId` → `air_intl_build_order_jump_url.py --forward-code <forwardCode>` 作按钮 href。

每步校验 `generation` 与 `optionKey`，禁止凭聊天记忆重建标识。
下单页按钮必须走完两步；禁止拿查询 priceId 冒充舱位 priceId。
页面不直接调 MCP。
