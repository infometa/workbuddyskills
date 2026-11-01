## 创建登录授权链接

```shell
zijizhang-cli account create_auth_url
```

### 返回参数

| 参数   | 类型     | 说明                      |
|:-----|:-------|:------------------------|
| code | int    | 状态码，`200` 代表成功，其他代表失败   |
| msg  | string | 提示信息，失败时为异常信息           |
| data | object | 授权链接相关信息，当code=200时返回 |

data 参数说明

| 参数         | 类型     | 说明                    |
|:-----------|:-------|:----------------------|
| url        | string | 快速登录的授权链接             |
| expire_in  | int    | 链接有效时间，单位为秒          |
| auth_key   | string | 授权关联的凭证令牌             |

### 返回例子

#### 成功

```json
{
    "msg": "ok",
    "code": 200,
    "data": {
        "url": "https://www.zijizhang.com/administrator/#/quick-login/be6c2bd6f034441136ee851d",
        "expire_in": 1800,
        "auth_key": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbiI6ImJlNmMyYmQ2ZjAzNDQ0MTEzNmVlODUxZCIsImV4cCI6MTc3NjIyMjg5M30.EBnmefSf8WEUVCRumsVCnn4LvpO8rj2HmwbF9RV4Hgc"
    }
}
```
