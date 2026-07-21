# AI 执行手册

本文件供 AI 在执行本 Skill 时使用，不面向普通用户解释内部接口细节。

## 用户沟通口径

对普通用户回复时，默认使用业务语言和结果导向表达，不要主动使用过多技术术语。

1. **默认不用技术词堆砌**：除非用户主动追问，否则不要直接说 `service_name`、`api_path`、`doc_url`、`biz_params`、JSON、接口编排、代理调用等术语。
2. **先说能帮用户做什么**：优先说"我先帮你看看""我先帮你查一下""我来帮你整理"这类表达，再说明还需要用户补充什么。
3. **权限提示说人话**：不要直接对用户说 TEAM、MINE、super_user；改为"你当前可以看团队数据"或"你当前只能看自己的数据"。
4. **配置提示说人话**：不要只说"未配置 SCRM_APP_KEY"；改为"你这边还没有完成企微管家授权，需要先获取 APP KEY 后我才能继续帮你查"。
5. **参数收集说业务信息**：不要说"请提供 biz_params"；改为"还需要补充时间范围、客户名称、标签、员工等信息"。
6. **反馈结果先讲结论**：查询成功时先总结查到了什么；失败时先说发生了什么和下一步怎么办，不先抛错误码。
7. **用户看不懂的内部信息不主动暴露**：接口路径、服务名、文档地址、原始返回结构，仅在用户明确要求查看时再展示。
8. **读取接口目录时统一使用仓库内的受控原文读取命令**：应直接获取目标地址的原始内容，统一执行 `python3 scripts/scrm.py fetch-raw-doc --url <目标地址>`；不要先做网页搜索，不要先打开站点首页，也不要仅基于摘要页或搜索结果推断接口。
9. **不要回退到 `web_fetch` 或其他网页抓取方式**：open.wshoto.com 文档读取统一走仓库内脚本命令，不使用网页正文抽取，不依赖首页跳转或搜索结果。

### 推荐话术示例

- 查询前：我先帮你看一下。
- 继续追问信息时：还需要你补充一下时间范围 / 客户名称 / 标签信息，我再继续帮你查。
- APP KEY 未配置时：你这边还没有完成企微管家授权，先去企业微信-工作台-企微管家-我的-我的 APP KEY 获取后发给我，我再继续帮你处理。
- 普通员工查团队数据时：你当前只能查看自己的数据，团队数据这边暂时查不了。
- 查询失败时：这次没有查成功，我把原因和下一步怎么处理跟你说一下。

## 脚本位置

脚本位于 SKILL.md 所在目录下的 `scripts/scrm.py`。AI 读取本文件时已知其路径，因此直接基于 SKILL.md 的目录拼接即可。

## 环境检测

触发 Skill 后，AI 应先检查当前是否具备脚本执行能力，以便运行仓库内命令读取原始文档并完成后续流程。

若用户当前处于 WorkBuddy 的 Ask 模式，且该模式下无法执行命令或脚本，应直接提示用户切换到 Craft（或其他具备命令执行能力的模式）后再继续；不要在明知当前模式无法执行命令时继续后续接口流程。

- **如果具备** → 正常继续后续调用流程。
- **如果不具备** → 引导用户切换到可执行脚本的模式或补齐命令执行能力，完成前不要继续后续流程。

处理原则：

- 缺少脚本执行能力时，先解决环境问题，再继续接口目录读取和后续 API 流程。
- 若已确认问题来自 WorkBuddy 的 Ask 模式限制，优先明确提示用户切换到 Craft（或其他具备所需能力的模式），不要只笼统提示"稍后再试"。
- 不要在缺少原文读取能力的情况下，直接把接口目录读取降级成普通网页搜索或首页浏览。
- 如果用户尚未完成重启，不要假装后续命令已经执行成功。

## 调用流程

AI 按以下编排流程执行：

1. **执行环境检测** → 先确认当前是否具备脚本执行能力；若不具备，则按"环境检测"章节优先引导用户切换到可用模式或补齐必要能力，完成前不要继续后续流程
   - 若已知用户当前在 Ask 模式且无法执行命令，先明确提示其切换到 Craft（或其他具备所需能力的模式）
2. **执行 check-env** → 检查运行环境（Python ≥3.9、SCRM_APP_KEY）；`check-env` 内部会自动尝试从 shell profile 或 Windows 注册表中恢复已持久化的 APP_KEY
   - 成功且返回中包含 `export_hint` → 说明 APP_KEY 是从持久化配置中恢复的，**立即执行返回的 `export_hint` 命令**（如 `export SCRM_APP_KEY='xxx'`）使当前 shell 会话生效，然后继续
   - 成功且无 `export_hint` → APP_KEY 已在环境变量中，直接继续
   - 失败（`config_error`）→ 引导用户获取 APP KEY 并执行 `set-app-key`，成功后执行 `export SCRM_APP_KEY='<值>'`，然后继续
   - 若用户主动要求更换或更新 APP KEY（即使当前已配置），同样执行 `set-app-key` 用新值覆盖、export 后再继续
3. **执行 check-identity** → 获取用户身份（超管/分管/员工）
4. **阅读远程接口目录（强制步骤，不得跳过）** → 必须先读取 [CLAW_SUMMARY.md](https://open.wshoto.com/doc/pages/claw/CLAW_SUMMARY.md) 的原始内容，再根据用户意图匹配目标接口；每次会话首次触发 Skill 时必须执行此步骤，不得凭已有认知直接跳到 list-apis。执行时统一使用仓库内命令 `python3 scripts/scrm.py fetch-raw-doc --url <url>`
5. **执行 list-apis** → 用接口名称关键词匹配调用规则（service_name、api_path、doc_url）
6. **阅读接口文档（doc_url）** → 阅读该文档获取完整参数定义，强制步骤，不得跳过
7. **通过对话收集 biz_params** → 基于 doc_url 文档中的参数说明收集必要参数，不得仅凭 description 推断
8. **执行 call-api** → 将 list-apis 返回的 service_name、api_path 及收集到的 biz_params 组装后通过通用代理调用

### 接口目录与文档读取要求

- 读取接口目录时，目标是拿到原始响应内容，而不是做网页正文抽取。
- 统一执行仓库内命令 `python3 scripts/scrm.py fetch-raw-doc --url https://open.wshoto.com/doc/pages/claw/CLAW_SUMMARY.md`。
- 该命令内置超时、域名白名单和响应大小限制，比 `web_fetch` 更稳定，也更容易通过安全审查。
- 读取 doc_url 对应在线文档时，也统一执行 `python3 scripts/scrm.py fetch-raw-doc --url <doc_url>`。
- 不要退化为首页浏览、搜索摘要或人工猜测。

> **⚠️ 文档内容截断处理：** 工具展示 stdout 时可能截断长文本，但数据本身未丢失。**必须通过管道解析完整 content**，不要直接读 stdout，否则会遗漏参数（如跟进记录接口的 `menu`、`searchField/searchValue` 曾因此被忽略）。
>
> ```bash
> python3 scripts/scrm.py fetch-raw-doc --url <url> | python3 -c "
> import sys, json; data = json.load(sys.stdin); print(data['data']['content'])
> "
> ```

### 接口匹配规则

1. 阅读远程接口目录后，根据用户意图匹配接口名称和使用说明
2. 匹配到唯一接口时直接使用，无需询问用户
3. 匹配到多个候选接口时，列出候选项让用户选择
4. 无法匹配时，告知用户当前无匹配接口

### 接口间数据依赖

doc_url 文档中的「业务参数数据来源说明」章节描述了每个参数的值从哪里获取。AI 组装 `biz_params` 时，**必须先识别依赖关系，按正确顺序调用前置接口获取参数值**，不能跳过或猜测。

**参数来源识别：**

| 来源描述关键词 | AI 行为 |
|----------------|---------|
| 「前端XX选择器」「前端输入框」 | 通过对话向用户收集 |
| 「XX接口返回数据中的 `field` 字段」 | **必须先调用前置接口获取**，再用返回值填充 |
| 「预设枚举值」 | 根据用户意图从固定选项中匹配 |
| 「用户选择/用户输入」 | 通过对话收集，可能需要先列出选项 |

**处理原则：**
1. 每次调用接口前，先阅读 doc_url 的「业务参数数据来源说明」，确认是否有参数依赖其他接口
2. 对于来源为其他接口的字段（如 tagId、userId、deptId），绝不能凭用户输入的名称自行构造，必须通过前置接口查询获取真实值
3. 前置接口返回多条匹配记录时，列出选项让用户确认
4. 同一会话内已获取的数据可复用，无需重复调用

**典型场景 — 按标签名查客户：**

用户说"查一下有多少客户打了高意向客户标签"，正确做法：
1. `list-apis --keyword "客户列表"` → 找到「客户列表分页查询」
2. 阅读 doc_url → 发现 `tagIds` 参数依赖「获取客户标签列表」接口
3. `list-apis --keyword "标签"` → 找到「获取客户标签列表」，用 `keyValue="高意向客户"` 搜索
4. 从返回结果中匹配 `tagName`，提取对应 `tagId`（多个同名标签时列出让用户选择）
5. 将 `tagId` 填入 `tagIds` 参数，调用客户列表接口

> **错误做法**：直接猜测或构造 tagId 去查询。

## 命令参考

所有命令统一以如下格式执行，参数通过对话收集，不依赖 stdin 交互：

```bash
SCRM_NON_INTERACTIVE=1 python3 "$SCRM_SCRIPT" <command> [--param value ...]
```

> **首次调用某个命令前，必须先执行 `<command> --help` 确认参数名称和格式，不得凭猜测传参。**
> **所有参数必须使用 `--param-name` 连字符格式，禁止使用下划线格式。**

### check-env — 环境检查

触发 Skill 时**立即**执行，失败则终止。检查项：Python ≥3.9、`SCRM_APP_KEY` 是否已配置。

```bash
python3 "$SCRM_SCRIPT" check-env
```

### check-env — 环境检查（含 APP_KEY 自动恢复）

触发 Skill 时**立即**执行，失败则终止。检查项：Python ≥3.9、`SCRM_APP_KEY` 是否已配置。

当 `SCRM_APP_KEY` 环境变量为空时，`check-env` 会自动尝试从 shell profile（Unix/macOS）或注册表（Windows）中读取之前通过 `set-app-key` 持久化的值。如果恢复成功，返回结果中会包含 `export_hint` 字段。

```bash
python3 "$SCRM_SCRIPT" check-env
```

**成功（APP_KEY 已在环境变量中）：**

```json
{
  "success": true,
  "data": {
    "checks": {
      "python_version": {"ok": true, "detail": "3.13.3"},
      "app_key": {"ok": true, "detail": "已配置"}
    }
  }
}
```

**成功（APP_KEY 从持久化配置中恢复）：**

```json
{
  "success": true,
  "data": {
    "checks": {
      "app_key": {"ok": true, "detail": "从持久化配置中恢复（profile）"}
    },
    "app_key_restored": {"source": "profile", "profile": "/Users/xxx/.zshrc", "app_key": "xxx"},
    "export_hint": "export SCRM_APP_KEY='xxx'"
  }
}
```

AI 处理逻辑：
- 成功且包含 `export_hint` → **立即执行返回的 `export_hint` 命令**使当前 shell 会话生效，然后继续
- 成功且无 `export_hint` → 直接继续
- 失败（`config_error`）→ 引导用户执行 `set-app-key`

**失败：**

```json
{
  "success": false,
  "error": "config_error",
  "details": {
    "checks": {
      "app_key": {"ok": false, "detail": "未配置 SCRM_APP_KEY"}
    }
  }
}
```

### set-app-key — 设置 APP_KEY

`SCRM_APP_KEY` 未配置时：先询问用户是否已有，若无则引导前往企微管家移动端「我的 → 我的 APP KEY」获取。用户提供后执行：

```bash
SCRM_NON_INTERACTIVE=1 python3 "$SCRM_SCRIPT" set-app-key "<用户提供的APP_KEY>"
```

成功后：
1. 立即执行 `export SCRM_APP_KEY='<用户提供的APP_KEY>'`（Unix/macOS）使变量在当前 shell 会话中立即生效；Windows 平台跳过此步骤
2. 将返回结果中的 `note` 告知用户一次
3. 直接继续原始请求，不再追问用户是否已重启终端

> ⚠️ **必须执行 `export` 步骤**：`set-app-key` 写入 shell profile 后，当前会话不会自动加载新变量，不执行 `export` 则后续命令（如 `check-env`、`check-identity`）在当前会话内仍读不到 `SCRM_APP_KEY`，导致每次新会话都重复追问用户。

### check-identity — 获取用户身份

无额外参数，自动使用缓存的 user_id。

```bash
SCRM_NON_INTERACTIVE=1 python3 "$SCRM_SCRIPT" check-identity
```

返回示例：

```json
{
  "success": true,
  "action": "check-identity",
  "data": {
    "user_id": "xxx",
    "user_name": "张三",
    "super_user": 1,
    "role_description": "超级管理员"
  }
}
```

### set-chat-mode — 设置会话存档模式

```bash
SCRM_NON_INTERACTIVE=1 python3 "$SCRM_SCRIPT" set-chat-mode --mode <key|zone>
```

设置一次后永久生效。若用户在对话中明确告知模式，立即执行保存后继续查询；若从未设置且用户未提及，则询问。

### list-apis — 接口仓库查询

```bash
SCRM_NON_INTERACTIVE=1 python3 "$SCRM_SCRIPT" list-apis --keyword "关键词1,关键词2"
```

| 参数 | 说明 |
|------|------|
| `--keyword` | (必填) 多个关键词逗号分隔，模糊匹配 api_name |

返回字段：

| 字段 | 说明 | 用途 |
|------|------|------|
| `api_name` | 接口名称 | 确认匹配结果 |
| `description` | 接口简要描述 | 辅助理解用途，**不含完整参数定义** |
| `api_path` | 接口 URI | 作为 `call-api --uri` 的值 |
| `service_name` | 下游微服务名 | 作为 `call-api --service-name` 的值 |
| `doc_url` | 接口文档地址 | **必读**，获取完整参数定义 |

### call-api — 通用代理调用

```bash
SCRM_NON_INTERACTIVE=1 python3 "$SCRM_SCRIPT" call-api \
  --service-name "wshoto-basebiz-service" \
  --uri "/bff/bizCustomer/private/h5/chat/pageQuery" \
  --biz-params '{"currentIndex":1,"pageSize":10}'
```

| 参数 | 说明 |
|------|------|
| `--service-name` | (必填) 取自 list-apis 返回的 `service_name` |
| `--uri` | (必填) 取自 list-apis 返回的 `api_path`（注意：字段名是 `api_path`，参数名是 `--uri`） |
| `--method` | (可选) HTTP 方法，默认 POST |
| `--biz-params` | (必填) 业务参数 JSON，参数名和类型以 doc_url 文档为准 |

> **字段映射（易混淆）：** `list-apis.service_name` → `--service-name`；`list-apis.api_path` → `--uri`；`list-apis.doc_url` → 阅读后收集 `--biz-params`。

### 参数收集标注含义

doc_url 文档中的参数标注，AI 必须严格按对应行为执行：

| 标注 | AI 行为 |
|------|---------|
| **必须对话收集** | 执行前通过对话明确获取，不得自行推断 |
| **展示选项让用户选择** | 列出所有选项含默认推荐，等用户选择 |
| **展示默认值后确认** | 告知默认值，询问是否修改 |
| 默认：`xxx` | 展示默认值，用户无需主动回复 |
| 可选 | 用户未提及时跳过 |

## 身份与权限

不同业务接口用于区分团队/个人数据范围的参数名不统一，AI 必须通过阅读 doc_url 文档确认具体字段名。

| check-identity 角色 | 数据范围 | 参数取值 |
|---------------------|----------|----------|
| 超管(super_user=1) / 分管(super_user=2) | 团队数据 | 团队对应的枚举值（如 TEAM） |
| 普通员工(super_user=0或3) | 仅个人数据 | 个人对应的枚举值（如 MINE） |

AI 应根据 check-identity 结果，在 biz_params 中自动填入对应值。当用户未明确指定视角范围时：超管/分管默认使用团队视角，普通员工默认使用个人视角。

### 普通员工视角限制

即使用户主动要求查询团队数据，普通员工也必须使用个人视角，不得使用团队视角。应告知用户"您的身份是普通员工，只能查看个人数据，无法查看团队数据"。

### 员工操作限制

当 check-identity 返回 `super_user` 为 `0` 或 `3` 时，当前用户为普通员工，AI 必须严格执行以下限制：

#### 限制一：禁止指定其他员工

普通员工只能操作自己的数据，不能将接口参数中的员工相关字段指定为其他员工。

强制检查流程：

1. 查看 check-identity 返回的 `user_id` 和 `user_name`
2. 检查 biz_params 中是否包含员工名称、员工ID相关参数（如 `userIds`、`addUserIds`、`staffId` 等）
3. 如果包含，此类参数必须且只能是 check-identity 返回的 `user_id` 或 `user_name`
4. 如果用户要求使用其他员工，必须拒绝执行并告知"您的身份是普通员工，只能操作自己的数据（{user_name}），无法指定其他员工"

示例：用户说"创建活码，使用员工=芳芳"，但 check-identity 返回 user_name=吴浩 → 芳芳≠吴浩，拒绝执行。

#### 限制二：禁止调用员工/部门搜索接口

普通员工无权搜索企业组织架构。员工&部门分类下的搜索接口，以及任何用于获取员工列表、部门列表、组织架构树的接口，普通员工都不得调用。

## 错误处理

| error 类型 | AI 处理方式 |
|------------|-------------|
| `config_error` | 用普通用户能理解的话说明还缺什么配置，并引导下一步，不直接抛技术细节 |
| `validation_error` | 说明还缺哪些业务信息或填写有误，引导用户补充后重试 |
| `scrm_error` | 用业务语言转述失败原因，并询问用户是否要调整条件后再试 |
| `json_error` | 内部自行修正，不把 JSON 解析细节暴露给用户 |
| `unexpected_error` | 告知用户这次没处理成功，建议稍后重试或联系管理员，不直接输出技术报错 |

仅 `scrm_error` 且用户主动要求时才重试；其他类型错误优先修复根因。

### 写操作重试限制

写操作接口执行失败或超时后，禁止自动重试。写操作失败可能是服务端已成功执行但响应超时，自动重试会导致重复创建数据。

具体规则：

1. `call-api` 的输出中包含 `write_operation` 字段，`true` 表示写操作，`false` 表示读操作
2. 写操作失败或超时时，AI 必须告知用户失败结果，由用户决定是否重试，AI 不得自行重新执行 `call-api`
3. 读操作不受此限制，AI 可以在合理范围内重试

## 行为规范

以下规则优先级最高，始终遵守：

1. 触发 Skill 时立即执行 `check-env`，在收集任何参数前完成；失败则告知用户并终止，不得继续
2. 若 `SCRM_APP_KEY` 未配置，先询问用户是否已有 APP_KEY；若没有，则引导前往企业微信-工作台-企微管家应用-我的-我的 APP KEY 获取
3. 写操作确认，读操作直接执行：查询类接口直接执行；写操作接口必须等待用户最终确认后再执行
4. 参数收集通过对话完成，不依赖脚本 stdin 交互；执行时统一携带 `SCRM_NON_INTERACTIVE=1`
5. 用户身份由 `SCRM_APP_KEY` 静默获取，禁止通过命令行参数传入
6. 所有输出统一为 JSON，便于上层 Skill 编排解析
7. 首次调用某个命令前，必须先执行 `<command> --help` 确认参数名称和格式，不得凭猜测传参
8. 面向普通用户回复时，优先使用业务口径：先说能帮用户做什么、查到了什么、还缺什么信息，不主动输出底层接口与参数细节
9. 涉及接口目录的读取动作一律走受控原文直读：读取 [CLAW_SUMMARY.md](https://open.wshoto.com/doc/pages/claw/CLAW_SUMMARY.md) 时，统一使用 `python3 scripts/scrm.py fetch-raw-doc --url <url>`。若当前环境缺少该能力，先修复环境并提示用户切换模式或完成必要配置，再继续，不要直接降级为网页搜索、首页访问或 `web_fetch`

## 文件上传与下载

涉及图片/文件操作时，参考 [file-utils.md](file-utils.md)。
