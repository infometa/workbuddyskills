# 招聘写操作

## 何时使用

需要变更招聘模块数据时使用：新建人才、安排面试、发送 Offer 邮件、办理入职、提交/修改面试反馈、催促面试评价。全部走 **prepare → 用户确认 → apply** 协议，禁止跳过确认直接执行。

写入边界（与源系统纪律一致）：

- 每个写操作必须先调 `*.prepare`（只读定位/查重/解析 + 确认摘要 + continuation），把摘要给用户确认后才调 `*.apply`（需 `confirm:true` + continuation）。
- `cancel-change-entry`（取消改期入职）未实现，属禁用边界，见 `safety-boundaries.md`。
- 面试通知（安排面试的 `notify`）、Offer 邮件、催评通知属 **L3 外部通知**，会打扰真实的人，必须用户明确同意后才传 `notify:true` / 执行 apply。

## 操作一览

| operation（prepare/apply 成对） | 用途 | 关键校验 |
| --- | --- | --- |
| `ehr.recruit.candidate.create.*` | 新建人才 | 手机号建前查重（apply 二次查重强制拦截）；渠道须在数据字典中 |
| `ehr.recruit.candidate.interview.arrange.*` | 安排面试 | 候选人 READ 权限；面试方式/轮次须在枚举内；面试官姓名须解析到 userId |
| `ehr.recruit.offer.send.*` | 发送 Offer 邮件（L3） | Offer 状态必须「未发送」；邮箱必填；模板须存在于 uf_rcrt_notify_mould |
| `ehr.recruit.entry.process.*` | 办理入职（落账号不可逆） | estValidateEntry 校验；已办理（status=2）拒绝；department/positionRank 必填 |
| `ehr.recruit.candidate.interview.feedback.edit.*` | 提交/修改面试反馈 | 已失效(INVALID)面试拒绝；结果须在枚举内；全字段集保存防清空 + 乐观锁 |
| `ehr.recruit.candidate.interview.feedback.urge.*` | 催促面试评价（L3） | 定位待反馈记录；催评按钮动作流运行时解析，解析不到阻断 |

## 协议细节

1. `prepare` 返回 `status: AWAITING_CONFIRMATION`、`preview`（人类可读摘要）、`continuation`（10 分钟有效）与 `expiresInSeconds`。
2. `apply` 入参 = prepare 相同业务参数 + `confirm: true` + `continuation`。**apply 会校验指纹**：业务参数与 prepare 快照不一致时报 `target_changed`，须重新 prepare。
3. continuation 与当前 CLI 登录环境绑定（由 `weaver-work-cli auth` 托管），切换租户或账号后报 `context_mismatch`，此时须重新 prepare。登录与认证细节见共享规则 [`../../weaver-e10-shared-connector/SKILL.md`](../../weaver-e10-shared-connector/SKILL.md)。
4. 多步写入（saveFormData → initTalentBatch / sendOffer / saveEstPreEntry / runEsb）中途网络中断时报 `partial/write_uncertain` 并给出已落地的记录 id——**禁止自动重试**，先按提示回查（`candidate.search` / `candidate.card`）确认实际状态。
5. prepare 与 apply 应连续执行。`arrange` 默认时间窗取「当前时刻」，间隔跨分钟后指纹不一致会报 `target_changed`；如需指定时间请显式传 `startTime`/`endTime`（格式 `YYYY-MM-DD HH:mm`）。

## 参数要点

- `create`：`name` + `mobile` 必填，`channel` 传中文名（如「BOSS直聘」），CLI 负责解析为字典 optionId，查不到报 `channel_not_found`。
- `arrange`：`talentId` + `interviewer`（姓名）必填；`type`（现场/视频/电话/AI面试）、`session`（初试/复试等，须在该环境枚举内）；`positionId` 不填时从人才当前应聘批次继承，继承不到报错要求显式提供。
- `offer.send`：`talentId` 必填；`email`/`deadline` 缺省时从 Offer 记录继承；`template` 默认「offer通知」。
- `entry.process`：`departmentId`/`positionRankId` 必填（Offer 记录无此字段）；`subcompanyId`/`positionId`/`entryTime` 缺省时从 Offer 记录继承。
- `feedback.edit`：`talentId` 必填；`feedbackId` 最稳定位，或 `feedbackIndex`（默认第 0 场含反馈的面试）；`result`/`comment` 至少一项。
- `feedback.urge`：`talentId` 必填，无需其他参数。

## 命令示例

安排面试（prepare → 确认 → apply）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.interview.arrange.prepare --input-json '{"talentId":"PLACEHOLDER_TALENT_ID","interviewer":"张三","type":"现场面试","session":"初试"}'
# 向用户确认 preview 后：
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.interview.arrange.apply --input-json '{"talentId":"PLACEHOLDER_TALENT_ID","interviewer":"张三","type":"现场面试","session":"初试","confirm":true,"continuation":"PREPARE 返回的 continuation"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.interview.arrange.prepare --input-json '{"talentId":"PLACEHOLDER_TALENT_ID","interviewer":"张三","type":"现场面试","session":"初试"}'
# 向用户确认 preview 后：
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.interview.arrange.apply --input-json '{"talentId":"PLACEHOLDER_TALENT_ID","interviewer":"张三","type":"现场面试","session":"初试","confirm":true,"continuation":"PREPARE 返回的 continuation"}'
```

## 错误形状（稳定 subtype）

`duplicate_blocked`（查重命中）/ `duplicate_ambiguous`（多条重复）/ `target_changed`（指纹不一致）/ `context_mismatch`（会话变化）/ `channel_not_found` / `interviewer_not_found` / `result_not_in_enum` / `offer_status_invalid` / `entry_already_processed` / `interview_invalid_status` / `esb_action_unresolved`（按钮/动作流解析不到，禁止编造 esbActionIds）/ `partial` + `write_uncertain`（多步写入中断）。

## 注意

- 所有 apply 前必须已获得用户对 preview 的明确确认；用户确认前不得调用 apply。
- Offer 邮件、面试通知、催评会触达真实候选人/面试官，误发无法撤回；拿不准时再问一次用户。
- `entry.process` 落人员账号后不可撤销，apply 前务必复述组织架构参数（分部/部门/职位/职级/入职日期）让用户确认。
- 写入成功后建议回查：`candidate.card` 查面试与反馈，`candidate.list type=offer` 查 Offer 状态，`candidate.list type=entry` 查 transact_status。
