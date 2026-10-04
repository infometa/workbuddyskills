---
name: wpe-invoice-check
display_name: 发票查验
display_name_en: Invoice Verification
description: 支持 PDF / PNG / JPG 上传识别发票要素，核验发票真伪与票面信息，并输出销方企业画像（登记地/行业/纳税人身份/开票特征）；内置票种映射、金额口径换算、查验配额与超时重试策略
description_zh: 从 PDF 或图片（png/jpg）识别发票要素，或按用户提供的号码/日期/金额，核验发票真伪与票面信息，并给出销方企业画像
description_en: Extract invoice fields from a PDF or image (png/jpg) — or from user-provided number, date and amount — verify the invoice, and profile the seller (registration, industry, taxpayer status, invoicing behavior).
category: data
version: 3.4.0
author: 微信支付电子发票 / 乐企开票
disable: false
agent_created: true
---

# 发票查验

两种入口，最终都到同一次查验：

- **A. 用户给发票文件**（PDF / PNG / JPG 路径）→ 视觉识别要素 → 用户确认 → 查验
- **B. 用户给文字要素**（号码/日期/金额/票种）→ 补齐规则化后直接查验

## 1. 认证与连接器定位（先做，别急着说"没有工具"）

唯一依赖连接器 **`wpe-general-connector`（中文名「腾讯数电发票」）**，通过它的 `call_internal_api` 工具调用。

| 项 | 值 |
|---|---|
| 连接器 | `wpe-general-connector`（中文名「腾讯数电发票」） |
| 税号传递 | 连接器请求头 `X-Subject-Id`（不是接口参数） |
| 令牌 | `Authorization: Bearer <token>`，由连接器管理 |

**定位与授权流程**：

1. 会话中找不到该连接器工具 → 用名称 `wpe-general-connector`（或「腾讯数电发票」）在连接器列表查找并加载 MCP。
2. 加载后**首次调用不带 token**（探活）。返回 **HTTP 401** → 未授权，**停下提示用户完成 MCP 授权**，通过后再继续。
3. 税号未接入（`access_status ≠ 00`）→ `403 / JSON-RPC -32007`，表现是 WorkBuddy 把**整个连接器下线**（工具从列表消失，易误判成"MCP 挂了"）。

> ⚠️ **禁止**用脚本、curl 或其它连接器直连服务端点——查验只能通过该连接器实现。

## 2. 工具说明

| 工具 | 用途 | 何时用 |
|---|---|---|
| `call_internal_api` | 调用内部 HTTP 接口 | 本技能唯一入口，`api="invoice_check"` |
| `list_internal_apis` | 列出可调用接口 | 排障 |
| `health_check` | 服务/DB 就绪 + 税号接入状态 | 排障 |

### 2.1 `call_internal_api`（查验唯一方式）

```json
call_internal_api(api="invoice_check", params={...})
```

**请求参数**（**严格大驼峰**，后端 `@JsonProperty` 强制大写）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `InvoiceType` | string | ✅ | 票种代码，不同代码走不同渠道，**不可臆造**（枚举见 `references/invoice-types.md`） |
| `InvoiceNo` | string | ✅ | 发票号码（数电票 20 位） |
| `InvoiceDate` | string | ✅ | 开票日期，**必须 `yyyyMMdd` 紧凑格式**（`20260916`） |
| `Amount` | number | ✅ | 金额，单位 **分**（整数）；**口径随票种变化**（见 §2.2） |
| `InvoiceCode` | string | 视票种 | 数电票（31/32/61/83）可空；其余**必填**（纸质票 10-12 位代码） |
| `CheckCode` | string | 视票种 | 见 §2.3 |

**调用示例**（数电普票 9.00 元）：

```json
{"api":"invoice_check","params":{
  "InvoiceType":"32","InvoiceNo":"26507200000011978330",
  "InvoiceDate":"20260916","Amount":900}}
```

**响应信封**（腾讯云风格，**没有 `code` 字段**）：

```json
{"Response":{"RequestId":"xxx","Error":null,"Data":{...票面...}}}
```

| 判定 | 含义 |
|---|---|
| `Error == null` 且 `Data` 有值 | 查验通过 |
| `HTTP 200 + Error.Code="InvoiceCheckError"` | 业务查验失败，`Error.Message` 是中文 |
| `HTTP 400 + Error.Code="InvalidParameter"` | 参数校验失败 |

### 2.2 `Amount` 口径（最容易错，务必先确认）

单位一律**分**：`Amount = int(round(元 × 100))`。口径随票种变化：

| 票种 | 取票面哪一栏 | 示例 |
|---|---|---|
| 01 / 09 / 23 | **不含税金额**（票面「金额」栏） | 8.26 → `826` |
| 04 / 10 / 24 | **不含税金额**（可空，置 `0`） | 8.26 → `826`；拿不到 → `0` |
| 11 / 14 | **不含税金额** | 8.26 → `826` |
| 31 / 32 / 61 / 83 | **价税合计** | 9.00 → `900` |
| 03 / 15 | **车价合计** | 120000.00 → `12000000` |

- 用户口头说的"开票金额 X 元"通常是**价税合计**；用在不含税口径的票种时**必须问到「金额」栏或税率**，不要拿价税合计直接填。
- 换算辅助脚本：`node scripts/calc-amount.mjs <票种> <元>`（如 `node scripts/calc-amount.mjs 31 9.00` → 900）。
- 单位或口径错，税局只回「发票信息不一致」，看不出是金额问题还是票不存在，极易误判成假票。

### 2.3 `CheckCode` / `InvoiceCode` 规则

| 情形 | `CheckCode` 取值 |
|---|---|
| 01/02/03/08/15/23/31/32/61/83 | 可省略，传 `""` |
| 24 | 全电号码（数电号码）**后六位** |
| 04/09/10/11/14 | 票面右下角「校验码」**后六位** |

`InvoiceCode`：31/32/61/83 数电票可空；其余票种必填。

## 3. 执行流程

### 步骤 1：获取要素

**入口 A（文件）**：用视觉能力直接读 PDF/图片提取要素；PDF 读不清先用
`node scripts/prepare-image.mjs <文件> [输出目录]` 转 PNG。

> ⚠️ **Python 解释器**：`scripts/decode-qr.py` / `pdf_to_png.py` 依赖 PyMuPDF + OpenCV，
> **系统 python3 通常没装**。请使用当前环境中已装好 `pymupdf` + `opencv-python-headless` 的 Python 解释器：
> `python3 scripts/decode-qr.py <文件>`
> 报 `No module named 'pymupdf'` 时先安装依赖（`pip install pymupdf opencv-python-headless`）再重试，
> 不要改用其它方式绕过二维码校验。
> Node 脚本用当前环境可用的 Node 运行：`node scripts/xxx.mjs`

待提取字段与位置：发票类型（标题区）/ 发票代码、发票号码、开票日期（右上角，输出 `yyyyMMdd`）/
金额（按 §2.2 票种口径取对应栏）/ 校验码（右下角，取后六位，部分票种无）。

识别后：

1. **二维码交叉校验（强制）**：`python3 scripts/decode-qr.py <发票文件>`。
   数电票 20 位号码视觉识别极易多读/漏读 0，票面二维码是**权威数据源**
   （格式 `01,<票种>,<代码>,<号码>,<金额>,<日期>,<校验码>,...`）。号码/票种/日期/金额以二维码为准。
2. 按 `templates/ocr-fields.md` 输出识别结果表（每字段标「清晰/存疑」）。
3. **存疑字段先让用户确认再查验**——错一位号码或选错口径就白烧当日配额。

**入口 B（文字）**：直接进步骤 2。

### 步骤 2：票种反查（票种未确认时）

**必须把全部支持票种列出让用户选**，不要只问"专票还是普票"。先读 `references/invoice-types.md`。
常见票面标题 → 枚举：增值税专用发票 `01`、增值税普通发票 `04`、增值税电子普通发票 `10`、
电子发票（普通发票）/数电普票 `32`、电子发票（增值税专用发票）/数电专票 `31` 等。

### 步骤 3：调用查验

```json
{"api":"invoice_check","params":{
  "InvoiceType":"<票种>","InvoiceNo":"<号码>","InvoiceDate":"<yyyyMMdd>","Amount":<分>}}
```

### 步骤 4：判读（中文 Message 原样转达，不要自行解读）

| 返回 | 含义 | 处置 |
|---|---|---|
| `Error==null` 且 `Data` 有值 | 查验通过 | 输出票面，与用户信息逐项比对 |
| 所查发票不存在 | 税局无此记录 | 核对号码/日期；**≠ 假票** |
| 发票信息不一致 | 要素组合未命中（金额单位/票种/日期任一不对，或票未同步） | **先查 `Amount` 单位与口径**（最高频），再查票种 |
| 查询发票不规范 | 多为入参问题（尤其日期格式） | 改 `yyyyMMdd` |
| 超过该张票当天查验次数 | 当日 5 次配额用尽 | 次日再查，勿重试 |
| 二维码参数不合法 | 票种走二维码渠道缺校验码/代码 | 补全或换票种 |
| 处理业务异常 / 查验异常 | 下游渠道异常 | 记 `RequestId`，稍后重试 |

## 4. 超时与重试

- **仅瞬时故障重试**（超时/网络异常/响应无 `Data`）：重试最多 2 次（合计 3 次），退避 2s → 4s。
- **业务错误一律不重试**（不存在/不一致/不规范/超限/二维码不合法）——重试只会白烧配额。
- 重试耗尽仍无票面 → 记录每次 `RequestId`，如实反馈"连续 3 次未取到票面"，**不要臆造票面、不要下真伪结论**。

## 5. 错误场景与边界

| 场景 | 现象 | 处置 |
|---|---|---|
| 日期格式错 | 全表「查询发票不规范」 | 改 `yyyyMMdd`（`2026-09-16` → `20260916`） |
| 金额单位错（元） | 「发票信息不一致」 | 改成「分」 |
| 小写驼峰字段 | 「参数不能为空」 | 用大驼峰 `InvoiceType/InvoiceCode/...` |
| 配额耗尽 | 「超过该张票当天查验次数」 | 次日再查；**换票种不获得新配额**（配额按票号跨票种共享） |
| 二维码不合法 | 号码多读/漏读 0 | 解码票面二维码拿权威号码 |

**配额铁律**：同一张票**每天限查 5 次**，**未命中也计数**（成功票面 `CheckCount`=当日累计次数）。
票种不确定就问用户，一次只查一个票种；不要批量扫票种、不要把"换几个代码试试"当排查手段。

**排查技巧**（号码 +1 对照实验）：保持其余参数不变，号码末位 +1 查对照票——若返回「所查发票不存在」说明链路正常；
⚠️ 但票种 `32` 对未命中统一报「发票信息不一致」，此时对照实验**失效**，改做渠道自检（用已知有记录的票同票种再查一次）。

## 6. 输出

按 `templates/report-template.md`：识别要素表（入口 A）+ 票面要素表 + 与用户信息逐项比对（一致/不一致）+
未通过时给税局原文 `Message` 与 `RequestId` + 下一步建议。**查验通过必补「F. 销方企业画像」**。

## 7. 销方企业画像（查验通过后必出）

用本地脚本把票面销方翻译成结构化描述：

```bash
node scripts/seller-profile.mjs \
  --name "销方名称" --taxno <税号> \
  --tax-class-code <税收分类编码> --tax-rate <税率> --total <价税合计元> \
  --net <不含税元> --tax <税额元> --date <yyyyMMdd> --invoice-type <票种> \
  --goods "<商品简称>"
```

输出 8 板块：主体标识（含 GB 32100-2015 校验位核验）/ 名称结构 / 登记画像 / 行业画像 /
纳税人身份（13/9/6%→一般纳税人高置信；1%→小规模减按；3%/5%→小规模或简易计税不可区分）/
开票特征 / 提示 / 数据边界。

硬规则：18 位代码按 GB 32100-2015 计算校验位，不通过直接提示「税号可能有误」；
**不编造工商要素**（注册资本/法人/成立日期/股东/经营状态/参保人数票面没有，需外部工商查询并标注来源）；
3%/5% 不区分小规模与简易计税；票面简称与编码归类两套口径并列展示。

## 参考

- 接口规范、参数、错误码与重试语义：`references/api_protocol.md`
- 票种枚举全表（唯一数据源）：`references/invoice-types.md`
- 实测记录（含踩坑）：`references/examples.md`
- 识别字段表与确认话术：`templates/ocr-fields.md`；工作流清单：`templates/workflow.md`
- 画像素材：`references/region-codes.md`、`references/tax-class-industry.md`、`references/industry-keywords.md`
