# 公海处理场景

覆盖两条子流程：**导入客户到公海** 与 **公海客户批量分配**（客户已在公海时可直接从分配流程开始）。

## 场景工具

参数结构以工具 schema 为准，本文档不写死字段。

| 工具 | 用途 |
|---|---|
| getImportCustomerTpl | 获取导入 Excel 模板（1=私有客户，2=公海客户） |
| convertImportCustomerData | 将 Excel 读出的数据行转换为标准客户数据（含行级校验） |
| checkImportCustomerSimilar | 批量查重（名称/联系人手机号/微信号），返回可覆盖的相似客户 ID |
| batchImportCustomer | 批量导入（客户导入流程最后一步，单批最多 1000 行；需【导入客户】权限） |
| getAllPubSea | 获取有管理权限的全部公海 |
| getPsCustomerList | 获取指定公海未分配客户列表（游标翻页） |
| getOrderRank | 获取员工成交排行（需指定 startTime/endTime；分配规则参考数据） |
| batchAllocPsCustomer | 批量分配公海客户到员工（需【分配客户】权限） |
| whoami | 查询当前登录用户的简要信息（pid/did/姓名），用于确认当前登录身份 |
| getAllPerson | 获取通讯录成员信息（含职位与所属部门；传 gid 时含其子部门，不传为公司全部成员），用于把员工姓名转换为 pid |

## 工作流 A：导入客户到公海

### 1. 获取模板并交给用户填写

调用 getImportCustomerTpl（type=2 为公海客户模板，type=1 为私有客户模板）：

- 返回 name（模板文件名）与 data（xlsx 文件内容 base64）：解码后按 name 落盘为 .xlsx 文件交给用户填写。

### 2. 获取表格数据（{titles, rows}）

convertImportCustomerData 的入参为 `{titles, rows}` 结构化数据（titles 为表头，rows 为数据行，row 为 excel 行号 1-based，表头为第 1 行）。

> **连接器模式限制**：本场景无本地 Excel 文件解析能力。需由agent自行将excel文件解析为 `{titles, rows}` 结构化数据后，再进入第 3 步。

### 3. 转换数据

调用 convertImportCustomerData：

- 与请求等长同序返回：成功行含 customer（标准客户数据），失败行含 errmsg（失败原因，用于提示用户修改后重试）；本步仅做转换与校验，不查重、不导入。

### 4. 批量查重

调用 checkImportCustomerSimilar：

- result 为 0 表示可导入；为负表示命中重复或受限（message 为原因说明）；命中可覆盖的重复客户时 similarCids 为该重复客户 ID 列表。
- 向用户逐行确认：覆盖（把 similarCids 一并传回下一步）或跳过；单批最多 1000 行，超出分批调用。

### 5. 批量导入（psid 决定导入目标）

调用 batchImportCustomer：

- 导入公海：psid>0（配合 getAllPubSea 获取目标公海 ID，跟进人由公海规则处理）；
- 导入私有：psid=0，此时 followerPids 必填（未指定跟进人的客户按顺序轮转分配，行内自带跟进人的优先）；
- 单批最多 1000 行，超出分批调用并回传 nextAllotFollower 以延续轮转；
- 返回 importCount（成功导入行数）与 errors（失败行及原因）：未出现在 errors 中的行视为导入成功。

## 工作流 B：公海客户批量分配

### 1. 确定目标公海

调用 getAllPubSea：

- 返回全部有管理权限的公海（psid/name/成员范围 gids/pids）；与用户确认目标 psid。

### 2. 拉取未分配客户

调用 getPsCustomerList（传 psid、count）：

- 返回该公海未分配客户总数 total 与一批客户（单批默认 100、最大 200）；
- hasMore 为 true 时把本批 nextCustmid 作为下批 lastCustmid 传入续拉，直至取完或满足本次分配数量。

### 3. 获取分配依据（可选）

调用 getOrderRank：

- 返回员工成交排行（ranking/pid/orderMoney/orderCnt，按名次升序）；需指定 startTime/endTime（GMT 毫秒时间戳）。分配规则（按业绩倾斜、平均分配等）由用户确定，本工具只提供数据。

### 4. 生成分配清单并批量分配

调用 batchAllocPsCustomer：

- allocations 每项 = 一名员工（pid）+ 其分到的客户（cids，来自第 2 步的 custmid）；psid 为公海 ID；
- 约束：调用者对公海有管理权限、客户须仍在公海中、目标员工须为公海成员；
- 单项 cids 最多 1000 个，超出分批调用；
- 分配前把清单（员工 → 客户数量/编号）展示给用户确认。

### 5. 核验

- 重新调用 getPsCustomerList 查看该公海剩余未分配客户数（total 应相应减少）。

## 常见异常

| 现象 | 处理方式 |
|---|---|
| 401 / 未授权 | 提示用户重新发起扫码授权（AGENT 会自动打开授权页） |
| 导入 errors 非空 | 逐行展示失败原因，修改后对失败行重试 |
| 分配报"客户须仍在公海中/员工须为公海成员" | 重新拉取最新公海客户与成员，修正清单后重试 |
| 导入/分配报权限错误 | 需对应【导入客户】/【分配客户】权限，提示用户联系管理员在权限组中分配 |

## 注意事项

- 单批上限：checkImportCustomerSimilar/batchImportCustomer 单批最多 1000 行，超出分批调用；getPsCustomerList 单批最多 200；batchAllocPsCustomer 单项 cids 最多 1000。
- 不要臆造 psid/custmid/pid：一切 ID 来自工具返回（公海来自 getAllPubSea，客户来自 getPsCustomerList/searchCustomer，员工来自 getOrderRank、getAllPerson 或用户提供）。
