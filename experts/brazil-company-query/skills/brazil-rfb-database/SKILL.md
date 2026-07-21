---
name: brazil-rfb-database
description: "Comprehensive Brazilian business, legal & economic intelligence skill. Covers RFB (Receita Federal) company database (19M companies, 199M branches), INPI open data (patents 1.1M, trademarks 6.5M, industrial designs 203K, software 98K, contracts 58K), BCB SGS economic indicators (USD/BRL, Selic, IPCA), World Bank indicators, and 6 reference texts. CNPJ INSTANT QUERY: For exact CNPJ lookups, use the built-in COS binary search tool (cnpj_query.py) — zero download, ~1s response via HTTP Range. AUTO-DOWNLOAD: For bulk analysis, AI automatically downloads required RFB/INPI data shards from official Brazilian government sources (~500MB per shard, cached at ~/.workbuddy/brazil-data/)."
agent_created: true
---

# Brazil RFB Database — 巴西企业工商信息查询

## 核心使用原则

**语料库优先原则（强制）**：使用本技能回答任何巴西相关问题（商业/法律/税务/出口/认证/信用等）时，必须优先读取语料库参考文本（Doing Business in Brazil 7th、OECD Trust Report、World Bank Subnational Brazil 2021、World Bank Reports）中的权威信息。语料库内容作为回答的基础骨架和核心依据，在线搜索及API实时数据仅用于补充最新动态和二次确认。禁止跳过语料库直接使用通用知识或网络搜索。每条回答末尾附来源说明。

---

## CNPJ 即时查询（COS 二进制搜索）— 零下载、秒级响应

**当用户输入一个具体的 14 位 CNPJ 号码时，这是最快的查询方式。** 无需下载任何大文件，通过 HTTP Range 直接在腾讯云 COS 上进行二进制搜索，每次查询仅消耗 ~600 字节流量。

### 使用方法

```bash
python skills/brazil-rfb-database/cnpj_query.py <14位CNPJ>
```

### 前置条件

| 查询模式 | 所需依赖 | 安装命令 |
|---------|---------|---------|
| **COS 即时查询**（推荐，零下载） | Python 3.8+, requests | `pip install requests`（一次性，~100KB） |
| **本地批量查询**（高级模式） | Python 3.8+, pyarrow, pandas | `pip install pyarrow pandas`（一次性，~200MB） |

> **说明**：COS 即时查询无需安装 pyarrow/pandas，仅需 requests 即可。仅当需本地执行 Parquet/CSV 批量查询（如扫描全部10个分片、分析 INPI 数据集）时才需要 pyarrow + pandas。AI 自动检测依赖可用性，如缺失会提示安装。

### 查询原理

```
用户输入 CNPJ（14位）→ 二分搜索 COS 索引文件（26次HTTP Range，~600字节）
                      → 定位到数据文件偏移量 → 下载一行文本 → 解析返回JSON
```

### COS 数据文件（69M+条记录，13.9GB，存储于腾讯云上海）

> **可用性说明**：COS 存储桶由专家作者维护，数据源自巴西联邦税务局（RFB）公开数据集。若 COS 不可达（如存储桶下线或权限变更），将自动回退到 WebSearch 在线查询或 RFB 官方源按需下载。数据更新频率：跟随 RFB 官方发布节奏，约每月更新一次，当前数据版本为 2026-06。

| 文件 | 大小 | 记录数 | 索引键 | 说明 |
|------|------|--------|--------|------|
| `estab.idx/.txt` | 3.8GB+1.3GB | 69.6M | 14位CNPJ | 分支机构：nome_fantasia, UF, situacao, CNAE, municipio |
| `empresa.idx/.txt` | 3.7GB+1.0GB | 68.6M | 8位CNPJ base | 公司主体：razao_social, natureza_juridica, capital_social, porte |
| `socio.idx/.txt` | 2.0GB+0.6GB | 37.5M | 8位CNPJ base | 合伙人：nome, qualificacao |
| `simples.idx/.txt` | 0.6GB+0.7GB | 49.0M | 8位CNPJ base | 税务身份：opcao_simples, opcao_mei |

### 返回示例

```json
{
  "cnpj": "00000000000191",
  "cnpj_base": "00000000",
  "nome_fantasia": "DIRECAO GERAL",
  "uf": "DF",
  "situacao": "02",
  "cnae": "6422100",
  "municipio": "9701",
  "data_inicio": "19660801",
  "razao_social": "BANCO DO BRASIL SA",
  "natureza_juridica": "2038",
  "capital_social": "0.0",
  "porte": "05",
  "socios": [{"nome": "...", "qualificacao": "10"}],
  "opcao_simples": "N",
  "opcao_mei": "N"
}
```

### 查询优先级

1. **用户提供精确 CNPJ（14位数字）→ 优先使用 COS 二进制搜索**（`cnpj_query.py`）
2. 用户提供公司名 → 使用 WebSearch + 语料库
3. 用户需要最新实时数据 → 使用在线 API（BCB）
4. 用户需要法律/税务/行业分析 → 使用语料库参考文本

---

## 数据自动检测 + 按需下载 — AI 全自动，用户无感

**用户无需任何手动操作。AI 自动检测本地缓存数据是否存在，按需从巴西官方源下载，后续查询自动使用缓存，毫秒级响应。**

### 官方数据源（AI 自动下载用）

```
─────────────────────────────────────────────────────────────────────
 RFB CNPJ 企业登记（每月更新）:
   官方源: https://arquivos.receitafederal.gov.br/public.php/dav/files/YggdBLfdninEJX9/
   类型: Nextcloud WebDAV，可列表+下载单个ZIP文件
   最新: 2026-06（约7.5GB压缩，10个分片，每片500MB~2GB）

 INPI 开放数据（每周更新）:
   官方源: https://dadosabertos.inpi.gov.br/download/
   ⚠️ 注意: 目录页 (/download/) 可能返回500（服务端CKAN应用异常），
      但不影响CSV文件直接下载，所有文件通过完整URL可正常访问。
   子目录:
   ├── marcas/          商标 (8个CSV)
   ├── patentes/        专利 (10个CSV)     ← 新增！原语料库没有
   ├── contratos/       技术合同 (5个CSV)
   ├── programas_de_computador/  计算机程序 (7个CSV)
   └── desenhos_industriais/     工业设计 (11个CSV)
   更新: 2026-06-27（均为最新）
─────────────────────────────────────────────────────────────────────
```

### 缓存目录约定

```python
import os

# 缓存根目录（自动创建，无需用户配置）
BRAZIL_CACHE = os.path.expanduser("~/.workbuddy/brazil-data")

# 缓存子目录结构
# ~/.workbuddy/brazil-data/
#   ├── cnpj-data/parquet/        ← RFB Parquet（从下载的ZIP解压后）
#   │   ├── empresas/0.parquet ~ 9.parquet
#   │   ├── estabelecimentos/0.parquet ~ 9.parquet
#   │   ├── socios/0.parquet ~ 9.parquet
#   │   └── ...
#   ├── inpi/                      ← INPI CSV（从dadosabertos下载）
#   │   ├── marcas/MARCAS_DEPOSITANTES.csv
#   │   ├── patentes/PATENTES_DEPOSITANTES.csv
#   │   └── ...
#   └── .metadata.json            ← 缓存元数据
```

### 自动检测 + 按需下载逻辑（AI 运行时严格遵循）

```python
import os, json

# ======== 官方源URL（固定，不可更改） ========
RFB_SOURCE  = "https://arquivos.receitafederal.gov.br/public.php/dav/files/YggdBLfdninEJX9"
INPI_SOURCE = "https://dadosabertos.inpi.gov.br/download"

# ======== 缓存检测（每次查询先检测） ========
def detect_cache():
    """检测已缓存了哪些数据"""
    cache = {
        "cnpj":          "none",
        "inpi_marcas":   False,
        "inpi_patentes": False,
        "inpi_contratos": False,
        "inpi_prog_comp": False,
    }
    B = os.path.expanduser("~/.workbuddy/brazil-data")

    # RFB CNPJ 检测
    empresas = os.path.exists(f"{B}/cnpj-data/parquet/empresas/0.parquet")
    estabs   = os.path.exists(f"{B}/cnpj-data/parquet/estabelecimentos/0.parquet")
    if empresas and estabs:
        cache["cnpj"] = "full"
    elif empresas:
        cache["cnpj"] = "partial"

    # INPI 各数据集检测
    cache["inpi_marcas"]   = os.path.exists(f"{B}/inpi/marcas/MARCAS_DEPOSITANTES.csv")
    cache["inpi_patentes"] = os.path.exists(f"{B}/inpi/patentes/PATENTES_DEPOSITANTES.csv")
    cache["inpi_contratos"] = os.path.exists(f"{B}/inpi/contratos/CONTRATOS_DESPACHO.csv")
    cache["inpi_prog_comp"] = os.path.exists(f"{B}/inpi/programas_computador/PROG_COMP_DADOS_BASICOS.csv")
    return cache

# ======== 按需下载函数（AI 在运行时用 curl 实际执行） ========

def download_rfb_shard(cnpj_8_prefix):
    """按CNPJ前8位计算分片号 → 只下载对应分片"""
    shard = int(cnpj_8_prefix) % 10
    target_dir = os.path.expanduser("~/.workbuddy/brazil-data/cnpj-data/parquet")
    os.makedirs(f"{target_dir}/empresas", exist_ok=True)
    os.makedirs(f"{target_dir}/estabelecimentos", exist_ok=True)
    os.makedirs(f"{target_dir}/socios", exist_ok=True)

    # 1. 通过WebDAV PROPFIND获取最新月份
    #    curl -X PROPFIND -H "Depth:1" {RFB_SOURCE}/
    #    → 解析XML中的<d:href>获取最新月份目录

    # 2. 只需下载所需分片（约500MB），不用下载全部7.5GB
    required_files = [
        f"Empresas{shard}.zip",        # 500MB
        f"Estabelecimentos{shard}.zip", # 2GB (largest, 按需)
        f"Socios{shard}.zip",           # 236MB
        "Cnaes.zip", "Municipios.zip", "Naturezas.zip",
        "Qualificacoes.zip", "Simples.zip",
    ]
    for fname in required_files:
        url = f"{RFB_SOURCE}/{{最新月份}}/{fname}"
        target = f"{target_dir}/{fname}"
        # AI执行: curl -L --connect-timeout 30 -o {target} {url}
        # AI执行: unzip -o {target} -d {target_dir}
        # AI执行: rm {target} （解压后删除zip节省空间）

def download_inpi_dataset(dataset):
    """按需下载指定的INPI数据集"""
    urls = {
        "marcas": [
            "MARCAS_DEPOSITANTES.csv",
            "MARCAS_CLASSIFICACOES_NACIONAIS.csv",
        ],
        "patentes": [
            "PATENTES_DEPOSITANTES.csv",
            "PATENTES_DADOS_BIBLIOGRAFICOS.csv",
            "PATENTES_DESPACHOS.csv",
        ],
        "contratos": [
            "CONTRATOS_DESPACHO.csv",
            "CONTRATOS_CEDENTE.csv",
            "CONTRATOS_CESSIONARIOS.csv",
        ],
    }
    for f in urls.get(dataset, []):
        url = f"{INPI_SOURCE}/{dataset}/{f}"
        target = os.path.expanduser(f"~/.workbuddy/brazil-data/inpi/{dataset}/{f}")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if not os.path.exists(target):
            pass  # AI执行: curl -L --connect-timeout 30 -o {target} {url}
```

### 查询优先级决策树（带按需下载）

```
用户输入公司名 / CNPJ
  │
  ├─ 缓存中有数据？──→ ✅ 本地查询（毫秒级）
  │
  └─ 无缓存 ──→ 执行按需下载（AI自动）
       │
       ├─ Step 1: WebSearch 在线查询 ───────────→ 5~10秒返回初步结果
       │   （用户优先看到结果，不等下载）
       │
       ├─ Step 2: 后台按需下载（一次性）
       │   ├─ CNPJ前8位 → 分片号 → 下载对应RFB ZIP (200~500MB)
       │   ├─ 如需商标 → 下载 MARCAS_DEPOSITANTES.csv (835MB)
       │   ├─ 如需专利 → 下载 PATENTES_DEPOSITANTES.csv (138MB)
       │   └─ 如需合同 → 下载 CONTRATOS_DESPACHO.csv (302MB)
       │
       └─ Step 3: 解压 → 缓存到 ~/.workbuddy/brazil-data/
           下次查询同一分片 → 毫秒级
```

### 用户实际体验流程

```
首次查询 "查一下 Petrobras":
  → AI: "正在查询...（首次使用，后台下载数据中，约30-60秒）"
  → 5秒后返回: WebSearch初步结果
  → 40秒后: 数据缓存完成
  → 后续查询: 即时返回

第二次查询 "查另一家公司":
  → AI检测缓存命中 → 毫秒级本地查询 + 在线补充最新状态
  → 立即返回完整结果
```

## 快速入门 — 自动按需查询

**用户拿到本专家后，零配置、零下载即可开始查询。AI 自动检测缓存 → 按需下载 → 在线兜底，全程用户无感。**

### 查询流程总览

```
用户输入
  │
  ├─ 有缓存数据 ───→ 毫秒级本地 Parquet/CSV 查询
  │
  ├─ 无缓存 ──────→ AI后台执行：
  │                  ① 在线 WebSearch 先返回（5~10秒）
  │                  ② 同时按需下载RFB/INPI官方数据（30~60秒）
  │                  ③ 缓存后后续查询加速
  │
  └─ 纯在线查询 ──→ 不需要本地数据的场景（汇率/Selic等）
```

### 方式一：WebSearch 在线查询（最稳定，零下载）

当需要查企业信息且无本地缓存时，首选 WebSearch 多站点并行查询：

- 搜索 "CNPJ {14位号码}" → 获取多家巴西企业查询网站的结果
- 搜索 "{公司名} CNPJ" → 获取公司 CNPJ 号
- 常用巴西企业查询网站：CNPJ.info, CNPJ.app, Consulta CNPJ, Receita WS

查询优先级：
1. **有 CNPJ 时**：WebFetch 查 CNPJ.info 或 CNPJ.app → 解析返回字段
2. **仅有公司名时**：WebSearch 搜索公司名获取 CNPJ → 查到 CNPJ 后再查详情
3. 如需最新税务状态：WebSearch 搜索 "CNPJ {号码} situação cadastral"

### 方式二：按需自动下载（首次查询触发）

当 WebSearch 无法满足深度查询（股东信息、历史数据、知识产权）时，AI 自动触发：

```python
# 这是 AI 的内部逻辑，用户完全无感
# Step 1: AI 检测到缓存 miss
# Step 2: AI 执行 curl 从官方源下载所需分片
# Step 3: AI 解压并查询，返回结果
# Step 4: 缓存数据到 ~/.workbuddy/brazil-data/ 后续秒级
```

### 在线查询返回字段说明

| 字段 | 含义 | 信息来源 |
|------|------|---------|
| CNPJ | 14位国家法人登记号 | WebSearch / 第三方站点 |
| Razao Social | 公司正式名称 | WebSearch / 第三方站点 |
| Nome Fantasia | 商业名称/店名 | WebSearch / 第三方站点 |
| Situacao | 状态 (Ativa/Suspensa/Inapta/Baixada/Nula) | WebSearch / 第三方站点 |
| Endereco | 注册地址 | WebSearch / 第三方站点 |
| CNAE | 行业分类代码 | WebSearch / 第三方站点 |
| Capital Social | 注册资本 | WebSearch / 第三方站点 |
| Natureza Juridica | 法律性质 | WebSearch / 第三方站点 |

---

## 完整 CNPJ 构造方法

完整 CNPJ = cnpj + cnpj_ordem + cnpj_dv

- 前8位 (cnpj)：公司根号
- 第9-12位 (cnpj_ordem)：分支编号（总部通常为 0001）
- 第13-14位 (cnpj_dv)：校验码
- 总计 14 位数字

格式化：XX.XXX.XXX/XXXX-XX

## 企业状态代码速查（在线查询结果解析用）

| Situacao | 含义 | 风险等级 |
|----------|------|---------|
| **Ativa** | 正常运营中 | 低 |
| **Suspensa** | 被暂停（税务欠款等） | 中高 |
| **Inapta** | 未申报税务超过60个月 | 中 |
| **Baixada** | 已注销 | 极高 |
| **Nula** | 登记无效 | 极高 |

**企业规模 (Porte) 代码：**
- 1: Microempresa (ME) — 微型企业
- 3: Empresa de Pequeno Porte (EPP) — 小型企业
- 5: Demais — 其他（大/中型）

---

## INPI 知识产权查询补充（5大数据集）

找到 CNPJ 后，如需查询知识产权信息。AI 自动检测缓存 → 按需下载 → 本地查询。

### INPI 全部数据集结构

```
INPI 开放数据 (https://dadosabertos.inpi.gov.br/download/)
> ⚠️ 目录列表页面 `/download/` 可能返回 500 错误（INPI 服务端 CKAN 应用偶发异常），
> 但**所有 CSV 文件均可通过完整 URL 直接下载**，不影响实际使用。
> 例如: `curl -L -O https://dadosabertos.inpi.gov.br/download/marcas/MARCAS_DEPOSITANTES.csv` 正常。
├── marcas/                         ← 商标（6.5M+申请，首条查询约835MB）
│   ├── MARCAS_DEPOSITANTES.csv             835MB  持有人/申请人（关键表）
│   ├── MARCAS_CLASSIFICACOES_NACIONAIS.csv 111MB  国内分类
│   ├── MARCAS_CLASSIFICACOES_NICE.csv       3.8GB 尼斯国际分类
│   ├── MARCAS_CLASSIFICACOES_VIENA.csv      800MB 维也纳图形分类
│   ├── MARCAS_DADOS_BIBLIOGRAFICOS.csv      916MB 书目信息
│   ├── MARCAS_DESPACHOS.csv                 5.8GB 批文
│   └── MARCAS_PRIORIDADES.csv              9.6MB  优先权
│
├── patentes/                       ← 专利（1.1M+申请，全新数据集！）
│   ├── PATENTES_DEPOSITANTES.csv           138MB  申请人
│   ├── PATENTES_DADOS_BIBLIOGRAFICOS.csv    76MB  书目信息
│   ├── PATENTES_DESPACHOS.csv              408MB  批文
│   ├── PATENTES_INVENTORES.csv             236MB  发明人
│   ├── PATENTES_CLASSIFICACAO_IPC.csv      143MB  IPC国际专利分类
│   ├── PATENTES_CONTEUDO.csv               751MB  内容摘要
│   ├── PATENTES_PROCURADORES.csv           103MB  代理人
│   └── PATENTES_PRIORIDADES.csv             34MB  优先权
│
├── contratos/                      ← 技术转让合同（5.8万+）
│   ├── CONTRATOS_DESPACHO.csv             302MB  批文
│   ├── CONTRATOS_CEDENTE.csv               36MB  转让方
│   ├── CONTRATOS_CESSIONARIOS.csv          97MB  受让方
│   ├── CONTRATOS_DADOS_BASICOS.csv         3.7MB 基础信息
│   └── CONTRATOS_MODALIDADE.csv            8.8MB 合同类型代码表
│
├── programas_de_computador/        ← 计算机程序（9.8万+登记）
│   ├── PROG_COMP_DADOS_BASICOS.csv         7.2MB 基础信息
│   ├── PROG_COMP_AUTORES.csv              22.7MB 作者
│   ├── PROG_COMP_TITULAR.csv              18.7MB 权利人
│   ├── PROG_COMP_DESPACHOS.csv            80.6MB 批文
│   ├── PROG_COMP_CAMPOS.csv               134MB  技术领域
│   ├── PROG_COMP_LINGUAGEM.csv             6.2MB 编程语言
│   └── PROG_COMP_TIPO.csv                 26.8MB 类型
│
└── desenhos_industriais/          ← 工业设计（20.3万+）
    ├── DI_DEPOSITANTES.csv                 90MB  申请人
    ├── DI_DESPACHOS.csv                   118MB  批文
    └── ... 另有8个CSV + 3个图片ZIP
```

### AI 查询逻辑

```
查询某CNPJ的商标:
  1. detect_cache() → 有缓存？→ 本地读MARCAS_DEPOSITANTES.csv
  2. 无缓存 → 后台curl下载835MB → 缓存 → 查询
  3. 返回: 商标名称、申请号、Nice分类、状态、持有人

查询某公司的专利:
  1. detect_cache() → 有缓存？→ 本地读PATENTES_DEPOSITANTES.csv
  2. 无缓存 → 后台curl下载138MB → 缓存 → 查询
  3. 返回: 专利标题、IPC分类、发明人、法律状态

查询技术合同:
  1. 按当事人名/CNPJ查 CONTRATOS_CESSIONARIOS.csv
  2. JOIN CONTRATOS_MODALIDADE.csv 获取合同类型描述
  3. JOIN CONTRATOS_DESPACHO.csv 获取法律状态
```

### 在线备选方案（无本地数据时）
- **INPI pePI** (busca.inpi.gov.br)：无官方API，仅网页搜索，结果最多100条
- **INPI Portal de Servicos**：Beta阶段，API v1.0.2计划中
- **数据滞后**：INPI 数据通常滞后 1~4 周（与 RPI 公告周期同步）

---

## 数据时效性参考（了解即可，在线查询无此问题）

RFB 数据特征（仅对需要离线高级模式的用户有用）：
| 项目 | 说明 |
|------|------|
| **数据来源** | 巴西联邦税务局 (RFB) 公开数据 |
| **更新频率** | 约每月一次 |
| **数据格式** | Apache Parquet (.parquet) |
| **滞后风险** | 离线数据可能滞后1-2个月，在线查询为实时数据 |

## 附录：本地缓存查询（AI 自动执行，用户无感）

> AI 自动检测 `~/.workbuddy/brazil-data/` 下的缓存数据，按需从官方源下载。
> **用户全程无需手动操作。首次查询自动下载，后续毫秒级响应。**

### 缓存数据路径与官方源对照

```
缓存位置                    数据内容              来源官方源
─────────────────────────────────────────────────────────────────
~/.workbuddy/brazil-data/
├── cnpj-data/parquet/      RFB CNPJ 企业登记     RFB WebDAV
│   ├── empresas/0.parquet ~ 9.parquet  (1.4GB)
│   ├── estabelecimentos/~ (5.2GB)
│   ├── socios/0.parquet ~ 9.parquet    (677MB)
│   ├── simples/0.parquet               (297MB)
│   └── cnaes/、municipios/、naturezas/...
│
└── inpi/                    INPI 知识产权        dadosabertos.inpi.gov.br
    ├── marcas/MARCAS_DEPOSITANTES.csv          (835MB)
    ├── patentes/PATENTES_DEPOSITANTES.csv       (138MB)  ← 新增！
    ├── contratos/CONTRATOS_DESPACHO.csv         (302MB)
    ├── contratos/CONTRATOS_CEDENTE.csv           (36MB)
    ├── contratos/CONTRATOS_CESSIONARIOS.csv      (97MB)
    └── programas_computador/                    (297MB)
```

### 数据格式说明

| 数据 | 格式 | 原始格式 | 下载后是否需转换 |
|:----|:---:|:--------:|:--------------:|
| RFB CNPJ | Parquet (.parquet) | ZIP（每片一个zip） | 解压即可，无需转换 |
| INPI 商标/专利/合同/程序 | CSV | CSV（明文） | 直接原样缓存 |

### AI 自动查询逻辑（缓存优先 + 按需下载）

#### 首次查询流程（缓存不存在时）

```python
import os, subprocess, pyarrow.parquet as pq, pandas as pd

BRAZIL_CACHE = os.path.expanduser("~/.workbuddy/brazil-data")
CNPJ_DATA = f"{BRAZIL_CACHE}/cnpj-data/parquet"
INPI_DATA = f"{BRAZIL_CACHE}/inpi"
RFB_SOURCE = "https://arquivos.receitafederal.gov.br/public.php/dav/files/YggdBLfdninEJX9"

def query_company(cnpj_or_name):
    """查询企业信息：缓存优先 → 按需下载 → 在线兜底"""
    is_cnpj = len(cnpj_or_name.replace(".","").replace("/","").replace("-","")) == 14

    if is_cnpj:
        cnpj_clean = cnpj_or_name.replace(".","").replace("/","").replace("-","")
        cnpj_8 = cnpj_clean[:8]
        shard = int(cnpj_8) % 10

        # 检查缓存
        empresas_parquet = f"{CNPJ_DATA}/empresas/{shard}.parquet"
        if not os.path.exists(empresas_parquet):
            # 无缓存 → 按需下载
            month = "2026-06"  # AI动态获取最新月份
            for f in [f"Empresas{shard}.zip"]:
                dl_url = f"{RFB_SOURCE}/{month}/{f}"
                dl_target = f"{CNPJ_DATA}/{f}"
                os.makedirs(f"{CNPJ_DATA}/empresas", exist_ok=True)
                # AI执行: curl -L -o {dl_target} {dl_url}
                # AI执行: unzip -o {dl_target} -d {CNPJ_DATA}
                pass

        # 本地查询
        df = pq.read_table(empresas_parquet).to_pandas()
        result = df[df['cnpj_8'] == cnpj_8]

        # 补充最新状态：WebSearch
        # ...

        return result
    else:
        # 按公司名搜索 → 扫描全部10个分片（缓存已存在时）
        for i in range(10):
            p = f"{CNPJ_DATA}/empresas/{i}.parquet"
            if os.path.exists(p):
                df = pq.read_table(p).to_pandas()
                found = df[df['razao_social'].str.contains(cnpj_or_name, case=False, na=False)]
                if len(found) > 0: return found
        # 全无缓存 → WebSearch在线查
        return websearch_company(cnpj_or_name)
```

#### 按 CNPJ 查询企业信息（缓存命中时 — 最快路径）

```python
CACHE = os.path.expanduser("~/.workbuddy/brazil-data/cnpj-data/parquet")
cnpj_8 = target_cnpj[:8]
shard = int(cnpj_8) % 10  # 计算分片号，只查1个分片

# 查询 empresas 表 → 企业基本信息
df = pq.read_table(f"{CACHE}/empresas/{shard}.parquet").to_pandas()
row = df[df['cnpj_8'] == cnpj_8]

# 查询 estabelecimentos 表 → 分支机构详情
est = pq.read_table(f"{CACHE}/estabelecimentos/{shard}.parquet").to_pandas()
est_row = est[est['cnpj_8'] == cnpj_8]

# 查询 socios 表 → 股东结构
soc = pq.read_table(f"{CACHE}/socios/{shard}.parquet").to_pandas()
soc_row = soc[soc['cnpj_8'] == cnpj_8]
```

#### 按公司名搜索（缓存命中时）

```python
CACHE = os.path.expanduser("~/.workbuddy/brazil-data/cnpj-data/parquet")
target = "公司名关键词"
for i in range(10):
    p = f"{CACHE}/empresas/{i}.parquet"
    if os.path.exists(p):
        df = pq.read_table(p).to_pandas()
        found = df[df['razao_social'].str.contains(target, case=False, na=False)]
        if len(found) > 0: break
```

#### 查 INPI 商标（缓存优先 → 按需下载）

```python
CACHE = os.path.expanduser("~/.workbuddy/brazil-data/inpi")
marcas_file = f"{CACHE}/marcas/MARCAS_DEPOSITANTES.csv"

if not os.path.exists(marcas_file):
    # 按需下载 (AI自动执行)
    # curl -L -o {marcas_file} https://dadosabertos.inpi.gov.br/download/marcas/MARCAS_DEPOSITANTES.csv
    pass

# 按 CNPJ 查商标申请/持有人
marcas = pd.read_csv(marcas_file, dtype=str, low_memory=False)
result = marcas[marcas['cnpj_cpf_titular'].str.contains(cnpj_8, na=False)]
```

#### 查 INPI 专利（缓存优先 → 按需下载）

```python
CACHE = os.path.expanduser("~/.workbuddy/brazil-data/inpi")
patentes_file = f"{CACHE}/patentes/PATENTES_DEPOSITANTES.csv"

if not os.path.exists(patentes_file):
    # curl -L -o {patentes_file} https://dadosabertos.inpi.gov.br/download/patentes/PATENTES_DEPOSITANTES.csv
    pass

patentes = pd.read_csv(patentes_file, dtype=str, low_memory=False)
result = patentes[patentes['cnpj_cpf_depositante'].str.contains(cnpj_8, na=False)]
```

#### 查 INPI 技术合同（缓存优先 → 按需下载）

```python
CACHE = os.path.expanduser("~/.workbuddy/brazil-data/inpi")
contratos_file = f"{CACHE}/contratos/CONTRATOS_DESPACHO.csv"

if not os.path.exists(contratos_file):
    # curl -L -o {contratos_file} https://dadosabertos.inpi.gov.br/download/contratos/CONTRATOS_DESPACHO.csv
    pass

contratos = pd.read_csv(contratos_file, dtype=str, low_memory=False)
result = contratos[contratos['nm_parte'].str.contains("关键词", case=False, na=False)]
```

## 参考资料

> **⚠️ 按需读取策略**：以下参考文本合计约 3.2MB，**禁止全量加载**。AI 应根据用户问题的主题和领域，按章节相关性选择性读取对应文件。例如：查询企业设立流程 → 读取 Doing Business 公司法章节；查询城市营商环境 → 读取 World Bank Subnational 对应城市章节；查询政府治理/反腐败 → 读取 OECD Trust Report。仅当问题涉及多领域交叉时才读取多个文件的相关章节。

本技能还引用以下参考资源：

### Doing Business in Brazil (7th Edition) — Britcham, 2020

- **位置**: `references/Doing_Business_in_Brazil_7th.txt`
- **内容**: 536页PDF，含992,850字符（约165,000单词），涵盖巴西商业环境全貌
- **章节**: 巴西概况 → 政治制度 → 公司法 → 税务 → 劳工 → 移民 → 环境 → 知识产权 → 竞争法 → 公共事业 → 国际贸易 → 争议解决
- **用途**: 回答关于巴西商业环境、法律法规、投资政策、税务制度等宏观问题时优先参考此文档

### Drivers of Trust in Public Institutions in Brazil — OECD, 2023

- **位置**: `references/OECD_Trust_in_Public_Institutions_Brazil_2023.txt`
- **内容**: OECD 经合组织报告，161页，含459,521字符（约76,000单词）
- **核心主题**: 巴西公民对公共机构的信任度驱动因素分析，涵盖政府透明度、反腐败、公共服务质量、司法体系信任度等
- **用途**: 回答巴西政治环境、政府治理、反腐败、司法效能等政策层面问题时优先参考此文档

### World Bank Subnational Doing Business in Brazil 2021

- **位置**: `references/World_Bank_Subnational_Brazil_2021.txt`
- **内容**: 354页报告，1,254,939字符（约209,000单词），覆盖巴西27城市 vs 190经济体的营商环境排名
- **核心主题**: 各州/市的开办企业、施工许可、产权登记、合同执行、纳税等指标排名
- **用途**: 按城市提供企业开办、合同执行、纳税便利度等微观营商环境数据

### World Bank Reports

- **位置1**: `references/World_Bank_1.txt`（125页，327,563字符）
- **位置2**: `references/World_Bank_2.txt`（70页，176,751字符）
- **核心主题**: 世界银行涉及巴西的营商环境、经济发展、贸易政策等相关报告
- **用途**: 补充宏观经济发展趋势、跨境投资环境等主题的参考

### INPI 开放数据与CNPJ数据库分析报告

- **位置**: `references/INPI_API_CNPJ_Analysis.md`
- **内容**: INPI 各API/数据库的技术分析，涵盖专利、商标、工业设计、计算机程序、技术转让合同五大类
- **关键发现**: 华为是巴西第二大专利申请人(18,753件)，中国排第7(88,847件)；旧版pePI系统与新Portal开发路线图

## 在线 API 资源（实时查询，无需下载）

以下 API 可在回答问题时实时调用获取数据：

### 世界银行国家/指标 API

- **端点**: `https://api.worldbank.org/v2/`
- **认证**: 无需 Key，完全开放
- **巴西基础信息**: `GET /v2/country/br?format=json`
- **经济指标**: `GET /v2/country/BR/indicator/{code}?format=json`
- **可用指标分类**: 私营部门(营商环境)、贸易、金融、税收、基础设施、劳动力等数百种
- **用途**: 查询巴西历年GDP、营商便利度排名、各经济指标等实时数据

**与企业最相关的巴西指标代码（✅ 已验证可用）：**

| 指标代码 | 中文含义 | API路径示例 | 最新值 |
|---------|---------|------------|:----:|
| `NY.GDP.MKTP.CD` | GDP (现价美元) | `/v2/country/BR/indicator/NY.GDP.MKTP.CD` | US$2.28T (2025) |
| `NY.GDP.PCAP.PP.CD` | 人均GDP (PPP) | `/v2/country/BR/indicator/NY.GDP.PCAP.PP.CD` | US$22,338 (2024) |
| `SP.POP.TOTL` | 总人口 | `/v2/country/BR/indicator/SP.POP.TOTL` | 212.8M (2025) |
| `IC.FRM.CORR.ZS` | 企业行贿发生率 (%企业) | `/v2/country/BR/indicator/IC.FRM.CORR.ZS` | 12.38% (2025) |

> ⚠️ 原表中营商便利度、企业开办成本、总税率、进出口耗时、信贷便利度、基尼系数等指标已被世界银行归档下架（2021年Doing Business项目终止），不可用。如需此类数据，请使用 WebSearch 查询最新报告。

### BCB 巴西中央银行开放数据

- **门户**: `https://dadosabertos.bcb.gov.br/`
- **API类型**: CKAN API (`/api/3/action/`) + OData
- **用途**: 查询巴西金融/经济实时数据

**与企业最相关的BCB数据集：**

| 数据集名称 | 数据内容 | 企业用途 | 可用格式 |
|-----------|---------|---------|---------|
| `dolar-americano-usd-todos-os-boletins-diarios` | 美元/雷亚尔每日汇率 | 进出口成本核算 | JSON/CSV/OData |
| `11-taxa-de-juros---selic` | Selic基准利率 | 融资成本评估 | JSON/CSV |
| `expectativas-mercado` | Focus市场预期(通胀/GDP/汇率) | 宏观经济预测 | JSON/CSV/OData |
| `ifdata` | 金融机构数据 | 银行信用分析 | JSON/CSV/OData |
| `scr_data` | 信用登记系统数据 | 企业信用查询 | ZIP/CSV |
| `20716-taxa-media-de-juros` | 各类型贷款平均利率 | 企业融资成本 | JSON/CSV |
| `29038-endividamento-das-familias` | 家庭负债率 | 消费市场判断 | JSON/CSV |
| `pix` | Pix即时支付统计 | 支付方式趋势 | JSON/CSV/OData |
| `25149-cartoes-de-credito-ativos` | 活跃信用卡数 | 消费市场指标 | JSON/CSV |
| SFN (`ir-{CNPJ}`) | 每家金融机构数据 | 可查具体银行 | JSON/API |

### BCB SGS 时间序列 API（实时数据查询）

- **端点**: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/{n}?formato=json`
- **调用说明**: `{codigo}` = SGS 序列号, `{n}` = 最近N条数据(最大20), 支持日期范围查询: `?formato=json&dataInicial=dd/mm/yyyy`
- **注意**: `ultimos/` 参数最大值是20，超过会报错

**已验证的巴西核心经济指标 SGS 代码：**

| SGS代码 | 指标名称 | 频率 | 最新数据(2026年6月18日) | 企业用途 |
|---------|---------|------|----------------------|---------|
| **10813** | 美元/雷亚尔汇率 (USD/BRL) | 每日 | 5.0635 (06/17) | 定价换算、成本核算 |
| **11** | Selic年化利率 (% a.a.) | 每日 | 5.34% (06/17) | 融资成本评估 |
| **433** | IPCA月度通胀率 (%) | 月度 | 0.58 (2026/05), 年化4.89% | 通胀风险评估 |
| **13621** | 国际储备(现金概念, 百万USD) | 每日 | US$372,009M (06/16) | 国家信用参考 |

**过去一年 USD/BRL 汇率波动分析（2025.06.18 - 2026.06.17）：**
- 最高：5.6028（2025/07/30）
- 最低：4.8967（2026/05/11）
- 波动率：(5.6028 - 4.8967) / 4.8967 ≈ **14.42%**
- 当前(2026/06/17)相比去年高点已回落约 9.6%

**实时数据调用示例：**
- `GET /bcdata.sgs.10813/dados/ultimos/5?formato=json` → 美元汇率最新5天
- `GET /bcdata.sgs.11/dados/ultimos/3?formato=json` → Selic利率
- `GET /bcdata.sgs.433/dados/ultimos/12?formato=json` → 最近12个月IPCA通胀
- `GET /bcdata.sgs.13621/dados/ultimos/5?formato=json` → 国际储备

### 定价报价查询工作流

当专家需要进行批量产品的定价报价分析时（用户询问「这个价格能不能做」等场景），工作流如下：

1. **获取产品清单**：从用户输入解析产品名称、数量、单价（CNY）
2. **实时查询BCB API序列**：
   - 10813 最新5天 → 获取当前 USD/BRL 汇率
   - 10813 日期范围查询 → 获取过去1年数据，计算波动率
   - 11 最新 → 获取 Selic 利率
   - 433 最近13个月 → 获取年度 IPCA 通胀率
3. **换算逻辑**：CNY → USD → BRL（或直接 CNY/BRL 交叉汇率）
4. **美元结算建议**：
   - BRL贬值 >8%(3月内) + 通胀 >6% + 波动 >10% → ✅ 强烈建议美元
   - 波动 5-10% + 通胀 4-6% → ⚠️ 混合结算
   - BRL稳定/升值 + 通胀 <4% + 波动 <5% → ❌ 可用BRL
5. **输出**：报价评估表 + 宏观经济参考表

### 信用风险评估工作流

当报价评估表生成后，专家必须自动执行信用风险评估。评估自动识别目标企业/行业/城市，依次调用以下数据源：

**数据源调用顺序**：
1. 如已有 CNPJ → 查询 RFB 工商状态（ativa/suspensa/inapta/baixada/nula）和税务制度
2. 如已有 CNPJ → 查询 INPI 数据库确定知识产权持有情况
3. 如仅有行业 → 引用 Doing Business 7th 及 OECD 报告的行业风险分析
4. 如仅有城市 → 引用 World Bank Subnational Brazil 2021 的城市排名

**举措建议矩阵**（综合风险等级决定）：
- ✅ 低风险：30%+70%见提单副本，标准合同
- ⚠️ 中风险：50%+50%发货前付清，巴西律师审合同
- ❌ 高风险：100% T/T预付或保兑不可撤销L/C，中国信保承保
- 🔴 极高风险：100%全款到账后发货，建议放弃该客户

**关键参考文本中的案例方向**：
- Doing Business 7th: 司法效率(2-4年)、Lava Jato反腐败、破产受偿顺序、CARF税务争议
- OECD 2023: 制度信任与公共服务效率
- World Bank 2021: 城市间营商环境差异（São Paulo vs Salvador）

### 出海法律提醒工作流

在报价评估 + 信用风险评估完成之后，检测到用户有向巴西出口意图时，自动输出本模块。

**触发信号**：用户提及「巴西客户」「出口巴西」「发往巴西」「巴西市场」或询问具体产品能否进入巴西。

**产品-监管机构映射**：
- 食品/农产品 → MAPA + ANVISA
- 药品/医疗器械/化妆品 → ANVISA
- 电子产品/家电/IT → INMETRO + ANATEL
- 化工/农药/肥料 → IBAMA + ANVISA + MAPA
- 汽车/零部件/机械 → INMETRO + CONTRAN + IBAMA
- 玩具 → INMETRO（强制认证）
- 建材/钢材 → INMETRO + ABNT
- 医疗器械 → ANVISA（注册+GMP）+ INMETRO
- 能源/电池 → INMETRO + ANEEL + IBAMA

**主要监管要求（引自语料库 Doing Business 7th）**：
- ANVISA：药品注册、医疗器械分类注册+GMP、化妆品登记、食品登记
- INMETRO：强制认证（产品测试+工厂检查+市场监督）、葡萄牙语标签、ILAC互认
- MAPA：动物源产品健康证书、植物检疫证书、农药登记、双边协议认可名单
- IBAMA：化学品环境许可证、农药双重登记（与MAPA）
- ANATEL：电信设备三类认证、认可实验室测试报告

**关键要求**：
- 所有进口消费品需要葡萄牙语标签（产品名+CNPJ+原产地+成分+净含量+使用说明+安全警告）
- 部分品类必须通过对应机构认证/注册后方可进口
- 农药登记周期 2-5 年（全球最严格之一）
- 高风险医疗器械需境外工厂 GMP 现场检查

**在线搜索确认规则**：
- 每次输出后必须搜索最新法规变更
- 搜索中巴双边协议更新
- 搜索近期巴西召回/禁入事件
- 标记来源：语料库内容 vs 🔍在线确认内容

### 法律案例查询工作流

用户提出巴西法律相关问题（合同纠纷、劳工诉讼、税务争议、知识产权侵权、环保处罚等）时，自动激活。

**语料库案例检索优先级**：
1. Doing Business 7th Ch.22 Dispute Resolution: 法院管辖、诉讼程序、仲裁制度、证据规则
2. Doing Business 7th Ch.9 Labour Law: 劳工法院执行、解雇补偿、集体谈判
3. Doing Business 7th Ch.6 Tax Law: CARF税务法庭、税务争议
4. Doing Business 7th Ch.12 Environmental Law: IBAMA处罚、生物多样性法
5. Doing Business 7th Ch.10 IP: 商标/专利侵权、INPI无效程序
6. OECD Trust Report: 司法效率与信任度
7. Lava Jato反腐败 (Doing Business 7th + OECD): 腐败定罪、合规要求

**用户行为提醒规则**：合同仲裁条款、书面合同要求、税务合规、认证前置、劳工法执行、环境许可等针对性提醒。

### 本地化经营指南工作流

用户表现出去巴西开分公司/子公司/办事处的意向后自动激活。

**设立形式对比**：分公司(Branch, 需总统法令) / LTDA有限责任公司(推荐) / S.A.股份有限公司 / 代表处

**关键城市信用数据**（参考 WB Subnational Brazil 2021）：
- ✅ 低风险城市：São Paulo, Belo Horizonte, Curitiba, Porto Alegre, Florianópolis
- ⚠️ 中风险城市：Rio de Janeiro, Brasília, Manaus(自贸区)
- ❌ 较高风险城市：Fortaleza, Salvador, Recife（执行合同3-4年）

**10步注册清单**：文件准备(海牙认证) → 城市选择 → 律师聘请 → Junta Comercial注册 → CNPJ → 经营许可 → 银行开户 → 会计师 → 劳工登记

**费用参考**：圣保罗设立LTDA初始成本BRL 5,000-15,000
