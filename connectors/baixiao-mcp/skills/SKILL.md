---
name: baixiao-mcp-skill
description: 百晓智能 —— 学术检索技能： 中文人文社科文献与政策检索、参考文献核实、引用追溯、投稿期刊与审稿人推荐
version: "1.0.0"
author: "百晓智能"
---

# 百晓智能

本 Skill 指导 AI 使用百晓智能的学术检索能力，服务于**中文人文社科**（公共管理、政治学、社会学、经济学、法学、教育学等）的文献调研、写作与投稿。

## 能做什么 / 不能做什么

**能做**：检索中文人文社科期刊论文、政策文件、基金申报与立项记录；检索国际英文文献；核实参考文献真伪；追溯引用关系；推荐投稿期刊与审稿人；检索用户自己在百晓的知识库。

**不能做**：不生成综述或论文正文（本服务只返回结构化检索结果，写作由你自己完成）；不提供文献全文正文；不做数据统计分析；不检索理工医科为主的中文文献。

## 工具路由：先选对工具，再调用

| 用户想做什么 | 用这个工具 |
|---|---|
| 找中文人文社科论文 | `baixiao_corpus_search` |
| 找英文/国际文献 | `baixiao_external_search` |
| 按标题/作者/期刊/年份等**具体字段**精确查 | `baixiao_advanced_search` |
| 查政府政策文件 | `baixiao_policy_search` |
| 查基金**申报机会**（还能投的） | `baixiao_grants_cfp_search` |
| 查基金**立项/中标记录**（谁拿到过） | `baixiao_grants_award_search` |
| 查香港科研基金 | `baixiao_hk_grants_search` |
| 查新思想相关理论文献 | `baixiao_xi_thought_search` |
| 核实**一条**参考文献真伪 | `baixiao_verify_reference` |
| 核实**整份参考文献表** | `baixiao_verify_references` |
| 把残缺引文补全成规范元数据（单条） | `baixiao_fetch_metadata` |
| 批量补全多条残缺引文 | `baixiao_fetch_metadata_batch` |
| 顺着一篇文献找上下游引用 | `baixiao_citation_graph` |
| 这篇稿子投哪个期刊 | `baixiao_journal_fit` |
| 找审稿人 | `baixiao_find_reviewers` |
| 搜用户自己的知识库 | `baixiao_my_kb_search` |
| 用户有哪些知识库 | `baixiao_list_my_kbs` |

> ⚠️ **最常见的错误**：中文文献去调 `baixiao_external_search`。中文人文社科一律先用 `baixiao_corpus_search`；只有用户明确要英文/国际文献时才用 `baixiao_external_search`。

## 工具说明

### baixiao_corpus_search — 中文人文社科文献检索
百晓自建的中文人文社科语料库检索，是本服务的核心能力。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| query | string | ✅ | 检索式，用中文自然语言或关键词 |
| collection_ids | string[] | - | 限定检索的子库，不填即全库 |
| page_size | integer | - | 返回条数，默认适中，最多按服务端上限 |

### baixiao_external_search — 国际英文文献检索
跨多个开放学术数据源检索英文文献。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| query | string | ✅ | **英文**检索词 |
| limit | integer | - | 返回条数 |
| from_year / to_year | integer | - | 年份区间 |

### baixiao_advanced_search — 字段精确检索
已知标题/作者/期刊等具体信息时用，比关键词检索更准。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| title / author / journal / publisher | string | - | 字段值，至少给一个 |
| year / year_from / year_to | integer | - | 年份或区间 |
| doc_type / language | string | - | 文献类型 / 语种 |
| limit | integer | - | 返回条数 |

### baixiao_verify_reference — 单条参考文献核实
核对一条引文是否真实存在，用于抓**编造/张冠李戴**的参考文献。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| title | string | ✅ | 文献标题 |
| year / journal / doi / authors / language | - | - | 已知的都填上，命中率更高 |
| is_book | boolean | - | 是否为专著 |

### baixiao_verify_references — 整份参考文献表批量核实
审稿、查重、核对书稿参考文献表时用这个，一次跑完整份。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| references | array | ✅ | 参考文献数组 |
| max_concurrency | integer | - | 并发度 |

### baixiao_fetch_metadata / baixiao_fetch_metadata_batch — 引文补全
把残缺、格式混乱的引文整理成规范元数据。`query`（单条）/ `queries`（批量）为必填。

### baixiao_citation_graph — 引用关系追溯
顺着一篇文献往上（被引）或往下（引用）扩展，做文献综述滚雪球。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| paper_id | string | ✅ | 文献标识 |
| direction | string | - | 追溯方向 |
| limit | integer | - | 返回条数 |

### baixiao_journal_fit — 投稿期刊推荐
| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| keywords | string[] | ✅ | 稿件主题关键词，建议 3~6 个 |
| language | string | - | 目标语种 |
| top / rounds | integer | - | 返回数量 / 检索轮次 |

### baixiao_find_reviewers — 审稿人推荐
参数同上，另有 `exclude_authors` 用于排除作者本人及利益相关者。

### baixiao_policy_search — 政策文件检索
中央与地方政府政策文件。支持 `query` / `author` / `issuer`（发文机关）/ `year` / `year_from` / `year_to` / `doc_type` / `limit`。

### baixiao_grants_cfp_search — 基金申报机会
| 参数 | 说明 |
|---|---|
| query / region / funder / status | 主题 / 地区 / 资助机构 / 状态 |
| deadline_from / deadline_to | 截止日期区间 |
| amount_min | 最低资助额 |

### baixiao_grants_award_search — 基金立项/中标记录
支持按 `person` / `institution` / `region` / `funder` / `program` / `discipline` / `outcome_grade` / 年份区间检索。适合查"某人/某单位拿过哪些项目"。

### baixiao_hk_grants_search — 香港科研基金
香港研究资助局（RGC）资助项目检索。

### baixiao_xi_thought_search — 新思想文献
重要理论文献专库检索。

### baixiao_get_pdf — 获取公开文献的 PDF 下载链接

对**百晓语料库中已公开**的文献，返回一个有时效的签名下载链接。

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| identifier | string | ✅ | 文献标识，取自检索结果条目里的 `external_id` |

- **必须先检索、再取链接**：`identifier` 只能来自 `baixiao_corpus_search` 等检索工具返回的条目，不要自行拼造。
- 仅对**公开语料**有效。非公开文献会返回 `{"available": false, "reason": "..."}`，
  这是正常业务响应，**如实告诉用户该文献暂无公开下载**，不要重试，也不要改用其他工具去"绕"。
- 对非百晓语料的检索结果（如国际数据源返回的条目），请直接使用条目自带的 `url` 或 DOI，不要调用本工具。
- 该工具**不消耗通晓币**，但会占用用户的下载流量额度。

### baixiao_my_kb_search / baixiao_list_my_kbs — 用户自己的知识库
检索用户在百晓智能上自建或所属团队的知识库。**只能访问该 API 密钥所属账号有权限的知识库**，无法访问他人数据。`baixiao_list_my_kbs` 无参数，先列出知识库再用 `baixiao_my_kb_search` 检索。

## 凭证

- 用户需在 <https://chat.know-pa.cn/settings/mcp> 登录后生成 API 密钥（`bxk_` 开头），填入 WorkBuddy 的连接表单。
- 密钥仅存放在用户本机 `~/.workbuddy` 目录下。
- ⚠️ **鉴权失败不会返回 HTTP 错误码**：HTTP 状态仍是 200，错误在**工具返回内容里**，形如
  `{"error": "unauthorized", "message": "missing API key ...", "items": []}`。
  看到 `error: "unauthorized"` 时**不要**把它当成"没有检索结果"，而要按下面处理：
  - `missing API key` → 用户还没填密钥，引导他到 <https://chat.know-pa.cn/settings/mcp> 生成后填入 WorkBuddy 连接表单。
  - `unknown or revoked API key` → 密钥失效或已撤销，引导用户重新生成并更新连接设置。
- 返回**额度不足**的错误 → 提示用户到账号页面查看余额，**不要反复重试同一请求**。
- 凡是返回体里带 `error` 字段的，一律**如实转述给用户**，不要静默忽略后继续编造结果。

## 计费与调用纪律

- 按次计费，**调用失败不计费**。
- 不同工具单价不同，其中**批量类**（`baixiao_verify_references`、`baixiao_fetch_metadata_batch`）和**聚合类**（`baixiao_journal_fit`、`baixiao_find_reviewers`）开销较高。
- **同一个问题不要反复重复调用**。先用一次检索拿到结果，再基于结果推进；确需换角度时应改写检索式，而不是原样重试。
- 批量核实整份参考文献表时，用 `baixiao_verify_references` 一次提交，**不要**对每条分别调用单条接口。

## 结果呈现

- 检索结果里的题录信息（标题、作者、期刊、年份）**原样引用，不要改写或"润色"**，否则会破坏引文准确性。
- 核实类工具返回"未命中"时，如实告诉用户"未能核实到该文献"，**不要**据此断言文献一定不存在，也不要替用户编造一条看起来合理的引文。
- 返回条目较多时，先给用户一个精炼列表，再按用户要求展开。
