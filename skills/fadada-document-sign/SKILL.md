---
name: fadada-document-sign
description: "FaDaDa e-signature tool"
description_zh: "法大大电子签"
description_en: "FaDaDa e-signature"
version: 1.0.2
display_name: "法大大"
display_name_en: "FaDaDa"
visibility: "public"
---

<!-- agent_created: true -->

# 法大大电子签 - 发起合同签署

基于法大大 FASC API 5.0，提供一键式合同发起签署能力，将合同文件发送给签署方进行电子签署。

## 概述

fadada-document-sign 提供合同签署的完整生命周期能力：

- **发起合同签署** - 上传合同文件，系统自动识别签署方，用户确认后发起签署
- **查询签署模板** - 查询签署模板列表和详情，基于模板快速发起
- **查询已有流程** - 查询当前账号下的签署任务列表，支持状态筛选和关键词搜索
- **撤回签署任务** - 撤回尚未完成的签署任务（待提交、签署中状态）
- **下载已签合同** - 获取并下载已完成签署的合同文件

## 职责边界

| 属于本 skill | 不属于本 skill |
|-------------|----------------|
| 发起新的合同签署流程 | 起草/生成合同正文或 PDF |
| 将文件发给签署方签署 | 审查合同条款、识别风险 |
| 上传合同后发起签署 | 审批通过/驳回 |
| 查询签署模板列表和详情 | 作废已完成合同 |
| 查询已有签署流程 | - |
| 撤回未完成签署任务 | - |
| 下载已签署合同 | - |

## 执行入口约束

- **发起签署**：用户说"发合同"、"发个合同"、"把合同发出去"等时，判定为发起签署意图
- **查询已有流程**：用户说"查合同"、"查流程"、"查任务"、"看看有哪些合同"、"我的签署任务"等时，判定为查询已有流程意图
- **撤回任务**：用户说"撤回合同"、"撤回签署"、"撤销任务"、"取消合同"等时，判定为撤回任务意图
- **下载合同**：用户说"下载合同"、"下载已签合同"、"下载签署文件"、"保存合同"等时，判定为下载合同意图
- 进入本 skill 后，禁止只给解释性文本、方案建议或下一步提示；必须推进到对应工作流
- 选择工作流后，必须严格按步骤推进；禁止跳过入口步骤直接调用中间脚本

## 工作流推进规则

### 工作流 1：上传合同后直接发起签署

进入条件：用户说"发合同"且当前会话有上传文件

1. **获取合同文件** → 2. **上传文件到法大大** → 3. **收集签署方信息** → 4. **发起签署** → 5. **发布结果卡片**

### 工作流 2：查询签署模板后发起

进入条件：用户说"用模板发起"、"查一下模板"等

1. **查询模板列表** → 2. **查询模板详情** → 3. **收集签署方信息** → 4. **发起签署** → 5. **发布结果卡片**

### 工作流 3：查询已有签署流程

进入条件：用户说"查合同"、"查流程"、"查任务"等

1. **查询流程列表** - 调用脚本查询签署任务列表
2. **展示列表卡片** - 显示任务列表，包含任务名称、状态、创建时间等
3. **用户选择任务** - 用户可选择某个任务查看详情或执行其他操作
4. **执行后续操作** - 根据用户选择执行查看详情/撤回/下载等

### 工作流 4：撤回签署任务

进入条件：用户说"撤回合同"、"撤销任务"等

1. **获取任务ID** - 用户需提供或从列表选择要撤回的任务
2. **验证撤回条件** - 检查任务状态是否为可撤回状态（待提交/签署中）
3. **执行撤回** - 调用撤回接口
4. **发布结果卡片** - 显示撤回结果

### 工作流 5：下载已签署合同

进入条件：用户说"下载合同"、"保存合同"等

1. **获取任务ID** - 用户需提供或从列表选择要下载的任务
2. **验证下载条件** - 检查任务状态是否为已完成
3. **获取下载链接** - 调用下载接口获取下载地址
4. **下载文件** - 可选：指定保存路径自动下载
5. **发布结果卡片** - 显示下载结果（链接或本地路径）

## 禁止事项

- 禁止进入本 skill 后仅回复"请上传文件"、"请选择模板"等普通文本，而不发布对应卡片
- 禁止未执行工作流 1 的步骤 1 就直接调用发起签署脚本
- 禁止未执行工作流 2 的步骤 1 和步骤 2 就直接调用发起签署脚本
- 禁止在需要用户选择、上传、填写、确认时，用普通文本替代卡片交互
- 禁止在步骤 3 未收到用户提交结果前调用发起签署脚本
- 禁止发起失败或未拿到 taskId 时继续调用查询结果脚本
- 禁止撤回非可撤回状态的任务（已完成/已作废/已过期）
- 禁止下载非已完成状态的任务

## 典型工作流

### 工作流 1：上传合同后直接发起签署

**适用场景**: 用户上传合同文件，说"发合同给对方签"
**执行流程**:

1. **获取合同文件** - 先获取当前会话中用户上传的文件列表
    - 无文件：发布上传卡片，**等待用户上传**；用户上传后，重新执行步骤 1
    - 仅 1 个文件：直接使用该文件进入步骤 2，不再额外弹选择卡片
    - 多个文件：发布文件选择卡片，**等待用户选择**；用户选择后，使用其所选文件进入步骤 2
2. **上传文件到法大大** - 调用 `scripts/upload_file.py` 将合同文件上传到法大大平台
    - 支持 PDF 格式文件
    - 脚本返回 fileId，用于创建签署任务
3. **收集签署方信息** - 发布签署方信息填写卡片
    - 签署方类型：个人 / 企业
    - 签署方信息：姓名/企业名称、手机号/邮箱
    - 企业签署时还需填写经办人信息
    - **等待用户填写并提交**
4. **发起签署** - 用户提交信息后，调用 `scripts/initiate_sign.py` 发起签署
    - 必须传入步骤 2 返回的 fileId
    - 必须传入用户填写的签署方信息
    - 脚本返回 taskId（签署任务ID）和 signUrl（签署链接）
5. **发布结果卡片** - 展示签署发起结果
    - 成功：显示 taskId、signUrl、签署方信息
    - 失败：显示错误原因

**关键要点**:
- 步骤 1、3、5 必须发布卡片
- 用户提交信息补全表单后直接发起，无需额外确认
- 禁止跳过步骤

### 工作流 2：查询签署模板后发起

**适用场景**: 用户说"查一下有哪些模板"，然后选择一个发起
**执行流程**:

1. **查询模板列表** - 调用 `scripts/list_templates.py` 查询签署模板
    - 发布模板列表卡片，**等待用户选择**
2. **查询模板详情** - 用户选择模板后，调用 `scripts/get_template_detail.py`
    - 提取模板中的文件作为签署文件（无需用户再上传）
    - 提取模板中的签署方角色信息
3. **收集签署方信息** - 发布签署方信息填写卡片
    - 预填充模板中的签署方角色
    - **等待用户填写并提交**
4. **发起签署** - 用户提交后，调用 `scripts/initiate_sign.py` 发起签署
    - 必须传入 `--template-id` 参数
    - 签署方必须包含模板中的 participantId
5. **发布结果卡片** - 展示签署发起结果

**关键要点**:
- 与普通发起的核心区别：文件来自模板，签署方角色固定
- 禁止跳过步骤

## 技术实现

### 脚本清单

| 脚本路径 | 用途 | 关键参数 |
|---------|------|---------|
| `scripts/upload_file.py` | 上传合同文件到法大大平台 | `--file-path`: 文件路径, `--file-name`: 文件名 |
| `scripts/initiate_sign.py` | 调用法大大API发起签署 | `--task-name`: 任务名称, `--file-ids`: 文件ID列表, `--signers`: 签署方JSON |
| `scripts/list_templates.py` | 查询签署模板列表 | `--template-name`: 模板名称(可选) |
| `scripts/get_template_detail.py` | 查询模板详情 | `--template-id`: 模板ID |
| `scripts/list_sign_tasks.py` | 查询已有签署流程列表 | `--status`: 状态筛选, `--keyword`: 关键词, `--page`: 页码 |
| `scripts/query_sign_status.py` | 查询签署任务详情/状态 | `--task-id`: 任务ID |
| `scripts/cancel_sign_task.py` | 撤回签署任务 | `--task-id`: 任务ID, `--reason`: 撤回原因 |
| `scripts/download_signed_contract.py` | 下载已签署合同 | `--task-id`: 任务ID, `--save-path`: 保存路径 |
| `scripts/utils.py` | 公共工具函数 | - |

### 脚本使用说明

```bash
# ==================== 发起签署 ====================
# 上传文件
python scripts/upload_file.py --file-path "/path/to/contract.pdf" --file-name "合同.pdf"

# 发起签署
python scripts/initiate_sign.py \
  --task-name "劳动合同签署" \
  --file-ids '["file_id_from_upload"]' \
  --signers '[{"name":"张三","phone":"13800138000","actorType":"person"}]'

# 基于模板发起
python scripts/initiate_sign.py \
  --task-name "劳动合同签署" \
  --template-id "template_id" \
  --signers '[{"name":"张三","phone":"13800138000","actorType":"person","participantId":"xxx"}]'

# ==================== 查询已有流程 ====================
# 查询所有签署任务
python scripts/list_sign_tasks.py

# 按状态筛选（signing=签署中, finished=已完成, cancelled=已撤销）
python scripts/list_sign_tasks.py --status signing

# 关键词搜索
python scripts/list_sign_tasks.py --keyword "劳动合同"

# 分页查询
python scripts/list_sign_tasks.py --page 1 --page-size 20

# 查询单个任务详情
python scripts/query_sign_status.py --task-id "task_id_here"

# ==================== 撤回任务 ====================
# 撤回签署任务
python scripts/cancel_sign_task.py --task-id "task_id_here"

# 撤回并填写原因
python scripts/cancel_sign_task.py --task-id "task_id_here" --reason "合同内容有误"

# ==================== 下载合同 ====================
# 获取下载链接
python scripts/download_signed_contract.py --task-id "task_id_here"

# 下载并保存到本地
python scripts/download_signed_contract.py \
  --task-id "task_id_here" \
  --save-path "./signed_contract.pdf"
```

## 签署方传参说明

`--signers` 参数为 JSON 数组，每个元素表示一个签署方。

### 个人签署方

| 字段 | 必填 | 说明 |
| :--- | :--- | :--- |
| `name` | 是 | 个人姓名 |
| `phone` | 条件 | 手机号，`phone` 和 `email` 至少传一个 |
| `email` | 条件 | 邮箱，`phone` 和 `email` 至少传一个 |
| `actorType` | 是 | 固定传 `person` |

**示例**：
```json
[
  {
    "name": "张三",
    "phone": "13800138000",
    "actorType": "person"
  }
]
```

### 企业签署方

| 字段 | 必填 | 说明 |
| :--- | :--- | :--- |
| `name` | 是 | 企业全称 |
| `contactName` | 是 | 经办人姓名 |
| `phone` | 条件 | 经办人手机号，`phone` 和 `email` 至少传一个 |
| `email` | 条件 | 经办人邮箱，`phone` 和 `email` 至少传一个 |
| `actorType` | 是 | 固定传 `corp` |
| `openCorpId` | 否 | 企业ID（已授权企业） |

**企业示例**：
```json
[
  {
    "name": "杭州未来科技有限公司",
    "contactName": "李经理",
    "phone": "13800138000",
    "actorType": "corp"
  }
]
```

### 混合场景示例（个人 + 企业）

```bash
python scripts/initiate_sign.py \
  --task-name "采购合同签署" \
  --file-ids '["file_id"]' \
  --signers '[{"name":"杭州未来科技有限公司","contactName":"李经理","phone":"13800138000","actorType":"corp"},{"name":"王五","phone":"13900139000","actorType":"person"}]'
```

## 错误处理

| 场景 | 处理方式 |
| :--- | :--- |
| 文件格式不支持 | 提示用户仅支持 PDF 格式，请上传 PDF 文件 |
| 上传失败 | 展示错误信息，建议重新上传 |
| 签署方信息不完整 | 停在信息填写步骤，等待用户补全 |
| 发起签署失败 | 展示错误原因，提供重试选项 |
| 未配置凭证 | 提示配置法大大 API 凭证 |
| 任务状态不可撤回 | 提示当前任务状态不支持撤回（如已完成/已作废） |
| 任务状态不可下载 | 提示当前任务状态不支持下载（如签署中/未完成） |
| 任务不存在 | 提示任务ID无效或无权访问 |
| 下载失败 | 展示错误信息，建议检查网络后重试 |

## 关键注意事项

1. **静默前置检查** - 凭证配置检查自动完成
2. **状态校验** - 撤回仅支持待提交/签署中状态，下载仅支持已完成状态
3. **必须等待用户提交** - 展示信息填写卡片后，必须等待用户提交表单
4. **禁止跳过卡片渲染** - 所有展示节点必须通过卡片形式展示
5. **签署任务ID保存** - 发起签署后应保存 taskId，供后续查询/撤回/下载使用

## 法大大API对接说明

### API凭证获取指引

#### 正式环境上线流程

| 步骤 | 内容 | 详细说明 |
|:---:|------|---------|
| 1 | 个人注册&认证 | 企业管理员完成个人实名认证 |
| 2 | 企业创建&认证 | 创建企业并完成企业实名认证 |
| 3 | 创建应用并启用 | 创建应用并提交审核启用 |
| 4 | **获取凭证** | **获取 AppID、AppSecret、openCorpId** |
| 5 | 配置正式环境 | 替换为正式环境信息 |

> **详细操作指引**：https://dev.fadada.com/api-guide/YYNLQW2Z2W/9QMQ2MU4FGK3AOXA

#### 获取 AppID 和 AppSecret

**获取步骤**：

| 步骤 | 操作 |
|:---:|------|
| 1 | 进入 `企业设置` → `集成管理` → `应用集成`，选择已启用的应用 |
| 2 | 点击 AppSecret 的【查看】按钮 |
| 3 | 获取短信验证码并填写验证 |
| 4 | 验证通过后，点击【复制图标】复制 AppID 和 AppSecret |

#### 凭证配置

| 环境变量 | 说明 | 来源 |
|---------|------|------|
| FADADA_APP_ID | 应用ID（AppID） | 应用详情页 |
| FADADA_APP_SECRET | 应用密钥（AppSecret） | 应用详情页（需验证） |
| FADADA_OPEN_CORP_ID | 企业ID（openCorpId） | 应用详情页 / 自动获取 |
| FADADA_ENV | 环境 (production/uat) | 默认 production |

> ⚠️ **注意**：openCorpId 可不配置，系统会自动通过 `/app/get-openId-list` 接口获取应用归属企业的 openCorpId

### API基础信息

- **API版本**: FASC API 5.0
- **正式环境**: https://api.fadada.com/api/v5
- **UAT测试环境**: https://uat-api.fadada.com/api/v5

### 环境配置

设置 `FADADA_ENV` 环境变量：
- `production` - 正式环境（默认）
- `uat` - UAT测试环境

### OpenCorpId 自动获取

**重要特性**：如果未配置 `FADADA_OPEN_CORP_ID`，系统会自动通过 `/app/get-openId-list` 接口获取应用归属企业的 openCorpId。

配置优先级：
1. 显式传入 `open_corp_id` 参数
2. 环境变量 `FADADA_OPEN_CORP_ID`
3. **自动获取**（调用 API 获取应用归属企业信息）

适用场景：
- 用户未提供 openCorpId 时，自动获取应用归属企业
- 企业管理员不确定企业 ID 时，自动解析
- 多企业切换时，验证归属企业信息

### 认证方式

使用 HMAC-SHA256 签名算法进行接口认证：

1. 获取 AccessToken（凭证管理接口）
2. 组装请求参数并计算签名
3. 携带签名和 Token 调用业务接口

## 核心接口

| 接口 | 地址 | 说明 | 状态 |
|-----|------|------|------|
| 获取服务访问凭证 | /service/get-access-token | 获取访问令牌 | ✅ 可用 |
| 上传本地文件 | /file/get-upload-url | 获取上传URL | ✅ 可用 |
| 文件处理 | /file/process | 转换为PDF | ✅ 可用 |
| 创建签署任务 | /sign-task/create | 发起签署 | ✅ 可用 |
| 添加签署参与方 | /sign-task/actor/add | 添加签署方 | ✅ 可用 |
| 获取签署链接 | /sign-task/actor/get-url | 获取签署URL | ✅ 可用 |
| 查询签署任务详情 | /sign-task/app/get-detail | 查询单个任务状态 | ✅ 可用 |
| 查询签署模板列表 | /sign-template/get-list | 模板列表 | ✅ 可用 |
| 查询签署模板详情 | /sign-template/get-detail | 模板详情 | ✅ 可用 |
| 查询签署任务列表 | /sign-task/owner/get-list | 批量查询任务 | ✅ 可用 |
| 撤回签署任务 | /sign-task/cancel | 撤回任务 | ✅ 可用 |
| 获取合同下载链接 | /sign-task/owner/get-download-url | 下载合同 | ✅ 可用 |
| **查询授权用户列表** | /app/get-openId-list | **获取归属企业openCorpId** | ✅ 可用 |

## API 已知限制

以下接口已验证可用：
- 批量查询签署任务列表（`/sign-task/owner/get-list`）
- 撤回签署任务（`/sign-task/cancel`）
- 获取合同下载链接（`/sign-task/owner/get-download-url`）

如遇 404 错误，请确认账户是否具备相应权限。

## 签署任务状态说明

| 状态 | 说明 |
|------|------|
| draft | 草稿 |
| waiting | 待提交 |
| signing | 签署中 |
| finished | 已完成 |
| cancelled | 已撤销 |
| abolished | 已作废 |
| expired | 已过期 |

## API返回码说明

| 返回码 | 说明 |
|--------|------|
| 100000 | 请求成功 |
| 100001 | 系统错误 |
| 100002 | 访问凭证失效 |
| 200001 | 参数错误 |
| 200002 | 签名验证失败 |
| 300001 | 业务处理失败 |
| 400001 | 权限不足 |
