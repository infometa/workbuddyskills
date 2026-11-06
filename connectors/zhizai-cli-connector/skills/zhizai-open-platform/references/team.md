# 智在记录 · 团队

团队与成员的增删改查。纯团队运维可跳过动态模版管线。删除团队/成员、加人前必须向用户确认。

## 统一结果判定

先看 HTTP：`400`/`401`/`406` → 无权限（检查 `ZHIZAI_REC_API_KEY`）。再看 JSON：`resultCode == "0"` 为成功。

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {},
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

对用户：可用 `resultMsg` 短句；禁止展示完整 Key、`stack`、未脱敏 `errorInfos`。限流 ≤2 次/秒。

`ZHIZAI_BASE_URL` = `https://openapi.zzjilu.com/api/v1`。Header：`Authorization: ${ZHIZAI_REC_API_KEY}`（无 Bearer）。


## 意图路由

| 意图 | 接口 |
|---|---|
| 添加团队 | `POST /team/addTeam` |
| 更新团队 | `POST /team/updateTeam` |
| 删除团队 | `GET /team/deleteTeam`（仅无子团队） |
| 团队树 | `POST /team/queryTeamTree` |
| 成员分页 | `POST /team/queryTeamMemberPage` |
| 添加成员 | `POST /team/addTeamMember`（`phone` 必填） |
| 删除成员 | `GET /team/deleteTeamMember` |

## 使用注意

- 展示成员 `phone`/`email` 时脱敏；勿整表无差别导出。
- `memberType=team` 时传 `memberTeamId`；默认 `person`。
- 头像可用 `uploadSingleFile` 得到的 `fileId`。

## 接口协议

### POST `/team/addTeam`  添加团队

**接口说明**：添加团队  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| parentTeamId | Long | 否 | 父级团队ID（不传则创建根团队） |
| teamName | string | 是 | 团队名称 |
| description | string | 否 | 团队描述 |
| sortOrder | Long | 否 | 排序 |
| avatarFileId | string | 否 | 团队头像文件ID |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/team/addTeam\
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "parentTeamId": 0,
  "teamName": "",
  "description": "",
  "sortOrder": 0
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码 |
| resultMsg | string | 是 | 结果信息 |
| resultObject | Long | 是 | 返回数据 |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 是 | 错误信息列表（为null） |
| guidance | null | 是 | 引导信息（为null） |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": 6218980040421376,
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/team/queryTeamMemberPage`  查询团队成员列表（分页）

**接口说明**：查询团队成员列表（分页）  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | Integer | 否 | 页数，默认 1 |
| pageSize | Integer | 否 | 每页数量，默认 20 |
| teamId | Long | 是 | 团队ID |
| keyword | string | 否 | 搜索关键词（姓名、组织、部门） |
| querySubTeamFlag | boolean | 否 | 是否查询子团队，默认false，true：则查询当前团队及所有子团队的数据 |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/team/queryTeamMemberPage\
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "pageNum": 0,
  "pageSize": 0,
  "teamId": 0,
  "keyword": "",
  "querySubTeamFlag": true
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | object | 是 | 分页结果对象 |
| stack | string | 是 | 异常堆栈信息 |

#### 响应示例

```json
{
  "resultCode": "",
  "resultMsg": "",
  "resultObject": {
    "total": 0,
    "list": [
      {
        "id": 0,
        "teamId": 0,
        "memberType": "",
        "memberTeamId": 0,
        "memberPersonId": 0,
        "memberName": "",
        "role": "",
        "position": "",
        "isManager": "",
        "displayOrder": 0,
        "employeeId": "",
        "email": "",
        "phone": "",
        "organization": "",
        "department": "",
        "avatarFileId": "",
        "joinDate": "",
        "subFlag": true
      }
    ],
    "pageNum": 0,
    "pageSize": 0,
    "size": 0,
    "startRow": 0,
    "endRow": 0,
    "pages": 0,
    "prePage": 0,
    "nextPage": 0,
    "isFirstPage": true,
    "isLastPage": true,
    "hasPreviousPage": true,
    "hasNextPage": true,
    "navigatePages": 0,
    "navigatepageNums": [],
    "navigateFirstPage": 0,
    "navigateLastPage": 0
  },
  "stack": ""
}
```

### GET `/team/deleteTeam`  删除团队

**接口说明**：删除团队（只能删除没有子团队的团队）  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| teamId | Long | 是 | 团队ID |

#### 请求示例

```bash
curl --request GET \
  --url https://openapi.zzjilu.com/api/v1/team/deleteTeam?teamId=0\
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | null | 是 | 返回数据对象（为null） |
| stack | string | 是 | 异常堆栈信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": null,
  "stack": ""
}
```

### POST `/team/addTeamMember`  添加团队成员

**接口说明**：添加团队成员  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| teamId | Long | 是 | 团队ID |
| memberType | string | 否 | 成员类型：team-子团队，person-个人（默认person） |
| memberTeamId | Long | 否 | 子团队ID（memberType=team时有效） |
| memberPersonId | Long | 否 | 个人ID（memberType=person时有效） |
| memberName | string | 否 | 在团队中显示的名称（可自定义） |
| role | string | 否 | 角色 |
| position | string | 否 | 职位/职级 |
| permissions | string | 否 | 权限配置（json格式） |
| isManager | string | 否 | 是否是管理者（true-是，false-否） |
| employeeId | string | 否 | 工号 |
| email | string | 否 | 邮箱 |
| phone | string | 是 | 手机号 |
| avatarFileId | string | 否 | 头像文件ID |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/team/addTeamMember\
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "teamId": 0,
  "memberType": "person",
  "memberName": "",
  "employeeId": "",
  "email": "",
  "phone": ""
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码 |
| resultMsg | string | 是 | 结果信息 |
| resultObject | Long | 是 | 返回数据（团队成员ID） |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 是 | 错误信息列表（为null） |
| guidance | null | 是 | 引导信息（为null） |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": 1234567890123456800,
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/team/deleteTeamMember`  删除团队成员

**接口说明**：删除团队成员  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| memberId | Long | 是 | 团队成员ID |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/team/deleteTeamMember?memberId=12345' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | null | 是 | 返回数据对象（为null） |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": null,
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/team/updateTeam`  更新团队

**接口说明**：更新团队  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| teamId | Long | 是 | 团队ID |
| teamName | string | 否 | 团队名称 |
| description | string | 否 | 团队描述 |
| sortOrder | Long | 否 | 排序 |
| avatarFileId | string | 否 | 团队头像文件ID |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/team/updateTeam\
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "teamId": 0,
  "teamName": "",
  "description": "",
  "sortOrder": 0
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码 |
| resultMsg | string | 是 | 结果信息 |
| resultObject | null | 是 | 返回数据对象（为null） |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 是 | 错误信息列表（为null） |
| guidance | null | 是 | 引导信息（为null） |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": null,
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/team/queryTeamTree`  查询团队树

**接口说明**：查询团队树形结构  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| keyword | string | 否 | 搜索关键词（组织或成员名称） |
| parentTeamId | Long | 否 | 父团队ID（不传则查询根团队） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/team/queryTeamTree\
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "keyword": "",
  "parentTeamId": 0
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | array | 是 | 团队树数据集合 |
| stack | string | 是 | 异常堆栈信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": [
    {
      "teamId": 0,
      "memberTeamId": 0,
      "employeeId": null,
      "userId": 0,
      "teamCode": "",
      "teamName": "",
      "fullTeamName": "",
      "description": "",
      "avatarFileId": "",
      "teamLevel": 0,
      "memberCount": 0,
      "phone": "",
      "isFriend": true,
      "authorize": true,
      "subFlag": true,
      "sortOrder": 0,
      "children": [
        {
          "teamId": 0,
          "memberTeamId": 0,
          "employeeId": null,
          "userId": 0,
          "teamCode": "",
          "teamName": "",
          "fullTeamName": "",
          "description": "",
          "avatarFileId": "",
          "teamLevel": 0,
          "memberCount": 0,
          "phone": "",
          "isFriend": true,
          "authorize": true,
          "subFlag": true,
          "sortOrder": 0,
          "children": []
        }
      ]
    }
  ],
  "stack": ""
}
```
