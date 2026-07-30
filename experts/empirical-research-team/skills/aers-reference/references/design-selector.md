# 因果识别策略选择决策树

## 核心决策逻辑

```
数据 + 研究问题
  │
  ├── 有运行变量 + 已知截断点？
  │     → RDD (Regression Discontinuity Design)
  │     条件：密度连续（McCrary检验通过）、无操纵
  │     估计器：rdrobust (sharp/fuzzy)
  │
  ├── 有外生工具变量 Z？
  │     → IV / 2SLS
  │     条件：相关性（F≥10）、排除限制、单调性
  │     估计器：IV2SLS.from_formula() / linearmodels
  │
  ├── 有明确的 前/后 × 处理/对照 结构？
  │     ├── 所有单位同时处理？ → 2×2 DID
  │     └── 不同单位不同时间处理？ → 交错 DID
  │           检查：Bacon分解是否有负权重
  │           有负权重 → Callaway-Sant'Anna / Sun-Abraham
  │           无负权重 → 传统 TWFE 可用
  │     估计器：pf.feols("y ~ sunab(G,t) | i + t")
  │
  ├── 只有 1 个处理单位 + 长面板？
  │     → SCM (Synthetic Control Method)
  │     条件：前期拟合良好、插值有效
  │     估计器：pysynth / synthdid
  │
  ├── 高维协变量 X，可观测选择？
  │     → ML 因果推断
  │     ├── 只关心 ATE → DML (LinearDML)
  │     ├── 关心异质性 CATE → CausalForest / X-Learner
  │     └── 需要策略学习 → DRPolicyTree
  │     条件：无混淆（CIA）+ 重叠
  │
  └── 以上都不满足？
        → 匹配 + 敏感性分析
        方法：PSM / CEM / Mahalanobis
        必须：Oster δ* + E-value 报告
```

## 方法 × 关键检验 × 通过标准

| 方法 | 关键检验 | 通过标准 |
|------|---------|---------|
| DID | 预趋势（事件研究 pre-period ≈ 0） | 联合F检验 p > 0.1 |
| DID | Bacon分解（负权重检查） | 负权重占比 < 10% |
| IV | 第一阶段F统计量 | F ≥ 10 (OLS), F ≥ 23 (AR) |
| IV | 过度识别（Hansen J） | p > 0.1 |
| RDD | McCrary密度检验 | 断点处密度连续 |
| RDD | 带宽敏感性 | 不同带宽下系数稳定 |
| SCM | 前期拟合RMSPE | 拟合良好（视觉+数值） |
| DML | 交叉拟合残差均值 ≈ 0 | 残差分布对称 |

## 何时选择哪种标准误

| 数据结构 | 推荐 SE | pyfixest 语法 |
|---------|---------|--------------|
| 横截面，异方差 | HC3 | `vcov="HC3"` |
| 面板，单层聚类 | CRV1 | `vcov={"CRV1":"firm_id"}` |
| 面板，双层聚类 | Two-way | `vcov={"CRV1":"firm_id+year"}` |
| 时间序列 | HAC (Newey-West) | statsmodels `cov_type="HAC"` |
| 空间相关 | Conley SE | 自定义核 |
