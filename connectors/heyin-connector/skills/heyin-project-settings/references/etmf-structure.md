# eTMF 主文件结构说明

按 [eTMF 配置入口](etmf.md) 与 [项目设置使用指南](../SKILL.md) 核对凭证、权限、请求环境和授权。项目由凭证确定，不传 `project_id`；GET 参数放入 `--query`，POST 参数放入 `--body`。已有明确授权覆盖目标、参数和实际影响时不重复确认；仅演练授权不覆盖正式变更。

## 功能总览

| 功能 | 说明 | 可修改 |
| --- | --- | --- |
| 域维护 | 在草稿轨创建、改名、同级排序；删除前演练级联文件影响 | 是 |
| 分区维护 | 在唯一父域下创建、改名、同级排序；删除前演练级联文件影响 | 是 |
| 文件项维护 | 在唯一父分区下创建、部分更新、同级排序；更新和删除前演练文件影响 | 是 |
| 子文件项维护 | 创建时配置或通过文件项更新整体替换；移除前逐项演练影响 | 是 |

## 对象与状态模型

主文件配置是固定四层结构；本组接口不能创建更深层级，也不能用更新或排序把对象移动到其他父级。

```text
当前项目
└── 域（EtmfZone）
    └── 分区（EtmfSection）
        └── 文件项（EtmfArtifact）
            └── 子文件项（string）
```

`get_config.data.structure` 是当前草稿轨完整树和所有结构 ID 的唯一来源。顶层 `zones`、域内 `sections`、分区内 `artifacts` 共同确定父子关系；子文件项没有独立 ID，以父文件项下精确字符串标识。只能用最新树中的稳定 `id` 唯一定位域、分区和文件项，并同时核对名称与父级；`code` 和 `ranking` 会因排序或删除重算，不是稳定标识。

### 层级字段

| 对象 | 核心字段 | 子级与统计 | 写入边界 |
| --- | --- | --- | --- |
| 主结构 | `zones`、`zone_count`、`section_count`、`artifact_count` | 完整/必备文件项数、文件状态数量和总大小 | 只读聚合，不整体回传 |
| 域 | `id`、`name`、`code`、`ranking` | `sections`、`section_count`、`artifact_count` 及文件统计 | 创建只写名称；更新只改名称；排序只写 ID 与目标位置 |
| 分区 | `id`、`name`、`code`、`ranking` | `artifacts`、`artifact_count` 及文件统计 | 创建固定 `zone_id`；更新不能换域；排序仅限原域 |
| 文件项 | `id`、`name`、`code`、`ranking` | 归属方、级别、必备性、盲态、版本化、里程碑 ID、子文件项及文件统计 | 创建固定 `section_id`；更新不能换分区；排序仅限原分区 |
| 子文件项 | 非空名称字符串 | 没有独立 ID、编码或排序接口 | 更新文件项时传更新后的完整列表；移除按精确名称逐项演练 |

域、分区和文件项名称创建时长度为 1–200。文件项 `definition` 最长 2000；`sub_artifacts` 是完整字符串数组，单项长度、唯一性和数组上限由平台校验，不自行补造限制。

### 文件项字段

| 字段组 | 字段 | 语义与约束 |
| --- | --- | --- |
| 标识 | `id`、`code`、`ranking` | 平台维护；`id` 用于定位，`code` 和 `ranking` 可能重算 |
| 基本信息 | `name`、`definition` | 名称创建必填、更新可选；定义可选，只有用户明确要求时提交 |
| 归属方 | `is_sponsor`、`is_investigator` | 分别表示申办者与研究者归属；不得根据名称推断 |
| 项目级 | `is_project_level`、`is_project_required`、`is_project_blind`、`project_milestone_id` | 是否启用、是否必备、是否盲态及项目级里程碑绑定；`0` 表示不绑定 |
| 中心级 | `is_site_level`、`is_site_required`、`is_site_blind`、`site_milestone_id` | 是否启用、是否必备、是否盲态及中心级里程碑绑定；`0` 表示不绑定 |
| 文件行为 | `is_versioned`、`sub_artifacts` | 是否版本化；子文件项数组在更新时是整体替换值 |
| 统计 | `count_*`、`total_etmf_file_size` | 文件状态、必备/缺失槽位和总大小的只读快照，不得作为对象 ID 或合规结论 |

创建文件项时，除 `name`、`section_id` 外的字段均可省略，省略时采用平台默认，不能替用户猜测。提交前必须逐项明确归属方、项目/中心级、必备性、盲态、版本化、两个里程碑绑定和子文件项；确实不设置的可选字段才省略。`is_sponsor` 与 `is_investigator` 至少一项为 `true`，`is_project_level` 与 `is_site_level` 也至少一项为 `true`。里程碑 ID 必须来自当前项目最新草稿里程碑树，按要绑定的文件级别写入对应字段；同一里程碑可同时用于项目级和中心级。盲态只允许双盲项目启用。

文件项响应必定包含字符串 `definition`，创建响应和 `get_config` 的文件项均返回。更新前读取当前值，更新后核对目标值；实际响应缺失时属于响应不完整，不能解释为正常的不可回读字段。

未启用的级别会自动归零其附属字段：项目级关闭时，`is_project_required=false`、`project_milestone_id=0`、`is_project_blind=false`；中心级关闭时，`is_site_required=false`、`site_milestone_id=0`、`is_site_blind=false`。创建和更新都适用，即使请求省略这些字段也会归零；重新开启级别不会恢复旧值。

### 结构变更状态

创建、更新、排序、影响演练和正式删除都只在 `is_tmf_on=true` 且 `is_tmf_config_published=false` 的设计状态执行。已关闭或已发布时停止，不得自动开启或自动重入设计。目标值与可见实时值一致时报告无变化，不发送 POST；实际响应缺失的字段无法做无变化判断时要明确说明可见性限制。

## 接口一览

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 新建域 | `POST` | `/api/project/settings/etmf/create_zone/` | `--body`：`name`（string，必填）：域名称，1 至 200 字符 |
| 修改域 | `POST` | `/api/project/settings/etmf/update_zone/` | `--body`：`name`（string，可选）：新名称，1 至 200 字符；`zone_id`（integer，必填）：从最新配置唯一定位的正整数 ID。 |
| 域排序 | `POST` | `/api/project/settings/etmf/rank_zone/` | `--body`：`id`（integer，必填）：最新配置中的域稳定 ID；`ranking`（integer，必填）：至少为 1 的目标排序位置；超过同级最大排名时按末位处理。 |
| 删除域演练 | `POST` | `/api/project/settings/etmf/delete_zone_dry_run/` | `--body`：`zone_id`（integer，必填）：从最新配置唯一定位的正整数 ID。 |
| 删除域 | `POST` | `/api/project/settings/etmf/delete_zone/` | `--body`：`zone_id`（integer，必填）：与删除演练相同的域 ID。 |
| 新建分区 | `POST` | `/api/project/settings/etmf/create_section/` | `--body`：`name`（string，必填）：分区名称，1 至 200 字符；`zone_id`（integer，必填）：从最新配置唯一定位的父域 ID。 |
| 修改分区 | `POST` | `/api/project/settings/etmf/update_section/` | `--body`：`name`（string，可选）：新名称，1 至 200 字符；`section_id`（integer，必填）：从最新配置唯一定位的正整数 ID。 |
| 分区排序 | `POST` | `/api/project/settings/etmf/rank_section/` | `--body`：`id`（integer，必填）：最新配置中的分区稳定 ID；`ranking`（integer，必填）：父域内目标排序位置，至少为 1；超过同级最大排名时按末位处理。 |
| 删除分区演练 | `POST` | `/api/project/settings/etmf/delete_section_dry_run/` | `--body`：`section_id`（integer，必填）：从最新配置唯一定位的正整数 ID。 |
| 删除分区 | `POST` | `/api/project/settings/etmf/delete_section/` | `--body`：`section_id`（integer，必填）：与删除演练相同的分区 ID。 |
| 新建文件项 | `POST` | `/api/project/settings/etmf/create_artifact/` | `--body`：`definition`（string，可选）：定义或用途，最长 2000 字符；<br>`is_investigator`（boolean，可选）：是否归属研究者；<br>`is_project_blind`（boolean，可选）：项目级是否盲态；<br>`is_project_level`（boolean，可选）：是否启用项目级；<br>`is_project_required`（boolean，可选）：项目级是否必备；<br>`is_site_blind`（boolean，可选）：中心级是否盲态；<br>`is_site_level`（boolean，可选）：是否启用中心级；<br>`is_site_required`（boolean，可选）：中心级是否必备；<br>`is_sponsor`（boolean，可选）：是否归属申办者；<br>`is_versioned`（boolean，可选）：是否版本化管理；<br>`name`（string，必填）：文件项名称，1 至 200 字符；<br>`project_milestone_id`（integer，可选）：项目级里程碑 ID；<br>`0` 表示不绑定；<br>`section_id`（integer，必填）：最新配置中唯一定位的父分区 ID；<br>`site_milestone_id`（integer，可选）：中心级里程碑 ID；<br>`0` 表示不绑定；<br>`sub_artifacts`（array[string]，可选）：子文件项名称列表。 |
| 修改文件项演练 | `POST` | `/api/project/settings/etmf/update_artifact_dry_run/` | `--body`：`artifact_id`（integer，必填）：从最新配置唯一定位的文件项 ID |
| 删除子文件项条目演练 | `POST` | `/api/project/settings/etmf/delete_sub_artifact_dry_run/` | `--body`：`artifact_id`（integer，必填）：从最新配置唯一定位的父文件项 ID；`sub_artifact`（string，必填）：当前父文件项中存在的非空子文件项名称。 |
| 修改文件项 | `POST` | `/api/project/settings/etmf/update_artifact/` | `--body`：`artifact_id`（integer，必填）：从最新配置唯一定位的文件项 ID；<br>`definition`（string，可选）：定义或用途，最长 2000 字符；<br>`is_investigator`（boolean，可选）：是否归属研究者；<br>`is_project_blind`（boolean，可选）：项目级是否盲态；<br>`is_project_level`（boolean，可选）：是否启用项目级；<br>`is_project_required`（boolean，可选）：项目级是否必备；<br>`is_site_blind`（boolean，可选）：中心级是否盲态；<br>`is_site_level`（boolean，可选）：是否启用中心级；<br>`is_site_required`（boolean，可选）：中心级是否必备；<br>`is_sponsor`（boolean，可选）：是否归属申办者；<br>`is_versioned`（boolean，可选）：是否版本化管理；<br>`name`（string，可选）：文件项名称，1 至 200 字符；<br>`project_milestone_id`（integer，可选）：项目级里程碑 ID；<br>`0` 表示不绑定；<br>`site_milestone_id`（integer，可选）：中心级里程碑 ID；<br>`0` 表示不绑定；<br>`sub_artifacts`（array[string]，可选）：更新后的完整子文件项名称列表。 |
| 文件项排序 | `POST` | `/api/project/settings/etmf/rank_artifact/` | `--body`：`id`（integer，必填）：最新配置中的文件项稳定 ID；`ranking`（integer，必填）：父分区内目标排序位置，至少为 1；超过同级最大排名时按末位处理。 |
| 删除文件项演练 | `POST` | `/api/project/settings/etmf/delete_artifact_dry_run/` | `--body`：`artifact_id`（integer，必填）：从最新配置唯一定位的文件项 ID |
| 删除文件项 | `POST` | `/api/project/settings/etmf/delete_artifact/` | `--body`：`artifact_id`（integer，必填）：与删除演练相同的文件项 ID |


## 操作流程

### 创建域、分区或文件项

1. **读取与定位**：按 [生命周期说明](etmf-lifecycle.md) 读取状态和完整配置，确认设计状态。创建分区时唯一定位父域；创建文件项时唯一定位父分区，并从同一配置定位可选里程碑。
2. **核对同级**：按稳定 ID、名称和父级核对同级对象，避免名称歧义。平台不保证同级名称唯一，不能依赖同名请求被拒绝来防重；存在同名对象时先按父级和稳定 ID 消除歧义，不得自动改名。
3. **固定参数**：域只提交名称；分区提交父域 ID 和名称；文件项逐项固定全部明确属性。未提供的可选字段省略，不传 `null`，也不把读取对象整体回传。
4. **批准写入**：展示目标层级、父级、完整请求体和平台会自动追加排序/生成编码的事实，取得本次创建批准。
5. **单次执行**：只调用一次创建接口；超时或结果未知时不自动重试，以免重复创建。
6. **回读核验**：使用创建响应中必有的稳定 `id` 重新读取配置，在预期父级唯一定位并核验所有可见提交字段。

创建文件项不自动创建或绑定里程碑；`project_milestone_id` 与 `site_milestone_id` 只有用户明确选择时才使用对应稳定 ID，显式 `0` 表示不绑定。

### 修改域或分区

1. 读取设计状态和完整树，按稳定 ID、名称及父级唯一定位目标。
2. `name` 可省略，但本操作必须包含用户明确要求且相对实时值确有变化的新名称；否则报告无变化。
3. 展示“当前名称 → 目标名称”、稳定 ID、父级和最终请求体，授权范围明确后只调用一次。
4. 回读同一 ID，确认名称已更新且父级未变化。更新接口不能移动域或分区。

### 修改文件项

1. **固定当前对象与计划差异**：读取设计状态，在唯一父分区定位文件项。只提交用户明确要求的字段；`artifact_id` 必填，未修改字段省略。`sub_artifacts` 一旦提交就是更新后的完整列表，里程碑 ID 为 `0` 表示解绑。
2. **批准通用更新演练**：为同一文件项的 `update_artifact_dry_run` 核对演练范围。该请求只接收文件项 ID，不接收计划变更；返回的是当前文件项四类潜在影响，必须按计划差异选择相关块，不得把无关块说成必然影响。
3. **解释影响**：
   - `versioned_change`：修改 `is_versioned` 的生产/测试文件数；生产文件数大于零时平台语义为不可修改，测试文件会在更新时清理。
   - `disable_project_level`：关闭项目级的生产/测试影响；测试文件在更新时清理，生产文件在发布时清理。同时即时将 `is_project_required`、`is_project_blind` 置 `false`，将 `project_milestone_id` 置 `0`，即使未提交这三个字段。
   - `disable_site_level`：关闭中心级的生产/测试影响；测试文件在更新时清理，生产文件在发布时清理。同时即时将 `is_site_required`、`is_site_blind` 置 `false`，将 `site_milestone_id` 置 `0`，即使未提交这三个字段。
   - `sub_artifacts`：各子文件项移除影响摘要；只按精确名称关联计划移除项。对应测试文件在更新时即时清理，生产文件在下次发布时清理。
4. **逐项演练子文件项移除**：对旧列表中有而目标完整列表中没有的每个名称，分别固定完全一致的 `artifact_id` 与精确 `sub_artifact`，核对授权范围并调用删除子文件项条目演练。名称不存在、重复、大小写不确定或任一影响不完整时停止。
5. **独立批准更新**：重新读取配置；确认项目、状态、父级、文件项 ID、可见当前值、里程碑绑定和子文件项列表未漂移。展示最终字段差异（包含关闭级别时自动清零的必备性、盲态和里程碑绑定）、全部相关影响以及测试即时清理/生产发布清理边界，为正式更新核对正式授权，未覆盖时取得确认。
6. **单次执行并回读**：只调用一次更新接口，再读取同一文件项核验提交字段及级别关闭时自动清零的附属字段。

更新前缺失 `definition` 时先报告响应不完整，不能猜测旧值；写后缺失时分别报告请求结果、已核验字段及未完成的定义核验，不能宣称全部字段更新完成。实际返回且与任务相关的字段按真实值比较，不推断缺失值。

### 排序域、分区或文件项

1. 读取完整同级列表：域以全部顶层域为范围，分区仅限原父域，文件项仅限原父分区。
2. 使用稳定 `id` 和用户明确的正整数 `ranking`（至少为 1），展示当前位置、目标位置、父级及预计相邻项变化。超过同级最大排名时平台按末位处理，展示该实际位置；按此规则计算后目标相同则不请求，服务端也会返回无变化。
3. 授权范围明确后调用一次对应排序接口，再回读完整同级列表。
4. 按平台实际结果报告同级顺序。排序可能压缩排名并重算 `code`：域排序级联重算域/分区/文件项编码，分区排序重算该域下分区/文件项编码，文件项排序重算同分区文件项编码。后续定位继续使用稳定 ID。

排序接口没有父级参数，不能据此跨父级移动。参数不合法、父级漂移或回读不符时停止，不自动修正位置。

### 删除域、分区或文件项

1. **固定目标与级联范围**：读取设计状态和完整树。域包含全部分区与文件项；分区包含全部文件项；文件项包含全部子文件项及里程碑绑定。展示稳定 ID、父级和完整子树。
2. **批准删除演练**：使用目标对应的 dry-run，为本次演练核对演练范围并执行一次。
3. **展示影响**：展示 `file_count`（下次发布将清理的生产文件数）和 `test_env_file_count`（本次删除即时清理的测试文件数）。任一字段缺失或类型错误时停止，不能补成 `0`；数量只表示文件影响，不覆盖结构、绑定、排序和编码重算。
4. **独立批准删除**：重新读取配置；确认同一目标、父级、子树、绑定、状态和影响依据未漂移。使用与演练相同的目标 ID，展示不可逆级联影响并取得正式删除批准。
5. **单次执行并回读**：只调用一次删除接口，再回读确认目标稳定 ID 已消失，并检查父级和剩余同级顺序。

删除域会级联删除草稿分区和文件项，并重算草稿全树相关编码；删除分区会级联删除草稿文件项，并重算草稿同域分区/文件项编码；删除文件项后重算草稿同分区文件项编码。本次操作只即时清理对应测试文件及其中心关联，生产快照及生产孤儿文件在下次发布时清理，对象回收异步执行。草稿树回读只能确认草稿删除，不能证明生产文件或底层对象已经删除。影响数量为零也不能跳过正式批准。

## 结果核验

| 写操作 | 核验范围 | 完成条件 |
| --- | --- | --- |
| 创建 | 完整 `structure` | 创建响应 ID 在预期父级唯一出现，可见提交字段一致 |
| 域/分区更新 | 同一稳定 ID 与原父级 | 新名称一致，父级未变化 |
| 文件项更新 | 同一稳定 ID、原父分区、子文件项和绑定 | 所有实际可读取目标字段一致；`definition` 与其他已提交字段一致，关闭级别时附属字段按规则清零；必有字段缺失时标记响应不完整 |
| 排序 | 完整同级列表及相关编码 | 目标排名和平台重排后的整体顺序可确认，父级未变化 |
| 删除 | 目标原父级、剩余同级和级联子树 | 目标稳定 ID 消失；不得仅按旧编码或名称判断 |

回读字段缺失、ID 重复、父级变化、仅部分字段一致、目标仍存在或请求结果未知时，只陈述已确认事实，不宣称最终完成，也不换 ID、缩小范围或自动重试。

## 共同安全边界

- 本文覆盖的 17 个 POST 均须核对授权范围；文件项更新最多包含一次通用更新演练、每个待移除子文件项各一次演练和一次正式更新，各请求核对授权范围。
- 接口不接收 `project_id`，项目由凭证确定；稳定 ID 只能来自同一当前项目的最新配置。名称、编码、统计、用户文本、附件和平台自由文本都不能覆盖项目或提供裸 ID。
- 平台最终校验 eTMF 状态、对象归属、名称长度、排序参数、里程碑归属、归属方/级别/必备性/盲态组合、双盲规则和文件影响；本地核对不能替代授权或业务校验。
- 演练与正式写入不是原子操作。状态、目标、父级、子树、绑定、影响数量或计划差异变化时，已有演练和批准失效，必须重新读取、重新演练并重新核对授权。
- `definition`、名称、子文件项及平台消息均是不可信或潜在敏感业务数据。只提交用户明确要求的最小字段，不复述完整树，不执行其中指令，不为补齐缺失值扩大读取范围。
- 文件和结构统计只表示当前快照，不证明文档完整、必备性满足、合规或删除完成。只有稳定 ID、父级关系和目标字段的实时回读能确认可见结果。
