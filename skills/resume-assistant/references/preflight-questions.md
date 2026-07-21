# Preflight 澄清问答（v0.3.2 新增）

> **触发时机**：所有需要"生成 / 改写 / 定制"内容的 mode（`generate` / `tailor` / `rewrite`）开始前必须执行。
>
> **目标**：把 3 类隐含偏好显式化（**模板 / 长度 / 语言**），避免 AI 凭"默认"瞎猜后产生大幅返工。
>
> **吸收来源**：`refs/resume/_picked/tailored-resume-generator/SKILL.md` §1 Gather Information（L156-170）+ §9 Best Practices；本 skill 原 `preferences` 输入字段。

---

## 一、Preflight 决策矩阵

```
┌──────────────────────────────────────────────────────────────────────┐
│                     PREFLIGHT (3 选项 + 1 fallback)                  │
├──────────────────────────────────────────────────────────────────────┤
│ 1. 模板风格 (template)                                                │
│    a) star            STAR 公式（行为面试 / 业务岗 / 应届首选）        │
│    b) project_oriented 项目导向（技术岗 / 有可量化成果）              │
│    c) skill_oriented   技能导向（转岗 / 跨行业 / 长 skill stack）     │
│    d) hybrid           混合（高管 / 复合背景）                       │
├──────────────────────────────────────────────────────────────────────┤
│ 2. 长度 (length)                                                     │
│    a) 1page    应届 / 入行 < 5 年 / 投美企外企                        │
│    b) 2page    经验 5-15 年 / 国内中大厂 / 项目密集                    │
│    c) auto     由系统按经历密度自动选（默认）                         │
├──────────────────────────────────────────────────────────────────────┤
│ 3. 语言 (language)                                                   │
│    a) zh       仅中文（投国内）                                       │
│    b) en       仅英文（投外企 / 出海）                                │
│    c) both     中英双版（**本土化重写**，非翻译）                       │
├──────────────────────────────────────────────────────────────────────┤
│ 4. (Fallback) 自动决策                                                │
│    用户说"你看着办" / "默认就行" → 系统按下文 §三 启发式自动选择        │
│    并在产出顶部用注释行写明"本次自动选择：template=X / length=Y..."     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 二、Preflight 问询脚本（中文 UI · 一次问完）

> 系统**一次性**抛出全部 3 个选项让用户回答，**不要逐项追问**——避免 3 轮对话浪费用户耐心。

### 标准模板（生成前必发）

```
开始前请确认 3 个偏好（直接回 a/b/c 或自然语言均可，不确定回"默认"）：

1) 模板风格
   a) STAR — 故事化叙述（推荐：业务岗、应届、行为面试）
   b) 项目导向 — 项目 → 责任 → 量化（推荐：技术岗、产品岗）
   c) 技能导向 — 技能聚类 + 经历佐证（推荐：转岗、跨行业）
   d) 混合 — 上面任意组合（推荐：高管、复合背景）

2) 长度
   a) 1 页 — 投外企 / 经验 < 5 年
   b) 2 页 — 投国内 / 经验 5-15 年
   c) 自动 — 由系统按经历密度判断（默认）

3) 语言
   a) 中文
   b) 英文
   c) 中英双版（独立重写、非翻译）

例：回"b / a / c"或"项目导向 / 1 页 / 中英双版"或"默认"。
```

### 已知 mode 时的快捷模板

如果上下文已经锁定一些参数，可以省略对应问题：

| 场景 | 跳过的问题 | 仅问 |
|---|---|---|
| 用户已说"投谷歌 SDE" | 语言（自动 = en）| 模板 + 长度 |
| 用户已说"我是应届" | 长度（auto = 1page）| 模板 + 语言 |
| 用户已说"做中英双版" | 语言（= both）| 模板 + 长度 |
| `tailor` 模式从 master 派生 | 全部继承 master，仅在用户主动改时问 | （静默继承）|

---

## 三、Fallback 启发式（用户回"默认"时使用）

> **必须在简历顶部用注释行声明 auto-selection 结果，便于用户事后复审**：
> `<!-- preflight: template=project_oriented · length=auto · language=zh · auto-selected: true -->`

| 信号源 | 推断 |
|---|---|
| `role_family = tech` 且 `experience.count ≥ 3` | template = `project_oriented` |
| `role_family = biz` 或 `ops` | template = `star` |
| `role_family = design` | template = `project_oriented`（含作品集 link）|
| `seniority = senior` 或 `years ≥ 10` | template = `hybrid` |
| `experience.years ≤ 5` | length = `1page` |
| `experience.years ≥ 5` 且 `projects ≥ 5` | length = `2page` |
| 否则 | length = `auto`（由 export 时按字数估算）|
| JD 含 "海外 / overseas / global / 外企" 关键词 | language = `both` |
| JD 公司名为外企（Google/Meta/Stripe...）| language = `en` |
| 其他 | language = `zh` |

启发式之间冲突时按**用户最近的显式信号**优先，例如用户说"投腾讯"（中文）但 JD 里有"global"，按"投腾讯"判 `zh`。

---

## 四、与 input-schema 的对齐

`preferences` 字段已存在于 [`input-schema.md`](input-schema.md)，preflight 的产出物**直接填入** `preferences`：

```yaml
preferences:
  template: project_oriented        # ← preflight Q1
  length: 1page                     # ← preflight Q2
  language: en                      # ← preflight Q3
  auto_selected: false              # 用户显式回答 → false / fallback 启发式 → true
```

`auto_selected: true` 时，必须在产出 markdown 顶部插入注释行：

```markdown
<!-- preflight: template=X · length=Y · language=Z · auto-selected: true -->
<!-- 系统自动选择，若不符合预期请告诉我重新选 -->
```

---

## 五、Preflight 与 PDF 输入的次序

当用户用 `@xxx.pdf` 上传简历时：

```
Step A.  PDF 提取 + 用户逐段确认（v0.3.1 §四 流程）
Step B.  写入 _master/（处于 ready 状态）
Step C.  Preflight 三选项问询（本文件）
Step D.  正式进入 mode 工作流（generate/tailor/rewrite）
```

**必须**在 PDF 已确认完成进入 master 后才发 preflight，否则用户面对一堆"提取 + 选择"会眼花。

---

## 六、NEVER

- **NEVER** 跳过 preflight 直接生成（即使你"觉得"用户的偏好很明显）
- **NEVER** 一次只问一个问题（3 轮对话浪费）
- **NEVER** 在 fallback 启发式产出物中**省略**顶部注释行
- **NEVER** 在 preflight 之前就开始调用 `parse_jd.py` / 写文件（提前消费 token）
- **NEVER** 把 preflight 答案写入 User Layer（仅写 `resume-output/<version>/result.json` 的 `preferences` 字段）
