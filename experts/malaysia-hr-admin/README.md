# Amelia — 马来西亚人力资源与行政合规专家

> **版本**: v1.4.0 | **类型**: Agent 型专家 | **作者**: Patrick

## 一句话描述

马来西亚 HR & Admin 全链路合规顾问，基于 52 份权威法律语料 + 77 张 DuckDB 数据表，覆盖劳动法、薪酬福利、外劳准证、公司行政、招聘渠道、员工管理六大场景。

## 类型

Agent 型（单个 AI 专家），无需团队编排。

## 核心功能

### 六模工作流 (L/C/F/A/R/M)

| 模式 | 覆盖领域 | 核心语料 |
|------|---------|---------|
| **L Mode** 劳动法咨询 | 加班/年假/解雇/合同/产假/劳资纠纷 | Employment Act 1955 / IRA 1967 / 判例汇编 |
| **C Mode** 薪酬福利 | EPF/SOCSO/EIS/PCB/BIK/薪资对标 | EPF Act / SOCSO Act / 薪资指南 / PCB 指南 |
| **F Mode** 外籍劳工 | 工作准证/人头税/宿舍/PLKS | 移民法案 / Levy 2026 / Act 446 |
| **A Mode** 公司行政 | 注册/PDPA/办公室/采购/保险/差旅 | Companies Act 2016 / PDPA 2010 / MIDA CODB |
| **R Mode** 招聘渠道 | 猎头/校园/面试/背景调查 | 招聘渠道指南 / 劳动力市场情报 |
| **M Mode** 员工管理 | 考勤/绩效/PIP/纪律处分/DI | 考勤假期管理 / 绩效纪律手册 |

### 数据底座

- **Reference_Texts**: 52 份权威文献（3.8MB+），含完整法律文本 + 官方报告 + 判例
- **DuckDB 数据库**: 77 张 HR 专项表（24MB），离线 SQL 即时查询
- **定向数据源**: JTK/PERKESO/EPF/IMMI/SSM/DOSM/LHDN/Bomba 共 8 大官方源
- **容错降级**: 语料库 → API → site:搜索 → 通用搜索，逐级降级并标注可信度

### 输出特性

- **3-8 条要点铁律**: 默认回答严格限制条数，拒绝信息轰炸
- **来源占比标注**: 每次回答末尾标注 `📊 来源占比：语料库 XX% | ...`
- **互动式扩展**: 回复数字深入探索细分主题
- **多模式切换**: 支持 `详细模式` / `简洁模式` / `计算模式`
- **反幻觉防火墙**: data_verifier.py 独立验证 + 语料库强制检索

## 使用示例

### 劳动法咨询
```
马来西亚《1955年劳工法》对加班、年假和解雇有什么规定？
```

### 薪酬对标
```
帮我在吉隆坡招聘一名软件工程师，对标一下薪资和福利方案。
```

### 外劳管理
```
在马来西亚招聘外籍劳工的流程和成本是怎样的？包括人头税和工作准证。
```

### 公司行政
```
外国人怎么在马来西亚注册 Sdn Bhd？需要什么文件？
```

### 招聘预算
```
RM 50K 月预算能招几个人？流水线工人月薪多少？
```

## 目录结构

```
malaysia-hr-admin/
├── .codebuddy-plugin/
│   └── plugin.json          # 插件元信息（版本/名称/技能列表）
├── agents/
│   └── malaysia-hr-admin.md  # Agent 主 prompt（六模工作流+输出铁律）
├── skills/
│   └── malaysia-hr-admin/
│       └── SKILL.md          # 语料库索引+脚本使用说明+环境依赖
├── Reference_Texts/           # 52 份 .txt 法律/报告/判例语料（核心知识库）
├── Databases/
│   └── hr.duckdb             # 77 张 HR 专项数据表（24MB）
├── scripts/
│   ├── duckdb_query.py       # DuckDB SQL 查询引擎
│   ├── ref_text_search.py    # 语料库全文检索
│   ├── data_verifier.py      # 数据完整性验证器
│   └── pressure_test.py      # 压力测试脚本
├── avatars/
│   └── expert.png            # 专家头像（512×512, <500KB）
└── requirements.txt           # Python 依赖（duckdb>=0.9.0）
```

## 安装

### 方法一：直接复制（推荐）

将 `malaysia-hr-admin` 文件夹放到以下路径：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/malaysia-hr-admin/
```

重启 WorkBuddy 即可在专家中心看到 Amelia。

### 方法二：解压 zip 包

```bash
# 解压到插件目录
unzip malaysia-hr-admin-v1.4.0.zip -d ~/.workbuddy/plugins/marketplaces/my-experts/plugins/
```

## 运行前提与环境依赖

### Python 依赖

脚本首次运行时会**自动检测并安装** `duckdb`（通过 pip install），无需手动操作。

如果自动安装失败（网络问题/权限不足）：
```bash
pip install -r requirements.txt
```

`requirements.txt` 仅含一项依赖：`duckdb>=0.9.0`

### 路径说明

所有 Python 脚本（`scripts/` 目录下）使用**相对路径自动解析**插件根目录：

- `duckdb_query.py` → 自动定位 `Databases/hr.duckdb`
- `ref_text_search.py` → 自动定位 `Reference_Texts/` 目录
- `data_verifier.py` → 同时验证数据库和语料库完整性

路径解析逻辑：脚本通过 `Path(__file__).resolve().parent.parent` 定位插件根目录，因此**只要目录结构不变，在任何安装位置均可正常运行**。

## 打包分享

```bash
# 在 plugins 目录上级执行
zip -r malaysia-hr-admin-v1.4.0.zip malaysia-hr-admin/
```

或使用 expert-deploy skill 一键打包验证。

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.4.0 | 2026-07-06 | 统一版本号；扩展 displayDescription；填充 README；补充引导路径；语料数修正为 52 份 |
| v1.1.x | 2026-07-03 | 初版打包，通过审查上架 |
