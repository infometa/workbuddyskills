# 获取资金账户信息 (funds/get)

查询指定广告主账户的各类资金账户余额、锁定金额、今日消耗及状态。

## 调用方式

```bash
node scripts/get-funds.mjs '{"account_id": 123456}'
# 按类型过滤
node scripts/get-funds.mjs '{"account_id": 123456, "fund_type_list": ["GENERAL_SHARED"]}'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | **是** | 推广账号 ID（代理商或广告主均支持） |
| `fund_type_list` | string[] | 否 | 资金账户类型过滤，不传则返回全部类型 |

### fund_type 枚举值

| 值 | 说明 |
|----|------|
| `GENERAL_CASH` | 现金账户 |
| `GENERAL_SHARED` | 共享账户（所属共享钱包的余额） |
| `GENERAL_GIFT` | 赠金账户 |
| `BANK` | 银行账户 |

## 返回格式

```json
{
  "list": [
    {
      "fund_type": "GENERAL_CASH",
      "balance": 120000,
      "bill_deposit_amount": 100,
      "fund_status": "FUND_STATUS_NORMAL",
      "realtime_cost": 100
    }
  ]
}
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `fund_type` | enum | 资金账户类型，见上方枚举值 |
| `balance` | integer | 余额，单位：**分**（÷100 得元） |
| `bill_deposit_amount` | integer | 锁定金额，单位：**分**。广告投放预锁定，未曝光会释放 |
| `fund_status` | enum | 资金状态，`FUND_STATUS_NORMAL` 表示正常 |
| `realtime_cost` | integer | 今日消耗，单位：**分** |
