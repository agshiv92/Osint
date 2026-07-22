"""
Phantom Signal — Demo Mode Streamlit Page
Showpiece for competition presentation.
"""
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from config import PRIORITY_COLORS
from data.database import (
    get_alert_by_id, get_fraud_signal_by_id, get_assessment_by_signal,
    get_simulation_by_signal, get_intervention_rules,
)
from pipeline.ingestion import ingest_text
from pipeline.normalization import normalize_raw_signal
from pipeline.filtration import run_filtration
from pipeline.simulation import run_simulation
from pipeline.alert_generator import generate_alert_document
from utils.pdf_generator import read_pdf_bytes

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Phantom Signal - Live Demo", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@keyframes gradient-x {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}
.hero-demo {
    background: linear-gradient(270deg, #0D1B3E, #028090, #060D1F);
    background-size: 600% 600%;
    animation: gradient-x 15s ease infinite;
    border-radius: 20px;
    padding: 60px 40px;
    text-align: center;
    border: 1px solid #1E3A5F;
    box-shadow: 0 10px 50px rgba(2, 128, 144, 0.4);
    margin-bottom: 30px;
}
.demo-title {
    font-size: 3.5rem;
    font-weight: 900;
    color: white;
    letter-spacing: -1px;
    margin-bottom: 10px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
.demo-subtitle {
    font-size: 1.2rem;
    color: rgba(255,255,255,0.8);
    max-width: 700px;
    margin: 0 auto;
}
.scenario-card {
    background: #0D1B3E;
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    height: 100%;
}
.scenario-card:hover {
    transform: translateY(-5px);
    border-color: #03A4B8;
    box-shadow: 0 8px 24px rgba(2, 128, 144, 0.2);
}
.scenario-icon {
    font-size: 3rem;
    margin-bottom: 15px;
}
.scenario-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: white;
    margin-bottom: 8px;
}
.scenario-desc {
    font-size: 0.9rem;
    color: #8FA3BF;
}
.pipeline-box {
    background: #112244;
    border: 1px solid #1E3A5F;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    flex: 1;
}
.pipeline-arrow {
    color: #03A4B8;
    font-size: 1.5rem;
    align-self: center;
    padding: 0 10px;
}
.pipeline-container {
    display: flex;
    justify-content: space-between;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# CSS mapping for document rendering
PRIORITY_CSS = {
    "CRITICAL": {"bg": "rgba(220,38,38,0.2)", "color": "#F87171", "border": "#DC2626"},
    "HIGH":     {"bg": "rgba(234,88,12,0.2)", "color": "#FB923C", "border": "#EA580C"},
    "MEDIUM":   {"bg": "rgba(217,119,6,0.2)", "color": "#FCD34D", "border": "#D97706"},
    "LOW":      {"bg": "rgba(22,163,74,0.2)", "color": "#4ADE80", "border": "#16A34A"},
}


def render_alert_document(alert_id: str):
    """Renders the generated risk alert document."""
    alert = get_alert_by_id(alert_id)
    if not alert:
        st.error(f"Alert {alert_id} not found.")
        return

    fraud_signal = get_fraud_signal_by_id(alert["fraud_signal_id"])
    assessment = get_assessment_by_signal(alert["fraud_signal_id"])
    simulation = get_simulation_by_signal(alert["fraud_signal_id"])
    rules = get_intervention_rules(alert["fraud_signal_id"])

    doc = alert.get("document", {})
    priority = alert.get("priority", "HIGH")
    p_style = PRIORITY_CSS.get(priority, PRIORITY_CSS["HIGH"])

    st.markdown("---")
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0D1B3E 0%, #112244 100%); border-left: 5px solid {p_style['border']}; padding: 20px; border-radius: 8px; margin-bottom: 24px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size: 0.8rem; color: #8FA3BF; text-transform: uppercase;">Generated Alert ID: {alert_id[:8]}</span>
                <h2 style="margin: 5px 0; color: white;">{alert.get('fraud_typology', 'Unknown Threat')}</h2>
            </div>
            <div style="background: {p_style['bg']}; border: 1px solid {p_style['border']}; color: {p_style['color']}; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                {priority} PRIORITY
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.tabs(["📝 Executive Summary", "💰 Financial Impact", "⚖️ Gate Results", "🛡️ Intervention Rules", "🎯 Actions"])

    with t1:
        st.markdown(f"""
        <div style="background: #112244; padding: 20px; border-radius: 8px; border-left: 3px solid #03A4B8;">
            <p style="font-size: 1.1rem; line-height: 1.6; color: #E8EDF5;">{doc.get('executive_summary', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        st.subheader("Threat Description")
        st.write(doc.get('threat_description', ''))
        st.subheader("UOB Relevance")
        st.write(doc.get('uob_relevance', ''))

    with t2:
        st.write(doc.get('financial_exposure', ''))
        if simulation:
            fi = simulation.get('financial_impact', {})
            st.metric("Baseline Exposure", f"SGD {fi.get('baseline_exposure_sgd', 0):,.0f}")
            st.metric("With Proposed Interventions", f"SGD {fi.get('with_proposed_controls_sgd', 0):,.0f}")
            st.info(simulation.get('scenario_name', ''))

    with t3:
        if assessment:
            for gate_name, gate_key in [("Gate 1: Novelty", "gate1_novelty"), ("Gate 2: Customer Exposure", "gate2_customer_exposure"), ("Gate 3: Control Gap", "gate3_control_gap")]:
                g = assessment.get(gate_key, {})
                color = "green" if g.get('passed') else "red"
                icon = "✅" if g.get('passed') else "❌"
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 15px; margin-bottom: 10px; background: #0D1B3E; border-radius: 5px;">
                    <h4>{icon} {gate_name} (Score: {g.get('score', 0)})</h4>
                    <p>{g.get('explanation', '')}</p>
                </div>
                """, unsafe_allow_html=True)

    with t4:
        for r in rules:
            st.markdown(f"""
            <div style="background: #112244; border-left: 3px solid #03A4B8; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                <strong>{r.get('rule_type')}</strong> - Risk: {r.get('deployment_risk')} - Impact: ~{r.get('expected_impact_pct', 0)}%
                <p>{r.get('rule_description', '')}</p>
                <code>{r.get('rule_logic', '')}</code>
            </div>
            """, unsafe_allow_html=True)

    with t5:
        recs = doc.get('recommended_actions', {})
        for k, v in recs.items():
            st.markdown(f"**{k.replace('_', ' ').title()}**")
            for item in v:
                st.markdown(f"- {item}")


def run_pipeline(text: str):
    """Executes the Phantom Signal pipeline live."""
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Stage 1: Ingestion
        status_text.markdown("### 🔍 STAGE 1: Ingesting Signal...")
        progress_bar.progress(20)
        raw_signal = ingest_text(text, source_name="DEMO_INPUT")
        if not raw_signal:
            st.error("Failed to ingest text. Please provide valid text.")
            return
        time.sleep(1)

        # Stage 2: Normalization
        status_text.markdown("### 🤖 STAGE 2: Normalizing with Gemini AI...")
        progress_bar.progress(40)
        fraud_signal = normalize_raw_signal(raw_signal)
        if not fraud_signal:
            st.error("Normalization failed.")
            return
        time.sleep(1)

        # Stage 3: Filtration
        status_text.markdown("### ⚖️ STAGE 3: Running 3-Gate Filtration...")
        progress_bar.progress(60)
        assessment = run_filtration(fraud_signal)
        if not assessment:
            st.error("Filtration failed.")
            return
        time.sleep(1)

        # Stage 4: Simulation
        status_text.markdown("### 📊 STAGE 4: Running Impact Simulation...")
        progress_bar.progress(80)
        simulation = None
        if assessment.get("overall_passed"):
            simulation = run_simulation(fraud_signal, assessment, "Live Demo Scenario")
        time.sleep(1)

        # Stage 5: Alert Generation
        status_text.markdown("### 📄 STAGE 5: Generating Risk Alert Document...")
        progress_bar.progress(100)
        alert = None
        if assessment.get("overall_passed"):
            alert = generate_alert_document(fraud_signal, assessment, simulation)
            status_text.success("✅ Pipeline Complete: Alert Generated!")
            render_alert_document(alert["alert_id"])
        else:
            status_text.warning("⚠️ Pipeline Complete: Signal filtered out by relevance gates. No alert generated.")
            st.json(assessment)

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        logger.exception("Pipeline error")


def run_guided_journey():
    """Executes a highly visual, step-by-step guided journey for the Android Malware scam."""
    st.markdown("---")
    st.markdown("## 🕵️‍♂️ The Phantom Signal Journey: End-to-End")
    st.markdown("Follow the exact lifecycle of how unstructured OSInt chatter is transformed into a quantified Risk Alert Document.")
    
    # STEP 1: Collection
    st.markdown("### 📡 STAGE 1: OSInt Data Collection (The Source)")
    st.info("Our scrapers monitor dark web forums, Telegram groups, and open-source intelligence feeds 24/7. Here is raw intercepted chatter from a known cybercrime Telegram channel targeting Singapore.")
    
    raw_telegram_text = (
        "🔥 [NEW RELEASE] SG Banking Bypass Kit V2.4 🔥\n\n"
        "Looking for serious buyers. We just updated our Android payload (disguised as 'SG Seafood Deals' APK).\n"
        "It fully abuses Android Accessibility Services to silently intercept SMS OTPs and execute unauthorized FAST wire transfers in the background while the screen is black.\n"
        "Works on major SG banks (UOB, POSB, OCBC).\n"
        "Price: $5,000 USD / month. DM for escrow."
    )
    
    st.markdown(f"""
    <div style="background-color: #1E293B; border-radius: 12px; padding: 20px; border-left: 5px solid #38BDF8; font-family: monospace; color: #E2E8F0; margin-bottom: 30px;">
        <span style="color: #38BDF8; font-weight: bold;">@SG_ExploitBroker [22:14 PM]:</span><br><br>
        {raw_telegram_text.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)
    time.sleep(2.5)
    
    # STEP 2: Normalization
    st.markdown("### 🤖 STAGE 2: AI Intelligence Generation (Normalization)")
    st.info("The raw text is unstructured and unusable for traditional rules engines. Our Gemini-powered agent normalizes this into a structured threat profile.")
    
    with st.spinner("Gemini is analyzing the raw chatter..."):
        from pipeline.ingestion import ingest_text
        from pipeline.normalization import normalize_raw_signal
        raw_sig = ingest_text(raw_telegram_text, source_name="TELEGRAM_DARKWEB")
        fraud_signal = normalize_raw_signal(raw_sig)
    
    if not fraud_signal:
        st.error("Failed to generate intelligence.")
        return
        
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ Extracted Intelligence Profile")
        st.json({
            "Typology": fraud_signal.get("fraud_typology"),
            "Attack Vector": fraud_signal.get("attack_vector"),
            "Victim Profile": fraud_signal.get("victim_profile"),
            "Severity": fraud_signal.get("severity_estimate"),
        })
    with col2:
        st.markdown(f"""
        <div style="background-color: #0F172A; padding: 20px; border-radius: 8px; border: 1px solid #1E293B; height: 100%;">
            <h4 style="color: #10B981; margin-top: 0;">How it works:</h4>
            <p style="font-size: 0.95rem; color: #94A3B8; line-height: 1.6;">The AI instantly recognized that this isn't just spam; it's a <strong>Malware-as-a-Service (MaaS)</strong> threat targeting retail banking customers via <strong>Android Accessibility exploits</strong> and SMS OTP interception.</p>
        </div>
        """, unsafe_allow_html=True)
    
    time.sleep(2.5)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # STEP 3: Relevance Assessment
    st.markdown("### ⚖️ STAGE 3: Relevance Assessment (3-Gate Engine)")
    st.info("Not all threats matter to our bank. Phantom Signal scores this specific intelligence against UOB's internal risk profile using a rigorous 3-Gate assessment.")
    
    with st.spinner("Evaluating relevance against bank profile..."):
        from pipeline.filtration import run_filtration
        assessment = run_filtration(fraud_signal)
    
    if not assessment:
        st.error("Filtration failed.")
        return
        
    g1 = assessment.get("gate1_novelty", {})
    g2 = assessment.get("gate2_customer_exposure", {})
    g3 = assessment.get("gate3_control_gap", {})
    
    g1_color = "#10B981" if g1.get("passed") else "#EF4444"
    g2_color = "#10B981" if g2.get("passed") else "#EF4444"
    g3_color = "#10B981" if g3.get("passed") else "#EF4444"
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div style="border-top: 4px solid {g1_color}; background: #1E293B; padding: 15px; border-radius: 5px; height: 100%;">
            <h4 style="margin-top:0;">Gate 1: Novelty</h4>
            <h2 style="color:{g1_color}; margin:0;">{g1.get('score', 0):.0f}/100</h2>
            <p style="font-size:0.8rem; color:#94A3B8; margin-top:10px;">{g1.get('explanation')}</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="border-top: 4px solid {g2_color}; background: #1E293B; padding: 15px; border-radius: 5px; height: 100%;">
            <h4 style="margin-top:0;">Gate 2: Exposure</h4>
            <h2 style="color:{g2_color}; margin:0;">{g2.get('score', 0):.0f}/100</h2>
            <p style="font-size:0.8rem; color:#94A3B8; margin-top:10px;">{g2.get('explanation')}</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="border-top: 4px solid {g3_color}; background: #1E293B; padding: 15px; border-radius: 5px; height: 100%;">
            <h4 style="margin-top:0;">Gate 3: Control Gap</h4>
            <h2 style="color:{g3_color}; margin:0;">{g3.get('score', 0):.0f}/100</h2>
            <p style="font-size:0.8rem; color:#94A3B8; margin-top:10px;">{g3.get('explanation')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"<p style='text-align:center; color:#FCD34D; font-weight:bold; font-size:1.2rem; margin-top:15px;'>Overall Priority: {assessment.get('alert_priority', 'HIGH')}</p>", unsafe_allow_html=True)
    time.sleep(2.5)
    st.markdown("<br>", unsafe_allow_html=True)

    # STEP 4: Simulation
    st.markdown("### 📊 STAGE 4: Customer & Financial Impact Simulation")
    st.info("Because the signal passed the relevance gates, we now run a Monte Carlo simulation to quantify the expected financial damage to our customer base if no action is taken.")
    
    with st.spinner("Running 10,000 Monte Carlo simulation paths..."):
        from pipeline.simulation import run_simulation
        simulation = run_simulation(fraud_signal, assessment, "Live Demo Scenario")
    
    fi = simulation.get("financial_impact", {})
    st.markdown(f"""
    <div style="display:flex; justify-content:space-around; background: #0F172A; padding: 25px; border-radius: 12px; border: 1px solid #1E293B; margin-bottom: 30px;">
        <div style="text-align:center;">
            <p style="color:#94A3B8; margin:0; text-transform:uppercase; font-size:0.8rem;">Baseline Exposure (No Action)</p>
            <h2 style="color:#EF4444; margin:5px 0 0 0;">SGD {fi.get('baseline_exposure_sgd', 0):,.0f}</h2>
        </div>
        <div style="text-align:center;">
            <p style="color:#94A3B8; margin:0; text-transform:uppercase; font-size:0.8rem;">With Proposed Interventions</p>
            <h2 style="color:#10B981; margin:5px 0 0 0;">SGD {fi.get('with_proposed_controls_sgd', 0):,.0f}</h2>
        </div>
        <div style="text-align:center;">
            <p style="color:#94A3B8; margin:0; text-transform:uppercase; font-size:0.8rem;">Expected Savings</p>
            <h2 style="color:#38BDF8; margin:5px 0 0 0;">SGD {(fi.get('baseline_exposure_sgd', 0) - fi.get('with_proposed_controls_sgd', 0)):,.0f}</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(2.5)
    
    # STEP 5: Alert Generation
    st.markdown("### 📄 STAGE 5: The Final Intelligence Output")
    st.info("Finally, the system synthesizes all the intelligence, relevance scoring, and simulations into a professional, executive-ready Risk Alert Document with recommended transaction monitoring rules.")
    
    with st.spinner("Drafting executive alert document..."):
        from pipeline.alert_generator import generate_alert_document
        alert = generate_alert_document(fraud_signal, assessment, simulation)
    
    st.success("✅ End-to-End Journey Complete! Review the final output below.")
    render_alert_document(alert["alert_id"])


# ── UI ────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-demo">
    <div class="demo-title">PHANTOM SIGNAL LIVE DEMO</div>
    <div class="demo-subtitle">Instantly transform raw OSInt threat data into structured, quantified Risk Alert Documents via 3-gate filtration and Monte Carlo simulation.</div>
</div>
""", unsafe_allow_html=True)

if 'selected_alert' not in st.session_state:
    st.session_state.selected_alert = None
if 'run_guided' not in st.session_state:
    st.session_state.run_guided = False

st.markdown("<br>", unsafe_allow_html=True)
col_guided1, col_guided2, col_guided3 = st.columns([1, 2, 1])
with col_guided2:
    if st.button("🕵️‍♂️ START GUIDED END-TO-END SCAM JOURNEY", use_container_width=True, type="primary"):
        st.session_state.run_guided = True
        st.session_state.selected_alert = None

if st.session_state.run_guided:
    run_guided_journey()
    st.stop()

st.markdown("---")
st.markdown("### 🎬 Pre-loaded Scenarios")
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📱 SMS Spoofing (CRITICAL)", use_container_width=True, key="btn1"):
        st.session_state.selected_alert = "alert-sms-spoofing-001"
with c2:
    if st.button("💔 Sextortion Surge (HIGH)", use_container_width=True, key="btn2"):
        st.session_state.selected_alert = "alert-sextortion-001"
with c3:
    if st.button("🎭 Deepfake CFO Fraud (HIGH)", use_container_width=True, key="btn3"):
        st.session_state.selected_alert = "alert-deepfake-cfo-001"

if st.session_state.selected_alert:
    render_alert_document(st.session_state.selected_alert)


st.markdown("---")
st.markdown("### ⚡ Live Pipeline Analysis")
st.write("Paste a raw intelligence bulletin, news article, or threat advisory below to run it through the live Phantom Signal pipeline.")

input_text = st.text_area("Raw Intelligence Input", height=200, placeholder="Paste text here...")
if st.button("Run Phantom Signal Analysis", type="primary"):
    st.session_state.selected_alert = None # Clear pre-loaded
    run_pipeline(input_text)


st.markdown("---")
st.markdown("### 🏗️ Pipeline Architecture")
st.markdown("""
<div class="pipeline-container">
    <div class="pipeline-box"><strong>🔍 1. Ingest</strong><br><small>OSInt Crawlers</small></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-box"><strong>🤖 2. Normalize</strong><br><small>Gemini Extractor</small></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-box"><strong>⚖️ 3. Filter</strong><br><small>3-Gate Relevance</small></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-box"><strong>📊 4. Simulate</strong><br><small>Monte Carlo Impact</small></div>
    <div class="pipeline-arrow">→</div>
    <div class="pipeline-box"><strong>📄 5. Alert</strong><br><small>Gemini PDF Gen</small></div>
</div>
""", unsafe_allow_html=True)
