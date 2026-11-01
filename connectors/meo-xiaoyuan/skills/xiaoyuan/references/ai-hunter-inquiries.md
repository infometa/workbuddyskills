# AI 猎客询盘、解锁、沟通与提醒

## 列表与详情

工具：`xiaoyuan_wa_inquiry_list` 拉列表，`xiaoyuan_wa_inquiry_detail` 下钻单条。列表支持 cursor、limit、status 和 include_pending；include_pending 用于对账查看待轮到的时段，不能据此越过权限或提前解锁。读取询盘详情，空串等价空值。错误按实际业务 code／success／msg 判断，不仅看 HTTP 200。

展示意向产品、摘要，随后展示规格、采购数量、目标价、交期、目的地；没有的字段省略。不要根据空字段补写采购事实。

| inquiry_status | 展示和操作 |
|---|---|
| UNLOCK_PENDING | 待解锁，只展示授权摘要，不暴露 buyer_contact；提供有效的解锁动作 |
| COMMUNICATING | 沟通中，按实际返回展示已授权 buyer_contact 的 nickname／wa_number、剩余时段及沟通入口 |
| CLOSED_FORFEIT_UNLOCK_EXPIRED | 解锁时段过期，关闭 |
| CLOSED_FORFEIT_ZERO_REPLY | 时段内零回复，关闭 |
| CLOSED_HANDOFF_FULFILLED | 履约交接完成，关闭 |

保留 slot_start、slot_end、queue_index、slot_state（PENDING／ACTIVE／ENDED）。倒计时主锚为本企业 slot_end，不能拿批次 window_ends_at 冒充本企业沟通时段。时间带明确时区并显示剩余天／小时／分钟；缺主锚时显示待确认。沟通中提醒用户在当前时段内跟进，超过时段能否继续发送以平台权限为准。

列表保留 cursor、limit、status、include-pending 等筛选与翻页语义；详情按真实 inquiry_id 下钻。协议允许的空串按无值处理，不补数据；status_timeline 中 CREATED、SLOT_STARTED、UNLOCKED、FULFILLED 保留原始时间线供追溯。业务错误 400（鉴权）、40001（参数）、40301（不存在或无权限）按原协议及实际消息解释，不用其他企业身份重试。

原时段规则要求段内剩余不足 1 小时关闭解锁入口，尚未轮到或已结束同样不可解锁。最终可操作性由服务端决定。关闭记录不再显示排队中或活动解锁动作。

## 解锁与收费

用户确认询盘、真实费用及操作后，调 `xiaoyuan_wa_unlock` 提交 inquiry_id 与按授权提供的 operator_id。企业身份由 Key 解析；幂等键由平台按企业和询盘派生，小元不生成替代键，也不自行扣点。扣费和开通由平台同事务完成。

| provision_result | 后续动作 |
|---|---|
| OPENED | 开通成功，回查详情并更新为沟通中 |
| OPENED_REPLAY | 同一请求已处理，沿用首次结果，不重复扣费 |
| ALREADY_OPENED_OTHER_KEY | 已开通，回查现态，不再次解锁 |
| REJECTED_CLOSED | 关闭，更新展示，停止解锁 |
| REJECTED_SLOT_UNAVAILABLE | 当前时段不可解锁，停止重试循环 |
| REJECTED_NOT_FOUND | 查询目标是否存在，不换目标盲试 |
| REJECTED_MISMATCH | 企业与询盘归属不符，检查权限路由 |
| REJECTED_CREDIT_INSUFFICIENT | 保持待解锁，转 account-credit.md 的充值／账户流程，恢复后核对时段并重试同一询盘 |

未知结果先核对，不承诺已经扣费或已经开通。联系方式只依据授权后的详情，不从普通摘要恢复明文。

## 打开沟通与回信

解锁成功后，把平台询盘页链接发给用户：`https://xyconsole.tradechina.com/wa-chat/{inquiry_id}`（以真实询盘标识替换；详情 chat_enterable=true 时可下发）。链接不含登录态，用户点击若浏览器未登录会先进入平台登录页，登录后直达询盘页——这是预期行为，向用户说明即可，不是故障。链接只发给本企业有权人员，不进群聊、不写入日志；不把内部租户 ID 或 token 交给用户填写。

买家回信呈现原话并附买家、此前触达和时间等最小上下文；询问或遵循用户已授权的处理方式，不因创建猎客任务就自动回复。已授权的回复按实际聊天通道完成，不能重复转发。

## 提醒、展示更新与停止

- 原询盘轮询基线为每 5 分钟；部署可用服务端事件替代。使用游标、询盘 ID 和持久化快照去重，不在每次对话里起一个新轮询。
- 新询盘呈现待解锁或沟通中视图；解锁后更新原展示，保留消息／展示标识，避免发重复卡。WorkBuddy 用适合自己的消息或任务界面呈现。
- 按 slot_end 在剩余 4 小时、1 小时内各提醒一次；不足 1 小时首次看到时只发 1 小时提醒并标记两档已覆盖。过期不再催办解锁，先核对终态。
- 提醒发出成功后才记已投递；失败保留待投递状态。查询中记录消失不能直接判关闭，先查详情并核对分页。
- 进入关闭状态后更新原展示并停止该询盘后续提醒。任务日报的停止与询盘提醒分别按各自 ID 维护。
- 用户要求开启、修改或停止提醒时操作实际订阅；仅在服务端返回订阅回执后报告已设置。
