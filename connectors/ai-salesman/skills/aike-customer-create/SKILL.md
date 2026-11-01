---
name: aike-customer-create
display_name: 新增客户
display_name_en: New Customer
description: 新增展会/销售客户，支持手动录入与名片图片 OCR 识别两种方式。当用户说"扫一下这个客户名片录入系统""新增一个客户""录个新客户"时触发。
description_zh: 新增客户：手动录入或名片图片 OCR 识别建档。
description_en: Create a new customer manually or via business-card OCR.
category: sales-commerce
version: 1.3.0
author: AI销客
---

# 新增客户

面向「展会现场专家」与「客户管理专家」的客户创建技能，支持手动录入 + 名片 OCR。

## 功能描述

- 手动录入新客户（客户名、来源、国家、规模、意向等级、价格敏感度、标签、联系人等）
- 通过名片图片 OCR 自动识别企业与联系人信息（提交后**异步完成**，需轮询查询结果）；识别完成后**服务端自动创建客户与联系人**，无需再手动建档
- 创建后返回客户 ID，可衔接「写跟进」「上传对话录音」

## 触发场景（自然语言示例）

- "扫一下这个客户名片，录入系统"
- "新增一个客户：XX 公司，联系人小李"
- "把这张名片存成客户"

## 通用调用约定（gsales MCP）

本技能通过 `gsales` 连接器（GlobalSales 外贸销客 MCP 网关）调用工具，统一遵循：

- **鉴权与归属**：以当前用户 OAuth 授权身份调用，数据回流该用户自己的外贸销客空间（跨用户数据隔离）。
- **`dry_run` 预演**：`create_customer` 支持 `dry_run=true`，仅回显载荷、**不落库**；默认 `false` 正式写入。
- **文件形态**：名片图片支持两种形态——`file_paths`（文件在运行环境可见，服务端代传）或 **预签名直传**（逐张 `presign_file_upload({ kind: "image", file_ext: "jpg" })` 拿 uploadUrl → 沙箱 `curl -T` 直传 → 以 `image_urls` 交接；远程连接器形态推荐）。
- **永不开放**：邮箱配置、营销发送、系统管理等凭证与外发能力（L4）任何面均不提供。
- **错误与恢复**：`401`=授权无效/过期/已断开 → 引导用户在 WorkBuddy 连接器管理中断开并重新连接「外贸销客」（会重新打开浏览器完成授权）；`403`=用户角色无此权限（本技能依赖 pc:customers:ls:add；连接器授权已固定全量业务权限，403 多为角色未配置该权限码）→ 联系管理员开通，或断开重连；`source` 必须用英文枚举值，传中文会校验失败。
- **OCR 直传流程（远程连接器推荐）**：每张图片 ① `presign_file_upload({ kind: "image", file_ext: "jpg" })` → ② 沙箱 `curl -T <图片路径> "<uploadUrl>" -H "Content-Type: <presign 返回的 contentType>"` → ③ 收集各张 `objectUrl`，`recognize_card_images({ image_urls: [...] })` 拿到记录 id → ④ 轮询 `get_card_ocr({ id })` 直到 `status=completed`；识别完成后服务端**已自动创建客户与联系人**，回显结果即可（仅在需要补录/修正时再用 `create_customer` / `update_customer`）。`file_ext` 必传（扩展名进对象 key 并决定 Content-Type，OCR 靠它识别格式）；凭证 10 分钟有效，过期重新 presign。手动录入（`create_customer`）不受影响。

## 依赖的 MCP 工具

通过 `gsales` 连接器调用：

| 工具名 | 用途 | 所需权限范围 | 状态 |
|---|---|---|---|
| `create_customer` | 新增客户 | `pc:customers:ls:add` | ✅ 已开放 |
| `presign_file_upload` | 申请 OSS 预签名直传凭证 | `mobile:ai_records:add` | ✅ 已开放 |
| `recognize_card_images` | 提交名片 OCR 识别任务（异步，完成后自动创建客户与联系人） | `mobile:ai_records:add` | ✅ 已开放 |
| `get_card_ocr` | 查询名片识别结果（轮询） | `mobile:ai_records:list` | ✅ 已开放 |

## 工具调用说明

### `create_customer`
- **用途**：创建客户档案
- **入参**（注意参数为下划线命名，与查询工具的驼峰不同）：
  - `customer_name`（string，**必填**）：客户 / 企业名称
  - `source`（enum，**必填**）：客户来源，取值 `online_channels`（线上渠道）/ `exhibitions`（展会）/ `other_offline_channels`（其他线下）/ `referrals`（转介绍）/ `others`（其他）
  - `country_code`（string，可选）：国家区号，如 +86 / ARG
  - `scale`（enum，可选）：企业规模 `large` / `medium` / `small`
  - `intention_level`（enum，可选）：意向等级 `high` / `medium` / `low`
  - `price_sensitivity`（enum，可选）：`very_high` / `high` / `medium` / `low` / `very_low`
  - `follow_status`（enum，可选）：跟进状态 `pending_assign` / `following` / `dealed` / `serving` / `lost`（不传走系统默认）
  - `remark`（string，可选）：备注
  - `product_tags`（string[]，可选）：产品偏好标签
  - `contacts`（object[]，可选）：联系人列表，元素 `{ name（必填）, position?, enterprise_name?（联系人所在企业名，与客户主体不同时填）, country_code?, email?（多个用英文逗号分隔）, phone?, wechat?, whatsapp?, extra_info?（额外信息，自由文本）, card_ocr_record_id?（关联名片 OCR 记录 id，便于溯源） }`
  - `dry_run`（boolean，可选，默认 `false`）：为 `true` 时返回 `{ dryRun: true, wouldCreate: <载荷> }`
- **返回**：`{ id, customerName, message: '客户已创建，可在 APP 客户管理中查看' }`
- **注意**：**客户名与来源为必填**，其余信息不全时可先落最小档案再补；`source` 必须用英文枚举值，用户说"展会上认识的"要映射为 `exhibitions`。

### `presign_file_upload`
- **用途**：申请 OSS 预签名 PUT 凭证（名片直传时逐张调用）
- **入参**：
  - `kind`（enum，**必填**）：名片/现场照片固定传 `image`
  - `file_ext`（string，**必填**）：图片扩展名（`jpg` / `png` / `webp`）——进对象 key 并决定 Content-Type，OCR 靠它识别格式
- **返回**：`{ objectUrl, uploadUrl, contentType, expiresInSeconds, hint }`

### `recognize_card_images`
- **用途**：提交名片图片发起 OCR 识别任务（**异步**，本次只返回记录 id 与初始状态，不返回识别结果）；识别完成后**服务端自动创建客户与联系人**
- **支持的图片**：jpg / png / webp，1–4 张（支持正反面）
- **入参**：
  - `file_paths`（string[]）：名片图片路径列表（1-4 张）——与 `image_urls` **二选一**；文件在运行环境可直接读取时用
  - `image_urls`（string[]）：已 curl 直传完成的 `objectUrl` 列表（1-4 张）——与 `file_paths` **二选一**（远程连接器推荐）
  - `exhibition_id`（string uuid，可选）：关联展会 ID
- **返回**：`{ id, status, reason, message }`（`status` 初始为 `processing`；OCR 提交失败时为 `failed`，看 `reason`）
- **注意**：本工具是"提交"不是"查询"——每次调用都会发起一次新识别任务并各自自动建档；查结果用 `get_card_ocr`

### `get_card_ocr`
- **用途**：按 id 查询名片识别记录（`recognize_card_images` 提交后的轮询入口）
- **入参**：
  - `id`（string uuid，**必填**）：识别记录 id（`recognize_card_images` 返回）
- **返回**：`{ id, status, ocrResult, reason, completedAt }`
  - `status`：`processing`=识别中（继续轮询）/ `completed`=成功（取 `ocrResult`）/ `failed`=失败（看 `reason`）
  - `ocrResult`：识别出的企业与联系人结构化信息（识别失败/未完成时为 null）
- **用法**：`recognize_card_images` 拿到 id → 周期性 `get_card_ocr({ id })` 直到 `status=completed` → 向用户回显关键字段（企业 / 联系人）。**识别成功时客户与联系人已由服务端自动创建**，不要重复调 `create_customer`；仅当信息不全需补录或用户要求修正时，再用 `create_customer` / `update_customer`

## 返回格式

- 创建成功：返回客户 ID + 摘要卡（名称 / 来源 / 联系人数）
- OCR 场景：提交识别后轮询 `get_card_ocr`，`completed` 即客户与联系人已自动建档，回显结果给用户即可（手动 `create_customer` 仅用于补录/修正）
- 手动录入信息不全时建议先 `dry_run=true` 预演，确认后正式写入
