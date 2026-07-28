---
name: get_competitor_list
description: 从 Databrain 系统查询指定游戏的竞品列表。输入己方游戏名，输出 Databrain 中配置的 opinion 类型竞品游戏名称列表。
---

# Get Competitor List 子模块

## Purpose

从 Databrain 系统查询指定游戏（`my_game`）的竞品列表，返回 `entity_name` 列表供后续 opinion_query 模块使用。

---

## 执行步骤

### 第一步：查询 my_game 的 unified_id

使用已有的 `game_search.py` 脚本查询 `my_game` 对应的 `unified_edition_id`：

```bash
PYTHONUTF8=1 python scripts/game_search.py "<my_game>"
```

从输出 JSON 中提取第一条结果的 `game_id` 字段，记为 `my_game_unified_id`。

**将查询结果展示给用户，仅置信度极低时需要用户确认**，确保整体流程能全自动运行，尽量避免用户在中途手动介入。仅当某个游戏 `game_id` 为空或 `match_score` 极低时，提示用户核实。

---

### 第二步：查询竞品列表

使用 Bash 工具执行（将 `<my_game_unified_id>` 替换为上一步得到的实际值）：

```bash
PYTHONUTF8=1 python scripts/get_competitor_list.py "<my_game_unified_id>"
```

---

### 第三步：处理返回结果

**情况 A：输出第一行为 `OK`**

后续每行为一个竞品游戏的 `entity_name`，收集为列表 `competitor_game_names`，展示给用户：

> ✅ 已从 Databrain 获取 **{my_game}** 的竞品列表，共 N 款游戏：
> - Wuthering Waves
> - Genshin Impact
> - …
>

直接将 `competitor_game_names` 作为 `game_names` 传入后续 opinion_query 流程，无需用户确认中断整体进程。

**情况 B：输出为 `EMPTY`**

Databrain 中未为该游戏配置竞品列表，告知用户：

> ⚠️ Databrain 系统中未找到 **{my_game}** 的竞品配置列表。
>
> 请改用**模式二**，手动指定要分析的竞品游戏名称，例如：
> ```
> 帮我分析以下游戏从 YYYY-MM-DD 到 YYYY-MM-DD 的官媒活动：
> - Honkai: Star Rail
> - Genshin Impact
> ```

**不得**继续执行后续步骤，等待用户重新输入。

**情况 C：执行出错（stderr 有 ERROR 输出）**

将错误信息展示给用户，询问是否重试或切换为模式二。
