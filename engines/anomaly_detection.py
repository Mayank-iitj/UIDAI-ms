"""
Engine 3: Anomaly Detection
Identifies unusual patterns, spikes, and data quality issues in enrollment data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import yaml
import logging
from sklearn.ensemble import IsolationForest
from scipy import stats

logger = logging.getLogger(__name__)


class AnomalyDetectionEngine:
    """Detect anomalies and unusual patterns in UIDAI enrollment data"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.config = config['anomaly_detection']
        self.schema = config['schema']
        
        # Thresholds
        self.z_threshold = self.config['z_score_threshold']
        self.iqr_multiplier = self.config['iqr_multiplier']
        self.quantile_lower = self.config['quantile_lower']
        self.quantile_upper = self.config['quantile_upper']
        self.mom_threshold = self.config['mom_change_threshold']
        
        # Isolation Forest params
        self.contamination = self.config['contamination']
        self.random_state = self.config['random_state']
        
        # Severity levels
        self.severity_levels = self.config['severity_levels']
        
        logger.info("Initialized AnomalyDetectionEngine")
    
    def detect_statistical_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect statistical anomalies using multiple methods
        
        Methods:
        1. Z-score
        2. IQR (Interquartile Range)
        3. Quantile-based
        
        Returns:
            DataFrame with anomaly flags
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        df_flagged = df.copy()
        
        for col in age_cols + ['total_enrollment']:
            if col not in df.columns:
                continue
            
            # Method 1: Z-score
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                df_flagged[f'{col}_zscore_anomaly'] = z_scores > self.z_threshold
            else:
                df_flagged[f'{col}_zscore_anomaly'] = False
            
            # Method 2: IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - self.iqr_multiplier * IQR
            upper_bound = Q3 + self.iqr_multiplier * IQR
            df_flagged[f'{col}_iqr_anomaly'] = (df[col] < lower_bound) | (df[col] > upper_bound)
            
            # Method 3: Quantile-based
            lower_q = df[col].quantile(self.quantile_lower)
            upper_q = df[col].quantile(self.quantile_upper)
            df_flagged[f'{col}_quantile_anomaly'] = (df[col] < lower_q) | (df[col] > upper_q)
            
            # Combined: at least 2 methods agree
            df_flagged[f'{col}_is_anomaly'] = (
                df_flagged[f'{col}_zscore_anomaly'].astype(int) +
                df_flagged[f'{col}_iqr_anomaly'].astype(int) +
                df_flagged[f'{col}_quantile_anomaly'].astype(int)
            ) >= 2
        
        # Overall anomaly flag
        anomaly_cols = [f'{col}_is_anomaly' for col in age_cols + ['total_enrollment'] if f'{col}_is_anomaly' in df_flagged.columns]
        df_flagged['has_statistical_anomaly'] = df_flagged[anomaly_cols].any(axis=1)
        
        num_anomalies = df_flagged['has_statistical_anomaly'].sum()
        pct_anomalies = (num_anomalies / len(df)) * 100
        
        logger.info(f"Detected {num_anomalies:,} statistical anomalies ({pct_anomalies:.2f}%)")
        
        return df_flagged
    
    def detect_temporal_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect temporal anomalies (sudden spikes/drops)
        
        Returns:
            DataFrame with temporal anomaly flags
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # Aggregate by date
        daily = df.groupby('date')[age_cols + ['total_enrollment']].sum().sort_index()
        
        # Calculate month-over-month changes
        daily_flagged = daily.copy()
        
        for col in age_cols + ['total_enrollment']:
            if col not in daily.columns:
                continue
            
            # Percent change
            daily_flagged[f'{col}_pct_change'] = daily[col].pct_change() * 100
            
            # Flag sudden changes
            daily_flagged[f'{col}_sudden_change'] = (
                daily_flagged[f'{col}_pct_change'].abs() > (self.mom_threshold * 100)
            )
            
            # Moving average deviation
            ma_7d = daily[col].rolling(window=7, min_periods=1).mean()
            ma_30d = daily[col].rolling(window=30, min_periods=1).mean()
            
            # Flag if current value deviates significantly from moving average
            daily_flagged[f'{col}_ma_deviation'] = (
                (daily[col] - ma_30d).abs() / (ma_30d + 1e-8) > 0.5
            )
            
            # Combined temporal anomaly
            daily_flagged[f'{col}_temporal_anomaly'] = (
                daily_flagged[f'{col}_sudden_change'] | 
                daily_flagged[f'{col}_ma_deviation']
            )
        
        # Overall temporal anomaly
        temporal_cols = [f'{col}_temporal_anomaly' for col in age_cols + ['total_enrollment'] if f'{col}_temporal_anomaly' in daily_flagged.columns]
        daily_flagged['has_temporal_anomaly'] = daily_flagged[temporal_cols].any(axis=1)
        
        num_anomalies = daily_flagged['has_temporal_anomaly'].sum()
        pct_anomalies = (num_anomalies / len(daily_flagged)) * 100
        
        logger.info(f"Detected {num_anomalies} temporal anomalies ({pct_anomalies:.2f}% of days)")
        
        return daily_flagged.reset_index()
    
    def detect_geographic_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect geographic anomalies (unusual patterns by location)
        
        Returns:
            DataFrame with geographic anomaly flags
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # Aggregate by district
        district_data = df.groupby(['state', 'district'])[
            age_cols + ['total_enrollment']
        ].sum().reset_index()
        
        # Calculate state-level statistics
        state_stats = df.groupby('state')[age_cols + ['total_enrollment']].agg(['mean', 'std'])
        
        # Flag districts that deviate significantly from state average
        district_flagged = district_data.copy()
        
        for col in age_cols + ['total_enrollment']:
            if col not in district_data.columns:
                continue
            
            # Merge state statistics
            district_flagged = district_flagged.merge(
                state_stats[col].reset_index(),
                on='state',
                how='left'
            )
            
            # Z-score relative to state
            district_flagged[f'{col}_state_zscore'] = (
                (district_flagged[col] - district_flagged['mean']) / 
                (district_flagged['std'] + 1e-8)
            )
            
            # Flag if z-score exceeds threshold
            district_flagged[f'{col}_geo_anomaly'] = (
                district_flagged[f'{col}_state_zscore'].abs() > self.z_threshold
            )
            
            # Clean up temporary columns
            district_flagged = district_flagged.drop(columns=['mean', 'std'], errors='ignore')
        
        # Overall geographic anomaly
        geo_cols = [f'{col}_geo_anomaly' for col in age_cols + ['total_enrollment'] if f'{col}_geo_anomaly' in district_flagged.columns]
        district_flagged['has_geographic_anomaly'] = district_flagged[geo_cols].any(axis=1)
        
        num_anomalies = district_flagged['has_geographic_anomaly'].sum()
        pct_anomalies = (num_anomalies / len(district_flagged)) * 100
        
        logger.info(f"Detected {num_anomalies} geographic anomalies ({pct_anomalies:.2f}% of districts)")
        
        return district_flagged
    
    def detect_ml_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies using Isolation Forest (ML-based)
        
        Returns:
            DataFrame with ML anomaly scores and flags
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        feature_cols = age_cols + ['total_enrollment']
        
        # Prepare features
        X = df[feature_cols].fillna(0).values
        
        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=300,
            max_samples='auto'
        )
        
        # Predict (-1 for anomalies, 1 for normal)
        predictions = iso_forest.fit_predict(X)
        scores = iso_forest.score_samples(X)
        
        df_flagged = df.copy()
        df_flagged['ml_anomaly_score'] = scores
        df_flagged['ml_is_anomaly'] = predictions == -1
        
        num_anomalies = df_flagged['ml_is_anomaly'].sum()
        pct_anomalies = (num_anomalies / len(df)) * 100
        
        logger.info(f"ML detected {num_anomalies:,} anomalies ({pct_anomalies:.2f}%)")
        
        return df_flagged
    
    def compute_anomaly_severity(self, df_anomalies: pd.DataFrame) -> pd.DataFrame:
        """
        Compute severity scores for detected anomalies
        
        Severity levels:
        - Low (1): Minor deviation
        - Medium (2): Moderate deviation
        - High (3): Significant deviation
        - Critical (4): Extreme deviation
        
        Returns:
            DataFrame with severity scores
        """
        df_scored = df_anomalies.copy()
        
        # Count total anomaly flags
        anomaly_flag_cols = [col for col in df_scored.columns if '_is_anomaly' in col or '_anomaly' in col]
        df_scored['anomaly_count'] = df_scored[anomaly_flag_cols].sum(axis=1)
        
        # Compute aggregate score (for numerical columns with _zscore)
        zscore_cols = [col for col in df_scored.columns if '_zscore' in col]
        if zscore_cols:
            df_scored['max_zscore'] = df_scored[zscore_cols].abs().max(axis=1)
        else:
            df_scored['max_zscore'] = 0
        
        # Severity scoring
        def assign_severity(row):
            if row['anomaly_count'] == 0:
                return 0  # No anomaly
            elif row['anomaly_count'] <= 2 and row.get('max_zscore', 0) < 4:
                return self.severity_levels['low']
            elif row['anomaly_count'] <= 4 and row.get('max_zscore', 0) < 6:
                return self.severity_levels['medium']
            elif row['anomaly_count'] <= 6 or row.get('max_zscore', 0) < 8:
                return self.severity_levels['high']
            else:
                return self.severity_levels['critical']
        
        df_scored['severity_score'] = df_scored.apply(assign_severity, axis=1)
        
        # Reason Classification (Hackathon Requirement)
        def assign_reason(row):
            if row['severity_score'] == 0:
                return "Normal"
            
            # Data Quality Issue (High Z-score but low count or missing fields)
            if row.get('max_zscore', 0) > 4:
                return "Potential Data Quality Error"
            
            # Operational Issue (Specific center drift)
            if row.get('has_temporal_anomaly'):
                return "Operational Batch Delay"
                
            # Geographic/Policy (Regional deviation)
            if row.get('has_geographic_anomaly'):
                 return "Regional Policy Variance"
            
            return "Unclassified Anomaly"

        df_scored['anomaly_reason'] = df_scored.apply(assign_reason, axis=1)
        
        # Severity label
        severity_map = {
            0: 'NORMAL',
            1: 'LOW',
            2: 'MEDIUM',
            3: 'HIGH',
            4: 'CRITICAL'
        }
        df_scored['severity_label'] = df_scored['severity_score'].map(severity_map)
        
        logger.info(f"Severity distribution: {df_scored['severity_label'].value_counts().to_dict()}")
        
        return df_scored
    
    def generate_anomaly_report(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive anomaly detection report"""
        # Run all detection methods
        df_stat = self.detect_statistical_anomalies(df)
        df_temporal = self.detect_temporal_anomalies(df)
        df_geo = self.detect_geographic_anomalies(df)
        df_ml = self.detect_ml_anomalies(df)
        
        # Combine flags
        df_combined = df.copy()
        df_combined['has_statistical_anomaly'] = df_stat['has_statistical_anomaly']
        df_combined['ml_is_anomaly'] = df_ml['ml_is_anomaly']
        df_combined['ml_anomaly_score'] = df_ml['ml_anomaly_score']
        
        # Compute severity
        df_final = self.compute_anomaly_severity(df_combined)
        
        # Generate report
        report = {
            'summary': {
                'total_records': len(df),
                'statistical_anomalies': int(df_stat['has_statistical_anomaly'].sum()),
                'temporal_anomalies': int(df_temporal['has_temporal_anomaly'].sum()),
                'geographic_anomalies': int(df_geo['has_geographic_anomaly'].sum()),
                'ml_anomalies': int(df_ml['ml_is_anomaly'].sum())
            },
            'severity_distribution': df_final['severity_label'].value_counts().to_dict(),
            'critical_anomalies': df_final[df_final['severity_score'] == 4].to_dict('records')[:50],
            'temporal_anomalies': df_temporal[df_temporal['has_temporal_anomaly']].to_dict('records')[:20],
            'geographic_anomalies': df_geo[df_geo['has_geographic_anomaly']][
                ['state', 'district', 'total_enrollment']
            ].to_dict('records')[:20],
            'recommendations': self._generate_recommendations(df_final, df_temporal, df_geo)
        }
        
        return report
    
    def _generate_recommendations(
        self, 
        df_final: pd.DataFrame, 
        df_temporal: pd.DataFrame, 
        df_geo: pd.DataFrame
    ) -> List[str]:
        """Generate actionable recommendations based on detected anomalies"""
        recommendations = []
        
        # Critical anomalies
        critical_count = (df_final['severity_score'] == 4).sum()
        if critical_count > 0:
            recommendations.append(
                f"URGENT: {critical_count} critical anomalies detected. "
                "Immediate investigation required."
            )
        
        # High anomalies
        high_count = (df_final['severity_score'] == 3).sum()
        if high_count > 10:
            recommendations.append(
                f"ATTENTION: {high_count} high-severity anomalies. "
                "Review data quality and enrollment processes."
            )
        
        # Temporal patterns
        temporal_count = df_temporal['has_temporal_anomaly'].sum()
        if temporal_count > len(df_temporal) * 0.1:
            recommendations.append(
                f"Frequent temporal anomalies detected ({temporal_count} days). "
                "Investigate enrollment system stability."
            )
        
        # Geographic concentration
        geo_count = df_geo['has_geographic_anomaly'].sum()
        if geo_count > len(df_geo) * 0.2:
            recommendations.append(
                f"Widespread geographic anomalies ({geo_count} districts). "
                "Review regional data collection processes."
            )
        
        if not recommendations:
            recommendations.append("No significant anomalies detected. Data quality is acceptable.")
        
        return recommendations


def main():
    """Test the Anomaly Detection Engine"""
    from utils.data_loader import UidaiDataLoader
    
    # Load data
    loader = UidaiDataLoader()
    df = loader.load_all_data()
    
    # Run anomaly detection
    engine = AnomalyDetectionEngine()
    report = engine.generate_anomaly_report(df)
    
    print("\n" + "="*60)
    print("ANOMALY DETECTION REPORT")
    print("="*60)
    
    print(f"\n--- Summary ---")
    print(f"Total Records: {report['summary']['total_records']:,}")
    print(f"Statistical Anomalies: {report['summary']['statistical_anomalies']:,}")
    print(f"Temporal Anomalies: {report['summary']['temporal_anomalies']:,}")
    print(f"Geographic Anomalies: {report['summary']['geographic_anomalies']:,}")
    print(f"ML-Detected Anomalies: {report['summary']['ml_anomalies']:,}")
    
    print(f"\n--- Severity Distribution ---")
    for severity, count in sorted(report['severity_distribution'].items()):
        print(f"{severity}: {count:,}")
    
    print(f"\n--- Critical Anomalies ---")
    print(f"Found {len(report['critical_anomalies'])} critical anomalies")
    if report['critical_anomalies']:
        print("\nTop 5 critical cases:")
        for i, anomaly in enumerate(report['critical_anomalies'][:5], 1):
            print(f"{i}. {anomaly.get('state', 'N/A')} - {anomaly.get('district', 'N/A')}")
    
    print(f"\n--- Recommendations ---")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
