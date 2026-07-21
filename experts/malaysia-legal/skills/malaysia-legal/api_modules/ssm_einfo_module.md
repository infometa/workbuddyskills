# SSM e-Info / MyData — 马来西亚工商注册 Web-Scrape 模块

> 模块类型：Web-Scrape（无公开免费 API，但有官方查询门户）
> 生成日期：2026-06-25
> 官网：https://www.ssm-einfo.my/
> 目标：提取企业注册号 (Registration No.)、成立日期、注册状态、董事信息
> Risa 调用优先级：DD Mode Phase DD-2 核心入口

---

## 一、可用的公开查询入口

### 1.1 SSM e-Info（官方门户）

| 属性 | 值 |
|------|-----|
| 网址 | https://www.ssm-einfo.my/ |
| 查询方式 | 按公司名 / 注册号搜索 |
| 费用 | 基础信息 MYR 5-25（约 ¥8-40） |
| 输出 | 公司基本信息、注册状态、成立日期 |
| API 可用性 | 官方提供的 API 仅面向商业客户（需签约） |
| 语言 | 英文 UI |

**Risa Web-Scrape 策略**：
- **搜索入口**：`https://www.ssm-einfo.my/` → 输入公司名称 → 提取 Registration No.
- **限制**：未付费仅能看到公司名和注册号（模糊匹配），详细信息需付费
- **建议**：Risa 在 DD Phase DD-2 中，用 e-Info 验证公司名是否真实存在并获取注册号即可

### 1.2 MyData-SSM（第三方服务）

| 属性 | 值 |
|------|-----|
| 网址 | https://mydata-ssm.my/ |
| 能力 | 获取带 CTC 印章的官方注册文件 |
| 用途 | 尽调报告附件 |

### 1.3 SSM Search（第三方 API）

| 属性 | 值 |
|------|-----|
| 网址 | https://ssmsearch.com/ |
| API 文档 | https://ssmsearch.com/blog/a-foolproof-guide-to-understanding-ssmsearch-api |
| 能力 | 商业 API，提供公司搜索、董事查询、财务报表 |

---

## 二、Risa Web-Scrape 流程

### DD Phase DD-2：锁定注册号

```
输入：公司名称（如 "Top Glove Corporation Bhd"）

Step 1: 网络搜索定向
搜索关键词 → site:ssm-einfo.my "公司名称"
替代搜索 → "公司名称" SSM registration number Malaysia

Step 2: 提取注册号
匹配模式：
  - 新格式: 202401234567 (12位数字)
  - 旧格式: 1234567-A / 1234567-A

Step 3: 验证格式
正则：r'\d{12}' (新) 或 r'\d{7,8}-[A-Z]' (旧)

Step 4: 进入 MyData-SSM
https://mydata-ssm.my/ → 输入注册号 → 获取公司基本信息卡片

输出：
✅ Company Name: Top Glove Corporation Bhd
✅ Registration No.: 199801012345
✅ Status: Existing
✅ Date of Incorporation: 1998-01-01
```

### 搜索关键词矩阵

| 目标信息 | 搜索关键词 | 可信度 |
|---------|-----------|-------|
| 注册号 | `"<company_name>" "registration number" SSM` | A |
| 成立日期 | `"<company_name>" "date of incorporation" SSM` | A |
| 注册地址 | `"<company_name>" "registered address" Malaysia` | B |
| 董事名单 | `"<company_name>" directors SSM` | B |
| 股东/实控人 | `"<company_name>" shareholders "substantial shareholder"` | C |

---

## 三、Risa Agent 交叉验证指令

### Phase DD-4 OSINT 交叉验证（强制执行）

提取到注册号后，执行：

```
Step 1: OpenCorporates 比对
https://opencorporates.com/companies/my/<registration_number>
→ 核实: 成立日期、注册状态与 SSM 记录是否一致
→ 标注: 🟢 一致 / 🔴 冲突（标红预警）

Step 2: Google Maps 实体防伪
搜索: "<registered_address> Malaysia"
→ 核实: 是实体办公地址还是虚拟地址/代办处
→ 标注: 🟢 实体地址 / 🟡 共享办公 / 🔴 虚拟地址/住宅

Step 3: LinkedIn 人力资本核查
搜索: "<company_name> Malaysia" site:linkedin.com
→ 提取: 员工规模区间、核心高管、组织架构
→ 标注: 🟢 >50员工 / 🟡 10-50 / 🔴 <10或无页面
```

---

## 四、替代数据源（当 SSM e-Info 无法直达时）

| 来源 | 网址 | 可用信息 |
|------|------|---------|
| Companies Commission of Malaysia | https://www.ssm.com.my/ | 公司注册官方信息 |
| CTOS Malaysia | https://www.ctoscredit.com.my/ | 企业信用报告（含工商信息） |
| Experian Malaysia | https://www.experian.com.my/ | 企业信用报告 |
| Dun & Bradstreet Malaysia | https://www.dnb.com.my/ | 企业档案 |
| OpenCorporates | https://opencorporates.com/ | 全球公司注册开放数据 |
| Business Data Guide | https://www.businessdataguide.com/ | 各国工商查询指南 |

---

## 五、注意事项

1. **SSM e-Info 公开查询不返回完整董事/股东信息** — 这些是付费内容
2. **注册号是关键锚点** — Risa 的一切后续交叉验证以此为基础
3. **Web-Scrape 而非 API** — 马来西亚 SSM 不提供免费公开 API，Risa 以定向网络搜索模拟
4. **PDPA 2010 合规** — 个人董事信息使用受限于马来西亚个人数据保护法
5. **费用预估** — 完整 SSM 报告 MYR 5-25，Risa 仅需将费用告知用户（不作为自动扣费行为）
