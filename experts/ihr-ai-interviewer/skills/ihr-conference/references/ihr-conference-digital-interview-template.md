# 数字人面试模板

> **前置条件：** 先阅读 [`../../ihr-shared/SKILL.md`](../../ihr-shared/SKILL.md) 了解共享运行规则和 JSON 协议。

本 reference 只负责数字人面试模板，用于准备 `conference +launch --interviewCode`。这里的 `templateId` 是 `templateBusinessType=INTERVIEW` 的模板业务 ID，不是 conference 大纲模板 `templateId`。数字人陪练改读 [`ihr-conference-digital-practice-template.md`](ihr-conference-digital-practice-template.md)。

创建模板有真实副作用：`+create-avatar-template` 会直接创建并发布一套可发起面试的数字人模板。除非用户明确要新建模板，或者搜索后没有合适模板，否则不要创建。

## 标准流程

1. 先用 `+search-avatar-template` 搜索当前公司已有模板。
2. 如果已有模板匹配岗位、轮次和题量，复用搜索结果里的 `templateId`。
3. 如果没有合适模板，先完成 HR 面试设计分析，再创建新模板。
4. 创建成功后用完整 `templateName` 再搜索确认。
5. 创建或搜索得到的 `templateId` 填入 `conference +launch --interviewCode`。

```text
用户招聘目标
  -> 分析岗位职责 / 职级 / 业务场景
  -> 判断 dynamicConstraint.job_determination
  -> 设计考察维度和权重
  -> 设计面试题和题目配置
  -> dry-run 检查请求
  -> create 发布模板
  -> launch 使用 templateId 作为 interviewCode
```

## conference +search-avatar-template

```bash
ihr-cli conference +search-avatar-template \
  --keyword "Java 后端" \
  --page 1 \
  --pageSize 10
```

可用 JSON 或 stdin：

```bash
ihr-cli conference +search-avatar-template --json '{"keyword":"Java 后端","page":1,"pageSize":10}'
```

参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--keyword <text>` | 否 | 按方案名称、面试名称或岗位名称搜索；不传时由后端按当前公司分页返回已发布启用模板 |
| `--page <n>` | 否 | 页码，从 `1` 开始 |
| `--pageSize <n>` | 否 | 每页数量，默认 `10`，最大 `50` |
| `--json <json>` | 否 | 直接传入搜索 JSON，不能和分项参数混用 |
| `--stdin` | 否 | 从标准输入读取搜索 JSON，不能和分项参数混用 |
| `--dry-run` | 否 | 只打印请求，不真正调用接口 |

重点读取字段：

| 字段 | 说明 |
|------|------|
| `response.data.templates[].templateId` | 数字人模板业务 ID，可作为 `conference +launch --interviewCode` |
| `response.data.templates[].templateBusinessType` | 面试模板固定为 `INTERVIEW` |
| `response.data.templates[].templateName` | 方案名称 |
| `response.data.templates[].interviewName` | 面试名称 |
| `response.data.templates[].jobTitle` | 岗位名称 |
| `response.data.templates[].digitalHumanId` | 模板绑定的数字人配置 ID |
| `response.data.templates[].questionsCount` | 展示题数量；不含开场题和结束题 |
| `response.data.templates[].usageCount` | 使用次数 |
| `response.data.templates[].hasDraft` | 是否存在未发布草稿；搜索结果本身仍是已发布版本 |

复用已有模板时，至少检查：

1. `jobTitle` 和用户目标岗位是否一致或高度接近。
2. `templateName` / `interviewName` 是否符合当前轮次，例如初面、技术面、复面、终面。
3. `questionsCount` 是否足够。正式面试通常不要少于 6 道展示题；中高级、管理岗、专业岗建议 8 到 10 道。
4. `digitalHumanId` 是否符合用户指定的数字人配置；用户未指定时接受后端按当前配置保存并返回的实际值。
5. `hasDraft=true` 只表示存在未发布草稿；搜索结果仍是已发布版本，可以用于发起面试。

## 创建前的 HR 面试设计

创建模板前，先把“岗位”转成“可面试的评估模型”。不要直接根据岗位名生成几道泛题。

### 1. 分析岗位

先提取岗位上下文：

| 信息 | 用途 |
|------|------|
| 岗位名称 | 写入 `jobInfo.title`，用于搜索和模板归档 |
| 行业和业务场景 | 写入 `jobInfo.industry`、`jobInfo.desc`，帮助题目贴近真实工作 |
| 招聘类型 | `jobInfo.scene=1` 表示社招，`scene=2` 表示校招 |
| 岗位类型 | 写入 `jobInfo.type`，例如研发、销售、运营、客服、制造、管理 |
| 面试轮次 | 决定题目深度，例如初筛偏基础和动机，技术面偏专业能力，复面偏复杂场景和协作 |
| 候选人层级 | 决定 `dynamicConstraint.job_determination.job_level` 和题目难度 |

如果用户只给了岗位名，agent 应补一个简洁专业的岗位描述，不能留空或写成泛泛介绍。

### 2. 判断 `dynamicConstraint`

`dynamicConstraint` 是模板级动态约束。不要为了凑字段乱填；能判断岗位性质时再传。

当前最重要的是 `job_determination`：

```json
{
  "dynamicConstraint": {
    "job_determination": {
      "job_type": "白领",
      "job_level": "L3",
      "reason": "该岗位需要独立负责复杂模块、排查线上问题并推动跨角色协作。"
    }
  }
}
```

`job_level` 只能使用 `L1`、`L2`、`L3`、`L4`：

| 级别 | 适用岗位 | HR 面试考察重心 |
|------|----------|----------------|
| `L1` | 初级、实习、基础执行、体力型岗位 | 工作态度、纪律性、稳定性、基础沟通、到岗意愿 |
| `L2` | 熟练操作、一线执行、标准化岗位 | 流程规范、熟练度、安全意识、独立完成、常见问题处理 |
| `L3` | 中高级、资深、带班、复杂专业岗位 | 复杂问题处理、经验沉淀、跨角色协作、带教或流程改进 |
| `L4` | 经理、负责人、专家、总监 | 资源调配、体系建设、成本控制、风险管理、多任务协调 |

示例判断：

- Java 中高级工程师、资深客服主管、资深顾问：通常是 `L3`。
- 研发经理、销售负责人、运营负责人、专家岗：通常是 `L4`。
- 产线熟练操作员、客服专员、门店店长助理：通常是 `L2`。
- 实习生、初级专员、基础执行岗：通常是 `L1`。

`dynamicConstraint` 不能传空对象。不能确定时直接省略整个 `dynamicConstraint`。

### 3. 设计考察维度

维度是面试评价结构，不是题目列表。先设计维度，再设计问题。

正式模板建议 4 到 6 个维度：

1. 岗位硬技能或专业知识。
2. 核心场景经验。
3. 问题拆解和判断能力。
4. 沟通协作和推动能力。
5. 风险意识、合规意识或稳定性。
6. 对管理岗，可加入团队管理、资源协调、目标拆解。

维度权重是 1 到 5 的相对权重，不是百分比：

- 核心能力：4 或 5。
- 重要但非核心能力：3。
- 辅助观察项：1 或 2。

规则：

1. `dimensions[].name` 必须唯一。
2. `dimensions[].weight` 可不传，默认 1；传入时必须在 1 到 5。
3. 每个维度都必须至少被一道正式题引用。
4. 关键维度最好被 2 道以上题目覆盖。
5. 不要传 `color`；创建接口不接收维度颜色。

### 4. 设计面试问题

问题必须是候选人能回答的面试题，不要写成评价标签。

错误示例：

```text
考察线上排障能力。
```

正确示例：

```text
请描述一次线上接口响应变慢或错误率升高的排查经历。你从哪些指标开始看，如何定位根因，最后怎么复盘和预防？
```

正式面试建议 6 到 10 道展示题：

- 初筛或轻量岗位：6 到 7 道。
- 中高级、管理岗、专业岗：8 到 10 道。
- 客观题通常 1 到 2 道，用于确认关键知识点，不要过多。

题目结构建议：

1. `self_introduction`：自我介绍，帮助进入面试状态，通常不计分。
2. 2 到 4 道 `open_ended`：围绕核心经历、岗位场景和关键能力追问。
3. 1 到 2 道 `objective`：确认关键知识点或规范理解。
4. 1 到 2 道 `user_question`：让 AI 根据前面回答围绕关键维度继续深挖。
5. 需要在流程中播报公司、岗位、培训或制度资料，并允许候选人围绕资料提问时，可加入 `knowledge_introduction`。
6. 必要时加入 `detection` 或 `psychological_test`，仅在岗位确实需要时使用。
7. `closing`：结束语，通常不计分。

## conference +create-avatar-template

创建请求必须通过 `--json` 或 `--stdin` 提供完整 JSON。不要尝试用大量分项参数拼复杂题目结构。

创建会直接发布模板，有真实副作用。正式执行前先 dry-run：

```bash
ihr-cli conference +create-avatar-template --stdin < avatar-template.json --dry-run
```

确认请求体无误后去掉 `--dry-run` 执行真实创建：

```bash
ihr-cli conference +create-avatar-template --stdin < avatar-template.json
```

也可以用 `--json`：

```bash
ihr-cli conference +create-avatar-template --json '{"templateName":"后端研发技术一面","jobInfo":{"title":"后端研发工程师"},"dimensions":[{"name":"工程实践"}],"questions":[{"type":"open_ended","content":"请介绍一个你深度参与的后端项目。","dimensionNames":["工程实践"]}]}'
```

上面 `--json` 只演示命令格式，不是推荐的正式模板。正式创建应使用完整结构。

## 创建字段

### 顶层字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `templateName` | 是 | 方案名称，最多 26 个字符；当前公司内已生效模板名称必须唯一 |
| `interviewName` | 否 | 候选人看到的面试名称，最多 50 个字符；不传时服务端按模板名处理 |
| `jobInfo` | 是 | 岗位信息 |
| `keyPoint` | 否 | 面试重点，应概括本模板要考察的能力 |
| `dynamicConstraint` | 否 | 模板级动态约束，例如岗位类型和岗位级别；不确定时省略，不要传空对象 |
| `digitalHumanId` | 否 | 数字人配置 ID；不传时后端保存链路按当前配置决定实际值并校验可见性 |
| `anticheatingEnabled` | 否 | 是否开启反作弊；不传默认 `true` |
| `dimensions` | 是 | 考察维度列表 |
| `questions` | 是 | 题目列表 |

### `jobInfo`

```json
{
  "title": "后端研发工程师",
  "industry": "互联网",
  "desc": "负责 Java/Spring Boot 后端服务开发、接口设计、问题排查和系统稳定性建设。",
  "type": "研发",
  "scene": "1"
}
```

规则：

1. `title` 必填。
2. `scene=1` 表示社招，`scene=2` 表示校招。
3. `desc` 应写岗位真实职责和场景，便于题目贴合岗位。
4. `type` 写岗位类别，例如研发、销售、运营、管理、客服、制造。

### `dimensions`

```json
[
  {
    "name": "系统设计与工程实践",
    "desc": "考察接口设计、模块拆分、可靠性和工程权衡。",
    "weight": 5
  }
]
```

规则：

1. `name` 必填且唯一，最多 20 个字符。
2. `desc` 建议填写，描述这个维度如何被评价。
3. `weight` 可不传，传入时必须是 1 到 5。
4. 每个维度必须被至少一道正式题的 `dimensionNames` 引用。

### `questions`

支持的 `type`：

| 类型 | 用途 | 维度 | 计分 | AI 面试官追问 | 候选人 AI 资料咨询 |
|------|------|------|------|----------------|--------------------|
| `self_introduction` | 自我介绍 | 不要求 | 通常不计分 | 简历疑点可用 `resume` | 不适用 |
| `open_ended` | 开放式问答，正式面试最常用 | 必填 | 通常计分 | 根据题目目标选择 `never`、`low`、`medium` 或 `high` | 不适用 |
| `objective` | 客观选择题 | 必填 | 通常计分 | 通常关闭 | 不适用 |
| `psychological_test` | 心理测试题 | 必填 | 按场景决定 | 谨慎使用 | 不适用 |
| `user_question` | 维度深挖题，让 AI 动态追问 | 必填 | 通常计分 | 通常开启 | 不适用 |
| `detection` | 普通话、纹身、五官等检测题 | 必填 | 按场景决定 | 按检测场景决定 | 不适用 |
| `opening` | 开场说明 | 不要求 | 通常不计分 | 通常关闭 | 不适用 |
| `knowledge_introduction` | 资料介绍/知识问答引导题：播报资料，并可允许候选人围绕资料咨询 | 不要求 | 固定不计分 | 固定关闭 | 由 `allowAiConsultation` 控制 |
| `closing` | 结束语 | 不要求 | 通常不计分 | 通常关闭 | 不适用 |

“AI 面试官追问”和“候选人 AI 资料咨询”是两个独立概念：

- **AI 面试官追问**：AI 面试官根据候选人的回答继续提出考察问题，由 `showFollowUp` 和 `questionConfig.followUpType` 控制。
- **候选人 AI 资料咨询**：候选人主动围绕 `knowledgeIntroduction.generalIntroduction` 提问，由 `knowledgeIntroduction.allowAiConsultation` 控制。

`knowledge_introduction` 只允许按配置开启第二种能力。即使 `allowAiConsultation=true`，后端仍会固定关闭 AI 面试官追问，并保持该节点不计分、不关联考察维度。

除 `self_introduction`、`opening`、`knowledge_introduction`、`closing` 外，题目必须填写 `dimensionNames`，且名称必须存在于 `dimensions`。

`dimensionDepth` 用于描述这道题希望继续验证的细分能力、判断点和追问方向。它不是维度名称，也不替代 `dimensionNames`；填写时应写可观察的验证重点，避免只重复题干。

### `questionConfig`

常用配置：

```json
{
  "questionConfig": {
    "language": "ZH_CN",
    "followUpType": "medium",
    "questionTimeoutSeconds": 300,
    "minAnswerLengthForFollowUp": 20,
    "pauseSupported": true
  },
  "showFollowUp": true,
  "scoringEnabled": true
}
```

字段说明：

上面的 JSON 只是一个合法示例，不表示 `medium` 是 Skill 默认值。模型应结合题目目标自行决定是否传 `followUpType`。

| 字段 | 可选值及含义 | 模型选择规则 | 省略行为 |
|------|------|------|------|
| `language` | `ZH_CN`：中文；`EN_US`：英文 | 根据候选人作答语言选择 | CLI 不补值；后端默认 `ZH_CN` |
| `followUpType` | `never`：不追问；`low`：最多 2 次；`medium`：最多 4 次；`high`：最多 8 次；`resume`：结合简历疑点追问 | 根据题目目标、需要的探查深度和整体面试时长选择；没有充分依据时可以不传 | CLI 原样透传；后端默认 `never` |
| `evaluationList` | 检测项字符串列表 | 仅在明确的检测类题目中使用已知检测项，不要自行编造字符串 | 后端默认空列表；部分检测逻辑仍会按题型触发 |
| `questionTimeoutSeconds` | 整数，单位秒 | 根据题目复杂度和期望回答长度选择 | 后端默认 300 秒 |
| `minAnswerLengthForFollowUp` | 整数，单位字符 | 需要追问时，根据有效回答的最低长度选择 | 后端默认 20 字符 |
| `pauseSupported` | `true`：允许暂停；`false`：不允许暂停 | 根据题目是否允许候选人中途暂停选择 | 后端默认 `true` |

`language` 只控制题目级候选人可见对话和期望作答语言，不负责翻译题干，也不控制系统界面、ASR/TTS 或面试报告语言。

当前已知 `evaluationList` 项包括：

- `mandarin_recording`：普通话录音检测。
- `tattoo_detection`：纹身检测。
- `interview_finish`：面试结束检测。

只有题目场景明确匹配时才传对应项；不确定时省略，不要创造新的字符串。

题目级布尔字段：

| 字段 | 模型选择规则 | 省略行为 |
|------|------|------|
| `showFollowUp` | 题目是否允许进入追问流程；客观题、开场和结束通常设为 `false` | 后端默认 `true` |
| `scoringEnabled` | 题目是否参与评分；开场、结束和不计分的自我介绍通常设为 `false` | 后端默认 `true` |
| `hasCorrectAnswer` | 存在标准答案时设为 `true`；客观题至少一个选项需标记正确，非客观题需提供 `correctAnswer` 文本 | 后端默认 `false` |

`correctAnswer` 最多 500 个字符。客观题可以填写正确选项 ID，非客观题可以填写标准答案文本。

### 资料介绍/知识问答引导题 `knowledge_introduction`

当面试流程需要先向候选人介绍一段资料，并允许候选人围绕资料提问时，使用后端规范类型 `knowledge_introduction`。它是流程说明节点，不是评分题，也不是要求候选人回答知识点的客观题。

```json
{
  "type": "knowledge_introduction",
  "content": "下面介绍本岗位的值班与故障响应机制。介绍完成后，你可以用英文就相关内容提问。",
  "knowledgeIntroduction": {
    "generalIntroduction": "The team uses an on-call rotation. Critical incidents require immediate acknowledgement, mitigation, and a written review within two business days.",
    "allowAiConsultation": true
  },
  "questionConfig": {
    "language": "EN_US"
  }
}
```

规则：

1. `content` 必填，最多 500 个字符，用于向候选人展示或播报本节点的引导文案。
2. `knowledgeIntroduction.generalIntroduction` 可选，最多 2000 个字符，填写候选人可咨询的通用资料上下文。
3. `knowledgeIntroduction.allowAiConsultation=true` 表示允许候选人主动围绕资料咨询；省略或传 `false` 时仅播报资料，不开放候选人咨询。
4. Skill 创建接口不接受 `knowledgeIntroduction.companyIntroduction` 和 `knowledgeIntroduction.jobIntroduction`；不要传这两个字段，也不要编造附件或资源绑定字段。
5. 不需要 `dimensionNames`。后端会清空维度关联，并强制 `scoringEnabled=false`、`showFollowUp=false`、`hasCorrectAnswer=false`、`followUpType=never`。这里关闭的是“AI 面试官追问”，不影响 `allowAiConsultation=true` 时的“候选人主动资料咨询”；不要用请求字段尝试覆盖这些规则。
6. 可以设置 `questionConfig.language=ZH_CN` 或 `EN_US`，其语义与其他题型一致：控制题目级候选人可见对话和期望作答语言，不翻译 `content` 或资料文本，也不切换系统界面、ASR/TTS 或报告语言。

### 客观题 `options`

`objective` 必须填写 `options[].text`。

```json
{
  "type": "objective",
  "content": "在 Spring Bean 生命周期中，以下哪一项通常发生在 Bean 属性填充之后？",
  "dimensionNames": ["Java 与框架基础"],
  "hasCorrectAnswer": true,
  "correctAnswer": "B",
  "showFollowUp": false,
  "scoringEnabled": true,
  "options": [
    {"id": "A", "label": "A", "text": "实例化 Bean 对象", "correct": false},
    {"id": "B", "label": "B", "text": "调用初始化回调方法", "correct": true}
  ]
}
```

规则：

1. `id` 不传时后端按顺序生成 `A`、`B`、`C`。
2. 建议显式填写 `id`、`label`、`correct`，并同步填写 `correctAnswer`。
3. 选项要互斥、清晰，不要设置多个含糊正确项。

## 后端硬校验

创建前先自查这些规则：

| 校验项 | 规则 |
|--------|------|
| `templateName` | 必填，最多 26 个字符；当前公司内已生效模板名称必须唯一 |
| `interviewName` | 最多 50 个字符 |
| `jobInfo.title` | 必填 |
| `dimensions` | 必须非空 |
| `dimensions[].name` | 必填、去空白后非空、不能重复，最多 20 个字符 |
| `dimensions[].weight` | 传入时必须在 1 到 5 |
| `questions` | 必须非空 |
| `questions[].type` | 必填，只能使用支持的题型 |
| `questions[].content` | 必填、去空白后非空 |
| `opening` | 最多一个，必须是第一题，内容最多 200 个字符 |
| `knowledge_introduction` | `content` 最多 500 个字符；不要求 `dimensionNames`；保存时强制非计分、无追问 |
| `knowledgeIntroduction.generalIntroduction` | 最多 2000 个字符 |
| `knowledgeIntroduction.companyIntroduction/jobIntroduction` | Skill 创建接口禁止传入 |
| `closing` | 最多一个，必须是最后一题，内容最多 500 个字符 |
| 正式题 `dimensionNames` | 除 `self_introduction`、`opening`、`knowledge_introduction`、`closing` 外必须填写 |
| 维度引用 | `dimensionNames` 必须精确匹配 `dimensions[].name` |
| 维度覆盖 | 每个定义的维度都必须被至少一道正式题引用 |
| `objective.options` | 客观题必须有选项，每个选项必须有 `text` |
| `questionConfig.language` | 只能使用 `ZH_CN` 或 `EN_US` |
| `correctAnswer` | 最多 500 个字符；`hasCorrectAnswer=true` 时必须存在有效答案 |
| `dynamicConstraint` | 不传可以；传空对象不可以 |
| `job_level` | 传入时必须是 `L1`、`L2`、`L3`、`L4` |
| `digitalHumanId` | 不传可以；传入时后端会校验配置存在、启用，并属于系统或当前公司 |

## 创建请求样例

下面是一套中等复杂度的后端研发工程师技术一面模板。它展示结构和专业度，不要机械复用到其他岗位；其他岗位应重新分析职责、级别、维度和题目。

```json
{
  "templateName": "后端研发技术一面",
  "interviewName": "后端研发技术一面",
  "jobInfo": {
    "title": "后端研发工程师",
    "industry": "互联网",
    "desc": "负责 Java/Spring Boot 后端服务开发、接口设计、数据库建模、线上问题排查和系统稳定性建设。",
    "type": "研发",
    "scene": "1"
  },
  "keyPoint": "重点考察 Java 基础、Spring Boot 实践、数据库设计、系统设计、线上排障和协作沟通。",
  "dynamicConstraint": {
    "job_determination": {
      "job_type": "白领",
      "job_level": "L3",
      "reason": "该岗位需要独立负责后端模块设计、线上问题排查和跨角色协作，属于资深工程实践角色。"
    }
  },
  "anticheatingEnabled": false,
  "dimensions": [
    {
      "name": "Java 与框架基础",
      "desc": "考察 Java 语言、集合并发、Spring Boot 和常见框架机制理解。",
      "weight": 4
    },
    {
      "name": "数据库与数据建模",
      "desc": "考察 SQL、索引、事务、表结构设计和性能优化能力。",
      "weight": 4
    },
    {
      "name": "系统设计与工程实践",
      "desc": "考察接口设计、服务拆分、可靠性、可观测性和工程权衡。",
      "weight": 5
    },
    {
      "name": "问题排查与沟通协作",
      "desc": "考察线上问题定位、跨角色沟通、复盘和推进能力。",
      "weight": 3
    }
  ],
  "questions": [
    {
      "type": "self_introduction",
      "content": "请用 2 分钟介绍你的后端研发经历，重点说明你最熟悉的技术栈和最近负责的核心项目。",
      "showFollowUp": false,
      "scoringEnabled": false,
      "questionConfig": {
        "followUpType": "resume",
        "questionTimeoutSeconds": 180
      }
    },
    {
      "type": "open_ended",
      "content": "请介绍一个你主导或深度参与的后端项目，说明业务目标、系统架构、你的职责，以及你做过的关键技术决策。",
      "dimensionNames": ["系统设计与工程实践"],
      "dimensionDepth": "重点追问服务边界、接口设计、数据流、异常处理和技术取舍。",
      "showFollowUp": true,
      "scoringEnabled": true,
      "questionConfig": {
        "followUpType": "low",
        "questionTimeoutSeconds": 360
      }
    },
    {
      "type": "open_ended",
      "content": "请结合一个具体场景，说明你如何设计数据库表结构和索引；如果数据量增长 10 倍，你会如何评估和优化？",
      "dimensionNames": ["数据库与数据建模", "系统设计与工程实践"],
      "dimensionDepth": "关注范式与反范式、索引选择、慢查询分析、事务边界和扩展方案。",
      "showFollowUp": true,
      "scoringEnabled": true
    },
    {
      "type": "objective",
      "content": "在 Spring Bean 生命周期中，以下哪一项通常发生在 Bean 属性填充之后？",
      "dimensionNames": ["Java 与框架基础"],
      "hasCorrectAnswer": true,
      "correctAnswer": "B",
      "showFollowUp": false,
      "scoringEnabled": true,
      "options": [
        {"id": "A", "label": "A", "text": "实例化 Bean 对象", "correct": false},
        {"id": "B", "label": "B", "text": "调用初始化回调方法", "correct": true},
        {"id": "C", "label": "C", "text": "扫描 BeanDefinition", "correct": false},
        {"id": "D", "label": "D", "text": "销毁单例 Bean", "correct": false}
      ]
    },
    {
      "type": "open_ended",
      "content": "请描述一次线上接口响应变慢或错误率升高的排查经历。你从哪些指标开始看，如何定位根因，最后怎么复盘和预防？",
      "dimensionNames": ["问题排查与沟通协作", "系统设计与工程实践"],
      "dimensionDepth": "关注监控日志、链路追踪、假设验证、止血方案和复盘机制。",
      "showFollowUp": true,
      "scoringEnabled": true,
      "questionConfig": {
        "followUpType": "medium",
        "questionTimeoutSeconds": 360
      }
    },
    {
      "type": "user_question",
      "content": "围绕候选人的工程实践经历，继续追问一个能验证其真实参与深度和技术判断的问题。",
      "dimensionNames": ["系统设计与工程实践"],
      "dimensionDepth": "要求 AI 根据候选人前面回答动态追问，验证其是否真正理解方案细节。",
      "showFollowUp": true,
      "scoringEnabled": true
    },
    {
      "type": "open_ended",
      "content": "请讲一次你和产品、测试、前端或其他后端同学协作解决复杂问题的经历。你如何对齐目标、拆分任务并推进结果？",
      "dimensionNames": ["问题排查与沟通协作"],
      "dimensionDepth": "关注沟通结构、冲突处理、结果交付和复盘。",
      "showFollowUp": true,
      "scoringEnabled": true
    },
    {
      "type": "closing",
      "content": "本轮面试问题已完成，感谢你的回答。后续请等待招聘团队通知。",
      "showFollowUp": false,
      "scoringEnabled": false
    }
  ]
}
```

## 创建响应

```json
{
  "response": {
    "code": 0,
    "data": {
      "templateId": "000123157a080005dea5dcbdca1c9e87",
      "templateUri": "/web/page/ai-digital-avatar/interview-template-edit?interviewCode=000123157a080005dea5dcbdca1c9e87&outUserId=user-001&companyId=company-001",
      "templateUrl": "https://qa2.ihr360.com/web/page/ai-digital-avatar/interview-template-edit?interviewCode=000123157a080005dea5dcbdca1c9e87&outUserId=user-001&companyId=company-001",
      "template": {
        "templateId": "000123157a080005dea5dcbdca1c9e87",
        "templateName": "后端研发技术一面",
        "interviewName": "后端研发技术一面",
        "jobTitle": "后端研发工程师",
        "digitalHumanId": 123,
        "questionsCount": 7,
        "usageCount": 0,
        "hasDraft": false
      }
    },
    "success": true
  },
  "success": true
}
```

保存 `response.data.templateId` 和 `response.data.template.digitalHumanId`。前者是发起数字人面试时的 `interviewCode`，后者是模板保存后实际生效的数字人配置 ID；示例中的 `123` 仅表示返回结构，不能当作默认值。
后端会返回 `response.data.templateUri`；CLI 会额外补 `response.data.templateUrl`，其值是当前登录 profile 的业务域名加上 `templateUri`，可用于创建后直接打开模板。

创建成功后建议用完整模板名再查一次：

```bash
ihr-cli conference +search-avatar-template \
  --keyword "后端研发技术一面" \
  --page 1 \
  --pageSize 10
```

## 与 launch 串联

```bash
ihr-cli conference +launch \
  --title "候选人A数字人初面" \
  --purposeId purpose_002 \
  --startTime "2026-07-09T10:00:00+08:00" \
  --thirdPartyPlatform DIGITAL_AVATAR \
  --interviewCode "<search/create 返回的 templateId>" \
  --interviewers '[{"staffId":"<search/create 返回的 digitalHumanId>","name":"数字人面谈官","sourceType":"DIGITAL_HUMAN"}]' \
  --interviewees '[{"name":"候选人A","sourceType":"EXTERNAL","phone":"13800000000"}]' \
  --dry-run
```

规则：

1. `templateId` 只作为数字人 `interviewCode` 使用。
2. 不要把数字人模板 `templateId` 填到 conference `--templateId`。
3. 不要读取或传递 `uniqueId`、`questionBuilderId`、草稿版本 ID、发布版本 ID 等内部模板版本字段。
4. 数字人候选人必须且只能有一个，且必须有 `name` 和 `phone` 或 `email`。
5. 发起时把搜索/创建结果中的实际 `digitalHumanId` 转为十进制字符串写入数字人面谈官 `staffId`；不要在 CLI 或 Skill 中复制后端默认值。

## 常见错误

接口返回 `ResultVO`。判断成功优先看：

- `response.code=0`
- `response.success=true`
- CLI 外层 `success=true`

常见错误和处理：

| 错误 | 含义 | 处理 |
|------|------|------|
| `方案名称参数长度不能超过26个字符` | `templateName` 过长 | 缩短方案名，保留岗位和轮次即可 |
| `字段校验失败: templateName` | 方案名称缺失 | 填写短方案名 |
| `字段校验失败: jobInfo.title` | 岗位名称缺失 | 填写岗位名称 |
| `字段校验失败: dimensions[0].weight` | 维度权重不在 1 到 5 | 调整权重 |
| `字段校验失败: dynamicConstraint` | 传了空动态约束对象 | 删除空对象或填入有效字段 |
| `字段校验失败: dynamicConstraint.job_determination.job_level` | 岗位级别不是 `L1` 到 `L4` | 改成有效级别或省略 |
| `字段校验失败: questions[0].dimensionNames` | 正式题没有关联维度 | 为正式题补 `dimensionNames` |
| `字段校验失败: questions[1].options` | 客观题没有选项 | 补 `options[].text` |
| `业务规则校验失败: questions[2].dimensionNames[0]` | 题目引用了不存在的维度 | 确保维度名完全一致 |
| `业务规则校验失败: dimensions[1].name` | 维度未被任何正式题引用，或维度名重复 | 去重并让每个维度至少关联一道正式题 |

收到字段路径后，修正对应字段并重试。不要用空字段、无关默认值或减少到两三道泛题来绕过校验。
