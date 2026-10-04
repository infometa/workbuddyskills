# 已知问题与错误处理

## 已知问题

### OpenD 连接慢 / 多账户查询超时

**现象**：连续查询多个账户时 OpenD 响应变慢甚至超时，尤其是创建多个 `OpenSecTradeContext` 连接时。

**解决**：
- **复用同一个连接**：只创建一次 `OpenSecTradeContext`，用同一个 `trd_ctx` 查询所有账户，避免反复建连
- **不要用脚本循环调用**：不要对每个账户分别运行 `get_portfolio.py`（每次都会新建/关闭连接），应直接写 Python 代码在一个连接内完成所有查询
- **加 `sys.stdout.flush()`**：在循环中每次打印后刷新输出，避免输出缓冲导致看不到中间结果

### 非保证金账户字段返回 N/A

**现象**：TFSA、RRSP 等非保证金账户的 `accinfo_query` 返回中，`initial_margin`、`maintenance_margin`、`available_funds` 等保证金相关字段为 `N/A`，直接 `float()` 转换会报 `ValueError`。

**解决**：
- 对所有数值字段使用安全转换：`float(val) if val != 'N/A' else 0.0`
- `available_funds` 为 N/A 时，保证金账户用 `total_assets - initial_margin` 计算；非保证金账户（TFSA/RRSP）可用资金等于 `total_assets`（因为没有保证金要求）

### pandas 与 numpy 版本不兼容

**现象**：运行代码时报错 `ValueError: numpy.dtype size changed`。

**解决**：`pip install --upgrade pandas`

## 错误处理

| 错误 | 解决 |
|------|------|
| 连接失败 | 启动 OpenD |
| 订单不存在 | 用 get_orders.py 检查 |
| 未找到账户 | 用 get_accounts.py 检查。若查不到实盘账户，可能是 `security_firm` 不匹配，运行券商自动探测流程（get_accounts.py 会遍历所有 SecurityFirm），或让用户确认所属地区后手动指定 `--security-firm` 参数 |
| OpenSecTradeContext 拉取不到实盘账号 | `create_trade_context()` 默认 `filter_trdmarket=TrdMarket.NONE`（不过滤市场），但如果手动创建 `OpenSecTradeContext` 时传了具体市场（如 `TrdMarket.US`、`TrdMarket.HK`），可能导致部分账号被过滤掉。解决：将 `filter_trdmarket` 改为 `TrdMarket.NONE` 重新拉取即可返回所有账号 |
| 解锁交易失败 / `unlock needed` | 需在 OpenD GUI 界面手动解锁交易密码 |
| 行情权限不足（如订阅失败、BMP 权限不支持等） | 提示用户开通行情权限，参考：https://openapi.futunn.com/futu-api-doc/intro/authority.html |
| 期货购买力不足 | 提示用户入金或平仓部分合约释放保证金 |
| 期货用 OpenSecTradeContext 下单失败 | 期货必须使用 `OpenFutureTradeContext`，不能用证券交易上下文 |
| 实盘下单 `Nonexisting acc_id` | `get_accounts.py --json` 输出的 acc_id 可能因 `safe_int` 中 `int(float())` 导致大整数精度丢失（已修复）。如仍遇到，用 `filter_trdmarket=TrdMarket.NONE` 创建上下文并直接打印 DataFrame 核对真实 acc_id |
| 实盘下单 `没有解锁交易` / `unlock needed` | 实盘交易需用户先在 **OpenD GUI** 界面点击「解锁交易」输入交易密码，API 无法代替此操作。解锁后重新执行下单即可 |
| 账户购买力不足 | 账户可用资金不足以完成下单。用 `get_portfolio.py` 查看资金详情，可减少数量、卖出持仓释放资金、或入金后重试 |
| 模拟账户资金不足 | 模拟账户资金不足时有两种方式恢复：1）卖出当前持仓股票释放资金；2）在手机 App 中重置模拟账户（路径：牛牛 → 我的 → 模拟交易 → 我的头像 → 我的道具 → 复活卡，参考 https://openapi.futunn.com/futu-api-doc/qa/trade.html#1690 ）。注意：重置后账户资金恢复初始值，但历史订单记录会被清空 |

## 自定义 Handler 模板

对于脚本未覆盖的推送类型（如摆盘、逐笔、交易推送），可生成临时代码：

```python
import time
from futu import *

class MyHandler(OrderBookHandlerBase):  # 替换为需要的 Handler 基类
    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print("error:", data)
            return RET_ERROR, data
        print("收到推送:")
        print(data)
        return RET_OK, data

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111, ai_type=1)
quote_ctx.set_handler(MyHandler())
ret, data = quote_ctx.subscribe(['HK.00700'], [SubType.ORDER_BOOK], subscribe_push=True)
if ret == RET_OK:
    print('订阅成功，等待推送...')
time.sleep(60)
quote_ctx.close()
```

## 券商自动探测（security_firm）

首次涉及交易操作时，如果环境变量 `FUTU_SECURITY_FIRM` 未设置，需确定用户所属券商：

1. 运行 `get_accounts.py --json` 获取所有账户（脚本会自动遍历所有 SecurityFirm）
2. 查看返回结果中 `trd_env` 为 `REAL` 的账户的 `security_firm` 字段
3. 将该值作为后续所有交易命令的 `--security-firm` 参数
4. 如果遍历完仍无实盘账户，提示用户可能未完成开户，或确认所属地区

探测代码示例：

```python
from futu import *

FIRMS = ['FUTUSECURITIES', 'FUTUINC', 'FUTUSG', 'FUTUAU', 'FUTUCA', 'FUTUJP', 'FUTUMY']

for firm in FIRMS:
    trd_ctx = OpenSecTradeContext(
        filter_trdmarket=TrdMarket.NONE,
        host='127.0.0.1', port=11111,
        security_firm=getattr(SecurityFirm, firm),
        ai_type=1
    )
    ret, data = trd_ctx.get_acc_list()
    trd_ctx.close()
    if ret == RET_OK and not data.empty:
        real_accounts = data[data['trd_env'] == 'REAL']
        if not real_accounts.empty:
            print(f'找到实盘账户，券商: {firm}')
            print(real_accounts.to_string())
            break
```
