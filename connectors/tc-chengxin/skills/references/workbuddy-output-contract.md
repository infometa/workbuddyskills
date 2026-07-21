# WorkBuddy 输出契约

脚本在 `CHENGXIN_OUTPUT_GUARD=display_contract` 下输出 `WORKBUDDY_VISUAL_JSON_START/END` 包裹的 JSON。

必须展示：

- 直接逐字输出 `markdown` 字段；不要只输出 `summaryMarkdown`，也不要自行写“已完成”摘要替代 Markdown。
- 如果 JSON 含 `responsePolicy.finalAnswerField=markdown`，必须按该字段输出最终回复。
- 如果 JSON 含 `finalAnswerInstruction`，按该字段执行；它优先于模型自己的总结习惯。
- 如果 JSON 含 `responsePolicy.mustDisplayInChat=true`，最终对话正文必须显示 `markdown` 字段，不能只展示 HTML 文件卡片。
- 如果 JSON 含 `responsePolicy.presentFilesIsSupplementOnly=true`，`present_files` 只是补充展示，不是最终回答正文。
- 如果 JSON 含 `responsePolicy.finalAnswerMustStartWith`，最终回复正文必须以该字符串开头。
- 如果 JSON 含 `responsePolicy.requiredFinalAnswerSections`，最终回复必须包含这些章节/关键词。
- 如果 JSON 含 `responsePolicy.requiredTransportMarkdownHeaders`，交通/机票/火车/汽车表格必须按对应业务保留表头顺序。
- 保留 `markdown` 顶部的「推荐建议」段落；这是脚本根据接口结果生成的建议性回答。
- 保留 `markdown` 末尾的「客服支持」段落。
- 保留交通/机票/火车/汽车表格里的 `预订` 列；该列是强制列，并且必须是最后一列。
- `htmlFilePath` 非空时，调用 `present_files` 打开该 HTML 文件。

交通表格表头：

- 机票：`序号 | 航班 | 出发到达 | 日期 | 时间 | 时长 | 价格 | 预订`
- 火车：`序号 | 车次 | 出发到达 | 日期 | 时间 | 历时 | 票价/席别 | 预订`
- 汽车：`序号 | 班次 | 出发到达 | 日期 | 时间 | 车程 | 票价 | 预订`

禁止展示：

- 原始 JSON。
- 只有一句完成摘要、但缺少脚本 `markdown` 中的分组表格、预订入口和客服支持。
- 只有 HTML 文件卡片、或只说“点击右侧 HTML 页面查看完整列表”。
- “已为你查到……点击右侧 HTML 页面……”这类摘要替代脚本 `markdown`。
- 模型自行重排的表格、亮点总结、二次推荐；建议性回答使用脚本 `markdown` / `adviceMarkdown` 中已生成的内容。
- 因列宽、移动端显示或美观原因删除 `预订` 列。
- 把交通表格表头改成不含 `预订`，或把 `预订` 移出最后一列。
- 被改写或删除过的预订链接、手机链接、二维码链接。
- 被删除的推荐建议。
- 被删除的同程旅行客服支持信息。

客服支持固定文案：

```markdown
#### 客服支持

使用过程中遇到问题?同程旅行提供 7×24 小时服务:

📞 旅行者热线:95711
💬 [在线客服](https://www.ly.com/public/newhelp/CustomerService.html)
```

HTML 文件要求：

- 文件名使用中文主题名。
- 由脚本写入本地绝对路径。
- 优先输出到当前工作区的 `outputs` 目录。
- PC 链接使用普通 `<a target="_blank" rel="noopener">`。
- 二维码支持 hover 查看和点击放大。

产物路径处理：

- 执行脚本前推荐设置 `CHENGXIN_WORKBUDDY_OUTPUT_DIR` 为当前工作区的 `outputs` 目录。
- macOS/Linux shell 可使用 `CHENGXIN_WORKBUDDY_OUTPUT_DIR="$PWD/outputs"`。
- Windows PowerShell 必须使用 `Join-Path (Get-Location).Path "outputs"` 得到 `D:\...\outputs` 这类原生盘符路径。
- Windows 下不要把路径改写成 `/d/...`、`\d\...`、`/mnt/d/...` 或字面量 `$PWD/outputs`。
- 如果脚本返回的 `htmlFilePath` 不在当前工作区内，复制到当前工作区 `outputs/` 后再调用 `present_files`。
