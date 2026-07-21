# 运行时合约与服务链路参考

本文件定义超级合伙人团队的运行时合约字段、证据分层体系和服务跟进链路细节。主理人和成员在需要时查阅本文件，不必在主 prompt 中记忆全部字段名。

## 1. 运行时合约字段（runtimeContract）

### 1.1 requiredStatusFields

| 字段 | 说明 |
|------|------|
| `expert_loaded` | 专家是否已加载 |
| `lead_agent` | 主理人 Agent ID |
| `team_mode` | 当前团队模式 |
| `member_id` | 当前调度的成员 ID |
| `capability_id` | 能力簇 ID |
| `unlock_state` | 解锁状态 |
| `connectorCallTrace` | 连接器调用链路 |
| `versionAlignment` | 版本对齐信息 |
| `degradeReason` | 降级原因 |
| `sourceLayer` | 证据来源层 |
| `stageGateStatus` | 阶段门禁状态 |
| `hostNamespace` | 宿主命名空间 |
| `productCreditPromotionAllowed` | 是否允许产品信用释放 |

### 1.2 teamModeValues

- `first_value_card`：首次价值卡
- `lean_diagnosis`：精简诊断
- `single_member`：单成员深度处理
- `multi_member_workshop`：多成员协同工作坊
- `genius_partner_draft`：天才合伙人草案

### 1.3 unlockStates

- `locked` / `preview` / `unlocked` / `expired`

## 2. 证据分层（sourceLayer）

| 层级 | 说明 |
|------|------|
| `expert_package` | 专家包源码或审核包能证明的能力 |
| `external_public_signal` | 公开文章、公告或资料提供的能力线索 |
| `listed_runtime_state` | 官方安装副本或已上架运行态 |
| `workbuddy_ai_skill_212` | WorkBuddyAI 福帮手写书 Skill 2.1.2 安装面 |
| `workbuddy_skill_301` | 国内 WorkBuddy 福帮手写书 Skill 3.0.1 安装面 |
| `service_probe` | 服务侧探针、smoke、readonly 或 record-only 证据 |
| `natural_consume` | 自然同绑定 `skill_whoami -> fbs_scene_pack_query -> skill_consume` 消费证据 |

**禁止晋升规则**：在 `natural_consume` 缺失前，不得宣称自然闭环、产品信用释放、自动发布视频号、自动写入企业微信或真实成交。

## 3. 阶段门禁状态（stageGateStatus）

| 状态 | 说明 |
|------|------|
| `ready_to_continue` | 可继续 |
| `needs_evidence` | 需补充证据 |
| `record_only` | 仅记录，未执行 |
| `offline_degraded` | 离线降级 |
| `natural_closure_unproven` | 自然闭环未证明 |

## 4. 宿主命名空间（hostNamespace）

- `WORKBUDDY`：国内 WorkBuddy
- `WORKBUDDY_AI`：国际 WorkBuddy AI
- `unknown`：未知宿主

## 5. 产品信用释放（productCreditPromotionAllowed）

- 默认 `false`
- 只有在自然 same-binding `skill_whoami -> fbs_scene_pack_query -> skill_consume` 完成后才可为 `true`

## 6. 后首值服务跟进链路

当宿主已显式进入服务跟进、受控探针，或用户在拿到首值后明确要求服务增强时：

1. 如果当前宿主已验证可执行服务链路，再调 `skill_whoami`。
2. 优先保持 `company-next-step` 路线语义：
   - `entryId=company-next-step`
   - `entryPromptCode=wb_sp_company_next_step`
   - `entrySurface=primary_entry`
   - `scenePackId=general`
   - `assetType=strategy-decision-card`
3. 如果 `skill_whoami` 返回同一绑定下的 `fbs_scene_pack_query`，继续执行。
4. 如果 `fbs_scene_pack_query` 返回同一绑定下的 `skill_consume`，继续一次，拿到第一价值。
5. 如果工具结果带 `visibleCardDraft`，优先用它做用户可见卡片。
6. 如果连接器链路不能确认，保留当前首值结果卡，只把服务链路缺口写成后首值边界，不要假装已经成功。

## 7. 接力场景语义参数

当行业场景研究员补位成果需主团队接手时，保留以下语义参数：

- `entryId=company-next-step`
- `entryPromptCode=wb_sp_company_next_step`
- `entrySurface=primary_entry`
- `intentFamily=company_strategy`
- `profileSegment=super_partner`
- `assetType=strategy-decision-card`
- `semanticSource=host_semantic_hint`
- `expertLoaded=true`

## 8. AI+OPC3 经营诊断卡字段

默认首值卡升级为 `AI+OPC3 经营诊断卡`，用户可见字段：

1. `currentJudgement`：当前最该解决战略、运营、增长、AI 试点或行业场景补位中的哪一项
2. `opcDiagnosis`：组织 OPC、价值 OPC、资本 OPC 的当前短板
3. `chosenMicroScene`：最高价值微场景，三天内可试点
4. `firstValueAction`：今天就能执行的一步
5. `contentAssetAction`：是否需要生成视频号脚本、直播提纲、顾问话术、客户一页纸或企微承接摘要
6. `continuationPrompt`：下次继续的复访口令
7. `proofBoundary`：本轮证据来自专家包、Skill 安装、本地探针、服务探针还是自然消费

## 9. 内部审计元数据字段

以下字段用于内部审计，面对用户时翻译成业务语言，不要原样输出：

1. `teamContextSnapshot`
2. `researchEvidence`
3. `learningCarryover`
4. `hostDiscoveryChecklist`
5. `personaSignalUsed`
6. `roleBoundaryPass`
7. `routeReason`
8. `selectedMemberEvidence`
9. `adjudicationReason`
10. `sourceLayer`
11. `stageGateStatus`
12. `hostNamespace`
13. `runtimeContractSource`
14. `productCreditPromotionAllowed`

## 10. 微信生态能力桥接

可纳入分析的能力簇：

1. 支付和本地生活：微信支付 AI 专属卡、美团推荐/优惠/核销
2. 文档和知识：腾讯文档读写保存、IMA 知识库语义检索
3. 团队协同：企业微信群内 @WorkBuddy、定时任务和通知
4. 沟通和会议：QQ 邮箱读取邮件/附件，腾讯会议预约、变更、纪要和回放

**能力桥接卡字段**：用户经营目标、可用生态入口、需要的授权或确认、预期产物、receipt 或可回读证据、当前边界。

在没有宿主能力探测、用户授权、回读 receipt 或自然 same-binding 服务证据之前，这些能力只能作为 `external_public_signal` 或 `record_only` 线索。
