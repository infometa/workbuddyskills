# tmeet record — 录制管理

> 已登录后使用；未登录时按主 SKILL 完成授权。示例中的 ID、链接、密码和 token 都是占位值，执行时使用真实值。

时间使用 ISO 8601，包含时区，例如 `2026-03-12T14:00:00+08:00`。content/access 每次只查一种内容，不支持组合读取；CLI 不自动追页，不支持 all/out 参数。响应使用公共信封，业务 data 按各命令说明读取。

## 目录

- [录制查询路由总则](#录制查询路由总则)
- [search — 找/搜录制](#search--找搜录制)
- [content — 读录制内容](#content--读录制内容)
  - [子形态总览](#子形态总览)
  - [minutes(file) — 单文件智能纪要](#minutes--file---单文件智能纪要)
  - [minutes(url) — 分享链接纪要](#minutes--url---分享链接纪要)
  - [todos — 单文件待办](#todos--单文件待办)
  - [transcript(details) — 单文件转写正文](#transcript--details---单文件转写正文)
  - [transcript(search) — 单文件内检索](#transcript--search---单文件内检索)
  - [transcript(url) — 分享链接转写](#transcript--url---分享链接转写)
  - [paragraphs — 转写段落列表](#paragraphs--转写段落列表)
  - [timeline — 智能时间轴](#timeline--智能时间轴)
- [access — 查访问信息与配置](#access--查访问信息与配置)
- [share-set — 修改分享与授权成员](#share-set--修改分享与授权成员)
- [settings-set — 修改智能录制配置](#settings-set--修改智能录制配置)
- [permission-apply — 预览与提交权限申请](#permission-apply--预览与提交权限申请)
- [输出与分页](#输出与分页)
- [典型工作流](#典型工作流)
- [常见错误](#常见错误)
- [参考](#参考)

---

## 录制查询路由总则

先复用已有目标；只有缺少后续操作必需的信息时才补查。下表是选择表，不是依次执行的步骤。

| 用户已有信息或目标 | 入口 | 注意 |
|------|------|------|
| 文件 ID，要纪要/待办/原文 | `content --record-file-id`，选择对应 action | 直接读，不固定补查地址或会议权限 |
| 录制 ID，要地址/分享配置/成员 | `access --meeting-record-id`，选择对应 action | 不把录制 ID 当文件 ID |
| 录制访问链接，要纪要或转写 | `content --share-url`，选 minutes 或 transcript | 无需先补文件 ID 或查询会议 |
| 查自己已有权限的录制、录音或上传文件 | `record search` | 时间、关键词、会议范围和文件类型可组合 |
| 记得原文关键词，不知哪条录制 | `record search --query-field transcript_content --query` | 跨录制检索，仅覆盖已有访问权的录制 |
| 已知文件，在其中找原话 | `content --action transcript --record-file-id --text` | 单文件检索；只有位置时再取正文 |
| 指定会议号/ID，需发现该会录制及权限 | `meeting get` | 可发现无权限录制及 permission_status |
| 按会议主题/创建人找某场会议的录制 | `meeting search`；缺必要录制信息时再 `meeting get` | 会议主题与录制标题可能不同 |
| 按时间找多场已结束会议及录制权限 | `meeting list-ended` | 与查已有权限的录制列表区分 |

用户明确只查可访问的录制时，可直接用 search 的 meeting-id/meeting-code 过滤。search 命中后不额外检查每条权限；按会议线索定位、了解录制权限或补齐必要会议信息时走上表的会议链路，已有可靠文件 ID/链接则直接读。

| 已知状态 | 处理 |
|------|------|
| state 为录制中/转码中 | 等待就绪，不读内容或申请权限 |
| permission_status 为 can_view | 按需求读取 |
| permission_status 为 can_apply，且已转码完成 | 需要申请时先 prepare，展示后由用户确认 commit |
| permission_status 为 closed/deleted | 告知不可申请或已删除，不进入申请流程 |
| permission_status 为 password_required | 仅在支持 pwd 的路径使用用户提供的密码，不转为权限申请 |
| search 空结果、缺少 records 字段或一般读取错误 | 说明已查询范围；必要时查询会议权限，不能据此判定不存在或可申请 |

会议查询失败不能直接推断用户未参会或无权访问录制；可按目标改用 `record search --meeting-code` 查已有权限的录制，不反复执行同一失败查询。

**目标与内容边界**：会议 ID 用于会议范围；meeting_record_id 用于地址、分享、成员、申请（**申请前的 can_apply/转码状态只能从 meeting 域查，见 permission-apply 节**）；record_file_id 用于内容和智能配置。分享链接使用用户提供的录制访问链接或地址响应的 view_address，不把任意媒体下载地址当分享链接。同一录制可能有多个文件，需唯一操作目标但无法确定时请用户选择。

只要待办且已有文件 ID 就选 todos；已取纪要中的待办足够时复用。原话只能引用实际转写正文，纪要、时间轴、段落目录及检索位置都不能代替原话。

---

## search — 找/搜录制

统一查询已有权限的录制；无关键词也可使用。**默认只查最近 30 天。** 用户指定更早或明确的时间范围时，同时填写 start/end，避免依赖单边时间参数的默认行为。不能把默认窗口未命中当作全部历史无结果。

```bash
# 最近 30 天内按原文关键词检索
tmeet record search --query "季度目标" --query-field transcript_content

# 指定更早时间段；按需增加会议范围或文件类型
tmeet record search --start "2026-07-01T00:00+08:00" --end "2026-07-31T23:59:59+08:00" --file-type video

# 同一原文检索继续下一页，保留原筛选条件
tmeet record search --query "季度目标" --query-field transcript_content --page-size 30 --page-token "<next_page_token>"
```

### 参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--query <text>` | 否 | — | 关键词，最大长度 50 |
| `--query-field <f>` | 否 | `all` | `subject`-录制主题；`creator`-创建者昵称/备注；`transcript_content`-原始转写；`smart_minutes`-纪要和待办；`timeline`-时间轴；`todo`-待办；`all`-全部 |
| `--file-type <t>` | 否 | `all` | `video`、`audio`、`transcript`、`upload`、`external`、`all` |
| `--meeting-id <id>` | 否 | — | 会议 ID 过滤 |
| `--meeting-code <code>` | 否 | — | 会议号精确过滤，纯数字、不带短横线 |
| `--start <time>` | 否 | 与 end 均省略时为最近 30 天起点 | 开始时间，ISO 8601 |
| `--end <time>` | 否 | 与 start 均省略时为当前时间 | 结束时间，ISO 8601；与 start 同传时须晚于 start |
| `--page-token <token>` | 否 | — | 首页不传；续页复制该查询返回的 token |
| `--page-size <n>` | 否 | `30` | 最大 30 |

### 响应字段

录制数组字段为 `data.record_meetings[]`；具体查询可能返回不同业务层级，应按实际字段读取，不重组回包。关键字段：

| 字段 | 用途 |
|------|------|
| meeting_record_id | 后续地址、分享、成员和申请的录制 ID |
| meeting_id / meeting_code | 会议上下文 |
| subject / state / record_type | 标题、录制状态、类型 |
| media_start_time / host_user_id | 录制开始时间、主持人 ID |
| record_files[] | 文件列表，含 record_file_id、record_start_time、record_end_time；部分条目可能不含此列表 |

仅在需要内容但缺文件 ID 时，根据已有会议/录制标识补查 meeting get 或 access address。search 不作为无权限录制的发现入口，也不依赖它返回 permission_status/url。缺字段时保留实际回包并说明缺失，不猜 ID 或反复改查询碰运气。

---

## content — 读录制内容

每次必填一个 action：minutes、todos、transcript、paragraphs 或 timeline。目标为 record-file-id 与 share-url 二选一。只传当前路径支持的业务参数；适用的全局参数仍按主 SKILL 执行。

### 子形态总览

form 只是文档和报错中的路径名称，**不是额外的 CLI 参数**。先按用户要的内容与已有来源选择一行，再填写该行参数。

| form | action | 必填业务参数 | 可选业务参数 |
|------|------|------|------|
| minutes(file) | minutes | record-file-id | lang、pwd |
| minutes(url) | minutes | share-url | lang、pwd、page-token、page-size |
| todos | todos | record-file-id | lang、pwd |
| transcript(details) | transcript | record-file-id | meeting-id、pid、limit |
| transcript(search) | transcript | record-file-id、text | meeting-id |
| transcript(url) | transcript | share-url | page-token、page-size |
| paragraphs | paragraphs | record-file-id | meeting-id |
| timeline | timeline | record-file-id | lang |

未列出的业务参数不适用。minutes 按文件/链接区分；transcript 传 share-url 走链接，传文件 ID 和 text 走检索，否则走文件正文。share-url 与 record-file-id/text 互斥；text 与 pid/limit 不能合用。operator_id/operator_id_type 由 CLI 自动处理，不自行添加。

### 参数取值

| 参数 | 说明 |
|------|------|
| `--action <a>` | 单选，不用逗号、数组或重复 action 组合内容 |
| `--record-file-id <id>` | 真实文件 ID |
| `--share-url <url>` | 录制访问链接，可对应多个文件；不是任意下载地址 |
| `--meeting-id <id>` | 仅表中支持的文件路径接收会议上下文 |
| `--lang <lang>` | `default`-原文、`zh`-简体中文、`en`-英文、`ja`-日语；minutes/todos 默认 default，timeline 不传或空值为原文 |
| `--pwd <pwd>` | 访问密码；仅表中支持的路径接收，缺密码时不猜测 |
| `--text <keyword>` | 非空的单文件检索关键词；不是 search 命令的 query 参数 |
| `--pid <id>` | 文件正文起始段落 ID，来自真实返回值，不是页码或 token |
| `--limit <n>` | 文件正文读取段落数，省略沿用现有服务默认；不能替换为 page-size |
| `--page-token <token>` | 仅链接路径接收，首页不传 |
| `--page-size <n>` | 仅链接路径接收，默认 5、最大 5 |

### minutes(file) — 单文件智能纪要

```bash
tmeet record content --action minutes --record-file-id "file_abc123"
```

按需加 lang/pwd；文件纪要不分页。保留原 meeting_minute 业务内容，其中已有 todos 且足以回答时直接复用，不再调用 todos。纪要不是逐字稿。

### minutes(url) — 分享链接纪要

```bash
tmeet record content --action minutes --share-url "https://meeting.tencent.com/recording/xxxxx" --page-size 5
```

按链接分页取得对应文件的纪要列表，无需先取文件 ID；按需加 lang/pwd。只持有链接且只要待办时，可从返回纪要中的结构化待办读取，不为改用 todos 额外补齐文件 ID。

### todos — 单文件待办

```bash
tmeet record content --action todos --record-file-id "file_abc123"
```

只要结构化待办时用本路径，不拉取整篇纪要。返回 `data.todos[]`：

| 字段 | 说明 |
|------|------|
| content | 待办正文；按实际文本读取，不因列表符号/@前缀格式差异判定为不同任务 |
| executorList[] | 执行人列表，无执行人时为空数组 |
| executorList[].nick | 执行人昵称 |
| executorList[].openId | 对应身份标识；无法匹配时可能为空，不编造、不为补齐而查通讯录 |

结构与纪要中的 meeting_minute.todos[] 一致。空数组表示本次未返回结构化待办；历史纪要也可能缺该字段，不据此断言会议从未产生待办。内容未生成、无权限或文件 ID 无效时保留原错误，不能把无权限错误直接转为申请。

### transcript(details) — 单文件转写正文

```bash
tmeet record content --action transcript --record-file-id "file_abc123" --pid "<paragraph_id>" --limit 10
```

不定位时省略 pid/limit。正文中实际返回的文字、说话人、时间与段落标识用于回答；有限范围读取不能称为全文。后续需要其他段落时使用真实定位信息，不计算 pid+1、不把 token 填到 pid；只有缺定位信息时才补查 paragraphs。

### transcript(search) — 单文件内检索

```bash
tmeet record content --action transcript --record-file-id "file_abc123" --text "季度目标"
```

不接收分页或正文定位参数。命中若只有 pid/sid/offset 等位置，就按真实 pid 调 details 取正文后再引用；若已返回足够原文则直接回答，不重复取正文。未知文件时才先用 record search 跨录制定位。

### transcript(url) — 分享链接转写

```bash
tmeet record content --action transcript --share-url "https://meeting.tencent.com/recording/xxxxx" --page-size 2
```

链接转写不接收 lang/pwd/text/pid/limit/meeting-id。原 data 包含 record_file_id、minutes[]、has_more、next_page_token；正文层级为 `minutes[] → paragraphs[] → sentences[] → words[]`，words 含 text、start_time、end_time，sentences 含 speaker。按 CLI 实际时间表示读取，不重复转换或凭摘要补原文。

### paragraphs — 转写段落列表

```bash
tmeet record content --action paragraphs --record-file-id "file_abc123"
```

含说话人与起止时间，用于段落浏览/定位。可加 meeting-id；不作为每次正文读取的固定前置步骤，不把目录、标题或位置当作发言原话。

### timeline — 智能时间轴

```bash
tmeet record content --action timeline --record-file-id "file_abc123" --lang zh
```

返回 AI 时间轴；不需要翻译时省略 lang。章节摘要不能替代逐字稿。

---

## access — 查访问信息与配置

每次必填一个 action，只查需要的一项，不同时补齐全部配置。

| action | 返回内容 | 必填参数 | 可选参数 |
|------|------|------|------|
| address | 播放/下载地址 | meeting-record-id | page-token、page-size（默认/最大 30） |
| sharing | 当前分享配置 | meeting-record-id | — |
| members | 已授权成员 | meeting-record-id | page-token；不接收 page-size |
| settings | 智能录制配置 | record-file-id | — |

```bash
tmeet record access --action address --meeting-record-id "record_abc123"
tmeet record access --action sharing --meeting-record-id "record_abc123"
tmeet record access --action members --meeting-record-id "record_abc123"
tmeet record access --action settings --record-file-id "file_abc123"
```

以上四条是互相独立的用法示例，不是执行清单。录制 ID 可来自 search 或会议录制信息；文件 ID 用于 settings。address 也支持非会议场景，已有录制 ID 时无需先查会议。view_address 用于录制访问，其他媒体地址按实际用途使用，不承诺永久有效。

修改分享、成员或智能配置前，只在缺少必要当前状态时查询对应 action；已有足够且有效的结果就复用。settings 中的未知状态不能自动解释成关闭。

展示授权成员按主 SKILL「成员回显」规则，缺显示名写「未知成员（open_id 前缀）」，不把 userid/OpenId/邮箱前缀当真实姓名。

---

## share-set — 修改分享与授权成员

> ⚠️ **写操作**：展示目标、具体变更及影响，取得真实确认后执行。已有明确确认覆盖同一目标和变更时复用，不把一般读取需求当作写授权。

至少提供一项配置或成员变更；支持在一次调用中组合配置修改、批量添加成员与批量移除成员。content/access 的单查限制不适用于此命令。

### 分享模式

| permission-point-id | 含义 | 需要 pwd |
|------|------|------|
| 1 | 所有人可查看 | 否 |
| 2 | 所有人需密码查看 | 是 |
| 3 | 所有人需申请权限 | 否 |
| 4 | 同企业可查看 | 否 |
| 5 | 同企业需密码查看 | 是 |
| 6 | 同企业需申请权限 | 否 |

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--meeting-record-id <id>` | ✅ | 目标录制 ID |
| `--switch-state` | 否 | 分享总开关；关闭显式传 `--switch-state=false`；与 permission-point-id 互斥 |
| `--permission-point-id <n>` | 否 | 分享模式 1～6；模式 2/5 必须提供 pwd |
| `--pwd <pwd>` | 按模式 | 4～10 位字母或数字密码；不沿用旧 password 参数 |
| `--expired-time-type <n>` | 否 | `0`-永久、`1`-7天、`2`-15天、`3`-30天、`4`-自定义；填枚举而非天数 |
| `--expired-time <time>` | 按类型 | ISO 8601，自定义类型 4 时必填；仅类型 4 生效 |
| `--download-enable` | 否 | 是否允许观看者下载；企业锁定下载时后端可能忽略，以实际结果为准 |
| `--view-minutes-enable` | 否 | 是否允许观看者查看转写与纪要 |
| `--rooms-enable` | 否 | 是否允许 Rooms 会议室设备查看 |
| `--add-members <openid:perm>` | 否 | 可重复；perm 为 `0`-查看、`1`-管理，省略默认 0 |
| `--remove-members <openid>` | 否 | 可重复，填真实 OpenId |

```bash
# 以下写示例只在具体变更已确认后执行
# 所有人凭密码查看
tmeet record share-set --meeting-record-id "record_abc123" --permission-point-id 2 --pwd "ab1234"

# 关闭分享；不同时传分享模式
tmeet record share-set --meeting-record-id "record_abc123" --switch-state=false

# 链接 30 天有效，枚举是 3
tmeet record share-set --meeting-record-id "record_abc123" --expired-time-type 3

# 自定义有效期
tmeet record share-set --meeting-record-id "record_abc123" --expired-time-type 4 --expired-time "2026-12-31T23:59+08:00"

# 同企业查看，并变更已确认的成员
tmeet record share-set --meeting-record-id "record_abc123" --permission-point-id 4 --add-members "openid_a:0" --remove-members "openid_b"
```

只传用户要改的项目；布尔关闭显式传 false，不把省略解释成关闭。成员优先使用已知 OpenId；需要按姓名完成授权动作时，可按主 SKILL 的通讯录规则解析，不能用 ms_open_id 替代或用于通用查人。

### 响应结构

响应中的 data 为 JSON 字符串，解析这一层后读取以下字段；若实际类型不同，保留原输出并记录差异，不强制重复解析。

| 字段 | 说明 |
|------|------|
| results[] | 各项包含 op（settings/add/remove）、ok、message、trace_id、原始 data，失败时含 error |
| succeeded / failed | 成功/失败子操作数 |

整体非零退出不代表全部失败。逐项报告结果，不整批重跑；超时或结果未知时先核对状态，不盲目重复写入。需要重试时只针对确认范围内、已核实失败的操作。

---

## settings-set — 修改智能录制配置

`tmeet record settings-set` 修改由 record-file-id 指定的单个录制文件的逐字稿和 AI 录制开关。它用于文件级配置，不用于设置预约会议的自动录制，也不用于修改分享权限。

仅询问命令用途或参数含义时，依据本节解释即可，无需查询账号或修改文件。需要操作具体文件时，优先复用已有真实文件 ID；缺少 ID 才按录制查询路由定位目标，不调用 record list。

> ⚠️ **写操作**：先按需取得配置，展示目标文件、拟改值及联动影响，用户明确确认后执行。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--record-file-id <id>` | ✅ | 文件 ID |
| `--subtitle-switch <n>` | 至少一项 | `1`-关闭、`2`-开启逐字稿 |
| `--enable-ai-switch <n>` | 至少一项 | `1`-关闭、`2`-开启 AI 录制 |

开启 AI 会一并开启逐字稿；关闭逐字稿会一并关闭 AI。不要传相互矛盾的目标值，写后按实际状态核对，不仅根据入参推断成功。

查询当前配置用 `record access --action settings --record-file-id`。只在缺少所需当前状态或写入结果未能确认时补查，已有可靠结果则复用。

开关状态不等于内容已生成。当前接口说明未确认开启开关是否会为历史录制补生成转写、重新生成纪要或何时完成；不能仅凭配置修改成功作此承诺。用户需要内容时，按需用对应 content action 读取实际结果。

```bash
# 已确认后同时开启
tmeet record settings-set --record-file-id "file_abc123" --subtitle-switch 2 --enable-ai-switch 2
```

---

## permission-apply — 预览与提交权限申请

进入流程前，必须从 **meeting 域** 命令（`meeting get` / `meeting list-ended` / `meeting search`，见 [tmeet-meeting](tmeet-meeting.md)）取得目标 meeting_record_id 对应的 `permission_status=can_apply` 且 `state` 非录制中/转码中；prepare 不是只读查询，用户说「告诉我」「不要提交」仅覆盖 commit，不覆盖 prepare 的前置核实义务。closed/deleted 不申请；password_required 走支持 pwd 的读取路径；普通无权限错误、空结果或缺字段都不能替代此判断。

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--action <a>` | 否 | prepare | prepare 只预览，commit 正式提交并触发审批 |
| `--meeting-record-id <id>` | ✅ | — | 预览与提交保持相同录制 ID |
| `--meeting-id <id>` | 否 | — | 已有会议上下文时提供，前后保持一致 |

```bash
# 预览，action 省略时也是 prepare
tmeet record permission-apply --action prepare --meeting-record-id "record_abc123"

# 展示有效预览、取得用户明确确认后才能提交
tmeet record permission-apply --action commit --meeting-record-id "record_abc123"
```

### 响应关键字段

以下为业务 data 中的字段路径：

| 阶段 | 字段 | 用途 |
|------|------|------|
| prepare | preview.meeting_record_id | 核对目标 |
| prepare | preview.approval_name / preview.subject | 申请类型、会议标题 |
| prepare | preview.file_owner / preview.apply_note / preview.applicant | 所有者、备注、申请人；展示给用户确认 |
| prepare | expires_in | 预览有效秒数，以返回值为准 |
| commit | unique_id / status / message | 申请 ID、状态、说明 |
| commit | approval_url / share_text | 供用户查看的审批链接和说明，不自动向他人发送 |

预览过期时重新 prepare，并核对目标、身份和拟提交信息；原确认仍有效且内容一致时复用，发生变化则重新确认。commit 结果未知时不自动重提，不增加 stage 或 confirm-token 参数。

---

## 输出与分页

响应使用公共信封与各能力的业务 data，不提供统一业务字段或额外包装。使用默认紧凑 JSON 排版；compact 会裁剪字段，仅在同版本、同路径已验证保留所需正文、ID 和续页信息时启用。不要常规将同一请求带/不带 compact 各执行一次。

| 查询 | 参数 | 数量说明 |
|------|------|------|
| search / access address | page-token、page-size，默认/最大 30 | 原接口列表项 |
| minutes(url) / transcript(url) | page-token、page-size，默认/最大 5 | 链接列表；不拿内部 words/paragraphs 数量反推页大小 |
| access members | page-token | 页大小沿用接口行为，不传 page-size |
| transcript(details) | pid、limit | 段落定位与读取范围，不是 token 分页 |
| 其他 content/access 路径 | 无 | 不附带分页参数 |

1. 首页不传 page-token；续页原样复制该查询的 data.next_page_token，保持 action、目标和原筛选条件，包括显式指定的页大小、语言、密码。
2. 每条查询独立保留 token；minutes 与 transcript、文件与链接之间不能串用。一次命令只取本次范围，按用户实际需要继续，不为完整而无条件翻页。
3. 非空 token 且无相反结束信号时可续页；空 token 或明确 has_more=false、且无相反信号时可结束。缺字段不能一概视为末页；has_more=true 却无 token、token 不前进或信号冲突时停止并说明已读范围。
4. 如果启用 compact 后缺少必要正文/续页字段，可去掉 compact 核对当前同一请求一次；仍缺失就记录问题，不循环重读。
5. 文件正文用真实段落定位继续；没有可靠续读依据时说明范围，不把部分结果称为全部。完整结果的连续读取和展示规则遵循主 SKILL。

---

## 典型工作流

### 已有文件，只要待办

直接 `content --action todos --record-file-id`；若已取得同一纪要的结构化待办则复用。无需先查会议、地址或智能配置。

### 找一句原话

未知文件时先 search 的 transcript_content 检索；已有文件则跳过。随后用 transcript(search) 定位；只有命中不含正文时，才用真实 pid 调 transcript(details)，例如：

```bash
tmeet record content --action transcript --record-file-id "file_abc123" --text "预算延期"
# 仅在上一步只有位置时执行
tmeet record content --action transcript --record-file-id "file_abc123" --pid "<matched_pid>" --limit 1
```

### 同时要纪要与原文

分别选 minutes 和 transcript，复用相同已知目标；两条查询各自保留分页条件。一侧失败时保留另一侧成功结果，不重新执行已成功的查询。

### 变更分享或申请权限

分享变更：按需读取当前状态 → 解析/确认目标成员 → 展示具体变更 → 真实确认 → 写入并核对。权限申请：可申请且已就绪 → prepare → 展示有效预览 → 确认 → commit；两条流程不能因读取失败互相替代。

真实账号的相依写测应先记录可恢复原值并确认变更及恢复范围，同一目标串行执行，检查后恢复并读回核对，再开始下一轮；恢复失败或状态被并发修改时停止，不覆盖他人变更。

## 常见错误

| 错误或异常 | 处理 |
|------|------|
| action 缺失/非法 | 按用户目标选择一个合法 action，不猜默认或组合多值 |
| `--xxx is not supported by --action yyy (form: zzz)` | 对照 form 表，修正当前目标路径的参数；不为使用某个 flag 换成另一个文件或来源 |
| 文件 minutes 带了 page-token/page-size | 删除多余分页参数；不能为分页擅自获取分享链接扩大读取范围 |
| transcript(search) 带了 pid/limit | 检索和正文分两步；先检索，再按真实位置读正文 |
| share-url 与文件 ID/text 混传 | 按原任务保留正确来源；不轮流试分支 |
| 缺必需 ID 或密码 | 先复用已有真实值，必要时按路由查询；仍不能确定时请用户补充，不猜测 |
| search 为空 | 先检查明确时间范围和查询字段，说明覆盖范围；不盲目换词，也不自动申请权限 |
| closed/deleted、录制中/转码中 | 停止相关读取/申请，说明状态 |
| 链接无效、过期或不支持 | 核对原链接或请求可用链接，不切换无关 action 试探 |
| token 缺失、不前进或结束信号冲突 | 按分页规则停止核对，不宣称已读完 |
| share-set 部分成功或写结果未知 | 检查各项/当前状态，不整批重跑或重复提交 |
| 分享参数不识别 | 核对 v1.0.20-internal.3 帮助；不回退到旧 enable-sharing/password 等参数碰运气 |

## 参考

- [tmeet](../SKILL.md) — 全部命令与通用规则
- [tmeet-meeting](tmeet-meeting.md) — 会议查询与录制权限
- [tmeet-minutes](tmeet-minutes.md) — 元宝纪要，与录制纪要区分
- [tmeet-report](tmeet-report.md) — 会议报告