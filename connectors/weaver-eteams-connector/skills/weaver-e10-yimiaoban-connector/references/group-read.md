# 群组读取（搜索 / 信息 / 成员 / 公告）

## 何时使用

找群、看群资料、拉群成员名单、找群主/管理员、判断群是否存在、读群公告。只读操作：

| operation | 用途 |
| --- | --- |
| `im.group.search` | 按条件搜群（`name`/`type`/`members`/`owner`/`creator`/`today`/`yesterday`/`createBegin`/`createEnd`，服务端过滤） |
| `im.group.info` | 群基础信息（`groupIds` 数组或 `groupId`，支持批量） |
| `im.group.users` | 群成员列表（`groupId`；`syncType` 0 全量/1 增量 + `clientUc` 游标） |
| `im.group.admins` | 群主/管理员批量获取（`mask` 位 1=群主/负责人、2=管理员，默认 3） |
| `im.group.exist` | 群是否存在（ret=0 存在；1209 不存在） |
| `im.group.userExist` | 某用户是否在群内 |
| `im.group.announce.get` | 群公告（`aid` 不传/0 = 最新） |
| `im.group.announce.list` | 公告列表（id 降序，`end_flag` 表示是否还有下一页） |

## 输入要点

- 搜群至少给一个条件；`type` 常见 1 普通/6 部门/7 全员。搜索/过滤全部由服务端完成，**禁止本地过滤结果**。
- `group.users` 默认返回 uid/cid/角色/入群时间（mask=142），**默认不含 `name` 位**；姓名由 CLI 逐条走 hrm 解析后回填 `name`。不要依赖接口自身的 name 字段。
- 成员增量同步：拿到 `server_uc` 游标后传 `syncType:1` + `clientUc` 拉增量。
- `group.announce.list` 单页若干条；还有更多时用返回的 id 锚点继续请求下一页。
- `group.announce.get` 返回 `found`（是否查到公告）+ `aid`/`annouce`/`addUserName`/`time`/`updateTime`/`mustRead`/`related`；查不到时为 `found:false`（不是报错）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.group.search --input-json '{"members":true,"pageSize":100}'
weaver-work-cli --profile eteams --json im run im.group.users --input-json '{"groupId":"1788334281700000004"}'
weaver-work-cli --profile eteams --json im run im.group.info --input-json '{"groupIds":["1788334281700000004"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.group.search --input-json '{"members":true,"pageSize":100}'
weaver-work-cli --profile eteams --json im run im.group.users --input-json '{"groupId":"1788334281700000004"}'
weaver-work-cli --profile eteams --json im run im.group.info --input-json '{"groupIds":["1788334281700000004"]}'
```

## 输出处理

- 群搜索结果：`data.groups[]` 每行是 `id`（群 id）/`name`/`type`/`num`（群人数）/`createTime`；结果量大时按共享规则汇总渲染（列群名/id/人数/类型），不要整表倾倒。
- 成员列表：`data.members[].name` 是 hrm 解析结果，角色取 `roleName`、入群时间取 `addTime`；响应还带 `totalNum`（成员总数）、`endFlag`、`serverUc`（增量同步游标）。展示大群成员时按需分页输出。
- 「谁在群里」用 `group.userExist`：返回 `users[].inGroup` 布尔，便于区分在群/不在群。
- 群公告内容同样"完整展示不截断"。

## 失败处理

- `1209`/群不存在：告知用户该群不存在或已解散。
- 空条件（`cond_required`）：补搜索条件。
- 只读操作，无确认链；认证失败参照共享规则。
