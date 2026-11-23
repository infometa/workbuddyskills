---
name: xuanxing-catalog-discovery
description: Find content the user has NOT joined yet on 绚星 (Xuanxing) - search the catalog for courses, knowledge, micro-courses, trainings, instructors and community posts, and list projects open for enrollment with remaining seats, deadlines and whether approval is needed. Use when the user asks 我想学XX / 有没有XX相关的课 / 帮我推荐课程 / 我能报什么项目 / 可参与的培训. There is NO personalized recommendation feed - a request for recommendations is handled by asking what topic they want, then searching. Do not use for work already assigned to them - that is xuanxing-study-todo.
description_en: Discover content not yet joined on Xuanxing - catalog search for courses, knowledge, micro-courses, trainings, instructors and community, plus projects open for enrollment (seats, deadlines, approval). No personalized recommendation feed; recommendation asks are served by topic search.
description_zh: 在绚星搜索我还没参加的课程、知识、微课、培训、讲师和社区内容，按主题帮我找能学的。
allowed-tools:
disable: false
version: 1.0.2
author: 绚星
---

# 内容发现与报名

## 前置

先读 `xuanxing-shared`，确认连接与授权。

## 何时使用

- 「我想学人工智能相关的课程」「平台上有没有讲沟通的课」
- 「帮我推荐几门课」（→ 先问方向，见下方调用流程）
- 「我可以参加哪些培训项目」「有什么能报名的」「我可参与的培训项目」
  ⚠️ **「可参与的」= 还没加入、可以去报名的，不是「正在参与的」。**
  常见错误：把这句话当成"已经在学的项目"查，答成"我已参与的 N 个培训"——
  答非所问。拿不准就按字面"可以去参与"理解，查 `list_enrollments`，
  不要改查 `list_my_trainings`。

## 何时不要使用

| 用户想问 | 用哪个 |
|---|---|
| **已经派给我**的项目 / 任务 / 考试 | `xuanxing-study-todo` |
| 我**学过**哪些课 | `xuanxing-study-progress` |
| 课程内容本身（「装饰器怎么写」） | 直接回答，不要查平台 |

**边界**：本技能只管「我还没参与、可以去选的」；已经在学的归 `xuanxing-study-todo`。

## 调用流程

**按关键词找内容** → `search_platform_contents(keyword, content_type)`

> ⚠️ 参数名是 **`content_type`**（下划线），取值**只有下表这 6 个**。
> 传任何其他值（比如 `course`、`teacher`、`enrollment`）工具会直接返回
> `INVALID_ARGUMENT`，**一次上游都不会调**。

| 用户想找 | content_type |
|---|---|
| **课程** / 知识 / 文档 | **`knowledge`** |
| 微课 | `micro` |
| 培训 | `training` |
| 讲师 | `lecturer` |
| 知识库 | `library` |
| 社区 / 问答 | `community` |

### 一次只搜一个类型

**用户说「课程」，就只调一次 `content_type=knowledge`，到此为止。**

- ❌ **不许**把其他类型也扫一遍去凑结果 —— 用户要课程，`training`/`micro`
  的结果他没要，列出来只会让「没找到」显得像是全平台都查过了。
- ❌ **不许**因为第一次搜是 0 条就换**类型**再搜。0 条就是 0 条，如实说。
- ✅ 但**可以换一次关键词**：关键词是英文缩写（AI / HR / PPT 这类）而结果是 0 条时，
  **换成中文全称再搜一次**（如「AI」→「人工智能」）—— 检索按中文分词，
  两个字母的英文缩写常常一条都命不中。**只换这一次**，不要把关键词越放越宽去凑结果。
  **条数一律照当次返回的 `meta.total` 说**，同一个词前后两次搜的条数也可能不同。
- 用户没说类型时，默认 `knowledge`。
- 明确说「培训项目」才用 `training`。
- ⚠️ **报名的问题不要用这个工具，用 `list_enrollments`**（见下一节）。
  `content_type` 没有报名类取值，报名数据不在检索服务里。
  **不要**换成 `training` 去凑 —— 培训搜索的返回里没有名额字段，
  拿它回答「还能报吗」就是用另一类数据冒充。
- 关键词原样传，不要自己扩写成一堆同义词。
- ⚠️ **`meta.truncated` 为 true 时，不许说"唯一""全平台只有""就这几条"这类
  穷尽性断言。** 常见错误：`meta.total` 有几百条，只看了前一页就说
  "……是唯一标题里含这个词的内容"——后面的条目根本没看过。
  正确说法是「这一页看到的是……」或「前 N 条里有这些」，`meta.total` 照实报，
  **不要**因为自己只看了一部分就暗示那就是全部。`meta.title_hit_count`
  统计的也**只是本页**，不是全量，同样不能拿它断言"全平台唯一"。

### 报名类问题 → `list_enrollments`（**不是** `search_platform_contents`）

| 用户问 | 怎么调 |
|---|---|
| 我能报名哪些 / 有什么能报的 / 哪些还有名额 | `list_enrollments(scope="open")` |
| XX 项目还能报吗 | `list_enrollments(scope="open", keyword="XX")` |
| 我报了哪些 / 我的报名审核过了吗 | `list_enrollments(scope="mine")` |

⚠️ **两个 scope 能答的问题不一样，不能互相顶替**（两侧返回的字段不一样）：

- **名额只有 `open` 侧有。** `mine` 侧名额字段一律是 null —— 那是「这一侧不给」，
  **不是**「不限名额」。要名额就换 `open` 再查一次。
- **「要不要审批」**：传 `with_audit_info=True` 才查（按条逐个查详情，N+1，默认关），
  返回干净的布尔 `need_audit`。
  用户问「报这个要审批吗」时才开这个参数，平时查名额/剩余座位不要带上它。
- **「什么时候截止」** 看 `deadline_unlimited`（只在 `scope="open"` 有）：
  **为 true 就是「长期有效，没有截止时间」**，直接这样回答 —— 平台报名中心卡片
  对这类活动显示的就是「申请时间：长期」，不是查不到。为 false 时
  `start_time`/`end_time` 的格式不保证读得对，照实说这边读不出具体日期、
  给链接让用户去页面看。`scope="mine"` 侧这个字段恒为
  `null`，不代表「我的报名」就是长期的，只是没有判断依据。
  **绝不要**拿 `published_at`（发布时间）冒充截止时间。
- `quota_unlimited` 为 true 是**不限名额**。⚠️ **绝不要**说成「0 个名额」
  或「已经报满了」—— 正好说反。
- `quota_remaining` 已经算好（上限 − 已报），直接用，不要自己再减一遍。
- `audit_status_raw` / `quota_type_raw` 是**原始码值**，没有含义对照表，
  **绝不许**猜它是「已审核」还是「待审核」——要「要不要审批」用 `need_audit`，
  不要用这两个码值猜。
- 每条都有 `url`（绝对短链），**做成链接给用户**去报名。
  本工具**不能替用户报名**。

### ⚠️ `ok: false` 不是「0 条」

拿到 `ok: false` 时，**这次查询根本没发生**。

**绝对不许**把它显示成「0 条」「没有找到」「平台上没有」——
那是在用一次失败的调用，向用户断言一个平台事实。
按 `xuanxing-shared` 的错误码表处理：`INVALID_ARGUMENT` 就按 `hint` 改对参数**重试**，
重试仍失败就说「我这边没查成」，**不要说「平台上没有」**。

**用户说「推荐」「有什么适合我的」** → 仍然走 `search_platform_contents`，
但**先问方向**。

本助手没有接入个性化推荐（没有对应工具），所以没有"猜他想学什么"的能力。
正确做法是问一句「你想往哪个方向学？比如沟通、数据分析、管理」，
拿到关键词再搜。

⚠️ **不要**自己挑几个热门词去搜了充当推荐，那是在冒充个性化；
也**不要**说「推荐功能没有」——用户要的是"帮我找点课"，这件事做得到，
只是需要他给个方向。

## 输出规范

- **有 `url` 的每条都要给可点击链接**，写成 Markdown：`[课程名](url)`。
  用户点了要能直接进学习平台的课程详情页。
  - `url` 已由工具拼好（机构域名 + `/kng/#/scan?kngId=<id>`），**原样用，不要改写**。
  - ⚠️ **只有 `knowledge` / `micro` 两类有 `url`。** 讲师、社区、知识库、培训
    一律是 `null`：那个链接模板是**知识详情页**的，它们的 id 不是 `kngId`，
    拼出来会把用户送到错的页面，而且点开之前看不出来。
  - `url` 为 `null` 时**只给标题**（可带作者 / 学院），**不许自己拼链接**——
    域名每家机构不一样，编出来会把用户送到别人家的站点；
    也**不要**说成「这个在平台上没有详情页」，那是另一回事。
- 结果按工具返回的顺序展示，**不要自己重排**——排序口径是平台定的。
  ⛔⛔ **更不许拿别的东西替换掉搜索结果**。常见错误：
  问"想学人工智能相关的课程"，工具已经按关键词搜回了结果，
  回答却列了"自己正在学的几个 AI 相关项目"——这不是排序错，是**答非所问**，
  用户要的是"可以去学的课"，不是"自己已经在学的"。拿到 `search_platform_contents`
  的结果后，前几条直接按原样展示，**不要**转头去查别的工具、也不要混入
  自己的判断去挑"更合适"的内容。
- 有 `study_status` 的，顺带标一下（未学习 / 学习中 / 已完成）；为 `null` 就不提，
  **不要当成「未学习」**。
- 一次给 5–8 条就够，太多用户看不完；说明还有多少条。
- 搜不到时如实说「没有找到相关的 X」，**不要放宽关键词再搜一遍去凑结果**，
  也不要把不相关的条目硬说成相关。

### 已知限制（照实说，不要编）

> ⚠️ 本表是**预期管理**，不是本次调用的观察结果。
> 照实回答要以工具返回的 `not_available` 为准（见 `xuanxing-shared` 的三条硬规矩）。
> **没调过的工具，不要替它声明限制。**

| 用户可能会问 | 现状 | 你该怎么回答 |
|---|---|---|
| 这些课是按什么排的 / 匹配度多少 | 检索按分词模糊匹配，单字也能命中；以本次返回为准，返回里没有相关度分字段时就是没有分值 | 说「只能按平台给的顺序展示」，**不要编分数**。看 `meta.title_hit_count`：为 0 时说「没搜到标题里带这个词的内容」，不要把一堆不相关的硬说成相关 |
| 这个项目还剩几个名额 | 用 `list_enrollments(scope="open")` | 给剩余名额 + 报名链接。⚠️ **不要**拿检索结果冒充，那里面没有名额 |
| 报名要审批吗 | 用 `list_enrollments(..., with_audit_info=True)` | 给 `need_audit`（true/false）。只在用户真问审批时才开这个参数 |
| 什么时候截止 | 看 `deadline_unlimited`：平台卡片对 null 起止时间显示的就是「申请时间：长期」 | `deadline_unlimited=true` 直接答「长期有效，没有截止时间」；为 false 才说这边读不出具体日期，给报名链接让用户去页面看。**不要**拿发布时间冒充截止时间 |
| 为什么推荐这门课 / 有按我的岗位推吗 | 助手没有个性化推荐 | 说清这些是按他给的关键词搜出来的，不是系统按他的画像推的，**不要编推荐理由** |

## 错误处理

按 `xuanxing-shared` 的错误码表。搜索无结果返回空列表是正常结果，不是错误。
