---
name: gaodun-job-selection
display_name: 公考选岗顾问
display_name_en: Gaodun Job Selection
description: 公考、事业编、教师编智能选岗与岗位查询。当用户说「推荐」「适合我」「帮我推荐」「我能报什么」「有什么好岗位」等推荐类话术时，根据考生条件（学历、专业、意向地区等）结合个人画像推荐适合报考的岗位，带推荐理由和推荐值；当用户说「查询xx的岗位」「查一下XX的职位」「XX有什么职位/岗位」「有哪些招考职位」「帮我看看xx地区的职位」等查询/浏览类话术时，以卡片列表展示招考职位（支持按职位名/招录单位名/企业名关键词模糊搜索，可按考试类型、地区、年份、报名状态筛选，卡片含职位名、招考人数、报名状态、工作单位、来源公告、专业标签，点击卡片可查看详情）；当用户说「帮我查下工资高的岗位」「工资高的岗位」「薪资高的岗位」「待遇好的岗位」「月薪5000以上的岗位」等薪资/工资/待遇类话术时按薪资筛选岗位；当用户查竞争比（报录比）、进面分数线时按对应维度筛选岗位。推荐场景条件不明确时先问清学历和意向地区两项。
description_zh: 按你的条件（学历、专业、意向地区等）智能推荐适合报考的岗位，会结合个人画像给出推荐理由和推荐值；也支持以卡片列表查询/浏览招考职位（按职位/企业名称关键词、考试类型、地区、年份、报名状态筛选，点卡片看详情），以及按竞争比、进面分、薪资（工资/待遇）筛选岗位。
description_en: Recommends suitable civil-service, public-institution, and teacher positions based on your qualifications (education, major, target area), with recommendation reasons and scores; also supports browsing positions as a card list (search by position/company keyword, filter by exam type, area, year, or application status; click a card for details), and filtering by competition ratio, interview cutoff score, or salary (pay/wage, e.g. "high-paying positions"). Ask for education and target area first when unclear.
category: 15-Education
version: 1.7.3
author: 上海高顿教育科技有限公司
agent_created: true
---

# 公考选岗顾问（gaodun-job-selection）

本技能负责**选岗相关工具的意图识别与派发**，根据用户话术路由到对应 MCP 工具：主入口为 `position_recommend`（个性化推荐）和 `recommend_jobs`（卡片式职位列表），另有竞争比、进面分、薪资三个专项查询工具，以及配套的 `open_job_detail`（打开职位详情侧栏）。`position_quick_search` 已下线，**不再使用**。

## 触发场景

**推荐类话术 → position_recommend**：用户说「推荐」「适合我」「帮我推荐」「我能报什么」「有什么好岗位」「哪些岗位适合我」等，或给出个人情况（学历、专业、意向地区等）希望得到"适合我"的岗位建议。推荐结果强调**个性化匹配**与**推荐理由**，而非精确条件过滤。

**查询/浏览类话术 → recommend_jobs**：用户说「查询xx的岗位」「查一下XX的职位」「XX有什么职位/岗位」「有哪些招考职位」「帮我看看xx地区的职位」等，想看**职位列表**时，以卡片形式在会话中展示招考职位（卡片含职位名、考试类型、招考人数、报名状态、工作单位、来源公告、专业标签、地区，点击卡片可在侧栏看详情）。用户查询里的**职位名、招录单位名、企业名**（如「教师」「税务局」「上海烟草」）作为 `positionName` 关键词模糊搜索传入；其余条件映射考试类型、地区、年份、报名状态。用户只报企业名查职位、不带「校招/实习」字样时，同样走本技能。

> ⚠️ **消歧规则**：「查/帮我查 + 岗位」句式里，查询对象是**维度词**时走专项工具，不走 recommend_jobs：「工资高/薪资/待遇」→ `salary_search`；「竞争小/报录比」→ `competition_ratio_search`；「进面分/分数线」→ `interview_score_search`。例：「帮我查下工资高的岗位」→ `salary_search`，不是 recommend_jobs。

## 工具路由（先判断意图，再选工具）

| 用户意图 / 触发话术 | 使用的工具 |
|---------|--------------|
| 推荐、适合我、帮我推荐、我能报什么、有什么好岗位等**综合推荐**意图 | `position_recommend` |
| 「查询xx的岗位/职位」「XX有什么职位」「有哪些招考职位」「看看xx地区的职位」等**查询/浏览职位列表**意图 | `recommend_jobs` |
| 查竞争比/报录比，如「竞争小的岗位」「报录比低于 50:1 的岗位」 | `competition_ratio_search` |
| 查往年进面分数线，如「进面分 120 以下的岗位」「分数线低的岗位」 | `interview_score_search` |
| 查薪资待遇（薪资/工资/待遇同义），如「帮我查下工资高的岗位」「月薪 5000 以上的岗位」 | `salary_search` |
| 想看某个职位的完整详情（`position_recommend` / 专项 3 工具返回的文本列表职位） | `open_job_detail`（`recommend_jobs` 卡片由用户点击打开，无需调用） |

用户意图属于**单一维度检索**（竞争比、进面分、薪资）时，优先使用对应专项工具，不要调 position_recommend。

## 工具文档索引

**调用任一工具前，先读对应文档**（入参、枚举取值、返回结构、注意事项均在文档内）：

| 工具 | 文档 | 一句话定位 |
|------|------|-----------|
| `position_recommend` | [tools/position-recommend.md](tools/position-recommend.md) | 个性化推荐，带推荐值（0-99）和推荐理由 |
| `recommend_jobs` | [tools/recommend-jobs.md](tools/recommend-jobs.md) | 卡片式职位列表，按职位/企业名关键词 + 考试类型/地区/年份/报名状态筛选，点击卡片看详情 |
| `open_job_detail` | [tools/open-job-detail.md](tools/open-job-detail.md) | 在右侧侧栏打开职位详情（报考要求、薪资、往年进面分/报录比等） |
| `competition_ratio_search` | [tools/competition-ratio-search.md](tools/competition-ratio-search.md) | 按竞争比（报录比）区间筛选岗位 |
| `interview_score_search` | [tools/interview-score-search.md](tools/interview-score-search.md) | 按往年进面分数线区间筛选岗位 |
| `salary_search` | [tools/salary-search.md](tools/salary-search.md) | 按薪资（月薪）区间筛选岗位 |

## 跨工具公共约定（强制遵守）

- **考试类型三套口径不通用**：`position_recommend` 用 `exam_type`（自然语言词，14 类，含军队文职/选调生/遴选/三支一扶/大学生村官）；专项 3 工具用 `project_id`（自然语言词，仅 9 类）；`recommend_jobs` 用 `examBizType`（**整数数组**，仅 1=公务员、2=事业单位、4=国企、5=银行，多选如 `[1,5]`）。跨工具复用取值前先核对各自文档
- **地区两套格式不通用**：`position_recommend` 的 `position_area_list` 与 `recommend_jobs` 的 `positionAreaList` 用标准地域串数组（如 `["安徽省"]`，带完整「省」「市」字样，省/市/区级均可）；专项 3 工具用 `region`（**省份简称字符串**，不带「省」「市」字样，如"上海"）。可选值：`国家`、`安徽`、`北京`、`福建`、`甘肃`、`广东`、`广西`、`贵州`、`海南`、`河北`、`河南`、`黑龙江`、`湖北`、`湖南`、`吉林`、`江苏`、`江西`、`辽宁`、`内蒙古`、`宁夏`、`青海`、`山东`、`山西`、`陕西`、`上海`、`四川`、`天津`、`西藏`、`新疆`、`云南`、`浙江`、`重庆`、`新疆兵团`
- **education 语义相反**：`position_recommend` 传**考生本人最高学历**；专项 3 工具传**岗位要求的学历**；`recommend_jobs` 无学历入参。勿混用
- **返回结构分两类**：`position_recommend` 与专项 3 工具返回 `{"total", "items", "note"}`，`note` 是给模型的处理提示，遵守但不展示给用户；`recommend_jobs` 返回一句话摘要 + 卡片数据（`structuredContent.jobs` 由前端渲染成卡片），模型**不要逐条复述卡片里的职位明细**
- **查多少显示多少（强制）**：`page_size` 传多少就**完整展示**多少条，**禁止多查之后只挑一部分展示**（用户翻下一页会错位）。用户想看更多 → 翻页重查：专项 3 工具与 `position_recommend` 传 `page+1`、`page_size` 保持不变；`recommend_jobs` 传 `pageNum+1`、`pageSize` 保持不变（卡片会渲染全部返回条目，查多少就显示多少）
- **专项查询的核心字段必显示（强制）**：调用了 `competition_ratio_search`，展示的每条岗位必须带竞争比（`competition_ratio`）；调用了 `interview_score_search`，必须带进面分（`interview_min_score`）；调用了 `salary_search`，必须带薪资（`salary_range`）。该字段值缺失时如实标注「暂无数据」，**即使整批全部缺失，该列也必须保留在输出里（禁止因空值整列省略），也不得为此换工具重查**
- **分页规则**：专项 3 工具 `page_size` 默认 10（最大 50）；`position_recommend` 的 `page_size` **固定传 5**（查 5 展示 5，不查多余的职位数据）；`recommend_jobs` 的 `pageSize` 默认 6（最大 50）
- **参数必须按声明类型传值，禁止字符串化**：数组参数（`position_area_list`、`certifications`、`examBizType`、`targetYearList`、`positionAreaList`、`recruitmentStatus`）传真正的 JSON 数组（`["安徽省"]`、`[1,5]`），禁止传 `"[\"安徽省\"]"`（数组序列化成字符串）或裸标量；数值参数（`page`、`page_size`）传数字（`1`、`10`），禁止传字符串（`"1"`、`"10"`）
- **本组工具均不返回学历要求、政治面貌要求、报名时间**，用户问到这些时说明需查阅招考公告原文，不要推测（专业要求仅 `recommend_jobs` 卡片有专业标签 `majorTag`，也仅为标签，具体以公告原文为准）
- **结果字段为空时如实告知，不得扩大查询范围**：岗位条目中进面分、竞争比、薪资、招录人数、推荐理由等字段为空，表示该岗位无此项数据——如实告知用户即可，不得估算补充，**也不得为补全该字段擅自放宽条件、扩大查询范围或改用其他工具重查**。（区别：「结果列表为空」= 一条岗位都没有，此时才建议放宽条件）
- **空结果重查上限：最多重新查询 2 次**：「结果列表为空」时可按建议维度放宽条件重查，**重查最多 2 次**（含首次查询累计不超过 3 次调用）。2 次重查后仍无结果必须停止查询，如实告知用户未搜到匹配岗位并请用户调整条件，**不得继续放宽、反复重试或改用其他工具反复尝试**
- **查看职位详情**：`recommend_jobs` 的卡片由用户点击（卡片或「查看详情」按钮），前端自动在侧栏打开详情，模型无需调用；`position_recommend` / 专项 3 工具返回的文本列表职位，用户想看详情时调用 `open_job_detail` 工具，入参 `jobId` 传该职位的 `position_id`。`open_job_detail` **仅支持公考招考类职位**
- **学历属硬性报考资格**，结果为空时建议放宽的维度是地区、关键词、区间值，**不得放宽学历**
- 服务异常时只以用户视角话术告知暂时无法获取数据（如「暂时没能获取到相关信息，请稍后再试」），不得向用户提及 MCP、接口、工具、服务异常等技术细节，不得基于推测提供任何岗位、推荐理由、分数线、报录比或薪资信息

## 禁止行为（强制遵守）

- ❌ **禁止引申工具不支持的参数/功能**：当用户提出工具不支持的需求时（如某种排序/筛选方式），不得说"试试XX参数/可以用XX"，应直接说明当前支持的选项
- ❌ **建议后续操作时禁止推荐别的工具或技能**：只说明操作本身，不得说"可使用XX工具/建议用XX技能/参考其他工具"（**例外**：用户想查看职位详情时，调用 `open_job_detail` 打开详情是允许的配套动作）
- ❌ **查询无结果时禁止暴露内部实现**：结果为空时只用用户视角话术告知未找到匹配结果（如「暂时没有找到匹配的岗位，建议调整条件后再试试」），禁止出现「接口未命中」「接口未返回数据」「数据源无数据」等任何提及接口、工具、MCP、服务或系统内部实现的表述
- ❌ **工具/MCP 未连接或调用异常时禁止告知用户**：不得向用户提及「MCP 未连接」「工具调用失败」「服务异常」「接口报错」等技术细节，只以用户视角话术回复（如「暂时没能获取到相关信息，请稍后再试」），也不得基于推测编造数据
