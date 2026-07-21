---
description: 配置安全门禁通知渠道和自动扫描设置。交互式引导用户依次完成通知配置和自动扫描配置。
allowed-tools: Read, Write, Bash, AskUserQuestion
---

# 安全门禁配置

> 所有面向用户的输出使用**简体中文**。禁止使用 emoji。JSON 字段名保持英文。

---

## 概述

本命令引导用户**依次**完成三项配置：

| 步骤 | 说明 |
|------|------|
| **步骤 1: 通知配置** | 配置企业微信 Webhook 通知渠道 |
| **步骤 2: 自动扫描配置** | 配置 git commit 后自动扫描的开关、扫描模式和触发模式 |
| **步骤 3: 知识自动更新配置** | 配置定时知识新鲜度检查，防止检测规则腐化 |

每个步骤均可跳过，全部完成后统一写入配置文件。

> **与 `--auto` 模式的关系**：`/security-scan:diff --auto` 和 `/security-scan:project --auto` 支持无人值守自动执行，其中扫描模式（`--scan-level`）可通过命令行参数指定，也可在此处通过 `auto_scan.scan_level` 预设默认值。通过 setup 提前完成权限白名单和通知渠道配置后，auto 模式可以完全无交互地执行到底。

配置采用**分层架构**：

| 层级 | 路径 | 内容 | Git 提交 |
|------|------|------|---------|
| **用户级** | `~/.codebuddy/security-scan/config.json` | Webhook URL 等个人配置 | 不提交 |
| **项目级** | `.codebuddy/security-scan/config.json` | 门禁模式、auto_scan 等项目配置 | 可提交 |

合并规则：项目级 > 用户级 > 内置默认值。

---

## 步骤 0: 加载现有配置

分别读取用户级和项目级配置文件的**完整内容**：

```
Read: ~/.codebuddy/security-scan/config.json
Read: .codebuddy/security-scan/config.json
```

> 如果 `Read` 失败（文件不存在），视为该层级无配置。

- 如果**任一**配置文件已存在，标记为**已有配置**（后续各步骤进入 Flow B）；否则标记为**首次配置**（后续各步骤进入 Flow A）。
- 如果进入 Flow B，**必须解析已读取的 JSON 内容**，按「项目级 > 用户级 > 内置默认值」的优先级合并，提取最终配置值（如 `auto_scan.scan_level`、`auto_scan.blocking`、`notification.enabled`、`notification.webhook_url` 等），用于后续步骤中展示当前配置的实际值。
- 缺失字段按「默认配置值」节中的默认值补全。

---

## 步骤 1+2+3: 一次性配置（多标签页）

根据步骤 0 的结果，进入 Flow A 或 Flow B。使用多问题 `AskUserQuestion` 一次展示所有配置项，用户通过顶部标签页（← →）切换，最后一次 Submit 提交。

### Flow A: 首次配置

首次配置直接进入 Webhook URL 输入。这样可以避免先选"配置企业微信通知"后仍需点击 `Submit` 才进入下一步的问题。

```
AskUserQuestion:
  questions:
    - header: "通知配置"
      question: |
        [1/3] 配置企业微信通知

        请直接粘贴企业微信群机器人 Webhook URL（格式:
        https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx）

        也可从下方选项中选择操作。
      options:
        - label: "获取方式"
          description: "了解如何获取企业微信群机器人 Webhook URL"
        - label: "跳过"
          description: "跳过通知配置，使用默认设置（后续可通过 /security-scan:setup 修改）"

    - header: "自动扫描"
      question: |
        [2/3] 配置 git commit 后的自动扫描功能

        当前默认设置:
          自动扫描: 已启用
          扫描模式: Fast（极速扫描）
          触发模式: 非阻断（静默执行）

        请选择操作：
      options:
        - label: "使用默认配置"
          description: "启用自动扫描，Fast + 非阻断模式（推荐日常开发使用）"
        - label: "自定义配置"
          description: "自定义扫描模式（Fast/Light/Deep）和触发模式（阻断/非阻断）"
        - label: "关闭自动扫描"
          description: "关闭 git commit 后的自动扫描功能"

    - header: "知识更新"
      question: |
        [3/3] 配置检测规则知识库的定时更新

        安全检测规则（Sink 模式、密钥格式等）会随时间腐化。
        启用定时更新后，系统每周自动检查知识新鲜度，为过期规则生成更新建议。

        当前默认设置:
          定时检查: 已启用
          检查频率: 每周一次
          更新方式: 半自动（生成候选更新，人工审核后合并）

        请选择操作：
      options:
        - label: "使用默认配置"
          description: "每周自动检查知识新鲜度，过期时生成更新建议（推荐）"
        - label: "自定义频率"
          description: "自定义检查频率（每天/每周/每两周/每月）"
        - label: "关闭知识更新"
          description: "关闭定时知识检查（不推荐，可能导致检测规则过期失效）"
```

**处理逻辑**：

Submit 后同时获得三个标签页的答案，分别处理：

**通知配置标签页**：

- **选择 `跳过`** → 使用默认配置（notification.enabled = false）。
  > 注意："跳过"仅跳过通知渠道，auto_scan 等其他配置项仍按默认值写入。

- **选择 `获取方式`** → 输出获取指引后，**单独重新展示通知配置问题**（单问题模式）：
  ```
  获取企业微信群机器人 Webhook URL:
    1. 打开企业微信群 → 右上角"..." → 群机器人 → 添加机器人
    2. 设置机器人名称（如"安全门禁告警"）
    3. 创建后复制 Webhook URL
  ```

- **通过 Other 输入内容** → 作为 Webhook URL 处理，验证格式：
  - 必须以 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=` 开头
  - key 参数不能为空
  - 格式不正确时提示并**单独重新展示通知配置问题**

  验证通过后，自动发送测试消息。

  > **脚本调用前必须先解析插件根目录**，使用以下命令（**禁止**用 `find`、`ls` 等方式手动搜索）：

  ```bash
  python3 -c "
  import json, sys; from pathlib import Path
  try:
    home = Path.home()
    s = json.loads((home/'.codebuddy'/'settings.json').read_text())
    km = json.loads((home/'.codebuddy'/'plugins'/'known_marketplaces.json').read_text())
    mid = [k.split('@',1)[1] for k,v in s.get('enabledPlugins',{}).items() if v and k.startswith('security-scan@')]
    if not mid: raise KeyError('not in enabledPlugins')
    loc = km[mid[0]]['installLocation']
    src = next((p['source'] for p in km[mid[0]].get('manifest',{}).get('plugins',[]) if p.get('name')=='security-scan'), './plugins/security-scan')
    root = str((Path(loc)/src).resolve())
    assert (Path(root)/'.codebuddy-plugin'/'plugin.json').exists()
    print(root)
  except Exception as e:
    print('FALLBACK:' + str(e), file=sys.stderr); sys.exit(1)
  "
  ```

  将输出记录为 `CODEBUDDY_PLUGIN_ROOT`，然后调用测试脚本：

  ```bash
  export CODEBUDDY_PLUGIN_ROOT="<解析出的路径>" && python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/gate_reminder.py" test \
    --webhook-url "<用户输入的URL>"
  ```

  - 成功 → "测试消息发送成功，请在企业微信群中确认是否收到。"
  - 失败 → 显示错误信息，提供"重新输入 URL / 保存当前 URL（跳过测试）"选项。选择跳过测试时，仍保存用户输入的 URL 并设置 notification.enabled = true。

**自动扫描标签页**：

- **选择 `使用默认配置`** → 设置 `auto_scan.enabled = true, auto_scan.scan_level = "fast", auto_scan.blocking = false, auto_scan.background = true`（`background` 仅在 `scan_level == "fast"` 时生效，让 commit 后的自动扫描走后台 bg-scan Agent，不占用主对话）。

- **选择 `自定义配置`** → **必须**调用 `AskUserQuestion` 展示「扫描模式选择」追问（包含扫描模式和触发模式两个问题）。等待用户回答后，根据用户选择设置对应值，并设置 `auto_scan.enabled = true`。

- **选择 `关闭自动扫描`** → 设置 `auto_scan.enabled = false`。

**知识更新标签页**：

- **选择 `使用默认配置`** → 设置 `knowledge_update.enabled = true, knowledge_update.frequency = "weekly", knowledge_update.auto_suggest = true`。

- **选择 `自定义频率`** → **必须**调用 `AskUserQuestion` 展示「知识检查频率选择」追问。等待用户回答后，根据用户选择设置对应值，并设置 `knowledge_update.enabled = true`。

- **选择 `关闭知识更新`** → 设置 `knowledge_update.enabled = false`。

三个标签页的答案均处理完毕后 → 进入**写入配置**。

### Flow B: 更新配置

使用步骤 0 中已解析的合并配置值，展示当前状态。

Webhook URL 脱敏：仅显示前 60 字符 + `...`。

根据当前 `auto_scan.enabled` 和 `knowledge_update.enabled` 的值，动态生成标签页选项：

**当自动扫描已启用时**：

```
AskUserQuestion:
  questions:
    - header: "通知配置"
      question: |
        [1/3] 更新企业微信通知配置

        当前配置:
          Webhook: {masked_url}
          状态: {notification.enabled ? "已启用" : "已关闭"}

        请直接粘贴新的企业微信群机器人 Webhook URL（格式:
        https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx）

        也可从下方选项中选择操作。
      options:
        - label: "发送测试消息"
          description: "使用当前 Webhook URL 发送一条测试消息，验证配置是否有效"
        - label: "关闭通知"
          description: "关闭企业微信通知（保留 URL 配置，后续可重新启用）"
        - label: "跳过"
          description: "不修改通知配置"

    - header: "自动扫描"
      question: |
        [2/3] 更新自动扫描配置

        当前配置:
          状态: 已启用
          扫描模式: {scan_level == "deep" ? "Deep（深度扫描）" : (scan_level == "fast" ? "Fast（极速扫描）" : "Light（快速扫描）")}
          触发模式: {blocking ? "阻断（询问用户）" : "非阻断（静默执行）"}
          执行方式: {background && scan_level == "fast" ? "后台（bg-scan Agent，不占用主对话）" : "前台（主对话内联）"}

        请选择操作：
      options:
        - label: "自定义配置"
          description: "修改扫描模式（Fast/Light/Deep）和触发模式（阻断/非阻断）"
        - label: "关闭自动扫描"
          description: "关闭 git commit 后的自动扫描功能"
        - label: "跳过"
          description: "不修改自动扫描配置"

    - header: "知识更新"
      question: |
        [3/3] 更新知识自动检查配置

        当前配置:
          状态: {knowledge_update.enabled ? "已启用" : "已关闭"}
          检查频率: {knowledge_update.frequency == "daily" ? "每天" : (knowledge_update.frequency == "weekly" ? "每周" : (knowledge_update.frequency == "biweekly" ? "每两周" : "每月"))}
          更新方式: 半自动（生成候选更新，人工审核后合并）

        请选择操作：
      options:
        - label: "自定义频率"
          description: "修改知识检查频率（每天/每周/每两周/每月）"
        - label: "{knowledge_update.enabled ? '关闭知识更新' : '启用知识更新'}"
          description: "{knowledge_update.enabled ? '关闭定时知识检查（不推荐）' : '启用定时知识新鲜度检查'}"
        - label: "跳过"
          description: "不修改知识更新配置"
```

**当自动扫描已关闭时**：

```
AskUserQuestion:
  questions:
    - header: "通知配置"
      question: |
        （同上，通知配置标签页内容不变）
      options:
        （同上）

    - header: "自动扫描"
      question: |
        [2/3] 更新自动扫描配置

        当前配置:
          状态: 已关闭

        请选择操作：
      options:
        - label: "启用自动扫描"
          description: "启用 git commit 后的自动扫描功能"
        - label: "跳过"
          description: "不修改自动扫描配置"

    - header: "知识更新"
      question: |
        （同上，知识更新标签页内容不变）
      options:
        （同上）
```

**处理逻辑**：

Submit 后同时获得三个标签页的答案，分别处理：

**通知配置标签页**：

- **选择 `发送测试消息`** → 使用当前配置中的 Webhook URL 执行测试，复用 Flow A 的测试逻辑（注意脚本路径定位方式，见 Flow A 中的注意事项）。

- **选择 `关闭通知`** → 设置 `notification.enabled: false`，保留其他配置（方便后续重新启用）。

- **选择 `跳过`** → 不修改通知配置。

- **通过 Other 输入内容** → 作为新 Webhook URL 处理，复用 Flow A 的 URL 验证与测试流程（注意脚本路径定位方式，见 Flow A 中的注意事项）。

**自动扫描标签页**：

- **选择 `自定义配置`** → **必须**调用 `AskUserQuestion` 展示「扫描模式选择」追问（包含扫描模式和触发模式两个问题）。等待用户回答后，根据用户选择设置对应值，并设置 `auto_scan.enabled = true`。

- **选择 `关闭自动扫描`** → 设置 `auto_scan.enabled = false`。

- **选择 `启用自动扫描`** → **必须**调用 `AskUserQuestion` 展示「扫描模式选择」追问（包含扫描模式和触发模式两个问题）。等待用户回答后，根据用户选择设置对应值。

- **选择 `跳过`** → 不修改配置。

**知识更新标签页**：

- **选择 `自定义频率`** → **必须**调用 `AskUserQuestion` 展示「知识检查频率选择」追问。等待用户回答后，根据选择设置对应值，并设置 `knowledge_update.enabled = true`。

- **选择 `关闭知识更新`** → 设置 `knowledge_update.enabled = false`。

- **选择 `启用知识更新`** → **必须**调用 `AskUserQuestion` 展示「知识检查频率选择」追问。等待用户回答后，根据选择设置对应值。

- **选择 `跳过`** → 不修改配置。

三个标签页的答案均处理完毕后 → 进入**写入配置**。

### 扫描模式选择

当用户需要选择扫描配置时（从"自定义配置"或"启用自动扫描"进入），单独追问（两个问题同时展示）：

```
AskUserQuestion:
  questions:
    - header: "扫描模式"
      question: |
        请选择扫描模式：
      options:
        - label: "Fast 极速扫描"
          description: "Light + 执行纪律（并行 Read / 扫描验证合并）。Hook 场景推荐"
        - label: "Light 快速扫描"
          description: "基于 Grep 模式匹配的快速增量扫描"
        - label: "Deep 深度扫描"
          description: "多 Agent 并行 + 语义追踪的深度增量扫描"

    - header: "触发模式"
      question: |
        请选择触发模式：

        git commit 后检测到变更时的行为方式。
      options:
        - label: "非阻断（推荐）"
          description: "静默执行扫描，不询问用户，扫描完自动结束"
        - label: "阻断"
          description: "弹出选项询问用户是否扫描、选择扫描模式"
```

- **扫描模式**：选择 `Fast 极速扫描` → `auto_scan.scan_level = "fast"`；选择 `Light 快速扫描` → `auto_scan.scan_level = "light"`；选择 `Deep 深度扫描` → `auto_scan.scan_level = "deep"`
- **触发模式**：选择 `非阻断` → `auto_scan.blocking = false`；选择 `阻断` → `auto_scan.blocking = true`

设置完成后 → 进入**写入配置**。

### 知识检查频率选择

当用户需要选择知识更新频率时（从"自定义频率"或"启用知识更新"进入），单独追问：

```
AskUserQuestion:
  questions:
    - header: "检查频率"
      question: |
        请选择知识新鲜度检查频率：

        频率越高，知识腐化风险越低，但会产生更多的候选更新需要审核。
        建议：安全生态变化快，推荐至少每周检查一次。
      options:
        - label: "每天"
          description: "每天检查一次知识新鲜度（适合安全研究团队）"
        - label: "每周（推荐）"
          description: "每周检查一次，平衡更新频率和审核负担"
        - label: "每两周"
          description: "每两周检查一次"
        - label: "每月"
          description: "每月检查一次（不推荐，部分知识可能 30 天内就过期）"
```

- **检查频率**：选择 `每天` → `knowledge_update.frequency = "daily"`；选择 `每周（推荐）` → `knowledge_update.frequency = "weekly"`；选择 `每两周` → `knowledge_update.frequency = "biweekly"`；选择 `每月` → `knowledge_update.frequency = "monthly"`

设置完成后 → 进入**写入配置**。

---

## 默认配置值

首次配置自动使用以下默认值，无需逐项询问（用户在各步骤中修改的值会覆盖对应默认值）：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `gate_mode` | `"warn"` | 告警模式，发现问题仅提醒不阻断 |
| `notification.trigger` | `"on_scan"` | 扫描完成且门禁不通过时通知 |
| `auto_scan.enabled` | `true` | git commit 后自动触发增量扫描 |
| `auto_scan.scan_level` | `"fast"` | 自动扫描使用的模式（`fast` / `light` / `deep`；Hook 场景默认 fast 追求执行稳定性与耗时可预期） |
| `auto_scan.blocking` | `false` | 非阻断模式，静默执行扫描不询问用户 |
| `knowledge_update.enabled` | `true` | 启用定时知识新鲜度检查 |
| `knowledge_update.frequency` | `"weekly"` | 检查频率（`daily` / `weekly` / `biweekly` / `monthly`） |
| `knowledge_update.auto_suggest` | `true` | 过期时自动生成候选更新建议 |

---

## 写入配置

### 分层写入

**用户级** `~/.codebuddy/security-scan/config.json`：
```json
{
  "version": "1.0",
  "configuredAt": "<ISO8601>",
  "notification": {
    "enabled": true,
    "channel": "wecom",
    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    "trigger": "on_scan"
  }
}
```

**项目级** `.codebuddy/security-scan/config.json`：
```json
{
  "version": "1.0",
  "configuredAt": "<ISO8601>",
  "gate_mode": "warn",
  "auto_scan": {
    "enabled": true,
    "scan_level": "fast",
    "blocking": false
  },
  "knowledge_update": {
    "enabled": true,
    "frequency": "weekly",
    "auto_suggest": true
  }
}
```

### 写入步骤

1. 确保 `~/.codebuddy/security-scan/` 和 `.codebuddy/security-scan/` 目录存在
2. 将通知相关配置写入用户级文件
3. 将门禁策略和自动扫描配置写入项目级文件
4. 如果是更新配置（Flow B），仅更新本次修改的字段，保留未修改的现有配置

### 配置完成输出

```
安全门禁配置完成。

  模式: 告警模式
  自动扫描: {auto_scan.enabled ? "已启用（" + (auto_scan.scan_level == "deep" ? "Deep" : (auto_scan.scan_level == "fast" ? "Fast" : "Light")) + "，" + (auto_scan.blocking ? "阻断" : "非阻断") + "）" : "已关闭"}
  知识更新: {knowledge_update.enabled ? "已启用（" + (knowledge_update.frequency == "daily" ? "每天" : (knowledge_update.frequency == "weekly" ? "每周" : (knowledge_update.frequency == "biweekly" ? "每两周" : "每月"))) + "检查）" : "已关闭"}
  通知渠道: {notification.enabled ? "企业微信机器人" : "未配置"}
  通知时机: {notification.enabled ? "扫描完成后" : "-"}

配置文件:
  用户级: ~/.codebuddy/security-scan/config.json
  项目级: .codebuddy/security-scan/config.json

可用命令:
  /security-scan:diff --auto          增量扫描（自动模式，无人值守）
  /security-scan:project --auto       全项目扫描（自动模式，无人值守）
  /security-scan:setup                随时修改配置
```

### 知识更新定时任务注册

当 `knowledge_update.enabled = true` 时，写入配置后**自动注册** CodeBuddy Automation 定时任务：

**频率到 RRULE 映射**：

| frequency | RRULE | 说明 |
|-----------|-------|------|
| `daily` | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` | 每天上午 9:00 |
| `weekly` | `FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0` | 每周一上午 9:00 |
| `biweekly` | `FREQ=WEEKLY;INTERVAL=2;BYDAY=MO;BYHOUR=9;BYMINUTE=0` | 每两周一上午 9:00 |
| `monthly` | `FREQ=WEEKLY;INTERVAL=4;BYDAY=MO;BYHOUR=9;BYMINUTE=0` | 约每月一上午 9:00 |

**Automation prompt**（注册到 CodeBuddy Automation 的执行指令）：

```
执行安全扫描知识库新鲜度检查和候选更新生成：

1. 解析插件根目录（CODEBUDDY_PLUGIN_ROOT）
2. 执行 check-freshness：
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/knowledge_updater.py" check-freshness --resource-dir "${CODEBUDDY_PLUGIN_ROOT}/resource/"
3. 如果有 stale 或 aging 文件，执行 suggest-updates：
   python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/knowledge_updater.py" suggest-updates --resource-dir "${CODEBUDDY_PLUGIN_ROOT}/resource/" --output-dir "${CODEBUDDY_PLUGIN_ROOT}/pending-updates/"
4. 输出简要摘要：哪些文件过期、生成了哪些候选更新文件
5. 如果所有知识文件均为 fresh 状态，输出"知识库状态良好，无需更新"
```

**注册逻辑**：

- 如果 `knowledge_update.enabled = true`：使用 `automation_update` 工具的 `suggested create` 模式创建定时任务，状态设为 `ACTIVE`
- 如果 `knowledge_update.enabled = false`：检查是否有已存在的知识更新 Automation，如有则用 `suggested update` 将状态改为 `PAUSED`
- 如果是更新配置（Flow B）且频率变更：用 `suggested update` 更新 rrule

---

## 错误处理

- Webhook URL 格式不合法 → 重新询问
- 测试消息发送失败 → 提供"重新输入 URL / 保存当前 URL（跳过测试）"选项
- 目录不存在 → 自动创建
- 配置文件写入失败 → 显示错误并提示手动创建
