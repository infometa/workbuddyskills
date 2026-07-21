# 结果可视化：必要时生成图表

数据洞察的结论，趋势/排名/占比类用图比文字更直观。本文说明**何时作图、选哪种图、怎么生成**。

> **路径变量**：`SKILL_DIR` = 本 skill 的根目录。脚本调用统一写 `${SKILL_DIR}/scripts/render_chart.py`。

## 1) 何时生成图表（按需，不强求）

| 适合作图 | 典型场景 | 推荐图型 |
|---------|---------|---------|
| ✅ 趋势随时间变化 | 日活趋势、按天/月拜访量、费用走势 | 折线 line |
| ✅ 多项排名/对比 | 各成员拜访量、各类型会议费用、热门内容 Top N | 柱状 bar |
| ✅ 构成/占比 | 拜访渠道占比、会议状态分布、行为类型构成 | 饼图 pie |
| ✅ 多维分组对比 | 各成员的计划 vs 完成、多产品多月对比 | 多系列柱状 bar |
| ❌ 单个数值 | "本月拜访量 320 次" | 直接文字 |
| ❌ 2-3 行小表 | 极少类别的简单分布 | Markdown 表格即可 |

判断原则：**作图是为了让结论更快被看懂**。数据点 ≥4 且有趋势/对比/构成关系时才值得作图；单值或寥寥几行直接用文字或表格。

## 2) 生成方式：render_chart.py

脚本纯标准库、无第三方依赖，产出**单个自包含 HTML**（ECharts 走 CDN），用浏览器或 IDE 预览打开。

**spec JSON 结构**：

```jsonc
{
  "type":  "bar | line | pie",          // 必填
  "title": "图表标题",                   // 必填
  "subtitle": "可选副标题（如时间范围）",
  "x":     ["类目1", "类目2"],           // bar/line 的 x 轴类目；pie 作为扇区名
  "series":[ {"name":"系列名","data":[v1, v2]} ],  // pie 只取 series[0].data
  "out":   "输出路径.html"               // 也可用 --out 覆盖
}
```

**三种调用方式**（任选）：

```bash
# 1) stdin 传 JSON（推荐，省去临时文件）
echo '{"type":"line","title":"近7天日活","x":["06-24","06-25","06-26"],"series":[{"name":"DAU","data":[120,135,150]}]}' \
  | python3 ${SKILL_DIR}/scripts/render_chart.py --out dau.html

# 2) spec 文件
python3 ${SKILL_DIR}/scripts/render_chart.py --spec spec.json

# 3) 命令行参数
python3 ${SKILL_DIR}/scripts/render_chart.py --type bar --title "各成员拜访量" \
  --x '["张三","李四","王五"]' --series '[{"name":"次数","data":[187,170,159]}]' --out rank.html
```

## 3) 从 GraphqlQuery 结果到图表 spec

GraphqlQuery 返回 `data.<对象名>` 是记录数组。作图前做两件事：

1. **抽取 x 与 series**：分组字段值 → `x`，聚合值（别名如 `cnt`）→ `series[].data`。
2. **枚举翻译**：x 若是枚举字段（如 `channel`、`meeting_status`、`behavior_type`），先按 common-scenarios.md 的枚举表把 value 换成中文 label 再作图；金额（`real_cost` 等）÷100 转元再作图。

**示例**：拜访渠道分布（饼图）

```
GraphqlQuery 返回：
  {"visit_item":[{"cnt":1844,"channel":1},{"cnt":1573,"channel":2},{"cnt":1524,"channel":3}]}
        │  按枚举表 1→面对面、2→电话、3→邮件
        ▼
spec：{"type":"pie","title":"拜访渠道分布","x":["面对面","电话","邮件"],
       "series":[{"name":"拜访次数","data":[1844,1573,1524]}]}
```

**示例**：各类型会议实际费用（柱状，金额 ÷100）

```
返回 real_cost 为分 → data 里每项 ÷100 转元
spec：{"type":"bar","title":"各类型会议实际费用(元)","x":["科室会","城市会","区域会"],
       "series":[{"name":"实际费用","data":[730046.62,58045.52,10841.80]}]}
```

**示例**：计划 vs 完成（多系列柱状）

```
spec：{"type":"bar","title":"各成员 计划vs完成",
       "x":["张三","李四"],
       "series":[{"name":"计划","data":[20,18]},{"name":"完成","data":[17,15]}]}
```

## 4) 展示与降级

- **展示**：生成后把 HTML 路径告知用户，提示「在 IDE 中打开预览 / 用浏览器打开」。文字结论与洞察仍要照常给出，图表是补充而非替代。
- **降级**：若环境离线（ECharts CDN 不可达）或用户只想要纯文本，改用 **Markdown 表格** 呈现，不必强行作图。表格同样要先做枚举翻译和金额还原。

## 5) 小结

数据洞察的标准产出 = **文字结论 + 关键数据（表格）** ，趋势/排名/占比时再叠加 **一张图**。图表选型记住三句话：看变化用折线、比高低用柱状、看构成用饼图。
