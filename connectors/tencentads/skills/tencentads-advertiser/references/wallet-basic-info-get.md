# 通过钱包 ID 查询共享钱包基础信息 (wallet_basic_info/get)

通过钱包 ID 查询共享钱包基础信息，包含余额、代理商、主体、绑定账户、资金信息、监控预警等详细信息。

> **注意**：`account_id` 为代理商 ID，`wallet_id` 为钱包账号 ID。

## 调用方式

```bash
node scripts/get-wallet-basic-info.mjs '{"account_id": 78384, "wallet_id": 24111993}'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | integer | **是** | 代理商 ID |
| `wallet_id` | integer | **是** | 钱包 ID，钱包账号 ID |

## 返回格式

```json
{
  "wallet_id": 24111993,
  "wallet_name": "name",
  "balance": 9954999,
  "agency_id": 78384,
  "agency_name": "腾讯",
  "mdm_id": 63444781,
  "mdm_name": "mdmName",
  "tag_list": ["视频", "tag1"],
  "bind_advertiser_cnt": 4,
  "binding_account_list": [23870009, 23878247, 23953986, 23954003],
  "balance_info_list": [
    { "fund_type": "FUND_TYPE_CASH", "balance": 9954999 },
    { "fund_type": "FUND_TYPE_GIFT", "balance": 0 },
    { "fund_type": "FUND_TYPE_SHARED", "balance": 0 }
  ],
  "contact_info_list": [
    { "avatar_name": "哈哈", "contact": "18262997750", "status": 1 }
  ],
  "contact_notify_condition": {
    "status": 1,
    "status_desc": "启用中",
    "condition_list": [
      { "event_type": 1, "event_desc": "钱包余额偏低" },
      { "event_type": 2, "event_desc": "钱包余额不足" },
      { "event_type": 3, "event_desc": "钱包消耗过快", "trigger_amount": 1100 }
    ]
  }
}
```

## 返回字段说明

### wallet_info 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `agency_id` | integer | 代理商 ID |
| `agency_name` | string | 代理商名称 |
| `wallet_id` | integer | 钱包 ID，钱包账号 ID |
| `wallet_name` | string | 钱包名称 |
| `mdm_id` | integer | 主体 ID |
| `mdm_name` | string | 主体名称 |
| `balance` | integer | 余额，单位：**分**（÷100 得元） |
| `bind_advertiser_cnt` | integer | 关联账户数 |
| `binding_account_list` | integer[] | 绑定账户 ID 列表 |
| `tag_list` | string[] | 共享钱包标签 |
| `balance_info_list` | struct[] | 资金信息 |
| `contact_info_list` | struct[] | 监控预警联系人信息 |
| `contact_notify_condition` | struct[] | 监控预警信息 |

### balance_info_list 资金信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `fund_type` | enum | 资金账户类型，可通过 `node scripts/get-enum-options.mjs '{"fields": ["fund_type"]}'` 获取完整枚举值列表 |
| `balance` | integer | 余额，单位：**分** |

### contact_info_list 监控预警联系人信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `avatar_name` | string | 联系人名称 |
| `contact` | string | 联系电话 |
| `status` | integer | 联系人状态，1-启用 0-删除 |

### contact_notify_condition 监控预警信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | integer | 启用状态，1-启用 2-停用 |
| `status_desc` | string | 启用状态描述，1-启用中, 2-已停用 |
| `condition_list` | struct[] | 监控预警场景类型列表 |

### condition_list 预警条件

| 字段 | 类型 | 说明 |
|------|------|------|
| `event_type` | integer | 场景枚举，1-钱包余额偏低 2-钱包余额不足 3-钱包消耗过快 |
| `event_desc` | string | 场景描述 |
| `trigger_amount` | integer | 触发金额，单位：**分**（仅钱包消耗过快场景需要设置） |
