# Stata / R 代码参考模板

当审稿人要求 Stata 或 R 复现包时，使用以下模板作为参考。

---

## Stata 核心模板

### DID / 事件研究

```stata
* ══════════════════════════════════════════════════
* 1. 数据准备
* ══════════════════════════════════════════════════
use "data/panel_data.dta", clear
xtset id year

* ══════════════════════════════════════════════════
* 2. 基准 DID (TWFE)
* ══════════════════════════════════════════════════
reghdfe log_wage treated_post age edu tenure, ///
    absorb(id year) vce(cluster firm_id)
eststo m_base

* ══════════════════════════════════════════════════
* 3. 事件研究 (Sun-Abraham)
* ══════════════════════════════════════════════════
* 生成相对时间
gen rel_time = year - first_treat_year
* 基期 = -1
eventstudyinteract log_wage rel_time, ///
    cohort(first_treat_year) control_cohort(never_treated) ///
    absorb(id year) vce(cluster firm_id)

* 或使用 did_multiplegt (de Chaisemartin & D'Haultfoeuille)
did_multiplegt log_wage id year treated, ///
    robust_dynamic dynamic(5) placebo(3) breps(100) cluster(firm_id)

* ══════════════════════════════════════════════════
* 4. Callaway & Sant'Anna
* ══════════════════════════════════════════════════
csdid log_wage age edu, ivar(id) time(year) gvar(first_treat_year) ///
    method(dripw) vce(cluster firm_id)
csdid_plot

* ══════════════════════════════════════════════════
* 5. 渐进控制表 (Table 2)
* ══════════════════════════════════════════════════
eststo clear
reghdfe log_wage treated_post, vce(cluster firm_id)
eststo m1
reghdfe log_wage treated_post age edu, vce(cluster firm_id)
eststo m2
reghdfe log_wage treated_post age edu tenure firm_size, vce(cluster firm_id)
eststo m3
reghdfe log_wage treated_post age edu tenure firm_size, absorb(industry year) vce(cluster firm_id)
eststo m4
reghdfe log_wage treated_post age edu tenure firm_size, absorb(id year) vce(cluster firm_id)
eststo m5
reghdfe log_wage treated_post age edu tenure firm_size, absorb(id year industry#year) vce(cluster firm_id)
eststo m6

esttab m1 m2 m3 m4 m5 m6 using "tables/table2_main.tex", ///
    replace booktabs label star(* 0.1 ** 0.05 *** 0.01) ///
    se(3) b(4) r2 N ///
    title("Main Results: Effect on Log Wages") ///
    note("Standard errors clustered at firm level in parentheses.")
```

### IV / 2SLS

```stata
* 第一阶段
reghdfe edu_years college_proximity age age_sq, absorb(state year) vce(cluster state)
test college_proximity  // F统计量

* 2SLS
ivreghdfe log_wage age age_sq (edu_years = college_proximity), ///
    absorb(state year) cluster(state) first

* 弱工具变量稳健推断
weakivtest  // Stock-Yogo / Olea-Pflueger
rivtest     // Anderson-Rubin
```

### RDD

```stata
* Sharp RD
rdrobust outcome running_var, c(0) p(1) kernel(triangular) vce(cluster school_id)
rdplot outcome running_var, c(0) p(1)

* McCrary密度检验
rddensity running_var, c(0) plot
```

### 稳健性

```stata
* Oster (2019) — 需要安装 psacalc
psacalc delta treated_post, rmax(0.8) mcontrol(age edu tenure)
* delta > 1 → 稳健

* 规范曲线 — 需要安装 specurve
specurve log_wage treated_post, ///
    controls(age edu tenure firm_size) ///
    fe(id year industry#year) ///
    cluster(firm_id state)
```

---

## R 核心模板

### DID / 事件研究

```r
library(fixest)
library(did)
library(HonestDiD)

# ══════════════════════════════════════════════════
# 1. 基准 DID (TWFE)
# ══════════════════════════════════════════════════
m_base <- feols(log_wage ~ treated_post + age + edu | id + year,
                data = df, cluster = ~firm_id)

# ══════════════════════════════════════════════════
# 2. 事件研究 (Sun-Abraham via fixest)
# ══════════════════════════════════════════════════
m_es <- feols(log_wage ~ sunab(first_treat_year, year) | id + year,
              data = df, cluster = ~firm_id)
iplot(m_es)  # 事件研究图

# ══════════════════════════════════════════════════
# 3. Callaway & Sant'Anna
# ══════════════════════════════════════════════════
library(did)
cs_out <- att_gt(
  yname = "log_wage",
  tname = "year",
  idname = "id",
  gname = "first_treat_year",
  xformla = ~ age + edu,
  data = df,
  control_group = "nevertreated",
  est_method = "dr"
)
summary(cs_out)
ggdid(cs_out)

# ══════════════════════════════════════════════════
# 4. 渐进控制表
# ══════════════════════════════════════════════════
m1 <- feols(log_wage ~ treated_post, data = df, cluster = ~firm_id)
m2 <- feols(log_wage ~ treated_post + age + edu, data = df, cluster = ~firm_id)
m3 <- feols(log_wage ~ treated_post + age + edu + tenure | industry + year, data = df, cluster = ~firm_id)
m4 <- feols(log_wage ~ treated_post + age + edu + tenure | id + year, data = df, cluster = ~firm_id)
m5 <- feols(log_wage ~ treated_post + age + edu + tenure | id + year + industry^year, data = df, cluster = ~firm_id)

etable(m1, m2, m3, m4, m5,
       tex = TRUE, file = "tables/table2_main.tex",
       title = "Main Results",
       notes = "Clustered SE at firm level.")

# ══════════════════════════════════════════════════
# 5. HonestDiD 敏感性
# ══════════════════════════════════════════════════
library(HonestDiD)
# 从事件研究中提取系数和方差-协方差矩阵
betahat <- coef(m_es)
sigma <- vcov(m_es)

# 相对幅度敏感性
honest_result <- HonestDiD::createSensitivityResults_relativeMagnitudes(
  betahat = betahat, sigma = sigma,
  numPrePeriods = 4, numPostPeriods = 3,
  Mbarvec = seq(0, 2, by = 0.5)
)
```

### IV / 2SLS

```r
library(fixest)

# 2SLS with fixed effects
m_iv <- feols(log_wage ~ age + age_sq | state + year | edu_years ~ college_proximity,
              data = df, cluster = ~state)
summary(m_iv, stage = 1:2)  # 报告两阶段
fitstat(m_iv, "ivf")  # 第一阶段F
```

### RDD

```r
library(rdrobust)
library(rddensity)

# Sharp RD
rd_result <- rdrobust(y = df$outcome, x = df$running_var, c = 0, cluster = df$school_id)
summary(rd_result)
rdplot(y = df$outcome, x = df$running_var, c = 0)

# 密度检验
density_test <- rddensity(X = df$running_var, c = 0)
summary(density_test)
```

### Quarto 渲染

```yaml
# _quarto.yml
project:
  type: default
  output-dir: output

format:
  pdf:
    documentclass: article
    geometry: margin=1in
  html:
    toc: true

execute:
  echo: true
  warning: false
```

```r
#| label: tbl-main
#| tbl-cap: "Main Results"
etable(m1, m2, m3, m4, m5, markdown = TRUE)
```

---

## 关键 Stata 包安装

```stata
* 必须安装
ssc install reghdfe
ssc install ftools
ssc install estout
ssc install ivreghdfe
ssc install rdrobust
ssc install rddensity
ssc install csdid
ssc install did_multiplegt
ssc install eventstudyinteract
ssc install psacalc
ssc install bacondecomp

* 可选
ssc install coefplot
ssc install binscatter
ssc install synth
ssc install sdid
```

## 关键 R 包安装

```r
install.packages(c(
  "fixest", "did", "HonestDiD", "synthdid",
  "rdrobust", "rddensity",
  "modelsummary", "marginaleffects",
  "ggplot2", "patchwork",
  "quarto"
))
```
