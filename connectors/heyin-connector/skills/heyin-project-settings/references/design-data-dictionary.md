# 数据字典与 SDTM 数据域使用说明

数据字典汇总指定方案版本的表单、字段、变量名、数据类型、交互类型、单位及选项编码，可按表单或按 SDTM 数据域查看和导出。SDTM 数据域是项目内的数据域目录（内置加自定义），表单可设置默认数据域，字段可关联一个或多个数据域。

本页的“数据域”专指 SDTM 数据域，与角色或 API 令牌的中心数据范围无关；向用户说明时写“SDTM 数据域”，避免与“数据范围”混用。

## 功能总览

| 功能 | 说明 | 可修改 |
| --- | --- | --- |
| 查看数据字典 | 按表单或按 SDTM 数据域读取指定方案版本的字段定义 | 否 |
| 导出数据字典 | 生成 xlsx 文件并返回短期签名地址 | 是，生成导出文件并记录日志 |
| 查询数据域 | 数据域目录、候选列表及在各方案版本中的使用情况 | 否 |
| 维护数据域 | 新建或删除项目自定义数据域 | 是 |

## 权限与前置条件

- 查看数据字典、导出数据字典和读取数据域候选列表需要 `PRJ_SETTINGS_DESIGN_ACCESS`。
- 数据域目录列表和使用情况需要 `PRJ_SETTINGS_SDTM_DOMAIN_ACCESS`；新建和删除需要 `PRJ_SETTINGS_SDTM_DOMAIN_EDIT`，并受项目可写状态约束。
- `meta_data_version_id` 从[方案版本与生命周期](design-version.md)的版本列表唯一定位，必须属于当前项目。设计中版本的表单与字段定义 ID 返回 `0`，只能用设计 ID（`form_dsn_id`、`field_dsn_id`）对应；已发布版本才有定义 ID。

## 查看数据字典（只读）

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 按表单获取数据字典 | `GET` | `/api/project/settings/design/data_dictionary/list_by_form/` | `--query`：`meta_data_version_id` = 方案版本 ID（必填） |
| 按数据域获取数据字典 | `GET` | `/api/project/settings/design/data_dictionary/list_by_sdtm_domain/` | `--query`：`meta_data_version_id` = 方案版本 ID（必填） |
| 获取数据域候选列表 | `GET` | `/api/project/settings/design/form/list_sdtm_domain_name/` | 无 |

返回内容：

- 按表单：`list`（`DataDictionaryForm[]`），按表单排序。每个表单含 `vid`、`name`、设计与定义 ID、默认数据域（`default_sdtm_domain_id` / `code` / `name`，未设置为 `0` 或空），以及按表单内定义顺序排列的 `fields`。
- 字段（`DataDictionaryField`）含所属表单 `form_vid` / `form_name`、直接所属字段组 `section_name`、`vid`、`name`、`data_type`、`resp_type`、`units`（首项为默认单位，`ratio` 为换算率）和 `options`（`name`、`data_value`、`null_flavor`、`unit_label`）。
- 按数据域：`list`（`DataDictionarySdtmDomain[]`）。首项固定为 `id=0` 的“未分配数据域”分组（`code`、`name` 为空，无字段时 `fields` 为空数组）；其后只列出该版本中至少关联一个字段的数据域，内置在前、自定义在后。关联多个数据域的字段在每个域下各出现一次，不能直接按行数统计字段总数。
- 候选列表：`list`（`SdtmDomainName[]`：`id`、`code`、`name`、`is_builtin`），用于表单默认数据域和字段数据域的取值校验与名称回显。

数据字典反映方案配置，不含研究参与者数据。统计分析、数据管理计划和变量映射以它为来源时，记录方案版本 ID、版本名称和读取时间；字典中没有的变量不能凭字段名称推测编码或单位。

## 导出数据字典（写）

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 导出数据字典 | `POST` | `/api/project/settings/design/data_dictionary/export_data_dictionary/` | `--body`：`meta_data_version_id` = 方案版本 ID（必填）；`view` = `FORM` 或 `SDTM_DOMAIN`（必填） |

- `FORM` 生成表单、字段、选项及编码三张表；`SDTM_DOMAIN` 生成数据域、字段、选项及编码三张表，多数据域字段逐域拆行，不含未分配字段。
- 平台同步生成 xlsx 并记录导出日志，响应 `file_path` 是短期签名下载地址。调用前确认方案版本和查看方式已获授权，只调用一次；超时或结果不明时不自动重试。
- 签名地址不在对话中公开。用户需要本地文件时，参照 `heyin-project` 技能“eTMF 文件管理使用说明”中“文件正文受控读取”的受控进程方式：在进程内存中使用地址，保存为授权位置的新 xlsx 文件，核对文件可打开且包含对应三张表；只读取字段定义时优先使用上面的查看接口，不为此生成导出文件。

## 查询与维护 SDTM 数据域

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 获取数据域列表 | `GET` | `/api/project/settings/sdtm_domain/list_sdtm_domain/` | `--query`：`limit` = 1–100（必填）；`offset` ≥ 0（可选）；`is_builtin` = `true` / `false`（可选，省略为全部）；`keyword` = 变量名或名称关键词（可选） |
| 获取数据域使用情况 | `GET` | `/api/project/settings/sdtm_domain/get_sdtm_domain_usage/` | `--query`：`id` = 列表返回的数据域 ID（必填） |
| 新建数据域 | `POST` | `/api/project/settings/sdtm_domain/create_sdtm_domain/` | `--body`：`code` = 变量名（必填）；`name` = 名称，最长 32 字（必填）；`description` = 说明，最长 200 字（可选） |
| 删除数据域 | `POST` | `/api/project/settings/sdtm_domain/delete_sdtm_domain/` | `--body`：`id` = 列表唯一定位的自定义数据域 ID（必填） |

- 列表返回 `list`（`SdtmDomain[]`：`id`、`code`、`name`、`description`、`is_builtin`、`count_used_mdv`）和 `total`，内置在前、自定义在后。`count_used_mdv` 只计对外可见的方案版本，分页按 `total` 读完。
- 使用情况返回 `list`（`SdtmDomainUsage[]`：`meta_data_version_id`、`meta_data_version_name`、`mdv_status`、`count_default_form`、`count_field`），只列出使用该数据域的对外可见版本，按版本先后排列。
- 新建时平台去掉首尾空格并转为大写：须以字母开头、仅含大写字母、数字和下划线、最多 32 位，不能是保留名 `UNASSIGNED`，也不能与内置或本项目已有数据域重复。成功返回新 `SdtmDomain`，按返回 `id` 回读列表核验。
- 内置数据域不可删除。自定义数据域被任一方案版本（含设计中、草稿与历史版本）的表单默认数据域或字段关联引用时不可删除；使用情况只覆盖对外可见版本，不能据其为空断言可删。删除没有演练接口且不可恢复：先展示数据域、使用情况及影响，取得授权后只提交一次，失败时按平台返回的引用版本说明，不自行解除表单或字段关联。

## 在表单与字段中使用数据域

表单的 `default_sdtm_domain_id` 和字段的 `sdtm_domain_ids` 在[表单设计使用说明](design-form.md)和[字段组与字段设计使用说明](design-form-item.md)的写接口中维护，只能使用候选列表实际返回的 ID。表单默认数据域只作为之后新建字段的初始值；新建字段省略 `sdtm_domain_ids` 时继承表单默认值。读取表单或字段设计时，响应同时返回数据域 ID 和名称（`default_sdtm_domain_name`、`sdtm_domains`）。

数据域分配属于方案设计变更，只在方案设计中执行并按设计流程发布。SDTM 映射规则来自用户提供的映射规范或统计负责人确认，不按字段名称自行推断；写入后用“按数据域获取数据字典”回读核对。
