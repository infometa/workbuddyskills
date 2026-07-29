# 新股专家 V5（严格符合 WorkBuddy 专家开发规范 v2.3 的 Skill 结构）

> 版本：5.0.0 ｜ 面向：WorkBuddy 专家市场提交
> 相较 V4 的核心变化：**按审查报告修复 1 个 BLOCKER + 5 个 SUGGESTION**
> - B01 输出末尾免责声明统一为四要素模板（AI 生成 + 基于公开信息 + 不构成投资建议 + 不构成个股推荐）
> - S01 README `rm -rf` 加危险命令警示；S02 kline.py 补 Windows 中文字体候选
> - S03 补 finance-data 安装来源 + cross_check.py 补 Windows managed venv 路径
> - S04 修正 references 中 `ipo-cross-check` skill 名称笔误；S05 K 线图统一输出 `charts/` 目录

## V3 → V4 的 Skill 规范性修正

| 项 | V3（不合规） | V4（符合规范 7.1-7.6） |
|---|---|---|
| SKILL.md 内容定位 | ipo-workflow 塞了 200 行场景流程，像 Agent 系统提示词 | 严格按规范「功能说明/调用方式/命令/输出格式」模板，场景流程迁回 Agent MD |
| description 格式 | 单行紧凑 | YAML `\|` 块标量多行，含「用途 + 触发词」 |
| 脚本调用路径 | `<此 skill 目录>/scripts/...` 占位符 | 规范相对路径 `cd <skill-dir> && python3 scripts/xxx.py` |
| ipo-workflow 定位 | 当作"主工作流"塞业务逻辑 | 重新定位为「知识库索引型」skill，只做 references 索引 |
| ipo-compliance-gate | 冗长重复铁律 | 精简为「模板型」skill，只含工作流 + 风险提示模板 |
| Agent MD 与 Skill 职责 | 业务逻辑散落 SKILL.md | 严格分离：Agent MD = 系统提示词（角色/能力/工作流/输出规范/铁律），Skill = 工具封装 |

## 目录结构（严格按规范 2.1 + 7.1）

```
new-share-expert-v5/
├── .codebuddy-plugin/
│   └── plugin.json                    # ★ 配置文件（规范 3.1）
├── avatars/
│   └── expert.png                     # ★ 头像（规范 8）
├── agents/
│   └── new-share-expert.md            # ★ Agent 定义（规范 4，系统提示词）
├── skills/                            # 技能目录（规范 7）
│   ├── ipo-compliance-gate/           # 模板型 skill（规范 7.2，仅 SKILL.md）
│   │   └── SKILL.md
│   ├── ipo-workflow/                  # 知识库型 skill（规范 7.3 references/）
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── board-rules.md
│   │       ├── data-source-priority.md
│   │       └── factual-matrix-template.md
│   ├── ipo-cross-check/               # 脚本型 skill（规范 7.3 scripts/）
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── cross_check.py
│   └── ipo-kline-chart/               # 脚本型 skill（规范 7.3 scripts/）
│       ├── SKILL.md
│       └── scripts/
│           └── kline.py
└── README.md
```

## 三种 Skill 类型的规范对照

按规范 7.1-7.6，Skill 可含 `SKILL.md` + `references/` + `scripts/` + `templates/` 四类资源。本专家用了三种类型：

| Skill | 类型 | 资源 | 规范依据 |
|---|---|---|---|
| ipo-compliance-gate | 模板型 | 仅 SKILL.md | 7.2（SKILL.md 格式） |
| ipo-workflow | 知识库型 | SKILL.md + references/ | 7.3 references/ |
| ipo-cross-check | 脚本型 | SKILL.md + scripts/ | 7.3 scripts/ |
| ipo-kline-chart | 脚本型 | SKILL.md + scripts/ | 7.3 scripts/ |

## SKILL.md 格式对照（规范 7.2）

每个 SKILL.md 严格遵循「YAML frontmatter + Markdown 正文」，frontmatter 只用规范定义的字段：

```yaml
---
name: <skill-name>           # 规范：技能标识，省略则用目录名
description: |                # 规范：推荐，AI 据此判断何时触发，写清用途和触发词
  <用途说明>
  触发词：<关键词列表>
---
```

正文按 skill 类型采用对应模板：
- **脚本型**：功能说明 → 调用方式 → 支持的命令 → 参数说明 → 输出格式
- **知识库型**：功能说明 → 参考资料（@references/xxx.md）→ 工作流 → 输出格式
- **模板型**：功能说明 → 工作流 → 标准模板文本 → 边界处理

## 一致性约束自检（对齐规范 10.1、10.2）

- ✅ plugin.json agentName = "new-share-expert" = agents/new-share-expert.md 的 name = 文件名
- ✅ plugin.json avatar = "avatars/expert.png"，文件存在
- ✅ plugin.json skills[] 每个路径下都有 SKILL.md
- ✅ Agent MD frontmatter 无 tools 字段（规范 4.2）
- ✅ agents/、skills/ 都在根目录，不在 .codebuddy-plugin/ 里（规范 2.3）
- ✅ 未包含 hooks/、commands/、.lsp.json（规范 2.3）
- ✅ 每个 SKILL.md frontmatter 只有 name + description（规范 7.2）
- ✅ 脚本型 skill 的 scripts/ 下脚本可被 `python3 scripts/xxx.py` 相对路径调用（规范 7.3）
- ✅ 知识库型 skill 的 references/ 通过 @references/xxx.md 引用（规范 7.3）

## plugin.json 关键字段（规范 3.3）

- `name`: `new-share-expert`（小写字母 + 连字符）
- `version`: `5.0.0`（语义化）
- `expertType`: `"agent"`
- `displayDescription.zh`: 50 字（规范要求 40-50 字）
- `tags`: 固定 3 个，全中英文
- `quickPrompts`: 固定 3 个，全中英文
- `defaultInitPrompt`: = quickPrompts[0]（规范要求一致）

## 五大功能承接（V2/V3 传承）

1. **数据来源多源比对**：`ipo-cross-check` 强制交叉，差异同呈两边
2. **K 线精准绘制**：`ipo-kline-chart` 覆盖日/周/月 K + 1 分钟分时 + 发行价水位 + 临停阈值
3. **能力范围明确**：仅 A 股，港美股拒答
4. **交易规则准确**：主板 2023-04-10 后前 5 日不设、北交所仅首日不设、T+1 转 ±30%
5. **合规门禁**：`ipo-compliance-gate` 每会话首次深度操作强制确认

## 安装

```bash
# 提交给 WorkBuddy 官方审核
zip -r new-share-expert-v5.zip new-share-expert-v5 -x "*.DS_Store" "*__pycache__*"

# 本地开发验证
# ⚠️ 以下 rm -rf 会删除旧版本地安装目录，路径收敛于本插件自身安装位置，仅限开发者本地验证使用；执行前请确认路径无误
rm -rf ~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-expert
cp -r new-share-expert-v5 ~/.workbuddy/plugins/marketplaces/cb_teams_marketplace/external_plugins/new-share-expert
```

## 数据源依赖

依赖 `finance-data` 或 `strategy-backtest-expert` 等插件提供的 `westock-data` + `neodata-financial-search` 两个 skill。脚本内置 glob 兜底搜索，可自动定位数据源 skill 的安装位置。

**获取方式**：请先在 WorkBuddy 专家市场（推荐市场 / 团队市场）搜索并安装 `finance-data` 插件（或 `strategy-backtest-expert`），它会把 `westock-data` 与 `neodata-financial-search` 两个 skill 安装到 `~/.workbuddy/plugins/marketplaces/.../skills/` 下，本专家脚本即可自动定位。若两者均未安装，事实矩阵/交叉校验/K 线等深度场景将因数据源缺失而无法执行。

## Python 环境

优先使用 WorkBuddy managed venv（已含 matplotlib + pandas + requests），脚本会按平台自动选择：

- macOS / Linux：`~/.workbuddy/binaries/python/envs/default/bin/python`
- Windows：`~/.workbuddy/binaries/python/envs/default/Scripts/python.exe`

若 managed venv 不存在，则回退到系统 PATH 中的 `python`（Windows）/ `python3`（macOS/Linux）。
