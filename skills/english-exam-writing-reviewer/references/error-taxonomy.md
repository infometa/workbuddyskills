# 错误分类 & 严重度

> 服务于 [scoring-workflow.md](scoring-workflow.md) 的 Step 6 错误清单。
> 错误分为 **5 大类** × **3 级严重度**。
> **`type` 字段使用 5 大类标签**，具体问题细节在 `description` 字段中说明。

---

## 一、5 大类（type 枚举）

| 类别 | `type` 标签 | 典型问题 |
|------|------------|------|
| **内容问题** | `content` | 题型要求未完成（如 proverb 未解释名言）、主题偏移、论点缺失、内容与题目无关 |
| **结构问题** | `structure` | 段落划分、衔接失误、主题句缺失、逻辑跳跃、论证残缺、结尾跑题 |
| **语法问题** | `grammar` | 时态、语态、主谓一致、代词指代、冠词、介词、非谓语误用、拼写、标点 |
| **句式问题** | `sentence` | 句式单一、衔接生硬、过渡机械、句子结构不当 |
| **词汇问题** | `vocabulary` | 用词层次偏低、搭配不自然、中式英语、重复单调、词性混用 |

> **注意**：细粒度的问题类型（如 `proverb_subtype`、`pronoun_reference`、`coherence`、`theme_deviation` 等）
> 统一归入上述 5 大类，具体原因在 `description` 字段中详细说明。
---

## 二、3 级严重度

| 级别 | 标签 | 定义 | 对评分的影响 |
|------|------|------|-------------|
| **critical** | 致命错误 | 影响理解、改变句意、造成歧义 | 计入"严重错误"数量，直接影响档次判定 |
| **warning** | 待优化 | 明显错误但不影响理解 | 计入总错误数，影响档内调节 |
| **tip** | 提升点 | 可选改进，不算错 | 仅升档建议，不扣分 |

---

## 三、典型错误示例与分级

### 3.1 机械错（mechanical）

| 示例 | 分级 | 说明 |
|------|------|------|
| `teknologe`（technology 拼错）| warning | 可辨认即不致命 |
| `eassyth`（essay 拼错到无法辨认） | critical | 词已无法识别 |
| 句首未大写 | warning | |
| 缺句号导致两句连写 | critical | 句子边界模糊 |
| 缩略词错误 `don't` → `dont` | warning | |

### 3.2 语法错（grammar）

| 示例 | 分级 | 说明 |
|------|------|------|
| `a soldier who don't want` → `doesn't` | warning | 不影响理解 |
| `most of men want to become great man` | critical | 冠词 + 单复数双重错 + 搭配怪异 |
| `I have state that...` → `I stated` | warning | 时态错但意思清 |
| `I very like` → `I like...very much` | warning | 搭配错但可理解 |
| `if has only a general but no soldiers`（主语缺失）| critical | 句子残缺 |
| `the saying that it saying "..."`（结构错乱）| critical | 无法解析 |
| `given reasons`（应为 given reasons below）| warning | |
| `which seems`（指代复数）→ `which seem` | warning | 指代一致 |

### 3.3 词汇错（lexical）

| 示例 | 分级 | 说明 |
|------|------|------|
| `hot of saucer`（应为 hot major）| critical | 用词完全错误 |
| `doing...as way of serving for people`（介词搭配）| tip | `serving people` 更自然 |
| 反复使用 `great`（重复度过高）| warning | 词汇单调 |
| `views` 当动词用 | warning | 词性错误 |
| `more biased`（应为 quite/highly biased）| tip | 程度修饰不地道 |

### 3.4 结构错（discourse）

| 示例 | 分级 | 说明 |
|------|------|------|
| 全文一整段无分段 | critical | 结构缺失 |
| 结尾段与全文无关 | critical | 跑题/不收束 |
| 第 2 段缺主题句 | warning | |
| 段内用 `firstly...secondly...` 后无 `finally`（列举断尾）| tip | |
| 逻辑连接词误用 `though` 代替 `because` | critical | 逻辑反向 |

---

## 四、输出格式（每条 issue 字段）

```json
{
  "id": "iss-3",
  "severity": "critical | warning | minor | tip",
  "type": "content | structure | grammar | sentence | vocabulary",
  "location": "P2",                             // 段落号，如 P1/P2/P3/P4
  "original": "原文句子或片段",
  "description": "为什么有问题 + 依据（可选引用大纲），用中文详细说明",
  "suggestion": "改写：具体改写示例 / 增加：需补充的内容 / 替换：候选词 / 删除：说明"
}
```

**要求**：
- `location` 精确到段落（P1/P2/P3/P4），词汇问题可精确到段落
- `original` 必须是作文原文逐字切片，禁止改写
- `description` 用中文详细说明问题原因，可含关键术语双语（如- `original` 必须是作文原文逐字切片，禁止改写
- `suggestion` 给具体改写，不写"应当修改"这种泛泛话
- `reason` 用中文 + 关键术语双语（eg. "主谓一致 subject-verb agreement"）

---

## 五、严重错误（critical）的量化规则

服务于 [band-decision-rules.md](band-decision-rules.md) 的档次判定。

| 档次 | 允许的 critical 数量 |
|------|--------------------|
| 14 档 | 0 |
| 11 档 | 0（偶发 1 处可下调 -1） |
| 8 档 | 必须 ≥ 1（这是 8 档与 11 档的关键分水岭）|
| 5 档 | ≥ 3，且占总错误 30% 以上 |
| 2 档 | 大多数句子都有 critical 错误 |

---

## 六、不算错的情况（NEVER 标记）

- ❌ 不要标记"不够地道"为错（这是 tip，只在升档建议里出现）
- ❌ 不要标记"可用更高级词"为错（tip 级别）
- ❌ 不要按 Grammarly 风格标记 passive voice（CET 不禁止被动态）
- ❌ 不要标记语域偏随意但仍合规的表达
- ❌ 不要重复标记同一个错误（全文重复出现的同类错误合并为 1 条，`location` 改为"¶1/¶2/¶3 均出现"）

---

## 七、错误汇总统计（issues_summary）

```json
{
  "issues_summary": {
    "critical": 0,
    "warning": 2,
    "minor": 2,
    "tip": 1,
    "by_type": {
      "content": 1,
      "structure": 1,
      "grammar": 1,
      "sentence": 1,
      "vocabulary": 1
    }
  }
}
```

用于：
- 档次判定交叉验证（critical 数量应与档次匹配）
- HTML 报告头部概览
