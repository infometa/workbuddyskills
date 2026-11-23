# 支出流水接口

工具：`pageQueryExpenseFlow`，使用当前音为有数连接器发现的真实工具名称。

仅经本包生产环境 MCP 连接器调用实际发现的工具，使用平铺 JSON；身份由连接器认证取得，沿用收支管理功能和行数据权限，不自行发起 OpenAPI 请求。

## 查询

| 参数 | 含义 |
| --- | --- |
| pageNo / pageSize | 默认 1 / 10；每页最多 1,000 条 |
| depId | 可选部门，缺省读取当前选择部门 |
| paymentStartTime / paymentEndTime | 成对传 13 位毫秒时间戳，转为北京时间日期，包含起止整天 |
| paymentTimeRangePreset | 可选 RECENT_7_NATURAL_DAYS；不能与上述日期同时传 |
| firstFeeType / secondFeeType | 业务动态维护的大类/子类名称，精确匹配 |
| trackName / accountName | 歌曲名/收款户名，包含匹配 |
| paymentSubjectId / paymentSubjectName | 付款主体 ID/名称；名称包含匹配 |
| feeType / contractName | 费用类型编码/合同文件名 |
| minAmount / maxAmount | 元金额十进制字符串，包含边界，不带千位符或单位 |

排序为付款时间倒序，同付款时间按流水编号升序；分页不是数据快照。`feeType` 支持 PRODUCTION、PROMOTION、COPYRIGHT、SPARE、SPARE_WRITE_OFF、PROMOTION_MATERIAL、PROMOTION_TO_PUBLIC、REIMBURSEMENT，不能把中文大类名称直接作为费用类型编码。

响应数据为分页对象，保留其总数、页码和当前页 `content`；外层成功码按连接器真实契约判断，不把异常响应视作无结果。

## 每条流水

原有：firstFeeType、secondFeeType、trackName、lyricists、composers、performers、recordings、amount（元字符串）、accountName、paymentSubjectName、feeType、contractName、paymentTime（毫秒）。

新增：

| 字段 | 含义 |
| --- | --- |
| key | 稳定流水编号，跨页去重付款明细 |
| feeNo | 申请单号，同单可能有多笔费用 |
| feeDetailNo / feeContractNo | 费用明细/费用合同编号，无值为 "" |
| payOrderNo | 支付单编号，无支付单时为 "" |
| invoiceBizNo | 发票归属的费用合同或明细编号，无值为 "" |
| accountUserType | ENTERPRISE 企业、NATURAL 自然人，未知为 "" |
| invoiceArrivalOrder | INVOICE_FIRST / INVOICE_LATER，未记录为 "" |
| invoiceArrivalOrderDesc | 发票先到/发票后到，未记录为 "" |
| invoices / paymentReceipts | 发票/付款凭证数组，无文件为 [] |

文件项：`key`（文件记录唯一标识）、`fileName`、`fileType`（文件格式）、`downloadUrl`。私有文件生成链接时申请 15 分钟有效期；历史 URL 保持其原有效期，不承诺重新签发。下载失败或签发失败应据实处理，不据此填写零金额。

票种、含税金额、税额、不含税金额由读取真实发票得出，不在接口中预计算。只凭费用分类不能判定票种。
