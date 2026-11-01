# 销售报告场景

用于销售经理/管理层按时间范围自动生成销售报告，涵盖新增线索、电话过程量、商机进展、成交订单、回款情况，并标注需要关注的异常事项。

典型问题示例：
- "生成运营部 8 月份的销售日报"
- "看下团队上周的销售报告，标出未跟进的新线索"
- "帮我出一份本月各员工的商机、订单和回款汇总"

## 场景工具

参数结构以工具 schema 为准，本文档不写死字段。

| 工具 | 用途 |
|---|---|
| whoami | 查询当前登录用户的简要信息（pid/did/姓名），用于确认当前登录身份 |
| findPersons / getAllPerson | 按姓名批量查找成员 / 获取部门（含子部门）或全公司成员，解析员工范围与 pid→姓名 |
| getAllGroup | 获取全部部门列表（含部门名称/父部门/成员），用于按部门名称查找 gid |
| getCallStat | 按时间范围获取权限范围内员工的电话过程量统计（拨打次数/接通数/时长等，按人聚合，按拨打次数降序） |
| getAssignedCustomerList | 按分配时间范围获取公海分配的客户列表，含客户名称/标签/跟进阶段/成交状态/分配时间/归属人等 |
| getCreateCustomerList | 按创建时间范围获取员工创建的客户列表（不含公海分配），支持按创建人/部门过滤，返回客户名称/标签/跟进阶段/成交状态/创建人/创建时间等，按创建时间倒序 |
| getCustomerFollowRecords | 按客户 ID 获取该客户的跟进记录（沟通/外勤合并，按时间倒序），含跟进内容/图片/语音/表单/通话信息等，用于逐客户判定是否有效客户与是否未跟进 |
| getSalesChanceList | 按创建时间范围获取商机列表，支持按跟进人/部门过滤，返回商机名称/阶段/金额/客户/跟进人等，按创建时间倒序 |
| getOrderList | 按创建时间范围获取订单列表，支持按归属人/部门过滤，返回订单编号/状态/金额/已回款/已退款/客户/归属人等 |
| getReceivePaymentList | 按创建时间范围获取回款与退款列表，支持按归属人/部门过滤，回款含金额/方式/状态，退款含金额/原因/状态（回款与退款分两次拉取后合并返回） |
| getWorkReportTemplate | 按汇报类型(daily/weekly/monthly)查询当前账号的工作汇报自定义表单模板，返回字段ID/名称/类型/是否必填/可选项/长度限制；未配置模板时 template 为空 |
| createWorkReport | 创建一份工作汇报（日报/周报/月报），创建人自动为当前账号；wrDate 自动对齐（日报→当天 0 点/周报→周一 0 点/月报→1 号 0 点），支持 content 正文或 forms 自定义表单提交（至少一项），返回 workReportId |
| getWorkReportList | 按时间范围获取工作汇报列表，支持按汇报类型(日报/周报/月报)、部门/成员过滤，返回汇报ID/创建人/正文/归属日期/自定义字段/图片附件(含下载链接)/其他附件；无管理权限时自动降级为仅查自己的汇报 |
| modifyWorkReport | 修改自己创建的工作汇报（正文或自定义表单，均为整篇替换），写入前回查校验，归属日期/类型不变，返回新 version |

## 工作流

### 1. 确认身份与员工范围

先调用 whoami 确认当前授权账号：

- 用 getAllGroup 获取部门列表，建立 gid→部门名称 映射；用户指定部门名称时查找对应 gid。
- 用 getAllPerson 获取全员列表，建立 pid→姓名 映射（后续所有工具返回的 pid 都需要映射）。
- 用户指定了员工姓名时，用 findPersons 解析为 pid；用户指定部门/团队时，从 getAllPerson 结果中提取 gid。
- 用户未指定员工范围时，不传 pids/gids，查权限范围内全部员工。

### 2. 确认报告口径

向用户确认（用户未明说时按默认口径，不必反复追问）：

| 口径项 | 取值 | 说明 |
|---|---|---|
| 时间范围 | 必须明确 | 如"8 月""上周"，换算为 GMT 毫秒时间戳（左闭右开），**开始与结束不能超过一年** |
| 员工范围 | 默认权限范围内全部 | 姓名→pids，部门→gids |
| 报告类型 | 默认日报 | 日报=单日，周报=7 天，月报=整月；影响"今日必须处理"等时间相关标注的计算 |

### 3. 拉取数据

#### 3a. 并行拉取基础数据源

六个数据源可并行拉取（入参均使用步骤 2 确认的时间范围和员工范围）：

- **getCallStat**：入参 statStime/statEtime（GMT 毫秒时间戳）、pids/gids（可选）。返回每人聚合的拨打次数/接通数/时长等。
- **getAssignedCustomerList**：入参 obtainTimeStart/obtainTimeEnd（分配时间范围，GMT 毫秒时间戳）、followerPids/followerGids（可选，归属人/部门）。返回区间内公海分配的客户列表，含标签/跟进阶段/成交状态。
- **getCreateCustomerList**：入参 createTimeStart/createTimeEnd（创建时间范围，GMT 毫秒时间戳）、createPids/createGids（可选，创建人/部门）。返回区间内员工创建的客户列表，含标签/跟进阶段/成交状态/创建人。
- **getSalesChanceList**：入参 stime/etime（GMT 毫秒时间戳）、pids/gids（可选）。返回每条商机的阶段/金额/跟进人/客户等。
- **getOrderList**：入参 stime/etime（GMT 毫秒时间戳）、pids/gids（可选）。返回每条订单的状态/金额/已回款/客户/归属人等。
- **getReceivePaymentList**：入参 stime/etime（GMT 毫秒时间戳）、pids/gids（可选）。返回回款列表 + 退款列表。

所有工具内部自动分批拉取全部数据，无需传分页参数。

#### 3b. 逐客户查跟进记录（依赖 3a 的客户列表结果）

拿到 getAssignedCustomerList 与 getCreateCustomerList 返回的客户列表后，合并去重（同一客户可能既被创建又被分配），对每个客户调用 getCustomerFollowRecords 判定有效性：

- 入参 customerId（必填，客户 ID）、timeStart/timeEnd（可选，GMT 毫秒时间戳，建议与报告时间范围一致）。
- 返回该客户的跟进记录列表（沟通/外勤合并，按时间倒序）。
- **有效客户**：有跟进记录（records 非空）的客户。
- **未跟进新线索**：最近 3 天分配且无跟进记录的客户。
- 为提高效率，可对多个客户并发调用（无依赖关系）。

### 4. 按员工汇总并生成报告

将四个数据源按 pid 聚合，用步骤 1 的 pid→姓名映射输出报告。每个员工汇总：

| 维度 | 数据来源 | 汇总方式 |
|---|---|---|
| 新增线索 | getCreateCustomerList | count（该员工区间内创建的客户数，自建线索） |
| 分配线索 | getAssignedCustomerList | count（该员工区间内公海分配的客户数） |
| 电话 | getCallStat | callAcnt（拨打次数） |
| 接通 | getCallStat | callScnt（接通数） |
| 有效客户 | getCreateCustomerList + getAssignedCustomerList + getCustomerFollowRecords | 对每个创建/分配客户调 getCustomerFollowRecords，有跟进记录的客户 = 有效客户，按归属人/创建人聚合 |
| 商机 | getSalesChanceList | 按阶段分布（初步接触/跟进中/方案报价/合同谈判/赢单/输单） |
| 成交 | getOrderList | count + 金额汇总（状态为已确认/已出库的订单） |
| 回款 | getReceivePaymentList | 回款金额汇总 + 笔数 |
| 退款 | getReceivePaymentList | 退款金额汇总 + 笔数 |

输出格式示例：

```
运营部 2026年8月 销售报告

员工    新增线索  分配线索  电话  接通  有效客户  商机(阶段分布)       成交  成交金额   回款金额  退款金额
昆昆    1      2       15   6    2      跟进2/赢单1         1    50000    30000   0
张看活  0      1       8    3    1      初步接触1/跟进1       0    0        0       0
刘虎    0      0       5    1    0      跟进中1             0    0        0       0
```

### 5. 标注异常事项

根据数据标注以下需要关注的事项（在报告末尾单独列出）：

#### 5.1 未跟进新线索

从 getCreateCustomerList 与 getAssignedCustomerList 中取最近 3 天创建/分配的客户，逐个调 getCustomerFollowRecords 检查——无跟进记录的客户，标注为"未跟进新线索"。

#### 5.2 连续 7 天没推进的 S 级客户

- 需要额外调用 getCustomerLabels 或从客户数据中识别 S 级客户（如果工具不支持直接获取标签，则跳过此项并说明）。
- 对 S 级客户，通过 getCustomerFollowRecords 检查其最近跟进时间，超过 7 天未跟进的标注为"连续 7 天没推进的 S 级客户"。

#### 5.3 今天必须处理的事项

根据当前日期，标注以下紧急事项：
- 商机截止时间为今天的（scdeadline = 今天）。
- 订单状态为"待确认"且创建超过 3 天的。
- 回款状态为"待确认"且创建超过 5 天的。

### 6. 简要点评（可选）

- 对比各员工数据，指出：线索多但转化低的（跟进效率）、电话多但接通低的（话术/号码）、有商机但长期未推进的（跟进力度）。
- 只基于已获取的数据点评，不编造。

### 7. 报告落库（可选，用户确认后执行）

用户要求保存/写入报告时，展示报告全文给用户确认，确认后调用 createWorkReport 写入口袋工作汇报：

- **写入前先查模板**：调用 getWorkReportTemplate（入参 reportType）确认当前账号是否配置了自定义表单模板；返回 template 为空时用 content 提交，否则优先用 forms 提交。
- **createWorkReport**：入参 reportType（daily/weekly/monthly）、wrDate（归属周期内任一时间，工具自动对齐）、content（报告全文）或 forms（表单填写项，`[{formId, value}]`，formId 取自模板 fields）。返回 workReportId/version。
- **forms 填写值约定**：radio/checkbox=选项文本或提交值（多选英文逗号分隔）；textareafield/number=原文；customerfield=客户ID（多个英文逗号分隔）；datefield=YYYY-MM-DD 或毫秒时间戳；timefieldhour=YYYY-MM-DD HH:mm、HH:mm（默认当天）或毫秒时间戳。必填字段缺值、选项不匹配、超长均会报错。
- **getWorkReportList**：回看/对比历史报告时用。入参 startDate/endDate（时间范围，GMT 毫秒时间戳）、reportType（可选）、pids/gids（可选）。返回该时间范围的汇报列表，含自定义字段(forms)、图片附件(pictures)和其他附件(attachments，均含下载链接)。
- **modifyWorkReport**：报告写错需修正时用。入参 workReportId（取自 getWorkReportList/createWorkReport 返回）、content（新正文，整篇替换）或 forms（整套替换原表单，不传则保留原表单）。只能修改当前账号创建的汇报。
- **写入必须用户确认**：报告全文（或表单内容）经用户确认后才调用 createWorkReport；未确认时只展示不落库。
- 归属日期超限（如创建未来周期的汇报）时服务端报“提交时间错误”，向用户说明并改用当前周期。

## 常见异常

| 现象 | 处理方式 |
|---|---|
| 401 / 未授权 | 提示用户重新发起扫码授权（AGENT 会自动打开授权页） |
| 时间范围超过一年 | 工具限制 stime 与 etime 间隔不超过 365 天，缩小范围重试 |
| 某个工具返回空列表 | 输出"该时间范围内无对应数据"，不报错 |
| pid 映射不到姓名 | 显示原始 pid 并提示"该 pid 未在通讯录中找到" |
| getReceivePaymentList 报参数错误 | 确认已部署最新版本（LookPerson 必须设置） |
| createWorkReport 报提交时间错误 | 归属日期超出服务端允许范围（不能超过下一周期），改用当前周期重试 |
| createWorkReport 报未配置模板/未定义表单字段 | 当前账号无该类型模板，改用 content 提交 |
| forms 报必填字段未填写/值不在可选项内/超长 | 对照 getWorkReportTemplate 返回的字段定义修正填写值后重试 |
| modifyWorkReport 报汇报不存在/只能修改自己创建的 | workReportId 必须原样取自 getWorkReportList/createWorkReport 返回值，且汇报创建人须为当前账号 |

## 注意事项

- **时间范围必须明确**：stime/etime 为必填（GMT 毫秒时间戳，左闭右开），用户只说"8 月"时按当前年份换算并复述确认。
- **时间范围不超过一年**：getCreateCustomerList 与三个列表工具均限制开始与结束时间间隔 ≤ 365 天。
- **无需分页**：所有工具内部自动分批拉取全部数据，不要自己拼分页参数。
- **pid 转姓名**：所有工具返回的 pid 都需要用 getAllPerson 的结果映射，映射不到的显示原始 pid。
- **时长单位为秒**：getCallStat 的 callLen/listenLen 为秒，输出可换算为分钟但需注明。
- **金额单位为元**：getOrderList/getReceivePaymentList 的金额已转换为元（decimal 口径）。
- **商机阶段编号**：1=初步接触、2=跟进中、3=方案报价、4=合同谈判、5=赢单、6=输单。
- **订单状态**：已确认包含未出库/出库中/已出库三个子状态。
- **回款/退款分两次拉取**：getReceivePaymentList 内部自动分别拉取回款（refunds=0）和退款（refunds=1），响应中 receivePayments 和 refunds 两个列表。
- **报告写入需确认**：createWorkReport/modifyWorkReport 为写操作，必须先把报告全文展示给用户确认后再写入；modifyWorkReport 只能修改当前账号创建的汇报。
- **自定义表单汇报**：配置了模板的汇报正文在 forms 各字段里，content 为老客户端占位文案（读取时工具已置空）；写入优先用 forms，字段定义以 getWorkReportTemplate 为准。
- **汇报时间范围查询**：getWorkReportList 入参为 startDate/endDate（GMT 毫秒时间戳），不再需要 wrDate 归一化对齐；reportType 可选，不传则查全部类型。
