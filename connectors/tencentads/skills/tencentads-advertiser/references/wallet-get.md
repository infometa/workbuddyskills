# 获取钱包信息 (wallet/get)

查询广告主账户所属共享钱包的余额、名称、代理商、主体及绑定账户等信息。

> **注意**：`account_id` 仅支持广告主账号，不支持代理商 ID。

## 调用方式

```bash
node scripts/get-wallet.mjs '{"account_id": 123456}'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | **是** | 广告主账号 ID（不支持代理商 ID） |

## 返回格式

```json
{
  "wallet_id": 24080128,
  "wallet_name": "xxx钱包",
  "balance": 10021001976591,
  "agency_id": 78384,
  "agency_name": "腾讯",
  "mdm_id": 51424622,
  "mdm_name": "深圳市腾讯计算机系统有限公司",
  "tag_list": ["标签"],
  "binding_account_list": [5897205],
  "bind_advertiser_cnt": 1
}
```

## 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `wallet_id` | integer | 钱包 ID |
| `wallet_name` | string | 钱包名称 |
| `balance` | integer | 余额，单位：**分**（÷100 得元） |
| `agency_id` | integer | 代理商 ID |
| `agency_name` | string | 代理商名称 |
| `mdm_id` | integer | 主体 ID |
| `mdm_name` | string | 主体名称（企业全称） |
| `tag_list` | string[] | 共享钱包标签列表 |
| `binding_account_list` | integer[] | 绑定的广告主账号 ID 列表 |
| `bind_advertiser_cnt` | integer | 关联账户数 |
