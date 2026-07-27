# 职级浮动范围规则

> 用于 Step 3 客户端过滤层 - level_within_range() 函数。

---

## 规则

**用户职级 → 接受候选职级范围 = 用户职级 ± 1**

| 用户 | 候选范围 | 说明 |
|---|---|---|
| P5 | P4 / P5 / P6 | 标准范围 |
| P10 | P9 / P10 / P11 | 标准范围 |
| T7 | T6 / T7 / T8 | 标准范围 |
| T11 | T10 / T11 / T12 | 标准范围 |
| 跨体系（P↔T） | 同数字 ±1 | P5 ≈ T5（按数字对齐） |
| S 级（如 S3） | **不过滤**（全放行）| S 是 BG 简称不是职级，避免误判 |
| 用户未提供 | **不过滤**（全放行）+ summary 标注 | "未提供职级，候选可能跨度大" |
| 管理职级（M/L 系列） | 不过滤（管理岗 skill 已禁用） | — |

---

## 接口返回数据格式

`recruit.huoshui-server.PostAdvancedSearch` 返回的 `estimatePassLevelName` 字段格式：

```
"P5,P6"           # 多职级用逗号分隔
"T9,T10"
"P5"              # 单职级
null              # 未填，按全放行处理
```

`initMrgPositionLevelName` 字段：管理职级（如 L1-1）。**本 skill 已禁用管理职位**，遇到非空时**额外过滤掉**这条候选。

---

## 实现伪代码

```python
def parse_user_level(level_str):
    """
    输入："P5" / "T7" / "S3" / "p10" / "" / None
    输出：(prefix, num) or None
    """
    if not level_str:
        return None
    s = level_str.strip().upper()
    m = re.match(r'^([PTSML]+)(\d+)', s)
    if not m:
        return None
    return m.group(1), int(m.group(2))


def parse_job_levels(level_field):
    """
    输入："P5,P6" / "T9,T10" / null
    输出：[(P,5), (P,6)] / [] (空表 = 全放行)
    """
    if not level_field:
        return []
    out = []
    for part in level_field.split(','):
        parsed = parse_user_level(part.strip())
        if parsed:
            out.append(parsed)
    return out


def level_within_range(job_level_field, user_level_str):
    """
    主过滤函数。
    - user_level_str 为空 → 全放行 True
      * 注意：实习生（careerLevelId/careerLevelName = null）的 level 也为空，会走到这里。
        实习生走活水的准入拦截在 LJ §1.2.1 做（实习生不在活水准入范围），
        如果实习生坚持要看岗位（§1.2.1 分支 B），这里放行是合理的——
        让 ta 能看到按能力匹配的岗位作为职业参考，但最终 LJ.OUT 会说明"不能走活水渠道"。
    - user prefix 是 S → 全放行 True
    - 候选无职级（job_level_field 空）→ 放行 True
    - 候选职级中**任一**在 user ±1 范围内 → 放行
    """
    user = parse_user_level(user_level_str)
    if not user or user[0] == 'S':
        return True

    user_prefix, user_num = user
    candidates = parse_job_levels(job_level_field)
    if not candidates:
        return True   # 候选无职级，放行

    for prefix, num in candidates:
        # 跨体系按数字对齐（P5 ≈ T5）
        if abs(num - user_num) <= 1:
            return True
    return False


def is_management_job(job):
    """
    管理岗硬过滤——管理族 LS 已在 LLM Step 1 排除，
    这里再加一道：initMrgPositionLevelName 非空 → 是管理岗 → 排除。
    """
    return bool(job.get('initMrgPositionLevelName'))
```

---

## 单元测试用例

```
level_within_range("P5,P6", "P5")  → True   (5 in 4-6)
level_within_range("P3,P4", "P5")  → True   (4 in 4-6)
level_within_range("P3", "P5")     → False  (3 not in 4-6)
level_within_range("P10,P11", "P5")→ False
level_within_range("T6,T7", "P5")  → True   (6 in 4-6 跨体系)
level_within_range("T10", "P5")    → False
level_within_range(None, "P5")     → True   (候选无职级)
level_within_range("P5", "")       → True   (用户无职级)
level_within_range("P5", "S3")     → True   (S 级放行)
level_within_range("P5", None)     → True   (用户无职级)
```

---

## 兜底

- 如果按 ±1 严格过滤后候选池 < 3 个 → 自动放宽到 ±2，标注"为你放宽到 ±2 级范围"
- 如果用户主动说"我想跨级看看" → 放宽到 ±3
- 如果还 0 个 → 提示用户："这个职级范围当前没合适岗，可以等等或试试别的方向"
