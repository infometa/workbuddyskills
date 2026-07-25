# 腾讯探元文博专家（Tanyuan Cultural Heritage Expert）

> WorkBuddy 专家市场 Agent 型专家。基于腾讯探元的文物数据库、世界遗产数据库与文博知识库，面向文博爱好者、亲子家庭及职场办公人群（策划、编辑、教师、设计师等），提供文物与世界遗产查询、知识问答、文物对比、攻略规划与研学方案五大能力。

- **专家类型**：Agent
- **分类**：`12-IndustryConsultant`（行业顾问）
- **作者**：腾讯 SSV 数字文化实验室
- **版本**：1.0.0

## 目录结构

```
tanyuan-cultural-heritage-expert/
├── .codebuddy-plugin/
│   └── plugin.json                       # 专家核心配置
├── agents/
│   └── tanyuan-cultural-heritage-expert.md   # Agent 定义（系统提示词）
├── skills/
│   └── tanyuan-search/                   # 探元检索技能
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── search-relics.js          # 文物 / 世界遗产结构化检索
│       │   └── search-knowledge.js       # 文博知识向量检索
│       └── references/
│           └── api-spec.md               # 精简版 API 参考
├── avatars/
│   └── expert.png                        # 头像（512×512 PNG，420KB，已就绪）
└── README.md
```

## 核心能力（5 项）

| 能力 | 典型问题 |
|------|---------|
| 文物与世界遗产查询 | 查询文物名称/年代/类别/等级/馆藏机构等信息，以及世界遗产国家/入选年份/类别/标准/濒危状态等结构化事实 |
| 知识问答 | 考古发现、文物保护、历史脉络、艺术鉴赏、工艺技术等专业问答 |
| 文物对比 | 两件及以上文物的产地/釉色/工艺/存世量/代表作等多维对比 |
| 攻略规划 | 博物馆参观建议、主题展览推荐、文博研学路线定制 |
| 研学方案 | 面向不同年龄段（尤其亲子）的主题研学教案设计 |

## 工具选择与 Agentic RAG 策略（概览）

本专家**不把能力硬绑定到某个工具**，而是由 Agent 依据问题特征自主选择工具、重构检索 query、并按需多轮迭代（Agentic RAG）：

- `search-relics.js`（文物 / 世界遗产数据库 NL→SQL）：面向**精确事实查询**。`datasourceType=0` 按明确的馆藏机构/出土地/年代/类别/等级等条件查询数据库内文物；`datasourceType=1` 查询世界遗产国家/洲别、入选年份、类别、评定标准、濒危状态及关联知识层数据。
- `search-knowledge.js`（关键词 + 向量）：擅长**单件文物或单主题**的背景、工艺、故事、鉴赏、对比论证、攻略、研学等细节说明。
- **平台联网检索**：探元两个库覆盖有限、均非全集，**"代表作/著名/最重要/十大/排名"这类总结评价类问题以联网检索建立清单与知名度判断为主，再用探元库补单件细节**。

> 本节仅为面向读者的概览。**工具选择信号、query 重构规则、组合与迭代等完整策略以运行时文档为单一事实源**：技能侧见 `skills/tanyuan-search/SKILL.md`，Agent 决策逻辑见 `agents/tanyuan-cultural-heritage-expert.md`。

## 运行依赖

- **Node.js ≥ 18**（使用内置 `fetch` + `AbortController`，**无第三方 npm 依赖**）
- 无需 `chmod +x`，跨平台一致（macOS / Linux / Windows）
- **外网连接**：两个脚本运行时需能访问探元后端 API 域名 `api-ai-creation.tanyuan.qq.com`（`https`）。部署环境须放通该出站访问，否则检索调用会失败。
- **凭据合规**：当前后端接口无需鉴权，脚本内**未硬编码任何密钥**。若后续接口需要 Token，须通过 `.mcp.json` 的 `tokenSchema` 或环境变量注入，**严禁在脚本 / 仓库中硬编码密钥**。

## 环境准备与验证

本专家无需安装任何第三方依赖，仅要求运行环境具备 Node.js 18 及以上版本。使用前可执行以下命令确认：

```bash
# 1. 验证 Node.js 版本（需 ≥ 18）
node -v

# 2. 校验脚本语法可正常解析
node -c skills/tanyuan-search/scripts/search-relics.js
node -c skills/tanyuan-search/scripts/search-knowledge.js
```

若 `node -v` 输出低于 v18，请先升级 Node.js；两条 `node -c` 命令无报错即表示脚本可正常加载。

## 脚本用法

两个脚本均通过 `node` 调用，Agent 在响应用户请求时由平台的 `Bash` 工具执行：

```bash
# 文物查询
node skills/tanyuan-search/scripts/search-relics.js "<query>" [datasourceType]

# 知识问答 / 攻略
node skills/tanyuan-search/scripts/search-knowledge.js "<query>" [datasourceType]
```

- `query`：自然语言检索问题（必填）。调用 `search-relics.js` 时应保留全部有效过滤条件、问题形态和返回意图，不要压缩成关键词串
- `datasourceType`：对 `search-relics.js`，`0`=文物数据库（默认）、`1`=世界遗产数据库；对 `search-knowledge.js`，`0`=默认/文物知识源、`1`=文化遗产知识源

**stdout 输出（扁平化 JSON）**：

- `search-relics.js` → `{ requestId, rowCount, items: [...对象] }`（脚本已对 `rows[]` 做 `JSON.parse` 预解析；`rowCount` 为本次返回行数、受后端条数上限约束，**非匹配总数**）
- `search-knowledge.js` → `{ requestId, text }`

**失败**：exit code 非 0，stderr 打印 `HTTP <code>: <body>` 或 `API error: <msg>`；参数缺失 exit code = 2。

### 本地手工验证示例

```bash
# 文物结构化查询：保留过滤条件与返回意图
node skills/tanyuan-search/scripts/search-relics.js "故宫博物院收藏的明代青铜器有哪些，请返回名称、年代和馆藏机构" 0
# 世界遗产结构化查询（datasourceType=1）
node skills/tanyuan-search/scripts/search-relics.js "中国有哪些文化类世界遗产，请返回入选年份、评定标准和简介" 1
# 开放语义问答（适合 knowledge）
node skills/tanyuan-search/scripts/search-knowledge.js "三星堆 青铜面具 造型特征 文化含义" 0
```

## 头像

`avatars/expert.png` **已就绪**：512×512 px PNG，约 420KB（≤500KB），符合规范。如需替换，保持同样的尺寸与格式约束即可。

## 打包提交

打包前先清理仓库产生的临时/评审文件（这些**不应**进入专家包）：

```bash
# 1. 清理临时与评审产物
find tanyuan-cultural-heritage-expert -name '.DS_Store' -delete
rm -rf tanyuan-cultural-heritage-expert/.review-cache

# 2. 打包上架（排除评审报告与临时文件）
zip -r tanyuan-cultural-heritage-expert.zip tanyuan-cultural-heritage-expert/ \
  -x "*.DS_Store" -x "*/__pycache__/*" \
  -x "*/.review-cache/*" -x "*/审查报告-*.md"
```

> 说明：`审查报告-*.md`、`.review-cache/` 仅用于开发期自检，不属于专家包内容，打包时排除。

## 提交前自检清单

### 文件结构
- [x] `.codebuddy-plugin/plugin.json` 存在且 JSON 有效
- [x] `agents/tanyuan-cultural-heritage-expert.md` 存在
- [x] `skills/tanyuan-search/SKILL.md` 与两个 `.js` 脚本存在
- [x] `avatars/expert.png` 已放入（512×512 PNG，420KB ≤500KB）
- [x] 不含 `hooks/` / `commands/` / `.lsp.json` / `settings.json`
- [x] `agents/` 和 `skills/` 在根目录（不在 `.codebuddy-plugin/` 里）
- [ ] 打包前已删除 `.DS_Store`、`.review-cache/`，并排除 `审查报告-*.md`

### plugin.json
- [x] `name = plugin = tanyuan-cultural-heritage-expert`
- [x] `expertType = "agent"`，`agentName = tanyuan-cultural-heritage-expert`
- [x] `displayName / profession / displayDescription / defaultInitPrompt / tags / quickPrompts` 全部中英双语
- [x] `displayDescription.zh` 字数在 40-50 之间（当前 49 字）
- [x] `tags` 固定 3 个
- [x] `quickPrompts` 固定 3 条，第 1 条 = `defaultInitPrompt`
- [x] `categoryId = "12-IndustryConsultant"`
- [x] `skills = ["./skills/tanyuan-search"]`
- [x] **不含** `tools` / `dependencies` / `teamInfo` / `members`

### Agent MD
- [x] frontmatter `name` 与文件名一致（`tanyuan-cultural-heritage-expert`）
- [x] frontmatter 含 `description / displayName / profession / maxTurns`
- [x] **frontmatter 中不含 `tools` 字段**
- [x] 正文清晰定义了五大能力、Agentic RAG 工具选择策略、脚本调用方式、输出模板与边界
- [x] 明确约束**不向用户暴露内部运行信息**（工具/检索/query 改写/失败等）

### 脚本
- [x] `node -c skills/tanyuan-search/scripts/search-relics.js` 通过
- [x] `node -c skills/tanyuan-search/scripts/search-knowledge.js` 通过
- [x] 参数缺失时 exit 2；HTTP/API 失败时 exit 1
- [x] `BASE_URL` 指向的环境符合上架预期（**已切换为正式环境** `https://api-ai-creation.tanyuan.qq.com`）

### 头像
- [x] PNG 格式，512×512 px，≤500KB（420KB）
- [x] 内容合规、风格专业
