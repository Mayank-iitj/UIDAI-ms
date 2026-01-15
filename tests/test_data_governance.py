"""
Unit tests for Data Governance Engine
Tests data quality validation, DRI computation, and extreme value detection
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.data_governance import DataGovernanceEngine


class TestDataGovernanceEngine:
    """Test suite for DataGovernanceEngine"""
    
    def test_init(self, mock_config):
        """Test engine initialization"""
        engine = DataGovernanceEngine(mock_config)
        assert engine is not None
        assert engine.min_dri == 0.7
        assert engine.k_anonymity == 5
    
    def test_validate_schema_valid(self, mock_config, sample_enrollment_df):
        """Test schema validation with valid data"""
        engine = DataGovernanceEngine(mock_config)
        is_valid, issues = engine.validate_schema(sample_enrollment_df)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_schema_missing_columns(self, mock_config, sample_enrollment_df):
        """Test schema validation with missing columns"""
        engine = DataGovernanceEngine(mock_config)
        
        # Remove required column
        df_missing = sample_enrollment_df.drop(columns=['age_0_5'])
        is_valid, issues = engine.validate_schema(df_missing)
        
        assert is_valid is False
        assert len(issues) > 0
        assert 'age_0_5' in str(issues[0])
    
    def test_validate_schema_negative_values(self, mock_config, sample_enrollment_df):
        """Test schema validation detects negative values"""
        engine = DataGovernanceEngine(mock_config)
        
        # Add negative values
        df_negative = sample_enrollment_df.copy()
        df_negative.loc[0, 'age_0_5'] = -100
        
        is_valid, issues = engine.validate_schema(df_negative)
        
        assert is_valid is False
        assert any('negative' in issue.lower() for issue in issues)
    
    def test_compute_completeness_full(self, mock_config, sample_enrollment_df):
        """Test completeness computation with complete data"""
        engine = DataGovernanceEngine(mock_config)
        completeness = engine.compute_completeness(sample_enrollment_df)
        
        assert completeness == 1.0
    
    def test_compute_completeness_partial(self, mock_config, sample_enrollment_df_with_missing):
        """Test completeness computation with missing data"""
        engine = DataGovernanceEngine(mock_config)
        completeness = engine.compute_completeness(sample_enrollment_df_with_missing)
        
        assert completeness < 1.0
        assert completeness > 0.0
    
    def test_compute_consistency(self, mock_config, sample_enrollment_df):
        """Test consistency computation"""
        engine = DataGovernanceEngine(mock_config)
        consistency = engine.compute_consistency(sample_enrollment_df)
        
        assert consistency == 1.0  # total_enrollment should match sum of age groups
    
    def test_compute_validity(self, mock_config, sample_enrollment_df):
        """Test validity computation"""
        engine = DataGovernanceEngine(mock_config)
        validity = engine.compute_validity(sample_enrollment_df)
        
        assert validity == 1.0  # All values should be valid
    
    def test_compute_dri(self, mock_config, sample_enrollment_df):
        """Test DRI computation"""
        engine = DataGovernanceEngine(mock_config)
        dri_result = engine.compute_dri(sample_enrollment_df)
        
        assert 'dri_score' in dri_result
        assert 'assessment' in dri_result
        assert 'components' in dri_result
        assert dri_result['dri_score'] >= 0.0
        assert dri_result['dri_score'] <= 1.0
        assert dri_result['assessment'] in ['PASS', 'FAIL']
    
    def test_compute_dri_pass(self, mock_config, sample_enrollment_df):
        """Test DRI passes with good quality data"""
        engine = DataGovernanceEngine(mock_config)
        dri_result = engine.compute_dri(sample_enrollment_df)
        
        # Complete data should pass
        assert dri_result['assessment'] == 'PASS'
        assert dri_result['dri_score'] >= 0.7
    
    def test_detect_extreme_values(self, mock_config, sample_enrollment_df_with_anomalies):
        """Test extreme value detection"""
        engine = DataGovernanceEngine(mock_config)
        df_with_flags = engine.detect_extreme_values(sample_enrollment_df_with_anomalies)
        
        assert 'has_extreme_values' in df_with_flags.columns
        assert df_with_flags['has_extreme_values'].sum() > 0
    
    def test_apply_k_anonymity(self, mock_config, sample_enrollment_df):
        """Test k-anonymity application"""
        engine = DataGovernanceEngine(mock_config)
        
        # Apply k-anonymity grouping by state and district
        df_anonymized = engine.apply_k_anonymity(
            sample_enrollment_df, 
            group_cols=['state', 'district']
        )
        
        # Check that small groups were removed
        group_sizes = df_anonymized.groupby(['state', 'district']).size()
        assert (group_sizes >= engine.k_anonymity).all()
    
    def test_generate_quality_report(self, mock_config, sample_enrollment_df):
        """Test quality report generation"""
        engine = DataGovernanceEngine(mock_config)
        report = engine.generate_quality_report(sample_enrollment_df)
        
        assert 'timestamp' in report
        assert 'total_records' in report
        assert 'schema_validation' in report
        assert 'dri' in report
        assert 'data_quality' in report
        assert 'recommendations' in report
        
        assert report['total_records'] == len(sample_enrollment_df)
    
    def test_generate_quality_report_structure(self, mock_config, sample_enrollment_df):
        """Test quality report has correct structure"""
        engine = DataGovernanceEngine(mock_config)
        report = engine.generate_quality_report(sample_enrollment_df)
        
        # Check DRI structure
        assert 'dri_score' in report['dri']
        assert 'components' in report['dri']
        assert 'completeness' in report['dri']['components']
        assert 'consistency' in report['dri']['components']
        assert 'validity' in report['dri']['components']
        
        # Check data quality structure
        assert 'missing_values' in report['data_quality']
        assert 'duplicate_records' in report['data_quality']
        assert 'extreme_values' in report['data_quality']


class TestDRIWeighting:
    """Test DRI weighting calculations"""
    
    def test_dri_weights_sum_to_one(self, mock_config):
        """Verify DRI weights sum to 1.0"""
        engine = DataGovernanceEngine(mock_config)
        total_weight = sum(engine.dri_weights.values())
        assert abs(total_weight - 1.0) < 0.001
    
    def test_dri_components_bounded(self, mock_config, sample_enrollment_df):
        """Verify all DRI components are between 0 and 1"""
        engine = DataGovernanceEngine(mock_config)
        dri_result = engine.compute_dri(sample_enrollment_df)
        
        for component, value in dri_result['components'].items():
            assert 0.0 <= value <= 1.0, f"{component} out of bounds: {value}"
