# Step 7 · 装「km MCP」（搜内部 KM 文章）

> ⬜ 推荐 · 用户问"经验/案例/实战/沉淀文章"类问题时按需引导装。共用太湖 PAT，已有 PAT 的话装它就一段配置的事。

---

## 装它干啥

- 提供 `mcp__km__*` 工具，主要用 km 搜索（搜内部 KM 文章、案例沉淀、实战复盘）
- 教练对话里用户问"有没有 X 的经验文章 / 谁写过类似的复盘 / 想看看实战案例"时，agent 调 km 搜内部沉淀
- 它跟 case 库（教练 T2 的 7 条结构化案例）是互补关系：
  - case 库：少而精，**结构化**的转型故事，用于"找像我这样的人"
  - km：多而杂，**长文/沉淀**，用于"看看别人怎么干的具体细节"

---

## 安装步骤（约 30 秒，太湖 PAT 复用）

### 一、确认你已经有太湖 PAT

```bash
grep "tai_pat_" ~/.workbuddy/mcp.json
```

- ✅ 有 → 复用，跳到第二步
- ❌ 没有 → 先去 https://tai.it.woa.com/user/pat 申一个，参 skills/career-broker-core/references/setup/00-mcp-bundle.md Step 1

### 二、加配置到 ~/.workbuddy/mcp.json

打开 `~/.workbuddy/mcp.json`（**注意：无点前缀**），把下面这段加到 `mcpServers` 里：

```json
"km": {
  "url": "https://prod.mcp.it.woa.com/paasfront_km-pro_woa_com/mcp",
  "headers": {
    "Authorization": "Bearer <你的 tai_pat_xxx>"
  },
  "disabled": false
}
```

把 `<你的 tai_pat_xxx>` 替换成你已有的太湖 PAT 全串（跟 QLearning / recruit-mcp 用的同一份）。

### 三、客户端「专家 - 连接器 - 自定义连接器」点信任

「专家」→「连接器」→「自定义连接器」→ 找到 `km` → 点「信任」→ 状态变绿。

---

## 验证装好了

随便让经纪人去搜个内部经验：

```
有没有腾讯内部讲 B 端产品转 C 端的复盘文章？
```

能返回 km 真实文章列表 = 装好了。

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 「自定义连接器」里找不到 km | mcp.json 没保存 / JSON 语法错 | `jq . ~/.workbuddy/mcp.json` 验证 |
| 调用报 401 | PAT 失效 / Bearer 前缀漏 | 检查 `Bearer ` + 空格；过期回 tai.it.woa.com 重新申 |
| 搜不到文章 | 关键词太宽 / 主题确实没人写 | 换关键词；或退一步给方向 |

---

## 跳过会怎样

不装 km，经纪人仍可工作——只是用户问"有没有内部沉淀文章 / 案例文章 / 经验复盘"时只能答"我这边没接 km，建议你直接去 km.woa.com 自己搜"。case 库（T2）的 7 条结构化案例不受影响。
