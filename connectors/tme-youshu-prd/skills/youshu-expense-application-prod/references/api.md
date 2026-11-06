# API 与字段映射

使用运行环境实际暴露的 SaaS 工具。这里的名称和 DTO 对应本次代码契约；不把 Java 类名或 HTTP 路径自行当作可调用的连接器工具名。服务尚未发布、工具未发现或身份未授权时只能完成整理，不能声称创建成功。

## 候选查询

四个费用候选（备用金账号、付款主体、制作费子类、报销子类）使用 `AiFeeApplicationOptionsRequest`，无业务筛选参数，传平铺空对象 `{}`。银行查询 `queryFeeBanks` 单独使用 `AiFeeBankQueryRequest`：`level` 默认1，两级 `keyword` 均必填，二级还必填一级选定的 `bankName`，不能传空对象。银行字典只需基础登录认证和原子接口限流，不要求费用申请、连接器接入菜单或数据权限。其余候选与四个创建工具仍校验费用申请菜单；宣推对私沿用原简化导入功能开关。查询银行成功不代表可以创建草稿。

| 工具 | 结果 | 提交时使用 |
| --- | --- | --- |
| `querySpareFeeAccounts` | `key`、`accountId`、`platformType`、`platformTypeDesc`、`accountName`、`displayName` | `platformAccountId = accountId`；展示 `displayName` 供选择，平台码是枚举名 |
| `queryFeeBanks` | `key`、`bankName`、`branchName`；一级查银行，branchName为 `""`；二级查指定银行的支行；沿用页面顺序，无匹配为 `[]` | `key` 为当前级别名称标识；提交真实bankName/branchName，不把key另当银行ID |
| `queryFeePaymentSubjects` | `key`、`subjectId`、`subjectName` | 匹配用户指定的付款主体后取 `ourSubjectId = subjectId`，不是 `key` |
| `queryProductionFeeSubtypes` | `key`、`name` | 制作费 `subtype = name` |
| `queryReimbursementFeeSubtypes` | `key`、`name` | 报销 `subtype = name` |

费用子类继续使用业务已存在的名称字符串，包括历史中文名称；不能自创英文编码，也不能把查询结果的 `key` 换作 `subtype`。

歌曲基本信息复用 `batchQueryTrackBasicInfo`，结果已包含 `tmeTrackId`。`trackId` 筛选字段和同名返回字段表示 SaaS 歌曲 ID；传已知中央曲库 ID 查询时使用 `platformType = "TME"` 与 `platformIds` 成组传入。用户只有歌名、歌手时按这些条件查询，核实版本及候选后取返回的正数 `tmeTrackId` 创建费用，不能使用 SaaS `trackId` 代替；结果未关联中央曲库 ID 时追问，不猜测。

### 银行与支行选择

- **一级查银行**：传 `level=1`（可省略）和非空白 `keyword`，按银行名称包含匹配。展示实际返回的 `bankName` 供核对，用户明确指定且唯一匹配可直接复用，不默认首条。
- **二级查支行**：先选定一级结果的完整 `bankName`，再传 `level=2`、该 `bankName` 和非空白支行 `keyword`；精确限定银行后模糊查支行。不能跨银行拼接结果或把简称作为选定的完整银行名。
- 两级关键词都必填。缺少银行/支行关键词时集中补问；不查全量、不提供臆造关键词，不传pageNo/pageSize/limit。查询不创建收款账户。银行名确认后若用户只要求查银行或业务不需要支行，就不额外查支行。同一办理过程复用已确认结果，避免逐行重复。
- **宣推对私**：与页面简化导入一致，仅用 `payee.bankName` 保存用户完整开户银行原文（可含支行），不拆分，不填写 `branchName`。银行字典可以参考，不是建单前置条件；未命中字典不阻断、不擅自替换原文。银行卡收款仍须开户银行，账号、证件、手机号等其他校验不变。
- **制作费、报销、银行收款备用金**：提供银行资料时，通过字典核实银行名/支行名；填写支行时使用同一记录的 `bankName`、`branchName`，不能跨记录拼接。用户指定值唯一匹配时直接复用；简称、多义、银行和支行不对应时按原生提问规则消歧。若只指定银行且该场景允许不填支行，可只填该银行名称，不默认附加第一条支行；法人两项均必填。自然人是否必须填银行/支行仍按接口条件，不因字典新增而增加必填项。已有收款账户的资料冲突仍需财务核对，不用字典选择覆盖原账户。
- **支付宝 / 平台账号收款**：不查询银行，不填银行支行；支付宝账号与银行卡号仍互斥。
- **无匹配或失败**：`[]` 表示当前级别与搜索条件下无匹配记录，不能据此断言整个字典为空，不是无权限或请求失败。工具尚未暴露、服务异常与字典未命中分别说明；其他费用需要字典校验的银行资料不能伪造名称或绕过校验，保留资料并请用户核对或联系财务。宣推对私按原文处理，不因字典不可用阻断其流程；创建本身的权限和必填校验照常执行。

例（虚构名称）：用户在宣推对私模板填写“甲银行乙支行”，保留 `bankName="甲银行乙支行"`，不拆出 `branchName`。制作费用户选择字典项 `{"key":"乙支行", "bankName":"甲银行", "branchName":"乙支行"}` 后，填 `bankName="甲银行"`、`branchName="乙支行"`，不提交字典 `key` 作为银行名或新增支付字段。

#### 分级查询示例

以下为参数示例，不代表查询已执行或银行真实存在；bankName须替换为一级实际返回并选定的完整名称。

```json
{"level":1,"keyword":"甲银行"}
```

选定一级返回的 `bankName="甲银行"`，且用户需要“乙支行”后：

```json
{"level":2,"bankName":"甲银行","keyword":"乙支行"}
```

一级读取 `bankName`，二级读取对应 `branchName`；不要将一级的空branchName当作“该银行没有支行”。接口报错、未上线和查无匹配分别说明，不移除关键词重试。HTTP适配为 POST `/openapi/musician/companySaas/aiAssistant/query/expense/banks`，实际连接器调用仍用运行时发现的工具。

### 付款主体取值

- 分别保留用户输入的付款主体、付款主体候选和歌曲查询结果。用户在对话或表格中已指定主体时，查询用于核实与映射；不能把后返回的歌曲对象整体合并到申请参数，也不能用歌曲的 `issuingSubject`（发行主体）、`displayBrandName`（厂牌）或其他主体字段覆盖它。
- 使用 `queryFeePaymentSubjects` 返回的 `subjectName` 或 `subjectId` 匹配用户指定值，唯一匹配后取该项 `subjectId`。只给名称时不猜 ID；只给 ID 时核实其存在及对应名称；同时给出名称和 ID 时必须对应同一候选。简称、近似名称无法唯一确定、查无匹配或主体不可用时，保留用户指定值并追问/说明原因，不取首项、不换成歌曲归属主体。仅用户后续明确更正可以替换原值。
- **宣推对私未指定付款主体**：`ourSubjectId` 可省略。资料齐全且已授权创建时，直接交后端尝试自动补全，不为了付款主体先查候选或要求用户选择。后端在导入校验补齐歌曲资料后，取有效发行厂牌；仅有一个有效厂牌时，按当前租户的厂牌关联查找状态正常的“我方公司主体”。模型不得用 `issuingSubject`、`displayBrandName`、厂牌 ID 或歌曲 ID 猜测付款主体 ID。
- 多厂牌、没有有效厂牌、找不到关联主体或主体状态不可用时，后端明确提示无法自动确定；此时调用 `queryFeePaymentSubjects`，请用户选择真实主体再补入 `ourSubjectId`。不默认首项、不擅自拆单，也不把该业务错误描述为已创建。先核对原请求结果；明确未创建且补选改变了请求内容时使用新 `requestId`，原请求超时或结果不确定时仍须先核验，不能换 ID 重建。
- **用户已经指定主体**：仍优先核实、显式传入，后端校验该值；匹配失败时补问，不省略后改走自动补全。其他费用的主体必填及原有补全条件保持其各自接口契约，不能套用宣推对私的省略规则。
- 宣推对私、备用金、报销将选定主体放在请求顶层 `ourSubjectId`；制作费放在每个 `songs[i].ourSubjectId`。用户给出整批公共主体时应用到相应歌曲；明确的逐行/逐歌曲主体按各自范围保留，来源冲突而无明确更正时追问。相同歌曲对应不同付款主体时不能合并成一个 `songs` 项；整单只能有一个主体的费用遇到多个主体时先确认拆单方式。
- 制作费已有 `tmeTrackId` 时，用户指定的付款主体仍须显式传 `songs[i].ourSubjectId`。服务端优先采用请求值，缺失时才按歌曲归属尝试唯一匹配；省略会失去用户的指定。创建前核对用户原值、候选名称/ID、请求字段三者一致。

例：用户指定“甲公司”，付款主体查询唯一匹配为 `subjectId=101`，而歌曲查询返回发行主体“乙公司”。制作费该歌曲仍显式传 `ourSubjectId=101`；只从歌曲结果补齐中央曲库 ID 等歌曲资料。若付款主体列表没有“甲公司”，则说明无法匹配并请用户补充或选择，不能改成“乙公司”建单。

## 通用写入契约

四个创建请求均有：

| 字段 | 类型 / 要求 |
| --- | --- |
| `requestId` | 必填，1–64 位英文字母、数字、`_`、`-`；同一逻辑请求唯一 |
| `remark` | 选填，整单备注 |
| 各列表元素的 `key` | 必填、非空 `String`，在所属列表中唯一；用稳定行标识，不用个人证件或账号作 key |
| `amount` | 正数 `String`，人民币元，最多两位小数，例如 `"1234.56"`；接口值不带千位符或货币符号 |

最多 1,000 条费用明细；超过上限时询问或按用户已明确的规则拆分为独立申请，并给每个逻辑申请独立 `requestId`，不能静默丢行。

幂等映射存放 Redis，窗口为 7 日，并非永久去重。同 `requestId`、同内容复用原单的当前结果；内容变更使用新 ID。调用超时必须保留原 ID，核验或按契约重试同内容，不能换 ID 规避冲突。原草稿删除、窗口届满或缓存丢失时，不能自动换 ID 重建，也不能假定原申请不存在；先核实费用页已有结果，再按用户明确的新申请意图处理。

费用负责人默认当前申请账号、负责比例 100%，要求该账号已关联真实费用负责部门；缺少组织信息时返回业务错误。当前原子接口不提供自定义负责人与分摊比例，不从表格填造这些信息。

## 收款信息 `AiFeePayeeDTO`

| 字段 | 来源 / 值 |
| --- | --- |
| `userName` | 收款户名 / 收款人姓名 |
| `userType` | `NATURAL` 自然人，`ENTERPRISE` 法人；制作费与报销必填；宣推对私、银行收款备用金缺省为自然人 |
| `idType` | 自然人使用 `ID_CARD`、`HK_CARD`、`MACAO_CARD`、`TAIWAN_CARD`、`HOME_RETURN_PERMIT` 之一；法人固定 `UNIFIED_SOCIAL_CREDIT_CODE` |
| `idNumber` | 证件号，字符串 |
| `contactPhone` | 联系手机号，字符串；自然人必填，法人选填 |
| `bankCardNumber` | 银行卡号，字符串 |
| `alipayAccount` | 支付宝账号，字符串；自然人与银行卡二选一，法人不可用 |
| `bankName` | 开户银行；宣推对私银行卡收款必填，保存完整原文、不匹配字典；其他费用提供时核实字典，法人必填 |
| `branchName` | 开户支行；其他费用按同一银行字典项填写，法人必填；宣推对私不填写此字段 |

制作费、费用报销和银行收款备用金复用或追加当前租户公共收款人及收款账户。只追加缺失记录，不覆盖已存在的姓名、类型、电话或银行资料；冲突需联系财务核对。目录追加在创建草稿前独立提交，后续草稿保存失败时不会回滚已经追加的目录，使用同一信息重试可复用。宣推对私使用收款快照，不追加公共收款目录。

## `createPrivatePromotionFeeDraft`

请求 `AiPrivatePromotionFeeDraftRequest`：必填 `requestId`、`rows`；可选 `ourSubjectId`、`remark`。用户指定主体时按[付款主体取值](#付款主体取值)核实并显式传入；未指定时省略 `ourSubjectId`，由后端按发行厂牌关联的我方公司主体尝试补全，无法补全时再补选。

`rows` 每项：

| 字段 | 映射 |
| --- | --- |
| `key` | 来源费用行的稳定唯一 key |
| `tmeTrackId` | 中央曲库歌曲 ID |
| `scheduleName` | 宣推轮次 |
| `promotePlatform` | `DOU_YIN` 抖音、`VIDEO_ACCOUNT` 视频号、`KUAI_SHOU` 快手、`XIAO_HONG_SHU` 小红书 |
| `videoUrl` | 视频链接；无链接时按模板允许传用户提供的文字用途 |
| `talentName` | 达人名，选填 |
| `likeCount` | 点赞量，选填；非负整数 |
| `amount` | 元字符串 |
| `payee` | 收款信息对象，仅自然人身份证；`userType` 缺省 `NATURAL`、`idType` 缺省 `ID_CARD`，也可显式传入这两个值 |
| `remark` | 行备注，选填 |

## `createSpareFeeDraft`

请求 `AiSpareFeeDraftRequest`：`requestId`、`platformAccountId`、`ourSubjectId`、`amount`、`paymentType`、条件所需 `payee`、`attachments`、可选 `remark`。

- `platformAccountId`：从备用金账号查询选择；`ourSubjectId`：按[付款主体取值](#付款主体取值)匹配后的付款主体 ID。
- `paymentType`：`PLATFORM_ACCOUNT` 或 `BANK_ACCOUNT`。平台账号方式不需要收款资料；银行账户方式传自然人 `payee`，银行卡和支付宝二选一。
- `attachments`：`AiFeeUploadReferenceDTO` 文件列表，每项 `{key, uploadId}`，最多 20 份 PDF 或支持的图片，同一 `uploadId` 不重复引用。备用金账号平台不是 `GE_DAN` 歌单时沿用原费用校验，需要充值证明附件；付款主体与附件是既有业务策略的额外要求，不能因需求文字未列而省略。先收集并上传，再传通用上传工具返回且未过期的 `uploadId`。

## `createProductionFeeDraft`

请求 `AiProductionFeeDraftRequest`：`requestId`、`songs`、可选 `remark`。

`songs` 每项包含 `key`、歌曲信息和 `expenses`：

- 有中央曲库 ID 时填 `tmeTrackId`，复用查询核实歌曲；用户已指定付款主体时必须同时传当前歌曲的 `ourSubjectId`，按[付款主体取值](#付款主体取值)匹配，不能被歌曲查询结果覆盖或因已有 ID 而省略。未指定且原接口无法唯一补全时，仍需用户选择。
- 无中央曲库 ID 时填 `trackName`、`singers`、`lyrics`、`composings`、`ourSubjectId`；后者必填，按同一付款主体规则取真实 ID。前四项均为字符串，多个歌手用英文逗号分隔；词曲作者的人名组合保持用户原意。
- `expenses` 每项 `{key, subtype, amount, payee, remark}`。`subtype` 使用制作费候选的 `name`，`remark` 可选；每笔保留独立金额和收款人。

## `createReimbursementFeeDraft`

请求 `AiReimbursementFeeDraftRequest`：`requestId`、`subtype`、`ourSubjectId`、`payee`、`invoices`、`items`、可选 `remark`。

- `subtype` 是一个报销费用子类名称，整单共用；`ourSubjectId` 和 `payee` 也是整单公共信息，主体按[付款主体取值](#付款主体取值)匹配。
- `invoices` 为必填的 `AiFeeUploadReferenceDTO` 列表，最多 20 份，每项 `{key, uploadId}`。`uploadId` 来源于已成功上传的 PDF、JPG、JPEG、PNG、GIF 或 WEBP 文件且未过期；同一 `uploadId` 不重复引用，后端核实当前租户账号归属及对象真实存在。
- `items` 每项 `{key, tmeTrackId, amount, description}`。中央曲库 ID 和金额必填，`description` 选填。

## 创建结果 `AiFeeDraftDTO`

成功结果字段为 `key`、`feeNo`、`status`、`statusDesc`、`feeType`、`feeTypeDesc`、`creator`、`createTime`、`url`。四种工具均只创建 `DRAFT`；幂等复用返回原单的实际当前状态，不将用户已提交的单据改回草稿。

`createTime` 为 13 位毫秒时间戳。展示后端返回的单号、实际状态、类型、创建人、创建时间和 `url`；仍为草稿时提醒用户进入申请单核对并手动提交。`key` 用于结果标识，不能代替单号显示为申请单号；不自行拼接 URL。

如回显用户指定的付款主体，使用本次已核实且实际传入请求的主体名称与 ID，并标明为申请参数；不从歌曲结果重新取值。宣推对私省略主体、由后端自动匹配时，未取得页面或可用回查的实际结果前不编造主体名称或 ID，可提示到申请单核对自动填入结果。成功响应不含付款主体字段，不能仅凭成功响应声称已核验落库主体。若已有页面或其他可用回查明确显示不同主体，提示不一致并核对原单，不自动重建草稿。
