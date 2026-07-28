# 新股专家 V3（严格符合 WorkBuddy 专家开发规范 v2.3）

> 版本：3.0.0 ｜ 面向：WorkBuddy 专家市场提交
> 相较 V2 的核心变化：**完全按官方专家开发规范 v2.3 重写目录、plugin.json、Agent MD frontmatter、SKILL.md frontmatter**

## 相较 V2 的规范性修正

| 项 | V2（错） | V3（对，符合规范） |
|---|---|---|
| 插件配置目录 | `.workbuddy-plugin/plugin.json` | **`.codebuddy-plugin/plugin.json`** |
| Agent MD frontmatter | 加了 `expertType` 等混合字段 | 严格只用 `name / description / displayName / profession / maxTurns / skills` |
| plugin.json displayDescription.zh | 未卡长度 | 严格 40-50 字 |
| plugin.json tags | 3 个 ✅ | 3 个 ✅ |
| plugin.json quickPrompts | 3 个 ✅ | 3 个 ✅ |
| defaultInitPrompt | 与 quickPrompts[0] 不一致 | 严格 = quickPrompts[0] |
| SKILL.md frontmatter | 加了 `agent_created` 等私字段 | 只用规范定义的 `name / description` |
| Skill 命名 | new-share-workflow / ipo-data-cross-check | ipo-workflow / ipo-cross-check（更简洁） |
| Agent 与 Skill 归属 | 分散 | 4 个 skill 由 plugin.json 显式声明并加载 |

## 目录结构（严格按规范 2.1）

```
new-share-expert-v3/
├── .codebuddy-plugin/
│   └── plugin.json                    # ★ 配置文件（必须）
├── avatars/
│   └── expert.png                     # ★ 头像（必须）
├── agents/
│   └── new-share-expert.md            # ★ Agent 定义（必须）
├── skills/                            # 技能目录（可选，本专家用了 4 个）
│   ├── ipo-compliance-gate/           # 合规门禁
│   │   └── SKILL.md
│   ├── ipo-workflow/                  # 7 大场景主流程
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── board-rules.md         # 4 板块交易规则速查
│   │       ├── data-source-priority.md
│   │       └── factual-matrix-template.md
│   ├── ipo-cross-check/               # 多源交叉验证
│   │   ├── SKILL.md
│   │   └── scripts/cross_check.py
│   └── ipo-kline-chart/               # K 线/分时绘制
│       ├── SKILL.md
│       └── scripts/kline.py
└── README.md
```

## 一致性约束自检（对齐规范 10.1）

- ✅ plugin.json agentName = "new-share-expert" = agents/new-share-expert.md 的 name = 文件名
- ✅ plugin.json avatar = "avatars/expert.png"，文件存在
- ✅ plugin.json skills[] 每个路径下都有 SKILL.md
- ✅ Agent MD frontmatter 无 tools 字段
- ✅ agents/、skills/ 都在根目录，不在 .codebuddy-plugin/ 里
- ✅ 未包含 hooks/、commands/、.lsp.json

## plugin.json 自检（对齐规范 10.2）

- ✅ name：`new-share-expert`（小写字母 + 连字符）
- ✅ version：`3.0.0`（语义化）
- ✅ description：英文简短
- ✅ author：含 name + email
- ✅ agents：`["./agents/new-share-expert.md"]`
- ✅ expertType：`"agent"`
- ✅ agentName：`"new-share-expert"`
- ✅ displayName：中英文全填
- ✅ profession：中英文全填
- ✅ displayDescription：中英文全填，中文 50 字
- ✅ avatar：路径存在
- ✅ categoryId：`08-FinanceInvestment`
- ✅ defaultInitPrompt：中英文全填，且 = quickPrompts[0]
- ✅ plugin：与 name 一致
- ✅ tags：固定 3 个，全中英文
- ✅ quickPrompts：固定 3 个，全中英文

## 五大功能承接（V2 传承）

1. **数据来源多源比对**：`ipo-cross-check` 强制交叉，差异同呈两边
2. **K 线精准绘制**：`ipo-kline-chart` 覆盖日/周/月 K + 1 分钟分时 + 发行价水位 + 临停阈值
3. **能力范围明确**：仅 A 股，港美股拒答
4. **交易规则准确**：主板 2023-04-10 后前 5 日不设、北交所仅首日不设、T+1 转 ±30%
5. **合规门禁**：`ipo-compliance-gate` 每会话首次深度操作强制确认

## 安装

```bash
# 提交给 WorkBuddy 官方审核
zip -r new-share-expert-v3.zip new-share-expert-v3 -x "*.DS_Store" "*__pycache__*"

# 本地开发验证：直接复制到插件目录（推荐用 .codebuddy-plugin 作为主目录）
rm -rf ~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-expert
cp -r new-share-expert-v3 ~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-expert
```

## 数据源依赖

依赖 `finance-data` 插件，提供 `westock-data` + `neodata-financial-search` 两个 skill。本机路径：
```
~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/plugins/finance-data/skills/{westock-data,neodata-financial-search}
```

若 finance-data 未安装，`ipo-cross-check` / `ipo-kline-chart` 脚本会失败并返回明确错误。

## Python 环境

已验证使用 `~/.workbuddy/binaries/python/envs/default/bin/python`（已含 matplotlib + pandas + requests + python-docx）。
