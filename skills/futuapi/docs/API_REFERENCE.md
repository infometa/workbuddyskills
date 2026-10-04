# API 速查（完整函数签名）

## 行情 API（OpenQuoteContext）

### 订阅管理（4 个）

```
subscribe(code_list, subtype_list, is_first_push=True, subscribe_push=True, is_detailed_orderbook=False, extended_time=False, session=Session.NONE)  -- 订阅(消耗订阅额度, 每只股票每个类型占1个额度; 调用前应先用 query_subscription 检查额度; session 仅用于美股实时K线/分时/逐笔，不支持 OVERNIGHT)
unsubscribe(code_list, subtype_list, unsubscribe_all=False)  -- 反订阅(订阅后至少1分钟才能反订阅)
unsubscribe_all()  -- 反订阅所有
query_subscription(is_all_conn=True)  -- 查询订阅状态(调用subscribe前应先检查)
```

### 实时数据 - 需要先订阅（6 个）

```
get_stock_quote(code_list)  -- 获取实时报价
get_cur_kline(code, num, ktype=KLType.K_DAY, autype=AuType.QFQ)  -- 获取实时 K 线
get_rt_data(code)  -- 获取实时分时
get_rt_ticker(code, num=500)  -- 获取实时逐笔
get_order_book(code, num=10)  -- 获取实时摆盘
get_broker_queue(code)  -- 获取实时经纪队列(仅港股)
```

### 快照与历史（4 个）

```
get_market_snapshot(code_list)  -- 获取快照(无需订阅, 每次最多400个)
request_history_kline(code, start=None, end=None, ktype=KLType.K_DAY, autype=AuType.QFQ, fields=[KL_FIELD.ALL], max_count=1000, page_req_key=None, extended_time=False, session=Session.NONE)  -- 获取历史K线(消耗历史K线额度, 调用前应先用 get_history_kl_quota 检查剩余额度; 单次max_count最大1000, 超过需用page_req_key翻页; session 仅用于美股分时段历史K线，不支持 OVERNIGHT)
get_rehab(code)  -- 获取复权因子
get_history_kl_quota(get_detail=False)  -- 查询历史K线额度(调用request_history_kline前应先检查)
```

### 基础信息（5 个）

```
get_stock_basicinfo(market, stock_type=SecurityType.STOCK, code_list=None)  -- 获取股票静态信息
get_global_state()  -- 获取各市场状态（返回 dict，key 包括 market_hk/market_us/market_sh/market_sz/market_hkfuture/market_usfuture/server_ver/qot_logined/trd_logined 等）
request_trading_days(market=None, start=None, end=None, code=None)  -- 获取交易日历
get_market_state(code_list)  -- 获取市场状态
get_stock_filter(market, filter_list, plate_code=None, begin=0, num=200)  -- 条件选股
```

### 板块（3 个）

```
get_plate_list(market, plate_class)  -- 获取板块列表
get_plate_stock(plate_code, sort_field=SortField.CODE, ascend=True)  -- 获取板块内股票
get_owner_plate(code_list)  -- 获取股票所属板块
```

### 衍生品（5 个）

```
get_option_chain(code, index_option_type=IndexOptionType.NORMAL, start=None, end=None, option_type=OptionType.ALL, option_cond_type=OptionCondType.ALL, data_filter=None)  -- 获取期权链
get_option_expiration_date(code, index_option_type=IndexOptionType.NORMAL)  -- 获取期权到期日
get_referencestock_list(code, reference_type)  -- 获取关联股票(正股/窝轮/牛熊/期权)
get_future_info(code_list)  -- 获取期货合约信息
get_warrant(stock_owner='', req=None)  -- 获取窝轮/牛熊证
```

### 资金（2 个）

```
get_capital_flow(stock_code, period_type=PeriodType.INTRADAY, start=None, end=None)  -- 获取资金流向
get_capital_distribution(stock_code)  -- 获取资金分布
```

### 自选股（3 个）

```
get_user_security_group(group_type=UserSecurityGroupType.ALL)  -- 获取自选股分组
get_user_security(group_name)  -- 获取自选股列表
modify_user_security(group_name, op, code_list)  -- 修改自选股
```

### 到价提醒（2 个）

```
get_price_reminder(code=None, market=None)  -- 获取到价提醒
set_price_reminder(code, op, key=None, reminder_type=None, reminder_freq=None, value=None, note=None)  -- 设置到价提醒
```

### IPO（1 个）

```
get_ipo_list(market)  -- 获取IPO列表
```

**行情 API 小计：35 个**

---

## 交易 API（OpenSecTradeContext / OpenFutureTradeContext）

### 账户（3 个）

```
get_acc_list()  -- 获取交易业务账户列表
unlock_trade(password=None, password_md5=None, is_unlock=True)  -- 解锁/锁定交易（⚠️ 本技能不通过 API 解锁，需用户在 OpenD GUI 手动解锁）
accinfo_query(trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False, currency=Currency.HKD, asset_category=AssetCategory.NONE)  -- 查询账户资金
```

### 下单改单（3 个）

```
place_order(price, qty, code, trd_side, order_type=OrderType.NORMAL, adjust_limit=0, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, remark=None, time_in_force=TimeInForce.DAY, fill_outside_rth=False, aux_price=None, trail_type=None, trail_value=None, trail_spread=None, session=Session.NONE)  -- 下单(限频: 15次/30秒; session 仅对美股生效，支持 RTH/ETH/OVERNIGHT/ALL)
modify_order(modify_order_op, order_id, qty, price, adjust_limit=0, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, aux_price=None, trail_type=None, trail_value=None, trail_spread=None)  -- 改单/撤单(限频: 20次/30秒)
cancel_all_order(trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, trdmarket=TrdMarket.NONE)  -- 撤销所有订单
```

### 订单查询（3 个）

```
order_list_query(order_id="", order_market=TrdMarket.NONE, status_filter_list=[], code='', start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)  -- 查询今日订单
history_order_list_query(status_filter_list=[], code='', order_market=TrdMarket.NONE, start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0)  -- 查询历史订单
order_fee_query(order_id_list=[], acc_id=0, acc_index=0, trd_env=TrdEnv.REAL)  -- 查询订单费用
```

### 成交查询（2 个）

```
deal_list_query(code="", deal_market=TrdMarket.NONE, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)  -- 查询今日成交
history_deal_list_query(code='', deal_market=TrdMarket.NONE, start='', end='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0)  -- 查询历史成交
```

### 持仓与资金（4 个）

```
position_list_query(code='', position_market=TrdMarket.NONE, pl_ratio_min=None, pl_ratio_max=None, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, refresh_cache=False)  -- 查询持仓
acctradinginfo_query(order_type, code, price, order_id=None, adjust_limit=0, trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, session=Session.NONE)  -- 查询最大可买/卖数量(session 仅对美股生效，支持 RTH/ETH/OVERNIGHT/ALL)
get_acc_cash_flow(clearing_date='', trd_env=TrdEnv.REAL, acc_id=0, acc_index=0, cashflow_direction=CashFlowDirection.NONE)  -- 查询账户现金流水
get_margin_ratio(code_list)  -- 查询融资融券比率
```

**交易 API 小计：15 个**

---

## 推送 Handler（9 个）

### 行情推送（7 个）

```
StockQuoteHandlerBase   -- 报价推送回调
OrderBookHandlerBase    -- 摆盘推送回调
CurKlineHandlerBase     -- K线推送回调
TickerHandlerBase       -- 逐笔推送回调
RTDataHandlerBase       -- 分时推送回调
BrokerHandlerBase       -- 经纪队列推送回调
PriceReminderHandlerBase -- 到价提醒推送回调
```

### 交易推送（2 个）

```
TradeOrderHandlerBase   -- 订单状态推送回调
TradeDealHandlerBase    -- 成交推送回调
```

注意：交易推送不需要单独订阅，设置 Handler 后自动接收。

---

## 基础接口

```
OpenQuoteContext(host='127.0.0.1', port=11111, ai_type=1)  -- 创建行情连接
OpenSecTradeContext(filter_trdmarket=TrdMarket.NONE, host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES, ai_type=1)  -- 创建证券交易连接（security_firm 需根据用户所属券商设置，见 FUTU_SECURITY_FIRM 枚举表）
OpenFutureTradeContext(host='127.0.0.1', port=11111, security_firm=SecurityFirm.FUTUSECURITIES, ai_type=1)  -- 创建期货交易连接（security_firm 同上）
ctx.close()  -- 关闭连接
ctx.set_handler(handler)  -- 注册推送回调
SysNotifyHandlerBase  -- 系统通知回调
```

**全部 API 总计：行情 35 + 交易 15 + 推送 Handler 9 + 基础 6 = 65 个接口**

## SubType 订阅类型完整列表

| SubType | 说明 | 对应推送 Handler |
|---------|------|-----------------|
| `QUOTE` | 报价 | `StockQuoteHandlerBase` |
| `ORDER_BOOK` | 摆盘 | `OrderBookHandlerBase` |
| `TICKER` | 逐笔 | `TickerHandlerBase` |
| `K_1M` ~ `K_MON` | K 线 | `CurKlineHandlerBase` |
| `RT_DATA` | 分时 | `RTDataHandlerBase` |
| `BROKER` | 经纪队列（仅港股） | `BrokerHandlerBase` |

## 关键枚举值

- **TrdSide**: `BUY` | `SELL`
- **OrderType**: `NORMAL`(限价) | `MARKET`(市价)
- **TrdEnv**: `REAL` | `SIMULATE`
- **ModifyOrderOp**: `NORMAL`(改单) | `CANCEL`(撤单)
- **TrdMarket**: `HK` | `US` | `CN` | `HKCC` | `SG`
- **Session**: `NONE` | `RTH`(盘中) | `ETH`(盘前盘后) | `OVERNIGHT`(夜盘) | `ALL`(全部) — 订阅仅支持 RTH/ETH/ALL（不支持 OVERNIGHT）；下单支持 RTH/ETH/OVERNIGHT/ALL
