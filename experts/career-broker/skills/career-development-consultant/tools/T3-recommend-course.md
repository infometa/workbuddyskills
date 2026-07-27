# T3 · 课程推荐（QLearning MCP · 已实测）

## 触发信号
- 用户在 step 14-15 已对某方向承诺，问"我现在该学什么 / 需要补什么 / 推荐点课"
- 教练做完 T1 方向建议后，用户共鸣并问"那我要怎么准备"

> 不是用户问"有什么课"立刻就调——先看用户是否已"承诺方向"。
> 没承诺就推课，等于教练在替决定。

---

## 前置条件

需要用户已**装好 QLearning MCP**。详细教程：`skills/career-broker-core/references/setup/05-qlearning-mcp.md`。

### 启动 T3 自检（4 步）

```
1. 查工具列表里有没有 mcp__QLearning__searchQlCourse
   - 有  → 直接调，进主流程
   - 没有 → 进 step 2

2. 跑 python skills/career-broker-core/scripts/inspect_mcp_json.py
   读它返回的 JSON：
   - has_tai_pat=true  → 用户已为别的 MCP 配过太湖 PAT，可复用（脚本只给掩码 tai_pat_masked，**真正写入时由 LLM 自己 Read mcp.json 拿全串**，脚本不输出明文）
   - missing 列表      → 用户还缺哪几个本专家用的 MCP
   - advice            → 直接说给用户的一句话建议

3. 用 step 2 的结果决定「自动配置」还是「引导用户操作」（详见下方分支）

4. 配置完成后必须告诉用户：还要去客户端点一下「专家 → 连接器 → 自定义连接器 → 信任 QLearning」
```

### 处理分支（按 inspect 结果走）

#### ✅ 分支 A · 已有可复用 PAT + 只缺 QLearning（最常见）

**直接帮用户写到 mcp.json**——不要让用户复制粘贴 JSON 片段，这是反人类的。

执行步骤（用 Read/Edit 工具）：

```
1. Read ~/.workbuddy/mcp.json
2. 解析 JSON，往 mcpServers 字段里加上 QLearning 段（PAT 从 mcp.json 里已有 MCP 的 Authorization 直接复用同一份全串；不要用 inspect 的掩码）
   - `url`: `https://qlearning.mcp.it.woa.com/api/mcp`
   - `transportType`: `streamable-http`
   - `timeout`: `300000`
   - `headers.Authorization`: `Bearer <tai_pat>`
   - `disabled`: `false`
3. Write 写回 ~/.workbuddy/mcp.json（保持其它字段不变）
4. 告诉用户：
```

**配置完话术**：

```
我看到你为 <tai_pat_source> 配过太湖 PAT，已经直接复用了——QLearning 的配置我帮你写到 ~/.workbuddy/mcp.json 了。

现在还差最后一步，要你手动操作：
打开 WorkBuddy 客户端 →「专家」→「连接器」→「自定义连接器」→ 列表里能看到 QLearning →
点旁边的「信任」按钮（没信任的话 MCP 不会激活）。

点完信任后回我一句"装好了"，我立刻给你搜真实的 QLearning 课。
```

> **硬约束**：写文件前必须 Read 确认现有配置；写后必须告诉用户「点信任」这一步——客户端 UI 操作 LLM 帮不了，只能引导。

#### ⚠️ 分支 B · 还没装过任何 mcpgw 系 MCP（tai_pat == null）

PAT 拿不到，没法直接帮配。但仍要尽量减少用户操作：

```
推课得借学堂的力——你这边一个 mcpgw 系 MCP 都还没装过，
我这没法帮你跳过申请太湖 PAT 这一步。

3 步走（大概 3 分钟）：
1) 去 https://tai.it.woa.com/user/pat 申一个 PAT，复制下来
2) 把它发给我，我帮你写 ~/.workbuddy/mcp.json（学堂 + km 都帮你配上，省得回头再跑一次；招活MCP 走一键授权，不用 PAT）
3) 写完后你去客户端「专家 → 连接器 → 自定义连接器」点「信任」即可

完整指南：skills/career-broker-core/references/setup/00-mcp-bundle.md（一次装齐 mcpgw 全家）
```

> **关键**：用户给了 PAT 之后（第 2 步），LLM **直接帮 ta 写 mcp.json**——不要再让用户自己粘贴 JSON。
> 写完一样要提示去客户端「专家 → 连接器 → 自定义连接器」点「信任」。

#### 🔀 分支 C · 已有可复用 PAT + 缺多个 MCP

PAT 能复用，**一次帮用户把缺的几个 MCP 都写进 mcp.json**：

```
我看到你 mcp.json 里已经有 <tai_pat_source> 配的太湖 PAT，本专家这边还差这几个：<missing>。

我帮你一次写齐——已经直接复用 PAT 了（招活MCP / 自评MCP 不在这里，它俩走一键授权弹窗，切走再切回本对话连接卡会自动弹出来点「连接」就行）。

写完之后你去客户端「专家 → 连接器 → 自定义连接器」依次点「信任 <每个 MCP 名>」就好了。
```

执行：Read mcp.json → 把所有 missing 中的 mcpgw 系条目加进去（PAT 复用） → Write 回去 → 引导信任。

---

### 通用规则：MCP 缺失时的标准动作（所有需要 MCP 的 skill 都遵守）

**不要**只丢一句"你去装 MCP 吧"+ setup 文档链接。**正确流程**：

1. **检测**：调 `skills/career-broker-core/scripts/inspect_mcp_json.py` 看用户已有什么
2. **能帮就帮**：PAT 已存在 → LLM 直接 Read/Edit `~/.workbuddy/mcp.json` 写配置（不要让用户自己粘贴 JSON 片段）
3. **必须告知用户最后一步**：写完文件后，客户端要去「专家 → 连接器 → 自定义连接器 → 信任 <MCP 名>」才能激活
4. **严禁**：让用户已申过 PAT 时再申一遍；让用户手抄 JSON；不告诉用户「信任」这一步导致 ta 以为装好了但 MCP 没激活
---
> 严禁在 QLearning 没装时假装搜过然后凭训练知识列课名（详见末尾「硬约束」段）。
> 严禁承诺"装完我自动给你搜"之外的"以后帮你推"——不装就是不装，等用户主动说装好了再说。
> 严禁在用户已有可复用 PAT 时让 ta "再申一个"——这是对用户时间的浪费。

### 没装时只能给"能力地图"，不给课名

用户选"现在不装"分支后，T3 不再走 searchQlCourse。改成给"能力地图"：

```
你这方向（<用户方向>）一般要补这 3 块：

· <能力 1>：<一句解释为啥它对这方向重要>
· <能力 2>：<同上>
· <能力 3>：<同上>

具体怎么补——读书 / 网课 / 项目实战 / 找人聊都行，你自己挑。
（学堂里其实有不少现成的课，等你装好 MCP 我给你搜。）
```

**绝对不许**：
- 列具体课名（《XX 课》——不管 LLM 训练里听过没）
- 列具体平台课（"极客时间的 YY 课"）
- 给课程链接 / itemId

**只许**：
- 描述能力维度（"产品 sense" / "数据分析" / "用户增长基本功"）
- 抽象的资源类型（"读书 / 网课 / 项目实战 / 找人聊"）

---

## QLearning MCP 工具清单（实测确认 · 7 个工具）

| 工具 | 干啥 | T3 是否用 |
|---|---|---|
| `mcp__QLearning__searchQlCourse` | 关键词搜课，默认 12 条 | ✅ **主力工具** |
| `mcp__QLearning__getRecommendedCourses` | 个性化推荐（基于职级/学习记录）| ✅ 备选（首次调有点慢） |
| `mcp__QLearning__getCourseRank` | 内部热门榜单（日榜/月榜）| ✅ 偶尔用（"大家都在学什么"） |
| `mcp__QLearning__getCourseDetail` | 单课详情（actType+actId） | ⏭️ 用户点开问详情才调 |
| `mcp__QLearning__getLatestLearnedCourses` | 当前用户最近学的课 | ⏭️ 用于"避免重复推" |
| `mcp__QLearning__chatWithXiaoQ` | 学堂内置问答智能体（小Q）| ⏭️ T3 不用，更适合 career-qa 兜底 |
| `mcp__QLearning__fetchMentorKnowledge` | 导师辅导知识库 | ⏭️ 跟职业咨询无关 |

---

## 主调用模板（searchQlCourse）

```python
mcp__QLearning__searchQlCourse(
  keyword="AI 产品",        # 必填
  moduleName="网络课",       # 可选筛选：网络课/培养项目/活动/文章/直播/案例/行家/面授课
  currentPage=1              # 可选
)
```

### 实测返回结构（关键字段）

```json
{
  "structuredContent": {
    "courses": [
      {
        "itemId": "24697",
        "moduleName": "网络课",
        "title": "AI 产品榜面向鹅厂独家数据分享与解读 | AI 产品学习营",
        "courseLevel": 1,
        "href": "https://sdc.qq.com/s/b5GaSG?scheme_type=netcourse&course_id=24697",
        "thumbnailUrl": "...",
        "createdAt": "2025-03-24 10:56:12",
        "brief": "<课程简介，约 200-500 字>"
      }
    ],
    "total": 12,
    "keyword": "AI 产品"
  }
}
```

> 注意：title 和 brief 里带 `<span class='highlight'>...</span>` HTML 标记，输出给用户前要先**正则去除**。

---

## 输入提取（教练做的事）

课程推荐前先读取 `profile.json.basic`：

- `position_name` / `position`：当前职位
- `level` / `careerLevelName`：当前职级
- `genus_name` / `clan_name`：职位类/职位族

教练根据**用户承诺的方向 + 当前职位 + 当前职级**，提炼 **2-3 个关键词**给 QLearning。
不要直接用 profile_compact 的 skill_tags。

| 用户承诺的方向 | 关键词 | moduleName 偏好 |
|---|---|---|
| AI 产品 / LLM 应用 | `AI 产品` / `大模型 产品` | 网络课 / 培养项目 |
| B 端 / 流程产品 | `B 端产品` / `企业服务` | 培养项目 / 文章 |
| 用户增长 | `用户增长` / `数据分析` | 网络课 |
| 管理转型 | `管理` / `领导力` | 培养项目（系统课） |
| HR Tech 深耕 | `HR 数字化` / `招聘 AI` | 文章 / 案例 |

关键词组合规则：

1. **同职位精进**：用户没有明确转型，只说“提升/精进/补课”时，关键词优先用 `当前职位 + 用户方向`，如 `产品策划 AI`、`产品策划 数据分析`。
2. **职级适配**：P5/T5 及以下优先基础方法论、实操课；P6/T6 及以上优先体系化、影响力、跨团队协同、项目负责人类课程。
3. **明确转型**：用户明确说想转型/换赛道，或前序职业发展沟通已经形成新方向承诺，才把关键词重心转到目标方向。
4. **职位未知**：如果 profile.basic 没有职位/职级，不猜；只按用户方向搜，并在内部标注画像 basic 不完整。

> 多关键词时**分别 search 后合并去重**——QLearning 的 search 不支持多 keyword。

---

## 输出形态（教练翻译规则）

### ❌ 错误：直接 dump 12 条课程清单
### ✅ 正确：教练挑 3 门用对话语言端给用户

```
学堂里搜了一下「AI 产品」，挑 3 门可能合适的：

· 《成为 AI 产品经理》| 极客时间 — 系统课，从 0 到 1 转 AI PM 的路径
· 《AI 产品实战：解码需求、复盘失败、探索未来》— 一线 AI PM 真案例
· 《AI 产品入门小文》— 1 篇文章先建立框架感，30 分钟读完

要不要先从那篇短文开始？读完再决定要不要刷系统课？
```

### 选课规则

1. **类型搭配**：1 门系统课（培养项目/网络课）+ 1 门短读物（文章）+ 1 门可选实战（案例/活动）
2. **去重已学**：调 `getLatestLearnedCourses` 拿用户已学清单，过滤掉
3. **优先短的**：30 天行动计划吃不下 ≥20h 大课，标注一下时长（brief 里通常有）
4. **去掉 `<span class='highlight'>` 标记**：正则 `re.sub(r'<[^>]+>', '', text)` 清洗
5. **每门一句话理由**：≤ 30 字，连接到用户方向，并尽量说明为什么适合当前职位/职级

---

## 调用后续

| 用户回应 | 教练动作 |
|---|---|
| "好，我去学第 X 门" | 把这门课写入 30 天行动计划（T4），用 itemId 留个 link |
| "都太长 / 都不感兴趣" | 不强推，问"你之前学新东西，都是怎么入门的" |
| 沉默 | "没事，课只是工具。我们再回到刚才那个想法——你说想试 X，最让你心动的是什么？" |
| "再多看看其他方向" | 不立刻换，反问"是哪一个让你不太确定？" |

---

## 兜底

- searchQlCourse 调用失败 / 超时 → "学堂这会儿没响应，先把这事记下来，下次找我再推。"
- 0 hit / 关键词搜不出 → 换关键词重试，仍 0 → "学堂里这块课不太多，你可以试试外部资源（极客时间 / Coursera / B 站）。"
- 用户问"有没有热门课" → 改调 `getCourseRank(rankType=month, recommendType=14)`（热学榜）

---

## 隐私

- 输出 url 给用户没问题（站内链接）
- 不主动调 `getLatestLearnedCourses`——除非要做"已学过滤"，调完只用做去重，不要展示给用户"我看到你之前学过 X"（侵入感）

---

## 硬约束：课程必须是 QLearning 真实返回

**只推 `searchQlCourse` / `getRecommendedCourses` / `getCourseRank` 真实返回里的课**——itemId / title / href / brief 都必须从 API 来。

**不许**：
- 编课程名（"《成为 AI 产品经理》"这种本文档里的示例**只是格式样例**，不是真实存在的课）
- 编 itemId / 自造 sdc.qq.com 链接
- 把 LLM 训练数据里听过的外部课（极客时间 / Coursera）当 QLearning 课推
- QLearning 没装时假装搜过

QLearning 没装 → 按 §前置条件指引用户装。0 hit → 按 §兜底处理。**绝对**不要凭空给课名顶上去。

