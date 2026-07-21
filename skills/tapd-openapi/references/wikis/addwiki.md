# AddWiki

## 接口描述
在项目下创建一条 Wiki，一次只能插入一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/tapd_wikis

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 一次插入一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| name | 是 | string | 标题 |
| creator | 是 | string | 创建人 |
| description | 否 | string | 富文本 |
| markdown_description | 否 | string | Markdown |
| note | 否 | string | 备注 |
| parent_wiki_id | 否 | string | 父wiki ID |

## 请求示例

```bash
# 创建最简 Wiki
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tapd_wikis" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "Wiki 标题",
    "creator": "username"
  }'

# 创建带 Markdown 内容的 Wiki
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tapd_wikis" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "Wiki 标题",
    "creator": "username",
    "markdown_description": "# 标题\n\n正文内容",
    "parent_wiki_id": "父wiki ID"
  }'

# 创建带富文本内容的 Wiki
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tapd_wikis" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "Wiki 标题",
    "creator": "username",
    "description": "<div>富文本内容</div>",
    "note": "备注信息"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Wiki": {
            "id": "1210104801000043897",
            "name": "test111",
            "workspace_id": "10104801",
            "description": "xxxxxxx",
            "markdown_description": "",
            "is_rich": "1",
            "parent_wiki_id": "0",
            "note": "",
            "view_count": "0",
            "created": "2020-08-26 10:15:28",
            "creator": "v_xuanfang",
            "modified": "2020-08-26 10:15:28",
            "modifier": "v_xuanfang"
        }
    },
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

## 注意事项

- `name`、`creator`、`workspace_id` 为必填参数
- `description`（富文本）和 `markdown_description`（Markdown）二选一即可，同时传以 `description` 为准
- `parent_wiki_id` 不传或传 `"0"` 表示创建顶层 Wiki
