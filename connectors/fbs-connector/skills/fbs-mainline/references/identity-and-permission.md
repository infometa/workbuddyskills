# 身份发送、一次补正与工具边界

机器合同见[identity-contract.json](identity-contract.json)。v2的resourceProfiles区分默认旧API2与经审核配置的OAuth画像Gateway；原transport/textAttribution/correction章节属于legacyApi2，不能套到另一资源。本合同是包侧约定，不是部署、登录或宿主证明；启用仍按[能力门](../../fbs-connector/references/capability-routing.md)。

## 发送前核对真实对象

1. 先核对用户本轮允许的工具、读写和文件操作范围。只读或仅MCP的限制同样适用于专家的记忆、日志、启动习惯；不调用 Edit/Write/Bash 写记忆、统计大响应或补内部记录。包有这个能力不等于本轮获准。
2. 默认正式资源以实际加载清单 `.codebuddy-plugin/plugin.json` 的 `name` 为产品包ID，发送为 `packageName`；`productId`如提供，应是同一包ID。目录名称只作清单一致性核对，显示名、当前版本、记忆和相邻产品不作识别键。
3. 机器合同登记14个产品包及其包内入口。专家团的产品身份是整个包ID；`board-convener`或具体成员入口是该包内的角色信息。不得把成员当独立客户，也不将成员名单视为真实协作证明。
4. `packageVersion`仅传本次实际加载的版本；版本升级不改变产品身份，不需要新增版本白名单。未知版本可以省略，服务保持未知。工具原参数、幂等键及返回的完整actionEnvelope仍须原样接续。
5. 产品ID、包名、入口或路由显式冲突时停止补写。包ID匹配不等于登录、权益、画像用途同意或宿主认证；未知包不借用现有产品。OAuth画像预览是独立资源，其历史三产品/版本门和账号授权仍以该资源实际合同为准，不由此默认入口策略替代。
6. 只发送当前schema允许的顶层参数，检查真正交给SDK的对象；没有授权读取清单时不越过用户工具限制。

例如，只有本轮加载信息确为该版本时，首跳参数才可包含：

```json
{"productId":"fbsir-super-partner","packageName":"fbsir-super-partner","expertEntryId":"fbsir-super-partner","packageVersion":"26.9.15"}
```

已加载版本不同就使用其原值；例子不是默认配置。其它来源字段仅在真实已知且当前 schema 接受时追加。`identityTrust`和信用布尔值是服务输出，不能由模型作为参数自证。

## 仅一次有界身份补正

只读取本次真正的工具结果；外层completed不代表成功，宿主工具失败也不能伪装成服务成功。服务小错误的已约定形状是：

```json
{"success":false,"serviceRequestAccepted":false,"retryAllowedAfterIdentityCorrection":true,"error":{"code":"FBS_ATTRIBUTION_FIELDS_MISSING","missingFields":["packageName","expertEntryId","packageVersion"],"requiredFields":["productId","packageName","expertEntryId","packageVersion"]}}
```

三个错误字段也可能在顶层冗余；两处冲突时停止。只有错误码精确一致、缺失字段合法、服务明确未接受、允许身份补正、用户仍允许该工具且本逻辑操作尚未补正，才可继续：

- `skill_whoami`：用本轮真实加载身份补齐SDK实际参数，最多再调用一次。
- `fbs_scene_pack_query`：仅当上一跳完整原始 `actionEnvelope.toolArguments` 的产品包ID与加载身份一致时，重新完整传递该原对象；不得改写已封印参数来补身份。原信封本身缺少服务要求的产品标识或其它必要参数则停止。
- `skill_consume`、激活、完结、登出和奖励写入不自动补正重试。超时、丢回执、业务已接受或结果未知都不属于上述例外；保留原业务号并按原合同回读。

计数只留在当前对话/操作上下文，不为计数写记忆文件。一次补正后再失败立即停，不换号、不扩大工具集合、不把再次ToolSearch或新对话包装成无限重试。

## 旧API2与legacy上游的归因解释

从实际响应JSON的 `attribution` 读取四字段、`identityTrust`和三个信用布尔值。null表示未知；缺失或类型不符时不推定成功。先比较本轮声明与服务回显，冲突就保持冲突并停止依赖归因的写入。

`server_registered_route`只是服务登记路由，`source_bound_route_unverified`是声明路由，`server_registered_identity_no_route`仅登记身份，`untrusted_or_unknown`仍未知。仅凭这些枚举、相同binding或HTTP成功，不能说已认证账号或专家。它们不是新七工具的identityTrust枚举；信用flags不由模型改true。

服务若同时给出 `accountAuthenticationProven:false` / `hostExecutionProven:false`，原样理解为对应能力未证明；不能拿其它路由字段抵消。`FBS_TOOL_NOT_IMPLEMENTED`表示未实现的能力，不属于缺字段补正，不换工具或代理另一后台绕过。

## OAuth Gateway的账号与声明来源

已审核且本轮有效的OAuth资源，新七工具在text/structuredContent中给独立的accountAuthenticationProven与accountIdentityTrust。仅当实际结果明确为true / oauth_resource_verified，才可说明本次福帮手账号授权已校验；这不等于自然人实名。attribution.identityTrust是client_declared或unknown，描述产品声明；hostExecutionProven及自然/产品信用仍为false，不能用账号认证提升专家来源。

条件开放的legacy core3保持上游原结果形状。其账号绑定所有权信号在MCP结果的`_meta["fbs.gateway/ownership"]`，不在旧匿名binding里。只有实际可观察到该层的accountAuthenticationProven/bindingOwnerVerified才记录它；宿主未暴露_meta时保持该层未观察。上游路由、Gateway账号所有权和宿主执行分别解释，不能互相覆盖。

新五个profile工具的未决写使用operationId，网页expectedVersion不是其输入；不将上述仅适用于whoami/scene的一次补正扩为画像写入重试。完整参数见[画像协议](../../fbs-profile/references/profile-purpose-and-provenance.md)。

## 团队只声明实际参与

只有当前schema明确开放时，才发送 `participantExpertIds`、`collaborationMode`、`handoffFrom`、`handoffTo`。当前合同上限16个唯一合法ID，participants不含主agent；模式仅 `single/parallel/sequential/delegated/handoff/unknown`。未发生/未观察派发时用空列表与unknown（未开放字段则省略），不能按团型或名单推成delegated。显式single要求无additional participant；parallel/sequential/delegated至少有一个本轮实际参与者。handoff两端同时提供、不同且属于主agent或实际participants，mode必须为handoff。

成员列表来自本次实际执行记录，不从专家团包的角色名单补全。用户要求某角色参与，也不等于它已经参与。`teamId`、`canonicalTeamId`、`primaryExpertId`由服务从身份派生，不作为客户端输入；不发送旧别名 `expertIds`。字段尚未开放就保持未观察，不能塞进额外对象。

真实团内派发/回传后才可带实际子集与delegated；成员参数被拒绝时停止并核对原执行记录，不自动改成其它模式或删成员来绕过校验。

共享连接器的成员声明仍是client-declared，不构成逐成员执行证明。只由主服务链记录同一成果，不按席位重复whoami/consume、重复收费或多算客户。读取schema或写这些说明都不证明宿主实际发送了成员参数。

## 按需协作与关系边界

知识社交、主理人空间、组织和社群只在用户当前事项需要时选择专家，不强制三专家流水线。使用关系、组织角色、资源权限、服务权益和画像用途同意分别核对。访客、报名、OAuth账号都不能自动升级为自然人实名、组织成员或资源权限；关系通过本人主动授权、报名或需求及相应服务回执建立。

画像同意不包含联系许可；本合同不启用外发消息，不把主理人个人企微凭据共享给多人应用。公共应用、个人空间产品和定价仍是待确认建议，不写成已上线能力，也不自动创建销售线索。
