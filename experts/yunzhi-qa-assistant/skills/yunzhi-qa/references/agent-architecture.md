# Agent 整体架构

> 腾讯云知识问答专家的端到端流水线说明。

---

## 总览

```
用户原始问题
    ↓
[Phase 1] MCP 权限判断（前置门禁 · 个人 Token 绑定）
    ├─ 已绑定 → 进入 Phase 2
    ├─ 401 / 过期 → 引导续期，终止
    └─ 未绑定 → 仅引导用户通过 https://lexiangla.com/mcp?company_from=CSIG 获取 LEXIANG_TOKEN，终止
    ↓
[Phase 2] 意图闸门 + 问题泛化（生成多个检索 Query）
    ├─ 意图判定：同时命中「对比动作」+「外部友商实体」？
    │     ├─ 否（默认/不确定）→ mode=standard（纯站内链路）
    │     └─ 是 → mode=competitive（站内+站外双通道）
    ├─ 国际化叠加判定（与 mode 正交）：命中「海外/国际版/出海/多语言/翻译/本地化/overseas/international」？
    │     ├─ 是 → intl=on（站内检索注入「国际版=是」UDF 过滤 + 强制二次筛选，仍不联网）
    │     └─ 否/不确定 → intl=off
    ├─ 主关键词保留 / 缩写补全 / 子问题拆解 / 意图补全 / 同义词扩展 / 时间语义转换
    └─ competitive 额外：逐友商独立改写 + 查品类维度词典装配对比维度
    ↓
[Phase 3] 检索模块（按 mode 分流）
    ├─ 通道 A 站内乐享（两种 mode 都跑；intl=on 时每次 embedding 调用注入 udf_values 过滤「国际版=是」）
    │     ├─ ① search_kb_embedding_search（语义向量，每次都先跑）
    │     ├─ ② 判断无召回 / 全部低相关 / 缺精确实体命中？ → 是则 search_kb_search 兜底
    │     ├─ ③ intl=on 强制二次筛选：软过滤会混国内版，须按标题/正文特征剔除仅留国际版
    │     └─ ④ entry_describe_ai_parse_content（精读高分召回，按需）
    └─ 通道 B 站外竞品官网（⚠️ 仅 mode=competitive 破例联网）
          ├─ 逐厂商独立 WebSearch/WebFetch（site: + allowed_domains 双重过滤）
          ├─ 每厂商 ≥2 轮（功能/规格 + 定价/计费）+ 第二引擎交叉验证
          └─ 过滤流水线：非白名单/代理商页一律丢弃
    ↓
[结果排序与过滤] Rerank、按 target_id 去重、相关性阈值过滤；站内/站外来源分区
    ↓
[Phase 4] 总结生成模块
    ├─ 严格基于检索结果
    ├─ [1][2] 学术风数字角标内联引用（禁用 [citation:X]）
    ├─ 结构化 Markdown 输出（competitive 用对比模板 + 来源分级标签）
    └─ 附文档标题 + 原文链接
    ↓
[拒答策略]
    ├─ standard：知识库无结果 / 全部低于阈值 → 直接拒答（禁止联网兜底）
    └─ competitive：站内外多轮仍无官方数据 → 就该项写「官方未披露」，其余照常输出
```

---

## Phase 1：MCP 权限判断（前置门禁）

> 🔒 本专家以「用户绑定个人乐享 MCP Token」的方式接入，**权限判断永远是第一步**，未通过前禁止进入 Phase 2~4。

### 检测方法

按以下优先级尝试：

1. 调用 `mcp__lexiang__whoami`（成功即通过）。
2. 若客户端未暴露 `mcp__lexiang__*` 工具，使用 Streamable HTTP JSON-RPC 直连：
   ```python
   import requests, json, os
   url = "https://mcp.lexiang-app.com/mcp?company_from=<COMPANY_FROM>"
   headers = {"Authorization": f"Bearer {os.environ['LEXIANG_TOKEN']}"}
   payload = {"jsonrpc":"2.0","id":1,"method":"tools/call",
              "params":{"name":"whoami","arguments":{}}}
   resp = requests.post(url, headers=headers, json=payload, timeout=10)
   ```

### 三种结果分支

#### ✅ 成功（200 + 用户信息）

记录返回的 `company.company_domain`（用于后续生成原文链接），简短播报：

```
✅ 乐享 MCP 已就绪
👤 当前用户：{name}
🏢 绑定企业：{company_name}
```

**禁止回显完整 Token。**

#### ❌ 401 / Token 过期

```
🔒 检测到乐享 MCP 令牌已过期或无效。
请打开链接，点击「续期」按钮重新获取 LEXIANG_TOKEN：
https://lexiangla.com/mcp?company_from=CSIG

完成续期后，把新的 LEXIANG_TOKEN 告诉我即可。
```

#### ❌ 工具不存在 / 未配置 / 连接失败

仅简洁提示用户去查询 Token，**不要回显完整的 mcp.json 配置块**：

```
⚠️ 你尚未绑定乐享（云知）MCP，无法检索知识库。

请打开下方链接获取你的 LEXIANG_TOKEN（lxmcp_ 开头）：
https://lexiangla.com/mcp?company_from=CSIG

拿到 Token 后告诉我，我会帮你完成绑定（默认 COMPANY_FROM=CSIG）。
```

> ⚠️ **绝不**回显完整 Token，**也不要**主动展示 mcp.json 配置块。
> 默认 `COMPANY_FROM=CSIG`，无需让用户提供。
> **绑定未完成前，绝不进入 Phase 2。**

---

## Phase 2：意图闸门 + 问题泛化模块

### 意图判定（前置闸门，决定走哪条链路）

`mode=competitive` **必须同时满足**：① **对比动作**（对比/比较/vs/相比/差异/区别/优劣/对标/横评）；② **外部友商实体**（阿里云/华为云/火山引擎/百度智能云/AWS/Azure，或 OSS/OBS/S3/ECS/RDS/通义/盘古 等友商产品）。任一不满足 → `mode=standard`；**判定不确定也按 `standard`**（默认不联网）。

- 只有友商名无对比动作（「介绍下阿里云 OSS」）→ `standard`，纯站内，无果拒答。
- 只有对比动作无外部友商（「CVM 和 CDB 的区别」）→ `standard`，纯站内。
- 两者都命中 → `competitive`，进入双通道；额外**逐友商独立改写** + 查 `competitive-analysis.md` 品类词典装配对比维度。

> competitive 链路的完整规则（白/黑名单、过滤流水线、来源分级、品类维度词典、对比模板）见 [`competitive-analysis.md`](./competitive-analysis.md)。

### 国际化叠加判定（与 mode 正交 · 纯站内不联网）

`intl=on` 触发条件：问题涉及**海外 / 国际版 / 国际站 / 出海 / 海外市场 / 多地区 / 多语言 / 语言支持 / 翻译 / 本地化 / overseas / international / global**，或明确点名海外地区/站点（「新加坡节点」「海外金融行业案例」等）。命中即 `intl=on`，未命中/不确定 → `intl=off`。

- `intl` 与 `mode` **相互独立**：`intl=on` 只影响通道 A 站内检索的参数（注入「国际版=是」UDF 过滤 + 强制二次筛选），**不触发联网**；竞品对比里若同时涉及海外，通道 A 基线可叠加 `intl=on`，通道 B 站外仍按竞品规则走。
- 完整参数模板、field_id / 值代码速查、软过滤二次筛选、字段重新枚举方式见 [`overseas-search.md`](./overseas-search.md)。

### 问题泛化

详见 [`query-rewriting.md`](./query-rewriting.md)。

**最低质量门槛**：

- 至少 3 条 Query；
- 至少覆盖 1 次缩写补全（若问题含缩写）；
- 至少覆盖 1 次同义词扩展；
- 时间相关问题必须做时间语义转换。

---

## Phase 3：检索模块（按 mode 分流）

> **分流总则**：`mode=standard` **只走通道 A（站内乐享），严禁联网**；`mode=competitive` 先跑通道 A 拿腾讯云基线，再**允许**开通道 B（站外竞品官网）。

### 通道 A · 站内乐享检索（两种 mode 都跑）

#### 工具优先级（强约束 · 2026-05-18 更新）

| 优先级 | 工具 | 触发条件 |
|--------|------|----------|
| **P0：默认首选** | `mcp__lexiang__search_kb_embedding_search` | **每次问答都先且仅跑这一个工具**，对 Phase 2 产出的多条 Query 并行调用 |
| **P1：兜底** | `mcp__lexiang__search_kb_search` | **仅在以下条件成立时启用**：① embedding 对所有 Query 都返回空 chunks；或 ② 召回全部低相关 / 与问题无关；或 ③ 用户问题含精确产品名 / 错误码 / API 名 / 文件名，但 embedding 召回里没有这类精确命中 |
| **P2：精读** | `mcp__lexiang__entry_describe_ai_parse_content` | 高分片段不足以回答时，对前 3~5 个 entry 精读正文；**仅对 `target_type=kb_entry` 调用，disknode 会 403** |
| **P2：元信息** | `mcp__lexiang__entry_describe_entry` | 需要确认 entry_type / extension / target_id 时使用（工具名是 `entry_describe_entry`，**不是** `entry_describe`） |

> ⚠️ **不要默认并行跑两路检索**——除非满足上面的兜底触发条件，否则只跑 embedding_search。
> 这一规则的目的：减少 token / 上下文浪费，提高检索专注度。

### 批量执行（合并执行策略）

为避免逐条审批中断用户，**必须**把多 Query 检索合并为一次脚本执行，例如：

```python
# 伪代码：默认只跑 embedding；按条件判断是否兜底 keyword
queries = [...]  # Phase 2 产出
intl = ...       # Phase 2 国际化叠加判定结果（True/False）

# intl=on 时，注入「国际版=是」UDF 过滤（软过滤，仍需二次筛选）
UDF_INTL = [{
    "match_logic_type": "and",
    "k_values": {
        "field_id": "250b20760fb74e8bb32955fe83c919cc",
        "values": [{"value": "lsihfg3ix6d"}],
    },
}]

all_hits = []
for q in queries:
    # 参数最简即可：filters.keyword 包装 query。
    # ✅ 实测：chunks[].content（命中片段正文）默认就返回，无需追加 _mcp_fields。
    filters = {"keyword": q}
    if intl:
        filters["udf_values"] = UDF_INTL   # 定向召回国际版
    hits = call_mcp("search_kb_embedding_search", {
        "filters": filters,
        "limit": 10,
    })
    all_hits.extend(hits)

# 去重（按 target_id 合并 content 片段，保留最长/最相关的一条）
dedup = {}
for h in all_hits:
    k = h["target_id"]
    if k not in dedup or len(h.get("content", "")) > len(dedup[k].get("content", "")):
        dedup[k] = h
top = list(dedup.values())[:10]

# intl=on 强制二次筛选：软过滤会混国内版，仅保留含国际版/海外/international 等特征的条目
if intl:
    def is_intl(h):
        t = (h.get("title","") + h.get("content","")).lower()
        return any(k in t for k in ["国际版","海外","出海","国际站","international","overseas","global"])
    top = [h for h in top if is_intl(h)]

# 兜底触发：只有 embedding 完全没命中或全部低相关，才启用 keyword 检索
need_fallback = (
    len(top) == 0
    or all(not (h.get("content") or "").strip() for h in top)
    or has_precise_entity_but_no_match(queries, top)
)
if need_fallback:
    for q in queries:
        # keyword 接口的 docs.title / docs.content 默认返回，无需追加字段
        # intl=on 时用 filters.udf_filters.find_values 施加同一 UDF 过滤
        kw_hits = call_mcp("search_kb_search", {
            "keyword": q,
            "limit": 10,
            "highlight": True,
        })
        # ... 合并去重排序
```

### `_mcp_fields` 与默认字段速查

> 来源：MCP 工具真实 schema + 实跑校准，2026-07-16。

**核心结论**：正文默认返回，`_mcp_fields` 只用于负向精简（不是必传项）。

| 接口 | 默认就返回（不传 `_mcp_fields`） | 说明 |
|---|---|---|
| `search_kb_embedding_search` | `chunks[].content`（命中片段正文）、`chunks[].target_type`、`chunks[].target_id`、`chunks[].score` | 实跑确认：不传任何字段参数即可拿到正文，可直接用于引用 |
| `search_kb_search` | `docs[].title`、`docs[].content`、`docs[].target_type`、`docs[].target_id` 等 | `highlight:true` 时附命中高亮 |

`_mcp_fields` 参数真实语义（来自工具 schema 原文）：

- **只接受负向排除路径**，如 `["-staffs", "-entry.html_content"]`，用于裁掉不需要的字段以省 token；
- **正向选择和 `@default` 会被工具忽略**——所以 `["@default","chunks.content"]` 这种写法**无效且具误导性，禁止使用**；
- 正文既然默认返回，**常规检索无需传 `_mcp_fields`**；只有返回体过大想省 token 时才用负向路径。
- 想看完整 Output Fields，可调 `mcp__lexiang__get_tool_schema`。

### 链接生成

> 🎯 **核心规则**：按 `target_type` 区分**云知 1.0**（旧版团队文档）和**云知 2.0**（乐享 AI 知识库）两套 URL 模板。
> ❌ **不要用** `/teams/{team_id}/docs/{xxx}` 这种早期 docs 文档模板——实测对 `kb_file` / `kb_video` 类型 404。

| `target_type` | 文档版本 | 推荐 URL |
|---------------|---------|----------|
| `disknode` | **云知 1.0**（旧版团队文档 / 网盘节点） | `https://{domain}/docs/{target_id}` |
| `kb_entry` | **云知 2.0**（乐享 AI 知识库条目；含 page/file/video/folder） | `https://{domain}/pages/{target_id}` |
| `kb_smartsheet` | 云知 2.0 智能表 | `https://{domain}/pages/{target_id}` |
| `attachment` | 附件 | 不直接出查看 URL，调附件下载接口 |
| `ai_external_doc` | 外部抓取的公开文档（如腾讯云官网） | 用原文档自带 URL，或不附链接 |

其中 `{target_id}` = `search_kb_*` 返回的 `chunks[].target_id`。

⚠️ `entry_describe_entry` 返回的 `entry.target_id` 对 `kb_file` 是底层存储 file_id（与 `entry.id` 不同），**只用于附件下载等内部接口**，不能拿来拼查看页 URL。

⚠️ 同一文档可能既以 `disknode` 又以 `kb_entry` 形式被召回（同步双轨期），此时两条都是有效链接，但优先用 `kb_entry`（2.0）版本。

`{domain}` 取自 Phase 1 的 `whoami` 返回的 `company.company_domain`；缺失默认 `https://csig.lexiangla.com`。

### 通道 B · 站外竞品检索（⚠️ 仅 `mode=competitive` 破例联网）

> 本小节是全专家**唯一允许 `WebSearch`/`WebFetch` 联网**处。`mode=standard` 绝不进入。完整规则（白/黑名单、过滤流水线、来源分级、品类维度词典）见 [`competitive-analysis.md`](./competitive-analysis.md)，此处仅列关键动作。

| 步骤 | 动作 |
|------|------|
| 1. 逐厂商独立检索 | 每个友商单独执行，禁止多厂商混进同一条查询 |
| 2. 每厂商 ≥2 轮 | 第一轮功能/规格，第二轮定价/计费；关键数据换第二个引擎交叉验证 |
| 3. 双重过滤 | `WebSearch(allowed_domains=[...])` + 查询词带 `site:官网域名`，只认白名单官网 |
| 4. 过滤流水线 | 域名非白名单 / 路径含代理商特征 / 页面含经销商词 → 一律丢弃 |
| 5. 抓全文 | 目标页用 `WebFetch` 抓取，记录 URL + 页面日期 |
| 6. 实体防污染 | COS↔OSS↔OBS↔S3 先映射再比，绝不交叉归属 |
| 7. 无数据 | 多轮仍无官方数据 → 写「官方未披露」，**绝不用黑名单来源填补** |

### 错误兜底

| 错误 | 处理 |
|------|------|
| **业务码 `code≠0`（如 `101 系统错误`）** | HTTP 200 但 `code≠0` **不等于无召回**，多为后端瞬时异常。换语义等价 Query 重试 1~2 次；只要有一条 Query `code:0` 成功即继续。**禁止**因单条 `code:101` 直接拒答 |
| 401 / 鉴权失败 | **回到 Phase 1 引导用户续期 LEXIANG_TOKEN**；续期完成前不再重复检索 |
| `tool_search` 返回碎片化 JSON | 改用全限定名 `mcp__lexiang__search_kb_embedding_search` 直接调用 |
| 客户端未暴露 mcp 工具 | 走 Streamable HTTP JSON-RPC 兜底链路 |
| 所有 Query 均 `code:0` 且召回为空 / 全部低分 | `standard`：转 Phase 4「拒答策略」（禁止联网）；`competitive`：站内无果则依赖通道 B 站外官网补充 |

---

## Phase 4：总结生成模块

详见 [`answer-generation.md`](./answer-generation.md)。

**最低质量门槛**：

- 关键论点 100% 有学术风数字角标 `[1]`（禁用 `[citation:X]`，WorkBuddy 不渲染）；
- 「参考资料」100% 是可点 Markdown 链接 `[标题](url)`，且链接全部来自检索返回，无虚构；
- 对比题强制表格、步骤题强制有序列表；
- 输出末尾必须有「参考资料」+「信息来源说明」两个区块。

---

## 拒答策略

**`mode=standard`**：当 Phase 3 通道 A 的相关性整体偏低（例如 top1 score 也不达标），或召回为空时：

1. **直接拒答**，明确告知用户："抱歉，我在你绑定的乐享知识库中未检索到与该问题直接相关的内容。"
2. 给出建设性建议：换用更具体的关键词重新提问，或确认资料是否已上传至当前知识库。
3. **严禁调用 WebSearch / WebFetch 等联网工具兜底**。
4. **严禁基于通用知识凭空作答 / 编造**。

**`mode=competitive`**：站内 + 站外官网多轮检索后仍无某项官方数据时，**不整体拒答**——就该缺失项写明「经检索，官方渠道未公开披露此数据」，其余已查到的维度照常输出；全程仍严禁引用黑名单来源。
