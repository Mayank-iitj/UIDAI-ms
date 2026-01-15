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

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload Enrollment Data (CSV)", type=['csv'])

# Drill-Down Filters (Hackathon Requirement 4)
st.sidebar.header("🔍 Drill-Down")
# Determine available states/districts - Load basic metadata if possible without full pipeline run
# For simplicity, we filter AFTER loading the report/df. 
# Ideally, interactive filtering requires reloading the charts. 
# Since charts are static, we might need to re-run visualization or handle filtering in the future.
# For now, let's just show the selectors as "Global Filters" for the Data Table if nothing else.

if st.sidebar.button("▶️ Run Analysis Pipeline"):
    with st.spinner("Initializing Intelligence System..."):
        try:
            system = UidaiIntelligenceSystem()
            input_path = None
            if uploaded_file:
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                input_path = temp_dir / uploaded_file.name
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.sidebar.success(f"Uploaded: {uploaded_file.name}")
            
            with st.spinner("Running Engines..."):
                report, df = system.run_pipeline(input_file=input_path)
            
            if input_path and input_path.exists():
                shutil.rmtree(temp_dir)
                
            st.sidebar.success("Analysis Complete!")
            st.rerun()
        except Exception as e:
            st.error(f"Pipeline Failed: {e}")

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
tab_exec, tab_trends, tab_anomalies, tab_forecast, tab_policy, tab_raw = st.tabs([
    "📋 Executive Brief", 
    "📈 Trends & Demographics", 
    "🔍 Anomaly Detection", 
    "🔮 Forecast", 
    "🛡️ Policy Impact",
    "📝 Raw Data"
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

# --- TAB 6: RAW DATA ---
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
    st.json(report)

# Footer
st.markdown("---")
st.caption("UIDAI Intelligence System v2.0 | 'Hackathon Ready' Build | Team Antigravity")
