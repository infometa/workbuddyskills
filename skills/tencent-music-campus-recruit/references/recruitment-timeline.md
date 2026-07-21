<!-- 最后更新：2026-04-27 | 说明：本文件提供信息获取策略和引导话术 -->

# 招聘动态与流程信息获取策略

## ✅ 已实测：join.qq.com 公开 API（无需鉴权）

`scripts/fetch_recruit_info.py` 封装公告/宣讲会公开接口，`scripts/fetch_recruit_jds.py` 封装岗位列表与 JD 详情公开接口。**优先用脚本抓，不要用 WebFetch**（官网页面多为 SPA，HTML 里不一定有正文）。

| 命令 | 接口 | 方法 | 返回内容 |
|------|------|------|---------|
| `python scripts/fetch_recruit_info.py latest` | 公告+宣讲会一站式 | - | 最新公告标题/时间 + 近期宣讲会日程 |
| `python scripts/fetch_recruit_info.py notices` | `/noticeDynamic/getNoticeDynamicList` | GET | 公告列表（id/title/tag/time） |
| `python scripts/fetch_recruit_info.py notice <id>` | `/noticeDynamic/getNoticeDynamicById?id=xxx` | GET | 单条公告全文（HTML 转纯文本，含 FAQ） |
| `python scripts/fetch_recruit_info.py talks` | `/jointalk/getTalkList` | POST | 宣讲会日程（含线上直播+线下校园专场） |
| `python scripts/fetch_recruit_info.py families` | `/position/getPositionFamily` | GET | 岗位类别（软件开发/技术运营/产品类等） |
| `python scripts/fetch_recruit_jds.py all --max-pages 50 --page-size 100` | `/position/searchPosition` | POST | 无明确筛选条件时全量抓取官网岗位列表，避免只返回第一页 |
| `python scripts/fetch_recruit_jds.py search --keyword 后台` | `/position/searchPosition` + 本地字段匹配 | POST | 有明确关键词/筛选条件时搜索官网岗位列表；脚本会补充按招聘标签、项目名称等字段本地匹配，避免青云等标签漏召回 |
| `python scripts/fetch_recruit_jds.py detail <post_id>` | `/jobDetails/getJobDetailsByPostId` | GET | 官网完整 JD（描述/要求/加分项/工作地） |
| `python scripts/fetch_recruit_jds.py match "<简历文本>"` | 列表+详情组合 | GET/POST | 基于官网 JD 的岗位匹配候选 |

输出均为 JSON，可直接解析。

## 信息获取优先级

### 用户问"最新招聘动态/有什么公告/什么时候开始"

1. **首选**：调脚本 `python scripts/fetch_recruit_info.py latest`
2. 拿到公告列表后，根据用户问题选 1-2 条调 `notice <id>` 取全文
3. 用自然语言总结给用户（**不要直接贴 JSON**）
4. 末尾附原文链接：`https://join.qq.com/dynamic.html`

### 用户问"宣讲会什么时候/能不能看回放"

1. 调 `python scripts/fetch_recruit_info.py talks`
2. 按时间筛选近期场次，列出场次/时间/直播二维码或回放链接
3. 提醒：直播在腾讯招聘视频号

### 用户问"投递规则/制度细节"（如能否改志愿、笔试规则等）

1. 不查 MCP，不凭经验代答制度规则
2. 必须运行 `python scripts/fetch_recruit_info.py flow "<用户问题>" --question-time "<提问时间>" --top-k 3`，从 `join.qq.com/notice.html` 官网公告动态匹配依据
3. 回答前对比用户提问时间与公告发布时间，优先采用不晚于提问时间、发布时间更近且内容最匹配的公告；必要时再运行 `python scripts/fetch_recruit_info.py notice <id>` 获取原文
4. 规则未覆盖、可能随个人状态变化或涉及个人流程信息时，引导 `join.qq.com → 校招官网 offer 鹅智能体` 或 `campus@tencent.com` 获取最新官方口径

### 用户问"有什么岗位/某个岗位的JD/能推荐岗位吗"

1. **首选**：调 `scripts/fetch_recruit_jds.py` 从 `join.qq.com` 官网接口获取真实岗位/JD：
   - 搜索岗位：`python scripts/fetch_recruit_jds.py search --keyword <关键词> --page-size 10`
   - 看 JD 详情：`python scripts/fetch_recruit_jds.py detail <post_id>`
   - 按简历匹配：`python scripts/fetch_recruit_jds.py match "<简历或背景文本>"`
2. **仅受控内测且 JD MCP 可用时**：可选调 `campus-recruit-jd-qa` 工具辅助检索：
   - 通用搜：`search_jds(query=...)`
   - 按方向：`search_jds_by_direction(direction="技术|设计|产品|职能|市场", query=可选)`
   - 按招聘类型：`search_jds_by_recruit_type(recruit_type="应届毕业生|应届实习|日常实习|青云计划-应届生|青云计划-实习生|Pre留学生实习", query=可选)`
   - 按工作地：`search_jds_by_location(location=..., query=可选)`
   - 看 JD 详情：`get_jd_detail(position=..., recruit_type=可选)`
3. 用 MCP 或官网脚本返回的真实岗位、招聘部门、工作地作答，附投递链接，不凭经验编造岗位
4. 岗位详情页“招聘部门和工作地”模块来自官网接口 `/resume/getBGAndDepartmentListByPostId?postId=<post_id>`，不要用截图或经验补部门信息
5. 如涉及学校层级、院校标签或学历背景，只能作为中性客观信息和岗位匹配参考；不得对学校或学生做优劣、档次、含金量等价值评判
6. 仅当 MCP 和官网脚本均不可用或无命中时，再引导 `https://join.qq.com/post.html`

### 用户问"某个 BG/部门是做什么的/组织架构有哪些"

1. **首选**：调 `scripts/fetch_recruit_jds.py` 从 `join.qq.com/about.html` 对应接口获取真实组织架构与部门介绍：
   - 全量组织架构：`python scripts/fetch_recruit_jds.py orgs`
   - 搜部门或关键词：`python scripts/fetch_recruit_jds.py department --keyword <关键词>`
   - 按 BG 搜索：`python scripts/fetch_recruit_jds.py department --bg <BG关键词>`
2. 回答只基于接口返回的 `bg_name`、`department_name`、`introduction`，不要凭经验补部门职责。
3. 无命中或接口失败时，引导 `https://join.qq.com/about.html`，不要编造组织架构或部门介绍。

## 引导话术

### 用户问"招聘流程/时间/最新公告"

```
我帮你抓一下官网最新动态——
[执行 python scripts/fetch_recruit_info.py latest]
[根据返回 JSON，用自然语言总结公告标题、发布时间、关键信息]
[必要时再调 notice <id> 取全文]

具体投递规则建议在 join.qq.com 上问「校招官网 offer 鹅智能体」，制度调整以官方答复为准。
原文：https://join.qq.com/dynamic.html
```

### 用户问"宣讲会"

```
我看看近期宣讲会安排——
[执行 python scripts/fetch_recruit_info.py talks]
[按日期排序，列出场次、时间、类型（直播/线下）、直播二维码]

直播都在腾讯招聘视频号，错过可以看回放。
```

### 用户问"有什么岗位"

```
[如果用户没有提供关键词、方向、城市、招聘类型、BG 或简历背景等筛选条件，先执行：python scripts/fetch_recruit_jds.py all --max-pages 50 --page-size 100]
[基于全量岗位结果按招聘类型/方向/工作地做汇总，避免只抓第一页导致岗位不全]
[如果用户已有明确筛选条件，再运行 scripts/fetch_recruit_jds.py search/detail/match 从官网接口获取真实岗位；仅受控内测且 JD MCP 可用时，才用 campus-recruit-jd-qa 辅助检索]
[用表格列出 3-5 个与同学简历/背景最符合的真实校招岗位；如果用户要求全部岗位，先分组摘要，再询问要展开哪类]

| # | 岗位名称 | 招聘部门 | 工作地 | 匹配理由 | 投递链接 |
|---:|---------|----------|--------|----------|----------|
| 1 | **官网脚本/可选 JD MCP 返回的岗位名称** | 官网脚本/可选 JD MCP 返回的招聘部门 | 官网脚本/可选 JD MCP 返回的工作地 | ① 课程/项目经历对口<br>② 技能关键词匹配 JD 要求<br>③ 城市/实习类型偏好一致 | [点击投递](官网脚本/可选 JD MCP 返回的投递链接) |

[岗位名称加粗；匹配理由可写 2-3 个短点并用 `<br>` 换行；链接统一显示为"点击投递"]
[不出现评分、分数、匹配度百分比、排名算法等内容]
[结尾问："要不要看某个岗位的完整 JD？或者按方向/城市再筛一下？"]

如 MCP 和官网脚本都未命中，再引导：
🔗 https://join.qq.com/post.html （登录后筛选）
🤖 也可以问「校招官网 offer 鹅智能体」当前有什么在招
```

### 脚本抓取失败时的兜底

```
官网接口暂时没响应（可能是网络问题）。你可以直接看：
🔗 https://join.qq.com/dynamic.html — 招聘动态页
🤖 join.qq.com 右下角「校招官网 offer 鹅智能体」— 实时问答
📱「腾讯招聘」公众号 — 最新公告推送

面试准备和简历相关我可以直接帮你，要先聊这块吗？
```

## 重要约束

- **不要硬编码具体日期/批次/岗位名称**：所有时间敏感信息一律走脚本现拉
- **不要直接把 JSON 丢给用户**：用自然语言总结，提取关键字段
- **公告全文较长**：按用户问题截取相关段落，不要全文贴回
- **接口偶发返回 data=null**：脚本已做保护，遇到空数据走兜底话术
