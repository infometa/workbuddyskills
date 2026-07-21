---
name: tencent-survey
description: "腾讯问卷（wj.qq.com）MCP Skill。涉及「问卷」「调查」「表单」「投票」「考试」「测评」「wj.qq.com」等操作时使用。支持能力：(1) 获取问卷详情（标题、设置、页面、题目、选项完整结构 + 纯文本 DSL）(2) 使用纯文本创建问卷（text 必填，支持指定场景/指定项目）(3) 更新问卷中的单个题目（DSL 格式）(4) 获取问卷回答列表（支持游标分页）。支持场景：调查(1)、考试(3)、测评(6)、投票(8)。"
---

# 腾讯问卷 MCP Skill

腾讯问卷 MCP Skill 提供问卷查询、创建、编辑与回答查看能力，通过 MCP 协议直接调用工具操作问卷系统。

## 调用方式

所有工具通过 MCP function call 直接调用：

```json
{"name": "get_survey", "arguments": {"survey_id": 12345}}
{"name": "create_survey", "arguments": {"text": "员工满意度调查\n\n1. 您对工作环境是否满意？[单选题]\n非常满意\n满意\n一般\n不满意"}}
{"name": "update_question", "arguments": {"survey_id": 12345, "question_id": "q-1-abcd1234", "text": "您的性别[单选题]\n男\n女\n其他"}}
{"name": "list_answers", "arguments": {"survey_id": 12345}}
```

---

## 触发场景

### 明确触发

以下情况应直接激活本 skill：
- 用户提到「问卷」「调查」「表单」「投票」「考试」「测评」等关键词
- 用户提供了 `wj.qq.com` 链接
- 用户说「帮我做个调查」「创建一个投票」等

### 模糊场景

| 用户表述 | 判断方式 |
|---------|---------|
| 「帮我做个投票」 | 直接使用，scene=8 |
| 「做个考试」 | 直接使用，scene=3 |
| 「做个测评」 | 直接使用，scene=6 |
| 「收集一下大家的意见」 | 直接使用，scene=1（调查） |
| 「我有个问卷链接…」 | 解析链接提取 survey_id，调用 get_survey |
| 「修改问卷的第X题」 | 先 get_survey 获取 question_id，再 update_question |
| 「看看问卷的回答」 | 调用 list_answers，注意翻页获取全部数据 |
| 「问卷收了多少份」 | 调用 list_answers 查看 total 字段 |

---

## 工具列表

| 工具名称 | 功能说明 | 参考文档 |
|---------|---------|---------|
| `get_survey` | 获取指定问卷的详细信息（标题、设置、页面、题目、选项 + 纯文本 DSL） | `references/get_survey.md` |
| `create_survey` | 使用纯文本创建问卷（text 必填，支持指定场景/指定项目） | `references/create_survey.md` |
| `update_question` | 更新问卷中的某一道题目（需先获取 question_id） | `references/update_question.md` |
| `list_answers` | 获取问卷的回答列表（支持游标分页） | `references/list_answers.md` |

---

## URL 解析规则

问卷投放链接格式为 `https://wj.qq.com/s2/{survey_id}/{hash}`

当用户提供链接时，取路径第二段为 `survey_id`：

| URL 格式 | 提取方式 | 示例 |
|----------|---------|------|
| `wj.qq.com/s2/{id}/{hash}` | 取路径第二段 | `wj.qq.com/s2/292192/abc1` → `292192` |

> 提取到 `survey_id` 后，调用 `get_survey(survey_id=...)` 获取问卷详情。

---

## 数据模型

```
问卷（Survey）
├── 基本信息：id, hash, title, scene, state
├── 设置：prefix(欢迎语), suffix(结束语), started_at, end_at ...
├── 项目：project { id, name }
├── 纯文本内容：text（DSL 格式，包含标题和所有题目）
├── 页面列表（Pages[]）
│   └── 题目列表（Questions[]）
│       ├── 基本属性：id, type, sub_type, title, required
│       ├── 选项列表（Options[]）：id, text, exclusive
│       ├── 量表属性：starBeginNum, starNum
│       ├── 矩阵子问题：subTitles[]
│       └── 联动层级：levels[], groups[]
└── 回答列表（Answers[]）← 通过 list_answers 获取
    ├── 基本信息：answer_id, respondent_nickname, started_at, ended_at
    ├── 地理信息：country, province, city
    └── 回答内容（answer[]）
        └── 页面 → 题目回答 { id, type, text, options, blanks, groups }
```

> 核心嵌套：`Survey → Pages[] → Questions[] → Options[]`
> 回答嵌套：`Answer → answer[] (Pages) → questions[]`

---

## 问卷场景

| scene | 场景 | 说明 |
|-------|------|------|
| **1** | **调查** | **默认值**，通用问卷调查 |
| 3 | 考试 | 带评分的考试问卷 |
| 6 | 测评 | 测评类问卷 |
| 8 | 投票 | 投票类问卷 |

---

## 核心工作流

### 查看问卷详情

```
1. 从用户提供的链接或 ID 获取 survey_id（链接解析见上方）
2. 调用 get_survey(survey_id=...) 获取问卷详情
3. 递归解析 pages → questions → options 嵌套结构
4. 向用户展示问卷标题、题目列表等信息
```

### 创建问卷

```
1. 根据用户需求判断 scene：调查(1)、考试(3)、测评(6)、投票(8)
2. 按问卷文本语法组织 text 内容（语法详见 references/create_survey.md）
3. 如果用户指定了项目，传入 project_id
4. 调用 create_survey 创建问卷
5. 从返回结果取 survey_id 和 hash，拼接投放链接告知用户：
   https://wj.qq.com/s2/{survey_id}/{hash}
6. 可选：调用 get_survey 确认问卷结构
```

### 更新问卷题目

```
1. 调用 get_survey(survey_id=...) 获取问卷详情
2. 从返回的 pages → questions 中找到目标题目的 id（格式如 q-1-xxxx）
3. 参考返回的 text 字段了解当前问卷的 DSL 格式
4. 按 DSL 语法编写新的题目文本（只写这一道题）
5. 调用 update_question(survey_id=..., question_id=..., text=...) 更新
6. 可选：再次调用 get_survey 确认更新结果
```

### 查看问卷回答

```
1. 调用 list_answers(survey_id=...) 获取首页回答
2. ⚠️ 注意翻页：如果 list.length == per_page，可能还有下一页：
   - 将返回的 last_answer_id 作为下一次请求的参数
   - 继续调用 list_answers(survey_id=..., last_answer_id=...)
   - 直到 list.length < per_page 表示已到最后一页
3. 解析每条回答的 answer 字段（嵌套结构：页面 → 题目回答）
4. 向用户展示回答汇总或详情
```

---

## 文本语法速查（create_survey / update_question）

### 基础结构

```
问卷标题

问卷引导语（可选）

题目标题[题型](描述)
选项/内容
```

- 第一行为**问卷标题**（仅 create_survey 需要）
- 题目之间用空行分隔
- `=== 分页 ===` 插入分页符

### 题型语法

| 题型 | 语法 |
|------|------|
| 单选题 | `标题[单选题]\n选项A\n选项B` |
| 多选题 | `标题[多选题]\n选项A\n选项B` |
| 下拉题 | `标题[下拉题]\n选项A\n选项B` |
| 排序题 | `标题[排序题]\n选项A\n选项B` |
| 单行文本题 | `标题[单行文本题]` |
| 多行文本题 | `标题[多行文本题]` |
| 多项填空题 | `标题[多项填空题]\n填空1：____` |
| 量表题 | `标题[量表题]\n1~5` |
| 日期时间题 | `标题[日期时间题]` |
| 附件题 | `标题[附件题]` |
| 段落说明 | `描述内容[段落说明]` |
| 矩阵单选题 | `标题[矩阵单选题]\n选项A 选项B\n子问题1\n子问题2` |
| 矩阵量表题 | `标题[矩阵量表题]\n1~5\n子问题1\n子问题2` |
| 联动题 | `标题[联动题]\n第一层 第二层\n答案A+子答案A1\n答案B+子答案B1` |

### 题目设置

| 设置 | 语法 |
|------|------|
| 必答 | `[必答]` |
| 选答 | `[选答]` |

### 考试场景专用（scene=3）

| 设置 | 语法 |
|------|------|
| 答案 | `[答案：A、B]` |
| 分值 | `[分数：5]` |
| 全部正确得分 | `[全部]` |
| 部分正确得分 | `[部分]` |
| 人工评分 | `[人工]` |

额外题型：`[判断题]`、`[不定项选择题]`、`[问答题]`

### 测评场景专用（scene=6）

选择题用 `[测评单选题]`、`[测评多选题]` 替代普通题型。

---

## 注意事项

- **title 可能含 HTML 标签**：`get_survey` 返回的 `title` 可能含 `<p>`、`<br>` 等，展示前需清理
- **text 参数格式**：JSON 中换行使用 `\n`，选项不需要字母前缀（写 `满意` 而非 `A. 满意`）
- **题目内不允许空行**：一道题的标题和选项之间不能有空行
- **update_question 需先获取 question_id**：必须先调用 `get_survey`，不能自行构造
- **list_answers 需要翻页**：超过 `per_page` 条时必须循环调用
- **非幂等写操作**：`create_survey` 每次调用都会创建新问卷，`update_question` 会覆盖原题目

---

## 错误速查

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| `missing_token` | 未携带 Token | 检查 MCP 配置中的 Authorization header |
| `invalid_token` | Token 不存在或已撤销 | 重新获取 Token |
| `token expired` | Token 已过期 | 重新授权 |
| `claim_error` | 问卷不属于当前团队 | 确认问卷 ID 与 Token 绑定的团队一致 |
| `invalid_text_format` | 文本格式错误 | 检查 DSL 语法 |
| `survey_not_editable` | 问卷不可编辑 | 问卷可能在回收中，需先暂停 |
