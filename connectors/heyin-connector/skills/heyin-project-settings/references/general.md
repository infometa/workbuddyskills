# 项目通用设置

按 [项目设置技能](../SKILL.md) 核对项目和凭证后使用本文。示例中的凭证、项目、中心和版本 ID 均需替换为实际查询结果。

查询项目设置、容量和 OCR 记录需要 `PRJ_SETTINGS_GENERAL_ACCESS`；更新设置、关闭演练和启动演练需要 `PRJ_SETTINGS_GENERAL_EDIT`。正式项目生命周期操作须在平台受控界面完成，见下文。

## 功能总览

| 功能 | 说明 | 可修改 |
| --- | --- | --- |
| 查询项目设置 | 获取项目基础信息、功能许可与开关、状态、容量和派生统计 | 否 |
| 更新项目设置 | 修改基础字段、编号规则和功能开关 | 是 |
| 容量与 OCR 查询 | 获取 eTMF、SD 存储用量及 SD AI OCR 记录 | 否 |
| 高影响关闭演练 | 统计关闭 SD 或 eTMF 将删除的数据量 | 否 |
| 启动条件演练 | 检查项目启动所需的方案、模板和模块配置 | 否 |
| 生命周期管理 | 说明启动、暂停、恢复、锁定、解锁、结束与撤销结束条件 | 受凭证边界限制 |

## 查询项目与容量（只读）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 获取项目设置 | `GET` | `/api/project/settings/general/get_project/` | 无 | 当前项目的 `Project` 对象 |
| 获取 eTMF 存储空间用量 | `GET` | `/api/project/settings/general/get_etmf_storage_usage/` | 无 | 项目总文件数与大小，以及已发布域、分区的两级用量明细 |
| 获取 SD 存储空间用量 | `GET` | `/api/project/settings/general/get_sd_storage_usage/` | 无 | 生产中心及其生产研究参与者的 SD 文件条数与大小 |
| 获取 SD AI OCR 记录列表 | `GET` | `/api/project/settings/general/list_sd_ai_ocr_record/` | `--query`：`limit` = 10–100（必填）；`offset` = 非负偏移（可选） | `list` 和 `total` |

查询 SD AI OCR 记录示例：

```sh
heyincli req --token-id <token-id> --method GET \
  --path '/api/project/settings/general/list_sd_ai_ocr_record/' \
  --query '{"limit":20,"offset":0}'
```

需要全部记录时，每次将 `req --query` 的 JSON 对象中的 `offset` 增加实际返回的记录数，直到已读取数量达到 `total`；尚未读完却返回空列表时，应报告结果不完整。容量查询使用上表对应路径，不传查询参数。

项目对象包含大量配置与派生统计。处理通用设置时优先使用以下字段：

| 类别 | 核心字段 |
| --- | --- |
| 标识与资料 | `id`、`name`、`short_name`、`code`、`logo_path`（当前 Logo 签名地址）、`protocol_name`、`sponsor` |
| 编号与入组 | `planned_sample_size`、`is_over_enroll_allowed`、`site_sn_prefix`、`patient_sn_digit` |
| 生命周期 | `status`、`start_date`、`locked_date`、`suspended_date`、`terminated_date`、`is_disabled`、`is_expired` |
| 功能开关 | `is_test_env_on`、`is_sd_on`、`is_consent_on`、`is_rtsm_on`、`is_drug_supply_on`、四项 AI 开关、`is_follow_up_on`、`is_pro_on`、`is_analysis_on`、`is_tmf_on` |
| 功能许可 | `is_rtsm_allowed`、`is_drug_supply_allowed`、`is_consent_allowed`、`is_pro_allowed`、`is_follow_up_allowed`、`is_ai_ocr_allowed`、`is_ai_monitoring_allowed` |
| 发布与使用状态 | `is_sd_config_published`、`is_pro_config_published`、`is_tmf_config_published`、`is_tmf_ever_published`、`rtsm_count_used_number`、`mdv_status` |

eTMF 用量只统计生产环境已发布结构，域和分区按各自排序返回；总量由域统计汇总。SD 用量只返回生产中心和生产研究参与者。缺少派生统计时响应中的数值可能为零，但请求失败或字段缺失不能解释为零。

SD AI OCR 记录只包含生产环境中状态为处理中或成功的记录，按创建时间降序分页。每项可能包含中心、研究参与者、访视、SD 分类与文件夹、文件数据 ID，以及本次 OCR 用于智能分类、智能脱敏或数据录入的标记。

## 更新项目设置（写）

### 接口一览

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 更新项目设置 | `POST` | `/api/project/settings/general/update_project/` | `--body`：只提交用户明确要求变化的字段；项目由凭证确定，不传 `id` 或 `project_id` | 无 |

更新采用部分字段语义：未提交的字段保持原值；提交字段与当前值完全相同时会被平台拒绝为“对象未变化”。写后必须重新获取项目设置确认实际结果。

### 可更新字段

| 设置 | 字段 | 类型与限制 |
| --- | --- | --- |
| 项目名称 | `name` | 字符串，1–200 |
| 内置项目 Logo | `builtin_logo_id` | 非负整数；有效 ID 来自内置图片列表的 `project` 项，正数 ID 优先于 `logo_path` |
| 自定义项目 Logo | `logo_path` | 当前用户已上传图片的对象路径；未指定正数内置 ID 时，空字符串清空 Logo，省略保持原值 |
| 项目编码 | `code` | 字符串，4–32，全局唯一 |
| 项目简称 | `short_name` | 字符串，1–32 |
| 研究方案编号 | `protocol_name` | 字符串，最长 32 |
| 计划样本量 | `planned_sample_size` | 整数，至少 0 |
| 允许超额入组 | `is_over_enroll_allowed` | boolean |
| 申办者 | `sponsor` | 字符串，最长 200 |
| 中心编码前缀 | `site_sn_prefix` | 字符串，1–8 |
| 研究参与者编码位数 | `patient_sn_digit` | 整数，1–10 |
| 测试环境 | `is_test_env_on` | boolean |
| 功能开关 | `is_sd_on`、`is_consent_on`、`is_rtsm_on`、`is_drug_supply_on`、`is_ai_data_entry_on`、`is_ai_classify_on`、`is_ai_sd_masking_on`、`is_ai_monitoring_on`、`is_follow_up_on`、`is_pro_on`、`is_analysis_on`、`is_tmf_on` | boolean |

`patient_sn_digit` 为整数 1–10。项目响应不含 `is_tmf_allowed`，eTMF 是否获准开启以平台校验为准。

内置 Logo ID 必须来自当前可信内置图片查询，上传路径必须属于当前用户已上传的图片；没有有效图片来源时先完成平台图片选择或上传。响应中的 `logo_path` 是有时效的签名 URL，请求中的同名字段是上传对象路径，两者不能互传；不能把本地文件路径或任意 URL 当作上传路径。

不得提交接口未开放的 `site_sn_digit`、`patient_sn_prefix`、`is_share_on` 或项目返回对象中的其他字段。

### 字段副作用与功能依赖

- 修改项目名称、申办者或研究方案编号后，已缓存的 CRF 文件在下次下载时按新信息重新生成。
- 修改计划样本量会按生产环境实际入组数重新计算项目的 `ENROLLING` 或 `FINISH_ENROLLMENT` 状态。
- 关闭测试环境在 `IN_PREPARATION` 和 `STARTED` 状态下会被拒绝；其他前置条件仍以平台校验为准。
- 开启 RTSM 要求已获许可且项目处于 `IN_PREPARATION`。关闭 RTSM 也只允许在 `IN_PREPARATION`，且不能已有已使用随机号；关闭会删除 RTSM 相关数据，并在药物供应已开启时级联关闭和删除药物供应数据。
- 开启药物供应要求 RTSM 在本次更新后的状态为开启、项目已获药物供应许可且处于 `IN_PREPARATION`。单独关闭只允许在 `IN_PREPARATION`，并要求生产环境不存在已发药药物；关闭会删除药物供应配置与相关数据。
- 开启 eConsent、ePRO、随访分别要求对应项目许可。开启 AI 数据录入、智能分类或 SD 智能脱敏要求 AI OCR 许可；开启智能监查要求智能监查许可；开启 eTMF 要求 eTMF 许可。
- ePRO 或随访开关发生任何方向的变化时，项目内不能有正在方案升级的研究参与者。开启随访会为项目整理随访计划。
- eConsent 或 ePRO 开关变化会刷新照护用户与项目的关联。ePRO 开关变化会重置 ePRO 发布状态；关闭还会删除全部问卷配置及非终态问卷数据，保留已填写（`FILLED`）与逾期已填写（`OVERDUE_FILLED`）数据，并重算相关表单标记。
- SD 开关变化会重置 SD 发布状态；关闭会删除生产与测试环境 SD 文件数据和 SD 结构关联。eTMF 任一开关变化都会重置当前及历史发布标记；关闭会删除生产与测试环境的全部 eTMF 结构、文件和中心关联，并异步回收文件对象。
- 每次由关闭变为开启 AI SD 智能脱敏时，若当前词表为空，都会写入姓名、手机号和身份证号三项默认词；清空词表后关闭再开启也会重新补入。

## 高影响关闭演练

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 关闭 SD 演练 | `POST` | `/api/project/settings/general/close_sd_dry_run/` | 无（省略 `--body`） | `will_delete_file_data_count`、`test_will_delete_file_data_count` |
| 关闭 eTMF 演练 | `POST` | `/api/project/settings/general/disable_etmf_dry_run/` | 无（省略 `--body`） | `file_count`、`test_env_file_count` |

演练命令仅返回影响数量，不执行关闭：

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/general/close_sd_dry_run/'

heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/general/disable_etmf_dry_run/'
```

关闭 SD 或 eTMF 前必须读取最新项目设置并执行对应演练。演练结果只是调用时的数量快照，不执行关闭，也不覆盖结构、关联和异步对象回收等全部影响。

向用户展示生产与测试环境数量、完整级联影响以及本次将提交的开关字段。已有明确授权覆盖同一目标及演练揭示的删除和级联影响时，无需重复确认；否则先取得用户确认，再通过更新项目设置提交 `is_sd_on=false` 或 `is_tmf_on=false`。项目现状或目标发生变化时必须重新演练。写后回读开关和发布状态；关闭请求结果不明时不得重试。

## 项目启动演练与生命周期

### 启动演练

| 用途 | 方法 | 路径 | 请求参数 | 业务返回内容 |
| --- | --- | --- | --- | --- |
| 启动项目演练 | `POST` | `/api/project/settings/general/start_project_dry_run/` | 无（省略 `--body`） | 启动条件快照 |

```sh
heyincli req --token-id <token-id> --method POST \
  --path '/api/project/settings/general/start_project_dry_run/'
```

启动演练只适用于未禁用且处于 `IN_PREPARATION` 的项目。返回项目是否有已正式发布方案、是否有已发布知情同意书模板、各模块开关与发布状态、RTSM 与药物供应配置状态，以及生产中心总数、已应用方案中心数、已应用知情同意书模板中心数。

正式启动还要求至少有已正式发布方案；已开启 SD、ePRO 或 eTMF 时对应配置必须发布；已开启 eConsent 时必须有已发布模板；已开启 RTSM 或药物供应时必须有对应配置。演练结果不执行启动，也不能替代正式调用时的并发校验。

### 生命周期状态规则

| 用途 | 方法 | 路径 | 允许的当前状态 | 目标状态 |
| --- | --- | --- | --- | --- |
| 启动 | `POST` | `/api/project/settings/general/start_project/` | `IN_PREPARATION` 且启动条件满足 | `STARTED` |
| 锁定 | `POST` | `/api/project/settings/general/lock_project/` | `ENROLLING`、`FINISH_ENROLLMENT` | `LOCKED` |
| 解锁 | `POST` | `/api/project/settings/general/unlock_project/` | `LOCKED` | 按生产入组数计算 `ENROLLING` 或 `FINISH_ENROLLMENT` |
| 结束 | `POST` | `/api/project/settings/general/terminate_project/` | `LOCKED` | `TERMINATED` |
| 撤销结束 | `POST` | `/api/project/settings/general/revoke_terminate_project/` | `TERMINATED` | `LOCKED` |
| 暂停 | `POST` | `/api/project/settings/general/suspend_project/` | `STARTED`、`ENROLLING`、`FINISH_ENROLLMENT`、`LOCKED` | `SUSPENDED`，记录暂停前状态 |
| 恢复 | `POST` | `/api/project/settings/general/resume_project/` | 手动暂停且未过期的 `SUSPENDED` | 恢复为暂停前状态 |

所有正式生命周期接口除当前项目 ID 外，还强制要求短信临时凭证，或加密密码与公钥事务 ID。本技能不通过 CLI 收集或提交 `temp_token`、`password` 和 `transaction_id` 等二次认证材料，因此这些正式状态变更应在平台受控界面完成；不得索取、转述或尝试发送这些字段。用户要求执行时，应说明需要在平台受控界面完成。可以读取当前状态，启动前还可以执行不需要凭证的启动演练。

## 结果核验

一般容量答复只展示聚合统计；仅在用户明确要求且有权访问时展示逐人明细。不要展示 Logo 或文件签名地址。

更新计划样本量后同时回读项目生命周期状态；变更功能开关后核对发布标记和级联开关。关闭 SD 或 eTMF 时，同时引用演练返回的生产与测试环境数量。回读失败、字段不符或级联结果不完整时，报告“变更未确认生效”。
