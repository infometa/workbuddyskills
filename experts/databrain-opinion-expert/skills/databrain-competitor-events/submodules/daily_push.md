# 每日自动推送子模块

## 引导时机

报告生成完毕后，读取 `{skill_root}/cron_jobs.json`（不存在则视为空数组），在其中搜索是否已有 `status: "running"` 且 `games` 完全匹配本次查询游戏名的记录：

- **有匹配记录** → 不展示引导，跳过本模块
- **无匹配记录** → 在报告输出**末尾**追加以下引导块：

```
━━ 每日自动推送 ━━
💡 我可以每天自动帮你生成上述查询竞品对象的活动报告推送。
   默认推送时间：每天 09:30
   你也可以自定义推送时间，比如 "每天早上10点" 或 "每天下午2点"。

是否需要开启每日自动推送？（回复"开启"或告诉我你希望的推送时间）
```

## 用户确认后的操作

当用户回复确认（如"开启"、"好的"、"开启每天早上10点推送"等），执行以下操作：

1. **解析推送时间**：从用户回复中提取期望时间，映射为 cron 表达式（时区固定 Asia/Shanghai）：

| 用户说 | cron 表达式 | 含义 |
|--------|------------|------|
| "开启"（未指定时间） | `30 9 * * *` | 每天 09:30 |
| "每天早上10点" | `0 10 * * *` | 每天 10:00 |
| "每天下午2点" | `0 14 * * *` | 每天 14:00 |
| "每天早上9点半" | `30 9 * * *` | 每天 09:30 |

2. **确认投递目标**：在注册 cron 之前，先从 inbound metadata 中提取渠道信息：

   **企业微信（主要渠道）的获取规则：**
   - `delivery.channel` 固定填 `wecom`（⛔ 不是 `openclaw-wecom-bot`，后者无主动推送能力）
   - 私聊场景：`delivery.to` = inbound metadata 中的 `sender_id`（如 `mattyijielu`）
   - 群聊场景：`delivery.to` = inbound metadata 中的 `group_space` 字段值
   - ⛔ 严禁使用 `chat_id`（如 `wecom:T46790049A`）作为 `delivery.to`，会导致消息无法送达

   **若无法从 inbound metadata 中获取到有效的渠道或用户信息**，停止注册流程，向用户说明并引导配置：

   ```
   ⚠️ 我无法自动识别你的推送平台和目标，请问需要推送到企业微信吗？
   可以告诉我以下企业微信的相关信息，以便开启推送：
   1. 推送到个人还是群聊？
   2. 如果是个人：你的企业微信账号 ID（sender_id，通常是英文名，如 mattyijielu）
      如果是群聊：群的 group_space ID（可从群消息 metadata 中获取）

   如需推送企业微信以外的其他平台，请告知我平台的具体名称以便获得更多引导信息。
   ```

   收到用户提供的信息后，继续执行注册步骤。

   **其他平台参考（非主要场景）：**

   | 平台 | delivery.channel | delivery.to 格式 |
   |------|-----------------|-----------------|
   | 企业微信 | `wecom` | sender_id 或 group_space ID |
   | 飞书 | `lark` / `feishu` | `user:ou_xxx` 或 `chat:oc_xxx` |
   | Telegram | `telegram` | 用户 chat_id |
   | Slack | `slack` | channel_id 或 `@username` |

3. **注册定时任务**：使用 `cron` 工具注册任务，**必须**按以下参数配置：

   ⚠️ **重要**：`payload.message` 必须在注册时将当前会话的实际参数**硬编码填入**，不得使用"根据上次"等依赖历史上下文的表述。cron 触发时运行在完全隔离的新 session 中，没有任何当前会话的记忆。

   **时间范围的处理规则（注册前必须判断）：**
   - 用户输入的是**相对时间**（如"过去7天"、"最近3天"）→ 直接填入 payload.message
   - 用户输入的是**绝对时间**（如"3月5日"、"2025年Q1"）→ **不可直接使用**，暂停注册流程，询问用户希望例行监控的时间范围：
     ```
     ℹ️ 你本次查询使用了绝对时间（{原始时间}），无法直接用于每日例行推送。
     请问每次推送希望查询多长时间范围的数据？（如"过去1天"、"过去7天"等）
     ```
   收到用户回复后，以该相对时间范围继续完成注册。

```
sessionTarget: "isolated"
payload.kind: "agentTurn"
payload.message: "现在是每日自动推送时间。请执行竞品活动报告任务：
- 游戏名称：<填入本次实际的 game_names，如：王者荣耀、原神>
- 时间范围：<填入处理后的相对时间范围，如：过去1天 / 过去7天>
请完整执行 Step 1–4（数据获取 → 事件聚合 → 联网搜索 → 总结分析），生成完整竞品活动报告后，使用 message tool 发送到 channel=<当前渠道>, target=<sender_id 或 group_space ID>"
delivery.mode: "announce"
delivery.channel: "<当前渠道>"
delivery.to: "<sender_id 或 group_space ID>"
schedule.kind: "cron"
schedule.expr: "<cron表达式>"
schedule.tz: "Asia/Shanghai"
```

4. **写入本地 cron 记录文件**：注册成功后，读取 `{skill_root}/cron_jobs.json`（不存在则初始化为 `[]`），将新记录 append 进数组后写回：

```json
{
  "cron_id": "{注册后返回的 cron job ID}",
  "games": ["{game_name_1}", "{game_name_2}"],
  "time_range": "{处理后的相对时间范围，如：过去1天}",
  "schedule_expr": "{cron表达式}",
  "push_time": "{HH:MM}",
  "channel": "{delivery.channel}",
  "delivery_to": "{delivery.to}",
  "created_at": "{当前时间 ISO8601 格式，Asia/Shanghai}",
  "status": "running"
}
```

5. **确认输出**：

```
✅ 已开启每日自动推送！
   推送时间：每天 {HH:MM}
   推送内容：竞品活动报告（发送到你的企业微信）
   监控范围：{time_range}
   游戏：{game_names}
   任务记录已保存至 cron_jobs.json
   如需修改时间或关闭，告诉我即可。
```

## 修改 / 关闭

操作时，先读取 `cron_jobs.json`，按 `cron_id` 定位目标记录，修改后写回整个文件。

- 用户说"改成每天下午3点推送" → 用 cron 工具更新 schedule，同步更新对应记录的 `schedule_expr` 和 `push_time`
- 用户说"关闭自动推送" → 用 cron 工具移除对应任务，将对应记录的 `status` 改为 `"stopped"`
- 用户说"推送到群里" → 重新确认 group_space ID，更新 `delivery_to`，同步更新 cron 任务的 `payload.message`
- 用户说"查看我的推送任务" → 读取 `cron_jobs.json`，将 `status: "running"` 的记录格式化后展示给用户

> ⚠️ **重要**：`cron_jobs.json` 是结构化记录文件，供 agent 读写使用。用户直接编辑该文件**不会**影响实际运行的 cron 任务。唯一生效的操作是通过 cron 工具增删改任务。
