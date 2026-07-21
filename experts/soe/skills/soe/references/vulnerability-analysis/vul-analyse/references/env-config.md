# 环境配置

> **v1.1 起开箱即用**：Skill 仓库自带 `providers.yaml` 默认配置，首次运行 `plan_gate.py --init` 会自动复制到用户目录。
> 默认运行模式为 `with-intel`（步骤 3 通过 `default_intel.py` 查询 NVD + EPSS，无需任何 token）。
> **仅当你需要对接内部知识库或自建威胁情报源时，才需要编辑 `providers.yaml` 并配置 `.env`。**

## 文件清单

| 文件 | 路径 | 用途 | 是否进版本库 |
|---|---|---|:---:|
| `providers.yaml`（默认） | `{SKILL_DIR}/providers.yaml` | 仓库自带默认配置，作为首次落盘源 | ✅ |
| `providers.yaml`（用户） | `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/providers.yaml`（兜底 `~/ninetail/tmp/vul-analyse/providers.yaml`） | 用户实际运行时配置，首次 `--init` 自动从默认配置复制 | ❌（不在仓库下） |
| `providers.yaml.example` | `{SKILL_DIR}/providers.yaml.example` | 完整字段样例（已废弃，保留兼容） | ✅ |
| `.env.example` | `{SKILL_DIR}/.env.example` | 环境变量样例 | ✅ |
| `.env` | `{SKILL_DIR}/.env` 或用户自定义 | 实际密钥（自建 Provider 时） | ❌ |

## 开箱即用（推荐，绝大多数场景）

**不需要任何配置**。直接运行：

```bash
python3 scripts/plan_gate.py --plan PLAN.md --init --input-report report.zip
# 输出：✅ 已从内置默认配置创建用户配置: $CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/providers.yaml
#       （未设置 CODEBUDDY_PLUGIN_DATA 时兜底为 ~/ninetail/tmp/vul-analyse/providers.yaml）
#       运行模式: with-intel
#       intel_provider 实际后端: default_intel.py（NVD + EPSS 兜底）
```

后续步骤 3 通过 `default_intel.py` 查询 NVD + EPSS，NVD_API_KEY 已在脚本中硬编码。

## 高级配置（仅当需要自建 Provider 时）

### 启用内部知识库（步骤 2）

```bash
# 1. 编辑用户配置（首次 init 后已自动创建）
vim $CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/providers.yaml
# 或 vim ~/ninetail/tmp/vul-analyse/providers.yaml

# 2. 把 knowledge_provider.enabled 改为 true，填写 server_name / tool_name
#    示例：
#    knowledge_provider:
#      enabled: true
#      server_name: your_knowledge_mcp
#      tool_name: knowledgebase_search
#      fixed_args:
#        knowledge_uuid: "${KB_UUID}"

# 3. 配置环境变量（如果使用 ${VAR_NAME} 占位符）
cp .env.example $CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/.env
vim $CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/.env
set -a && source $CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/.env && set +a
# 未设置 CODEBUDDY_PLUGIN_DATA 时，路径替换为 ~/ninetail/tmp/vul-analyse/
```

### 启用自建威胁情报源（步骤 3 替换默认 NVD+EPSS）

```yaml
# providers.yaml
intel_provider:
  enabled: true       # ← 改为 true 后走用户 Provider；false / 缺失则走 default_intel.py
  server_name: your_intel_mcp
  tool_name: query_vulnerability
  fixed_args:
    api_key: "${INTEL_API_KEY}"
```

## .env 字段说明

```ini
# 知识库 Provider 鉴权
KB_UUID=replace_with_your_knowledge_base_uuid
KB_API_TOKEN=replace_with_your_knowledge_base_token

# 威胁情报 Provider 鉴权
INTEL_API_KEY=replace_with_your_intel_api_key
```

| 变量 | 用途 | 来源 |
|---|---|---|
| `KB_UUID` | 知识库唯一标识 | 知识库管理员提供 |
| `KB_API_TOKEN` | 知识库访问令牌 | 知识库管理员提供 |
| `INTEL_API_KEY` | 威胁情报 API 密钥 | NVD / Vulners / 自建情报源 |

> 💡 **NVD_API_KEY 不需要在此配置**。`default_intel.py` 已硬编码内置 key（限速 50 req/30s）。

## providers.yaml 结构

```yaml
knowledge_provider:
  enabled: false          # ← 改为 true 启用
  type: mcp
  server_name: <MCP 服务名>
  tool_name: <工具名>
  fixed_args:
    knowledge_uuid: "${KB_UUID}"      # 引用环境变量
    api_token: "${KB_API_TOKEN}"
  query_args:
    query: "{cve_id}"                 # 占位符，运行时替换
  result_mapping:
    found_when: "$.results[0]"        # JSONPath 判断是否命中
    fix_status: "$.results[0].status"
    fix_version: "$.results[0].fixed_version"

intel_provider:
  enabled: false          # false → 走 default_intel.py（NVD+EPSS）
                          # true  → 走下方用户配置的 MCP Provider
  type: mcp
  server_name: <MCP 服务名>
  tool_name: <工具名>
  fixed_args:
    api_key: "${INTEL_API_KEY}"
  query_args:
    cve_id: "{cve_id}"
  result_mapping:
    found_when: "$.vulnerabilities[0]"
    cvss_score: "$.vulnerabilities[0].cve.metrics.cvssMetricV31[0].cvssData.baseScore"
    threat_level: "$.vulnerabilities[0].cve.metrics.cvssMetricV31[0].cvssData.baseSeverity"
    references: "$.vulnerabilities[0].cve.references[*].url"

options:
  rate_limit_ms: 200      # 调用间隔
  timeout_sec: 30         # 单次超时
  min_severity: high      # 仅查 高危及以上
  report_locale: zh
```

## 字段语义

| 字段 | 用途 |
|---|---|
| `enabled` | 该 Provider 是否启用 |
| `type` | 调用协议，目前仅支持 `mcp` |
| `server_name` | MCP 服务名，对应 `use_mcp_tool(serverName=...)` |
| `tool_name` | MCP 工具名，对应 `use_mcp_tool(toolName=...)` |
| `fixed_args` | 每次调用都带的固定参数（鉴权、配置） |
| `query_args` | 含占位符的查询参数，运行时按 CVE 渲染 |
| `result_mapping` | JSONPath 表达式，从 Provider 返回结果中抽取标准字段 |
| `options.min_severity` | 仅查询达到此严重度的 CVE，可选 `all` / `high` / `medium` |

> ⚠️ **`intel_provider.enabled` 特殊语义（v1.1）**
> - `enabled: true` → 步骤 3 调用用户配置的 MCP Provider
> - `enabled: false` 或字段缺失 → 步骤 3 调用 `default_intel.py`（NVD + EPSS）
> - **步骤 3 始终运行**，区别仅在于走哪个后端。这是开箱即用的核心契约，不可破坏。

## 升级兼容

| Skill 升级时 | 行为 |
|---|---|
| 仓库内 `providers.yaml` 更新 | 不影响用户配置（用户配置存在用户目录） |
| 用户配置不存在 | 下次 `--init` 自动复制最新默认配置 |
| 用户已修改配置 | `--init` 不会覆盖（仅首次落盘） |

如需强制重置用户配置：

```bash
rm $CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/providers.yaml
# 或 rm ~/ninetail/tmp/vul-analyse/providers.yaml（未设置 CODEBUDDY_PLUGIN_DATA 时）
python3 scripts/plan_gate.py --plan PLAN.md --init --input-report xxx --force
```

## 安全约定

- **禁止硬编码密钥**：所有 token 必须通过 `${ENV_VAR}` 占位符引用 `.env`
- **`.env` 已被 `.gitignore` 排除**，防止凭据误提交
- **`providers.yaml` 默认配置不含任何敏感字段**（仅占位符），可安全入库
- **报告交付前自检**：报告中如包含内部 Jira/Confluence 链接，请脱敏后再交付外部

## 占位符渲染规则

| 占位符 | 渲染时机 | 示例 |
|---|---|---|
| `${ENV_VAR}` | `plan_gate.py` 加载 yaml 时替换 | `${KB_API_TOKEN}` → 实际 token |
| `{cve_id}` | 每次 Provider 调用时按 CVE 替换 | `{cve_id}` → `CVE-2025-8194` |

## 调用方式

详见 [mcp_guide.md](mcp_guide.md)。
