# 发表级输出规范

## 必需表格（5 个）

| # | 表格 | 内容 | 格式 |
|---|------|------|------|
| T1 | Balance Table | 处理vs对照，含均值、SD、差异、SMD、p值 | .xlsx + .tex + .docx |
| T2 ★ | Main Results | 渐进控制 M1→M6（核心！） | .xlsx + .tex + .docx |
| T3 | Mechanism | 同一处理，3+ 结果变量并列 | .xlsx + .tex + .docx |
| T4 | Heterogeneity | 子群×主系数 + Wald等式检验 | .xlsx + .tex + .docx |
| T5 | Robustness | 8列综合稳健性 | .xlsx + .tex + .docx |

## Table 2 标准 6 列结构

| 列 | 规范 | 含义 |
|----|------|------|
| M1 | y ~ D | 原始双变量 |
| M2 | y ~ D + demographics | + 人口统计学 |
| M3 | y ~ D + demographics + industry | + 行业控制 |
| M4 | y ~ D + X \| unit_FE | + 单位固定效应 |
| M5 | y ~ D + X \| unit_FE + time_FE | + 双向固定效应 |
| M6 | y ~ D + X \| unit_FE + time_FE + interaction_FE | + 交互FE + 聚类稳健SE |

## 必需图形（4 个）

| # | 图形 | 内容 | 格式 |
|---|------|------|------|
| F1 | Trend/Motivation | 处理vs对照组均值随时间变化 | PNG(300dpi) + PDF |
| F2 | Event Study | 事件研究系数图，95% CI，基期-1 | PNG(300dpi) + PDF |
| F3 | Coefficient Plot | M1→M6 系数+CI 横向排列 | PNG(300dpi) + PDF |
| F4 | Sensitivity | 规范曲线/Oster/HonestDiD | PNG(300dpi) + PDF |

## 图形规范

- 分辨率：PNG ≥ 300 dpi
- 尺寸：宽 8 英寸，高 5 英寸（标准）
- 字号：最小 8pt（缩放后可读）
- 配色：黑白友好（灰度可区分）
- 图注：放图下方，含数据来源和样本说明
- CI：95% 置信区间（虚线或阴影）

## 表格规范

- 风格：AER booktabs（三线表，无垂直线）
- 标准误：括号内，紧跟系数下方
- 显著性：*** p<0.01, ** p<0.05, * p<0.1
- 注释：表底，含 SE 类型说明、样本量、R²/Adjusted R²
- 控制变量指示：Yes/No 行

## 标准输出目录

```
project/
├── tables/
│   ├── table1_balance.xlsx/.tex/.docx
│   ├── table2_main.xlsx/.tex/.docx
│   ├── table3_mechanism.xlsx/.tex/.docx
│   ├── table4_heterogeneity.xlsx/.tex/.docx
│   └── table5_robustness.xlsx/.tex/.docx
├── figures/
│   ├── fig1_trend.png/.pdf
│   ├── fig2_event_study.png/.pdf
│   ├── fig3_coefplot.png/.pdf
│   └── fig4_sensitivity.png/.pdf
├── artifacts/
│   ├── pap.json              (预分析计划)
│   ├── sample_construction.json (样本构建日志)
│   ├── data_contract.json    (数据合约)
│   └── result.json           (可复现性印章)
└── manuscript/
    └── paper.tex/.docx
```

## 可复现性印章

每次分析结束必须生成 `artifacts/result.json`：

```json
{
  "python_version": "3.11.x",
  "pyfixest_version": "0.x.x",
  "dataset_sha256_16": "abcdef1234567890",
  "n_obs": 12000,
  "estimate": 0.045,
  "se_cluster": 0.012,
  "ci95": [0.021, 0.069],
  "pre_registration": "artifacts/pap.json",
  "data_contract": "artifacts/data_contract.json",
  "timestamp": "2026-07-30T12:00:00Z"
}
```
