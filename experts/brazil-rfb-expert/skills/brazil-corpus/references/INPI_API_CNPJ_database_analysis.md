# INPI API 全面分析 + CNPJ 本地数据库说明

## 一、INPI（巴西国家工业产权局）API 现状与局限性

### 1.1 当前系统架构

INPI 正在经历**系统全面重构**。目前并存两套系统：

| 系统 | 状态 | 说明 |
|------|------|------|
| **pePI 旧系统** (busca.inpi.gov.br) | 生产运行 | 传统JSP页面，无官方API |
| **Portal de Serviços 新系统** (data lake) | Beta版 | 2026年4月上线，逐步替代旧系统 |

### 1.2 API 可用性

**❌ 目前没有稳定、官方、可直接用的API**

旧系统 pePI：
- 纯JSP网页界面，仅支持**浏览器人工查询**
- 无REST API、无JSON/XML输出接口
- Infosimples 等第三方公司通过自动化技术（类RPA）提供API服务，但这是商业付费服务

新系统 Portal de Serviços（data lake）：
- 版本 1.0.2（**开发中**）将首次提供 **API + JSON/XML 导出（ST.96格式）**
- 但截至 2026年5月27日仍在开发中
- 版本 1.0.3（计划中）将完成专利、商标、工业设计的数据处理
- 版本 1.2.0（计划 Q4/2026）将提供 RPI 查询模块

### 1.3 数据滞后问题（非常关键！）

#### 旧系统 pePI

| 数据类别 | 更新频率 | 延迟情况 |
|---------|---------|---------|
| 专利 (Patentes) | 与 RPI 公告同步 | **通常滞后 1~4 周**，取决于审查流程 |
| 商标 (Marcas) | 每日/每周批量更新 | **一般滞后 1~2 周** |
| 工业设计 (DI) | 与 RPI 同步 | **滞后 1~3 周** |
| 技术合同 | 不定期 | 滞后不定 |

#### 新系统 Portal de Serviços (data lake)

| 数据类别 | 延迟说明 |
|---------|---------|
| 所有类别 | **处于beta阶段，数据整合尚未完成**。官方明确承认："可能存在不一致或临时空白" |
| 商标/专利 | 1.0.3版本才计划"完成数据处理" |
| RPI 官方公告 | 要到 **Q4/2026** 版本 1.2.0 才上线 |

### 1.4 搜索限制

- 仅支持网页搜索，**无批量查询能力**
- 搜索结果**最多返回100条**
- **无CNPJ会搜不到企业关联的知识产权**
- 新系统目前搜索算法与旧系统不同（官方承认结果可能不同）
- 移动端兼容性差

---

## 二、CNPJ 反向查询问题 — 最关键的限制！

### 2.1 INPI 搜索依赖 CNPJ 的困境

INPI 的商标/专利搜索通常需要以下条件之一：
- **申请号/注册号**（Número do Processo）
- **商标/专利名称**
- **权利人名**（Titular / Depositante）
- **CNPJ/CPF**

**问题：用户通常只知道公司名，没有CNPJ。**

INPI 的商标搜索按**商标名/分类**检索，而不是按公司名。要查某公司的全部知识产权，需要：
1. 知道该公司的 **CNPJ**
2. 在INPI中按CNPJ搜索权利人

### 2.2 解决方案：本地 CNPJ 数据库

你上传的 archive.zip 正好解决了这个问题！

---

## 三、本地 CNPJ 数据库（archive.zip）完整说明

### 3.1 数据来源与时效性

| 项目 | 值 |
|------|-----|
| 数据来源 | **巴西联邦税务局 (RFB - Receita Federal do Brasil)** 公开数据 |
| 最后更新 | **2024年9月**（距今约 9 个月） |
| 全量数据 | 约 1,916 万家公司 + 约 1.99 亿分支机构 |

### 3.2 包含的 38 个 Parquet 文件

| 目录 | 文件数 | 内容 | 总大小 |
|------|-------|------|-------|
| **empresas/** | 10 | 公司基础信息（CNPJ前8位、公司名、法律性质、注册资本） | 1,005 MB |
| **estabelecimentos/** | 10 | 分支/总部信息（完整CNPJ、地址、CNAE行业、邮箱、电话、状态） | 3,065 MB |
| **socios/** | 10 | 股东/合伙人信息（姓名、CPF/CNPJ、身份、进入日期） | 453 MB |
| **simples/** | 1 | Simples Nacional/MEI 税务制度信息 | 185 MB |
| **cnaes/** | 1 | CNAE行业分类代码表（1,359条） | <1 MB |
| **naturezas/** | 1 | 法律性质代码表（90条） | <1 MB |
| **qualificacoes/** | 1 | 股东身份代码表（68条） | <1 MB |
| **municipios/** | 1 | 巴西城市代码表（5,571条） | <1 MB |
| **motivos/** | 1 | 分支机构状态原因代码表（61条） | <1 MB |
| **paises/** | 1 | 国家代码表（255条） | <1 MB |

### 3.3 各表核心字段

**empresas（公司基础表）**
```
cnpj_8          → CNPJ前8位（与estabelecimentos.cnpj关联）
razao_social    → 公司正式名称（通过名称反向查CNPJ的关键字段！）
natureza_juridica → 法律性质编码（可关联naturezas表）
capital_social  → 注册资本（雷亚尔）
porte_empresa   → 企业规模编码
```

**estabelecimentos（分支机构表）**
```
cnpj            → CNPJ前8位（与empresas关联）
cnpj_ordem      → CNPJ第9-12位（分支编号）
cnpj_dv         → CNPJ第13-14位（校验码）
→ 完整CNPJ = cnpj + cnpj_ordem + cnpj_dv = 14位数字

matriz_filial   → 1=总部, 2=分支
nome            → 商业名称/店铺名
situacao        → 状态（2=活跃, 4=冻结, 8=暂停等）
cnae_fiscal     → 主CNAE行业代码
endereço completo → 完整地址信息
email, telefone → 联系方式
```

**socios（股东表）**
```
cnpj            → 关联CNPJ
nome_socio      → 股东姓名/公司名
cpf_cnpj_socio  → 股东CPF/CNPJ
qualificacao_socio → 股东身份（可关联qualificacoes表）
data_entrada_sociedade → 入伙日期
```

### 3.4 如何通过公司名查CNPJ

```sql
-- 通过公司名搜索（razao_social或nome字段模糊匹配）
SELECT e.cnpj + '-' + e.cnpj_ordem + '/' + e.cnpj_dv AS CNPJ_Completo,
       emp.razao_social,
       e.nome AS nome_fantasia,
       e.situacao,
       e.cnae_fiscal
FROM empresas emp
JOIN estabelecimentos e ON e.cnpj = emp.cnpj_8
WHERE emp.razao_social LIKE '%关键词%'
   OR e.nome LIKE '%关键词%'
```

---

## 四、数据时效性对比总结

| 数据来源 | 最后更新 | 更新频率 | 延迟风险 |
|---------|---------|---------|---------|
| **INPI pePI 旧系统** | 每日/每周 | 与RPI公告同步 | **1~4周** |
| **INPI Portal de Serviços** | Beta | 增量交付 | **数据整合未完成**（官方承认） |
| **RFB 本地数据库 (archive.zip)** | **2024年9月** | 约每月 | **约9个月滞后** |
| **RFB 在线查询** | 实时 | 每日 | **无延迟** |

### 关键发现

1. **INPI没有稳定API** — 计划中的API（v1.0.2）仍在开发，旧系统纯网页
2. **INPI数据存在1~4周滞后**，因为依赖RPI公告周期
3. **archive.zip的数据滞后约9个月**（2024年9月→2026年6月），对2025年后注册的公司不包含
4. **通过公司名反向查CNPJ**可以解决INPI搜索的入口问题
5. **最完整的查询方案**：本地数据库查CNPJ → INPI用CNPJ查知产 → 实时RFB网站验证最新状态

### 建议方案

1. 从 `empresas.razao_social` 或 `estabelecimentos.nome` 模糊匹配找到CNPJ
2. 用CNPJ到INPI查询知识产权信息
3. 如需最新状态（开户/注销/欠税），访问RFB官网：https://cnpj.receita.fazenda.gov.br
4. 对2024年9月后的新公司，必须结合RFB在线查询补充
