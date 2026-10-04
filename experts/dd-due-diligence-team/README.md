# dd-due-diligence-team · AI尽调专家团

WorkBuddy Team 型专家，基于《WorkBuddy 专家开发规范 v2.4》构建。
由 aidd-saas 的 12 个尽调 Skill 封装：主理人统筹流程，成员分阶段协作。

## 编制（完整版：主理人 + 8 位专员）

| 角色                  | Agent                           | 依赖 Skill                                   |
| --------------------- | ------------------------------- | -------------------------------------------- |
| 主理人 · 尽调总控     | `dd-due-diligence-lead`         | `dd-full-process`、`dd-project-manager`      |
| 进件管家 · 甄齐全     | `intake-material-custodian`     | `dd-intake-manager`、`dd-intake-recognition` |
| 财务核验专员 · 秦核真 | `finance-verify-specialist`     | `dd-finance-verify`                          |
| 财务分析师 · 察盈亏   | `financial-analysis-specialist` | `dd-financial-analysis`                      |
| 企业画像专家 · 查明悉 | `enterprise-profiling-expert`   | `dd-profile-analysis`                        |
| 经营分析专家 · 鉴产销 | `business-analysis-expert`      | `dd-business-analysis`                       |
| 行业分析专家 · 杭知微 | `industry-analysis-expert`      | `dd-industry-analysis`                       |
| 风控合规专家 · 方守正 | `risk-compliance-expert`        | `dd-risk-overview`                           |
| 报告撰写专员 · 文报章 | `report-writer`                 | `dd-report`                                  |

技能地图（`ai-due-diligence-workflow-map`）随包分发，供成员定位流程节点。

## 标准七步尽调工作流（SOP）

```
S1 项目识别与创建 ── 主理人（list_projects / get_project / create_project）
S2 进件材料准备 ── 甄齐全（入库/解析/识别/标签，save_intake_summary）
S3 财务核验    ── 秦核真（P0 确认 / P1 勾稽 / submit_finance_p1）
S4 四路分析    ── 查明悉(画像) + 察盈亏(财务) + 鉴产销(经营) + 杭知微(行业)（可并行）
S5 专项报告    ── 各专项成员（save_*_report）
S6 风险总览    ── 方守正（跨维度关联 + 剩余数据，sync_cross_dimension_risks）
S7 最终报告    ── 文报章（create_report / submit_report）
```

主理人负责建立 TeamCreate、按 SOP 调度成员、汇总回传与向用户通报；所有跨成员信息流经主理人中转。非强制线性：无财务数据可跳过 S3（须记录影响），材料不足可先启动具备条件的分析。

## 外部依赖：aidd-saas 连接器（完整 `.mcp.json`）

所有数据读写经由 aidd-saas 后端 MCP。包内 `.mcp.json` 完整内容如下，
用户召唤专家团时 WorkBuddy 会弹出引导卡片引导完成 OAuth 连接：

```json
{
  "mcpServers": {
    "aidd-saas": {
      "type": "http",
      "url": "https://aidd-saas.txfc.cloud/mcp",
      "x-workbuddy": {
        "displayName": { "zh": "AI 尽调助手", "en": "AI Due Diligence" },
        "description": {
          "zh": "连接后可访问尽调项目与进件材料，发起并推进财务核验（P0 标准化/P1 三表勾稽），执行财务、企业画像、经营、行业四路分析，汇总风险清单，生成与提交尽调报告，并在右侧面板打开各业务页面。",
          "en": "Access due diligence projects and intake materials, run finance verification (P0 standardization / P1 reconciliation), perform finance / profiling / business / industry analyses, consolidate risk inventories, generate and submit due diligence reports, and open business pages in the side panel."
        },
        "icon": "./avatars/aidd-saas.svg",
        "auth": { "type": "oauth" }
      }
    }
  }
}
```

字段说明：

| 字段                      | 值                                                                                                                                                  | 说明                                                               |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `type`                    | `http`                                                                                                                                              | 远程 MCP（Streamable HTTP）传输                                    |
| `url`                     | `https://aidd-saas.txfc.cloud/mcp`                                                                                                                  | aidd-saas 后端 MCP 端点（当前指向 dev 环境；上架前按需切生产域名） |
| `x-workbuddy.displayName` | AI 尽调助手                                                                                                                                         | 引导卡片标题（双语）                                               |
| `x-workbuddy.description` | 连接后可访问尽调项目与进件材料，发起并推进财务核验（P0/P1），执行财务、画像、经营、行业四路分析，汇总风险清单，生成与提交尽调报告，并打开各业务页面 | 引导卡片描述（双语），覆盖 S1-S7 全流程能力                        |
| `x-workbuddy.icon`        | `./avatars/aidd-saas.svg`                                                                                                                           | 卡片图标（盾牌，相对插件根目录）                                   |
| `x-workbuddy.auth.type`   | `oauth`                                                                                                                                             | 走 aidd-saas 的 MCP OAuth 授权（jointAuth 同源）                   |

> 注意：`x-workbuddy` 为 WorkBuddy 私有元信息，用户完成连接后会被剥离，不污染本地连接器配置；包内严禁硬编码任何 Token。

## 可选增强连接器：企查查 / 天眼查（企业事实查询）

企业公开事实（工商底档、股权结构、实控人/受益人、董监高、对外投资、司法风险、知识产权、招投标、专利商标等）的查询，优先使用两个权威企业数据连接器，**未连接时回退到 aidd-saas**：

| 连接器                  | 覆盖数据                                                                     | 用途           |
| ----------------------- | ---------------------------------------------------------------------------- | -------------- |
| `qcc-company`（企查查） | 工商注册、股权结构、实控人/受益人、董监高、对外投资、财务数据、发票信息等    | 企业核验主源   |
| `tyc-mcp`（天眼查）     | 企业画像、股权集团、人员、司法风险、知识产权、招投标、专利商标等 160+ 项数据 | 企业画像补充源 |

### 优先级与回退

查询企业公开事实时按以下顺序，前者不可用才回退后者：

```
qcc-company（企查查，优先）
  └─ 未连接/未授权/无结果
      → tyc-mcp（天眼查）
      └─ 未连接/未授权/无结果
          → aidd-saas: get_profile_data（已落库画像，仅当前序分析已写入时可用）
          └─ 无结果或不完整
              → 联网搜索（web_search / web_search_enhanced，需项目开启在线信源）
              → 历史项目数据
```

### 范围界定

- **走 qcc/tyc**：企业公开事实查询（工商/股权/实控人/董监高/对外投资/司法/知识产权/招投标/专利商标等）
- **仍走 aidd-saas**：项目管理、进件材料、已落库画像分析结论、报告生成等业务数据（与 qcc/tyc 无关）

### 连接器缺失提示（非强制）

当 aidd-saas 无企业信息查询结果或结果不完整，且 qcc-company 和 tyc-mcp 均未连接时，**提示用户连接这两个连接器以增强企业事实查询能力**（非强制，不阻塞流程）：

> 当前未连接企查查/天眼查企业数据连接器，企业公开事实（工商/股权/司法/知识产权等）覆盖度可能受限。建议在 WorkBuddy 连接器面板连接 `qcc-company` 和 `tyc-mcp` 以获取权威企业数据。是否继续基于现有数据完成分析？

### 为何不写入 `.mcp.json`

`.mcp.json` 声明的是专家团**强依赖**（用户召唤专家团时 WorkBuddy 引导完成 OAuth 连接）。qcc/tyc 是**可选增强**，写入会让用户必须连接才能使用专家团，违背"非强制"要求。两个连接器由用户在 WorkBuddy 连接器面板自行连接，专家团运行时检测到已连接则优先调用，未连接则按上述回退链处理。

## 打开嵌入页面（embed_code 登录码）

主理人与各成员通过 `present_files` 向用户展示 `/embed/` 业务页面（进件中心/财务核验/各分析页/报告页）。
页面需要登录态，打开前必须：`create_embed_code` 生成一次性登录码（约 60 秒有效）→ 拼接 `?embed_code=<code>` 到 URL → `present_files` 展示；过期重换，禁止让用户自行登录业务系统。

## ⚠️ 待验证项

1. **OAuth 链路**：专家市场的 `auth.type: oauth` 是否走通 aidd-saas 的 MCP 授权（jointAuth 基础）
2. **present_files**：专家会话内 embed 页面打开是否正常（`create_embed_code` → `?embed_code=`）
3. **包体积**：当前 ~4.8MB（含 10 张 512×512 头像 + 12 个 skill）；规范未写专家包上限，提交前需实测审核校验
4. **头像**：dark blue with gold accent 插画风格，符合 08-FinanceInvestment 分类背景色要求

## 打包与提交

```bash
cd experts && zip -r dd-due-diligence-team.zip dd-due-diligence-team/ -x '*.DS_Store' -x '*__pycache__*' -x '*.pyc'
```

提交前按规范 10.2 自检清单核对（一致性约束见下）。

## 一致性约束备忘

- `plugin.json.agentName` = `settings.json.agent` = 主理人 MD 文件名（不含 .md）
- `teamInfo.memberAgents[]` = `members[].id`（member）= 成员 MD 文件名
- Agent MD frontmatter **不得包含 tools 字段**（工具由系统统一分配）
- 主理人文件名已带团队前缀 `dd-`（规范禁止通用 `team-lead.md`）
- `displayName.zh` = `profession.zh`（Team 必填约束）
- `.mcp.json` 为必须文件（依赖 aidd-saas 连接器）；icon 相对路径基于插件根目录解析
- 包内 skill 与仓库 `skills/` 目录为两套维护线，改 skill 需双写同步
