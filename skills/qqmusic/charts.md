# charts — 排行榜

查看 QQ 音乐各类排行榜，按分组展示。

## 接口

### 排行榜分组

获取所有榜单分组及每组下的榜单摘要（含前几首歌）。

**PATH：** `/charts`

**请求参数 (`params`)：** 无

**回包：**

| 字段                                               | 类型   | 说明                          |
| -------------------------------------------------- | ------ |-----------------------------|
| `groupList`                                        | array  | 榜单分组列表                      |
| `groupList[].groupName`                            | string | 分组名称（如巅峰榜、地区榜）              |
| `groupList[].groupTopList`                         | array  | 该分组下的榜单                     |
| `groupList[].groupTopList[].topId`                 | int32  | 榜单 ID，用于 `/charts/detail` 查详情 |
| `groupList[].groupTopList[].topName`               | string | 榜单名称（如热歌榜、新歌榜、飙升榜）          |
| `groupList[].groupTopList[].listenNum`             | int32  | 收听人数                        |
| `groupList[].groupTopList[].totalNum`              | int32  | 榜单歌曲总数                      |
| `groupList[].groupTopList[].songList`              | array  | 榜单前几首歌                      |
| `groupList[].groupTopList[].songList[].rank`       | int32  | 排名                          |
| `groupList[].groupTopList[].songList[].songName`   | string | 歌曲名                         |
| `groupList[].groupTopList[].songList[].singerName` | string | 歌手名                         |

### 榜单详情

查看某个榜单的完整信息及全部歌曲。

**PATH：** `/charts/detail`

**请求参数 (`params`)：**

| 参数    | 类型  | 必填 | 说明                                       |
| ------- | ----- | ---- | ------------------------------------------ |
| `topId` | int32 | 是   | 榜单 ID，从 `/charts` 获取                 |
| `page`  | int32 | 否   | 分页页码，默认 0；服务端按固定页大小切分 |

**回包：**

| 字段                     | 类型   | 说明               |
| ------------------------ | ------ | ------------------ |
| `topId`                  | int32  | 榜单 ID            |
| `topType`                | int32  | 榜单类型           |
| `topName`                | string | 榜单名称           |
| `topDesc`                | string | 榜单描述           |
| `topHeaderPic`           | string | 榜单头图 URL       |
| `topBannerPic`           | string | 榜单 Banner 图 URL |
| `listenNum`              | int32  | 收听人数           |
| `totalNum`               | int32  | 歌曲总数           |
| `updateTime`             | string | 更新时间           |
| `hasMore`                | bool   | 是否有更多         |
| `trackList`              | array  | 歌曲列表           |
| `trackList[].songMid`    | string | 歌曲 mid           |
| `trackList[].songName`   | string | 歌曲名             |
| `trackList[].singerName` | string | 歌手名             |
| `trackList[].songH5Url`  | string | H5 详情页链接      |

## 工作流

1. 用户想看排行榜 → `/charts`，按分组展示榜单列表。
2. 用户选某个榜单 → `/charts/detail`，传入 `topId` 获取完整歌曲列表。
3. 支持分页：通过 `page` 翻页，根据 `hasMore` 判断是否还有更多。

## 输出格式

- 榜单按分组归类展示，每个榜单标注收听人数 + H5 链接（接口未返回时按 `https://i2.y.qq.com/a/toplist/{topId}` 拼接）
- 榜单详情：榜单名称 + 描述 + 更新时间 + 歌曲列表（排名 + 歌名 + 歌手 + 播放链接 H5）
