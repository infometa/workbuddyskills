# 埃及 公共事务 (Egypt Public Affairs)

## 简介

埃及公共事务专家，服务中资企业跨境经营一站式公共事务咨询。

## 能力覆盖

- 政府关系建设（政府部门识别、沟通渠道、礼仪规范）
- 政策跟踪与解读（Vision 2030、投资法、新行政首都、经济特区）
- 监管沟通策略（GAFI、ITIDA、NTRA 等）
- 行业协会与商会参与
- 公共舆论监测（Arab Barometer 民调数据）
- ESG 与企业社会责任
- 媒体关系与传播策略
- 危机公关与突发事件应对
- 利益相关方管理
- 招投标与政府采购

## 语料库

| 来源 | 文件数 | 规模 |
|------|--------|------|
| Reference_Texts | 25 份 | ~95K 字符 |
| DuckDB | 5 表 | 语料元数据 + 政府/媒体联系人 + 危机案例 + 利益相关方 |

## 引擎脚本

- `fetch_with_fallback.py` — 多层网络抓取降级（直连→Google缓存→CORS网关（可配置）），支持域名白名单和环境变量配置
- `corpus_manager.py` — 自动化语料归档与状态索引

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖说明：
- `requests` — HTTP 网络请求（fetch_with_fallback 依赖）
- `duckdb` — 结构化数据查询（政府/媒体联系人、危机案例、利益相关方）

## 环境变量（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FETCH_GATEWAYS` | CORS 代理网关列表（逗号分隔） | 内置 3 个免费网关 |
| `ENABLE_GATEWAY` | 是否启用 CORS 网关降级 | `true` |
| `FETCH_ALLOWED_DOMAINS` | 允许抓取的域名白名单（逗号分隔） | `*.gov.eg,*.com.eg,...` |
| `HTTPS_PROXY` / `HTTP_PROXY` | 自定义代理 | 无 |

## 维护

- 语料更新：将新 .txt 放入 `Reference_Texts/`，运行 `corpus_manager.py`
- 定向搜索站点：capmas.gov.eg, cbe.org.eg, gafi.gov.eg, itida.gov.eg

## 版本

v1.0.0 — 初始版本
