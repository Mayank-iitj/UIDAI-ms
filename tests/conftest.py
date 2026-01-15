"""
Shared pytest fixtures for UIDAI Intelligence System tests
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import yaml


@pytest.fixture
def sample_enrollment_df():
    """Create a sample enrollment DataFrame for testing"""
    np.random.seed(42)
    n_records = 500
    
    states = ['Uttar Pradesh', 'Bihar', 'Maharashtra', 'Karnataka', 'Gujarat']
    districts_per_state = {
        'Uttar Pradesh': ['Lucknow', 'Agra', 'Bareilly'],
        'Bihar': ['Patna', 'Gaya', 'Muzaffarpur'],
        'Maharashtra': ['Mumbai', 'Pune', 'Thane'],
        'Karnataka': ['Bengaluru', 'Mysuru', 'Hubli'],
        'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara']
    }
    
    data = {
        'date': pd.date_range(start='2025-01-01', periods=n_records, freq='D'),
        'state': np.random.choice(states, n_records),
        'pincode': np.random.randint(100000, 999999, n_records),
        'age_0_5': np.random.randint(0, 500, n_records),
        'age_5_17': np.random.randint(0, 400, n_records),
        'age_18_greater': np.random.randint(0, 100, n_records),
    }
    
    df = pd.DataFrame(data)
    
    # Add district based on state
    df['district'] = df['state'].apply(
        lambda s: np.random.choice(districts_per_state[s])
    )
    
    # Compute total enrollment
    df['total_enrollment'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
    
    return df


@pytest.fixture
def sample_enrollment_df_with_anomalies(sample_enrollment_df):
    """Create sample DataFrame with known anomalies"""
    df = sample_enrollment_df.copy()
    
    # Add extreme values (anomalies)
    df.loc[0, 'age_0_5'] = 50000  # Extreme high
    df.loc[1, 'age_5_17'] = 40000
    df.loc[2, 'total_enrollment'] = 100000
    
    return df


@pytest.fixture
def sample_enrollment_df_with_missing(sample_enrollment_df):
    """Create sample DataFrame with missing values"""
    df = sample_enrollment_df.copy()
    
    # Add missing values
    df.loc[0:10, 'age_0_5'] = np.nan
    df.loc[15:20, 'pincode'] = np.nan
    
    return df


@pytest.fixture
def sample_timeseries_df():
    """Create a sample time series DataFrame for forecasting tests"""
    dates = pd.date_range(start='2024-01-01', periods=24, freq='M')
    
    # Create seasonal pattern with trend
    trend = np.linspace(1000, 2000, 24)
    seasonal = 200 * np.sin(np.linspace(0, 4*np.pi, 24))
    noise = np.random.randn(24) * 50
    
    values = trend + seasonal + noise
    
    df = pd.DataFrame({
        'date': dates,
        'total_enrollment': values.astype(int)
    })
    df.set_index('date', inplace=True)
    
    return df


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration file for testing"""
    config = {
        'data': {
            'raw_data_path': str(tmp_path / 'raw'),
            'processed_data_path': str(tmp_path / 'processed'),
            'external_data_path': str(tmp_path / 'external')
        },
        'output': {
            'reports_path': str(tmp_path / 'reports'),
            'models_path': str(tmp_path / 'models'),
            'visualizations_path': str(tmp_path / 'visualizations')
        },
        'schema': {
            'date_format': '%d-%m-%Y',
            'required_columns': ['date', 'state', 'district', 'pincode', 
                                'age_0_5', 'age_5_17', 'age_18_greater'],
            'age_groups': ['age_0_5', 'age_5_17', 'age_18_greater']
        },
        'data_governance': {
            'extreme_value_percentile': 99,
            'iqr_multiplier': 1.5,
            'z_score_threshold': 3,
            'min_acceptable_dri': 0.7,
            'dri_weights': {
                'completeness': 0.4,
                'consistency': 0.3,
                'validity': 0.3
            }
        },
        'descriptive_analytics': {
            'top_n_states': 10,
            'top_n_districts': 20,
            'n_clusters': 5,
            'child_adult_ratio_threshold': 2.0,
            'underserved_enrollment_threshold': 0.5
        },
        'anomaly_detection': {
            'z_score_threshold': 3,
            'iqr_multiplier': 1.5,
            'quantile_lower': 0.01,
            'quantile_upper': 0.99,
            'mom_change_threshold': 0.5,
            'contamination': 0.04,
            'random_state': 42,
            'severity_levels': {
                'low': 1,
                'medium': 2,
                'high': 3,
                'critical': 4
            }
        },
        'forecasting': {
            'forecast_horizon_short': 3,
            'forecast_horizon_long': 6,
            'sarima': {
                'seasonal_order': [1, 1, 1, 12]
            },
            'xgboost': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            },
            'lightgbm': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            },
            'confidence_levels': [0.80, 0.95],
            'surge_percentile': 95,
            'metrics': ['MAPE', 'RMSE', 'MAE']
        },
        'policy_impact': {
            'priority_weights': {
                'low_enrollment': 0.3,
                'high_inequity': 0.25,
                'high_forecast_demand': 0.25,
                'low_dri': 0.2
            },
            'optimal_enrollment_per_center': 500,
            'optimal_enrollment_per_staff': 100,
            'intervention_thresholds': {
                'enrollment_rate_low': 0.6,
                'inequity_high': 0.7,
                'forecast_surge_high': 1.5
            }
        },
        'ethics': {
            'k_anonymity': 5,
            'min_group_size': 10,
            'enable_audit_log': False
        },
        'performance': {
            'enable_caching': False,
            'n_jobs': 1,
            'max_memory_gb': 8
        }
    }
    
    config_path = tmp_path / 'config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Create directories
    for key in ['raw', 'processed', 'external', 'reports', 'models', 'visualizations']:
        (tmp_path / key).mkdir(exist_ok=True)
    
    return str(config_path)


@pytest.fixture
def district_data_df(sample_enrollment_df):
    """Create aggregated district-level data for policy tests"""
    df = sample_enrollment_df.groupby(['state', 'district']).agg({
        'age_0_5': 'sum',
        'age_5_17': 'sum',
        'age_18_greater': 'sum',
        'total_enrollment': 'sum'
    }).reset_index()
    
    # Add child-adult ratio
    df['child_adult_ratio'] = (
        (df['age_0_5'] + df['age_5_17']) / 
        df['age_18_greater'].replace(0, 1)
    )
    
    return df
