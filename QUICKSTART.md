# UIDAI Intelligence System - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```powershell
cd C:\Users\MS\.gemini\antigravity\scratch\uidai-intelligence-system
pip install -r requirements.txt
```

### Step 2: Configure Data Path
Edit [`config/config.yaml`](file:///C:/Users/MS/.gemini/antigravity/scratch/uidai-intelligence-system/config/config.yaml) (line 5):
```yaml
data:
  raw_data_path: "C:/UIDAI-dataset"  # ← Change to your dataset location
```

### Step 3: Run Analysis
```powershell
python main.py
```

---

## 📊 Expected Output

The system will:
1. ✅ Load enrollment data
2. ✅ Validate data quality (DRI score)
3. ✅ Generate descriptive analytics
4. ✅ Detect anomalies
5. ✅ Create forecasts
6. ✅ Analyze policy impact
7. ✅ Save reports to `outputs/reports/`

---

## 📁 Where to Find Results

After running, check:
- `outputs/reports/intelligence_report_[timestamp].json` - Complete analysis
- `outputs/reports/executive_summary_[timestamp].txt` - Summary
- `outputs/system.log` - Execution log

---

## 🧪 Test Individual Engines

```powershell
# Test each engine independently
python engines/data_governance.py
python engines/descriptive_analytics.py
python engines/anomaly_detection.py
python engines/forecasting.py
python engines/policy_impact.py
```

---

## 🔧 Common Configuration Changes

### Adjust Forecast Horizon
In [`config/config.yaml`](file:///C:/Users/MS/.gemini/antigravity/scratch/uidai-intelligence-system/config/config.yaml), lines 84-86:
```yaml
forecasting:
  forecast_horizon_short: 3  # Change to desired months
  forecast_horizon_long: 6   # Change to desired months
```

### Adjust Data Quality Threshold
In [`config/config.yaml`](file:///C:/Users/MS/.gemini/antigravity/scratch/uidai-intelligence-system/config/config.yaml), line 45:
```yaml
data_governance:
  min_acceptable_dri: 0.7  # Minimum quality score (0-1)
```

### Adjust Resource Planning
In [`config/config.yaml`](file:///C:/Users/MS/.gemini/antigravity/scratch/uidai-intelligence-system/config/config.yaml), lines 130-131:
```yaml
policy_impact:
  optimal_enrollment_per_center: 500  # Enrollments per center
  optimal_enrollment_per_staff: 100   # Enrollments per staff
```

---

## 📊 Sample Executive Summary

```
═══════════════════════════════════════════════════════════
UIDAI INTELLIGENCE SYSTEM - EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════

📊 DATA QUALITY
Data Reliability Index: 0.XXX (PASS/FAIL)
  • Completeness: 0.XX
  • Consistency: 0.XX
  • Validity: 0.XX

📈 KEY INSIGHTS
Geographic Coverage: X states, Y districts, Z PIN codes
Underserved Districts: N

🔍 ANOMALY DETECTION
Statistical Anomalies: X,XXX
Geographic Anomalies: XX

🔮 FORECAST
Forecast Horizon: 6 months
✓ No enrollment surges predicted
(or)
⚠️  SURGE ALERT: X period(s) predicted

🎯 POLICY RECOMMENDATIONS
Critical Districts: XX
Required Centers: X,XXX
Required Staff: XX,XXX
Immediate Interventions Needed: XX

📋 STRATEGIC RECOMMENDATIONS
1. [Actionable recommendation]
2. [Resource allocation strategy]
3. [Quality improvement suggestion]
```

---

## 🆘 Troubleshooting

### Issue: "No CSV files found"
**Solution**: Check that `raw_data_path` in `config/config.yaml` points to the correct directory with CSV files.

### Issue: "Module not found"
**Solution**: Install dependencies:
```powershell
pip install -r requirements.txt
```

### Issue: "Insufficient data for forecasting"
**Solution**: Ensure you have at least 12 months of historical data (24+ months recommended).

### Issue: "Memory error"
**Solution**: Adjust `max_memory_gb` in `config/config.yaml` or use Polars:
```python
df = loader.load_all_data(use_polars=True)
```

---

## 📚 Documentation

- **Full Documentation**: [`README.md`](file:///C:/Users/MS/.gemini/antigravity/scratch/uidai-intelligence-system/README.md)
- **Implementation Guide**: [`walkthrough.md`](file:///C:/Users/MS/.gemini/antigravity/brain/668a10f4-070b-4187-b3f7-8f8ebbc27d1b/walkthrough.md)
- **Configuration**: [`config/config.yaml`](file:///C:/Users/MS/.gemini/antigravity/scratch/uidai-intelligence-system/config/config.yaml)

---

## 🎯 Next Steps

1. ✅ Run the system with your data
2. 📊 Review the generated reports
3. 🎛️ Adjust configuration as needed
4. 🔄 Schedule regular runs for monitoring
5. 📈 Build dashboard (Phase 2)

---

**Need Help?** Check `outputs/system.log` for detailed execution logs.

---

Built with Python 🐍 | Powered by Advanced Analytics 📊 | Serving UIDAI 🇮🇳
