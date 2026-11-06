# 智在记录 · 笔记集

查询我创建的、我收到的笔记集及集内详情。基于集内笔记做总结/问答时，仍须先走 `note.md` 动态模版管线。

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
| 笔记集详情 | `POST /note/queryNoteKnowledgeDetail` |
| 我收到的笔记集 | `POST /note/queryNoteKnowledgeEmpower` |
| 我创建的笔记集 | `POST /note/queryNoteKnowledge` |

## 使用注意

- 我创建：`qryType` 必填，默认 `myCreate`。
- 我收到：`qryEmpowerToMe=true`，`qryEmpowerFromMe=false`。
- 详情：`knowledgeId` 必填；`needSummaryContent` 默认 false，需要时再开。
- 条目 `noteType` 展示前转中文（见 `note.md`）。

## 接口协议

### POST `/note/queryNoteKnowledgeDetail`  查询笔记集详情

**接口说明**：查询笔记集详情  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| knowledgeId | Long | 是 | 知识库ID |
| knowledgeSourceType | string | 否 | 知识来源类型(note:笔记, file:文件) |
| searchContent | string | 否 | 搜索内容 |
| startTime | string | 否 | 开始时间 |
| endTime | string | 否 | 结束时间 |
| pageNum | integer | 否 | 页码（默认1） |
| pageSize | integer | 否 | 每页大小（默认10） |
| needSummaryContent | boolean | 否 | 是否需要返回摘要内容(summaryContent)，默认false |
| needNoteContentTotal | boolean | 否 | 是否需要返回笔记内容总数(noteContentTotal)，默认false |

#### 请求示例

```bash
curl --request POST \
  --url 'https://openapi.zzjilu.com/api/v1/note/queryNoteKnowledgeDetail' \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "knowledgeId": 10101,
  "pageNum": 1,
  "pageSize": 10,
  "needSummaryContent": false,
  "needNoteContentTotal": false
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.knowledgeId | string | 是 | 所属知识库id |
| resultObject.boteKnowledgeId | string | 否 | bote知识库id |
| resultObject.knowledgeName | string | 是 | 知识库名称 |
| resultObject.knowledgeDetail | string | 是 | 知识库描述 |
| resultObject.knowledgeAttribute | string | 是 | 知识库属性(私密,公开,部分可见) |
| resultObject.parentKnowledgeId | string | 是 | 父知识库ID |
| resultObject.rootKnowledgeId | string | 是 | 根知识库ID |
| resultObject.frontFileId | string | 是 | 封面文件id |
| resultObject.knowledgePublic | string | 是 | 是否公开 |
| resultObject.useTotal | string | 是 | 使用次数 |
| resultObject.knowledgeType | string | 是 | 知识库类型 |
| resultObject.memberVisibility | string | 否 | 团队成员笔记可见范围（PRIVATE:私密, SHARED:共享） |
| resultObject.languageCode | string | 否 | 语言编码 |
| resultObject.squareFlag | string | 是 | 广场标识 |
| resultObject.userName | string | 是 | 用户名称 |
| resultObject.accountNum | string | 是 | 账号 |
| resultObject.avatarFileId | string | 是 | 头像文件ID |
| resultObject.contentTotal | integer | 是 | 内容总数 |
| resultObject.subscribeTotal | integer | 是 | 订阅总数 |
| resultObject.messageType | string | 是 | 消息类型 |
| resultObject.hasNotification | boolean | 是 | 是否有通知 |
| resultObject.existApprove | boolean | 是 | 是否存在审批 |
| resultObject.noteId | string | 是 | 笔记ID |
| resultObject.noteName | string | 是 | 笔记名称 |
| resultObject.noteType | string | 是 | 笔记类型 |
| resultObject.voiceFileIdList | array | 是 | 语音文件ID列表 |
| resultObject.empowerNameList | array | 是 | 授权名称列表 |
| resultObject.notChat | boolean | 是 | 是否不允许聊天 |
| resultObject.stickyFlag | boolean | 是 | 是否置顶 |
| resultObject.creatorId | string | 是 | 创建人ID |
| resultObject.createTime | string | 是 | 创建时间 |
| resultObject.updatorId | string | 是 | 更新人ID |
| resultObject.updateTime | string | 是 | 更新时间 |
| resultObject.status | string | 是 | 状态 |
| resultObject.noteTotal | integer | 是 | 笔记总数 |
| resultObject.fileTotal | integer | 是 | 文件总数 |
| resultObject.knowledgeSign | string | 是 | 知识库标记 |
| resultObject.editable | boolean | 是 | 是否可编辑（当前用户是否可关联/移除笔记） |
| resultObject.role | string | 否 | 当前用户在团队或公开笔记集中的有效角色（ADMIN/MEMBER） |
| resultObject.appletList | array | 否 | 关联的小程序列表（含小程序配置信息） |
| resultObject.pageInfo.total | integer | 是 | 总条数 |
| resultObject.pageInfo.pageNum | integer | 是 | 当前页码 |
| resultObject.pageInfo.pageSize | integer | 是 | 每页条数 |
| resultObject.pageInfo.size | integer | 是 | 当前页数量 |
| resultObject.pageInfo.startRow | integer | 是 | 起始行 |
| resultObject.pageInfo.endRow | integer | 是 | 结束行 |
| resultObject.pageInfo.pages | integer | 是 | 总页数 |
| resultObject.pageInfo.prePage | integer | 是 | 上一页 |
| resultObject.pageInfo.nextPage | integer | 是 | 下一页 |
| resultObject.pageInfo.isFirstPage | boolean | 是 | 是否第一页 |
| resultObject.pageInfo.isLastPage | boolean | 是 | 是否最后一页 |
| resultObject.pageInfo.hasPreviousPage | boolean | 是 | 是否有上一页 |
| resultObject.pageInfo.hasNextPage | boolean | 是 | 是否有下一页 |
| resultObject.pageInfo.navigatePages | integer | 是 | 导航页数 |
| resultObject.pageInfo.navigatepageNums | array | 是 | 导航页码数组 |
| resultObject.pageInfo.navigateFirstPage | integer | 是 | 导航第一页 |
| resultObject.pageInfo.navigateLastPage | integer | 是 | 导航最后一页 |
| resultObject.pageInfo.list[].creatorId | string | 是 | 创建人ID |
| resultObject.pageInfo.list[].createTime | string | 是 | 创建时间 |
| resultObject.pageInfo.list[].updatorId | string | 是 | 更新人ID |
| resultObject.pageInfo.list[].updateTime | string | 是 | 更新时间 |
| resultObject.pageInfo.list[].status | string | 是 | 状态 |
| resultObject.pageInfo.list[].knowledgeDetailId | string | 是 | 知识库明细ID |
| resultObject.pageInfo.list[].knowledgeId | string | 是 | 所属知识库id |
| resultObject.pageInfo.list[].knowledgeSourceType | string | 是 | 知识库来源类型 |
| resultObject.pageInfo.list[].knowledgeSourceId | string | 是 | 知识库来源ID |
| resultObject.pageInfo.list[].boteKnowledgeDocId | string | 是 | bote知识库文档ID |
| resultObject.pageInfo.list[].boteKnowledgeDocStatus | string | 是 | bote知识库文档状态 |
| resultObject.pageInfo.list[].docChainId | string | 是 | 文档链ID |
| resultObject.pageInfo.list[].sortOrder | string | 是 | 排序值，值越大越靠前 |
| resultObject.pageInfo.list[].rowNum | integer | 是 | 行号 |
| resultObject.pageInfo.list[].noteId | string | 是 | 笔记ID |
| resultObject.pageInfo.list[].name | string | 是 | 名称 |
| resultObject.pageInfo.list[].summary | string | 是 | 摘要 |
| resultObject.pageInfo.list[].summaryContent | string | 否 | 摘要内容（needSummaryContent=true时返回） |
| resultObject.pageInfo.list[].noteContentTotal | string | 否 | 笔记内容总数（needNoteContentTotal=true时返回） |
| resultObject.pageInfo.list[].noteType | string | 是 | 笔记类型 |
| resultObject.pageInfo.list[].catalogName | string | 是 | 目录名称 |
| resultObject.pageInfo.list[].noteUpdateTime | string | 是 | 笔记更新时间 |
| resultObject.pageInfo.list[].templateName | string | 是 | 模板名称 |
| resultObject.pageInfo.list[].detailViewed | boolean | 是 | 明细是否已查看 |
| resultObject.pageInfo.list[].contentTotal | integer | 是 | 内容总数 |
| resultObject.pageInfo.list[].voiceFileIdList | array | 是 | 语音文件ID列表 |
| resultObject.pageInfo.list[].allowDelete | boolean | 是 | 是否允许从当前笔记集移除该笔记关联 |
| resultObject.pageInfo.list[].noteCreatorId | string | 否 | 笔记正文创建人ID |
| resultObject.pageInfo.list[].userName | string | 是 | 用户名称 |
| resultObject.pageInfo.list[].accountNum | string | 是 | 账号 |
| resultObject.pageInfo.list[].avatarFileId | string | 是 | 头像文件ID |
| resultObject.pageInfo.list[].userId | string | 是 | 用户ID |
| resultObject.pageInfo.list[].exploreId | string | 是 | 探索ID |
| resultObject.pageInfo.list[].exploreCategory | string | 是 | 探索分类 |
| resultObject.pageInfo.list[].imageBase64List | array | 否 | 笔记关联的图片base64列表 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "knowledgeId": "10101",
    "boteKnowledgeId": null,
    "knowledgeName": "项目周报笔记集",
    "knowledgeDetail": "每周项目会议纪要",
    "knowledgeAttribute": "私密",
    "parentKnowledgeId": "-1",
    "rootKnowledgeId": "10101",
    "frontFileId": null,
    "knowledgePublic": "F",
    "useTotal": "0",
    "knowledgeType": "person",
    "memberVisibility": "PRIVATE",
    "languageCode": "zh_CN",
    "squareFlag": "F",
    "userName": "张三",
    "accountNum": "13900001111",
    "avatarFileId": null,
    "contentTotal": 12,
    "subscribeTotal": 0,
    "messageType": null,
    "hasNotification": false,
    "existApprove": false,
    "noteId": null,
    "noteName": null,
    "noteType": null,
    "voiceFileIdList": [],
    "empowerNameList": [],
    "notChat": false,
    "stickyFlag": false,
    "creatorId": "8912493637529600",
    "createTime": "2026-05-01 10:00:00",
    "updatorId": null,
    "updateTime": null,
    "status": "00A",
    "noteTotal": 12,
    "fileTotal": 0,
    "knowledgeSign": "",
    "editable": true,
    "role": "ADMIN",
    "appletList": [],
    "pageInfo": {
      "total": 1,
      "list": [
        {
          "knowledgeDetailId": "30101",
          "knowledgeId": "10101",
          "knowledgeSourceType": "note",
          "knowledgeSourceId": "31023",
          "boteKnowledgeDocId": null,
          "boteKnowledgeDocStatus": null,
          "docChainId": null,
          "sortOrder": 100,
          "rowNum": 1,
          "noteId": "31023",
          "name": "语音识别技术进展",
          "summary": "讨论语音识别模块升级、测试反馈及数据收集方案",
          "summaryContent": null,
          "noteContentTotal": null,
          "noteType": "voice",
          "catalogName": null,
          "noteUpdateTime": "2026-03-17 13:45:18",
          "templateName": null,
          "detailViewed": false,
          "contentTotal": 0,
          "voiceFileIdList": [
            "1351071340606681088"
          ],
          "allowDelete": true,
          "noteCreatorId": "8912493637529600",
          "userName": "张三",
          "accountNum": "13900001111",
          "avatarFileId": null,
          "userId": "8912493637529600",
          "exploreId": null,
          "exploreCategory": null,
          "imageBase64List": [],
          "creatorId": "8912493637529600",
          "createTime": "2026-05-01 10:00:00",
          "updatorId": null,
          "updateTime": null,
          "status": "00A"
        }
      ],
      "pageNum": 1,
      "pageSize": 10,
      "size": 1,
      "startRow": 0,
      "endRow": 0,
      "pages": 1,
      "prePage": 0,
      "nextPage": 0,
      "isFirstPage": true,
      "isLastPage": true,
      "hasPreviousPage": false,
      "hasNextPage": false,
      "navigatePages": 8,
      "navigatepageNums": [
        1
      ],
      "navigateFirstPage": 1,
      "navigateLastPage": 1
    }
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/note/queryNoteKnowledgeEmpower`  查询我收到的笔记集

**接口说明**：查询我收到的笔记集  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| qryEmpowerToMe | boolean | 是 | 是否查询授权给我的，固定值:true |
| qryEmpowerFromMe | boolean | 是 | 是否查询我授权出去的，固定值:false |
| knowledgeId | Long | 否 | 知识库ID |
| knowledgeEmpowerType | string | 否 | 权限类型(人,组) |
| knowledgeEmpowerTargetId | Long | 否 | 权限目标ID(用户ID,组ID) |
| knowledgeEmpowerTargetIdList | array | 否 | 权限目标ID列表 |
| qryContent | string | 否 | 查询条件 |
| pageNum | integer | 否 | 页码（默认1） |
| pageSize | integer | 否 | 每页大小（默认10） |

#### 请求示例

```bash
curl --request POST \
  --url 'https://openapi.zzjilu.com/api/v1/note/queryNoteKnowledgeEmpower' \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "qryEmpowerToMe": true,
  "qryEmpowerFromMe": false,
  "pageNum": 1,
  "pageSize": 10
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象（PageInfo分页结构） |
| resultObject.startRow | integer | 否 | 起始行 |
| resultObject.endRow | integer | 否 | 结束行 |
| resultObject.pageNum | integer | 是 | 当前页码 |
| resultObject.pageSize | integer | 是 | 每页条数 |
| resultObject.total | integer | 是 | 总记录数 |
| resultObject.pages | integer | 是 | 总页数 |
| resultObject.size | integer | 是 | 当前页实际记录数 |
| resultObject.hasNextPage | boolean | 是 | 是否TF有下一页 |
| resultObject.hasPreviousPage | boolean | 是 | 是否TF有上一页 |
| resultObject.isFirstPage | boolean | 是 | 是否TFT第一页 |
| resultObject.isLastPage | boolean | 是 | 是否TFT最后一页 |
| resultObject.prePage | integer | 否 | 上一页页码 |
| resultObject.nextPage | integer | 否 | 下一页页码 |
| resultObject.navigateFirstPage | integer | 否 | 导航第一页 |
| resultObject.navigateLastPage | integer | 否 | 导航最后一页 |
| resultObject.navigatepageNums | array | 否 | 导航页码数组 |
| resultObject.navigatePages | integer | 是 | 导航页码数量 |
| resultObject.list | array | 是 | 数据列表 |
| resultObject.list[].creatorId | string | 是 | 创建人ID |
| resultObject.list[].createTime | string | 是 | 创建时间 |
| resultObject.list[].updatorId | string | 是 | 更新人ID |
| resultObject.list[].updateTime | string | 是 | 更新时间 |
| resultObject.list[].status | string | 是 | 状态 |
| resultObject.list[].knowledgeEmpowerId | string | 是 | 权限明细id |
| resultObject.list[].knowledgeId | string | 是 | 所属知识库id |
| resultObject.list[].knowledgeEmpowerType | string | 是 | 权限类型(人,组) |
| resultObject.list[].knowledgeEmpowerTargetId | string | 是 | 目标id(用户id,组id) |
| resultObject.list[].knowledgeEmpowerEditable | string | 是 | 是否可编辑 |
| resultObject.list[].knowledgeEmpowerRole | string | 否 | 团队成员角色（ADMIN:管理员, MEMBER:成员） |
| resultObject.list[].knowledgeName | string | 是 | 知识库名称 |
| resultObject.list[].knowledgeDetail | string | 是 | 知识库描述 |
| resultObject.list[].knowledgePublic | string | 是 | 是否公开 |
| resultObject.list[].knowledgeAttribute | string | 是 | 知识库属性(私密,公开,部分可见) |
| resultObject.list[].frontFileId | string | 是 | 封面文件id |
| resultObject.list[].userName | string | 是 | 用户名称 |
| resultObject.list[].accountNum | string | 是 | 账号 |
| resultObject.list[].avatarFileId | string | 是 | 头像文件ID |
| resultObject.list[].groupName | string | 是 | 分组名称 |
| resultObject.list[].contentTotal | integer | 是 | 内容总数 |
| resultObject.list[].subscribeTotal | integer | 是 | 订阅总数 |
| resultObject.list[].noteId | string | 是 | 笔记ID |
| resultObject.list[].noteName | string | 是 | 笔记名称 |
| resultObject.list[].noteType | string | 是 | 笔记类型 |
| resultObject.list[].memberName | string | 是 | 成员名称 |
| resultObject.list[].voiceFileIdList | array | 是 | 语音文件ID列表 |
| resultObject.list[].empowerTotal | integer | 是 | 授权总数 |
| resultObject.list[].squareFlag | string | 是 | 广场标识 |
| resultObject.list[].stickyFlag | boolean | 是 | 是否置顶 |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "total": 1,
    "list": [
      {
        "knowledgeEmpowerId": "20101",
        "knowledgeId": "10101",
        "knowledgeEmpowerType": "person",
        "knowledgeEmpowerTargetId": "8912493637529600",
        "knowledgeEmpowerEditable": "T",
        "knowledgeEmpowerRole": "MEMBER",
        "knowledgeName": "项目周报笔记集",
        "knowledgeDetail": "每周项目会议纪要",
        "knowledgePublic": "F",
        "knowledgeAttribute": "私密",
        "frontFileId": null,
        "userName": "张三",
        "accountNum": "13900001111",
        "avatarFileId": null,
        "groupName": null,
        "contentTotal": 12,
        "subscribeTotal": 0,
        "noteId": null,
        "noteName": null,
        "noteType": null,
        "memberName": "张三",
        "voiceFileIdList": [],
        "empowerTotal": 3,
        "squareFlag": "F",
        "stickyFlag": false,
        "creatorId": "8912493637529600",
        "createTime": "2026-05-01 10:00:00",
        "updatorId": null,
        "updateTime": null,
        "status": "00A"
      }
    ],
    "pageNum": 1,
    "pageSize": 10,
    "size": 1,
    "startRow": 0,
    "endRow": 0,
    "pages": 1,
    "prePage": 0,
    "nextPage": 0,
    "isFirstPage": true,
    "isLastPage": true,
    "hasPreviousPage": false,
    "hasNextPage": false,
    "navigatePages": 8,
    "navigatepageNums": [
      1
    ],
    "navigateFirstPage": 1,
    "navigateLastPage": 1
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/note/queryNoteKnowledge`  查询我创建的笔记集

**接口说明**：查询我创建的笔记集  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| qryType | string | 是 | 查询类型(square:广场, personal:个人, browseHistory:浏览历史, myCreate:我创建的, myEditable:我可编辑的)；本接口使用myCreate |
| qryContent | string | 否 | 查询条件 |
| knowledgeId | Long | 否 | 知识库ID |
| parentKnowledgeId | Long | 否 | 父知识库ID |
| knowledgePublic | string | 否 | 是否公开(T:公开, F:不公开) |
| knowledgeSourceType | string | 否 | 知识来源类型(note:笔记, file:文件) |
| knowledgeType | string | 否 | 笔记集类型 |
| searchContent | string | 否 | 搜索内容 |
| editable | boolean | 否 | 是否查询可编辑知识库 |
| random | boolean | 否 | 是否随机获取 |
| knowledgeIdList | array | 否 | 查询的知识库ID列表 |
| pageNum | integer | 否 | 页码（默认1） |
| pageSize | integer | 否 | 每页大小（默认10） |

#### 请求示例

```bash
curl --request POST \
  --url 'https://openapi.zzjilu.com/api/v1/note/queryNoteKnowledge' \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "qryType": "myCreate",
  "pageNum": 1,
  "pageSize": 10
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象（PageInfo分页结构） |
| resultObject.startRow | integer | 否 | 起始行 |
| resultObject.endRow | integer | 否 | 结束行 |
| resultObject.pageNum | integer | 是 | 当前页码 |
| resultObject.pageSize | integer | 是 | 每页条数 |
| resultObject.total | integer | 是 | 总记录数 |
| resultObject.pages | integer | 是 | 总页数 |
| resultObject.size | integer | 是 | 当前页实际记录数 |
| resultObject.hasNextPage | boolean | 是 | 是否TF有下一页 |
| resultObject.hasPreviousPage | boolean | 是 | 是否TF有上一页 |
| resultObject.isFirstPage | boolean | 是 | 是否TFT第一页 |
| resultObject.isLastPage | boolean | 是 | 是否TFT最后一页 |
| resultObject.prePage | integer | 否 | 上一页页码 |
| resultObject.nextPage | integer | 否 | 下一页页码 |
| resultObject.navigateFirstPage | integer | 否 | 导航第一页 |
| resultObject.navigateLastPage | integer | 否 | 导航最后一页 |
| resultObject.navigatepageNums | array | 否 | 导航页码数组 |
| resultObject.navigatePages | integer | 是 | 导航页码数量 |
| resultObject.list | array | 是 | 数据列表 |
| resultObject.list[].knowledgeId | string | 是 | 知识库ID |
| resultObject.list[].boteKnowledgeId | string | 否 | bote知识库id |
| resultObject.list[].knowledgeName | string | 是 | 知识库名称 |
| resultObject.list[].knowledgeDetail | string | 是 | 知识库描述 |
| resultObject.list[].knowledgeAttribute | string | 是 | 知识库属性(私密,公开,部分可见) |
| resultObject.list[].parentKnowledgeId | string | 是 | 父知识库(不为-1时为目录) |
| resultObject.list[].rootKnowledgeId | string | 是 | 根知识库 |
| resultObject.list[].frontFileId | string | 是 | 封面文件id |
| resultObject.list[].knowledgePublic | string | 是 | 是否公开 |
| resultObject.list[].useTotal | string | 是 | 使用次数 |
| resultObject.list[].knowledgeType | string | 是 | 知识库类型(person:个人知识库, note_comm:笔记共用知识) |
| resultObject.list[].memberVisibility | string | 否 | 团队成员笔记可见范围（PRIVATE:私密, SHARED:共享） |
| resultObject.list[].languageCode | string | 否 | 语言编码 |
| resultObject.list[].squareFlag | string | 是 | 广场标识 |
| resultObject.list[].userName | string | 是 | 用户名称 |
| resultObject.list[].accountNum | string | 是 | 账号 |
| resultObject.list[].avatarFileId | string | 是 | 头像文件ID |
| resultObject.list[].contentTotal | integer | 是 | 内容总数 |
| resultObject.list[].subscribeTotal | integer | 是 | 订阅总数 |
| resultObject.list[].messageType | string | 是 | 消息类型(empower:权限,subscribe:订阅) |
| resultObject.list[].creatorId | string | 是 | 创建人ID |
| resultObject.list[].createTime | string | 是 | 创建时间 |
| resultObject.list[].updatorId | string | 是 | 更新人ID |
| resultObject.list[].updateTime | string | 是 | 更新时间 |
| resultObject.list[].status | string | 是 | 状态 |
| resultObject.list[].hasNotification | boolean | 是 | 是否有通知 |
| resultObject.list[].existApprove | boolean | 是 | 是否存在审批 |
| resultObject.list[].noteId | string | 是 | 笔记ID |
| resultObject.list[].noteName | string | 是 | 笔记名称 |
| resultObject.list[].noteType | string | 是 | 笔记类型 |
| resultObject.list[].voiceFileIdList | array | 是 | 语音文件ID列表 |
| resultObject.list[].empowerNameList | array | 是 | 授权名称列表 |
| resultObject.list[].stickyFlag | boolean | 是 | 是否置顶 |
| resultObject.list[].notChat | boolean | 是 | 是否不允许聊天 |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "total": 1,
    "list": [
      {
        "knowledgeId": "10101",
        "boteKnowledgeId": null,
        "knowledgeName": "项目周报笔记集",
        "knowledgeDetail": "每周项目会议纪要",
        "knowledgeAttribute": "私密",
        "parentKnowledgeId": "-1",
        "rootKnowledgeId": "10101",
        "frontFileId": null,
        "knowledgePublic": "F",
        "useTotal": "0",
        "knowledgeType": "person",
        "memberVisibility": "PRIVATE",
        "languageCode": "zh_CN",
        "squareFlag": "F",
        "userName": "张三",
        "accountNum": "13900001111",
        "avatarFileId": null,
        "contentTotal": 12,
        "subscribeTotal": 0,
        "messageType": null,
        "hasNotification": false,
        "existApprove": false,
        "noteId": null,
        "noteName": null,
        "noteType": null,
        "voiceFileIdList": [],
        "empowerNameList": [],
        "stickyFlag": false,
        "notChat": false,
        "creatorId": "8912493637529600",
        "createTime": "2026-05-01 10:00:00",
        "updatorId": null,
        "updateTime": null,
        "status": "00A"
      }
    ],
    "pageNum": 1,
    "pageSize": 10,
    "size": 1,
    "startRow": 0,
    "endRow": 0,
    "pages": 1,
    "prePage": 0,
    "nextPage": 0,
    "isFirstPage": true,
    "isLastPage": true,
    "hasPreviousPage": false,
    "hasNextPage": false,
    "navigatePages": 8,
    "navigatepageNums": [
      1
    ],
    "navigateFirstPage": 1,
    "navigateLastPage": 1
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```
