# FASC API 5.0 参考文档

本文档包含法大大 FASC API 5.0 的核心接口说明，供 fadada-document-sign Skill 使用。

## API 基础信息

| 项目 | 值 |
|------|-----|
| API 版本 | FASC API 5.0 |
| 正式环境 | https://api.fadada.com/api/v5 |
| UAT测试环境 | https://uat-api.fadada.com/api/v5 |
| 认证方式 | HMAC-SHA256 |

## 认证流程

### 1. 获取 Access Token

**接口**: `POST /service/get-access-token`

**请求头**:
```
X-FASC-App-Id: {app_id}
X-FASC-Sign: {signature}
X-FASC-Timestamp: {timestamp}
X-FASC-Nonce: {nonce}
X-FASC-Grant-Type: client_credential
X-FASC-Api-SubVersion: 5.1
Content-Type: application/json
```

**请求体**:
```json
{
  "appId": "{app_id}",
  "grantType": "client_credential"
}
```

**响应**:
```json
{
  "code": "100000",
  "data": {
    "accessToken": "...",
    "expiresIn": 7200
  }
}
```

### 1.1. 查询授权用户列表（获取归属企业 OpenCorpId）

**接口**: `POST /app/get-openId-list`

**请求体**:
```json
{
  "idType": "corp",
  "owner": true,
  "listPageNo": 1,
  "listPageSize": 1
}
```

**请求参数说明**:

| 参数名称 | 数据类型 | 必须 | 说明 |
| ------------ | -------- | ---- | ------------------------------------------------------------ |
| idType | string | 是 | 查询授权用户类型：corp=企业，person=个人 |
| owner | boolean | 否 | 是否仅查询应用归属企业，默认 false。true=仅查询归属企业，false=查询所有用户 |
| listPageNo | int | 否 | 分页页码，从 1 开始 |
| listPageSize | int | 否 | 每页条数，默认 100，最大 100 |

**响应**:
```json
{
  "code": "100000",
  "data": {
    "totalCount": 1,
    "listPageCount": 1,
    "listPageNo": 1,
    "countInPage": 1,
    "openIdInfos": [
      {
        "name": "企业名称",
        "openId": "a814cfeeefdb4a5c92b9e147f02fe99d",
        "clientId": "AutoClient..."
      }
    ]
  }
}
```

**响应参数说明**:

| 参数名称 | 数据类型 | 必须 | 说明 |
| --------------- | -------- | ---- | -------------------------------------------------- |
| openIdInfos | array | 是 | 授权应用用户的信息数组 |
| openIdInfos[].name | string | 否 | 企业或个人名称 |
| openIdInfos[].openId | string | 是 | 企业 openCorpId 或个人 openUserId |
| openIdInfos[].clientId | string | 是 | 企业 clientCorpId 或个人 clientUserId |

## 文件接口

### 2. 获取上传 URL

**接口**: `POST /file/get-upload-url`

**请求体**:
```json
{
  "fileType": "doc"
}
```

**响应**:
```json
{
  "code": "100000",
  "data": {
    "uploadUrl": "https://...",
    "fddFileUrl": "https://..."
  }
}
```

### 3. 处理文件

**接口**: `POST /file/process`

**请求体**:
```json
{
  "fddFileUrlList": [{
    "fileType": "doc",
    "fddFileUrl": "https://...",
    "fileName": "合同.pdf",
    "fileFormat": "pdf"
  }]
}
```

**响应**:
```json
{
  "code": "100000",
  "data": {
    "fileIdList": [{
      "fileId": "...",
      "fileType": "doc",
      "fileName": "合同.pdf",
      "fileTotalPages": 3
    }]
  }
}
```

## 签署任务接口

### 4. 创建签署任务

**接口**: `POST /sign-task/create`

**请求体**:
```json
{
  "initiator": {
    "idType": "corp",
    "openId": "{open_corp_id}"
  },
  "signTaskSubject": "合同签署",
  "signDocType": "contract",
  "autoStart": true,
  "autoFinish": true,
  "docs": [{
    "docId": "doc1",
    "docName": "合同.pdf",
    "docFileId": "{file_id}"
  }],
  "actors": [{
    "actor": {
      "actorId": "signer1",
      "actorType": "person",
      "actorName": "张三",
      "permissions": ["sign"],
      "notification": {
        "sendNotification": true,
        "notifyWay": "mobile",
        "notifyAddress": "13800138000"
      }
    }
  }]
}
```

**响应**:
```json
{
  "code": "100000",
  "data": {
    "signTaskId": "..."
  }
}
```

### 5. 获取签署链接

**接口**: `POST /sign-task/actor/get-url`

**请求体**:
```json
{
  "signTaskId": "{sign_task_id}",
  "actorId": "signer1"
}
```

**响应**:
```json
{
  "code": "100000",
  "data": {
    "actorSignTaskUrl": "https://fdd1.cn/xxx",
    "actorSignTaskEmbedUrl": "https://...",
    "actorSignTaskMiniAppInfo": {
      "wxOriginalId": "gh_xxx",
      "path": "/signPackages/pages/..."
    }
  }
}
```

### 6. 查询签署任务详情

**接口**: `POST /sign-task/app/get-detail`

**请求体**:
```json
{
  "signTaskId": "{sign_task_id}"
}
```

**响应**:
```json
{
  "code": "100000",
  "data": {
    "signTaskId": "...",
    "taskStatus": "signing",
    "signTaskSubject": "...",
    "docs": [...],
    "actors": [...]
  }
}
```

## 模板接口

### 7. 查询签署模板列表

**接口**: `POST /sign-template/get-list`

**请求体**:
```json
{
  "templateName": "",
  "pageNo": 1,
  "pageSize": 20
}
```

### 8. 查询签署模板详情

**接口**: `POST /sign-template/get-detail`

**请求体**:
```json
{
  "templateId": "{template_id}"
}
```

## 签署方类型

| actorType | 说明 | 必填字段 |
|-----------|------|---------|
| person | 个人签署 | name, phone/email |
| corp | 企业签署 | name, contactName, phone/email |

## 签署任务状态

| 状态 | 说明 |
|------|------|
| draft | 草稿 |
| waiting | 待提交 |
| signing | 签署中 |
| finished | 已完成 |
| cancelled | 已撤销 |
| abolished | 已作废 |
| expired | 已过期 |

## 返回码

| 返回码 | 说明 |
|--------|------|
| 100000 | 请求成功 |
| 100001 | 系统错误 |
| 100002 | 访问凭证失效 |
| 200001 | 参数错误 |
| 200002 | 签名验证失败 |
| 300001 | 业务处理失败 |
| 400001 | 权限不足 |

## 错误排查

### initiator 参数必填
创建签署任务时必须提供 initiator，使用 open_corp_id 作为 openId。

### 文件格式限制
- 支持格式: PDF, OFD
- 最大文件大小: 50MB

### 签署方信息
- 个人签署: 必须提供 name + (phone 或 email)
- 企业签署: 必须提供 name + contactName + (phone 或 email)
