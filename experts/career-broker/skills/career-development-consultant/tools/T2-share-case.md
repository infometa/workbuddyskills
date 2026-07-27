# T2 · 案例陪伴（教练对话中调）

## 触发信号（任一即可）

- **【最高优先级】用户主动求案例**：「有没有像我这样的人」「类似案例」「谁转过」「别人怎么走的」「有没有先例」「类似的人转型成功」
- 教练在阶段 B/C 判断"用一个案例能让用户对号入座"
- 用户描述的卡点能精确匹配到案例库 scene_tags / event_tags

> **关键**：用户主动求案例时**立即调本工具**——不要以"流程还没到"为由跳过。
> 案例库就是为了**让用户感到不孤单**而存在的，用户开口求案例的瞬间就该给。

> **绝对不许**用"我没腾讯内部的人才流动数据"之类的话术拒答——
> 你**有 13 条案例**（CASE-001~013），支持 5 轴标签召回（stage/event/scene/persona/span）。
> 库在 `skills/career-development-consultant/references/cases/all_cases.json`，受控词表在 `skills/career-development-consultant/references/cases/tag_definitions.md`。
> 路由 LLM 把「有没有像我这样的人」直接路由到 `CC.T2`——主入口收到这个编号就该跑本工具。

---

## 调用方式（v2 · 5 轴标签召回）

```bash
# 按场景召回（最常用）
python scripts/search_cases.py --scene "<场景标签>" --top-k 2

# 双轴精准召回
python scripts/search_cases.py --scene "路径选择" --persona "🌱开放型" --top-k 2

# 按事件召回
python scripts/search_cases.py --event "跨BG活水" --top-k 2

# 查看具体 case 详情（调试用）
python scripts/search_cases.py --scene "身份焦虑" --top-k 2 --reveal-code-name
```

**标签必须来自受控词表** (`skills/career-development-consultant/references/cases/tag_definitions.md`)——不允许自由文本。

### 标签从哪来
用户对话里描述的**情境词**映射到受控词表的 scene/event/stage 标签。

| 用户说 | 映射到标签 | 轴 |
|---|---|---|
| "我担心换岗第一年绩效不好" | `转型后90天`, `绩效下滑` | scene + event |
| "现在 leader 不太支持我转" | `leader关系` | scene |
| "想换行业，不知道值不值" | `跨行业活水`, `路径选择` | event + scene |
| "新业务上手太慢" | `转型后90天`, `沟通节奏` | scene |
| "想清楚做什么" | `身份焦虑`, `决策犹豫` | scene |

教练自己**做语义映射**，从 tag_definitions.md 中选最贴的标签传入。

> **不要**把 profile 里的 skill_tags 传进来——case 的标签体系是情境维度，不是技能维度。

---

## 输出形态（两档）

### 形态 A · M2 完整陪伴（用在 step 11-13 深化）

```
有个像你的同事——CASE-001（5-10 年, 🔍 挑剔型），他/她跨BG+跨行业(2次)。

当时 ta 也在想"想换行业又怕亏一年绩效"，后来有这些复盘：

> "我每一次过去，带过去的不是行业经验，是一种快速理解陌生业务底层逻辑的能力。"

ta 给后来人的话是这样：

> "先问自己真正的瓶颈在哪：你想换的是行业，还是岗位？只是岗位，公司内部活水就够了……"

听到这里，你心里浮出什么。
```

调 `format_case_narrative.py --mode m2 --user-context "<用户原话>"` 自动生成。

### 形态 B · M3 教练引子（用在 step 4-7 澄清，不亮整个故事）

```
我有个同事（代号 CASE-001, 🔍挑剔型），他给我说过一句话——

> "我下班只想关掉所有游戏相关的东西。"

这句话落到你身上，会让你想到什么。
```

调 `format_case_narrative.py --mode m3` 自动生成。

---

## 调用规则

| 规则 | 说明 |
|---|---|
| 一次只用 1 条案例 | 多了用户记不住 |
| 不替决定 | 案例只是镜子，不是答案 |
| 不真名 | 永远用代号，rtx_name 已在 search_cases 输出剥离 |
| 不暗示对错 | "这个人最后选了 X" ≠ "你也应该选 X" |
| 用户共鸣弱时换工具 | "听起来这条不像你"——不要硬塞 |

---

## 0 hit 时怎么办

`search_cases.py` v2 有精度 5 兜底——**永不返回空**。但最低精度（全库兜底）时匹配度差，此时：

教练应当退一步：
```
我手头案例库里没找到特别贴你这种情况的——
要不我顺手去 km 上搜一下内部沉淀文章看看？或者你跟我多说说[用户卡点的某个具体面]？
```

如果用户答应去 km 搜 → 走 §"km 经验文章兜底"。
否则换标签重试，或干脆放弃 T2 走 T1（或继续教练对话）。

---

## km 经验文章兜底（结构化案例 0 hit 时的第二档）

case 库里没贴心案例时，**km MCP（搜内部 KM 文章）是合理的兜底**——
两者关系：
- case 库（7 条结构化案例）：少而精，结构化转型故事，找"像我这样的人"
- km：多而杂，长文/沉淀，看"别人怎么干的具体细节"

### 触发条件

- T2 search_cases 返回 0 hit + 用户答应"那看看 km 上有没有"
- 用户主动求**经验/案例/实战/沉淀文章/复盘**：「有没有内部讲 X 的文章」「谁写过 X 的复盘」「想看看实战经验」

### 自检 km MCP 是否可用

跑 `python skills/career-broker-core/scripts/inspect_mcp_json.py`：
- `installed` 含 `"km"` → 直接调 `mcp__km__*` 工具搜
- `missing` 含 `"km"` 且 `has_tai_pat=true` → 走「分支 A · 已有 PAT 引导话术」（PAT 复用即可，告诉用户 30 秒装好）
- `missing` 含 `"km"` 且 `has_tai_pat=false` → 走「分支 B · 全新装话术」，引导先去 skills/career-broker-core/references/setup/00-mcp-bundle.md

### ✅ 分支 A 处理（已有 PAT）：LLM 直接帮配

LLM 直接 Read `~/.workbuddy/mcp.json` → 加 km 段（PAT 从 mcp.json 已有 MCP 的 Authorization 复用同一份全串，不要用 inspect 的掩码） → Write 回去。

写完话术：

```
我手头那 7 条结构化案例没贴你的情况——但内部 KM 上一定有人写过类似主题的实战文章。

我看到你 mcp.json 里给 <tai_pat_source> 配过太湖 PAT，km MCP 的配置我直接帮你写到
~/.workbuddy/mcp.json 了——PAT 已复用。

最后一步：去客户端「专家 → 连接器 → 自定义连接器」点「信任 km」，回我"装好了"我就搜。
不想装也行，告诉我我跳过这一段。
```

### ⚠️ 分支 B 处理（全新装）

PAT 都没有，让用户先申。话术：

```
内部 KM 上肯定有相关实战文章，但你 mcpgw 系 MCP 还没装过，得先有太湖 PAT。

3 分钟搞定：
1) 进 https://tai.it.woa.com/user/pat 申一个 PAT
2) 把它发给我，我直接帮你写 ~/.workbuddy/mcp.json（学堂 + km 全配上，省得再跑一次；招活MCP 走一键授权，不用 PAT）
3) 写完后你去客户端「专家 → 连接器 → 自定义连接器」点「信任」即可

不想装也行，告诉我我跳过。
```

> 通用 MCP 安装规则：能 LLM 直接 Read/Edit `~/.workbuddy/mcp.json` 写好的，就直接写——不要让用户复制粘贴 JSON。
> 写完一定要告诉用户：还要去客户端「专家 → 连接器 → 自定义连接器」点「信任」才能激活。

### 输出形态（km 文章命中后）

km 返回的是文章列表（标题 + URL + 摘要）。**不要**把整列表 dump，挑 1-2 篇最贴用户卡点的，按教练腔翻译：

```
内部 KM 上找到一篇贴你这情况的——

《[文章标题]》[作者代号或部门]
摘要里说：[一两句最有共鸣的句子]
链接：[URL]

要不要点开看？看完我们继续聊。
```

### 硬约束（km 兜底）

- **不许编 km 文章**：标题 / 作者 / URL / 摘要必须从 km API 真实返回。LLM 训练里"听过类似的文章"不算
- **km 没装时不许假装搜过**：直接走分支 A/B 引导，不许凭训练知识凑文章名
- **隐私边界**：作者 RTX/姓名按 km 接口本身的脱敏给（如果接口返回了真实作者名，原样透传——这是 km 内部知识库默认设置）。**不主动调"获取作者画像"类工具**

---

## 隐私

- 案例库已 P0 脱敏（rtx_name 在 search_cases 输出层剥离）
- interview_at 不输出
- 用户问"这是谁"→ "为保护他的隐私，我只能用代号告诉你他的故事"

---

## 硬约束：不许编案例

case 库里没的代号、没的人物、没的引言——一律不准编。**`search_cases.py` 返回什么，你只能用什么。** 看到 `CASE-001` / `BIZ-AI-03` 这种格式不要照样自己造。0 hit 时严格按 §"0 hit 时怎么办"处理：退回去让用户多说 / 切到 km 兜底，**不要塞个看起来像案例的东西**。

LLM 训练数据里听过的"我有个朋友"、"以前有人这样"也不算——那不是案例，那是脑补。

