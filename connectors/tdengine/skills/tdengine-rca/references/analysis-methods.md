# Root Cause Analysis Methods

Use these methods to select tests that distinguish competing root-cause
hypotheses. Start with dimensional attribution to locate the affected segment,
then use metric attribution and time-series evidence to identify plausible
drivers. Do not treat association as proof of causation.

## 1. Attribution Analysis

### 1.1 Dimensional Attribution

Decompose a metric change across dimensions and quantify each segment's
contribution. Common dimensions include:

- levels in the asset hierarchy;
- time buckets such as year, month, day, and hour;
- tag and categorical attributes;
- numeric ranges or operating-state bands.

Choose a decomposition that matches the metric definition:

- **Additive attribution:** `Y = A + B + C`, such as total electricity use as
  the sum of area-level use. A Pareto ranking can identify the segments
  responsible for the first 80% of the change.
- **Ratio attribution:** `Y = A / B`, such as water cut as produced water
  divided by total liquid production. Analyze numerator and denominator
  separately before interpreting the ratio.

### 1.2 Metric Attribution

Assess how related metrics contribute to a change in the target metric:

- **Multiplicative relationship:** `Y = A x B`, such as electrical power from
  voltage and current.
- **Regression relationship:** `Y = beta_0 + beta_1*x_1 + ... + beta_n*x_n`.
  Fit an appropriate model, inspect residuals, and use feature importance or
  SHAP values only after validating model quality.

## 2. Causal Inference

Causal methods require assumptions that observations alone may not prove.
State the assumptions, confounders, sample requirements, and uncertainty.

### 2.1 Constraint-Based Discovery

| Method | Principle | Suitable use |
|---|---|---|
| PC algorithm | Removes edges using conditional-independence tests | Low-dimensional sensor groups |
| FCI algorithm | Extends PC to account for possible latent confounders | Complex production lines with hidden variables |

### 2.2 Score-Based Discovery

| Method | Principle | Suitable use |
|---|---|---|
| Bayesian structure search | Searches graph structures with scores such as BIC, optionally using MCMC | Small or medium sensor networks |
| Greedy Equivalence Search (GES) | Combines forward and backward greedy graph search | Approximately stationary production processes |

### 2.3 Time-Series Causal Methods

| Method | Principle | Suitable use |
|---|---|---|
| Granger causality | Tests whether the history of X improves prediction of Y | Directional screening in regularly sampled time series |
| Transfer entropy | Measures directional information transfer from X to Y | Nonlinear signals such as vibration or current harmonics |
| Dynamic causal modeling (DCM) | Combines differential equations with Bayesian inference | Continuous-time systems with a defensible mechanism model |

Granger causality and transfer entropy are directional evidence, not automatic
proof of a physical cause. Check stationarity, sampling cadence, lag selection,
and common drivers.

### 2.4 Intervention-Based Inference

| Method | Principle | Suitable use |
|---|---|---|
| Regression discontinuity design (RDD) | Compares observations around an intervention threshold | Threshold-triggered changes |
| Difference in differences (DID) | Compares treated and control groups before and after an intervention | Fleet firmware or configuration rollouts |
| Instrumental variables (IV) | Uses a variable related to treatment but not directly to the outcome | Confounded effects with a defensible instrument |

## 3. Machine Learning Methods

| Method | Suitable use | Strength | Limitation |
|---|---|---|---|
| Correlation analysis | Fast screening of metrics related to the target | Simple and interpretable | Correlation is not causation and Pearson correlation is linear |
| PCA or factor analysis | Reducing high-dimensional sensor data | Reveals dominant variation and removes redundancy | Components can be difficult to map to physical mechanisms |
| Dynamic time warping (DTW) | Finding similar historical episodes | Uses sequence shape despite timing differences | Depends on representative history and distance choices |
| Causal forests | Estimating heterogeneous conditional treatment effects | Supports nonlinearities and interactions | Sensitive to data volume, treatment definition, and tuning |
| Counterfactual reasoning | Estimating how an outcome would change without a suspected driver | Matches hypothesis-verification reasoning | Depends on a validated predictive or structural model |

## 4. Industrial Time-Series Methods

### 4.1 Same-Time Historical Comparison

- Compare the incident period with the same clock or production period over
  the previous N days.
- Distinguish a one-off excursion from periodic degradation.
- Match operating state before calculating baseline statistics.

### 4.2 Recipe or Batch Comparison

- Select historical runs with the same recipe and comparable process settings.
- Compare control stability and output quality.
- Test whether the anomaly is specific to a new recipe or batch condition.

### 4.3 Rolling Statistical Drift

- Compare the pre-incident and incident distributions using rolling mean,
  standard deviation, kurtosis, and rate of change.
- Use a Z-score, Kolmogorov-Smirnov test, or baseline quantile threshold.
- Pass the pre-incident series explicitly as `baseline` to
  `zscore_anomaly_mask()` and `rolling_drift()`. Computing the reference mean
  and variance from the incident itself can hide a sustained level shift.
- When the historical baseline has zero variance, `rolling_drift()` reports a
  finite difference normalized by the baseline magnitude rather than a
  standard-deviation score.
- Example: a fivefold increase in valve-signal variance can support a control
  oscillation hypothesis when cadence and operating state are unchanged.

### 4.4 State-Duration Distribution

- Measure the duration of each contiguous operating state.
- Compare durations with historical P10, P50, and P90 values.
- Example: an average running state of 200 ms against a historical value above
  five minutes supports a state-chatter hypothesis.

### 4.5 Multivariate Phase Alignment

- Align state transitions with measurements, actuator commands, and alarms.
- Measure lead and lag instead of relying on visual proximity.
- Example: a measurement rising 100 ms after a `false` to `true` command is
  consistent with, but does not alone prove, command-to-response direction.

### 4.6 Control-Loop Performance

- Integral absolute error: `IAE = integral(abs(setpoint - measurement)) dt`.
- Overshoot.
- Settling time.
- Actuator saturation and sustained oscillation.

A mismatch in PID parameters may produce oscillation and a protective trip, but
verify the setpoint, measurement, controller output, limits, and operating mode.

### 4.7 Event-Sequence Pattern Mining

- Extract the ordered event sequence before the incident, for example the
  preceding five minutes.
- Compare it with normal or successfully completed sequences.
- Identify missing, repeated, reordered, or unusually delayed transitions.

### 4.8 Frequency-Domain Analysis

- Apply FFT or wavelet analysis only when cadence and sample density support it.
- Look for persistent frequencies and sidebands around the incident.
- Example: a 2 Hz component may be consistent with power ripple or a PLC scan
  cycle, but requires corroborating electrical or control evidence.

### 4.9 Data-Quality Screening

Check for interrupted ingestion; timestamp jumps, duplicates, or reordering;
groups of fields becoming null together; flat lines; resets; unit changes; and
cadence changes. Separate a physical fault from a communication, mapping, or
ingestion artifact before ranking equipment hypotheses.

### 4.10 Environment, Shift, and Operator Association

- Test whether incidents cluster by environmental condition, shift, operator,
  recipe, maintenance state, or production mode.
- Compare exposure counts as well as incident counts to avoid base-rate errors.
- Report association as a contributing condition until a mechanism or
  intervention supplies stronger evidence.
