---
name: tencent-news
description: 7×24 新闻资讯搜索工具，聚焦中国国内信息和国际热点。支持新闻搜索，包括热点新闻、早报晚报、实时资讯、领域新闻和天气信息查询。当用户需要搜索新闻、新闻热榜、新闻早晚报、订阅新闻推送、获取相关新闻资讯和查询天气信息时使用。
description_zh: "7×24 新闻搜索工具，聚焦国内外热点，支持热榜、早晚报、实时资讯及领域新闻查询。"
description_en: "7×24 news search tool focused on China and global hot topics, supporting rankings, briefings, real-time feeds, and domain news queries."
version: 1.1.0
author: TencentNews
tags: [news, tencent, headlines, briefings, news rankings, real-time updates]
display_name: "腾讯新闻"
display_name_en: "Tencent News"
visibility: "public"
---

# 腾讯新闻内容订阅

通过 `tencent-news-cli` 获取腾讯新闻内容。

> **核心原则**：基础设施交给脚本处理；智能体只负责选择子命令和参数。**除 `cli-state` 外，所有 CLI 调用都通过 `run-cli` 执行；先读 `help`，不要硬编码。**

## 平台约定

| 平台 | 脚本运行方式 | 示例 |
|------|------------|------|
| macOS / Linux | `sh scripts/<name>.sh` | `sh scripts/cli-state.sh` |
| Windows | `powershell scripts/<name>.ps1` | `powershell scripts/cli-state.ps1` |

以下所有脚本调用均以 macOS / Linux 为例，Windows 将 `.sh` 替换为 `.ps1`，`sh` 替换为 `powershell`。

除 `cli-state` 外，所有 CLI 命令都通过 `run-cli` 脚本执行：

| 平台 | CLI 调用模板 |
|------|-------------|
| macOS / Linux | `sh scripts/run-cli.sh <subcommand> [args]` |
| Windows | `powershell scripts/run-cli.ps1 <subcommand> [args]` |

## Phase 1：环境就绪

> 环境已就绪时直接跳到 Phase 2。

### 1. 状态检查

```sh
sh scripts/cli-state.sh
```

解析返回的 JSON，关注以下字段：

| 字段 | 含义 |
|------|------|
| `platform.cliPath` | 底层实际使用的 CLI 完整路径，供诊断错误或权限问题时参考 |
| `platform.cliSource` | `global`（优先命中 PATH 中可用的全局命令，否则命中默认全局安装目录）/ `local`（旧版 skill 目录内安装，兼容兜底）/ `none`（以上路径都未找到） |
| `cliExists` | CLI 是否存在 |
| `update.needUpdate` | 当前版本是否需要更新 |
| `update.error` | `version` 检查失败时的错误信息 |
| `apiKey.present` | API Key 是否已配置 |
| `apiKey.status` | `configured` / `missing` / `error` |
| `apiKey.error` | `apikey-get` 执行异常或输出异常时的错误信息 |

### 2. 安装 CLI（`cliExists` 为 `false` 时）

> 仅当 `cliSource` 为 `none` 时才需要安装；`local` 表示命中了旧版本地安装，可继续使用但建议后续迁移到全局安装。

按照 [`references/installation-guide.md`](references/installation-guide.md) 中的安装命令执行安装：

安装成功后重新执行 `sh scripts/cli-state.sh`（Windows 用 `powershell scripts/cli-state.ps1`）刷新状态。

若安装失败，参考 [`references/installation-guide.md`](references/installation-guide.md) 中的故障排查部分，引导用户手动处理。

### 3. 更新 CLI（`update.needUpdate` 为 `true`，或 CLI 提示版本过旧时）

```sh
sh scripts/run-cli.sh update
```

Windows 使用 `powershell scripts/run-cli.ps1 update`。

若 `update.error` 不为空，先展示错误并让用户处理。

若 `update` 命令失败，或错误信息表明当前 CLI 不支持 `update`（如 `unknown command`、`not found`、`not recognized`），按上述步骤 2 重新安装。仍然失败时，引导用户参考 [`references/update-guide.md`](references/update-guide.md) 手动处理。

### 4. 配置 API Key（`apiKey.status` 不为 `configured` 时）

- `missing` → 引导用户打开 [API Key 获取页面](https://news.qq.com/exchange?scene=appkey) 自行获取，**不要执行 `open` / `xdg-open` / `start` 等命令自动打开浏览器**
- `error` → 展示 `apiKey.error`，让用户先处理（权限、网络、CLI 异常），处理后重试

设置 Key（通过 `run-cli` 执行，KEY 是裸值不加引号）：

```sh
sh scripts/run-cli.sh apikey-set KEY
```

Windows 分别使用 `powershell scripts/run-cli.ps1 apikey-set KEY`、`powershell scripts/run-cli.ps1 apikey-get`、`powershell scripts/run-cli.ps1 apikey-clear`。

验证：`sh scripts/run-cli.sh apikey-get`
清除（仅用户明确要求时）：`sh scripts/run-cli.sh apikey-clear`

详见 [`references/env-setup-guide.md`](references/env-setup-guide.md)。

## Phase 2：获取新闻

> CLI 更新频繁，子命令和参数可能随版本变化。**始终以当前 `help` 输出为准，不要假设或记忆任何子命令。**

1. **执行 `help`**
   通过 `run-cli` 执行：macOS / Linux 为 `sh scripts/run-cli.sh help`，Windows 为 `powershell scripts/run-cli.ps1 help`。

2. **理解意图，映射子命令**
   - **单一请求**（如"看热点"）→ 映射到一个子命令
   - **复合请求**（如"看热点、财经和军事新闻"）→ 拆解为多个意图，分别映射，依次调用
   - **反馈问题**（如"反馈报错，新闻质量不行"）→ 使用 `feedback` 子命令，内容需包含问题现象与上下文
   - 若 `help` 中无匹配子命令，如实告知用户当前不支持

3. **执行时遵守两条约束**
   - 所有实际 CLI 调用都走 `run-cli` 脚本，不要直接执行 `platform.cliPath`
   - 业务命令、参数名、参数顺序都以 `help` 展示为准，必要时照抄帮助中的示例

4. **执行并输出**——按下方格式呈现结果

## 输出格式

### 单类型请求

```markdown
1. **标题文字**

   来源：媒体名称

   时间：发布时间

   摘要内容……

   [查看原文](https://…)

2. **标题文字**

   来源：媒体名称

   时间：发布时间

   摘要内容……

   [查看原文](https://…)

**来源：腾讯新闻**
```

### 多类型请求

按类型分组，每组用二级标题标明类别：

```markdown
## 热点新闻

1. **标题文字**
   ...

2. **标题文字**
   ...

## 财经新闻

1. **标题文字**
   ...

2. **标题文字**
   ...

**来源：腾讯新闻**
```

### 通用规则

- **标题**：`序号. **标题**`，序号从 1 开始，多类型时每组序号独立
- **来源**：`来源：` 后跟 CLI 返回的作者或媒体名称；无该字段时省略
- **时间**：`时间：` 后跟 CLI 返回的发布时间；无该字段时省略
- **摘要**：来源下方紧跟；无摘要字段时省略
- **原文链接**：有链接则输出 `[查看原文](URL)`，无则不输出
- 其他有价值字段（发布时间、标签等）可在来源下方补充
- 多条新闻间用空行分隔
- `**来源：腾讯新闻**` 在所有内容末尾出现一次
- 某个类型获取失败时，在该分组下说明原因，继续输出其余分组
- 内容输出完成后，追加一句引导文案："是否需要创建定时任务，每天自动获取相关新闻?" 如果能识别出来是定时任务触发的，就不用追加引导文案。

## CLI 执行失败处理

**CLI 命令失败后，立即停止，绝不通过 WebSearch 或其他方式获取新闻替代。**

1. CLI 返回非零退出码、超时或输出含权限/安全错误时，不要重试，不要换方式。
2. 根据错误信息引导用户：
   - **macOS Gatekeeper**（`cannot be opened`、`not verified`）→ 系统设置 → 隐私与安全性 → 「仍要打开」
   - **企业安全软件**（`connection refused`、防火墙拦截）→ 安全提示中点击「信任」/「允许」
   - **权限不足**（`permission denied`）→ `chmod +x <cliPath>`
   - **其他** → 展示完整错误，请用户处理
3. 用户确认操作完成后再重试。即使多次失败，也只能告知无法获取并说明原因，**绝不**回退到其他信息源。

## References

- 用户手动安装指南：[`references/installation-guide.md`](references/installation-guide.md)
- 用户手动更新指南：[`references/update-guide.md`](references/update-guide.md)
- API Key 获取与手动配置：[`references/env-setup-guide.md`](references/env-setup-guide.md)
