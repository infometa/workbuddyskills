# 万方选题 API 参考手册

> **本文件是全部 API 配置的唯一权威来源（Single Source of Truth）。**
> 所有团员 agent 文件中的 Base URL、AppKey、请求体模板、curl 示例、返回数据结构均以此文件为准。
> 如需修改 API 配置，只需修改本文件，无需逐个改 agent 文件。

---

## 一、通用配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Base URL | `https://api.wfdata.com` | 不带 .cn 后缀 |
| 认证头 | `X-Ca-AppKey: 108_9288c3c77544491b_3a14cd` | 主用密钥（已验证有效） |
| 备用密钥 | `X-Ca-AppKey: 108_3fcefc21a2f14ef9_6fddcc` | 备用（主密钥失效时使用） |
| Content-Type | `application/json` | 所有 POST 请求 |
| 路径格式 | `/topic/{module}/{endpoint}` | 必须斜杠格式，下划线返回 403 |

> ⚠️ **已作废密钥**：`30084_b82d79d5e1154fcc_62c12f` 已失效，切勿使用。

---

## 二、POST 接口

### read 系列（欧阳搜文）

| 接口 | 路径 | 请求体 | 用途 |
|------|------|--------|------|
| 文献查询 | `/topic/read/paper` | `{"keyword":"关键词","page":1,"type":"HIGH"}` | 按关键词检索论文 |
| 学者查询 | `/topic/read/scholar` | `{"keyword":"关键词","page":1,"sort":"HINDEX"}` | 检索领域学者 |

**type 枚举**：HIGH(高关注) / NEW(新发表) / DEGREE(学位论文) / REVIEW(综述)
**sort 枚举**：RELATIVITY(相关性) / HINDEX(H指数) / ARTICLE(发文量) / CITED(被引量)

```json
// 文献查询（高关注）
{"keyword":"帮信罪","page":1,"type":"HIGH"}
// 文献查询（学位论文）— 返回字段为 thesis 不是 periodical
{"keyword":"帮信罪","page":1,"type":"DEGREE"}
// 学者查询（按H指数排序）
{"keyword":"帮信罪","page":1,"sort":"HINDEX"}
```

### assess 系列（皇甫评度）

> ⚠️ assess 系列需要 3 个字段：title + keyword + abstract，不是单个 param。

| 接口 | 路径 | 请求体 | 用途 |
|------|------|--------|------|
| 新颖性评测 | `/topic/assess/NoveltyData` | `{"title":"标题","keyword":"关键词","abstract":"摘要"}` | 相似文献数量和趋势 |
| 新颖性评测论文 | `/topic/assess/NoveltyPaper` | 上述 + `,"type":"title"` | 相似文献论文详情 |
| 选题拓展 | `/topic/assess/TopicExtendData` | `{"title":"标题","keyword":"关键词","abstract":"摘要"}` | 关联主题分析 |
| 选题拓展论文 | `/topic/assess/TopicExtendPaper` | 上述 + `,"type":"HIGH_CNT","key":"主题名"` | 拓展方向论文 |
| 学科渗透 | `/topic/assess/SubjectOsmosisData` | `{"title":"标题","keyword":"关键词","abstract":"摘要"}` | 跨学科渗透特征 |
| 学科渗透论文 | `/topic/assess/SubjectOsmosisPaper` | 上述 + `,"education_code":"0301"` | 渗透学科论文 |

**NoveltyPaper.type**：title / keyword / abstracts
**TopicExtendPaper.type**：HIGH_CNT / NEWS

```json
// 新颖性评测 / 选题拓展 / 学科渗透（共用请求体）
{"title":"帮信罪的司法适用研究","keyword":"帮助信息网络犯罪活动罪;帮信罪","abstract":"本文研究帮信罪在司法实践中的适用问题"}
// 选题拓展论文
{"title":"...","keyword":"...","abstract":"...","type":"HIGH_CNT","key":"主观明知"}
// 学科渗透论文
{"title":"...","keyword":"...","abstract":"...","education_code":"0301"}
```

### find Data 系列（上官选道）

> ⚠️ find Data 的 param=关键词（不是 cluster）；search=KEYWORD 或 CODE。

| 接口 | 路径 | 请求体 | 用途 |
|------|------|--------|------|
| 学科列表 | `/topic/find/eduCodeList` | `{}` | 获取学科分类列表 |
| 学科热点 | `/topic/find/hotspot` | `{"param":"07","search":"HOTS"}` | 学科热点/新兴主题 |
| 回溯学术脉络 | `/topic/find/acadamicData` | `{"search":"KEYWORD","param":"关键词"}` | 学术脉络知识节点 |
| 追踪研究重点 | `/topic/find/frontierData` | `{"search":"KEYWORD","param":"关键词"}` | 前沿研究方向 |
| 拓展研究边界 | `/topic/find/acrossData` | `{"search":"KEYWORD","param":"关键词"}` | 跨学科拓展 |
| 发掘新兴主题 | `/topic/find/newthemeData` | `{"search":"KEYWORD","param":"关键词"}` | 新兴研究方向 |

**hotspot**：param=学科号（如"07"=生物学），search=HOTS(热点)/NEWS(新兴)

### find Paper 系列（上官选道，两步联动）

> ⚠️ find Paper 的 param=cluster 值（不是关键词！），cluster 必须从对应 Data 接口返回的 `nodes[].cluster` 获取。
> 建议使用 `bin/wanfang_topic_cli.py` 一键完成两步联动。

| 接口 | 路径 | 请求体 | 前置步骤 |
|------|------|--------|---------|
| 学术脉络论文 | `/topic/find/acadamicPaper` | `{"paper":"HIGH","param":"cluster值"}` | 先调 acadamicData |
| 前沿重点论文 | `/topic/find/frontierPaper` | `{"paper":"HIGH","param":"cluster值"}` | 先调 frontierData |
| 边界拓展论文 | `/topic/find/acrossPaper` | `{"paper":"HIGH","param":"cluster值"}` | 先调 acrossData |
| 新兴主题论文 | `/topic/find/newthemePaper` | `{"paper":"NEW","param":"cluster值"}` | 先调 newthemeData |

**paper 枚举**：HIGH / NEW / DEGREE / REVIEW

### title 系列（夏侯拟言）

| 接口 | 路径 | 请求体 | 用途 |
|------|------|--------|------|
| 标题推荐 | `/topic/title/recommend` | `{"keyword":"关键词"}` | 生成推荐标题 |
| 关键词关联主题 | `/topic/title/synonyms` | `{"keyword":"关键词","page":1}` | 获取关联主题词 |

### report 系列（太史撰域）

| 接口 | 路径 | 请求体 | 用途 |
|------|------|--------|------|
| 研究趋势分析 | `/topic/report/reportNovelty` | `{"keyword":"关键词"}` | 主题相似数据与趋势 |
| 社科基金资助 | `/topic/report/reportSocial` | `{"keyword":"关键词"}` | 社科基金指南内容 |
| 自科基金资助 | `/topic/report/reportNatural` | `{"keyword":"关键词"}` | 自科基金标题内容 |
| 期刊重点选题 | `/topic/report/reportPeriodical` | `{"keyword":"关键词"}` | 期刊重点选题数据 |

---

## 三、GET 接口

### pool 系列（司徒启思）

> pool 系列使用 GET 方法，参数通过 URL query string 传递。

| 接口 | 路径 | Query 参数 | 用途 |
|------|------|-----------|------|
| 选题指导 | `/topic/pool/listTopics` | `?page=1&size=10` | 选题指导列表 |
| 自然基金指南 | `/topic/pool/listNaturals` | `?page=1&size=10` | 自科基金指南 |
| 期刊选题指南分类 | `/topic/pool/listSubjectTypes` | 无 | 学科分类列表 |
| 期刊选题指南查询 | `/topic/pool/listPapers` | `?page=1&size=10&classCode=ALL` | 按学科查期刊选题 |
| 社科基金指南分类 | `/topic/pool/listSocialCategorys` | 无 | 社科基金分类 |
| 社科基金指南查询 | `/topic/pool/listSocials` | `?socialId=123` | 按分类查社科基金 |

**classCode**：ALL(全部) / A(哲学政法) / B(社科) / C(文化教育) / F(经济财政) / T(工业技术) 等

---

## 四、返回数据结构映射

### read/paper

**外层**：`{ Code, Msg, pageInfo: { totalCount, pageCount, currentPage, pageSize, pageDatas[] } }`

| type 参数 | 数据路径 | 说明 |
|---------|---------|------|
| HIGH / NEW / REVIEW | `pageInfo.pageDatas[].periodical` | 期刊论文对象 |
| DEGREE | `pageInfo.pageDatas[].thesis` | 学位论文（注意字段名是 thesis） |

**periodical 字段**：title, keywords[], abstracts, publishYear, creators[], unitNames[], citedCount, downloadCount, periodicalTitle, issue, corePeriodical[], doi

**thesis 字段**：title, keywords[], abstracts, publishYear, creators[], unitNames[], degree, citedCount

### read/scholar

**外层**：同 read/paper

**数据路径**：`pageInfo.pageDatas[].scholar`

**scholar 字段**：scholarName, scholarId, unitNames[], publishCount, citedCount, hIndex, keywords[]

### assess/NoveltyData

**外层**：`{ Code, Msg, innovation: { ... } }`

**innovation 字段**：years[], titleCount, keywordCount, abstractCount, titleTrends[], keywordTrends[], abstractTrends[]

> titleCount/keywordCount/abstractCount 为 "0" 表示新颖性极高。注意这里是 `innovation`，report/reportNovelty 用的是 `reportInnovation`。

### assess/TopicExtendData

**外层**：`{ Code, Msg, keyword: { nodes[] } }`

**keyword.nodes 字段**：show(显示名), keywords(关联词), count(文献数)

### assess/SubjectOsmosisData

**外层**：`{ Code, Msg, subject: { nodes[] } }`

**subject.nodes 字段**：educationCode, name, count, ratio(百分比)

### assess/*Paper 系列

返回结构与 read/paper 相同：`pageInfo.pageDatas[].periodical`

### find/acadamicData

**外层**：`{ Code, Msg, knowledge: { nodes[] } }`

**knowledge.nodes 字段**：cluster(聚类标识，用于调 Paper 接口), 其他主题字段

> Code="success" 但 data 为空或 code=2 → 该关键词无知识脉络数据（正常返回，非故障）

### find/frontierData

**外层**：`{ Code, Msg, frontier: { nodes[] } }`

**frontier.nodes 字段**：cluster, name(方向名), count(文献数)

### find/acrossData

**外层**：`{ Code, Msg, across: { nodes[] } }`

**across.nodes 字段**：cluster, name(跨学科名), count(文献数)

### find/newthemeData

**外层**：`{ Code, Msg, newTheme: { nodes[] } }`

**newTheme.nodes 字段**：cluster, theme(主题名), count, status(是否突发), yearRange[], burstSum, publishYear, yearArea

### find/*Paper 系列

返回结构与 read/paper 相同：`pageInfo.pageDatas[].periodical`

### find/hotspot

**外层**：`{ Code, Msg, hotSpotSubject: { ... } }`

**hotSpotSubject 字段**：code(学科码), keywords[](热点词), trends[](趋势数组, 含 quantity[]), index[](总指数)

### title/recommend

**外层**：`{ Code, Msg, template: { nodes[] } }`

> ⚠️ 数据在 `template.nodes[]` 中，不是 pageInfo.pageDatas[]

**template.nodes 字段**：templateTitle(推荐标题), templateKeyword(关联关键词)

### title/synonyms

**外层**：`{ Code, Msg, pageInfo: { totalCount, ..., pageDatas[] } }`

> totalCount 为 "0" 表示该关键词无关联主题词

### report/reportNovelty

**外层**：`{ Code, Msg, reportInnovation: { ... } }`

> ⚠️ 注意是 `reportInnovation`，不是 `innovation`（assess/NoveltyData 用的是 innovation）

**reportInnovation 字段**：years[], themeDecadeCount(近十年数), themeSumCount(累计数), themeTrends[](逐年量)

### report/reportSocial

**外层**：`{ Code, Msg, reportSocialGuideInfo: { texts[] } }`

> texts 为空数组 `[]` 表示无社科基金数据（正常返回）

### report/reportNatural

**外层**：`{ Code, Msg, reportNaturalGuide: { titles[] } }`

> titles 为空数组 `[]` 表示无自科基金数据（正常返回）

### report/reportPeriodical

**外层**：`{ Code, Msg, reportPeriodicalGuide: { nodes[] } }`

> nodes 为空数组 `[]` 表示无期刊重点选题数据（正常返回）

### pool/listTopics

**外层**：`{ Code, Msg, pageInfo: { ..., pageDatas[] } }`

**数据路径**：`pageInfo.pageDatas[].topicGuide`

**topicGuide 字段**：id, title, type, publishYear, resourceType

### pool/listNaturals

**外层**：同上分页结构

**数据路径**：`pageInfo.pageDatas[].naturalGuide`

**naturalGuide 字段**：id, title, createTime

### pool/listSubjectTypes

**外层**：`{ Code, Msg, subjectTypeInfo: { subjectTypes[] } }`

> ⚠️ 数据路径是 `subjectTypeInfo.subjectTypes[]`，不是 `subjectInfo`，也不是 pageInfo.pageDatas[]

**subjectTypes 字段**：recordId, discipline(学科名), periodicalYear, classCode(分类码)

### pool/listPapers

**外层**：同分页结构

**数据路径**：`pageInfo.pageDatas[].periodicalGuide`

**periodicalGuide 字段**：id, title(期刊名), classCode, corePeriodical, impactFactor, focus[](重点选题方向数组)

### pool/listSocialCategorys

**外层**：`{ Code, Msg, socialCategoryInfo: { socialYear, socialCategory[] } }`

> ⚠️ 数据路径是 `socialCategoryInfo.socialCategory[]`，不是 pageInfo.pageDatas[]

### pool/listSocials

**外层**：同分页结构

**数据路径**：`pageInfo.pageDatas[].socialGuide`

---

## 五、参数名差异速记

| 参数名 | 出现在哪些接口 | 含义 |
|--------|--------------|------|
| `keyword` | read/*, title/*, report/* | 检索关键词 |
| `title` + `keyword` + `abstract` | assess/* | 选题三要素（不是单个 param） |
| `search` + `param` | find/*Data | search=KEYWORD/CODE，param=关键词或学科号 |
| `param` (cluster) | find/*Paper | 上一步 Data 接口返回的 cluster 值 |
| `paper` | find/*Paper | 论文类型：HIGH/NEW/DEGREE/REVIEW |
| `type` | read/paper | 论文类型：HIGH/NEW/DEGREE/REVIEW |
| `sort` | read/scholar | 排序：RELATIVITY/HINDEX/ARTICLE/CITED |
| `classCode` | pool/listPapers | 学科分类码 |
| `socialId` | pool/listSocials | 社科基金分类 ID |

---

## 六、调用前自检清单

1. **对照本文件参数表**：确认请求体参数名与本文件一致
2. **禁止通用 param**：不得用 `param` 作为所有接口的通用参数名
3. **复制优先**：直接复制本文件的 JSON 模板，而非手动构造
4. **枚举值校验**：type/sort/paper/search 必须使用本文件列出的合法值

### 常见错误模式

| 错误 | 正确 |
|------|------|
| read/paper 用 `{"param":"关键词"}` | `{"keyword":"关键词","type":"HIGH"}` |
| assess 用 `{"param":"关键词"}` | `{"title":"标题","keyword":"关键词","abstract":"摘要"}` |
| find Data 用 `{"param":"关键词"}` | `{"search":"KEYWORD","param":"关键词"}` |
| title 用 `{"param":"关键词"}` | `{"keyword":"关键词"}` |
| report 用 `{"param":"关键词"}` | `{"keyword":"关键词"}` |
| find Paper 用 `{"param":"关键词"}` | `{"paper":"HIGH","param":"cluster值"}` |

---

## 七、返回数据相关性检查

> 万方 API 在参数名错误时返回 HTTP 200 + 不相关数据（静默容错），不会报错。必须在解析阶段主动检查。

### 文本类（read/paper, read/scholar, title/recommend）

查看前 3-5 条数据的标题/关键词是否包含查询关键词或同义词。0 条相关 → 极可能参数名错误。

### 统计类（assess/NoveltyData, TopicExtendData, SubjectOsmosisData）

检查 titleCount/keywordCount/abstractCount 是否全为 0（全 0 可能参数未传递）。检查 nodes[] 是否为空。

### 图谱类（find/acadamicData, frontierData, acrossData, newthemeData）

Code=2 → 该关键词无知识脉络数据（正常）。nodes 为空 + Code=success → 可能关键词无对应聚类或参数错误。

### 报告类（report/*）

检查 guide 对象是否为空。空对象表示该报告类型暂无数据。

### 列表类（pool/*）

空列表通常是数据未录入（正常），不是参数错误。
