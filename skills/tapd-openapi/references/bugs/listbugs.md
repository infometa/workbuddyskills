# ListBugs

## 接口描述
返回符合查询条件的所有缺陷（分页显示，默认一页30条）。

> **状态查询注意事项** : 按状态查询时，建议使用 `v_status` 参数直接传中文状态名（如 `v_status=新`）。因为缺陷状态的英文 Key 是每个项目单独配置的，使用中文名更直观、不易出错。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/bugs

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

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
| v_status | 否 | string | 状态（支持传入中文状态名称） | |
| label | 否 | string | 标签查询 | 支持枚举查询 |
| iteration_id | 否 | string | 迭代 | 支持枚举查询 |
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
| feature | 否 | string | 特性 | |
| current_owner | 否 | string | 处理人 | 支持模糊匹配 |
| cc | 否 | string | 抄送人 | |
| reporter | 否 | string | 创建人 | 支持多人员查询 |
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
| size | 否 | string | 规模 | |
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
| custom_field_* | 否 | string/integer | 自定义字段参数 | 支持枚举查询 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 | |
| limit | 否 | integer | 返回数量限制，默认30，最大200 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/bugs?workspace_id=$TAPD_WORKSPACE_ID&limit=2'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Bug": {
                "id": "1010158231500628817",
                "title": "【示例】新官网Chrome浏览器兼容性bug",
                "description": null,
                "priority": "high",
                "severity": "prompt",
                "module": null,
                "status": "in_progress",
                "reporter": "anyechen",
                "deadline": null,
                "created": "2017-06-20 16:49:19",
                "bugtype": "",
                "resolved": null,
                "closed": null,
                "modified": "2018-01-12 14:45:27",
                "lastmodify": "anyechen",
                "auditer": null,
                "de": null,
                "fixer": null,
                "version_test": "",
                "version_report": "版本1",
                "version_close": "",
                "version_fix": "",
                "baseline_find": "",
                "baseline_join": "",
                "baseline_close": "",
                "baseline_test": "",
                "sourcephase": "",
                "te": null,
                "current_owner": null,
                "iteration_id": "0",
                "resolution": "",
                "source": "",
                "originphase": "",
                "confirmer": null,
                "milestone": null,
                "participator": null,
                "closer": null,
                "platform": "",
                "os": "",
                "testtype": "",
                "testphase": "",
                "frequency": "",
                "cc": null,
                "regression_number": "0",
                "flows": "new",
                "feature": null,
                "testmode": "",
                "estimate": null,
                "issue_id": null,
                "created_from": null,
                "in_progress_time": null,
                "verify_time": null,
                "reject_time": null,
                "reopen_time": null,
                "audit_time": null,
                "suspend_time": null,
                "due": null,
                "begin": null,
                "release_id": null,
                "label": "阻塞|重点关注",
                "custom_field_one": "",
                "custom_field_two": "",
                "custom_field_three": "",
                "custom_field_four": "",
                "custom_field_five": "",
                "workspace_id": "10158231"
            }
        }
    ],
    "info": "success"
}
```
