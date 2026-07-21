# 公共概念与规则

本文档包含所有业务域共享的公共内容，包括 CLI 安装要求、凭证配置、通用调用格式、返回格式、错误处理、通讯录查询方法和时间格式规范。

---

## CLI 安装与版本要求

- **包名**：`@wecom/cli`
- **安装命令**：

```bash
npm install -g @wecom/cli
```

- **检查安装**：

```bash
which wecom-cli || echo "NOT_INSTALLED"
```

---

## 凭证配置

### 检查凭证状态

```bash
wecom-cli auth show --auth-status
```

- 输出 `authorized` → 已配置
- 输出 `unauthorized` → 未配置，需执行初始化

### 配置凭证

```bash
wecom-cli init
```

> 交互式命令，引导用户完成授权配置，仅需执行一次。

---

## 通用调用格式

所有业务域的命令遵循统一格式：

```bash
wecom-cli <品类> <接口名> '<json入参>'
```

**品类列表**：

| 品类 | 说明 |
|------|------|
| `contact` | 通讯录 |
| `msg` | 消息 |
| `doc` | 文档 & 智能表格 |
| `schedule` | 日程 |
| `meeting` | 会议 |
| `todo` | 待办 |

**示例**：

```bash
wecom-cli msg send_message '{"chat_type": 1, "chatid": "zhangsan", "msgtype": "text", "text": {"content": "hello"}}'
```

---

## 通用返回格式

所有接口返回 JSON 对象，包含以下公共字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `errcode` | integer | 返回码，`0` 表示成功，非 `0` 表示失败 |
| `errmsg` | string | 错误信息，成功时为 `"ok"` |

**成功示例**：

```json
{
    "errcode": 0,
    "errmsg": "ok",
    ...
}
```

**失败示例**：

```json
{
    "errcode": 40001,
    "errmsg": "invalid credential"
}
```

---

## 通用错误处理与重试策略

1. **errcode 非 0**：说明接口调用失败，将 `errcode` 和 `errmsg` 展示给用户
2. **可重试错误**：遭遇 HTTP 错误或网络问题时，主动重试，最多重试 3 次
3. **不可重试错误**：参数错误、权限不足等，直接告知用户错误信息
4. **errcode 非 0 但可能是临时性错误**：可重试 1 次，若仍失败则展示错误信息

---

## 通讯录查询（userid ↔ 姓名转换）

多个业务域（消息、日程、会议、待办等）在涉及人员操作时，需要将用户姓名转换为 `userid`，或将 `userid` 转换为可读姓名。

### 获取通讯录

```bash
wecom-cli contact get_userlist '{}'
```

返回当前用户**可见范围内**的成员列表：

```json
{
    "errcode": 0,
    "errmsg": "ok",
    "userlist": [
        {"userid": "zhangsan", "name": "张三", "alias": "Sam"},
        {"userid": "lisi", "name": "李四", "alias": ""}
    ]
}
```

### 姓名 → userid（用于创建/修改操作）

1. 调用 `get_userlist` 获取全量成员
2. 按 `name` 或 `alias` 匹配目标人员
3. **精确匹配唯一结果**：直接使用
4. **模糊匹配多个结果**：展示候选列表让用户选择
5. **无匹配结果**：告知用户未找到

> ⚠️ 禁止根据用户姓名自行猜测 userid，必须通过通讯录查询获取。

### userid → 姓名（用于展示操作）

1. 调用 `get_userlist` 获取全量成员
2. 建立 `userid` → `name` 的映射关系
3. 展示时将 `userid` 替换为可读姓名
4. 若通讯录中找不到某个 ID，展示时标注"未知用户(ID：xxx)"

### 注意事项

- `get_userlist` 返回的是当前用户**可见范围内**的成员，非全量成员
- ⚠️ 超过 10 人时接口将报错，本功能仅适用于可见范围较小的场景
- `alias` 字段可能为空字符串，搜索时需做空值判断
- 若搜索结果有多个同名人员，需将所有候选人展示给用户选择，不得自行决定
- 只需调用一次 `get_userlist`，在本地对结果进行多次筛选，避免重复调用接口

---

## 时间格式规范

不同业务域的时间格式略有差异，请注意区分：

| 业务域 | 入参格式 | 返回格式 |
|--------|----------|----------|
| 消息 (msg) | `YYYY-MM-DD HH:mm:ss` | `YYYY-MM-DD HH:mm:ss` |
| 文档 (doc) | 无时间参数 | 无时间参数 |
| 日程 (schedule) | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:mm:ss` | Unix 时间戳（秒），需转为可读格式 |
| 会议 (meeting) | `YYYY-MM-DD HH:mm` | `YYYY-MM-DD HH:mm` |
| 待办 (todo) | `YYYY-MM-DD HH:mm:ss` | `YYYY-MM-DD HH:mm:ss` |

### 相对时间支持

用户说"今天"、"明天"、"昨天"、"最近三天"、"下周一"等相对时间时，根据当前日期自动推算为具体日期时间。
