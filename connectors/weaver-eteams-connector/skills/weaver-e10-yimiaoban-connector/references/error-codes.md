# 易秒办错误码参考

接口返回非 0 错误码（`actionMsg.code` / `ret`）时，据此向用户解释原因；成功码为 `0`。命令失败时 stderr JSON 的 `error.code` / `error.subtype` / `error.message` 与之对应，**不要用退出码 0 判断成功**。

## 通用 / 基础

| 错误码 | 含义 |
|---:|---|
| 1014 | 服务器内部错误（常见于请求体缺必填协议字段，如 `trans_id`） |
| 1016 | 参数错误 |
| 1038 / 1039 | 解析错误 / 默认错误 |
| 1058 / 1059 | token 过期 / token 信息验证失败（登录态失效，重新登录） |
| 1060 | 禁止操作 |

## 登录 / 用户

| 错误码 | 含义 |
|---:|---|
| 1100 / 1101 | token 错误 / token 过期 |
| 1106 / 1107 | 用户不存在 / 用户被禁用 |
| 1109 | 用户未登录 |

## 群相关

| 错误码 | 含义 | 处理建议 |
|---:|---|---|
| 1200 | 群邀请人数超过最大限制 | 分批邀请 |
| 1201 | 一次获取群信息数量限制 | 减少 `groupIds` 数量 |
| 1203 | 一次踢人数量超过上限 | 分批踢人 |
| 1206 | 一次同步消息数量限制 | 降低 `num` |
| 1207 | 群成员人数为 0 | 确认群内是否仍有成员 |
| 1208 | 用户不是群成员 | 群 id 传错或操作者已不在群内 |
| 1209 | 群信息不存在 | 群 id 错误或群已解散 |
| 1210 | 没有权限 | 确认操作者是否为群主/管理员 |
| 1212 | 用户已存在（重复邀请） | 该成员已在群内 |
| 1218 | 邀请失败 | 被邀请人可能被 UCP「群邀请权限限制」拦截，需本人/管理员调整权限或改走申请入群 |
| 1220 | 超过管理员最大个数 | 减少管理员数量 |
| 1225 | 进群链接/二维码失效 | 让用户重新获取邀请入口 |
| 1226 | 群已销毁 | 无法再操作该群 |
| 1232 | 规则内人员不可主动退群 | 告知用户该群由规则维护 |
| 1233 / 1237 / 1246 | 部门群/全员群/事项群已存在 | 普通群建群不涉及；如需其他类型请在客户端操作 |
| 1269 / 1270 | 创建群聊功能关闭 / 超过每日建群上限 | 联系管理员或改日再试 |
| 1271 | 加入群需要对方同意 | 属于审批流程，等待管理员/群主处理 |
| 1210（退群后） | 退出群聊后再对同一群执行 `join` / `destroy` 会被拒绝 | 群主或最后一人退群会让群变成无主空群，只能由客户端或管理员处理；`group.exit.prepare` 已内置该风险护栏 |

## 消息相关

| 错误码 | 含义 | 处理建议 |
|---:|---|---|
| 1303 | 数据为空（无聊天记录） | **按成功空列表处理**，结合返回的 `emptyReason` 说明口径 |
| 1500 / 1501 | mask 无效 / 参数类型无效 | 检查输入字段 |
| 1502 | 无用户信息 | 检查 uid/cid |
| 1504 | 消息类型未定义 | 转必达等场景按源消息类型处理 |
| 1505 | 撤销超时 | 消息超过可撤回时限（回包 `time_out` 给出实际时限，CLI `withdrawInterval` 会带上） |
| 1506 | 消息不是自己撤回 | 只能撤回本人发送的消息 |
| 1507 | 编辑撤回超时 | 不支持再撤回 |
| 1511 / 1512 | 消息敏感词强控/弱控检测失败 | 调整内容后重试 |
| 1520 | 不允许删除未读会话 | 本技能不提供删除会话能力 |

## 数据 / 其他

| 错误码 | 含义 |
|---:|---|
| 1307 | 用户不存在于 db |
| 1311 / 1312 / 1653 | 数据已存在 / 数据不存在 |
| 1654 | cid/uid 为 0（不允许，CLI 已在入参拦截） |
| 1655 | 请求超时 |
| 2000 | 网络异常，请稍后重试 |
| 2001 | json 解析失败 |

## CLI 侧校验错误（`error.type=validation`）

| subtype | 含义与处理 |
|---|---|
| `forbidden_key` | 输入含操作人字段（`user`/`sender`/`creator` 等），去掉后重试 |
| `alias_conflict` | 旧字段（`filePath`/`shareGroups`）与新字段（`file`/`shareGroup`）同时出现且取值不一致，只保留一个 |
| `id_invalid` / `id_required` | uid/cid/群 id 缺失、为 0 或非数字 |
| `content_required` | 发送内容为空（含全空白文本）或必达既无 `txt` 也无 `convertMsgid` |
| `content_conflict` | 一次只允许一种媒体（`img` 与 `file` 不能同时传） |
| `members_resolve_failed` / `members_empty` | 成员 hrm 解析失败/为空，列出失败项后由用户决定是否 `removeFailed:true` |
| `members_empty` | 群内没有可接收成员（或只有本人） |
| `target_required` / `to_cid_required` | 必达缺少目标：群需 `groupId`，单聊需 `toUid`+`toCid` |
| `unread_only_group_only` | `unreadOnly` 仅支持群聊转必达 |
| `source_not_found` / `source_invalid` / `unread_empty` | 转必达源消息缺失/无法解析、群内无未读人员（不自动回退全员） |
| `self_not_included` | 建群成员必须包含操作者自己 |
| `owner_exit_ack_required` | 群主或最后一个成员退群未传 `acknowledgeOrphanRisk:true`（退群后群会变成无主空群，无法再 join/destroy） |
| `output_required` / `output_parent_missing` / `output_exists` | `file.download` 输出路径缺失、父目录不存在、目标已存在（拒绝覆盖） |
| `context_mismatch` / `continuation_expired` / `target_changed` | 确认上下文变化/过期/目标变化，重新 `prepare` |
| `self_identity_missing` / `self_identity_incomplete` | 当前登录态解析不到本人 `imCid`/`imUid`（`group.search` 的 members/owner/creator、撤回、必达、建群自检需要），按共享规则重新登录后重试；**不要用 0 兜底** |
| `num_invalid` / `time_invalid` | `num` 非正整数，或时间参数无法解析（支持 unix 秒 / `YYYY-MM-DD` / `YYYY-MM-DD HH:mm:ss`） |
| `session_type_invalid` / `reminder_invalid` | 会话提醒设置（`im.user.setRemind`）的 `sessionType` 不是 `1` 单聊会话 / `2` 群聊会话 / `4` 系统会话，或 `reminder` 不是 `0` 接收提醒 / `1` 免打扰 |
| `target_required` 补充 | 会话免打扰目标缺失：单聊会话缺 `toUid`/`toCid`、群聊会话缺 `groupId`、系统会话缺 `group` |

## 拉取口径相关的成功语义（非错误）

| 现象 | 说明 |
| --- | --- |
| `data.empty=true` + `emptyReason` | `actionMsg.code=1303`（无聊天记录）按成功空列表返回，用 `emptyReason` 说明是"当天无消息/时间范围无消息/会话无历史" |
| `data.rangeShrink.notice` | 时间范围跨度 > 7 天时自动收敛为该范围最后 7 天，**必须把 notice 转述给用户** |
| `data.pages` / `data.autoPaged` / `data.hasMore` / `data.nextStart` | 本次实际拉了几页、是否自动翻页、是否还有更早数据、续拉锚点（有界区间自动翻页最多 100 页） |
| `data.hasMore=true` 且 `cappedAtMaxPages=true` | 已达单次自动翻页上限，用 `nextStart` 显式续拉 |
