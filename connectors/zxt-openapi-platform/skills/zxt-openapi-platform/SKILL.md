---
name: zxt-openapi-platform
description: 通过自然语言调用中兴通简税开放平台。查询企业发票池（进项发票列表与详情）、查验发票真伪、采集与 OCR 识别发票、查询与提交发票勾选认证、发票入账、处理红字信息确认单、发票风险检测、查询企业授权。当用户提到进项发票、发票池、发票查验、发票识别、勾选认证、抵扣、发票入账、红字确认单、红冲、发票风险等税票业务时使用本技能。
---

# 中兴通简税使用指南

## 凭证获取（首次使用必读）

本连接器需要 **openId** 与 **openKey** 两个凭证，由中兴通简税开放平台分配。

**若用户尚未获取凭证，或提示凭证无效，请引导用户前往官网获取：**

> https://open.quandianfapiao.com/

获取路径：访问上述官网 → 注册/登录企业账号 → 申请开通开放平台能力 → 在开放平台控制台查看该企业对应的 openId 与 openKey。

拿到后，让用户在连接器的配置表单中填入这两个值即可。凭证仅保存在用户本机（`~/.workbuddy` 目录），不会上传云端。

**当用户反馈以下任一情况时，主动给出上述官网链接与获取路径：**

- 不知道该填什么、问"openId/openKey 从哪来"
- 尚未开通开放平台
- 凭证报错（见下文错误表 303 / 302）

## 能力范围

本连接器覆盖**进项（收票）侧**业务，共 14 个分类。**不含销项发票开具能力**（无法开具、红冲销项发票），如果用户需求涉及"开票""开具发票""销项"，请明确告知本连接器不支持。

| 分类 | 能力 | 是否依赖税局登录 |
|---|---|---|
| 通用接口 | 系统时间、获取/刷新 Token | 否 |
| 数电登录 | 账号登录、短信验证码、登录状态查询 | — |
| 发票池 | 进项发票列表、发票详情 | 否 |
| 发票采集 | 数据上传采集、文件采集（支持混贴票据） | 否 |
| 报账单 | 新增/修改/撤销/查询 | 否 |
| 发票认证 | 属期、待认证、已认证、提交与取消勾选、认证状态 | **是** |
| 发票入账 | 待入账、已入账、提交与撤销、入账状态 | **是** |
| 红字信息单 | 列表、操作、详情、申请明细、申请、申请撤销 | 否 |
| 发票查验 | 按票面查验、按文件查验 | 否 |
| 发票识别 | 文件识别、链接识别、混贴票据识别 | 否 |
| 发票风险雷达 | 单张/多张/按文件查风险 | 否 |
| 消息提醒 | 通知详情、历史消息列表 | 否 |
| 授权 | 授权查询 | 否 |
| 附录 | 发票类型、状态码、地区编码（仅参考，不可调用） | — |

## 工具说明

本连接器提供 7 个工具。**先用 `search_api` 或 `list_api_categories` 找到接口，再用 `call_api` 调用**，不要凭记忆猜测接口路径。

| 工具 | 用途 | 关键参数 |
|---|---|---|
| `list_api_categories` | 列出全部接口分类与接口清单 | 无 |
| `search_api` | 按关键词搜接口，返回 path、参数、文档链接 | `keyword`（必填） |
| `call_api` | 调用任意业务接口 | `path`（必填）、`params`、`file_refs` |
| `query_invoice_list` | 进项发票池列表查询（免记 path 的高层封装） | 全部可选，见下 |
| `get_token` | 获取 accessToken（每天限 200 次） | 无 |
| `get_system_datetime` | 获取服务器时间（无需鉴权） | 无 |
| `create_upload_ticket` | 为上传文件签发一次性票据 | `filename`（必填） |

`query_invoice_list` 参数（**全部为下划线命名**，与 `call_api` 的驼峰不同）：

- `page_no`、`page_size`
- `invoice_date_begin`、`invoice_date_end`（yyyy-MM-dd，需同时传才按日期检索）
- `invoice_code`、`invoice_number`
- `xsf_mc`（销方名称）、`qszt`（0未签收/1已签收）、`invoice_type`

## 调用铁律（务必遵守）

### 1. 判断成功必须看内层 `status`，不能看 `isError`

业务失败（如 `status: "300"` 参数错误、`"1024"` 登录失效）和凭证错误的返回中，`isError` **仍然是 `false`**。只有"工具名不存在"才会置 `true`。

拿到结果后必须解析内容并判断 `status === "200"` 才算成功。

### 2. `call_api` 一律使用驼峰参数名

参数名必须与 `search_api` 返回的 `params[].name` 完全一致。**传错参数名不会报错**，服务端会静默忽略该条件并按默认值查询——比如只传了错误参数名，会返回全库数据。这是最容易出错的地方。

正确示例：

```json
{
  "path": "/api/jxplus/zxtOpen/invoicePool/invoicePoolList",
  "params": {
    "invoiceDateBegin": "2026-06-20",
    "invoiceDateEnd": "2026-09-20",
    "pageNo": "1",
    "pageSize": "20"
  }
}
```

### 3. 查询类接口必须传日期范围

发票池等查询接口没有强制筛选护栏，不传条件会返回全库数据（可能上万条）。调用前先确认日期区间已传入。

### 4. 调用前先用 `search_api` 确认 path

传错 path 时返回的是"开放平台网络错误（HTTPError）"，**看起来像网络问题，实际是接口不存在**。不要据此判断网络故障，应先用 `search_api` 搜索接口中文名拿到准确 path。

常见接口 path 速查：

| 接口 | path |
|---|---|
| 授权查询 | `/api/jxplus/zxtOpen/auth/queryAuth` |
| 发票池列表 | `/api/jxplus/zxtOpen/invoicePool/invoicePoolList` |
| 按票面查验 | `/api/jxplus/zxtOpen/inspection/queryInspectionInvoice` |
| 查询登录状态 | `/api/jxplus/zxtOpen/natApp/getAppLoginStatus` |
| 获取当前属期 | `/api/jxplus/zxtOpen/invoiceCheck/getCurrSkssq` |
| 获取待认证发票 | `/api/jxplus/zxtOpen/invoiceCheck/getWaitAuthInvoice` |
| 红字信息单列表 | `/api/jxplus/zxtOpen/redInfo/getGmfRedInfoList` |
| 红字信息确认单申请 | `/api/jxplus/zxtOpen/redInfo/redInfoApply` |
| 获取申请红字发票明细 | `/api/jxplus/zxtOpen/redInfo/redInfoApplyDetail` |

### 5. 税费类接口需先完成税局登录

发票认证、发票入账、属期查询等接口依赖电子税局登录态。未登录时返回 `status: "1024"`、`message: "电局登录状态失效，请重新登录"`。

遇到 1024 时，先调 `/api/jxplus/zxtOpen/natApp/getAppLoginStatus` 查询登录状态，再按需走数电登录流程（账号登录或短信验证码登录）。发票池、红字信息单列表、发票查验、授权查询**不需要登录**。

## 上传文件类接口

识别、查验、风险检测、采集这几类接口需要先上传文件。流程分三步：

1. 调 `create_upload_ticket(filename)` 获取票据与上传命令，`filename` 扩展名须为 pdf、ofd、jpeg、jpg、png 之一；
2. 执行返回的 curl 命令把文件 POST 上去，拿到 `uploadId`；
3. 调 `call_api(path, params, file_refs={"fileStream": "<uploadId>"})`。

注意两级有效期：**票据本身 120 秒内有效**，必须在拿到后立刻上传；**上传得到的 `uploadId` 1800 秒内有效**，须在此时间内完成业务接口调用。票据单次使用，重复上传会返回 `invalid_ticket`。

Windows 环境执行 curl 时使用 `curl.exe`。

## 常见错误与恢复

| 错误 | 含义 | 处理方式 |
|---|---|---|
| `missing_credentials` | 未配置凭证 | 引导用户前往官网 https://open.quandianfapiao.com/ 获取 openId 与 openKey 后填入连接器配置 |
| `303 无效openId` | openId 错误 | 提示用户核对 openId；若确认未获取或已失效，请前往官网 https://open.quandianfapiao.com/ 重新获取 |
| `302 验签失败` | openKey 错误 | 提示用户核对 openKey；若确认未获取或已失效，请前往官网 https://open.quandianfapiao.com/ 重新获取 |
| `status: "300"` | 参数错误（如日期格式） | 检查参数格式，日期须为 yyyy-MM-dd |
| `status: "1024"` | 税局登录态失效 | 引导用户完成数电登录 |
| `platform_error` 网络错误 | **多为 path 不存在** | 先用 `search_api` 确认正确 path |
| `invalid_ticket` | 上传票据失效 | 重新调用 `create_upload_ticket` |

## 调用示例

**查询近三个月进项发票**

```
query_invoice_list(
  invoice_date_begin="2026-06-20",
  invoice_date_end="2026-09-20",
  page_no="1",
  page_size="50"
)
```

**查验一张发票**（数电票的 `jejym` 传价税合计金额，`invoiceCode` 可留空）

```
call_api(
  path="/api/jxplus/zxtOpen/inspection/queryInspectionInvoice",
  params={"invoiceNumber": "26117000001393073244", "invoiceDate": "2026-09-11", "jejym": "63.41"}
)
```

**查询企业授权有效期**

```
call_api(path="/api/jxplus/zxtOpen/auth/queryAuth", params={})
```

## 高风险操作须知

以下操作会改变税局或平台侧的真实状态，**执行前必须先向用户复述操作内容并取得明确确认**：

- 提交或取消发票勾选认证（影响当期抵扣）
- 提交或撤销发票入账
- 红字信息确认单的申请、确认、拒绝、撤销（影响开票方与受票方，涉及税额冲红）
- 报账单的新增、修改、撤销

确认时须说明：涉及的具体发票（号码/金额）、操作类型、可能产生的税务影响。用户未明确同意前不得调用。

## 返回数据说明

发票字段常见含义：`hjje` 金额（不含税）、`hjse` 税额、`jshj` 价税合计、`xsfMc` 销方名称、`gmfMc` 购方名称、`invoiceType` 发票种类代码（81 数电专票、82 数电普票）、`fpStatus` 发票状态（0 正常、8 红冲）、`qszt` 签收状态。

金额可能为负数，表示红冲或折让行。发票明细中可能出现同一商品正数行加负数折让行的结构，属正常业务情况，不是错误。
