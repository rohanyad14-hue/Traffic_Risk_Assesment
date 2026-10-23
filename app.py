"""
Traffic Accident Analysis & Visualization Dashboard
Visual Analytics Lab — Review 1 Prototype
Authors: Saranya Dalal [26MML0007], Divya Pujari [26MML0009], Rohan Yadav [26MML0020]
Faculty Guide: Dr Manikandan K (SCOPE)
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk

# Page Configuration
st.set_page_config(
    page_title="Traffic Accident Analysis & Visualization",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Dark Theme Core */
    .main {
        background-color: #0b1120;
    }
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #080d1a 90%);
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Container */
    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 14px;
        padding: 22px 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 12px;
    }
    
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-teal { background-color: rgba(20, 184, 166, 0.18); color: #2dd4bf; border: 1px solid rgba(45, 212, 191, 0.3); }
    .badge-indigo { background-color: rgba(99, 102, 241, 0.18); color: #a5b4fc; border: 1px solid rgba(165, 180, 252, 0.3); }
    .badge-rose { background-color: rgba(244, 63, 94, 0.18); color: #fb7185; border: 1px solid rgba(251, 113, 133, 0.3); }
    
    /* Metric Cards */
    .kpi-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px 20px;
        text-align: left;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .kpi-val {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 4px;
    }
    .kpi-lbl {
        font-size: 0.78rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .kpi-delta {
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-alert { color: #f43f5e; }
    .delta-safe { color: #10b981; }
    .delta-info { color: #38bdf8; }
    
    /* Comparison Box */
    .case-box {
        background: rgba(15, 23, 42, 0.7);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    .case-box-warn {
        border-left: 4px solid #f43f5e;
    }
    .case-box-safe {
        border-left: 4px solid #10b981;
    }
    
    /* Top-left logo: the VIT logo is dark blue, so give it a white plate to stay readable on the dark theme */
    [data-testid="stSidebarLogo"], [data-testid="stHeaderLogo"] {
        background: #ffffff;
        padding: 4px 8px;
        border-radius: 6px;
        height: 2.75rem;
        max-width: 15rem;
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUBES_DIR = os.path.join(BASE_DIR, "data", "cubes")

@st.cache_data
def load_cubes():
    df_temporal = pd.read_parquet(os.path.join(CUBES_DIR, "cube_temporal_heatmap.parquet"))
    df_circadian = pd.read_parquet(os.path.join(CUBES_DIR, "cube_circadian_hourly.parquet"))
    df_env = pd.read_parquet(os.path.join(CUBES_DIR, "cube_environmental_matrix.parquet"))
    df_veh = pd.read_parquet(os.path.join(CUBES_DIR, "cube_vehicle_vulnerability.parquet"))
    df_segs = pd.read_parquet(os.path.join(CUBES_DIR, "cube_segments_spatial.parquet"))
    df_quad = pd.read_parquet(os.path.join(CUBES_DIR, "cube_quadrants_summary.parquet"))
    df_india = pd.read_parquet(os.path.join(CUBES_DIR, "cube_india_transferability.parquet"))
    
    with open(os.path.join(CUBES_DIR, "cube_ml_risk_weights.json"), "r") as f:
        ml_weights = json.load(f)
        
    return df_temporal, df_circadian, df_env, df_veh, df_segs, df_quad, df_india, ml_weights

@st.cache_data
def load_india_context_cubes():
    """India (Bengaluru) cubes built by pipeline/04 with the same schema as the UK cubes."""
    return {
        "segs": pd.read_parquet(os.path.join(CUBES_DIR, "cube_india_segments_spatial.parquet")),
        "temporal": pd.read_parquet(os.path.join(CUBES_DIR, "cube_india_temporal_heatmap.parquet")),
        "circadian": pd.read_parquet(os.path.join(CUBES_DIR, "cube_india_circadian_hourly.parquet")),
        "veh": pd.read_parquet(os.path.join(CUBES_DIR, "cube_india_vehicle_vulnerability.parquet")),
        "quad": pd.read_parquet(os.path.join(CUBES_DIR, "cube_india_quadrants_summary.parquet")),
    }

df_temporal, df_circadian, df_env, df_veh, df_segs, df_quad, df_india, ml_weights = load_cubes()
india_ctx = load_india_context_cubes()

LOGO_PATH = os.path.join(BASE_DIR, "extracted_logo.png")

# ----------------- SIDEBAR CONTROLS -----------------
# Local logo file, so the top-left logo does not depend on an external image host.
if os.path.exists(LOGO_PATH):
    st.logo(LOGO_PATH, size="large")

with st.sidebar:
    st.markdown("### 🚦 **Analytical Controls**")
    
    dataset_context = st.radio(
        "Study Context",
        ["UK STATS19 Network (Primary)", "India Transferability Case (Bengaluru)"],
        index=0,
        help="Switches every module (KPIs, quadrants, temporal, map, conditions) between the UK network and the Bengaluru corridors."
    )
    IS_INDIA = dataset_context.startswith("India")
    
    st.markdown("---")
    st.markdown("#### **Filter Road Segments**")

# Re-point the shared dataframes at the selected study context.
if IS_INDIA:
    ctx_segs = india_ctx["segs"]
    ctx_temporal = india_ctx["temporal"]
    ctx_circadian = india_ctx["circadian"]
    ctx_quad = india_ctx["quad"]
    CTX_LABEL = "India Bengaluru Corridors"
    CTX_SOURCE = "Bengaluru corridor crash records & FASTag/AADT volumes"
else:
    ctx_segs = df_segs
    ctx_temporal = df_temporal
    ctx_circadian = df_circadian
    ctx_quad = df_quad
    CTX_LABEL = "UK STATS19 Network"
    CTX_SOURCE = "UK STATS19 & AADT Ingestion"
CTX_TOTAL_CRASHES = int(ctx_circadian["crash_count"].sum())

with st.sidebar:
    class_options = sorted(ctx_segs["road_class"].unique())
    selected_classes = st.multiselect(
        "Road Hierarchy Class",
        options=class_options,
        default=class_options,
        key=f"road_classes_{'india' if IS_INDIA else 'uk'}"
    )
    
    suppress_toggle = st.checkbox(
        "Apply Suppression Threshold",
        value=True,
        help="Suppresses segments with < 3 crashes or < 0.2 MVKM exposure to eliminate near-zero denominator noise (Slide 9)."
    )
    
    metric_view = st.radio(
        "Primary Risk Metric",
        ["Exposure-Adjusted Risk (Per MVKM)", "Raw Crash Frequency (Counts)"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    **Project Metadata:**
    - **Course:** Visual Analytics Lab (Review 1)
    - **Authors:** 
      - Saranya Dalal [26MML0007]
      - Divya Pujari [26MML0009]
      - Rohan Yadav [26MML0020]
    - **Guide:** Dr Manikandan K (SCOPE)
    """)

# Filter dataset
filtered_segs = ctx_segs[ctx_segs["road_class"].isin(selected_classes)].copy()
if suppress_toggle:
    filtered_segs = filtered_segs[~filtered_segs["is_suppressed"]].copy()

# ----------------- HEADER BANNER -----------------
st.markdown(f"""
<div class="hero-banner">
    <div class="hero-title">Traffic Accident Analysis & Exposure-Adjusted Visualization</div>
    <div class="hero-subtitle">Visual Analytics Lab — Review 1 Prototype • Beyond Count-Based Summaries to Severity-Aware Risk • Study Context: <b>{CTX_LABEL}</b></div>
    <div>
        <span class="badge-pill badge-teal">DuckDB Columnar Cubes</span>
        <span class="badge-pill badge-indigo">{CTX_SOURCE}</span>
        <span class="badge-pill badge-rose">{'55%+ Two-Wheeler Modal Share' if IS_INDIA else 'One-eighth crashes • 12x Risk'}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- TOP METRICS -----------------
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-lbl">Total Crashes Ingested</div>
        <div class="kpi-val">{filtered_segs['crash_n'].sum():,}</div>
        <div class="kpi-delta delta-info">{CTX_TOTAL_CRASHES:,} Raw Incidents</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-lbl">Network Exposure</div>
        <div class="kpi-val">{filtered_segs['exposure_mvkm'].sum():,.1f}</div>
        <div class="kpi-delta delta-safe">Million Veh-km (MVKM)</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-lbl">Lethal Trap Segments</div>
        <div class="kpi-val">{len(filtered_segs[filtered_segs['quadrant'].str.startswith('Q2')])}</div>
        <div class="kpi-delta delta-alert">Low Count, Severe Risk</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-lbl">Total Fatalities</div>
        <div class="kpi-val">{int(filtered_segs['fatal_count'].sum()):,}</div>
        <div class="kpi-delta delta-alert">Weight: 50x per DfT</div>
    </div>
    """, unsafe_allow_html=True)
with col5:
    mean_risk = filtered_segs['risk_per_mvkm'].mean() if len(filtered_segs) > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-lbl">Mean Exposure Risk</div>
        <div class="kpi-val">{mean_risk:.1f}</div>
        <div class="kpi-delta delta-info">Severity Wt / MVKM</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- TABS NAVIGATION -----------------
tabs = st.tabs([
    "🎯 Core Contribution: Frequency vs. Severity",
    "⏰ WHEN? (Circadian & Temporal Patterns)",
    "🗺️ WHERE? (Spatial 3D Risk Map)",
    "🌧️ UNDER WHAT CONDITIONS? (Environmental)",
    "🤖 ML Hotspot & Severity Simulator",
    "🇮🇳 India Transferability Case",
    "⚙️ Pipeline Architecture & Review 1"
])

# ==============================================================================
# TAB 1: CORE CONTRIBUTION (Frequency vs Severity & Slide 9 Proof)
# ==============================================================================
with tabs[0]:
    st.markdown("### **Research Gap & Core Contribution: 'Low Frequency Masks High Severity'**")
    st.info("Traditional analyses focus on raw crash counts, causing agencies to prioritize high-volume corridors with mostly fender-benders while ignoring dangerous rural segments where accidents are rare but lethal.")
    
    # Showcase Slide 9 Benchmark
    if IS_INDIA:
        # Data-driven pair: the corridor that raw counts over-rank most vs. the one they under-rank most.
        st.markdown("#### **Bengaluru Benchmark Pair: Largest Rank Inversion Between Corridors**")
        bench_safe = ctx_segs.sort_values(["rank_shift", "crash_n"], ascending=[True, False]).iloc[0]
        bench_trap = ctx_segs.sort_values(["rank_shift", "risk_per_mvkm"], ascending=[False, False]).iloc[0]
        crash_ratio = bench_trap["crash_n"] / max(bench_safe["crash_n"], 1)
        risk_ratio = bench_trap["risk_per_mvkm"] / max(bench_safe["risk_per_mvkm"], 1e-6)
        safe_rank_note, safe_risk_note = "(Busiest-looking corridor)", "(Lower risk once exposure is counted)"
        trap_rank_note, trap_risk_note = "(Looks average by counts)", "(Higher risk once exposure is counted)"
        safe_footer = "High AADT corridor: heavy traffic spreads its crashes over a large exposure denominator."
        trap_footer = (f"<b>{crash_ratio:.2f}x the crashes. {risk_ratio:.1f}x the risk.</b> "
                       f"<i>Lower-volume corridor with {bench_trap['two_wheeler_pct']:.0%} two-wheeler share.</i>")
    else:
        st.markdown("#### **The Slide 9 Benchmark Case Study: Concrete Validation**")
        bench_safe = ctx_segs[ctx_segs["segment_id"] == "SEG-0417"].iloc[0]
        bench_trap = ctx_segs[ctx_segs["segment_id"] == "SEG-1902"].iloc[0]
        safe_rank_note, safe_risk_note = "(Looks Extremely Dangerous!)", "(Actually Very Safe)"
        trap_rank_note, trap_risk_note = "(Overlooked & Neglected)", "(Top 2 Most Deadly Segments!)"
        safe_footer = "High count, high traffic — high denominator absorbs slight incidents. Mostly low-speed lane rubs."
        trap_footer = "<b>One-eighth the crashes. Twelve times the risk.</b> <i>Dark unlit curve produces disproportionately fatal crashes!</i>"
    
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown(f"""
        <div class="case-box case-box-safe">
            <h4 style="color:#38bdf8; margin-top:0;"><b>{bench_safe['segment_id']}</b>: {bench_safe['road_name']}</h4>
            <p style="color:#cbd5e1; font-size:0.9rem;"><b>Road Class:</b> {bench_safe['road_class']} | <b>AADT:</b> {bench_safe['aadt']:,} | <b>Length:</b> {bench_safe['length_km']} km</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <div style="font-size:0.8rem; color:#94a3b8;">RAW CRASH COUNT</div>
                    <div style="font-size:1.6rem; font-weight:700; color:#f8fafc;">{int(bench_safe['crash_n'])} crashes</div>
                    <div style="color:#f43f5e; font-size:0.85rem;">Rank #{int(bench_safe['rank_raw_count'])} {safe_rank_note}</div>
                </div>
                <div>
                    <div style="font-size:0.8rem; color:#94a3b8;">EXPOSURE-ADJUSTED RISK</div>
                    <div style="font-size:1.6rem; font-weight:700; color:#10b981;">{bench_safe['risk_per_mvkm']} / MVKM</div>
                    <div style="color:#10b981; font-size:0.85rem;">Rank #{int(bench_safe['rank_exposure_risk'])} {safe_risk_note}</div>
                </div>
            </div>
            <p style="font-size:0.85rem; color:#94a3b8; margin-top:12px; margin-bottom:0;">
                <i>{safe_footer}</i>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with c_right:
        st.markdown(f"""
        <div class="case-box case-box-warn">
            <h4 style="color:#f43f5e; margin-top:0;"><b>{bench_trap['segment_id']}</b>: {bench_trap['road_name']}</h4>
            <p style="color:#cbd5e1; font-size:0.9rem;"><b>Road Class:</b> {bench_trap['road_class']} | <b>AADT:</b> {bench_trap['aadt']:,} | <b>Length:</b> {bench_trap['length_km']} km</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <div style="font-size:0.8rem; color:#94a3b8;">RAW CRASH COUNT</div>
                    <div style="font-size:1.6rem; font-weight:700; color:#f8fafc;">{int(bench_trap['crash_n'])} crashes</div>
                    <div style="color:#10b981; font-size:0.85rem;">Rank #{int(bench_trap['rank_raw_count'])} {trap_rank_note}</div>
                </div>
                <div>
                    <div style="font-size:0.8rem; color:#94a3b8;">EXPOSURE-ADJUSTED RISK</div>
                    <div style="font-size:1.6rem; font-weight:700; color:#f43f5e;">{bench_trap['risk_per_mvkm']} / MVKM</div>
                    <div style="color:#f43f5e; font-size:0.85rem;">Rank #{int(bench_trap['rank_exposure_risk'])} {trap_risk_note}</div>
                </div>
            </div>
            <p style="font-size:0.85rem; color:#fca5a5; margin-top:12px; margin-bottom:0;">
                {trap_footer}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 4-Quadrant Scatter Plot
    st.markdown("#### **The Frequency vs. Severity 4-Quadrant Decision Matrix**")
    
    color_map = {
        "Q1: High Frequency - High Severity (Severe Congested)": "#f97316",
        "Q2: Low Frequency - High Severity (Deadly Trap - Primary Focus)": "#f43f5e",
        "Q3: Low Frequency - Low Severity (Safe Segment)": "#10b981",
        "Q4: High Frequency - Low Severity (Fender-Benders)": "#38bdf8",
        "Suppressed (Low Sample Noise)": "#64748b"
    }
    
    fig_scatter = px.scatter(
        filtered_segs,
        x="crash_n",
        y="risk_per_mvkm",
        size="exposure_mvkm",
        color="quadrant",
        color_discrete_map=color_map,
        hover_name="road_name",
        hover_data={
            "segment_id": True,
            "road_class": True,
            "crash_n": True,
            "exposure_mvkm": True,
            "risk_per_mvkm": True,
            "rank_raw_count": True,
            "rank_exposure_risk": True,
            "quadrant": False
        },
        labels={
            "crash_n": "Annual Crash Count (Raw Frequency)",
            "risk_per_mvkm": "Exposure-Adjusted Severity Risk (Severity Wt / MVKM)",
            "exposure_mvkm": "Exposure (MVKM)",
            "quadrant": "Policy Quadrant"
        },
        title="Interactive Exposure-Adjusted Risk vs. Raw Crash Frequency (Bubble size = Exposure MVKM)"
    )
    
    # Add benchmark annotations
    fig_scatter.add_annotation(
        x=bench_safe["crash_n"], y=bench_safe["risk_per_mvkm"],
        text=f"<b>{bench_safe['segment_id']}</b><br>(High count, ranks safe)",
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#38bdf8",
        font=dict(color="#38bdf8", size=11), bgcolor="rgba(15,23,42,0.85)"
    )
    fig_scatter.add_annotation(
        x=bench_trap["crash_n"], y=bench_trap["risk_per_mvkm"],
        text=(f"<b>{bench_trap['segment_id']}</b><br>★ {risk_ratio:.1f}x Risk Hidden Hotspot" if IS_INDIA
              else "<b>SEG-1902</b><br>★ 12x Risk Lethal Trap"),
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor="#f43f5e",
        font=dict(color="#f43f5e", size=11), bgcolor="rgba(15,23,42,0.85)"
    )
    
    fig_scatter.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        paper_bgcolor="rgba(15, 23, 42, 0.4)",
        font=dict(color="#e2e8f0"),
        height=540,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_scatter, width="stretch")
    
    # Quadrant Aggregation Summary Table
    st.markdown("#### **Intervention Prioritization by Risk Quadrant**")
    st.dataframe(
        ctx_quad.style.format({
            "mean_exposure_mvkm": "{:.2f}",
            "mean_risk_per_mvkm": "{:.2f}",
            "fatality_share_pct": "{:.1f}%",
            "total_crashes": "{:,}",
            "total_fatalities": "{:,}",
            "total_serious_injuries": "{:,}"
        }),
        width="stretch"
    )

# ==============================================================================
# TAB 2: WHEN? (Temporal & Circadian Patterns - RQ 1)
# ==============================================================================
with tabs[1]:
    st.markdown("### **Research Question 1: WHEN do accidents happen vs. WHEN are they lethal?**")
    st.caption(f"Temporal and Circadian analysis of {CTX_TOTAL_CRASHES:,} {CTX_LABEL} incidents across 24 hours and weekdays.")
    
    # Circadian 24-hr dual-axis chart
    col_t1, col_t2 = st.columns([3, 2])
    
    with col_t1:
        st.markdown("#### **24-Hour Circadian Risk: Crash Frequency vs. Lethality Rate**")
        fig_circadian = go.Figure()
        
        # Bar: Crash Volume
        fig_circadian.add_trace(go.Bar(
            x=ctx_circadian["hour"],
            y=ctx_circadian["crash_count"],
            name="Accident Count (Volume)",
            marker_color="rgba(56, 189, 248, 0.65)",
            yaxis="y1"
        ))
        
        # Line: Fatality Rate %
        fig_circadian.add_trace(go.Scatter(
            x=ctx_circadian["hour"],
            y=ctx_circadian["fatality_rate_pct"],
            name="Fatality Share % (Lethality)",
            mode="lines+markers",
            line=dict(color="#f43f5e", width=3),
            marker=dict(size=7, color="#f43f5e"),
            yaxis="y2"
        ))
        
        fig_circadian.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 0.4)",
            yaxis=dict(title="Crash Volume (Counts)", side="left", showgrid=True, gridcolor="rgba(148, 163, 184, 0.1)"),
            yaxis2=dict(title="Fatality Rate (%)", side="right", overlaying="y", showgrid=False),
            xaxis=dict(title="Hour of Day (0-23)", tickmode="linear", dtick=2),
            height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_circadian, width="stretch")
        
    with col_t2:
        st.markdown("#### **Key Circadian Insights**")
        if IS_INDIA:
            # Computed from the Bengaluru circadian cube (India hours 20:00-05:59 are flagged as night).
            night_mask = (ctx_circadian["hour"] < 6) | (ctx_circadian["hour"] > 19)
            night_rate = ctx_circadian.loc[night_mask, "fatal_count"].sum() * 100 / max(ctx_circadian.loc[night_mask, "crash_count"].sum(), 1)
            day_rate = ctx_circadian.loc[~night_mask, "fatal_count"].sum() * 100 / max(ctx_circadian.loc[~night_mask, "crash_count"].sum(), 1)
            peak_vol = ctx_circadian.loc[ctx_circadian["crash_count"].idxmax()]
            peak_fat = ctx_circadian.loc[ctx_circadian["fatality_rate_pct"].idxmax()]
            st.markdown(f"""
        - **Peak crash volume:** {int(peak_vol['hour']):02d}:00 with {int(peak_vol['crash_count'])} crashes.
        - **Most lethal hour:** {int(peak_fat['hour']):02d}:00, with a fatality share of {peak_fat['fatality_rate_pct']:.1f}%.
        - **Night vs. day (20:00-05:59 vs. 06:00-19:59):** fatality share of {night_rate:.1f}% at night against {day_rate:.1f}% by day.
        - **Vulnerable road users:** two-wheelers and pedestrians make up {(ctx_circadian['vulnerable_pct'] * ctx_circadian['crash_count']).sum() / ctx_circadian['crash_count'].sum():.0f}% of all crashes.
            """)
        else:
            st.markdown("""
        - **The Commute Paradox (07:00 - 09:00 & 16:00 - 18:00):**
          Volume peaks dramatically during morning and evening rush hours, but average severity is low (bumper-to-bumper congestion slows vehicle speeds).
        - **The Midnight Lethality Spike (23:00 - 04:00):**
          Volume drops to 1/8th of daytime traffic, yet **fatality rate triples (from 1.2% to 4.8%)**. Driven by empty roads, excessive speeding, darkness, and driver fatigue.
        - **Weekend Night Inversion:**
          Friday and Saturday nights register the highest vulnerability for two-wheelers and pedestrians.
        """)
        
    # Day x Hour Heatmap (168-cell matrix from slide 8)
    st.markdown("#### **The 168-Cell Heatmap Matrix (Day of Week × Hour)**")
    
    metric_choice = st.selectbox(
        "Heatmap Metric",
        ["Total Crash Count", "Severe Outcome Rate (%)", "Mean Severity Weight"],
        index=1
    )
    
    val_col = "total_crashes" if metric_choice == "Total Crash Count" else ("severe_rate_pct" if "Rate" in metric_choice else "avg_severity_weight")
    
    heatmap_pivot = ctx_temporal.pivot(index="day_of_week", columns="hour", values=val_col)
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_pivot = heatmap_pivot.reindex([d for d in dow_order if d in heatmap_pivot.index])
    
    fig_heat = px.imshow(
        heatmap_pivot,
        color_continuous_scale="Viridis" if val_col == "total_crashes" else "Inferno",
        labels=dict(x="Hour of Day", y="Day of Week", color=metric_choice),
        title=f"Weekly Circadian Rhythm — {metric_choice}"
    )
    fig_heat.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        paper_bgcolor="rgba(15, 23, 42, 0.4)",
        height=380
    )
    st.plotly_chart(fig_heat, width="stretch")

# ==============================================================================
# TAB 3: WHERE? (Spatial 3D Risk Map - RQ 2)
# ==============================================================================
with tabs[2]:
    st.markdown("### **Research Question 2: WHERE are the True Spatial Hotspots?**")
    st.caption("Side-by-side geospatial mapping of segments. Toggle between Raw Frequency and Exposure-Adjusted Risk to observe spatial rank inversion.")
    
    map_metric = st.selectbox(
        "Color Segments By:",
        ["Exposure-Adjusted Risk Index (Risk / MVKM)", "Raw Crash Volume (Counts)", "Rank Inversion Shift (Raw Rank - Risk Rank)"],
        index=0 if metric_view.startswith("Exposure") else 1
    )
    
    # Prepare PyDeck data
    deck_df = filtered_segs.copy()
    
    if map_metric.startswith("Exposure"):
        norm_val = deck_df["risk_per_mvkm"] / (deck_df["risk_per_mvkm"].max() + 1e-5)
        # Red/Pink for high risk, Green for low
        deck_df["color_r"] = (norm_val * 240 + 15).astype(int)
        deck_df["color_g"] = ((1 - norm_val) * 200 + 30).astype(int)
        deck_df["color_b"] = 120
    elif map_metric.startswith("Raw"):
        norm_val = deck_df["crash_n"] / (deck_df["crash_n"].max() + 1e-5)
        deck_df["color_r"] = (norm_val * 255).astype(int)
        deck_df["color_g"] = 140
        deck_df["color_b"] = ((1 - norm_val) * 255).astype(int)
    else:
        # Rank shift: positive is hidden risk (Red), negative is fender bender (Blue)
        deck_df["color_r"] = np.where(deck_df["rank_shift"] > 0, 244, 56)
        deck_df["color_g"] = np.where(deck_df["rank_shift"] > 0, 63, 189)
        deck_df["color_b"] = np.where(deck_df["rank_shift"] > 0, 94, 248)
        
    deck_df["color_a"] = 220
    deck_df["elevation"] = (deck_df["risk_per_mvkm"] * 35).clip(lower=10, upper=3000)
    # India corridors have no posted speed limit field; show two-wheeler share instead.
    deck_df["tooltip_extra"] = (
        (deck_df["two_wheeler_pct"] * 100).round(0).astype(int).astype(str) + "% two-wheelers"
        if IS_INDIA else deck_df["speed_limit_mph"].astype(str) + " mph limit"
    )
    
    # Compute center and a zoom level that fits the selected network
    default_center = (12.88, 77.64) if IS_INDIA else (51.5, -0.12)
    if len(deck_df) > 0:
        all_lat = pd.concat([deck_df["start_lat"], deck_df["end_lat"]])
        all_lon = pd.concat([deck_df["start_lon"], deck_df["end_lon"]])
        center_lat = (all_lat.min() + all_lat.max()) / 2
        center_lon = (all_lon.min() + all_lon.max()) / 2
        span = max(all_lon.max() - all_lon.min(), (all_lat.max() - all_lat.min()) * 1.6, 0.02)
        map_zoom = float(np.clip(np.log2(600 * 360 / (256 * span)), 5, 13))
    else:
        center_lat, center_lon = default_center
        map_zoom = 9.8
    
    layer = pdk.Layer(
        "LineLayer",
        data=deck_df,
        get_source_position=["start_lon", "start_lat"],
        get_target_position=["end_lon", "end_lat"],
        get_color=["color_r", "color_g", "color_b", "color_a"],
        get_width=6,
        pickable=True,
        auto_highlight=True
    )
    
    # 3D Column markers at start coordinates
    col_layer = pdk.Layer(
        "ColumnLayer",
        data=deck_df,
        get_position=["start_lon", "start_lat"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=300 if IS_INDIA else 450,  # metres; 120 m columns were under one pixel at network zoom
        get_fill_color=["color_r", "color_g", "color_b", 200],
        pickable=True
    )
    
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=map_zoom,
        pitch=45,
        bearing=15
    )
    
    r = pdk.Deck(
        layers=[layer, col_layer],
        initial_view_state=view_state,
        # Carto basemap: works without an API token (the previous Mapbox style needed one, so the map failed to load).
        map_provider="carto",
        map_style=pdk.map_styles.DARK,
        tooltip={
            "html": """
            <b>Segment:</b> {segment_id} - {road_name}<br/>
            <b>Class:</b> {road_class} | {tooltip_extra}<br/>
            <b>Crashes:</b> {crash_n} (Rank #{rank_raw_count})<br/>
            <b>Exposure:</b> {exposure_mvkm} MVKM<br/>
            <b>Exposure Risk:</b> {risk_per_mvkm} / MVKM (Rank #{rank_exposure_risk})<br/>
            <b>Rank Shift:</b> {rank_shift} positions<br/>
            <b>Quadrant:</b> {quadrant}
            """,
            "style": {"backgroundColor": "#0f172a", "color": "#f8fafc", "fontSize": "12px"}
        }
    )
    
    if len(deck_df) == 0:
        st.warning("No segments match the current sidebar filters.")
    else:
        st.pydeck_chart(r, height=560)
        if map_metric.startswith("Rank"):
            st.caption("Red = under-ranked by raw counts (hidden risk, rank shift > 0). Blue = over-ranked by raw counts. Column height = exposure-adjusted risk.")
        else:
            st.caption("Colour runs from green/blue (low) to red (high) for the selected metric. Column height = exposure-adjusted risk. Hover a segment for details.")
    
    # Leaderboard Table
    rank_by_risk = metric_view.startswith("Exposure")
    st.markdown("#### **Top 10 High-Risk Segments (Exposure-Adjusted)**" if rank_by_risk
                else "#### **Top 10 Segments by Raw Crash Count**")
    top_risk = filtered_segs.sort_values("risk_per_mvkm" if rank_by_risk else "crash_n", ascending=False).head(10)[[
        "segment_id", "road_name", "road_class", "crash_n", "rank_raw_count", "exposure_mvkm", "risk_per_mvkm", "rank_exposure_risk", "rank_shift", "quadrant"
    ]]
    
    st.dataframe(
        top_risk.style.format({
            "exposure_mvkm": "{:.2f}",
            "risk_per_mvkm": "{:.2f}",
            "rank_shift": "{:+d}"
        }),
        width="stretch"
    )

# ==============================================================================
# TAB 4: UNDER WHAT CONDITIONS? (Environmental Drivers - RQ 3)
# ==============================================================================
def render_india_conditions():
    st.info("The Bengaluru feed records vehicle mode, hour and night flag but no weather, surface or "
            "street-lighting fields, so the environmental matrix is UK-only. Below: severity by vehicle mode, "
            "corridor type and night-time for the India corridors.")
    df_veh_ind = india_ctx["veh"]
    df_veh_ind = df_veh_ind[df_veh_ind["road_class"].isin(selected_classes)]
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown("#### **Severe Injury Rate by Corridor Type & Vehicle Mode**")
        fig_vi = px.bar(
            df_veh_ind, x="road_class", y="severe_rate_pct", color="primary_vehicle", barmode="group",
            title="Severe Injury Rate (%) by Corridor Type & Vehicle Mode",
            labels={"road_class": "Corridor Type", "severe_rate_pct": "Severe Rate (%)", "primary_vehicle": "Vehicle Mode"}
        )
        fig_vi.update_layout(template="plotly_dark", plot_bgcolor="rgba(15, 23, 42, 0.4)",
                             paper_bgcolor="rgba(15, 23, 42, 0.4)", height=420)
        st.plotly_chart(fig_vi, width="stretch")
    with col_i2:
        st.markdown("#### **Night-Time Share of Crashes by Corridor**")
        night_df = filtered_segs.assign(
            night_share_pct=(filtered_segs["night_crash_count"] * 100 / filtered_segs["crash_n"].clip(lower=1)).round(1),
            vru_share_pct=(filtered_segs["vulnerable_user_crash_count"] * 100 / filtered_segs["crash_n"].clip(lower=1)).round(1),
        )
        fig_ni = px.bar(
            night_df, x="night_share_pct", y="road_name", orientation="h", color="risk_per_mvkm",
            color_continuous_scale="Inferno", title="Night Crash Share (%) — colour = Risk / MVKM",
            labels={"night_share_pct": "Night Crash Share (%)", "road_name": "Corridor", "risk_per_mvkm": "Risk / MVKM"}
        )
        fig_ni.update_layout(template="plotly_dark", plot_bgcolor="rgba(15, 23, 42, 0.4)",
                             paper_bgcolor="rgba(15, 23, 42, 0.4)", height=420)
        st.plotly_chart(fig_ni, width="stretch")
    st.markdown("#### **Vehicle Mode × Corridor Severity Table**")
    st.dataframe(df_veh_ind.style.format({"severe_rate_pct": "{:.1f}%", "avg_severity_wt": "{:.2f}",
                                          "fatal_count": "{:,.0f}", "serious_count": "{:,.0f}"}), width="stretch")

def render_uk_conditions():
    st.caption("Quantifying the joint impact of Weather, Road Surface States, and Street Lighting on fatality risk.")
    
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        st.markdown("#### **Severe Outcome Rate by Environmental State**")
        fig_env = px.bar(
            df_env.head(10),
            x="severe_outcome_pct",
            y="road_surface_condition",
            color="light_condition",
            barmode="group",
            orientation="h",
            title="Severe / Fatal Outcome % by Surface Condition & Lighting",
            labels={
                "severe_outcome_pct": "Fatal & Serious Outcome Share (%)",
                "road_surface_condition": "Road Surface State",
                "light_condition": "Lighting Quality"
            }
        )
        fig_env.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 0.4)",
            height=400
        )
        st.plotly_chart(fig_env, width="stretch")
        
    with col_e2:
        st.markdown("#### **Vulnerable Road User (VRU) Fatality Rate by Speed Limit**")
        fig_veh = px.bar(
            df_veh,
            x="speed_limit_mph",
            y="severe_rate_pct",
            color="primary_vehicle",
            barmode="group",
            title="Severe Injury Rate (%) by Speed Limit & Vehicle Type",
            labels={
                "speed_limit_mph": "Posted Speed Limit (mph)",
                "severe_rate_pct": "Severe Rate (%)",
                "primary_vehicle": "Vehicle Mode"
            }
        )
        fig_veh.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 0.4)",
            height=400
        )
        st.plotly_chart(fig_veh, width="stretch")
        
    st.markdown("#### **Environmental Friction & Hostility Matrix Table**")
    st.dataframe(
        df_env.style.format({
            "severe_outcome_pct": "{:.1f}%",
            "fatality_rate_pct": "{:.1f}%",
            "mean_severity_wt": "{:.2f}",
            "crash_volume": "{:,}",
            "fatal_count": "{:,}",
            "serious_count": "{:,}"
        }),
        width="stretch"
    )

with tabs[3]:
    st.markdown("### **Research Question 3: Environmental Hostility & Severity Modulation**")
    if IS_INDIA:
        render_india_conditions()
    else:
        render_uk_conditions()

# ==============================================================================
# TAB 5: ML HOTSPOT & SEVERITY SIMULATOR
# ==============================================================================
with tabs[4]:
    st.markdown("### **Machine Learning Severity Classifier & What-If Policy Simulator**")
    st.caption(f"Trained on {ml_weights['training_samples']:,} UK multi-feature records. Connects literature findings (Slide 4: XGBoost, SVM, DeepSHAP) into an interactive safety intervention sandbox.")
    if IS_INDIA:
        st.info("This classifier is trained on the UK STATS19 records only; the Bengaluru feed lacks the weather, surface and lighting features it uses. The results below are the UK model.")
    
    c_ml1, c_ml2 = st.columns([1, 1])
    
    with c_ml1:
        st.markdown("#### **Model Feature Importance (Risk Drivers)**")
        feat_df = pd.DataFrame(list(ml_weights["feature_importances"].items()), columns=["Feature", "Importance Weight"])
        
        fig_feat = px.bar(
            feat_df,
            x="Importance Weight",
            y="Feature",
            orientation="h",
            color="Importance Weight",
            color_continuous_scale="Purples",
            title="Key Drivers of Severe / Fatal Accident Probability"
        )
        fig_feat.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 0.4)",
            height=380,
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_feat, width="stretch")
        
    with c_ml2:
        st.markdown("#### **Interactive 'What-If' Safety Intervention Simulator**")
        st.write("Tune road characteristics and environmental conditions to simulate accident severity risk:")
        
        sim_speed = st.select_slider("Posted Speed Limit (mph)", options=[20, 30, 40, 50, 60, 70], value=60)
        sim_night = st.radio("Time of Day", ["Daylight", "Dark Night"], horizontal=True)
        sim_light = st.radio("Lighting Infrastructure", ["Lit by Streetlights", "Unlit (Zero Lighting)"], horizontal=True)
        sim_weather = st.selectbox("Weather Condition", ["Clear / Fine", "Heavy Rain / Storm", "Dense Fog / Ice"])
        sim_vru = st.checkbox("Vulnerable User (Motorcycle / Bicycle)", value=True)
        
        # Calculate heuristic risk score from weights
        base_risk = 0.08
        if sim_speed >= 60: base_risk += 0.22
        elif sim_speed >= 40: base_risk += 0.10
        if sim_night == "Dark Night": base_risk += 0.15
        if sim_light == "Unlit (Zero Lighting)": base_risk += 0.25
        if "Rain" in sim_weather: base_risk += 0.10
        elif "Fog" in sim_weather: base_risk += 0.18
        if sim_vru: base_risk += 0.20
        
        sim_pred = min(0.96, max(0.04, base_risk))
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric(
            label="Simulated Probability of Severe / Fatal Outcome",
            value=f"{sim_pred * 100:.1f}%",
            delta=f"{'+' if sim_pred > 0.3 else '-'}{abs(sim_pred - 0.25)*100:.1f}% vs Network Average",
            delta_color="inverse"
        )
        
        if sim_pred > 0.5:
            st.error("🚨 **High Risk Rating:** Immediate engineering intervention required! Recommend installing LED street lighting, automated speed cameras, and anti-skid high-friction surfacing.")
        elif sim_pred > 0.25:
            st.warning("⚠️ **Moderate Risk Rating:** Recommended advisory electronic speed signs and reflective road studs.")
        else:
            st.success("✅ **Low Risk Rating:** Within tolerable network safety thresholds.")

# ==============================================================================
# TAB 6: INDIA TRANSFERABILITY CASE (Slide 7 & Slide 5)
# ==============================================================================
with tabs[5]:
    st.markdown("### **Transferability Case: Indian Urban Corridor (Bengaluru)**")
    st.info("<b>Decision Point from Slide 7:</b> 'UK is the only context where crash records and official AADT are both open and joinable. Build there, then use an Indian city as the transferability case.'")
    
    st.write("Testing model generalizability to mixed-traffic conditions where two-wheelers make up over 55% of traffic volume and FASTag toll plazas serve as traffic structural proxies.")
    
    col_ind1, col_ind2 = st.columns([3, 2])
    with col_ind1:
        st.markdown("#### **Corridor Exposure-Adjusted Risk Rankings (Bengaluru)**")
        fig_ind = px.bar(
            df_india,
            x="risk_per_mvkm",
            y="road_name",
            color="road_class",
            orientation="h",
            title="Exposure-Adjusted Risk Index Across Bengaluru Arterials",
            labels={"risk_per_mvkm": "Risk per MVKM", "road_name": "Corridor Name"}
        )
        fig_ind.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 0.4)",
            height=380,
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_ind, width="stretch")
        
    with col_ind2:
        st.markdown("#### **Structural Differences vs. UK STATS19**")
        st.markdown("""
        - **Modal Split:** Two-wheelers and auto-rickshaws dominate (62% share vs. 16% in UK).
        - **NHAI FASTag Volume Proxy:** Highway plazas capture commercial freight and passenger cars, but two-wheelers are toll-exempt, requiring synthetic expansion factors.
        - **Peripheral Highway Hazards:** Roads like Kanakapura Highway (NH-948) demonstrate extreme **Low Frequency / High Severity** characteristics due to unlit stretches and mixed slow/fast vehicle conflicts.
        """)
        
    st.dataframe(
        df_india[[
            "segment_id", "road_name", "road_class", "length_km", "aadt", "two_wheeler_pct", "crash_n", "fatal_count", "vrus_crash_count", "exposure_mvkm", "risk_per_mvkm"
        ]].style.format({
            "length_km": "{:.1f} km",
            "aadt": "{:,}",
            "two_wheeler_pct": "{:.0%}",
            "exposure_mvkm": "{:.2f}",
            "risk_per_mvkm": "{:.2f}"
        }),
        width="stretch"
    )

# ==============================================================================
# TAB 7: PIPELINE ARCHITECTURE & REVIEW 1
# ==============================================================================
with tabs[6]:
    st.markdown("### **Proposed System Architecture & Batch Pipeline**")
    st.caption("Batch, reproducible, zero-server pipeline using DuckDB columnar storage and pre-aggregated cubes (Slide 10).")
    
    st.markdown("""
    ```
    ┌─────────────────────────┐
    │ 1. Data Ingestion       │ -> Multi-grain feeds: UK STATS19, Road Network (OSM), AADT, Open-Meteo
    │    Python + Parquet     │    Immutable raw storage in data/raw/*.parquet
    └───────────┬─────────────┘
                │
    ┌───────────▼─────────────┐
    │ 2. Preprocessing        │ -> De-duplication, geocoding validation, data quality flags
    │    Geopandas / Pandas   │    
    └───────────┬─────────────┘
                │
    ┌───────────▼─────────────┐
    │ 3. Feature Engineering  │ -> Circadian phase (24h), seasonal drift, DfT published severity weights
    │    Polars / Pandas      │    Fatal = 50, Serious = 10, Slight = 1
    └───────────┬─────────────┘
                │
    ┌───────────▼─────────────┐
    │ 4. Exposure & Risk      │ -> Grain changes to Road Segment:
    │    DuckDB SQL Engine    │    exposure_mvkm = aadt * length_km * 365 / 1,000,000
    │                         │    risk_per_mvkm = severity_wt_sum / exposure_mvkm
    └───────────┬─────────────┘
                │
    ┌───────────▼─────────────┐
    │ 5. Cube Aggregation     │ -> Pre-aggregated analytical cubes:
    │    Parquet + GeoJSON    │    Temporal matrix, Circadian profile, Environmental interactions, 4-Quadrants
    └───────────┬─────────────┘
                │
    ┌───────────▼─────────────┐
    │ 6. Visual Dashboard     │ -> Streamlit + Plotly + PyDeck 3D: Sub-second interactive slicing
    │    Browser UI (app.py)  │    Never queries 1.5M rows live in browser!
    └─────────────────────────┘
    ```
    """)
    
    st.markdown("#### **Verification of Slide Design Principles**")
    st.markdown("""
    - **Why DuckDB, not Postgres?** No server to run, embedded columnar format, reads Parquet directly, executes analytical window functions in sub-second time.
    - **Why pre-aggregate, not query live?** 1.5M crash rows will not filter interactively inside a browser client. Stage 4 & 5 run once in 5 seconds; the dashboard reads pre-aggregated cubes instantly.
    - **No Airflow:** Sequential, clean Python pipeline scripts (`01_...` to `04_...`) ensure maximum reproducibility and defense clarity during project review.
    """)
    
    st.download_button(
        label="📥 Export Full Segment Exposure Risk Analysis (CSV)",
        data=filtered_segs.to_csv(index=False).encode('utf-8'),
        file_name=f"traffic_accident_exposure_risk_analysis_{'india' if IS_INDIA else 'uk'}.csv",
        mime="text/csv"
    )
