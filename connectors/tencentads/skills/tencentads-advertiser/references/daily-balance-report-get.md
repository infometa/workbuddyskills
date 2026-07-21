# 获取资金账户日结明细 (daily_balance_report/get)

查询指定广告主账户的资金账户日结明细，包含日终结余数据。

> **注意**：`account_id` 仅支持广告主账号，不支持代理商 ID。

## 调用方式

```bash
# 查询指定日期范围的日结明细
node scripts/get-daily-balance-report.mjs '{"account_id": 123456, "date_range": {"start_date": "2024-05-10", "end_date": "2024-05-15"}}'

# 指定分页参数
node scripts/get-daily-balance-report.mjs '{"account_id": 123456, "date_range": {"start_date": "2024-05-10", "end_date": "2024-05-15"}, "page": 1, "page_size": 20}'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | **是** | 账户 ID，有操作权限的帐号 ID，不支持代理商 ID |
| `date_range` | struct | **是** | 日期范围，单次查询跨度不能超过 10 天，支持两年内的数据查询 |
| `date_range.start_date` | string | **是** | 开始日期，格式：YYYY-MM-DD，且小于等于 end_date，长度 10 字节 |
| `date_range.end_date` | string | **是** | 结束日期，格式：YYYY-MM-DD，且大于等于 start_date，长度 10 字节 |
| `page` | integer | 否 | 搜索页码，最小值 1，最大值 99999，默认值 1 |
| `page_size` | integer | 否 | 一页显示的数据条数，最小值 1，最大值 100，默认值 10 |

## 返回格式

```json
{
  "list": [
    {
      "account_id": 123456,
      "fund_type": "FUND_TYPE_CASH",
      "time": 1715270400,
      "deposit": 100000,
      "paid": 50000,
      "trans_in": 1100000,
      "trans_out": 55000,
      "credit_modify": 400000,
      "balance": 300000,
      "preauth_balance": 11,
      "preauth_out_pay": 2,
      "preauth_in_refund": 20,
      "acct_out_pay": 0,
      "acct_out_pay_share": 50,
      "share_out_pay": 10
    }
  ],
  "page_info": {
    "page": 1,
    "page_size": 10,
    "total_number": 1,
    "total_page": 1
  }
}
```

## 返回字段说明

### list 数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 账户 ID |
| `fund_type` | enum | 资金账户类型，可通过 `node scripts/get-enum-options.mjs '{"fields": ["fund_type"]}'` 获取完整枚举值列表 |
| `time` | integer | 记录对应的时间，时间戳 |
| `deposit` | integer | 总存入，单位：**分** |
| `paid` | integer | 总支出，单位：**分** |
| `trans_in` | integer | 总转入，单位：**分** |
| `trans_out` | integer | 总转出，单位：**分** |
| `credit_modify` | integer | 授信调整，单位：**分** |
| `balance` | integer | 日终结余，单位：**分** |
| `preauth_balance` | integer | 预授权额度，单位：**分** |
| `preauth_out_pay` | integer | 预授权消耗，单位：**分** |
| `preauth_in_refund` | integer | 预授权退回，单位：**分** |
| `acct_out_pay` | integer | 非预授权消耗，单位：**分** |
| `acct_out_pay_share` | integer | 账户总消耗，单位：**分** |
| `share_out_pay` | integer | 共享钱包消耗，单位：**分** |

### page_info 分页信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `page` | integer | 搜索页码 |
| `page_size` | integer | 一页显示的数据条数 |
| `total_number` | integer | 总条数 |
| `total_page` | integer | 总页数 |
