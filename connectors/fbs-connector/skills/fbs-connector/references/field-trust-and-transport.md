# 字段、信任、失败与传输边界

## 运行时真源

每次会话先核对宿主本轮 ToolSearch/实际暴露清单对应的 `tools/list`。不要求模型伪造原始协议调用。发行时保存的 schema、本文档和服务描述不能增加当前不存在的参数；新域还必须满足 [capability-routing](capability-routing.md) 的审定合同门。

字段仅在三项同时成立时发送：调用方确实掌握；来源允许用于该目的；当前 input schema 接受。`additionalProperties=false` 时禁止试探额外字段。

## 动态字段

旧业务字段包括产品/包/入口、渠道、意图、交互、场景、binding和幂等材料；不把这些整包复制到新profile工具。`attributionContext`、`installInstanceId`或任意账户主体覆盖不是新Gateway输入。认证账户由OAuth服务验证；profile参数按[实际协议](../../fbs-profile/references/profile-purpose-and-provenance.md)，不能补userId/subject/grant或旧会话材料。

产品、包名、专家入口和专家版本只来自本次实际加载且可核验的 manifest/宿主字段；静态产品表、候选目标版本和旧记忆不证明本次加载。canonical 旧业务合同以清单 name 对应的产品包ID识别登记产品；在其 schema 允许时未知版本可省略。七个 OAuth 工具一旦声明专家则校验完整四元组与当前版本准入，五个 profile 工具不能省略未知版本或假填旧值。升级不改变产品身份。成员入口用于区分同一包内的专家，可选字段按schema省略。连接器版本不填入packageVersion/expertPackageVersion，不能套用邻近产品或缓存版本。具体规则见[身份与权限](../../fbs-mainline/references/identity-and-permission.md)。

意图须来自本次明确请求和合同允许的分类，不能以服务默认 general 或高非空率冒充已识别意图。日志字段缺失可能来自生产者/查询器投影差异，模型不得补 natural、可信来源或产品信用标签。探针只用真实测试载体提供的标记；自然/业务分类由独立服务证据判定，不由 Skill 自证。

未知、冲突和不适用必须分开：

- `unknown`：字段适用但没有可靠值。
- `not_applicable`：本动作不属于该业务域。
- `conflict`：声明、登记或服务规范化结果不一致。

客户端声明、工具可见、登记匹配、账号认证和事实确认是不同证据，不组成自动升级阶梯。新Gateway的oauth_resource_verified只属于账号授权；client_declared仍未证明专家执行，ACCOUNT_OWNER也不提升sourceEvidenceTrust。读取回执仅表示服务准备结果。

## 凭证来源

- `accessCode`：用户为当前激活步骤明确提供。
- `sessionRef` / `sessionToken`：服务端在同一授权业务链返回，或当前 schema 接受且来源可验证。
- 乐包凭证：同一 issuer 产生的完整 voucher、nonce、payload 和 signature。
- MCP session、SSE event ID、JSON-RPC request ID、trace、匿名 hash 和 server binding 均不是账户认证凭证。

上述访问码/旧会话/奖励材料仅限旧资源确实接受它们的对应步骤。OAuth Gateway的legacy桥禁止调用方提供accessCode、sessionRef/sessionToken等覆盖字段；Bearer由宿主管理且不得透传到下游。任何凭据都不进入回复、调试输出、归因事件或持久研究报告。

## 失败和重试

| 动作 | 策略 |
| --- | --- |
| discovery / `tools/list` | 仅在宿主实际支持时做有界只读重试；保留次数和总预算 |
| `skill_whoami` / 场景读取 | 不重放未决请求；仅FBS_ATTRIBUTION_FIELDS_MISSING且明确未接受/允许补正时，按身份合同最多一次只读纠正 |
| `skill_consume` | 超时/丢响应保留同一binding、真实成果和原幂等键；先按服务已有状态工具及原参数回读，明确可继续后才沿用原键；无安全回读能力则停止自动动作 |
| activate / finish / logout | 丢响应保持未决；不自动重放，先确认状态和用户意图 |
| claim / redeem | 不自动重试；先按同一 binding 查询状态 |
| profile_manage_entry / profile_propose | 服务已接受或响应未知时保留原operationId及载荷，先查当前grant回执；不改号，不塞expectedVersion |
| profile_read | 当前用途下最小字段；每次成功有新auditOperationId，不写业务正文/不扣费；截断时按更小字段重读，不冒充先前结果已被完整读取 |

HTTP 200、SSE 建连或 JSON-RPC 成功包络均不能替代工具和业务成功字段。`timeout=60000` 是连接配置，不是所有工具或长流生命周期的统一预算。

新域能力的发现、响应预算和未决操作另按 [response-and-error-contract](response-and-error-contract.md)；旧 action envelope 原样传递，不因摘要预算裁剪参数。

## 版本轴

- connector package：`2026.9.25-r7`
- connector contract header：`1.3.0`（不替代专家版本）
- expert package：各专家自己的当前版本
- host、MCP protocol 和 service release：由各自运行时事实产生

这些字段不得互相推导或填充。

本候选没有新的公开生产准入结论；历史生产拒绝与隔离验证按各自时点记录，见[capability-routing](capability-routing.md)。不得改写包头冒充26.8.20或2026.9.10；原址、包版本与legacy合同头分别保持真实声明。
