---
name: patsnap-search
description: 搜索全球专利和期刊文献，读取专利、文献与专利生命周期信息，并进行申请人标准化和集团层级确认。用于技术调研、专利检索、文献核实和专利布局分析。
---

# 智慧芽专利&文献融合检索

通过已连接的 patsnap-search MCP Server 调用工具。用户通过 WorkBuddy 的 OAuth 授权流程连接服务；不要要求用户在对话或工具参数中提交凭证。

## 工具选择

| 工具 | 用途与关键参数 |
| --- | --- |
| search_patent | 全球专利检索；支持 semantic、keyword、filter 或独占的 boolean 策略。 |
| search_literature | 期刊文献检索；支持 semantic、keyword、filter。 |
| fetch_patent | 按 patent_id（内部 ID 或公开号）读取专利基本信息和全文；include 仅用于 relations、media 等可选扩展。 |
| fetch_literature | 按 paper_id 读取文献标题、摘要、作者、机构和期刊等信息。 |
| fetch_patent_lifecycle | 按 patent_id 读取法律事件、年费、转让、许可、质押、诉讼、复审等信息。 |
| build_patent_boolean_query | 将用户完整自然语言意图原样放入 text，构造布尔检索式；不执行检索。 |
| describe_search_capability | 使用非 general 的专业 domain 前先调用；按返回的字段、操作符及 operand schema 构造 domain_filters。 |
| get_standard_assignee_name | 将未确认的公司或机构名称传给 query，获取候选 company_id、ans_id、标准名称和匹配依据。 |
| get_corptree_hierarchy | 仅使用已解析的 company_id 查询 ancestors、children、descendants 或 root_group；不执行专利检索。 |

工具参数和限制见 [工具参考](references/tools.md)。实际调用以服务器公布的当前工具 schema 为准，不构造 schema 中未定义的过滤字段。

## 检索流程

1. 保留用户完整技术概念和限定条件。专利和文献融合调研分别调用两种搜索工具，按各自来源汇总。
2. 专利技术主题通常选择 semantic + keyword：semantic_query 表达完整意图，keywords 保留完整技术概念短语。未指定语言时为专利核心概念提供含义一致的中英日词组。不要拆成可单独召回的泛词。
3. 文献研究问题用 semantic，具体方法、材料、缩写或术语用 keyword。文献关键词使用原子化术语，通常 3–8 个，不传完整句子。
4. 作者、机构、日期、申请人、受理局和法律状态等用户明确条件放入对应 filters；filters 必须是对象。策略和参数严格绑定，未选策略时不要传其参数。
5. Boolean 检索的 search_strategy 必须恰为 ["boolean"]。将 build_patent_boolean_query 返回的 data.boolean_query 原样传给 search_patent.boolean_query，不解析或改写引用；用户已提供可执行字段检索式时原样保留。不要混用 semantic_query、keywords、filters、domain_filters 或非 general 的 domain。
6. 公司身份不明确时先解析，依据匹配证据确认。company_id 与 ans_id 用途不同，不可互换、补造或改写。仅在用户要求集团或下属公司范围时扩展集团层级。
7. 专业领域过滤先调用 describe_search_capability，仅使用返回能力定义允许的字段、属性和操作符。
8. 搜索默认按相关性排序；用户要求最新或高被引时再选择相应排序。limit 范围 1–100，默认 10；offset 默认 0，offset + limit 不超过 1000。collapse_family 默认 false，需要每同族一条时设为 true，并说明统计口径。
9. 需要核实单项内容时使用 fetch_patent 或 fetch_literature。生命周期问题使用 fetch_patent_lifecycle。format 可选 json 或 markdown，语言偏好可为 en、zh-CN、zh-TW、ja。

## 调用示例

专利语义检索：

```json
{"search_strategy":["semantic"],"semantic_query":"用于固态电池的高离子电导率电解质材料","limit":10}
```

文献关键词检索：

```json
{"search_strategy":["keyword"],"keywords":["固态电解质","solid-state electrolyte"],"limit":10}
```

申请人解析：

```json
{"query":"宁德时代","limit":5}
```

## 输出与错误处理

- 根据实际结果保留专利公开号、文献标题、作者、日期和可用来源链接，区分原始证据与分析推断。
- 不编造全文、权利要求、标识符、法律状态或命中数量；同族数若为估算值应说明。
- 无结果时说明检索范围，并在用户原意内调整检索词。分页结果不是全库穷尽结果。
- 认证失效时引导用户在 WorkBuddy 重新连接并完成 OAuth 授权，不打印访问令牌。参数错误时核对工具 schema；限流或暂时性超时应提示并控制重试次数。

官方服务说明：https://open.zhihuiya.com/marketplace/mcp-servers/patsnap-search
