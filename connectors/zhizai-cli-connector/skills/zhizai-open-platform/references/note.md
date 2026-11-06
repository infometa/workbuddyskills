# 智在记录 · 笔记

通过开放 API 完成笔记检索、问答总结、CRUD、上传与下载。不要凭印象猜字段；机器调用以本文件「接口协议」为准。

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

## 动态模版管线（基于笔记作答 / 总结 · 强制）

**可跳过**（仅限）：纯新建/编辑/删除、上传、下录音、视频笔记创建、文字总结 SSE、以及不依赖多篇笔记成文的操作。

否则必须：

1. **归一化**：主题词、时间词、用户自带模版。
2. **查模版**：`GET /know/queryStandardInputOutputByCommand?command=`（URL 编码）。先关键词；`output` 空再用完整原句；两次仍空则语义兜底。
3. **查笔记**：`POST /note/queryNoteList`（时间范围、`pageSize` 默认 100 翻页）；需要正文再 `GET /note/querySingleNoteDetail`。
4. **成文**：用户模版 > 接口 `output` > 语义兜底（概览→发现→建议）。无相关笔记则柔和说明，禁止编造。

### 时间粒度

| 表述 | startTime | endTime |
|---|---|---|
| 本周 | 本周一 00:00:00 | 本周日 23:59:59 |
| 本月 | 本月 1 日 00:00:00 | 本月最后一天 23:59:59 |
| 本季度 | 本季首月 1 日 00:00:00 | 本季末月最后一天 23:59:59 |
| 本年 | 1 月 1 日 00:00:00 | 12 月 31 日 23:59:59 |

不得跨入未来。「上周/上月」等减一个周期。

### note_type 中文映射

| 值 | 中文 |
|---|---|
| text | 文本 |
| voice | 录音 |
| document | 文档 |
| link | 链接 |
| image | 图片 |
| knowCard | 知识卡片 |

### noteState（仅进度，非正文）

`completed` 已完成 / `pending` 处理中 / `recognizing` 转写中 / `analyzing` 总结中 / `failed` 失败。

## 意图路由

| 意图 | 接口入口 |
|---|---|
| 标准输出模版 | `GET /know/queryStandardInputOutputByCommand` |
| 列表筛选 | `POST /note/queryNoteList` |
| 详情 | `GET /note/querySingleNoteDetail` |
| 构建进度 | `GET /note/queryNoteStatus` |
| 删除 | `GET /note/deleteNote`（先确认） |
| 修改标题/摘要/总结 | `POST /note/updateNoteInfo` |
| 上传文件 | `POST /file/uploadSingleFile` |
| 创建笔记 | `POST /note/createNote` |
| 文字总结（SSE） | `POST /note/createTextNoteSummary` |
| 视频建笔记 | `POST /note/addVideoLinkNoteByFileId` |
| 下载录音 | `GET /note/downloadNoteAudio` |
| 问小智 URL 配置 | `GET /note/addOrUpdateParamsByCode` |

## 新建与文件依赖

| 场景 | noteType | 须先上传 |
|---|---|---|
| 文本 | text | 否 |
| 链接 | link | 否 |
| 文档 | document | 是 → `documentContent.fileId` |
| 图片 | image | 是 → `imageContent.fileIds[].fileId` |
| 录音 | voice | 是 → `voiceContent.voiceFileId` |
| 视频笔记 | — | 是 → `addVideoLinkNoteByFileId.fileId` |

推荐：`uploadSingleFile` → `createNote`（或视频接口）→ 必要时 `queryNoteStatus`。

## 结果呈现

- 列表：`id`、`title`、中文类型、`create_time`；有 `summary` 用总结否则 `abstract`。
- 保存成功：真实 ID、标题、`note_state`；处理中勿伪造成文完成。
- 进度接口只谈系统阶段，内容问题必须用列表/详情。

## 接口协议

### POST `/note/queryNoteList`  查询笔记列表

**接口说明**：获取用户笔记列表，支持模糊查询，支持分页，支持按是否返回详情查询  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| title | string | 否 | 标题（模糊匹配） |
| abstractContent | string | 否 | 摘要（模糊匹配） |
| summary | string | 否 | 总结（模糊匹配） |
| content | string | 否 | 内容（模糊匹配） |
| noteType | string | 否 | 笔记类型（voice/text/image/document/link） |
| noteCategory | integer | 否 | 笔记分类 |
| startTime | string | 否 | 开始时间 |
| endTime | string | 否 | 结束时间 |
| pageNum | integer | 否 | 当前页码（默认1） |
| pageSize | integer | 否 | 每页条数（默认10） |
| withContent | string | 否 | 是否返回内容（true/false） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/note/queryNoteList \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
	"title": "语音识别",
	"abstractContent": "",
	"summary": "",
	"content": "",
	"noteType": "",
	"noteCategory": null,
	"startTime": "",
	"endTime": "",
	"pageNum": 1,
	"pageSize": 20,
	"withContent": ""
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.startRow | string | 否 | 起始行 |
| resultObject.pageNum | integer | 是 | 当前页码 |
| resultObject.pageSize | integer | 是 | 每页条数 |
| resultObject.total | string | 是 | 总记录数 |
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
| resultObject.list[].id | string | 是 | 记录ID |
| resultObject.list[].title | string | 是 | 标题 |
| resultObject.list[].summary | string | 是 | 总结 |
| resultObject.list[].abstract | string | 是 | 摘要 |
| resultObject.list[].content | object | 否 | 内容（录音笔记为转写数组，文本/文档类型为字符串，可为空） |
| resultObject.list[].status | string | 是 | 状态码 |
| resultObject.list[].note_type | string | 是 | 笔记类型 |
| resultObject.list[].note_state | string | 是 | 笔记状态 |
| resultObject.list[].create_time | string | 是 | 创建时间 |
| resultObject.list[].creator_id | string | 是 | 创建人ID |
| resultObject.list[].scene_name | string | 是 | 场景名称 |
| resultObject.list[].scene_id | string | 是 | 场景ID |
| resultObject.list[].source_note_id | string | 否 | 来源笔记ID |
| resultObject.list[].note_category | integer | 否 | 笔记分类 |
| resultObject.list[].device_sn | string | 否 | 录音卡SN码（仅录音笔记返回） |
| resultObject.list[].latitude | string | 否 | 录音地理位置纬度（仅录音笔记返回） |
| resultObject.list[].longitude | string | 否 | 录音地理位置经度（仅录音笔记返回） |
| resultObject.list[].rec_end_time | string | 否 | 录制结束时间（仅录音笔记返回） |
| resultObject.list[].account_num | string | 否 | 创建者账号/手机号（仅录音笔记返回） |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "startRow": "0",
    "navigatepageNums": null,
    "prePage": 0,
    "hasNextPage": false,
    "nextPage": 0,
    "pageSize": 20,
    "endRow": "0",
    "list": [
      {
        "id": "31023",
        "title": "语音识别技术进展",
        "summary": "![ai:1351071340606681088](https://lingxi.iwhalecloud.com/LCDP-RECORD/lcdp-app/server/app/file/file/id/1351071340606681088?appId=1277144354029191168&width=1736&height=1920)\n\n## 模块升级进展\n- **语音转文字模块升级**：多模型切换策略\n- **说话人分离模块效果提升**：说话人日志错误率从37%降到6%\n- **声纹向量模块升级**：维度从192维升到256维",
        "content": [],
        "status": "00A",
        "abstract": "讨论语音识别模块升级、测试反馈及数据收集方案，包括方言处理和英文识别优化",
        "note_type": "voice",
        "create_time": "2026-03-17 13:45:18",
        "creator_id": "8912493637529600",
        "note_state": "completed",
        "scene_name": "智能场景",
        "source_note_id": null,
        "scene_id": "0",
        "note_category": null,
        "device_sn": "1234567890",
        "latitude": "32.060255",
        "longitude": "118.796877",
        "rec_end_time": "2026-03-17 13:45:18",
        "account_num": "13900001111"
      }
    ],
    "pageNum": 1,
    "navigatePages": 0,
    "total": "1",
    "navigateFirstPage": 0,
    "pages": 0,
    "size": 1,
    "isLastPage": false,
    "hasPreviousPage": false,
    "navigateLastPage": 0,
    "isFirstPage": false
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/note/querySingleNoteDetail`  查询笔记

**接口说明**：查询单条笔记信息，支持按笔记ID查询笔记详情  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| noteId | string | 是 | 笔记ID |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/note/querySingleNoteDetail?noteId=30480' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.id | string | 是 | 笔记ID |
| resultObject.title | string | 是 | 标题 |
| resultObject.summary | string | 是 | 总结内容 |
| resultObject.abstract | string | 是 | 摘要 |
| resultObject.content | object | 是 | 详细内容（录音笔记为转写数组，文本/文档类型为字符串） |
| resultObject.status | string | 是 | 状态码 |
| resultObject.note_type | string | 是 | 笔记类型 |
| resultObject.note_state | string | 是 | 笔记状态 |
| resultObject.create_time | string | 是 | 创建时间 |
| resultObject.creator_id | string | 是 | 创建人ID |
| resultObject.scene_name | string | 是 | 场景名称 |
| resultObject.scene_id | string | 是 | 场景ID |
| resultObject.source_note_id | string | 否 | 来源笔记ID |
| resultObject.note_category | integer | 否 | 笔记分类 |
| resultObject.device_sn | string | 否 | 录音卡SN码（仅录音笔记返回） |
| resultObject.latitude | string | 否 | 录音地理位置纬度（仅录音笔记返回） |
| resultObject.longitude | string | 否 | 录音地理位置经度（仅录音笔记返回） |
| resultObject.rec_end_time | string | 否 | 录制结束时间（仅录音笔记返回） |
| resultObject.account_num | string | 否 | 创建者账号/手机号（仅录音笔记返回） |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "id": "30480",
    "title": "通话测试确认",
    "summary": "## 会议目标\n- 进行通话设备测试。\n\n## 关键信息\n- 通话开始阶段，陈楚旭多次重复“喂”和“你好”，并进行“测试测试”的呼叫。",
    "content": [
      {
        "recording_id": "14853",
        "transcript": [
          {
            "raw_text": "嗯，喂喂喂喂喂喂，你好，你好，你好喂喂喂，测试测试",
            "start": 280,
            "end": 7245,
            "tn_text": "嗯，",
            "text": "嗯，喂喂喂喂喂喂，你好，你好，你好喂喂喂，测试测试。",
            "spk": "陈楚旭"
          }
        ],
        "duration": "7",
        "start_time": null,
        "create_time": "2026-01-26 10:52:40"
      }
    ],
    "status": "00A",
    "abstract": "通话开始前的设备测试和连接确认过程",
    "note_type": "voice",
    "create_time": "2026-01-26 10:52:40",
    "creator_id": "8912493637529600",
    "note_state": "completed",
    "scene_name": "智能场景",
    "source_note_id": null,
    "scene_id": "0",
    "note_category": null,
    "device_sn": "0012345678",
    "latitude": null,
    "longitude": null,
    "rec_end_time": "2026-01-26 10:52:47",
    "account_num": "13900001111"
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/note/deleteNote`  删除笔记

**接口说明**：删除笔记，支持按笔记ID删除笔记  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| noteId | string | 是 | 笔记ID |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/note/deleteNote?noteId=31559' \
  --header 'Authorization: your api-key'
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

### GET `/note/queryNoteStatus`  查询笔记状态

**接口说明**：查询笔记处理进度，completed:已完成；pending:处理中；recognizing:转写中；analyzing:总结中；failed:失败  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| noteId | string | 是 | 笔记ID |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/note/queryNoteStatus?noteId=31560' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.noteState | string | 是 | 笔记状态（completed：已完成） |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 是 | 错误信息列表 |
| guidance | null | 是 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "noteState": "completed"
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/note/updateNoteInfo`  修改笔记

**接口说明**：修改笔记，部分修改笔记标题、短摘要或AI录音总结；未传或空白的字段保持不变  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| noteId | string | 是 | 笔记ID |
| title | string | 否 | 笔记标题（未传或空白保持不变） |
| abstractContent | string | 否 | 笔记摘要（未传或空白保持不变） |
| summary | string | 否 | 笔记总结（未传或空白保持不变） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/note/updateNoteInfo \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
	"noteId": "31560",
	"title": "测试1",
	"abstractContent": "",
	"summary": ""
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

### POST `/note/createNote`  创建笔记

**接口说明**：创建新笔记，支持创建录音、文档、图片、链接、文字等类型的笔记，支持按指定场景总结  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| noteType | string | 是 | 笔记类型（voice/text/image/document/link） |
| sceneId | Long | 否 | 场景ID（按指定场景总结） |
| voiceContent | object | 否 | 录音笔记内容（noteType=voice时传入） |
| voiceContent.text | string | 否 | 随手记（语音转文字内容） |
| voiceContent.voiceFileId | string | 否 | 音频文件ID |
| voiceContent.recStartTime | string | 否 | 录制开始时间 |
| voiceContent.recEndTime | string | 否 | 录制结束时间（yyyy-MM-dd HH:mm:ss） |
| voiceContent.duration | string | 否 | 录音时长 |
| voiceContent.imageFileIds | array | 否 | 随手拍图片文件ID列表 |
| voiceContent.appendNoteId | string | 否 | 追加笔记ID |
| voiceContent.deviceSn | string | 否 | 录音卡SN码 |
| voiceContent.latitude | string | 否 | 录音地理位置纬度 |
| voiceContent.longitude | string | 否 | 录音地理位置经度 |
| textContent | object | 否 | 文字笔记内容（noteType=text时传入） |
| textContent.title | string | 否 | 笔记标题 |
| textContent.content | string | 否 | 文字内容 |
| imageContent | object | 否 | 图片笔记内容（noteType=image时传入） |
| imageContent.fileIds | array | 否 | 图片文件列表 |
| imageContent.fileIds[].fileId | string | 否 | 图片文件ID |
| imageContent.fileIds[].remark | string | 否 | 图片备注 |
| documentContent | object | 否 | 文档笔记内容（noteType=document时传入） |
| documentContent.fileId | string | 否 | 文件ID |
| documentContent.fileName | string | 否 | 文件名称 |
| linkContent | object | 否 | 链接笔记内容（noteType=link时传入） |
| linkContent.url | string | 否 | 链接地址 |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/note/createNote \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "noteType" : "document",
  "documentContent" : {
    "fileId" : "1357179569765883904",
    "fileName" : "开店选址手册.docx"
  }
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.id | string | 是 | 笔记ID |
| resultObject.title | string | 是 | 标题 |
| resultObject.summary | string | 是 | 总结内容（处理中时为提示文案） |
| resultObject.abstract | string | 是 | 摘要（处理中时为提示文案） |
| resultObject.content | object | 否 | 详细内容（处理中时为null；录音笔记为转写数组，文本/文档类型为字符串） |
| resultObject.status | string | 是 | 状态码 |
| resultObject.note_type | string | 是 | 笔记类型 |
| resultObject.note_state | string | 是 | 笔记状态（pending:处理中，completed:已完成） |
| resultObject.create_time | string | 是 | 创建时间 |
| resultObject.creator_id | string | 是 | 创建人ID |
| resultObject.scene_name | string | 否 | 场景名称（pending时为null） |
| resultObject.scene_id | string | 否 | 场景ID（pending时为null） |
| resultObject.source_note_id | string | 否 | 来源笔记ID |
| resultObject.note_category | integer | 否 | 笔记分类 |
| resultObject.device_sn | string | 否 | 录音卡SN码（仅录音笔记返回） |
| resultObject.latitude | string | 否 | 录音地理位置纬度（仅录音笔记返回） |
| resultObject.longitude | string | 否 | 录音地理位置经度（仅录音笔记返回） |
| resultObject.rec_end_time | string | 否 | 录制结束时间（仅录音笔记返回） |
| resultObject.account_num | string | 否 | 创建者账号/手机号（仅录音笔记返回） |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "id": "31561",
    "title": "开店选址手册.docx",
    "summary": "等待约 1 分钟！整理下桌面的便利贴，把杂乱归位，记录就新鲜出炉咯～",
    "content": null,
    "status": "00A",
    "abstract": "等待约 1 分钟！整理下桌面的便利贴，把杂乱归位，记录就新鲜出炉咯～",
    "note_type": "document",
    "create_time": "2026-04-08 17:17:48",
    "creator_id": "8912493637529600",
    "note_state": "pending",
    "scene_name": null,
    "source_note_id": null,
    "scene_id": null,
    "note_category": null,
    "device_sn": null,
    "latitude": null,
    "longitude": null,
    "rec_end_time": null,
    "account_num": null
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/note/createTextNoteSummary`  生成文字笔记总结

**接口说明**：生成文字笔记总结  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| content | string | 是 | 笔记内容 |
| sceneId | string | 是 | 场景ID（用于AI总结的场景） |

#### 请求示例

```bash
curl --request POST \
  --url 'https://openapi.zzjilu.com/api/v1/note/createTextNoteSummary' \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "content" : "笔记内容",
  "sceneId" : "场景ID"
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| Content-Type | header | 是 | text/event-stream，SSE流式响应 |
| data | string | 是 | SSE事件流数据，每个data事件为AI总结的增量文本片段，逐块推送直至流结束 |

#### 响应示例

```json
data: ## 会议目标
data: - 进行通话设备测试。
data: （SSE流式响应，每个data事件为AI总结增量文本片段，直至流结束）
```

### POST `/note/addVideoLinkNoteByFileId`  根据视频文件ID新增视频链接笔记

**接口说明**：根据视频文件ID创建视频链接笔记，服务端自动完成音频提取、转写、AI总结与知识库同步（异步处理）  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| fileId | Long | 是 | 视频文件ID（文件服务中的文件ID，需先调用文件上传接口获取） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/note/addVideoLinkNoteByFileId \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
  "fileId" : 1410460000000000123
}'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功，-1表示失败 |
| resultMsg | string | 是 | 结果信息，成功时为success，失败时为失败原因描述 |
| resultObject | object | 是 | 返回数据对象；失败时若笔记已创建仍会返回 |
| resultObject.mainNoteId | string | 是 | 主笔记ID；部分失败场景（转写失败）笔记已创建时也会返回 |
| resultObject.notesCount | integer | 是 | 当前用户有效笔记数量（排除demo来源笔记）；失败时为null |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "mainNoteId": "1410461159968960512",
    "notesCount": 23
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/file/uploadSingleFile`  文件上传

**接口说明**：文件上传，仅支持单个文件上传，可以通过设置compressFile控制是否压缩存储  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| compressFile | boolean | 否 | 是否压缩存储 |
| file | file | 是 | 上传的文件（支持图片、文档等） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/file/uploadSingleFile \
  --header 'Authorization: your api-key' \
  --header 'content-type: multipart/form-data' \
  --form file=@/Users/xxx/Desktop/20260408_085359_8922_0.m4a
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.fileId | string | 是 | 文件ID |
| resultObject.storeType | string | 是 | 存储类型 |
| resultObject.filePathInServer | string | 是 | 服务器文件路径 |
| resultObject.fileName | string | 是 | 文件名称 |
| resultObject.fileDesc | string | 否 | 文件描述 |
| resultObject.createDate | string | 是 | 创建时间 |
| resultObject.statusCd | string | 是 | 状态码 |
| resultObject.statusDate | string | 是 | 状态时间 |
| resultObject.appId | string | 是 | 应用ID |
| resultObject.fileSize | string | 否 | 文件大小 |
| resultObject.fileType | string | 否 | 文件类型 |
| resultObject.isPicture | string | 否 | TF为图片 |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 是 | 错误信息列表 |
| guidance | null | 是 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "fileId": "1359112903776927744",
    "storeType": "MINIO",
    "filePathInServer": "lcdp-g/2026/04/08/a7cfe905-108f-4e38-b495-320ae3545f25.m4a",
    "fileName": "20260408_085359_8922_0.m4a",
    "fileDesc": null,
    "createDate": "2026-04-08 18:29:28",
    "statusCd": "00A",
    "statusDate": "2026-04-08 18:29:28",
    "appId": "1358762423120310272",
    "fileSize": null,
    "fileType": null,
    "isPicture": null
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/note/downloadNoteAudio`  下载录音笔记音频

**接口说明**：根据笔记ID下载当前用户录音笔记的音频文件；单个音频直接返回音频文件，多个音频打包为ZIP压缩包下载  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| noteId | Long | 是 | 笔记ID |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/note/downloadNoteAudio?noteId=30480' \
  --header 'Authorization: your api-key' \
  --output 'note-audio.zip'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| Content-Type | header | 是 | 单个音频返回音频文件MIME类型（如audio/mpeg）；多个音频打包返回application/octet-stream |
| Content-Disposition | header | 是 | 单个音频为inline;filename=笔记标题.扩展名；多个音频为attachment;filename=笔记标题.zip |
| responseBody | binary | 是 | 二进制文件流，单个音频为音频文件，多个音频为ZIP压缩包 |
| HTTP 404 | error | 否 | 笔记不存在或录音文件不存在 |
| HTTP 400 | error | 否 | 当前笔记不是录音笔记 |

#### 响应示例

```json
{
  "description": "成功时返回二进制文件流（单个音频文件或ZIP压缩包），非JSON格式",
  "successResponse": {
    "status": 200,
    "headers": {
      "Content-Type": "application/octet-stream",
      "Content-Disposition": "attachment; filename*=UTF-8''通话测试确认.zip"
    },
    "body": "<binary file stream>"
  },
  "errorResponses": [
    {
      "status": 404,
      "message": "笔记不存在"
    },
    {
      "status": 400,
      "message": "当前笔记不是录音笔记"
    },
    {
      "status": 404,
      "message": "录音文件不存在"
    },
    {
      "status": 404,
      "message": "录音文件不存在: <fileId>"
    }
  ]
}
```

### GET `/know/queryStandardInputOutputByCommand`  按指令查询标准输入输出模板

**接口说明**：按指令查询标准输入输出模板，支持控制问小智指定大模型的输入输出格式  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| command | string | 是 | 指令 |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/know/queryStandardInputOutputByCommand?command=生成周报' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，查询成功 |
| resultObject | object | 是 | 返回数据对象 |
| resultObject.input | string | 是 | 查询输入提示词/检索条件描述 |
| resultObject.output | string | 是 | 查询输出结果/周报内容 |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | null | 否 | 错误信息列表 |
| guidance | null | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "查询成功",
  "resultObject": {
    "input": "检索知识库中本周（2024年11月18日-2024年11月24日）【部门例会/项目评审会/跨部门协调会/研谈沟通】类工作会议笔记：1. 周报基础信息：姓名{姓名}、岗位{岗位}、周期{YYYY.MM.DD-YYYY.MM.DD}、汇报对象{汇报对象}；2 核心工作模块：{模块1（优先级1）、模块2（优先级2）、模块3（优先级3）}；3. 量化指标：{指标1、指标2、指标3}；4. 特殊要求：{重点内容+新增模块+汇报风格}；要求输出格式：含\"工作概述、核心成果、数据复盘、问题与改进、下周计划\"五大模块，核心成果需关联知识库笔记来源。",
    "output": "【{周/月/季/年报标题}】{用户姓名}-2025.11.10-2025.11.16{周/月/季/年}报（汇报对象：{汇报人姓名}）<br>一、工作概述<br>本周聚焦核心项目V2.0版本开发迭代目标，完成3个核心功能模块开发，修复线上Bug12个（修复率92.3%），编写技术文档5份；重点攻克\"用户登录权限加密\"技术难点，确保模块按时交付；同步配合测试部完成首轮功能测试，整体工作符合项目排期，开发任务完成率100%。<br><br>二、核心成果（按优先级排序）<br>1. 项目V2.0核心功能开发完成（重点成果）<br>成果内容：独立完成\"用户登录权限加密\"\"数据批量导出\"\"异常日志自动上报\"3个核心模块开发，代码提交量2100行，通过内部代码评审（通过率100%），按时交付测试部，较计划提前0.5个工作日。<br>关键动作：11月10日拆解模块开发任务并制定时间表、11月11-13日完成\"权限加密\"模块开发与自测、11月14-15日完成剩余2个模块开发、11月16日提交代码评审并交付测试。<br><br>2. 线上Bug高效修复<br>成果内容：本周接收线上Bug工单13个，完成修复12个，修复率92.3%，平均修复时长2.5小时（目标4小时）；其中2个高优先级Bug（影响10%用户登录）1小时内响应并修复，未造成用户流失。<br>关键动作：11月12日建立\"Bug优先级分级处理机制\"、每日早会同步Bug修复进度、晚间复盘修复方案优化点。<br><br>3. 技术文档规范化编写<br>成果内容：完成《V2.0权限加密模块开发文档》《Bug修复方案汇总》等5份技术文档编写，其中3份被纳入部门\"技术文档规范案例\"，为后续迭代及新人交接提供支撑。<br>关键动作：11月13-15日分模块同步编写文档、11月16日结合代码评审意见优化文档细节。"
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/note/addOrUpdateParamsByCode`  添加或修改问小智URL配置

**接口说明**：添加或修改问小智URL配置  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| teamId | string | 是 | 团队ID |
| url | string | 是 | 问小智配置链接地址 |

#### 请求示例

```bash
curl --request GET \
  --url https://openapi.zzjilu.com/api/v1/note/addOrUpdateParamsByCode?teamId=&url= \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 状态码，0 表示成功, 其它均为失败 |
| resultMsg | string | 是 | 提示信息 |
| resultObject | string | 是 | 返回结果字符串 |
| stack | string | 是 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "",
  "resultMsg": "",
  "resultObject": "",
  "stack": ""
}
```
