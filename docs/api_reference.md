# API Reference

## Core Classes

### UidaiIntelligenceSystem

Master orchestrator for the intelligence platform.

```python
from main import UidaiIntelligenceSystem

system = UidaiIntelligenceSystem(config_path="./config/config.yaml")
report, df = system.run_pipeline(input_file=None)
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `run_pipeline()` | `input_file: Optional[Path]` | `Tuple[Dict, DataFrame]` | Execute full analysis |
| `generate_executive_summary()` | `complete_report: Dict` | `str` | Generate text summary |
| `save_report()` | `report: Dict, format: str` | `Path` | Save to JSON/text/PDF |

---

## Engine 1: DataGovernanceEngine

```python
from engines.data_governance import DataGovernanceEngine

engine = DataGovernanceEngine(config_path="./config/config.yaml")
```

### Methods

| Method | Parameters | Returns |
|--------|------------|---------|
| `validate_schema(df)` | `DataFrame` | `Tuple[bool, List[str]]` |
| `compute_completeness(df)` | `DataFrame` | `float` |
| `compute_consistency(df)` | `DataFrame` | `float` |
| `compute_validity(df)` | `DataFrame` | `float` |
| `compute_dri(df)` | `DataFrame` | `Dict` |
| `detect_extreme_values(df)` | `DataFrame` | `DataFrame` |
| `apply_k_anonymity(df, group_cols)` | `DataFrame, List[str]` | `DataFrame` |
| `generate_quality_report(df)` | `DataFrame` | `Dict` |

---

## Engine 2: DescriptiveAnalyticsEngine

```python
from engines.descriptive_analytics import DescriptiveAnalyticsEngine

engine = DescriptiveAnalyticsEngine(config_path="./config/config.yaml")
```

### Methods

| Method | Parameters | Returns |
|--------|------------|---------|
| `compute_temporal_trends(df)` | `DataFrame` | `DataFrame` |
| `compute_geographic_patterns(df)` | `DataFrame` | `Dict` |
| `analyze_age_demographics(df)` | `DataFrame` | `Dict` |
| `detect_inequities(df)` | `DataFrame` | `Dict` |
| `perform_pincode_clustering(df)` | `DataFrame` | `Tuple[DataFrame, Dict]` |
| `generate_summary_statistics(df)` | `DataFrame` | `Dict` |

---

## Engine 3: AnomalyDetectionEngine

```python
from engines.anomaly_detection import AnomalyDetectionEngine

engine = AnomalyDetectionEngine(config_path="./config/config.yaml")
```

### Methods

| Method | Parameters | Returns |
|--------|------------|---------|
| `detect_statistical_anomalies(df)` | `DataFrame` | `DataFrame` |
| `detect_temporal_anomalies(df)` | `DataFrame` | `DataFrame` |
| `detect_geographic_anomalies(df)` | `DataFrame` | `DataFrame` |
| `detect_ml_anomalies(df)` | `DataFrame` | `DataFrame` |
| `compute_anomaly_severity(df)` | `DataFrame` | `DataFrame` |
| `generate_anomaly_report(df)` | `DataFrame` | `Dict` |

---

## Engine 4: ForecastingEngine

```python
from engines.forecasting import ForecastingEngine

engine = ForecastingEngine(config_path="./config/config.yaml")
```

### Methods

| Method | Parameters | Returns |
|--------|------------|---------|
| `prepare_timeseries(df, freq)` | `DataFrame, str` | `DataFrame` |
| `forecast_sarima(ts, horizon)` | `Series, int` | `Dict` |
| `forecast_exponential_smoothing(ts, horizon)` | `Series, int` | `Dict` |
| `forecast_xgboost(ts, target_col, horizon)` | `DataFrame, str, int` | `Dict` |
| `ensemble_forecast(forecasts)` | `List[Dict]` | `Dict` |
| `detect_forecast_surges(forecast, historical)` | `List, Series` | `Dict` |
| `generate_forecast_report(df, horizon)` | `DataFrame, int` | `Dict` |

---

## Engine 5: PolicyImpactEngine

```python
from engines.policy_impact import PolicyImpactEngine

engine = PolicyImpactEngine(config_path="./config/config.yaml")
```

### Methods

| Method | Parameters | Returns |
|--------|------------|---------|
| `compute_priority_score(...)` | `district_data, dri_scores, forecast_data, inequity_data` | `DataFrame` |
| `recommend_resource_allocation(priority_df)` | `DataFrame` | `Dict` |
| `identify_intervention_needs(...)` | `district_data, anomaly_data, forecast_surge_data` | `Dict` |
| `simulate_policy_impact(baseline, scenario)` | `DataFrame, Dict` | `Dict` |
| `generate_policy_report(...)` | Multiple DataFrames | `Dict` |

---

## Utility Classes

### UidaiDataLoader

```python
from utils.data_loader import UidaiDataLoader

loader = UidaiDataLoader(config_path="./config/config.yaml")
df = loader.load_all_data()
```

### Visualizer

```python
from utils.visualizer import Visualizer

viz = Visualizer(output_dir="./outputs/visualizations")
plot_paths = viz.generate_all_plots(df, analysis_results)
```
