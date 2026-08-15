# 员工档案 - 绩效晋升

> 本场景使用 beisen-data-query 通用流水线，详见 [../../beisen-data-query/SKILL.md](../../beisen-data-query/SKILL.md)。

## 覆盖场景

| 场景 | 北森查询场景 | 敏感等级 |
|------|------------|:------:|
| 查询考核结果 | 租户配置的"考核结果"场景 | L2 |
| 查询晋升结果 | 租户配置的"晋升结果"场景 | L2 |

## 特殊规则

- L2 敏感数据：查自己 → 完整展示；查他人 → 仅摘要
- 详见 [../../beisen-shared/references/security.md](../../beisen-shared/references/security.md)

