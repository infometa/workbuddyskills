# 🟨 用户域 SQL 模板

> 用户域 SQL 以引用全局 `sql_templates_Q.md`（Q 组）、`sql_templates_A.md`（A 组）、`sql_templates_D.md`（D 组）中的编号为主。

---

## 引用的全局 SQL 模板

| SQL 编号 | 名称 | 服务的能力 |
|---------|------|-----------|
| Q-4 | 用户分群快查（`dim_type='user_order_type'` 为新老客，`'lifecycle'` 为生命周期，`'rfm'` 为 RFM） | 能力 13, 16, 17, 18 |
| A-5 | 用户分群分布（复用 Q-4，分别查 user_order_type / lifecycle / rfm） | 能力 13, 16, 17 |
| A-10 | 留存复购趋势 | 能力 14, 18 |
| D-4 | 新老客贡献度 | 能力 15 |
| D-5 | 生命周期/RFM 拆解（`dim_type='lifecycle'` 或 `'rfm'`） | 能力 15 |
| D-6 | 留存复购诊断 | 能力 15 |

---

## 域特有补充模板

### U-1：RFM 分群环比流转矩阵（能力 16 S4）

```sql
-- U-1: RFM 分群 T 期 vs T-1 期人数对比（用于桑基图）
-- 需执行两次 Q-4c（当期+基期），在应用层计算流转
-- 当期
SELECT dim_value AS rfm_label, BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS pay_uv
FROM app_user_stat_di
WHERE dim_type = 'rfm' AND stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY dim_value;

-- 基期（同结构，换日期）
```

### U-2：生命周期阶段环比流转（能力 17 S3）

```sql
-- U-2: 生命周期各阶段 T 期 vs T-1 期人数（用于桑基图）
SELECT dim_value AS lifecycle_stage, BITMAP_COUNT(BITMAP_UNION(pay_uv)) AS pay_uv
FROM app_user_stat_di
WHERE dim_type = 'lifecycle' AND stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY dim_value;
```
