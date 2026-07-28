---
name: databrain-opinion-hotposts
version: 3.0.0
agent_created: true
description: 按订阅游戏生成「过去 N 小时各平台热帖日报」，分平台（Reddit / X / YouTube / Steam / TikTok / Discord / 官方论坛 / Instagram / Facebook）出榜、每榜 Top 1-10 可配，输出 markdown / html 并可一键投递到 AI Gallery 与企业微信。当用户提到「每日热帖」/「热帖榜单」/「热帖推送」/「分平台热门帖子」/「日报」时使用。数据走 feeds 表（与 databrain-opinion-metrics / databrain-opinion-alert 同源）。
author: databrain-team
metadata: {"openclaw": {"requires": {"env": ["DATABRAIN_TOKEN"]}}}
disable-model-invocation: true
---

# Databrain · Opinion Hotposts (每日热帖日报)

按订阅游戏，**每日定时生成「过去 24h 各平台热帖榜单」**，分平台展示 Top N，输出 markdown / html 供推送或网页展示。

## 架构：脚本取数 → 你填 spec → 校验 → 脚本渲染 → 原样展示

```
make_daily_digest.py --json   →  候选帖 JSON（脚本取数，确定性）
        ↓
你（agent）填 digest_spec.json  →  去重裁断 / AI 摘要 / 热议话题 / 选帖（智能）
        ↓
validate_digest.py            →  schema 校验，不过就改了重填
        ↓
render_digest.py --format ... →  markdown / html（版式由代码锁死）
        ↓
原样展示渲染产物
```

> **分工**：脚本做「算得出的」（取数 + 格式）；你做「算不出的」（摘要语义 / 同事件判断 / 话题归纳）。这些智能产物**不影响版式**——版式 100% 由渲染器保证。

## 🚨 首要硬规则（必须遵守）

1. **禁止手写最终推送正文。** 不要自己拼 `📰...━━━...` 这类文本或 HTML。
2. 必须走完整流程：⓪ 调 `report_log.py` 打点 ① 跑取数脚本 ② 按 schema 填 `digest_spec.json` ③ 跑 `validate_digest.py` 通过 ④ 跑 `render_digest.py` 生成目标格式 ⑤ **原样返回/展示渲染产物，不增删一字** ⑥ 跑 `publish_digest.py` 投递：AI Gallery 默认自动上传免批准；企业微信仅在用户已提供 webhook 时推送，否则只产出预览，不强推。
3. 你只在 `digest_spec.json` 里填「算不出的」字段（标题取原文、摘要、情感词、去重后的选帖、话题）。版式相关（分隔线 / emoji / 万粉换算 / 时间 / 千分位 / 标题截断 / 空平台隐藏）**交给渲染器，不要自己做**。

## 执行流程

### Step 0：打点（每次请求开始时调一次）

每次用户发起热帖请求，**先**调一次打点 CLI 记录本次调用（`-m` 传用户原始问题）：

```bash
python scripts/report_log.py -m "<用户原始问题>"
```

best-effort：`DATABRAIN_TOKEN` 缺失或网络失败都会静默跳过，不影响后续流程，也无需重试。打点只在此处做一次（取数时），后续渲染/投递不再重复打点。

### Step 1：取数（脚本）

```bash
python scripts/make_daily_digest.py --game_name "PUBG Mobile" --out_file /tmp/candidates.json
# 可选：--game_id（跳过自动查询）/ --platforms reddit,x,youtube / --top_n 5 / --hours 24
```

输出 `candidates.json` 结构：

```json
{
  "params": {"game_id": "...", "game_name": "PUBG Mobile", "hours": 24, "top_n": 5, "digest_time": "2026-04-22 09:00"},
  "summary_data": {"sentiment": {"pos": 0.33, "neu": 0.42, "neg": 0.25}},
  "platforms": [
    {"key": "reddit", "display": "🔥 Reddit", "candidates": [ {帖子...}, ... ], "candidate_total": 15, "skipped": false, "error": null}
  ]
}
```

每个候选帖含：`author / followers / time / engagement / sentiment_rating / sentiment / url / snippet / title(空) / language / country`。候选数 = `top_n × 3`，已按互动量降序，留给你去重后补位。

### Step 2：你做 4 件智能活，产出 `digest_spec.json`

schema 权威定义见 [references/digest_schema.md](references/digest_schema.md)。逐平台处理候选：

**① 去重（§4.3.3）**

读每条候选的 `title`（若空用 `snippet`）+ `snippet`，判断哪些是「同一事件」。

判同事件的判据（满足任一即同事件，**跨语种同样适用**）：
- 指向**同一具体对象/事件**：同一角色、同一卡池/banner、同一活动/复刻、同一版本更新、同一 bug/事故、同一官方公告。
- 标题措辞不同 / 标题党改写 / 翻译成不同语言，只要指向同一具体事件 → 同事件。

不算同事件：
- 同一对象但**不同侧面**：同一角色「技能数值」vs「皮肤外观」→ 不同话题。
- 泛泛吐槽/讨论 vs 具体事件。

正例（应合并）：
```
A "New 5-star kit leak shows insane scaling"     互动 2150
B "新キャラのスキル倍率がぶっ壊れ"                互动 1980
C "leak: upcoming banner character is broken"     互动 900
→ 同一「新角色数值泄露」事件：保留 A、B（互动最高 2 条），C 被挤出由下一候选补位；
  merged_note: "同一话题 3 条相关讨论已合并展示 2 条"
```

反例（不合并）：
```
A "新卡池抽卡体验吐槽"   ← 卡池付费/出货
B "新角色皮肤展示"       ← 外观
→ 不同话题，各自占位
```

处理规则：
- 同平台同事件**最多保留 2 条**（互动最高的 2 条）；被挤出的位置由下一位候选补齐到 Top N。
- 该平台若发生合并，在 `platforms[].merged_note` 写：`同一话题 N 条相关讨论已合并展示 2 条`（N = 该事件候选总数）。
- 候选很多时可先用粗筛工具减少比对量：库函数 `dedup.fingerprint`（标题前缀指纹，`python scripts/dedup.py --self_test` 可验证）；最终裁断仍以你的语义判断为准。

**② 标题（§4.4.1）**
- `title` 填**原文标题全文，不翻译**（feeds 无独立标题，从 `snippet` 提炼一句作标题；保持原文语种）。
- **不要自己截断**——超长截断（超 20 中文字等效宽度显示 `...`）由渲染器按显示宽度处理。

**③ AI 一句话摘要（§4.4.2）**
- 基于「标题 + 正文 `snippet`（已按信息量归一：中文≈200字 / 拉丁≈400字符）」生成，**≤30 字中文**，概括帖子主题。
- 只描述内容，**禁止评价/观点**。
- 原文非中文 → 摘要**直接输出中文**。
- 生成不了/失败 → `summary` 填 `null`（渲染器自动不显示摘要行，不要硬塞正文）。

**④ 热议话题（§4.5）**
- 通读所有平台入选帖，归纳 **Top 3** 话题标签 + 命中帖数，填 `summary.topics`：`[["新卡池", 7], ["剧情更新", 4], ["外观皮肤", 3]]`。
- 归纳不出/无文本 → 省略 `topics`（该行不渲染）。

**其余字段**：`sentiment` 直接用候选里的 `sentiment` 词（正面/中性/负面）；`summary.sentiment` 用 `candidates.summary_data.sentiment`；`game_name` / `digest_time` 用 `params`。热帖总数与各平台计数**不用填**，渲染器自动算。

> **时区约定**：feeds 的 `comment_time` 实为 **UTC+8** 墙钟（入库被误标 `+00`，实测最新帖时间贴合上海当前时刻）。故 `post.time` 原样回填、**勿做时区换算**；`digest_time` 由取数脚本按同一时区（`utcnow + 8`）生成，二者同基准，渲染器 naive 比对算「Xh 前」。SQL 时间窗也以 +8 锚点卡「过去 24h」。需改时区设 env `DIGEST_TZ_OFFSET_HOURS`（默认 8）。

### Step 3：校验

```bash
python scripts/validate_digest.py --input /tmp/spec.json --top_n 5
```

不通过会列出错误（缺字段 / sentiment 非三词 / url 非法 / 超 top_n / 同事件 >2）。**按提示修正 spec 后重跑，直到通过**。

### Step 4：渲染并原样展示

```bash
python scripts/render_digest.py --input /tmp/spec.json --format markdown    # 企微/飞书/Slack/WorkBuddy
python scripts/render_digest.py --input /tmp/spec.json --format html        # AI Gallery / 内部网页
```

把渲染产物**原样**交给下游渠道，不要再加工。

### Step 5：投递（自己网站 + 企业微信）

`publish_digest.py` 把一份 spec 同时投递到两条渠道：使用当前用户 `DATABRAIN_TOKEN` 上传 HTML 到 **AI Gallery（visibility=self）**，回读链接写回底部 `查看完整列表`，并把 **markdown** 推送到**企业微信**机器人。

```bash
# 双渠道：上传网站 + 推企微（webhook 可多个，用 ; 分隔）
python scripts/publish_digest.py --input /tmp/spec.json \
  --webhook_url "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"

# 只预览渲染结果（不上传、不推送）
python scripts/publish_digest.py --input /tmp/spec.json --preview_only

# 只上传网站 / 只推企微
python scripts/publish_digest.py --input /tmp/spec.json --no_webhook
python scripts/publish_digest.py --input /tmp/spec.json --no_gallery \
  --webhook_url "$WEBHOOK_URL"
```

| 参数 | 默认 | 说明 |
|------|------|------|
| `--webhook_url` | 空 | 企微 Webhook，多个用 `;`；空则回退 env `WEBHOOK_URLS`，再空则只渲染不推 |
| `--preview_only` | - | 只渲染 markdown 打印，不上传不推送 |
| `--no_gallery` | - | 不使用当前用户 token 上传 AI Gallery（保留 spec 已有 `detail_url`） |
| `--no_webhook` | - | 不推企微 |
| `--html_dir` | `/tmp` | HTML 落盘目录 |
| `--detail_url_base` | 空 | 自托管网站时填 base URL 前缀，覆盖默认 AI Gallery |

> 网站投递走 `publish_gallery_html.py`，默认使用当前用户的 `DATABRAIN_TOKEN`，作品归属当前用户账号并保持 `visibility=self`。投递降级而不阻断：Gallery 失败保留本地 HTML 链接并继续推企微；企微推送超 4096 字自动分段。

**渠道与凭证（两条渠道权限模型不同，agent 需遵守）**：
- **AI Gallery（当前用户账号）= 自动、免批准**：HTML 渲染好之后默认使用当前用户的 `DATABRAIN_TOKEN` 上传，并保持 `visibility=self`。发布出的作品归属当前用户账号；若用户 token 没有 Gallery 创建/访问权限，自动降级为本地 HTML 链接。
- **企业微信 = 用户自己设置**：webhook 不随 skill 预置，必须是用户提供的 `--webhook_url` 或环境变量 `WEBHOOK_URLS`。**推送前必须先拿到用户提供的 webhook**；没有就只产出 markdown 预览（`--preview_only` 或省略 `--webhook_url`），不要伪造、猜测或在未确认的情况下用别的 webhook 强推。

## 两种输出格式对应渠道

| format | 用途 | 说明 |
|--------|------|------|
| `markdown` | 企微 / 飞书 / Slack / WorkBuddy | 这些聊天平台不渲染原始 HTML；`publish_digest.py` 推企微用它 |
| `html` | AI Gallery / 内部产品网页 | 自带样式，可直接嵌入展示；`publish_digest.py` 上传 Gallery 用它 |

## 设计要点

- **时间锚点**：以「调用时刻」为锚点向前回溯（默认 24h），不做「自然日 00:00–24:00」（避免割裂跨零点的热度）。
- **分榜呈现**：每平台一个榜，平台间互动量不可比（Reddit 1k 已爆款 / X 1k 中等），不做全局总榜。
- **入榜门槛**：各平台独立配置（见 `platforms.yaml`），避免冷门时段堆出「互动 50 的 Top 5」。
- **去重**：同事件最多 2 条 + 后裔补位 + 合并提示（你裁断，spec 落实）。
- **空平台隐藏**：0 帖平台整块跳过，两种 format 同步生效（渲染器负责）。
- **链接安全**：渲染器自动过滤非 http(s) 的恶意 url。

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABRAIN_TOKEN` | 是 | — | 认证 token 原始值（**不含** `Bearer ` 前缀），脚本自动拼接；不要写死在代码中 |
| `DATABRAIN_HOST` | 否 | 自动 fallback | API 主机；不设置时按 `databrain.woa.com → databrain.intlgame.com → databrain-global.intlgame.com` 顺序尝试（前两个内网需 VPN/SSO，外网自动 fallback 到 global）。显式设置仅用该地址，仅允许受信任域名 |
| `HOTPOSTS_QUERY_INTERVAL` | 否 | `3.0` | 全局请求节流（秒）；调小加速但更易触发 EdgeOne 限流 |
| `DATABRAIN_GALLERY_TOKEN` | 否 | — | 可选，仅当需要单独覆盖 Gallery 上传 token 时使用；默认直接复用当前用户的 `DATABRAIN_TOKEN` |
| `WEBHOOK_URLS` | 否 | — | 企业微信机器人 Webhook，多个用 `;` 分隔；命令行 `--webhook_url` 优先；**需用户自建机器人并提供**，skill 不预置 |

Token 为空时引导用户前往 `https://databrain.woa.com/v2/user-center/personal-tokens-center` 获取，设置 `DATABRAIN_TOKEN` 环境变量（不加 `Bearer`）。外网用 `https://databrain-global.intlgame.com/...`。

## 模块结构

| 文件 | 职责 |
|------|------|
| `scripts/make_daily_digest.py` | **取数主入口**：`--game_name` → game_id → 全平台 SQL → 候选 JSON（不去重/不渲染） |
| `scripts/render_digest.py` | **渲染器（格式真相源）**：digest_spec.json → markdown / html |
| `scripts/validate_digest.py` | **校验器**：渲染前校验 digest_spec 是否合 schema |
| `scripts/publish_digest.py` | **投递编排**：render → 上传网站(AI Gallery) + 推企业微信 + 打点 |
| `scripts/publish_gallery_html.py` | 使用当前用户 token 上传 HTML 到 AI Gallery，保持 `visibility=self`，回读 `display_url` |
| `scripts/report_log.py` | 打点上报 CLI：每次请求开始 agent 调一次 `-m "<用户原问题>"`（best-effort，token 缺失静默跳过） |
| `scripts/game_search.py` | 游戏名 → `unified_edition_id` 查询 |
| `scripts/query_executor.py` | 通用 SQL 执行器（host fallback / 限流退避 / 节流） |
| `scripts/dedup.py` | 同事件去重的**可选粗筛工具**（`fingerprint`）；最终裁断归 agent |
| `platforms.yaml` | 9 平台配置：channel_name 映射 / 入榜门槛 / 默认 Top N / game_id override |
| `references/digest_schema.md` | **digest_spec 产出契约**（你必读） |
| `references/sql_templates.md` | SQL 模板 + feeds 字段说明 + EdgeOne 关键字坑 |

## platforms.yaml 入榜门槛（§4.3.1）

| 平台 | channel_name | 入榜最低互动 |
|------|--------------|--------------|
| Reddit | `reddit` | 200 |
| X (Twitter) | `twitter` | 500 |
| YouTube | `youtube_keyword` | 1000 |
| TikTok | `tiktok` | 1000 |
| Discord | `discord` | 50 |
| 官方论坛 | `forumgamer` | 50 |
| Instagram | `instagram` | 300 |
| Facebook | `facebook` | 300 |
| Steam 社区 | `steam_community` | 50（默认 `enabled=false`，需 game_id override 启用） |

> Steam 不在产品 §4.3.1 门槛表内，为本 skill 扩展项，默认关闭以避免 PC/移动游戏返回大量低质 Steam 评论；通过 yaml `overrides` 按 game_id 启用。
> channel_name 已通过 PUBG Mobile / NIKKE 实测；查不到数据自动 skip + stderr 提示。

按 game 覆盖：

```yaml
overrides:
  ufc454d9b1af70b40588e2a6fa4da4a8b:
    platforms:
      reddit:
        min_engagement: 50      # 该游戏 reddit 社区小，调低门槛
    defaults:
      top_n: 3
```

## 不联网自检

```bash
python scripts/make_daily_digest.py --self_test   # 取数 + JSON 结构
python scripts/render_digest.py    --self_test    # markdown/html + 宽度截断
python scripts/validate_digest.py  --self_test    # spec 校验
python scripts/game_search.py      --self_test
python scripts/query_executor.py   --self_test
python scripts/dedup.py            --self_test    # 可选粗筛工具
python scripts/publish_gallery_html.py --self_test  # 网站上传（tags/url 构造）
python scripts/publish_digest.py   --self_test    # 投递编排（SSRF 白名单/分段/链接注入）
```

## 与其他 skill 的关系

- **依赖**：无。
- **数据源同源**：与 `databrain-opinion-metrics` 共享 feeds 表，遵循同样的 EdgeOne 黑名单约束。
- **投递自带**：`scripts/publish_digest.py` 直接把热帖投递到当前用户账号下的 AI Gallery（`visibility=self`）+ 企业微信，无需借用其他 skill。渲染产物也可手动喂飞书/Slack/WorkBuddy 或嵌内部网页。

## 参考

- digest_spec 产出契约：[references/digest_schema.md](references/digest_schema.md)
- SQL 模板与字段：[references/sql_templates.md](references/sql_templates.md)
- feeds 表字段权威表（含 EdgeOne 黑名单详情）：`databrain-opinion-metrics/references/feeds_templates.md`
