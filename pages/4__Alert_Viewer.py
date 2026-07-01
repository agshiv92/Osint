"""
Phantom Signal — Page 4: Alert Viewer
Risk Alert Document viewer with full styled sections and PDF download.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from config import (
    PRIORITY_COLORS, COLOR_BG, COLOR_NAVY, COLOR_TEAL, COLOR_SURFACE2,
    COLOR_BORDER, COLOR_TEXT, COLOR_MUTED, TYPOLOGY_LABELS,
)
from data.database import (
    get_risk_alerts, get_alert_by_id,
    get_simulation_by_signal, get_fraud_signal_by_id,
    get_intervention_rules,
)
from utils.pdf_generator import read_pdf_bytes

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alert Viewer · Phantom Signal",
    page_icon="🚨",
    layout="wide",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {COLOR_BG} !important;
      color: {COLOR_TEXT} !important;
      font-family: 'Inter', sans-serif;
  }}
  [data-testid="stSidebar"] {{
      background-color: {COLOR_NAVY} !important;
      border-right: 1px solid {COLOR_BORDER};
  }}
  [data-testid="stSidebar"] * {{ color: {COLOR_TEXT} !important; }}

  section.main > div {{ padding-top: 1rem; }}
  #MainMenu, footer, header {{ visibility: hidden; }}

  /* ── Topbar ── */
  .ps-topbar {{
      background: linear-gradient(135deg, {COLOR_NAVY} 0%, #091530 100%);
      border-bottom: 1px solid {COLOR_TEAL};
      padding: 0.9rem 1.6rem;
      margin-bottom: 1.6rem;
      border-radius: 12px;
      display: flex;
      align-items: center;
      gap: 1rem;
  }}
  .ps-topbar-title {{
      font-size: 1.45rem;
      font-weight: 700;
      color: {COLOR_TEXT};
      letter-spacing: 0.5px;
  }}
  .ps-topbar-sub {{
      font-size: 0.8rem;
      color: {COLOR_TEAL};
      letter-spacing: 1px;
      text-transform: uppercase;
  }}

  /* ── Metric chips ── */
  .metric-row {{
      display: flex;
      gap: 1rem;
      margin-bottom: 1.4rem;
      flex-wrap: wrap;
  }}
  .metric-chip {{
      background: {COLOR_NAVY};
      border: 1px solid {COLOR_BORDER};
      border-radius: 10px;
      padding: 0.75rem 1.25rem;
      min-width: 130px;
      flex: 1;
  }}
  .metric-chip .chip-val {{
      font-size: 1.8rem;
      font-weight: 700;
      color: {COLOR_TEXT};
      line-height: 1;
  }}
  .metric-chip .chip-lbl {{
      font-size: 0.72rem;
      color: {COLOR_MUTED};
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-top: 0.3rem;
  }}

  /* ── Alert list table ── */
  .alert-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.83rem;
  }}
  .alert-table th {{
      background: {COLOR_SURFACE2};
      color: {COLOR_TEAL};
      text-transform: uppercase;
      font-size: 0.7rem;
      letter-spacing: 0.8px;
      padding: 0.6rem 0.85rem;
      border-bottom: 1px solid {COLOR_BORDER};
      text-align: left;
  }}
  .alert-table td {{
      padding: 0.55rem 0.85rem;
      border-bottom: 1px solid rgba(30,58,95,0.5);
      color: {COLOR_TEXT};
      vertical-align: middle;
  }}
  .alert-table tr:last-child td {{ border-bottom: none; }}
  .alert-table tr.selected-row td {{ background: rgba(2,128,144,0.12); }}
  .alert-table tr:hover td {{ background: rgba(2,128,144,0.06); cursor: pointer; }}

  /* ── Priority badge ── */
  .priority-badge {{
      display: inline-block;
      padding: 0.22rem 0.7rem;
      border-radius: 20px;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
  }}

  /* ── Alert document card ── */
  .doc-card {{
      background: {COLOR_NAVY};
      border: 1px solid {COLOR_BORDER};
      border-radius: 14px;
      padding: 1.5rem 1.6rem;
      margin-bottom: 1.2rem;
  }}
  .doc-section-header {{
      font-size: 0.78rem;
      font-weight: 700;
      color: {COLOR_TEAL};
      text-transform: uppercase;
      letter-spacing: 1px;
      padding-bottom: 0.5rem;
      border-bottom: 1px solid {COLOR_TEAL}44;
      margin-bottom: 0.9rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
  }}

  /* ── Executive Summary box ── */
  .exec-summary-box {{
      background: {COLOR_SURFACE2};
      border: 1px solid {COLOR_BORDER};
      border-left: 3px solid {COLOR_TEAL};
      border-radius: 8px;
      padding: 1rem 1.2rem;
      font-size: 0.88rem;
      line-height: 1.65;
      color: {COLOR_TEXT};
  }}

  /* ── Financial impact table ── */
  .fi-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
  }}
  .fi-table th {{
      background: rgba(2,128,144,0.15);
      color: {COLOR_TEAL};
      padding: 0.5rem 0.8rem;
      text-align: left;
      font-size: 0.72rem;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      border-bottom: 1px solid {COLOR_BORDER};
  }}
  .fi-table td {{
      padding: 0.5rem 0.8rem;
      border-bottom: 1px solid rgba(30,58,95,0.4);
      color: {COLOR_TEXT};
  }}
  .fi-table tr:last-child td {{ border-bottom: none; }}
  .fi-num {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}
  .fi-num.red {{ color: #F87171; }}
  .fi-num.amber {{ color: #FCD34D; }}
  .fi-num.green {{ color: #4ADE80; }}

  /* ── Gate results columns ── */
  .gate-col {{
      border-radius: 10px;
      padding: 0.85rem 1rem;
      text-align: center;
  }}
  .gate-col.pass {{
      background: rgba(22,163,74,0.12);
      border: 1.5px solid #16A34A;
  }}
  .gate-col.fail {{
      background: rgba(220,38,38,0.12);
      border: 1.5px solid #DC2626;
  }}

  /* ── Action sections ── */
  .action-section {{
      border-radius: 8px;
      padding: 0.85rem 1rem;
      margin-bottom: 0.75rem;
  }}
  .action-section.immediate {{ background: rgba(220,38,38,0.08); border-left: 3px solid #DC2626; }}
  .action-section.short    {{ background: rgba(234,88,12,0.08); border-left: 3px solid #EA580C; }}
  .action-section.strategic{{ background: rgba(2,128,144,0.08); border-left: 3px solid {COLOR_TEAL}; }}
  .action-section h4 {{
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin: 0 0 0.5rem 0;
  }}
  .action-section.immediate h4 {{ color: #F87171; }}
  .action-section.short h4    {{ color: #FB923C; }}
  .action-section.strategic h4{{ color: {COLOR_TEAL}; }}
  .action-item {{
      font-size: 0.84rem;
      color: {COLOR_TEXT};
      padding: 0.18rem 0;
      line-height: 1.5;
  }}

  /* ── Intervention rule card ── */
  .rule-card {{
      background: {COLOR_SURFACE2};
      border: 1px solid {COLOR_BORDER};
      border-radius: 10px;
      padding: 1rem 1.1rem;
      margin-bottom: 0.9rem;
      transition: border-color 0.2s;
  }}
  .rule-card:hover {{ border-color: {COLOR_TEAL}; }}
  .rule-type-badge {{
      display: inline-block;
      padding: 0.18rem 0.6rem;
      border-radius: 4px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
  }}
  .rule-logic-box {{
      background: #060D1F;
      border: 1px solid {COLOR_BORDER};
      border-radius: 6px;
      padding: 0.6rem 0.8rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: #93C5FD;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0.5rem 0;
  }}
  .rule-meta {{
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      margin-top: 0.4rem;
  }}
  .rule-meta-item {{
      font-size: 0.73rem;
      color: {COLOR_MUTED};
  }}
  .rule-meta-item span {{
      color: {COLOR_TEXT};
      font-weight: 600;
  }}

  /* ── Analyst notes (amber) ── */
  .analyst-notes-box {{
      background: rgba(217,119,6,0.1);
      border: 1px solid rgba(217,119,6,0.35);
      border-left: 3px solid #D97706;
      border-radius: 8px;
      padding: 0.9rem 1.1rem;
      font-size: 0.85rem;
      line-height: 1.6;
      color: #FDE68A;
  }}

  /* ── Divider ── */
  .section-divider {{
      border: none;
      border-top: 1px solid {COLOR_BORDER};
      margin: 1.2rem 0;
  }}

  /* ── Routing team tag ── */
  .routing-tag {{
      display: inline-block;
      background: rgba(2,128,144,0.15);
      color: {COLOR_TEAL};
      border: 1px solid rgba(2,128,144,0.3);
      border-radius: 4px;
      padding: 0.15rem 0.55rem;
      font-size: 0.73rem;
      font-weight: 600;
      margin: 0.1rem 0.2rem 0.1rem 0;
  }}

  /* ── Document title bar ── */
  .doc-title-bar {{
      background: linear-gradient(135deg, {COLOR_SURFACE2} 0%, #0D1B3E 100%);
      border: 1px solid {COLOR_BORDER};
      border-radius: 12px;
      padding: 1.2rem 1.5rem;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.8rem;
  }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def priority_badge_html(priority: str) -> str:
    color = PRIORITY_COLORS.get(priority, "#6B7280")
    bg = color + "22"
    return (
        f'<span class="priority-badge" '
        f'style="background:{bg};color:{color};border:1px solid {color};">'
        f'{priority}</span>'
    )


def fmt_sgd(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if v >= 1_000_000:
        return f"SGD {v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"SGD {v/1_000:.0f}K"
    return f"SGD {v:,.0f}"


RULE_TYPE_COLORS = {
    "TM_DETECTION":      "#3B82F6",
    "CUSTOMER_FRICTION": "#A855F7",
    "POLICY_CHANGE":     "#F97316",
    "ADVISORY":          "#16A34A",
}


def rule_badge_html(rule_type: str) -> str:
    color = RULE_TYPE_COLORS.get(rule_type, COLOR_TEAL)
    bg = color + "22"
    label = rule_type.replace("_", " ")
    return (
        f'<span class="rule-type-badge" '
        f'style="background:{bg};color:{color};border:1px solid {color}44;">'
        f'{label}</span>'
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ps-topbar">
  <span style="font-size:1.8rem;">🚨</span>
  <div>
    <div class="ps-topbar-title">Alert Viewer</div>
    <div class="ps-topbar-sub">Risk Alert Document Centre · Phantom Signal</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Load alerts ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_alerts():
    return get_risk_alerts(limit=100)

alerts = load_alerts()

if not alerts:
    st.warning("⚠️ No risk alerts found. Run the pipeline first to generate alerts.")
    st.stop()

# ── Metrics ───────────────────────────────────────────────────────────────────
total_alerts = len(alerts)
critical_count = sum(1 for a in alerts if a.get("priority") == "CRITICAL")
high_count     = sum(1 for a in alerts if a.get("priority") == "HIGH")
has_pdf_count  = sum(1 for a in alerts if a.get("pdf_path"))

st.markdown(f"""
<div class="metric-row">
  <div class="metric-chip">
    <div class="chip-val">{total_alerts}</div>
    <div class="chip-lbl">Total Alerts</div>
  </div>
  <div class="metric-chip" style="border-color:#DC262655;">
    <div class="chip-val" style="color:#F87171;">{critical_count}</div>
    <div class="chip-lbl">Critical</div>
  </div>
  <div class="metric-chip" style="border-color:#EA580C55;">
    <div class="chip-val" style="color:#FB923C;">{high_count}</div>
    <div class="chip-lbl">High</div>
  </div>
  <div class="metric-chip" style="border-color:{COLOR_TEAL}55;">
    <div class="chip-val" style="color:{COLOR_TEAL};">{has_pdf_count}</div>
    <div class="chip-lbl">PDFs Available</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Alert List Table ──────────────────────────────────────────────────────────
st.markdown(f'<h3 style="color:{COLOR_TEXT};font-size:1.05rem;font-weight:700;margin-bottom:0.8rem;">📋 Alert Registry</h3>', unsafe_allow_html=True)

# Filter controls
col_pf, col_sf, col_search = st.columns([2, 2, 3])
with col_pf:
    pf_opts = ["All Priorities"] + ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    priority_sel = st.selectbox("Priority", pf_opts, label_visibility="collapsed", key="av_priority")
with col_sf:
    sort_sel = st.selectbox("Sort by", ["Newest First", "Oldest First", "Priority (High→Low)"],
                            label_visibility="collapsed", key="av_sort")
with col_search:
    search_text = st.text_input("Search by typology or ID", placeholder="🔍  Search alerts…",
                                label_visibility="collapsed", key="av_search")

# Filter & sort
def filter_alert(a: dict) -> bool:
    if priority_sel != "All Priorities" and a.get("priority") != priority_sel:
        return False
    if search_text:
        haystack = (
            a.get("alert_id", "").lower() +
            str(a.get("document", {}).get("fraud_typology", "")).lower() +
            a.get("fraud_signal_id", "").lower()
        )
        if search_text.lower() not in haystack:
            return False
    return True

filtered_alerts = [a for a in alerts if filter_alert(a)]

if sort_sel == "Oldest First":
    filtered_alerts = sorted(filtered_alerts, key=lambda x: x.get("generated_at", ""))
elif sort_sel == "Priority (High→Low)":
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    filtered_alerts = sorted(filtered_alerts, key=lambda x: order.get(x.get("priority", "LOW"), 9))

# Build table HTML
rows_html = ""
alert_ids_list = [a["alert_id"] for a in filtered_alerts]
for i, a in enumerate(filtered_alerts):
    aid       = a.get("alert_id", "")
    aid_short = aid[:8].upper()
    priority  = a.get("priority", "LOW")
    gen_at    = a.get("generated_at", "")[:16].replace("T", " ")
    routing   = a.get("routing", {})
    teams     = [k.replace("_", " ").title() for k, v in routing.items() if v]
    teams_str = " · ".join(teams[:3]) if teams else "—"

    # Typology from document or fraud_signal
    doc = a.get("document", {})
    typology_raw = doc.get("fraud_typology", "")
    if not typology_raw:
        fs_tmp = get_fraud_signal_by_id(a.get("fraud_signal_id", ""))
        typology_raw = fs_tmp.get("fraud_typology", "UNKNOWN") if fs_tmp else "UNKNOWN"
    typology_label = TYPOLOGY_LABELS.get(typology_raw, typology_raw)

    p_html = priority_badge_html(priority)
    rows_html += f"""
    <tr>
      <td style="font-family:monospace;font-size:0.78rem;color:{COLOR_MUTED};">#{aid_short}</td>
      <td><span style="color:{COLOR_TEAL};font-weight:600;">{typology_label}</span></td>
      <td>{p_html}</td>
      <td style="color:{COLOR_MUTED};font-size:0.78rem;">{gen_at}</td>
      <td style="font-size:0.78rem;color:{COLOR_TEXT};">{teams_str}</td>
    </tr>"""

st.markdown(f"""
<div style="overflow-x:auto;margin-bottom:1rem;">
<table class="alert-table">
  <thead>
    <tr>
      <th>Alert ID</th>
      <th>Fraud Typology</th>
      <th>Priority</th>
      <th>Generated At</th>
      <th>Routing Teams</th>
    </tr>
  </thead>
  <tbody>{rows_html}</tbody>
</table>
</div>
<p style="color:{COLOR_MUTED};font-size:0.78rem;">Showing {len(filtered_alerts)} of {total_alerts} alerts.</p>
""", unsafe_allow_html=True)

# ── Alert selector ────────────────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(f'<h3 style="color:{COLOR_TEXT};font-size:1.05rem;font-weight:700;margin-bottom:0.8rem;">🔍 Alert Document Viewer</h3>', unsafe_allow_html=True)

if not filtered_alerts:
    st.info("No alerts match the current filters.")
    st.stop()

select_options = {
    f"#{a['alert_id'][:8].upper()} · {TYPOLOGY_LABELS.get(a.get('document', {}).get('fraud_typology', ''), 'Unknown')} · {a.get('priority','LOW')}": a["alert_id"]
    for a in filtered_alerts
}

selected_label = st.selectbox(
    "Select an alert to view",
    options=list(select_options.keys()),
    key="alert_selector",
)
selected_alert_id = select_options[selected_label]

# ── Load full alert ───────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_full_alert(aid: str):
    return get_alert_by_id(aid)

@st.cache_data(ttl=60)
def load_simulation(fsid: str):
    return get_simulation_by_signal(fsid)

@st.cache_data(ttl=60)
def load_fraud_signal(fsid: str):
    return get_fraud_signal_by_id(fsid)

@st.cache_data(ttl=60)
def load_rules(fsid: str):
    return get_intervention_rules(fsid)

alert      = load_full_alert(selected_alert_id)
if not alert:
    st.error("Could not load alert. Please try again.")
    st.stop()

fsid       = alert.get("fraud_signal_id", "")
doc        = alert.get("document", {})
routing    = alert.get("routing", {})
priority   = alert.get("priority", "LOW")
pri_color  = PRIORITY_COLORS.get(priority, COLOR_TEAL)
gen_at     = alert.get("generated_at", "")[:19].replace("T", " ")
aid_short  = selected_alert_id[:8].upper()

sim        = load_simulation(fsid)
fraud_sig  = load_fraud_signal(fsid)
rules_db   = load_rules(fsid)

typology_raw   = doc.get("fraud_typology") or (fraud_sig.get("fraud_typology", "UNKNOWN") if fraud_sig else "UNKNOWN")
typology_label = TYPOLOGY_LABELS.get(typology_raw, typology_raw)

# Routing teams HTML
teams      = [k.replace("_", " ").title() for k, v in routing.items() if v]
teams_html = "".join(f'<span class="routing-tag">🏢 {t}</span>' for t in teams) if teams else "—"

# ── Document Title Bar ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="doc-title-bar">
  <div>
    <div style="font-size:1.15rem;font-weight:700;color:{COLOR_TEXT};margin-bottom:0.3rem;">
      🚨 Risk Alert &nbsp;
      <span style="font-family:monospace;font-size:0.85rem;color:{COLOR_MUTED};">#{aid_short}</span>
    </div>
    <div style="font-size:0.85rem;color:{COLOR_TEAL};font-weight:600;margin-bottom:0.4rem;">
      {typology_label}
    </div>
    <div style="font-size:0.78rem;color:{COLOR_MUTED};">
      🕐 Generated: {gen_at} UTC &nbsp;|&nbsp; {teams_html}
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:0.8rem;">
    {priority_badge_html(priority)}
    <div style="font-size:0.72rem;color:{COLOR_MUTED};text-align:right;">
      RESTRICTED<br>UOB Group Compliance
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── PDF Download ──────────────────────────────────────────────────────────────
pdf_path = alert.get("pdf_path", "")
col_dl, col_spacer = st.columns([2, 5])
with col_dl:
    pdf_bytes = read_pdf_bytes(pdf_path) if pdf_path else None
    if not pdf_bytes:
        with st.spinner("Regenerating PDF for Cloud Run instance..."):
            from data.database import get_assessment_by_signal
            from utils.pdf_generator import generate_pdf
            assmt = get_assessment_by_signal(fsid) or {}
            new_pdf_path = generate_pdf(alert, fraud_sig or {}, assmt, sim)
            if new_pdf_path:
                pdf_bytes = read_pdf_bytes(new_pdf_path)

    if pdf_bytes:
        st.download_button(
            label="📄 Download PDF Alert",
            data=pdf_bytes,
            file_name=f"alert_{aid_short}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.warning("⚠️ Could not generate PDF alert document.")

st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_exec, tab_financial, tab_gates, tab_actions, tab_rules, tab_notes = st.tabs([
    "📝 Executive Summary",
    "💰 Financial Impact",
    "⚖️ Gate Results",
    "🎯 Recommended Actions",
    "🛡️ Intervention Rules",
    "🔖 Analyst Notes",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab_exec:
    exec_sum = doc.get("executive_summary", "")
    threat_desc = doc.get("threat_description", doc.get("uob_relevance", ""))

    st.markdown(f"""
    <div class="doc-card">
      <div class="doc-section-header">📝 Executive Summary</div>
      <div class="exec-summary-box">{exec_sum if exec_sum else "<i>No executive summary available.</i>"}</div>
    </div>
    """, unsafe_allow_html=True)

    if threat_desc:
        st.markdown(f"""
        <div class="doc-card" style="margin-top:0.6rem;">
          <div class="doc-section-header">🌐 Threat Intelligence Brief</div>
          <div class="exec-summary-box" style="border-left-color:#A855F7;">
            {threat_desc}
          </div>
        </div>
        """, unsafe_allow_html=True)

    if fraud_sig:
        st.markdown(f"""
        <div class="doc-card" style="margin-top:0.6rem;">
          <div class="doc-section-header">🔬 Signal Intelligence</div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem;">
            <div>
              <div style="font-size:0.7rem;color:{COLOR_MUTED};text-transform:uppercase;margin-bottom:0.2rem;">Typology</div>
              <div style="font-weight:600;color:{COLOR_TEAL};">{typology_label}</div>
            </div>
            <div>
              <div style="font-size:0.7rem;color:{COLOR_MUTED};text-transform:uppercase;margin-bottom:0.2rem;">Severity</div>
              <div style="font-weight:600;">{fraud_sig.get('severity_estimate','—')}</div>
            </div>
            <div>
              <div style="font-size:0.7rem;color:{COLOR_MUTED};text-transform:uppercase;margin-bottom:0.2rem;">Novelty Score</div>
              <div style="font-weight:600;">{fraud_sig.get('novelty_score',0):.0%}</div>
            </div>
            <div>
              <div style="font-size:0.7rem;color:{COLOR_MUTED};text-transform:uppercase;margin-bottom:0.2rem;">Confidence</div>
              <div style="font-weight:600;">{fraud_sig.get('confidence_score',0):.0%}</div>
            </div>
            <div>
              <div style="font-size:0.7rem;color:{COLOR_MUTED};text-transform:uppercase;margin-bottom:0.2rem;">Attack Vector</div>
              <div style="font-weight:600;">{fraud_sig.get('attack_vector','—')}</div>
            </div>
            <div>
              <div style="font-size:0.7rem;color:{COLOR_MUTED};text-transform:uppercase;margin-bottom:0.2rem;">Source Credibility</div>
              <div style="font-weight:600;">{fraud_sig.get('source_credibility','—')}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FINANCIAL IMPACT
# ══════════════════════════════════════════════════════════════════════════════
with tab_financial:
    fi = {}
    if sim:
        fi = sim.get("financial_impact", {})

    fi_doc = doc.get("financial_exposure", "")

    def fi_row(label: str, value_key: str, cls: str = "") -> str:
        v = fi.get(value_key, None)
        if v is None:
            return f"<tr><td>{label}</td><td><span class='fi-num'>—</span></td></tr>"
        return f"<tr><td>{label}</td><td><span class='fi-num {cls}'>{fmt_sgd(v)}</span></td></tr>"

    st.markdown(f"""
    <div class="doc-card">
      <div class="doc-section-header">💰 Financial Impact Simulation (SGD)</div>
      <table class="fi-table">
        <thead>
          <tr>
            <th>Scenario</th>
            <th>Exposure (SGD)</th>
          </tr>
        </thead>
        <tbody>
          {fi_row("📛 Baseline (no intervention)", "baseline_exposure_sgd", "red")}
          {fi_row("🛡️ With current TM controls", "with_current_controls_sgd", "amber")}
          {fi_row("✅ With proposed interventions", "with_proposed_controls_sgd", "green")}
          <tr><td colspan="2" style="padding:0.3rem 0.8rem;"><hr style="border-color:#1E3A5F;margin:0;"></td></tr>
          {fi_row("📊 P10 — Optimistic", "p10_sgd", "green")}
          {fi_row("📊 P50 — Median", "p50_sgd", "amber")}
          {fi_row("📊 P90 — Worst Case", "p90_sgd", "red")}
        </tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    if fi_doc:
        st.markdown(f"""
        <div class="doc-card" style="margin-top:0.4rem;">
          <div class="doc-section-header">📌 Financial Exposure Summary</div>
          <div class="exec-summary-box" style="border-left-color:#EA580C;">{fi_doc}</div>
        </div>
        """, unsafe_allow_html=True)

    if sim:
        ce = sim.get("customer_exposure", {})
        if ce:
            exposed = ce.get("total_exposed_customers", ce.get("exposed_count", "—"))
            high_risk = ce.get("high_risk_count", ce.get("high_risk_customers", "—"))
            at_risk_pct = ce.get("at_risk_percentage", ce.get("exposure_pct", "—"))

            st.markdown(f"""
            <div class="doc-card" style="margin-top:0.4rem;">
              <div class="doc-section-header">👥 Customer Exposure</div>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;">
                <div style="text-align:center;background:{COLOR_SURFACE2};border-radius:8px;padding:0.8rem;">
                  <div style="font-size:1.5rem;font-weight:700;color:#F87171;">{f"{exposed:,}" if isinstance(exposed,(int,float)) else exposed}</div>
                  <div style="font-size:0.72rem;color:{COLOR_MUTED};text-transform:uppercase;margin-top:0.2rem;">Exposed Customers</div>
                </div>
                <div style="text-align:center;background:{COLOR_SURFACE2};border-radius:8px;padding:0.8rem;">
                  <div style="font-size:1.5rem;font-weight:700;color:#FCD34D;">{f"{high_risk:,}" if isinstance(high_risk,(int,float)) else high_risk}</div>
                  <div style="font-size:0.72rem;color:{COLOR_MUTED};text-transform:uppercase;margin-top:0.2rem;">High-Risk Customers</div>
                </div>
                <div style="text-align:center;background:{COLOR_SURFACE2};border-radius:8px;padding:0.8rem;">
                  <div style="font-size:1.5rem;font-weight:700;color:{COLOR_TEAL};">{at_risk_pct}{'%' if isinstance(at_risk_pct,(int,float)) else ''}</div>
                  <div style="font-size:0.72rem;color:{COLOR_MUTED};text-transform:uppercase;margin-top:0.2rem;">At-Risk Percentage</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GATE RESULTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_gates:
    # Read from the assessment if available
    from data.database import get_assessment_by_signal
    assessment = get_assessment_by_signal(fsid)

    if assessment:
        g1 = assessment.get("gate1", {})
        g2 = assessment.get("gate2", {})
        g3 = assessment.get("gate3", {})
        composite = assessment.get("composite_risk_score", 0)
        overall   = assessment.get("overall_passed", False)
        a_priority = assessment.get("alert_priority", priority)
    else:
        # Fallback to document
        g1 = doc.get("gate1", {})
        g2 = doc.get("gate2", {})
        g3 = doc.get("gate3", {})
        composite = 0
        overall   = False
        a_priority = priority

    def gate_section_html(gate: dict, idx: int, name: str) -> str:
        if not gate:
            return f"""
            <div class="gate-col fail" style="opacity:0.5;">
              <div style="font-size:1.8rem;">⊘</div>
              <div style="font-weight:700;font-size:0.85rem;color:{COLOR_MUTED};margin:0.3rem 0;">Gate {idx}: {name}</div>
              <div style="font-size:0.82rem;color:{COLOR_MUTED};">No data available</div>
            </div>"""

        passed = gate.get("passed", False)
        score  = gate.get("score", gate.get("novelty_score",
                  gate.get("exposure_score", gate.get("gap_score", 0))))
        expl   = gate.get("explanation", gate.get("rationale", "—"))
        cls    = "pass" if passed else "fail"
        icon   = "✅" if passed else "❌"
        result = "PASSED" if passed else "FAILED"
        score_c = "#4ADE80" if passed else "#F87171"
        score_display = f"{score:.0f}" if isinstance(score, (int, float)) else str(score)

        return f"""
        <div class="gate-col {cls}">
          <div style="font-size:2rem;margin-bottom:0.4rem;">{icon}</div>
          <div style="font-weight:700;font-size:0.85rem;color:{COLOR_MUTED};margin-bottom:0.25rem;">
            Gate {idx} · {name}
          </div>
          <div style="font-size:1.4rem;font-weight:700;color:{score_c};margin-bottom:0.4rem;">
            {score_display}<span style="font-size:0.7rem;font-weight:400;color:{COLOR_MUTED};">/100</span>
          </div>
          <div style="display:inline-block;padding:0.15rem 0.6rem;border-radius:20px;
                      background:{'rgba(22,163,74,0.2)' if passed else 'rgba(220,38,38,0.2)'};
                      color:{score_c};font-size:0.72rem;font-weight:700;margin-bottom:0.6rem;">
            {result}
          </div>
          <div style="font-size:0.78rem;color:{COLOR_MUTED};line-height:1.5;">{expl}</div>
        </div>"""

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(gate_section_html(g1, 1, "Novelty"), unsafe_allow_html=True)
    with col2:
        st.markdown(gate_section_html(g2, 2, "Customer Exposure"), unsafe_allow_html=True)
    with col3:
        st.markdown(gate_section_html(g3, 3, "Control Gap"), unsafe_allow_html=True)

    overall_color = "#4ADE80" if overall else "#F87171"
    overall_text  = "ALL GATES PASSED ✅" if overall else "ONE OR MORE GATES FAILED ❌"
    score_c2 = PRIORITY_COLORS.get(a_priority, COLOR_TEAL)

    st.markdown(f"""
    <div style="background:{COLOR_SURFACE2};border:1px solid {COLOR_BORDER};border-radius:10px;
                padding:1rem 1.4rem;margin-top:1rem;display:flex;align-items:center;
                justify-content:space-between;flex-wrap:wrap;gap:0.8rem;">
      <div>
        <div style="font-size:0.72rem;color:{COLOR_MUTED};text-transform:uppercase;letter-spacing:0.8px;">Overall Result</div>
        <div style="font-size:1rem;font-weight:700;color:{overall_color};margin-top:0.2rem;">{overall_text}</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:0.72rem;color:{COLOR_MUTED};text-transform:uppercase;letter-spacing:0.8px;">Composite Risk Score</div>
        <div style="font-size:2rem;font-weight:700;color:{score_c2};">{composite:.0f}<span style="font-size:0.85rem;font-weight:400;color:{COLOR_MUTED};">/100</span></div>
      </div>
      <div>
        {priority_badge_html(a_priority)}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RECOMMENDED ACTIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab_actions:
    rec = doc.get("recommended_actions", {})

    # Normalise to dict
    if isinstance(rec, list):
        rec = {"immediate": rec}

    def action_list_html(items) -> str:
        if not items:
            return '<div style="color:#6B7280;font-size:0.82rem;font-style:italic;">No actions specified.</div>'
        if isinstance(items, str):
            items = [items]
        return "".join(
            f'<div class="action-item">• {item}</div>'
            for item in items
        )

    immediate_items = rec.get("immediate", rec.get("IMMEDIATE", []))
    short_items     = rec.get("short_term", rec.get("SHORT_TERM", rec.get("short", [])))
    strategic_items = rec.get("strategic", rec.get("STRATEGIC", []))

    st.markdown(f"""
    <div class="doc-card">
      <div class="doc-section-header">🎯 Recommended Actions</div>

      <div class="action-section immediate">
        <h4>⚡ Immediate (&lt;24 hours)</h4>
        {action_list_html(immediate_items)}
      </div>

      <div class="action-section short">
        <h4>📅 Short-term (1–7 days)</h4>
        {action_list_html(short_items)}
      </div>

      <div class="action-section strategic">
        <h4>🔭 Strategic (1–4 weeks)</h4>
        {action_list_html(strategic_items)}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Evidence sources
    sources = doc.get("evidence_sources", [])
    if isinstance(sources, str):
        sources = [sources]
    if sources:
        src_html = "".join(f'<div class="action-item">📎 {s}</div>' for s in sources if s)
        st.markdown(f"""
        <div class="doc-card" style="margin-top:0.6rem;">
          <div class="doc-section-header">📚 Evidence Sources</div>
          {src_html}
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — INTERVENTION RULES
# ══════════════════════════════════════════════════════════════════════════════
with tab_rules:
    # Combine DB rules and document rules
    doc_rules = doc.get("intervention_rules", [])
    if isinstance(doc_rules, dict):
        doc_rules = [doc_rules]

    all_rules = rules_db if rules_db else []

    # Fall back to doc rules if no DB rules
    if not all_rules and doc_rules:
        all_rules = doc_rules

    if not all_rules:
        st.info("No intervention rules found for this alert.")
    else:
        st.markdown(f"""
        <div style="margin-bottom:0.8rem;">
          <span style="font-size:0.78rem;color:{COLOR_MUTED};">
            {len(all_rules)} intervention rule{'s' if len(all_rules)!=1 else ''} proposed
          </span>
        </div>
        """, unsafe_allow_html=True)

        for i, rule in enumerate(all_rules, 1):
            rule_type   = rule.get("rule_type", "UNKNOWN")
            rule_desc   = rule.get("rule_description", rule.get("description", "—"))
            rule_logic  = rule.get("rule_logic", rule.get("logic", ""))
            impact_pct  = rule.get("expected_impact_pct", 0)
            dep_risk    = rule.get("deployment_risk", "—")
            approval    = rule.get("approval_required", False)
            auto_dep    = rule.get("auto_deployable", False)
            target_layer = rule.get("target_layer", "—")

            approval_html = (
                '<span style="color:#FCD34D;font-size:0.72rem;">⚠️ Approval Required</span>'
                if approval else
                '<span style="color:#4ADE80;font-size:0.72rem;">✅ No Approval Needed</span>'
            )
            auto_html = (
                '<span style="color:#4ADE80;font-size:0.72rem;">🤖 Auto-deployable</span>'
                if auto_dep else
                '<span style="color:#6B7280;font-size:0.72rem;">👤 Manual Deploy</span>'
            )

            risk_colors = {"LOW": "#16A34A", "MEDIUM": "#D97706", "HIGH": "#EA580C", "CRITICAL": "#DC2626"}
            risk_color  = risk_colors.get(str(dep_risk).upper(), COLOR_MUTED)

            logic_section = f'<div class="rule-logic-box">{rule_logic}</div>' if rule_logic else ""

            st.markdown(f"""
            <div class="rule-card">
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.4rem;">
                <div>
                  {rule_badge_html(rule_type)}
                  <span style="font-size:0.72rem;color:{COLOR_MUTED};margin-left:0.5rem;">#{i} · Layer: {target_layer}</span>
                </div>
                <div style="display:flex;gap:0.8rem;align-items:center;">
                  {approval_html} &nbsp; {auto_html}
                </div>
              </div>
              <div style="font-size:0.86rem;color:{COLOR_TEXT};margin-bottom:0.5rem;line-height:1.55;">{rule_desc}</div>
              {logic_section}
              <div class="rule-meta">
                <div class="rule-meta-item">Impact: <span>~{impact_pct:.0f}%</span></div>
                <div class="rule-meta-item">Deployment Risk: <span style="color:{risk_color};">{dep_risk}</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ANALYST NOTES
# ══════════════════════════════════════════════════════════════════════════════
with tab_notes:
    analyst_notes = doc.get("analyst_notes", doc.get("caveats", ""))

    if analyst_notes:
        st.markdown(f"""
        <div class="doc-card">
          <div class="doc-section-header">🔖 Analyst Notes &amp; Caveats</div>
          <div class="analyst-notes-box">
            ⚠️ &nbsp; {analyst_notes}
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No analyst notes recorded for this alert.")

    # UOB relevance narrative
    uob_rel = doc.get("uob_relevance", "")
    if uob_rel:
        st.markdown(f"""
        <div class="doc-card" style="margin-top:0.6rem;">
          <div class="doc-section-header">🏦 UOB Relevance Assessment</div>
          <div class="exec-summary-box" style="border-left-color:#D97706;">{uob_rel}</div>
        </div>
        """, unsafe_allow_html=True)

    # Raw signal excerpt
    if fraud_sig and fraud_sig.get("raw_evidence"):
        with st.expander("🔬 Raw Evidence (excerpt)", expanded=False):
            st.code(str(fraud_sig["raw_evidence"])[:2000], language="text")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center;font-size:0.72rem;color:{COLOR_MUTED};border-top:1px solid {COLOR_BORDER};padding-top:0.8rem;">
  Phantom Signal · Alert Viewer · RESTRICTED — UOB Group Compliance
</div>
""", unsafe_allow_html=True)
