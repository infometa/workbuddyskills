# 生涯测评算法说明（10 题简版）

## 生涯方向定义

生涯测评共 6 个生涯方向标签，每题 6 选一（A/B/C/D/E/F），每个选项归属一个方向：

| 标签 | 名称 | 优先级（数值越小越优先） |
|------|------|------------------------|
| A | 公考/央国企 | 2 |
| B | 自由职业 | 5 |
| C | 打工人 | 4 |
| D | 留学 | 3 |
| E | 保研/考研 | 1 |
| F | 躺平 | 6 |

每道题的 6 个选项（A-F）分别归属上述 6 个标签之一。选中即把对应标签的计数 +1。

## 题目设计原则

- 共 10 题，每题 6 选一（A-F），无中间项；
- 用户作答为 `A`-`F`（也接受 `1`-`6`，统一归一为 A-F）；
- 每个选项归属一个标签，选中即把对应标签计数 +1；
- 标签最终计数代表用户对该方向的倾向强度。

## 评分公式

### 1. 标签计数

```text
score[A] = sum(1 for q in answered_questions
               for opt in q.options
               if opt.tag == "A" and user_answer == opt.option)
score[B], score[C], score[D], score[E], score[F] 同理
```

简化形式：

```text
score[tag] = sum(1 for q in answered_questions
                 for opt in q.options
                 if opt.tag == tag and user_answer == opt.option)
```

6 个标签计数之和 = 用户实际作答题数（满分 10 时，6 个标签计数和 = 10）。

### 2. 标签百分比

```text
percent[tag] = score[tag] / total_questions * 100   # 保留两位小数，四舍五入（ROUND_HALF_UP）
```

例：A=4 → percent[A] = 4 / 10 * 100 = 40.00%

### 3. 胜出标签

取计数最多的标签为胜出标签；若多个标签并列最高，按优先级排序取优先级最高者：

```text
max_count = max(score[A..F])
candidates = [t for t in [A,B,C,D,E,F] if score[t] == max_count]
dominant_tag = min(candidates, key=PRIORITY)
```

优先级：保研/考研(E=1) > 公考/央国企(A=2) > 留学(D=3) > 打工人(C=4) > 自由职业(B=5) > 躺平(F=6)

### 4. 总分（display_score，0-100）

```text
display_score = round(score[dominant_tag] / total_questions * 100)   # 保留整数，ROUND_HALF_UP
```

例：胜出标签 A 计数 4 → 4/10*100 = 40.00 → 40

### 5. 标签档案（tag_detail）

依据 `dominant_tag` 在 `references/tag_profiles.md` 中按 `tag` 查表，输出：

- `tag`：生涯标签字母（如 `"A"`）
- `name`：方向中文名（如 `"公考/央国企"`）
- `priority`：平局优先级（1-6，数值越小越优先）
- `section_1` ~ `section_4`：4 段固定文案，原样透传生产原文
  - section_1：身份认同（如「【天选公考/央国企圣体】...」）
  - section_2：大学四年规划
  - section_3：分年级实施路径
  - section_4：寄语

6 个方向必须全部覆盖，缺一不可。

## 输出示例

```json
{
  "assessment_id": "SYCP-10-001",
  "status": "completed",
  "answered_count": 10,
  "total_questions": 10,
  "display_score": 40,
  "tag_counts": {"A": 4, "B": 1, "C": 2, "D": 1, "E": 1, "F": 1},
  "dominant_tag": "A",
  "dominant_name": "公考/央国企",
  "tag_stats": [
    {"tag": "A", "name": "公考/央国企", "score": 4, "percent": 40.00},
    {"tag": "B", "name": "自由职业", "score": 1, "percent": 10.00},
    {"tag": "C", "name": "打工人", "score": 2, "percent": 20.00},
    {"tag": "D", "name": "留学", "score": 1, "percent": 10.00},
    {"tag": "E", "name": "保研/考研", "score": 1, "percent": 10.00},
    {"tag": "F", "name": "躺平", "score": 1, "percent": 10.00}
  ],
  "tag_detail": {
    "tag": "A",
    "name": "公考/央国企",
    "priority": 2,
    "section_1": "【天选公考/央国企圣体】\n生来就是为了报效祖国！未来国家建设的中坚力量非你莫属！\n",
    "section_2": "公考/央国企人的大学四年规划：\n绩点：大学四年认真学习，争取各科高分通过，提升绩点\n技能：高分通过英语四六级、国家计算机二级考试\n身份：入党；竞选学生会/社团主席\n背提：参加专业相关竞赛、科研项目，进入企业实习\n论文：写完毕业论文并通过答辩",
    "section_3": "备考：\n大一--了解公考/央国企的报考要求及考试内容\n大二--明确公考/央国企入职路径与目标\n大三--复习申论、行测、公基等考试内容\n大四--参加公考/央国企笔试、面试，成功上岸",
    "section_4": "志当存高远，慎始而敢行！"
  },
  "analysis": {
    "summary": "用户在 10 道题中，公考/央国企 方向选了 4 次（最多），生涯测评结果为：公考/央国企。",
    "recommendation": "公考/央国企"
  }
}
```

## 状态判定

- 全部 10 题作答：`status = "completed"`
- 未答完全：`status = "incomplete"`，输出 `missing_questions`（缺失题号列表），不生成 `dominant_tag` 与 `tag_detail`

## 确定性约束

- 相同 `answers` 必产生 byte-equal JSON（无随机数、无时间戳、无外部依赖）；
- 文案全部来自 `references/tag_profiles.md` 生产原文，模型不得改写；
- 百分比与总分使用 `decimal.ROUND_HALF_UP`（与 Java `BigDecimal.ROUND_HALF_UP` 一致）；
- 输出字段顺序固定，`tag_counts` 按 `A/B/C/D/E/F` 顺序输出。

## 扩展说明

- 本 10 题简版与需求方提供的 `sycpData.json` 完全一致；
- 若需扩展题量，只需替换 `references/questions.md`，评分逻辑无需改动；
- 文案需要变更时，覆盖 `references/tag_profiles.md` 即可生效，无需改动评分脚本。
