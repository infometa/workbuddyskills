# UpdateBug

## 接口描述
更新缺陷，返回缺陷更新后的数据。每次只允许更新一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/bugs

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只允许更新一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| id | 是 | integer | 缺陷ID |
| workspace_id | 是 | integer | 项目ID |
| title | 否 | string | 标题 |
| priority_label | 否 | string | 优先级（推荐），如 urgent / high / medium / low |
| priority | 否 | string | 优先级（已废弃，请用 priority_label） |
| severity | 否 | string | 严重程度：fatal / serious / normal / prompt / advice |
| status | 否 | string | 状态 |
| v_status | 否 | string | 状态（支持传入中文状态名称） |
| module | 否 | string | 模块 |
| feature | 否 | string | 特性 |
| release_id | 否 | integer | 发布计划 |
| version_report | 否 | string | 发现版本 |
| version_test | 否 | string | 验证版本 |
| version_fix | 否 | string | 合入版本 |
| version_close | 否 | string | 关闭版本 |
| baseline_find | 否 | string | 发现基线 |
| baseline_join | 否 | string | 合入基线 |
| baseline_test | 否 | string | 验证基线 |
| baseline_close | 否 | string | 关闭基线 |
| current_owner | 否 | string | 处理人 |
| current_user | 否 | string | 变更人 |
| cc | 否 | string | 抄送人 |
| reporter | 否 | string | 创建人 |
| participator | 否 | string | 参与人 |
| te | 否 | string | 测试人员 |
| de | 否 | string | 开发人员 |
| auditer | 否 | string | 审核人 |
| confirmer | 否 | string | 验证人 |
| fixer | 否 | string | 修复人 |
| closer | 否 | string | 关闭人 |
| begin | 否 | date | 预计开始（格式：YYYY-MM-DD） |
| due | 否 | date | 预计结束（格式：YYYY-MM-DD） |
| deadline | 否 | date | 解决期限（格式：YYYY-MM-DD） |
| os | 否 | string | 操作系统 |
| size | 否 | string | 规模 |
| platform | 否 | string | 软件平台 |
| testmode | 否 | string | 测试方式 |
| testphase | 否 | string | 测试阶段 |
| testtype | 否 | string | 测试类型 |
| source | 否 | string | 缺陷根源 |
| bugtype | 否 | string | 缺陷类型 |
| frequency | 否 | string | 重现规律 |
| originphase | 否 | string | 发现阶段 |
| sourcephase | 否 | string | 引入阶段 |
| resolution | 否 | string | 解决方法（见候选值） |
| estimate | 否 | integer | 预计解决时间 |
| description | 否 | string | 详细描述（支持 HTML） |
| label | 否 | string | 标签，多个用英文竖线分隔，不存在时自动创建 |
| effort | 否 | integer | 预估工时 |
| keep_owner | 否 | integer | 是否保留处理人，传 1 则保留 |
| custom_field_* | 否 | string/integer | 自定义字段，具体字段名通过「获取缺陷自定义字段配置」接口获取 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 |
| cus_{自定义字段别名} | 否 | string | 自定义字段（后台自动转义为 custom_field_*） |

## 请求示例

```bash
# 更新缺陷处理人
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/bugs" \
  -d '{
    "id": "缺陷ID",
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "current_owner": "username"
  }'

# 更新缺陷状态和解决方法
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/bugs" \
  -d '{
    "id": "缺陷ID",
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "status": "resolved",
    "resolution": "fixed",
    "current_user": "username"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Bug": {
            "id": "1010158231500628817",
            "title": "【示例】新官网Chrome浏览器兼容性bug",
            "workspace_id": "10158231",
            "status": "in_progress",
            "priority": "high",
            "severity": "prompt",
            "current_owner": "anyechen;",
            "modified": "2019-06-27 14:29:03",
            "lastmodify": "anyechen"
        }
    },
    "info": "success"
}
```

## 注意事项

- `id` 和 `workspace_id` 为必传字段，其余字段按需传入，未传字段不会被修改
- `priority` 字段已废弃，请统一使用 `priority_label`
- `status` 与 `v_status` 二选一，`v_status` 支持中文状态名
- `keep_owner=1` 可在状态流转时保留当前处理人不被重置
- `status` / `module` 等动态字段的可选值需通过「获取缺陷所有字段及候选值」接口获取
