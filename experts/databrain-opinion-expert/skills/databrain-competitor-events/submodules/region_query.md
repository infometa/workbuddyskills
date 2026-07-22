---
name: region_query
description: 区域定向舆情查询子模块。当 region 参数非空时使用，调用 opinion_query.py 并传入 --country 或 --language 标志，执行针对特定国家/语言的官号数据查询。
---

# Region Query 子模块

## 目的

当子 Agent 收到非空的 `region` 参数时，使用本模块替代直接调用 `opinion_query.md`，在查询时加入国家或语言维度的过滤条件。

底层脚本与全局查询相同（`opinion_query.py`），通过 `--country` / `--language` 标志区分。

---

## region 参数的解读规则

`region` 是**小写 code 字符串**，由主控在解析用户自然语言后、查阅 `references/country_language_code_mapping.csv` 转换而来。格式约定如下：

| region 示例 | 含义 | 对应标志 |
|---|---|---|
| `us` / `jp` / `br` 等国家 code | 按国家筛选官号账号 | `--country=us` |
| `en` / `ja` / `zh` 等语言 code | 按帖子语言筛选 | `--language=ja` |
| `us:ja`（国家:语言 复合格式） | 同时按国家和语言筛选 | `--country=us --language=ja` |

> 解读时：若 region 包含 `:` 则拆分为 `country:language`；否则按 xlsx 映射表判断该 code 属于 `country code` 列还是 `language code` 列，再决定使用哪个标志。
> **查询区域为某个大洲时**，可能会包含多个国家code，例如`--country=us, ca, mx`

---

## 执行步骤

**Step 1 — 解析 region，构造调用命令**

根据上表规则，将 `region` 映射为 `--country` / `--language` 标志。

**Step 2 — 调用 opinion_query.py**

```bash
python "{skill_root}/scripts/opinion_query.py" \
  "{game_id}" "{game_name}" "{start_time}" "{end_time}" "{timestamp}" \
  [--country=<country>] [--language=<language>]
```

- `file_key` 由脚本自动计算为 `{safe_name}_{COUNTRY}` / `{safe_name}_{LANGUAGE}` / `{safe_name}_{COUNTRY}_{LANGUAGE}`，与 SKILL.md 的命名规则一致。
- 输出两个 CSV 文件路径通过 stdout 以 JSON 返回，格式与 `opinion_query.md` 完全相同。

**Step 3 — 返回结果**

将脚本输出的 JSON 中的 `official_posts.path` 和 `post_comments.path` 作为后续 Step 2（活动聚合）的输入。

---

## 错误处理

与 `opinion_query.md` 相同：若脚本返回 `{"error": ...}`，记录原因后按"合法的失败处理"规则处理。
