# me — 听歌报告

## 听歌报告

获取用户的听歌报告，按日 / 周 / 月聚合统计听歌时长、Top 歌手、Top 歌曲、活跃时段、流派偏好、小众/尝鲜歌曲、连续听歌天数、听歌城市等数据。

> ⚠️ 该接口需要用户已登录，未登录会返回登录态错误。

按 `timeKey` 切换日 / 周 / 月报告，回包中只会有对应时间维度的字段。

**PATH：** `/me/report`

**请求参数 (`params`)：**

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `timeKey` | string | 否 | 时间维度：`"d"` 日报、`"w"` 周报、`"m"` 月报。不传或空串默认 `"m"` |
| `startTime` | int64 | 否 | 起始时间戳（秒）。日报传目标日期 0 点 0 分 0 秒的 Unix 时间戳，周报传目标周周一 0 点 0 分 0 秒的 Unix 时间戳。不传默认当天/当周。月报忽略此参数 |

**timeKey 选择指引：**

- "今天听了什么"、"今日听歌"、"今天的听歌报告"：`"d"`
- "本周听歌"、"这周听了多少"、"周报"：`"w"`
- "本月听歌"、"这个月听歌报告"、"月度报告"：`"m"`
- 用户没明确说时间维度：不传或传 `"m"`，走月报

**回包：**

回包中三个字段只会按 `timeKey` 返回对应的一个，其余为空。

| 字段        | 类型   | 说明                                     |
| ----------- | ------ | ---------------------------------------- |
| `dayData`   | object | `timeKey="d"` 时返回，见下方「日报字段」 |
| `weekData`  | object | `timeKey="w"` 时返回，见下方「周报字段」 |
| `monthData` | object | `timeKey="m"` 时返回，见下方「月报字段」 |

#### 通用条目

报告中的歌曲 / 歌手 / 流派 / 时段列表都使用同一个通用条目结构，按场景填充不同字段：

| 字段         | 类型   | 说明                    |
| ------------ | ------ |-----------------------|
| `sum`        | int32  | 数值，含义随场景变化（时长（秒）、次数等） |
| `songMid`    | string | 歌曲 mid（仅歌曲条目填充）       |
| `songName`   | string | 歌曲名（仅歌曲条目填充）          |
| `singerMid`  | string | 歌手 mid（歌曲 / 歌手条目均填充）  |
| `singerName` | string | 歌手名（歌曲 / 歌手条目均填充）     |

每个使用通用条目的位置在下文都会标注其场景类型（**歌曲条目** / **歌手条目** / **时段/流派条目**）。

> 时段/流派条目（如时段平均时长、`preferHour.preferInfo`）只填 `sum`，其余字段为空；条目所对应的时段 / 流派**靠数组下标定位**。

#### 带名称的条目

仅用于流派分布等需要展示名称的场景：

| 字段   | 类型   | 说明               |
| ------ | ------ | ------------------ |
| `name` | string | 名称（如流派名称） |
| `sum`  | int32  | 次数 / 时长        |

#### 日报字段（`dayData`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `listenTime` | int32 | 当日听歌时长（秒） |
| `activeHour` | int32 | 当日活跃时段（小时，0-23） |
| `averageTime` | array | 各时段平均时长（每项含 `currentAverage` / `nearAverage`，均为**时段/流派条目**：`sum` = 时长（秒）） |
| `singerListen` | array | 当日 Top 歌手列表（**歌手条目**，`sum` = 听歌时长（秒）） |
| `songListen` | array | 当日 Top 歌曲列表（**歌曲条目**，`sum` = 播放次数） |

#### 周报字段（`weekData`）

| 字段           | 类型  | 说明                                                  |
| -------------- | ----- | ----------------------------------------------------- |
| `listenTime`   | int32 | 本周日均听歌时长（秒）                                |
| `floatNumber`  | float | 对比上周浮动比例（正=上升 负=下降）                   |
| `averageTime`  | array | 各时段平均时长，结构同日报                            |
| `singerListen` | array | 本周 Top 歌手列表（**歌手条目**，`sum` = 时长（秒）） |
| `songListen`   | array | 本周 Top 歌曲列表（**歌曲条目**，`sum` = 次数）       |

#### 月报字段（`monthData`）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `monthDetailList` | array | 月度听歌明细列表 |
| `monthDetailList[].listenCount` | int64 | 当月听歌次数 |
| `monthDetailList[].dataTime` | string | 数据所属月份 |
| `monthDetailList[].exportTime` | string | 数据导出时间 |
| `monthDetailList[].songs` | array | 当月歌曲列表（**歌曲条目**） |
| `topDataList` | array | 月度 Top 数据列表（每月一条） |
| `topDataList[].selectType` | int32 | 数据维度类型 |
| `topDataList[].month` | string | 所属月份 |
| `topDataList[].topSinger` | array | 该月 Top 歌手（**歌手条目**，单元素列表，`sum` = 时长） |
| `topDataList[].topSong` | array | 该月 Top 歌曲（**歌曲条目**，单元素列表，`sum` = 次数） |
| `topDataList[].favSongMid` | string | 最爱歌曲 mid |
| `topDataList[].favSongName` | string | 最爱歌曲名 |
| `topDataList[].favSingerMid` | string | 最爱歌曲的歌手 mid |
| `topDataList[].favSingerName` | string | 最爱歌曲的歌手名 |
| `topDataList[].repeatSong` | object | 单曲循环之最 |
| `topDataList[].repeatSong.listenDate` | string | 循环日期 |
| `topDataList[].repeatSong.songMid` | string | 循环歌曲 mid |
| `topDataList[].repeatSong.songName` | string | 循环歌曲名 |
| `topDataList[].repeatSong.singerMid` | string | 歌手 mid |
| `topDataList[].repeatSong.singerName` | string | 歌手名 |
| `topDataList[].repeatSong.count` | int32 | 循环次数 |
| `topDataList[].midnightSong` | object | 深夜单曲 |
| `topDataList[].midnightSong.month` | int32 | 月份 |
| `topDataList[].midnightSong.hour` | int32 | 听歌时段（小时） |
| `topDataList[].midnightSong.songMid` | string | 深夜歌曲 mid |
| `topDataList[].midnightSong.songName` | string | 深夜歌曲名 |
| `topDataList[].midnightSong.singerMid` | string | 歌手 mid |
| `topDataList[].midnightSong.singerName` | string | 歌手名 |
| `topSinger` | array | 月度 Top 艺人（**歌手条目**，`sum` = 时长） |
| `topSong` | array | 月度 Top 歌曲（**歌曲条目**，`sum` = 次数） |
| `preferHour` | object | 最爱时段 |
| `preferHour.preferHour` | int32 | 最爱时段（小时，0-23） |
| `preferHour.preferInfo` | array | 各时段听歌详情（**时段/流派条目**，仅 `sum` 字段；时段顺序由数组下标对应） |
| `preferHour.songListen` | array | 该时段最爱歌曲（**歌曲条目**） |
| `consDays` | object | 连续听歌 |
| `consDays.conDays` | int32 | 连续听歌天数 |
| `consDays.conInfoList` | array | 连续听歌每日详情（**歌曲条目**，每条对应当日代表歌曲；`sum` = 1 表示当日有听歌，0 表示未听） |
| `consDays.topListen` | int32 | 单日最多听歌数 |
| `consDays.singerDay` | object | 连续听歌天数最多的歌手（**歌手条目**，`sum` = 该歌手连续听歌天数） |
| `consDays.songListen` | array | 连续听歌期间的歌曲（**歌曲条目**） |
| `topGenre` | object | 偏爱流派 |
| `topGenre.genreId` | int32 | 偏爱流派 ID |
| `topGenre.genre2Count` | array | 近六个月流派对应次数（**带名称的条目**，`name` = 流派名，`sum` = 次数） |
| `topGenre.genreSong` | array | 该流派代表歌曲（**歌曲条目**） |
| `nicheSongs` | object | 小众 / 热门偏好 |
| `nicheSongs.nichePercent` | int32 | 小众歌曲占比（百分比 0-100） |
| `nicheSongs.list` | array | 小众歌曲代表列表（**歌曲条目**） |
| `nicheSongs.hotPercent` | int32 | 热门歌曲占比（百分比 0-100） |
| `newSongs` | object | 尝鲜歌曲 |
| `newSongs.newSongCount` | int32 | 本月尝鲜歌曲数 |
| `newSongs.floatNumber` | float | 对比上月浮动比例 |
| `newSongs.lastNewSongCount` | int32 | 上月尝鲜歌曲数 |
| `newSongs.list` | array | 尝鲜歌曲代表列表（**歌曲条目**） |
| `listenCityInfo` | array | 听歌城市列表（按解锁时间排序） |
| `listenCityInfo[].cityId` | int32 | 城市 ID |
| `listenCityInfo[].cityName` | string | 城市名 |
| `listenCityInfo[].provinceId` | int32 | 省份 ID |
| `listenCityInfo[].provinceName` | string | 省份名 |
| `listenCityInfo[].countryId` | int32 | 国家 ID |
| `listenCityInfo[].countryName` | string | 国家名 |
| `listenCityInfo[].unlockTime` | int64 | 城市解锁时间戳（秒） |
| `listenCityInfo[].cityRank` | int32 | 城市排名 |

**听歌报告工作流：**

1. 用户问「今天/今日听了什么」「今天的听歌报告」：`/me/report`，传 `{"timeKey": "d"}`。
2. 用户问「本周/这周/周报」：`/me/report`，传 `{"timeKey": "w"}`。
3. 用户问「本月/月度」：`/me/report`，传 `{"timeKey": "m"}`，或直接传空 `{}`（默认月报）。

**听歌报告输出格式：**

- **日报**：当日听歌时长（换算为时分）+ 活跃时段 + Top 3 歌手（用 `singerName`）+ Top 3 歌曲（`songName` + `singerName`）。
- **周报**：本周日均听歌时长（换算为时分）+ 与上周浮动（用 `floatNumber` 转百分比，正负号区分上升/下降）+ Top 3 歌手 + Top 3 歌曲。
- **月报**：分版块呈现，建议顺序：
  1. Top 艺人（`topSinger` 前 3，用 `singerName`）+ Top 歌曲（`topSong` 前 3，`songName` + `singerName`）
  2. 最爱时段（`preferHour.preferHour` 转「X 点」）
  3. 连续听歌天数（`consDays.conDays`）+ 单日最多听歌数（`consDays.topListen`）+ 最常听歌手（`consDays.singerDay.singerName`）
  4. 偏爱流派 + 流派分布（`topGenre.genre2Count` 用 `name` + `sum` 展示）+ 代表歌曲（`topGenre.genreSong[].songName`）
  5. 小众 / 热门占比（`nichePercent` / `hotPercent`）
  6. 尝鲜歌曲数及对比上月浮动
  7. 听歌城市数（`listenCityInfo` 长度）+ 列出 `cityName`
  8. 月度 Top 板块（`topDataList`）：循环之最（`repeatSong.songName` + `count`）、深夜单曲（`midnightSong.songName` + `hour` 点）、最爱歌曲（`favSongName`）
- **时长换算**：`listenTime` 秒："X 小时 Y 分钟"，不足 1 小时时显示 "Y 分钟"。
- **名称展示**：直接使用回包中的 `songName` / `singerName` / `cityName` 等字段，**不要展示 `songMid` / `singerMid` / `cityId`** 等内部 ID。
- **空字段处理**：若 `songName`与`singerName` 均为空，则跳过该条不展示。
- **空版块**：回包中字段为空数组 / `null` 时，对应版块跳过不展示。
- **H5 链接**：输出中出现的每首歌、每位歌手均需附带 H5 链接，拼接规则见 SKILL.md「H5 链接拼接」