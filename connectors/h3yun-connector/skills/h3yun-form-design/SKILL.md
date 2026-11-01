---
name: h3yun-form-design
description: Use when a user needs to design or restructure H3Yun applications at design time — create/modify/rename applications, forms, fields, or form groups, reorganize forms into groups, or refresh the design cache. This is the structural/canvas counterpart of h3yun-form-workflow (which handles business-data CRUD). Triggers on requests like "create an H3Yun app", "add a field to a form", "rename the app", "group these forms", "refresh the cache", or any schema/form design task.
version: "1.0.1"
author: WorkBuddy
---

# 氚云设计时（应用 / 表单 / 字段 / 分组搭建）Skill

本 Skill 负责氚云的**设计态（结构）**操作：应用的创建/改名、表单（schema）的创建/改字段、字段的增改、表单分组的创建与整理、设计时缓存刷新。

> ⚠️ **与 h3yun-form-workflow 的分工**：本 Skill 改「结构」（应用/表单/字段/分组），h3yun-form-workflow 改「数据」（业务记录的增删改查与审批）。用户若在谈"某条记录/某笔数据"，交给 h3yun-form-workflow；在谈"建应用/加字段/分组/改名"，用本 Skill。

> 📍 **工具名映射**：本 Skill 使用驼峰短名（如 `createApp`）；MCP 实际工具名为 `h3yun_` 前缀 + 短名的 snake_case（如 `h3yun_create_app`）。下文统一用短名，调用时按实际接入的连接器展开。

---

## 强制工作流（四步，不可跳步）

### 步骤 1：识别用户意图

- 判定请求属于**设计态（结构）**还是**数据态（记录）**。结构类 → 本 Skill；数据类 → h3yun-form-workflow。
- 锁定目标对象：涉及哪个应用 / 表单 / 字段 / 分组。
- 用户只给名称（不给编码）时，**先检索再使用**：用 `searchApps` / `searchFormNode` / `searchFormGroup` 拿到编码，**禁止猜测** `appCode` / `schemaCode` / 分组编码 / 字段编码。

### 步骤 2：梳理需求 + 与用户确认（关键闸门）

- **先判断是否需要表单分组**，再按「完整应用方案」的粒度做设计，而不是零散罗列字段：
  - **需要分组**（表单 ≥3 张，或跨职能/跨阶段）：给出**分组清单**（分组名 + 归入的表单），并说明每个分组的业务含义。
  - **不需要分组**（单表或极简场景）：明确声明"平铺到根目录、不建分组"，避免用户事后才发现缺分组。
- 输出**完整应用方案**，至少覆盖：
  1. **应用**：应用名、应用编码（裸 code，后续会加前缀）。
  2. **分组**（若有）：分组名、包含哪些表单。
  3. **表单**：每张表的名称、角色定位（主表 / 枢纽 / 明细）、归属分组。
  4. **字段**：每张表的字段清单（code、名称、类型、是否必填、下拉选项、默认值）。
  5. **跨表关联**：`refSingle`/`refMulti` 谁指向谁，据此给出**创建拓扑顺序**。
- 把方案呈现给用户，**明确请求确认**。**只有用户确认需求内容后，才允许调用任何写入/修改类工具。**
- 修改类需求（改字段、加选项、改名、调分组）同样要先给出"变更前 → 变更后"的对照，确认后再执行。
- **删除类操作二次确认（硬性规则）**：凡是涉及删除（`removeApp` / `removeFormGroup` / `removeSchema` / `deleteField`），在用户确认需求清单之外，**还必须等待用户单独输入确切短语「我已知晓风险」**后方可执行。
  - 未收到该短语，**禁止**调用任何删除类工具，即使用户已"大致同意"或"你看着办"。
  - **禁止**未经用户同意自行删除，也**禁止**把一次笼统的"确认"当作覆盖了你没有单独列出的删除项。
- 约束：**绝不**在用户未确认前执行写入；**绝不**主动删除。

### 步骤 3：调用设计时工具执行

- **严格按「应用 → 分组 → 表单 → 字段」的层级顺序依次生成**，每层拿到返回码再进入下一层：
  1. **应用层**：`createApp` → 取**最终应用编码**；已有应用则 `updateApp` 改名，或直接沿用其编码。
  2. **分组层**（仅在需要分组时）：逐个 `createFormGroup` → 记录每个**分组编码**（系统 hash，非前缀式，务必逐个保存）。
  3. **表单层**：按依赖拓扑逐张 `createSchema`（无外键的表先建，取最终编码后再建引用它的表）；需要归组的，在 `createSchema` 时直接带上对应的 `moduleCode`。
  4. **字段层**：表单已存在时，用 `addFields` 追加、`updateFields` 修改、`deleteField` 删除（删除须走步骤 2 闸门）。
- **每一层执行完核对返回**：编码是否带前缀、是否为预期值；对不上立即停止并报告，不要带着错误编码继续往下建。
- **非幂等调用**（`createApp` / `createSchema` / `createFormGroup` / `addFields` / `updateFields` / `updateApp` / `updateSchema` / 全部删除类）：超时或断网时结果未知，**禁止自动重试**——先查询确认上一次是否成功，再决定是否补做。
- 同一层内若**无相互依赖**（如几张只引用同一枢纽表的明细表），可并行；有依赖关系的必须串行。

### 步骤 4：收尾——刷新缓存 + 返回预览地址

- 全部结构调整完成后，**调用一次 `refreshDesignCache`**。
- 返回预览地址（每个表单一条，或主表单一条）：

  ```
  https://{域名}/nx/application/{应用编码}/{表单编码}
  ```

  - ⚠️ **呈现方式（务必遵守）**：返回地址时**用 Markdown 链接 `[名称](完整URL)` 逐条列出，不要放进代码块或纯文本**。代码块会把 URL 渲染成等宽纯文本、不可点击；直接给出可点击链接用户才能一键打开。示例：

    ```
    - 应用首页：[人事管理验证应用](https://www.h3yun.com/nx/application/D00018hr_verify_app)
    - 员工信息表：[D00018hr_employee](https://www.h3yun.com/nx/application/D00018hr_verify_app/D00018hr_employee)
    ```

  | 变量 | 取值 |
  | --- | --- |
  | `{域名}` | 线上预览域名：`www.h3yun.com` |
  | `{应用编码}` | `createApp` 返回的**最终应用编码**（带前缀，如 `D00018zmt_tf_app`） |
  | `{表单编码}` | `createSchema` 返回的**最终表单编码**（带前缀，如 `D00018plan`） |

- 若用户此前报过"无权限访问"：刷新缓存只能修复**元数据滞后**；若刷新后仍"无权限"，属真实 ACL 问题，需在控制台 **应用管理 → 权限/成员** 把账号或角色加入并赋权（缓存刷不掉授权问题）。

---

## 环境说明

- **预览域名**：以实际接入的连接器对应域名为准，线上环境为 `www.h3yun.com`。
- **最终编码 = 开发者前缀（如 `D00018`） + 自建 code**，确定可复现。引用他表时，`refSingle`/`refMulti` 的 `targetModelCode` 必须填**带前缀的最终编码**。
- 分组编码由系统生成（hash，非前缀式），`createFormGroup` 返回后需自行记录。

---

## 工具调用顺序（设计依赖）

跨表关联字段（`refSingle`/`refMulti`）的 `targetModelCode` 必须指向目标表的**最终编码（带前缀）**，而最终编码只有目标表建完才拿得到。因此**引用其他表的字段必须等目标表创建并取到返回码之后再建**——这是串行拓扑，不能并行。

典型拓扑：

```
应用(createApp)
  ├─ 被引用表（如 品牌/客户、账号）createSchema   ← 无外键，先建
  │     └─ 返回最终编码
  ├─ 枢纽表（如 投流方案）createSchema           ← refSingle 指向上面的表
  │     └─ 返回最终编码
  └─ 明细表（如 预算/ROI/任务）createSchema       ← refSingle 指向枢纽表
```

分组（`moduleCode`）只能在 `createSchema` 时指定，且分组须已存在（`createFormGroup` 先建并取返回码）。**已存在的表单无法直接"移动"到分组**：要么创建时就带 `moduleCode`，要么删除后重建（本 Skill 无"移动表单"接口）。无业务数据时删后重建是安全做法。

---

## 工具速查与注意事项

### createApp — 创建应用

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `code` | 是 | ≤30 字符，仅字母/数字/下划线，不能为纯数字 |
| `displayName` | 是 | 去首尾空格后 2–32 字符 |

- **返回带开发者前缀的最终应用编码**（如 `D00018zmt_tf_app`）。后续所有 `createSchema` 的 `appCode` 用这个**最终编码**，不要用你传入的裸 code。
- 非幂等，禁止自动重试。

### createSchema — 创建表单并初始化字段

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `schemaCode` | 是 | ≤43 字符，字母/数字/下划线，不能以数字开头，不能等于应用编码 |
| `schemaName` | 是 | 2–32 字符 |
| `appCode` | 是 | 用 `createApp` 返回的**最终应用编码** |
| `fields` | 是 | 字段数组（见下「字段类型与 extendInfo 要点」） |
| `moduleCode` | 否 | 分组编码；省略则放根目录。传入时必须已存在 |

- **一次性建表 + 字段，非幂等，禁止自动重试。**
- ⚠️ **`refSingle`/`refMulti` 的 `targetModelCode` 必须是目标表的「最终编码（带前缀）」**——所以被引用表要先建。
- ⚠️ **系统保留字段编码不可用**：如 `status` 会被拒（报"编码不能为空/系统保留编码"）。自定义状态字段改用 `planStatus` / `taskStatus` 等。
- ⚠️ **`number` 默认无小数**：需显式 `decimalPlaces`，否则整数位会被截断。
- ⚠️ **`date` / `dateTime` 无需 `extendInfo`**（仅 `dateTime` 可用 `format`）。
- 返回最终表单编码（带前缀）。

### addFields — 向已有表单追加字段

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `schemaCode` | 是 | 表单最终编码 |
| `fields` | 是 | 待新增字段数组 |

- 字段类型与 `createSchema` 一致；保留编码、`number` 小数位等约束同样适用。
- 非幂等，禁止自动重试。

### updateFields — 修改已有字段定义

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `schemaCode` | 是 | 表单最终编码 |
| `fields` | 是 | 字段数组，需提供**完整字段对象**（code / name / type / extendInfo） |
| `subModelCode` | 否 | 子表编码；空表示主表字段 |

- 常用于**给下拉（selectSingle/radio/checkbox）增加选项**：把 `options` 改成包含新项的完整列表，`defaultValue` 维持原值即可。
- 改选项不影响已有数据（旧选项仍有效，新选项变为可选）。
- 非幂等，禁止自动重试。

### updateSchema — 仅改表单显示名

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `schemaCode` | 是 | 表单最终编码 |
| `displayName` | 是 | 新显示名（2–32 字符），同步更新功能节点名 |

- ⚠️ **只能改名，不修改字段、不改页面配置、不能移动分组**。要改字段用 `updateFields`；要改分组只能删后重建（见「工具调用顺序」）。

### updateApp — 修改应用属性

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `code` | 是 | 应用最终编码 |
| `displayName` | 否 | 新显示名 |

- 改名后建议 `refreshDesignCache` 让控制台生效。

### createFormGroup — 创建表单分组

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 2–32 字符，不含控制字符 |
| `appCode` | 是 | 应用最终编码 |

- 返回**分组编码（系统 hash，非前缀式）**，需记录，供 `createSchema` 的 `moduleCode` 使用。
- 非幂等，禁止自动重试。

### updateFormGroup — 修改分组名

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| （分组编码 + 新名称） | 是 | 具体以工具 schema 为准 |

- 仅改名；不能调整分组层级或归属。

### removeSchema / removeFormGroup / removeApp / deleteField — 删除（破坏性，强闸门）

- **全部属于删除操作，必须走步骤 2 的二次确认**：用户确认需求清单 **且** 单独输入「我已知晓风险」后才可执行；否则**禁止调用**。
- 删除有依赖顺序：先删被引用方？不——**先删引用方（叶子），再删被引用方**。例如表单被其他表 `refSingle` 引用时，应先删引用表，再删被引用表，否则可能报"被引用无法删除"。
- `removeSchema` 删除表单会一并清除其字段与数据（若有）；`deleteField` 删除字段会丢失该字段数据；均不可逆。
- 非幂等，禁止自动重试。

### searchApps / searchFormNode / searchFormGroup — 只读检索

- `searchApps`：按应用名关键字分页查应用。
- `searchFormNode`：按表单名关键字查表单，`appCode` 可缩小范围（只匹配表单名，不匹配应用名）。
- `searchFormGroup`：按分组名关键字 / `appCode` / `code` 查分组。
- 用途：步骤 1 锁定目标编码、步骤 3/4 前后做校验。只读，无风险。

### getBizObjectSchema / getBizObjectSchemaAcl — 读结构（改字段前建议先看）

- 修改字段前，建议先用 `getBizObjectSchema` 确认当前字段编码、类型、子表结构；用 `getBizObjectSchemaAcl` 确认字段是否可写/必填。避免改出一个不存在或不可写的字段。

### refreshDesignCache — 刷新设计时缓存

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| （无） | — | 刷新应用、分组、表单、表单字段的缓存 |

- 步骤 4 必做：所有结构调整完后调用一次，使控制台立即反映变更。
- ⚠️ **只修复元数据滞后，不修复 ACL 权限问题**。"无权限访问"刷新后仍出现 = 真实授权缺失，需在控制台应用管理加成员。

---

## 字段类型与 extendInfo 要点

支持的类型与 `extendInfo`（每个都必须带 `discriminator`）：

| type | extendInfo 要点 |
| --- | --- |
| `shortText` / `bool` / `date` / `location` / `staffSingle` / `staffMulti` / `departmentSingle` / `departmentMulti` / `seqNo` | 无需 extendInfo（date 也可不带） |
| `longText` | `{ "discriminator": "longText", "rows": 4 }` |
| `number` | `{ "discriminator": "number", "decimalPlaces": 2, "minimum": 0, "maximum": 999999.99 }` ⚠️ 不写 `decimalPlaces` 默认无小数 |
| `selectSingle` | `{ "discriminator": "selectSingle", "options": ["A","B"], "defaultValue": "A" }` |
| `radio` | `{ "discriminator": "radio", "options": ["高","中","低"], "defaultValue": "中" }` |
| `checkbox` | `{ "discriminator": "checkbox", "options": [...], "defaultValue": "A;B" }` |
| `image` | `{ "discriminator": "image", "uploadMultiple": true, "cameraOnly": false }` |
| `attachment` | `{ "discriminator": "attachment", "maxUploadSizeMb": 10 }` |
| `dateTime` | `{ "discriminator": "dateTime", "format": "yyyy-MM-dd" }` |
| `refSingle` | `{ "discriminator": "refSingle", "targetModelCode": "目标表最终编码" }` ⚠️ 必须带前缀 |
| `refMulti` | `{ "discriminator": "refMulti", "targetModelCode": "目标表最终编码" }` |
| `subTable` | `{ "discriminator": "subTable", "fields": [子字段数组] }` 子表内不能用 seqNo / subTable |
| `address` | `{ "discriminator": "address", "areaMode": "P-C-T", "showDetailAddress": true }` |

字段通用属性：`code`（唯一，普通 ≤32 字符 / 子表 ≤43）、`name`、`type`、`description`（可选）、`required`（布尔，业务必填）。

⚠️ **保留编码**：`status`、`OwnerId`、`OwnerDeptId`、`CreatedBy`、`CreatedTime`、`ObjectId`、`Name` 等为系统保留/系统字段，自定义字段编码须避开（状态类改用 `planStatus` / `taskStatus` 等）。

---

## 常见错误与排查

| 现象 | 原因 / 处理 |
| --- | --- |
| "编码不能为空/系统保留编码" | 字段 code 用了保留字（如 `status`）。改名后重试 |
| `refSingle` 关联报错 / 找不到目标 | `targetModelCode` 没用**带前缀的最终编码**；或目标表尚未创建。按拓扑先建被引用表 |
| 数字被截掉小数 | `number` 未设 `decimalPlaces`。补 `decimalPlaces` |
| 改完控制台看不到 / 报"无权限" | 先 `refreshDesignCache`；若仍"无权限"＝ACL 授权缺失，去控制台应用管理加成员 |
| 想移动已有表单进分组 | 无移动接口；只能在 `createSchema` 时指定 `moduleCode`，或删后重建 |
| 删除被引用表报错 | 先删引用方（叶子表），再删被引用方 |
| 超时/断网后不确定是否成功 | 非幂等，禁止自动重试；用检索工具确认状态后再补做 |

---

## 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | 初始版本 |
| 1.0.1 | 2026-10-19 | 步骤 4 增加预览地址呈现规范：必须用 Markdown 链接逐条列出、禁止放进代码块（代码块会渲染成不可点击纯文本） |
