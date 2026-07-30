"""
RDD (Regression Discontinuity Design) 代码模板
基于 AERS Full Empirical Analysis Skill (Python)
技术栈: rdrobust + rddensity + matplotlib
"""

import pandas as pd
import numpy as np
from rdrobust import rdrobust, rdplot, rdbwselect
from rddensity import rddensity, rdplotdensity
import matplotlib.pyplot as plt


def run_rdd_analysis(df, outcome, running_var, cutoff=0, fuzzy_var=None, cluster_var=None, covariates=None):
    """
    完整 RDD 分析流水线
    
    Parameters
    ----------
    df : DataFrame
    outcome : str — 因变量
    running_var : str — 运行变量
    cutoff : float — 断点（默认0）
    fuzzy_var : str — 模糊RD的处理变量（可选，None=Sharp RD）
    cluster_var : str — 聚类变量（可选）
    covariates : list[str] — 协变量（可选）
    """
    
    results = {}
    y = df[outcome].values
    x = df[running_var].values
    
    # ═══════════════════════════════════════════════════
    # 1. McCrary 密度检验（操纵检验）
    # ═══════════════════════════════════════════════════
    
    density_test = rddensity(X=x, c=cutoff)
    results["mccrary_pvalue"] = density_test.hat["p"]
    
    # 绘制密度图
    fig = rdplotdensity(density_test, X=x)
    plt.title(f"McCrary Density Test (p = {density_test.hat['p']:.3f})")
    plt.savefig("figures/fig_mccrary.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig_mccrary.pdf", bbox_inches="tight")
    plt.close()
    
    # 判断：p > 0.05 → 密度连续，无操纵证据
    if density_test.hat["p"] < 0.05:
        print("⚠️ 警告：McCrary检验拒绝H0，存在操纵嫌疑！")
    
    # ═══════════════════════════════════════════════════
    # 2. RD 估计（Sharp 或 Fuzzy）
    # ═══════════════════════════════════════════════════
    
    if fuzzy_var is not None:
        # Fuzzy RD
        fuzzy = df[fuzzy_var].values
        rd_result = rdrobust(y=y, x=x, c=cutoff, fuzzy=fuzzy,
                           cluster=df[cluster_var].values if cluster_var else None)
    else:
        # Sharp RD
        rd_result = rdrobust(y=y, x=x, c=cutoff,
                           cluster=df[cluster_var].values if cluster_var else None)
    
    results["rd_estimate"] = rd_result
    results["tau"] = rd_result.coef.iloc[0]  # 处理效应
    results["se"] = rd_result.se.iloc[0]
    results["pvalue"] = rd_result.pv.iloc[0]
    results["ci"] = [rd_result.ci.iloc[0, 0], rd_result.ci.iloc[0, 1]]
    results["bandwidth"] = rd_result.bws.iloc[0, 0]  # 最优带宽
    
    # ═══════════════════════════════════════════════════
    # 3. RD Plot（标准可视化）
    # ═══════════════════════════════════════════════════
    
    rdplot(y=y, x=x, c=cutoff,
           title="Regression Discontinuity Plot",
           x_label=f"Running Variable: {running_var}",
           y_label=f"Outcome: {outcome}")
    plt.savefig("figures/fig_rdplot.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig_rdplot.pdf", bbox_inches="tight")
    plt.close()
    
    results["rdplot_fig"] = "figures/fig_rdplot.png"
    
    # ═══════════════════════════════════════════════════
    # 4. 带宽敏感性检验
    # ═══════════════════════════════════════════════════
    
    # 最优带宽的 50%, 75%, 100%, 125%, 150%, 200%
    optimal_bw = results["bandwidth"]
    bw_multipliers = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
    sensitivity_results = []
    
    for mult in bw_multipliers:
        bw = optimal_bw * mult
        try:
            rd_bw = rdrobust(y=y, x=x, c=cutoff, h=bw,
                           fuzzy=df[fuzzy_var].values if fuzzy_var else None,
                           cluster=df[cluster_var].values if cluster_var else None)
            sensitivity_results.append({
                "bandwidth": bw,
                "multiplier": mult,
                "estimate": rd_bw.coef.iloc[0],
                "se": rd_bw.se.iloc[0],
                "pvalue": rd_bw.pv.iloc[0],
                "n_left": rd_bw.N_h.iloc[0],
                "n_right": rd_bw.N_h.iloc[1] if len(rd_bw.N_h) > 1 else None,
            })
        except Exception:
            pass
    
    results["bandwidth_sensitivity"] = sensitivity_results
    
    # 绘制带宽敏感性图
    fig, ax = plt.subplots(figsize=(8, 5))
    coefs = [r["estimate"] for r in sensitivity_results]
    ses = [r["se"] for r in sensitivity_results]
    bws = [r["multiplier"] for r in sensitivity_results]
    
    ax.errorbar(bws, coefs, yerr=[1.96*s for s in ses], fmt="o-", capsize=4)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
    ax.axvline(x=1.0, color="red", linestyle="--", linewidth=0.5, alpha=0.5, label="Optimal BW")
    ax.set_xlabel("Bandwidth Multiplier")
    ax.set_ylabel("RD Estimate")
    ax.set_title("Bandwidth Sensitivity")
    ax.legend()
    plt.tight_layout()
    plt.savefig("figures/fig_bw_sensitivity.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig_bw_sensitivity.pdf", bbox_inches="tight")
    plt.close()
    
    # ═══════════════════════════════════════════════════
    # 5. 协变量平衡检验（断点处协变量不应跳跃）
    # ═══════════════════════════════════════════════════
    
    if covariates:
        covariate_tests = []
        for cov in covariates:
            cov_y = df[cov].values
            try:
                rd_cov = rdrobust(y=cov_y, x=x, c=cutoff)
                covariate_tests.append({
                    "covariate": cov,
                    "estimate": rd_cov.coef.iloc[0],
                    "pvalue": rd_cov.pv.iloc[0],
                    "significant": rd_cov.pv.iloc[0] < 0.05,
                })
            except Exception:
                pass
        
        results["covariate_balance"] = covariate_tests
        # 如果任何协变量在断点处显著跳跃 → 问题信号
    
    # ═══════════════════════════════════════════════════
    # 6. 多项式阶数敏感性
    # ═══════════════════════════════════════════════════
    
    poly_results = []
    for p in [1, 2, 3]:
        try:
            rd_p = rdrobust(y=y, x=x, c=cutoff, p=p,
                          fuzzy=df[fuzzy_var].values if fuzzy_var else None)
            poly_results.append({
                "polynomial_order": p,
                "estimate": rd_p.coef.iloc[0],
                "se": rd_p.se.iloc[0],
            })
        except Exception:
            pass
    
    results["polynomial_sensitivity"] = poly_results
    
    return results


# ═══════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    df = pd.read_csv("data/rdd_data.csv")
    
    results = run_rdd_analysis(
        df=df,
        outcome="test_score",
        running_var="running_variable",
        cutoff=0,
        fuzzy_var=None,  # Sharp RD
        cluster_var="school_id",
        covariates=["age", "female", "income"],
    )
    
    print(f"RD 估计: {results['tau']:.4f} (SE: {results['se']:.4f})")
    print(f"McCrary p-value: {results['mccrary_pvalue']:.3f}")
    print(f"最优带宽: {results['bandwidth']:.2f}")
