# 每日自动推送

## 引导时机

当用户**首次手动触发**本 Skill 时（即当前对话中没有已注册的 cron job），在趋势情报输出**末尾**追加以下引导块：

```
━━ 每日自动推送 ━━
💡 我可以每天自动帮你生成趋势情报推送。
   默认推送时间：每天 09:30
   你可以自定义推送时间，比如 "每天早上10点" 或 "每天下午2点"。

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

2. **注册定时任务**：使用 `cron` 工具注册任务，**必须**按以下参数配置：

> 关于推送语言：cron 触发由 agent 在 `payload.message` 中显式声明 `target_language`（默认 `zh`，未来可由用户在开启时指定，如"用英文推"、"中英两版"），agent 收到任务消息后按 [language-policy.md](language-policy.md) 第 1 节的判定流程渲染情报卡。

```
sessionTarget: "isolated"
payload.kind: "agentTurn"
payload.message: "现在是每日自动推送时间。请执行以下步骤：
1. 读取 ~/.openclaw/.env 中的 TAI_IT_TOKEN 并设置环境变量
2. 运行 python scripts/query_trending.py --limit 10 --json 获取热门视频数据
3. 运行 python scripts/query_trending.py --memes --limit 10 --json 获取热梗数据
4. 按 target_language=<zh|en|both>（用户开启推送时指定，未指定时默认 zh）渲染游戏内容趋势情报卡：核心信号 3 条、精选视频 5 条（含链接 / 播放量 / 互动率 / 增速）、不建议跟进方向。段落标题、字段标签、创意类型标签必须按 references/language-policy.md 第 6 节对照表用 target_language 渲染；生成前执行第 8 节 checklist 自检无异种语言残留。
5. 使用 message tool 发送到 channel=<当前渠道>, target=<当前用户ID或群ID>"
delivery.mode: "announce"
delivery.channel: "<当前渠道>"
delivery.to: "<当前用户ID或群ID>"
schedule.kind: "cron"
schedule.expr: "<cron表达式>"
schedule.tz: "Asia/Shanghai"
```

> ⚠️ **关键说明 — 渠道与投递目标（必读）**：
>
> **`<当前渠道>` 和 `<当前用户ID或群ID>` 必须从当前对话的 inbound metadata 中动态获取，不要硬编码：**
>
> | 平台 | delivery.channel | delivery.to 格式 |
> |------|-----------------|-----------------|
> | 企业微信 | `wecom` | 用户 ⁠sender_id（如 `mattyijielu`）或群 group_space ID |
> | 飞书 | `lark` / `feishu` | `user:ou_xxx` 或 `chat:oc_xxx` |
> | Telegram | `telegram` | 用户 chat_id |
> | Discord | `discord` | channel_id 或 user_id |
> | Slack | `slack` | channel_id 或 `@username` |
> | WhatsApp | `whatsapp` | 手机号 |
>

企业微信特别注意： ⁠delivery.channel⁠  必须填  ⁠wecom⁠ （不是  ⁠openclaw-wecom-bot⁠ ），后者没有主动推送能力
⛔ 企业微信私聊时， ⁠delivery.to⁠  必须填  ⁠sender_id⁠ （即 inbound metadata 中的  ⁠sender_id⁠  字段值，如  ⁠mattyijielu⁠ ）
⛔ 严禁使用  ⁠chat_id⁠ （如  ⁠wecom:T46790049A⁠  或  ⁠T46790049A⁠ ）作为  ⁠delivery.to⁠ ，这会导致消息无法送达
群聊触发时， ⁠delivery.to⁠  填 group_space ID，可从 inbound metadata 的  ⁠group_space⁠  字段获取
isolated agent 内部通过  ⁠message tool⁠  主动发送消息时，target 同样使用  ⁠sender_id⁠ ，不用 chat_id

3. **确认输出**：

```
✅ 已开启每日自动推送！
   推送时间：每天 {HH:MM}
   推送内容：游戏内容趋势情报（发送到你的企业微信）
   如需修改时间或关闭，告诉我即可。
```

## 修改 / 关闭

- 用户说"改成每天下午3点推送" → 更新 cron schedule
- 用户说"关闭自动推送" → 用 cron 工具移除对应任务
- 用户说"推送到群里" → 将 `delivery.to` 改为群聊 group_space ID，`payload.message` 中的 target 也同步修改
- 用户说"用英文推 / 切到英文版 / 中英两版都推" → 在 `payload.message` 内更新 `target_language=<en|both>`，下次推送即生效（详见 [language-policy.md](language-policy.md)）
