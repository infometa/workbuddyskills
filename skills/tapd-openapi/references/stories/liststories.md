# ListStories

## 接口描述
- 批量查询所有符合条件的需求（Story）列表，分页显示，默认一页30条。
- **注意**：支持通过ID查询单个需求信息，结果以列表形式返回。

> **状态查询注意事项** : 按状态查询时，建议使用 `v_status` 参数直接传中文状态名（如 `v_status=规划中`），同时设置 `with_v_status=1` 以便返回中文状态。因为需求状态的英文 Key 是每个项目单独配置的，使用中文名更直观、不易出错。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/stories

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| name | 否 | string | 标题 | 支持模糊匹配 |
| priority | 否 | string | 优先级（旧字段，已废弃，请用 priority_label） | |
| priority_label | 否 | string | 优先级（推荐），所见即所得，直接传 High/Middle/Low 等文本值，无需数字映射 | |
| business_value | 否 | integer | 业务价值 | |
| status | 否 | string | 状态 | 支持枚举查询 |
| v_status | 否 | string | 状态（支持中文状态名） | |
| with_v_status | 否 | string | 值=1可以返回中文状态 | |
| label | 否 | string | 标签查询 | 支持枚举查询 |
| workitem_type_id | 否 | string | 需求类别ID | 支持枚举查询 |
| version | 否 | string | 版本 | |
| module | 否 | string | 模块 | |
| feature | 否 | string | 特性 | |
| test_focus | 否 | string | 测试重点 | |
| size | 否 | integer | 规模 | |
| tech_risk | 否 | string | 技术风险 | |
| owner | 否 | string | 处理人 | 支持模糊匹配 |
| cc | 否 | string | 抄送人 | 支持模糊匹配 |
| creator | 否 | string | 创建人 | 支持多人员查询 |
| developer | 否 | string | 开发人员 | |
| begin | 否 | date | 预计开始 | 支持时间查询 |
| due | 否 | date | 预计结束 | 支持时间查询 |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | 支持时间查询 |
| completed | 否 | datetime | 完成时间 | 支持时间查询 |
| iteration_id | 否 | string | 迭代ID | 支持不等于查询或枚举查询 |
| include_sub_iteration | 否 | string | 是否包含子迭代 | 取值 0或1，默认0 |
| effort | 否 | string | 预估工时 | |
| effort_completed | 否 | string | 完成工时 | |
| remain | 否 | float | 剩余工时 | |
| exceed | 否 | float | 超出工时 | |
| category_id | 否 | integer | 需求分类 | 支持枚举查询 |
| include_sub_category | 否 | string | 是否包含子分类 | 取值 0或1，默认0 |
| release_id | 否 | integer | 发布计划 | |
| source | 否 | string | 需求来源 | |
| type | 否 | string | 需求类型 | |
| ancestor_id | 否 | integer | 祖先需求，查询指定需求下所有子需求 | |
| parent_id | 否 | integer | 父需求 | |
| children_id | 否 | string | 子需求 | 为空查询传：丨 |
| include_leaf_stories | 否 | string | 是否包含子需求 | 取值 0或1，默认0 |
| description | 否 | string | 详细描述 | 支持模糊匹配 |
| custom_field_* | 否 | string/integer | 自定义字段参数 | 支持枚举查询 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 | |
| limit | 否 | integer | 返回数量限制，默认30，最大200 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/stories?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Story": {
                "id": "1010104801124922063",
                "workitem_type_id": "1010104801000022091",
                "name": "story_created_by_api",
                "description": "<div>富文本HTML内容</div>",
                "workspace_id": "10104801",
                "creator": "v_xuanfang",
                "created": "2025-06-16 14:42:59",
                "modified": "2025-06-16 16:46:51",
                "status": "planning",
                "step": "",
                "owner": "",
                "cc": "",
                "begin": null,
                "due": null,
                "size": null,
                "priority": "",
                "developer": "",
                "iteration_id": "0",
                "test_focus": "",
                "type": "",
                "source": "",
                "module": "",
                "version": "",
                "completed": null,
                "category_id": "-1",
                "path": "1010104801124922063:",
                "parent_id": "0",
                "children_id": "|",
                "ancestor_id": "1010104801124922063",
                "level": "0",
                "business_value": "5",
                "effort": null,
                "effort_completed": "0",
                "exceed": "0",
                "remain": "0",
                "release_id": "0",
                "bug_id": null,
                "templated_id": null,
                "created_from": "api",
                "feature": "",
                "label": "",
                "progress": "0",
                "is_archived": "0",
                "tech_risk": "2",
                "flows": null,
                "custom_field_one": "",
                "custom_field_two": "",
                "custom_field_three": "1",
                "custom_field_four": "",
                "custom_field_five": ""
            }
        }
    ],
    "info": "success"
}
```
