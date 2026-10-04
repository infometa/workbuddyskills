# 报销自动填单

## 什么时候读取

用户提到报销、发票报销、自动填单、提交报销单、事前申请报销，或需要把已选发票生成 E10 报销流程时读取本文件。纯查发票仍优先读个人/企业票夹 reference。

## Operation

| 意图 | Operation | 风险 |
| --- | --- | --- |
| E10 fileId 转发票识别结果 | `invoice.reim.file-ocr.preview` | read-with-upload |
| 查询事前申请 | `invoice.reim.requests.list` | read |
| 获取报销工作流 ID | `invoice.reim.workflow.resolve` | read |
| 获取报销表单结构 | `invoice.reim.form.structure` | read |
| 获取单张发票明细行预填信息 | `invoice.reim.row-info` | read |
| 获取当前人员及上级 | `invoice.reim.employee-superiors` | read |
| 搜索表单关联字段值 | `invoice.reim.field.search` | read |
| 准备/确认创建报销单 | `invoice.reim.flow.create.prepare/apply` | read-before-write / high-risk-write |
| 准备/确认更新报销单 | `invoice.reim.flow.update.prepare/apply` | read-before-write / high-risk-write |

## 处理链

1. 获取发票：已有 `fid` 时可用 `invoice.get` 或 `invoice.browse-field.data`；已有 E10 `fileId` 时用 `invoice.reim.file-ocr.preview`；需要查票夹时用 `invoice.list`，默认未报销发票。
2. 展示发票汇总，让用户确认哪些发票进入报销。
3. 用 `invoice.reim.requests.list` 获取事前申请，再按时间、费用类型和标题做匹配；原始 ID、日期、金额必须逐字符保留。
4. 用 `invoice.reim.workflow.resolve` 得到报销工作流，必要时按工作流分组。
5. 对每组并行读取 `invoice.reim.form.structure`、`invoice.reim.row-info` 和 `invoice.reim.employee-superiors`；只有需要用户修正关联字段时才用 `invoice.reim.field.search`。
6. Agent 按表单结构组装报销单 JSON，先调用 `invoice.reim.flow.create.prepare`，展示标题、主表字段数、明细行数、发票和风险；用户明确确认后再调用 `.apply`。
7. 报销单创建成功后，后续修正使用 `invoice.reim.flow.update.prepare/apply`，不要重复创建同一组发票的报销单。

## 命令

查询事前申请：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20,"requestname":"交通","cusCreateDateStart":"2026-07-01","cusCreateDateEnd":"2026-07-31"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20,"requestname":"交通","cusCreateDateStart":"2026-07-01","cusCreateDateEnd":"2026-07-31"}'
```

创建报销单建议用 UTF-8 JSON 文件传入完整报销单 JSON。

Windows PowerShell：

```powershell
Set-Content -Encoding utf8 -LiteralPath .\reim-create.json -Value @'
{
  "work_flow_id": "1181057526276915214",
  "mainFormId": "1181057741029226975",
  "request_name": "交通费报销-示例-2026-08-04",
  "main_fields": [],
  "detail_rows": [{"dataIndex":1,"subFormId":"1181057741029227992","invoiceId":"12345","fields":[]}]
}
'@
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.prepare --input .\reim-create.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./reim-create.json <<'JSON'
{
  "work_flow_id": "1181057526276915214",
  "mainFormId": "1181057741029226975",
  "request_name": "交通费报销-示例-2026-08-04",
  "main_fields": [],
  "detail_rows": [{"dataIndex":1,"subFormId":"1181057741029227992","invoiceId":"12345","fields":[]}]
}
JSON
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.prepare --input ./reim-create.json
```

确认后把 prepare 返回的 continuation 原样放入 apply 输入，并在同一个顶层 JSON 中加入 `"confirm": true`。`invoice.reim.flow.create.*` 的 `inputSchema` 会逐字段暴露 `work_flow_id`、`mainFormId`、`request_name`、`main_fields`、`detail_rows`、`need_user_confirm` 和 `unable_to_fill`，不要再包一层通用 `payload`。

## 输出处理

`invoice.reim.flow.create.apply` 成功返回 `requestId`、`requestName` 和 `viewUrl`。给用户展示报销单标题、总金额、发票摘要和链接。若返回 `partial/write_uncertain`，停止，不要重放 `.apply`；最多做一次只读查询或请用户在 E10 页面核对。

`invoice.reim.flow.update.apply` 若服务端返回删除或更新部分失败，CLI 会按 `partial/write_uncertain` 报告，Agent 不要继续连环重试。

## 注意

报销单创建和更新都是高风险写入，必须走 `prepare -> 用户确认 -> apply`。同一组发票 `invoice.reim.flow.create.apply` 成功后禁止再次创建；要修改已创建的报销单只能走 `invoice.reim.flow.update.prepare/apply`。

出差/差旅流程需要具体相关客户。未拿到用户提供的客户并完成关联字段搜索前，不要调用 `invoice.reim.flow.create.prepare/apply`。

`invoice.reim.file-ocr.preview` 会让 E10 侧文件进入发票识别流程；如果 fileId 来自用户新上传或附件解析，先提醒用户文件内容可能进入大模型上下文，也可能发送到 E10/OCR 服务，并等待明确确认。
