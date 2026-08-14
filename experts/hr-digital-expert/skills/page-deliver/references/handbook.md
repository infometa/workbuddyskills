# Page-Deliver Handbook

> **遇到任何阻断（CLI 返回 `status:failed` / 工具不可用 / state 不一致 / 依赖缺失）**——先来这里查匹配卡片，按"给用户的话"原文输出，按"后续动作"决定下一步。
> 没匹配的卡片，按本页"通用处置思路"自行判断，不要自由发挥话术。
>
> 本 handbook 是**全局错误处理入口**，由 SKILL.md 顶层 Checklist 统一导流；其他文件不会再单独指路。
>
> 卡片结构：
> - **触发**：什么时刻撞到
> - **识别信号**：看到什么就走这条
> - **给用户的话**：转述给用户的内容（必要时附"复制即用"模板）
> - **后续动作**：用户回复后从哪里继续

---

## 通用处置思路（卡片没覆盖时按这套走）

### 1. 先分类：是哪种性质的阻断？

| 性质 | 示例 | 默认动作 |
|------|------|----------|
| **可自愈**（瞬时抖动、可幂等重试） | 网络超时、单次 HTTP 5xx、agent 通道掉线 | **自动重试 1 次**，不打扰用户 |
| **需用户操作**（凭证/配置/资源在用户那一侧） | 未登录、配额满、缺插件、状态前置不足 | 停下，按"给用户的话"模板汇报，等用户处理后回复"重试/继续" |
| **代码/数据 bug**（产物本身有问题） | SQL 报错、前端 JS 异常、健康检查 404 | 先抓证据（日志/响应/stderr）→ 自己判断能否定位 → 能定位就改 + 重新 full-deploy；不能定位再问用户 |
| **环境破坏**（插件文件缺失、二进制不兼容） | `BIN_NOT_FOUND`、`SCRIPT_NOT_FOUND` | 不要自行回退到系统 PATH 工具，提示用户重装/更新 page-deliver 插件 |

判断不准时按"需用户操作"处理，宁可多问一次也不要乱重试。

### 2. 自查顺序（看到 `status:failed` 时）

1. **读 `error.hint`**：hint 是 CLI 写死的可执行指引，存在就照做或转述给用户，不要忽略
2. **匹配卡片**：按 `error.code` / 关键 stderr 字段在本 handbook 里搜一下
3. **走兜底**：没匹配的，按下面"兜底输出模板"汇报

### 3. 兜底输出模板

```
执行 {做了什么} 时遇到问题：
   - 错误码: {error.code}
   - 信息: {error.message}
   - 现场: {关键 stderr / 上下文，最多 5 行，不要截断关键字段}

我的判断：{自愈 / 需要你处理 / 疑似代码问题，给出 1-2 句理由}
建议下一步：{1-3 条可选动作，让用户在选项里选}
```

要点：
- **不要自己脑补 hint**，没把握的地方写"判断不准，需要你定一下"
- **不要把 stderr 截没**，关键报错行（含表名/字段名/路径/exit code）必须保留
- **不要自由发挥安抚话术**，多说一句不如把现场给清楚
- **不要在用户没回复前重试相同命令**（除"自愈"类）

### 4. 永远的红线

- 任何步骤失败都**不允许**伪造 `status:success` 继续往下走
- `anydev publish` 在用户没点"确认注册"前**禁止**执行（无论 plan 写没写）
- `BIN_NOT_FOUND` / `SCRIPT_NOT_FOUND` **禁止**回退到系统 PATH 找替代品
- state / plan 不一致时**禁止**靠"猜测"恢复，要么按卡片走，要么问用户

---

## A. 启动 / 环境类

### A1. MCP 服务预检失败（HARD-GATE）

**触发**：启动序列第 3 步 — 按 `references/mcp-preflight.md` 检查 `hr_data_service_v1` MCP 服务的 `check_version` tool 是否可用。
**识别信号**：会话内未列出 `hr_data_service_v1`，或调用其 `check_version` tool 返回错误/超时。
**给用户的话**（按实际填 ✅/❌）：

```
⚠️ MCP 服务检查未通过，无法启动 page-deliver：
   - {✅/❌} hr_data_service_v1

修复步骤：
   1. 确认 MCP 服务已安装/连接：
      - 如果是 CodeBuddy，点击右上角齿轮 → 设置 → MCP，确认 `hr_data_service_v1` 已安装
      - 如果是 Workbuddy，点击左边专家 → 连接器 → 右上角"自定义连接器"，确认 `hr_data_service_v1` 已安装
   2. MCP 配置中确认服务已连接
   3. 检查网络可达
修复后回复「继续」或「重试」。
```

**后续动作**：**立即停止响应**，等用户回复"继续/重试"后从启动序列重跑（不落盘，每次进入流程都重检，含断点续传 / 重新部署）。**先于"快速跳过"规则。**

---

### A2. preflight Node 装不上

**触发**：启动序列第 2 步 — 执行 `preflight.sh` / `preflight.ps1` 失败。
**识别信号**：脚本退出码 1（网络/下载失败）、2（SHA256 校验失败）、3（解压/路径校验失败），或 stderr 含 `[preflight] download failed` / `verification failed` / `extract failed`。
**给用户的话**：

```
⚠️ Page-Deliver 自带 Node 装载失败（exit {code}）：{stderr 关键行}

修复建议：
   - exit 1：检查网络，是否正确连接公司办公网，重试一次
   - exit 2：如果使用 WorkBuddy，检查聊天框下方是否打开完全访问权限
修复后回复「重试」继续。
```

**后续动作**：等用户处理后从启动序列第 2 步重跑。

---

---

## B. CLI 调用类

### B1. 参数报错先 `--help`，禁止瞎拼 JSON

**触发**：调用 `node $PD <topic> <subcommand>` 拼输入 JSON 时不确定字段，或返回 `BAD_INPUT` / `BAD_SUBCOMMAND` / `MISSING_FIELD`。
**识别信号**：`status:failed` + `error.code in {BAD_INPUT, BAD_SUBCOMMAND}`，或 `error.message` 含 `required` / `Unknown subcommand` / `is required`。
**给用户的话**：通常**不需要**告诉用户——先自己执行 `node $PD <topic> <subcommand> --help` 拿到输入 schema 与示例，再纠正 JSON 后重试。
仍无法纠正才告诉用户：

```
调用 page-deliver 内部命令时参数不对（{error.code}: {error.message}）。我已经查了 --help 仍无法对齐，可能是 plan 或上游数据缺字段。
请确认：{你怀疑的字段} 是不是 ...
```

**后续动作**：模型自查 `--help` → 修正输入 → 重新调用。

---

### B2. anydev 永远用 page-deliver 封装好的，不要用 CodeBuddy/WorkBuddy 或者其他任何插件内置的

**触发**：调用 page-deliver 时出错，找不到插件自带的 any CLI。 
**识别信号**：`error.code = BIN_NOT_FOUND` 且 `error.message` 含 `any CLI binary ... not found`等
**给用户的话**：

```
找不到插件自带的 any CLI（路径：{SKILL_DIR}/bin/anydev/{any-macos|any-linux|any-windows.exe}）。

修复：
   在插件市场重新安装/更新 page-deliver 插件
重装后回复「重试」。
```

**禁止**：使用 CodeBuddy/WorkBuddy 或者其他插件内置的 anydev 功能
**后续动作**：等用户重装后重试。

---

### B3. 禁止本地启动预览（`LOCAL_START_FORBIDDEN`）

**触发**：模型在 plan 执行过程中试图本地启动项目来"预览"，或 `validate plan` 返回 `S7_FORBIDDEN_LOCAL_START`。
**识别信号**：plan 中出现或模型执行了以下任一命令：`node server.js` / `node app.js` / `npm start` / `npm run dev` / `npm run serve` / `npm run start` / `npx <tool> --port` / `yarn dev` / `pnpm dev` / `python app.py` / `flask run`；或预览 URL 含 `localhost` / `127.0.0.1` / `0.0.0.0`。
**给用户的话**（如果模型已经执行了本地启动命令，先停掉再告知）：

```
⚠️ 检测到本地启动命令（{具体命令}），已停止。

预览只能通过 anydev full-deploy 在 AnyDev 容器内进行：
   1. 本地启动产生的 localhost:xxxx 无法被外网访问
   2. 绕过了 PM2 进程管理与健康检查
   3. 无法走后续 publish 注册流程

我现在改为执行 anydev full-deploy 来预览，请稍候。
```

**后续动作**：
1. 如已在本地启动了进程，先 kill 掉（`lsof -ti:PORT | xargs kill` 或等价方式）
2. 如 plan 中写了本地启动步骤，用 `replace_in_file` 删除该步骤，替换为标准 `anydev full-deploy` 步骤
3. 执行 `anydev full-deploy` 重新预览
4. **禁止**在任何情况下以本地启动替代 full-deploy——即使 anydev full-deploy 失败，也按 C 类卡片排查修复后重试，不得退回本地启动

> ⚠️ **红线**：此卡片为**全局禁止项**，不存在"anydev 不可用时退回本地预览"的 fallback。anydev 失败走 C 类卡片处理。

---

## C. anydev 全流程类

### C1. 未登录（`LOGIN_REQUIRED`）

**触发**：`anydev full-deploy` / `anydev publish` 返回 `LOGIN_REQUIRED`。
**识别信号**：`error.code = LOGIN_REQUIRED`。
**给用户的话**：

```
检测到 AnyDev 未登录。即将打开浏览器完成 OA 登录，登录后回到这里回复「已登录」继续。
```

`full-deploy` 会在错误 details/hint 中返回授权链接；把链接给用户点击。
**后续动作**：等用户回复"已登录"或显式继续 → 重试触发了 `LOGIN_REQUIRED` 的核心命令。

---

### C1.5 MCP Gateway 授权（`AUTH_REQUIRED`）

**触发**：`anydev publish` 的 step 1 (registry-register) 返回 `AUTH_REQUIRED`。
**识别信号**：`error.code = AUTH_REQUIRED`。
**给用户的话**：

```
MCP Gateway 首次注册需要 OAuth 授权。请点击以下链接完成授权：

{error.message 中的授权链接}

授权完成后回复「已授权」，我将继续发布流程。
```

`publish` 会在 `error.message` 中内嵌授权链接（`details.authUrl` 与 `hint` 同步）。直接把 `error.message` 里的链接给用户点击即可，无需另查 `details.authUrl`。
子进程在后台等待 OAuth 回调并自动写入 credential cache，用户授权后重试秒过。
**后续动作**：等用户回复"已授权"或显式继续 → 重试 `anydev publish`（token 已缓存，秒过）。

---

### C2. agent 不可达（`AGENT_NOT_RUNNING` / `AGENT_INIT_TIMEOUT`）

**触发**：`anydev remote-exec` / `anydev full-deploy` 内部步骤报 agent 不可达。
**识别信号**：`error.code in {AGENT_NOT_RUNNING, AGENT_INIT_TIMEOUT}`，或 stderr 含 `agent未运行或不可达`。
**给用户的话**（首次失败时不打扰用户，自动恢复）：

不要调用底层 `agent-init`。优先重试触发失败的核心命令（`full-deploy` / `publish` / `remote-exec`），核心命令内部会尝试恢复 agent 通道。
连续两次失败才告诉用户：

```
容器内 agent 通道反复初始化失败（已重试 2 次）。可能原因：
   - 容器已离线或被回收
   - 容器 agent 版本与 any CLI 不兼容

建议：
   1. 在 AnyDev 控制台确认容器 {envInsId} 仍然在线
   2. 必要时重新建一个容器（删除项目下的 .deploy-state.json 后重跑 /page-deliver）
处理后回复「重试」。
```

**后续动作**：自动恢复成功 → 续跑；连续失败 → 等用户。

---

### C3. any CLI 网络/超时（`ANY_TIMEOUT` / `ANY_EXIT_NONZERO` / `ANY_SPAWN_FAILED`）

**触发**：调任意 any 子命令时网络抖动或非零退出。
**识别信号**：`error.code in {ANY_TIMEOUT, ANY_EXIT_NONZERO, ANY_SPAWN_FAILED, ANY_BAD_JSON, ANY_FAILED}`。
**给用户的话**：首次抖动**自动重试一次**，不打扰用户。仍失败：

```
AnyDev CLI 调用持续失败（{error.code}）：
{error.message 关键行}

建议检查 page-deliver 插件安装与 AnyDev 登录/网络状态；也可能是 AnyDev 后端波动，稍后重试。
```

**后续动作**：等几分钟重试核心命令；若持续失败，提示用户检查插件安装或 AnyDev 控制台状态。

---

### C4. 容器创建/启动失败（`ENV_CREATE_FAILED` / `ENV_START_TIMEOUT`）

**触发**：full-deploy 创建/启动 AnyDev 容器时失败。
**识别信号**：`error.code in {ENV_CREATE_FAILED, ENV_START_TIMEOUT}`。
**给用户的话**：

```
AnyDev 容器创建/启动失败（{error.code}）。常见原因：
   - 当前 AnyDev 配额已满
   - 容器镜像或地域临时不可用
处理后回复「重试」继续从 full-deploy 重跑。
```

**后续动作**：等用户清配额后重试 full-deploy。

---

### C5. 服务起来了但探针不过（`PORT_PARSE_FAILED` / `BAD_STATUS` / `BODY_MISMATCH` / `EARLY_CRASH`）

**触发**：full-deploy 第 14 步（内部健康检查）或本地 preview 早期崩溃。
**识别信号**：`error.code in {PORT_PARSE_FAILED, BAD_STATUS, BODY_MISMATCH, EARLY_CRASH, NO_FREE_PORT}`。
**给用户的话**（先自查再汇报）：

1. 自动跑 `anydev remote-exec` 抓 PM2 日志：
   ```
   echo '{"projectDir":"<project_dir_abs>","cmd":"pm2 logs <projectId> --lines 80 --nostream"}' | node "$PD" anydev remote-exec --input -
   ```
   `anydev remote-exec` 只接受 `projectDir` + `cmd`，不要传 `skillDir/envInsId/ip/port`。
2. 从日志判断是代码错误（如 missing module、SQL 报错）还是服务未起来（端口被占）
3. 把诊断结论给用户：

```
服务在容器内未通过健康检查（{error.code}）。我看了 PM2 日志，疑似原因：
   - {一句话结论：缺依赖 / 代码异常 / 端口被占 / 数仓接口报错 ...}

我会 {自动修复并重新 full-deploy / 等你确认怎么改}。
```

**后续动作**：能定位代码 bug 就改代码 + 重新 full-deploy；定位不了就停下问用户。

---

### C6. publish/上传失败（`PACK_UPLOAD_FAILED` / `REGISTER_FAILED` / `ENSURE_PACK_UPLOAD_FAILED`）

**触发**：用户点"确认注册"后跑 `anydev publish`。
**识别信号**：`error.code in {PACK_UPLOAD_FAILED, REGISTER_FAILED, ENSURE_PACK_UPLOAD_FAILED, SCRIPT_NOT_FOUND, EXEC_FAILED}`。
**注意**：`AUTH_REQUIRED` 不属于此卡片，走 C1.5 卡片处理（展示授权链接，等用户点完重试）。
**给用户的话**（按子环节区分）：

| code | 根因 | 处理 |
|------|------|------|
| `REGISTER_FAILED` | Gateway 注册失败（多见于网络/权限） | 自动重试 1 次；仍失败 → 把 error.message 转述给用户  |
| `PACK_UPLOAD_FAILED` | tar 打包或 COS 上传失败 | 看 `error.hint` 如有就照做；否则提示用户检查项目目录是否过大（>500M）或是否有非常规文件 |
| `ENSURE_PACK_UPLOAD_FAILED` | 容器内 pack-upload 脚本预置失败 | 重试 `anydev publish`；核心命令内部会尝试恢复 agent 通道 |
| `SCRIPT_NOT_FOUND` | 插件自带脚本缺失 | 走 B2 卡片（重装 page-deliver 插件） |

**后续动作**：自动恢复成功 → 输出部署模板（output-templates.md）；持续失败 → 等用户。

---

## D. 数据/SQL 类

### D1. 数仓 SQL 失败

**触发**：`needs_dw=true` 场景下 — 前端 `queryDW` 报错、starrocks_query MCP 验证 SQL 失败、或 hr-code-reviewer 报 SQL 不通过。
**识别信号**：`code !== 0` 的数仓返回 / `queryDW` 异常 / `starrocks_query` 工具返回错误。
**给用户的话**：先按 `dw-readonly-guide.md`（并行查询 / 列名核对 / 首屏 vs 渐进 / `batchQueryDW`）自查 SQL；定位不了再问：

```
数仓查询失败：{表名/SQL 关键片段} → {error.message}
可能原因：表名/字段名错、权限不足、数据范围筛选过严。
请确认：{1-2 个关键字段或筛选条件}
```

**后续动作**：能改 SQL 就改 + 重新 full-deploy；改不了停下问用户。
