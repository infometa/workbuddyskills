# ListWikis

## 接口描述
返回符合查询条件的所有 Wiki（分页显示，默认一页30条）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/tapd_wikis

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | |
| name | 否 | string | 标题 | |
| modifier | 否 | string | 修改人 | |
| creator | 否 | string | 创建人 | |
| note | 否 | string | 备注 | |
| view_count | 否 | string | 浏览量 | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | 支持时间查询 |
| limit | 否 | integer | 返回数量限制，默认30 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/tapd_wikis?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Wiki": {
                "id": "1210104801000043827",
                "name": "test888",
                "workspace_id": "10104801",
                "description": "",
                "markdown_description": "",
                "is_rich": "0",
                "parent_wiki_id": "0",
                "note": "",
                "view_count": "0",
                "created": "2020-08-25 11:24:44",
                "creator": "dev",
                "modified": "2020-08-25 11:24:44",
                "modifier": "dev"
            }
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | ID |
| name | 标题 |
| description | 富文本 |
| markdown_description | Markdown |
| parent_wiki_id | 父wiki ID |
| author | 修改人 |
| creator | 创建人 |
| note | 备注 |
| view_count | 浏览量 |
| created | 创建时间 |
| modified | 最后修改时间 |
| modifier | 最后修改人 |
| workspace_id | 项目ID |
