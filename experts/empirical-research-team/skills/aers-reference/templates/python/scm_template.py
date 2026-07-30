"""
SCM (Synthetic Control Method) 代码模板
基于 AERS Full Empirical Analysis Skill
技术栈: pysynth / synthdid + matplotlib
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def run_scm_analysis(df, outcome, unit_id, time_id, treated_unit, treatment_time, donor_pool=None):
    """
    完整 SCM/SDID 分析流水线

    Parameters
    ----------
    df : DataFrame — 面板数据（长格式）
    outcome : str — 因变量列名
    unit_id : str — 单位 ID 列名
    time_id : str — 时间列名
    treated_unit : str/int — 处理单位 ID
    treatment_time : int — 处理发生的时间
    donor_pool : list — 供体池单位列表（可选，默认全部非处理单位）
    """

    results = {}

    # ═══════════════════════════════════════════════════
    # 1. 数据准备
    # ═══════════════════════════════════════════════════

    if donor_pool is None:
        donor_pool = [u for u in df[unit_id].unique() if u != treated_unit]

    # 处理单位数据
    treated_data = df[df[unit_id] == treated_unit].set_index(time_id)[outcome]

    # 供体池数据（宽格式矩阵）
    donor_df = df[df[unit_id].isin(donor_pool)].pivot(
        index=time_id, columns=unit_id, values=outcome
    )

    # 分割前期/后期
    pre_periods = [t for t in treated_data.index if t < treatment_time]
    post_periods = [t for t in treated_data.index if t >= treatment_time]

    results["n_pre_periods"] = len(pre_periods)
    results["n_post_periods"] = len(post_periods)
    results["n_donors"] = len(donor_pool)

    # ═══════════════════════════════════════════════════
    # 2. 合成控制权重估计
    # ═══════════════════════════════════════════════════

    # 前期数据
    Y1_pre = treated_data[pre_periods].values  # 处理单位前期
    Y0_pre = donor_df.loc[pre_periods].values  # 供体池前期

    # 约束优化求权重：min ||Y1 - Y0 @ w||^2, s.t. w >= 0, sum(w) = 1
    from scipy.optimize import minimize

    def objective(w):
        synthetic = Y0_pre @ w
        return np.sum((Y1_pre - synthetic) ** 2)

    n_donors = Y0_pre.shape[1]
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1},  # 权重和=1
    ]
    bounds = [(0, 1)] * n_donors  # 权重非负
    w0 = np.ones(n_donors) / n_donors  # 初始等权

    result = minimize(objective, w0, bounds=bounds, constraints=constraints, method="SLSQP")
    weights = result.x

    results["weights"] = dict(zip(donor_pool, weights))
    results["top_donors"] = sorted(results["weights"].items(), key=lambda x: -x[1])[:5]

    # ═══════════════════════════════════════════════════
    # 3. 合成控制预测
    # ═══════════════════════════════════════════════════

    all_periods = sorted(treated_data.index)
    synthetic_outcome = donor_df.loc[all_periods].values @ weights

    results["treated_series"] = treated_data[all_periods].values
    results["synthetic_series"] = synthetic_outcome
    results["gap"] = results["treated_series"] - results["synthetic_series"]

    # 处理效应 = 后期平均缺口
    post_gap = results["gap"][len(pre_periods):]
    results["att"] = np.mean(post_gap)
    results["att_pct"] = results["att"] / np.mean(results["synthetic_series"][len(pre_periods):]) * 100

    # 前期拟合质量
    pre_gap = results["gap"][:len(pre_periods)]
    results["pre_rmspe"] = np.sqrt(np.mean(pre_gap ** 2))
    results["post_rmspe"] = np.sqrt(np.mean(post_gap ** 2))
    results["rmspe_ratio"] = results["post_rmspe"] / results["pre_rmspe"]

    # ═══════════════════════════════════════════════════
    # 4. 合成控制轨迹图 + 缺口图
    # ═══════════════════════════════════════════════════

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 轨迹图
    ax = axes[0]
    ax.plot(all_periods, results["treated_series"], "b-", linewidth=2, label="Treated")
    ax.plot(all_periods, results["synthetic_series"], "r--", linewidth=2, label="Synthetic Control")
    ax.axvline(x=treatment_time, color="gray", linestyle=":", linewidth=1)
    ax.set_ylabel(outcome)
    ax.set_title("Synthetic Control: Treated vs Synthetic")
    ax.legend()

    # 缺口图
    ax = axes[1]
    ax.plot(all_periods, results["gap"], "k-", linewidth=2)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
    ax.axvline(x=treatment_time, color="gray", linestyle=":", linewidth=1)
    ax.fill_between(all_periods[len(pre_periods):], results["gap"][len(pre_periods):],
                    alpha=0.3, color="blue", label=f"ATT = {results['att']:.3f}")
    ax.set_xlabel("Time")
    ax.set_ylabel("Gap (Treated - Synthetic)")
    ax.set_title("Treatment Effect (Gap)")
    ax.legend()

    plt.tight_layout()
    plt.savefig("figures/fig_scm.png", dpi=300, bbox_inches="tight")
    plt.savefig("figures/fig_scm.pdf", bbox_inches="tight")
    plt.close()

    # ═══════════════════════════════════════════════════
    # 5. 安慰剂检验（逐一排列）
    # ═══════════════════════════════════════════════════

    placebo_ratios = []
    for placebo_unit in donor_pool:
        try:
            placebo_treated = df[df[unit_id] == placebo_unit].set_index(time_id)[outcome]
            placebo_donors = [u for u in donor_pool if u != placebo_unit] + [treated_unit]
            placebo_donor_df = df[df[unit_id].isin(placebo_donors)].pivot(
                index=time_id, columns=unit_id, values=outcome
            )

            Y1_p = placebo_treated[pre_periods].values
            Y0_p = placebo_donor_df.loc[pre_periods].values

            def obj_p(w):
                return np.sum((Y1_p - Y0_p @ w) ** 2)

            n_p = Y0_p.shape[1]
            res_p = minimize(obj_p, np.ones(n_p)/n_p,
                           bounds=[(0,1)]*n_p,
                           constraints=[{"type":"eq","fun":lambda w:np.sum(w)-1}],
                           method="SLSQP")

            synth_p = placebo_donor_df.loc[all_periods].values @ res_p.x
            gap_p = placebo_treated[all_periods].values - synth_p
            pre_rmspe_p = np.sqrt(np.mean(gap_p[:len(pre_periods)]**2))
            post_rmspe_p = np.sqrt(np.mean(gap_p[len(pre_periods):]**2))

            if pre_rmspe_p > 0:
                placebo_ratios.append(post_rmspe_p / pre_rmspe_p)
        except Exception:
            pass

    # p值 = 处理单位的RMSPE比在安慰剂分布中的排位
    results["placebo_pvalue"] = np.mean(
        np.array(placebo_ratios) >= results["rmspe_ratio"]
    )

    return results


if __name__ == "__main__":
    df = pd.read_csv("data/scm_panel.csv")
    results = run_scm_analysis(
        df=df, outcome="gdp_pc", unit_id="state",
        time_id="year", treated_unit="California", treatment_time=1989,
    )
    print(f"ATT: {results['att']:.3f}")
    print(f"前期RMSPE: {results['pre_rmspe']:.4f}")
    print(f"安慰剂p值: {results['placebo_pvalue']:.3f}")
    print(f"Top donors: {results['top_donors']}")
