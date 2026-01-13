"""
Engine 2: Descriptive Analytics
Provides comprehensive descriptive insights from enrollment data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import yaml
import logging
from sklearn.cluster import KMeans
from scipy import stats

logger = logging.getLogger(__name__)


class DescriptiveAnalyticsEngine:
    """Generate descriptive insights and patterns from UIDAI enrollment data"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize with configuration"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.config = config['descriptive_analytics']
        self.schema = config['schema']
        
        # Configuration parameters
        self.top_n_states = self.config['top_n_states']
        self.top_n_districts = self.config['top_n_districts']
        self.n_clusters = self.config['n_clusters']
        self.child_adult_ratio = self.config['child_adult_ratio_threshold']
        self.underserved_threshold = self.config['underserved_enrollment_threshold']
        
        logger.info("Initialized DescriptiveAnalyticsEngine")
    
    def compute_temporal_trends(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute enrollment trends over time
        
        Returns:
            DataFrame with monthly aggregations
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # Group by year_month
        monthly = df.groupby('year_month')[age_cols + ['total_enrollment']].sum()
        
        # Add growth rates
        for col in age_cols + ['total_enrollment']:
            monthly[f'{col}_mom_change'] = monthly[col].pct_change() * 100
            monthly[f'{col}_yoy_change'] = monthly[col].pct_change(periods=12) * 100
        
        # Add moving averages
        monthly['total_ma_3m'] = monthly['total_enrollment'].rolling(window=3).mean()
        monthly['total_ma_6m'] = monthly['total_enrollment'].rolling(window=6).mean()
        
        logger.info(f"Computed temporal trends for {len(monthly)} months")
        
        return monthly.reset_index()
    
    def compute_geographic_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze geographic distribution of enrollments
        
        Returns:
            Dictionary with state and district level insights
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # State-level analysis
        state_totals = df.groupby('state')[age_cols + ['total_enrollment']].sum()
        state_totals = state_totals.sort_values('total_enrollment', ascending=False)
        
        top_states = state_totals.head(self.top_n_states)
        
        # District-level analysis
        district_totals = df.groupby(['state', 'district'])[
            age_cols + ['total_enrollment']
        ].sum().reset_index()
        district_totals = district_totals.sort_values('total_enrollment', ascending=False)
        
        top_districts = district_totals.head(self.top_n_districts)
        
        # Geographic concentration (Gini coefficient)
        gini = self._compute_gini(state_totals['total_enrollment'].values)
        
        result = {
            'top_states': top_states.to_dict('index'),
            'top_districts': top_districts.to_dict('records'),
            'concentration': {
                'gini_coefficient': round(gini, 3),
                'interpretation': self._interpret_gini(gini)
            },
            'coverage': {
                'num_states': df['state'].nunique(),
                'num_districts': df['district'].nunique(),
                'num_pincodes': df['pincode'].nunique()
            }
        }
        
        logger.info(f"Analyzed {result['coverage']['num_states']} states and {result['coverage']['num_districts']} districts")
        
        return result
    
    def analyze_age_demographics(self, df: pd.DataFrame) -> Dict:
        """
        Analyze age group distribution and patterns
        
        Returns:
            Dictionary with age demographic insights
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # Overall totals
        totals = {col: int(df[col].sum()) for col in age_cols}
        grand_total = sum(totals.values())
        
        # Proportions
        proportions = {col: round((totals[col] / grand_total) * 100, 2) for col in age_cols}
        
        # State-level age distribution
        state_age = df.groupby('state')[age_cols].sum()
        state_age['total'] = state_age.sum(axis=1)
        
        for col in age_cols:
            state_age[f'pct_{col}'] = (state_age[col] / state_age['total'] * 100).round(2)
        
        # Find states with unusual age distributions
        unusual_states = []
        
        # Child-heavy states (high proportion of age_0_5 + age_5_17)
        if 'age_0_5' in age_cols and 'age_5_17' in age_cols:
            state_age['child_pct'] = state_age['pct_age_0_5'] + state_age['pct_age_5_17']
            child_heavy = state_age.nlargest(5, 'child_pct')[['child_pct']]
            unusual_states.append({
                'category': 'child_heavy',
                'states': child_heavy.to_dict('index')
            })
        
        # Adult-heavy states
        if 'age_18_greater' in age_cols:
            adult_heavy = state_age.nlargest(5, 'pct_age_18_greater')[['pct_age_18_greater']]
            unusual_states.append({
                'category': 'adult_heavy',
                'states': adult_heavy.to_dict('index')
            })
        
        result = {
            'overall': {
                'totals': totals,
                'proportions': proportions,
                'grand_total': grand_total
            },
            'unusual_distributions': unusual_states,
            'state_summary': state_age.to_dict('index')
        }
        
        logger.info(f"Analyzed age demographics across {len(state_age)} states")
        
        return result
    
    def detect_inequities(self, df: pd.DataFrame) -> Dict:
        """
        Detect enrollment inequities and underserved areas
        
        Returns:
            Dictionary with inequity analysis
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # District-level analysis
        district_data = df.groupby(['state', 'district'])[
            age_cols + ['total_enrollment']
        ].sum().reset_index()
        
        # Calculate child-to-adult ratio
        if 'age_0_5' in age_cols and 'age_5_17' in age_cols and 'age_18_greater' in age_cols:
            district_data['children'] = district_data['age_0_5'] + district_data['age_5_17']
            district_data['child_adult_ratio'] = district_data['children'] / district_data['age_18_greater'].replace(0, np.nan)
            
            # Flag high child-to-adult ratio (may indicate data quality issues or demographics)
            high_ratio = district_data[
                district_data['child_adult_ratio'] > self.child_adult_ratio
            ].sort_values('child_adult_ratio', ascending=False)
        else:
            high_ratio = pd.DataFrame()
        
        # Identify underserved districts (low enrollment relative to median)
        median_enrollment = district_data['total_enrollment'].median()
        underserved_threshold = median_enrollment * self.underserved_threshold
        
        underserved = district_data[
            district_data['total_enrollment'] < underserved_threshold
        ].sort_values('total_enrollment')
        
        # Calculate enrollment inequality (coefficient of variation)
        cv = district_data['total_enrollment'].std() / district_data['total_enrollment'].mean()
        
        result = {
            'summary': {
                'total_districts': len(district_data),
                'median_enrollment': int(median_enrollment),
                'coefficient_of_variation': round(cv, 3)
            },
            'high_child_ratio_districts': high_ratio.head(20).to_dict('records') if not high_ratio.empty else [],
            'underserved_districts': underserved.head(50).to_dict('records'),
            'recommendations': self._generate_inequity_recommendations(len(underserved), cv)
        }
        
        logger.info(f"Identified {len(underserved)} underserved districts")
        
        return result
    
    def perform_pincode_clustering(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Cluster PIN codes by enrollment patterns
        
        Returns:
            (DataFrame with cluster assignments, cluster summary)
        """
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        # Aggregate by PIN code
        pin_data = df.groupby('pincode')[age_cols].sum().reset_index()
        
        # Remove zero-enrollment PINs
        pin_data = pin_data[pin_data[age_cols].sum(axis=1) > 0]
        
        if len(pin_data) < self.n_clusters:
            logger.warning(f"Not enough PIN codes for clustering ({len(pin_data)} < {self.n_clusters})")
            return pin_data, {}
        
        # Normalize features with error handling for Python 3.14 numpy compatibility
        X = pin_data[age_cols].values
        try:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_normalized = scaler.fit_transform(X)
        except:
            # Fallback to manual normalization
            X_mean = X.mean(axis=0)
            X_std = np.array([X[:, i].std() for i in range(X.shape[1])])
            X_normalized = (X - X_mean) / (X_std + 1e-8)
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        pin_data['cluster'] = kmeans.fit_predict(X_normalized)
        
        # Compute cluster statistics
        cluster_summary = {}
        for cluster_id in range(self.n_clusters):
            cluster_pins = pin_data[pin_data['cluster'] == cluster_id]
            
            cluster_summary[f'cluster_{cluster_id}'] = {
                'size': len(cluster_pins),
                'total_pincodes': len(cluster_pins),
                'avg_enrollment': {
                    col: int(cluster_pins[col].mean()) for col in age_cols
                },
                'total_enrollment': {
                    col: int(cluster_pins[col].sum()) for col in age_cols
                },
                'characteristics': self._characterize_cluster(cluster_pins, age_cols)
            }
        
        logger.info(f"Clustered {len(pin_data)} PIN codes into {self.n_clusters} groups")
        
        return pin_data, cluster_summary
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive summary statistics"""
        age_cols = [col for col in self.schema['age_groups'] if col in df.columns]
        
        summary = {}
        
        for col in age_cols + ['total_enrollment']:
            summary[col] = {
                'count': int(df[col].count()),
                'sum': int(df[col].sum()),
                'mean': round(df[col].mean(), 2),
                'median': round(df[col].median(), 2),
                'std': round(df[col].std(), 2),
                'min': int(df[col].min()),
                'max': int(df[col].max()),
                'percentiles': {
                    '25': round(df[col].quantile(0.25), 2),
                    '50': round(df[col].quantile(0.50), 2),
                    '75': round(df[col].quantile(0.75), 2),
                    '90': round(df[col].quantile(0.90), 2),
                    '95': round(df[col].quantile(0.95), 2),
                    '99': round(df[col].quantile(0.99), 2)
                }
            }
        
        return summary
    
    def _compute_gini(self, values: np.ndarray) -> float:
        """Compute Gini coefficient for inequality measurement"""
        sorted_values = np.sort(values)
        n = len(values)
        index = np.arange(1, n + 1)
        gini = (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n
        return gini
    
    def _interpret_gini(self, gini: float) -> str:
        """Interpret Gini coefficient"""
        if gini < 0.3:
            return "Low inequality - relatively uniform distribution"
        elif gini < 0.5:
            return "Moderate inequality - some concentration"
        else:
            return "High inequality - significant concentration"
    
    def _characterize_cluster(self, cluster_data: pd.DataFrame, age_cols: List[str]) -> str:
        """Characterize a cluster based on enrollment patterns"""
        total = cluster_data[age_cols].sum(axis=1).mean()
        proportions = {col: cluster_data[col].sum() for col in age_cols}
        dominant_group = max(proportions, key=proportions.get)
        
        if total > 10000:
            size_char = "High-enrollment"
        elif total > 1000:
            size_char = "Medium-enrollment"
        else:
            size_char = "Low-enrollment"
        
        group_char = dominant_group.replace('age_', '').replace('_', '-')
        
        return f"{size_char}, {group_char}-dominant"
    
    def _generate_inequity_recommendations(self, num_underserved: int, cv: float) -> List[str]:
        """Generate recommendations based on inequity analysis"""
        recommendations = []
        
        if num_underserved > 100:
            recommendations.append(
                f"CRITICAL: {num_underserved} districts identified as underserved. "
                "Prioritize resource allocation and outreach programs."
            )
        elif num_underserved > 50:
            recommendations.append(
                f"ATTENTION: {num_underserved} districts show low enrollment. "
                "Consider targeted interventions."
            )
        
        if cv > 1.0:
            recommendations.append(
                f"High enrollment inequality detected (CV={cv:.2f}). "
                "Geographic disparities require policy intervention."
            )
        
        if not recommendations:
            recommendations.append("Enrollment distribution is relatively equitable.")
        
        return recommendations


def main():
    """Test the Descriptive Analytics Engine"""
    from utils.data_loader import UidaiDataLoader
    
    # Load data
    loader = UidaiDataLoader()
    df = loader.load_all_data()
    
    # Run descriptive analytics
    engine = DescriptiveAnalyticsEngine()
    
    print("\n" + "="*60)
    print("DESCRIPTIVE ANALYTICS REPORT")
    print("="*60)
    
    # Temporal trends
    print("\n--- Computing Temporal Trends ---")
    trends = engine.compute_temporal_trends(df)
    print(f"Analyzed {len(trends)} months of data")
    print("\nRecent trends (last 3 months):")
    print(trends[['year_month', 'total_enrollment', 'total_enrollment_mom_change']].tail(3))
    
    # Geographic patterns
    print("\n--- Analyzing Geographic Patterns ---")
    geo = engine.compute_geographic_patterns(df)
    print(f"Coverage: {geo['coverage']['num_states']} states, {geo['coverage']['num_districts']} districts")
    print(f"Gini Coefficient: {geo['concentration']['gini_coefficient']} - {geo['concentration']['interpretation']}")
    
    # Age demographics
    print("\n--- Age Demographics ---")
    age_demo = engine.analyze_age_demographics(df)
    print("Overall proportions:")
    for age_group, pct in age_demo['overall']['proportions'].items():
        print(f"  {age_group}: {pct}%")
    
    # Inequities
    print("\n--- Inequity Detection ---")
    inequities = engine.detect_inequities(df)
    print(f"Total districts: {inequities['summary']['total_districts']}")
    print(f"Median enrollment: {inequities['summary']['median_enrollment']:,}")
    print(f"Underserved districts: {len(inequities['underserved_districts'])}")
    print("\nRecommendations:")
    for rec in inequities['recommendations']:
        print(f"  • {rec}")
    
    # PIN code clustering
    print("\n--- PIN Code Clustering ---")
    pin_clusters, cluster_summary = engine.perform_pincode_clustering(df)
    if cluster_summary:
        print(f"Clustered {len(pin_clusters)} PIN codes into {len(cluster_summary)} groups")
        for cluster_name, info in list(cluster_summary.items())[:3]:
            print(f"\n{cluster_name}: {info['total_pincodes']} PINs - {info['characteristics']}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
