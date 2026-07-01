"""
Phantom Signal — Main Streamlit Application Entry Point (PRD-011)
OSInt Early Warning Framework · UOB Innovation Challenge POC
"""
import sys
import logging
from pathlib import Path

# ── Path setup (must come first) ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from config import APP_TITLE, APP_SUBTITLE, APP_VERSION, COLOR_TEAL, COLOR_NAVY
from data.database import init_db, count_raw_signals_by_status, get_alerts_count_today

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_TITLE} — OSInt Early Warning",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"**{APP_TITLE}** {APP_VERSION} — UOB Innovation Challenge POC",
    },
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* === ROOT VARIABLES === */
:root {
    --bg-primary:   #060D1F;
    --bg-surface:   #0D1B3E;
    --bg-surface2:  #112244;
    --bg-elevated:  #162855;
    --border:       #1E3A5F;
    --teal:         #028090;
    --teal-light:   #03A4B8;
    --teal-glow:    rgba(2, 128, 144, 0.2);
    --text-primary: #E8EDF5;
    --text-muted:   #8FA3BF;
    --text-dim:     #4A6080;
    --critical:     #DC2626;
    --high:         #EA580C;
    --medium:       #D97706;
    --low:          #16A34A;
    --radius:       10px;
    --radius-lg:    16px;
    --shadow:       0 4px 24px rgba(0,0,0,0.4);
}

/* === GLOBAL === */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: var(--text-primary) !important;
}

.stApp {
    background-color: var(--bg-primary) !important;
}

/* === SIDEBAR === */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A1628 0%, #0D1B3E 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

[data-testid="stSidebarNav"] a {
    border-radius: var(--radius) !important;
    margin: 2px 8px !important;
    padding: 8px 12px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarNav"] a:hover {
    background: var(--teal-glow) !important;
    border-left: 3px solid var(--teal) !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--teal-glow) !important;
    border-left: 3px solid var(--teal-light) !important;
}

/* === BUTTONS === */
.stButton > button {
    background: linear-gradient(135deg, var(--teal) 0%, var(--teal-light) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 12px var(--teal-glow) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px var(--teal-glow) !important;
    filter: brightness(1.1) !important;
}

/* === METRICS === */
[data-testid="metric-container"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 16px 20px !important;
    box-shadow: var(--shadow) !important;
}

[data-testid="stMetricValue"] {
    color: var(--teal-light) !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
}

[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}

/* === TABLES === */
[data-testid="stDataFrame"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}

/* === INPUTS === */
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div input,
.stTextArea textarea {
    background: var(--bg-surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
}

/* === EXPANDERS === */
.streamlit-expanderHeader {
    background: var(--bg-surface) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

.streamlit-expanderContent {
    background: var(--bg-surface2) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-surface) !important;
    border-radius: var(--radius) !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

.stTabs [aria-selected="true"] {
    background: var(--teal) !important;
    color: white !important;
}

/* === PROGRESS BAR === */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--teal) 0%, var(--teal-light) 100%) !important;
    border-radius: 4px !important;
}

.stProgress > div {
    background: var(--bg-surface2) !important;
    border-radius: 4px !important;
}

/* === DIVIDERS === */
hr {
    border-color: var(--border) !important;
    margin: 16px 0 !important;
}

/* === ALERTS / INFO BOXES === */
.stAlert {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
}

/* === CUSTOM COMPONENTS === */
.ps-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    margin: 8px 0;
    box-shadow: var(--shadow);
    transition: border-color 0.2s ease;
}

.ps-card:hover {
    border-color: var(--teal);
}

.priority-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.badge-critical { background: rgba(220,38,38,0.2); color: #F87171; border: 1px solid #DC2626; }
.badge-high     { background: rgba(234,88,12,0.2);  color: #FB923C; border: 1px solid #EA580C; }
.badge-medium   { background: rgba(217,119,6,0.2);  color: #FCD34D; border: 1px solid #D97706; }
.badge-low      { background: rgba(22,163,74,0.2);  color: #4ADE80; border: 1px solid #16A34A; }

.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.status-pending    { background: rgba(107,114,128,0.2); color: #9CA3AF; }
.status-normalized { background: rgba(59,130,246,0.2);  color: #60A5FA; }
.status-alerted    { background: rgba(220,38,38,0.2);   color: #F87171; }
.status-discarded  { background: rgba(31,41,55,0.5);    color: #6B7280; }
.status-filtered   { background: rgba(139,92,246,0.2);  color: #A78BFA; }

.gate-pass {
    background: rgba(22,163,74,0.15);
    border: 1px solid rgba(22,163,74,0.4);
    border-radius: var(--radius);
    padding: 12px 16px;
    text-align: center;
}

.gate-fail {
    background: rgba(220,38,38,0.1);
    border: 1px solid rgba(220,38,38,0.3);
    border-radius: var(--radius);
    padding: 12px 16px;
    text-align: center;
}

.section-header {
    color: var(--teal-light);
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--teal);
}

.metric-card {
    background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-surface2) 100%);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 20px;
    text-align: center;
    box-shadow: var(--shadow);
}

.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--teal-light);
    margin: 0;
}

.metric-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

.rule-card {
    background: var(--bg-surface2);
    border-left: 3px solid var(--teal);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 14px 18px;
    margin: 8px 0;
}

.rule-logic {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #A8D8E0;
    background: rgba(2,128,144,0.08);
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 8px;
    border: 1px solid rgba(2,128,144,0.2);
}

.pipeline-stage {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    border-radius: var(--radius);
    margin: 6px 0;
    border: 1px solid var(--border);
    background: var(--bg-surface);
    transition: all 0.3s ease;
}

.pipeline-stage.active {
    border-color: var(--teal);
    background: var(--teal-glow);
}

.pipeline-stage.done {
    border-color: rgba(22,163,74,0.4);
    background: rgba(22,163,74,0.08);
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--teal); }

/* Hide Streamlit default elements */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Database Initialization ───────────────────────────────────────────────────

@st.cache_resource
def initialize_system():
    """Initialize database and seed data once per session."""
    logger.info("Initializing Phantom Signal system...")
    init_db()

    from data.synthetic_generator import generate_all_synthetic_data
    generate_all_synthetic_data()

    from data.seed_data import seed_demo_scenarios
    seed_demo_scenarios()

    logger.info("System initialized successfully")
    return True


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        # Logo / Brand
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #0D1B3E 0%, #028090 100%);
            border-radius: 12px;
            padding: 20px 16px;
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #1E3A5F;
        ">
            <div style="font-size: 2rem; margin-bottom: 8px;">📡</div>
            <div style="
                font-size: 1.3rem;
                font-weight: 800;
                color: white;
                letter-spacing: 1px;
            ">PHANTOM SIGNAL</div>
            <div style="
                font-size: 0.7rem;
                color: rgba(255,255,255,0.7);
                letter-spacing: 1.5px;
                text-transform: uppercase;
                margin-top: 4px;
            ">OSInt Early Warning</div>
            <div style="
                margin-top: 10px;
                padding: 3px 10px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                display: inline-block;
                font-size: 0.65rem;
                color: rgba(255,255,255,0.8);
            ">{APP_VERSION} · UOB Innovation Challenge</div>
        </div>
        """, unsafe_allow_html=True)

        # Live stats
        try:
            status_counts = count_raw_signals_by_status()
            alerts_today = get_alerts_count_today()
            total_signals = sum(status_counts.values())
            alerted = status_counts.get("ALERTED", 0)

            st.markdown("""
            <div style="margin-bottom: 8px;">
            <span style="font-size:0.7rem; color:#8FA3BF; text-transform:uppercase; letter-spacing:1px;">System Status</span>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(2)
            with cols[0]:
                st.metric("Signals", f"{total_signals:,}")
            with cols[1]:
                st.metric("Alerts", f"{alerted:,}")

        except Exception:
            st.markdown("""
            <div style="
                background: rgba(2,128,144,0.1);
                border: 1px solid rgba(2,128,144,0.3);
                border-radius: 8px;
                padding: 10px;
                font-size: 0.8rem;
                color: #03A4B8;
                text-align: center;
            ">● System Online</div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation hint
        st.markdown("""
        <div style="font-size:0.7rem; color:#4A6080; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
        Navigation
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:0.82rem; color:#8FA3BF; line-height:2;">
        📡 Live Feed<br>
        🔍 Fraud Intelligence<br>
        ⚖️ Relevance Assessment<br>
        🚨 Alert Viewer<br>
        🎯 Demo Mode
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div style="font-size:0.68rem; color:#4A6080; text-align:center; line-height:1.6;">
        Powered by Google Gemini 1.5 Pro<br>
        Synthetic data only · POC scope<br>
        © 2024 Phantom Signal
        </div>
        """, unsafe_allow_html=True)


# ── Home Page ──────────────────────────────────────────────────────────────────

def render_home():
    # Hero
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0D1B3E 0%, #071428 50%, #028090 200%);
        border-radius: 20px;
        padding: 48px 40px;
        margin-bottom: 32px;
        border: 1px solid #1E3A5F;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    ">
        <div style="position:relative;z-index:1;">
            <div style="
                display: inline-block;
                background: rgba(2,128,144,0.2);
                border: 1px solid rgba(2,128,144,0.5);
                border-radius: 20px;
                padding: 4px 14px;
                font-size: 0.75rem;
                color: #03A4B8;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                margin-bottom: 16px;
            ">UOB Innovation Challenge · POC</div>
            <h1 style="
                font-size: 3rem;
                font-weight: 900;
                color: white;
                margin: 0 0 12px 0;
                letter-spacing: -0.5px;
                line-height: 1.1;
            ">📡 Phantom Signal</h1>
            <p style="
                font-size: 1.2rem;
                color: rgba(255,255,255,0.7);
                margin: 0 0 24px 0;
                max-width: 600px;
                line-height: 1.6;
            ">AI-powered OSInt Early Warning Framework that transforms global threat intelligence into actionable Risk Alert Documents — in minutes, not weeks.</p>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
                <div style="
                    background: rgba(2,128,144,0.2);
                    border: 1px solid rgba(2,128,144,0.4);
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size:0.85rem;
                    color:#03A4B8;
                ">🤖 Gemini 1.5 Pro</div>
                <div style="
                    background: rgba(2,128,144,0.2);
                    border: 1px solid rgba(2,128,144,0.4);
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size:0.85rem;
                    color:#03A4B8;
                ">🛡️ 3-Gate Filtration</div>
                <div style="
                    background: rgba(2,128,144,0.2);
                    border: 1px solid rgba(2,128,144,0.4);
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size:0.85rem;
                    color:#03A4B8;
                ">📊 Monte Carlo Simulation</div>
                <div style="
                    background: rgba(2,128,144,0.2);
                    border: 1px solid rgba(2,128,144,0.4);
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size:0.85rem;
                    color:#03A4B8;
                ">📄 Auto PDF Generation</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    try:
        status_counts = count_raw_signals_by_status()
        alerts_today = get_alerts_count_today()
        normalized = status_counts.get("NORMALIZED", 0)
        alerted = status_counts.get("ALERTED", 0)
        discarded = status_counts.get("DISCARDED", 0)
        total = sum(status_counts.values())
    except Exception:
        total, normalized, alerted, discarded, alerts_today = 3, 3, 3, 0, 3

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Signals", f"{total:,}", help="All raw signals ingested")
    with c2:
        st.metric("Normalized", f"{normalized:,}", help="Processed by Gemini AI")
    with c3:
        st.metric("🚨 Alerted", f"{alerted:,}", help="Passed all 3 gates")
    with c4:
        st.metric("Discarded", f"{discarded:,}", help="Failed relevance filters")
    with c5:
        st.metric("Alerts Today", f"{alerts_today:,}", help="Risk Alert Documents generated")

    st.markdown("---")

    # Pipeline overview
    st.markdown('<p class="section-header">🔄 Intelligence Pipeline</p>', unsafe_allow_html=True)

    pipeline_steps = [
        ("01", "📡 OSInt Ingestion", "SPF · MAS · FBI IC3 · ENISA · Reddit", "#028090"),
        ("02", "🤖 AI Normalization", "Gemini 1.5 Pro extracts structured FraudSignal", "#0369a1"),
        ("03", "⚖️ 3-Gate Filtration", "Novelty · Customer Exposure · Control Gap", "#7c3aed"),
        ("04", "📊 Impact Simulation", "Monte Carlo · P10/P50/P90 · SGD exposure", "#b45309"),
        ("05", "📄 Alert Document", "Gemini generates 9-section Risk Alert PDF", "#dc2626"),
    ]

    cols = st.columns(len(pipeline_steps))
    for col, (num, title, desc, color) in zip(cols, pipeline_steps):
        with col:
            st.markdown(f"""
            <div style="
                background: linear-gradient(160deg, #0D1B3E 0%, #112244 100%);
                border: 1px solid {color}40;
                border-top: 3px solid {color};
                border-radius: 12px;
                padding: 20px 16px;
                text-align: center;
                height: 140px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="font-size:0.7rem; color:{color}; font-weight:700; letter-spacing:1px; margin-bottom:6px;">STAGE {num}</div>
                <div style="font-size:0.95rem; font-weight:700; color:white; margin-bottom:8px; line-height:1.3;">{title}</div>
                <div style="font-size:0.73rem; color:#8FA3BF; line-height:1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Demo scenarios preview
    st.markdown('<p class="section-header">🎬 Pre-loaded Demo Scenarios</p>', unsafe_allow_html=True)

    scenarios = [
        ("alert-sms-spoofing-001", "📱 SMS Spoofing", "CRITICAL", "180,000 retail customers at risk · SGD 6.2M–28.5M exposure · SG/MY"),
        ("alert-sextortion-001",   "💔 Sextortion Surge", "HIGH", "67,200 male retail customers · SGD 3.2M–22M exposure · ASEAN"),
        ("alert-deepfake-cfo-001", "🎭 Deepfake CFO Fraud", "HIGH", "11,000 trade finance customers · SGD 18M–125M exposure · SG/HK"),
    ]

    priority_css = {
        "CRITICAL": ("badge-critical", "#DC2626"),
        "HIGH":     ("badge-high",     "#EA580C"),
    }

    for alert_id, name, priority, description in scenarios:
        badge_cls, border_color = priority_css.get(priority, ("badge-low", "#16A34A"))
        st.markdown(f"""
        <div class="ps-card" style="border-left: 4px solid {border_color};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <span style="font-size:1.05rem; font-weight:700; color:white;">{name}</span>
                    &nbsp;<span class="priority-badge {badge_cls}">{priority}</span>
                </div>
                <div style="font-size:0.78rem; color:#8FA3BF;">{description}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.info("👉 Navigate to **🎯 Demo Mode** in the sidebar to run the live demonstration pipeline")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Initialize system
    with st.spinner("⚡ Initializing Phantom Signal..."):
        initialize_system()

    render_sidebar()
    render_home()


if __name__ == "__main__" or True:
    main()
