---
name: yunzhi-qa
description: |
  Tencent Yunzhi (Lexiang) knowledge base Q&A capability. Wraps the lexiang MCP `search_kb_embedding_search` tool with query rewriting, parallel retrieval, dedup, citation-grounded answer generation. Supports a gated competitive-analysis mode (the only web-search exception) and an orthogonal international/overseas retrieval switch (UDF filtering, no web). When the knowledge base has no relevant hits, explicitly refuses to answer (no web search fallback). Activates whenever the user asks a question that should be answered from the bound Lexiang knowledge base.
  触发词：云知问答、乐享检索、知识库问答、kb_embedding_search、search_kb_embedding_search、查知识库、问知识库、检索增强、RAG、citation、竞品对比、竞对、友商、海外、国际版、出海、多语言、overseas、international
---

# 腾讯云知识问答专家能力（Tencent Yunzhi Knowledge Q&A Expert）

## 功能说明

封装腾讯云知（乐享）MCP 的 **语义向量搜索** 能力（`search_kb_embedding_search`），并叠加：

- **MCP 权限判断（前置门禁 · 个人 Token 绑定）**：动手检索前先调用 `whoami` 校验用户是否已绑定乐享 MCP 个人 Token；未绑定 / 401 时按规范话术引导用户去 `https://lexiangla.com/mcp?company_from=CSIG` 获取 `LEXIANG_TOKEN`（默认 `COMPANY_FROM=CSIG`），验证连接后再继续。
- **查询改写与泛化**：缩写补全、子问题拆解、意图补全、同义词扩展、时间语义转换。
- **并行召回与去重**：多 Query 并发检索 → 按 `target_id` 去重 → 相关性过滤。
- **引用式答案生成**：基于检索片段产出带学术风数字角标 `[1][2]` 的结构化 Markdown 回答（禁用 WorkBuddy 不渲染的 `[citation:X]`），「参考资料」用可点 Markdown 链接列出文档标题与原文链接。
- **拒答策略**：知识库无相关结果时直接拒答（明确告知"未在乐享知识库检索到相关内容"），**默认禁止使用联网搜索兜底**，**禁止基于通用知识凭空作答**。
- **竞品对比模式（意图门控 · 唯一联网例外）**：仅当问题**同时命中「对比动作 + 外部友商实体」**时切 `mode=competitive`，走「站内乐享 + 站外竞品官网」双通道；其余意图严格纯站内。规则见 `@references/competitive-analysis.md`。
- **国际化 / 海外定向检索（正交叠加开关 · 不联网）**：当问题命中「海外 / 国际版 / 出海 / 多语言 / 语言支持 / 翻译 / 本地化 / 多地区 / overseas / international / global」等场景时置 `intl=on`，本轮所有 `search_kb_embedding_search` **注入「国际版=是」的 UDF 过滤**（`field_id=250b20760fb74e8bb32955fe83c919cc`、`value=lsihfg3ix6d`）定向召回国际版知识，并**强制二次筛选**剔除混入的国内版内容。该开关与 `mode` 正交、仍属纯站内链路（不触发联网）。规则见 `@references/overseas-search.md`。

## 调用方式

主要调用全限定名工具（建议直接调用，避免 `tool_search` 长参数碎片化）：

| 优先级 | 工具 | 用途 |
|--------|------|------|
| **前置门禁** | `mcp__lexiang__whoami` | **第一步必跑**：校验个人 Token 是否已绑定 / 是否过期，成功后获取 `company.company_domain`（用于拼原文链接）。未通过前不进入检索。 |
| **P0（默认首选）** | `mcp__lexiang__search_kb_embedding_search` | **语义向量检索（每次问答的默认且唯一首选检索工具）**。参数最简即可：`{"filters": {"keyword": "<query>"}, "limit": 10}`。✅ 实测（2026-07-16）**正文片段 `chunks[].content` 与 `target_type/target_id/score` 默认就返回**，无需追加字段。⚠️ **不要**传 `_mcp_fields:["@default","chunks.content"]`——该参数只认负向排除，正向选择会被忽略（见下）。 |
| **P1（仅作兜底）** | `mcp__lexiang__search_kb_search` | 关键词检索。**仅在 embedding_search 对所有 Query 都返回空 / 全部低相关时**作为兜底使用，不在常规流程中并行调用。参数：`{"keyword": "<query>", "limit": 10, "highlight": true}`。`docs.title`、`docs.content` 默认返回，无需追加。 |
| **P2（按需精读）** | `mcp__lexiang__entry_describe_ai_parse_content` | 精读 Phase 3 高分召回的正文（可选，召回片段不足时启用）；**仅对 `target_type=kb_entry` 调用，disknode 会 403**。 |
| **P2（按需精读）** | `mcp__lexiang__entry_describe_entry` | 拿条目元信息（标题 `entry.name` / `entry_type` / `extension`），用于答案佐证。⚠️ 工具名是 `entry_describe_entry`，**不是** `entry_describe`。 |
| **竞品破例联网** | `WebSearch` / `WebFetch` | **仅 `mode=competitive`** 时用于站外竞品官网检索；`mode=standard` 严禁调用。白/黑名单与过滤规则见 `@references/competitive-analysis.md`。 |

### `_mcp_fields` 使用规范（实测校准 · 2026-07-16）

1. ✅ **正文默认返回**：`search_kb_embedding_search` 的 `chunks[].content`、`search_kb_search` 的 `docs.content` / `docs.title` **默认就返回**，Phase 3 有内容可引用，**不需要为拿正文而传 `_mcp_fields`**。
2. ⚠️ **`_mcp_fields` 只认负向排除**：该参数的真实语义是「排除不需要的字段以省 token」，只接受负向路径（如 `["-staffs"]`）；**正向选择和 `@default` 会被工具忽略**。
3. ❌ **不要**写 `["@default","chunks.content"]` / `["@default","docs.content"]`——这是正向选择，会被忽略，等于没传，且误导后续维护。
4. 仅当返回体过大、想主动裁掉某些字段省 token 时，才用负向路径，例如 `["-staffs","-entry.html_content"]`。
5. 想看某工具完整 Output Fields，可调 `mcp__lexiang__get_tool_schema`（正文既然默认返回，通常无需查）。

### 工具调用优先级规则（强约束）

1. **第一步永远是** `whoami`，没通过不进入检索。
2. **常规检索阶段只跑** `search_kb_embedding_search`，对 Phase 2 产出的多条 Query **批量并行调用一次**，去重排序后判断结果。
3. **是否启用 `search_kb_search` 兜底，按以下条件判断（满足任一即启用）**：
   - `search_kb_embedding_search` 对**所有 Query** 都返回 `chunks=[]`（彻底无召回）；
   - 或召回总数虽 > 0，但**全部相关性极低** / 与问题主题明显无关（典型表现：全是同名混淆词、无任何关键 entity 命中）；
   - 或用户问题包含**精确的产品名 / 错误码 / API 名 / 文件名**这类适合 BM25 的强字面信号，且 embedding 召回里**没有**这类精确命中。
4. **不要默认并行跑两路检索**，避免重复消耗 token / 上下文。
5. 兜底后仍无结果 → 进入 Phase 4 的「拒答策略」（**`mode=standard` 下禁止启用联网搜索**）。

## 竞品对比子流程（意图门控 · 双通道）

**默认所有问答走纯站内链路（`mode=standard`）。** 只有 Phase 2 判定为竞品对比才破例联网。

### 意图判定（Phase 2 前置闸门）

`mode=competitive` **必须同时满足**：① 含**对比动作**（对比/比较/vs/相比/差异/区别/优劣/对标/横评）；② 含**外部友商实体**（阿里云/华为云/火山引擎/百度智能云/AWS/Azure，或 OSS/OBS/S3/ECS/RDS/通义/盘古 等友商产品）。任一不满足 → `mode=standard`；**判定不确定也按 `standard`**。

- 只有友商名无对比动作（「介绍下阿里云 OSS」）→ `standard`，纯站内，无果拒答。
- 只有对比动作无外部友商（「CVM 和 CDB 的区别」）→ `standard`，纯站内。

### 两条互斥链路

| mode | 检索 | 联网 | 拒答规则 |
|------|------|------|----------|
| `standard`（默认） | 仅通道 A 站内乐享（P0 embedding → P1 keyword 兜底 → P2 精读） | ❌ 严禁 | 无召回即拒答 |
| `competitive` | 通道 A 站内基线 + 通道 B 站外竞品官网（`WebSearch`/`WebFetch`） | ✅ 仅此例外 | 缺失项写「官方未披露」，其余照常输出 |

### competitive 链路要点（完整规则见 `@references/competitive-analysis.md`）

1. **逐厂商独立检索**，每厂商 ≥ 2 轮（功能/规格 + 定价/计费），第二引擎交叉验证。
2. **`site:` + `allowed_domains` 双重过滤**，只认白名单官网；CSDN/知乎/新闻媒体/代理商页一律丢弃。
3. **来源分级 P0/P1/P2** + **通道标签（站内/站外）**，答案里分区标注。
4. **实体防污染**：COS↔OSS↔OBS↔S3 先映射再比，绝不交叉归属。
5. **品类维度装配**：按产品品类查 `competitive-analysis.md` 词典取专属对比维度。

## 国际化 / 海外定向检索子流程（正交叠加 · 纯站内）

**与竞品门控相互独立**，判定命中即在站内链路上叠加 UDF 过滤，**不联网**。

### 意图判定（Phase 2 前置闸门）

`intl=on` 触发条件：问题涉及**海外 / 国际版 / 国际站 / 出海 / 海外市场 / 多地区 / 多语言 / 语言支持 / 翻译 / 本地化 / overseas / international / global**，或明确点名海外地区/站点（如「新加坡节点」「海外金融行业案例」）。命中即置 `intl=on`；未命中 / 不确定 → `intl=off`。

### 命中后的处理（叠加进 Phase 3 通道 A）

1. **注入 UDF 过滤**：本轮每条 Query 的 `search_kb_embedding_search` 都追加 `filters.udf_values`，固定 `field_id=250b20760fb74e8bb32955fe83c919cc`、`value=lsihfg3ix6d`（「是」值代码，**不能用中文「是」**）、`match_logic_type=and`。
2. **强制二次筛选（必须）**：乐享 UDF 是**软过滤（加权召回非硬排除）**，返回仍混国内版内容 —— 需再按标题/正文含「国际版/海外/出海/international/overseas/global」等特征筛一遍，仅保留国际版条目。
3. 二次筛选后有效条目为 0 → 按 `mode=standard` 拒答（告知「未检索到国际版/海外相关内容」，不联网兜底）。
4. 兜底、去重、链接、引用规则与常规站内一致。

> 完整参数模板、field_id 速查、字段重新枚举方式见 `@references/overseas-search.md`。

## 参考资料

- 查询改写完整规则：`@references/query-rewriting.md`
- 答案生成与引用规则：`@references/answer-generation.md`
- **竞品对比模式规则集（意图门控双通道 · 品类词典 · 白黑名单）**：`@references/competitive-analysis.md`
- **国际化 / 海外定向检索规则（国际版 UDF 过滤 · 软过滤二次筛选 · field_id 速查）**：`@references/overseas-search.md`
- 整体 Agent 流水线说明：`@references/agent-architecture.md`

## 输出格式

Markdown 结构，必须包含：

1. **简明结论**：1~3 句直击问题核心，关键处带学术风数字角标 `[1]`（禁用 `[citation:X]`，WorkBuddy 不渲染）。
2. **详细说明**：按需段落 / 列表 / 表格，**对比题用表格**，**步骤题用有序列表**；关键论点内联 `[X]`。
3. **参考资料**：每条用可点 Markdown 链接 `[文档标题](原文链接)`（编号与正文 `[X]` 对应，必要时附 1~2 行片段），不要写裸链纯文本。
4. **信息来源说明**：标注命中文档数；`standard` 明确"仅基于乐享知识库（不使用联网搜索）"；`competitive` 站内/站外来源分区标注。

## 注意事项

1. **MCP 权限判断永远是第一步**，未通过前禁止进入 Phase 2~4。未绑定 MCP / 401 时不得继续检索，按 `references/agent-architecture.md` 中的话术引导。**默认 `COMPANY_FROM=CSIG`**，未绑定时仅引导用户通过 `https://lexiangla.com/mcp?company_from=CSIG` 获取 `LEXIANG_TOKEN`，**无需让用户提供 COMPANY_FROM**，**也不要回显完整的 mcp.json 配置块**。
2. **改写阶段必须覆盖**：缩写补全 + 子问题拆解 + 同义词扩展（缺一不可）。
3. **链接生成（⚠️ 按 target_type 区分云知 1.0 / 2.0 两套规则）**：

   | `target_type` | 文档版本 | URL 模板 |
   |---|---|---|
   | `disknode` | **云知 1.0**（旧版团队文档/网盘节点） | `https://{domain}/docs/{target_id}` |
   | `kb_entry` | **云知 2.0**（乐享 AI 知识库条目，含 page/file/video/folder） | `https://{domain}/pages/{target_id}` |
   | `kb_smartsheet` | 云知 2.0 智能表 | `https://{domain}/pages/{target_id}` |
   | `attachment` | 附件 | 按需调附件下载接口，不直接出查看 URL |
   | `ai_external_doc` | **外部抓取的文档**（如 cloud.tencent.com 等公开来源） | 不属于云知体系，应使用原文档自带 URL 或不附链接 |

   - `{target_id}` 取 search 返回的 `chunks[].target_id`；`{domain}` 取自 `whoami` 返回的 `company.company_domain`，缺失默认 `https://csig.lexiangla.com`。
   - **绝对不要使用** `https://{domain}/teams/{team_id}/docs/{xxx}` 这种模板（实测 404）。
   - `entry_describe_entry` 返回的 `entry.target_id` 对 `kb_file` 是底层存储 file_id（≠ entry.id），**只用于附件下载等内部接口，不能拼查看页 URL**。
   - 兜底原则：若 target_type 未在上表中且需要给链接，优先尝试 `/pages/{target_id}`（云知 2.0 会自动重定向）。
4. **批量检索合并执行**：多 Query 在一次脚本中完成，避免逐条审批。
5. **港澳台 / 政治敏感问题** 直接拒答，不进入检索流程。
6. **不得回显完整 Token**。
7. **拒答优先于联网兜底（默认）**：`mode=standard` 下知识库召回为空 / 全部低相关时，直接拒答，**禁止调用 WebSearch / WebFetch 等联网工具**。**唯一例外**：Phase 2 判定 `mode=competitive` 的竞品对比链路可走站外通道 B，须严格遵守 `@references/competitive-analysis.md` 的白/黑名单与过滤规则。
