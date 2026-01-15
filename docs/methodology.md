# Methodology Guide

## Data Reliability Index (DRI)

### Overview
DRI is a composite score measuring data quality for analytical reliability.

### Formula
```
DRI = 0.4 × Completeness + 0.3 × Consistency + 0.3 × Validity
```

### Components

| Component | Weight | Calculation |
|-----------|--------|-------------|
| Completeness | 40% | `non_null_cells / total_cells` |
| Consistency | 30% | Percentage of rows where `total = sum(age_groups)` |
| Validity | 30% | Percentage of values within valid ranges |

### Threshold
- **PASS**: DRI ≥ 0.7
- **FAIL**: DRI < 0.7

---

## Anomaly Detection Methods

### 1. Z-Score Method
Detects values more than 3 standard deviations from mean.
```
z = (x - μ) / σ
Anomaly if |z| > 3
```

### 2. IQR Method
Uses interquartile range for robust outlier detection.
```
Upper Bound = Q3 + 1.5 × IQR
Lower Bound = Q1 - 1.5 × IQR
```

### 3. Isolation Forest
Unsupervised ML algorithm isolating anomalies based on split depth.
- Contamination: 5% (configurable)
- Random partitioning identifies points requiring fewer splits

### 4. Temporal Anomaly Detection
Identifies sudden changes relative to historical patterns.
```
Spike if: |Δ| > threshold% of rolling mean
```

---

## Forecasting Models

### SARIMA (Seasonal ARIMA)
Time series model with seasonal components.
- **Order**: (p, d, q) = (1, 1, 1)
- **Seasonal Order**: (P, D, Q, s) = (1, 1, 1, 12)

### Exponential Smoothing (Holt-Winters)
Captures level, trend, and seasonality.
- Triple exponential smoothing for seasonal data

### XGBoost/LightGBM
ML models using engineered features:
- Lag features (1, 2, 3, 6, 12 months)
- Rolling statistics (mean, std)
- Calendar features (month, quarter)

### Ensemble
Simple averaging of all forecasting methods for robustness.

---

## Surge Detection

### Definition
A surge is predicted when forecast exceeds threshold.
```
Surge if: forecast > historical_mean × 1.5
```

### Context
Surges are contextualized based on timing (school admissions, government deadlines, etc.)

---

## Inequity Measurement

### Gini Coefficient
Measures enrollment inequality across districts.
```
G = Σ|xi - xj| / (2n²μ)
```

| Gini Range | Interpretation |
|------------|----------------|
| 0.0 - 0.3 | Low inequality |
| 0.3 - 0.5 | Moderate inequality |
| 0.5 - 0.7 | High inequality |
| 0.7 - 1.0 | Extreme inequality |

### Underserved Detection
Districts with enrollment below:
```
threshold = mean - 1.5 × std_dev
```

---

## Priority Scoring

### Factors
| Factor | Weight | Description |
|--------|--------|-------------|
| Enrollment Rate | 30% | Low enrollment = higher priority |
| Inequity | 25% | High child-adult skew = higher priority |
| Forecast Demand | 25% | Expected surge = higher priority |
| DRI Score | 20% | Low data quality = higher priority |

### Tiers
- **CRITICAL**: Score > 0.8
- **HIGH**: Score 0.6 - 0.8
- **MEDIUM**: Score 0.4 - 0.6
- **LOW**: Score < 0.4

---

## Resource Allocation

### Center Calculation
```
Required Centers = Total Enrollment / 500
```

### Staff Calculation
```
Required Staff = Total Enrollment / 100
```

### K-Anonymity
Groups smaller than k=5 are suppressed for privacy.
