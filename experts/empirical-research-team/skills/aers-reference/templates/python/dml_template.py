"""
DML (Double/Debiased Machine Learning) 代码模板
基于 AERS Full Empirical Analysis Skill (Mode B)
技术栈: econml + sklearn + matplotlib
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
import matplotlib.pyplot as plt


def run_dml_analysis(df, outcome, treatment, covariates, heterogeneity_vars=None):
    """
    完整 DML / ML因果推断流水线

    Parameters
    ----------
    df : DataFrame
    outcome : str — 因变量
    treatment : str — 处理变量（二元）
    covariates : list[str] — 协变量/混淆变量
    heterogeneity_vars : list[str] — 异质性变量（用于CATE估计）
    """

    from econml.dml import LinearDML, CausalForestDML
    from econml.metalearners import SLearner, TLearner, XLearner
    from econml.dr import DRLearner

    results = {}
    Y = df[outcome].values
    T = df[treatment].values
    X = df[covariates].values

    if heterogeneity_vars:
        W = df[heterogeneity_vars].values
    else:
        W = X

    # ═══════════════════════════════════════════════════
    # 1. 干扰学习器栈定义
    # ═══════════════════════════════════════════════════

    model_y = GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42)
    model_t = GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42)

    # ═══════════════════════════════════════════════════
    # 2. ATE 估计器竞赛
    # ═══════════════════════════════════════════════════

    estimators = {}

    # 2a. LinearDML
    dml = LinearDML(model_y=model_y, model_t=model_t, cv=5, random_state=42)
    dml.fit(Y, T, X=W, W=X)
    ate_dml = dml.ate(X=W)
    ci_dml = dml.ate_interval(X=W, alpha=0.05)
    estimators["LinearDML"] = {"ate": float(ate_dml), "ci": [float(ci_dml[0]), float(ci_dml[1])]}

    # 2b. CausalForestDML
    cf = CausalForestDML(model_y=model_y, model_t=model_t, n_estimators=200, random_state=42)
    cf.fit(Y, T, X=W, W=X)
    ate_cf = cf.ate(X=W)
    ci_cf = cf.ate_interval(X=W, alpha=0.05)
    estimators["CausalForest"] = {"ate": float(ate_cf), "ci": [float(ci_cf[0]), float(ci_cf[1])]}

    # 2c. DRLearner
    dr = DRLearner(model_regression=model_y, model_propensity=model_t, cv=5, random_state=42)
    dr.fit(Y, T, X=W, W=X)
    ate_dr = dr.ate(X=W)
    ci_dr = dr.ate_interval(X=W, alpha=0.05)
    estimators["DRLearner"] = {"ate": float(ate_dr), "ci": [float(ci_dr[0]), float(ci_dr[1])]}

    # 2d. S-Learner
    sl = SLearner(overall_model=GradientBoostingRegressor(n_estimators=200, max_depth=4))
    sl.fit(Y, T, X=X)
    ate_sl = float(np.mean(sl.effect(X)))
    estimators["S-Learner"] = {"ate": ate_sl, "ci": None}

    # 2e. T-Learner
    tl = TLearner(models=[
        GradientBoostingRegressor(n_estimators=200, max_depth=4),
        GradientBoostingRegressor(n_estimators=200, max_depth=4),
    ])
    tl.fit(Y, T, X=X)
    ate_tl = float(np.mean(tl.effect(X)))
    estimators["T-Learner"] = {"ate": ate_tl, "ci": None}

    results["ate_comparison"] = estimators

    # ═══════════════════════════════════════════════════
    # 3. ATE 竞赛表（ML因果的"Table 2"）
    # ═══════════════════════════════════════════════════

    print("\n" + "="*60)
    print("ML Causal Estimator Comparison (ATE)")
    print("="*60)
    print(f"{'Estimator':<18} {'ATE':>8} {'95% CI':>20}")
    print("-"*60)
    for name, est in estimators.items():
        ci_str = f"[{est['ci'][0]:.4f}, {est['ci'][1]:.4f}]" if est["ci"] else "N/A"
        print(f"{name:<18} {est['ate']:>8.4f} {ci_str:>20}")

    # ═══════════════════════════════════════════════════
    # 4. CATE 分布（异质性处理效应）
    # ═══════════════════════════════════════════════════

    cate = cf.effect(X=W)
    results["cate"] = cate

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # CATE 直方图
    ax = axes[0]
    ax.hist(cate, bins=30, color="#378ADD", alpha=0.7, edgecolor="white")
    ax.axvline(x=np.mean(cate), color="red", linestyle="--", linewidth=2, label=f"Mean = {np.mean(cate):.4f}")
    ax.axvline(x=0, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel("CATE (Individual Treatment Effect)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Heterogeneous Treatment Effects")
    ax.legend()

    # CATE 按协变量分位数
    if heterogeneity_vars and len(heterogeneity_vars) > 0:
        ax = axes[1]
        het_var = heterogeneity_vars[0]
        het_values = df[het_var].values
        quartiles = pd.qcut(het_values, 4, labels=["Q1", "Q2", "Q3", "Q4"])
        cate_by_q = pd.DataFrame({"cate": cate, "quartile": quartiles}).groupby("quartile")["cate"].mean()

        ax.bar(cate_by_q.index, cate_by_q.values, color="#1D9E75", alpha=0.8)
        ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
        ax.set_xlabel(f"Quartiles of {het_var}")
        ax.set_ylabel("Mean CATE")
        ax.set_title(f"CATE by {het_var} Quartile")

    plt.tight_layout()
    plt.savefig("figures/fig_cate.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig_cate.pdf", bbox_inches="tight")
    plt.close()

    # ═══════════════════════════════════════════════════
    # 5. 策略学习（最优处理分配）
    # ═══════════════════════════════════════════════════

    from econml.policy import DRPolicyTree

    policy = DRPolicyTree(max_depth=3, min_samples_leaf=50)
    policy.fit(Y, T, X=W, W=X)

    # 策略值
    policy_value = policy.policy_value(Y, T, X=W, W=X)
    results["policy_value"] = float(policy_value)

    # 最优分配规则
    optimal_treatment = policy.predict(W)
    results["treat_share"] = float(np.mean(optimal_treatment))

    # ═══════════════════════════════════════════════════
    # 6. 诊断检验
    # ═══════════════════════════════════════════════════

    # 重叠检查（倾向得分分布）
    from sklearn.linear_model import LogisticRegression
    ps_model = LogisticRegression(max_iter=1000).fit(X, T)
    ps = ps_model.predict_proba(X)[:, 1]

    results["propensity_min"] = float(np.min(ps))
    results["propensity_max"] = float(np.max(ps))
    results["overlap_violation"] = float(np.mean((ps < 0.05) | (ps > 0.95)))

    if results["overlap_violation"] > 0.1:
        print("⚠️ 警告：>10%样本的倾向得分在极端区域，重叠假设可能不满足")

    return results


if __name__ == "__main__":
    df = pd.read_csv("data/observational_data.csv")
    results = run_dml_analysis(
        df=df,
        outcome="log_earnings",
        treatment="job_training",
        covariates=["age", "education", "experience", "married", "black", "hispanic"],
        heterogeneity_vars=["age", "education"],
    )
    print(f"\nATE比较: {results['ate_comparison']}")
    print(f"最优策略处理比例: {results['treat_share']:.1%}")
