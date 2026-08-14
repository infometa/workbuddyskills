# 嵌入式对话组件（chat-widget v3）

> 在阶段三 §3.6 中被引用。将对话组件嵌入到用户项目的页面中。
>
> v3 新增：多会话切换 + 上下文持久化（刷新不丢失）。

---

## 复制 widget 文件

复制 `assets/templates/chat-widget.js` 到 `{project}/public/chat-widget.js`。
复制 `assets/templates/agent-entry-widget-icon.svg` 到 `{project}/public/agent-entry-widget-icon.svg`。

---

## 注入到 HTML 页面

**自动**追加到 `public/index.html` 的 `</body>` 之前（已存在则跳过）：

```html
<!-- agent-boost: chat widget -->
<script src="chat-widget.js"></script>
<script>
  AgentChat.init({
    // serviceUrl 留空 = 自动推断（按页面 hostname 匹配 prod/dev 环境）
    agentName: '<agent-name>',
    owner: '<STAFF_NAME>'   // agent 所属用户（§0.0 MCP check_identity 获取），按用户隔离时必填
  });
</script>
```

### serviceUrl 地址解析（优先级从高到低）

| 优先级 | 方式 | 适用场景 |
|--------|------|------|
| 1 | URL 参数 `?server=xxx` | 调试用 |
| 2 | `init({ serviceUrl: '...' })` | 显式指定 |
| 3 | hostname 自动推断 | **默认行为，零配置** |

**默认自动推断规则**：
- `*.prod.hrainative.woa.com` → 生产 agent-server
- `*.app.hrainative.woa.com` → 开发 agent-server
- 其他（含 localhost）→ 开发环境地址

> **身份模型（owner vs caller）**：
> - **owner**：agent 的拥有者，决定加载哪份配置。通过 `owner: '<STAFF_NAME>'` 显式指定；不填时服务端按名兜底解析，多人同名可能命中错误 agent，故**建议必填**。
> - **caller**：正在对话的终端使用者，用于会话隔离与调用日志归属。**无需在 widget 配置**——chat-widget 直连 agent-server Gateway 域名，Gateway 从 OA cookie 解出身份并注入 `X-Staff-Name`。
>
> **直连方案说明**：chat-widget 直连 `https://agent-server.app.hrainative.woa.com`（agent-server Gateway 域名），`fetch` 请求携带 `credentials: 'include'`，浏览器自动带上 OA cookie。Gateway 验证 cookie 后注入 `X-Staff-Name`，agent-server 的 `get_caller()` 读取该头获得真实终端用户身份。
> 此方案**无需在用户应用注入反代代码**，也无需修改 `server.js`。agent-server 的 CORS 已配置跨域支持。

---

## 自动展开面板

URL 参数 `?chat=open` 可在页面加载后自动展开右下角对话面板（无需手动点击浮动按钮）。

| 参数值 | 效果 |
|--------|------|
| `open` / `1` / `true` | 自动展开 |
| 其他 / 缺省 | 默认折叠（仅显示浮动按钮） |

用法示例：`https://your-app.example.com/dashboard?chat=open`

> 可与其他 URL 参数组合使用，如 `?agent=my-agent&chat=open`。

---

## 多会话能力（v3）

### 功能说明

- **会话持久化**：刷新页面/关闭浏览器后重新打开，对话历史自动恢复
- **多会话切换**：侧边栏管理多个对话，可切换、重命名、删除
- **双重保障**：localStorage 缓存（快）+ 服务端会话 API 兜底（全量恢复）

### UI 布局

```
┌─────────────────────────────────────────┐
│ chat-hdr  [☰]  AI 助手    [+新对话] [✕] │
├──────────┬──────────────────────────────┤
│ sidebar  │  chat-msgs                   │
│ ┌──────┐ │  ┌─ user ─┐                 │
│ │会话1 │ │  └────────┘                 │
│ │会话2 │ │  ┌─ agent ─┐                 │
│ │会话3 │ │  └────────┘                 │
│ └──────┘ │                              │
│          │  ┌────────────────────┐     │
│          │  │ chat-input    [发送]│     │
└──────────┴──────────────────────────────┘
```

- 点击 `☰` 展开侧边栏（默认折叠）
- 点击 `+ 新对话` 创建新会话
- 点击会话项切换；hover 显示重命名(✎)和删除(✕)按钮

### 数据存储

| 层级 | 位置 | 内容 |
|------|------|------|
| 前端缓存 | `localStorage: agentchat:sessions:{agentName}:{owner}` | 会话列表 + 消息内容（含工具调用） |
| 服务端 meta | `chat_sessions` 表 | 会话标题、归属、时间戳 |
| 服务端消息 | LangGraph checkpointer（PostgreSQL） | 完整对话状态（messages、工具调用） |

**恢复流程**：
1. 页面加载 → 读取 localStorage（快，毫秒级）
2. localStorage 为空或首次访问 → 调 `/api/session/list` 拉取会话列表
3. 切换到某会话 → 若本地无消息则调 `/api/session/{tid}/messages` 懒加载

**容量保护**：
- 单会话最多保留 200 条消息（超出裁剪旧消息）
- 最多保留 100 个会话（超出淘汰最旧）

### threadId 约定

- 前端生成 `raw_tid`（如 `t1700000000abc`），发 invoke 时传 `raw_tid`
- 服务端组装完整 thread_id = `{owner}:{agent}:{staff}:{raw_tid}`，存入 checkpointer + chat_sessions
- 前端从 `list_sessions` 响应获取 `staffName`，自行组装完整 thread_id 用于会话 API

### 会话 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/session/list?agentName=&owner=` | GET | 列出当前用户的会话（meta only） |
| `/api/session/{threadId}/messages` | GET | 拉取某会话的完整历史消息 |
| `/api/session/{threadId}/rename` | POST | 重命名会话 |
| `/api/session/{threadId}` | DELETE | 删除会话（meta + checkpoint） |

> **权限隔离**：会话归属三元组 `(agent_name, owner, staff_name)` 必须匹配，防止越权访问他人会话。未登录（无 `X-Staff-Name`）时所有接口返回 401。

---

## 多页面支持

如果用户项目有多个 HTML 页面（如 `dashboard.html`、`report.html`），引导用户手动添加同样的 `<script>` 注入到各页面中。

对于 React/Vue 等 SPA 框架，提供通过 `<meta>` 标签配置的方式：

```html
<meta name="agent-name" content="my-agent">
<meta name="agent-owner" content="timmyuan">
<script src="chat-widget.js"></script>
```

---

## 版本升级

chat-widget.js 的 `WIDGET_VERSION` 字段（语义化版本）：
- 阶段三复制到用户项目时写入 `boost-state.json` 的 `widgetVersion`
- 后续重新执行 `/agent-boost` 时，对比版本号，不一致则自动覆盖用户项目的旧 widget

**v2 → v3 升级**：v3 引入多会话能力，需配合 agent-server 的会话 API（`/api/session/*`）。若 agent-server 未升级到支持会话 API 的版本，widget 会降级为本地模式（仅 localStorage，刷新仍可恢复，但无法跨设备同步）。
