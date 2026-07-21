# playlists — 歌单详情

查看某个歌单的完整信息及全部歌曲。

## 接口

### 歌单详情

**PATH：** `/playlists/detail`

**请求参数 (`params`)：**

| 参数     | 类型  | 必填 | 说明             |
| -------- | ----- | ---- | ---------------- |
| `dissId` | int64 | 是   | 歌单 ID          |
| `page`   | int32 | 否   | 分页页码，默认 0 |

**回包：**

| 字段                     | 类型   | 说明                         |
| ------------------------ | ------ | ---------------------------- |
| `dissId`                 | int64  | 歌单 ID                      |
| `dissName`               | string | 歌单名称                     |
| `desc`                   | string | 歌单描述                     |
| `picUrl`                 | string | 歌单封面图 URL               |
| `totalNum`               | int64  | 歌曲总数                     |
| `hasMore`                | bool   | 是否有更多，false=无 true=有 |
| `trackList`              | array  | 歌曲列表                     |
| `trackList[].songMid`    | string | 歌曲 mid                     |
| `trackList[].songName`   | string | 歌曲名                       |
| `trackList[].singerName` | string | 歌手名                       |
| `trackList[].songH5Url`  | string | H5 详情页链接                |

## 工作流

1. 用户选某个歌单看详情 → `/playlists/detail`，传入 `dissId` 获取完整歌曲列表。

## 输出格式

- 歌单名称 + 描述 + 封面 + 歌曲列表（歌名 + 歌手 + 播放链接 H5）
