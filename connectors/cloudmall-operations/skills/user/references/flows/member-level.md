# 会员子域 — 会员等级与升级礼包流程（高危全租户配置）

> 对应契约：`apis/member/member-level-query.md` / `apis/member/member-level-action.md`（等级）、`apis/member/upgrade-gift-query.md` / `apis/member/upgrade-gift-action.md`（升级礼包）；概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

## 会员等级管理

**场景**：等级体系配置（高危，影响全租户）。

### 操作步骤

1. **看现态**：`ops.member.level.list`（全量）→ 需要详情用 `level.detail`
2. **配套配置**：`level.rule-description`（等级规则富文本，读后改后保存）/ `level.downgrade-rule`（降级策略三选一）/ `level.change-logs`（升级降级流水排查）
3. **执行**（复述影响面后）：
   - 新建：`level.create`——levelCode 格式 V+1~2位数字且唯一；growthValue 不得与现有等级重复且须符合编号顺序
   - 编辑：`level.update`——levelCode 不可改；growthValue 顺序校验同上
   - 启停：`level.status`（0=启用/1=停用）
   - 降级规则：`level.downgrade-rule-save`（strategyType=1 时 expiryYears 1~5；=2 时 expiryNthYear/expiryMonth/expiryDay 必填）
   - 规则描述：`level.rule-description-save`（content 为富文本 HTML）
4. **核验**：`level.list` / `level.downgrade-rule` 回读

### 业务规则
- 等级数量上限 10；levelName ≤10 字且唯一。
- 卡面图/背景图：用户给出图片文件时，先 `ops.member.level.upload-image`（JPG/JPEG/PNG ≤2MB）取回 URL 再填入 create/update 的 cardImage/bgImage；用户直接给 URL 时原样使用。

## 升级礼包配置

**场景**：升级发积分/优惠券的礼包配置（影响全租户）。

### 操作步骤

1. **读现配置**：`ops.member.upgrade-gift.list`（全量，各等级一行：giftPoints + coupons）+ `ops.member.upgrade-gift.config`（全局开关；未配置过返回 enabled=false 即功能关闭）
2. **保存** 🔴：`ops.member.upgrade-gift.save`——levels 为**全量清单**（先删后插；**未包含在 levels 中的等级其礼包配置被静默删除**——以 `upgrade-gift.list` 回读值回填所有需保留的等级）：{levelId, levelEnabled, giftPoints 0~999999, coupons ≤2 张 [{couponId, couponName, quantity 1~99}]}；couponId 来自促销域券模板；revision 可省略（服务端当前不做严格校验）
3. **功能总开关** 🔴：`ops.member.upgrade-gift.config-save`（enabled）——**发放链路第一道门禁**（关闭后所有等级礼包停发、配置保留，重新开启即恢复）。⚠️ 会员权益 `benefit.status`（UPGRADE_GIFT）不拦截发放（仅权益行展示口径），停发必须用本开关
4. **发放记录**：`ops.member.upgrade-gift.issue-records`（按会员/等级/状态筛选，排查发放失败）
