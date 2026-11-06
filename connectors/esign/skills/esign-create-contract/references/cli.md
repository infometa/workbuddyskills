# 草稿、模板与发送命令

仅在用户要求发送的范围内执行；当前身份、文件接入和展示见[执行规则](execution.md)。参数必须来自用户输入、真实文件或实际返回；JSON使用序列化和参数数组或正确shell转义，不把姓名、文件名等拼成可执行代码。

## 创建与设置草稿

材料或模板已明确且实际身份可用后才创建；已有属于本任务、尚未发送且仍有效的草稿可复用，不为每次补信息创建新草稿。

```bash
esign sign draft start
esign sign draft set --draft-id '<实际draftId>' --files '<完整files数组>'
esign sign draft set --draft-id '<实际draftId>' --flow-template-id '<用户选择的真实模板ID>'
esign sign draft set --draft-id '<实际draftId>' --signers '<当前完整signers数组>'
esign sign draft set --draft-id '<实际draftId>' --process-name '<用户指定或已展示的流程名称>'
```

- `draftId` 来自真实创建结果；创建成功是草稿，不是已发起签署。
- `files` 每项包含真实 `file_key`、`file_name`；文件是否需上传按执行规则处理。按真实文件标识去重，不能从路径/名称猜标识。
- `signers` 使用本次选定的完整名单。企业字段：`type: enterprise`、`name`、`contactName`、`phone`或`email`。个人字段：`type: individual`、`name`、`phone`或`email`。未提供的可选字段省略，不传占位文字。修改时整体设置，不假设支持单元素局部更新。
- 审批流或发起部门按[确认规则](confirmation.md)判断实际必要性及有效选择。真实必选项尚未确定，或用户要求设置／更换时，取得本次实际可用列表供选择后，使用 `--approval-template-id`、`--initiator-dept-id` 实际设置；不能据名字猜ID。列表仅从实际草稿／模板返回或已验证可用命令取得，无候选来源时不发明查询子命令。有列表不代表可省略审批；文件发送不无依据强加这两项，但真实必选仍需补齐。当前命令帮助明确：设置审批模板必须同时设置真实 `--initiator-dept-id`；部门未知时随审批选择一起补齐，不能猜部门ID。
- 用户明确要求且当前命令支持时可设置 `--sign-order unordered` 或 `--sign-order sequential`；不让用户为默认设置多答一轮，不自造顺序含义或模板字段参数。

## 模板作为发送的一步

```bash
esign sign template select --flow-template-name '<用户提供的关键词>' --page-num 1 --page-size 50 --format json
```

关键词未提供就省略该参数。展示实际返回的可用模板并等待选择；有分页时不能把一页当全部。没有模板如实说明，不伪造默认模板。只有需要用户选择的真实模板列表，没有独立模板查询服务或独立查询后自动创建草稿行为。模板详情与默认配置仅使用实际返回或已有已验证能力，不发明额外子命令。

## 仅检查与真正发送

```bash
# 不发送，只检查草稿
esign sign draft submit --draft-id '<实际draftId>'
# 信息齐全、检查通过且用户授权覆盖当前配置后，真正发送
esign sign draft submit --draft-id '<实际draftId>' --yes
```

检查成功不能仅以存在卡片、URL或零退出码判断；须同时核对实际业务结果。返回不符合已知结构时先核对实际帮助/返回，不猜字段、不把日志当结果。

成功后使用实际返回的 `longResultUrl` 或明确的用户查看入口；未返回链接时只报告可确认结果，不拼接URL。不自动加命令帮助未支持的参数。当前能力明确不支持时友好说明，不用其他业务操作替代。
