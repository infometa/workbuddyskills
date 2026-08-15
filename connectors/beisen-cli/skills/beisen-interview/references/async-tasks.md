# 招聘面试 - 异步任务轮询协议

> CLI 版本要求：beisen-cli >= 0.2.5

面试域的以下接口为**异步任务**模式，发起后立即返回 `taskId`，需轮询任务状态获取最终结果：

| 接口 | 返回 |
|------|------|
| `beisen-cli interview interviewAnalysis analyzeInterviewQuality` | `data.taskId` |
| `beisen-cli interview interviewAnalysis analyzeCompetitorIntelligence` | `data.taskId` |

## 轮询命令

异步任务的状态查询与取消命令在 **recruitment 域**：

```bash
# 查询任务结果
beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<id>"}'

# 取消任务
beisen-cli recruitment async_task bs_cancel_async_task --data '{"taskId":"<id>"}'
```

## 轮询流程

1. 发起异步任务 → 提取返回的 `taskId`
2. 调用 `beisen-cli recruitment async_task bs_get_async_task_status --data '{"taskId":"<id>"}'` 轮询
3. 轮询间隔 2-5 秒，最长等待不超过 5 分钟
4. `isFinished == true` 后：
   - `status == "Succeeded"` → 从 `resultJson`（JSON 字符串，需 `JSON.parse`）解析报告/结果
   - `status == "Failed"` → 读取 `errorMessage` 向用户说明失败原因
   - `status == "Cancelled"` → 任务已取消

## 状态枚举

| status | 说明 |
|--------|------|
| `Running` | 执行中，继续轮询 |
| `Succeeded` | 执行成功，从 `resultJson` 取结果 |
| `Failed` | 执行失败，从 `errorMessage` 取原因 |
| `Cancelling` | 取消中 |
| `Cancelled` | 已取消 |

## 注意事项

- `taskId` 必须从发起接口返回值中提取，严禁编造
- `resultJson` 是 JSON **字符串**，先 `JSON.parse` 再解析展示
- 分析类任务（面试质量/竞品情报）耗时较长，轮询期间可告知用户"正在生成报告，请稍候"
- 避免高频轮询，间隔控制在 2-5 秒
