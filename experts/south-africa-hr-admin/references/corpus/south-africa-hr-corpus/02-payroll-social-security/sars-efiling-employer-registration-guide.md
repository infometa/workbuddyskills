# SARS eFiling 雇主注册与薪酬合规实操指南

> **数据来源**：SARS官网（sars.gov.za）、Sparrows Accounting、John-Naicker Accounting、MyCompanyRegistrations
> **时效提示**：SARS eFiling界面和流程可能更新，以SARS官网最新指南为准

---

## 一、雇主注册总览

在南非雇佣员工，雇主须向以下机构注册：

| 注册项目 | 机构 | 条件 | 费用 |
|----------|------|------|------|
| **PAYE** | SARS | 员工收入超年度免税门槛（2024/25: R95,750/年 ≈ R7,979/月） | 免费 |
| **UIF** | SARS + DOL | 所有员工（每月工作超24小时即须注册） | 免费 |
| **SDL** | SARS | 年薪酬总额超R500,000 | 免费 |
| **COIDA** | Compensation Fund | 所有雇主（强制） | 按行业费率 |
| **BCEA合规** | — | 所有员工须有书面合同 | — |

### 注册时限
- SARS（PAYE/UIF/SDL）：1-3周
- DOL（UIF）：1-2周
- COIDA：2-4周

---

## 二、PAYE/UIF/SDL 注册流程（SARS eFiling）

### 前置准备文件
- 公司CIPC注册文件
- 银行账户信息
- 董事/负责人南非ID + 地址证明
- 公司物理地址与通讯地址
- 首位员工信息（姓名、ID、薪资、入职日期）

### 注册步骤

#### Step 1：登录SARS eFiling
- 访问 [sars.gov.za](https://www.sars.gov.za) → eFiling
- 个人portfolio：Home → SARS Registered Details
- 组织/税务师portfolio：Organisations菜单 → SARS Registered Details

#### Step 2：维护注册信息
- 选择 "Maintain SARS Registered Details"
- 确认授权声明（I Agree）

#### Step 3：添加税务产品注册
- 选择 "Add new product registration"
- 系统弹出RAV01表单（Registration Amendments and Verification Form）

#### Step 4：填写RAV01表单
- **PAYE状态**：默认"Yes"
- **SDL状态**：年薪酬超R500,000选"Yes"（显示SDL与豁免详情容器）
- **UIF状态**：选择PAYE后自动变为"New Registration"
- **商业活动代码**：选择适用的Business Activity Code

#### Step 5：生物识别认证
- 个人申请者可能需要完成面部生物识别认证
- 税务师代申请：纳税人须通过邮件/短信中的唯一识别码授权，并完成生物识别认证

#### Step 6：提交与验证
- 提交后SARS进行验证（因欺诈注册增多，验证可能需额外文件）
- 若收到"Registration Application Review Notice"，须在**21个工作日内**提交支持文件
- 支持文件提交渠道：eFiling / SARS在线查询系统 / SARS分行
- SARS分行仅接受A4格式文件

> ⚠️ **未在21个工作日内提交文件将导致申请被拒绝。**

---

## 三、UIF双重注册（重要！）

### SARS注册 ≠ DOL注册
- **SARS注册**：用于月度EMP201申报缴费（PAYE+UIF+SDL合并申报）
- **DOL注册**：用于UIF索赔处理，须通过uFiling（ufiling.co.za）单独注册

### DOL UIF注册流程
1. 访问 [ufiling.co.za](https://www.ufiling.co.za)
2. 提交UI-8（雇主注册表）
3. 为每位员工提交UI-19（雇员申报表）
4. 获取DOL UIF参考号

> **常见错误**：仅向SARS注册UIF而未向DOL注册，导致员工无法索赔UIF津贴。

---

## 四、COIDA注册

### 注册流程
1. 向Compensation Fund提交 **W.As.2表**
2. 获取雇主注册号（Employer Registration Number）
3. 按行业风险等级缴纳保费
4. 每年提交ROE（Return of Earnings）

### 注册时限：2-4周

---

## 五、月度合规：EMP201申报

### EMP201内容
- **PAYE**：从员工薪资中预扣的个人所得税
- **UIF**：雇主1% + 雇员1% = 2%
- **SDL**：雇主1%（年薪酬超R500,000时）
- **ETI**：雇佣税激励扣减额（如有）

### 申报截止日
- **每月7日**（若7日为周末/公共假日，提前至前一工作日）
- 通过SARS eFiling / e@syFile / 第三方薪酬软件提交
- 支付截止日同申报截止日

### 逾期后果
- **10%罚金** + 每日复利
- SARS审计风险增加

---

## 六、半年度合规：EMP501对账

### 两次对账申报

| 对账类型 | 申报期 | 截止日 |
|----------|--------|--------|
| **中期对账**（Interim Reconciliation） | 3月1日-8月31日 | 9月底/10月初（每年SARS公告具体日期） |
| **年度对账**（Annual Reconciliation） | 3月1日-次年2月28/29日 | 5月31日 |

### EMP501内容
- 所有员工的IRP5/IT3(a)税务证书
- PAYE/UIF/SDL总额汇总
- 月度EMP201与实际薪酬的一致性核对

### 提交方式
- 通过 **e@syFile Employer**（SARS桌面软件，当前v8.0）
- 批量上传IRP5源代码文件

---

## 七、IRP5税务证书

### IRP5必须包含
- SARS源代码（如3601=薪资、3701=差旅津贴、4001=医疗援助等）
- 员工税号
- 雇佣起止日期
- 所有收入、扣减、附加福利

### 关键源代码示例

| 源代码 | 含义 |
|--------|------|
| 3601 | 普通薪资 |
| 3605 | 奖金 |
| 3701 | 差旅津贴 |
| 3702 | 公司车使用 |
| 4001 | 医疗援助雇主缴费 |
| 4005 | 退休金雇主缴费 |
| 4474 | UIF雇员缴费 |

---

## 八、记录保存要求

### 最低保存期限：5年

须保存的记录包括：
- IRP5证书
- 工资单（Payslips）
- EMP201和EMP501提交凭证
- 薪酬汇总与计算记录
- 签署的劳动合同及修订

---

## 九、常见合规错误

1. **错过EMP201截止日** — 无宽限期，必须7日前提交+付款
2. **IRP5源代码错误** — 导致员工税务申报不匹配，触发SARS审计
3. **仅向SARS注册UIF未向DOL注册** — 员工无法索赔
4. **"账外"支付员工** — 不注册PAYE/UIF，SARS严查disguised employment
5. **兼职/临时工未注册UIF** — 每月工作超24小时即须注册UIF
6. **未更新员工变动** — 员工增减时未及时通知SARS
7. **未使用合规薪酬软件** — 手工计算易出错，建议使用SARS认证薪酬系统

---

## 十、中资企业实操建议

1. **注册前置**：CIPC注册→SARS税号→PAYE/UIF/SDL注册→COIDA注册→DOL UIF注册，全流程2-4周
2. **薪酬系统选择**：使用SARS合规的薪酬软件（如Sage Payroll、SimplePay、PaySpace），自动生成IRP5
3. **月度日历**：设置EMP201截止日提醒（每月7日前），确保不逾期
4. **半年度准备**：9月中期对账和5月年度对账前1个月即开始准备IRP5数据
5. **ETI利用**：若雇佣18-29岁、月薪<R7,500的员工，务必在EMP201中申报ETI扣减
6. **税务师合作**：建议聘请SARS注册税务师（Registered Tax Practitioner）处理月度和年度申报
7. **审计准备**：保持5年完整薪酬记录，随时可应对SARS审计
8. **e@syFile版本**：确保使用最新版e@syFile（当前v8.0），旧版可能不兼容

---

**免责声明**：SARS eFiling流程可能随时更新，本指南基于2024-2025年公开信息整理。具体操作请以SARS官网最新指南和注册税务师建议为准。
