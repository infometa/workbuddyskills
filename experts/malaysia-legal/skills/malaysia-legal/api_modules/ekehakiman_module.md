# e-Kehakiman — 马来西亚司法查询 Web-Scrape 模块

> 模块类型：Web-Scrape（无公开 API，需授权访问详细内容）
> 生成日期：2026-06-25
> 官网：https://www.kehakiman.gov.my/
> 电子司法系统：https://efs.kehakiman.gov.my/
> Risa 调用优先级：DD Mode Phase DD-6 司法风控

---

## 一、可用司法查询入口

### 1.1 e-Kehakiman（官方门户）

| 属性 | 值 |
|------|-----|
| 网址 | https://www.kehakiman.gov.my/ms/e-kehakiman |
| 功能 | 司法系统电子服务入口 |
| 子服务 | e-Filing（电子立案）、e-Court（电子法院）、Case Search（案件搜索） |

### 1.2 e-Court Services（案件搜索）

| 属性 | 值 |
|------|-----|
| 网址 | https://ecourtservices.kehakiman.gov.my/ |
| 搜索入口 | https://ecourtservices.kehakiman.gov.my/Ticket/Search2?cultureCode=en |
| 访问限制 | 需注册法院授权方可查看案件详情 |
| 公开信息 | 仅可确认"是否有案件"（有限信息） |

### 1.3 Malaysian Courts — Cause List（开庭排期）

| 属性 | 值 |
|------|-----|
| 搜索方式 | 网络搜索 `site:kehakiman.gov.my "cause list" <company_name>` |
| 用途 | 发现目标企业是否在近期法院排期中 |

---

## 二、替代公开搜索策略（无需法院授权）

由于 e-Court 详细数据需要法院授权，Risa 采用以下多层替代搜索：

### 层 1：主流财经媒体报道（最高效）

```
搜索关键词：
"<company_name>" lawsuit court Malaysia
"<company_name>" winding-up petition
"<company_name>" sued legal action
"<company_name>" bankruptcy liquidation Malaysia
site:theedgemarkets.com "<company_name>" court
site:thestar.com.my "<company_name>" lawsuit
site:nst.com.my "<company_name>" legal
site:freemalaysiatoday.com "<company_name>" court case
```

### 层 2：破产管理局 (MDI) 公开公告

```
搜索关键词：
"<company_name>" "Malaysian Department of Insolvency"
"<company_name>" "winding-up" "gazette" Malaysia
site:mdi.gov.my "<company_name>"
```

### 层 3：劳动纠纷 (Industrial Court)

```
搜索关键词：
"<company_name>" "Industrial Court" Malaysia
"<company_name>" "industrial dispute" employee
"<company_name>" "unfair dismissal" Malaysia
```

### 层 4：仲裁与商业纠纷

```
搜索关键词：
"<company_name>" arbitration Malaysia
"<company_name>" "breach of contract" litigation
"<company_name>" "debt recovery" court Malaysia
```

---

## 三、高管个人司法筛查

DD Mode 必须同时对核心高管执行司法排雷：

```
搜索关键词：
"<director_name>" court case Malaysia
"<director_name>" bankruptcy Malaysia
"<director_name>" "director disqualification" SSM
"<director_name>" fraud Malaysia
```

若检出高管有不良记录 → 触发 `🔴 高管司法红灯` 预警

---

## 四、Risa Agent 调用指令

### Phase DD-6 司法破产排雷标准流程

```
Step 1: 企业诉讼检索
并行搜索 6 大财经媒体 + 3 大法律关键词
→ 提取：案件类型（民事/刑事/商业）、涉案金额、审理进度

Step 2: 破产/清盘公告
定向搜索 MDI 公告 + 政府公报
→ 提取：清盘令状态、接管人信息、债权人会议日期

Step 3: 劳动纠纷
定向搜索 Industrial Court + 劳动仲裁
→ 提取：纠纷原因、涉及员工数、裁决结果

Step 4: 高管司法
对核心董事/股东逐个执行司法搜索
→ 提取：个人破产、董事资格、欺诈记录

Step 5: 汇总评级
🟢 无公开司法记录
🟡 存在一般民事诉讼（非核心经营影响）
🔴 存在清盘令/破产/刑事指控/高管司法红灯
```

---

## 五、可信度分级

| 来源 | 可信度 | 说明 |
|------|--------|------|
| e-Kehakiman 官方（授权访问） | A | 法院官方记录 |
| 财经媒体（The Edge, The Star, NST, FMT, Malay Mail, BFM） | B | 经过编辑核实的报道 |
| MDI 破产公告 | A | 政府官方公告 |
| 社交媒体/论坛 | C | 需交叉验证 |
| 公司自行披露（Bursa Malaysia 公告） | A | 上市公司强制披露 |

---

## 六、输出格式

在 DD 报告中写入：

```
## 📋 信用与司法风险

| 风险维度 | 状态 | 详情 |
|---------|------|------|
| 民事诉讼 | 🟢/🟡/🔴 | ... |
| 刑事指控 | 🟢/🟡/🔴 | ... |
| 清算/破产 | 🟢/🟡/🔴 | ... |
| 劳动纠纷 | 🟢/🟡/🔴 | ... |
| 高管司法 | 🟢/🟡/🔴 | ... |
| 综合评级 | 🟢/🟡/🔴 | ... |

**数据来源**：The Edge Markets, e-Court (kehakiman.gov.my), MDI, Bursa Malaysia
**检索日期**：YYYY-MM-DD
```

**铁律**：若检出任一 🔴 项，必须在报告开头以粗体红字**全红预警**："⚠️ 经司法检索发现目标企业/高管存在严重法律风险，强烈建议暂停合作并进一步调查。"
