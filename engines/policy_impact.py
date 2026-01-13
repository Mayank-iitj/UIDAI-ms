"""
Engine 5: Policy Impact Analysis
Provides actionable insights for UIDAI policy and resource planning
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import yaml
import logging

logger = logging.getLogger(__name__)


class PolicyImpactEngine:
    """Generate policy recommendations and impact analysis for UIDAI"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.config = config['policy_impact']
        self.schema = config['schema']
        
        # Priority scoring weights
        self.weights = self.config['priority_weights']
        
        # Resource allocation parameters
        self.optimal_enrollment_per_center = self.config['optimal_enrollment_per_center']
        self.optimal_enrollment_per_staff = self.config['optimal_enrollment_per_staff']
        
        # Intervention thresholds
        self.thresholds = self.config['intervention_thresholds']
        
        logger.info("Initialized PolicyImpactEngine")
    
    def compute_priority_score(
        self,
        district_data: pd.DataFrame,
        dri_scores: pd.DataFrame,
        forecast_data: pd.DataFrame,
        inequity_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute priority scores for districts
        
        Priority factors:
        1. Low enrollment rate
        2. High inequity
        3. High forecast demand
        4. Low Data Reliability Index (DRI)
        
        Args:
            district_data: District-level enrollment data
            dri_scores: DRI scores by district
            forecast_data: Forecasted demand by district
            inequity_data: Inequity metrics by district
        
        Returns:
            DataFrame with priority scores
        """
        # Merge all data
        priority_df = district_data.copy()
        
        # 1. Low enrollment score (normalized, inverse)
        national_median = district_data['total_enrollment'].median()
        priority_df['enrollment_score'] = 1 - (
            district_data['total_enrollment'] / district_data['total_enrollment'].max()
        )
        
        # 2. Inequity score
        if 'child_adult_ratio' in inequity_data.columns:
            priority_df = priority_df.merge(
                inequity_data[['state', 'district', 'child_adult_ratio']],
                on=['state', 'district'],
                how='left'
            )
            ratio_median = priority_df['child_adult_ratio'].median()
            priority_df['inequity_score'] = (
                (priority_df['child_adult_ratio'] - ratio_median).abs() / 
                priority_df['child_adult_ratio'].std()
            ).fillna(0)
        else:
            priority_df['inequity_score'] = 0
        
        # 3. Forecast demand score
        if not forecast_data.empty and 'forecasted_enrollment' in forecast_data.columns:
            priority_df = priority_df.merge(
                forecast_data[['state', 'district', 'forecasted_enrollment']],
                on=['state', 'district'],
                how='left'
            )
            priority_df['forecast_score'] = (
                priority_df['forecasted_enrollment'] / 
                priority_df['forecasted_enrollment'].max()
            ).fillna(0)
        else:
            priority_df['forecast_score'] = 0
        
        # 4. DRI score (inverse - lower DRI = higher priority)
        if not dri_scores.empty and 'dri_score' in dri_scores.columns:
            priority_df = priority_df.merge(
                dri_scores[['state', 'district', 'dri_score']],
                on=['state', 'district'],
                how='left'
            )
            priority_df['dri_priority_score'] = 1 - priority_df['dri_score'].fillna(0.7)
        else:
            priority_df['dri_priority_score'] = 0
        
        # Compute weighted priority score
        priority_df['priority_score'] = (
            self.weights['low_enrollment'] * priority_df['enrollment_score'] +
            self.weights['high_inequity'] * priority_df['inequity_score'] +
            self.weights['high_forecast_demand'] * priority_df['forecast_score'] +
            self.weights['low_dri'] * priority_df['dri_priority_score']
        )
        
        # Normalize to 0-100
        priority_df['priority_score'] = (
            (priority_df['priority_score'] / priority_df['priority_score'].max()) * 100
        ).round(2)
        
        # Priority tier
        priority_df['priority_tier'] = pd.cut(
            priority_df['priority_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['Low', 'Medium', 'High', 'Critical']
        )
        
        logger.info(f"Computed priority scores for {len(priority_df)} districts")
        
        return priority_df
    
    def recommend_resource_allocation(self, priority_df: pd.DataFrame) -> Dict:
        """
        Recommend optimal resource allocation based on priority scores
        
        Args:
            priority_df: DataFrame with priority scores
        
        Returns:
            Dictionary with resource recommendations
        """
        # Calculate required resources
        priority_df['required_centers'] = np.ceil(
            priority_df['total_enrollment'] / self.optimal_enrollment_per_center
        ).astype(int)
        
        priority_df['required_staff'] = np.ceil(
            priority_df['total_enrollment'] / self.optimal_enrollment_per_staff
        ).astype(int)
        
        # Aggregate by priority tier
        tier_summary = priority_df.groupby('priority_tier').agg({
            'total_enrollment': 'sum',
            'required_centers': 'sum',
            'required_staff': 'sum',
            'state': 'count'
        }).rename(columns={'state': 'num_districts'})
        
        # Top priority districts
        top_priority = priority_df.nlargest(50, 'priority_score')[
            ['state', 'district', 'total_enrollment', 'priority_score', 
             'priority_tier', 'required_centers', 'required_staff']
        ].to_dict('records')
        
        recommendations = {
            'summary_by_tier': tier_summary.to_dict('index'),
            'total_required_centers': int(priority_df['required_centers'].sum()),
            'total_required_staff': int(priority_df['required_staff'].sum()),
            'top_priority_districts': top_priority,
            'critical_districts': len(priority_df[priority_df['priority_tier'] == 'Critical']),
            'allocation_strategy': self._generate_allocation_strategy(tier_summary)
        }
        
        logger.info(f"Generated resource allocation for {len(priority_df)} districts")
        
        return recommendations
    
    def identify_intervention_needs(
        self,
        district_data: pd.DataFrame,
        anomaly_data: pd.DataFrame,
        forecast_surge_data: pd.DataFrame
    ) -> Dict:
        """
        Identify districts requiring immediate intervention
        
        Intervention triggers:
        1. Low enrollment rate
        2. High inequity
        3. Forecast surge
        4. Data quality issues
        
        Args:
            district_data: District-level enrollment
            anomaly_data: Anomaly detection results
            forecast_surge_data: Forecast surge predictions
        
        Returns:
            Dictionary with intervention recommendations
        """
        interventions = []
        
        # 1. Low enrollment districts
        national_avg = district_data['total_enrollment'].mean()
        low_enrollment_threshold = national_avg * self.thresholds['enrollment_rate_low']
        
        low_enrollment = district_data[
            district_data['total_enrollment'] < low_enrollment_threshold
        ][['state', 'district', 'total_enrollment']].copy()
        
        low_enrollment['intervention_type'] = 'Low Enrollment'
        low_enrollment['urgency'] = 'High'
        low_enrollment['recommended_action'] = 'Increase outreach and enrollment campaigns'
        
        # 2. High inequity districts
        if 'child_adult_ratio' in district_data.columns:
            high_inequity = district_data[
                district_data['child_adult_ratio'] > self.thresholds['inequity_high']
            ][['state', 'district', 'total_enrollment']].copy()
            
            high_inequity['intervention_type'] = 'High Inequity'
            high_inequity['urgency'] = 'Medium'
            high_inequity['recommended_action'] = 'Investigate demographic disparities'
        else:
            high_inequity = pd.DataFrame()
        
        # 3. Forecast surge districts
        if not forecast_surge_data.empty and 'surge_detected' in forecast_surge_data.columns:
            surge_districts = forecast_surge_data[
                forecast_surge_data['surge_detected'] == True
            ][['state', 'district', 'total_enrollment']].copy()
            
            surge_districts['intervention_type'] = 'Forecast Surge'
            surge_districts['urgency'] = 'Critical'
            surge_districts['recommended_action'] = 'Prepare additional capacity immediately'
        else:
            surge_districts = pd.DataFrame()
        
        # 4. Data quality issues
        if not anomaly_data.empty and 'severity_score' in anomaly_data.columns:
            quality_issues = anomaly_data[
                anomaly_data['severity_score'] >= 3
            ][['state', 'district', 'total_enrollment']].copy()
            
            quality_issues['intervention_type'] = 'Data Quality'
            quality_issues['urgency'] = 'High'
            quality_issues['recommended_action'] = 'Audit enrollment processes and data collection'
        else:
            quality_issues = pd.DataFrame()
        
        # Combine all interventions
        all_interventions = pd.concat([
            low_enrollment, 
            high_inequity, 
            surge_districts, 
            quality_issues
        ], ignore_index=True)
        
        # Group by urgency
        urgency_summary = all_interventions.groupby('urgency').size().to_dict()
        
        result = {
            'total_interventions': len(all_interventions),
            'by_urgency': urgency_summary,
            'by_type': all_interventions.groupby('intervention_type').size().to_dict(),
            'intervention_list': all_interventions.to_dict('records')[:100],  # Top 100
            'immediate_action_required': len(all_interventions[all_interventions['urgency'] == 'Critical'])
        }
        
        logger.info(f"Identified {len(all_interventions)} intervention needs")
        
        return result
    
    def simulate_policy_impact(
        self,
        baseline_data: pd.DataFrame,
        policy_scenario: Dict
    ) -> Dict:
        """
        Simulate the impact of policy changes
        
        Args:
            baseline_data: Current enrollment data
            policy_scenario: Dictionary with policy parameters
                - 'enrollment_increase_pct': Expected enrollment increase (%)
                - 'target_districts': List of target districts
                - 'resource_allocation': Additional resources
        
        Returns:
            Dictionary with impact simulation results
        """
        simulated = baseline_data.copy()
        
        # Apply enrollment increase
        increase_pct = policy_scenario.get('enrollment_increase_pct', 10) / 100
        target_districts = policy_scenario.get('target_districts', 'all')
        
        if target_districts == 'all':
            simulated['simulated_enrollment'] = (
                simulated['total_enrollment'] * (1 + increase_pct)
            )
        else:
            # Apply to specific districts
            mask = simulated['district'].isin(target_districts)
            simulated.loc[mask, 'simulated_enrollment'] = (
                simulated.loc[mask, 'total_enrollment'] * (1 + increase_pct)
            )
            simulated.loc[~mask, 'simulated_enrollment'] = simulated.loc[~mask, 'total_enrollment']
        
        # Calculate impact
        baseline_total = simulated['total_enrollment'].sum()
        simulated_total = simulated['simulated_enrollment'].sum()
        absolute_increase = simulated_total - baseline_total
        
        # Resource implications
        additional_centers = np.ceil(
            absolute_increase / self.optimal_enrollment_per_center
        )
        additional_staff = np.ceil(
            absolute_increase / self.optimal_enrollment_per_staff
        )
        
        result = {
            'scenario': policy_scenario,
            'baseline_enrollment': int(baseline_total),
            'simulated_enrollment': int(simulated_total),
            'absolute_increase': int(absolute_increase),
            'percentage_increase': round((absolute_increase / baseline_total) * 100, 2),
            'resource_requirements': {
                'additional_centers': int(additional_centers),
                'additional_staff': int(additional_staff)
            },
            'districts_affected': len(simulated[simulated['simulated_enrollment'] > simulated['total_enrollment']])
        }
        
        logger.info(f"Simulated policy impact: +{result['percentage_increase']}% enrollment")
        
        return result
    
    def generate_policy_report(
        self,
        district_data: pd.DataFrame,
        dri_data: pd.DataFrame = pd.DataFrame(),
        forecast_data: pd.DataFrame = pd.DataFrame(),
        inequity_data: pd.DataFrame = pd.DataFrame(),
        anomaly_data: pd.DataFrame = pd.DataFrame()
    ) -> Dict:
        """Generate comprehensive policy impact report"""
        # Compute priority scores
        priority_df = self.compute_priority_score(
            district_data, dri_data, forecast_data, inequity_data
        )
        
        # Resource allocation
        resource_rec = self.recommend_resource_allocation(priority_df)
        
        # Intervention needs
        interventions = self.identify_intervention_needs(
            district_data, anomaly_data, forecast_data
        )
        
        # Policy simulation example
        policy_scenario = {
            'enrollment_increase_pct': 15,
            'target_districts': 'all',
            'policy_name': 'Universal Outreach Campaign'
        }
        impact_sim = self.simulate_policy_impact(district_data, policy_scenario)
        
        report = {
            'priority_districts': priority_df.nlargest(20, 'priority_score').to_dict('records'),
            'priority_tier_distribution': priority_df['priority_tier'].value_counts().to_dict(),
            'resource_allocation': resource_rec,
            'interventions': interventions,
            'policy_simulation': impact_sim,
            'strategic_recommendations': self._generate_strategic_recommendations(
                priority_df, resource_rec, interventions
            )
        }
        
        return report
    
    def _generate_allocation_strategy(self, tier_summary: pd.DataFrame) -> List[str]:
        """Generate resource allocation strategy"""
        strategy = []
        
        if 'Critical' in tier_summary.index:
            critical = tier_summary.loc['Critical']
            strategy.append(
                f"PRIORITY 1: Allocate {critical['required_centers']} centers and "
                f"{critical['required_staff']} staff to {critical['num_districts']} critical districts"
            )
        
        if 'High' in tier_summary.index:
            high = tier_summary.loc['High']
            strategy.append(
                f"PRIORITY 2: Deploy {high['required_centers']} centers to "
                f"{high['num_districts']} high-priority districts"
            )
        
        if not strategy:
            strategy.append("No critical resource allocation needs identified")
        
        return strategy
    
    def _generate_strategic_recommendations(
        self,
        priority_df: pd.DataFrame,
        resource_rec: Dict,
        interventions: Dict
    ) -> List[str]:
        """Generate high-level strategic recommendations"""
        recommendations = []
        
        # Critical districts
        critical_count = resource_rec['critical_districts']
        if critical_count > 0:
            recommendations.append(
                f"URGENT: {critical_count} districts require immediate attention. "
                "Deploy rapid response teams for enrollment acceleration."
            )
        
        # Resource gaps
        total_centers = resource_rec['total_required_centers']
        if total_centers > 1000:
            recommendations.append(
                f"Large-scale infrastructure needed: {total_centers} enrollment centers. "
                "Consider phased rollout strategy."
            )
        
        # Intervention needs
        immediate_action = interventions['immediate_action_required']
        if immediate_action > 0:
            recommendations.append(
                f"{immediate_action} districts need critical interventions. "
                "Establish dedicated task force."
            )
        
        # General recommendation
        recommendations.append(
            "Implement continuous monitoring system to track policy impact and adjust strategies."
        )
        
        return recommendations


def main():
    """Test the Policy Impact Engine"""
    from utils.data_loader import UidaiDataLoader
    
    # Load data
    loader = UidaiDataLoader()
    df = loader.load_all_data()
    
    # Prepare district data
    age_cols = ['age_0_5', 'age_5_17', 'age_18_plus']
    district_data = df.groupby(['state', 'district'])[
        age_cols + ['total_enrollment']
    ].sum().reset_index()
    
    # Run policy impact analysis
    engine = PolicyImpactEngine()
    report = engine.generate_policy_report(district_data)
    
    print("\n" + "="*60)
    print("POLICY IMPACT ANALYSIS REPORT")
    print("="*60)
    
    print(f"\n--- Priority District Distribution ---")
    for tier, count in report['priority_tier_distribution'].items():
        print(f"{tier}: {count} districts")
    
    print(f"\n--- Top 5 Priority Districts ---")
    for i, district in enumerate(report['priority_districts'][:5], 1):
        print(f"{i}. {district['state']} - {district['district']}")
        print(f"   Priority Score: {district['priority_score']:.1f} ({district['priority_tier']})")
    
    print(f"\n--- Resource Allocation Summary ---")
    print(f"Total Centers Required: {report['resource_allocation']['total_required_centers']:,}")
    print(f"Total Staff Required: {report['resource_allocation']['total_required_staff']:,}")
    print(f"Critical Districts: {report['resource_allocation']['critical_districts']}")
    
    print(f"\n--- Intervention Needs ---")
    print(f"Total Interventions: {report['interventions']['total_interventions']}")
    print(f"Immediate Action Required: {report['interventions']['immediate_action_required']}")
    print("\nBy Urgency:")
    for urgency, count in report['interventions']['by_urgency'].items():
        print(f"  {urgency}: {count}")
    
    print(f"\n--- Policy Simulation ---")
    sim = report['policy_simulation']
    print(f"Scenario: {sim['scenario']['policy_name']}")
    print(f"Expected Increase: {sim['percentage_increase']}%")
    print(f"Additional Resources Needed:")
    print(f"  Centers: {sim['resource_requirements']['additional_centers']}")
    print(f"  Staff: {sim['resource_requirements']['additional_staff']}")
    
    print(f"\n--- Strategic Recommendations ---")
    for i, rec in enumerate(report['strategic_recommendations'], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
