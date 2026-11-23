# ChainGuard 插件配置文档

本文列出 ChainGuard 供应链安全插件的**全部开关**。插件无独立运行时总开关，安装即挂载 `PreToolUse` / `PostToolUse`（见 `hooks/hooks.json`），所有可调项均为**环境变量**，在运行 agent / 插件的环境中注入。

> 权威定义见客户端源码 `security-guard-js/src/filters/privacy.js` 的 `loadConfigFromEnv()` / `resolveMode()`。

## 一、默认值与生效方式

- 所有开关均为环境变量。
- 未设置任何变量时，默认进入 **`strict`** 模式（`disableAutofix=true`）：**放行 + 引导**，不自动改写用户输入。
- 服务端不可达时 **fail-open 放行**（`no_server_url_fail_open` / `SOURCE_UNAVAILABLE`），不会因插件故障阻断研发。
- 插件**启用 / 停用**靠在 CodeBuddy 中安装 / 卸载，无运行时 kill 开关。

## 二、行为模式（核心开关）

### `SECURITY_GUARD_MODE`
- 取值：`smooth` | `strict` | `audit`
- 默认：不设 → `strict`
- 作用：决定安全响应策略。
  - `smooth`：自动化为安全版本后放行（`AUTO_REMEDIATE_AND_ALLOW`），对研发无感。
  - `strict` / `audit`：`disableAutofix=true`，放行但在 `hookSpecificOutput.additionalContext` 中给出修复引导，**不自动改写文件**。

### `SECURITY_GUARD_DISABLE_AUTOFIX`（遗留变量）
- 取值：`false` → 归一化为 `smooth`；其余取值或未设 → `strict`
- 作用：在 `SECURITY_GUARD_MODE` 未设置时作为历史兼容输入源。新部署建议直接使用 `SECURITY_GUARD_MODE`。

### `SECURITY_GUARD_ALLOW_MAJOR_AUTOFIX`（risk-policy 维度，**v1 只标记**）
- 取值：`true` → 开启标记；未设/其他 → 关闭
- 与 `SECURITY_GUARD_MODE` **正交**：mode 只决定交互摩擦量，本变量决定机器授权边界——`smooth=true` **不等于**允许高爆炸半径修改。
- **v1 语义（重要）**：即使设为 `true`，**跨 Major 升级仍然不会自动改写**：
  - 命中跨 Major 时，高危 → 拦截 + 引导，中低危 → 放行 + 建议；
  - 仅在 `hookSpecificOutput.cross_major_opt_in` 打 `opted_in_pending`，并写入审计日志与埋点（`cross_major_hit` / `cross_major_opt_in`）。
- 用途：先观测真实诉求量，再决定是否解锁行为。
- 判定规则见客户端 `security-guard-js/src/version.js`：版本解析不出、或首段为年份的 calver（如 `2023.10 → 2024.1`）**不判为跨 Major**（保守取向，避免把常规升级变成硬拦）。

## 三、分级敏感度阈值

| 变量 | 默认 | 作用 |
|---|---|---|
| `SECURITY_GUARD_HIGH_THRESHOLD` | `9.0` | 高于此 CVSS 视为**高危**（拦截 / 强提示） |
| `SECURITY_GUARD_MEDIUM_THRESHOLD` | `4.0` | 高于此 CVSS 视为**中危**（通知 / 放行） |

## 四、检查范围与豁免

| 变量 | 格式 | 作用 |
|---|---|---|
| `SECURITY_GUARD_PRIVATE_SCOPES` | 逗号分隔 scope | 指定私有 scope，按私有策略处理 |
| `SECURITY_GUARD_ALLOW_LIST` | 逗号分隔包名 | 白名单包，跳过拦截 |

## 五、审计 / 日志 / 调试

| 变量 | 取值 | 作用 |
|---|---|---|
| `SECURITY_GUARD_AUDIT_LOG` | 文件路径 | 审计日志落盘位置（默认 `null`，使用内置 `DEFAULT_AUDIT_LOG`） |
| `SECURITY_GUARD_DEBUG` | `1` | 向 stderr 打印 `[D2V4]` 熔断诊断（`decision` / `digest` / `shouldTrip` / `streak`） |
| `CODEBUDDY_DEBUG` / `MCP_DEBUG` | `1` | 通用调试（含隐私过滤日志） |

## 六、服务端连接（平台注入，通常不需修改）

以下变量由 CodeBuddy 平台注入，插件通过 `node dist/security-guard.cjs` 运行：

| 变量 | 作用 |
|---|---|
| `CODEBUDDY_SECURITY_SERVER_URL` | 审计服务端地址 |
| `CODEBUDDY_SECURITY_JWT_TOKEN` | 鉴权令牌 |
| `CODEBUDDY_SECURITY_CA_CERT` | 自定义 CA 证书 |
| `CODEBUDDY_SECURITY_TIMEOUT` | 请求超时（毫秒） |
| `CODEBUDDY_SECURITY_TLS_REJECT_UNAUTHORIZED` | 是否校验 TLS 证书 |
| `CODEBUDDY_SERVICE_PROXY_URL` | 代理地址 |

## 七、典型配置示例

### 默认（严格 + 引导，不自动改）
```bash
# 不设置任何变量即可
```

### 丝滑自动修（推荐体验"无感修复"）
```bash
export SECURITY_GUARD_MODE=smooth
```

### 严格模式显式声明
```bash
export SECURITY_GUARD_MODE=strict
```

### 放宽阈值 + 白名单
```bash
export SECURITY_GUARD_HIGH_THRESHOLD=9.5
export SECURITY_GUARD_MEDIUM_THRESHOLD=5.0
export SECURITY_GUARD_ALLOW_LIST=numpy,pillow
```

### 开启调试
```bash
export SECURITY_GUARD_DEBUG=1
export CODEBUDDY_DEBUG=1
```

## 八、与"研发心流"的关系

- 想测"无感自动修"的丝滑：必须 `SECURITY_GUARD_MODE=smooth`。
- 默认 `strict` 下，插件**不自动改文件**，依赖 `additionalContext` 引导 agent 自纠为安全版本；若 agent 仍落盘漏洞版本，属引导文案未被消费，需排查客户端是否读取 `additionalContext` 字段。
