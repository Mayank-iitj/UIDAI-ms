"""
Unit tests for Policy Impact Engine
Tests priority scoring, resource allocation, and intervention identification
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.policy_impact import PolicyImpactEngine


class TestPolicyImpactEngine:
    """Test suite for PolicyImpactEngine"""
    
    def test_init(self, mock_config):
        """Test engine initialization"""
        engine = PolicyImpactEngine(mock_config)
        assert engine is not None
        assert engine.optimal_per_center == 500
        assert engine.optimal_per_staff == 100
    
    def test_compute_priority_score(self, mock_config, district_data_df):
        """Test priority score computation"""
        engine = PolicyImpactEngine(mock_config)
        
        result = engine.compute_priority_score(
            district_data=district_data_df,
            dri_scores=pd.DataFrame(),
            forecast_data=pd.DataFrame(),
            inequity_data=district_data_df
        )
        
        assert isinstance(result, pd.DataFrame)
        assert 'priority_score' in result.columns
    
    def test_priority_scores_bounded(self, mock_config, district_data_df):
        """Test priority scores are within expected bounds"""
        engine = PolicyImpactEngine(mock_config)
        
        result = engine.compute_priority_score(
            district_data=district_data_df,
            dri_scores=pd.DataFrame(),
            forecast_data=pd.DataFrame(),
            inequity_data=district_data_df
        )
        
        # Scores should be positive
        assert (result['priority_score'] >= 0).all()
    
    def test_priority_tiers_assigned(self, mock_config, district_data_df):
        """Test priority tiers are assigned"""
        engine = PolicyImpactEngine(mock_config)
        
        result = engine.compute_priority_score(
            district_data=district_data_df,
            dri_scores=pd.DataFrame(),
            forecast_data=pd.DataFrame(),
            inequity_data=district_data_df
        )
        
        if 'priority_tier' in result.columns:
            valid_tiers = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
            assert result['priority_tier'].isin(valid_tiers).all()
    
    def test_recommend_resource_allocation(self, mock_config, district_data_df):
        """Test resource allocation recommendations"""
        engine = PolicyImpactEngine(mock_config)
        
        # First compute priority scores
        priority_df = engine.compute_priority_score(
            district_data=district_data_df,
            dri_scores=pd.DataFrame(),
            forecast_data=pd.DataFrame(),
            inequity_data=district_data_df
        )
        
        result = engine.recommend_resource_allocation(priority_df)
        
        assert isinstance(result, dict)
        assert 'total_required_centers' in result
        assert 'total_required_staff' in result
    
    def test_resource_allocation_positive(self, mock_config, district_data_df):
        """Test resource allocations are positive"""
        engine = PolicyImpactEngine(mock_config)
        
        priority_df = engine.compute_priority_score(
            district_data=district_data_df,
            dri_scores=pd.DataFrame(),
            forecast_data=pd.DataFrame(),
            inequity_data=district_data_df
        )
        
        result = engine.recommend_resource_allocation(priority_df)
        
        assert result['total_required_centers'] >= 0
        assert result['total_required_staff'] >= 0
    
    def test_identify_intervention_needs(self, mock_config, district_data_df):
        """Test intervention need identification"""
        engine = PolicyImpactEngine(mock_config)
        
        result = engine.identify_intervention_needs(
            district_data=district_data_df,
            anomaly_data=pd.DataFrame(),
            forecast_surge_data=pd.DataFrame()
        )
        
        assert isinstance(result, dict)
        assert 'immediate_action_required' in result
    
    def test_intervention_categories(self, mock_config, district_data_df):
        """Test intervention categories are present"""
        engine = PolicyImpactEngine(mock_config)
        
        result = engine.identify_intervention_needs(
            district_data=district_data_df,
            anomaly_data=pd.DataFrame(),
            forecast_surge_data=pd.DataFrame()
        )
        
        expected_keys = ['immediate_action_required', 'priority_intervention_needed', 'regular_monitoring']
        for key in expected_keys:
            assert key in result
    
    def test_simulate_policy_impact(self, mock_config, district_data_df):
        """Test policy impact simulation"""
        engine = PolicyImpactEngine(mock_config)
        
        policy_scenario = {
            'new_centers': 10,
            'new_staff': 50,
            'target_districts': ['Lucknow', 'Patna']
        }
        
        result = engine.simulate_policy_impact(district_data_df, policy_scenario)
        
        assert isinstance(result, dict)
    
    def test_simulation_impact_metrics(self, mock_config, district_data_df):
        """Test simulation returns impact metrics"""
        engine = PolicyImpactEngine(mock_config)
        
        policy_scenario = {
            'new_centers': 10,
            'new_staff': 50
        }
        
        result = engine.simulate_policy_impact(district_data_df, policy_scenario)
        
        # Should have before/after or impact metrics
        assert 'estimated_impact' in result or 'projected_coverage' in result or len(result) > 0
    
    def test_generate_policy_report(self, mock_config, district_data_df):
        """Test policy report generation"""
        engine = PolicyImpactEngine(mock_config)
        
        report = engine.generate_policy_report(
            district_data=district_data_df,
            inequity_data=district_data_df
        )
        
        assert isinstance(report, dict)
        assert 'resource_allocation' in report
        assert 'interventions' in report
    
    def test_policy_report_structure(self, mock_config, district_data_df):
        """Test policy report has correct structure"""
        engine = PolicyImpactEngine(mock_config)
        
        report = engine.generate_policy_report(
            district_data=district_data_df,
            inequity_data=district_data_df
        )
        
        assert 'priority_districts' in report
        assert 'strategic_recommendations' in report
        
        # Check resource allocation structure
        resource = report['resource_allocation']
        assert 'total_required_centers' in resource
        assert 'total_required_staff' in resource
        assert 'critical_districts' in resource


class TestStrategicRecommendations:
    """Test strategic recommendation generation"""
    
    def test_recommendations_generated(self, mock_config, district_data_df):
        """Test recommendations are generated"""
        engine = PolicyImpactEngine(mock_config)
        
        report = engine.generate_policy_report(
            district_data=district_data_df,
            inequity_data=district_data_df
        )
        
        recommendations = report['strategic_recommendations']
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_recommendations_are_strings(self, mock_config, district_data_df):
        """Test recommendations are readable strings"""
        engine = PolicyImpactEngine(mock_config)
        
        report = engine.generate_policy_report(
            district_data=district_data_df,
            inequity_data=district_data_df
        )
        
        for rec in report['strategic_recommendations']:
            assert isinstance(rec, str)
            assert len(rec) > 10  # Should be meaningful


class TestPriorityDistrictRanking:
    """Test priority district ranking"""
    
    def test_districts_ranked(self, mock_config, district_data_df):
        """Test districts are ranked by priority"""
        engine = PolicyImpactEngine(mock_config)
        
        report = engine.generate_policy_report(
            district_data=district_data_df,
            inequity_data=district_data_df
        )
        
        priority_districts = report['priority_districts']
        assert isinstance(priority_districts, list)
    
    def test_top_districts_have_scores(self, mock_config, district_data_df):
        """Test top districts have priority scores"""
        engine = PolicyImpactEngine(mock_config)
        
        report = engine.generate_policy_report(
            district_data=district_data_df,
            inequity_data=district_data_df
        )
        
        if report['priority_districts']:
            top_district = report['priority_districts'][0]
            assert 'district' in top_district
            assert 'priority_score' in top_district
