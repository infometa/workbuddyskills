# workbuddyskills

WorkBuddy 公开市场归档：技能包 / 连接器 / 专家包 / 插件市场，便于离线学习、检索与对照写法。

> **版权声明**：内容来自 WorkBuddy / CodeBuddy 公开 CDN 与市场包，版权归原作者与腾讯相关产品所有。本仓库仅作学习归档，请勿用于未授权商业再分发。

## 说明

- 本仓库内容来自 WorkBuddy / CodeBuddy **公开市场包**（技能、连接器配置模板、专家插件等）。

## 仓库结构

```text
skills/          # 推荐技能市场技能包
connectors/      # 连接器配置（mcp.json）+ 自带 skills
experts/         # 专家插件（agents / skills / avatars）+ expert_center.json
plugins/
  codebuddy-plugins-official/
  cb_teams_marketplace/
CATALOG.md       # 完整清单（全部名称与分类）
```

## 数量一览

| 分类 | 数量 |
|------|------|
| 技能包 `skills/`（含 `SKILL.md` 的顶层包） | **295** |
| 连接器 `connectors/` | **69** |
| 专家插件 `experts/` | **371** |
| 官方插件 market | **57** |
| 团队插件 market | **30** |

### 技能包分类（概览）

- **AI / Agent 工具**：159
- **腾讯 / 微信 / 企微**：47
- **文档 / 办公 / 协作**：44
- **搜索 / 研究 / 知识**：15
- **设计 / UI / 地图**：12
- **数据 / 金融 / 股票**：6
- **内容 / 营销 / 媒体**：5
- **云 / 存储 / 部署**：4
- **开发 / 工程**：2
- **其他**：1









### 专家包分类（概览，来自 expert_center.json）

- **产品设计**：18
- **全球发展**：21
- **内容创作**：43
- **技术工程**：39
- **数据智能**：36
- **法务安全**：23
- **游戏空间**：25
- **腾讯专区**：29
- **营销增长**：33
- **行业顾问**：22
- **运营人力**：12
- **金融投资**：33
- **销售商务**：14
- **项目质量**：23











每个技能/连接器/专家的**中文用途**、**前置条件**（API Key/登录或「无」）及**可点击链接**，见 **[CATALOG.md](./CATALOG.md)**。

## 快速浏览

```bash
# 技能
ls skills | head

# 某个技能
cat skills/lark-unified/SKILL.md

# 专家（例：全域内容分发）
ls experts/content-distribution-team/agents
cat experts/content-distribution-team/.codebuddy-plugin/plugin.json

# 连接器
ls connectors | head
cat connectors/westock-mcp/mcp.json
```

## 装回 WorkBuddy（可选）

| 内容 | 拷贝到 |
|------|--------|
| 技能 | `~/.workbuddy/skills/<name>/` |
| 专家 | `~/.workbuddy/plugins/marketplaces/experts/plugins/<name>/` |
| 连接器市场 | `~/.workbuddy/connectors-marketplace/connectors/<id>/` |

连接器**启用**仍需在 App 内完成 OAuth / 扫码，本仓库只有配置模板。

## 数据来源（公开 CDN）

- Skills: `https://download.codebuddy.cn/skill-marketplace/skill-marketplace.zip`
- Connectors: `https://acc-1258344699.cos.ap-guangzhou.myqcloud.com/connectors-config-v2/connectors-config.zip`
- Experts catalog: `.../workbuddy/expert-marketplace/expert_center.json`
- Experts bundles: `.../workbuddy/expert-marketplace/bundles/<name>.tar.gz`
- Plugins: `https://download.codebuddy.cn/plugin-marketplace/*.zip`

## 许可与免责

- 第三方 skill / 专家包可能各自有 LICENSE，请在对应子目录查看。
- 归档可能与官方最新版本存在差异；以官方市场为准。
- 使用本仓库内容产生的任何后果由使用者自行承担。

## 维护

本仓库由自动化脚本每日检查 WorkBuddy 公开市场（skills / connectors / experts / plugins）并同步更新。

## 友情链接

[linux.do](https://linux.do/)
