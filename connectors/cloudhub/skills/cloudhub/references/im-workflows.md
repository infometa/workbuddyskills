# im 核心工作流

> 本文档承接 [im.md](./im.md) 的「意图映射」「发消息前参数审查」「细节清单」之后，给出 7 个高频场景的完整 CLI 链路与命令速览。

## 给某人发私聊消息

私聊支持两种目标方式：

- 已有对方 openId：用 `--to-open-id`。
- 已有私聊会话 groupId：用 `--group-id`，不需要再转成 openId。

如果用户只说人名、手机号、工号或关键词，不要直接猜 openId：

```bash
yzj-cli contact user search --keyword "<关键词>"
```

从返回中选择目标用户的 `oId` / `openId`。如果结果有多个相似用户，先让用户确认。确认后：

```bash
yzj-cli im message send --to-open-id <OPEN_ID> --msg-type text --content "<消息内容>"
```

如果已经从最近会话或用户输入拿到了私聊会话 `groupId`：

```bash
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "<消息内容>"
```

## 给群发消息

用户只说群名或“最近那个群”时，先查最近群组：

```bash
yzj-cli im group recent --limit 20 --page 1
```

从返回中找目标群的 `groupId`。如果第一页没有目标群，继续扩大最近会话范围：

```bash
yzj-cli im group recent --limit 100 --page 1
yzj-cli im group recent --limit 100 --page 2
yzj-cli im group recent --limit 100 --page 3
```

多页仍未命中时，不要把“请提供群 ID”作为首选兜底。应说明当前 CLI 只能查最近会话，让用户打开目标群、提供更准确群名/成员线索，或在确实知道时再提供群 ID。

```bash
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "<消息内容>"
```

## 发送文件消息

如果用户给的是本地文件路径，不要直接调用 `im message send`。先上传文件：

```bash
yzj-cli file upload --file "<LOCAL_FILE_PATH>"
```

从返回中提取 `fileId`，再根据目标类型发送：

```bash
# 群聊文件
yzj-cli im message send --group-id <GROUP_ID> --msg-type file --file-id <FILE_ID>

# 私聊文件：通过 openId
yzj-cli im message send --to-open-id <OPEN_ID> --msg-type file --file-id <FILE_ID>

# 私聊文件：通过私聊会话 groupId
yzj-cli im message send --group-id <GROUP_ID> --msg-type file --file-id <FILE_ID>
```

如果用户已经提供 `fileId`，可以跳过上传。

## 发送富文本图片

如果用户给的是本地图片路径，先上传图片文件，再用返回的 `fileId` 作为 `--image`：

```bash
yzj-cli file upload --file "<IMAGE_PATH>"
yzj-cli im message send --group-id <GROUP_ID> --msg-type richText --content "[图片]图片说明" --image <FILE_ID>
```

多张图片按顺序逐个上传，发送时传多个 `--image` 值，正文里保留对应数量的 `[图片]` 占位：

```bash
yzj-cli im message send --group-id <GROUP_ID> --msg-type richText --content "[图片]第一张 [图片]第二张" --image <FILE_ID_1> --image <FILE_ID_2>
yzj-cli im message send --group-id <GROUP_ID> --msg-type richText --content "[图片]第一张 [图片]第二张" --image <FILE_ID_1> <FILE_ID_2>
```

## 回复一条消息

如果用户没有给 `msgId`，先查目标会话最近消息：

```bash
yzj-cli im message list --group-id <GROUP_ID> --type newest --limit 20
```

从返回中确认要回复的 `msgId`，再发送：

```bash
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "<回复内容>" --reply-msg-id <MSG_ID>
```

## 查看历史聊天记录

不知道会话 ID 时，先用 `im group recent` 找 `groupId`。查看最近消息不需要 `msgId`：

```bash
yzj-cli im message list --group-id <GROUP_ID> --type newest --limit 20
```

基于某条消息翻更早或更新记录时，必须传 `msgId`：

```bash
yzj-cli im message list --group-id <GROUP_ID> --msg-id <MSG_ID> --type old --limit 20
yzj-cli im message list --group-id <GROUP_ID> --msg-id <MSG_ID> --type new --limit 20
```

## @ 人或 @ 全员

消息正文里的 `@all`、`@姓名` 必须是独立片段：前面是行首或空格，后面跟一个空格，再接正文。例如 `@all 请关注`、`请 @张三 处理`；不要写成 `请@张三 处理`、`@all请关注`、`@张三请处理`。

不知道被 @ 人的 openId 时，先用通讯录搜索。正文里每个 `@姓名` 对应一个 `--at-open-id`：

```bash
yzj-cli contact user search --keyword "<姓名>"
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "@张三 请处理" --at-open-id <OPEN_ID>
```

多个 @ 用户时：

```bash
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "@张三 @李四 请处理" --at-open-id <ZHANGSAN_OPEN_ID> --at-open-id <LISI_OPEN_ID>
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "@张三 @李四 请处理" --at-open-id <ZHANGSAN_OPEN_ID> <LISI_OPEN_ID>
```

@ 全员必须显式传 `--at-all`：

```bash
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "@all 请关注" --at-all
```

## 命令速览

```bash
# 群聊文本
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "CLI 测试消息"

# 私聊文本：通过 openId
yzj-cli im message send --to-open-id <OPEN_ID> --msg-type text --content "CLI 私聊测试消息"

# 私聊文本：通过私聊会话 groupId
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "CLI 私聊测试消息"

# 群聊文件
yzj-cli im message send --group-id <GROUP_ID> --msg-type file --file-id <FILE_ID>

# 富文本图片
yzj-cli im message send --group-id <GROUP_ID> --msg-type richText --content "[图片]图片说明" --image <FILE_ID>

# 多图富文本
yzj-cli im message send --group-id <GROUP_ID> --msg-type richText --content "[图片]第一张 [图片]第二张" --image <FILE_ID_1> --image <FILE_ID_2>
yzj-cli im message send --group-id <GROUP_ID> --msg-type richText --content "[图片]第一张 [图片]第二张" --image <FILE_ID_1> <FILE_ID_2>

# @ 指定成员：每个 @姓名 对应一个 --at-open-id
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "@张三 请处理" --at-open-id <OPEN_ID>

# @ 全员
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "@all 请关注" --at-all

# 回复消息
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "收到" --reply-msg-id <MSG_ID>

# 获取最近聊天记录
yzj-cli im message list --group-id <GROUP_ID> --type newest --limit 20

# 基于锚点消息向前/向后翻页
yzj-cli im message list --group-id <GROUP_ID> --msg-id <MSG_ID> --type old --limit 20
yzj-cli im message list --group-id <GROUP_ID> --msg-id <MSG_ID> --type new --limit 20

# 获取最近群组会话
yzj-cli im group recent --limit 20 --page 1

# 上传本地文件，返回 fileId 后用于文件消息或富文本图片
yzj-cli file upload --file ./demo.txt
```
