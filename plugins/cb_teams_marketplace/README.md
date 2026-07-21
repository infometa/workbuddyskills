# CB Teams Marketplace

CodeBuddy Teams Marketplace - 团队协作、文档处理与开发工具插件集合

## 📦 插件列表

| 插件名 | 版本 | 描述 | 分类 |
|--------|------|------|------|
| **internal-comms** | 1.0.0 | 内部沟通文档编写工具（3P更新、通讯、FAQ等） | productivity |
| **executing-marketing-campaigns** | 1.0.0 | 营销活动策划与执行（内容策略、社媒、邮件营销） | productivity |
| **document-skills** | 1.0.0 | 文档处理套件（Excel、Word、PPT、PDF） | productivity |
| **general-skills** | 1.0.0 | 通用技能集合（文档转换、UI/UX设计、前端开发） | utility |
| **data-analysis** | 1.0.0 | 数据分析插件（Excel表格创建、编辑、分析） | productivity |
| **modern-webapp** | 1.0.0 | 现代Web应用开发（React、TypeScript、Vite、Tailwind） | development |
| **ppt-implement** | 1.0.10 | 一键生成PPT（10种演示风格、丰富模板库） | productivity |
| **deep-research** | 1.0.0 | 深度研究插件（网络调研、信息综合、微信文章检索） | research |
| **data** | 1.0.0 | 数据分析插件（SQL查询、数据探索、可视化、仪表板） | productivity |

## 🚀 快速开始

### 方式一：团队配置自动安装（推荐） 

在项目的 `.codebuddy/settings.json` 中添加：

```json
{
  "extraKnownMarketplaces": {
    "cb-teams": {
      "source": {
        "source": "github",
        "repo": "codebuddy/cbteamsmarketplace"
      }
    }
  },
  "enabledPlugins": {
    "internal-comms@cb-teams": true,
    "document-skills@cb-teams": true,
    "ppt-implement@cb-teams": true
  }
}
```

团队成员启动 CodeBuddy 时会自动安装这些插件。

### 方式二：交互式安装

```bash
# 1. 添加市场
/plugin marketplace add codebuddy/cbteamsmarketplace

# 2. 浏览并安装插件
/plugin

# 或直接安装
/plugin install internal-comms@cb-teams
```

### 方式三：命令行安装

```bash
# 添加市场
codebuddy plugin marketplace add https://cnb.cool/codebuddy/cbteamsmarketplace

# 安装插件
codebuddy plugin install internal-comms@cb-teams
```

## 📖 插件详情

### 🗣️ internal-comms

内部沟通文档编写工具，支持多种企业内部沟通格式。

**包含功能：**
- 3P 更新 (Progress, Plans, Problems)
- 公司通讯
- FAQ 回复
- 状态报告
- 领导汇报
- 事故报告

**使用示例：**
```
帮我写一份本周的 3P 更新，包括完成了用户认证模块、
下周计划开始支付集成、遇到第三方 API 延迟问题
```

---

### 📢 executing-marketing-campaigns

营销活动策划与执行工具，包含完整的营销工作流。

**包含功能：**
- 活动策划框架
- 内容创作指南
- 社交媒体策略
- 邮件营销模板
- 数据分析与 KPI
- 品牌指南

**使用示例：**
```
帮我策划一个产品发布的营销活动，目标是提高品牌知名度，
预算 5 万，周期 2 周，主要渠道是微信和小红书
```

---

### 📄 document-skills

文档处理套件，支持主流办公文档格式的创建、编辑和分析。

**包含技能：**
| 技能 | 功能 |
|------|------|
| **xlsx** | Excel 电子表格创建、编辑、公式、数据分析、可视化 |
| **docx** | Word 文档创建、编辑、格式化、追踪修改、批注 |
| **pptx** | PowerPoint 演示文稿创建和编辑 |
| **pdf** | PDF 文档处理、表单填写、文本提取、表格提取 |

**使用示例：**
```
读取 data.xlsx 并生成一份销售报告的 PowerPoint
```

---

### 🛠️ general-skills

通用技能集合，包含文档转换、设计和开发辅助功能。

**包含技能：**
- **markitdown** - 文档格式转换（PDF、Word、Excel等转Markdown）
- **find-skills** - 技能发现工具
- **ui-ux-pro-max** - UI/UX 设计专家
- **frontend-design** - 前端设计工具

**使用示例：**
```
将这个 PDF 转换为 Markdown 格式
```

---

### 📊 data-analysis

数据分析插件，专注于 Excel 表格的创建、编辑和数据分析。

**功能特性：**
- Excel 电子表格创建和编辑
- 公式和格式化支持
- 数据分析和可视化
- 图表生成

**使用示例：**
```
分析这份销售数据，生成月度趋势图表
```

---

### 💻 modern-webapp

现代 Web 应用开发插件，集成了主流前端技术栈。

**技术栈：**
- React + TypeScript
- Vite（构建工具）
- Tailwind CSS（样式）
- shadcn/ui（组件库）
- 浏览器测试工具

**包含技能：**
- **modern-web-app** - 项目初始化和开发
- **ui-ux-pro-max** - UI/UX 设计系统
- **lucide-icons** - 图标管理
- **agent-browser** - 浏览器测试

**使用示例：**
```
创建一个用户管理后台，包含登录、用户列表和编辑功能
```

---

### 📊 ppt-implement

一键生成 PPT，支持 10 种演示风格和丰富的模板库。

**演示风格：**
- 极简（minimalist）
- 中国风（chinese）
- 商务（business）
- 几何（geometric）
- 文艺（literary）
- 黑金（black-gold）
- 卡通（cartoon）
- 科技（tech）
- 扁平（flat）
- 手绘（hand-drawn）

**包含组件：**
- Agent: geniekit-ppt-creator
- Skill: ppt-implement
- Hooks: 自动文件复制

**使用示例：**
```
创建一个产品介绍PPT，使用科技风格，包含封面、目录、
3个内容页和结束页
```

---

### 🔍 deep-research

深度研究插件，支持全面的网络调研和信息综合。

**功能特性：**
- 多源网络调研
- 信息综合分析
- 微信公众号文章检索（高质量中文内容）
- 结构化报告生成

**包含组件：**
- Agent: research-subagent
- Skill: wechat-article-search

**使用示例：**
```
调研一下AI代码助手的市场现状和主要竞争对手
```

---

### 📊 data

数据分析插件，支持 SQL 查询、数据探索、可视化和仪表板构建。

**包含命令：**
- `/analyze` - 回答数据问题，从快速查询到完整分析
- `/explore-data` - 分析和探索数据集，了解其形状、质量和模式
- `/write-query` - 为您的 SQL 方言编写优化的查询和最佳实践
- `/create-viz` - 使用 Python 创建出版质量的可视化
- `/build-dashboard` - 构建带过滤器和图表的交互式 HTML 仪表板
- `/validate` - 在分享前进行 QA 分析——方法论、准确性和偏差检查

**包含技能：**
- **sql-queries** - SQL 最佳实践、常见模式和性能优化
- **data-exploration** - 数据分析、质量评估和模式发现
- **data-visualization** - 图表选择、Python 可视化代码模式和设计原则
- **statistical-analysis** - 描述性统计、趋势分析、异常值检测和假设检验
- **data-validation** - 交付前 QA、健全性检查和文档标准
- **interactive-dashboard-builder** - HTML/JS 仪表板构建，使用 Chart.js、过滤器和样式

**使用示例：**
```
分析这份销售数据，生成月度趋势图表和关键洞察
```

## 📂 目录结构

```
cb_teams_marketplace/
├── .codebuddy-plugin/
│   └── marketplace.json           # 市场配置文件
├── plugins/
│   ├── internal-comms/            # 内部沟通插件
│   ├── executing-marketing-campaigns/  # 营销活动插件
│   ├── document-skills/           # 文档处理套件
│   ├── general-skills/            # 通用技能集合
│   ├── data-analysis/             # 数据分析插件
│   ├── modern-webapp/             # 现代Web应用开发
│   ├── ppt-implement/             # PPT生成插件
│   ├── deep-research/             # 深度研究插件
│   └── data/                      # 数据分析插件（SQL、可视化、仪表板）
├── CODEBUDDY.md                   # 项目记忆文件（已忽略）
├── plugins.md                     # CodeBuddy插件系统文档（已忽略）
├── plugin-marketplaces.md         # 插件市场文档（已忽略）
├── plugins-reference.md           # 插件参考文档（已忽略）
└── README.md                      # 本文件
```

## ✅ 规范合规

所有插件已通过 CodeBuddy 官方规范检查：

- ✅ 符合标准目录结构（`.codebuddy-plugin/plugin.json`）
- ✅ 包含必需字段（name、description、version、author）
- ✅ 移除了所有第三方作者信息（Anthropic、Claude等）
- ✅ Marketplace 配置符合官方标准

## 🤝 贡献指南

要添加新插件到这个市场：

### 1. 创建插件

```bash
# 创建插件目录
mkdir -p plugins/my-plugin/.codebuddy-plugin
cd plugins/my-plugin

# 创建 plugin.json
cat > .codebuddy-plugin/plugin.json << 'EOF'
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "插件描述",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "license": "MIT"
}
EOF
```

### 2. 添加组件

根据需要创建以下目录：
- `commands/` - 斜杠命令
- `agents/` - AI 代理
- `skills/` - 技能模板
- `hooks/` - 事件钩子

### 3. 更新市场配置

在 `.codebuddy-plugin/marketplace.json` 的 `plugins` 数组中添加：

```json
{
  "name": "my-plugin",
  "description": "插件描述",
  "source": "./plugins/my-plugin",
  "version": "1.0.0",
  "category": "productivity",
  "author": {
    "name": "Your Name"
  },
  "license": "MIT"
}
```

### 4. 更新文档

更新本 README.md 的插件列表和详情部分。

### 5. 验证插件

```bash
# 验证插件配置
codebuddy plugin validate ./plugins/my-plugin

# 验证市场配置
codebuddy plugin validate .
```

## 📚 参考文档

- [CodeBuddy 插件系统](./plugins.md)
- [插件市场](./plugin-marketplaces.md)
- [插件参考文档](./plugins-reference.md)

## 📝 版本历史

- **v1.0.1** (2026-02-06)
  - ✅ 新增 data 插件（数据分析、SQL 查询、可视化）
  - ✅ 插件总数：9 个
  
- **v1.0.0** (2026-02-05)
  - ✅ 通过 CodeBuddy 官方规范检查
  - ✅ 移除所有第三方作者信息
  - ✅ 新增 8 个规范化插件
  - ✅ 完善文档体系

## 👥 维护者

- Laurent Zhou (laurentzhou@tencent.com)

---

*通过插件让 CodeBuddy 更强大 🚀*
