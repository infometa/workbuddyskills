# 万方选题API测试报告

## 测试时间
2026-07-01

## 测试密钥
- （主用）
- （备用，已验证可用）

## 关键配置发现

| 项目 | 正确配置 | 错误配置 |
|------|---------|---------|
| Base URL | `https://api.wfdata.com` | - |
| 路径格式 | **斜杠格式**: `/topic/find/hotspot` | `_find/hotspot`（下划线格式返回403） |
| HTTP方法 | find/assess/report/title/read → POST<br>pool模块 → GET | - |
| Content-Type | `application/json` | - |
| AppSecret | **不需要** | - |

## 测试结果汇总

### ✅ 全部通过 (26/26)

#### 夏侯拟言 — title模块 (POST)
| 接口 | 路径 | 状态 |
|------|------|------|
| 标题推荐 | `/topic/title/recommend` | ✅ |
| 关键词关联主题 | `/topic/title/synonyms` | ✅ |

#### 欧阳搜文 — read模块 (POST)
| 接口 | 路径 | 状态 |
|------|------|------|
| 文献查询 | `/topic/read/paper` | ✅ |
| 学者查询 | `/topic/read/scholar` | ✅ |

#### 上官选道 — find模块 (POST)
| 接口 | 路径 | 状态 | 备注 |
|------|------|------|------|
| 学科列表 | `/topic/find/eduCodeList` | ✅ | |
| 学科热点 | `/topic/find/hotspot` | ✅ | |
| 回溯学术脉络 | `/topic/find/acadamicData` | ✅ | |
| 学术脉络论文 | `/topic/find/acadamicPaper` | ✅ | param=acadamicData返回的cluster |
| 追踪研究重点 | `/topic/find/frontierData` | ✅ | |
| 研究重点论文 | `/topic/find/frontierPaper` | ✅ | param=frontierData返回的cluster |
| 拓展研究边界 | `/topic/find/acrossData` | ✅ | |
| 边界拓展论文 | `/topic/find/acrossPaper` | ✅ | param=acrossData返回的cluster |
| 发掘新兴主题 | `/topic/find/newthemeData` | ✅ | |
| 新兴主题论文 | `/topic/find/newthemePaper` | ✅ | param=newthemeData返回的cluster |

> ⚠️ **Paper 接口调用须知**：4个 Paper 接口（acadamicPaper / frontierPaper / acrossPaper / newthemePaper）的 `param` 参数**必须填对应 Data 接口返回的 `cluster` 值**，不能直接填关键词。正确流程：Data → 提取 `cluster` → Paper。各接口 cluster 字段路径：
> - `acadamicData` 响应 → `knowledge.nodes[].cluster`
> - `frontierData` 响应 → `frontier.nodes[].cluster`
> - `acrossData`   响应 → `across.nodes[].cluster`
> - `newthemeData` 响应 → `newTheme.nodes[].cluster`

#### 皇甫评度 — assess模块 (POST)
| 接口 | 路径 | 状态 |
|------|------|------|
| 新颖性评测 | `/topic/assess/NoveltyData` | ✅ |
| 新颖性评测论文 | `/topic/assess/NoveltyPaper` | ✅ |
| 选题拓展 | `/topic/assess/TopicExtendData` | ✅ |
| 选题拓展论文 | `/topic/assess/TopicExtendPaper` | ✅ |
| 学科渗透 | `/topic/assess/SubjectOsmosisData` | ✅ |
| 学科渗透论文 | `/topic/assess/SubjectOsmosisPaper` | ✅ |

#### 司徒启思 — pool模块 (GET)
| 接口 | 路径 | 状态 |
|------|------|------|
| 期刊选题指南 | `/topic/pool/listPapers` | ✅ |
| 自科基金指南 | `/topic/pool/listNaturals` | ✅ |
| 社科基金分类 | `/topic/pool/listSocialCategorys` | ✅ |
| 选题指导列表 | `/topic/pool/listTopics` | ✅ |
| 学科分类 | `/topic/pool/listSubjectTypes` | ✅ |
| 社科基金内容 | `/topic/pool/listSocials` | ✅ |

#### 太史撰域 — report模块 (POST)
| 接口 | 路径 | 状态 |
|------|------|------|
| 研究趋势 | `/topic/report/reportNovelty` | ✅ |
| 社科基金 | `/topic/report/reportSocial` | ✅ |
| 自科基金 | `/topic/report/reportNatural` | ✅ |
| 期刊选题 | `/topic/report/reportPeriodical` | ✅ |

## 文件更新情况

所有6个团员agent文件已更新：
- Key: `30084_*（已作废）` → ``
- 路径: 下划线格式 → 斜杠格式
