# 组织范围与服务生命周期

先通过 [capability-routing](../../fbs-connector/references/capability-routing.md)；所有本域工具当前均不可调用。member_organization_list 只是拟议发现能力，未开放时使用已核实的本人门户入口选择组织，不从画像猜组织ID。

主体、组织、成员角色、本人私有事项和企业账本分别校验。用户属于企业不说明有付费/邀请/全员数据权限；企业管理员也不自动获得他人私有事项。组织移除、停用和撤权后旧上下文不可继续用；企业A事实不覆盖企业B或个人事实。

| 审定后的工具 | 合同 |
|---|---|
| member_enterprise_prepare | 用户选择服务后创建 PENDING 入口，复用 preparationKey；不预占、不扣分 |
| member_enterprise_start | 网页先确认组织、服务范围、成本和说明版本；仅 shouldExecute=true 才开始新交付；重复调用只回状态 |
| member_enterprise_complete | 真实完成后用原 contextId 和实际文件 SHA-256 结算；摘要不得编造；同号同摘要只一个终态 |
| member_enterprise_cancel | 仅取消未结算服务并释放预占，不伪称退还已结算款 |
| member_enterprise_receipt | 原 contextId 只读回执，未找到不代表失败，不换号重开 |

价格变化、付款组织变化或跨 grant 恢复需服务端重新核对批准。企业余额不足不得自动转个人。质量修订沿原服务，额外范围按合同另行确认；摘要匹配不代表质量验收。

member_enterprise_case_list/get 只读本人事项；create 保存用户同意的短标题/目标；link 只关联本人同企业服务。member_enterprise_artifact_save 仅保存标题、版本和实际摘要，不上传正文/路径。accepted 与 noticeVersion 只可来自实际告知和同意，不能作为绕过服务端批准的证明；matchesReceipt 仅表示摘要关系。

企业邀请、调权、审批加入、联系和对外投递不在本包自动操作范围。仅给入口不称已办理；组织服务数据不能默认用于个人销售画像。

主理人/社群角色不自动授予企业资源或服务权益。不得将个人企微登录态、凭据或联系人权限共享为多人公共应用凭据；需要多人服务时另行实现组织授权和访问隔离。本包不实现外发消息。
