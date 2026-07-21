# Provider 调用指南

本 Skill 通过两个**可插拔 Provider**与外部数据源交互。Provider 是抽象接口，**不绑定任何特定厂商**，
你可以接入腾讯 Knot/XTI、NVD、Vulners、自建 Confluence/Wiki/Jira 等任意符合接口规范的服务。

---

## 1. 两类 Provider

| Provider 类别 | 用途 | 步骤 | 是否必需 |
|---|---|---|---|
| `knowledge_provider` | 查询**内部知识库**中的漏洞历史修复记录（需求单/缺陷单/修复版本/补丁链接） | 步骤 2 | 可选 |
| `intel_provider` | 查询**外部威胁情报**（CVSS、PoC、利用情况、官方修复建议） | 步骤 3 | 可选 |

两个 Provider **均可独立启用或禁用**。当全部禁用时，Skill 退化为 `extract-only` 模式：仅做格式归一化 + 统计 + 报告生成，跳过步骤 2/3。

---

## 2. 配置文件：`providers.yaml`

用户首次使用前应在 `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/providers.yaml`
（未设置 `CODEBUDDY_PLUGIN_DATA` 时兜底为 `~/ninetail/tmp/vul-analyse/providers.yaml`）
创建配置文件（v1.1 起 `plan_gate.py --init` 会自动从仓库内置默认配置复制）。
样例见仓库根目录 [`providers.yaml`](../providers.yaml)。

```yaml
# ─────────── 知识库 Provider（步骤 2 使用，可选）───────────
knowledge_provider:
  enabled: true
  type: mcp                              # mcp | http | none
  server_name: knot                      # 你 mcp 配置中的 server 别名
  tool_name: knowledgebase_search        # 该 server 真实存在的工具名
  fixed_args:
    knowledge_uuid: "${KB_UUID}"         # 占位符自动替换为环境变量
  query_args:
    query: "{cve_id} {vuln_name}"
    keyword: "{cve_id}"
  result_mapping:
    found_when: "$.results[*]"
    fix_status: "$.results[0].status"
    ticket_links: "$.results[*].url"
    fix_version: "$.results[0].fix_version"
    fix_time: "$.results[0].fix_time"

# ─────────── 威胁情报 Provider（步骤 3 使用，可选）───────────
intel_provider:
  enabled: true
  type: mcp
  server_name: xti
  tool_name: query_vulnerability
  fixed_args:
    api_key: "${INTEL_API_KEY}"
  query_args:
    cve_id: "{cve_id}"
  result_mapping:
    found_when: "$.data.cve_id"
    cvss_score: "$.data.cvss_v3_score"
    threat_level: "$.data.severity"
    has_public_exploit: "$.data.exploit_available"
    fix_advice: "$.data.solution"
    references: "$.data.references[*]"
```

> ⚠️ **占位符 `${VAR_NAME}` 会自动替换为同名环境变量**。请勿把 token / api_key 直接写进 yaml。
> 推荐在 `$CODEBUDDY_PLUGIN_DATA/soe-skill/vul-analyse/.env`（或兜底 `~/ninetail/tmp/vul-analyse/.env`）中维护密钥，或导出到 shell 环境。

---

## 3. 调用方式（统一接口）

无论后端是 MCP / HTTP / 其他，Skill 内部统一用 `use_mcp_tool` 调用，参数从 `providers.yaml` 读取：

```
use_mcp_tool(
  serverName=<knowledge_provider.server_name>,
  toolName=<knowledge_provider.tool_name>,
  arguments=<fixed_args ⊕ 渲染后的 query_args>
)
```

**严禁**调用 `mcp_get_tool_description`、`mcp_list_tools` 等"探测型"伪工具名 ——
所有工具名必须由用户在 `providers.yaml` 显式声明。

---

## 4. 查询策略

### 4.1 知识库查询（步骤 2）
- **CVE 优先**：对 `unique_cves.json.cve_list` 的每个唯一 CVE 调用一次
- **名称回退**：对 `vulns_without_cve` 中的中高危条目，用 `search_keyword` 调用
- **同一 CVE 只查一次**，结果通过 `affected_records` 索引 fan-out 给所有原始记录
- **低危可跳过**：通过 `--severity high` 控制只查中高危，节省配额

### 4.2 威胁情报查询（步骤 3）
- **仅查未命中**：仅对 `knot_results.json.not_found_cves` 中的 CVE 查询
- **不重复 fan-out**：知识库已命中的 CVE 不重复查情报源
- **关注字段**：CVSS 评分、是否有公开利用 PoC、官方修复建议、参考链接

---

## 5. 结果文件结构

### `knot_results.json`（知识库查询结果）
```json
{
  "provider": "knowledge_provider",
  "queried_count": 87,
  "hit_count": 42,
  "hit_rate": 0.48,
  "results": [
    {
      "cve_id": "CVE-2025-8194",
      "affected_records": [0, 15, 203],
      "found": true,
      "fix_status": "已修复",
      "ticket_links": ["..."],
      "fix_version": "...",
      "fix_time": "..."
    }
  ],
  "not_found_cves": ["CVE-xxx"]
}
```

### `xti_results.json`（威胁情报查询结果）
```json
{
  "provider": "intel_provider",
  "queried_count": 45,
  "hit_count": 30,
  "results": [
    {
      "cve_id": "...",
      "found": true,
      "cvss_score": "9.8",
      "threat_level": "critical",
      "has_public_exploit": true,
      "fix_advice": "...",
      "references": ["..."]
    }
  ]
}
```

---

## 5.5 默认情报工具：default_intel.py（无需任何配置即可用）

**触发条件**：
- `intel_provider.enabled = false`（用户未配置外部情报源）
- 或 `intel_provider` 块完全缺失

**调用命令**：
```bash
python3 scripts/default_intel.py query \
  --from-unique-cves "$TASK_DIR/unique_cves.json" \
  --output "$TASK_DIR/xti_results.json"
```

**集成的三个公开数据源**：

| 数据源 | URL | 维度 | 凭据 |
|---|---|---|:---:|
| **NVD** | `https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve}` | CVE → CVSS/CWE/参考链接 | ❌ 无需 |
| **EPSS** | `https://api.first.org/data/v1/epss?cve={cve}` | CVE → 利用概率/百分位 | ❌ 无需 |
| **OSV** | `https://api.osv.dev/v1/query` (POST) | package+version → 漏洞 | ❌ 无需 |

**与 `use_mcp_tool(intel_provider)` 的关系**：
- 二者**叠加**而非互斥
- 用户配置 `intel_provider.enabled=true` 时，依然可手动调用 `default_intel.py` 做交叉验证
- 字段冲突时优先使用用户配置的 `intel_provider` 结果

**内置优化**：
- `NVD_API_KEY` 已硬编码在脚本中（限速 50 req/30s），无需配置环境变量。如需更换可通过 `--nvd-api-key` 参数覆盖
- `--include-osv`：仅当 `unique_cves.json` 含 `packages` 字段时启用 OSV 查询

**输出 schema**（与原 `xti_results.json` 兼容，扩展 epss_score/epss_percentile/source 字段）：
```json
{
  "provider": "default_intel",
  "sources": ["nvd", "epss"],
  "queried_count": 45,
  "hit_count": 32,
  "hit_rate": 0.7111,
  "results": [{
    "cve_id": "CVE-2024-1234",
    "found": true,
    "source": "nvd+epss",
    "cvss_score": 9.8,
    "threat_level": "critical",
    "epss_score": 0.92,
    "epss_percentile": 0.978,
    "has_public_exploit": true,
    "fix_advice": "...",
    "references": ["..."]
  }],
  "query_errors": []
}
```

**连通性自检**：
```bash
python3 scripts/default_intel.py validate
# 输出：✅ NVD  ✅ EPSS  ✅ OSV  + 当前 NVD API Key 状态
```

---

## 6. 降级与失败处理

| 情况 | 行为 |
|---|---|
| `knowledge_provider.enabled = false` | 跳过步骤 2，`knot_results.json` 写入空骨架（`provider_disabled: true`） |
| `intel_provider.enabled = false` | **自动降级为 default_intel.py**（NVD + EPSS）；如需完全跳过请显式 `plan_gate.py --skip-step 3` |
| Provider 网络/鉴权失败 | `plan_gate.py --mark-failed N`，**禁止用本地统计冒充** |
| `default_intel.py` 三源全部失败 | `plan_gate.py --mark-failed 3`，与上同 |
| 单条 CVE 查询失败 | 该 CVE 加入 `query_errors`，整体流程继续 |

---

## 7. 注意事项

1. **频率控制**：Provider 可能限流，建议批量调用间隔 100~500ms
2. **编号规范**：CVE 必须为 `CVE-YYYY-NNNNN` 标准格式（`dedupe_cves.py` 已自动归一）
3. **不要硬编码 token**：所有密钥通过环境变量注入
4. **结果脱敏**：报告中如包含内部链接（如 Jira/Confluence URL），交付前请自行脱敏
