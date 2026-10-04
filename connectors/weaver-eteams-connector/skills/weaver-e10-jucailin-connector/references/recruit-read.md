# 招聘查询

## 何时使用

需要查询招聘模块数据时使用：人才库搜索、招聘需求/职位/入职/录用列表、人才详情卡片。全部为只读操作。招聘**写操作**（新建人才、安排面试、发 Offer、入职办理、面试反馈等）已单独提供，走 prepare→apply 确认协议，见 [`recruit-write.md`](recruit-write.md)。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `ehr.recruit.candidate.search` | 无 | 按姓名/手机号模糊搜索人才库；都不传时列出全部人才用于浏览 |
| `ehr.recruit.candidate.list` | `type` | 查询招聘业务列表，`type` 取 `demand`（招聘需求）/`position`（招聘职位）/`entry`（入职管理）/`offer`（录用管理）之一 |
| `ehr.recruit.candidate.card` | `talentId` | 人才详情卡片：基本信息 + 应聘进展 + 面试安排 + 沟通备注 |
| `ehr.recruit.context.resolve` | 无 | 返回当前环境的招聘模块运行时参数（appId/表单/列表），仅用于调试与兜底 |

运行时参数（appId、菜单 listId/cusMenuId、字段 ID 映射）由 CLI 自动五层解析并缓存（进程内 + 磁盘；缓存根 = `E10_SKILL_CACHE_DIR` 环境变量，未设置回退 CLI 数据目录 `WEAVER_WORK_CLI_HOME`（默认用户主目录下 `.weaver-work-cli`）的 `env-cache/recruit-ops/`），业务调用**不需要也无法手工传这些参数**。解析失败会报明确错误（如未安装招聘服务、菜单缺失），此时先运行 `ehr.recruit.context.resolve` 检查环境，不要重试猜测。

`candidate.search` 返回白名单字段：`talentId`/`name`/`mobile`/`channel`/`status`/`creator`/`createTime`。`candidate.list` 返回对应业务列表的展示字段（显示层直出，已剔除内部键）。

## 命令

搜索人才（姓名模糊匹配）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.search --input-json '{"name":"张三"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"name":"张三"}' | weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.search --input -
```

查询招聘需求列表：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.list --input-json '{"type":"demand","current":1,"pageSize":10}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"type":"demand","current":1,"pageSize":10}' | weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.list --input -
```

查看人才详情卡片：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.card --input-json '{"talentId":"PLACEHOLDER_TALENT_ID"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"talentId":"PLACEHOLDER_TALENT_ID"}' | weaver-work-cli --profile eteams --json ehr run ehr.recruit.candidate.card --input -
```

## 输出处理

- `candidate.search` 与 `candidate.list` 的分页信息在返回数据内（`total`/`current`/`pageSize`），不在 `meta.page`。
- 人才姓名、渠道（`channel`）、招聘状态（`status`）已是中文可读值，无需再反查。
- `candidate.card` 返回结构化四段：`baseInfo`（姓名/手机/渠道/状态）、`position`（职位/当前阶段/阶段历程 `stages`/招聘负责人）、`interviews`（每场面试含 `feedbacks` 反馈列表）、`remarks`（沟通备注）。`cardLink` 是 E10 网页端人才卡片链接（环境未配置详情页时为 `null`）。
- 无权限查看某人才详情时报 `recruit_rights_denied`，不要换参数重试。

## 注意

- 姓名、手机号都是**模糊匹配**，多人命中时必须列出候选让用户选择，不得自动取第一条。
- `candidate.card` 会完整读取候选人的面试反馈与沟通备注，属敏感个人信息；回复用户时给摘要与关键字段，不要原样粘贴完整 JSON。
- 手机号、身份证等敏感字段不要回显给与业务无关的对话。
- 需要变更数据（新建人才/安排面试/发 Offer/办理入职/面试反馈）时，使用 `recruit-write.md` 的写操作协议，不要用只读接口编造变更。
