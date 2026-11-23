# 加入项目申请

```sh
heyincli project application list --result PENDING
heyincli project application list --result PENDING --json
heyincli project application create --code DEMO --scope PROJECT
heyincli project application create --code DEMO --scope SITE --role-tpl-id 401 --site-name '示例中心' --comment '申请加入'
heyincli project application revoke 123
```

- `list` 默认获取全部申请，可用 `--result`（`PENDING/APPROVE/REJECT/REVOKED`）筛选结果。
- `create` 必填 `--code`（最多 16 个字符）和 `--scope`（`PROJECT` 或 `SITE`）。可选 `--role-tpl-id`（0 表示不指定）、`--site-name`（最多 64 个字符）、`--comment`（最多 255 个字符）；指定中心级角色模板时必须填写中心名称。角色模板 ID 应使用已知的有效值，不从项目角色 ID 推断。
- `revoke <application-id>` 使用申请记录 ID，撤销待处理申请；已批准、已拒绝或已撤销的申请不能再次撤销。默认输入 `yes` 确认；用户已明确授权撤销时，可加 `--yes` 跳过提示。

申请列表默认以 Markdown 表格显示申请 ID、项目编码、项目名称、项目简称、申请范围、角色模板、状态、申请时间及备注，并在末尾显示总数；无记录时显示“暂无申请”。申请时间按 `YYYY-MM-DD HH:mm:ss` 显示，沿用记录自身时区。加 `--json` 时改为输出合并后的 `list` 和 `total`，保留各项原始字段及嵌套结构。

创建和撤销成功默认输出中文提示；脚本加 `--json`，分别读取申请对象或 `{"application_id":123,"revoked":true}`。

创建或撤销遇到超时、断连、响应异常或输出失败时，先查询申请列表核实是否已创建或变为 `REVOKED`，不要自动重试写入；不能仅凭非零退出码判断远端未生效。无法核实时停止并说明结果尚未确认。
