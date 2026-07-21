# UpdateWiki

## 接口描述
更新一条 Wiki，返回更新后的数据。每次只允许更新一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/tapd_wikis

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只允许更新一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| id | 是 | integer | Wiki ID |
| name | 否 | string | 标题 |
| description | 否 | string | 富文本 |
| markdown_description | 否 | string | Markdown |
| note | 否 | string | 备注 |
| parent_wiki_id | 否 | string | 父wiki ID |

## 请求示例

```bash
# 更新 Wiki 标题和富文本内容
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tapd_wikis" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "id": "Wiki ID",
    "name": "新标题",
    "description": "<div>更新后的富文本内容</div>"
  }'

# 更新 Wiki Markdown 内容
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tapd_wikis" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "id": "Wiki ID",
    "markdown_description": "# 更新后的标题\n\n更新后的正文"
  }'

# 移动 Wiki 到其他父节点下
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tapd_wikis" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "id": "Wiki ID",
    "parent_wiki_id": "目标父wiki ID"
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
            "description": "内容被更新",
            "markdown_description": "",
            "is_rich": "1",
            "parent_wiki_id": "0",
            "note": "",
            "view_count": "1",
            "created": "2020-08-26 10:15:28",
            "creator": "v_xuanfang",
            "modified": "2020-08-26 10:30:11",
            "modifier": "dev"
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

- `workspace_id` 和 `id` 为必填参数
- 只需传入要更新的字段，未传入的字段保持不变
- `description`（富文本）和 `markdown_description`（Markdown）二选一即可
- 可通过修改 `parent_wiki_id` 将 Wiki 移动到其他父节点下
