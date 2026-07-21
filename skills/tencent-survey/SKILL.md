---
name: tencent-survey
description: 腾讯问卷（wj.qq.com）- 在线问卷调查平台。涉及「问卷」「调查」「表单」「投票」「考试」「测评」「wj.qq.com」等操作时优先使用。支持能力：(1) 获取问卷详情（标题、设置、页面、题目、选项完整结构 + 纯文本 DSL + 自定义逻辑）(2) 使用纯文本创建问卷（text 必填，支持指定场景/指定项目）(3) 更新问卷中的单个题目（DSL 格式）(4) 获取问卷回答列表（支持游标分页）(5)
  更新问卷自定义逻辑（条件显示/隐藏、跳转、替换、随机排序等）。支持场景：调查(1)、考试(3)、测评(6)、投票(8)。
description_zh: 腾讯问卷操作（创建、修改、逻辑设置、统计）
description_en: Tencent Survey operations (create, edit, logic settings, view statistical analysis of various surveys)"
version: 1.1.1
homepage: https://wj.qq.com
metadata:
  clawdbot:
    primaryEnv: TENCENT_SURVEY_TOKEN
    category: tencent
    tencentTokenMode: custom
    emoji: 📋
---

# SKILL 更新

每天使用 SKILL 前进行一次更新检查，按照如下的步骤执行:

1. **查看当前版本version**：读取本文件顶部 frontmatter 中的 `version` 字段；格式为 MAJOR.MINOR.PATCH
2. **查看最新版本latest**：通过命令获取最新版本信息`latest`，输入参数 `current_version` 为上一步获取的当前版本
```bash
mcporter call tencent-survey "check_skill_update" --args '{"current_version": "当前版本"}'
```
JSON 格式数据返回，返回参数示例：
- `has_update`: 是否有更新（true/false）
- `latest`: 最新版本号，格式为 MAJOR.MINOR.PATCH
- `current_version`: 当前传入的版本号
- `release_note`: 最新版本发布说明
- `instruction`: 更新指令

3. **更新版本**：如果 `has_update` 为 true（即当前版本`current_version`低于最新版本`latest`），则遵循 `instruction` 指令进行更新，或提示用户更新

# 腾讯问卷 MCP 使用指南

腾讯问卷 MCP 提供问卷查询、创建、编辑与回答查看能力，让 AI 助手可以直接操作问卷系统。

## 触发场景

### 明确触发

以下情况应直接激活本 skill：
- 用户提到「问卷」「调查」「表单」「投票」「考试」「测评」等关键词
- 用户提供了 `wj.qq.com` 链接
- 用户说「帮我做个调查」「创建一个投票」等

### 模糊场景

| 用户表述 | 判断方式 |
|---------|---------|
| 「帮我做个投票」 | 直接使用本 skill，scene=8 |
| 「做个考试」 | 直接使用本 skill，scene=3 |
| 「做个测评」 | 直接使用本 skill，scene=6 |
| 「收集一下大家的意见」 | 直接使用本 skill，scene=1（调查） |
| 「我有个问卷链接…」 | 解析链接提取 survey_id，调用 get_survey |
| 「修改问卷的第X题」 | 先 get_survey 获取 question_id，再 update_question |
| 「设置跳题逻辑」「设置显示逻辑」 | 先 get_survey 获取题目/选项 ID 和当前 survey_dsl，再 update_logic |
| 「选了A就跳到结束」 | 先 get_survey 获取 ID，用 branch 语句调用 update_logic |
| 「随机显示题目」「选项随机排序」 | 先 get_survey 获取 ID，用 random show / shuffle 调用 update_logic |
| 「看看问卷的回答」 | 调用 list_answers，注意翻页获取全部数据 |
| 「问卷收了多少份」 | 调用 list_answers 查看 total 字段 |

## 配置

**在本次会话首次调用工具前**，完成一次鉴权检查（完整流程见 `references/auth.md`）：

> `${SKILL_DIR}` 为本 skill 所在目录路径（即 `SKILL.md` 所在目录）。由 AI Agent 框架在加载 skill 时自动注入；如果框架未注入，请替换为 `SKILL.md` 所在目录的绝对路径。

### 方式一：环境变量传入 Token

如果已有 Token（环境变量 `TENCENT_SURVEY_TOKEN`），直接完成配置，无需 OAuth 授权：

```bash
TENCENT_SURVEY_TOKEN=xxx bash "${SKILL_DIR}/setup.sh" wj_check_and_start_auth
```

脚本检测到 `TENCENT_SURVEY_TOKEN` 后会自动写入 mcporter 配置，输出 `READY` 即表示就绪。

### 方式二：OAuth 设备授权

未设置 `TENCENT_SURVEY_TOKEN` 时，自动进入 OAuth 授权流程：

1. 执行 `bash "${SKILL_DIR}/setup.sh" wj_check_and_start_auth`
2. 输出 `READY` → 鉴权已就绪，直接继续
3. 输出 `AUTH_REQUIRED:<url>` → 向用户展示授权链接，然后执行 `bash "${SKILL_DIR}/setup.sh" wj_wait_auth` 等待授权完成
4. 输出 `ERROR:*` → 告知用户对应错误

> 鉴权通过后，**同一会话内后续调用无需重复检查**。仅当工具返回 `invalid_token`、`token expired`、`missing_token` 等鉴权错误时，才需要重新执行上述流程。

- Token 前缀固定为 `wjpt_`，长度 70 字符
- 每个 Token 绑定一个团队，只能操作该团队下的问卷

## 工具列表与调用方式

| 工具名称 | 功能说明 | 参考文档 |
|---------|---------|---------|
| get_survey | 获取指定问卷的详细信息（标题、设置、页面、题目、选项 + 纯文本 DSL） | `references/get_survey.md` |
| create_survey | 使用纯文本创建问卷（text 必填，支持指定场景/指定项目） | `references/create_survey.md` |
| update_question | 更新问卷中的某一道题目（需先获取 question_id） | `references/update_question.md` |
| update_logic | 更新问卷的自定义逻辑设置（条件显示/隐藏、跳转、替换、随机等） | `references/update_logic.md` |
| list_answers | 获取问卷的回答列表（支持游标分页） | `references/list_answers.md` |
| check_skill_update | 检查 Skill 是否有新版本可更新 | 见上方「SKILL 更新」章节 |

调用优先级：

1. **MCP 原生调用**：如果当前 AI Agent 已通过 MCP 协议连接了 tencent-survey 服务（工具列表中可见 `get_survey`、`create_survey`、`update_question`、`update_logic`、`list_answers`），直接调用工具即可
2. **mcporter CLI 调用**：如果 AI Agent 不支持 MCP 原生调用，或工具列表中未出现 tencent-survey 工具，通过终端执行 `mcporter call tencent-survey.<tool_name> --args '{...}'`
3. **确认工具可用**：使用 `mcporter list tencent-survey` 查看已注册的工具列表和参数 Schema

> 参考文档中的参数说明应与 MCP 工具 Schema 保持一致。如有冲突，以 `mcporter list tencent-survey` 返回的 Schema 为准。

## URL 解析规则

问卷投放链接格式为 `https://wj.qq.com/s2/{survey_id}/{hash}`

当用户提供链接时，取路径第二段为 `survey_id`：

| URL 格式 | 提取方式 | 示例 |
|----------|---------|------|
| `wj.qq.com/s2/{id}/{hash}` | 取路径第二段为 survey_id | `wj.qq.com/s2/292192/abc1` → `292192` |

> 提取到 `survey_id` 后，调用 `get_survey(survey_id=...)` 获取问卷详情。

## 数据模型

```
问卷（Survey）
├── 基本信息：id, hash, title, scene, state
├── 设置：prefix(欢迎语), suffix(结束语), started_at, end_at ...
├── 项目：project { id, name }
├── 纯文本内容：text（DSL 格式，包含标题和所有题目）
├── 自定义逻辑：survey_dsl { code, errors }  ← 通过 update_logic 更新
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

> 核心嵌套关系：`Survey → Pages[] → Questions[] → Options[]`
> 回答嵌套关系：`Answer → answer[] (Pages) → questions[]`

## 常见工作流

### 查看问卷详情

参考文档：`references/get_survey.md`

1. 执行鉴权检查（见上方「配置」节）
2. 从用户提供的链接或 ID 获取 `survey_id`（链接解析见「URL 解析规则」）
3. 调用 `get_survey(survey_id=...)` 获取问卷详情
4. 递归解析 `pages → questions → options` 嵌套结构
5. 向用户展示问卷标题、题目列表等信息

### 创建问卷

参考文档：`references/create_survey.md`

1. 执行鉴权检查（见上方「配置」节）
2. 根据用户需求判断 `scene`：调查(1, 默认)、考试(3)、测评(6)、投票(8)
3. 按问卷文本语法组织 `text` 内容（语法详见参考文档）
4. 如果用户指定了项目，传入 `project_id`
5. 调用 `create_survey` 创建问卷
6. 从返回结果中取 `survey_id` 和 `hash`，拼接投放链接 `wj.qq.com/s2/{survey_id}/{hash}` 告知用户
7. 可选：调用 `get_survey` 确认问卷结构

### 更新问卷题目

参考文档：`references/update_question.md`

1. 执行鉴权检查（见上方「配置」节）
2. 调用 `get_survey(survey_id=...)` 获取问卷详情
3. 从返回的 `pages → questions` 中找到目标题目的 `id`（格式如 `q-1-xxxx`）
4. 参考返回的 `text` 字段了解当前问卷的 DSL 格式
5. 按 DSL 语法编写新的题目文本（只写这一道题，不需要问卷标题）
6. 调用 `update_question(survey_id=..., question_id=..., text=...)` 更新题目
7. 可选：再次调用 `get_survey` 确认更新结果

### 设置问卷逻辑

参考文档：`references/update_logic.md`

1. 执行鉴权检查（见上方「配置」节）
2. 调用 `get_survey(survey_id=...)` 获取问卷详情
3. 从返回的 `survey_dsl.code` 获取当前自定义逻辑代码（如有）
4. 从返回的 `pages → questions → options` 中获取题目 ID 和选项 ID
5. 根据用户需求编写 DSL 逻辑代码（ID 用反引号包裹，如 `` `q-1-abcd::o-100-EFGH` ``）
6. 如需追加规则，在原有 `survey_dsl.code` 基础上添加新规则
7. 调用 `update_logic(survey_id=..., dsl=...)` 更新逻辑（整体覆盖）
8. 可选：再次调用 `get_survey` 确认逻辑已生效

### 查看问卷回答

参考文档：`references/list_answers.md`

1. 执行鉴权检查（见上方「配置」节）
2. 调用 `list_answers(survey_id=...)` 获取首页回答
3. **⚠️ 注意翻页**：如果 `list.length == per_page`，说明可能还有下一页，需要循环翻页：
   - 将返回的 `last_answer_id` 作为下一次请求的参数
   - 继续调用 `list_answers(survey_id=..., last_answer_id=...)` 获取下一页
   - 直到 `list.length < per_page` 表示已到最后一页
4. 解析每条回答的 `answer` 字段（嵌套结构：`页面 → 题目回答`）
5. 向用户展示回答汇总或详情

## 注意事项

- **标题可能含 HTML 标签**：`get_survey` 返回的 `title` 字段可能包含 `<p>`、`<br>` 等标签，展示给用户前需清理
- **text 字段（DSL 格式）**：`get_survey` 返回的 `text` 字段是纯文本 DSL 格式的问卷内容，可作为 `update_question` 的参考
- **text 参数格式**：`create_survey` 和 `update_question` 的 `text` 为必填，JSON 中换行使用 `\n`，选项不需要字母前缀（写 `满意` 而非 `A. 满意`）
- **update_question 需先获取 question_id**：必须先调用 `get_survey` 获取题目列表，不能自行构造 question_id
- **update_logic 整体覆盖**：每次调用 `update_logic` 会覆盖所有已有逻辑，追加规则需先获取当前 `survey_dsl.code`
- **survey_dsl 字段**：`get_survey` 返回的 `survey_dsl` 包含当前自定义逻辑代码（`code`）和错误信息（`errors`），作为 `update_logic` 的参考
- **list_answers 需要翻页**：回答列表使用游标分页，如果回答数量超过 `per_page`（默认 20），必须循环调用直到获取完所有数据
- **非幂等的写操作**：`create_survey` 每次调用都会创建新问卷，`update_question` 每次调用都会覆盖原题目

## 问题定位指南

### 常见错误码

| 错误码 | 错误类型 | 解决方案 |
|--------|---------|---------|
| `missing_token` | 请求未携带 Token | 检查 Authorization Header 或 access_token 参数 |
| `invalid_token_prefix` | Token 前缀错误 | 确认使用 `wjpt_` 开头的 Token |
| `invalid token` | Token 不存在或已撤销 | 重新创建 Token |
| `token expired` | Token 已过期 | 重新授权，详见 `references/auth.md` |
| `claim_error` | 问卷不属于当前团队 | 确认问卷 ID 正确且属于当前 Token 绑定的团队 |
| `invalid_text_format` | 文本格式错误（create_survey / update_question） | 检查 text DSL 语法 |
| `survey_not_editable` | 问卷不可编辑（update_question） | 问卷可能正在回收中，需先暂停 |
| `paid_function_trial_no_permission` | 付费功能无权限（如自定义逻辑） | 引导用户前往[腾讯问卷购买页](https://wj.qq.com/pricing)升级为付费版本 |

### 排查步骤

1. **检查错误信息**：查看返回的 error 字段，确定错误类型
2. **检查请求参数**：确认 `survey_id` 等参数值正确
3. **阅读参考文档**：`references/` 目录下包含所有工具的参数说明
4. **获取工具列表**：使用 `mcporter list tencent-survey` 确认工具是否可用
