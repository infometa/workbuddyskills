# 产品身份与 2026.9.20 待核映射

本表记录2026-09-20审查的公开列表与本机市场缓存，不把缓存、已安装登记和本次实际加载混为一体。专家/专家团之外另列 fbs-bookwriter Skill；连接器是传输产品，不借用任一专家身份。原2026.9.10服务映射仅作历史核对，不能因静态清单自动扩展；当前调用还须通过本候选的版本/schema准入。

本表是历史产品映射，不是当前 OAuth 画像准入白名单。当前 canonical 源码快照的四产品/版本见[机器合同](identity-contract.json)的 resourceProfiles.canonicalProfileGateway.acceptedExpertVersions；它不是新版本准入回执。172a425 的三产品限制只属于 historicalPreviewGateway。研究员后继等新版本须按原值验证，不能借用旧版本或另一专家身份。没有已加载专家来源时，账号级 member_whoami/fbs_capabilities 与需要完整四字段的五个 profile 工具分别处理。

公开列表的董秘助手 `git:fbsir-board-assistant:fbsir-board-assistant`、智能原生案例研究员 `git:fbsir-industry-scene-expert:fbsir-industry-scene-expert` 与下列缓存包ID不同。没有迁移或别名回执，统一标记 `identity_mapping_unverified`；不因中文名称相同或版本不同就合并。

| 专家产品 | `productId` / `packageName` | `serviceProductId` | 已确认入口/字段 | 当前连接器状态 |
| --- | --- | --- | --- | --- |
| AIGC 合规红队 | `fbsir-aigc-compliance-red-team` | 未确认 | 有值时透传 `entryId`、`entrySurface`、`intentFamily`、`assetType` | `registered_no_route`；待当前 schema/registry |
| 备课易 | `fbsir-beike-yi` | 未确认 | 无服务入口字段被本次研究确认 | `registered_no_route`；保持本地首值 |
| 董秘助手 | 缓存 `fbsir-board-secretary-assistant`；公开 `fbsir-board-assistant` | 未确认 | 分别保留原始ID，不互相改名 | `identity_mapping_unverified`；旧缓存不证明当前公开条目身份 |
| 独董会 | `fbsir-eight-seat-board` | `fbsir-eight-seat-board`（26.8.20 已声明） | `expertEntryId=board-convener`、`channelTrack=official_experts` | 待 current registry/宿主回读，不由本地 eventId 晋级 |
| 智能原生案例研究员 | 缓存 `fbsir-industry-scene-researcher`；公开 `fbsir-industry-scene-expert` | `workbuddy_industry_scene_researcher` 仅为旧合同值 | 历史 `entryId=genius-industry-scene-researcher`、`intentFamily=genius_partner` 不回填当前未知入口 | `identity_mapping_unverified`；须核对真实加载包和映射 |
| 实习生 | `fbsir-internship` | 未确认 | 本地交付日志不是服务遥测 | `registered_no_route`；不补发历史事件 |
| 妈妈对话 | `fbsir-mom-dialogue-expert` | 未确认 | 家庭作品和媒体字段不进入归因参数 | `registered_no_route`；保持本地优先 |
| 超级独董会 | `fbsir-super-independent-board` | 未确认 | 只传本次已核验的包/入口/版本；保留福帮手、企业微信、腾讯会议企业微信版三授权及产品降级合同 | 当前服务实际返回为准；不以共享连接器证明宿主专家 |
| 自适应成果交付专家 | 缓存 `fbsir-super-partner` | `workbuddy_super_partner_expert` 仅为旧合同值 | 历史 `workbuddy_super_partner_group` 保持独立 | 核对实际加载；不从展示改名推导当前路由 |
| 产业园招商 | `industrial-park-investment-attraction-expert` | 未确认 | 本地研究摘要不是企业意向；CRM 交接需独立授权 | `registered_no_route` |
| 留学研学 | `liuxue-yanxue-expert` | `workbuddy_liuxue_yanxue_expert`（26.8.20 已声明） | `expertEntryId=liuxue-yanxue-expert`、`channelTrack=study_abroad_study_tour`、`entryId=liuxue-yanxue-dual-track`、`entryPromptCode=wb_qp_liuxue_yanxue_dual_track_48h`、`entrySurface=workbuddy_expert_center`、`scenePackId=liuxue_yanxue_dual_track` | 首批联调；字段仍服从当前 `tools/list` |
| 长文档专家 | `long-manuscript-expert` | `workbuddy_long_manuscript_expert`（26.8.20 已声明） | `expertEntryId=long-manuscript-expert`、`channelTrack=long_manuscript_expert` | 首批 provider binding 联调；保留已有项目 |
| 秘宝媒体归档 | `mibao-media-archivist` | 未确认 | 只在另行授权增强时传最小引用；不传媒体路径或原件 | `registered_no_route`；本地媒体内核优先 |
| 贴图头条 | `tietu-toutiao` | 未确认 | 作品计划/候选/集合摘要属于本地工作流；企微 webhook 独立 | `registered_no_route`；投递不算 FBS 消费 |
| fbs-bookwriter（Skill，观察版本3.0.1） | `fbs-bookwriter` | 未确认 | 使用真实 Skill 类型/版本；不得填成长文档专家或专家团 | 当前会员模型仅agent/team；独立Skill权益需新增合同，未在本Gateway开放 |

## 使用规则

默认正式入口以实际清单name（产品包ID）为主键。表中版本仅表示历史观测，不是准入白名单；服务登记覆盖当前14个运行时产品包，包版本升级不需要更换产品ID。仅有包ID不授予账号或业务权限。

- productId、packageName、skillId、入口和版本只使用本次真实 manifest/宿主可核字段，且仅在 schema 支持时传入。表内缓存/公开ID不是可二选一的调用参数；待核映射不猜补。
- 不把 `my_expert` 等通用入口名当成具体产品身份。
- 服务端返回的规范化身份是当前调用结果；若其与输入不同，按未知/降级处理并停止依赖归因的写操作。
- 映射只服务于内部工具参数。用户可见回复使用中文产品名，不展示这些机器字段。
- `registered_no_route` 是服务的登记/路由状态。静态登记、已选业务路由与宿主真实执行分别验证；服务未返回可用下一步时不自动调用增强。
- 本表不改写服务端历史 registry 或旧回执；历史产品仍按对应合同核对。专家团子角色不计成独立客户，连接器成功不计成某个专家的真实使用。
- 意图未知不补 general，字段缺失不补 natural 或信用标签；版本轴和投影差异按 [字段与传输规则](../../fbs-connector/references/field-trust-and-transport.md) 处理。
