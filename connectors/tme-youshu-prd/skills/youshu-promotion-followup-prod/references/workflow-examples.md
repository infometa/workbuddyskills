# 宣推跟进调用示例

以下ID、日期和URL均为格式示例，必须替换为本环境真实返回且由用户确认的对象。写入前展示实际歌曲、轮次、日期、跟进人和资源清单；不是默认执行脚本。

1. 页面搜索 `searchPromotionSongs`：`{"searchKey":"某歌手","pageNo":1,"pageSize":10}`；精确字段筛选：`{"singerName":"某歌手","trackName":"某歌曲"}`。读取content/totalCount，确认真实globalTrackId、planTrackId；该列表不是全曲库，空页不能作为创建新计划的依据。
2. 已有计划时 `listPromotionSchedules`：`{"planTrackId":123}`；`listPromotionFollows`：`{"tmeTrackId":123456}`。取真实轮次ID和候选userId。
3. `parsePromotionLinks`：`{"type":"DY_VIDEO","url":["https://www.douyin.com/video/实际视频ID"]}`。BGM/话题分别用DY_BGM/DY_TOPIC，不混组。精选页链接也可直接传入，例如 `https://www.douyin.com/jingxuan?modal_id=实际视频ID`；保持完整一行，不在协议或域名中插入回车/换行。创建与追加都使用解析返回的有效url，视频放dyVideoUrlList。校验UNRESOLVED时说明尚未提交写入，不当作createPromotionPlan的失败。
4. 用户确认后向已有轮次追加：

```json
{"planTrackId":123,"videoScheduleId":456,"promotePlatform":"DY","dyVideoUrlList":["https://www.douyin.com/video/实际视频ID"]}
```

没有计划时，经确认后 `createPromotionPlan` 的结构：

```json
{"globalTrackId":123456,"promotePlatform":"DY","followAccountIds":[789],"videoSchedule":{"scheduleName":"首轮","type":"FIXED_INVESTMENT","startTime":"2026-10-22","endTime":"2026-10-29","promotePlatform":"DY","followAccountIds":[789]},"dyVideoUrlList":["https://www.douyin.com/video/实际视频ID"]}
```

`createPromotionSchedule` 的字段与首轮类似，但平铺填写并传 `planTrackId`，不传 `videoSchedule` 或旧轮次ID。可同次传dyVideoUrlList/dyBgmUrlList/dyTopicList；成功直接返回新轮次ID，不再重复提交同批链接。超时先回查，不自动重建。

`queryPromotionPlanDetail` 和 `getPromotionEntry` 使用 `planTrackId`；视频/BGM/话题列表的 `taskId` 必须取详情返回的 `monitorTaskId`。真实字段与类型仍以实时Schema为准。

链接解析保留msg/url，并返回与输入等长的items，key为1开始的输入序号；按SUCCESS、DUPLICATE、UNRESOLVED对应来源行，保留原始与归一化URL，不猜测未提供的失败原因。请求超时后先回查计划、轮次和资源，不自动重新创建/追加。写入后调用getPromotionEntry；READY时展示miniProgramCodeUrl图片及有效期，FAILED/UNAVAILABLE时保留PC/小程序链接。本包需配套后端和小程序scene解析版本；READY图片不等于已经真机验收。

用户明确确认撤销视频后，调用 `removePromotionLinks`：`{"planTrackId":123,"monitorId":789}`。monitorId来自视频列表的trackMonitorId，不是platVideoId。仅撤销计划关联，不删除抖音源视频，不用于BGM/话题级联删除。

## 同视频换轮次

先核对视频当前scheduleId；若目标不同，明确说明原轮次将失去关联并影响统计，用户确认迁移后再append。成功仅表示受理，异步完成前保留待核验状态，不自动重试。
