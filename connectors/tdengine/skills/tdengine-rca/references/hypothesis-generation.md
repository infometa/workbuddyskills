# Root-Cause Hypothesis Generation

Generate hypotheses that make different, testable predictions. A list of
generic failure modes is insufficient: each hypothesis must identify the
incident, relevant observations, validation method, and decision threshold.

## Core Constraints

1. **Time anchor:** include the incident timestamp or range explicitly, for
   example `2026-01-15T10:00:00Z`.
2. **Adequate validation window:** use a validation-window half-width at least
   twice the exploratory-window half-width when data coverage allows it.
3. **Real attributes:** every entry in `related_columns` must exist in retrieved
   metadata. Do not invent names or use SQL expressions in this field.
4. **Testability:** every hypothesis must be verifiable with available data.
5. **Diversity:** cover distinct physical or operational mechanisms, such as
   sensing, drive train, control, structure, process input, environment, or data
   quality.
6. **Discrimination:** define evidence that would support, contradict, or leave
   the hypothesis inconclusive.

## Analysis Perspectives

Select perspectives relevant to the symptom. For a broad RCA, cover at least
five distinct perspectives when the available attributes support them.

### 1. Anomaly Detection

- abrupt sensor change, such as `abs(Z-score) > 3`;
- value outside a historical P5-P95 range;
- sensor flat line with near-zero variance;
- IQR-based outliers.

### 2. Time-Series Patterns

- moving-average or linear-slope trend;
- CUSUM or Bayesian change point;
- FFT or autocorrelation periodicity;
- rolling-window statistical drift.

### 3. Multivariate Association

- Pearson or Spearman correlation matrix;
- cross-correlation and lag analysis;
- phase alignment across related signals;
- partial correlation with known confounders.

### 4. Cross-Entity Comparison

- same-model peer equipment;
- the same asset at a comparable historical period;
- same recipe or batch;
- pre-maintenance versus post-maintenance behavior.

### 5. Causal and Event Evidence

- Granger causality screening;
- conditional probability;
- event-sequence pattern comparison;
- alarm-chain timing and ordering.

## Advanced Methods

### Same-Time Historical Comparison

Compare the incident period with the same operating or clock period over the
previous N days to distinguish an isolated event from periodic degradation.

### Statistical Drift Detection

Compare rolling mean, standard deviation, kurtosis, and rate of change before
and during the incident. Match operating state before interpreting a shift.

### State-Duration Anomaly

Calculate contiguous state durations and compare them with historical P10,
P50, and P90 values.

### Control-Loop Performance

- `IAE = integral(abs(setpoint - measurement)) dt`;
- overshoot;
- settling time;
- actuator saturation and sustained oscillation.

### Frequency-Domain Analysis

Use FFT or wavelet analysis to detect a persistent periodic component. Confirm
that cadence, sample density, and timestamp regularity support the method.

### Data-Quality Alternative

Test whether missing ingestion, timestamp jumps, simultaneous null fields,
mapping changes, resets, or flat lines can explain the apparent equipment fault.

## Hypothesis Output Schema

```json
[
  {
    "task_id": "H001",
    "hypothesis": "The symptom at {incident_time} may be caused by {mechanism}, which predicts {observable evidence}.",
    "related_columns": ["actual_column_1", "actual_column_2"],
    "validation_method": "Evaluate data within +/-{window} of T_acc={incident_time}, apply {operating filters}, calculate {statistic}, and support the hypothesis only if {threshold} is met.",
    "analysis_type": "anomaly detection and conditional threshold analysis"
  }
]
```

## Validation-Method Requirements

A useful `validation_method` includes:

1. **Time window:** explicit start and end.
2. **Operating filters:** conditions such as load, speed, state, or recipe.
3. **Statistic:** a named calculation or test.
4. **Decision threshold:** a numeric, testable criterion.
5. **Baseline:** the historical period, peer group, or predicted value used for
   comparison.
6. **Contradicting evidence:** a result that would reject the hypothesis.

### Example

```text
Center an eight-hour window on T_acc=2026-01-15T10:00:00Z (06:00-14:00).
Keep normal operating samples with wind speed from 6 to 14 m/s and exclude
stopped states. For each 15-minute interval, calculate the relative difference
between actual power and PREPOWER. Build a threshold from the P95 difference at
matched times over the preceding 30 days. Support the icing hypothesis if more
than 60% of the incident intervals exceed that threshold while temperature is
below 2 degrees C. As secondary evidence, compare the residual standard
deviation of the WS-POWER fit with history; a value above three times the
historical standard deviation supports the hypothesis. Normal power residuals
under comparable cold conditions contradict it.
```
