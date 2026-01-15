"""
UIDAI Intelligence System - Master Orchestrator
Coordinates all five analytical engines to generate comprehensive intelligence reports
"""

import pandas as pd
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Optional
import json

# Import all engines
from engines import (
    DataGovernanceEngine,
    DescriptiveAnalyticsEngine,
    AnomalyDetectionEngine,
    ForecastingEngine,
    PolicyImpactEngine
)

# Import utilities
from utils.data_loader import UidaiDataLoader
from utils.pdf_generator import PdfReportGenerator
from utils.visualizer import Visualizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./outputs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UidaiIntelligenceSystem:
    """
    Master orchestrator for the UIDAI Intelligence System
    Coordinates all analytical engines and generates comprehensive reports
    """
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """Initialize the intelligence system"""
        logger.info("="*60)
        logger.info("INITIALIZING UIDAI INTELLIGENCE SYSTEM")
        logger.info("="*60)
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        logger.info("Loading data...")
        self.data_loader = UidaiDataLoader(config_path)
        
        logger.info("Initializing analytical engines...")
        self.governance_engine = DataGovernanceEngine(config_path)
        self.descriptive_engine = DescriptiveAnalyticsEngine(config_path)
        self.anomaly_engine = AnomalyDetectionEngine(config_path)
        self.forecast_engine = ForecastingEngine(config_path)
        self.policy_engine = PolicyImpactEngine(config_path)
        
        # Output paths
        self.output_path = Path(self.config['output']['reports_path'])
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("System initialized successfully!")
        logger.info("="*60)
    
    def run_pipeline(self, input_file: Optional[Path] = None) -> Tuple[Dict, pd.DataFrame]:
        """
        Run the complete intelligence pipeline
        
        Args:
            input_file: Optional path to a single CSV file to analyze
            
        Returns:
            Tuple of (Complete analysis results, Main dataframe)
        """
        logger.info("\n[STARTING] Full intelligence analysis pipeline...")
        
        # Stage 1: Load and validate data
        logger.info("\n[STAGE 1] Data Loading & Governance")
        logger.info("-" * 60)
        
        if input_file:
            logger.info(f"Processing uploaded file: {input_file}")
            df = self.data_loader.load_file(input_file)
        else:
            logger.info("Processing default dataset from raw directory")
            df = self.data_loader.load_all_data()
            
        logger.info(f"Loaded {len(df):,} records")
        
        # Run data governance
        governance_report = self.governance_engine.generate_quality_report(df)
        logger.info(f"DRI Score: {governance_report['dri']['dri_score']} ({governance_report['dri']['assessment']})")
        
        # Check if data passes quality threshold
        if governance_report['dri']['assessment'] == 'FAIL':
            logger.warning("⚠️  Data quality below threshold. Proceeding with caution.")
        else:
            logger.info("✓ Data quality acceptable")
        
        # Stage 2: Descriptive Analytics
        logger.info("\n[STAGE 2] Descriptive Analytics")
        logger.info("-" * 60)
        
        # Temporal trends
        temporal_trends = self.descriptive_engine.compute_temporal_trends(df)
        logger.info(f"Analyzed {len(temporal_trends)} months of data")
        
        # Geographic patterns
        geo_patterns = self.descriptive_engine.compute_geographic_patterns(df)
        logger.info(f"Coverage: {geo_patterns['coverage']['num_states']} states, "
                   f"{geo_patterns['coverage']['num_districts']} districts")
        
        # Age demographics
        age_demo = self.descriptive_engine.analyze_age_demographics(df)
        logger.info("Age distribution analysis completed")
        
        # Inequity detection
        inequities = self.descriptive_engine.detect_inequities(df)
        logger.info(f"Identified {len(inequities['underserved_districts'])} underserved districts")
        
        # PIN clustering
        pin_clusters, cluster_summary = self.descriptive_engine.perform_pincode_clustering(df)
        logger.info(f"Clustered {len(pin_clusters)} PIN codes")
        
        # Summary statistics
        summary_stats = self.descriptive_engine.generate_summary_statistics(df)
        
        # Stage 3: Anomaly Detection
        logger.info("\n[STAGE 3] Anomaly Detection")
        logger.info("-" * 60)
        
        anomaly_report = self.anomaly_engine.generate_anomaly_report(df)
        logger.info(f"Statistical anomalies: {anomaly_report['summary']['statistical_anomalies']:,}")
        logger.info(f"Temporal anomalies: {anomaly_report['summary']['temporal_anomalies']}")
        logger.info(f"Geographic anomalies: {anomaly_report['summary']['geographic_anomalies']}")
        logger.info(f"ML-detected anomalies: {anomaly_report['summary']['ml_anomalies']:,}")
        
        # Stage 4: Forecasting
        logger.info("\n[STAGE 4] Forecasting & Prediction")
        logger.info("-" * 60)
        
        forecast_report = self.forecast_engine.generate_forecast_report(df, horizon=6)
        logger.info(f"Generated {forecast_report['forecast_horizon']}-month forecast")
        
        if forecast_report['surge_detection']['surge_detected']:
            logger.warning(f"⚠️  Surge predicted in {forecast_report['surge_detection']['num_surge_periods']} period(s)")
        else:
            logger.info("✓ No enrollment surges predicted")
        
        # Stage 5: Policy Impact
        logger.info("\n[STAGE 5] Policy Impact Analysis")
        logger.info("-" * 60)
        
        # Prepare district data
        age_cols = [col for col in self.config['schema']['age_groups'] if col in df.columns]
        district_data = df.groupby(['state', 'district'])[
            age_cols + ['total_enrollment']
        ].sum().reset_index()
        
        # Add child-adult ratio for inequity analysis
        if 'age_0_5' in age_cols and 'age_5_17' in age_cols and 'age_18_plus' in age_cols:
            district_data['child_adult_ratio'] = (
                (district_data['age_0_5'] + district_data['age_5_17']) / 
                district_data['age_18_plus'].replace(0, 1)
            )
        
        policy_report = self.policy_engine.generate_policy_report(
            district_data=district_data,
            inequity_data=district_data,
            forecast_data=pd.DataFrame(),
            anomaly_data=pd.DataFrame()
        )
        
        logger.info(f"Identified {policy_report['resource_allocation']['critical_districts']} critical districts")
        logger.info(f"Resource requirements: {policy_report['resource_allocation']['total_required_centers']:,} centers, "
                   f"{policy_report['resource_allocation']['total_required_staff']:,} staff")
        
        # Compile complete report
        complete_report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'system_version': '1.0.0',
                'data_records': len(df),
                'analysis_period': {
                    'start': df['date'].min().isoformat(),
                    'end': df['date'].max().isoformat()
                }
            },
            'data_governance': governance_report,
            'descriptive_analytics': {
                'temporal_trends': temporal_trends.to_dict('records')[-12:],  # Last 12 months
                'geographic_patterns': geo_patterns,
                'age_demographics': age_demo,
                'inequities': inequities,
                'pin_clustering': cluster_summary,
                'summary_statistics': summary_stats
            },
            'anomaly_detection': anomaly_report,
            'forecasting': forecast_report,
            'policy_impact': policy_report
        }
        
        logger.info("\n[SUCCESS] Full analysis pipeline completed successfully!")
        logger.info("="*60)
        
        return complete_report, df
    
    def generate_executive_summary(self, complete_report: Dict) -> str:
        """
        Generate executive summary from complete analysis
        
        Args:
            complete_report: Complete analysis results
        
        Returns:
            Executive summary as formatted string
        """
        summary = []
        summary.append("="*60)
        summary.append("UIDAI INTELLIGENCE SYSTEM - EXECUTIVE SUMMARY")
        summary.append("="*60)
        summary.append(f"\nGenerated: {complete_report['metadata']['generated_at']}")
        summary.append(f"Analysis Period: {complete_report['metadata']['analysis_period']['start']} to "
                      f"{complete_report['metadata']['analysis_period']['end']}")
        summary.append(f"Total Records Analyzed: {complete_report['metadata']['data_records']:,}")
        
        # Data Quality
        summary.append("\n[DATA QUALITY]")
        summary.append("-" * 60)
        dri = complete_report['data_governance']['dri']
        summary.append(f"Data Reliability Index: {dri['dri_score']} ({dri['assessment']})")
        summary.append(f"  * Completeness: {dri['components']['completeness']}")
        summary.append(f"  * Consistency: {dri['components']['consistency']}")
        summary.append(f"  * Validity: {dri['components']['validity']}")
        
        # Key Insights
        summary.append("\n[KEY INSIGHTS]")
        summary.append("-" * 60)
        geo = complete_report['descriptive_analytics']['geographic_patterns']
        summary.append(f"Geographic Coverage: {geo['coverage']['num_states']} states, "
                      f"{geo['coverage']['num_districts']} districts, "
                      f"{geo['coverage']['num_pincodes']} PIN codes")
        
        inequity = complete_report['descriptive_analytics']['inequities']
        summary.append(f"Underserved Districts: {len(inequity['underserved_districts'])}")
        
        # Anomalies
        summary.append("\n[ANOMALY DETECTION]")
        summary.append("-" * 60)
        anomalies = complete_report['anomaly_detection']['summary']
        summary.append(f"Statistical Anomalies: {anomalies['statistical_anomalies']:,}")
        summary.append(f"Geographic Anomalies: {anomalies['geographic_anomalies']}")
        
        # Forecast
        summary.append("\n[FORECAST]")
        summary.append("-" * 60)
        forecast = complete_report['forecasting']
        summary.append(f"Forecast Horizon: {forecast['forecast_horizon']} months")
        if forecast['surge_detection']['surge_detected']:
            summary.append(f"WARNING: SURGE ALERT - {forecast['surge_detection']['num_surge_periods']} period(s) predicted")
        else:
            summary.append("STATUS: No enrollment surges predicted")
        
        # Policy Recommendations
        summary.append("\n[POLICY RECOMMENDATIONS]")
        summary.append("-" * 60)
        policy = complete_report['policy_impact']
        summary.append(f"Critical Districts: {policy['resource_allocation']['critical_districts']}")
        summary.append(f"Required Centers: {policy['resource_allocation']['total_required_centers']:,}")
        summary.append(f"Required Staff: {policy['resource_allocation']['total_required_staff']:,}")
        summary.append(f"Immediate Interventions Needed: {policy['interventions']['immediate_action_required']}")
        
        summary.append("\n[STRATEGIC RECOMMENDATIONS]")
        summary.append("-" * 60)
        for i, rec in enumerate(policy['strategic_recommendations'], 1):
            summary.append(f"{i}. {rec}")
        
        summary.append("\n" + "="*60)
        
        return "\n".join(summary)
    
    def save_report(self, complete_report: Dict, format: str = 'json', plot_paths: Dict = None):
        """
        Save complete report to file
        
        Args:
            complete_report: Complete analysis results
            format: Output format ('json', 'text', or 'pdf')
            plot_paths: Optional dictionary of plot image paths for PDF
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            filepath = self.output_path / f"intelligence_report_{timestamp}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(complete_report, f, indent=2, default=str)
            logger.info(f"[SAVED] JSON report to: {filepath}")
        
        elif format == 'text':
            filepath = self.output_path / f"executive_summary_{timestamp}.txt"
            summary = self.generate_executive_summary(complete_report)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"[SAVED] Executive summary to: {filepath}")
        
        elif format == 'pdf':
            filepath = self.output_path / f"intelligence_report_{timestamp}.pdf"
            try:
                pdf_generator = PdfReportGenerator()
                pdf_generator.generate_report(complete_report, str(filepath), plot_paths=plot_paths)
                logger.info(f"[SAVED] PDF report to: {filepath}")
            except Exception as e:
                logger.error(f"Failed to generate PDF: {e}")
                logger.info("Continuing without PDF export. Install reportlab: pip install reportlab")
                return None
        
        return filepath


def main():
    """Main entry point for the UIDAI Intelligence System"""
    print("\n")
    print("="*60)
    print("=" + " "*58 + "=")
    print("=" + "  UIDAI INTELLIGENCE SYSTEM".center(58) + "=")
    print("=" + "  Production-Ready Analytical & Predictive Platform".center(58) + "=")
    print("=" + " "*58 + "=")
    print("="*60)
    print("\n")
    
    try:
        # Initialize system
        system = UidaiIntelligenceSystem()
        
        # Run full analysis
        complete_report, df = system.run_pipeline()
        
        # Generate and display executive summary
        executive_summary = system.generate_executive_summary(complete_report)
        print("\n" + executive_summary)
        
        # Generator visualizations
        logger.info("\n[GENERATING] Generating visual analytics...")
        visualizer = Visualizer()
        plot_paths = visualizer.generate_all_plots(df, complete_report)
        
        # Save reports in all formats
        system.save_report(complete_report, format='json')
        system.save_report(complete_report, format='text')
        system.save_report(complete_report, format='pdf', plot_paths=plot_paths)
        
        logger.info("\n[SUCCESS] All reports generated successfully!")
        logger.info("System analysis complete. Reports saved to ./outputs/reports/")
        
    except Exception as e:
        logger.error(f"❌ System error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
