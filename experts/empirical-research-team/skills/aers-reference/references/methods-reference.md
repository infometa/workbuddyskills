# 方法论速查

## 估计器 × Python 库 × 适用场景

| 方法 | 估计器 | Python 库 | 适用场景 |
|------|--------|-----------|---------|
| OLS | `smf.ols()` | statsmodels | 横截面基准 |
| 高维FE | `pf.feols()` | pyfixest | 面板+多维固定效应 |
| IV/2SLS | `IV2SLS.from_formula()` | linearmodels | 内生性+工具变量 |
| 2×2 DID | `pf.feols("y~D:Post\|i+t")` | pyfixest | 前后×处理对照 |
| 交错 DID (CS) | `att_gt()` | csdid (R via rpy2) | 多时期交错处理 |
| 交错 DID (SA) | `pf.feols("y~sunab(G,t)\|i+t")` | pyfixest | Sun-Abraham 估计 |
| SDID | `synthdid.estimate()` | synthdid | 合成双重差分 |
| Sharp RD | `rdrobust(y, x, c=0)` | rdrobust | 断点回归 |
| Fuzzy RD | `rdrobust(y, x, c=0, fuzzy=D)` | rdrobust | 模糊断点 |
| SCM | `Synth()` | pysynth | 合成控制 |
| DML | `LinearDML()` | econml | 双重机器学习 |
| 因果森林 | `CausalForest()` | econml.grf | 异质性处理效应 |
| S/T/X/R-Learner | `SLearner/TLearner/...` | econml.metalearners | 元学习器 |
| DR-Learner | `DRLearner()` | econml.dr | 双重稳健CATE |
| IPTW | `IPTW()` | zepid | 逆概率加权 |
| TMLE | `TMLE()` | zepid | 目标最大似然 |
| KM/Cox | `KaplanMeierFitter/CoxPHFitter` | lifelines | 生存分析 |

## 标准误选择速查

| 场景 | SE 类型 | 代码 |
|------|---------|------|
| 异方差 | HC3 | `vcov="HC3"` |
| 聚类（firm） | CRV1 | `vcov={"CRV1":"firm_id"}` |
| 双向聚类 | Two-way CRV | `vcov={"CRV1":"firm_id+year"}` |
| 时序相关 | Newey-West | `cov_type="HAC", cov_kwds={"maxlags":4}` |

## 必需 Python 库

```bash
pip install pandas numpy scipy matplotlib seaborn \
            statsmodels linearmodels pyfixest \
            rdrobust rddensity \
            econml causalml \
            stargazer python-docx openpyxl
```

## 关键数值基准（验证用）

这些是经典因果推断教科书数据集的已知真实值，可用于验证代码正确性：

| 数据集 | 方法 | Gold Value | 陷阱 |
|--------|------|-----------|------|
| LaLonde (1986) | 观测匹配 | 朴素ATT = -$635（错误符号！）；OLS调整后 ≈ +$1,548 | 朴素比较给出反向结果 |
| Card (1995) | IV | OLS回报 ~0.075；IV回报 ~0.131；F ~13.3 | IV > OLS 表明下偏 |
| RDD 模拟 | Sharp RD | True TAU = 3.0 | 朴素均值差 = 5.51 ≠ 真值 |
| Staggered DiD | TWFE | 存在负权重偏误 | 必须用 CS/SA 而非朴素 TWFE |
| Bad Control | 后处理 | Total=2.5, Direct=0.5, Mediator bias=2.0 | 加入中介变量=坏控制 |

## 效应量解释速查

| 模型 | 解释 |
|------|------|
| level-level | X增加1单位，Y增加β单位 |
| log-level | X增加1单位，Y增加β×100% |
| level-log | X增加1%，Y增加β/100单位 |
| log-log | X增加1%，Y增加β% |
| 对数点 | 0.05 log points ≈ 5%（精确：exp(0.05)-1 = 5.13%） |
