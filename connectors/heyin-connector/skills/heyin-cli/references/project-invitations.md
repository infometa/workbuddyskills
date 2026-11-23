# 项目邀请

```sh
heyincli project invitation list --result PENDING
heyincli project invitation list --json
heyincli project invitation accept 456 --comment '接受邀请'
heyincli project invitation reject 456 --comment '暂不加入'
```

`list` 默认获取全部可见邀请，可用 `--result`（`PENDING`/`ACCEPT`/`REJECT`）筛选结果。项目方已撤销的邀请不会出现在列表中，筛选 `REVOKED` 恒为空。

邀请列表默认以 Markdown 表格显示邀请 ID、项目编码、项目名称、项目简称、角色、状态、邀请时间及备注，并在末尾显示总数；无记录时显示“暂无邀请”。角色列区分项目角色和中心角色，中心级角色附带中心名称；邀请时间按 `YYYY-MM-DD HH:mm:ss` 显示，沿用记录自身时区。加 `--json` 时改为输出合并后的 `list` 和 `total`，保留各项原始字段，`roles` 保持数组结构。

接受或拒绝邀请必须使用邀请记录 ID，可选 `--comment`（最多 255 个字符）。这两个命令执行即提交，运行前确认用户的选择。

接受和拒绝以位置参数 `<invitation-id>` 指定目标，成功默认输出中文提示；加 `--json` 输出 `{"invitation_id":456,"result":"ACCEPT"}` 或相应 REJECT 结果。

回复遇到超时、断连、响应异常或输出失败时，先查询邀请列表核实该邀请的结果，不要自动重试接受或拒绝；不能仅凭非零退出码判断回复未生效。无法核实时停止并说明结果尚未确认。
