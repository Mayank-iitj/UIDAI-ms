import streamlit as st
import json
import pandas as pd
from pathlib import Path
import os
import shutil
from main import UidaiIntelligenceSystem

# Page Config
st.set_page_config(
    page_title="UIDAI Intelligence System (Hackathon Edition)",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    /* Force text color to black for all metric elements */
    [data-testid="stMetricValue"], 
    [data-testid="stMetricLabel"], 
    [data-testid="stMetricDelta"] {
        color: #000000 !important;
    }
    div[data-testid="metric-container"] * {
        color: #000000 !important;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .report-box {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2196f3;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Title
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.markdown("<h1>🇮🇳</h1>", unsafe_allow_html=True)
with col_title:
    st.title("UIDAI Intelligence System")
    st.caption("Advanced Analytics & Predictive Modeling for Data Hackathon 2026")

# Sidebar
st.sidebar.header("🕹️ System Controls")

# Data Source Selection
data_source = st.sidebar.radio(
    "Select Data Source",
    ["📁 Upload CSV", "🗃️ Use Default Dataset", "📊 Generate Sample Data"],
    index=1
)

uploaded_file = None
input_path = None

if data_source == "📁 Upload CSV":
    st.sidebar.markdown("---")
    st.sidebar.subheader("📤 Upload Your Dataset")
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload Enrollment Data (CSV)", 
        type=['csv'],
        help="Upload a CSV file with enrollment data. The system will auto-detect columns."
    )
    
    if uploaded_file:
        # Show data preview
        try:
            preview_df = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)  # Reset for later use
            
            st.sidebar.success(f"✅ Loaded: {uploaded_file.name}")
            st.sidebar.write(f"📊 Rows: {len(preview_df):,} | Columns: {len(preview_df.columns)}")
            
            # Show column mapping
            with st.sidebar.expander("🔧 Column Mapping", expanded=False):
                st.write("Map your columns to required fields:")
                
                required_cols = ['date', 'state', 'district', 'pincode', 'age_0_5', 'age_5_17', 'age_18_greater']
                available_cols = ['Auto-detect'] + list(preview_df.columns)
                
                column_mapping = {}
                for req_col in required_cols:
                    # Try to auto-detect matching column
                    default_idx = 0
                    for i, col in enumerate(available_cols):
                        if col.lower().replace(' ', '_').replace('-', '_') == req_col.lower():
                            default_idx = i
                            break
                    
                    column_mapping[req_col] = st.selectbox(
                        f"{req_col}:",
                        available_cols,
                        index=default_idx,
                        key=f"map_{req_col}"
                    )
                
                # Store mapping in session
                st.session_state['column_mapping'] = column_mapping
            
            # Data preview
            with st.sidebar.expander("👁️ Data Preview", expanded=False):
                st.dataframe(preview_df.head(5), height=150)
            
            # Validation status
            missing_cols = []
            for col in ['date', 'state', 'district']:
                if col not in [c.lower() for c in preview_df.columns]:
                    found = False
                    for c in preview_df.columns:
                        if col in c.lower():
                            found = True
                            break
                    if not found:
                        missing_cols.append(col)
            
            if missing_cols:
                st.sidebar.warning(f"⚠️ May need mapping: {', '.join(missing_cols)}")
            else:
                st.sidebar.success("✅ Schema looks compatible!")
                
        except Exception as e:
            st.sidebar.error(f"Error reading file: {e}")

elif data_source == "📊 Generate Sample Data":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎲 Sample Data Generator")
    
    sample_size = st.sidebar.slider("Number of records", 100, 10000, 1000, step=100)
    
    if st.sidebar.button("Generate Sample Dataset"):
        import numpy as np
        from datetime import datetime, timedelta
        
        np.random.seed(42)
        states = ['Uttar Pradesh', 'Bihar', 'Maharashtra', 'Karnataka', 'Gujarat', 
                 'Rajasthan', 'Madhya Pradesh', 'West Bengal', 'Tamil Nadu', 'Andhra Pradesh']
        districts = ['District_' + str(i) for i in range(1, 51)]
        
        sample_data = {
            'date': [(datetime(2025, 1, 1) + timedelta(days=np.random.randint(0, 365))).strftime('%d-%m-%Y') 
                    for _ in range(sample_size)],
            'state': np.random.choice(states, sample_size),
            'district': np.random.choice(districts, sample_size),
            'pincode': np.random.randint(100000, 999999, sample_size),
            'age_0_5': np.random.randint(0, 500, sample_size),
            'age_5_17': np.random.randint(0, 400, sample_size),
            'age_18_greater': np.random.randint(0, 100, sample_size)
        }
        
        sample_df = pd.DataFrame(sample_data)
        sample_df['total_enrollment'] = sample_df['age_0_5'] + sample_df['age_5_17'] + sample_df['age_18_greater']
        
        # Save to temp file
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        sample_path = temp_dir / "sample_data.csv"
        sample_df.to_csv(sample_path, index=False)
        
        st.session_state['generated_sample_path'] = str(sample_path)
        st.sidebar.success(f"✅ Generated {sample_size:,} records!")
        st.sidebar.dataframe(sample_df.head(), height=150)

st.sidebar.markdown("---")

# Drill-Down Filters
st.sidebar.header("🔍 Drill-Down Filters")

if st.sidebar.button("▶️ Run Analysis Pipeline", type="primary"):
    with st.spinner("Initializing Intelligence System..."):
        try:
            system = UidaiIntelligenceSystem()
            input_path = None
            
            # Handle different data sources
            if data_source == "📁 Upload CSV" and uploaded_file:
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                input_path = temp_dir / uploaded_file.name
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.sidebar.success(f"📂 Using: {uploaded_file.name}")
                
            elif data_source == "📊 Generate Sample Data" and 'generated_sample_path' in st.session_state:
                input_path = Path(st.session_state['generated_sample_path'])
                st.sidebar.success("📂 Using: Generated Sample Data")
            else:
                st.sidebar.info("📂 Using: Default UIDAI Dataset")
            
            with st.spinner("Running 5 Analytical Engines..."):
                report, df = system.run_pipeline(input_file=input_path)
            
            # Cleanup temp files
            if input_path and input_path.exists() and 'temp_uploads' in str(input_path):
                try:
                    shutil.rmtree(Path("temp_uploads"))
                except:
                    pass
                
            st.sidebar.success("✅ Analysis Complete!")
            st.rerun()
        except Exception as e:
            st.error(f"Pipeline Failed: {e}")
            st.exception(e)

st.sidebar.markdown("---")
st.sidebar.header("👨‍💻 Team Antigravity")
st.sidebar.caption("Solutions for a Digital India")

# Load Helpers
def load_latest_report():
    report_dir = Path("outputs/reports")
    if not report_dir.exists(): return None
    json_files = list(report_dir.glob("*.json"))
    if not json_files: return None
    latest_file = max(json_files, key=os.path.getctime)
    with open(latest_file, 'r') as f: return json.load(f)

@st.cache_data
def load_dataframe():
    from utils.data_loader import UidaiDataLoader
    loader = UidaiDataLoader()
    try: return loader.load_all_data()
    except: return pd.DataFrame()

report = load_latest_report()
df = load_dataframe()

if not report:
    st.warning("Please run the analysis pipeline to generate intelligence.")
    st.stop()

# Helper for images
vis_dir = Path("outputs/visualizations")
def show_image(filename, caption):
    path = vis_dir / filename
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Plot {filename} not generating (Check Data Sufficiency)")

# --- APP TABS ---
# Executive Brief is Tab 1 (Hackathon Req 11)
tab_exec, tab_trends, tab_anomalies, tab_forecast, tab_policy, tab_report, tab_raw = st.tabs([
    "📋 Executive Brief", 
    "📈 Trends & Demographics", 
    "🔍 Anomaly Detection", 
    "🔮 Forecast", 
    "🛡️ Policy Impact",
    "� Full Report",
    "�📝 Raw Data"
])

# --- TAB 1: EXECUTIVE BRIEF ---
with tab_exec:
    st.subheader("🚀 Strategic Overview & Key Insights")
    
    # KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Lives Touched", f"{report['metadata']['data_records']:,}")
    with kpi2:
        dri = report.get('data_governance', {}).get('dri', {})
        st.metric("Data Reliability (DRI)", f"{dri.get('dri_score', 0)}", delta=dri.get('assessment', 'N/A'))
    with kpi3:
        # Child-Adult Ratio from new logic
        ratios = report.get('descriptive_analytics', {}).get('ratios', {})
        st.metric("Child-Adult Ratio", f"{ratios.get('child_adult_ratio', 'N/A')}", delta=ratios.get('adult_inclusion_gap', ''))
    with kpi4:
        # Surge alert
        surge = report.get('forecasting', {}).get('surge_detection', {})
        val = "YES" if surge.get('surge_detected') else "NO"
        st.metric("Upcoming Surge?", val, delta="Prepared" if val=="NO" else "Action Req", delta_color="inverse")

    # The Story
    col_story, col_actions = st.columns([2, 1])
    with col_story:
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.markdown("### 📢 Why This Matters")
        st.write("This system uses advanced machine learning to detect **unseen patterns** in enrollment data. "
                 "Currently, we are seeing a specific need to balance **child enrollments vs adult updates** in key districts. "
                 "Our forecast models indicate stable demand, allowing for **targeted resource reallocation** to underserved zones.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.subheader("Key Findings")
        recs = report.get('policy_impact', {}).get('strategic_recommendations', [])[:3]
        for r in recs:
            st.success(f"🎯 {r}")

    with col_actions:
        st.markdown("### ⚡ Immediate Actions")
        # Extract critical districts
        critical = report.get('policy_impact', {}).get('priority_districts', [])[:5]
        if critical:
            st.write("**Deploy Mobile Teams to:**")
            for d in critical:
                st.write(f"- 🔴 {d.get('district')} (Score: {d.get('priority_score')})")
        else:
            st.write("✅ No critical districts pending intervention.")

# --- TAB 2: TRENDS & DEMOGRAPHICS ---
with tab_trends:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Enrollment Momentum")
        show_image("temporal_trend.png", "Monthly Trends")
        st.caption("💡 *Understanding temporal patterns helps align operator shifts.*")
    with c2:
        st.subheader("Demographic Balance")
        show_image("child_adult_imbalance.png", "Child vs Adult Split")
        st.caption("💡 *A balanced ratio ensures comprehensive coverage across generations.*")
    
    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        show_image("age_distribution.png", "Detailed Age Breakdown")
    with c4:
         st.info("Additional demographic metrics will appear here.")

# --- TAB 3: ANOMALY DETECTION ---
with tab_anomalies:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Anomaly Severity Distribution")
        show_image("anomaly_severity.png", "Severity of Detected Issues")
    with c2:
        st.subheader("Detection Logic")
        st.markdown("""
        - **Data Quality**: High statistical deviation (Z-Score > 4).
        - **Operational**: Sudden drop/spike in specific centers.
        - **Policy**: Regional deviations matching external factors.
        """)
    
    st.subheader("Detailed Anomaly Log")
    anomalies = report.get('anomaly_detection', {}).get('critical_anomalies', [])
    if anomalies:
        for a in anomalies:
            with st.expander(f"🔴 {a.get('district')} - {a.get('anomaly_reason', 'Unknown')}"):
                st.write(f"Severity Score: {a.get('severity_score')}")
                st.write("Action: Immediate Field Verification Recommended")
    else:
        st.success("✅ System Clean: No critical anomalies detected.")

# --- TAB 4: FORECAST ---
with tab_forecast:
    st.subheader("🔮 Predictive Intelligence (6-Month Horizon)")
    show_image("forecast_plot.png", "Enrollment Forecast with Confidence Intervals")
    
    surge = report.get('forecasting', {}).get('surge_detection', {})
    if surge.get('surge_detected'):
        st.error(f"⚠️ SURGE ALERT: Expect high demand in {surge.get('num_surge_periods')} periods.")
        periods = surge.get('surge_periods', [])
        for p in periods:
            st.write(f"- **Month +{p.get('period')}**: {p.get('context', 'Unknown Context')}")
    else:
         st.success("✅ Demand Stability: Operations can continue at current capacity.")

# --- TAB 5: POLICY IMPACT ---
with tab_policy:
    st.subheader("🛡️ Strategic Resource Allocation")
    c1, c2 = st.columns(2)
    with c1:
        show_image("policy_impact.png", "Intervention Status")
    with c2:
        show_image("priority_districts.png", "Top Districts for Intervention")
    
    st.markdown("### Resource Reallocation Plan")
    res = report.get('policy_impact', {}).get('resource_allocation', {})
    st.write(f"**Total New Centers Required:** {res.get('total_required_centers', 0):,}")
    st.write(f"**Additional Staff Needed:** {res.get('total_required_staff', 0):,}")

# --- TAB 6: FULL REPORT ---
with tab_report:
    st.subheader("📄 Complete Intelligence Report")
    
    # Report file listing
    report_dir = Path("outputs/reports")
    
    col_summary, col_download = st.columns([2, 1])
    
    with col_summary:
        st.markdown("### 📝 Executive Summary")
        
        # Find latest executive summary
        txt_files = list(report_dir.glob("executive_summary_*.txt"))
        if txt_files:
            latest_txt = max(txt_files, key=os.path.getctime)
            with open(latest_txt, 'r', encoding='utf-8') as f:
                summary_text = f.read()
            
            # Display in expandable container
            with st.expander("View Executive Summary", expanded=True):
                st.text(summary_text)
        else:
            st.info("No executive summary found. Run the pipeline first.")
    
    with col_download:
        st.markdown("### 📥 Download Reports")
        
        # PDF download
        pdf_files = list(report_dir.glob("intelligence_report_*.pdf"))
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getctime)
            with open(latest_pdf, 'rb') as f:
                pdf_bytes = f.read()
            st.download_button(
                "📕 Download PDF Report",
                pdf_bytes,
                file_name=latest_pdf.name,
                mime="application/pdf",
                use_container_width=True
            )
        
        # JSON download
        json_files = list(report_dir.glob("intelligence_report_*.json"))
        if json_files:
            latest_json = max(json_files, key=os.path.getctime)
            with open(latest_json, 'r') as f:
                json_content = f.read()
            st.download_button(
                "📊 Download JSON Report",
                json_content,
                file_name=latest_json.name,
                mime="application/json",
                use_container_width=True
            )
        
        # TXT summary download
        if txt_files:
            with open(latest_txt, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            st.download_button(
                "📝 Download Summary (TXT)",
                txt_content,
                file_name=latest_txt.name,
                mime="text/plain",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Full JSON Report Viewer
    st.markdown("### 🔍 Interactive Report Explorer")
    
    report_sections = [
        "Select Section...",
        "📋 Metadata",
        "🔒 Data Governance",
        "📊 Descriptive Analytics",
        "🔍 Anomaly Detection",
        "🔮 Forecasting",
        "🛡️ Policy Impact"
    ]
    
    selected_section = st.selectbox("Explore Report Section", report_sections)
    
    if selected_section == "📋 Metadata":
        st.json(report.get('metadata', {}))
    elif selected_section == "🔒 Data Governance":
        st.json(report.get('data_governance', {}))
    elif selected_section == "📊 Descriptive Analytics":
        # Show summary, not full data
        desc = report.get('descriptive_analytics', {})
        st.write("**Coverage:**", desc.get('geographic_patterns', {}).get('coverage', {}))
        st.write("**Age Demographics:**", desc.get('age_demographics', {}).get('overall', {}))
        with st.expander("View Full Section"):
            st.json(desc)
    elif selected_section == "🔍 Anomaly Detection":
        anomaly = report.get('anomaly_detection', {})
        st.write("**Summary:**", anomaly.get('summary', {}))
        with st.expander("View Full Section"):
            st.json(anomaly)
    elif selected_section == "🔮 Forecasting":
        forecast = report.get('forecasting', {})
        st.write("**Horizon:**", forecast.get('forecast_horizon', 'N/A'), "months")
        st.write("**Surge Detected:**", forecast.get('surge_detection', {}).get('surge_detected', False))
        with st.expander("View Full Section"):
            st.json(forecast)
    elif selected_section == "🛡️ Policy Impact":
        policy = report.get('policy_impact', {})
        st.write("**Strategic Recommendations:**")
        for rec in policy.get('strategic_recommendations', [])[:5]:
            st.markdown(f"- {rec}")
        with st.expander("View Full Section"):
            st.json(policy)
    
    # List all generated reports
    st.markdown("---")
    st.markdown("### 📁 All Generated Reports")
    
    all_reports = list(report_dir.glob("*"))
    if all_reports:
        report_data = []
        for rp in sorted(all_reports, key=os.path.getctime, reverse=True):
            report_data.append({
                "File": rp.name,
                "Type": rp.suffix.upper(),
                "Size": f"{rp.stat().st_size / 1024:.1f} KB",
                "Created": pd.to_datetime(os.path.getctime(rp), unit='s').strftime('%Y-%m-%d %H:%M')
            })
        st.dataframe(pd.DataFrame(report_data), use_container_width=True, hide_index=True)

# --- TAB 7: RAW DATA ---
with tab_raw:
    st.markdown("### Filtered Dataset")
    
    # Drill Down Filters Logic (Simple implementation)
    states = ['All'] + list(df['state'].unique())
    sel_state = st.selectbox("Filter by State", states)
    
    if sel_state != 'All':
        filt_df = df[df['state'] == sel_state]
        districts = ['All'] + list(filt_df['district'].unique())
        sel_dist = st.selectbox("Filter by District", districts)
        if sel_dist != 'All':
            filt_df = filt_df[filt_df['district'] == sel_dist]
    else:
        filt_df = df
        
    st.dataframe(filt_df)
    st.download_button("Download Data CSV", filt_df.to_csv(index=False), "filtered_data.csv")

# Footer
st.markdown("---")
st.caption("UIDAI Intelligence System v2.0 | 'Hackathon Ready' Build | Team Antigravity")
