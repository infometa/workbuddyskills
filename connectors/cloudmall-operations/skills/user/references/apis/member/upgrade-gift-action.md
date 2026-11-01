# 会员域 — 升级礼包写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-level.md`；礼包现值读取（配置列表/全局开关/发放记录）先读 `upgrade-gift-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.upgrade-gift.save 保存升级礼包配置 🔴 · member.upgrade-gift.config-save 更新全局开关 🔴

---

## ✅ 保存升级礼包配置 — ops.member.upgrade-gift.save

- 🔴 整体保存（先删后插，事务原子）——levels 为全部等级的最终配置全集，**未包含在 levels 中的等级其现有礼包配置（giftPoints/coupons）会被静默删除**，必须以 `upgrade-gift.list` 回读值回填所有需保留的等级；revision 当前为弱化乐观锁（可省略；服务端接受传值但不严格校验）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| revision | String | — | 修订版本号（可省略；十进制字符串；当前服务端不做严格校验） |
| levels | Array | ✅ | 各等级礼包配置（非空） |
| levels[].levelId | String | ✅ | 等级 ID（来自 `ops.member.level.list`） |
| levels[].levelEnabled | Boolean | — | 该等级礼包开关（true=启用；null 视为 false） |
| levels[].giftPoints | Integer | — | 升级赠送积分 0~999999（null=不配置） |
| levels[].coupons | Array | — | 赠送优惠券（≤2 张） |
| coupons[].couponId | String | ✅ | 优惠券模板 ID（来自促销域；⚠️ 服务端无 @NotBlank 校验，调用方保证必传） |
| coupons[].couponName | String | — | 优惠券名称 |
| coupons[].quantity | Integer | — | 发放数量 1~99（可省略，服务端兜底默认 1） |

### 出参（原始返回）

`data` 为 `null`；回读 `upgrade-gift.list` 核验。

### 调用示例

```json
{"capability":"ops.member.upgrade-gift.save","input":{"revision":"2","levels":[{"levelId":"1000012345678901234","levelEnabled":true,"giftPoints":500,"coupons":[{"couponId":"3000012345678901234","couponName":"满100减20券","quantity":1}]}]},"summary":"为黄金会员配置升级礼包：500积分+1张券"}
```

---

## ✅ 升级礼包全局开关更新 — ops.member.upgrade-gift.config-save

- 🔴 全租户——**该开关是礼包发放链路的第一道门禁**（关闭后所有等级礼包停发、配置保留，重新开启即恢复）；upsert 语义

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| enabled | Boolean | ✅ | 目标开关状态 |

### 出参（原始返回）

`data` 为 `null`；回读 `upgrade-gift.config` 核验。

### 调用示例

```json
{"capability":"ops.member.upgrade-gift.config-save","input":{"enabled":true},"summary":"开启升级礼包功能"}
```
