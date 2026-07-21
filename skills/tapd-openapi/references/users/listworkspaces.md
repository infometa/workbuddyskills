# ListWorkspaces

## 接口描述
获取当前用户有权限访问的所有工作空间（项目）列表。当 `TAPD_WORKSPACE_ID` 和 `TAPD_WORKSPACE_IDS` 均未配置时，可用此接口自动获取。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/open_user_app/workspace_list

**支持格式：** JSON

### 请求参数

无额外请求参数，使用 Token 自动获取当前用户可访问的工作空间列表。

## 请求示例

```bash
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/open_user_app/workspace_list"
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Workspace": {
                "id": "20001921",
                "name": "示例项目",
                "pretty_name": "20001921"
            }
        },
        {
            "Workspace": {
                "id": "33356006",
                "name": "DevOps项目",
                "pretty_name": "33356006"
            }
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | 工作空间（项目）ID |
| name | 工作空间名称 |
| pretty_name | 工作空间标识 |
