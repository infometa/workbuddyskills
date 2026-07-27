# Step 0 · 一次装齐所有 MCP（推荐先看这篇）

> 进了任何一个 setup/0X 之前，先看这里——招活MCP 走一键授权（召唤专家时自动弹连接提示，最省事），QLearning / km 共用同一份太湖 PAT（一次申请、一次配置、处处复用）。

---

## 这个专家用到的 MCP 全家福

| MCP | 干啥 | 鉴权方式 | 接入入口 |
|---|---|---|---|
| **招活MCP**（`recruit-mcp`） | 画像 basic + 活水/招聘问询知识库 + 活水机会推荐 | **一键授权弹窗**（平台注入凭证，无需申请 token / 审批） | 召唤专家时自动弹连接卡；跳过了想再连就「切走再切回本对话」，卡会自动重弹 |
| **自评 MCP** | 画像感知主数据源 | **一键授权弹窗**（OAuth SSO，**不用太湖 PAT、不用装套件**） | 召唤专家时自动弹连接卡；跳过了想再连就「切走再切回本对话」重弹（旧客户端兜底见 setup/01） |
| **QLearning** | T3 课程推荐 + QA 兜底（小Q） | 太湖 PAT (`Authorization: Bearer tai_pat_xxx`) | https://tai.it.woa.com/user/pat |
| **km** ★ 推荐装 | 经验类问答（搜内部 KM 文章） | 太湖 PAT (`Authorization: Bearer tai_pat_xxx`) | https://tai.it.woa.com/user/pat |
| **tapd-woa**（可选） | 画像里的事项级证据 | 客户端 OAuth 连接器 | 客户端「连接器」面板点连接 |
| **gongfeng-woa**（可选） | 画像里的代码语言 | 客户端 OAuth 连接器 | 客户端「连接器」面板点连接 |

**关键事实**：
- **招活MCP、自评MCP 都是一键授权弹窗型**——召唤专家时客户端自动弹连接卡，点「连接」即可；如果一开始点了「暂不连接」、后面想连，**切到别的对话、再切回本对话，连接卡会自动重新弹出来**（不用自己进「自定义连接器」里翻）。平台自动注入凭证 / 走 SSO，**不用申太湖 PAT、不用申任何 token、不用审批、不用手填 mcp.json**。
- `QLearning` / `km`（以及 hr_data_service 等 mcpgw 系）**共用同一份太湖 PAT**——你之前为其中任意一个配过 PAT，这里**直接复用同一串，不用再去申**。

---

## 一站式安装流程（推荐）

### Step 0 · 先扫一眼你已经有什么

打开 `~/.workbuddy/mcp.json`（**注意：无点前缀**），找有没有 `Authorization: Bearer tai_pat_xxx` 这样的字段：

```bash
grep "tai_pat_" ~/.workbuddy/mcp.json
```

| 情况 | 你要做的 |
|---|---|
| ✅ 已经有 `tai_pat_xxx`（QLearning / km / hr_data_service 任一配过） | **直接复用同一串**——下面 Step 1 跳过申 PAT 这一步 |
| ❌ 没有 `tai_pat_xxx` | 进 Step 1 申一个，**这一份够用所有走 PAT 的 mcpgw 系 MCP（QLearning / km 等）** |

> 招活MCP 不在这张表里——它走一键授权，不用 PAT，也不用扫这一步。

### Step 1 · 申太湖 PAT（如果还没有）

打开 https://tai.it.woa.com/user/pat → 点「创建 PAT」→ 描述写"WorkBuddy MCP 通用"→ 复制保存 token（形如 `tai_pat_xxx.yyy`）。

> ⚠️ Token 关掉页面就看不到了，立刻复制保存。

### Step 2 · 看你需要哪几个

| 你打算用 | 必装 |
|---|---|
| 想做画像 | 招活MCP（setup/06，一键授权）+ 自评 MCP（setup/01） |
| 想问活水/招聘规则 | 招活MCP（setup/06，一键授权） |
| 想推课 / 30 天计划带具体课 | QLearning（setup/05） |
| 想看真实在招活水机会 | 招活MCP（setup/06，一键授权） |
| 想问"经验/案例/实战"类问题（搜内部 KM 文章） | km（setup/07） |
| 想画像里有"做过的事" | tapd-woa + gongfeng-woa（setup/03 + setup/04） |

**贪心组合**：招活MCP + QLearning + km + 自评 + tapd + gongfeng → 4 个 skill 全开。

### Step 3 · 一键连招活MCP / 自评MCP（无需写 mcp.json）

招活MCP、自评MCP 走平台一键授权：**召唤「鹅厂职业经纪人」时会自动弹出连接卡**，直接点「连接」完成即可；如果一开始点了「暂不连接」、后面想连，**切到别的对话、再切回本对话，连接卡就会自动重新弹出来**——不用自己进「专家 → 连接器 → 自定义连接器」里翻。

凭证由平台自动注入 / 走 SSO，**不用申 PAT、不用申任何 token、不用审批**。详见 setup/06、setup/01。

### Step 4 · 把还需手填 PAT 的 MCP 写进 mcp.json（QLearning / km）

QLearning 和 km 仍用太湖 PAT。打开 `~/.workbuddy/mcp.json`，把需要的段合并到 `mcpServers`（已有的别覆盖，加进去就行）：

```json
{
  "mcpServers": {
    "QLearning": {
      "url": "https://qlearning.mcp.it.woa.com/api/mcp",
      "transportType": "streamable-http",
      "timeout": 300000,
      "headers": {
        "Authorization": "Bearer <你的 tai_pat_xxx>"
      },
      "disabled": false
    },
    "km": {
      "url": "https://prod.mcp.it.woa.com/paasfront_km-pro_woa_com/mcp",
      "headers": {
        "Authorization": "Bearer <你的 tai_pat_xxx>"
      },
      "disabled": false
    }
  }
}
```

**占位符**：`<你的 tai_pat_xxx>` 是 Step 1 申到的 PAT，两处填同一份。写完后同样去「专家 → 连接器 → 自定义连接器」对 `QLearning` / `km` 点「信任」。

> 招活MCP 不在这段里——它走一键授权，不用手填。

### Step 5 · 自评 MCP 单独走一遍 setup/01（不走太湖 PAT 这条线）

详见 skills/career-broker-core/references/setup/01-self-assess-plugin.md。

### Step 6 · 可选连接器（tapd / gongfeng）

客户端「连接器」面板搜 TAPD / Gongfeng → 点连接 → OAuth 完成。详见 setup/03 / setup/04。

---

## 验证全装好了

随便问经纪人一句：

```
最近想看看活水有什么岗 + 有没有学堂的 AI 课
```

如果它能：
- 调招活MCP 回答活水问询或拉真实岗位 ✅ → 招活MCP OK
- 推 QLearning 真实课名 + 链接 ✅ → QLearning OK
- 不报"接口没装" ✅ → 全 OK

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 召唤专家没弹招活MCP / 自评MCP 连接卡 | 客户端版本旧 / 已连过 | 升级客户端；或切走再切回本对话让连接卡重新弹出 |
| 招活MCP / 自评MCP 点了连接没变绿 / 报 401 / 403 | 授权未完成或过期 | 切走再切回本对话让连接卡重新弹出，重新点「连接」 |
| 「自定义连接器」里找不到 QLearning / km | mcp.json 没保存 / 有 JSON 语法错误 | `jq . ~/.workbuddy/mcp.json` 验证；重新保存 |
| QLearning / km 调用报 401 | PAT 失效 / Bearer 前缀漏 | 检查 `Bearer ` + 空格；过期的话回 tai.it.woa.com 重新申 |
| 调用都正常但 agent 还说"没装" | 授权/信任后会话还没刷新 | 开个新对话即可 |

---

## 太湖 PAT 共享的边界（重要）

**同一份 `tai_pat_xxx` 可以被复用的范围**：走太湖 PAT 鉴权的 mcpgw 系 MCP——本专家相关的目前包括：

- `qlearning.mcp.it.woa.com`（QLearning · 本专家用）
- `prod.mcp.it.woa.com/paasfront_km-pro_woa_com/mcp`（km 知识库 · 不归本专家管）
- 其他 mcpgw 系 MCP 同理

**不用 / 不能复用 PAT 的**：

- 招活MCP（`recruit-mcp`）——已改为一键授权，平台注入凭证，不用手填 PAT
- 自评 MCP（套件方式 + 客户端连接器，根本没用 Bearer）
- TAPD / Gongfeng（OAuth 连接器，腾讯 OA SSO，不是 PAT）

---

## 相关文档

- 自评 MCP 单独装：`skills/career-broker-core/references/setup/01-self-assess-plugin.md`
- TAPD 连接器：`skills/career-broker-core/references/setup/03-tapd-connector.md`
- Gongfeng 连接器：`skills/career-broker-core/references/setup/04-gongfeng-connector.md`
- QLearning 详细教程：`skills/career-broker-core/references/setup/05-qlearning-mcp.md`
- recruit-mcp 详细教程：`skills/career-broker-core/references/setup/06-recruit-mcp.md`
