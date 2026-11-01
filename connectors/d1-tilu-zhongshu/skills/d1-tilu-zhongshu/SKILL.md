---
name: d1-tilu-zhongshu  
display_name: D1 题录中枢 · 标准查新检索  
description: 跨层级、跨语种检索全域标准题录（国标/行标/地标/团标/企标/ISO/IEC），用于标准查新、重复立项风险排查、现行有效性核验与标准台账治理。当用户询问"有没有同类标准""这个标准号是否现行""查一下某领域有多少标准"时使用本技能。  
description_zh: 跨层级、跨语种检索全域标准题录（国标/行标/地标/团标/企标/ISO/IEC），用于标准查新、重复立项风险排查、现行有效性核验与标准台账治理。  
description_en: Search the global standards bibliographic database across all tiers and languages for novelty searches, duplicate-proposal risk checks, validity verification and ledger governance.  
---

# D1「题录中枢」标准题录检索

## 服务概述

D1 是深圳市标准技术研究院标准研究服务中心的全域标准题录数据库，通过 MCP 协议暴露 6 个只读查询工具。一次检索可跨 **国家标准（GB）、行业标准（QC/T、NB/T、SJ/T、JT/T 等）、地方标准（DB、SZDB/Z）、团体标准（T/ 系列）、企业标准（QB）以及 ISO/IEC/EN/DIN 等国际标准**。

服务地址：`https://mcp.sist.org.cn/mcp`（HTTPS，streamableHttp）

| 访问要素 | 值 |
| --- | --- |
| 公网 IP | `113.98.246.113`（中国电信 ChinaNet-GD） |
| 端口 | 443 |
| 证书 | `CN=*.sist.org.cn`，GlobalSign GCC R3 DV TLS CA 2020，有效期至 2027-01-24 |
| 协议 | TLS 1.3 / TLS_AES_256_GCM_SHA384 |
| 院内解析 | `10.204.67.101`（两条路径并存，均可用） |
| 实测 | 公网直连 HTTP 200，7 步全链路验证通过（2026-10-27） |

**服务已开通公网访问，审核与外部用户均可直接连接。**

---

## 六个工具

| 工具                       | 必填参数                | 用途                                                                  |
| ------------------------ | ------------------- | ------------------------------------------------------------------- |
| `std_health`             | 无                   | 服务与数据时效自检，返回 status、upstreamLatencyMs、lastSyncTime                  |
| `std_search`             | `keyword`           | 题录关键词检索，命中题名/主题词/摘要，是最常用的入口                                         |
| `std_get_by_code`        | `stdCode`           | 按标准号取单条全量题录：名称/类型/性质/状态/五个日期/ICS/CCS/主题词/摘要/采标/代替/修改件/被引用/发布组织/馆藏线索 |
| `std_get_relations`      | `stdCode`           | 代替关系链（含成环检测）、采标关系（IDT/MOD/NEQ+国际标准号）、被引用清单、修改件                      |
| `std_batch_check_status` | `stdCodes[]`        | 批量核查状态，1–100 个/次，返回顺序与入参一致                                          |
| `std_domain_stats`       | 无（keyword/ics 至少一项） | 领域存量分组计数，按 stdType / publishYear / status 分组，不返回明细。**P2 立项论证专用**    |

### 参数取值

- `stdType`：`GB,HB,DB,TB,QB,ISO,IEC`（逗号分隔，可组合）
- `status`：`CURRENT`（现行）/ `FUTURE`（即将实施）/ `ABOLISHED`（废止）/ `REPLACED`（被代替）/ `REVISING`（正在修订）
- `std_search` 的 `size` 最大 20，`page` 从 1 开始
- `std_get_by_code` 的 `includeAbstract` 默认 true；列表模式不返回摘要与馆藏线索

---

## ⚠️ 关键调用纪律（实测得出，务必遵守）

### 0. 任何工具调用前必须先 `initialize`

MCP 协议约束：`initialize` 会在响应头下发 `Mcp-Session-Id`，**后续所有请求都必须携带该头**。
未先 initialize 就调 `tools/list` 或任何 `tools/call`，服务端会抛
`WebMvcStreamableServerTransportProvider` 异常（表现为返回一段 Java 堆栈 JSON），并提示
`Session ID missing`。

**正确顺序**：`initialize` → 取 `Mcp-Session-Id` → 后续请求带上该头。
MCP 客户端通常自动处理；手动调用时务必注意。

### 1. `ics` 与 `yearFrom`/`yearTo` 参数不生效

传入 `ics:"29.240"` 与不传结果完全相同；传根本不存在的 `ics:"99.999"` 依然返回全部记录。年份过滤同样无效。

**正确做法**：先检索拿题录，再读每条的 `ics` / `publishDate` 字段做**本地筛选**。  
**禁止**在报告或结论中写"按 ICS XX 检索"或"限定年份检索"——那是不实陈述。

### 2. `stdType=HB` 会漏掉整个行业标准层

D1 中行业标准按各自行业代号存储前缀（`QC/T` 汽车、`NB/T` 能源、`SJ/T` 电子、`JT/T` 交通、`YB/T` 轻工…），**不是统一的 "HB"**。而 `std_domain_stats` 的 `groupBy=stdType` 只输出 GB/DB/HB/QB/ISO 等少数类型，行标编码根本不进统计。

**正确做法**：检索时**不加 `stdType` 过滤**、用 `page` 翻页拉全量，再在前端按标准号前缀分层归类。

### 3. 层级归属规则

- `GB` / `GB/T` → 国家标准（`GB` 强制、`GB/T` 推荐）
- `QC/T` `NB/T` `SJ/T` `JT/T` `YB/T` `DL/T` → **行业标准**
- `DB` `DB/T` `SZDB/Z` → 地方标准
- `T/` 前缀（`T/CAAMTB` `T/CSAE` `T/CPQS` `T/GERS`…）→ **团体标准**（注意：`T/` 是团标，不是行标）
- `QB` / `QB/T` → 企业标准
- `EN` `DIN` `UL` `IEEE` `BS` `IEC` `ISO` → 国际/国外标准

### 4. `page > 1` 时 `total` 字段返回 0

但 `items` 仍有内容。**判断是否还有下一页要用「返回条数 < size」**，不要依赖 `total`。

### 5. `std_batch_check_status` 的 `currentCode` 不可信

状态为 `REPLACED` 时 `currentCode` 仍可能指向自己。  
**判断现行版本要读 `std_get_by_code` 的 `replacedBy` / `replaces` 字段。**

### 6. 标准号必须用规范写法

`"GB/T 36547-2018"` ✅；`"gbt 1.1-2020"` ❌（上游 HTTP 502）。斜杠、年份、连字符齐全。

### 7. 部分题录 title 为空

如 `IEC 61071-2007`。此时标注"题录名称缺失"，**绝不编造名称**。

### 8. `std_domain_stats` 的 groupBy=status 键名特殊

键为 `A`（有效）/ `W`（作废），不是 CURRENT/ABOLISHED。两种维度键名不统一。

### 9. `lastSyncTime` 恒为 null

查新报告写检索日期时用**实际检索日期**，不要引用该字段。

### 10. 服务有速率限制

高频连续调用会返回 `{"code":-32002,"message":"触发限流（42901）"}`。批量核查请一次传 15–20 个标准号；遇 42901 退避 5–10 秒后重试。

---

## 标准调用范式

### 范式 A · 查新摸底（关键词 → 分层 → 逐条比对）

```
1. std_domain_stats {keyword:"XXX", groupBy:"stdType"}   先看存量分布
2. std_search {keyword:"XXX", size:20}                   不加 stdType，翻页拉全量
3. 按标准号前缀在前端分层（国标/行标/地标/团标/企标）
4. std_search {keyword:"XXX", status:"CURRENT"}          单独看现行子集
5. std_get_by_code {stdCode:"..."}                       取 ICS/CCS/摘要/代替关系
6. std_get_relations {stdCode:"...", depth:3}            查代替链与采标关系
```

### 范式 B · 台账治理 / 引用核验

```
std_batch_check_status {stdCodes:["GB/T 36547-2018","NB/T 33015-2014"]}
→ 对 REPLACED 项再调 std_get_by_code 读 replacedBy 确认现行版本
```

### 范式 C · 立项论证存量画像（P2 专用）

```
std_domain_stats {keyword:"XXX", groupBy:"publishYear"}   年度立项节奏
std_domain_stats {keyword:"XXX", groupBy:"status"}        现行/作废比例
```

---

## 服务接入形态说明（安装者与审核方常问）

### 为什么浏览器打开网址看到 404 / 401？

D1 是 **MCP 协议服务，不是网页服务**。根路径 `/` 无 Controller 映射，浏览器访问会看到
Spring Boot 默认错误页（Whitelabel Error Page）或 401 —— **都是正常现象**。

- 浏览器地址栏只能发 GET，且无法设置 `Authorization` 与 `Accept` 头，因此必然报错
- 服务端只实现 `/mcp` 一个端点
- 同一个 404 会因 `Accept` 头不同呈现两种形态：带 `text/html` 返回 HTML 错误页，
  默认 `*/*` 返回 JSON 错误对象。**两者都说明服务在线**

**判定服务正常的正确方法**：

| 方法 | 正常表现 |
| --- | --- |
| 访问 `https://mcp.sist.org.cn/mcp` | 返回 **401** `未认证或密钥无效（40101）` → 路由存在、校验生效 |
| `POST .../mcp` + Bearer 令牌 | 返回 **200** + `serverInfo: {"name":"d1-tilu-zhongshu","version":"1.0.0"}` |
| MCP 客户端连接 | 列出 6 个工具 |

### `Accept` 头必须同时声明两种类型

服务端**只接受 SSE 流式响应**。若 `Accept` 只写 `application/json`（不写 `text/event-stream`），
服务端直接抛错：

```
Invalid Accept headers. Expected TEXT_EVENT_STREAM and APPLICATION_JSON
```

✅ 正确：`Accept: application/json, text/event-stream`

响应体是 SSE 格式，从 `data:` 行取 JSON：
```
id:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
event:message
data:{"jsonrpc":"2.0","id":1,"result":{...}}
```

### 令牌换发

服务端令牌为静态凭证，**发生过换发**（2026-10-27 通用令牌已换发，旧值失效返回 401）。
用户若遇到 401 且确认令牌无误，请联系查新机构获取当前有效令牌——
**令牌由用户自行填写，本连接器不内置任何凭证**。

---

## 调用通道与审计归属

D1 提供两枚**功能完全等价**的访问令牌（同一服务、同一套 6 个工具、同一批数据、同一配额），
差别**仅在服务端日志的调用流水归集**：

| 令牌 | 适用场景 | 服务端流水归集 |
|---|---|---|
| 通用令牌 | 查新检索、立项论证、合规对标、对外交付 | 通用通道 |
| P9 专用通道令牌 | 标准台账治理、版本预警、批量状态核查 | P9 通道 |

**本连接器只上架一个**（`source: d1-tilu-zhongshu`），因为两枚令牌在客户端侧无任何差异，
拆成两个连接器会让市场出现两个功能相同的选择项。

**审计归属由用户填入的令牌决定**。因此：

- 用户做**台账治理、版本预警、批量状态核查**时，若其持有 P9 通道令牌，
  应提示其在连接器设置中改填 P9 令牌，以使调用流水归集到 P9 审计通道；
- 其余场景使用通用令牌即可。

已连接用户更换令牌的方式：连接器管理页 → 找到本连接器 → 重新填写令牌。

---

## 报告口径纪律

1. D1 已覆盖：GB / HB / DB / QB / ISO / IEC / EN / DIN / QC / NB / SJ / JT / YB 等  
   → 可写"经标准题录检索核验"
2. D1 **未覆盖社会团体标准**（`stdType=TB` 返回 0）→ 须写明团标层为公开来源补充检索
3. 不得写"按 ICS 检索""限定年份检索"
4. 空标题题录 → 标注"题录名称缺失"，不编造
5. `lastSyncTime` 为 null → 检索日期用实际日期

---

## 错误处理

| 现象                           | 原因       | 处理                      |
| ---------------------------- | -------- | ----------------------- |
| HTTP 401 / `未认证或密钥无效（40101）` | 令牌无效或过期  | 引导用户重新连接、重新填写令牌         |
| HTTP 502                     | 标准号写法不规范 | 改用规范写法（斜杠+年份+连字符）重试     |
| `触发限流（42901）`                | 调用过于频繁   | 退避 5–10 秒后重试；批量场景一次多传几个 |
| `item not found`             | 该标准号不在库中 | 如实写"经题录检索未检出"，不要臆造      |
| `ToolSearch` 找不到工具           | MCP 未连接  | 提示用户在连接器管理页确认已连接并信任     |
