"""
Phantom Signal — Page 3: Relevance Assessment
3-Gate assessment visualization with composite risk gauge.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go

from config import (
    PRIORITY_COLORS, COLOR_BG, COLOR_NAVY, COLOR_TEAL, COLOR_SURFACE2,
    COLOR_BORDER, COLOR_TEXT, COLOR_MUTED, TYPOLOGY_LABELS,
)
from data.database import get_relevance_assessments, get_fraud_signal_by_id

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Relevance Assessment · Phantom Signal",
    page_icon="⚖️",
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

  /* Hide default streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}

  /* ── Navbar brand ── */
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
      margin-bottom: 1.6rem;
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

  /* ── Assessment card ── */
  .assessment-card {{
      background: {COLOR_NAVY};
      border: 1px solid {COLOR_BORDER};
      border-radius: 12px;
      padding: 1.25rem 1.4rem 1rem;
      margin-bottom: 1.4rem;
      transition: border-color 0.2s;
  }}
  .assessment-card:hover {{
      border-color: {COLOR_TEAL};
  }}
  .assessment-card-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1rem;
      gap: 0.8rem;
      flex-wrap: wrap;
  }}
  .assessment-id {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: {COLOR_MUTED};
  }}
  .typology-badge {{
      background: {COLOR_SURFACE2};
      border: 1px solid {COLOR_BORDER};
      border-radius: 6px;
      padding: 0.2rem 0.65rem;
      font-size: 0.78rem;
      color: {COLOR_TEAL};
      font-weight: 600;
  }}

  /* ── 3-gate flow ── */
  .gate-flow {{
      display: flex;
      align-items: stretch;
      gap: 0;
      margin: 0.6rem 0 0.8rem;
  }}
  .gate-box {{
      flex: 1;
      border-radius: 10px;
      padding: 0.85rem 1rem;
      position: relative;
  }}
  .gate-box.pass {{
      background: rgba(22,163,74,0.12);
      border: 1.5px solid #16A34A;
  }}
  .gate-box.fail {{
      background: rgba(220,38,38,0.12);
      border: 1.5px solid #DC2626;
  }}
  .gate-box.na {{
      background: rgba(107,114,128,0.1);
      border: 1.5px solid #374151;
      opacity: 0.6;
  }}
  .gate-icon {{
      font-size: 1.5rem;
      line-height: 1;
      margin-bottom: 0.3rem;
  }}
  .gate-name {{
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: {COLOR_MUTED};
      margin-bottom: 0.3rem;
  }}
  .gate-score {{
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 0.3rem;
  }}
  .gate-score.pass {{ color: #4ADE80; }}
  .gate-score.fail {{ color: #F87171; }}
  .gate-score.na   {{ color: #6B7280; }}
  .gate-expl {{
      font-size: 0.73rem;
      color: {COLOR_MUTED};
      line-height: 1.45;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
  }}
  .gate-arrow {{
      display: flex;
      align-items: center;
      padding: 0 0.45rem;
      color: {COLOR_MUTED};
      font-size: 1.25rem;
      flex-shrink: 0;
  }}

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

  /* ── Summary table ── */
  .summary-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
  }}
  .summary-table th {{
      background: {COLOR_SURFACE2};
      color: {COLOR_TEAL};
      text-transform: uppercase;
      font-size: 0.7rem;
      letter-spacing: 0.8px;
      padding: 0.6rem 0.8rem;
      border-bottom: 1px solid {COLOR_BORDER};
      text-align: left;
  }}
  .summary-table td {{
      padding: 0.55rem 0.8rem;
      border-bottom: 1px solid rgba(30,58,95,0.5);
      color: {COLOR_TEXT};
      vertical-align: middle;
  }}
  .summary-table tr:last-child td {{ border-bottom: none; }}
  .summary-table tr:hover td {{ background: rgba(2,128,144,0.06); }}

  /* ── Section divider ── */
  .section-divider {{
      border: none;
      border-top: 1px solid {COLOR_BORDER};
      margin: 1.4rem 0;
  }}

  /* ── Gate result icon pill ── */
  .gate-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.18rem 0.5rem;
      border-radius: 20px;
      font-size: 0.72rem;
      font-weight: 600;
  }}
  .gate-pill.pass {{ background: rgba(22,163,74,0.15); color: #4ADE80; }}
  .gate-pill.fail {{ background: rgba(220,38,38,0.15); color: #F87171; }}

  /* ── Filter bar ── */
  .filter-label {{
      font-size: 0.78rem;
      color: {COLOR_MUTED};
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 0.3rem;
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


def gate_pill_html(passed: bool) -> str:
    cls = "pass" if passed else "fail"
    icon = "✓" if passed else "✗"
    return f'<span class="gate-pill {cls}">{icon} {"PASS" if passed else "FAIL"}</span>'


def score_color(score: float) -> str:
    if score >= 80:
        return "#DC2626"
    elif score >= 60:
        return "#EA580C"
    elif score >= 40:
        return "#D97706"
    return "#16A34A"


def make_gauge(score: float, priority: str) -> go.Figure:
    pri_color = PRIORITY_COLORS.get(priority, "#028090")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            "font": {"size": 32, "color": pri_color, "family": "Inter"},
            "suffix": "",
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#1E3A5F",
                "tickvals": [0, 20, 40, 60, 80, 100],
                "ticktext": ["0", "20", "40", "60", "80", "100"],
                "tickfont": {"color": "#8FA3BF", "size": 10},
            },
            "bar": {"color": pri_color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "rgba(22,163,74,0.18)"},
                {"range": [40, 60], "color": "rgba(217,119,6,0.18)"},
                {"range": [60, 80], "color": "rgba(234,88,12,0.18)"},
                {"range": [80,100], "color": "rgba(220,38,38,0.22)"},
            ],
            "threshold": {
                "line": {"color": pri_color, "width": 3},
                "thickness": 0.75,
                "value": score,
            },
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10, l=20, r=20),
        height=200,
        font={"family": "Inter", "color": "#E8EDF5"},
    )
    return fig


def render_gate_flow(g1: dict, g2: dict, g3: dict):
    """Render the 3-gate visual flow as HTML."""

    def gate_html(label: str, gate: dict, idx: int) -> str:
        if not gate:
            return f"""
            <div class="gate-box na">
              <div class="gate-icon">⊘</div>
              <div class="gate-name">Gate {idx}</div>
              <div class="gate-score na">N/A</div>
              <div class="gate-expl">No data</div>
            </div>"""

        passed = gate.get("passed", False)
        score  = gate.get("score", gate.get("novelty_score",
                  gate.get("exposure_score", gate.get("gap_score", 0))))
        expl   = gate.get("explanation", gate.get("rationale", "—"))
        cls    = "pass" if passed else "fail"
        icon   = "✅" if passed else "❌"
        score_display = f"{score:.0f}" if isinstance(score, (int, float)) else str(score)
        return f"""
        <div class="gate-box {cls}">
          <div class="gate-icon">{icon}</div>
          <div class="gate-name">Gate {idx} — {label}</div>
          <div class="gate-score {cls}">{score_display}<span style="font-size:0.65rem;font-weight:400;color:#8FA3BF;">/100</span></div>
          <div class="gate-expl">{expl}</div>
        </div>"""

    html = '<div class="gate-flow">'
    html += gate_html("Novelty", g1, 1)
    html += '<div class="gate-arrow">→</div>'
    html += gate_html("Customer Exposure", g2, 2)
    html += '<div class="gate-arrow">→</div>'
    html += gate_html("Control Gap", g3, 3)
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ps-topbar">
  <span style="font-size:1.8rem;">⚖️</span>
  <div>
    <div class="ps-topbar-title">Relevance Assessment</div>
    <div class="ps-topbar-sub">3-Gate Signal Qualification Engine · Phantom Signal</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_assessments():
    return get_relevance_assessments(limit=200)

assessments = load_assessments()

if not assessments:
    st.warning("⚠️ No relevance assessments found in the database. Run the pipeline first.")
    st.stop()

# Pre-load fraud signal info
@st.cache_data(ttl=60)
def get_signal_info(fsid: str):
    return get_fraud_signal_by_id(fsid)

# Determine gate failures for filter
def gate_filter_key(a: dict) -> str:
    g1 = a.get("gate1", {})
    g2 = a.get("gate2", {})
    g3 = a.get("gate3", {})
    if a.get("overall_passed"):
        return "Passed All Gates"
    if not g1.get("passed", True):
        return "Failed Gate 1"
    if not g2.get("passed", True):
        return "Failed Gate 2"
    return "Failed Gate 3"

# Compute metrics
total        = len(assessments)
passed_all   = sum(1 for a in assessments if a.get("overall_passed"))
failed_g1    = sum(1 for a in assessments if not a.get("gate1", {}).get("passed", True) and not a.get("overall_passed"))
failed_g2    = sum(1 for a in assessments
                   if a.get("gate1", {}).get("passed", True)
                   and not a.get("gate2", {}).get("passed", True)
                   and not a.get("overall_passed"))
avg_score    = sum(a.get("composite_risk_score", 0) for a in assessments) / max(total, 1)

# ── Metrics row ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="metric-row">
  <div class="metric-chip">
    <div class="chip-val">{total}</div>
    <div class="chip-lbl">Total Assessments</div>
  </div>
  <div class="metric-chip" style="border-color:#16A34A55;">
    <div class="chip-val" style="color:#4ADE80;">{passed_all}</div>
    <div class="chip-lbl">Passed All Gates</div>
  </div>
  <div class="metric-chip" style="border-color:#DC262655;">
    <div class="chip-val" style="color:#F87171;">{total - passed_all}</div>
    <div class="chip-lbl">Failed ≥1 Gate</div>
  </div>
  <div class="metric-chip" style="border-color:{COLOR_TEAL}55;">
    <div class="chip-val" style="color:{COLOR_TEAL};">{avg_score:.0f}</div>
    <div class="chip-lbl">Avg Risk Score</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Filter bar ────────────────────────────────────────────────────────────────
filter_options = ["All", "Passed All Gates", "Failed Gate 1", "Failed Gate 2", "Failed Gate 3"]

col_f1, col_f2 = st.columns([2, 4])
with col_f1:
    st.markdown('<div class="filter-label">Filter by Gate Result</div>', unsafe_allow_html=True)
    selected_filter = st.selectbox(
        "filter",
        options=filter_options,
        label_visibility="collapsed",
        key="gate_filter",
    )
with col_f2:
    st.markdown('<div class="filter-label">Priority Filter</div>', unsafe_allow_html=True)
    priority_filter = st.multiselect(
        "priority",
        options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        label_visibility="collapsed",
        key="priority_filter",
    )

# Apply filters
def passes_filter(a: dict) -> bool:
    if a.get("alert_priority") not in priority_filter:
        return False
    if selected_filter == "All":
        return True
    if selected_filter == "Passed All Gates":
        return bool(a.get("overall_passed"))
    g1 = a.get("gate1", {})
    g2 = a.get("gate2", {})
    g3 = a.get("gate3", {})
    if selected_filter == "Failed Gate 1":
        return not g1.get("passed", True) and not a.get("overall_passed")
    if selected_filter == "Failed Gate 2":
        return g1.get("passed", True) and not g2.get("passed", True) and not a.get("overall_passed")
    if selected_filter == "Failed Gate 3":
        return g1.get("passed", True) and g2.get("passed", True) and not g3.get("passed", True)
    return True

filtered = [a for a in assessments if passes_filter(a)]
st.markdown(f'<p style="color:{COLOR_MUTED};font-size:0.8rem;margin-bottom:0.8rem;">Showing <b style="color:{COLOR_TEXT};">{len(filtered)}</b> of {total} assessments</p>', unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Render assessment cards ───────────────────────────────────────────────────
if not filtered:
    st.info("No assessments match the current filter.")
else:
    # Show first N with a paginator
    PAGE_SIZE = 5
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)

    col_page_l, col_page_c, col_page_r = st.columns([1, 2, 1])
    with col_page_c:
        page_num = st.number_input(
            f"Page (1–{total_pages})",
            min_value=1, max_value=total_pages,
            value=1, step=1, key="assessment_page",
        )

    page_assessments = filtered[(page_num - 1) * PAGE_SIZE : page_num * PAGE_SIZE]

    for a in page_assessments:
        fsid     = a.get("fraud_signal_id", "")
        fs       = get_signal_info(fsid) or {}
        typology = fs.get("fraud_typology", "UNKNOWN")
        label    = TYPOLOGY_LABELS.get(typology, typology)
        score    = a.get("composite_risk_score", 0)
        priority = a.get("alert_priority", "LOW")
        assessed = a.get("assessed_at", "")[:16].replace("T", " ")
        aid_short = a.get("assessment_id", "")[:12].upper()

        g1 = a.get("gate1", {})
        g2 = a.get("gate2", {})
        g3 = a.get("gate3", {})

        overall_icon = "✅ ALL GATES PASSED" if a.get("overall_passed") else "❌ GATE FAILED"
        overall_color = "#4ADE80" if a.get("overall_passed") else "#F87171"

        st.markdown(f"""
        <div class="assessment-card">
          <div class="assessment-card-header">
            <div>
              <span class="assessment-id">#{aid_short}</span>
              &nbsp;&nbsp;
              <span class="typology-badge">🎯 {label}</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.8rem;">
              <span style="font-size:0.8rem;color:{overall_color};font-weight:700;">{overall_icon}</span>
              {priority_badge_html(priority)}
              <span style="font-size:0.75rem;color:{COLOR_MUTED};">🕐 {assessed}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Gate flow + gauge side by side
        col_gates, col_gauge = st.columns([3, 1])
        with col_gates:
            render_gate_flow(g1, g2, g3)
        with col_gauge:
            fig = make_gauge(score, priority)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(
                f'<p style="text-align:center;font-size:0.72rem;color:{COLOR_MUTED};margin-top:-0.5rem;">'
                f'Composite Risk Score</p>',
                unsafe_allow_html=True,
            )

        # Recommended actions (collapsed)
        rec_actions = a.get("recommended_actions", [])
        if rec_actions:
            with st.expander("📋 Recommended Actions", expanded=False):
                if isinstance(rec_actions, list):
                    for item in rec_actions:
                        st.markdown(f"&nbsp;&nbsp;• {item}")
                elif isinstance(rec_actions, dict):
                    for timing, items in rec_actions.items():
                        st.markdown(f"**{timing.replace('_',' ').title()}**")
                        for item in (items if isinstance(items, list) else [items]):
                            st.markdown(f"&nbsp;&nbsp;• {item}")

        st.markdown("<div style='height:0.2rem;'></div>", unsafe_allow_html=True)

# ── Summary Table ─────────────────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(f'<h3 style="color:{COLOR_TEXT};font-size:1.05rem;font-weight:700;margin-bottom:0.8rem;">📊 Assessment Summary Table</h3>', unsafe_allow_html=True)

rows_html = ""
for a in filtered[:50]:
    fsid     = a.get("fraud_signal_id", "")
    fs       = get_signal_info(fsid) or {}
    typology = fs.get("fraud_typology", "UNKNOWN")
    label    = TYPOLOGY_LABELS.get(typology, typology)
    score    = a.get("composite_risk_score", 0)
    priority = a.get("alert_priority", "LOW")
    aid_short = a.get("assessment_id", "")[:10].upper()
    assessed  = a.get("assessed_at", "")[:16].replace("T", " ")

    g1 = a.get("gate1", {})
    g2 = a.get("gate2", {})
    g3 = a.get("gate3", {})

    g1_html = gate_pill_html(g1.get("passed", False))
    g2_html = gate_pill_html(g2.get("passed", False))
    g3_html = gate_pill_html(g3.get("passed", False))
    p_html  = priority_badge_html(priority)
    score_c = score_color(score)

    rows_html += f"""
    <tr>
      <td><span style="font-family:monospace;font-size:0.78rem;color:{COLOR_MUTED};">#{aid_short}</span></td>
      <td><span style="color:{COLOR_TEAL};font-weight:600;">{label}</span></td>
      <td>{g1_html}</td>
      <td>{g2_html}</td>
      <td>{g3_html}</td>
      <td>{p_html}</td>
      <td><span style="font-weight:700;color:{score_c};">{score:.0f}<span style="font-size:0.65rem;font-weight:400;color:{COLOR_MUTED};">/100</span></span></td>
      <td style="color:{COLOR_MUTED};font-size:0.78rem;">{assessed}</td>
    </tr>"""

st.markdown(f"""
<div style="overflow-x:auto;">
<table class="summary-table">
  <thead>
    <tr>
      <th>Assessment ID</th>
      <th>Signal Typology</th>
      <th>Gate 1</th>
      <th>Gate 2</th>
      <th>Gate 3</th>
      <th>Priority</th>
      <th>Risk Score</th>
      <th>Assessed At</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
st.markdown(f"""
<div style="text-align:center;font-size:0.72rem;color:{COLOR_MUTED};border-top:1px solid {COLOR_BORDER};padding-top:0.8rem;">
  Phantom Signal · Relevance Assessment · RESTRICTED — UOB Group Compliance
</div>
""", unsafe_allow_html=True)
