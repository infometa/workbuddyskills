# Step 5 · 装 QLearning（学堂）MCP

> ⬜ 可选 · 不装教练对话也能跑，装了能在「30 天行动计划」里给用户推真实学堂课程。

---

## 装它干啥

- 提供 `mcp__QLearning__*` 工具集（7 个工具：searchQlCourse / getRecommendedCourses / getCourseDetail / getLatestLearnedCourses / getCourseRank / chatWithXiaoQ / fetchMentorKnowledge）
- 教练对话 T3 工具用 `searchQlCourse` 按方向推 3-5 门课
- 用户可直接点链接进腾讯学堂学习

---

## 安装步骤（约 2 分钟）

### ① 申请太湖 PAT

打开 https://tai.it.woa.com/user/pat

1. 点「创建 PAT」
2. 名称随意（如 `qlearning-career-broker`）
3. 复制生成的 token（形如 `tai_pat_xxxxxxxxxxxxxxxxxxxx`）
4. ⚠️ 这个 token **只显示一次**，关掉页面就看不到了，立刻复制保存

> **复用提醒**：如果你 `~/.workbuddy/mcp.json` 里已经为 km / recruit-mcp 配过 Bearer token，**同一个 PAT 在 mcpgw 系列共享**——可直接复用，不用再申请新的。

### ② 把 PAT 贴回对话

直接对 agent 说："这是我的太湖 PAT：tai_pat_xxxxx"

agent 会自动追加到 `~/.workbuddy/mcp.json`：

```json
{
  "mcpServers": {
    "QLearning": {
      "url": "https://qlearning.mcp.it.woa.com/api/mcp",
      "transportType": "streamable-http",
      "timeout": 300000,
      "headers": {
        "Authorization": "Bearer <你的 PAT>"
      },
      "disabled": false
    }
  }
}
```

> 其他 mcpServers 段不会动。

### ③ 重启 WorkBuddy 客户端

⌘Q 完全退出 → 重新打开。

> **必须完全退出**——关窗口 ≠ 退出。

### ④ 在「专家 - 连接器 - 自定义连接器」里点「信任」（首次必做）

重启后打开 WorkBuddy 客户端的「专家」→「连接器」→「自定义连接器」，QLearning 后面会有黄色提示条：

```
首次连接此 MCP 服务需要您的信任确认。  [信任]
```

**必须点这个「信任」按钮**——仅写 mcp.json + 重启还不够，这是 WorkBuddy 安全机制。

完成后状态点变绿。

---

## 验证装好了

WorkBuddy 主对话输入：

```
帮我搜下学堂里 AI 产品相关的课
```

应该返回 5-10 门课程（带标题 / 类型 / 链接）。

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 「自定义连接器」里看不到 QLearning | mcp.json 没改对 / 没重启 | 检查 `~/.workbuddy/mcp.json` 含 QLearning 段 + 完全退出重启 |
| 看到了但状态点是红的 | 没点「信任」按钮 | 找面板里黄色条点「信任」 |
| 工具列表里没有 `mcp__QLearning__*` | 信任后会话还没刷新 | 开个新对话即可 |
| 调用 401 | PAT 失效 | 去 tai.it.woa.com/user/pat 重新申请 |
| `transportType` 拼错 | 必须是 `streamable-http` | 严格按上面 JSON 写 |

---

## 跳过会怎样

不装 QLearning，**经纪人不会推具体课程**——只会描述"该补哪几块能力 / 哪几个方向"，具体课程你自己去学堂搜或外部资源找。

涉及的两个场景：

- **你直接说"推几门课"** → 经纪人引导你装 QLearning；不装就只给"能力地图"（如"补一下 AI 产品 sense"），不给课名/链接
- **30 天行动计划里的「学」一行** → 装了写"学《具体课名》前 3 章"；没装写"学一下「<能力方向>」的入门内容（自己挑课/书/网课）"

**不存在"装一半"或"装了再说"的中间态**——任何时候只要 QLearning 不在工具列表里，经纪人都不许编课名/链接顶上去。

其他能力（画像 / 问询 / 教练对话其他工具 / 活水机会推荐）完全不受影响。

---

## 同步参考

- `skills/career-broker-core/references/setup/00-mcp-bundle.md` — mcpgw 全家一次装齐（QLearning / km 共用太湖 PAT）
- 教练对话里需要引导配置 QLearning 时，直接引用本文件即可
