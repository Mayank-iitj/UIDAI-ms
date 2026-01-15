"""
Visualization Engine for UIDAI Intelligence System
Generates static charts and graphs for reports using Matplotlib and Seaborn
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class Visualizer:
    """Generates analytical visualizations for the intelligence report"""
    
    def __init__(self, output_dir: str = "./outputs/visualizations"):
        """Initialize visualizer"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("husl")
        
        # Configure fonts and sizes
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12
        
    def generate_all_plots(self, df: pd.DataFrame, analysis_results: Dict) -> Dict[str, str]:
        """
        Generate all required plots for the report
        
        Args:
            df: Main dataframe
            analysis_results: Dictionary containing results from all engines
            
        Returns:
            Dictionary of plot paths keyed by plot name
        """
        plot_paths = {}
        
        # Helper to safely generate plot
        def safe_plot(name, func, *args):
            try:
                path = func(*args)
                if path:
                    plot_paths[name] = path
            except Exception as e:
                logger.error(f"Failed to generate plot {name}: {e}")

        # 1. Temporal Trends
        safe_plot('temporal_trend', self.plot_temporal_trend, df)
        
        # 2. Age Distribution
        safe_plot('age_distribution', self.plot_age_distribution, df)
        
        # 3. Anomaly Distribution
        safe_plot('anomalies', self.plot_anomaly_distribution, analysis_results)
        
        # 4. Forecast
        safe_plot('forecast', self.plot_forecast, analysis_results)
        
        # 5. Policy Impact
        safe_plot('policy', self.plot_policy_impact, analysis_results)
        
        # 6. Child-Adult Imbalance (Hackathon)
        safe_plot('child_adult_imbalance', self.plot_child_adult_imbalance, analysis_results)
        
        # 7. Priority Districts (Hackathon)
        safe_plot('priority_districts', self.plot_district_priority, analysis_results)
        
        logger.info(f"Generated {len(plot_paths)} visualization plots")
            
        return plot_paths
        
    def plot_temporal_trend(self, df: pd.DataFrame) -> str:
        """Plot monthly enrollment trends"""
        plt.figure(figsize=(12, 6))
        
        daily_trends = df.groupby('date')['total_enrollment'].sum()
        
        # Plot actual data
        plt.plot(daily_trends.index, daily_trends.values, 
                linewidth=2, label='Daily Enrollment', color='#3498db')
                
        # Add moving average
        ma_30 = daily_trends.rolling(window=30).mean()
        plt.plot(ma_30.index, ma_30.values, 
                linewidth=2, label='30-Day Moving Avg', color='#e74c3c', linestyle='--')
        
        plt.title('National Enrollment Trends (2025)', fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Enrollments')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        output_path = self.output_dir / "temporal_trend.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)
        
    def plot_age_distribution(self, df: pd.DataFrame) -> str:
        """Plot age group distribution"""
        plt.figure(figsize=(10, 6))
        
        # Identify age columns
        age_cols = [c for c in df.columns if 'age_' in c and 'percentage' not in c 
                   and '_mean' not in c and '_std' not in c and '_median' not in c]
        
        if not age_cols:
            logger.warning("No age columns found for visualization")
            return ""
            
        totals = df[age_cols].sum().sort_values(ascending=True)
        
        if totals.empty:
            return ""
        
        colors = sns.color_palette("viridis", len(age_cols))
        bars = plt.barh(totals.index, totals.values, color=colors)
        
        plt.title('Enrollment Distribution by Age Group', fontweight='bold')
        plt.xlabel('Total Enrollments')
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            plt.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{int(width):,}', 
                    ha='left', va='center', fontweight='bold')
            
        output_path = self.output_dir / "age_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)
        
    def plot_anomaly_distribution(self, results: Dict) -> str:
        """Plot anomaly severity distribution"""
        plt.figure(figsize=(10, 6))
        
        # anomaly_detection.severity_distribution is at top level, not under summary
        severity_dist = results.get('anomaly_detection', {}).get('severity_distribution', {})
        
        if not severity_dist:
            # Fallback dummy plot if empty
            plt.text(0.5, 0.5, "No Anomaly Data", ha='center')
        else:
            # Filter out NORMAL
            data = {k:v for k,v in severity_dist.items() if k != 'NORMAL'}
            if not data:
                data = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
            
            labels = list(data.keys())
            values = list(data.values())
            colors = ['#f1c40f', '#e67e22', '#e74c3c', '#c0392b'] # Yellow to Red
            
            plt.bar(labels, values, color=colors[:len(labels)])
            plt.title('Anomaly Detection by Severity', fontweight='bold')
            plt.ylabel('Count')
            
        output_path = self.output_dir / "anomaly_severity.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)
        
    def plot_forecast(self, results: Dict) -> str:
        """Plot forecast data"""
        plt.figure(figsize=(12, 6))
        
        # Get ensemble_forecast.forecast instead of forecast_values
        ensemble = results.get('forecasting', {}).get('ensemble_forecast', {})
        forecast_values = ensemble.get('forecast', [])
        
        if forecast_values:
            # Generate future dates based on forecast horizon
            horizon = len(forecast_values)
            dates = [f"Month {i+1}" for i in range(horizon)]
            
            plt.plot(dates, forecast_values, marker='o', linestyle='-', linewidth=2, color='#2ecc71', label='Forecast')
            
            # Add confidence interval if available
            lower_ci = ensemble.get('lower_ci', [v * 0.9 for v in forecast_values])
            upper_ci = ensemble.get('upper_ci', [v * 1.1 for v in forecast_values])
            
            plt.fill_between(dates, lower_ci, upper_ci, 
                           color='#2ecc71', alpha=0.2, label='Confidence Interval')
            
            plt.title('6-Month Enrollment Forecast', fontweight='bold')
            plt.xlabel('Forecast Period')
            plt.ylabel('Predicted Enrollments')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
        else:
            plt.text(0.5, 0.5, "No Forecast Data", ha='center', va='center', transform=plt.gca().transAxes)
            
        output_path = self.output_dir / "forecast_plot.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)

    def plot_policy_impact(self, results: Dict) -> str:
        """Plot policy resource allocation"""
        plt.figure(figsize=(10, 6))
        
        policy = results.get('policy_impact', {})
        interventions = policy.get('interventions', {})
        
        # Handle both possible intervention structures
        if interventions:
            # Check for by_type or by_urgency structure
            by_type = interventions.get('by_type', {})
            by_urgency = interventions.get('by_urgency', {})
            
            if by_type:
                # Use intervention types
                labels = list(by_type.keys())
                values = [int(v) if pd.notna(v) else 0 for v in by_type.values()]
            elif by_urgency:
                # Use urgency levels
                labels = list(by_urgency.keys())
                values = [int(v) if pd.notna(v) else 0 for v in by_urgency.values()]
            else:
                # Fallback to resource allocation view
                resource = policy.get('resource_allocation', {})
                labels = ['Required Centers', 'Critical Districts']
                values = [
                    resource.get('total_required_centers', 0),
                    resource.get('critical_districts', 0)
                ]
            
            # Only plot if we have data
            if sum(values) > 0:
                colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#9b59b6'][:len(labels)]
                plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors)
                plt.title('District Intervention Status', fontweight='bold')
            else:
                plt.text(0.5, 0.5, "No Intervention Data", ha='center', va='center', transform=plt.gca().transAxes)
        else:
            plt.text(0.5, 0.5, "No Intervention Data", ha='center', va='center', transform=plt.gca().transAxes)
            
        output_path = self.output_dir / "policy_impact.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)
    
    def plot_child_adult_imbalance(self, results: Dict) -> str:
        """Plot Child-Adult Ratio Comparison (Hackathon Req)"""
        plt.figure(figsize=(10, 6))
        
        # Extract ratios grouped by Age Bucket (Conceptual logic based on available data)
        # We need to construct this from the 'age_demographics' section if available, or compute on the fly
        # For now, let's visualize the ratio metric directly if available
        
        ratios = results.get('descriptive_analytics', {}).get('age_demographics', {}).get('ratios', {})
        if not ratios:
            # Fallback based on schema cols if ratios not pre-calculated
            # Only visualizes if data exists
            return ""

        # Let's plot global proportions for "Child" vs "Adult"
        totals = results.get('descriptive_analytics', {}).get('age_demographics', {}).get('overall', {}).get('totals', {})
        children = 0
        adults = 0
        for k, v in totals.items():
            if '0_5' in k or '5_17' in k:
                children += v
            elif '18' in k:
                adults += v
                
        if children + adults == 0:
             return ""

        labels = ['Children (0-17)', 'Adults (18+)']
        sizes = [children, adults]
        colors = ['#3498db', '#95a5a6']
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, explode=(0.05, 0))
        plt.title('Child vs. Adult Enrollment Imbalance', fontweight='bold')
        
        # Add annotation for the Ratio
        ratio_val = ratios.get('child_adult_ratio', round(children/adults, 2) if adults else 0)
        plt.text(1.2, 0.9, f"Imbalance Ratio\n{ratio_val}x", 
                 bbox=dict(facecolor='white', alpha=0.5, edgecolor='black'),
                 ha='center', fontsize=12, fontweight='bold')

        output_path = self.output_dir / "child_adult_imbalance.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)

    def plot_district_priority(self, results: Dict) -> str:
        """Plot Grid of Priority Districts (Hackathon Req)"""
        plt.figure(figsize=(12, 6))
        
        priorities = results.get('policy_impact', {}).get('priority_districts', [])
        if not priorities:
             return ""
        
        # Top 10 Priority Districts
        top_10 = pd.DataFrame(priorities).head(10)
        if top_10.empty:
            return ""

        sns.barplot(data=top_10, x='priority_score', y='district', hue='priority_tier', dodge=False)
        plt.title('Top 10 Priority Districts for Intervention', fontweight='bold')
        plt.xlabel('Priority Score')
        plt.ylabel('District')
        plt.legend(title='Priority Tier')
        
        output_path = self.output_dir / "priority_districts.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        return str(output_path)
