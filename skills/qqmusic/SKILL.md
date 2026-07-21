---
name: qqmusic
description: QQ Music — search songs, albums, playlists, music videos, artists; daily recommendations; music charts & rankings; AI-powered playlists; personalized listening reports & music insights. QQ音乐官方智能助手：搜索、每日推荐、排行榜、AI歌单、听歌报告、AI解读。
version: 0.0.2
---

# QQ音乐官方智能助手

通过 Agent Gateway 调用 QQ 音乐开放平台接口，提供搜索、推荐、排行榜、歌单等能力。

## 支持的能力

| 能力    | 说明                                   | 用户示例                                        | 详细说明           |
|-------|--------------------------------------|---------------------------------------------|----------------|
| 搜索    | 搜索歌曲、专辑、歌单、MV、电台、歌手                  | "帮我搜一下周杰伦" "搜晴天这首歌"                         | `discover.md`  |
| 每日推荐  | 每日 30 首个性化推荐                         | "今天推荐什么歌"                                   | `discover.md`  |
| 猜你喜欢  | 猜你喜欢电台                               | "给我推荐一些可能喜欢的歌曲"                             | `discover.md`  |
| AI 歌单 | AI 推荐歌单                              | "给我推荐一些跑步歌单"                                | `discover.md`  |
| 排行榜   | 查看各类音乐排行榜                            | "看看排行榜"                                     | `charts.md`    |
| 歌单详情  | 查看歌单完整歌曲列表                           | "看看这个歌单里有什么"                                | `playlists.md` |
| 听歌报告  | 按日/周/月聚合的听歌统计                        | "今日听歌报告" "本周听了多少"                           | `me.md`        |
| AI 解读 | 基于您的QQ音乐旅程进行解读，**只有用户明确是解读操作才调用此接口** | "分析我的听歌风格" "我是一个什么样的听众" "基于我的听歌记录推荐 10 首歌"  | `assistant.md` |
| 技能升级  | 检查 skill 版本更新，自动下载替换到最新版             | "更新 QQ音乐 skill" "升级 QQ音乐技能" "检查 QQ音乐有没有新版本" | `version.md`   |

调用任何接口前，必须先读取对应能力说明文件（如 discover.md、me.md），确认接口参数和字段含义后方可调用。禁止仅凭字段名猜测。

### 路由优先级（重要）

**结构化接口优先，AI 解读兜底。** 先判断用户意图是否命中前 7 项能力（搜索/每日推荐/猜你喜欢/AI 歌单/排行榜/歌单详情/听歌报告），命中则走对应接口；仅当用户明确要求"分析/解读/画像"（如"分析我的听歌风格""我是一个什么样的听众"）时才走 AI 解读。

常见误判场景：

- "推荐一些歌"、"给我推荐xx" → 走每日推荐/猜你喜欢/AI 歌单，**不要**走 AI 解读
- "今天听了什么"、"听歌报告" → 走 `/me/report`，**不要**走 AI 解读
- "搜一下xx" → 走 `/discover/search`，**不要**走 AI 解读

---

## 接口调用规范

### 统一入口

```text
POST ${BaseUrl}{path}
```

- `BaseUrl` 默认 `https://a.y.qq.com`
- `{path}` 是具体的接口路径，如 `/discover/search`、`/discover/daily-mix` 等，详见各能力说明文件

### 鉴权

- Header：`Authorization: Bearer $QQMUSIC_API_KEY`
- API Key 格式 `qmk-xxxxxxxx`，与用户账号绑定，需要用户身份的接口会自动识别调用者
- 获取 API Key：<https://y.qq.com/n/ryqq_v2/qqmusic_skills>
- 鉴权依赖环境变量 `$QQMUSIC_API_KEY`

**Key 初始化流程（首次使用或 Key 未设置时）：**

1. 先执行 `echo $QQMUSIC_API_KEY` 检查是否已设置
2. 已设置则直接使用，跳过后续步骤
3. 未设置则主动询问用户提供 Key
4. 用户提供后，检测当前 Shell 类型，将 `export QQMUSIC_API_KEY="<API Key>"` 写入对应 profile：
   - bash → `~/.bashrc`
   - zsh → `~/.zshrc`
   - 写入前检查是否已有旧的 QQMUSIC_API_KEY 配置，有则替换
5. 写入后执行 `source <profile文件>` 使其立即生效，然后继续后续调用

### 请求格式

- **Method**：POST
- **Content-Type**：application/json
- **Body**：JSON，`params` 存放业务参数，`comm` 存放公共参数，**每次请求必须带 `comm.skill_version`**

```bash
curl -X POST "${BaseUrl}/discover/search" \
  -H "Authorization: Bearer $QQMUSIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"params": {"keyword": "周杰伦", "type": "0"}, "comm": {"skill_version": "0.0.2"}}'
```

| 字段                   | 类型     | 必填 | 说明                               |
|----------------------|--------|----|----------------------------------|
| `params`             | object | 是  | 业务参数，具体字段见各能力说明文件                |
| `comm`               | object | 是  | 公共参数                             |
| `comm.skill_version` | string | 是  | 当前 SKILL 版本号，取本文件顶部 `version` 字段 |

### 请求方式

**正确：业务参数包在 `params` 内，`comm.skill_version` 与之并列。**

```json
{
  "params": {
    "keyword": "周杰伦",
    "type": "0"
  },
  "comm": {
    "skill_version": "0.0.2"
  }
}
```

**错误：业务参数平铺在顶层、没有 `params` 包裹。**

```json
{
  "keyword": "周杰伦",
  "type": "0",
  "skill_version": "0.0.2"
}
```

上面的错误写法会让下游拿不到任何业务参数，按默认值返回。

### 响应格式

所有接口的响应均包含公共字段 + 业务字段，平铺在顶层。以搜索为例：

```json
{
  "traceId": "61f801eb3f0d5420",
  "ts": 1780035265227,
  "songs": [
    {
      "songMid": "0039MnYb0qxYhV",
      "songName": "晴天",
      "songH5Url": "https://y.qq.com/n/ryqq/songDetail/0039MnYb0qxYhV",
      "singerName": "周杰伦"
    },
    ...
  ],
  "albums": null,
  "playlists": null,
  "mvs": null,
  "radios": null,
  "singers": null
}
```

| 字段        | 说明                                           |
|-----------|----------------------------------------------|
| `traceId` | 全链路追踪 ID                                     |
| `ts`      | 响应时间戳（毫秒）                                    |
| `ret`     | 网关层错误码，有值且不为0表示有异常                           |
| `sub_ret` | 业务层错误码，有值且不为0表示有异常                           |
| `msg`     | 错误描述                                         |
| 业务字段      | 如 `songs`、`songlist` 等，与公共字段平铺在顶层，具体见各能力说明文件 |

### 通用规则

1. **版本上报**：每次请求 `comm` 中必须携带 `"skill_version": "0.0.2"`（取本文件顶部 version 字段的值）
2. **参数包裹**：业务参数必须放在 `params` 对象内；`comm` 中仅放公共参数。
3. **能力文档预检**：调用任何接口前，必须先根据「支持的能力」表阅读对应说明文件，确认接口参数和字段含义；禁止仅凭字段名猜测。
4. **结果展示**：列表用编号展示；歌曲展示歌名 + 歌手；有 H5 链接时附带「播放」链接，各能力的输出格式详见对应能力说明文件。
5. **上下文衔接**：对话中记住已查询的歌曲、歌手，后续操作无需重复提供。
6. **禁止内联 Key**：所有 curl 命令中**必须使用 `$QQMUSIC_API_KEY` 环境变量**，绝对禁止在 curl 命令行里出现真实的 Key 值（如 `-H "Authorization: Bearer qmk-xxx"`）。把 Key 写入 Shell profile 是一次性的初始化操作，不在此限。

---

## 使用限制

1. **频率限制**：接口有 QPS 限制，请勿在循环中连续高频调用。若返回限流错误，请等待后重试。
2. **数据隐私**：`/me/report` 等接口返回您的个人听歌数据（听歌习惯、偏好流派等），请勿将结果分享给不信任的第三方。
3. **用途限制**：本 skill 仅供个人音乐查询和体验使用，禁止用于批量爬取曲库、数据挖掘、商业分析等未授权场景。如发现滥用，服务端有权撤销
   API Key。

---

## 技能升级

建议至少每周检查一次升级，详见 [version.md](version.md)

---

## H5 链接拼接

当接口回包中有 H5 链接时，优先使用回包中的；
当接口回包中没有 H5 链接时，可按以下规则自动拼接：

- 歌曲：`https://i2.y.qq.com/a/song/{songMid}`
- 专辑：`https://i2.y.qq.com/a/album/{albumMid}`
- 歌手：`https://i2.y.qq.com/a/singer/{singerMid}`
- MV：`https://i2.y.qq.com/a/mv/{mvVid}`
- 歌单：`https://i2.y.qq.com/a/playlist/{dissId}`
- 排行榜：`https://i2.y.qq.com/a/toplist/{topId}`
- 电台：`https://i2.y.qq.com/a/album/{albumMid}`
