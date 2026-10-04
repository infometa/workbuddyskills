---
name: weaver-e10-yepiaotong-connector
display_name: 泛微业票通发票
display_name_en: Weaver Invoice
description: "泛微 E10 业票通发票管理：查询票夹、OCR/查验、附件、流程发票字段、报销填单、智能开票确认链。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "泛微 E10 业票通发票管理。支持查询个人/企业票夹、查看详情、上传、OCR/查验预览、下载附件、流程表单发票字段数据，通过 prepare/apply 确认链处理导入、新增、编辑、删除、报销单创建/更新、智能开票/存台账。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Weaver E10 Yepiaotong invoice skill for folder queries, detail lookup, OCR and validation previews, attachment downloads, workflow invoice field data, reimbursement form submission, and confirmed invoice issuing. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.1
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
cliHelp: "weaver-work-cli invoice --help"
---

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**
认证和登录态只能按共享规则通过 `weaver-work-cli auth ...` 命令判断；禁止直接读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
所有命令通过 `weaver-work-cli --profile eteams --json invoice run <operation>` 执行：简单 JSON 优先传 `--input-json '<json>'`，复杂或多行 JSON 先写入 UTF-8 文件再传 `--input <path>`，只有确认当前 shell 能稳定传管道时才使用 `--input -`。调用前先按需读取 references 下对应的文件，查参数结构，不要猜字段；**references 是第一信息源**，`weaver-work-cli invoice schema` 是 operation、字段和风险等级的合约来源。
命令示例、提示词和临时说明必须同时兼容 Windows 和 macOS/Linux；涉及 JSON 输入、用户目录、路径分隔符、Python 启动器、文件删除、目录查看或文件比对时，同时给 Windows PowerShell 与 macOS/Linux（bash/zsh）两套示例。Agent 先根据当前系统和 shell 选择对应示例，不确定时用 `node -p "process.platform"` 判断。Windows/PowerShell 下不要使用 `printf`、`$HOME/...`、`~/...`、bash 反斜杠续行、`rm/ls/diff/python3` 等 Unix-only 写法。
涉及发票附件、图片、本地文件、远程 URL 文件或 OCR/文件解析的操作，执行前必须提醒用户：文件内容可能被上传到 E10 业票通、OCR/查验服务，并可能进入当前大模型上下文用于理解和处理；必须等待用户明确确认后才继续。

# 泛微E10业票通发票管理

## 共享包依赖（随连接器下发，无需单独安装）

本包通过相对路径引用共享规则 `../weaver-e10-shared-connector/`（SKILL.md 与 references 内联路径）。连接器模式下共享技能与本包**一起下发**——引用目标一定在场，**不需要也不应该单独安装、上传或替换共享包**。

- Agent 发现引用目标不存在或内容明显过期时，停止执行并提示用户**断开后重新连接本连接器**以刷新共享规则，不要改写相对路径去适配其它目录名，也不要执行 `npm install` / `weaver-work-cli skills install`。

## 路由优先级（先判断是不是业票通发票，再选 operation）

业票通发票不是通用 E10 对象。**只要用户的核心对象是业票通发票、个人/企业票夹、发票 OCR、发票查验或发票附件，就优先使用 `weaver-e10-yepiaotong-connector`。**

### 明确归 `weaver-e10-yepiaotong-connector` 的高优先级语义

出现以下任一语义时，优先走本 Skill：

- 业票通 / 发票 / 票夹 / 个人票夹 / 企业票夹 / 发票详情 / 发票浏览按钮
- 发票上传 / OCR 识别 / 查验预览 / 附件下载
- 导入发票 / 新增发票 / 编辑发票 / 删除发票
- 发票报销 / 自动填单 / 事前申请报销 / 报销单创建或更新
- 开票 / 开专票 / 开普票 / 存台账 / 智能开票
- `fid` / `fileId` / 发票号码 / 发票代码 / 查验状态 / 报销状态

**判定规则：** 只要最终动作是对业票通发票做查询、查看、上传、OCR、查验预览、下载、导入、新增、编辑、删除、流程表单发票字段、发票报销填单或开票/存台账，就归 `weaver-e10-yepiaotong-connector`。只有当用户处理的是非发票类 E10 业务、通用工作流或尚未封装的业票通能力时，才不使用本 Skill。

## 选哪个命令

### 票夹管理（CLI 命令）

| 想做什么 | 命令 | 按需读取 reference |
|---|---|---|
| 查看可用 operation、字段和风险等级 | `invoice schema` | [`invoice-agent-entry.md`](references/invoice-agent-entry.md) |
| 查询个人票夹 | `invoice run invoice.list` | [`invoice-personal-list.md`](references/invoice-personal-list.md) |
| 查询企业票夹 | `invoice run invoice.enterprise.list` | [`invoice-enterprise-list.md`](references/invoice-enterprise-list.md) |
| 按 `fid` 或 `number` 查看详情 | `invoice run invoice.get` | [`invoice-detail.md`](references/invoice-detail.md) |
| 上传发票文件 | `invoice run invoice.upload` | [`invoice-file-upload.md`](references/invoice-file-upload.md) |
| OCR 预览，不保存到票夹 | `invoice run invoice.ocr.preview` | [`invoice-ocr-preview.md`](references/invoice-ocr-preview.md) |
| 查验预览，不回写查验结果 | `invoice run invoice.validate.preview` | [`invoice-validation-preview.md`](references/invoice-validation-preview.md) |
| 下载发票附件 | `invoice run invoice.download` | [`invoice-download.md`](references/invoice-download.md) |
| 准备/确认导入发票文件 | `invoice run invoice.import.prepare/apply` | [`invoice-import.md`](references/invoice-import.md) |
| 准备/确认手工新增发票 | `invoice run invoice.add.prepare/apply` | [`invoice-add.md`](references/invoice-add.md) |
| 准备/确认编辑发票 | `invoice run invoice.update.prepare/apply` | [`invoice-update.md`](references/invoice-update.md) |
| 准备/确认删除发票 | `invoice run invoice.delete.prepare/apply` | [`invoice-delete.md`](references/invoice-delete.md) |
| 生成流程表单发票浏览按钮 JSON | `invoice run invoice.browse-field.data` | [`invoice-browse-field-data.md`](references/invoice-browse-field-data.md) |
| 报销自动填单、报销单创建/更新 | `invoice run invoice.reim.*` | [`invoice-reim.md`](references/invoice-reim.md) |
| 报销完整工作流编排、行为准则 | AI 内部 | [`reim-workflow.md`](references/reim-workflow.md) |
| 报销 CLI operation 入参与返回值 | AI 内部 | [`reim-api-reference.md`](references/reim-api-reference.md) |
| 发票与事前申请匹配规则 | AI 内部 | [`reim-matching-rules.md`](references/reim-matching-rules.md) |
| 费用科目自动匹配规则 | AI 内部 | [`reim-expense-subject-rules.md`](references/reim-expense-subject-rules.md) |
| 报销表单字段填充与 JSON 组装规则 | AI 内部 | [`reim-form-fill-rules.md`](references/reim-form-fill-rules.md) |
| 报销端到端示例 | 参考 | [`reim-examples.md`](references/reim-examples.md) |
| 智能开票或存入待开台账 | `invoice run invoice.issuing.make.prepare/apply` | [`invoice-issuing.md`](references/invoice-issuing.md) |
| 开票字段提取规则、税率推断、金额计算 | AI 内部 | [`invoice-issuing-field-rules.md`](references/invoice-issuing-field-rules.md) |
| 开票端到端示例 | 参考 | [`invoice-issuing-examples.md`](references/invoice-issuing-examples.md) |
| 共享、转让、标签或 schema 未列出的能力 | 无可用命令 | [`invoice-disabled-capabilities.md`](references/invoice-disabled-capabilities.md) |

处理链：

- 查票夹/详情：`invoice.list` 或 `invoice.enterprise.list` -> 必要时 `invoice.get`
- OCR 识别预览：`invoice.ocr.preview`；如果先上传，可复用 `invoice.upload` 返回的 `upload`
- 导入文件：先 `invoice.ocr.preview` 预览票面识别结果；用户确认导入后，默认用 `invoice.import.prepare` 且传 `validate=true`、`syncToOa=true` -> 用户确认 -> `invoice.import.apply` -> 按返回 `fid` 回查/报告。只有用户明确要求“跳过查验/不同步 OA”时，才使用 `validate=false` 或 `syncToOa=false`。
- 手工新增：`invoice.add.prepare` -> 用户确认 -> `invoice.add.apply`
- 编辑发票：`invoice.update.prepare` -> 用户确认 -> `invoice.update.apply`
- 删除发票：`invoice.delete.prepare` -> 用户确认 -> `invoice.delete.apply`
- 流程发票字段：已有 `fid` 或详情时，用 `invoice.browse-field.data` 生成浏览按钮对象；不要运行旧源码脚本或直接调接口。
- 报销填单（完整工作流见 [`reim-workflow.md`](references/reim-workflow.md)）：先用 `invoice.list`/`invoice.get`/`invoice.reim.file-ocr.preview` 获取发票 -> 展示汇总并确认 -> 用 `invoice.reim.requests.list`、`invoice.reim.workflow.resolve`、`invoice.reim.form.structure`、`invoice.reim.row-info`、`invoice.reim.employee-superiors` 组装报销单 JSON（匹配规则见 [`reim-matching-rules.md`](references/reim-matching-rules.md)，填单规则见 [`reim-form-fill-rules.md`](references/reim-form-fill-rules.md)，科目匹配见 [`reim-expense-subject-rules.md`](references/reim-expense-subject-rules.md)）-> `invoice.reim.flow.create.prepare` -> 用户确认 -> `invoice.reim.flow.create.apply`。创建成功后修改只能用 `invoice.reim.flow.update.prepare/apply`。
- 智能开票：Agent 读取 `invoice-issuing.md` 和 `invoice-issuing-field-rules.md`，从用户输入或附件中提取购方、税号、商品明细、金额和税率；资料不足时追问用户补齐，再执行 `invoice.issuing.make.prepare` -> 用户确认开票或存台账 -> `invoice.issuing.make.apply`。当前资料包没有客户档案查询 operation，不要调用 `invoice.customer.*`。

## 执行原则（减少误路由、误重试和无效消耗）

### 1) 先拿最小必要信息，再执行

- 只是查票夹时，优先直接用 `invoice.list` 或 `invoice.enterprise.list`
- 列表默认先取小页，优先 `page_size=10`；用户没有要求全量时不要自动翻完整票夹
- 查询个人/企业票夹时，用户没有明确要求“全部发票/已报销/报销中/不可报销”就不要传 `sreim`；CLI 默认 `sreim="3"`，只查未报销发票
- 查询个人/企业票夹时，用户没有明确要求“凭证”就不要传 `bill_type`；CLI 默认 `bill_type=0`，只查发票
- 用户已经给出 `fid` 时，不要先查列表再过滤，直接用 `invoice.get` 或对应 prepare
- 只有需要附件归属、可编辑/可删除状态或完整票面时，才补 `invoice.get`

### 1.5) 大结果只摘要给用户

- 当前 CLI 会把完整 JSON envelope 写 stdout；Agent 回复时不要原样贴完整 JSON
- 列表最多先展示最相关的前 10 条，包含 `fid`、代码/号码、购销方、金额、日期、查验/报销状态和附件摘要
- 需要全量统计时，按 `start_pos` 分页读取并累计必要字段；说明已读取页数、命中数和是否还有更多
- OCR、详情或调试用完整响应过长时，优先落本地文件并向用户提供摘要和文件路径

### 2) 已知对象时直达动作

- 已拿到 `fid`、`fileId`、本地文件路径或完整 `info` 时，优先调用对应 operation
- 同一轮里如果已有足够的新鲜查询结果，不要重复查询同一票夹或同一详情
- 不要默认走 `list -> filter -> get -> prepare -> apply` 全链路；对象已明确时应压缩步骤

### 3) 错误语义驱动，而不是盲目重试

- 失败后先看进程退出码、`error.type`、`error.subtype` 和 `error.message`
- **除非错误明确提示可恢复或需要补充参数，否则不要重复刷同一个 operation**
- 写请求已经发出后，遇到结果不确定必须停止；不要把 `.apply` 当成可重试读操作
- **错误为 `authentication`（未登录，如 `E10 auth not found`）或 `session_expired`（登录态失效）时：立即停止当前操作，不要用示例占位域名或自行猜域名登录，也不要盲目重试**。先读取共享规则 `../weaver-e10-shared-connector/references/e10-auth-and-session.md`，按其中流程引导用户**断开并重新连接本连接器**完成重新登录，然后再继续原操作。

### 4) 附件、图片和文件解析确认

- 执行 `invoice.upload`、`invoice.ocr.preview`、`invoice.import.prepare/apply`、`invoice.reim.file-ocr.preview`，或任何会读取本地发票文件、上传远程 URL 文件、解析图片/PDF/OFD/XML、复用已上传 `upload` 对象、从附件提取开票字段的步骤前，必须先提醒用户文件内容可能进入大模型上下文，也可能发送到 E10 业票通或 OCR/查验服务。
- 用户未明确确认前，不要运行上传、OCR、解析、导入或复用已上传文件对象的命令。

## 写操作失败处理：`partial/write_uncertain` 决策树

当导入 / 新增 / 编辑 / 删除等写操作返回 `partial/write_uncertain`，或提示网络中断、部分成功、回查失败、回查字段不一致时，按下面规则处理：

1. **先停止盲目重试**，不要连续重复提交相同 `.apply`
2. 优先从以下角度解释：
   - 写请求可能已经到达服务端，但连接在结果确认前中断
   - 服务端可能只处理了部分发票
   - 写接口已返回成功，但详情回查失败或与预期不一致
   - continuation、目标文件、目标发票或登录上下文可能已经变化
3. 如需确认，只补 **一次** 只读查询（例如 `invoice.get` 或列表查询），不要陷入 query/write 循环
4. 最终给用户明确结论、已知 `workflow.state`、成功/失败项和下一步人工确认建议，而不是继续无意义重试

**特别注意：** 对导入、删除和编辑场景更要严格执行上述规则；这些场景最容易因重复提交造成重复入账、误删或覆盖用户刚修改的数据。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams invoice schema
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0}'
weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"fid":"12345"}'
weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"file":"./invoice.pdf"}'
weaver-work-cli --profile eteams --json invoice run invoice.import.prepare --input-json '{"file":"./invoice.pdf","validate":true,"syncToOa":true}'
weaver-work-cli --profile eteams --json invoice run invoice.import.apply --input-json '{"file":"./invoice.pdf","continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json invoice run invoice.browse-field.data --input-json '{"fid":"12345"}'
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20}'
weaver-work-cli --profile eteams --json invoice run invoice.issuing.make.prepare --input-json '{"mode":"ledger","payload":{"invoiceType":"7","externalDocumentNo":"AI-EXAMPLE-001","purchaserName":"示例个人","totalAmount":100,"taxAmount":6,"totalAmountWithTax":106,"details":[{"goodsName":"信息技术咨询服务","taxRate":0.06,"amount":100,"amountWithTax":106,"taxAmount":6}]}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams invoice schema
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0}'
weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"fid":"12345"}'
weaver-work-cli --profile eteams --json invoice run invoice.ocr.preview --input-json '{"file":"./invoice.pdf"}'
weaver-work-cli --profile eteams --json invoice run invoice.import.prepare --input-json '{"file":"./invoice.pdf","validate":true,"syncToOa":true}'
weaver-work-cli --profile eteams --json invoice run invoice.import.apply --input-json '{"file":"./invoice.pdf","continuation":"PREPARE_CONTINUATION","confirm":true}'
weaver-work-cli --profile eteams --json invoice run invoice.browse-field.data --input-json '{"fid":"12345"}'
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20}'
weaver-work-cli --profile eteams --json invoice run invoice.issuing.make.prepare --input-json '{"mode":"ledger","payload":{"invoiceType":"7","externalDocumentNo":"AI-EXAMPLE-001","purchaserName":"示例个人","totalAmount":100,"taxAmount":6,"totalAmountWithTax":106,"details":[{"goodsName":"信息技术咨询服务","taxRate":0.06,"amount":100,"amountWithTax":106,"taxAmount":6}]}}'
```
## 不在本 skill 范围

- 禁止加载原始 `weaver-e10-yepiaotong-connector` Skill 代替 CLI。
- 已有 CLI 封装的能力（list/get/upload/OCR/import/add/update/delete/issuing/reim）禁止 curl、fetch、浏览器自动化或直接访问 E10 `/api/inc/*`，必须通过 CLI。
- 当前修正源资料未提供客户档案查询或红字发票红冲接口，`invoice.customer.*` 与 `invoice.red.*` 不属于可用 operation；遇到这类请求时读取 [`invoice-disabled-capabilities.md`](references/invoice-disabled-capabilities.md) 并说明当前 CLI 不支持绕过调用。
- 禁止读取或复制 CLI runtime 内部 Token、Cookie、ETEAMSID。
- 禁止读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
- 共享、转让和标签当前未纳入 CLI manifest；新版源资料已给出提交接口，但仍需要补稳定接收人/标签 ID 来源、写后回查和测试后再开放。
- 非发票类 E10 能力、通用流程编排、非业票通表单/审批/组织等业务不由本 Skill 承载。
