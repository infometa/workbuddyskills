# 字段值解析与上下文传递

> 用户在对话里通常用**名称**描述关联对象（"张三"、"项目攻坚群"），接口要的是 **ID**。只解析用户**明确提供**的字段值；未提及的字段不主动解析、不主动追问。

## ID 判定规则

- 纯数字且长度 **>= 10** → 视为 ID，直接使用（按字符串传）。
- 其余（中文、字母、短数字） → 视为名称，走名称 → ID 解析。
- uid/cid/群 id/消息 id 都是 uint64，JSON 中必须写成字符串，`0` 一律非法。

## 名称 → ID 解析

| 对象 | 解析方式 | 产出 |
| --- | --- | --- |
| 人员 | `im.person.resolve`（姓名/工号/手机/邮箱模糊，走 hrm） | `uid`、`cid`（**成对使用**，对方 cid 可能与本人不同） |
| 人员（批量） | `im.person.resolveByIds`（uid 列表 → 姓名/部门/cid） | 姓名、`cid`、部门、岗位 |
| 群聊 | `im.group.search`（`name` + `precise:true` 精确匹配） | `id`（群 id） |
| 系统消息分组 | `im.sysmsg.groupSearch`（名称模糊） | `groupId`、`typesIds` |

解析优先级：① 本对话已出现的实体直接复用（已解析的 uid/cid、已拉取会话里的群 id）；② 精确匹配；③ 模糊搜索 + 消歧。**禁止跳过前两步直接全量模糊搜索。**

## 同名 / 模糊命中的消歧

命中多个同名项时**必须先让用户选择**，禁止猜：

- 人员：`姓名（所属部门）`，如"张三（技术部）""张三（市场部）"。
- 群聊：`群名称（群 ID）`，如"测试群2（1787129175701000001）"。
- 候选超过 4 个只展示前 4 个并提示缩小范围。
- 人员候选优先按"是否出现在最近会话列表"排序，唯一命中时可用一句话确认。

## 未匹配到（total=0）

直接告知「人员名『XX』获取失败，请确认姓名是否输入错误」/「未找到该用户或者群聊，请检查名称是否正确」，**立即停止**。🔴 禁止通过回顾历史会话、拉会话列表、按相似名/部分名模糊搜索等方式去猜测、查找或推荐可能的人；未匹配就是未匹配。

## 接口间上下文传递契约

上游产出的字段直接喂给下游操作，禁止凭空构造或重新解析：

| 上游操作（产出） | 提取字段 | 下游操作（消费） |
| --- | --- | --- |
| `im.person.resolve` | `uid`、`cid` | `msg.send.single`（`toUid`/`toCid`）、`msg.sync.single`（`fromUid`/`fromCid`）、`ding.send`（单聊 `toUid`/`toCid`）、`group.invite`/`group.kick`/`group.create`（`users`） |
| `im.group.search` / `group.info` | `groupId` | `msg.sync.group`、`msg.send.group`、`ding.send`（群）、`group.users`/`group.admins`/`group.invite`/`group.kick`/`group.exit`/`group.destroy`/`group.modify`/`group.rename`/`group.announce.*` |
| `im.session.list` | 会话类型、`fuser.uid/cid`（单聊）、`lastMsgid`（翻页锚点）、系统会话 `group` | `msg.sync.single` / `msg.sync.group` / `sysmsg.query`；翻页传 `msgid` |
| `im.msg.sync.*` / `msg.top.sync` | `messages[].msgid`（`ser_msgid`）、`media[].fileId`、`nextStart` | `msg.withdraw`（`msgid`）、`msg.top.set`（`msgid`）、`ding.send`（`convertMsgid`）、`file.download`（`fileId`+`msgid`）、下一页 `start`/`startId` |
| `im.sysmsg.groupSearch` / `sysmsg.typeSync` | `groupId`、`typeId` | `sysmsg.query`（`group`/`type`） |
| `im.file.upload` | `fileObj.id` | 发消息的 `img`/`file`（或直接用本地路径让 CLI 内部上传） |
