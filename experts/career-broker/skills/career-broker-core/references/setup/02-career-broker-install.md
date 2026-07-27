# Step 2 · 装「鹅厂职业经纪人」插件

> 这是本插件本体——职业画像 / 测评解读 / 职业发展咨询 / 司内资源获取都在这里。
> 问询能力所需服务配置已随插件内置，用户安装时不需要填写服务密钥。

---

## 安装步骤（约 30 秒）

### ① 进入「技能-套件」面板

WorkBuddy 客户端左侧菜单 → 「技能-套件」。

### ② 添加套件

`<上线后填 marketplace 地址>` → 安装。

> **开发期 sideload**（暂未上 marketplace 时）：
> ```bash
> mkdir -p ~/.workbuddy/plugins/marketplaces/career-broker-local/plugins
> ln -s "<工程目录>/." \
>       ~/.workbuddy/plugins/marketplaces/career-broker-local/plugins/career-broker
> # 在 ~/.workbuddy/plugins/marketplaces/career-broker-local/.workbuddy-plugin/marketplace.json
> # 写入 marketplace 清单
> # 重启 WorkBuddy
> ```

### ③（首次）信任新挂载的 MCP

如果安装时 WorkBuddy 提示“是否信任新 MCP 服务”→ 点「信任」。

---

## 验证装好了

WorkBuddy 主对话输入：

```text
活水有试用期吗
```

应该返回结构化答案。失败按下面排查。

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 主对话不响应职业相关意图 | 主入口 agent 没注册 | 检查 plugin.json 的 `agents` 字段含 `./agents/career-broker.md` |
| 问询「活水有试用期吗」提示接口未连接 | recruit-mcp 未安装或未信任 | 按 `skills/career-broker-core/references/setup/06-recruit-mcp.md` 配置并在「专家 → 连接器 → 自定义连接器」点信任 |
| 活水问询无命中或置信度低 | 招聘问询知识库未检索到贴切条目 | 经纪人会尝试小Q兜底；两边都不可靠时不会凭训练知识编答案 |
| 装完没出现在主对话能力卡片里 | 客户端缓存 | 完全退出（⌘Q）重启 |

---

## 安装后立刻能用的能力

| 能力 | 触发示例 | 是否需要其他依赖 |
|---|---|---|
| 💬 职业问询 | “活水有试用期吗” | 活水/招聘问询需 recruit-mcp；其他职场问询需 QLearning |
| 🧬 测评解读 | “我想做测评 / 帮我解读 DNA” | ✅ 立刻可用 |
| 🧭 职业发展咨询 | “我最近卡住了” | ✅ 立刻可用 |
| 🪞 职业画像 | “帮我做画像” | 需要 recruit-mcp + Step 1 自评插件 |
| 🧰 司内资源获取 | “帮我找课程 / 经验文章 / 活水机会” | 课程需 QLearning；文章需 km；活水机会和画像 basic 需 recruit-mcp |
