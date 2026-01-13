import json
import os

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# UIDAI Intelligence System - Analytical Walkthrough\n",
    "\n",
    "## 1. Introduction\n",
    "This notebook provides a comprehensive walkthrough of the **UIDAI Intelligence System**. \n",
    "We analyze over **1 million enrollment records** to extract insights, detect anomalies, forecast demand, and recommend policy interventions.\n",
    "\n",
    "### Objectives\n",
    "- 📊 **Data Governance**: Ensure data quality and reliability.\n",
    "- 📈 **Descriptive Analytics**: Understand enrollment trends and demographics.\n",
    "- 🔍 **Anomaly Detection**: Identify irregularities and potential fraud.\n",
    "- 🔮 **Forecasting**: Predict future enrollment demand.\n",
    "- 🎯 **Policy Impact**: Optimize resource allocation based on data."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "from utils.data_loader import UidaiDataLoader\n",
    "from engines import (\n",
    "    DataGovernanceEngine, \n",
    "    DescriptiveAnalyticsEngine, \n",
    "    AnomalyDetectionEngine,\n",
    "    ForecastingEngine,\n",
    "    PolicyImpactEngine\n",
    ")\n",
    "\n",
    "# Set plotting style\n",
    "plt.style.use('seaborn-v0_8-whitegrid')\n",
    "sns.set_palette(\"husl\")\n",
    "plt.rcParams['figure.figsize'] = (12, 6)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Data Loading & Governance\n",
    "We load the dataset and compute the **Data Reliability Index (DRI)** to ensure data quality."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Load data\n",
    "loader = UidaiDataLoader()\n",
    "df = loader.load_all_data()\n",
    "print(f\"Loaded {len(df):,} records\")\n",
    "\n",
    "# Check Data Governance\n",
    "gov_engine = DataGovernanceEngine()\n",
    "dri = gov_engine.compute_dri(df)\n",
    "print(f\"Data Reliability Index: {dri['dri_score']} ({dri['assessment']})\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Descriptive Analytics\n",
    "Analyzing temporal trends and demographic distributions."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Temporal Trends\n",
    "daily_trends = df.groupby('date')['total_enrollment'].sum()\n",
    "\n",
    "plt.figure(figsize=(15, 6))\n",
    "plt.plot(daily_trends.index, daily_trends.values, linewidth=2, label='Daily Enrollment', color='#3498db')\n",
    "plt.plot(daily_trends.rolling(30).mean(), linewidth=2, label='30-Day Moving Avg', color='#e74c3c', linestyle='--')\n",
    "plt.title('Enrollment Trends (2025)', fontsize=16)\n",
    "plt.legend()\n",
    "plt.grid(True, alpha=0.3)\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. Anomaly Detection\n",
    "Using statistical and ML-based methods to identify irregularities."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "anomaly_engine = AnomalyDetectionEngine()\n",
    "anomalies = anomaly_engine.generate_anomaly_report(df)\n",
    "\n",
    "print(f\"Statistical Anomalies: {anomalies['summary']['statistical_anomalies']:,}\")\n",
    "print(f\"ML Anomalies: {anomalies['summary']['ml_anomalies']:,}\")\n",
    "\n",
    "# Visualize Severity\n",
    "severity = anomalies['severity_distribution']\n",
    "labels = list(severity.keys())\n",
    "values = list(severity.values())\n",
    "\n",
    "plt.figure(figsize=(10, 5))\n",
    "plt.bar(labels, values, color=['green', 'yellow', 'orange', 'red', 'darkred'])\n",
    "plt.title('Anomaly Severity Distribution')\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 5. Forecasting\n",
    "Predicting future enrollment demand using ensemble models."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "forecast_engine = ForecastingEngine()\n",
    "forecast = forecast_engine.generate_forecast_report(df, horizon=6)\n",
    "\n",
    "dates = [x['date'] for x in forecast['forecast_values']]\n",
    "values = [x['predicted_enrollment'] for x in forecast['forecast_values']]\n",
    "\n",
    "plt.figure(figsize=(12, 6))\n",
    "plt.plot(dates, values, marker='o', color='#2ecc71', linewidth=2)\n",
    "plt.fill_between(dates, \n",
    "               [v*0.9 for v in values], \n",
    "               [v*1.1 for v in values], \n",
    "               color='#2ecc71', alpha=0.2, label='Confidence Interval')\n",
    "plt.title('6-Month Enrollment Forecast', fontsize=16)\n",
    "plt.grid(True, alpha=0.3)\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 6. Strategic Recommendations\n",
    "Based on the analysis, we recommend the following strategic interventions:"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "policy_engine = PolicyImpactEngine()\n",
    "policy = policy_engine.generate_policy_report(df, forecast)\n",
    "\n",
    "for i, rec in enumerate(policy['strategic_recommendations'], 1):\n",
    "    print(f\"{i}. {rec}\")\n",
    "\n",
    "critical = policy['resource_allocation']['critical_districts']\n",
    "print(f\"\\nCRITICAL: {critical} districts require immediate resource augmentation.\")"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

# Create notebooks directory if not exists
os.makedirs("notebooks", exist_ok=True)

with open("notebooks/UIDAI_Analysis_Walkthrough.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=1)

print("Notebook created successfully!")
