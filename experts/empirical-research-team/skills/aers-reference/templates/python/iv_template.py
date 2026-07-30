"""
IV / 2SLS 代码模板
基于 AERS Full Empirical Analysis Skill (Python)
技术栈: linearmodels + pyfixest + statsmodels
"""

import pandas as pd
import numpy as np
from linearmodels.iv import IV2SLS
import pyfixest as pf
import matplotlib.pyplot as plt


def run_iv_analysis(df, outcome, endogenous, instrument, controls, cluster_var, unit_id=None, time_id=None):
    """
    完整 IV/2SLS 分析流水线
    
    Parameters
    ----------
    df : DataFrame
    outcome : str — 因变量
    endogenous : str — 内生变量
    instrument : str — 工具变量
    controls : list[str] — 外生控制变量
    cluster_var : str — 聚类变量
    unit_id : str — 面板个体ID（可选）
    time_id : str — 面板时间ID（可选）
    """
    
    results = {}
    ctrl_str = " + ".join(controls)
    
    # ═══════════════════════════════════════════════════
    # 1. 第一阶段回归
    # ═══════════════════════════════════════════════════
    
    first_stage_formula = f"{endogenous} ~ {instrument} + {ctrl_str}"
    if unit_id and time_id:
        first_stage_formula += f" | {unit_id} + {time_id}"
    
    m_first = pf.feols(first_stage_formula, data=df, vcov={"CRV1": cluster_var})
    
    # 第一阶段 F 统计量
    f_stat = m_first.wald_test(f"{instrument} = 0")
    results["first_stage"] = m_first
    results["first_stage_F"] = f_stat
    
    # 判断工具强度
    # F >= 10: 可用OLS推断
    # F >= 23: 可用AR等价推断（Stock-Yogo 5%临界值）
    # F < 10: 弱工具变量，需要AR/CLR推断
    
    # ═══════════════════════════════════════════════════
    # 2. 简化式回归（Reduced Form）
    # ═══════════════════════════════════════════════════
    
    rf_formula = f"{outcome} ~ {instrument} + {ctrl_str}"
    if unit_id and time_id:
        rf_formula += f" | {unit_id} + {time_id}"
    
    m_rf = pf.feols(rf_formula, data=df, vcov={"CRV1": cluster_var})
    results["reduced_form"] = m_rf
    
    # ═══════════════════════════════════════════════════
    # 3. 2SLS 估计
    # ═══════════════════════════════════════════════════
    
    # 使用 linearmodels
    iv_formula = f"{outcome} ~ 1 + {ctrl_str} + [{endogenous} ~ {instrument}]"
    m_iv = IV2SLS.from_formula(iv_formula, data=df).fit(
        cov_type="clustered", clusters=df[cluster_var]
    )
    results["iv_2sls"] = m_iv
    
    # ═══════════════════════════════════════════════════
    # 4. OLS 对比（忽略内生性）
    # ═══════════════════════════════════════════════════
    
    ols_formula = f"{outcome} ~ {endogenous} + {ctrl_str}"
    if unit_id and time_id:
        ols_formula += f" | {unit_id} + {time_id}"
    
    m_ols = pf.feols(ols_formula, data=df, vcov={"CRV1": cluster_var})
    results["ols"] = m_ols
    
    # ═══════════════════════════════════════════════════
    # 5. IV 三联表（Pattern E）
    # ═══════════════════════════════════════════════════
    
    # 第一阶段 | 简化式 | 2SLS
    # 输出为一个表格
    
    # ═══════════════════════════════════════════════════
    # 6. 第一阶段散点图
    # ═══════════════════════════════════════════════════
    
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df[instrument], df[endogenous], alpha=0.3, s=10)
    
    # 添加拟合线
    z = np.polyfit(df[instrument].values, df[endogenous].values, 1)
    p = np.poly1d(z)
    x_range = np.linspace(df[instrument].min(), df[instrument].max(), 100)
    ax.plot(x_range, p(x_range), "r-", linewidth=2)
    
    ax.set_xlabel(f"Instrument: {instrument}")
    ax.set_ylabel(f"Endogenous: {endogenous}")
    ax.set_title(f"First Stage: F = {f_stat:.1f}")
    plt.tight_layout()
    plt.savefig("figures/fig_first_stage.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig_first_stage.pdf", bbox_inches="tight")
    plt.close()
    
    # ═══════════════════════════════════════════════════
    # 7. 诊断检验
    # ═══════════════════════════════════════════════════
    
    diagnostics = {
        "first_stage_F": f_stat,
        "weak_iv": f_stat < 10,
        "iv_coef": float(m_iv.params[endogenous]),
        "ols_coef": float(m_ols.coef().iloc[0]),
        "hausman_direction": "IV > OLS" if float(m_iv.params[endogenous]) > float(m_ols.coef().iloc[0]) else "IV < OLS",
    }
    results["diagnostics"] = diagnostics
    
    return results


# ═══════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    df = pd.read_csv("data/panel_data.csv")
    
    results = run_iv_analysis(
        df=df,
        outcome="log_wage",
        endogenous="edu_years",
        instrument="college_proximity",
        controls=["age", "age_sq", "experience"],
        cluster_var="state",
        unit_id="person_id",
        time_id="year",
    )
    
    print(f"OLS 估计: {results['ols'].coef().iloc[0]:.4f}")
    print(f"IV 估计: {results['iv_2sls'].params.iloc[-1]:.4f}")
    print(f"第一阶段 F: {results['diagnostics']['first_stage_F']:.1f}")
