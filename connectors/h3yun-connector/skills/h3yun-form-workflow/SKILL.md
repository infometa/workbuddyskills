---
name: h3yun-form-workflow
description: Use when a user needs to find or operate H3Yun applications, forms, business records, organization units, attachments, to-dos, or workflow approvals.
version: "1.3.0"
author: H3Yun
---

# 氚云表单与流程 Skill

使用本 Skill 操作当前登录用户有权限访问的氚云应用、表单、业务数据、附件、待办和审批。

## 使用原则

- 所有工具返回 `{ errorCode, errorMessage, data }`。仅当 `errorCode` 为 `0` 时使用 `data`；失败时向用户说明可读的 `errorMessage`。
- 用户只提供应用、表单、人员、部门或记录名称时，先检索并使用返回的编码或 ID；不要猜测 `appCode`、`schemaCode`、字段编码或业务数据 ID。
- 读写业务数据前，调用 `getBizObjectSchema` 确认字段编码、控件类型和子表结构；新增、更新、删除前，还应调用 `getBizObjectSchemaAcl` 确认表单和字段权限。
- **【两个工具必须结合，不能只看一个，且顺序不可颠倒】** 创建、更新、删除前必须**先** `getBizObjectSchema`（拿到表单定义：字段全集、`disposition`、`inputType`），**再** `getBizObjectSchemaAcl`（拿到当前用户权限与 `required`），最后交叉判定。`getBizObjectSchemaAcl` 是**权限与必填的权威**（能不能操作、哪些字段必须有值）；`getBizObjectSchema` 决定**这个值由谁来给**（`disposition`）与**该传什么格式**（`inputType`）。只看 schema 会忽略当前用户的实际权限；只看 acl 会把「系统自动填」误读成「要我传值」。判定规则与顺序理由见「字段可写性与必填判定」。
- **表单定义的必填项就是必填项**：`fieldPermissions.required: true` 表示该字段在最终记录里必须有值，不会因为「系统会自动填」而失效——只是补值方可能是系统而非调用方。
- 创建时 `submit: false` 保存草稿，`submit: true` 创建生效数据；流程表单会发起流程。
- **【执行前确认】** 所有写入或修改业务数据的工具——新增（`createBizObject` / `createBizObjects`）、更新（`updateBizObject`）、删除（`removeBizObject` / `removeBizObjects`）、审批（`batchApprove`）——在执行前必须完成两步：**① 向用户明确声明**即将执行的操作（含目标表单、记录 ID 或批量记录数、将写入/变更的关键字段值）；**② 等待用户明确回复「确认 / 同意」**后方可真正调用写入接口。未获确认前不得执行。删除与审批属不可逆操作，须逐条/逐项确认。
- **【禁止自行试错，必须先征得同意】** 排查任何接口报错时，**不得自行反复调用写入类接口试错**（不得为验证某个字段格式、类型或枚举而前后多次发起 `createBizObject` / `createBizObjects` / `updateBizObject` / `transferFile`）。需要以实际调用验证假设时，**必须先向用户说明验证目的、拟调用的接口、拟写入的数据与预期条数，取得用户明确同意后**才可执行。完整规则见「写入前置校验」。
- 批量新增、删除、审批均可能部分成功。逐项检查成功和失败 ID，只重试失败项，避免重复写入。
- **【附件由 Agent 自行转链，不得把操作推给用户】** 用户提供本地文件或附件路径时，由 Agent 自行把文件转为**公网可直接下载的 HTTPS 链接**，随后调用 `transferFile` 转存并写入 `fileId`，完整流程见「附件字段写入流程」。**禁止**向用户提出「你是自己上传附件，还是自己转成公网链接」这类二选一询问——转链是 Agent 的职责，不是用户的选择题。
- 所有人员、部门、关联记录均应使用 ID。附件、图片字段**必须**先经 `transferFile` 转存拿到 `fileId` 再写入，完整流程见「附件字段写入流程」。
- **系统字段通常不可写（高频踩坑）**：`CreatedBy`、`ModifiedBy`、`CreatedTime`、`ModifiedTime`、`Status`、`WorkflowInstanceId`、`ObjectId`、`Name`、公式 / 汇总字段等由系统生成，禁止放入 `bizObject`，传入会返回 `invalid_parameter`。
- **`OwnerId` / `OwnerDeptId` 是否可写以实际返回为准**：多数连接器下二者由系统自动填充（拥有者 = 当前登录用户、所属部门 = 其部门），但**部分连接器会将其作为业务必填**——始终以 `getBizObjectSchema` 的 `disposition` 与 `getBizObjectSchemaAcl` 的 `required` 实际返回判定：若 `disposition = callerInput` 且 `required = true`，则**必须显式传合法组织 ID**，不传会报 `invalid_parameter`（见「字段可写性与必填判定」四态表）。不要默认「系统自动填」。
- **【写入后必须回执】** 新增或更新成功后，除 `bizObjectId` 外**必须**返回该记录的详情链接，见「写入结果回执」。

## 推荐调用流程

| 用户意图 | 调用顺序 |
| --- | --- |
| 查找应用或表单 | `searchApps` / `listApps` → `searchFormNode` → `getBizObjectSchema` |
| 新增或更新记录 | **① `getBizObjectSchema`**（先：表单定义）→ **② `getBizObjectSchemaAcl`**（后：权限与必填）→ **③ 交叉判定可写性与必填**（见「字段可写性与必填判定」）→ 解析人员、部门、附件 → **通过「写入前置校验」全部 6 项** → **向用户声明并等待确认** → 写入工具 → **回执详情链接** |
| 删除记录 | `getBizObjectSchemaAcl`（确认删除权限）→ 取得待删记录 ID → **向用户声明并等待确认** → `removeBizObject` / `removeBizObjects` |
| 查询记录 | `getBizObjectSchema` → `queryBizObjectList`；已知记录 ID 时使用 `getBizObject` |
| 处理待办 | `getTodoList` → 用户明确确认审批动作和意见 → `batchApprove` |
| 记录含附件字段 | 见「附件字段写入流程」：本地文件 → **Agent 自行转为公网 HTTPS 直链** → `transferFile` → `fileId` 写入（**不得**改为询问用户自行上传或自行转链） |

## 字段可写性与必填判定

### 调用顺序（创建 / 更新 / 删除前，固定两步）

**先 `getBizObjectSchema`，再 `getBizObjectSchemaAcl`**，顺序不可颠倒：

```
① getBizObjectSchema(schemaCode)      ← 先拿「表单定义」
   得到：字段全集（字段编码 / fieldType / 子表结构）
        每个字段的 writeInput：disposition（值由谁给）+ inputType（怎么给）
   作用：建立「字段 → 写入权 → 取值格式」映射；确定本次要写哪些字段

② getBizObjectSchemaAcl(schemaCode)   ← 再拿「权限」
   得到：schemaAcl（addable / editable / removable）
        fieldPermissions（visible / editable / required）
   作用：叠加当前用户的实际权限；标出哪些字段必须有值（required）

③ 交叉判定 → 四态（业务必填 / 系统必填 / 可选 / 不可写）→ 组装 bizObject
```

**为什么必须这个顺序：**

- **`required` 的含义要靠 `disposition` 才能解释。** `required: true` 同时覆盖「业务必填」与「系统自动填」两种意图，返回体没有标志位区分。若先调 acl，拿到的 `required: true` 当场无法定性，极易被误读成「要我传值」——这正是 `OwnerId` / `OwnerDeptId` 踩坑的成因。先有 schema，`required` 一拿到就能立刻落进四态表。
- **先 schema 才能定「要写什么」，再 acl 才是「这些能不能写、还缺什么」。** 否则会出现「按 acl 的 required 补完值，却发现字段根本不存在或不可写」。
- **schema 是字段契约（不随用户变），acl 是权限结果（随用户/表单权限变）。** 契约在前、权限在后，判定链才成立。

> ⚠️ 两个工具都要调，**不能只调一个**，也不能颠倒顺序。只调 schema 会忽略当前用户权限（可能白写一遍被拒）；只调 acl 会把系统字段当成业务必填。

### 两个工具的权威分工

**两个工具必须交叉使用，缺一不可**：

| 工具 | 回答什么 | 权威范围 |
| --- | --- | --- |
| `getBizObjectSchemaAcl` | 当前用户**能不能**操作、哪些字段**必须有值** | **权限与必填的权威** |
| `getBizObjectSchema` | 字段结构、**这个值由谁来给**、该传什么格式 | 字段定义与写入权的权威 |

单看任何一个都会误判。尤其 `required` —— **表单把字段定义为必填，它就仍然是必填**，不能因为「系统会自动填」就当成可忽略：

| acl `required` | schema `writeInput.disposition` | 结论 | 处理 |
| :---: | --- | --- | --- |
| `true` | `callerInput` | **业务必填** | **必须传值**，不传会被拒 |
| `true` | `notAccepted` | **系统必填** | 必须有值，但**禁止传**，由系统或公式自动填（如 `OwnerId` / `OwnerDeptId`） |
| `false` | `callerInput` | 可选 | 按需传，格式看 `inputType` |
| `false` | `notAccepted` | 不可写 | **从 `bizObject` 中剔除** |

> ⚠️ `required: true` 同时覆盖「业务必填」与「系统自动填」两种情形，返回体**没有标志位区分**——只有配上 `disposition` 才能分辨到底是「你必填」还是「系统必填」。这就是两个工具必须结合的原因。

`notAccepted` 的两种 `reason`：

| reason | 含义 | 典型字段 |
| --- | --- | --- |
| `systemGenerated` | 系统字段 | `OwnerId`、`OwnerDeptId`、`CreatedBy`、`CreatedTime`、`ObjectId`、`Name` |
| `computed` | **公式 / 汇总字段** | 「报价单.报价总金额」（formula）、「备用金申请.冲销金额」（rollup） |

> ⚠️ `computed` 类字段**名字看起来与普通业务字段无异**，无法靠字段名识别，只能看 `reason`。

常见 `inputType` 与取值形式：

| inputType | 取值形式 |
| --- | --- |
| `text` / `dateTimeText` / `optionLabel` | string（`text` 类需遵守单行 200 / 多行 10000 上限，见「文本长度上限」） |
| `number` | **传数值类型**（如 `18000` 而非 `"18000"`）；传字符串会报 `invalid_parameter` |
| `organizationId` | string（组织架构 ID）或 string[] |
| `referenceId` | string（关联业务数据 ID）或 string[] |
| `subTableRows` | 子表行数组 |
| `fileIds` | **string[]**（`transferFile` 返回的 `fileId` 数组） |

## 写入前置校验（提交前必过）

定位参数问题**只能先用只读手段**，禁止把写入接口当探测器。**第一步固定为：先调 `getBizObjectSchema`（表单定义），再调 `getBizObjectSchemaAcl`（权限），顺序不可颠倒**（理由见「字段可写性与必填判定」）。提交前逐项自检，任一项不过即不得调用写入：

| # | 校验项 | 数据来源 | 不通过时 |
| :---: | --- | --- | --- |
| 1 | 表单可新增 / 可编辑 | `getBizObjectSchemaAcl` 的 `addable` / `editable` / `removable` | 停止，告知用户无相应权限 |
| 2 | 每个字段的可写性与必填性 | acl 的 `required` **交叉** schema 的 `disposition` | 业务必填项须补值；系统必填与不可写字段须剔除 |
| 3 | 字段名是否存在于 schema，格式是否与控件匹配 | `getBizObjectSchema` 的 `fieldType` / `inputType` | 修正后再提交 |
| 4 | 无 `null`、空字符串、空数组、未知字段、系统字段 | 对照 schema 字段清单 | 剔除后再提交 |
| 5 | 人员、部门、关联记录、附件均已解析为 ID | `getOrgIdByName` / `getBizObjectIdsByNames` / `transferFile` | 先解析再提交 |
| 6 | 已向用户声明字段与值并获得确认 | — | 等待用户确认 |
| 7 | 文本类字段长度未超上限 | 字段控件类型与「文本长度上限」 | 先说明超限字段与建议处理方式（截断 / 拆分 / 改存附件），获用户同意后再处理 |

### 文本长度上限（提交前必查）

文本控件有硬性长度上限，**超长会直接返回 `invalid_parameter`**，且属于最常见的隐性失败原因之一。提交前按控件类型逐项核对：

| 控件类型 | 上限 | 典型 `fieldType` / `inputType` | 超限处理 |
| --- | :---: | --- | --- |
| **单行文本** | **≤ 200 字符** | `text`（`inputType: text`）、单行输入框 | 必须压缩到 200 字符内：优先精简措辞；信息确实不可丢时，改为写入长文本字段、附件或备注，并告知用户 |
| **多行文本** | **≤ 10000 字符** | 多行文本 / 备注 / 描述类控件 | 超过 1 万字符时拆分到多个字段（如「描述」+「备注」），或改为附件承载全文 |

> - 字符数按实际字符计（中文 1 字 = 1 字符，不是字节数）；换行符计入。
> - 若 `getBizObjectSchema` 的返回体带 `maxLength` 等长度属性，**以其为准**（表单可配置时可能小于上述默认值）；未返回时按本表默认上限执行。
> - **不得**为了"先提交成功"而在用户不知情的情况下擅自截断文本；截断、改写或转字段前须向用户说明并获同意。

### 静态校验定位不了时的处理

若完成上表 1–5、7 项后仍无法确定失败原因，**不得直接发起真实写入**，按以下顺序处理：

1. **停下来向用户说明**：已排除哪些可能、还剩哪些假设、需要用草稿数据验证哪一点、拟调用哪个接口、拟写入什么数据、预计产生几条记录；
2. **征求用户同意**：明确请求用户确认是否允许发起该次验证写入——**未获用户明确同意前，不得调用任何写入接口**。不得以"只试一次""不会留数据"为由跳过询问；
3. 获同意后的探测同样受限：**单次不超过 3 条**；**不得**使用 `createBizObjects` 批量接口探测；文本主字段统一加 `[TEST-YYYYMMDD]` 前缀，便于检索；
4. 探测产生的记录，须在**同一轮对话内**列出 `bizObjectId` 清单，请用户确认后删除。

### 失败后禁止的动作

- **禁止原样重试**：报错后不得直接重发同一请求。写入类接口可能产生重复记录；`transferFile` 明确非幂等，结果未知时禁止自动重试。
- **禁止连续换参数试错**：每次修改字段或格式后，须重新走「写入前置校验」并**重新向用户声明确认**，不得边试边猜。同一字段连续试探 2 次仍失败时，必须停止写入、改为向用户报告诊断结论。
- 先做静态归因，再决定是否需要重新写入。

## 可用工具

> 工具名对应：本 Skill 使用短名（如 `createBizObject`），MCP 实际工具名为 `h3yun_` 前缀 + 短名的 snake_case 形式，例如 `h3yun_create_bizobject`、`h3yun_get_bizobject_schema`、`h3yun_transfer_file`、`h3yun_get_bizobject_schema_acl`。

### listApps - 获取可访问应用

分页获取当前用户有权限访问的应用。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 1 开始 |
| pageSize | number | 是 | 每页数量 |

**返回值**：`data: { total: number, data: AppDetail[] }`。

**示例**：`{ "pageIndex": 1, "pageSize": 20 }`

### searchApps - 按名称搜索可访问应用

按应用名称关键字分页查询当前用户有权限访问的应用。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 0 开始 |
| pageSize | number | 是 | 每页数量 |
| keyword | string | 是 | 应用名称关键字 |

**返回值**：`data: { total: number, data: AppDetail[] }`。

**示例**：`{ "pageIndex": 0, "pageSize": 20, "keyword": "CRM" }`

### searchFormNode - 搜索表单

按名称关键字分页查询可访问表单；已知应用时传 `appCode` 缩小范围。

> 💡 **枚举某个应用下的全部表单**：`keyword` 为必填，但可传**全角空格** `　`（U+3000）作为「不过滤」占位符，配合 `appCode` 即可列出该应用下**全部**表单（实测可拿到 58 张）。传半角空格或空字符串会失败（返回 `h3yun.read.service_unavailable`）。
> ⚠️ 本工具只匹配**表单名**，不匹配应用名——想按应用找表单必须用 `appCode`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 0 开始 |
| pageSize | number | 是 | 每页数量 |
| keyword | string | 是 | 表单名称关键字 |
| appCode | string | 否 | 应用编码 |

**返回值**：`data: { total: number, data: FunctionNode[] }`。

**示例**：`{ "pageIndex": 0, "pageSize": 20, "keyword": "请假", "appCode": "APP_DEMO" }`

### getBizObjectSchema - 获取表单定义

获取表单字段及子表定义。业务数据读写前必须调用，以返回的字段编码作为 `bizObject` 的键。

> 📍 **两个工具的调用顺序：本工具先调（第 ① 步），`getBizObjectSchemaAcl` 后调（第 ② 步）。** 创建、更新、删除前固定按此顺序，见「字段可写性与必填判定」。
> 每个字段的 `writeInput` 说明**该字段由谁写入**：`disposition: "callerInput"`（附 `inputType`，由调用方传值）或 `"notAccepted"`（附 `reason`，由系统或公式接管，禁止传值）。
> ⚠️ 本工具**不反映当前用户的权限**，也无法单独判断「必填」——必须与 `getBizObjectSchemaAcl` 的 `required` **交叉判定**，见「字段可写性与必填判定」。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |

**返回值**：`data: BizObjectSchema`。

**示例**：`{ "schemaCode": "D0000001" }`

### getBizObjectSchemaAcl - 获取表单权限

获取当前用户的表单新增、编辑、删除权限和字段级权限。

> 📍 **两个工具的调用顺序：`getBizObjectSchema` 先调（第 ① 步），本工具后调（第 ② 步）。** 先拿到表单定义（字段全集与 `disposition`），本工具返回的 `required` 才能当场定性；顺序颠倒会把 `OwnerId` 这类系统字段误读成「要我传值」，见「字段可写性与必填判定」。
> **本工具是权限与必填的权威**：`schemaAcl` 的 `addable` / `editable` / `removable` 决定当前用户能否操作；`fieldPermissions` 的 `required` 表示该字段**必须有值**——**表单定义的必填项在这里依然是必填**。
> ⚠️ 但 `required: true` 不区分「业务必填」与「系统自动填」，须与 `getBizObjectSchema` 的 `writeInput.disposition` **交叉判定**才能确定该不该传值，见「字段可写性与必填判定」。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |

**返回值**：`data: SchemaPermissionResult`。

**示例**：`{ "schemaCode": "D0000001" }`

### createBizObject - 新增单条业务数据

创建一条记录；流程表单且 `submit: true` 时会发起流程。

> 📍 **调用顺序（创建前必做）**：先 `getBizObjectSchema`（表单定义）→ 再 `getBizObjectSchemaAcl`（权限与必填）→ 交叉判定后组装 `bizObject`。顺序不可颠倒，见「字段可写性与必填判定」。
> ⚠️ **执行前必须确认**：调用前须向用户声明将写入的字段与值（`bizObject`），并明确请求「确认」后再执行。
> ⚠️ **禁止用于联调探测**：不得为排查字段或格式问题而反复调用本接口，规则见「写入前置校验」。
> ✅ **成功后必须回执**：除 `bizObjectId` 外，必须返回详情链接，见「写入结果回执」。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObject | WriteBizObject | 是 | 字段编码到字段值的对象 |
| submit | boolean | 是 | `false` 创建草稿；`true` 创建生效数据或发起流程 |

**返回值**：`data: { bizObjectId: string }`。

**示例**：

```json
{
  "schemaCode": "D0000001",
  "bizObject": {
    "F0000002": "年假申请",
    "F0000003": 2,
    "F0000010": ["user_001"]
  },
  "submit": true
}
```

### createBizObjects - 批量新增业务数据

批量创建记录。检查返回的失败项；不要将部分成功表述为全部成功。

> 📍 **调用顺序（创建前必做）**：先 `getBizObjectSchema`（表单定义）→ 再 `getBizObjectSchemaAcl`（权限与必填）→ 交叉判定后组装 `bizObjectArray`。顺序不可颠倒，见「字段可写性与必填判定」。
> ⚠️ **执行前必须确认**：调用前须向用户声明批量条数及每条关键字段值，并明确请求「确认」后再执行。
> ⚠️ **禁止用于联调探测**：不得用本接口探测字段或格式；确需探测时单次不超过 3 条、须用户同意，且优先改用单条接口。
> ⚠️ **批量写入兜底**：若所在连接器未提供本批量接口，可改用「并行单条 `createBizObject`」实现批量写入，写入前仍须先 `getBizObjectSchema` + `getBizObjectSchemaAcl` 静态判定，并逐条检查成功 / 失败。
> ✅ **成功后必须回执**：逐条输出成功项的详情链接；失败项单独列出 ID 与原因。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectArray | WriteBizObject[] | 是 | 待创建的数据列表 |

**返回值**：`data: { successBizObjectIds: string[], failedBizObjectIds: string[] }`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectArray": [{ "F0000002": "记录一" }] }`

### removeBizObject - 删除单条业务数据

删除指定业务数据。删除属不可逆操作。

> ⚠️ **执行前必须确认**：调用前须向用户声明目标记录 ID（`bizObjectId`）与所属表单，并明确请求「确认」后再执行；未获确认不得删除。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectId | string | 是 | 业务数据 ID |

**返回值**：`data: {}`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectId": "bo_001" }`

### removeBizObjects - 批量删除业务数据

批量删除记录，属不可逆操作。调用前确认完整 ID 列表，并检查成功与失败项。

> ⚠️ **执行前必须确认**：调用前须向用户声明全部待删 ID 列表与所属表单，并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectIds | string[] | 是 | 待删除记录 ID 列表 |

**返回值**：`data: { successBizObjectIds: string[], failedBizObjectIds: string[] }`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectIds": ["bo_001", "bo_002"] }`

### updateBizObject - 更新单条业务数据

更新指定记录。只传要更新的字段；字段值遵循 `WriteBizObject` 规则。

> 📍 **调用顺序（更新前必做）**：先 `getBizObjectSchema`（表单定义）→ 再 `getBizObjectSchemaAcl`（权限与必填）→ 交叉判定后组装待更新字段。顺序不可颠倒，见「字段可写性与必填判定」。
> ⚠️ **执行前必须确认**：调用前须向用户声明目标记录 ID（`bizObjectId`）与将变更字段，并明确请求「确认」后再执行。
> ⚠️ **禁止用于联调探测**：不得为排查字段或格式问题而反复调用本接口，规则见「写入前置校验」。
> ✅ **成功后必须回执**：用传入的 `bizObjectId` 构造详情链接，见「写入结果回执」。
> ⚠️ **不支持子表更新**：`updateBizObject` 不能写入或修改子表行，含子表变更需在 `createBizObject` 创建时一次性写入，或重建记录。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectId | string | 是 | 业务数据 ID |
| bizObject | WriteBizObject | 是 | 待更新字段对象 |

**返回值**：`data: {}`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectId": "bo_001", "bizObject": { "F0000003": "3" } }`

### getBizObject - 查询单条业务数据

根据表单编码和业务数据 ID 查询一条记录。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectId | string | 是 | 业务数据 ID |

**返回值**：`data: { schemaCode: string, valueTable: SingleQueryBizObject }`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectId": "bo_001" }`

### queryBizObjectList - 筛选业务数据

使用 SQL 查询单表数据。不支持子表字段；SQL 表名必须为 `i_${schemaCode}`，并且必须带 `LIMIT`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| sql | string | 是 | 单表查询 SQL |

**返回值**：`data: BatchQueryBizObject[]`。

**示例**：

```json
{
  "schemaCode": "D0000001",
  "sql": "SELECT * FROM i_D0000001 LIMIT 20"
}
```

### getBizObjectNamesByIds - 按 ID 获取业务数据名称

批量解析业务数据 ID 为名称。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| bizObjectIds | string[] | 是 | 业务数据 ID 列表 |

**返回值**：`data: Array<{ name: string, id: string }>`。

**示例**：`{ "schemaCode": "D0000001", "bizObjectIds": ["bo_001", "bo_002"] }`

### getOrgNamesByIds - 按 ID 获取人员或部门名称

批量解析人员或部门 ID。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| ids | string[] | 是 | 人员或部门 ID 列表 |

**返回值**：`data: Array<{ name: string, id: string, type: "user" | "dept" }>`。

**示例**：`{ "ids": ["user_001", "dept_001"] }`

### getBizObjectIdsByNames - 按名称获取业务数据 ID

在指定表单内按名称查找记录。名称可能不唯一，返回多个候选时请用户确认。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| schemaCode | string | 是 | 表单编码 |
| names | string[] | 是 | 业务数据名称列表 |

**返回值**：`data: Array<{ name: string, bizObjectId: string }>`。

**示例**：`{ "schemaCode": "D0000001", "names": ["张三"] }`

### getOrgIdByName - 按名称获取人员或部门 ID

按名称查找一个人员或部门。存在同名结果或用户指代不明确时，请求用户确认，不要自行选择。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| name | string | 是 | 人员或部门名称 |
| type | string | 是 | `user` 表示人员；`dept` 表示部门 |

**返回值**：`data: { orgId: string }`。

**示例**：`{ "name": "人力资源部", "type": "dept" }`

### transferFile - 转存附件

将远程文件转存为氚云表单附件，返回可写入附件或图片字段的 `fileId`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| fileUrl | string | 是 | **可公开访问的 HTTPS 文件地址**；禁止携带用户信息（`user:pass@`）与 URL fragment（`#...`） |

**返回值**：`data: { fileId: string }`。

**示例**：`{ "fileUrl": "https://example.com/files/contract.pdf" }`

> ⚠️ **调用约束（必须遵守）**：
> - 只接受**远程 HTTPS 地址**。本地文件由 **Agent 自行**转为公网可直接下载的 HTTPS 直链后直接调用本接口——**不得**就此向用户提问、不得让用户自行上传或自行转链；
> - 地址须**无需登录、无需鉴权**即可被氚云服务端 GET 到；禁止传入带用户信息（`user:pass@`）或 URL fragment 的地址；
> - 调用会**立即产生未绑定附件记录**（属脏数据），因此只在确定要写入该附件时才调用；
> - **非幂等**：结果未知时**禁止自动重试**，须先确认上一次是否已成功。

### getTodoList - 获取用户待办

分页获取当前用户的待办工作项。处理审批前必须调用，以确认工作项及其状态。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| pageIndex | number | 是 | 页码，从 0 开始 |
| pageSize | number | 是 | 每页数量 |

**返回值**：`data: WorkItem[]`。

**示例**：`{ "pageIndex": 0, "pageSize": 20 }`

### getTodosCount - 获取用户待办数量

仅需要待办数量时调用。

**参数**：无。

**返回值**：`data: number`。

**示例**：`{}`

### batchApprove - 批量审批业务数据

对待办集合执行同意或不同意操作；单次最多 10 条。审批属不可逆操作。

> ⚠️ **执行前必须确认**：调用前须向用户声明每条待审批工作项、动作（`Submit` / `Reject`）与意见，并明确请求「确认」后再执行。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | :---: | --- |
| workItemIds | string[] | 是 | 工作项 ID 列表，最多 10 项 |
| comment | string | 是 | 审批意见 |
| action | string | 是 | `Submit`（同意）或 `Reject`（不同意） |

**返回值**：`data: { successWorkItemIds: string[], failedWorkItemIds: string[] }`。

**示例**：

```json
{
  "workItemIds": ["wi_001", "wi_002"],
  "comment": "同意",
  "action": "Submit"
}
```

## 附件字段写入流程

附件、图片字段（`fieldType` 为 `attachment` / `image`）**不能**直接传本地路径或普通 URL，必须走四步：

| 步骤 | 动作 | 责任方 |
| :---: | --- | --- |
| 1 | 把本地文件转为**公网可直接下载（无需登录、无需鉴权）的 HTTPS 直链** | **Agent 自行完成** |
| 2 | 调用 `transferFile`，拿到 `fileId` | Agent |
| 3 | 把 `fileId` 以**数组**形式写入附件字段，如 `{ "resumefile": ["file_001"] }` | Agent |
| 4 | 写入成功后，回执中告知用户本次转存的附件名与目标记录链接 | Agent |

> - **转链是 Agent 的职责，不是用户的选择题。** 用户提供本地文件时，Agent 直接自行转公网链接并继续 `transferFile`，**不得**询问「你是自己上传附件，还是自己转成公网链接」，**不得**要求用户先自行把文件传到某个网盘或图床再回来。此类询问一律视为未完成任务。
> - 用户已给出**公网可下载的 HTTPS 直链**时，跳过步骤 1，直接 `transferFile`。
> - 单个附件也传数组，不要传裸字符串。
> - 多附件：逐个执行步骤 1–2 拿到 `fileId`，最后一次性写入 `fileId` 数组。
> - 生成的直链只需满足「氚云服务端可公开 GET 到该文件」，无需先请用户确认链接本身；但须在回执中列出实际转存的文件名，便于用户核对是否传错文件。
> - 若确实无法生成公网直链（如文件位于内网、超出体积上限、格式不受支持），须**说明具体技术原因**并给出下一步建议（如请用户将文件放到可访问位置后重试），**不得**把「自行上传 / 自行转链」作为并列选项抛回用户。

## 写入结果回执

`createBizObject` / `createBizObjects` / `updateBizObject` 成功后，**必须**把详情链接返回给用户，不能只给 `bizObjectId`：

```
已写入「{表单显示名}」
- bizObjectId：{bizObjectId}
- 详情：https://www.h3yun.com/nx/form-detail?schemaCode={schemaCode}&bizObjectId={bizObjectId}
- 状态：{草稿 / 已提交}
```

- 批量新增：逐条输出成功项的链接；失败项单独列出 ID 与原因，**不得**把部分成功表述为全部成功。
- 更新：用传入的 `bizObjectId` 构造链接。

## 关键类型与写入规则

### BizObjectSchema 与权限

- `BizObjectSchema`：`{ schemaCode, displayName, description, fields }`；每个字段含 `fieldType`、`fieldCode`、`displayName` 与 `writeInput`。
- **`writeInput` 说明字段由谁写入**：
  - `disposition: "callerInput"` → 调用方可写，按 `inputType` 传值；
  - `disposition: "notAccepted"` + `reason`（`systemGenerated` / `computed`）→ **不可写**，禁止出现在 `bizObject` 中。
- `SchemaAcl`：`addable`、`editable`、`removable` 分别表示是否可新增、编辑、删除。
- `SchemaPermissionResult.fieldPermissions` 给出字段的 `visible`、`editable` 与 `required`。**`required` 表示该字段必须有值**；与 `disposition` 交叉后才知该由谁提供（见「字段可写性与必填判定」）。
- **判定顺序**：① acl 定「能否操作」→ ② acl `required` × schema `disposition` 定每个字段「必填 / 可选 / 不可写」→ ③ schema `inputType` 定值格式。

### WriteBizObject

`WriteBizObject` 是 `{ [fieldCode: string]: value }`。字段键以 `getBizObjectSchema` 返回的字段编码为准。

| 控件 | 写入类型 | 规则 |
| --- | --- | --- |
| **单行文本** | string | **≤ 200 字符**，超长返回 `invalid_parameter`。超限须先与用户确认后压缩或改存他处 |
| **多行文本** | string | **≤ 10000 字符**，超长返回 `invalid_parameter`。超限须先与用户确认后拆分或改存附件 |
| 日期、下拉、单选、单关联 | string | — |
| 数字 | **number（数值类型）** | 传 JSON 数值（如 `18000`），**不要**传字符串 `"18000"`（会报 `invalid_parameter`） |
| 复选框 / 多选（multiSelect） | string | 多值用英文分号拼接，如 `"A;B"`；数组形式不被接受 |
| 是/否 | boolean | 使用 `true` / `false` |
| 人员、部门 | string / string[] | 单选传单个 ID，多选传 ID 数组。传组织架构 ID（`getOrgIdByName` / `getOrgNamesByIds` 返回的 id） |
| **附件、图片** | **string[]** | 传 `transferFile` 返回的 `fileId` 数组；单个附件也传数组。流程见「附件字段写入流程」 |
| 关联表单多选 | string[] | 传关联业务数据 ID 数组 |
| 地址、定位 | string | 分别传对应对象序列化后的 JSON 字符串 |
| 子表 | WriteBizObject[] | 数组的每个元素是一行子表数据。**子表只能在 `createBizObject` 创建时写入；`updateBizObject` 不支持子表行，修改子表需重建记录**。 |
| 拥有者（`OwnerId`）、所属部门（`OwnerDeptId`） | 视连接器而定 | 多数连接器下由系统自动填充、禁止传入；但**部分连接器要求显式传合法组织 ID**（以 `getBizObjectSchema` 的 `disposition` + `getBizObjectSchemaAcl` 的 `required` 为准，见「字段可写性与必填判定」四态表）。可写且必填时必须传，否则报 `invalid_parameter`。 |
| 创建人、修改人、创建时间、修改时间、Status、WorkflowInstanceId、ObjectId、Name | 不可写 | **系统字段，禁止出现在 `bizObject` 中**；传入会返回 `invalid_parameter`（参数值不合法）。创建后由系统自动填充。 |
| 公式、汇总字段 | 不可写 | **字段名与普通业务字段无异**（如「报价总金额」「冲销金额」），但由公式 / 汇总自动计算。判定：`disposition = "notAccepted"` 且 `reason = "computed"`。 |

### 查询结果

- `getBizObject` 返回 `SingleQueryBizObject`：人员、部门、创建人、拥有者及所属部门的直接字段值可为 `{ id, name, type }`，多选字段为该对象数组。结果也可能带 `${fieldCode}Object` 扩展对象，含 `ObjectId`、`Name`、`EntryId`；优先使用直接字段值，兼容读取扩展字段。
- `queryBizObjectList` 返回 `BatchQueryBizObject[]`：不支持子表字段，也不返回组织机构扩展字段。
- `WorkItem` 包含 `workItemId`、`schemaCode`、`bizObjectId`、`activityName`、`summary`、`taskState`、`originatorName` 与 `fastApprove` 等信息。

## 常见错误及处理

> 连接器 MCP 返回的 `code` 是**语义码**（如 `h3yun.request.invalid_parameter`），其 `message` 即中文字面原因，与下表 API 数字错误码属同一套错误家族。两套编码同时出现时，优先按 `message` 定位。

| 错误码 | 处理建议 |
| --- | --- |
| 100100 | 检查网络后重试。 |
| 100200 | 请求过于频繁，稍后重试。 |
| 100300-100307、`h3yun.request.invalid_parameter`（参数值不合法） | **先静态归因，不要重试**。按序排查：① 是否误传了不可写的系统字段（`CreatedBy` / `CreatedTime` / `ObjectId` / `Name` 等；注意 `OwnerId` / `OwnerDeptId` 是否可写以 `getBizObjectSchema` 的 `disposition` 为准，可写时反而**必须传**）→ ② 是否传了公式 / 汇总字段（`reason` 为 computed，名字看不出来）→ ③ **文本是否超长（单行 > 200 或 多行 > 10000 字符）** → ④ 是否有未知或首版未开放字段 → ⑤ 字段值格式与控件类型不匹配（如数字传了字符串、多选传了数组）→ ⑥ 业务必填项漏传 → ⑦ 传了 `null` / 空字符串 / 空数组。排查手段见「写入前置校验」。**需以调用验证时，须先征得用户同意，不得自行反复试错。** |
| 100400、100401 | 提示用户重新登录或刷新登录凭证。 |
| 100402 | 告知用户无权执行此操作。 |
| 100500-100502 | 服务或上游暂不可用，稍后重试。 |
| 200104、200204、200206、200302 | 应用、表单、业务数据或待办不存在；重新确认标识。 |
| 200105、200205、200303 | 用户无相应的访问或处理权限。 |
| 200201、200207、200208 | 补全必填字段，并按表单定义校验字段值。 |
| 200202、200203 | 当前记录不可删除，或字段不允许修改。 |
| 200210、200211 | 修正业务数据筛选或排序条件。 |
| 200304、200305、200306 | 待办不可处理、动作不合法或部分审批失败；重新查询待办并逐项处理。 |
| 200401 | 未找到人员或部门；重新确认名称和类型。 |
| 200501 | 未找到匹配地址信息。 |
| 200601、200602 | 文件 URL 不可访问或转存失败。Agent 自行重新生成**可公开访问的 HTTPS 直链**（无用户信息与 fragment、无需鉴权）后再次转存；`transferFile` 非幂等，**禁止自动重试**，须先确认上一次是否已成功。**不得**因转存失败就要求用户自行上传或自行转链。 |

## 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 1.3.0 | 2026-10-20 | 试探写入须先征得用户同意；附件转链由 Agent 自行完成；新增文本长度限制（单行 200 / 多行 10000）。 |
| 1.2.2–1.2.3 | 2026-10-19 | 新增数据写入规则，重构为通用技能并去除环境限定表述。 |
| 1.1.0–1.2.1 | 2026-09-16 | 完善字段可写性判定、写入校验、附件流程与回执规范。 |
| 1.0.0 | — | 初始版本。 |
