# 共享初始化流程

> 引用方：commands/project.md、commands/diff.md
>
> **Fast / Light 模式快捷路径**：仅需执行 init-步骤0（插件根目录）→ init-步骤1（权限）→ init-步骤2（模式选择）→ init-步骤5（环境就绪确认），直接跳过 init-步骤3（tree-sitter）和 init-步骤4（LSP）。

---

## 自动模式（--auto）对初始化的影响

当命令传入 `--auto` 参数时，初始化流程中所有用户交互点均自动跳过，确保非交互式执行到底：

| 交互点 | 正常模式 | --auto 模式 |
|--------|---------|------------|
| init-步骤1 权限白名单确认 | AskUserQuestion | **自动执行配置/更新**（权限白名单仅涉及插件自身脚本的只读权限，auto 模式下自动配置是安全的） |
| init-步骤2 模式选择 | AskUserQuestion | 使用 `--scan-level` 参数（默认 light） |
| init-步骤5 环境就绪确认（pendingActions 不为空） | **直接降级继续扫描**（不再弹出 AskUserQuestion） | 行为同正常模式：自动降级继续扫描 |

---

## 设计原则

1. **做完一件再做下一件**：每个组件检测完立刻处理（安装/配置），不拆散到后续步骤
2. **能自动的不问人**：tree-sitter、LSP 二进制均尝试自动安装；权限白名单在正常模式下需用户确认后写入，**`--auto` 模式下自动执行配置**
3. **按需准备**：Fast / Light 模式不需要 tree-sitter 和 LSP，就不检测、不安装、不提示
4. **降级不中断**：安装失败或环境依赖未就绪时**始终自动降级继续扫描，不阻塞用户**（不再询问跳过或取消）；安装指引会在降级输出中给出，供用户事后手动配置

---

## 流程总览

```
init-步骤0  插件根目录：注册表定位（enabledPlugins + known_marketplaces.json）→ Glob 兜底 → export CODEBUDDY_PLUGIN_ROOT
init-步骤1  权限：检查 → 用户确认 → 配置
init-步骤2  模式选择
init-步骤3  tree-sitter：检测 → 自动安装（仅 Deep 模式）
init-步骤4  LSP：探活 → 自动安装（仅 Deep 模式）
init-步骤5  环境就绪确认
```

---

## 初始化阶段: 插件根目录解析

> **此步骤为所有后续步骤的前置条件，必须最先执行。**
>
> 插件文档和脚本通过 `${CODEBUDDY_PLUGIN_ROOT}` 引用自身目录。
> 框架**不一定**对 command 内容做内联替换（仅确认对 skill、agent、hook 内容做替换）。
> 因此需要在初始化阶段**确定性地**解析出插件根目录绝对路径，供编排器和子 Agent 使用。

### 解析方法

采用**注册表优先**策略：通过 `enabledPlugins` + `known_marketplaces.json` 确定性定位，避免同名插件跨 marketplace 时命中错误副本。

#### 方法一：注册表定位（优先）

执行以下内联命令（一次 Bash 调用）：

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

> 解析链路：`enabledPlugins["security-scan@{marketplace}"]` → `known_marketplaces.json[marketplace].installLocation` → 拼接 manifest 中的 `source` 相对路径 → 校验 `plugin.json` 存在。

- 正常输出插件根目录路径，直接赋给 `CODEBUDDY_PLUGIN_ROOT`，**解析完成**。
- exit 1 时进入方法二。

#### 方法二：Glob 兜底（仅当方法一失败时）

依次在以下目录搜索，合并所有匹配结果：

1. `~/.codebuddy/plugins/marketplaces/` — 覆盖所有已缓存的 marketplace（zip 类型）
2. `known_marketplaces.json` 中所有 `directory` 类型市场的 `installLocation` — 覆盖本地开发市场

> 若 `known_marketplaces.json` 不可读或解析失败，跳过搜索2，仅使用搜索1 的结果。

```
# 搜索1：已缓存的 marketplace
Glob(path: ~/.codebuddy/plugins/marketplaces): **/security-scan/.codebuddy-plugin/plugin.json

# 搜索2：directory 类型市场（从 known_marketplaces.json 读取 installLocation）
# 对每个 directory 类型市场执行：
Glob(path: {installLocation}): **/security-scan/.codebuddy-plugin/plugin.json
```

从匹配结果中提取插件根目录：取 `plugin.json` 路径去掉尾部 `/.codebuddy-plugin/plugin.json` 即为插件根目录。

**多结果消歧规则**（按优先级依次应用）：
1. 排除路径中包含 `node_modules`、`.cache`、`dist`、`vendor`、`build` 的结果
2. 优先选择路径中包含 `enabledPlugins` 对应 marketplace 的 `installLocation` 的结果
3. 若仍有多个结果，选择路径最短的结果
4. 若长度相同，选择字母序最前的结果（确保确定性）

### 结果记录

记录 `CODEBUDDY_PLUGIN_ROOT` 为解析出的绝对路径。后续所有 Bash 调用插件脚本时，必须使用以下格式：

```bash
export CODEBUDDY_PLUGIN_ROOT="<解析出的绝对路径>" && python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/xxx.py" ...
```

### 传递给子 Agent

编排器启动子 Agent 时，必须在 Agent 提示词中明确告知插件根目录的绝对路径：

```
[插件根目录] CODEBUDDY_PLUGIN_ROOT={resolvedPluginRoot}
后续所有 Bash 调用插件脚本前，必须先 export：
export CODEBUDDY_PLUGIN_ROOT="{resolvedPluginRoot}"
```

### 解析失败处理

若方法一和方法二均无结果，输出错误并终止：

```
插件根目录解析失败：未找到 security-scan/.codebuddy-plugin/plugin.json。
请确认 security-scan 插件已正确安装。可通过 /plugin 查看已安装插件列表。

排查步骤：
1. 检查 ~/.codebuddy/settings.json 中 enabledPlugins 是否包含 "security-scan@<marketplace>"
2. 检查 ~/.codebuddy/plugins/known_marketplaces.json 中对应 marketplace 的 installLocation 是否正确
3. 确认 installLocation 下 plugins/security-scan/.codebuddy-plugin/plugin.json 文件存在
```

---

## 初始化阶段: 权限检查与配置

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/check_permissions.py"
```

> 脚本支持 `--allowlist <path>` 覆盖默认白名单。默认读取 `${CODEBUDDY_PLUGIN_ROOT}/resource/permissions-allowlist.yaml`。
> 优先检查项目级 `.codebuddy/settings.json`，缺失则回退用户级 `~/.codebuddy/settings.json`。
> 输出 JSON：`{"status": "missing|outdated|current", "missing": [...]}`

记录 `permissionsStatus` 和 `permissionsMissing`。

| permissionsStatus | 行为 |
|-------------------|------|
| `current` | 跳过，无需操作 |
| `outdated` | 询问用户确认后，增量追加缺失条目到 `settings.json`（只追加不删除，保留用户自定义规则） |
| `missing` | 询问用户确认后，全新写入：读取 `permissions-allowlist.yaml` 完整内容写入 `.codebuddy/settings.json` |

### 用户确认（`missing` 或 `outdated` 时触发）

> **`--auto` 模式**：跳过 AskUserQuestion，直接自动执行配置/更新。权限白名单仅涉及插件自身脚本的只读执行权限和输出目录写权限，auto 模式下自动配置是安全的。
>
> - `missing` → 自动执行全新写入，输出 `[auto] 已自动配置权限白名单（.codebuddy/settings.json）。`
> - `outdated` → 自动执行增量追加，输出 `[auto] 已自动更新权限白名单，新增 {len(permissionsMissing)} 条授权规则。`

**全新配置**（`missing`，正常模式）：

```
AskUserQuestion:
  question: |
    检测到尚未配置插件权限白名单。
    配置后可自动授权插件运行所需Bash查询和插件输出目录的写权限，减少约 **90%+** 的授权弹窗。
    白名单将增量写入 `.codebuddy/settings.json`。
  options:
    - label: "确认配置"
      description: |
        增量写入权限白名单到 `.codebuddy/settings.json`，后续插件自动获得执行权限。
    - label: "跳过"
      description: |
        不配置白名单，扫描过程中每次执行脚本都需要手动授权。
```

用户选择「确认配置」：执行写入，输出：

```
已配置权限白名单（`.codebuddy/settings.json`）。
```

用户选择「跳过」：`permissionsStatus = "skipped"`，继续后续步骤。

**增量更新**（`outdated`，正常模式）：

```
AskUserQuestion:
  question: |
    权限白名单需要更新，新增 **{len(permissionsMissing)}** 条授权规则。
    更新方式为增量追加，不会删除您已有的自定义规则。
  options:
    - label: "确认更新"
      description: |
        追加新增的授权规则到 `.codebuddy/settings.json`，保留现有自定义规则。
    - label: "跳过"
      description: |
        不更新白名单，部分新增脚本可能需要手动授权。
```

用户选择「确认更新」：执行增量追加，输出：

```
已更新权限白名单，新增 **{len(permissionsMissing)}** 条授权规则。
```

用户选择「跳过」：`permissionsStatus = "skipped"`，继续后续步骤。

---

## 初始化阶段: 扫描模式选择

> Ref: `${CODEBUDDY_PLUGIN_ROOT}/references/workflows/scan-mode.md > 模式选择交互`

优先解析命令行参数 `--scan-level fast|light|deep`，未指定时弹出交互。

> **`--auto` 模式**：使用 `--scan-level` 参数指定的模式（默认 light），跳过 AskUserQuestion。

正常模式下未指定 `--scan-level` 时弹出交互：

```
AskUserQuestion:
  question: |
    请选择扫描模式：
  options:
    - label: "极速扫描（Fast）"
      description: |
        在 Light 基础上应用执行纪律（并行 Read、禁 sleep、禁后台 Agent）。
        扫描与验证合并。适合 Hook / IDE / CI 自动化场景。
        claude下参考耗时：{fastEstimate}
    - label: "轻量扫描（Light）"
      description: |
        基于 Grep/Glob 的快速扫描，聚焦高危漏洞，轻量验证。
        claude下参考耗时：{lightEstimate}
    - label: "深度扫描（Deep）"
      description: |
        多 Agent 并行 + 语义追踪 + 对抗验证，全面深度审计。
        claude下参考耗时：{deepEstimate}
```

> 耗时参考：project Fast 约 3-12 分钟、Light 约 5-10 分钟、Deep 约 20-40 分钟；diff Fast 约 2-8 分钟、Light 约 3-10 分钟、Deep 约 10-30 分钟。

记录 `scanMode = "fast" | "light" | "deep"`。

> Fast 与 Light 在初始化阶段完全相同（均跳过 tree-sitter 和 LSP）。Fast 的差异从阶段 1 开始生效，见 `scan-mode-fast.md > Fast 模式硬性约束（必读）`。

---

## 初始化阶段: AST解析器探活与安装（仅 Deep 模式）

Fast / Light 模式**整体跳过**（同时跳过 init-步骤4），直接进入 init-步骤5。

**前置条件**：`scanMode == "deep"`

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/ts_parser.py" check
```

记录 `treeSitterInstalled`。若 `false`，立刻安装：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/ts_parser.py" setup
```

安装成功输出：

```
**正在安装 AST 解析器（tree-sitter）...**
tree-sitter 安装成功，已启用 **{n}** 种语言的精确 AST 解析。
```

安装失败输出：

```
tree-sitter 安装失败（**{failReason}**），已自动降级为内置正则解析器。
```

> 常见失败原因：Python 3.12+ PEP 668 限制。手动安装：`python3 -m venv ~/.venvs/codebuddy-security && source ~/.venvs/codebuddy-security/bin/activate && pip install tree-sitter tree-sitter-languages`

记录 `parserType`：`treeSitterInstalled ? "tree-sitter" : "regex-fallback"`。

---

## 初始化阶段: LSP 探活与安装（仅 Deep 模式）

Fast / Light 模式**整体跳过**，直接进入 init-步骤5。

**前置条件**：`scanMode == "deep"`

### 4a 语言检测 + 探活

> **重要**：`lsp_setup.py` 仅有 3 个子命令：`detect`、`steps`、`format`。**没有** `probe` 子命令。
> 探活（probe）是通过 **IDE 的 LSP 工具**（hover / documentSymbol）执行的，不是通过 `lsp_setup.py` 执行的。

**第一步：语言检测**（调用 `lsp_setup.py detect`）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/lsp_setup.py" detect --project-path "$(pwd)"
```

> 输出 JSON：`{"language": "Java", "binaryInstalled": true, "binary": "jdtls", ...}`

- `language == null`：`lspStatus = "unsupported"`，**结束 init-步骤4**
- `language == "Kotlin"`（`supported == false`）：Kotlin 无可用 LSP 服务器，`lspStatus = "unsupported"`，自动降级为 `Grep+AST`（tree-sitter 支持 Kotlin AST 解析），**结束 init-步骤4**
- `language != null` 且 `supported == true`：进入第二步——使用 LSP 工具执行探活

**第二步：LSP 工具探活**（使用 IDE 的 LSP hover，**不是** `lsp_setup.py` 命令）：

```
1. 按语言选取优先级最高的文件类型的 1 个源文件（记为 probeFile）
2. 使用 IDE 的 LSP hover 工具：LSP hover(probeFile, line=targetLine, character=targetChar)
3. 有返回结果（含空对象/空数组）→ lspStatus = "available"，结束 init-步骤4
4. 返回错误信息 → 探活失败，记录 lspLanguage、binaryInstalled，进入 4b
```

**probeFile 选择**：排除 node_modules/vendor/dist/build/.git、自动生成文件、空文件、>10000 行文件。优选含类/函数定义、10-500 行的源文件。

**hover 位置选择**：Read probeFile 前 30 行，找第一个非空、非注释、非 import 且含标识符的行。前 30 行全是 import/注释时改用 LSP documentSymbol。

**成功/失败判定**：返回任何非错误结果即为成功。错误信息含 `"No LSP server configured"` / `"failed to start"` / `"timed out"` / `"request failed"` 或工具调用本身报错才视为失败。

### 4b 自动安装 LSP 二进制

若 `binaryInstalled == false`，使用 `detect` 输出的 `installCommand` 安装，成功后二次探活。

> **故障排除**：若 LSP 安装/探活反复失败，可能是 CodeBuddy 资产插件缓存损坏。可尝试删除用户目录下的 plugins 文件夹后重启 CodeBuddy，让其重新拉取插件资产：
> - macOS / Linux：`rm -rf ~/.codebuddy/plugins`
> - Windows：`rd /s /q %USERPROFILE%\.codebuddy\plugins`
>
> 删除后关闭并重新打开 CodeBuddy 即可自动恢复。

### 4c 生成 pendingActions

探活/二次探活失败时，调用 `lsp_setup.py steps` 生成结构化 `pendingActions`：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/lsp_setup.py" steps --language "{lspLanguage}" --probe-status failed --binary-installed {binaryInstalled}
```

> 输出 JSON 含 `lspStatus`、`needsRestart`、`pendingActions`（含 `setupSteps` 分步指引）。
>
> **`lsp_setup.py` 完整子命令列表（仅以下 3 个，无其他子命令）**：
> - `detect` — 语言检测 + LSP 二进制检测
> - `steps` — 根据探活结果生成 pendingActions
> - `format` — 格式化为可读文本（调试用）
>
> **禁止使用 `probe` 等不存在的子命令**。LSP 探活通过 IDE 的 LSP 工具（hover）执行，不通过此脚本。

记录 `lspStatus`、`needsRestart`、`pendingActions`。

---

## 初始化阶段: 环境就绪确认

> 仅 LSP 插件安装（`codebuddy plugin install`）需要重启 CodeBuddy（关闭窗口后重新打开项目）。其他组件均不需要重启。

### 情况 1：`pendingActions` 为空（环境就绪）

```
**环境检查完成，所有依赖已就绪。**
  扫描模式：**{scanMode == "fast" ? "极速扫描" : (scanMode == "light" ? "快速扫描" : "深度扫描")}**（预计耗时：**{timeEstimate}**）
  {scanMode == "deep" ? "LSP：**" + (lspStatus == "available" ? "可用（支持跨文件语义追踪）" : (lspStatus == "unsupported" ? (lspLanguage == "Kotlin" ? "Kotlin 无可用 LSP（已降级为 Grep+AST，tree-sitter 提供 AST 精度）" : "该语言不支持 LSP（已降级为 Grep+Read）") : "不可用（已降级为 Grep+Read）")) + "**" : ""}
  {scanMode == "deep" ? "AST 解析器：**" + (parserType == "tree-sitter" ? "tree-sitter（精确模式）" : "正则 fallback（基础模式）") + "**" : ""}
  正在开始扫描...
```

### 情况 2：`pendingActions` 不为空（环境未就绪 → 自动降级继续）

> **统一行为**：无论是否传入 `--auto`，环境检查发现未就绪项时**一律自动降级继续扫描，不再弹出 AskUserQuestion 询问用户**。设置 `lspStatus = "unavailable"`，全局回退 Grep+Read，流水线继续。

直接输出降级提示与延后安装指引（不阻塞）：

```
**检测到 {len(pendingActions)} 个环境依赖未就绪，已自动降级继续扫描。**

降级影响：
{foreach action in pendingActions}
- [{action.type}] 不可用：{action.degradeImpact}
{/foreach}

如需启用完整能力（可在本次扫描结束后手动配置，本次扫描不会阻塞）：

{foreach action in pendingActions}
**{action.description}**
{action.binary ? "  所需二进制：**" + action.binary + "**" : ""}
{action.installCommand ? "  二进制安装命令：`" + action.installCommand + "`" : ""}
{action.pluginInstallCommand ? "  插件安装命令：`" + action.pluginInstallCommand + "`" : ""}
{foreach step in action.setupSteps}
  {index}. {step}
{/foreach}

{/foreach}

{needsRestart ? "以上安装完成后需要重启 CodeBuddy 才能生效：关闭当前 CodeBuddy 窗口，然后重新打开项目即可。" : ""}

若以上步骤仍无法解决 LSP 问题，可能是 CodeBuddy 官方插件市场BUG，请尝试：
1. 删除插件缓存目录（macOS/Linux: ~/.codebuddy/plugins，Windows: %USERPROFILE%\.codebuddy\plugins）
2. 关闭并重新打开 CodeBuddy，等待插件自动重新拉取
3. 重新执行扫描命令

正在以降级模式开始扫描...
```

执行后：`lspStatus = "unavailable"`，全局回退 Grep+Read，流水线继续。

---

## LSP 降级规则

> **权威来源**：LSP 降级与错误处理规则以本节为准。其他文件（`error-recovery.md`、`agent-rules.md`）引用本节，不重复定义。
> 适用于所有使用 LSP 的 agent（vuln-scan、logic-scan、red-team、indexer 等）。

**完全不可用（unavailable）**：所有 agent 回退 Grep+Read，`traceMethod: "Grep+Read"`，整体置信度降低。

**部分可用（partial）**：对可用文件类型正常使用 LSP，不可用类型回退 Grep+Read。

### 扫描阶段 LSP 错误处理

| 错误信息 | 处理 |
|---------|------|
| `"No LSP server configured"` | 该文件回退 Grep+Read |
| `"failed to start"` | 重试 1 次，仍失败回退 |
| `"timed out"` | sleep 5 后重试，仍失败回退 |
| `"request failed"` | 换操作重试，仍失败回退 |
| 返回空结果（无错误） | 不是错误，继续使用 LSP |

**关键**：扫描过程中单次 LSP 错误应逐文件回退，不全局降级。
