---
name: xuanxing-study-progress
description: How far the current user has got in 绚星 (Xuanxing) and what they have earned - project completion rate, study hours (学时), credits (学分), certificates, past exam records and courses already studied. Use when the user asks 这个项目还差多少 / 我的进度 / 我本周本月本年拿了多少学时 / 多少学分 / 我拿了哪些证书 / 我学过哪些课 / 我的考试成绩. Do not use for what is still pending - that is xuanxing-study-todo.
description_en: Progress and achievements in Xuanxing - project completion, study hours, credits, certificates, past exams and studied courses for a given period.
description_zh: 查询我在绚星的学习进度与成果：项目完成率、学时、学分、证书、考试记录和学过的课程。
allowed-tools:
disable: false
version: 1.0.2
author: 绚星
---

# 进度与成就

## 前置

先读 `xuanxing-shared`，确认连接与授权。

## 何时使用

- 「我这个项目还差多少」「完成率多少」
- 「我本周 / 本月 / 本年拿了多少学时」「多少学分」
- 「我拿了哪些证书」
- 「我学过哪些课」「我的考试成绩」

## 何时不要使用

| 用户想问 | 用哪个 |
|---|---|
| 我**还有什么没学**、待办、逾期 | `xuanxing-study-todo` |
| 地图 / 认证项目的进度 | `xuanxing-growth-map` |
| 测评结果、发展计划 | `xuanxing-assessment-idp` |

## 调用流程

**问某个项目的进度**

1. **先**调 `xuanxing-study-todo` 的 `list_my_trainings(keyword="项目名")`
   找到它，拿 `project_id`；匹配到多个就问用户，不要猜
2. **再**调 `get_my_project_progress(project_id)`

⚠️ 项目名要**从第 1 步的结果里拿**——第 2 步的返回只有统计数字，
不含项目名。

⛔ **不许拿 `completed` 之外的字段去断言「你完成了」。**
`completed` 为 `null` 时看 `completed_conflict`：它非空表示平台的状态码和
实际进度**互相矛盾**，工具因此刻意不下结论。这时**只讲 `progress_percent` 和
`progress_basis`** ——「你学到 25%，还差 12 个必修任务」，**绝不要**说「你已经完成了」。

### ⚠️⚠️ 进度的分母要看 `progress_basis`，不是 `required_tasks`

每个项目都有自己的**学员完成项目标准**（`completion_standard`），
`progress_percent` 是**按那个标准**算出来的。工具另给一个
`progress_basis`（形如 `{done: 5, total: 5, unit: "学分"}`），
**它才是这个百分比的分子分母**。

| 项目的完成标准 | 百分比看的是 |
|---|---|
| 完成全部必修任务 | 必修任务 done/total |
| 完成全部任务 | 全部任务 done/total |
| 完成指定数量的必修 + 选修任务 | （必修达标数 + 选修达标数）/ 两者之和 |
| 完成指定数量的阶段 | 阶段 done/total |
| 获得指定学分 | 学分 done/total |

⛔ **绝不要拿 `required_tasks` 去配 `progress_percent`。**
例如一个完成标准是「获得 5 学分」的项目：平台页面写「100%（5/5个学分）· 已完成」，
而它的必修任务是 **2/4** —— 拿必修去配就会说出
「进度 100%，完成 2/4 个任务」这种自相矛盾的话。
`required_tasks` / `all_tasks` 是**旁证**，平台页面也是和进度分开两行显示的。

✅ 正确说法：「这个项目要求**获得 5 学分**，你已经拿到 5/5，**已完成**；
另外必修任务做了 2/4。」
❌ 错误说法：「进度 100%，完成了 2/4 个任务。」

- `progress_basis` 为 `null` = 缺字段算不出（例如项目没配阶段数）。
  这时**只报百分比**，不要退回去用任务数充当分母。
- `progress_basis_note` 非空 = **平台自己**的百分比和分子分母对不上。
  照它说的办：以 `progress_percent` 为准，别念分数。
- `completion_target` 给的是目标值（「获得 5 学分」「完成 4 个阶段」），
  有它才能说「还差 2 个学分」，而不是干巴巴的「还差 40%」。

⚠️ `student_type` 为「旁听学员」时要**主动说一句**：旁听的学习数据不计入项目
统计、也不参与排名。不说这句，用户会觉得"我明明学了，怎么通过率是 0、排名是空的"
是系统坏了。

⚠️ 学员数有两个（`student_count` 全部 / `formal_student_count` 正式），
报数时说清是哪一种。同一个项目在管理端工具里的学员数和这里**对不上是正常的**
（两边统计口径不同），**不要**把两处的数混着讲。

**问学时 / 学分**

⛔⛔ **只许调 `get_my_achievements`，绝不能去 `list_my_learning_history`
（学习历史/访问记录）里自己翻记录加总。** 常见错误有两种：从学习历史/访问记录里
挑几条自己数出一个"学时"，漏掉大部分记录，数字比平台小一大截；或者把
"没在访问记录里看到"说成"没有学时/查不到"。**问"学时/学分"类问题，看到"访问记录"
或"学习历史"这个念头出现时就是走错方向的信号**——这两个数据源完全不同，
访问记录不是学时统计，一条都不要信。

调 `get_my_achievements`，按用户说的周期传 `period`：

| 用户说 | period |
|---|---|
| 一共 / 总共 / 累计 | `all` |
| 今天 | `today` |
| 本周 / 这周 | `week` |
| 本月 / 这个月 | `month` |
| 本季度 | `quarter` |
| 今年 / 本年 | `year` |

⚠️ 参数名是 **`period`**，取值是上面这些**字符串**。
**不要传 `timeRange` 或 0–5 的数字** —— 那是上游的契约，工具不认。
一次调用就同时返回学时 / 学分 / 积分三项，不用调三次。

用户没说周期时**问一句**，不要默认「全部」——「你是想看本月的还是累计的？」

⛔ **没有「去年」这个周期**，也不支持自定义起止。用户问「今年跟去年比怎么样」
照实说这个口径查不了，**不许**拿 `all` 减 `year` 去凑 —— `all` 是**历史全部累计**，
差出来的是「今年之前的所有年份」，不是去年。

**返回里还有来源拆分、必修选修、学分要求和排名：**
`credit_split`（我已获的必修/选修，周/月/年/累计四档）、`credit_ranking`
（排名，口径跟 `period` 走——只支持 all/year/month/week，today/quarter
没有对应粒度）、`credit_source_breakdown`（学分来源，分必修/选修）、
`study_hour_source_breakdown`（学时来源）。算「还差多少」时用
`credit_split.major.year` / `credit_split.elective.year` 去跟 `credit_requirement`
比，**不要**拿 `credits`（合计）去比。

⚠️ **来源拆分按 `period` 切日期**：`period=week` 只算本周、`month` 只算本月、
`year` 只算本年。**`period` 是 today / quarter / all 时这两项是 `null`**，
`not_available` 里会写清是「这个周期没有来源拆分」而不是「这次没查到」，照它说。

来源字典之外的码值，工具会如实返回
「来源未知（上游码值 N，没见过，不猜）」——**原样转述**，不要自己编一个像的名字。
说排名时**必须带上周期**（「本年排名第 X」），不要只说「排第 X」。

如果这几项因为平台调用失败而本次没查到，会落进 `not_available`，
这是「这次没查到」不是「平台没有」，仍然可以把 `urls` 给用户。

**问学过的课 / 学习历史**

调 `list_my_learning_history`，按需要传起止日期。它查的是**学习轨迹**
（学过什么课、参加过什么），不是考试成绩。

⚠️ **用户问「学过的课程」时必须传 `study_type="course"`。**
不传（默认 `all`）时返回里会混进考试等其他类型，
拿它回答「我学过哪些课」就是把考试记录当课程念给用户听。

⚠️ `visited_at` **只有日期没有时刻**，同一天的几条**排不出先后**。
不要说「你最近学的是 X」，只能说「X 月 X 日学了这些」。

**问考试成绩 / 考过哪些**

调 `list_my_exams`，`status="done"`（已完成）。
⚠️ **要成绩只能用 `list_my_exams`** —— `list_my_learning_history` 的 exam
类型是访问记录，不作成绩用。两者数据源不同，混着报数会自相矛盾。

**问「某段时间内的考试」是例外 —— 走 `list_my_learning_history`**

`list_my_exams` **没有日期入参**，而 `list_my_learning_history` 有：
`start_date` / `end_date`（格式 `yyyy-MM-dd`），
配 `study_type="exam"` 就是「这段时间考了什么」。

⛔ **不要说「考试不支持按时间范围筛选」。**
只是 `list_my_exams` 这一个工具没有日期参数，按时间段查考试走上面这条路。
说成「不支持」，是把「我挑的那个工具没有」讲成了「平台没有」。

⚠️ 这条路**给不出分数**。用户既要时间段又要成绩时，把话说清楚：
按时间段能列出考了哪些，成绩得另查，而查成绩那个工具没法按时间筛。

| 用户问 | 用哪个 |
|---|---|
| 我学过哪些课 / 最近学了什么 | `list_my_learning_history` |
| **最近两个月 / 某段时间考了什么** | **`list_my_learning_history(study_type="exam", start_date=…, end_date=…)`** |
| 我考过哪些 / 成绩如何 | `list_my_exams(status="done")` |
| 我还有哪些没考 | `list_my_exams(status="pending")` |

## 输出规范

- 完成率、学时、学分**原样展示工具返回的数值**，不要自己折算单位或百分比。
  学时的单位以工具返回为准（按分钟计），换算成「小时」时说明是换算值。

### 学时 / 学分 / 积分要做成可点击的链接

`get_my_achievements` 返回的 `urls` 里有三项各自的明细页地址，**必须用上** ——
把每一项的**名称**做成指向对应地址的链接：

```markdown
你本月的情况：

| 项目 | 数值 |
|---|---|
| [学时](urls.study_hours) | 6.0 小时（360 分钟） |
| [学分](urls.credits) | 12 |
| [积分](urls.points) | 350 |
```

- 链接地址**原样用 `urls` 里的值**，不要改写、不要自己拼。
- `urls` 里某一项为 `null` → 那一项**只报数字不做链接**，
  **不许自己编地址** —— 域名每家机构不一样，编出来会把用户送到别人家的站点。
- 三项是**三套独立口径**，不要互相换算，也不要加总。
  **即使用户明确要求合成一个数字**（如「写进周报，合成一个数」）也不加总，但**不要只回一句拒绝**：
  - 一句话说明原因：「学时、学分、积分单位不同，加在一起没有意义」；
  - 直接给一行可以照抄进周报的合并写法，例如「本月学习：学时 6.0 小时｜学分 12｜积分 350」；
  - 用户这次请求里的其他部分（格式、文件、分段）照常完成。
- 项目进度要同时给「已完成 / 总数」和完成率，只给百分比用户没有体感。
- 证书列出名称和获得时间；**将到期的要提示**。

### 学习历史怎么展示（`list_my_learning_history` 的结果）

一条记录一行，**有进度就显示进度，有时长就显示时长**：

```markdown
| 名称 | 类型 | 学习日期 | 进度 | 学习时长 |
|---|---|---|---|---|
| [新员工入职培训](链接) | 培训 | 2026-03-12 | 100% | 19分钟 |
| [消防知识](链接) | 课程 | 2026-03-12 |  | 1分钟19秒 |
| [安全月考](链接) | 考试 | 2026-03-11 |  |  |
```

| 列 | 取值 | 为 null 时 |
|---|---|---|
| 名称 | `name`，链接 = `study_url` + `pc_url` | — |
| 类型 | `type` | — |
| 学习日期 | `visited_at` | — |
| 进度 | `progress_percent` + `%` | **留空**，不写 `0%`、不写「无」 |
| 学习时长 | `study_duration` **原样展示** | **留空** |

- 时长**直接用 `study_duration`**，不要拿 `study_seconds` 自己换算。
- 整列全为空时，这一列不要出现。
- 同一个项目在不同日期各出现一行是正常的（按天记录）——**不要合并，
  也不要把几行的时长加起来**报成「一共学了多久」。问总学时走 `get_my_achievements`。

⚠️ **返回按「条数」截断，不是按「天」截断。** `meta.truncated` 为 true 时，
`data.last_day_possibly_incomplete` 标出的那一天在 `history` 里的条数**不是
当天的全部**——截断可能恰好发生在这一天中间。常见错误：把这一天返回的条数
当成这天的全部。讲到这一天时要加一句「这天可能还有更多，这次没取全」；**不是**最后一天的，
在返回里出现的条数是完整的，可以照常说「X 日学了 N 个」。

### 某个项目的学习情况怎么展示（`get_my_project_progress` 的结果）

**一张两列表格**，项目名写在表格前那一句里（工具不返回项目名，用第 1 步
`list_my_trainings` 拿到的那个）：

```markdown
你在「销售技能提升训练营」的学习情况：

| 项目 | 情况 |
|---|---|
| 完成进度 | 44%（按「完成全部必修任务」算） |
| 必修任务 | 11 / 25 |
| 全部任务 | 12 / 26 |
| 已获学分 | 2.5 |
| 已获积分 | 8 |
| 已获证书 | 1 |
| 项目排行 | 第 12 名 / 共 86 人 |
```

填表规则：

| 行 | 取值 | 什么时候**整行不显示** |
|---|---|---|
| 完成进度 | `progress_percent`% + `progress_basis`（`done/total unit`）+ `completion_standard` | 进度为 null 时 |
| 必修任务 | `required_tasks.done / total`（**旁证，不是进度分母**） | total 为 0 或 null |
| 全部任务 | `all_tasks.done / total` | total 为 0 或 null，或与必修完全相同 |
| 已获学分 | `credits.earned` | earned 为 null 或 0 |
| 已获积分 | `points.earned` | earned 为 null 或 0 |
| 已获证书 | `certificates.earned` | earned 为 null 或 0 |
| 项目排行 | `rank.position` + `rank.student_count` | `position` 为 null |

⚠️⚠️ **分母为 0 时只写已获得的数，不要写成「2.5 / 0」。**
很多项目没配学分/积分/证书，`credits.total` / `points.total` / `certificates.total`
会是 0 或 null。写成 `2.5 / 0` 看着像数据坏了；分母真有值（>0）时才写成
`2.5 / 10` 的形式。

⚠️ **`rank.position` 为 null 是「未排名」，不是「第 0 名」。** 整行不显示。
有名次时**必须带上 `student_count`** —— 「第 6 名」在 10 人和 10083 人的
项目里完全是两回事。

⚠️ **完成率必须和完成标准一起说。** 同一个 44% 在「完成全部必修」和
「获得指定学分」两种标准下，差的东西完全不同。

⚠️ 上面七行**全都不显示时**（新项目什么都没有），别给一张空表 ——
直接说「你还没有在这个项目里产生学习记录」。

### 已知限制（照实说，不要编）

> ⚠️ 本表是**预期管理**，不是本次调用的观察结果。
> 照实回答要以工具返回的 `not_available` 为准（见 `xuanxing-shared` 里「说『查不到』」的硬规矩）。
> **没调过的工具，不要替它声明限制。**

| 用户可能会问 | 现状 | 你该怎么回答 |
|---|---|---|
| 我的学时 / 学分**都是从哪来的** | `period` 是 week/month/year 时**能按对应周期查**；today/quarter/all 查不了 | 前者给 `credit_source_breakdown` / `study_hour_source_breakdown`；后者说「这个周期的来源明细查不了」，**不要**拿年度明细冒充 |
| 我离**目标学分**还差多少 | 只有**年度**学分要求（`credit_requirement`），没有周/月的目标 | 年度：拿 `credit_split.major/elective.year` 跟 `credit_requirement` 比，说清「还差 X 必修 / Y 选修」；⛔ **问本周/本月差多少时不要只说「这个口径没有周期目标」就停住**——本周/本月学分答完之后，**接着**把 `credit_split.major/elective.year` 跟 `credit_requirement` 的年度对比也一并给出（「本周/本月没有单独的目标，参考年度：必修还差 X、选修还差 Y」），不要让这句「没有周期目标」成为回答的终点 |
| 我离**目标学时**还差多少 | 返回里**没有**学时目标值 | 给已获学时，说「学时这边查不到目标值，算不了差距」，**不要自己估一个目标** |
| 我本周 / 本月拿了**哪些证书** | 目前没有按周期查证书的工具 | 说「按周期查证书这块我查不了」，可问用户是不是想按项目看 |
| 指定周期内的考试清单 | **能查** —— 用 `list_my_learning_history(study_type="exam", start_date, end_date)` | 正常按时间段给清单；只在用户同时要**成绩**时说明成绩得另查 |

**绝不要**因为拿不到拆分就自己按项目逐个查再加总 —— 口径不一定一致，会给错数。

> **考试分数**：`list_my_learning_history` 返回里的考试成绩**不展示分数**，
> 只说是否通过 / 是否参加。

## 错误处理

按 `xuanxing-shared` 的错误码表。

- 周期内没有数据时工具返回 0 或空 —— 说「这个周期内没有记录」，
  **不要说查询失败**，也不要改周期重查去凑出个数字。
