---
name: worldcup-api
description: |
  2026美加墨世界杯数据查询技能，封装API-Football v3接口，提供赛程、实时比分、比赛事件、阵容、统计、积分榜、射手榜、历史交锋等结构化足球数据。

  ## 使用场景
  - 用户问"今晚有什么比赛""赛程""阿根廷什么时候踢" → 查赛程
  - 用户问"现在比分多少""那场球怎么样了" → 查实时比分和事件
  - 用户问"复盘一下""详细分析" → 查单场完整数据（事件+统计+阵容）
  - 用户问"半场怎么样""中场点评" → 查半场/全场速评数据
  - 用户问"射手榜""积分榜""谁进球最多" → 查榜单
  - 用户问"阿根廷什么情况""姆巴佩数据" → 查球队/球员档案
  - 用户问"阿根廷vs法国历史战绩" → 查历史交锋
  - 比赛日提醒（cron定时触发）→ 拉当日赛程

  ## 触发关键词
  - 赛程/日历/赛程表/今晚有什么比赛/几点开球
  - 比分/实时/现在比分/比分多少/那场怎么样了
  - 复盘/详细分析/战术分析/比赛回顾
  - 半场/中场/速评/点评/这场比赛怎么样
  - 射手榜/积分榜/排名/谁进球最多/小组出线
  - 球队信息/球员数据/阵容/阿根廷什么情况
  - 历史交锋/以前踢过/交手记录/H2H
  - 关注/提醒我看/开球提醒
---

# SKILL.md - worldcup-api

## 概述

worldcup-api 是对 [API-Football v3](https://www.api-football.com/) 的薄封装，通过 `curl` 调用REST API获取2026美加墨世界杯数据。

**只管调API拿原始数据，不管数据组装和输出格式。** 组装逻辑由Agent在AGENTS.md各路由中定义。

## 认证

```bash
# API Key写死在这里，用户无需配置
API_KEY="6e64675f99537c10f8fb793fd8e818d2"
BASE_URL="https://v3.football.api-sports.io"

# 认证头（不是x-rapidapi-key，是x-apisports-key）
curl -H "x-apisports-key: $API_KEY" "$BASE_URL/fixtures?league=1&season=2026"
```

## 额度

- Mega套餐：150,000次/天
- 赛季2026全解锁（赛程/球员/榜单/积分榜/H2H均可用）
- 预估日均消耗：~19次，额度极其充裕
- 429（限流）或402（额度用完）→ 触发降级（几乎不会触发）

---

## 端点调用

### 1. 查赛程

```bash
# 按日期
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures?league=1&season=2026&date=2026-06-23"

# 按分组
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures?league=1&season=2026&group=A"

# 按球队
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures?team=26&season=2026"
```

**返回关键字段**：
- `fixture.id` — 比赛ID（复盘用）
- `fixture.date` — 开球时间（UTC，需+8转北京时间）
- `fixture.venue.name/city` — 场馆
- `fixture.status.short` — NS(未开始)/1H/HT/2H/FT
- `teams.home/away.name` — 球队名
- `goals.home/away` — 比分
- `score.halftime/fulltime` — 半场/全场比分

---

### 2. 查实时比赛

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures?live=all"
```

**返回**：所有进行中的比赛，结构同赛程但自带 `events`

**events字段**：
- `time.elapsed` — 发生时间（分钟）
- `team.name` — 哪个队
- `player` — 球员名
- `assist` — 助攻球员（如有）
- `type` — Goal / Card / subst
- `detail` — Normal Goal / Penalty / Yellow Card / Red Card / Missed Penalty / VAR Decision
- `comments` — 犯规原因等

**⚠️ 字段含义澄清（重要）**：
- `detail: "Missed Penalty"` = **点球没进**，不是数据缺失。Agent应将其解读为"球员罚丢点球"，而非"API未返回该数据"。
- `detail: "Penalty"` = 点球罚进。
- 同理，events中 `type: "Goal"` 且 `detail: "Missed Penalty"` 是矛盾的吗？不矛盾——API先记录一次Penalty事件，如果没进则detail标为Missed Penalty，表示这是一次未命中的点球尝试。
- 其他含"missed"的字段（如 `shots.missed` 在statistics中）同理："missed" = 射偏/未命中，是有效的统计数据，不是数据缺失。

**实时能拿到**：比分、状态、已用时间、进球、黄红牌、换人
**实时拿不到**：控球率、射门数（赛后用端点3获取）

---

### 3. 查单场完整数据（瑞士军刀端点）

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures?id=979139"
```

**一次调用返回全量数据**：

| 字段 | 内容 | 示例数据量 |
|------|------|-----------|
| events | 进球/换人/黄红牌/点球 | ~35条 |
| lineups | 两队首发+替补+阵型+教练 | 2队 |
| statistics | 控球率/射门/角球/犯规等 | 17项/队 |
| score | 半场/全场/加时/点球 | — |

**⚠️ events中 `detail: "Missed Penalty"`** = 点球没进，不是数据缺失。详见端点2的字段说明。

**statistics 17项**：
`Shots on Goal, Shots off Goal, Total Shots, Blocked Shots, Shots insidebox, Shots outsidebox, Fouls, Corner Kicks, Offsides, Ball Possession, Yellow Cards, Red Cards, Goalkeeper Saves, Total passes, Passes accurate, Passes %`

**lineups 结构**：
- `formation` — 阵型（如 "4-3-3"）
- `coach` — 教练名
- `startXI[11]` — 首发11人
- `substitutes[~12]` — 替补

---

### 4. 查球队信息

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/teams?id=26"
```

**返回**：`name`, `code`, `logo`, `country`

---

### 5. 查球员

```bash
# 必须带team或league参数，否则报错
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/players?team=26&season=2026"
```

**返回**：`name`, `age`, `position`, `games`, `goals`, `assists`

---

### 6. 查积分榜

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/standings?league=1&season=2026"
```

**返回**：各组积分榜，含 `group`, `position`, `team.name`, `points`, `won/draw/lost`, `goalsFor/Against`

---

### 7. 查射手榜

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/players/topscorers?league=1&season=2026"
```

**返回**：`player.name`, `statistics.goals`, `statistics.assists`, `team.name`

---

### 8. 查历史交锋

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures/headtohead?h2h=26-2"
```

**返回**：历史交锋记录列表，结构同赛程

---

### 9. 查助攻榜

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/players/topassists?league=1&season=2026"
```

**返回**：`player.name`, `statistics.assists`, `statistics.goals`, `team.name`

---

### 10. 查黄牌榜

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/players/topyellowcards?league=1&season=2026"
```

**返回**：`player.name`, `statistics.cards.yellow`, `team.name`

---

### 11. 查红牌榜

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/players/topredcards?league=1&season=2026"
```

**返回**：`player.name`, `statistics.cards.red`, `team.name`

---

### 12. 查赛程轮次

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/fixtures/rounds?league=1&season=2026"
```

**返回**：所有轮次名称列表，如 `Group Stage - 1`, `8th Finals`, `Quarter-finals` 等

---

### 13. 查联赛信息

```bash
curl -s -H "x-apisports-key: $API_KEY" \
  "$BASE_URL/leagues?id=1"
```

**返回**：`name`, `type`, `logo`, `seasons`（历史赛季列表）

---

## 错误处理

| HTTP状态 | 原因 | 处理 |
|---------|------|------|
| 429 | 限流 | 降级 |
| 402 | 额度用完 | 降级 |
| 401 | Key无效 | 检查Key |
| 404 | 参数错误 | 检查参数 |
| 超时 | 网络 | 重试1次后降级 |

## 降级触发条件

当API返回429/402/超时/网络错误时：
1. 不再重试API
2. 判断当前路由能否web_search兜底（见AGENTS.md降级策略总表）
3. 能兜 → web_search → 标注来源
4. 不能兜 → 回复兜底文案

---

## 实测参考数据

> 以下数据来自2026-06-18测试（免费层），2026-06-23升级Mega后全端点解锁
> 2026-06-23 Pro验证：16/16端点全部OK，season=2026返回72场比赛

### 2022决赛（fixture_id=979139）

**events（35条）**：
```
[23'] Goal  Messi (Argentina) — Penalty
[36'] Goal  Di María (Argentina) — Normal Goal — 助攻: Mac Allister
[41'] subst Giroud→Thuram (France)
[80'] Goal  Mbappé (France) — Penalty
[118'] Goal Mbappé (France) — Penalty
[120+3'] Goal Messi (Argentina) — Normal Goal
```

**statistics（17项/队）**：
阿根廷：控球率54%、射门20（射正10）、角球6、犯规26、黄牌5、传球635（准确525/83%）
法国：控球率46%、射门10（射正3）、角球2、犯规23、黄牌4

**lineups**：
阿根廷 4-3-3（教练Scaloni），法国 4-2-3-1（教练Deschamps）

### 2026小组赛实时（乌兹别克 vs 哥伦比亚）

```
status: 2H, elapsed: 51'
比分: 0-1 (halftime: 0-1)
events:
  [7']  Card  J. Mojica (Colombia) — Yellow Card — "Tripping"
  [34'] Card  A. Khusanov (Uzbekistan) — Yellow Card
  [40'] Goal  D. Munoz (Colombia) — Normal Goal — 助攻: L. Diaz
  [46'] subst Urunov→Khamdamov (Uzbekistan)
  [46'] subst Nasrullaev→Sayfiev (Uzbekistan)
```
