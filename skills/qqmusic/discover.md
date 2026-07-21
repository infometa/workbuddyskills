# discover — 搜索、推荐与 AI 歌单

## 搜索

### 统一搜索

支持搜索歌曲、专辑、歌单、MV、电台、歌手，通过 `type` 参数切换。

**PATH：** `/discover/search`

**请求参数 (`params`)：**

| 参数      | 类型   | 必填 | 说明                         |
| --------- | ------ | ---- | ---------------------------- |
| `keyword` | string | 是   | 搜索关键词                   |
| `type`    | string | 否   | 搜索类型，默认 `"0"`（歌曲） |
| `page`    | int32  | 否   | 页码，从 0 开始，默认 0      |

**type 取值：**

| type  | 含义 |
| ----- | ---- |
| `"0"` | 歌曲 |
| `"1"` | 专辑 |
| `"2"` | 歌单 |
| `"3"` | MV   |
| `"4"` | 电台 |
| `"5"` | 歌手 |

**type 选择指引：**

- "搜歌""找某首歌"：`"0"`
- "搜专辑""xx的专辑"：`"1"`
- "搜歌单""xx歌单"：`"2"`
- "搜MV""xx的MV"：`"3"`
- "搜电台""xx电台"：`"4"`
- "搜歌手""xx是谁"：`"5"`
- 用户只说"搜xx"没限定类型：`"0"`

**回包（按 type 不同返回不同字段）：**

#### type="0"（歌曲）

| 字段                 | 类型   | 说明                               |
| -------------------- | ------ | ---------------------------------- |
| `songs`              | array  | 歌曲列表                           |
| `songs[].songMid`    | string | 歌曲 mid                           |
| `songs[].songName`   | string | 歌曲名                             |
| `songs[].singerName` | string | 歌手名                             |
| `songs[].songH5Url`  | string | H5 详情页链接                      |
| `hasMore`            | bool   | 是否有更多结果（所有搜索类型通用） |

#### type="1"（专辑）

| 字段                  | 类型   | 说明     |
| --------------------- | ------ | -------- |
| `albums`              | array  | 专辑列表 |
| `albums[].albumMid`   | string | 专辑 mid |
| `albums[].albumName`  | string | 专辑名   |
| `albums[].singerName` | string | 歌手名   |
| `albums[].publicTime` | string | 发行时间 |
| `albums[].listenNum`  | int64  | 播放量   |
| `albums[].category`   | string | 分类     |
| `albums[].albumDesc`  | string | 专辑描述 |

#### type="2"（歌单）

| 字段                      | 类型   | 说明       |
| ------------------------- | ------ | ---------- |
| `playlists`               | array  | 歌单列表   |
| `playlists[].dissId`      | int64  | 歌单 ID    |
| `playlists[].dissName`    | string | 歌单名称   |
| `playlists[].dissDesc`    | string | 歌单描述   |
| `playlists[].creatorName` | string | 创建者昵称 |

#### type="3"（MV）

| 字段               | 类型   | 说明          |
| ------------------ | ------ | ------------- |
| `mvs`              | array  | MV 列表       |
| `mvs[].mvVid`      | string | MV ID         |
| `mvs[].mvName`     | string | MV 名称       |
| `mvs[].singerName` | string | 歌手名        |
| `mvs[].playCount`  | int64  | 播放次数      |
| `mvs[].publicTime` | string | 发布时间      |
| `mvs[].mvUrl`      | string | MV 播放页链接 |

#### type="4"（电台）

| 字段                  | 类型   | 说明                       |
| --------------------- | ------ | -------------------------- |
| `radios`              | array  | 电台列表（字段和专辑相同） |
| `radios[].albumMid`   | string | 电台 mid                   |
| `radios[].albumName`  | string | 电台名                     |
| `radios[].singerName` | string | 演播者                     |
| `radios[].listenNum`  | int64  | 播放量                     |
| `radios[].albumDesc`  | string | 描述                       |

#### type="5"（歌手）

| 字段                   | 类型   | 说明     |
| ---------------------- | ------ | -------- |
| `singers`              | array  | 歌手列表 |
| `singers[].singerMid`  | string | 歌手 mid |
| `singers[].singerName` | string | 歌手名   |
| `singers[].songNum`    | int32  | 歌曲数   |
| `singers[].albumNum`   | int32  | 专辑数   |

**搜索工作流：**

1. 根据用户意图选择 `type`，调用 `/discover/search`。
2. 展示结果列表（编号），歌曲显示歌名+歌手+H5链接，专辑显示专辑名+歌手+发行时间+H5链接。

**搜索输出格式：**

- 编号列表展示，方便用户选择
- 歌曲：歌名 + 歌手 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/song/{songMid}` 拼接）
- 专辑：专辑名 + 歌手 + 发行时间 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/album/{albumMid}` 拼接）
- 歌单：歌单名称 + 创建者 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/playlist/{dissId}` 拼接）
- MV：MV 名称 + 歌手 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/mv/{mvVid}` 拼接）
- 电台：电台名 + 演播者 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/album/{albumMid}` 拼接）

---

## 每日推荐与猜你喜欢

### 每日 30 首

每日更新的个性化歌曲推荐。

**PATH：** `/discover/daily-mix`

**请求参数 (`params`)：** 无

**回包：**

| 字段                    | 类型   | 说明          |
| ----------------------- | ------ | ------------- |
| `songlist`              | array  | 推荐歌曲列表  |
| `songlist[].songMid`    | string | 歌曲 mid      |
| `songlist[].songName`   | string | 歌曲名        |
| `songlist[].singerName` | string | 歌手名        |
| `songlist[].songH5Url`  | string | H5 详情页链接 |

### 猜你喜欢

基于用户喜好的电台。

**PATH：** `/discover/radio`

**请求参数 (`params`)：** 无

**回包：**

| 字段                    | 类型   | 说明                           |
| ----------------------- | ------ | ------------------------------ |
| `songlist`              | array  | 电台歌曲列表（字段同每日推荐） |
| `songlist[].songMid`    | string | 歌曲 mid                       |
| `songlist[].songName`   | string | 歌曲名                         |
| `songlist[].singerName` | string | 歌手名                         |
| `songlist[].songH5Url`  | string | H5 详情页链接                  |

**推荐/电台工作流：**

1. 用户要推荐歌曲：`/discover/daily-mix`。
2. 用户要电台/随便听听：`/discover/radio`。
3. 展示推荐列表，每首歌显示歌名 + 歌手。

**推荐/电台输出格式：**

- 编号列表，每首歌：歌名 + 歌手 + 播放链接（H5）

---

## AI 歌单

### AI 歌单

根据用户意图通过 AI 推荐个性化歌单。

**PATH：** `/discover/ai-playlists`

**请求参数 (`params`)：**

| 参数      | 类型   | 必填 | 说明                                      |
| --------- | ------ | ---- | ----------------------------------------- |
| `reqType` | string | 是   | 歌单请求类型。传 `"all"` 获取 AI 歌单列表 |

**回包：**

| 字段                      | 类型   | 说明                      |
| ------------------------- | ------ | ------------------------- |
| `playlists`               | array  | AI 歌单列表               |
| `playlists[].dissId`      | int64  | 歌单 ID                   |
| `playlists[].dissName`    | string | 歌单名称                  |
| `playlists[].dissDesc`    | string | 歌单描述                  |
| `playlists[].creatorName` | string | 创建者（AI 歌单通常为空） |

**AI 歌单工作流：**

1. 用户说"生成歌单""推荐xx歌单"：`/discover/ai-playlists`，传 `{"reqType": "all"}`。
2. 用户选某个歌单看详情：使用 `/playlists/detail`（见 `playlists.md`）。

**AI 歌单输出格式：**

- 编号列表，歌单名称 + 描述 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/playlist/{dissId}` 拼接）