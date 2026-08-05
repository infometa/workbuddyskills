# 讲师 Onboarding、商业 Profile 与客户交付

## 自助开通

1. 未连接时请用户点击“连接 SalesNail”，在浏览器完成登录和授权。OAuth 获得 `salesnail:onboarding` 后，可以为当前学员账号自动开通讲师试用。
2. 先调用 `salesnail_get_instructor_lifecycle_dictionary`，再调用 `salesnail_get_instructor_workspace`（`workspaceType=overview`）。
3. 汇报实际账号状态、试用期、演示/正式课剩余额度、Starter 剧本授权、六项引导任务、Profile、客户、方案和交付工作区。
4. 如果仍需显式开通，调用 `salesnail_preview_instructor_onboarding`，说明角色、演示额度、Starter 授权和工作区变化，并明确系统不会自动发放正式额度；获得明确确认后调用 `salesnail_activate_instructor_trial`。
5. 自动开通仍失败时，只允许重新连接一次。之后将 `demo@long-arena.com` 作为兜底；邮件只提供注册手机号或邮箱，请勿发送密码。

## Starter 体验

- `self`：讲师以学员身份完成一次单人自动审批体验。
- `friend`：创建 2 组多人在线体验课，分别返回组 1、组 2 的加入链接，供讲师邀请好友并练习组织、课堂节奏和复盘。
- 先 `salesnail_preview_starter_course`，确认后再 `salesnail_ensure_starter_course`。
- 同一模式幂等复用原课程；演示额度在学员实际加入时扣减，不是在建课时扣减。

返回已验证的课程名称、课程号、人数上限，以及每组的名称和独立 joinPath。旧版首组 `teamId` / `joinPath` 只用于兼容，不展示 userId、tenantId 或 Token。

## Profile、Offering、客户、方案和交付

先用 `salesnail_get_instructor_workspace` 读取真实对象。写入时：

1. 根据生命周期字典选择准确的 `workspaceType` 和业务 `status`。
2. 调用 `salesnail_preview_instructor_workspace_save`，展示 before/after、公开风险和业务含义。
3. 等待用户明确确认。
4. 调用 `salesnail_save_instructor_workspace`，复用 preview 的类型，并使用稳定 `clientRequestId`。
5. 读回验证。发布 Profile 后，再调用 `salesnail_get_public_instructor_profile` 验证公开内容和发布时间。

Profile 发布至少需要 `displayName`、`headline`、`valueProposition` 和安全 slug。连接器只会在 Profile 状态为 `published` 时把 `visibility` 规范为 `public`，其他状态统一为 `private`。不得发布客户私密信息、学员信息、凭证或内部系统信息。

## 客户方案

调用 `salesnail_generate_proposal_draft` 时，只能提供一个已保存 `opportunityId` 或一个内联客户 Brief。工具会结合当前 Profile 返回结构化方案、Markdown、建议保存对象和明确假设。

方案是可在 CLI 中继续修改的草稿，不是客户承诺或正式报价。讲师确认内容后，再 preview/save 为 `proposal`。将方案改为 `shared`、`accepted`，或创建对应 `delivery`，均属于单独的确认写入。

## 引导任务

任务状态只是流程标记，不等于事实证明。先验证对应的 Profile、课程、客户 Brief 或方案确实存在，再调用 `salesnail_preview_instructor_task_update`，明确确认后调用 `salesnail_update_instructor_task`。

固定顺序为：01 `self_experience` 完成自我体验；02 `positioning` 明确讲师定位。只有 Profile 的展示名称、专业标题和价值主张均有效时才能完成 02；完成任务不会自动发放正式学员额度。

讲师可在讲师工作台使用已到账站内付费余额购买正式额度：国内站为人民币 800 元/人，国际站为美元 100 元/人。币种由账号所属站点固定，不换汇、不使用赠送余额，充值保持独立。Connector 可以解释并引导用户打开 `/instructor?tab=journey`，但不直接开放支付、余额扣减或额度购买写操作。
