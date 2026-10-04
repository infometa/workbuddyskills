# 期货交易命令

期货交易必须使用 **`OpenFutureTradeContext`**（而非证券交易的 `OpenSecTradeContext`），现有交易脚本（`place_order.py` 等）使用的是 `OpenSecTradeContext`，**不适用于期货**。期货交易需直接生成 Python 代码执行。

## 期货 vs 证券的关键区别

| 特性 | 证券交易 | 期货交易 |
|------|---------|---------|
| 上下文 | `OpenSecTradeContext` | `OpenFutureTradeContext` |
| 现有脚本 | `place_order.py` 等可用 | 不可用，需生成代码 |
| 模拟账户 | 按市场统一分配 | 按市场独立分配（如 `FUTURES_SIMULATE_SG`） |
| 合约代码 | 股票代码（如 `HK.00700`） | 期货主连代码（如 `SG.CNmain`），下单后自动映射到实际月份合约 |
| 数量单位 | 股 | 张（手） |

## SG 期货合约代码

常见 SG 期货主力合约（使用 `主连` 代码下单，系统自动映射到当月合约）：

| 代码 | 名称 | 每手 |
|------|------|------|
| `SG.CNmain` | A50 指数期货主连 | 1 |
| `SG.NKmain` | 日经期货主连 | 500 |
| `SG.FEFmain` | 铁矿期货主连 | 100 |
| `SG.SGPmain` | MSCI 新指期货主连 | 100 |
| `SG.TWNmain` | FTSE 台指期货主连 | 40 |

查询所有 SG 期货合约：
```python
from futu import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111, ai_type=1)
ret, data = quote_ctx.get_stock_basicinfo(Market.SG, SecurityType.FUTURE)
# 筛选主力合约
main_contracts = data[data['main_contract'] == True]
print(main_contracts[['code', 'name', 'lot_size']].to_string())
quote_ctx.close()
```

## 查询期货账户

期货账户通过 `OpenFutureTradeContext` 查询，与证券账户分开管理：

```python
from futu import *
trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111, ai_type=1)
ret, data = trd_ctx.get_acc_list()
print(data.to_string())
trd_ctx.close()
```

期货模拟账户按市场独立分配，关注 `trdmarket_auth` 字段：
- `FUTURES_SIMULATE_SG`：SG 期货模拟
- `FUTURES_SIMULATE_HK`：HK 期货模拟
- `FUTURES_SIMULATE_US`：US 期货模拟
- `FUTURES_SIMULATE_JP`：JP 期货模拟
- `FUTURES`：实盘期货

## 期货模拟交易下单流程

模拟交易（`TrdEnv.SIMULATE`）流程如下：

1. 用 `OpenFutureTradeContext` 查询账户，找到 `trdmarket_auth` 包含对应模拟市场的账户（如 `FUTURES_SIMULATE_SG`）
2. 获取合约行情确认价格
3. 用 AskUserQuestion 确认下单参数（合约、方向、数量、价格）
4. 执行下单

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111, ai_type=1)

ret, data = trd_ctx.place_order(
    price=14782.0,         # 限价
    qty=1,                 # 数量（张）
    code='SG.CNmain',      # 主连代码，自动映射到实际合约
    trd_side=TrdSide.BUY,
    order_type=OrderType.NORMAL,
    trd_env=TrdEnv.SIMULATE,
    acc_id=9492210         # 模拟账户 ID
)

if ret == RET_OK:
    print('下单成功:', data)
else:
    print('下单失败:', data)

trd_ctx.close()
```

## 期货实盘下单流程

与上方「实盘下单流程」相同的确认步骤（查询账户 → 二次确认 → 执行），区别：
- 使用 `OpenFutureTradeContext` 而非 `OpenSecTradeContext`
- 筛选 `trdmarket_auth` 包含 `FUTURES` 的账户
- 确认提示改为"确认实盘下单期货？"

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111, ai_type=1)

# 实盘下单
ret, data = trd_ctx.place_order(
    price=14785.0,
    qty=1,
    code='SG.CNmain',
    trd_side=TrdSide.BUY,
    order_type=OrderType.NORMAL,
    trd_env=TrdEnv.REAL,
    acc_id=281756475296104250  # 实盘期货账户 ID
)

if ret == RET_OK:
    print('实盘下单成功:', data)
else:
    print('下单失败:', data)

trd_ctx.close()
```

## 期货持仓与资金查询

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111, ai_type=1)

# 查询持仓
ret, data = trd_ctx.position_list_query(trd_env=TrdEnv.SIMULATE, acc_id=9492210)
if ret == RET_OK:
    print(data)

# 查询账户资金
ret, data = trd_ctx.accinfo_query(trd_env=TrdEnv.SIMULATE, acc_id=9492210)
if ret == RET_OK:
    print(data)

trd_ctx.close()
```

## 期货订单查询与撤单

```python
from futu import *

trd_ctx = OpenFutureTradeContext(host='127.0.0.1', port=11111, ai_type=1)

# 查询今日订单
ret, data = trd_ctx.order_list_query(trd_env=TrdEnv.SIMULATE, acc_id=9492210)
if ret == RET_OK:
    print(data)

# 撤单
ret, data = trd_ctx.modify_order(
    modify_order_op=ModifyOrderOp.CANCEL,
    order_id='7679570',
    qty=0, price=0,
    trd_env=TrdEnv.SIMULATE,
    acc_id=9492210
)

trd_ctx.close()
```

## 期货合约信息查询

```python
from futu import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111, ai_type=1)
ret, data = quote_ctx.get_future_info(['SG.CNmain', 'SG.NKmain'])
if ret == RET_OK:
    print(data)  # 包含合约乘数、最小变动价位、交易时间等
quote_ctx.close()
```
