# CountStories

## 接口描述
计算符合查询条件的需求数量并返回。

> **状态查询注意事项** 按状态查询时，建议使用 `v_status` 参数直接传中文状态名（如 `v_status=规划中`），同时设置 `with_v_status=1` 以便返回中文状态。因为需求状态的英文 Key 是每个项目单独配置的，使用中文名更直观、不易出错。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/stories/count

**支持格式：** JSON/XML（默认 JSON）

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| name | 否 | string | 标题 | 支持模糊匹配 |
| priority | 否 | string | 优先级。推荐使用 priority_label | |
| priority_label | 否 | string | 优先级（推荐） | |
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
| effort | 否 | string | 预估工时 | |
| effort_completed | 否 | string | 完成工时 | |
| remain | 否 | float | 剩余工时 | |
| exceed | 否 | float | 超出工时 | |
| category_id | 否 | integer | 需求分类 | 支持枚举查询 |
| release_id | 否 | integer | 发布计划 | |
| source | 否 | string | 需求来源 | |
| type | 否 | string | 需求类型 | |
| ancestor_id | 否 | integer | 祖先需求，查询指定需求下所有子需求 | |
| parent_id | 否 | integer | 父需求 | |
| children_id | 否 | string | 子需求 | 为空查询传：丨 |
| description | 否 | string | 详细描述 | 支持模糊匹配 |
| custom_field_* | 否 | string/integer | 自定义字段参数 | 支持枚举查询 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 | |
| include_sub_category | 否 | string | 是否包含子分类 | 取值 0或1，默认0 |
| include_sub_iteration | 否 | string | 是否包含子迭代 | 取值 0或1，默认0 |
| include_leaf_stories | 否 | string | 是否包含子需求 | 取值 0或1，默认0 |
| limit | 否 | integer | 返回数量限制，默认30 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

## 请求示例

```bash
# 获取项目下需求的数量
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/stories/count?workspace_id=$TAPD_WORKSPACE_ID'

# 获取项目下优先级为 High 的需求数量
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/stories/count?workspace_id=$TAPD_WORKSPACE_ID&priority=4'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "count": 7
    },
    "info": "success"
}
```
