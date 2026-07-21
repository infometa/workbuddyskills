# GetUserInfo

## 接口描述
可用于获取当前用户信息，便于后续需要使用用户信息时，直接调用此接口获取。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/users/info

**支持格式：** JSON/XML（默认 JSON）

### 请求参数

无额外请求参数，使用 Token 自动获取当前用户信息。

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/users/info'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "id": "6081",
        "nick": "robertyang",
        "name": "杨晓俊",
        "avatar": "http://tiger.oa.com/0/users/avatar/6081/jpg/0/large",
        "enabled": "1",
        "status_id": "1",
        "status_name": "在职"
    },
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | 用户ID |
| nick | 英文ID（nick 和 id 都能作为用户的唯一标识） |
| name | 中文名 |
| avatar | 头像 |
| enabled | 是否有效：1-是；0-否 |
| status_id | 状态：1-在职；2-离职；3-冻结 |
| status_name | 状态名 |
