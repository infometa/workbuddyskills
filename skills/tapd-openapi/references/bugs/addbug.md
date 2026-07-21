# AddBug

## 接口描述
在项目下创建一条缺陷（Bug），一次只能插入一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/bugs

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 一次插入一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| title | 是 | string | 缺陷标题 |
| priority_label | 否 | string | 优先级（推荐），如 urgent / high / medium / low |
| priority | 否 | string | 优先级（已废弃，请用 priority_label） |
| severity | 否 | string | 严重程度：fatal / serious / normal / prompt / advice |
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
| template_id | 否 | integer | 模板ID |
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
| iteration_id | 否 | string | 迭代ID |
| size | 否 | string | 规模 |
| os | 否 | string | 操作系统 |
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
| is_apply_template_default_value | 否 | integer | 传 1 则从模板继承默认值 |
| custom_field_* | 否 | string/integer | 自定义字段，具体字段名通过「获取缺陷自定义字段配置」接口获取 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 |
| cus_{自定义字段别名} | 否 | string | 自定义字段（后台自动转义为 custom_field_*） |

### 常用字段候选值

**severity（严重程度）**

| 取值 | 说明 |
|------|------|
| fatal | 致命 |
| serious | 严重 |
| normal | 一般 |
| prompt | 提示 |
| advice | 建议 |

**resolution（解决方法）**

| 取值 | 说明 |
|------|------|
| fixed | 已解决 |
| ignore | 无需解决 |
| duplicated | 重复 |
| failed | 无法重现 |
| intentional | 设计如此 |
| external | 外部原因 |
| feature | 需求变更 |
| hold | 挂起 |

## 请求示例

```bash
# 创建最简缺陷
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/bugs" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "title": "缺陷标题"
  }'

# 创建带完整信息的缺陷
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/bugs" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "title": "登录页面崩溃",
    "priority_label": "high",
    "severity": "serious",
    "current_owner": "username",
    "description": "<div>复现步骤：...</div>",
    "deadline": "2026-03-20",
    "iteration_id": "迭代ID"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Bug": {
            "id": "1010158231500643487",
            "title": "缺陷标题",
            "workspace_id": "10158231",
            "status": "new",
            "reporter": "api_doc_oauth",
            "severity": "",
            "priority": "",
            "current_owner": null,
            "iteration_id": "0",
            "created": "2019-06-27 14:19:47",
            "modified": "2019-06-27 14:19:47",
            "created_from": "api"
        }
    },
    "info": "success"
}
```

## 注意事项

- `priority` 字段已废弃，请统一使用 `priority_label`
- `status` / `module` / `iteration_id` 等动态字段的可选值需通过「获取缺陷所有字段及候选值」接口获取
- `label` 中不存在的标签会自动创建，多个标签用英文竖线 `|` 分隔
- `description` 支持 HTML 富文本格式
