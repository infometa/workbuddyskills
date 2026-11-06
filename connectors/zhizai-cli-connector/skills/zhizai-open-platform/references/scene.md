# 智在记录 · 场景与知识卡

查询总结场景与知识卡笔记。创建笔记或文字总结需要 `sceneId` 时先读本文件。

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
| 我的场景 | `GET /note/queryMySceneList` |
| 内置场景 | `GET /note/queryInnerSceneList` |
| 知识卡分页 | `POST /note/queryKnowledgeCardByPage` |

## 使用注意

- `createNote.sceneId` / `createTextNoteSummary.sceneId` 必须来自场景列表真实 `id`。
- 内置场景用 `groupInfo` 把分类 ID 转成中文分类名再展示。
- 知识卡 `summary_content` 可能为密文；对用户优先用 `summary` / `cards` 明文。

## 接口协议

### GET `/note/queryMySceneList`  查询我的场景列表

**接口说明**：查询我的场景列表，支持选择是否包含共享场景  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| includeSharedFlag | boolean | 否 | 是否包含共享场景，默认false |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/note/queryMySceneList?includeSharedFlag=true' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | array | 是 | 场景信息列表 |
| resultObject[].id | string | 是 | 场景ID |
| resultObject[].scene_name | string | 是 | 场景名称 |
| resultObject[].scene_desc | string | 是 | 场景描述 |
| resultObject[].scene_require | string | 否 | 场景提示词 |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": [
    {
      "id": "10192",
      "scene_name": "通用会议",
      "scene_desc": "快速生成清晰的会议记录"
    },
    {
      "id": "10194",
      "scene_name": "客户拜访总结",
      "scene_desc": "不仅仅是客户拜访总结，还是一份项目战术简报"
    }
  ],
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### GET `/note/queryInnerSceneList`  查询内置场景列表

**接口说明**：查询内置场景列表，返回按分类组织的内置场景数据  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |

#### 请求示例

```bash
curl --request GET \
  --url 'https://openapi.zzjilu.com/api/v1/note/queryInnerSceneList' \
  --header 'Authorization: your api-key'
```

#### 响应参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| resultCode | string | 是 | 结果码，0表示成功 |
| resultMsg | string | 是 | 结果信息，成功时为success |
| resultObject | object | 是 | 返回数据对象，结构为 Map<分类ID, 场景列表[]>，并包含 groupInfo 字段 |
| resultObject.{categoryId} | array | 是 | 场景分类下的场景列表，key为分类ID（如400011、200012等） |
| resultObject.{categoryId}[].id | string | 是 | 场景ID |
| resultObject.{categoryId}[].scene_name | string | 是 | 场景名称 |
| resultObject.{categoryId}[].scene_desc | string | 是 | 场景描述 |
| resultObject.groupInfo | object | 是 | 分类ID到分类名称的映射，如 {"400011":"会议","200012":"客户拜访"} |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "110019": [
      {
        "id": "10721",
        "scene_name": "AI外脑辅助分析",
        "scene_desc": "借助AI外脑能力，分析内容存在的风险、分歧、隐患、冲突等，给出建议和行动方案"
      }
    ],
    "800015": [
      {
        "id": "10383",
        "scene_name": "面试自我复盘",
        "scene_desc": "提供AI教练，帮助面试者进行面试复盘，发现问题点，提出改进建议，提高面试成功概率"
      },
      {
        "id": "10807",
        "scene_name": "晋级答辩自我复盘",
        "scene_desc": "提供AI教练，帮助参加职级晋级答辩者进行复盘，发现问题点，提出改进建议，协助你晋级成功"
      }
    ],
    "groupInfo": {
      "200012": "客户拜访",
      "300013": "学习成长",
      "400011": "会议"
    }
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```

### POST `/note/queryKnowledgeCardByPage`  分页查询我创建的知识卡笔记

**接口说明**：分页查询我创建的知识卡笔记  

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| pageNum | integer | 否 | 当前页码（默认1） |
| pageSize | integer | 否 | 每页条数（默认10） |

#### 请求示例

```bash
curl --request POST \
  --url https://openapi.zzjilu.com/api/v1/note/queryKnowledgeCardByPage \
  --header 'Authorization: your api-key' \
  --header 'content-type: application/json' \
  --data '{
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
| resultObject.hasNextPage | boolean | 是 | 是否有下一页 |
| resultObject.hasPreviousPage | boolean | 是 | 是否有上一页 |
| resultObject.isFirstPage | boolean | 是 | 是否第一页 |
| resultObject.isLastPage | boolean | 是 | 是否最后一页 |
| resultObject.prePage | integer | 否 | 上一页页码 |
| resultObject.nextPage | integer | 否 | 下一页页码 |
| resultObject.navigateFirstPage | integer | 否 | 导航第一页 |
| resultObject.navigateLastPage | integer | 否 | 导航最后一页 |
| resultObject.navigatepageNums | array | 否 | 导航页码数组 |
| resultObject.navigatePages | integer | 是 | 导航页码数量 |
| resultObject.list | array | 是 | 数据列表 |
| resultObject.list[].id | string | 是 | 记录ID |
| resultObject.list[].name | string | 是 | 名称/标题 |
| resultObject.list[].summary | string | 是 | 摘要 |
| resultObject.list[].summary_content | string | 否 | 总结内容（加密存储） |
| resultObject.list[].status | string | 是 | 状态码 |
| resultObject.list[].create_time | string | 是 | 创建时间 |
| resultObject.list[].creator_id | string | 是 | 创建人ID |
| resultObject.list[].cards | array | 是 | 知识卡列表 |
| resultObject.list[].cards[].id | string | 是 | 知识卡ID |
| resultObject.list[].cards[].title | string | 是 | 知识卡标题 |
| resultObject.list[].cards[].summary | string | 否 | 知识卡摘要 |
| resultObject.list[].cards[].answer | string | 是 | 知识卡答案 |
| resultObject.list[].cards[].remarks | string | 是 | 知识卡备注/解析 |
| stack | string | 否 | 异常堆栈信息 |
| errorInfos | array | 否 | 错误信息列表 |
| guidance | string | 否 | 引导信息 |

#### 响应示例

```json
{
  "resultCode": "0",
  "resultMsg": "success",
  "resultObject": {
    "total": 31,
    "list": [
      {
        "id": "31943",
        "name": "记账APP优化会议",
        "summary": "讨论记账APP三大功能优化：账单导入稳定性、AI分类准确率、收支分析深度，制定开发优先级和时间表",
        "summary_content": "{cipher}{aes}mhKP0j8CZFT+IKGVt440m8gSLErum7/fiQsDTAiMlEHhGvp9MhYGGsDN1iM1JmgXlOK4wvYGW68EYUI1dWC+lGF2nrJ9dXRClo4k82OSbJ8=",
        "status": "00A",
        "creator_id": "8764642605125632",
        "create_time": "2026-04-22 23:25:54",
        "cards": [
          {
            "id": "24793211863852020",
            "title": "记账APP用户反馈的3个主要问题是什么？",
            "summary": null,
            "answer": "AI自动分类准确率低、账单导入功能不稳定、AI收支分析功能比较浅显。",
            "remarks": "## 核心结论\n\n用户反馈的三大核心问题是：AI自动分类准确率低、账单导入功能不稳定、AI收支分析功能浅显。"
          }
        ]
      }
    ],
    "pageNum": 1,
    "pageSize": 10,
    "size": 10,
    "startRow": 0,
    "endRow": 9,
    "pages": 4,
    "prePage": 0,
    "nextPage": 2,
    "isFirstPage": true,
    "isLastPage": false,
    "hasPreviousPage": false,
    "hasNextPage": true,
    "navigatePages": 8,
    "navigatepageNums": [
      1,
      2,
      3,
      4
    ],
    "navigateFirstPage": 1,
    "navigateLastPage": 4
  },
  "stack": "",
  "errorInfos": null,
  "guidance": null
}
```
