# 创建客户场景

用于客户管理：「搜索既有客户 → 获取公司配置 → 创建/编辑客户 → 打标签与回访提醒」全流程。

## 场景工具

参数结构以工具 schema 为准，本文档不写死字段。

| 工具 | 用途 |
|---|---|
| searchCustomer | 按客户名称或联系人（姓名/手机号/微信）搜索既有客户，最多返回前 100 条 |
| createCustomer | 创建新客户（需【创建客户】权限） |
| editCustomer | 编辑已有客户（editFields 指定要更新的字段；默认查重，skipCheckSame=true 跳过）；contacts 为增量操作：contactId>0 编辑已有联系人（只更新传入的非空字段），contactId 留空为新增，deleted=true 为删除（仅需 contactId），未列出的已有联系人保持不变（需【编辑客户】权限） |
| setCustomerLabels | 全量覆盖客户标签配置树（自动读改写合并；需管理员/CRM 权限） |
| getCustomerProperties | 获取客户/联系人自定义属性配置（属性ID、类型、可选值等） |
| getCustomerLabels | 获取客户标签树配置 |
| getCustomerFollowLevel | 获取跟进阶段配置 |
| createRemind | 创建回访提醒（关联客户，指定提醒时间与重复规则） |
| whoami | 查询当前登录用户的简要信息（pid/did/姓名），用于确认当前登录身份 |
| findPersons | 按姓名批量查找通讯录成员（PID/姓名/职位/部门），用于把用户指定的姓名转换为 pid（重名时返回多个候选） |
| getAllPerson | 获取通讯录成员信息（含职位与所属部门；传 gid 时含其子部门，不传为公司全部成员） |

## 推荐工作流

### 1. 搜索既有客户（查重与画像）

调用 searchCustomer 工具：

- name 与联系人条件（contactName/mobile/wechat）至少提供一个，且联系人条件至多提供一个（底层同为联系人搜索字段）。
- 最多返回前 100 条，无分页；命中多条时须向用户确认唯一客户后再继续。

### 2. 获取公司配置（创建前按需查询）

三个配置工具均无入参，在需要填写属性/标签/跟进阶段时调用：

- getCustomerProperties：客户属性（propPosition=0）与联系人属性（propPosition=1）；单选/多选属性的取值必须来自配置的 options（可选值列表）。
- getCustomerLabels：客户标签树最多三层，创建时按层级提交标签 ID。
- getCustomerFollowLevel：跟进过程阶段（第 1 个固定为待跟进），用于 followLevel。

### 3. 创建客户

调用 createCustomer 工具：

- 必填 name；psid 为 0（私有客户）时 followers 至少提供一个（不指定时默认当前登录用户为负责人）；psid>0 时客户归入公海且不需要 followers。
- 自定义属性用 properties（propId/propValue/propPosition）；标签用 labels（支持三级）。
- forceCreate 默认 0：命中查重时不会创建，响应通过 similarCustomers 返回相似客户列表；用户确认后才可设 forceCreate=1 跳过查重直接创建。
- 成功响应含 custmid（新客户ID）、name、createTime、version。

### 4. 结果处理

- 返回 similarCustomers 非空：向用户展示相似客户，由用户决定「改为编辑现有客户」（改用 editCustomer，按 editFields 局部更新）或「强制创建（forceCreate=1 重试）」。
- 不要臆造创建参数与客户 ID，一切以工具返回为准。

### 5. 后续动作（按需）

- 编辑现有客户：调用 editCustomer，必填 custmid + editFields（仅更新列出的字段）；默认查重，用户确认后可用 skipCheckSame=true 跳过。
- 编辑/删除已有联系人：先用 searchCustomer 或 getCustomersByIds 拿到目标客户的联系人列表（含 contactid），再在 contacts 里携带 contactId 操作（编辑时只传要改的字段，删除时带 deleted=true 且仅需 contactId）；contactId 必须原样取自查询返回，写入前服务会回查校验，臆造的 contactId 会报参数错误（不校验的话服务端会误当新增联系人落库）。新增联系人则不带 contactId 直接传字段。
- 创建回访提醒：调用 createRemind，关联 customerIds；awokePids/awokeGids 不指定时默认提醒当前登录用户。
- 维护标签树（需管理员/CRM 权限）：调用 setCustomerLabels；为全量覆盖语义，建议先用 getCustomerLabels 取当前树，确认合并后再提交。

## 常见异常

| 现象 | 处理方式 |
|---|---|
| 401 / 未授权 | 提示用户重新发起扫码授权（AGENT 会自动打开授权页） |
| 创建被相似客户拦截（返回 similarCustomers） | 展示相似客户询问用户；确认后加 forceCreate=1 重试，或改用 editCustomer 局部更新 |
| 标签树写入报权限错误 | setCustomerLabels 需要管理员或 CRM 权限，提示用户确认账号权限 |
| 创建/编辑客户报权限错误 | 需对应【创建客户】/【编辑客户】权限，提示用户联系管理员在权限组中分配 |

## 注意事项

- 含中文的参数（客户名、地址、备注等）按工具 schema 正常传入 JSON 即可。
- 不要臆造客户 ID、联系人 ID，一切以工具返回为准。
