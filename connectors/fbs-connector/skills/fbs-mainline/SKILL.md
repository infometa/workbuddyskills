---
name: fbs-mainline
description: 福帮手旧业务场景、匿名绑定与进度主线；不用于核对OAuth登录账号或本人画像。获准且真实交付后才记录进度。
metadata:
  ai.workbuddy.description_zh: 核对福帮手服务身份与场景，仅在真实交付后记录使用进度。
  ai.workbuddy.description_en: Check FBSir identity and scene routing, then record progress only after actual delivery.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 福帮手身份与场景主线

执行前读取[身份发送与工具边界](references/identity-and-permission.md)，遵守[公共路由](../fbs-connector/SKILL.md)和当前产品前置。机器约定见[身份合同](references/identity-contract.json)，不把它当宿主证明。

以下保留 canonical 的旧 API2 主线，仅按当前旧工具 schema 与原信封执行。相同 URL 的七个 OAuth 账号/画像工具走独立合同，不必先走场景链。只有在另行选择历史预览资源时，才按该资源 legacyBridge.available 判断合成 core3；不把预览桥状态当成 canonical 旧工具的总开关。新七工具的受保护调用需要 OAuth，旧匿名身份不能替代。

## 仅旧场景与进度请求的固定顺序

用户只是核对登录账号、连接授权或本人画像时，不进入下列顺序，返回公共路由的 `member_whoami / fbs_capabilities`。已加载专家必须用自己包内的实际 ID 和版本；本技能不能把当前专家降为无身份调用。

1. 具名调用 `skill_whoami` 前，从本轮实际加载清单的 `name` 取得产品包ID，优先放入 `packageName`。已知 `productId` 应与包ID一致；已知成员入口和实际包版本按原值附带。未知版本省略，不填连接器版本，也不因版本升级改用别的身份。OAuth画像预览仍单独按其当前服务合同处理。
2. 仅当返回明确指定场景/身份读取类下一工具时，按 `references/action-envelope.md` 校验并原样转发完整 `actionEnvelope.toolArguments`；不得挑字段、改名或把 envelope 之外的候选字段并入调用。写入型下一步转交对应子技能并重新检查用户意图与写前条件。
3. 先把场景内容转化为用户可用的首值或继续使用成果。
4. 只有真实交付完成后，才按返回参数调用 `skill_consume`，记录一次 `first_value_completed` 或 `continued_use_completed`。 文件型成果必须先获得宿主展示工具对本次文件的成功回执；聊天型成果必须先出现在用户可见正文。创建文件、检查通过或进度播报均不满足此门，不能先consume后present_files。

## 强制边界

- 没有上一跳可验证 action envelope 时，不主动调用场景查询，也不跟随奖励或写入型下一步。
- 原样转发表示不增删、不改名、不改大小写；来源标记只能由真实宿主或测试夹具提供。
- `skill_consume` 必须使用同一 action envelope 中服务端提供的幂等键、binding 和真实交付类型；丢响应时先按当前工具能力回读未决状态，不生成新键重复记录。
- 连接器不可用时按当前产品合同提供允许的聊天帮助；不全局覆盖超级独董会三授权等产品专用前置，不因画像不可用增加阻塞。

## 归因

- 产品身份及待核映射见 [expert-routing](references/expert-routing.md)；专家、Skill 与连接器分别计型，版本不用于猜测身份。
- 产品包ID是默认正式资源的识别主键，版本仅作观测；显式身份冲突不能靠删除字段绕过。遇 `FBS_ATTRIBUTION_FIELDS_MISSING`，仅服务明确未接受且允许补正时，按身份说明对只读调用最多纠正一次；写操作不自动重试。
- text-only `attribution`是服务对声明的解释；null保持未知，路由登记不等于账户/宿主认证，不自行提升信用flags。
- 测试属性来自真实验证配置和服务准入。旧契约支持的probe/test字段才可发送；OAuth beta不允许在封闭schema里额外塞测试字段，也不由模型手工改请求头。合成账号、来源声明和技术审计不当自然WorkBuddy使用证明。
- 输入、服务登记或返回的规范化身份冲突时，保留 raw claim、规范化值和冲突原因；归因相关写入停止，聊天首值仍可继续。

## 工具最小合同

完整参数以 `tools/list` 为准；本技能只固定安全所需前置：

| 工具 | 最小前置 | 成功判定 | 副作用 |
| --- | --- | --- | --- |
| `skill_whoami` | 真实产品包ID；版本已知则传、未知则省略；匿名仅限允许它的旧资源，OAuth core另需account:read | 返回有效身份/路由信封与下一步 | 业务读取，可产生binding/观测记录 |
| `fbs_scene_pack_query` | whoami 明确指定；同一绑定原样转发 | 返回场景内容及可验证下一步 | 业务读取，可产生 binding/观测记录 |
| `skill_consume` | 内容已真实交付；事件类型与幂等键明确 | 服务端确认进度记录成功 | 写使用进度 |

这三个原名保留旧API2进度语义。OAuth core3另由网关核对当前账号/client/grant及原始下一跳，skill_consume需要work:write；不路由成会员结算或扣分。缺core时仍可按其自身授权使用新画像工具，不代理另一上游。

任何 `isError=true`、业务 `success=false`、错误包络或缺失预期字段都不是成功。
