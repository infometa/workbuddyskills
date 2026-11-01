# 智慧芽专利&文献融合检索工具参考

来源：https://open.zhihuiya.com/marketplace/mcp-servers/patsnap-search

可用能力

9 个可调用工具

输入 · 输出

fetch_literature
读取文献基本信息，包括标题、摘要、作者、机构、期刊名等，适合获取文献摘要并进行核实。
输入
format, language, paper_id
参数
format
string

v3.1：返回结构化 JSON（默认）或拼装后的 Markdown；选择 markdown 时，响应仅包含 response.markdown。

language
string

可选的语言偏好，支持 en、zh-CN、zh-TW、ja。

paper_id
必填
string

-

fetch_patent
按内部专利 ID 或公开号读取单件专利基本信息，例如标题、摘要、申请人、分类号和当前法律状态。
输入
patent_id, include, format, language
参数
patent_id
必填
string

-

include
array

在默认全文信息之外可选返回的扩展部分，支持 relations 和 media。全文始终返回，不应写入 include；生命周期信息需使用独立工具获取。

format
string

v3.1：返回结构化 JSON（默认）或拼装后的 Markdown；选择 markdown 时，响应仅包含 response.markdown。

language
string

可选的语言偏好，支持 en、zh-CN、zh-TW、ja。

fetch_patent_lifecycle
读取法律事件、年费、转让、许可、质押、诉讼、复审等生命周期信息，适合法律状态监测、交易风险评估和组合维护。
输入
patent_id, format, language
参数
patent_id
必填
string

-

format
string

v3.1：返回结构化 JSON（默认）或拼装后的 Markdown；选择 markdown 时，响应仅包含 response.markdown。

language
string

可选的语言偏好，支持 en、zh-CN、zh-TW、ja。

build_patent_boolean_query
将完整的自然语言专利检索意图转换为可执行的 PatSnap Boolean 字段检索式。该工具只构造检索式，不检索专利；请将返回的 data.boolean_query 原样传给 search_patent，并设置 search_strategy=["boolean"]。data.reference_query 字段可用于查看检索式原文。
输入
text
参数
text
必填
string

用户完整的自然语言专利检索意图。必须原样传入；不得传入已经可执行的 PatSnap 字段检索式。

describe_search_capability
描述指定专业专利检索领域支持的过滤字段、返回字段、操作符及操作数结构。使用非 general 的 domain 前应先调用；该工具只返回能力元数据，不执行专利检索。
输入
domain, corpus
参数
domain
必填
string

需要描述其过滤字段、支持的操作符和返回字段的专业检索领域。支持值列在本 Schema 中，匹配时不区分大小写；不能描述 'general'。 可选值： - ls：当用户检索涉及药物、治疗靶点、疾病、专利类别、技术、化学结构或生物序列的生命科学专利时使用。实体过滤器接受公开名称。

corpus
string

Capability 接口支持的语料库。

get_corptree_hierarchy
按已确认的 company_id 找到其直属父节点或根节点；不检索专利。
输入
company_filter, company_id, offset, max_depth, limit, direction
参数
company_filter
string

公司节点过滤方式：all 保留关系范围内的全部公司；with_direct_assignees 只保留直接标准申请人映射非空的节点。所选顶层公司不会被该过滤器移除。

company_id
必填
string

先前公司解析返回的公司标识。必须原样使用返回的 company_id，不得补造或改写。

offset
integer

继续获取列表时跳过的已有结果数量，必须大于等于 0。

max_depth
integer

可选的后代层级深度，范围为 1–8。仅当 direction 为 descendants 时允许设置；省略表示包含全部后代。

limit
integer

单次返回的关联公司最大数量，范围为 1–100。

direction
string

关系查询方向：ancestors 查询所选公司的上级公司；children 查询直属子公司；descendants 查询全部下属公司；root_group 查询同一根集团中的其他全部公司。

get_standard_assignee_name
根据未确认专利申请人/权利人的公司或机构名称关键词，推荐company_id、ans_id、标准名称及匹配证据；不检索专利。
输入
query, limit
参数
query
必填
string

需要同时按公司和标准专利申请人解析的名称。可以是正式名称、简称、缩写、别名、曾用名、翻译名、拼写变体或不完整名称。应填写名称，而不是标识符或专利检索表达式；首尾空白会被去除。

limit
integer

公司候选和标准申请人候选各自返回的最大数量，分别独立应用于两侧结果，范围为 1–20。

search_literature
检索全球期刊文献库，支持语义、关键词和结构化过滤；可按作者、机构、发表日期和被引次数等条件筛选，并返回分页结果与元数据
输入
semantic_query, offset, keywords, search_strategy, limit, sort, filters
参数
semantic_query
string

用自然语言描述研究问题或概念。仅当 'semantic' ∈ search_strategy 时必填。 必须使用自然语言，而不是关键词列表，例如 ✅“治疗青光眼的药物技术方案”，❌“青光眼 治疗 药物”。 适用于概念或机理探索。方法名、缩写或研究主题术语使用 keywords；作者、机构、日期或被引次数约束使用 filters。

offset
integer

分页偏移量，表示跳过前多少条结果，默认值为 0。 约束：`offset + limit ≤ 1000`。

keywords
array

用于匹配标题、摘要和全文的 BM25 关键词列表，建议 3–8 个。仅当 'keyword' ∈ search_strategy 时必填。 每一项必须是一个原子化技术术语、方法、材料、缩写、数据集或研究概念。去除“技术”“方法”“研究”等宽泛词；可增加中英文或缩写与全称变体以提高召回率，例如 ['基因编辑','gene editing']。不得传入句子或逗号拼接的字符串，避免超过 15 个术语。

search_strategy
array

检索策略，可从 'semantic'、'keyword'、'filter' 中选择 1–3 个。根据请求类型选择： - 自然语言研究问题或机理 → ['semantic'] + semantic_query - 具体术语、方法、材料或数据集 → ['keyword'] + keywords - 纯作者、机构或日期范围 → ['filter'] + filters - 主题术语 + 结构化论文约束 → ['keyword','filter']，主题术语放入 keywords，约束放入 filters - 自然语言研究问题 + 结构化论文约束 → ['semantic','filter']，问题或概念放入 semantic_query，约束放入 filters。 严格绑定：选择某个策略时必须提供对应参数，未选择时禁止提供——semantic↔semantic_query、keyword↔keywords、filter↔filters（至少设置一个字段）。默认值为 ['keyword']。

limit
integer

单页返回结果数量，范围为 1–100，默认值为 10。 与 `offset` 配合进行分页；约束：`offset + limit ≤ 1000`。

sort
string

结果排序方式。'relevance'（默认）表示最佳匹配优先；其他值按对应属性排序，'-' 前缀表示降序。 字段：publication、cited_count。 仅当用户明确要求按时间或影响力排序（例如“最新”“被引最多”）时使用字段排序。

filters
object

论文过滤条件。必须传入 JSON 对象，不得传入字符串化的 JSON。只设置用户明确给出的字段，不得推断或猜测。仅接受下列字段，未知字段会被拒绝。

search_patent
检索全球专利，支持语义、关键词、结构化过滤和 PatSnap 布尔检索，返回按相关性或指定字段排序的分页结果与元数据。collapse_family 默认为 false，设为 true 时每个专利同族返回一条结果；Boolean 检索支持全部列出的排序选项。 ## 必须遵守的约束 - 关键词保留完整核心技术概念及必要限定。未指定目标语言时，为每个概念提供含义一致的中英日词组；遵循用户明确的关键词或语言限制。
输入
semantic_query, offset, keywords, search_strategy, collapse_family, domain_filters, domain, limit, sort, filters, boolean_query
参数
semantic_query
string

用自然语言忠实表达完整技术意图，保留用户指定的对象、用途、机制或性能，不额外限定应用范围或技术路线。申请人、发明人、日期、受理局、IPC 或法律状态约束放入 filters。仅在选择 semantic 时提供，且必须提供。

offset
integer

分页偏移量，表示跳过前多少条结果，默认值为 0。 约束：`offset + limit ≤ 1000`。

keywords
array

用于标题、摘要、权利要求或说明书匹配的核心技术概念短语。每项保留完整概念及必要限定，不拆成可独立召回的泛词。每项关键词可独立召回，semantic_query 不会约束关键词命中范围。 未指定目标语言时，为每个核心概念提供含义一致的中英日词组；指定时使用所要求的受支持语言。仅支持中英日文本，系统不自动翻译；其他语言使用 semantic。保持列表精简，遵守用户明确的关键词限制。仅在选择 keyword 时提供，且必须提供。

search_strategy
array

根据检索意图选择策略： - 有核心术语的技术主题 → 优先 ['semantic','keyword']：semantic_query 表达完整意图，keywords 提供核心概念词组。 - 没有可用核心术语的概念问题，或检索关键词不支持的语言 → ['semantic']。 - 明确要求仅关键词或术语查找 → ['keyword']。 - 结构化约束 → 增加 filter；仅查元数据 → ['filter']。 - 可执行 PatSnap 字段检索式、明确要求 Boolean 检索，或过滤条件无法表达的字段级分组 → 独占使用 ['boolean']。 严格绑定：选择某个策略时必须提供对应参数，未选择时禁止提供——semantic↔semantic_query、keyword↔keywords、filter↔filters/domain_filters（至少设置一个字段）、boolean↔boolean_query。选择 boolean 时，search_strategy 必须恰好为 ['boolean']；不得提供 semantic_query、keywords、filters、domain_filters 或非 general 的 domain。默认值为 ['keyword']。

collapse_family
boolean

是否按专利同族折叠结果，默认 false，逐篇返回。设为 true 时每个同族返回一条结果，data.total_hits 按同族计数；适用于 semantic、keyword、filter 及独占的 boolean 策略。非 Boolean 检索的同族总数为估算值，缺失同族标识的专利逐篇计数。

domain_filters
object

专业领域约束采用字段优先、与类型无关的伪 JSON 模板：{"<field>":{"<operator>":<符合 Schema 和 value_shape 的 operand>}}。尖括号中的元变量仅用于说明，绝不能原样发送。构造本字段前必须调用 describe_search_capability。本字段仅适用于受支持的专业领域。字段或属性的 operators 数组是允许使用的操作符清单；只能使用所选能力中定义的字段名、属性名、操作符、Schema 和原始值示例。基本类型集合的操作数是字面量数组；对象集合的操作数是非空 Object Filter 数组，每个属性条件都是形如 {"eq":value} 的 Operator Object。不同字段之间、同一字段的多个操作符之间，以及同一 Object Filter 内的属性条件之间均为 AND；同一 Object Filter 内的属性必须匹配同一个集合元素。每个 Object Filter 至少需要一个不是 ne/not_in 的条件。所有字段、属性、操作符和操作数都必须符合所选能力；能力中未声明的名称或操作数无效。每个数组操作数最多接受 100 个不同元素。当 domain='general' 或 search_strategy 不包含 'filter' 时，本字段无效。

domain
string

检索能力选择器。常规专利元数据检索使用 'general'；当请求的概念、约束或返回字段超出常规专利元数据时，才使用本 Schema 中列出的专业领域能力。应根据语义范围选择，而不是根据值的表示形式选择。 可选值： - general：通用专利检索能力。 - ls：当用户检索涉及药物、治疗靶点、疾病、专利类别、技术、化学结构或生物序列的生命科学专利时使用。实体过滤器接受公开名称。

limit
integer

单页返回结果数量，范围为 1–100，默认值为 10。 与 `offset` 配合进行分页；约束：`offset + limit ≤ 1000`。

sort
string

结果排序方式。用户未要求特定顺序时，使用 relevance 按最佳匹配排序；仅在用户明确要求按时间或被引次数/影响力排序时使用对应属性排序。字段：publication、application、granted、expired、priority、cited_count；不带前缀为升序，'-' 前缀为降序。所有排序选项均适用于 Boolean 检索；Boolean 检索的 priority 按最早优先权日排序。

filters
object

专利过滤条件。必须传入 JSON 对象，不得传入字符串化的 JSON。只设置用户明确给出的字段，不得推断或猜测。仅接受下列字段，未知字段会被拒绝。

boolean_query
string

接受两种形式：（1）按照下列语法和字段说明构造的可直接执行的 PatSnap 字段检索式；（2）完整、精确且不透明的预生成引用。可依据本字段说明直接构造检索式；用户已提供可执行检索式时必须原样保留。预生成引用必须保持完整且原样使用，不得由其他值推导，不得与检索语法组合，也不得解析、展开或改写。引用格式：BOOLEAN_QUERY_ID:bq_<64 位小写十六进制字符>。Boolean 字段、含义和示例：使用用户明确提供的技术主题、关键词、短语、缩写、产品名、材料名或工艺词，并选择能够覆盖所需文档部分的最窄技术文本字段。同一技术字段中的每个备选项都必须能够独立、完整地表达用户要求的技术概念并保留必要上下文；多词概念应保留为带引号的完整短语，避免孤立的歧义缩写或宽泛组成词。TTL_ALL：在标题原文和译文中匹配，例如 TTL_ALL:("solid-state battery")；TA_ALL：在标题和摘要的原文及译文中匹配，例如 TA_ALL:("fuel cell" OR "hydrogen fuel cell")；TAC_ALL：在标题、摘要和权利要求的原文及译文中匹配，例如 TAC_ALL:("wireless charging")；TACD_ALL：在标题、摘要、权利要求和说明书的原文及译文中匹配，例如 TACD_ALL:("carbon capture")。申请人和受让人约束使用以下字段：ANC 按当前权利人名称匹配，例如 ANC:("Y")；ANCS 按已解析、标准化的当前权利人名称匹配，例如 ANCS:("S")；ANCS_ID 按已解析、标准化的专利申请人 ID 匹配，该 ID 不是公司 ID，例如 ANCS_ID:("A")；ANCS:(TREE@"<标准化公司名称>") 用于用户明确要求多公司范围时，选择已确认的指定公司及其全部下属公司节点。TREE@ 使用标准化公司名称而不是 ID，并保留名称中的标点和空格。ANCS、ANCS_ID 和 TREE@ 必须使用已解析、标准化的身份值；未经解析和标准化的用户名称使用 ANC。IN：发明人，例如 IN:("Y")；IPC：分类号，例如 IPC:(H04W)；AUTHORITY：专利受理局，例如 AUTHORITY:(CN)；APD：申请日，例如 APD:[YYYYMMDD TO YYYYMMDD]；PBD：公开日，例如 PBD:[YYYYMMDD TO YYYYMMDD]；PATENT_TYPE：专利类型，A 表示发明申请、B 表示授权发明、U 表示实用新型、D 表示外观设计，例如 PATENT_TYPE:(A OR B OR U OR D)；PN：公开（公告）号，例如 PN:(N)；APNO：申请号，例如 APNO:(N)。同一字段的备选值放在该字段条件内分组，各独立条件之间使用 AND、OR 或 NOT。
