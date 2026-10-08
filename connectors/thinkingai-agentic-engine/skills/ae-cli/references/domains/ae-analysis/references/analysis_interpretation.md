# Analysis interpretation

Use this guide after obtaining comparable result data. It defines how to attribute metric changes and how to distinguish evidence from hypothesis.

## Absolute contribution for additive metrics

Use for counts and sums such as DAU, event count, orders, or payment amount:

```text
delta_total = total_comparison - total_baseline
delta_dimension_i = value_i_comparison - value_i_baseline
contribution_i = delta_dimension_i / delta_total * 100%
```

Rank by `abs(delta_dimension_i)`, preserving the sign. Do not rank primary drivers by relative growth `delta_dimension_i / value_i_baseline`; a tiny baseline can create a large percentage with little effect on the total.

Report each leading dimension's baseline, comparison, absolute delta, relative change, and contribution share. Treat a zero baseline as a new/lost dimension rather than an infinite growth rate.

## Ratio and conversion metrics

A ratio changes because subgroup rates change, subgroup composition changes, or both. First report numerator, denominator, and subgroup rates. When the user requests structural decomposition, use:

```text
rate_effect_i = weight_i_baseline * (rate_i_comparison - rate_i_baseline)
composition_effect_i = (weight_i_comparison - weight_i_baseline) * rate_i_baseline
```

Keep rate effects and composition effects separate. Do not apply additive-count contribution directly to conversion rates.

## Workflow and checks

1. Keep project, population, filters, dimensions, timezone, and aggregation identical across periods.
2. Prefer one query with comparison mode when the model supports it; otherwise run two definitions that differ only in time.
3. Compute deltas and sort by absolute contribution.
4. Verify additive dimension deltas reconcile with the total delta. If contribution shares differ from 100% by more than 5 percentage points, flag missing dimensions or inconsistent scope.
5. Call a cause “observed” only when the data directly demonstrates it. Product releases, campaigns, and incidents remain hypotheses until independently verified.

Skip cross-dimension contribution only when the user explicitly asks for percentage ranking or a single dimension's trend.
