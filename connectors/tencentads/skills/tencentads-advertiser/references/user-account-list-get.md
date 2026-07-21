# 查询竞价广告主账号列表 (user_account_list/get)

## 请求参数

### 必需参数

无（所有参数均为可选）

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| corporation_name_fuzzy_list | string[] | 公司名称模糊匹配列表，最多 2 个字符串，每个字符串长度 2~50 字符 |
| page | integer | 页码，最小值 1，默认值 1 |
| page_size | integer | 每页条数，最小值 1，最大值 500，默认值 10 |

> **脚本层说明**：`get-account-list.mjs` 已封装该接口，无需传入 account_id 或 token，基于当前登录用户的 user_id 自动查询。

> **分页上限限制**：严格要求 `page × page_size ≤ 13000`，超出此限制接口将报错。

## 响应字段

### list（struct[]）— 账号信息列表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告账户 ID |
| account_type | integer | 账户类型（1: 竞价广告主） |
| nick_name | string | 账户简称/昵称 |
| corporation_name | string | 企业名称（公司全称） |

### page_info（struct）— 分页信息

| 字段名 | 类型 | 说明 |
|--------|------|------|
| page | integer | 当前页码 |
| page_size | integer | 每页条数 |
| total_number | integer | 总记录数 |
| total_page | integer | 总页数 |

## 应答示例

```json
{
  "code": 0,
  "message": "",
  "message_cn": "",
  "data": {
    "list": [
      {
        "account_id": 770592,
        "account_type": 1,
        "nick_name": "腾讯",
        "corporation_name": "腾讯计算机系统有限公司"
      }
    ],
    "page_info": {
      "total_number": 38,
      "total_page": 4,
      "page": 1,
      "page_size": 10
    }
  }
}
```
