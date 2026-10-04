---
name: qiqi-cli
description: 使用已就绪的 qiqi 命令处理企企服务业ERP通用工作。需要核对身份与 profile、发现对象和字段、查询记录、聚合统计或工作视图、处理分页和大输出、执行单据或审批动作、删除记录、处理附件，或核查结果不明确的写入时使用。
description_zh: "企企服务业ERP的通用业务入口与能力总览：贯通客户与合同、项目执行、费用与收入、订单、收付款、财务核算与经营分析，支持业务查询核对，以及任务管理、工时登记、单据审批等跨领域日常操作；专项业务域可由对应 Skill 进一步深化。"
description_en: "Serves as the general business entry point and capability overview for 77Hub ERP, spanning customers and contracts, project execution, expenses and revenue, orders, receipts and payments, financial accounting, and operational analysis. It supports cross-domain daily work such as business data queries and reconciliation, task management, time entry, and document approval, while dedicated Skills provide deeper guidance for specific business domains."
version: "1.0.0"
author: "77Hub"
---

# 企企服务业ERP qiqi

## 适用边界

本 Skill 处理已就绪的 `qiqi`。首次安装、升级、重装、CLI 缺失或登录授权由当前宿主的 Connector 生命周期处理；没有 Connector 托管时由 `qiqi-cli-installation` 处理。CLI 与授权就绪后，再回到本 Skill 执行身份、查询和业务请求。

本 Skill 只生成 `query` 查询命令。如果当前 binary 把 `query` 报告为未知根命令，先执行 `qiqi --version` 记录版本，再按已确认的最低支持版本引导升级；不得自动改用旧兼容根命令，也不得擅自切换 production/internal 渠道。首个支持版本尚未由正式产物确认时，本 Skill 的改版不得先行发布。

## 权威边界

把当前 qiqi 作为能力和语法权威：

1. 当前命令及参数以 `qiqi --help` 和目标叶子命令帮助为准。
2. 当前企业下的对象、字段、候选值、视图和动作以 `objects`、`describe`、`query values` 与实际返回为准；字段类型和操作符范围由服务端 metadata 决定，公共 CLI 语法不代表每个字段全部支持。
3. 本技能只定义通用能力选择、证据判断和安全执行规则，不预设用户必须加载其它技能，也不把示例当成完整命令契约。
4. 用户意图决定要完成什么，当前 qiqi 能力决定现在能否完成；二者不一致时停止操作并说明差异。

## 按需检查点

以下检查点按任务条件触发，不是每次都要完整执行的线性流程。目标和命令都明确的简单只读任务可以直接走最短路径，例如：确认 profile 后执行 `records get`，再解释返回结果。


| 触发条件                      | 必要检查                                                     |
| ------------------------- | -------------------------------------------------------- |
| 业务授权失败、profile 不明确或身份发生变化 | 用 `auth status` 在线核对当前企业和用户；优先为业务命令显式传递 `--profile`      |
| 命令、对象、字段、值、视图或动作不明确       | 读取对应 `--help`，并按需使用 `objects`、`describe` 或 `query values` |
| 名称、单号、人员或记录不唯一            | 先取得候选并消歧；写入必须使用稳定 `RecordRef`、唯一编码或可验证关系                 |
| 需要完整集合或统计                 | 明细全集走分页 `query list`；合计/分组/度量互比走 `query aggregate`，不能用第一页或本地加总代替 |
| 执行动作、删除或附件上传/删除           | 核对身份、稳定目标、用户意图和关键影响，只执行一次最小操作                            |
| 写入超时、连接中断或返回不明确           | 标记“状态未知”，先读取业务事实核查，不直接重试                                 |


任何任务都应按返回证据报告已确认事实、推导、状态未知和能力缺口，但不需要为了形式而重复执行与当前任务无关的发现步骤。

## 能力路由


| 意图 | 优先使用 |
| --- | --- |
| 查看或核对身份 | `auth list`、`auth status` |
| 发现对象类型 | `objects` |
| 查看字段类型和时间语义 | `describe fields` |
| 查看通用字段和少量数据样例 | `describe list` |
| 按跨对象文本寻找候选 | `seek` |
| 按对象和条件查询记录 | `query list` |
| 合计、分组统计或度量互比 | `query aggregate` |
| 查找枚举或引用候选值 | `query values` |
| 使用工作台预置视图查询 | 先 `describe view` 了解当前有哪些视图，匹配后再 `query view` |
| 读取、删除业务记录，或对该记录执行提交、审批及其它业务动作 | `records get`、`records delete`、`describe actions`、`do-action` |
| 处理附件 | `records attachments list/url/upload/delete` |
| 执行专用 业务命令 | 从 `qiqi --help` 的「业务命令」起，按父命令 `--help` 逐级发现叶子命令后再执行 |

`query list` 是按对象构造条件的通用查询入口。需要合计、分组或度量互比时用 `query aggregate`，不要拉分页明细再本地加总。工作台预置视图（如「我的单据」「待我审批」）先 `describe view` 再匹配执行；未匹配不要猜测 `viewId`，也不要按对象逐个 `query list` 去复现同一视图。

这些是用户可复制的 CLI 命令；底层 Gateway wire 仍使用 `operation=find` 和既有 mode。不要据此生成 `operation=query`，也不要把内部协议名重新暴露为用户命令。

提交、撤回、同意、驳回等是当前业务记录上的动作，走 `describe actions` 与 `do-action`。收到 `BUSINESS_WARNING` 时先展示警告，用户确认后再加 `--ignore-warn` 重试，不得自动补开关。当前 profile 未公开对应命令时，说明能力缺口，不构造替代请求。

## 读取与输出纪律

- qiqi 的文本输入、输出重定向和本地 JSON 文件统一使用 UTF-8。终端出现乱码时先将宿主终端的输入输出编码切换为 UTF-8，再重新执行只读操作；不得通过丢弃、替换或猜测字符掩盖编码问题。
- 内部查询、字段选择和结果核对保留对象与字段的 `apiName`；面向用户说明时优先使用当前元数据返回的对象标题和字段标题，减少无必要的技术名称。
- 标题缺失或不唯一、需要复现命令或排查错误、用户明确询问技术名称时，可以同时展示标题与 `apiName`。不得自行翻译标题或根据标题猜测 `apiName`。
- 消歧、写入确认和结果核查仍应按需展示唯一业务编码或 `RecordRef`，不能为了简化输出而删除证明记录身份的信息。
- `describe list` 的样例和 `seek` 的候选都不是全集或唯一性证明。
- 需要完整集合时持续读取分页（offset/limit/total），直到返回明确表示没有下一页（hasMore）；不能用第一页推断总量。合计、分组或度量互比使用 `query aggregate`，不要用局部列表假装全量汇总。
- 收到 `77hub.large-output` 时，打开 `uri` 或读取 `path` 指向的完整 JSON；`summary` 只用于定位主集合和分页，不能用于完整分析。
- 没有查到可能来自筛选、权限、对象未接入或数据不存在。没有额外证据时只报告“当前范围未查到”。

## 写入纪律

执行前确认当前企业、用户、稳定目标、动作和关键影响。用户已经明确授权同一目标与动作时不重复提问；目标不唯一、范围扩大或破坏性影响不清楚时先消歧。

- qiqi 已提供专用业务命令时，不用名称相近的通用动作代替。
- 删除必须先理解预检查结果；只有用户明确要求删除且目标已确认时才使用 `--yes`。
- 命令或动作定义过期时，重新读取当前帮助或动作描述，重新检查参数和影响；不得静默重放旧请求。
- 写调用超时、连接中断或返回不明确时标记为“状态未知”，优先按稳定引用、唯一编码或用户给出的业务事实核查；没有确认前不得盲目重试。
- 同一意图若用新记录替代，仍有效的旧记录必须处理或向用户声明遗留，不得只追加新记录。

## 按需读取

- 需要确认 qiqi、profile 或解释错误时，读取 [runtime-context.md](references/runtime-context.md)。
- 需要发现对象、字段、候选值、视图或单记录时，读取 [object-discovery.md](references/object-discovery.md)。
- 需要查询记录列表、构造过滤条件、使用结构化 input 文件或 stdin、排序分页或判断查询完整性时，读取 [list-query.md](references/list-query.md)。
- 需要合计、分组统计、度量互比或使用聚合 input 文件或 stdin 时，读取 [aggregate-query.md](references/aggregate-query.md)。
- 需要解释或传递时间值时，读取 [temporal-values.md](references/temporal-values.md)。
- 需要提交、撤回、删除或处理未知写入结果时，读取 [actions-and-recovery.md](references/actions-and-recovery.md)。
- 需要处理待审批事项或附件时，读取 [approvals-and-attachments.md](references/approvals-and-attachments.md)。

只读取当前任务需要的引用文件。
