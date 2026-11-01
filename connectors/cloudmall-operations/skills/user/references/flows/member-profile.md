# 会员子域 — 会员档案运营流程（查询/创建/编辑/黑名单/打标/积分调整）

> 对应契约：`apis/member/member-query.md`（档案查询）、`apis/member/member-action.md`（档案写操作）、`apis/member/point-flow.md`（租户维度积分明细）；概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

## 场景

查会员、看档案、改资料、调积分、黑名单、打标。

### 操作步骤

1. **定位会员**：`ops.member.member.search`（手机号/会员号/UID 精确，昵称模糊）
   - 手机号唯一命中 → 取 `records[].id`；多命中 → 向用户确认目标会员（复述昵称/会员号）
   - 用户只给「编号」时，先确认是会员号（memberNo）还是 uid（较长数字），存在歧义必须追问
   - 已有多个 uid 时可 `ops.member.member.batch-get-by-uids` 批量反查基本信息（⚠️ 返回**明文手机号**——答复中复述时自行脱敏为前 3 后 4）
2. **看档案**：`ops.member.member.detail`；子资源按需：`tags`（已绑标签）/ `coupons`（持券）/ `points-flows`（积分流水）/ `growth-flows`（成长值流水）/ `addresses`（收货地址，脱敏）
3. **写操作**（按需选一，均需明确用户意图 + 已确认的会员 id）：
   - 创建会员：`ops.member.member.create`（手机号必填、格式 1[3-9] 开头 11 位）
   - 编辑资料：`ops.member.member.update`（仅昵称/性别/生日可选更新，传用户要求修改的字段即可——非全量覆盖语义）
   - 积分调整 🔴：`ops.member.member.points-adjust`——复述方向/数量/原因（reason ≤10 字符）；DECREASE 前先看 detail 的可用积分确认余额充足；执行后回读 `points-flows` 核验
   - 黑名单 🔴：`ops.member.member.blacklist` / `unblacklist`（重复加/重复解会报错，先确认当前状态）
   - 打标：`ops.member.member.bind-tags`（幂等）→ **必须回读 `ops.member.member.tags` 核验生效**（见 domains 标签双轨警告）；解绑 `ops.member.member.unbind-tag`
4. **积分流水排查**（租户维度）：`ops.member.point-flow.search`（时间/手机号/交易类型筛选）+ `ops.member.point-flow.detail`

### 参数数据流

```
search 响应 records[].id → detail / update / blacklist / points-adjust / tags 路径参数
detail 响应 pointsBalance → points-adjust DECREASE 余额预检
points-adjust 执行 → points-flows 回读核验（direction=IN/OUT + amount）
```

### 异常处理
- INPUT_INVALID：积分 reason 超 10 字符、手机号格式不符、amount 超出 1~99999、DECREASE 超余额——按错误信息修正
- 标签绑定"成功但列表没出现"：跨体系 tagId 被静默跳过，向用户说明并核对 tagId 来源
- 超时：积分调整禁自动重试（可能重复加减），先查流水确认是否已执行
