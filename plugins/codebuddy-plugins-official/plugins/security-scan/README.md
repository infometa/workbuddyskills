# Security-Scan — 代码安全审计插件

一款智能代码安全审计工具，通过 **语义索引 + 多 Agent 并行扫描 + 对抗验证** 实现专业级漏洞发现。支持 **全链路 --auto 无人值守模式 + 安全门禁 + Git Hook 自动化 + 腾讯云安全基线**，覆盖代码安全与云安全的全链路审计。

---

## 工作原理

```
                          ┌──────── ③ 扫描 ────────┬──── ④ 验证 ─────┐
                          │                        │                 │
                          │  indexer ─▶┌───────────┐│  verifier      │
                          │  建索引    │ vuln-scan ││  攻击链验证     │
 ┌────────┐  ┌────────┐  │           │ logic-scan││  对抗审查 ─────┐│
 │ ①初始化 │─▶│ ②探索   │─┤  Deep     │ red-team  ││  过滤误报      ││
 └────────┘  └────────┘  │           └───────────┘│               ││  ┌──────────┐
  权限白名单   文件枚举     │            三路并行     │               ├┼─▶│ ⑤审计报告 │
  模式选择     技术栈识别   ├────────────────────────┼───────────────┤│  └──────────┘
  环境检测     危险函数定位  │                        │               ││   HTML 报告
                          │  Light                 │               ││   修复建议
                          │  编排器内联扫描(Grep)    │  轻量验证 ────┘│   置信度评分
                          │                        │                │
                          └────────────────────────┴────────────────┘
```

### 扫描 Agent 分工

三个扫描 Agent **并行工作，各看不同维度**，不重复：

**vuln-scan — 追踪数据流**
> 从用户输入（Source）追踪到危险函数（Sink），发现数据流上的安全漏洞。

**logic-scan — 审查业务逻辑**
> 遍历每个 API 端点，检查权限是否完整、业务逻辑是否安全。覆盖云安全审计（COS/S3 公开访问、IAM 过度授权、安全组暴露等）。

**red-team — 挖掘 0day 线索**
> 以攻击者视角，专挖前两个 Agent 覆盖不到的深层风险区域——这些正是 0day 漏洞最常出现的土壤。
> 三个聚焦方向：
> - **自造轮子**：自己实现加密/解析/鉴权而非用成熟库 → 高概率存在缺陷
> - **异常路径**：错误处理导致安全检查被跳过、权限状态不一致 → 传统测试最大盲区
> - **信任穿越**：内部 API 无认证暴露、微服务间盲信、第三方回调无验签

---

## 三种模式

| | Fast（极速） | Light（快速） | Deep（深度） |
|---|---|---|---|
| **耗时** | 3-12 分钟 | 5-10 分钟 | 20-40 分钟 |
| **适用** | Git Hook / IDE 自动扫 / CI 轻量门禁 | 日常开发、CI/CD、初筛 | 发布前审计、安全评审 |
| **扫描方式** | 编排器内联（Grep/Glob），执行纪律化（并行 Read、禁 sleep、禁后台 Agent） | 编排器内联（Grep/Glob） | 3 Agent 并行 + 语义追踪 |
| **验证深度** | 阶段 2 内联完成，无独立阶段 3 | 代码存在性 + 基础防御检查 | 脚本 3 层 + LLM 验证 + 评分 2 层 |
| **置信度上限** | 90 | 90 | 100 |
| **升级** | 扫完可一键升 Light / Deep | 扫完可一键升 Deep | — |

> 不确定选哪个？**自动化场景选 Fast，日常选 Light，正式审计选 Deep。**

---

## 使用方式

**全项目扫描：**
```
/security-scan:project [--scan-level fast|light|deep] [--include *.py,*.js] [--exclude node_modules] [--auto] [--background]
```

**Git 增量扫描：**
```
/security-scan:diff [--commit <hash>] [--scan-level fast|light|deep] [--mode staged|unstaged|all] [--auto] [--background]
```

**自动模式（无人值守）：**
```
/security-scan:diff --commit HEAD --scan-level light --auto
/security-scan:project --scan-level light --auto
```

> `--auto` 模式跳过所有交互（权限白名单自动配置、模式选择、修复跳过），自动执行扫描、验证、门禁评估和通知。**环境就绪降级**在正常模式与 `--auto` 模式下行为一致：检测到 LSP / tree-sitter 等依赖未就绪时一律自动降级继续，不再询问。**安全红线**：绝不自动修复代码。

> `--background` 支持将扫描放到后台运行（`project` / `diff` 均支持），仅支持 `--scan-level fast`。启动后主对话立即返回，扫描在独立 bg-scan Agent 中执行、不占用当前对话，完成后通过摘要回流告知结果。git commit 触发的自动扫描默认走后台（可在 `auto_scan.background` 配置项关闭）。

---

## 安全门禁配置

门禁相关能力分三块：**Setup 配置向导**（一键生成配置）、**企业微信通知**（发门禁告警）、**Git Hook 自动化**（commit 后自动增量扫描）。三者共享同一套分层配置。

### 分层配置架构

| 层级 | 路径 | 内容 | Git 提交 |
|------|------|------|---------|
| **用户级** | `~/.codebuddy/security-scan/config.json` | Webhook URL 等个人配置 | 不提交（隐私） |
| **项目级** | `.codebuddy/security-scan/config.json` | 门禁模式、auto_scan 等项目配置 | 可提交（团队共享） |
| **Hook 注册** | `.codebuddy/settings.json` | `hooks` 段 + 权限白名单 | 可提交 |

合并规则：**项目级 > 用户级 > 内置默认值**。Webhook 建议写入用户级（避免泄露），门禁/自动扫描策略建议写入项目级（团队对齐）。

---

## Setup 配置向导

执行 `/security-scan:setup` 进入交互式配置。向导会**一次性**展示两个标签页（← → 切换），Submit 后统一写入配置文件，首次配置与二次修改自动识别。

### 入口

```
/security-scan:setup
```

> 无参数。无需先运行 setup 才能扫描 —— 所有配置项都有合理默认值；但完成 setup 后，`--auto` 模式才能真正无人值守（不弹权限/通知/扫描模式询问）。

### 两个标签页

**标签页 1 · 通知配置**

- 直接粘贴企业微信 Webhook URL，即可完成并自动发送一条测试消息
- 选项：`获取方式`（显示获取指引）/ `跳过`（保持 `notification.enabled = false`）/ `发送测试消息`（二次配置下验证现有 URL）/ `关闭通知`
- URL 格式校验：必须 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...`，非法会重新询问

**标签页 2 · 自动扫描配置**

- 首次配置：`使用默认配置` / `自定义配置` / `关闭自动扫描`
- 二次配置：根据当前状态动态展示（已启用显示修改/关闭/跳过，已关闭显示启用/跳过）
- 选择"自定义"或"启用"后，会追问**扫描模式**（Fast / Light / Deep）和**触发模式**（阻断 / 非阻断）

### 默认值

| 配置项 | 默认 | 说明 |
|--------|------|------|
| `gate_mode` | `warn` | 告警模式，不阻断操作 |
| `notification.enabled` | `false` | 未配置 Webhook 则不通知 |
| `notification.trigger` | `on_scan` | 扫描完成后通知 |
| `auto_scan.enabled` | `true` | 启用 git commit 后自动扫描 |
| `auto_scan.scan_level` | `fast` | Hook 场景下 Fast 耗时最稳定 |
| `auto_scan.blocking` | `false` | 非阻断，静默执行不询问 |

### 写入位置

| 配置项 | 写入文件 |
|--------|---------|
| `notification.*`（Webhook URL、enabled、trigger） | 用户级 `~/.codebuddy/security-scan/config.json` |
| `gate_mode`、`auto_scan.*` | 项目级 `.codebuddy/security-scan/config.json` |
| Hook 注册、权限白名单 | 项目级 `.codebuddy/settings.json`（首次扫描时由权限白名单流程写入，非 setup 职责） |

二次配置时**只更新修改字段**，未改动项保留原值，不会覆写手工编辑。

### 典型使用场景

| 场景 | 操作 |
|------|------|
| 首次接入 | `/security-scan:setup` → 两个标签页都配一下 |
| 换企业微信群 | 重新 `/security-scan:setup`，在通知标签页粘贴新 URL |
| 临时关闭自动扫描 | `/security-scan:setup` → 自动扫描标签页选"关闭自动扫描" |
| 只想改扫描模式 | `/security-scan:setup` → 自动扫描标签页选"自定义配置" |
| 验证现有 Webhook | `/security-scan:setup` → 通知标签页选"发送测试消息" |

---

## 企业微信通知

> 当前仅支持企业微信机器人。Webhook URL 不硬编码，只从用户级 config.json 读取。

### 门禁模式

| 模式 | 行为 |
|------|------|
| `warn`（告警） | 发现问题时仅提醒，不阻断操作 |
| `strict`（严格） | 发现问题时强提醒，push 前二次确认 |

### 通知时机（`notification.trigger`）

| 配置值 | 触发场景 | 对应来源 |
|--------|---------|---------|
| `on_scan`（默认） | 扫描完成且门禁不通过 | `scan` / `hook-auto` |
| `on_push` | git push 前检测到门禁告警 | `push` |
| `both` | 两者都通知 | 全部来源 |

> 「trigger 和 source 不匹配」时会被静默丢弃。例如 `trigger=on_push` 时，Hook 自动扫描完成的告警不会发送。

### 消息样式

通知以 Markdown 格式发送，包含：

- **标题标签**：`[自动]`（Hook 触发）/ `[手动]`（用户运行）/ `[推送]`（push 前）
- **项目 / 分支 / 批次 ID**：取自 git 信息和扫描输出目录
- **门禁状态**：通过 / 告警 / 未通过（带颜色）
- **漏洞统计**：总数 / 严重 / 高 / 中 / 低 / 高置信度
- **违规项**：最多展示 5 条，超出以"及其他 N 项"折叠
- **评估时间**：北京时间 `YYYY-MM-DD HH:MM:SS`

### 调用点

| 触发点 | 命令 | 来源标记 |
|--------|------|---------|
| `/security-scan:project` 扫描完成 | `gate_reminder.py notify` | `scan` |
| `/security-scan:diff` 扫描完成 | `gate_reminder.py notify` | `scan` 或 `hook-auto` |
| `setup` 测试消息 | `gate_reminder.py test` | — |

> 发送为 best-effort：网络失败、URL 无效都不阻塞扫描流程，仅在 stderr 记录日志。

---

## Git Hook 自动化

插件通过**单一 Stop Hook** 实现 `git commit` 后自动增量扫描 + 静默上报，不劫持 PreToolUse，不修改 git 钩子脚本。

### 工作机制

Hook 注册在 `hooks/hooks.json` 的 `Stop` 事件下，每轮对话结束时由 CodeBuddy 执行：

| 脚本 | 作用 | 超时 |
|------|------|------|
| `git_commit_detector.py` | 扫 transcript 尾部（最多 2 MB），检测本轮是否成功执行过 `git commit`，若命中则指示 Agent 执行 `/security-scan:diff` | 10s |
| `report_upload_hook.py` | 静默上报未报告的审计/修复批次，始终 `exit 0` 不阻塞停止 | 25s |

> **检测范围**：只扫描当前轮次（从最后一条 user 消息到文件尾）的 Bash 调用与退出码，识别到 `git commit` 且 exit 0 才触发。
>
> **防止循环**：若 Agent 已因 Hook 继续过一次（`stop_hook_active=true`），直接跳过。

### 两种触发模式

由 `auto_scan.blocking` 决定（setup 第 2 个标签页配置）：

| 模式 | 行为 | 适用 |
|------|------|------|
| **非阻断**（`blocking: false`，默认） | Hook 直接指示 Agent 执行 `/security-scan:diff --commit <hash> --scan-level <level> --auto`，无交互 | 日常开发，"顺手扫一下"不打断思路 |
| **阻断** | Hook 让 Agent 用 `AskUserQuestion` 询问"是否扫描 + 选择扫描模式"，推荐项（当前配置的 `scan_level`）排在第一 | 重要分支 / 发版前 / 想每次人工确认 |

### 关闭 / 禁用 Hook

| 需求 | 操作 |
|------|------|
| 临时关闭自动扫描 | `/security-scan:setup` → 选"关闭自动扫描"（设 `auto_scan.enabled = false`） |
| 完全禁用 Hook | 卸载插件，或从 `.codebuddy/settings.json` 的 `hooks` 段移除 security-scan 条目 |
| 单次不扫 | 阻断模式下在 `AskUserQuestion` 选"跳过" |

### 配置示例

```json
// .codebuddy/security-scan/config.json（项目级，可提交）
{
  "version": "1.0",
  "gate_mode": "warn",
  "auto_scan": {
    "enabled": true,
    "scan_level": "fast",
    "blocking": false
  }
}
```

### 限制与约束

- **仅 commit 触发**：`git push`、`git merge`、`git rebase` 均不触发扫描（避免在 push 时卡住推送）
- **transcript 2 MB 窗口**：单轮对话过长（极少见）时，更早的 commit 可能被截断
- **不修改工作区**：Hook 只读 transcript，不注入 git hooks（`pre-commit` / `pre-push`），卸载插件即完全移除

---

## ⚠️ 初始化关键点

### 1. 权限白名单 — 必须配置

首次运行会弹出权限白名单配置确认，**请选择「确认配置」**。

| | 不配置 | 配置后 |
|---|---|---|
| 授权弹窗 | ~100 次/扫描 | ~8 次/扫描 |
| 体验 | 频繁中断 | 基本无感 |

> 白名单仅覆盖插件自身脚本和只读操作，**不涉及项目源码修改**。修复操作仍需逐次确认。
>
> 配置写入 `.codebuddy/settings.json`（项目级），团队可通过 Git 共享。

### 2. Deep 模式的可选依赖

以下依赖**缺失不影响扫描**，仅影响精度，插件会自动降级：

| 依赖 | 用途 | 缺失时 |
|------|------|--------|
| **tree-sitter** | 精确 AST 解析 | 降级为内置正则解析 |
| **LSP 服务器** | 跨文件语义追踪 | 降级为 Grep+Read |


### 3. 环境要求

| 依赖 | 要求 |
|------|------|
| CodeBuddy| 最新版本 |
| Python 3 | 3.8+ |
| Git | 任意版本 |

---

## 扫描产物

输出目录：`.codebuddy/security-scan/runs/{batch_id}/`

| 文件 | 说明 |
|------|------|
| `project-index.db` | 语义索引数据库 |
| `merged-scan.json` | 合并后的扫描结果 |
| `summary.json` | 验证后摘要 |
| `security-scan-report.html` | **HTML 审计报告**（自动生成） |
| `agents/*.json` | 各 Agent 产物 |

---

## 常见问题

**Q: 授权弹窗太多？**
→ 配置权限白名单。参考 `resource/permissions-allowlist.yaml` 底部示例，复制到 `.codebuddy/settings.json`。

**Q: Light 还是 Deep？**
→ 日常用 Light（快），发布前用 Deep（全）。不确定就先 Light，扫完可升级。

**Q: tree-sitter / LSP 安装失败？**
→ 不影响扫描，自动降级。如需完整能力：tree-sitter 用 venv 安装，LSP 安装后重启 CodeBuddy。

**Q: 扫描中断了？**
→ 部分 Agent 失败不影响整体，编排器会合并已有产物继续后续流程。

**Q: 不想 commit 后自动扫？**
→ `/security-scan:setup` → 自动扫描标签页选"关闭自动扫描"（设 `auto_scan.enabled = false`）。若要完全移除 Hook，从 `.codebuddy/settings.json` 的 `hooks` 段删掉 security-scan 条目或卸载插件。详见"Git Hook 自动化 > 关闭 / 禁用 Hook"。

**Q: 企业微信没收到通知？**
→ 依次检查：
1. `notification.enabled` 是否为 `true`（用户级 `~/.codebuddy/security-scan/config.json`）
2. `notification.trigger` 与触发来源是否匹配（`on_push` 不会收到 Hook 自动扫描的告警）
3. Webhook URL 是否有效：`/security-scan:setup` → 通知标签页选"发送测试消息"
4. 门禁状态是否为 `pass`（通过时不发通知，只有 warn / soft-block 会发）

---

## 更多信息

- 版本更新日志：[CHANGELOG.md](./CHANGELOG.md)
- 权限白名单详情：`resource/permissions-allowlist.yaml`
- 自定义规则：将 YAML 文件放入 `resource/custom/` 目录
