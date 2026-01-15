"""
Unit tests for Descriptive Analytics Engine
Tests temporal trends, geographic patterns, demographics, and clustering
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.descriptive_analytics import DescriptiveAnalyticsEngine


class TestDescriptiveAnalyticsEngine:
    """Test suite for DescriptiveAnalyticsEngine"""
    
    def test_init(self, mock_config):
        """Test engine initialization"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        assert engine is not None
    
    def test_compute_temporal_trends(self, mock_config, sample_enrollment_df):
        """Test temporal trend computation"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        trends = engine.compute_temporal_trends(sample_enrollment_df)
        
        assert isinstance(trends, pd.DataFrame)
        assert 'year_month' in trends.columns
        assert len(trends) > 0
    
    def test_temporal_trends_contains_aggregations(self, mock_config, sample_enrollment_df):
        """Test temporal trends contain expected aggregations"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        trends = engine.compute_temporal_trends(sample_enrollment_df)
        
        # Should have age group columns
        assert 'age_0_5' in trends.columns
        assert 'age_5_17' in trends.columns
        assert 'age_18_greater' in trends.columns
        assert 'total_enrollment' in trends.columns
    
    def test_compute_geographic_patterns(self, mock_config, sample_enrollment_df):
        """Test geographic pattern computation"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        patterns = engine.compute_geographic_patterns(sample_enrollment_df)
        
        assert isinstance(patterns, dict)
        assert 'top_states' in patterns
        assert 'top_districts' in patterns
        assert 'coverage' in patterns
    
    def test_geographic_coverage(self, mock_config, sample_enrollment_df):
        """Test geographic coverage metrics"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        patterns = engine.compute_geographic_patterns(sample_enrollment_df)
        
        coverage = patterns['coverage']
        assert 'num_states' in coverage
        assert 'num_districts' in coverage
        assert 'num_pincodes' in coverage
        
        # Should match actual unique values
        assert coverage['num_states'] == sample_enrollment_df['state'].nunique()
    
    def test_analyze_age_demographics(self, mock_config, sample_enrollment_df):
        """Test age demographic analysis"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        demographics = engine.analyze_age_demographics(sample_enrollment_df)
        
        assert isinstance(demographics, dict)
        assert 'overall' in demographics
        assert 'ratios' in demographics
    
    def test_age_demographics_totals(self, mock_config, sample_enrollment_df):
        """Test age demographics contain correct totals"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        demographics = engine.analyze_age_demographics(sample_enrollment_df)
        
        overall = demographics['overall']
        assert 'totals' in overall
        assert 'proportions' in overall
        
        totals = overall['totals']
        assert totals['age_0_5'] == sample_enrollment_df['age_0_5'].sum()
    
    def test_age_ratios(self, mock_config, sample_enrollment_df):
        """Test child-adult ratio computation"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        demographics = engine.analyze_age_demographics(sample_enrollment_df)
        
        ratios = demographics['ratios']
        assert 'child_adult_ratio' in ratios
        assert ratios['child_adult_ratio'] > 0
    
    def test_detect_inequities(self, mock_config, sample_enrollment_df):
        """Test inequity detection"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        inequities = engine.detect_inequities(sample_enrollment_df)
        
        assert isinstance(inequities, dict)
        assert 'underserved_districts' in inequities
        assert 'gini_coefficient' in inequities
    
    def test_gini_coefficient_bounds(self, mock_config, sample_enrollment_df):
        """Test Gini coefficient is within valid bounds"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        inequities = engine.detect_inequities(sample_enrollment_df)
        
        gini = inequities['gini_coefficient']
        assert 0.0 <= gini <= 1.0
    
    def test_perform_pincode_clustering(self, mock_config, sample_enrollment_df):
        """Test PIN code clustering"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        clusters, summary = engine.perform_pincode_clustering(sample_enrollment_df)
        
        assert isinstance(clusters, pd.DataFrame)
        assert 'cluster' in clusters.columns
        assert isinstance(summary, dict)
    
    def test_clustering_assigns_all_pincodes(self, mock_config, sample_enrollment_df):
        """Test clustering assigns clusters to all records"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        clusters, _ = engine.perform_pincode_clustering(sample_enrollment_df)
        
        # No NaN clusters
        assert clusters['cluster'].notna().all()
    
    def test_generate_summary_statistics(self, mock_config, sample_enrollment_df):
        """Test summary statistics generation"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        stats = engine.generate_summary_statistics(sample_enrollment_df)
        
        assert isinstance(stats, dict)
        assert 'total_enrollments' in stats
        assert 'date_range' in stats


class TestGiniCoefficient:
    """Test Gini coefficient calculation"""
    
    def test_gini_perfect_equality(self, mock_config):
        """Test Gini = 0 for perfect equality"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        
        # All same values = perfect equality
        values = np.array([100, 100, 100, 100, 100])
        gini = engine._compute_gini(values)
        
        assert abs(gini) < 0.01  # Should be ~0
    
    def test_gini_high_inequality(self, mock_config):
        """Test high Gini for unequal distribution"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        
        # One has everything, rest have nothing
        values = np.array([0, 0, 0, 0, 1000])
        gini = engine._compute_gini(values)
        
        assert gini > 0.7  # High inequality
    
    def test_gini_interpretation(self, mock_config):
        """Test Gini interpretation"""
        engine = DescriptiveAnalyticsEngine(mock_config)
        
        low_interp = engine._interpret_gini(0.2)
        high_interp = engine._interpret_gini(0.8)
        
        assert 'low' in low_interp.lower() or 'equal' in low_interp.lower()
        assert 'high' in high_interp.lower() or 'concentration' in high_interp.lower()
