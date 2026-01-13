"""
PDF Report Generator for UIDAI Intelligence System
Generates professional PDF reports from analysis results
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PdfReportGenerator:
    """Generate professional PDF reports from UIDAI intelligence analysis"""
    
    def __init__(self):
        """Initialize PDF generator with styling"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))
        
        # Section header style
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderColor=colors.HexColor('#3498db'),
                borderPadding=5
            ))
        
        # Subsection style
        if 'SubSection' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubSection',
                parent=self.styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=8,
                spaceBefore=10,
                fontName='Helvetica-Bold'
            ))
        
        # Body text
        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=6,
                alignment=TA_LEFT,
                fontName='Helvetica'
            ))
        
        # Highlight text (for metrics)
        if 'Highlight' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Highlight',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#e74c3c'),
                fontName='Helvetica-Bold'
            ))
    
    def generate_report(self, complete_report: Dict, output_path: str, plot_paths: Dict[str, str] = None) -> str:
        """
        Generate PDF report from complete analysis
        
        Args:
            complete_report: Complete analysis results
            output_path: Path to save PDF file
            plot_paths: Dictionary of paths to generated visualization images
        
        Returns:
            Path to generated PDF file
        """
        if plot_paths is None:
            plot_paths = {}
            
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=50
        )
        
        # Build report content
        story = []
        
        # Add title page
        story.extend(self._create_title_page(complete_report))
        story.append(PageBreak())
        
        # Add executive summary
        story.extend(self._create_executive_summary(complete_report))
        story.append(PageBreak())
        
        # Add detailed sections
        story.extend(self._create_data_quality_section(complete_report))
        story.extend(self._create_insights_section(complete_report, plot_paths))
        story.extend(self._create_anomaly_section(complete_report, plot_paths))
        story.extend(self._create_forecast_section(complete_report, plot_paths))
        story.extend(self._create_policy_section(complete_report, plot_paths))
        story.extend(self._create_technical_appendix())
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"PDF report generated: {output_path}")
        return output_path
    
    def _create_title_page(self, report: Dict) -> list:
        """Create title page"""
        elements = []
        
        # Add some space
        elements.append(Spacer(1, 2*inch))
        
        # Main title
        title = Paragraph(
            "UIDAI INTELLIGENCE SYSTEM",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Subtitle
        subtitle = Paragraph(
            "Analytical & Predictive Intelligence Report",
            self.styles['Heading2']
        )
        elements.append(subtitle)
        elements.append(Spacer(1, inch))
        
        # Metadata table
        metadata = report['metadata']
        data = [
            ['Generated:', metadata['generated_at']],
            ['Analysis Period:', f"{metadata['analysis_period']['start']} to {metadata['analysis_period']['end']}"],
            ['Total Records:', f"{metadata['data_records']:,}"],
            ['System Version:', metadata.get('version', '1.0.0')]
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c3e50')),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_executive_summary(self, report: Dict) -> list:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Key metrics table
        dri = report['data_governance']['dri']
        geo = report['descriptive_analytics']['geographic_patterns']
        anomalies = report['anomaly_detection']['summary']
        policy = report['policy_impact']
        
        summary_data = [
            ['Metric', 'Value', 'Status'],
            ['Data Quality (DRI)', f"{dri['dri_score']}", dri['assessment']],
            ['States Covered', f"{geo['coverage']['num_states']}", '✓'],
            ['Districts Analyzed', f"{geo['coverage']['num_districts']}", '✓'],
            ['PIN Codes', f"{geo['coverage']['num_pincodes']:,}", '✓'],
            ['Anomalies Detected', f"{anomalies['statistical_anomalies']:,}", 'Flagged'],
            ['Critical Districts', f"{policy['resource_allocation']['critical_districts']}", 'Action Required'],
        ]
        
        table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_data_quality_section(self, report: Dict) -> list:
        """Create data quality section"""
        elements = []
        
        elements.append(Paragraph("DATA QUALITY ASSESSMENT", self.styles['SectionHeader']))
        
        dri = report['data_governance']['dri']
        
        text = f"""
        The Data Reliability Index (DRI) score is <b>{dri['dri_score']}</b>, indicating <b>{dri['assessment']}</b> data quality.
        The analysis is based on three key components:
        """
        elements.append(Paragraph(text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
        
        # DRI components
        components_data = [
            ['Component', 'Score', 'Description'],
            ['Completeness', f"{dri['components']['completeness']}", 'No missing critical fields'],
            ['Consistency', f"{dri['components']['consistency']}", 'Data format uniformity'],
            ['Validity', f"{dri['components']['validity']}", 'Values within expected ranges'],
        ]
        
        table = Table(components_data, colWidths=[2*inch, 1*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_insights_section(self, report: Dict, plot_paths: Dict) -> list:
        """Create key insights section"""
        elements = []
        
        elements.append(Paragraph("KEY INSIGHTS", self.styles['SectionHeader']))
        
        # Add Temporal Trend Plot if exists
        if 'temporal_trend' in plot_paths:
            elements.append(Paragraph("Enrollment Trends:", self.styles['SubSection']))
            elements.append(Image(plot_paths['temporal_trend'], width=6*inch, height=3.5*inch))
            elements.append(Spacer(1, 0.2*inch))
            
        # Add Age Distribution Plot if exists
        if 'age_distribution' in plot_paths:
            elements.append(Paragraph("Demographic Analysis:", self.styles['SubSection']))
            elements.append(Image(plot_paths['age_distribution'], width=6*inch, height=3.5*inch))
            elements.append(Spacer(1, 0.2*inch))
        
        geo = report['descriptive_analytics']['geographic_patterns']
        inequity = report['descriptive_analytics']['inequities']
        
        insights = [
            f"Geographic coverage spans <b>{geo['coverage']['num_states']} states</b> and <b>{geo['coverage']['num_districts']} districts</b>.",
            f"<b>{len(inequity['underserved_districts'])} underserved districts</b> identified requiring targeted intervention.",
            f"Enrollment concentration shows a Gini coefficient of <b>{geo['concentration']['gini_coefficient']}</b> - {geo['concentration']['interpretation']}.",
        ]
        
        for insight in insights:
            elements.append(Paragraph(f"• {insight}", self.styles['BodyText']))
            elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_anomaly_section(self, report: Dict, plot_paths: Dict) -> list:
        """Create anomaly detection section"""
        elements = []
        
        elements.append(Paragraph("ANOMALY DETECTION", self.styles['SectionHeader']))
        
        # Add Anomaly Plot if exists
        if 'anomalies' in plot_paths:
            elements.append(Image(plot_paths['anomalies'], width=6*inch, height=3.5*inch))
            elements.append(Spacer(1, 0.2*inch))
            
        anomalies = report['anomaly_detection']['summary']
        
        anomaly_data = [
            ['Detection Method', 'Anomalies Found', 'Percentage'],
            ['Statistical Analysis', f"{anomalies['statistical_anomalies']:,}", 
             f"{(anomalies['statistical_anomalies']/anomalies['total_records']*100):.2f}%"],
            ['Temporal Patterns', f"{anomalies['temporal_anomalies']}", 'Days flagged'],
            ['Geographic Analysis', f"{anomalies['geographic_anomalies']}", 'Districts'],
            ['ML-Based Detection', f"{anomalies['ml_anomalies']:,}", 
             f"{(anomalies['ml_anomalies']/anomalies['total_records']*100):.2f}%"],
        ]
        
        table = Table(anomaly_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_forecast_section(self, report: Dict, plot_paths: Dict) -> list:
        """Create forecasting section"""
        elements = []
        
        elements.append(Paragraph("ENROLLMENT FORECAST", self.styles['SectionHeader']))
        
        # Add Forecast Plot if exists
        if 'forecast' in plot_paths:
            elements.append(Image(plot_paths['forecast'], width=6*inch, height=3.5*inch))
            elements.append(Spacer(1, 0.2*inch))
            
        forecast = report['forecasting']
        
        text = f"""
        The system has generated a <b>{forecast['forecast_horizon']}-month forecast</b> for enrollment trends.
        """
        elements.append(Paragraph(text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Surge detection
        surge = forecast['surge_detection']
        if surge['surge_detected']:
            warning = f"<font color='red'><b>WARNING:</b> {surge['num_surge_periods']} surge period(s) predicted. Capacity planning required.</font>"
        else:
            warning = "<font color='green'><b>STATUS:</b> No enrollment surges predicted. Stable demand expected.</font>"
        
        elements.append(Paragraph(warning, self.styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_policy_section(self, report: Dict, plot_paths: Dict) -> list:
        """Create policy recommendations section"""
        elements = []
        
        elements.append(Paragraph("POLICY RECOMMENDATIONS", self.styles['SectionHeader']))
        
        # Add Policy Plot if exists
        if 'policy' in plot_paths:
            elements.append(Image(plot_paths['policy'], width=6*inch, height=3.5*inch))
            elements.append(Spacer(1, 0.2*inch))
            
        policy = report['policy_impact']
        
        # Resource requirements
        elements.append(Paragraph("Resource Planning:", self.styles['SubSection']))
        
        resource_data = [
            ['Requirement', 'Quantity'],
            ['Critical Districts', f"{policy['resource_allocation']['critical_districts']}"],
            ['Required Enrollment Centers', f"{policy['resource_allocation']['total_required_centers']:,}"],
            ['Required Staff', f"{policy['resource_allocation']['total_required_staff']:,}"],
            ['Immediate Interventions', f"{policy['interventions']['immediate_action_required']}"],
        ]
        
        table = Table(resource_data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Strategic recommendations
        elements.append(Paragraph("Strategic Recommendations:", self.styles['SubSection']))
        
        for i, rec in enumerate(policy['strategic_recommendations'], 1):
            elements.append(Paragraph(f"{i}. {rec}", self.styles['BodyText']))
            elements.append(Spacer(1, 0.05*inch))
        
        return elements


    def _create_technical_appendix(self) -> list:
        """Create technical appendix with code summary"""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("TECHNICAL APPENDIX", self.styles['SectionHeader']))
        elements.append(Paragraph("System Architecture & Methodologies", self.styles['SubSection']))
        
        text = """
        This system utilizes a modular architecture with five specialized engines:
        1. Data Governance Engine: Ensures DRI compliance and schema validation.
        2. Descriptive Analytics: Computes demographic and temporal distributions.
        3. Anomaly Detection: Uses Isolation Forest and statistical Z-scores.
        4. Forecasting: Implements ensemble methods (SARIMA/XGBoost logic).
        5. Policy Impact: Simulates resource allocation based on predictive needs.
        
        The analysis was performed using Python 3.14, Pandas, Scikit-learn, and Statsmodels.
        Full source code is available in the accompanying submission files.
        """
        elements.append(Paragraph(text, self.styles['BodyText']))
        
        return elements


def main():
    """Test PDF generation"""
    import json
    
    # Load a sample report
    print("PDF Report Generator - Test Mode")
    print("This module is used by main.py to generate PDF reports.")
    

if __name__ == "__main__":
    main()
