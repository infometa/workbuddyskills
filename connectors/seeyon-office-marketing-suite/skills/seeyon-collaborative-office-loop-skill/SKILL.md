---
name: seeyon-collaborative-office-loop-skill
description: 在 Seeyon OA 中统一查询会议列表和详情、查询单位/部门/人员/岗位等组织信息、发起会议及发送自由协同，并复用 OA 环境变量认证会话。用户要求查询 OA 会议或组织架构、按人员/部门安排会议、检查会议时间冲突、上传可选附件、发送会议纪要或自由协同时使用；发起会议和发送协同默认直接执行，不额外要求用户确认。
---

# Seeyon 协同办公

使用 `scripts/seeyon_office.py` 作为唯一公开入口。脚本优先从环境变量登录 OA；账号或密码未配置时，复用连接器通过浏览器登录保存的本地会话。不要要求用户提供 Cookie、`JSESSIONID` 或 `route`。

## 准备认证

优先使用运行环境配置：

- `OA_BASE_URL`：完整 OA 登录地址。
- `OA_AUTH_USERNAME`：当前登录账号；同时作为会议主持人、记录人和自由协同发送人的默认登录名。
- `OA_AUTH_PASSWORD`：登录密码。

当 `OA_AUTH_USERNAME` 或 `OA_AUTH_PASSWORD` 未配置时，不要中止或要求用户复制 Cookie。先在 WorkBuddy 中连接“Seeyon 协同办公”连接器：连接器读取已配置的 OA 服务地址，打开隔离登录页面；用户登录成功后自动保存会话，当前 Skill 随后直接复用该 `sessionId`。`OA_BASE_URL`、`SEEYON_SERVICE_URL` 和连接器 `connector-config.json.serviceUrl` 按此顺序提供服务地址。

不要在命令、回复、日志或文件中展示这些变量的值。浏览器会话不可用时，只提示用户在 WorkBuddy 中重新连接对应连接器，不要索要 Cookie。

运行环境需要 Python 3.9+、`requests` 和 `pycryptodome`，版本范围见 `scripts/requirements.txt`。依赖缺失时，只有在用户授权修改环境后才能安装。

## 选择命令

```text
meeting-list        查询待开、已开、已发或待发会议
meeting-detail      按 meetingId 查询会议正文和详情
organization        查询单位、部门、人员、岗位、角色、职务级别或完整快照
meeting-create      检查分类、参与者和冲突后发起会议
collaboration-send  生成流程并发送自由协同
```

先运行帮助查看当前参数：

```bash
python scripts/seeyon_office.py --help
python scripts/seeyon_office.py meeting-create --help
```

若 `OA_BASE_URL` 无法正确推导业务根地址，使用当前命令的 `--base-url` 覆盖。不要把认证参数改为手工 Cookie。

## 执行只读查询

查询会议列表：

```bash
python scripts/seeyon_office.py meeting-list \
  --list-type send \
  --title "工作计划" \
  --begin-date "2026-08-01 00:00" \
  --end-date "2026-08-31 23:59"
```

`--list-type` 支持 `pending`、`done`、`send`、`wait` 及对应中文别名。

查询会议详情：

```bash
python scripts/seeyon_office.py meeting-detail --meeting-id "会议ID"
```

查询组织信息：

```bash
python scripts/seeyon_office.py organization accounts
python scripts/seeyon_office.py organization departments --account-id "单位ID"
python scripts/seeyon_office.py organization members --account-id "单位ID" --login-name "lisi"
python scripts/seeyon_office.py organization posts --account-id "单位ID"
python scripts/seeyon_office.py organization roles --account-id "单位ID"
python scripts/seeyon_office.py organization job-levels --account-id "单位ID"
python scripts/seeyon_office.py organization all --account-id "单位ID"
```

组织分页查询中途失败时，将返回已取得的数据并明确标记不完整；不要把部分结果描述为完整结果。

## 解析人员和部门

会议参与者支持：

- `Member|人员ID`
- `Department|部门ID`
- `member:登录名`
- `department:部门名称`
- 普通文本登录名或部门名称

普通文本必须在目标单位内精确且唯一匹配。人员和部门同时命中、零命中或多命中时，停止并请用户改用明确前缀或直接组织值，不猜测相似名称。

自由协同接收人使用登录名或完整人员 JSON。发送人未显式指定时使用 `OA_AUTH_USERNAME`。

## 发起会议

业务参数完整时直接执行会议分类查询、参与者解析、冲突检查和会议创建，不在发送前额外询问用户确认。只有用户明确要求预览或检查但暂不创建时，才增加 `--dry-run`。

直接创建示例：

```bash
python scripts/seeyon_office.py meeting-create \
  --account-id "单位ID" \
  --title "工作事项对称" \
  --content "<p>下午2点半，来1303，对称下近期工作安排</p>" \
  --begin-date "2026-08-11 14:30" \
  --end-date "2026-08-11 15:30" \
  --conferee "department:研发部" \
  --conferee "member:lisi" \
  --meeting-place "会议室1303"
```

默认从服务端会议分类中唯一选择“普通会议”。冲突查询返回人员明细时，最终结果完整展示 `memberName`、`title`、`startDate`、`endDate`、`category` 和 `categoryName`，冲突本身不阻止继续创建会议。冲突接口失败或响应无效时必须停止。

附件不是必填项。需要附件时重复使用：

```text
--attachment "D:/docs/报表.xlsx"
```

## 发送自由协同

业务参数完整时直接保存正文并发送自由协同，不在发送前额外询问用户确认。只有用户明确要求预览时才增加 `--dry-run`。

```bash
python scripts/seeyon_office.py collaboration-send \
  --account-id "单位ID" \
  --subject "会议纪要" \
  --content "<p>本次会议形成以下安排……</p>" \
  --recipient-login-name "lisi" \
  --recipient-login-name "wanger"
```

未提供原始流程 XML 时生成并行流程；提供 `--process-xml-file` 时先校验 XML 包含开始和结束节点。XML 无效时不得上传附件或保存正文。

## 写操作模式

`meeting-create` 和 `collaboration-send` 默认直接执行真实写入，不需要确认参数。用户明确要求预览时使用 `--dry-run`：它允许必要的只读查询，但不上传附件、不保存正文、不发送业务数据。

## 判断结果

所有命令输出单个 JSON 文档。使用 `ok` 判断业务成功，不以 HTTP 200 代替业务成功。

公共字段：

- `ok`
- `command`
- `completedStages`
- `failed_step`（失败时）
- `error`（失败时，已脱敏）

会议创建成功还应包含会议 ID、正文 ID、参与者、附件摘要和冲突详情。自由协同成功还应包含协同业务 ID、正文 ID、发送人、接收人和流程模式。

附件、正文或最终发送阶段失败时，报告已完成阶段和已有业务 ID，不自动重试、不自动回滚，避免产生重复会议或协同。

## 安全边界

- 不输出用户名、密码、Cookie、`JSESSIONID`、`route`、Token 或附件二进制。
- 不访问或加载同级原 Skill 目录；本 Skill 必须独立运行。
- 不在自动测试中连接真实 OA。
- 不在用户仅要求查询或 dry-run 时执行写接口。
