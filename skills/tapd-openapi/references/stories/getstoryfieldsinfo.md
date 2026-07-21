# GetStoryFieldsInfo

## 接口描述
获取需求所有字段及候选值。返回符合查询条件的所有需求字段及候选值。部分字段为静态候选值，建议参考下方"可选值说明"部分。其余动态字段（如 status、iteration_id、categories），需要通过该接口获取对应的候选值（中英文映射）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/stories/get_fields_info

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回所有数据。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/stories/get_fields_info?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "status": {
            "name": "status",
            "label": "状态",
            "options": {
                "planning": "规划中",
                "developing": "实现中",
                "resolved": "已实现",
                "rejected": "已拒绝"
            },
            "html_type": "select",
            "pure_options": [],
            "readonly": 0
        },
        "priority": {
            "name": "priority",
            "label": "优先级",
            "options": {
                "紧急": "紧急",
                "高": "高",
                "中": "中",
                "低": "低",
                "锦上添花": "锦上添花"
            },
            "html_type": "select",
            "pure_options": [],
            "readonly": 0
        },
        "iteration_id": {
            "name": "iteration_id",
            "label": "迭代",
            "options": {
                "1010104801001662155": "fromAPI"
            },
            "html_type": "select",
            "pure_options": [],
            "readonly": 0
        },
        "category_id": {
            "name": "category_id",
            "label": "分类",
            "options": {
                "1010104801000037409": "abc",
                "-1": "未分类"
            },
            "html_type": "select",
            "pure_options": [],
            "readonly": 0
        }
    },
    "info": "success"
}
```

### 返回格式说明

| 字段 | 说明 |
|------|------|
| name | 字段英文名 |
| label | 字段中文名称 |
| options | 候选值（英文Key → 中文值） |
| html_type | 字段类型（select、input、text、datetime、user_chooser、dateinput、float 等） |
| readonly | 是否只读（0 可编辑，1 只读） |

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | ID |
| name | 标题 |
| priority | 优先级 |
| business_value | 业务价值 |
| status | 状态 |
| version | 版本 |
| modified | 最后修改时间 |
| completed | 完成时间 |
| iteration_id | 迭代ID |
| templated_id | 模板ID |
| effort | 预估工时 |
| effort_completed | 完成工时 |
| remain | 剩余工时 |
| exceed | 超出工时 |
| category_id | 需求分类（取 -1 时为未分类） |
| release_id | 发布计划 |
| is_archived | 是否归档 |
| source | 来源 |
| type | 类型 |
| parent_id | 父需求 |
| children_id | 子需求 |
| description | 详细描述 |
| workspace_id | 项目ID |
| workitem_type_id | 需求类别 |
| confidential | 是否保密 |
| created_from | 需求创建来源（为空时代表 web 创建） |
| level | 层级 |
| bug_id | 缺陷ID（缺陷转需求时才有值） |
| owner | 处理人 |
| creator | 创建人 |
| created | 创建时间 |
| begin | 预计开始 |
| due | 预计结束 |
| cc | 抄送人 |
| developer | 开发人员 |
| module | 模块 |
| label | 标签 |
| size | 规模 |
| progress | 进度 |
| feature | 特性 |
| test_focus | 测试重点 |
| tech_risk | 技术风险 |
| has_attachment | 附件 |
| custom_field_* | 自定义字段 |
| custom_plan_field_* | 自定义计划字段 |

### 包含候选值的动态字段

| 字段 | 说明 |
|------|------|
| status | 状态枚举值（每个项目可单独配置，无固定映射，只能通过此接口获取） |
| iteration_id | 迭代枚举值 |
| category_id | 需求分类枚举值 |
| workitem_type_id | 需求类别枚举值 |
| release_id | 发布计划枚举值 |
| module | 模块枚举值 |
| version | 版本枚举值 |
| custom_field_* | 自定义字段枚举值 |
| custom_plan_field_* | 自定义计划字段枚举值 |

### 包含候选值的静态字段

| 字段 | 说明 |
|------|------|
| priority | 优先级枚举值 |
| source | 需求来源枚举值 |
| type | 需求类型枚举值 |

### 特殊说明

- **状态 (status)**：支持每个项目单独配置，没有固定的中英文映射，只能通过此接口获取。
- **优先级 (priority)**：为了兼容自定义优先级，请使用 `priority_label` 字段。
- **需求分类 (category_id)**：取值 `-1` 时表示"未分类"。
