# UIDAI Intelligence System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub](https://img.shields.io/github/stars/Mayank-iitj/UIDAI-ms?style=social)](https://github.com/Mayank-iitj/UIDAI-ms)

**Production-Ready Analytical & Predictive Intelligence Platform for UIDAI Enrollment Data

## 🎯 Overview

The UIDAI Intelligence System is a comprehensive, production-ready analytical platform designed to extract actionable insights from Aadhaar enrollment data. The system combines statistical analysis, machine learning, and forecasting to support data-driven policy decisions and operational planning for the Unique Identification Authority of India (UIDAI).

### ⚡ Quick Start - Deploy to Streamlit Cloud

Deploy your own instance in 5 minutes:

1. **Fork this repository**
2. **Sign in to [Streamlit Cloud](https://share.streamlit.io)**
3. **Deploy**: Select this repo, branch `main`, file `streamlit_app.py`
4. **Done!** Your app will be live at `https://[your-app].streamlit.app`

📖 **[Full Deployment Guide](STREAMLIT_CLOUD.md)**

### 🎨 Features

✅ **5 Analytical Engines**: Data Governance, Descriptive Analytics, Anomaly Detection, Forecasting, Policy Impact  
✅ **Interactive Dashboard**: Beautiful Streamlit interface  
✅ **Sample Data Generator**: Test without real data  
✅ **File Upload**: Analyze your own datasets  
✅ **Export Reports**: PDF, JSON, TXT formats  
✅ **Mobile Responsive**: Works on all devices

## 🏗️ Architecture

The system consists of five core analytical engines:

### 1. **Data Governance & Quality Engine**
- Schema validation and compliance checking
- Data Reliability Index (DRI) computation
- Extreme value detection (multiple methods)
- K-anonymity enforcement
- Comprehensive quality reporting

### 2. **Descriptive Analytics Engine**
- Temporal trend analysis (MoM, YoY growth)
- Geographic pattern identification
- Age demographic profiling
- Enrollment inequity detection
- PIN code clustering (K-Means)
- Summary statistics generation

### 3. **Anomaly Detection Engine**
- Statistical anomaly detection (Z-score, IQR, Quantile)
- Temporal anomaly detection (sudden spikes/drops)
- Geographic anomaly detection (regional deviations)
- ML-based anomaly detection (Isolation Forest)
- Severity scoring and classification

### 4. **Forecasting & Prediction Engine**
- Time series forecasting (SARIMA)
- Exponential Smoothing (Holt-Winters)
- Machine Learning models (XGBoost, LightGBM)
- Ensemble forecasting
- Surge detection and early warnings
- Confidence interval generation

### 5. **Policy Impact Analysis Engine**
- Priority district scoring
- Resource allocation optimization
- Intervention need identification
- Policy impact simulation
- Strategic recommendation generation

## 📁 Project Structure

```
uidai-intelligence-system/
├── config/
│   ├── config.yaml          # System configuration
│   └── schema.yaml          # Data schema definition
├── engines/
│   ├── __init__.py
│   ├── data_governance.py   # Engine 1
│   ├── descriptive_analytics.py  # Engine 2
│   ├── anomaly_detection.py      # Engine 3
│   ├── forecasting.py            # Engine 4
│   └── policy_impact.py          # Engine 5
├── utils/
│   ├── __init__.py
│   ├── data_loader.py       # Data loading utilities
│   └── validators.py        # Data validation utilities
├── data/
│   ├── raw/                 # Raw CSV files
│   ├── processed/           # Processed data
│   └── cache/               # Cached data
├── outputs/
│   ├── reports/             # Generated reports
│   ├── models/              # Saved ML models
│   └── visualizations/      # Charts and graphs
├── dashboard/               # Interactive dashboard
├── notebooks/               # Jupyter notebooks
├── tests/                   # Unit and integration tests
├── main.py                  # Master orchestrator
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- 16GB RAM recommended
- UIDAI dataset in CSV format

### Installation

1. **Clone or navigate to the project directory**:
   ```powershell
   cd C:\Users\MS\.gemini\antigravity\scratch\uidai-intelligence-system
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure data paths**:
   Edit `config/config.yaml` and set `raw_data_path` to your dataset location:
   ```yaml
   data:
     raw_data_path: "C:/UIDAI-dataset"
   ```

### Running the System

**Full Analysis Pipeline**:
```powershell
python main.py
```

This will:
1. Load and validate enrollment data
2. Run data governance checks
3. Perform descriptive analytics
4. Detect anomalies
5. Generate forecasts
6. Analyze policy impact
7. Save comprehensive reports to `outputs/reports/`

**Individual Engine Testing**:

```powershell
# Test Data Governance Engine
python engines/data_governance.py

# Test Descriptive Analytics
python engines/descriptive_analytics.py

# Test Anomaly Detection
python engines/anomaly_detection.py

# Test Forecasting
python engines/forecasting.py

# Test Policy Impact
python engines/policy_impact.py
```

## 📊 Expected Data Schema

The system expects CSV files with the following columns:

| Column       | Type   | Description                    |
|--------------|--------|--------------------------------|
| date         | String | Date in DD-MM-YYYY format      |
| state        | String | State name                     |
| district     | String | District name                  |
| pincode      | Int    | 6-digit PIN code               |
| age_0_5      | Int    | Enrollments for age 0-5        |
| age_5_17     | Int    | Enrollments for age 5-17       |
| age_18_plus  | Int    | Enrollments for age 18+        |

## 📈 Output Reports

The system generates two types of reports:

### 1. **JSON Intelligence Report**
Complete analysis results in machine-readable format:
- `outputs/reports/intelligence_report_[timestamp].json`

### 2. **Executive Summary (Text)**
Human-readable summary with key insights:
- `outputs/reports/executive_summary_[timestamp].txt`

## 🔧 Configuration

Key configuration parameters in `config/config.yaml`:

### Data Quality Thresholds
```yaml
data_governance:
  min_acceptable_dri: 0.7  # Minimum Data Reliability Index
  z_score_threshold: 3      # Outlier detection threshold
```

### Forecasting Parameters
```yaml
forecasting:
  forecast_horizon_short: 3  # Months
  forecast_horizon_long: 6   # Months
  confidence_levels:
    - 0.80
    - 0.95
```

### Policy Parameters
```yaml
policy_impact:
  optimal_enrollment_per_center: 500
  optimal_enrollment_per_staff: 100
```

## 🎓 Key Features

### ✅ Production-Ready
- Comprehensive error handling
- Audit logging
- Performance optimization
- Scalable architecture

### 🔒 Ethical & Compliant
- K-anonymity enforcement
- Privacy-preserving analytics
- UIDAI data governance adherence

### 🧠 Intelligent
- Multiple ML models (XGBoost, LightGBM, Isolation Forest)
- Statistical methods (SARIMA, Z-score, IQR)
- Ensemble approaches

### 📊 Explainable
- Clear methodology documentation
- Interpretable metrics (DRI, Gini, MAPE)
- Actionable recommendations

## 📝 Usage Examples

### Example 1: Quick Health Check
```python
from utils.data_loader import UidaiDataLoader
from engines.data_governance import DataGovernanceEngine

# Load data
loader = UidaiDataLoader()
df = loader.load_all_data()

# Check data quality
engine = DataGovernanceEngine()
report = engine.generate_quality_report(df)
print(f"DRI Score: {report['dri']['dri_score']}")
```

### Example 2: Generate Forecast
```python
from engines.forecasting import ForecastingEngine

engine = ForecastingEngine()
forecast_report = engine.generate_forecast_report(df, horizon=6)
print(forecast_report['ensemble_forecast']['forecast'])
```

### Example 3: Identify Priority Districts
```python
from engines.policy_impact import PolicyImpactEngine

engine = PolicyImpactEngine()
policy_report = engine.generate_policy_report(district_data)
print(f"Critical districts: {policy_report['resource_allocation']['critical_districts']}")
```

## 🧪 Testing

Run unit tests:
```powershell
pytest tests/
```

Run with coverage:
```powershell
pytest --cov=engines --cov=utils tests/
```

## 📚 Documentation

Detailed documentation available in `docs/`:
- Technical Architecture
- API Reference
- User Guide
- Deployment Guide

## 🤝 Contributing

This is a production system for UIDAI. All changes must:
1. Pass data governance checks
2. Maintain privacy compliance
3. Include comprehensive tests
4. Update documentation

## 📄 License

MIT License - Copyright (c) 2026 [Mayank Sharma](https://mayyanks.app)

## 👥 Authors

- **Developer**: [Mayank Sharma](https://mayyanks.app), IIT Jodhpur
  - 📧 b24bs1555@iitj.ac.in
  - 📧 ms1591934@gmail.com
- **System Design**: Advanced Analytics Team
- **Implementation**: Data Science Division

## 🆘 Support

For issues or questions:
- Check `outputs/system.log` for detailed logs
- Review configuration in `config/config.yaml`
- Consult technical documentation

## 🔄 Version History

### Version 1.0.0 (Current)
- ✅ Five core analytical engines
- ✅ Master orchestrator
- ✅ Data governance framework
- ✅ Production-ready architecture
- ✅ Comprehensive documentation

## 🎯 Roadmap

Future enhancements:
- [ ] Interactive Streamlit dashboard
- [ ] Real-time monitoring
- [ ] API endpoints
- [ ] Advanced visualizations
- [ ] Automated reporting

---

**Built with Python 🐍 | Powered by Advanced Analytics 📊 | Serving UIDAI 🇮🇳**
