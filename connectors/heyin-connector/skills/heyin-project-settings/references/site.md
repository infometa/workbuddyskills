# 中心设置

按 [项目设置技能](../SKILL.md) 核对项目和凭证后使用本文。示例中的凭证、项目、中心和版本 ID 均需替换为实际查询结果。

查询中心、方案版本和知情同意书模板需要 `PRJ_SETTINGS_SITE_ACCESS`；查询创建默认配置、医院候选及全部中心写操作（含删除演练）需要 `PRJ_SETTINGS_SITE_EDIT`。

## 功能总览

| 功能 | 说明 | 可修改 |
| --- | --- | --- |
| 查询中心 | 分页获取生产或测试中心及其配置、状态和数据进度 | 否 |
| 查询创建与配置候选 | 获取新建默认配置、医院候选、可用方案版本和知情同意书模板 | 否 |
| 维护中心配置 | 创建中心，更新单个或多个中心，应用方案或知情同意书模板，调整排序 | 是 |
| 管理中心状态 | 锁定、解锁、关闭、撤销关闭、暂停或恢复中心 | 是 |
| 删除中心 | 演练并删除中心及其关联业务数据 | 是，不可恢复 |

## 查询中心与配置候选（只读）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 获取中心列表 | `GET` | `/api/project/settings/site/list_site/` | `--query`：`special` = 空字符串或 `TEST`（可选，省略表示生产中心）；`limit` = 10–100（必填）；`offset` = 非负分页偏移（可选）；`keyword` = 匹配中心名称的关键词（可选，最长 16） |
| 获取新建中心默认配置 | `GET` | `/api/project/settings/site/creation_default_info/` | `--query`：`special` = 空字符串或 `TEST`（可选，省略表示生产中心） |
| 检索医院名称 | `GET` | `/api/project/settings/site/search_hospital_name/` | `--query`：`keyword` = 医院名称或别名关键词（必填，最长 16） |
| 获取方案版本列表 | `GET` | `/api/project/settings/site/list_meta_data_version/` | `--query`：`site_ids` = 同项目同类型的中心 ID 数组（批量场景可选）；`site_id` = 单个中心 ID（单中心场景可选）；`special` = 空字符串或 `TEST`（按类型查询时可选） |
| 获取知情同意书模板列表 | `GET` | `/api/project/settings/site/list_consent_tpl/` | `--query`：`site_ids` = 同项目同类型的中心 ID 数组（批量场景可选）；`site_id` = 单个中心 ID（单中心场景可选）；`special` = 空字符串或 `TEST`（按类型查询时可选） |

需要完整结果时，将 `req --query` 的 JSON 对象中的 `offset` 逐次增加实际返回的记录数，直到读取数量达到 `total`；尚未读完却返回空页时报告结果不完整。生产与测试中心需要分别查询，不能把一类的结果当成全部中心。

查询创建默认值或医院时，使用对应路径及表中参数。批量应用方案前，先针对完全相同的中心集合查询候选：

```sh
heyincli req --token-id <token-id> --method GET \
  --path '/api/project/settings/site/list_meta_data_version/' \
  --query '{"site_ids":[12,18]}'
```

### 只读接口返回内容

| 接口 | 业务返回内容 | 定义 |
| --- | --- | --- |
| 获取中心列表 | 必填的 `list`（`Site[]`）和 `total`（integer） | 指定中心类型的分页结果，按 `ranking` 升序返回；关键词只匹配中心名称。 |
| 获取新建中心默认配置 | `sn`、`patient_sn_prefix`、`patient_sn_digit` | 当前中心类型下一条建议中心编号和默认研究参与者编号规则；只表示建议值，不表示中心已创建。 |
| 检索医院名称 | 必填的 `hospitals`（`Hospital[]`） | 按名称或别名匹配的医院候选，最多 10 条。 |
| 获取方案版本列表 | 必填的 `list`（`MetaDataVersion[]`） | 当前范围内可选的已发布方案版本，按 ID 降序返回。 |
| 获取知情同意书模板列表 | 必填的 `list`（`ConsentTpl[]`） | 当前范围内可选的知情同意书模板，按 ID 降序返回；项目未启用知情同意时返回空列表。 |

`Site` 的核心属性如下：

| 属性 | 类型 | 定义 |
| --- | --- | --- |
| `id` | integer | 中心 ID，是更新、排序、状态流转和删除的唯一定位依据。 |
| `special` | string | 空字符串表示生产中心，`TEST` 表示测试中心。 |
| `number`、`sn`、`name`、`ranking` | integer / string | 中心顺序号、业务编号、名称和在同类型中心内的排序。 |
| `status` | string | `STARTED`、`ENROLLING`、`FINISH_ENROLLMENT`、`LOCKED`、`CLOSED` 或 `SUSPENDED`。 |
| `meta_data_version_id`、`meta_data_version` | integer / object | 当前方案版本 ID 及摘要。 |
| `consent_tpl_id`、`consent_tpl` | integer / object | 当前知情同意书模板 ID 及摘要。 |
| `planned_sample_size`、`is_over_enroll_allowed` | integer / boolean | 计划入组数量及达到计划后是否允许继续入组。 |
| `patient_sn_prefix`、`patient_sn_digit` | string / integer | 研究参与者自动编号前缀和位数。 |
| `is_disabled` | boolean | 中心是否被禁用；被禁用中心不能作为状态流转或写操作的正常目标。 |
| `is_entering`、`is_committed`、`is_sdv`、`is_data_frozen`、`is_sd_frozen`、`is_dm_reviewed`、`is_mm_reviewed`、`is_safety_reviewed`、`is_med_encoded`、`is_data_locked`、`is_sd_locked`、`is_data_signed`、`is_sd_signed` | boolean | 平台维护的数据进度与审核投影，只用于反馈当前状态，不作为授权或删除影响的推断依据。 |
| `count_*` 系列字段 | integer | 字段、质疑、表单、事件和研究参与者数量统计，只用于展示实际返回的汇总值。 |
| `data_signature_*`、`sd_signature_*` | string / integer / datetime | EDC 与 SD 电子签名状态及签署人投影；属于敏感字段，默认不向用户展开签署人账号等细节。 |

医院候选包含 `id`、`name`、`alias`、`operation_type`、`type` 和 `level`。候选名称相似或不能唯一匹配时必须让用户选择，不能自行挑选；创建中心只提交用户最终确认的中心名称，不把医院 ID 自动当作中心 ID。

方案版本与知情同意书模板的查询范围优先级都是 `site_ids` > `site_id` > `special`。不要同时提交多个相互冲突的范围：

- 使用 `site_ids` 时，所有中心必须属于当前项目且同为生产或测试中心。方案列表只返回 ID 严格大于这些中心当前最小方案版本 ID 的版本；模板列表只返回 ID 严格大于这些中心当前最小模板 ID 的模板。
- 使用 `site_id` 时，以该中心的类型决定候选范围。方案列表不按当前版本 ID 截断；模板列表包含当前模板及更高模板。
- 仅使用 `special` 时，空字符串表示生产中心，`TEST` 表示测试中心。生产中心只可选已发布的正式方案和已发布模板；测试中心可选已发布的草稿方案，也可选草稿或已发布模板。
- `site_ids`、`site_id` 和 `special` 都不提交时，平台按生产中心处理；不能把省略范围理解为“全项目所有中心类型”。

知情同意书模板响应含正文 `content`。只使用选择模板所需的 ID、名称、发布日期和发布状态，不向用户输出完整正文，也不把正文带入无关上下文。

只使用平台实际返回的中心、方案版本、模板和医院候选 ID。空列表只表示本次读取没有匹配项；缺失、部分响应或请求失败不得补造为默认中心、版本、模板或医院。

## 维护中心配置（写）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 创建中心 | `POST` | `/api/project/settings/site/create_site/` | `--body`：`special` = 空字符串或 `TEST`（可选，省略表示生产中心）；<br>`name` = 中心名称（必填，最长 64）；<br>`sn` = 中心编号（必填，最长 32）；<br>`planned_sample_size` = 非负计划入组数；<br>`is_over_enroll_allowed` = 是否允许超额入组；<br>`patient_sn_prefix` = 自动编号前缀（必填，1–64）；<br>`patient_sn_digit` = 自动编号位数（必填，1–10）；<br>`meta_data_version_id`、`consent_tpl_id` = 相应候选列表实际返回的 ID（按项目配置选填） |
| 更新单个中心 | `POST` | `/api/project/settings/site/update_site/` | `--body`：`id` = 最新中心列表返回的中心 ID（必填）；`sn`、`name`、`planned_sample_size`、`is_over_enroll_allowed`、`patient_sn_prefix`、`patient_sn_digit`、`meta_data_version_id`、`consent_tpl_id` = 仅提交用户明确要求变化的字段；`is_need_re_sign` = 模板升级后是否要求已签署参与者重签 |
| 批量更新中心 | `POST` | `/api/project/settings/site/batch_update_site/` | `--body`：`ids` = 最新中心列表唯一定位、去重且非空的中心 ID 数组（必填）；`is_over_enroll_allowed` = 要应用到全部目标中心的目标布尔值（可选，执行修改时显式提交） |
| 批量应用方案版本 | `POST` | `/api/project/settings/site/batch_apply_meta_data_version/` | `--body`：`site_ids` = 同项目同类型中心 ID 数组（必填）；`meta_data_version_id` = 批量候选列表实际返回的方案版本 ID（必填） |
| 批量应用知情同意书模板 | `POST` | `/api/project/settings/site/batch_apply_consent_tpl/` | `--body`：`site_ids` = 同项目同类型中心 ID 数组（必填）；`consent_tpl_id` = 批量候选列表实际返回的模板 ID（必填）；`is_need_re_sign` = 是否把已签署参与者标记为待重签 |
| 调整中心排序 | `POST` | `/api/project/settings/site/rank_site/` | `--body`：`id` = 最新中心列表返回的中心 ID（必填）；`ranking` = 正整数目标排序（必填） |

### 调用示例

用户已授权修改后，更新单个中心只使用 `id` 和本次要修改的字段；不要把项目 ID 填到 `id`：

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/site/update_site/' --body '{"id":12,"planned_sample_size":150}'
```

对同项目、同类型的明确中心集合更新超额入组开关时，使用 `ids`：

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/site/batch_update_site/' --body '{"ids":[12,18],"is_over_enroll_allowed":true}'
```

批量应用候选方案使用 `site_ids`；`meta_data_version_id` 必须来自针对同一中心集合查询的候选结果：

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/site/batch_apply_meta_data_version/' \
  --body '{"site_ids":[12,18],"meta_data_version_id":45}'
```

其他配置请求按上表选择路径与字段。创建中心必须先获取默认配置及可选方案、模板，不能直接套用其他中心的编号和版本。

### 写接口返回内容

| 接口 | 业务返回内容 |
| --- | --- |
| 创建中心 | 新创建的 `Site` 对象。 |
| 更新单个或多个中心 | 无 |
| 批量应用方案版本或知情同意书模板 | 无 |
| 调整中心排序 | 无 |

除创建中心返回新对象外，写接口成功后仍必须回读中心列表确认；创建后也要按返回 ID 回读，不能仅凭请求成功推断最终状态。

`patient_sn_digit` 为整数 1–10。单中心更新的名称为 1–64 字符、编号为 1–32 字符、自动编号前缀为 1–64 字符，计划入组数和方案版本、模板 ID 均不得小于 0；各字段均可省略以保持原值。

### 创建与基础配置限制

- 创建前先获取对应 `special` 的新建默认配置，并分别查询可选方案版本和知情同意书模板。默认值是本次建议，不应复用旧值；创建时的名称、编号和研究参与者编号前缀在当前项目内必须唯一。
- 若当前类型存在可选方案，创建时必须选择其中一个；不存在可选方案时可不关联。生产中心只能使用已发布的正式方案，测试中心可以使用已发布的草稿方案。
- 项目未启用知情同意时，创建请求中的模板会被归一化为未关联；已启用且存在可选模板时必须选择有效模板。生产中心只能使用已发布模板，测试中心可使用草稿或已发布模板。
- 新中心在所属类型的末尾生成独立 `number` 和 `ranking`，初始状态为 `STARTED`。提交的 `sn` 与当前建议编号一致时视为自动编号；自定义编号会标记为手动编号。
- 创建还受项目可写状态、测试环境开关、中心容量和项目中心编号位数限制。平台拒绝时不能切换中心类型、缩短编号或删去方案与模板后盲目重试。

### 单个与批量更新限制

- 单个更新是部分更新，只发送用户明确要求变化的字段；没有实际变化会被平台拒绝。修改 `sn` 后该中心编号转为手动编号。名称、编号和研究参与者编号前缀仍须在项目内唯一。
- 方案版本和知情同意书模板只能升级，不能降级。项目未启用知情同意时，单中心提交的模板变更会被忽略；不要将成功响应解释为模板已更新。
- `is_need_re_sign=true` 只在从已有模板升级到更高模板时生效，将该中心下已签署的研究参与者标记为待重新签署。执行前必须向用户说明影响，并确认用户确实要求重签。
- 单中心修改研究参与者编号前缀或位数时，平台会尝试重算该中心下非手动编号参与者的编号；处于方案升级中的参与者会阻止操作。若目标编号与项目内既有编号冲突，对应参与者可能不会更新，因此必须把中心配置回读与参与者编号副作用区分报告，不能声称所有编号均已同步。
- 批量更新接口只开放 `ids` 和 `is_over_enroll_allowed`，把同一超额入组开关应用到全部目标中心；已有值相同的中心会被跳过。计划入组数、研究参与者编号前缀和位数须使用单中心更新接口，不能作为批量更新字段发送。
- 修改计划入组数可能在 `ENROLLING` 与 `FINISH_ENROLLMENT` 之间同步中心状态。变更后必须回读状态，不能只反馈计划值。

### 批量应用版本与排序

- 批量目标必须属于当前项目、具有相同 `special`，且每个中心和项目均可写。方案或模板 ID 必须来自针对完全相同中心集合查询得到的最新候选列表。
- 批量应用只升级版本。已关联相同或更高 ID 的中心会被静默跳过，其他中心才实际更新；写后必须逐个中心回读并区分“已升级”和“未变化”。
- 批量应用模板时，`is_need_re_sign=true` 只影响从已有较低模板升级的中心；首次关联模板的中心不会因此产生重签。平台写接口不返回受影响人数，不能虚构人数。
- 中心排序只在同一 `special` 内调整，并同步移动相邻中心。目标排序超过当前最大值时会被归一化到末尾；目标与当前排序相同时平台拒绝。写后应读取足够分页范围，确认目标中心及被连带移动中心的实际排序。

## 管理中心状态（写）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 | 允许的变更前状态 | 目标状态 |
| --- | --- | --- | --- | --- | --- |
| 锁定中心 | `POST` | `/api/project/settings/site/batch_lock_site/` | `--body`：`site_ids` = 中心 ID 数组 | `ENROLLING`、`FINISH_ENROLLMENT` | `LOCKED` |
| 解锁中心 | `POST` | `/api/project/settings/site/batch_unlock_site/` | `--body`：`site_ids` = 中心 ID 数组 | `LOCKED` | 锁定前状态；缺失时按入组进度计算 |
| 关闭中心 | `POST` | `/api/project/settings/site/batch_close_site/` | `--body`：`site_ids` = 中心 ID 数组 | `LOCKED` | `CLOSED` |
| 撤销关闭中心 | `POST` | `/api/project/settings/site/batch_cancel_close_site/` | `--body`：`site_ids` = 中心 ID 数组 | `CLOSED` | `LOCKED` |
| 暂停中心 | `POST` | `/api/project/settings/site/batch_suspend_site/` | `--body`：`site_ids` = 中心 ID 数组 | `STARTED`、`ENROLLING`、`FINISH_ENROLLMENT`、`LOCKED` | `SUSPENDED` |
| 恢复中心 | `POST` | `/api/project/settings/site/batch_resume_site/` | `--body`：`site_ids` = 中心 ID 数组 | `SUSPENDED` | 暂停前状态；缺失时按入组进度计算 |

中心状态对应研究中心的实施阶段：锁定通常在该中心数据清理完成、准备锁库时执行，关闭在中心关闭访视及文件归档完成后执行，暂停用于伦理或申办者要求暂停入组和研究操作。平台状态不代替伦理通知、关闭报告等线下流程，变更前确认相应依据。

状态操作使用 `site_ids`，即使只操作一个中心也传入数组。确认目标中心当前满足锁定条件、且用户已授权后，例如：

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/site/batch_lock_site/' --body '{"site_ids":[12,18]}'
```

所有状态接口的业务返回均为空。批量目标必须属于同一项目和同一 `special`，项目必须可写，中心不能被禁用。

状态接口只处理满足“允许的变更前状态”的中心，不满足条件的目标会被跳过，调用仍可能整体返回成功。执行前要展示每个中心的当前状态和预期状态；写后必须逐个回读并分别报告已变更、未变化或无法确认，绝不能把请求成功解释为全部中心都完成流转。

## 删除中心（不可恢复）

### 接口与强制流程

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 删除演练 | `POST` | `/api/project/settings/site/batch_delete_site_dry_run/` | `--body`：`ids` = 最新中心列表唯一定位、去重且非空的中心 ID 数组 | `to_delete_patient_count`，目标中心下将删除的研究参与者数量 |
| 正式删除 | `POST` | `/api/project/settings/site/batch_delete_site/` | `--body`：`ids` = 与演练完全相同的中心 ID 数组 | 无 |

删除演练与正式删除都使用 `ids`。先执行演练，不删除中心：

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/site/batch_delete_site_dry_run/' --body '{"ids":[12,18]}'
```

正式删除使用上表的 `batch_delete_site/` 路径及完全相同的 `ids`，仅在完成下列步骤后执行：

1. 从最新中心列表唯一解析目标，确认全部中心属于同一项目和同一 `special`，向用户展示中心名称、编号、ID、状态和类型。
2. 对完整、规范化后的 `ids` 执行删除演练。演练也需要 `PRJ_SETTINGS_SITE_EDIT` 权限，但不会删除数据。
3. 展示平台返回的 `to_delete_patient_count`，并明确说明该数字只统计研究参与者，不包含下面列出的其他级联对象。
4. 已有明确授权覆盖相同 ID 集合及演练揭示的删除和级联影响时，无需重复确认；否则展示影响并取得明确确认后，才执行正式删除。ID 集合、中心现状或上下文发生变化时必须重新演练。

删除会移除中心及其研究参与者、知情同意数据、EDC/SD 数据、事件与表单数据、ePRO、随访、监查问题、中心统计、照护用户关系和中心级角色分配；相关质疑会被系统关闭，eTMF 中心关联会移除且无其他中心关联的文件会进入清理。待回复邀请中引用这些中心的角色明细会被删除，已接受或已拒绝的邀请历史保留；空角色的待回复邀请记录可能继续存在。相关用户的角色上下文会失效，绑定条件被破坏的 API 令牌 可能被吊销。

正式删除会拒绝仍有研究参与者处于方案升级中的目标；存在参与者数据时还要求项目及中心允许研究参与者数据副作用。删除后同类型剩余中心会重新连续排序，生产中心删除还会重新计算项目入组状态。

删除没有恢复接口。正式删除成功后，必须持续分页读取对应 `special` 的中心列表，确认所有目标均已消失并核对剩余中心排序；回读失败或任一目标仍存在时报告“删除未确认生效”，不能重试正式删除。

## 结果核验

涉及研究参与者编号重算、知情同意重签或带参与者的中心删除时，项目和目标中心必须允许相应研究参与者数据变更，最终以平台校验为准。

创建、更新、应用版本、排序和状态流转后逐中心回读，分别报告已变更、未变化及无法确认的结果。展示中心 ID、名称、类型和本次变化所需的字段，不展开研究参与者身份或编号、签署人信息或知情同意书正文。删除演练人数不能用于推断其他级联对象数量。

少量变化可用“属性 / 变更前 / 变更后 / 结果”表格；批量变化逐中心列出，使用实际查询结果。新建对象未出现、目标仍存在、状态或字段不符、被跳过原因不明时，报告“变更未确认生效”。
