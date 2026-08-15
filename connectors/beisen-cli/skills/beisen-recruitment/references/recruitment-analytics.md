# 招聘 - 分析类命令参考

## interview-quality — 面试质量分析

```bash
beisen-cli recruitment interview-quality --interviewer-id <id> [--period <range>]
```

### 参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `--interviewer-id` | string | 面试官 ID（必填） | — |
| `--period` | string | 统计周期（如 2026-Q3） | 当前季度 |

### 返回结构

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "interviewer": "面试官姓名",
    "period": "2026-Q3",
    "total_interviews": 15,
    "pass_rate": "60%",
    "avg_score": 82,
    "score_distribution": {
      "excellent": 5,
      "good": 7,
      "average": 2,
      "below_average": 1
    }
  }
}
```

### 注意事项

- `interviewer-id` 必须从 CLI 返回中提取，严禁编造
- 分析结果可能需要较长处理时间，执行前提醒用户耐心等待
- 需要 `beisen:recruitment:read` scope

## competitor-insight — 竞品情报分析

```bash
beisen-cli recruitment competitor-insight --company <name>
```

### 参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `--company` | string | 竞品公司名称（必填） | — |

### 返回结构

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "company": "公司名称",
    "job_openings": 25,
    "hot_positions": ["Java工程师", "产品经理", "UI设计师"],
    "salary_insight": {
      "avg_salary": "18k",
      "salary_range": "10k-35k"
    },
    "hiring_trend": "上升"
  }
}
```

### 注意事项

- 分析结果可能需要较长处理时间，执行前提醒用户耐心等待
- 需要 `beisen:recruitment:read` scope
