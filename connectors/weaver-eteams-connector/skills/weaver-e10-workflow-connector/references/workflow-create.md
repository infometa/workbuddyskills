# 发起流程

## 什么时候读取

用户要"发起/创建/提交一个 XX 流程""按某工作流填写表单并发起"时读取本文件。覆盖 `workflow.createList` / `workflow.createForm` / `workflow.createPrepare` / `workflow.createApply`。

## Operation

| Operation | 风险 | 固定规则 |
| --- | --- | --- |
| `workflow.createList` | read | 查询可发起工作流列表；不传凭据；`name`/`workflowId` **至少传一个**；`workflowId` 与 `name` 可同传精确校验 |
| `workflow.createForm` | read | 必传 `workflowId`；`relatesTo` 仅透传不影响表单初始化；返回 `context`/runtime/frame/字段清单/fileUploadParams |
| `workflow.createPrepare` | read-before-write | requiresConfirmation；必传 `context`/`data`/`intent`；`requestLevel` 取 `systemFields.levelOptions` 的 code，`secLevel` 取 `systemFields.secLevelOptions` 的 id；不落业务数据 |
| `workflow.createApply` | high-risk-write | requiresConfirmation；必传 `confirm:true`/`context`/`intent`；`intent` 不继承 prepare；遇 `partial`/`write_uncertain` 禁止重试 |

## 确认链（写操作）

1. `workflow.createList` → `workflow.createForm` 拿到 `context`（表单会话短句柄，载荷由 CLI 托管在本机）。
2. `workflow.createPrepare` 收集字段，向用户摘要目标/差异/风险（预览 + 联动结果；明细表按 Excel 列展示，不要平铺）。
3. 等用户明确确认。
4. `workflow.createApply` 带 `confirm:true` 与同一 `context`、显式 `intent` 提交。
5. 成功时命令**直接返回 `requestId` / `requestName` / `url`**（`status` 为 `CREATED` = 已建草稿、`CREATED_SUBMITTED` = 已提交审批）——**按返回值汇报即可，不需要再去查询反查**。
6. 遇 `partial`/`write_uncertain` 停止，先只读回查（detail/summary），不自动重放。
7. Apply 被重复执行时按句柄状态分流（**不要一看到"用过"就重跑 Prepare**）：
   - `ok:true` + `data.status = "ALREADY_APPLIED"`：该 `context` 上一次已经**发起成功**，本次没有重复写入——按返回值里的 `requestId` / `previousResult` 作为成功结果汇报，**不要重跑 Prepare、不要再 apply**；
   - `partial`/`write_uncertain`：上一次已经发出写入、结果未确认——先只读回查（`workflow.search --category mine --requestId <目标ID>`）确认是否已发起，确认没发起才重跑 Prepare；
   - `validation/continuation_busy`：该 `context` 正被另一次执行占用、上一次还没发出写入——**稍后原样重试同一条命令**即可（不要重跑 Prepare、不要换句柄）；
   - `validation/continuation_consumed`：占用该句柄的执行停在无法判定的旧状态——先只读回查确认是否已发起，确认没发起才重跑 Prepare。

**省时纪律（这几件事一次都别做，每违反一条就多烧一轮工具往返）**：① 拿字段清单**不要**写脚本解析 `resultFile`（`fields` 被移出时用同伴的 `writableFields`）；② `data` 的键**不要**写 `"字段名(字段ID)"`（只认字段 id）；③ 只读字段**不要**传（看 `editableFields`）；④ 浏览 / 人员 / 发票类必填项**不要**先猜一个值试试；⑤ 读命令输出**不要**用 `head`/`tail` 截断；⑥ 取表单默认值**不要**去 `workflow.detail` 草稿（读不到，默认值以 `initialValues` 为准）；⑦ 输出被宿主截断时**不要**去找宿主的工具结果目录（`~/.workbuddy/projects/**/tool-results/**`：读不了，去了必白跑一轮），按输出最前面的 `resultFile` 取。

## 输入

### workflow.createList

- `name`（string）：工作流名称关键字，模糊匹配。**与 `workflowId` 至少传一个**——两个都不传时 CLI **不做查询**（不发列表请求），直接返回 `MISSING_QUERY` 和提示。
- `workflowId`（string，可选）：记忆中已确认的工作流 ID。记忆有 ID 时名称与 ID 同传，按当前用户可发起权限列表精确校验并优先选中；命中 `SELECTED`，未命中 `NOT_FOUND`，禁止去掉 ID 退回名称候选。

**查询词策略（第 ① 步必读）**：

- **优先用记忆别名改写后查询**：用户给出的表达命中记忆别名（如"手机话费报销"含别名"费用报销"）→ **直接查记忆别名**，不要先试用户原词、再试宽泛词。
- **禁止用宽泛词撞无关工作流**：`name:"话费"` 这类宽泛词可能唯一命中**语义无关**的工作流（如"话费补贴标准审批流程"）。命中 `SELECTED` 后**先核对工作流名称/类型与用户意图是否一致**（报销类意图 → 名称应含"报销/费用"，不应是"补贴标准/行政事务"类）；不一致则**不要进入第 ② 步初始化表单**，改用记忆别名重查。
- `NOT_FOUND`（含记忆别名也查不到）→ 此时才反问用户确认工作流，不要自行换词试探。
- `SELECTED` 的 `selectionSource: "exactName"` 表示"候选里恰好有一个名字与所写完全一致"（如所写"总部费用报销"，候选是「总部费用报销 / 总部费用报销流程 / 总部费用报销（自定义）」）——CLI 已替用户选定，**不要再反问"您指的是哪一个"**，按正常流程继续即可。`selectionSource: "workflowId"` 表示按记忆 ID 精确命中。
- `NEEDS_SELECTION` 只出现在"多命中且候选中没有与所写完全一致的"（CLI 只回这一批，最多不限量但已按类型+名称排序）：多候选**原样展示工作流名，不要添加 "(Recommended)"/"推荐" 等后缀**（由用户明确选择）。

### workflow.createForm

- `workflowId`（string|integer，必填）：工作流 ID。
- `relatesTo`（string，可选）：关联对象 id，仅透传不影响表单初始化。
- 返回 `context`（表单会话短句柄 `wc-…`，形如 `wc-1a2b3c4d5e6f7a8b`，载荷由 CLI 托管在本机；prepare/apply 复用）、`runtime`/`frame`、字段清单、`initialValues`、`systemFields`、`fileUploadParams`。
- **字段多的表单有"大输出"形态**（字段少时无此字段）：结果最前面多出 `resultFile` / `persistedResult` / `outputBytes` / `largeOutputNotice`，且 `fields` 二选一——① 紧凑编码（`columns` 是列名，`rows` 每行一个字段、各列用 `|` 分隔、顺序同 `columns`，非列信息按字段 id 放 `extra`，**不在 `extra` 里就是默认值**）；② `fieldsOmitted: true` + `fieldCount`，`fields` 整体移出 stdout，**同一份输出里给 `writableFields` 补偿索引**（`columns` = `id|name|subFormId|componentKey|flags`，`flags` 含义见 `flagLegend`，带选项字段的选项名见 `optionIndex`）。
  - **有 `writableFields` 就直接用**：全部可写字段的「字段名 ↔ 字段 id」都在里面，**直接用它的字段 id 构造 `data` 的键**。
  - **不要为了拿字段清单去写脚本解析 `resultFile`**：只有需要某字段更细的元数据（`browserModule` / `fileUploadParams` / 完整 `options` 结构）时才按该字段 id 去取。读任何输出都**不要用 `head`/`tail` 截断**（截断会破坏 JSON，还会诱发重复执行同一条命令）。**输出被宿主截断时**（只看到 2048 字节预览、或提示"已保存到文件"），**不要去读宿主的工具结果目录**（`~/.workbuddy/projects/**/tool-results/**`：没有读权限，去了必白跑一轮），直接按同一份输出最前面的 `resultFile` 取完整结果。
  - 两种形态都**照常拼 `data` 并调 `createPrepare`**，**不要重跑 `createForm`**。

**拿到 form 返回后直接按用户已给信息拼 `data` 并立即调用 `createPrepare`**——不分析字段、不猜映射、不比对选项，**也不要用空 `data` 先探测必填清单**（用户说了什么字段就填什么、用用户原词；必填缺失由 prepare 的 `missing_fields` 告知）。

**`initialValues`**：OA 初始化表单时预填的字段值（含 onLoadForm 联动带出值），`data` 应包含这些值（用户明确填写的以用户为准）；**带 `subFormId` 的是明细表字段**（放进 `details` 对应行对象），**不带的是主表字段**（放 `main`）。这些默认值 **CLI 会自动并入**（主表进 `main`，明细按你建的行补），**漏带不会因此被报成缺必填**——不要为了"怕丢默认值"多跑一轮 prepare。反过来：**`missingFields` 里出现的字段就是真的没值**（OA 对浏览按钮类默认值可能只下发类型标记、不下发值），此时必须问用户，不要猜值、也不要翻 `workflow.detail` 草稿。

**`systemFields`**：`permissions` 给各系统字段的 isview/isedit/ismandatory，`defaults` 是默认值，`levelOptions`/`secLevelOptions` 是紧急程度/密级选项。**只有 `isview=true` 且 `isedit=true` 的系统字段才需要填**；紧急程度/密级**只从这两个 options 取**（不得使用记忆、表单字段或其他来源）；**`defaults` 已有非空值即视为已满足，不要询问用户、直接采用**；仅当 ismandatory=true 且默认值为空时才需要用户提供。

### workflow.createPrepare

- `context`（string，必填，minLength 1）：复用 createForm 返回的 `context`；prepare 与 apply 必须同一值，原样回传，禁止手工构造/修改/复用他处。
- `data`（object，必填）：表单字段值，结构 `{"main":{...},"details":{"<subFormId>":[{...}]}}`。
- `requestName`（string，可选）：流程标题。form 返回 `requestName` 非空（OA 已有标题）时用其值；为空时**只有用户原话明确给了标题**（如"标题叫 X"）才用用户给的；**用户没给就不要自己编**——标题 `ismandatory=true` 时 `createPrepare` 会返回 `NEEDS_INPUT`，按 `missing_fields` 向用户问一次并补齐。**标题不得用其他字段值（留言内容/工作流名/事由等）替代**：标题是用户可见的流程名称，用别的字段内容做标题会与流程内容耦合，OA 列表里难以辨识。
- `requestLevel`（string，可选）：紧急程度，取 `systemFields.levelOptions` 的 code。
- `secLevel`（string，可选）：密级，取 `systemFields.secLevelOptions` 的 id。
- `remark`（string，可选）：签字意见。
- `intent`（enum `submit`|`draft`，必填）：`submit`=提交审批（必填缺失阻断，返回 `NEEDS_INPUT`）；`draft`=仅保存草稿（必填缺失不阻断、状态仍是 `READY`，**但 `missing_fields` 仍随结果返回**，供模型查看并提示用户提交前补齐）。

### workflow.createApply

- `context`（string，必填）：复用 createPrepare 的 `context` 原样回传。
- `confirm`（const true，必填）：声明用户已明确确认本次发起。
- `intent`（enum `submit`|`draft`，必填）：不继承 prepare 的 intent，必须显式传入。
- `question`（string，可选）：用户发起时的原话（记忆保存参考）。
- `verificationConfirmed`（boolean，可选）：节点字段校验需用户确认时显式确认继续提交。

## 示例

### ① 查询可发起工作流

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.createList --input-json '{"name":"请假"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.createList --input-json '{"name":"请假"}'
```

### ② 初始化表单（拿到 context）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.createForm --input-json '{"workflowId":"123456"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.createForm --input-json '{"workflowId":"123456"}'
```

### ③ 收集并准备表单数据（intent 必填）

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.createPrepare --input-json '{"context":"<createForm返回的context>","data":{"main":{"报销事由":"客户约谈"}},"intent":"submit"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.createPrepare --input-json '{"context":"<createForm返回的context>","data":{"main":{"报销事由":"客户约谈"}},"intent":"submit"}'
```

### ④ 明确确认后发起并提交审批

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.createApply --input-json '{"context":"<同一context>","confirm":true,"intent":"submit","question":"帮我发起一个报销流程"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.createApply --input-json '{"context":"<同一context>","confirm":true,"intent":"submit","question":"帮我发起一个报销流程"}'
```

## 返回

- createList：`SELECTED`/`NEEDS_SELECTION`/`NOT_FOUND`/`MISSING_QUERY`；候选工作流名原样展示，不加"推荐"后缀。`MISSING_QUERY` ＝ `name` 与 `workflowId` 都没传，CLI **未发起查询**、`workflows` 为空 —— 补上名称或 ID 后重调即可（**不要试图拉全量再自己筛**）。**大清单形态**（`name` 命中太多、清单超 24 KB 时）：结果最前面多出 `resultFile` / `persistedResult` / `outputBytes` / `workflowsTotal` / `workflowsTruncated` / `largeOutputNotice`，且 `workflows` 只保留**前 100 条**——需要更多候选时从 `resultFile` 按需提取（**不要整份读入上下文**），更推荐把 `name` 写得更精确、或直接传 `workflowId` 来定位。
- createForm：`context`、`runtime`、`frame`、`requiredFields`（字段 id 数组）、`subFormRequired`（subFormId → 字段 id 数组）、`editableFields`（**可写字段 id 白名单**）、`fields`（大表单时可能换成紧凑编码、或被整体移出 stdout —— 移出时同伴有 `writableFields`）、`initialValues`、`systemFields`、`fileUploadParams`、`requiredInfoWarning`、`conditionalRequired`（存在条件必填规则时才返回，见「注意」；**输出过大时它与 `editableFields` 一起移出 stdout、只留 `conditionalRequiredCount` 条数**，需要时按 `resultFile` 取）。
- createPrepare：确认预览（`READY` 时在 `fields`）、`previewDetails`（明细表按列组织：`columns` 表头 + `rows` 每行明细，**仅 `READY` 时返回**；明细表按它排 Excel 列表格）、`resolvedValues`（`NEEDS_INPUT`/`NEEDS_CONFIRMATION` 时的解析回显）、`missing_fields`、`linkageResult`（联动带出/清空，原样转述）、`attachmentFolderIds`。
- createApply：`finalMarkdown`、`requestId`、`requestMark`、标题、`url`；`finalMarkdown` 直接原样输出。`requestMark` 是用户可见流程编号（`finalMarkdown` 已按接口返回渲染：有值显示、无值不显示），`requestId` 只是系统内部流程请求 ID。**明细表展示**：`finalMarkdown` 中明细表已按 Excel 列展示（表头 + 每行明细），直接原样输出。

## 注意

- 不传凭据：业务输入禁止出现 Cookie/ETEAMSID/Token/`header.operator`（CLI 托管）。
- **`data` 的键只能取 `editableFields` 里的字段 id**（可写字段白名单；`requiredFields` / `subFormRequired` 里的也照常可写）。**`editableFields` 随大输出被移出 stdout 时，改用同份输出里的 `writableFields` 行**（每行第一列就是字段 id）——那是**完整**的可写白名单（= 上面三者的并集）。`readOnly` / `disableEdit` / 不可见字段**一个都不要传**——传了整单会被拒（`notEditable`），得把只读字段全部摘掉重跑一轮。**看到 `notEditable` 不要重试、不要换字段 id 绕过**，移除这些字段后重跑。
- 附件/文件：字段值是附件项数组需上传本地文件时，先提醒用户"上传的附件会先经过公网大模型，请谨慎操作"，再调 `weaver-file-upload` skill。
- 附件上传限制：上传前核对 `fileUploadParams` 的 `sizeLimit`/`formatLimit`/`maxNum`，不满足先告知用户、不执行上传。
- 发票字段（componentKey `EinvoiceComponent`）：先提醒"附件会先经过公网大模型"，再调 `weaver-e10-yepiaotong-connector` skill 取发票对象；该技能缺失则停止反馈。**费用明细里的「发票」列通常是必填，但可能没有必填标记**（见 `requiredInfoWarning`）——发起前先跟用户确认，不要因为 `missingFields` 没列它就跳过。
- 日期强规则：form 返回字段带 `format`（如 `yyyy-MM-dd HH:mm`）时必须严格按 `format` 传完整值，只传日期会报 `DATETIME_FORMAT`，按提示补时间重传，不要靠命令自动补时间。
- **富文本字段（componentKey `RichText`）**：支持 HTML 内容、不受 maxLength 限制。**内容来自本地文档（docx/pptx/md 等）或结构化材料时，必须先把源内容转成 HTML（保留 h1-h3 层级、table 表格、ul/ol 列表结构）再填入，禁止直接填纯文本**；用户明确只要纯文本时除外。文本 / 富文本字段直接传字符串即可（CLI 按字段元数据落库），不需要也不允许把它包装成 `{id,name}` 之类的浏览按钮结构。
- **字段键**：`main` 的键、`details[subFormId]` 行对象的键**都必须是字段 id**（`fields[].id`，或 `writableFields` 的 `id` 列）。`"字段名(字段ID)"` 这种写法**表单 data 不支持**（那是查询条件 `filterFields` 的写法），混用会报「存在重名或无法识别的表单字段，请改用字段 id」并白跑一轮。
- 字段**值**格式：选项传 `name`；浏览按钮/人员/部门传名称自动转 ID；人员范围（EmployeeScope）传对象数组 `{"name":名称,"type":类型}`，类型取 user/dept/subcompany/group/role/position/external/all/allExternal。
- **`workflow.detail` 读不到草稿**（草稿的 `basicInfo`/`formData` 全空）——不要为了"抄一份历史单据的默认值"去 detail 草稿，那是白跑一轮；表单默认值一律以 `createForm` 的 `initialValues` 为准。
- **人员范围（EmployeeScope）解析失败**：`createPrepare` 返回 `NEEDS_CONFIRMATION`，`ambiguities` 里 `kind = "EMPLOYEE_SCOPE"`：
  - `reason = "NOT_FOUND"` → 系统里没有该名称，**一次明确告知用户**“没找到「XX（类型）」，请给出系统里的准确名称或 `{"optionId":"候选id","content":"候选名称","type":"类型"}`”，最多重试 1 次；
  - `reason = "MULTIPLE_MATCHES"` → 列出候选（`candidates`）让用户选，选定后按 `{"optionId","content","type"}` 回传；
  - `reason = "NOT_RESOLVED"` → 名称/类型齐了但没拿到 ID，通常上一次解析没成功，按上面两种口径让用户确认；
  - **禁止**因为"命令返回 ok"就当作字段已填好——出现 `ambiguities` 时必须先解决，否则该字段不会进入保存体。
- **静态必填标记未下发（`requiredInfoWarning`）**：`createForm` 返回的 `requiredInfoWarning` 非空时，说明 OA 没下发该表单的**静态**必填配置，此时 `requiredFields` / `subFormRequired` 只含系统字段（流程标题等）——**不代表该表单没有业务必填项**。按 `conditionalRequired` + `missing_fields` 处理即可：
  - **`conditionalRequired`**：本表单的**条件必填**清单（OA 联动规则原样结构化）。每项 = 一个会变必填的字段（`fieldId`/`fieldName`/`subFormId`）+ 触发条件 `when[]`（`fieldId`/`fieldName`/`term`/`values[]`），`match` 为 `AND`/`OR`。**发起前用它主动向用户问齐**（例："若「报销方式」选银行（付公司），则「账号」「开户机构名称」为必填"），不要等用户先填对触发字段。它是"可能的必填"，不是当前必填。**它随大输出被移出 stdout 时**（只剩 `conditionalRequiredCount`）不必回头取：直接照下一条按 `missing_fields` 走即可。
  - **`missing_fields` 可信**：条件命中与否由 `createPrepare` 按**实际所填数据**（含联动带出值）实时计算，`missing_fields` 就是当前真实缺失的必填项——照常 `createPrepare`，按它的返回补齐。**禁止**对用户说"系统不会校验必填项"，也**禁止**用 `requiredInfoWarning` 非空当作"无法校验必填"的理由跳过校验。
  - 只有需要向用户交代"OA 页面上带红色星号的字段"时，才提示用户对照表单红星核对（含明细表里的列，如费用明细的「发票」）。
- **必填缺失一次问齐**：`createPrepare` 返回 `NEEDS_INPUT`（`missing_fields`）时，**把主表 + 明细表全部缺失字段一次性列给用户**（每项注明需要的值类型/建议默认值），**禁止逐字段推演或逐个追问**；联动/默认值/记忆已覆盖的字段不会出现在 missing 里，直接采用即可。**`intent: draft` 时缺失不阻断、状态仍是 `READY`，但 `missing_fields` 同样会返回——必须原样转述（提交前需补齐），不要把 `READY` 读成"没有缺失"**。
- **必填的浏览 / 人员 / 发票类字段不要"先猜一个值试试"**：这类值要么来自用户（准确名称或 `{id,name}`），要么来自外部技能（发票走 `weaver-e10-yepiaotong-connector`）。**第一次 `createPrepare` 就在 `data` 里留空**，让 `missing_fields` 把它们列出来，再连同其它缺失项**一次性问用户**；用猜测值去 prepare 只会白跑一轮——就算被接受，你也不知道它解析成了**哪个**对象，仍然要回头问用户。
- **`resolvedValues` 用来自查解析结果**：`createPrepare` 返回 `NEEDS_INPUT` / `NEEDS_CONFIRMATION` 时，`resolvedValues` 就是"我传的值 → 服务端最终值"的回显（选项给名称，浏览/人员/部门给 `{id,name}` 数组）；`READY` 时同一内容在 `fields`（确认预览）。**解析结果与预期不符就不要往下走**（例如传「泛微」被解析成了另一个主体），按上面的口径向用户确认后续用准确名称/ID。
- **浏览按钮值匹配不上（BROWSER NOT FOUND）**：`createPrepare` 返回 `NEEDS_CONFIRMATION`（`ambiguities` 里 `kind = "BROWSER"`）时按 `reason` 分别处理：
  - `reason = "NOT_FOUND"` 且 `candidatesAvailable = true` → CLI 已把该浏览控件首页的合法取值放进 `candidates`，**逐条列给用户挑**，选定后按 `{"id":"候选id","name":"候选名称"}` 重新 prepare；
  - `reason = "NOT_FOUND"` 且 `candidatesAvailable = false` → **一次明确告知用户"系统里没有「XX」，请提供系统里准确的名称或 `{id,name}`"**，用户给出后最多重试 1 次；
  - `reason = "MULTIPLE_MATCHES"` → 列出 `candidates` 让用户选，选定后按 `{"id":"候选id","name":"候选名称"}` 回传；
  - **禁止自行换相近词反复 prepare**（如「差旅费」查不到就试「差旅」），也**禁止凭猜测直接构造 `{id,name}` 绕过澄清**。
- 明细表：`details` 的 key 是 subFormId，value 是行对象数组。
- **明细表（子表单）展示规则（Excel 列展示）**：`createPrepare` 返回的 `previewDetails`（明细表按列组织：`columns` 表头 + `rows` 每行明细）——明细表**必须用 Excel 列展示**（表头 + 每行一条明细，形如 `| 序号 | 费用日期 | 费用类型 | 费用说明 | 申请金额 |`，每行一行），**禁止把明细字段按"字段\|内容"平铺**；`previewDetails` 为空时才用 `fields` 平铺兜底。多条明细时逐行展示（序号递增）。
- 目录联动：附件字段 `folderDependsOnOption=true` 时，按最近一次 prepare 返回的 `attachmentFolderIds` 取 `folderId`（null=不指定目录）再上传。
- 初始化值：`createForm` 返回 `initialValues`（OA 预填值，含 onLoadForm 联动带出），prepare 的 `data` 应包含这些初始化字段值（用户明确填写的以用户为准）；含 subFormId 的放 details 对应行，主表字段放 main。**漏带不会导致缺必填**（默认值由 CLI 自动并入主表与明细行）；`missingFields` 里出现它就是真的没值，按上面口径问用户。
- 不重试：saveFormData/flow/create 失败、超时或结果不确定（`SAVE_UNCERTAIN`/`PARTIAL_SAVED`/`CONTEXT_ALREADY_WRITTEN`/`WRITE_UNCERTAIN`）禁止重试，返回恢复信息并让用户人工检查。
- 写操作遇登录失效：禁止自动重登重放，返回 `WRITE_UNCERTAIN` 停止，先只读回查。
- `context` 与工作流强绑定：prepare/apply 只用最终选定工作流那次 createForm 返回的 `context`。
- 发起成功且用户有新的语义记忆时，按 memory 规则主动调用 `workflow.memoryExtract` 保存本次工作流与字段偏好（见 workflow-memory.md）。
