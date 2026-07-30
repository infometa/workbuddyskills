"""
DID / 事件研究代码模板
基于 AERS Full Empirical Analysis Skill (Python)
技术栈: pyfixest + pandas + matplotlib
"""

import pandas as pd
import numpy as np
import pyfixest as pf
import matplotlib.pyplot as plt


def run_did_analysis(df, outcome, treatment, unit_id, time_id, first_treat_col, cluster_var, controls=None):
    """
    完整 DID/事件研究分析流水线
    
    Parameters
    ----------
    df : DataFrame — 面板数据
    outcome : str — 因变量列名
    treatment : str — 处理变量列名（0/1）
    unit_id : str — 个体 ID 列名
    time_id : str — 时间 ID 列名
    first_treat_col : str — 首次处理时间列名（用于交错 DID）
    cluster_var : str — 聚类变量列名
    controls : list[str] — 控制变量列表（可选）
    
    Returns
    -------
    dict — 包含估计结果、表格、图形路径
    """
    
    results = {}
    ctrl_str = " + ".join(controls) if controls else ""
    
    # ═══════════════════════════════════════════════════
    # 1. 2×2 DID（基准）
    # ═══════════════════════════════════════════════════
    
    if ctrl_str:
        formula_base = f"{outcome} ~ {treatment} + {ctrl_str} | {unit_id} + {time_id}"
    else:
        formula_base = f"{outcome} ~ {treatment} | {unit_id} + {time_id}"
    
    m_base = pf.feols(formula_base, data=df, vcov={"CRV1": cluster_var})
    results["baseline"] = m_base
    
    # ═══════════════════════════════════════════════════
    # 2. 事件研究（Sun-Abraham）
    # ═══════════════════════════════════════════════════
    
    # 构建相对时间
    df["rel_time"] = df[time_id] - df[first_treat_col]
    
    # Sun-Abraham 事件研究
    es_formula = f"{outcome} ~ sunab({first_treat_col}, {time_id}) | {unit_id} + {time_id}"
    m_es = pf.feols(es_formula, data=df, vcov={"CRV1": cluster_var})
    results["event_study"] = m_es
    
    # ═══════════════════════════════════════════════════
    # 3. 预趋势检验
    # ═══════════════════════════════════════════════════
    
    # 提取 pre-period 系数，联合F检验是否 = 0
    # pre_coefs = [c for c in m_es.coef().index if c contains negative rel_time]
    # Wald test for joint significance
    
    # ═══════════════════════════════════════════════════
    # 4. 渐进控制表（Table 2）
    # ═══════════════════════════════════════════════════
    
    m1 = pf.feols(f"{outcome} ~ {treatment}", data=df, vcov={"CRV1": cluster_var})
    m2 = pf.feols(f"{outcome} ~ {treatment} + {ctrl_str}", data=df, vcov={"CRV1": cluster_var}) if ctrl_str else m1
    m3 = pf.feols(f"{outcome} ~ {treatment} + {ctrl_str} | {time_id}", data=df, vcov={"CRV1": cluster_var})
    m4 = pf.feols(f"{outcome} ~ {treatment} + {ctrl_str} | {unit_id}", data=df, vcov={"CRV1": cluster_var})
    m5 = pf.feols(f"{outcome} ~ {treatment} + {ctrl_str} | {unit_id} + {time_id}", data=df, vcov={"CRV1": cluster_var})
    
    models = [m1, m2, m3, m4, m5]
    
    # 导出表格
    pf.etable(models, type="tex", file="tables/table2_main.tex")
    pf.etable(models, type="xlsx", file="tables/table2_main.xlsx")
    
    results["table2_models"] = models
    
    # ═══════════════════════════════════════════════════
    # 5. 事件研究图（Figure 2）
    # ═══════════════════════════════════════════════════
    
    fig, ax = plt.subplots(figsize=(8, 5))
    pf.iplot(m_es, ax=ax)
    ax.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
    ax.axvline(x=-0.5, color="red", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.set_xlabel("Relative Time to Treatment")
    ax.set_ylabel(f"Effect on {outcome}")
    ax.set_title("Event Study: Dynamic Treatment Effects")
    plt.tight_layout()
    plt.savefig("figures/fig2_event_study.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig2_event_study.pdf", bbox_inches="tight")
    plt.close()
    
    results["event_study_fig"] = "figures/fig2_event_study.png"
    
    # ═══════════════════════════════════════════════════
    # 6. 趋势/动机图（Figure 1）
    # ═══════════════════════════════════════════════════
    
    trend = df.groupby([time_id, treatment])[outcome].mean().reset_index()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    for grp, label in [(1, "Treatment"), (0, "Control")]:
        sub = trend[trend[treatment] == grp]
        ax.plot(sub[time_id], sub[outcome], marker="o", label=label)
    
    ax.set_xlabel("Year")
    ax.set_ylabel(f"Mean {outcome}")
    ax.set_title("Trend: Treatment vs Control")
    ax.legend()
    plt.tight_layout()
    plt.savefig("figures/fig1_trend.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig1_trend.pdf", bbox_inches="tight")
    plt.close()
    
    results["trend_fig"] = "figures/fig1_trend.png"
    
    return results


# ═══════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    # 加载数据
    df = pd.read_csv("data/panel_data.csv")
    
    # 运行完整 DID 分析
    results = run_did_analysis(
        df=df,
        outcome="log_wage",
        treatment="treated_post",
        unit_id="worker_id",
        time_id="year",
        first_treat_col="first_treat_year",
        cluster_var="firm_id",
        controls=["age", "edu_years", "tenure"],
    )
    
    print(f"基准DID估计: {results['baseline'].coef().iloc[0]:.4f}")
    print(f"标准误(聚类): {results['baseline'].se().iloc[0]:.4f}")
