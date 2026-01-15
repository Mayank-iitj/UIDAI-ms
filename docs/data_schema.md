# Data Schema Specification

## Input Data Format

The system expects CSV files with Aadhaar enrollment data.

### Required Columns

| Column | Type | Format | Description |
|--------|------|--------|-------------|
| `date` | String/Date | DD-MM-YYYY | Enrollment date |
| `state` | String | - | State name |
| `district` | String | - | District name |
| `pincode` | Integer | 6 digits | PIN code (100000-999999) |
| `age_0_5` | Integer | ≥0 | Enrollments for age 0-5 years |
| `age_5_17` | Integer | ≥0 | Enrollments for age 5-17 years |
| `age_18_greater` | Integer | ≥0 | Enrollments for age 18+ years |
| `total_enrollment` | Integer | ≥0 | Total enrollments (sum of age groups) |

### Sample Data

```csv
date,state,district,pincode,age_0_5,age_5_17,age_18_greater,total_enrollment
01-01-2025,Uttar Pradesh,Lucknow,226001,150,120,30,300
01-01-2025,Bihar,Patna,800001,200,180,40,420
```

## Validation Rules

### Schema Validation
- All required columns must be present
- Date column must be parseable as datetime
- PIN codes must be 6-digit numbers (100000-999999)

### Data Quality Rules
- Age group columns must be non-negative
- `total_enrollment` should equal sum of age groups
- No negative values allowed

### Data Consistency
The system validates:
```
total_enrollment == age_0_5 + age_5_17 + age_18_greater
```

## Output Schema

### JSON Report Structure

```json
{
  "metadata": {
    "generated_at": "ISO timestamp",
    "system_version": "1.0.0",
    "data_records": 1000000,
    "analysis_period": {"start": "date", "end": "date"}
  },
  "data_governance": {
    "dri": {"dri_score": 0.95, "assessment": "PASS"},
    "data_quality": {...}
  },
  "descriptive_analytics": {
    "temporal_trends": [...],
    "geographic_patterns": {...},
    "age_demographics": {...}
  },
  "anomaly_detection": {
    "summary": {...},
    "critical_anomalies": [...]
  },
  "forecasting": {
    "forecast_values": [...],
    "surge_detection": {...}
  },
  "policy_impact": {
    "priority_districts": [...],
    "resource_allocation": {...},
    "strategic_recommendations": [...]
  }
}
```

## Configuration Schema

See `config/config.yaml` for full configuration options.

### Key Configuration Sections

```yaml
data:
  raw_data_path: "path/to/data"

schema:
  required_columns: [date, state, district, ...]
  age_groups: [age_0_5, age_5_17, age_18_greater]

data_governance:
  min_acceptable_dri: 0.7
  z_score_threshold: 3

forecasting:
  forecast_horizon_long: 6

policy_impact:
  optimal_enrollment_per_center: 500
```
