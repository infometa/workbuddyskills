# CountBugs

## 接口描述
计算符合查询条件的缺陷数量并返回。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/bugs/count

**支持格式：** JSON/XML（默认 JSON）

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| title | 否 | string | 标题 | 支持模糊匹配 |
| priority | 否 | string | 优先级。推荐使用 priority_label | |
| priority_label | 否 | string | 优先级（推荐） | |
| severity | 否 | string | 严重程度 | 支持枚举查询 |
| status | 否 | string | 状态 | 支持不等于查询、枚举查询 |
| label | 否 | string | 标签查询 | 支持枚举查询 |
| iteration_id | 否 | integer | 迭代 | |
| module | 否 | string | 模块 | 支持枚举查询 |
| release_id | 否 | integer | 发布计划 | |
| version_report | 否 | string | 发现版本 | 枚举查询 |
| version_test | 否 | string | 验证版本 | |
| version_fix | 否 | string | 合入版本 | |
| version_close | 否 | string | 关闭版本 | |
| baseline_find | 否 | string | 发现基线 | |
| baseline_join | 否 | string | 合入基线 | |
| baseline_test | 否 | string | 验证基线 | |
| baseline_close | 否 | string | 关闭基线 | |
| current_owner | 否 | string | 处理人 | 支持模糊匹配 |
| cc | 否 | string | 抄送人 | |
| reporter | 否 | string | 创建人 | |
| participator | 否 | string | 参与人 | 支持多人员查询 |
| te | 否 | string | 测试人员 | 支持模糊匹配 |
| de | 否 | string | 开发人员 | 支持模糊匹配 |
| auditer | 否 | string | 审核人 | |
| confirmer | 否 | string | 验证人 | |
| fixer | 否 | string | 修复人 | |
| closer | 否 | string | 关闭人 | |
| lastmodify | 否 | string | 最后修改人 | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| in_progress_time | 否 | datetime | 接受处理时间 | 支持时间查询 |
| resolved | 否 | datetime | 解决时间 | 支持时间查询 |
| verify_time | 否 | datetime | 验证时间 | 支持时间查询 |
| closed | 否 | datetime | 关闭时间 | 支持时间查询 |
| reject_time | 否 | datetime | 拒绝时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | 支持时间查询 |
| begin | 否 | date | 预计开始 | |
| due | 否 | date | 预计结束 | |
| deadline | 否 | date | 解决期限 | |
| os | 否 | string | 操作系统 | |
| platform | 否 | string | 软件平台 | |
| testmode | 否 | string | 测试方式 | |
| testphase | 否 | string | 测试阶段 | |
| testtype | 否 | string | 测试类型 | |
| source | 否 | string | 缺陷根源 | 支持枚举查询 |
| bugtype | 否 | string | 缺陷类型 | |
| frequency | 否 | string | 重现规律 | 支持枚举查询 |
| originphase | 否 | string | 发现阶段 | |
| sourcephase | 否 | string | 引入阶段 | |
| resolution | 否 | string | 解决方法 | 支持枚举查询 |
| estimate | 否 | integer | 预计解决时间 | |
| description | 否 | string | 详细描述 | 支持模糊匹配 |
| effort | 否 | integer | 预估工时 | |
| custom_field_* | 否 | string/integer | 自定义字段参数 | 支持枚举查询 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 | |

## 请求示例

```bash
# 获取项目下的缺陷数量
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/bugs/count?workspace_id=$TAPD_WORKSPACE_ID'

# 获取指定处理人、高优先级、状态为新的缺陷数量
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/bugs/count?workspace_id=$TAPD_WORKSPACE_ID&current_owner=anyechen&priority=high&status=new'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "count": 2
    },
    "info": "success"
}
```
