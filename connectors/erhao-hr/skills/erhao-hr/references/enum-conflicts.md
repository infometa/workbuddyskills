# 枚举差异登记（阅读字典前必读）

`references/data-dictionary.md` 由机器源生成。仓库内多份枚举来源**并不完全一致**，
本文件登记全部已知差异，避免误用。**人事枚举唯一采信 `roster_filtering.STATIC_ENUMS`**
（考勤 / 薪酬枚举的机器源是各自命令组的 `_enums.py`）。

> `api-docs/*.md` 是**派生产物**（由仓库外脚本内省生成），**不得**作为枚举转写来源。

## A–G / E2：`api-docs` 与 `STATIC_ENUMS` 的差异

| # | 字段 | 采信（STATIC_ENUMS / 技能侧） | 派生物（api-docs） |
|---|---|---|---|
| A | `work_status` = -1 | 待入职 | 同文件自相矛盾：「未填写」↔「待入职」 |
| B | `sex` 未填写 | 0 | 高级搜索 -1 / 异动 0 |
| C | `ov_education` 未填写 | 0 | -1 |
| D | `age` 未填写 | 无该键 | -1 |
| E | `work_type` | 完整 0–12 + 99（**采信全量**） | `skills/hr-shared/SKILL.md` 散文表仅摘录 `0–3`（全职/兼职/实习生/退休返聘） |
| E2 | `credentials_type` / `zodiac` / `politics_status` 的「未填写」 | 无 `-1` 哨兵（`zodiac` 另有 未知=13） | 统一多出 `-1`未填写 |
| E2′ | `credentials_type` 取值集 | 无 `3`/`4`；`5`=**台胞证**、`6`=**返乡证** | 有 `3`=军(警)官证、`4`=士兵证；`5`=**台湾居民来往大陆通行证**、`6`=**港澳居民来往内地通行证** |
| F | `work_age` 司龄分段 | 「6个月以内」合并档 | 拆 3个月以内 / 3~6个月 |
| G | `work_status` = 6 | **禁用**（实测 35 ≠ 40 人） | 存在该聚合值 |

## T4：仓库内 `work_status` 标签分歧

| 来源 | `3` 的含义 | 其他 |
|---|---|---|
| `STATIC_ENUMS` / `hr-shared` | **待离职** | 无 `0` |
| `commands/attendance/_enums.py` | 离职中 | 含 `0`=未知 |

**处置**：字典按模块原样呈现两套标签（各属不同接口的用户可见真值）；
**分析语义**（在职三态、默认查询口径）一律读作 **待离职**。

## T3：同名参数不同接口不同枚举

`source_type` 在考勤各接口上是**不同枚举**（请假 / 外出 / 出差 / 加班），**禁止跨接口套用同一套取值**。

- 字典收录 `commands/attendance/_enums.py` 中**有常量**的三套：外出（`_OUTING_SOURCE_HELP`）、
  出差（`_TRIP_SOURCE_HELP`）、加班（`_OVERTIME_SOURCE_HELP`）；补卡数据来源见 `_REVAMP_RECORD_TYPE_HELP`。
- **请假接口的 `source_type` 在该文件中没有常量**，字典中**查不到**该套取值；遇到请假来源筛选时，
  须按请假接口自身的取值确认（`api-docs` 清单仅为派生物，不得作为转写来源）。
