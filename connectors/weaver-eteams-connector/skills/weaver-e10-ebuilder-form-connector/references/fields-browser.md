# 字段、选项与浏览字段解析

## 何时使用

写入前确认真实字段名、取选择类字段的选项、确认主表/明细表标识映射、把人员/部门/流程等名称解析成 ID 时使用。

**写入键的取值顺序**：字段定义里的 `text` 是显示名，**不能当写入键**；通常写入键用字段的 `name`；当 `name == id`（自定义字段常见）或目标接口明确要求组件数据键时，改用 `config.dataKey`。写入前一律用 `fields.get` 核对，不要凭用户叫法猜键名。

## 请求头契约（CLI 注入，Agent 不手写）

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## operation

| operation | risk | 必填 | 用途 |
| --- | --- | --- | --- |
| `ebuilder-form.fields.get` | read | 上下文 | 读 eBuilder 字段定义，返回主表与明细表字段、`config.dataKey`、`browserParams` 和组件类型 |
| `ebuilder-form.options.get` | read | 上下文 + 字段标识 | 按字段元数据 ID 读选择类字段选项 |
| `ebuilder-form.mapping.get` | read | `objId` | 读 `mainTable` / `detailN` 与主表、明细表标识映射 |
| `ebuilder-form.browser.resolve` | read | `module` + `browserType` + `query` | 把名称解析为可选项 ID |

### `fields.get` 参数

| 字段 | 说明 |
| --- | --- |
| `groupId` | eBuilder 应用或分组标识。**优先用菜单/上下文解析返回的 `appId`**；没有可靠值时从当前应用上下文取得，不要猜测 |
| `sourceId` | 来源对象 ID，通常传 `objId` |
| `sourceType` | 数据来源类型，表单场景传 `FORM`（默认）；布局逻辑字段传 `LOGIC` |
| `detailFieldsGroup` | 取明细表字段分组 |
| `enableMerge` | 合并主表与明细表字段 |
| `customParam` / `params` | 透传参数；一般不要手工构造 |

### `options.get` 参数

| 字段 | 说明 |
| --- | --- |
| `fieldName` / `fieldId` | **字段元数据 ID**（纯数字），取 `fields.get` 返回的 `fields[].id`，二选一。它不是字段显示文本，也不是字段对象的 `name` |
| `sourceType` | 数据来源类型，默认 `FORM` |
| `groupId` | 与 `fields.get` 使用时保持一致 |
| `optionLevel` | 选项层级，默认 `1`；存在层级选项时按实际层级传入 |

选项返回 `id`（选项 ID）与 `name`（选项名称）：**写入用 `id`，展示用 `name`**，层级选项按 `pid` 建立父子关系。

### `browser.resolve` 参数

| 字段 | 说明 |
| --- | --- |
| `module` | 浏览接口模块，例如 `hrm`、`workflow/core`、`doc`、`task` |
| `browserType` | 浏览类型，例如 `resource`（人员）、`department`（部门）、`subcompany`（分部）、`wfcRequest`（流程） |
| `query` | 要解析的业务名称（用户提供名称即可，不要求用户预先知道系统 ID） |
| `multiple` | 是否允许多选 |
| `limit` | 返回条数上限 |
| `extra` | 模块要求的附加参数 |

## 处理链

1. `fields.get` 取真实字段定义，确认写入键（默认 `name`；`name == id` 时用 `config.dataKey`）。
2. 选择类字段用 `options.get` 取选项，**传选项 `id`，不传中文名**。
3. 需要写明细表时用 `mapping.get` 确认 `detail1` / `detail2` 对应的标识，**按接口返回关系使用，不能按名称或本地顺序自行编号**。
4. 人员/部门/流程等关联字段用 `browser.resolve` 把名称解析为 ID；**多命中时必须让用户选**，不得自动取第一条，也不得要求用户先提供 ID。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.fields.get --input-json '{"context":{"objId":"121000000000000001"}}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.options.get --input-json '{"context":{"objId":"121000000000000001"},"fieldName":"customer_type"}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.mapping.get --input-json '{"objId":"121000000000000001"}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.browser.resolve --input-json '{"module":"hrm","browserType":"resource","query":"张三"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.browser.resolve --input-json '{"module":"hrm","browserType":"resource","query":"张三"}'
```

## 失败处理

| subtype | 含义 | 处置 |
| --- | --- | --- |
| `field_required` | 未提供字段标识 | 补 `fieldName` 或 `fieldId` |
| `field_invalid` | 字段标识非法或不存在 | 以 `fields.get` 返回的字段为准重新取值 |
| `field_forbidden` | 该字段不允许写入或不允许该操作 | 停止写入并原样转达，不要换字段绕过 |
| `obj_id_required` | 缺少 `objId` | 回 `context.resolve` 补齐 |
| `query_required` | `browser.resolve` 缺少 `query` | 补名称关键词 |
| `unknown_field` | 入参字段不在 schema 中 | 去掉该字段，不要猜参数 |
| `session_expired` | 登录态失效 | 引导用户断开并重新连接本连接器以重新登录，然后从只读步骤重新开始 |

## 红线

- 禁止用字段显示名（`text`）当写入键；默认用 `name`，`name == id` 或接口要求组件键时才用 `config.dataKey`。
- 选项一律传 `id`，不传中文名称；不要在调用方硬编码生产选项 ID 或名称。
- 名称解析多命中时必须让用户选，禁止自动取第一条；也不要把「让用户提供 ID」当成解析手段。
- 字段定义中的 `config.options` 已够用时可直接用，但要完整名称或最新选项时以 `options.get` 结果为准。
