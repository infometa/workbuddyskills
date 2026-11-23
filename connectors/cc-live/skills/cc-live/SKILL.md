---
name: cc-live
description: 查询和创建 CC 直播(获得场景视频)的直播间、直播场次、观看统计与回放数据。当用户提到直播间、直播数据、观看人次、峰值并发、回放、创建直播等需求时使用本技能的工具。
---

# CC 直播助手

数据全部来自当前授权用户的 CC 直播账号(用户隔离,只能操作自己的数据)。

## 工具清单与调用链

| 工具 | 输入 → 输出 |
|---|---|
| `query_room` | 关键词/状态 → roomId 列表 |
| `get_room_info` | roomId → 房间详情(状态/模板/开播时间等) |
| `get_live_list` | roomId(可选,留空查全部)→ 直播场次列表,含场次 id |
| `get_live_view_stats` | 场次 id → 总人次/峰值并发/峰值时刻/终端分布 |
| `get_record_list` | roomId(必填)→ 回放列表,含回放 id |
| `get_record_info` | 回放 id → 时长/观看地址/下载地址 |
| `create_room` | 名称等 → 新直播间 id + 推流/助教密码 |

## 标准调用链

- "某房间最近一场直播的数据" → `query_room` 拿 roomId → `get_live_list` 拿场次 id → `get_live_view_stats`
- "某房间的回放" → `query_room` 拿 roomId → `get_record_list` 拿回放 id → `get_record_info` 取观看/下载链接
- "创建一个直播间" → 直接 `create_room`

## 注意事项

- 时间参数格式统一为 `YYYY-MM-DD HH:MM:SS`(如 `2026-10-01 00:00:00`),留空表示不限;
- `create_room` 会真实创建直播间,返回结果里的 `publisherPass`(推流密码)与 `assistantPass`(助教密码)**必须转告用户**;
- 工具返回"未获取到 apiKey / 请在 MCP 客户端重新授权"时,提示用户在 WorkBuddy 中对该连接器重新绑定授权;
- 工具返回"无写权限"时,说明当前账号为子账号(只读),创建直播间需主账号操作。
