---
name: wecom-unified
description: "企业微信 CLI 全能套件，覆盖通讯录、消息、文档、日程、会议、待办 6 大业务域。支持按姓名/别名查找联系人、收发消息（文本/图片/文件/语音/视频）、读取/创建/编辑文档（可由'https://doc.weixin.qq.com/XXXX'链接触发）、读取表格（在线表格）内容、读写智能表格的子表/字段/记录、创建并导出智能文档、创建/修改/取消日程并查询闲忙、预约/管理会议、创建/跟踪/分派待办任务。即使用户未明确提到'企业微信'，只要消息中涉及doc.weixin.qq.com的url域名/消息/日程/待办/文档/表格/会议/找人等场景也应触发本技能"
description_zh: "企业微信 CLI 套件，覆盖文档/消息/日程/会议/待办/通讯录等业务功能。10人以上规模的企业，支持新建和读取文档/智能表格/智能文档；10人及以下个人及小团队，支持文档读写、收发单聊/群聊消息、日程/会议/待办管理、获取通讯录等能力。"
description_en: "WeCom CLI suite covering docs, messages, calendars, meetings, todos, and contacts. For organizations with 10+ members: create and read docs, smart sheets, and smart docs. For individuals and small teams (10 or fewer): read/write docs, send/receive direct and group messages, manage calendars, meetings, and todos, and look up contacts."
allowed-tools: Bash, Read
display_name: "企业微信套件"
display_name_en: "Wecom Unified"
version: 1.0.1
visibility: "public"
---

# 企业微信套件 (WeCom Unified)

企业微信 CLI (`wecom-cli`) 全能套件，通过命令行工具与企业微信系统交互，覆盖 6 大业务域：通讯录、消息、文档（含文档/表格/智能表格/智能文档 4 种品类）、日程、会议、待办。

## ⚠️ 前置检查 — 使用任何命令前必须执行

### Step 1: 检查 CLI 是否安装

```bash
wecom-cli --version
```

如果命令不存在或报错，执行安装：

```bash
npm install -g @wecom/cli@0.1.8
```

### Step 2: 检查凭证是否配置

```bash
wecom-cli auth show --auth-status
```

- 输出 `authorized` → 已配置，可以继续使用
- 输出 `unauthorized` → 未配置，需要执行 Step 3

### Step 3: 配置凭证（仅未授权时执行）

```bash
wecom-cli init --noninteractive
```

> ⚠️ 该命令会输出一个授权链接和二维码，并阻塞等待用户扫码完成验证。授权成功后命令会自动退出，仅需执行一次。

---

## 业务域概览

### 👤 通讯录 (contact)

获取可见范围成员列表、按姓名/别名搜索匹配、查询 userid。

→ 详见 [references/wecom-contact.md](references/wecom-contact.md)

### 💬 消息 (msg)

会话列表查询、消息记录拉取（文本/图片/文件/语音/视频）、多媒体文件获取、文本消息发送。

→ 详见 [references/wecom-msg.md](references/wecom-msg.md)

### 📄 文档、表格、智能表格 & 智能文档 (doc)

文档创建/读取/编辑（Markdown 格式），表格读取，智能表格子表管理、字段/列管理、记录增删改查，智能文档（智能主页）创建与内容导出。支持通过 docid 或 URL 定位文档，自动识别文档品类（文档/表格/智能表格/智能文档）并路由到正确接口。

→ 详见 [references/wecom-doc.md](references/wecom-doc.md)

### 📅 日程 (schedule)

查询日程列表与详情、创建/修改/取消日程、添加/移除参与人、查询多成员闲忙状态并分析共同空闲时段。

→ 详见 [references/wecom-schedule.md](references/wecom-schedule.md)

### 🎥 会议 (meeting)

创建预约会议、查询会议列表与详情、取消会议、更新受邀成员。

→ 详见 [references/wecom-meeting.md](references/wecom-meeting.md)

### ✅ 待办 (todo)

查询待办列表与详情、创建/更新/删除待办、变更用户处理状态（接受/拒绝/完成）、分派任务。

→ 详见 [references/wecom-todo.md](references/wecom-todo.md)

---

## 公共概念与规则

所有业务域共享的通用调用格式、返回格式、错误处理、通讯录查询方法和时间格式规范。

→ 详见 [references/wecom-shared.md](references/wecom-shared.md)

---

## 快速示例

### 查询通讯录成员

```bash
wecom-cli contact get_userlist '{}'
```

### 查看最近会话列表

```bash
wecom-cli msg get_msg_chat_list '{"begin_time": "2026-04-08 00:00:00", "end_time": "2026-04-15 23:59:59"}'
```

### 发送文本消息

```bash
wecom-cli msg send_message '{"chat_type": 1, "chatid": "zhangsan", "msgtype": "text", "text": {"content": "hello"}}'
```

### 创建文档

```bash
wecom-cli doc create_doc '{"doc_type": 3, "doc_name": "项目周报"}'
```

### 读取文档内容（Markdown 格式）

```bash
wecom-cli doc get_doc_content '{"docid": "DOCID", "type": 2}'
```

### 创建智能文档（智能主页）

> ⚠️ **特殊语法**：此命令必须使用 `+smartpage_create`（带 `+` 前缀），加号不可省略；该 `+` 仅适用于此命令，不要泛化到其他 `doc` 子命令。

```bash
wecom-cli doc +smartpage_create '{"title": "项目概览", "pages": [{"page_title": "需求文档", "content_type": 1, "page_filepath": "/path/to/requirements.md"}]}'
```

### 导出智能文档内容

```bash
wecom-cli doc smartpage_export_task '{"docid": "DOCID", "content_type": 1}'
```

### 查询今天的日程

```bash
wecom-cli schedule get_schedule_list_by_range '{"start_time": "2026-04-15 00:00:00", "end_time": "2026-04-15 23:59:59"}'
```

### 创建预约会议

```bash
wecom-cli meeting create_meeting '{"title": "周例会", "meeting_start_datetime": "2026-04-16 15:00", "meeting_duration": 3600}'
```

### 查看待办列表

```bash
wecom-cli todo get_todo_list '{}'
```

### 创建待办

```bash
wecom-cli todo create_todo '{"content": "完成Q2规划文档", "remind_time": "2026-04-20 09:00:00"}'
```
