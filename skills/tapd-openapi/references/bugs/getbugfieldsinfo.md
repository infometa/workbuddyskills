# GetBugFieldsInfo

## 接口描述
返回缺陷所有字段及候选值（枚举值），即通常理解的字段的"英文Key"和"中文值"。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/bugs/get_fields_info

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回所有数据。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| all_options | 否 | integer | 是否也返回已关闭的选项。1 返回，默认 0 不返回，与 TAPD 界面对齐 |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/bugs/get_fields_info?workspace_id=$TAPD_WORKSPACE_ID'
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
                "new": "新",
                "in_progress": "接受/处理",
                "resolved": "已解决",
                "closed": "已关闭"
            },
            "pure_options": [],
            "html_type": "select",
            "memo": ""
        },
        "priority": {
            "name": "priority",
            "label": "优先级",
            "options": {
                "urgent": "紧急",
                "high": "高",
                "medium": "中",
                "low": "低",
                "insignificant": "无关紧要"
            },
            "pure_options": [],
            "html_type": "select",
            "memo": ""
        },
        "severity": {
            "name": "severity",
            "label": "严重程度",
            "options": {
                "fatal": "致命",
                "serious": "严重",
                "normal": "一般",
                "prompt": "提示",
                "advice": "建议"
            },
            "pure_options": [],
            "html_type": "select",
            "memo": ""
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
| html_type | 字段类型（select、input、text、datetime、user_chooser 等） |

### 包含候选值的字段

| 字段 | 说明 |
|------|------|
| status | 状态枚举值（每个项目可单独配置，无固定映射，只能通过此接口获取） |
| priority | 优先级枚举值 |
| severity | 严重程度枚举值 |
| resolution | 解决方法枚举值 |
| iteration_id | 迭代枚举值 |
| module | 模块枚举值 |
| release_id | 发布计划枚举值 |
| version_report | 发现版本枚举值 |
| version_test | 验证版本枚举值 |
| version_fix | 合入版本枚举值 |
| version_close | 关闭版本枚举值 |
| platform | 软件平台枚举值 |
| os | 操作系统枚举值 |
| testmode | 测试方式枚举值 |
| testtype | 测试类型枚举值 |
| testphase | 测试阶段枚举值 |
| source | 缺陷根源枚举值 |
| bugtype | 缺陷类型枚举值 |
| frequency | 重现规律枚举值 |
| originphase | 发现阶段枚举值 |
| sourcephase | 引入阶段枚举值 |
| custom_field_* | 自定义字段枚举值 |

### 缺陷严重程度 (severity) 可选值

| 取值 | 字面值 |
|------|--------|
| fatal | 致命 |
| serious | 严重 |
| normal | 一般 |
| prompt | 提示 |
| advice | 建议 |

### 缺陷解决方法 (resolution) 可选值

| 取值 | 字面值 |
|------|--------|
| ignore | 无需解决 |
| fixed | 已修改 |
| fix later | 延期解决 |
| failed to recur | 无法重现 |
| external reason | 外部原因 |
| duplicated | 重复 |
| intentional design | 设计如此 |
| unclear description | 问题描述不准确 |
| feature change | 需求变更 |
| transferred to story | 已转需求 |
| hold | 挂起 |

### 特殊说明

- **状态 (status)**：支持每个项目单独配置，没有固定的中英文映射，只能通过此接口获取。
- **优先级 (priority)**：为了兼容自定义优先级，请使用 `priority_label` 字段。
