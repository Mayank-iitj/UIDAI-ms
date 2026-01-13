"""
Engine 1: Data Governance & Quality
Validates data quality, detects extreme values, and computes Data Reliability Index (DRI)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import yaml
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataGovernanceEngine:
    """Ensures data quality and reliability for UIDAI enrollment data"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.config = config['data_governance']
        self.schema = config['schema']
        self.ethics = config['ethics']
        
        # Thresholds
        self.extreme_percentile = self.config['extreme_value_percentile']
        self.iqr_multiplier = self.config['iqr_multiplier']
        self.z_score_threshold = self.config['z_score_threshold']
        self.min_dri = self.config['min_acceptable_dri']
        self.dri_weights = self.config['dri_weights']
        
        # Ethics
        self.k_anonymity = self.ethics['k_anonymity']
        self.min_group_size = self.ethics['min_group_size']
        
        logger.info("Initialized DataGovernanceEngine")
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that DataFrame conforms to required schema
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required columns
        required_cols = set(self.schema['required_columns'])
        actual_cols = set(df.columns)
        missing_cols = required_cols - actual_cols
        
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
        
        # Check data types
        if 'date' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                issues.append("Column 'date' must be datetime type")
        
        # Check for negative values in age groups
        age_cols = self.schema['age_groups']
        for col in age_cols:
            if col in df.columns:
                if (df[col] < 0).any():
                    issues.append(f"Column '{col}' contains negative values")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def compute_completeness(self, df: pd.DataFrame) -> float:
        """Compute data completeness score (0-1)"""
        total_cells = df.size
        non_null_cells = df.count().sum()
        completeness = non_null_cells / total_cells if total_cells > 0 else 0
        return completeness
    
    def compute_consistency(self, df: pd.DataFrame) -> float:
        """
        Compute data consistency score (0-1)
        Checks if total_enrollment = sum of age groups
        """
        if 'total_enrollment' not in df.columns:
            return 1.0
        
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        calculated_total = df[age_cols].sum(axis=1)
        
        # Check consistency
        is_consistent = np.isclose(df['total_enrollment'], calculated_total, rtol=1e-05)
        consistency = is_consistent.sum() / len(df)
        
        return consistency
    
    def compute_validity(self, df: pd.DataFrame) -> float:
        """
        Compute data validity score (0-1)
        Checks for valid ranges and formats
        """
        validity_checks = []
        
        # Check non-negative enrollments
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        for col in age_cols:
            valid = (df[col] >= 0).sum() / len(df)
            validity_checks.append(valid)
        
        # Check valid dates
        if 'date' in df.columns:
            valid_dates = df['date'].notna().sum() / len(df)
            validity_checks.append(valid_dates)
        
        # Check valid pincodes (6 digits)
        if 'pincode' in df.columns:
            valid_pins = df['pincode'].between(100000, 999999).sum() / len(df)
            validity_checks.append(valid_pins)
        
        validity = np.mean(validity_checks) if validity_checks else 1.0
        return validity
    
    def compute_dri(self, df: pd.DataFrame) -> Dict:
        """
        Compute Data Reliability Index (DRI)
        Weighted score: completeness (40%), consistency (30%), validity (30%)
        
        Returns:
            Dictionary with DRI scores and components
        """
        completeness = self.compute_completeness(df)
        consistency = self.compute_consistency(df)
        validity = self.compute_validity(df)
        
        # Weighted DRI
        dri = (
            self.dri_weights['completeness'] * completeness +
            self.dri_weights['consistency'] * consistency +
            self.dri_weights['validity'] * validity
        )
        
        assessment = "PASS" if dri >= self.min_dri else "FAIL"
        
        result = {
            'dri_score': round(dri, 3),
            'assessment': assessment,
            'components': {
                'completeness': round(completeness, 3),
                'consistency': round(consistency, 3),
                'validity': round(validity, 3)
            },
            'threshold': self.min_dri
        }
        
        logger.info(f"DRI Score: {dri:.3f} ({assessment})")
        
        return result
    
    def detect_extreme_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect extreme values using multiple methods:
        1. Percentile-based
        2. IQR method
        3. Z-score method
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        df_with_flags = df.copy()
        
        for col in age_cols:
            # Method 1: Percentile
            threshold = df[col].quantile(self.extreme_percentile / 100)
            df_with_flags[f'{col}_extreme_pct'] = df[col] > threshold
            
            # Method 2: IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + self.iqr_multiplier * IQR
            df_with_flags[f'{col}_extreme_iqr'] = df[col] > upper_bound
            
            # Method 3: Z-score
            mean = df[col].mean()
            std = df[col].std()
            if std > 0:
                z_scores = (df[col] - mean) / std
                df_with_flags[f'{col}_extreme_zscore'] = np.abs(z_scores) > self.z_score_threshold
            else:
                df_with_flags[f'{col}_extreme_zscore'] = False
            
            # Combined flag (at least 2 methods agree)
            df_with_flags[f'{col}_is_extreme'] = (
                df_with_flags[f'{col}_extreme_pct'].astype(int) +
                df_with_flags[f'{col}_extreme_iqr'].astype(int) +
                df_with_flags[f'{col}_extreme_zscore'].astype(int)
            ) >= 2
        
        # Overall extreme flag
        extreme_flags = [f'{col}_is_extreme' for col in age_cols]
        df_with_flags['has_extreme_values'] = df_with_flags[extreme_flags].any(axis=1)
        
        num_extreme = df_with_flags['has_extreme_values'].sum()
        pct_extreme = (num_extreme / len(df)) * 100
        
        logger.info(f"Detected {num_extreme:,} records ({pct_extreme:.2f}%) with extreme values")
        
        return df_with_flags
    
    def apply_k_anonymity(self, df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
        """
        Apply k-anonymity: suppress groups with < k members
        
        Args:
            df: Input DataFrame
            group_cols: Columns to group by (e.g., ['state', 'district'])
        
        Returns:
            DataFrame with small groups suppressed
        """
        # Count group sizes
        group_sizes = df.groupby(group_cols).size()
        
        # Identify groups below threshold
        valid_groups = group_sizes[group_sizes >= self.k_anonymity].index
        
        # Filter to valid groups
        df_anonymized = df.set_index(group_cols).loc[valid_groups].reset_index()
        
        suppressed = len(df) - len(df_anonymized)
        pct_suppressed = (suppressed / len(df)) * 100
        
        logger.info(f"K-anonymity applied: suppressed {suppressed:,} records ({pct_suppressed:.2f}%)")
        
        return df_anonymized
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive data quality report"""
        # Schema validation
        is_valid, schema_issues = self.validate_schema(df)
        
        # DRI computation
        dri_result = self.compute_dri(df)
        
        # Extreme values
        df_with_extremes = self.detect_extreme_values(df)
        num_extremes = df_with_extremes['has_extreme_values'].sum()
        
        # Missing data
        missing_data = df.isnull().sum().to_dict()
        total_missing = df.isnull().sum().sum()
        pct_missing = (total_missing / df.size) * 100
        
        # Duplicate records
        num_duplicates = df.duplicated().sum()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(df),
            'schema_validation': {
                'is_valid': is_valid,
                'issues': schema_issues
            },
            'dri': dri_result,
            'data_quality': {
                'missing_values': {
                    'total': int(total_missing),
                    'percentage': round(pct_missing, 2),
                    'by_column': {k: int(v) for k, v in missing_data.items() if v > 0}
                },
                'duplicate_records': int(num_duplicates),
                'extreme_values': int(num_extremes)
            },
            'recommendations': self._generate_recommendations(dri_result, is_valid, schema_issues)
        }
        
        return report
    
    def _generate_recommendations(
        self, 
        dri_result: Dict, 
        is_valid: bool, 
        schema_issues: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on quality checks"""
        recommendations = []
        
        if not is_valid:
            recommendations.append("CRITICAL: Fix schema validation issues before analysis")
        
        if dri_result['assessment'] == 'FAIL':
            recommendations.append(f"DRI score ({dri_result['dri_score']}) below threshold ({self.min_dri})")
            
            # Specific recommendations
            if dri_result['components']['completeness'] < 0.95:
                recommendations.append("Improve data completeness: investigate missing values")
            
            if dri_result['components']['consistency'] < 0.95:
                recommendations.append("Fix data consistency: verify total enrollment calculations")
            
            if dri_result['components']['validity'] < 0.95:
                recommendations.append("Validate data ranges: check for invalid values")
        
        if not recommendations:
            recommendations.append("Data quality is satisfactory for analysis")
        
        return recommendations


def main():
    """Test the Data Governance Engine"""
    from utils.data_loader import UidaiDataLoader
    
    # Load data
    loader = UidaiDataLoader()
    df = loader.load_all_data()
    
    # Run governance checks
    engine = DataGovernanceEngine()
    report = engine.generate_quality_report(df)
    
    # Display report
    print("\n" + "="*60)
    print("DATA GOVERNANCE & QUALITY REPORT")
    print("="*60)
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Total Records: {report['total_records']:,}")
    
    print(f"\n--- Schema Validation ---")
    print(f"Valid: {report['schema_validation']['is_valid']}")
    if report['schema_validation']['issues']:
        for issue in report['schema_validation']['issues']:
            print(f"  ⚠️  {issue}")
    
    print(f"\n--- Data Reliability Index (DRI) ---")
    print(f"Overall Score: {report['dri']['dri_score']} ({report['dri']['assessment']})")
    print(f"  Completeness: {report['dri']['components']['completeness']}")
    print(f"  Consistency: {report['dri']['components']['consistency']}")
    print(f"  Validity: {report['dri']['components']['validity']}")
    
    print(f"\n--- Data Quality Metrics ---")
    print(f"Missing Values: {report['data_quality']['missing_values']['total']} ({report['data_quality']['missing_values']['percentage']}%)")
    print(f"Duplicate Records: {report['data_quality']['duplicate_records']}")
    print(f"Extreme Values: {report['data_quality']['extreme_values']}")
    
    print(f"\n--- Recommendations ---")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
