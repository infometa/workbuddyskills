# AddStory

## 接口描述
在项目下创建一条需求（Story），一次只能插入一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/stories

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 一次插入一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| name | 是 | string | 标题 |
| priority_label | 否 | string | 优先级（推荐），如 High / Middle / Low |
| business_value | 否 | integer | 业务价值 |
| version | 否 | string | 版本 |
| module | 否 | string | 模块 |
| test_focus | 否 | string | 测试重点 |
| size | 否 | integer | 规模 |
| owner | 否 | string | 处理人 |
| cc | 否 | string | 抄送人 |
| creator | 否 | string | 创建人 |
| developer | 否 | string | 开发人员 |
| begin | 否 | date | 预计开始（格式：YYYY-MM-DD） |
| due | 否 | date | 预计结束（格式：YYYY-MM-DD） |
| iteration_id | 否 | string | 迭代ID |
| parent_id | 否 | integer | 父需求ID |
| effort | 否 | string | 预估工时 |
| category_id | 否 | integer | 需求分类 |
| workitem_type_id | 否 | integer | 需求类别 |
| release_id | 否 | integer | 发布计划 |
| source | 否 | string | 来源 |
| type | 否 | string | 类型 |
| feature | 否 | string | 特性 |
| tech_risk | 否 | string | 技术风险 |
| description | 否 | string | 详细描述（支持 HTML） |
| label | 否 | string | 标签，多个用英文竖线分隔，不存在时自动创建 |
| templated_id | 否 | integer | 模板ID |
| is_apply_template_default_value | 否 | integer | 传 1 则从模板继承默认值和保密设置 |
| apply_template | 否 | string | 模板选项，多个用英文逗号分隔，支持 preset_stories / preset_tasks |
| custom_field_* | 否 | string/integer | 自定义字段，具体字段名通过「获取需求自定义字段配置」接口获取 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 |
| cus_{自定义字段别名} | 否 | string | 自定义字段（后台自动转义为 custom_field_*） |

## 请求示例

```bash
# 创建最简需求
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/stories" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "新需求标题"
  }'

# 创建带完整信息的需求
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/stories" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "需求标题",
    "priority_label": "High",
    "owner": "username",
    "description": "<div>详细描述内容</div>",
    "begin": "2026-03-10",
    "due": "2026-03-31",
    "iteration_id": "迭代ID"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Story": {
            "id": "1010104801124922063",
            "workitem_type_id": "1010104801000022091",
            "name": "新需求标题",
            "description": null,
            "workspace_id": "10104801",
            "creator": "v_xuanfang",
            "created": "2025-06-16 14:42:59",
            "modified": "2025-06-16 14:42:59",
            "status": "planning",
            "owner": "",
            "iteration_id": "0",
            "parent_id": "0",
            "category_id": "-1",
            "label": "",
            "progress": "0",
            "created_from": "api"
        }
    },
    "info": "success"
}
```

## 注意事项

- `priority` 字段已废弃，请统一使用 `priority_label`
- `status` / `module` / `iteration_id` 等动态字段的可选值需通过「获取需求所有字段及候选值」接口获取
- `label` 中不存在的标签会自动创建，多个标签用英文竖线 `|` 分隔
- `description` 支持 HTML 富文本格式
