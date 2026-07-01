"""
Phantom Signal — Page 2: 🔍 Fraud Intelligence
Deep-dive into normalized fraud signals with typology analysis and geo-mapping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from data.database import (
    get_fraud_signals,
    get_signals_by_typology_counts,
    get_fraud_signal_by_id,
)
from config import (
    FRAUD_TYPOLOGIES,
    TYPOLOGY_LABELS,
    PRIORITY_COLORS,
    COLOR_BG,
    COLOR_SURFACE,
    COLOR_TEAL,
    COLOR_BORDER,
    COLOR_TEXT,
    COLOR_MUTED,
    COLOR_CRITICAL,
    COLOR_HIGH,
    COLOR_MEDIUM,
    COLOR_LOW,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fraud Intelligence · Phantom Signal",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {COLOR_BG} !important;
        color: {COLOR_TEXT};
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}
    [data-testid="stSidebar"] {{
        background-color: {COLOR_SURFACE} !important;
        border-right: 1px solid {COLOR_BORDER};
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    div.block-container {{ padding-top: 1.5rem; }}

    /* ── Page header ── */
    .ps-page-header {{
        display: flex; align-items: center; gap: 14px;
        margin-bottom: 24px; padding: 22px 28px;
        background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
        border-radius: 16px;
        background-image: linear-gradient(135deg, {COLOR_SURFACE} 0%, #0a1530 100%);
    }}
    .ps-page-header-icon  {{ font-size: 40px; }}
    .ps-page-header-title {{ font-size: 24px; font-weight: 800; color: {COLOR_TEXT}; margin: 0; }}
    .ps-page-header-sub   {{ font-size: 13px; color: {COLOR_MUTED}; margin: 2px 0 0; }}

    /* ── Metric cards ── */
    .ps-metric-row {{ display: flex; gap: 16px; margin-bottom: 8px; }}
    .ps-metric-card {{
        flex: 1; background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
        border-radius: 14px; padding: 18px 22px; position: relative;
        overflow: hidden; transition: transform 0.2s, box-shadow 0.2s;
    }}
    .ps-metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(2,128,144,0.22);
    }}
    .ps-metric-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, {COLOR_TEAL}, transparent);
        border-radius: 14px 14px 0 0;
    }}
    .ps-metric-label {{ font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
                        text-transform: uppercase; color: {COLOR_MUTED}; margin-bottom: 6px; }}
    .ps-metric-value {{ font-size: 34px; font-weight: 800; color: {COLOR_TEXT}; line-height: 1; }}
    .ps-metric-sub   {{ font-size: 12px; color: {COLOR_MUTED}; margin-top: 4px; }}
    .ps-metric-icon  {{ position: absolute; top: 18px; right: 18px;
                        font-size: 26px; opacity: 0.22; }}

    /* ── Section header ── */
    .ps-section-header {{
        display: flex; align-items: center; gap: 10px;
        margin: 24px 0 14px; padding-bottom: 10px;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    .ps-section-title {{ font-size: 15px; font-weight: 700; color: {COLOR_TEXT}; }}
    .ps-section-pill {{
        background: rgba(2,128,144,0.15); border: 1px solid {COLOR_TEAL};
        border-radius: 20px; padding: 2px 10px; font-size: 11px;
        color: {COLOR_TEAL}; font-weight: 700;
    }}

    /* ── Severity badges ── */
    .badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px;
              font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }}
    .badge-CRITICAL {{ background: rgba(220,38,38,0.2);  color: #FCA5A5; border: 1px solid {COLOR_CRITICAL}; }}
    .badge-HIGH     {{ background: rgba(234,88,12,0.2);  color: #FDBA74; border: 1px solid {COLOR_HIGH}; }}
    .badge-MEDIUM   {{ background: rgba(217,119,6,0.2);  color: #FCD34D; border: 1px solid {COLOR_MEDIUM}; }}
    .badge-LOW      {{ background: rgba(22,163,74,0.2);  color: #86EFAC; border: 1px solid {COLOR_LOW}; }}

    /* ── Novelty bar ── */
    .novelty-bar-wrap {{ background: rgba(30,58,95,0.5); border-radius: 4px;
                         height: 8px; width: 100%; min-width: 80px; }}
    .novelty-bar-fill {{ height: 8px; border-radius: 4px;
                         background: linear-gradient(90deg, {COLOR_TEAL}, #016070); }}

    /* ── Signal table ── */
    .ps-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .ps-table thead th {{
        background: rgba(13,27,62,0.9); color: {COLOR_MUTED};
        font-size: 10px; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; padding: 10px 14px;
        border-bottom: 1px solid {COLOR_BORDER}; text-align: left;
    }}
    .ps-table tbody tr {{
        border-bottom: 1px solid rgba(30,58,95,0.5);
        transition: background 0.15s;
    }}
    .ps-table tbody tr:hover {{ background: rgba(2,128,144,0.07); }}
    .ps-table tbody td {{ padding: 10px 14px; vertical-align: middle; }}
    .typology-chip {{
        display: inline-block; padding: 3px 9px; border-radius: 6px;
        font-size: 11px; font-weight: 600;
        background: rgba(2,128,144,0.12); border: 1px solid rgba(2,128,144,0.35);
        color: {COLOR_TEAL};
    }}
    .conf-pct {{ font-weight: 700; color: {COLOR_TEXT}; }}

    /* ── Detail card ── */
    .detail-card {{
        background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
        border-radius: 12px; padding: 20px 24px; margin-bottom: 12px;
    }}
    .detail-label {{
        font-size: 10px; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; color: {COLOR_MUTED}; margin-bottom: 4px;
    }}
    .detail-value {{
        font-size: 13px; color: {COLOR_TEXT}; line-height: 1.6;
    }}
    .geo-tag {{
        display: inline-block; padding: 2px 8px; border-radius: 5px;
        font-size: 11px; margin: 2px;
        background: rgba(13,27,62,0.8); border: 1px solid {COLOR_BORDER};
        color: {COLOR_MUTED};
    }}

    /* ── Sidebar ── */
    .sidebar-section-title {{
        font-size: 11px; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; color: {COLOR_TEAL}; margin-bottom: 8px;
    }}

    /* ── Streamlit widget overrides ── */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_TEAL}, #016070);
        color: white; border: none; border-radius: 8px;
        font-weight: 700; font-size: 13px; padding: 8px 20px;
        transition: opacity 0.2s;
    }}
    .stButton > button:hover {{ opacity: 0.85; }}
    [data-testid="stExpander"] {{
        background: {COLOR_SURFACE} !important;
        border: 1px solid {COLOR_BORDER} !important;
        border-radius: 10px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def severity_badge(sev: str) -> str:
    s = (sev or "MEDIUM").upper()
    return f'<span class="badge badge-{s}">{s}</span>'


def novelty_bar(score: float) -> str:
    pct = int(min(max(score or 0, 0), 1) * 100)
    color = COLOR_CRITICAL if pct >= 80 else (
        COLOR_HIGH if pct >= 60 else (COLOR_MEDIUM if pct >= 40 else COLOR_LOW)
    )
    return (
        f'<div class="novelty-bar-wrap">'
        f'<div class="novelty-bar-fill" style="width:{pct}%;background:{color};"></div>'
        f'</div>'
        f'<span style="font-size:11px;color:{COLOR_MUTED};margin-left:6px;">{pct}%</span>'
    )


def relative_time(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        s = int(delta.total_seconds())
        if s < 60:    return f"{s}s ago"
        if s < 3600:  return f"{s // 60}m ago"
        if s < 86400: return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return dt_str[:16] if dt_str else "—"


def safe_json_list(val) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return []

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding:16px 0 8px;">
            <div style="font-size:18px; font-weight:800; color:{COLOR_TEXT};">
                🔍 Fraud Intelligence
            </div>
            <div style="font-size:11px; color:{COLOR_MUTED}; margin-top:4px;">
                Filter & explore fraud signals
            </div>
        </div>
        <hr style="border-color:{COLOR_BORDER}; margin:8px 0 16px;">
        <div class="sidebar-section-title">🏷️ Typology</div>
        """,
        unsafe_allow_html=True,
    )

    typology_options = ["All"] + [TYPOLOGY_LABELS.get(t, t) for t in FRAUD_TYPOLOGIES]
    selected_labels  = st.multiselect(
        "Typologies",
        options=typology_options,
        default=[],
        label_visibility="collapsed",
    )
    # Map labels back to keys
    label_to_key = {v: k for k, v in TYPOLOGY_LABELS.items()}
    selected_typology_keys = [label_to_key.get(l, l) for l in selected_labels if l != "All"]

    st.markdown(
        f'<div class="sidebar-section-title" style="margin-top:20px;">⚡ Severity</div>',
        unsafe_allow_html=True,
    )
    severity_filter = st.selectbox(
        "Severity",
        options=["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
        label_visibility="collapsed",
    )

    st.markdown(
        f'<div class="sidebar-section-title" style="margin-top:20px;">📅 Date Range</div>',
        unsafe_allow_html=True,
    )
    date_from = st.date_input("From", value=datetime.now().date() - timedelta(days=30),
                               label_visibility="collapsed")
    date_to   = st.date_input("To",   value=datetime.now().date(),
                               label_visibility="collapsed")

    st.markdown("<hr style='border-color:{};margin:20px 0;'>".format(COLOR_BORDER), unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_fraud_signals():
    return get_fraud_signals(limit=200)

@st.cache_data(ttl=60)
def load_typology_counts():
    return get_signals_by_typology_counts()


all_signals     = load_fraud_signals()
typology_counts = load_typology_counts()

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = all_signals

if selected_typology_keys:
    filtered = [s for s in filtered if s.get("fraud_typology") in selected_typology_keys]

if severity_filter != "All":
    filtered = [s for s in filtered if s.get("severity_estimate", "").upper() == severity_filter]

# Date filter
def parse_date(dt_str):
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).date()
    except Exception:
        return None

filtered = [
    s for s in filtered
    if (d := parse_date(s.get("detected_at", ""))) and date_from <= d <= date_to
]

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="ps-page-header">
        <div class="ps-page-header-icon">🔍</div>
        <div>
            <p class="ps-page-header-title">Fraud Intelligence Hub</p>
            <p class="ps-page-header-sub">
                Normalized threat signals &nbsp;·&nbsp; Typology analysis &nbsp;·&nbsp;
                Geographic threat mapping
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Summary metrics ───────────────────────────────────────────────────────────
total   = len(filtered)
avg_conf = (
    round(sum(s.get("confidence_score", 0) or 0 for s in filtered) / total * 100, 1)
    if total else 0
)
avg_nov  = (
    round(sum(s.get("novelty_score", 0) or 0 for s in filtered) / total * 100, 1)
    if total else 0
)
high_crit = sum(1 for s in filtered if s.get("severity_estimate", "") in ("CRITICAL", "HIGH"))

metric_data = [
    ("🎯", "Total Signals",     total,      "matching current filters"),
    ("📈", "Avg Confidence",    f"{avg_conf}%", "mean AI confidence score"),
    ("🆕", "Avg Novelty",       f"{avg_nov}%",  "mean novelty score"),
    ("🔥", "Critical / High",   high_crit,  "high-priority signals"),
]

cols = st.columns(4)
for col, (icon, label, value, sub) in zip(cols, metric_data):
    with col:
        st.markdown(
            f"""
            <div class="ps-metric-card">
                <div class="ps-metric-icon">{icon}</div>
                <div class="ps-metric-label">{label}</div>
                <div class="ps-metric-value">{value}</div>
                <div class="ps-metric-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Charts row ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="ps-section-header">
        <span class="ps-section-title">📊 Typology Distribution</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_bar, col_map = st.columns([1, 1], gap="large")

with col_bar:
    if typology_counts:
        typo_labels = [TYPOLOGY_LABELS.get(k, k) for k in typology_counts.keys()]
        typo_values = list(typology_counts.values())
        bar_colors  = []
        for k in typology_counts.keys():
            # Colour by rough severity association
            if k in ("RANSOMWARE_FINANCIAL", "DEEPFAKE_CFO_FRAUD", "BEC_CEO_FRAUD"):
                bar_colors.append(COLOR_CRITICAL)
            elif k in ("SIM_SWAP", "ACCOUNT_TAKEOVER", "CREDENTIAL_STUFFING", "INSIDER_THREAT"):
                bar_colors.append(COLOR_HIGH)
            elif k in ("PHISHING_EMAIL", "VISHING", "SEXTORTION", "INVESTMENT_SCAM", "CRYPTO_FRAUD"):
                bar_colors.append(COLOR_MEDIUM)
            else:
                bar_colors.append(COLOR_LOW)

        fig_bar = go.Figure(
            go.Bar(
                y=typo_labels,
                x=typo_values,
                orientation="h",
                marker=dict(
                    color=bar_colors,
                    line=dict(color="rgba(0,0,0,0.3)", width=0.5),
                ),
                text=typo_values,
                textposition="outside",
                textfont=dict(color="#8FA3BF", size=10),
                hovertemplate="<b>%{y}</b><br>Signals: %{x}<extra></extra>",
            )
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=40, t=10, b=10),
            height=420,
            xaxis=dict(
                showgrid=True, gridcolor="rgba(30,58,95,0.5)",
                color="#8FA3BF", tickfont=dict(size=10), zeroline=False,
            ),
            yaxis=dict(
                color="#8FA3BF", tickfont=dict(size=10),
                automargin=True, categoryorder="total ascending",
            ),
            font=dict(family="Inter, Segoe UI, sans-serif", color="#8FA3BF"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.markdown(
            f"<div style='text-align:center;padding:40px;color:{COLOR_MUTED}'>No typology data yet.</div>",
            unsafe_allow_html=True,
        )

with col_map:
    # Build geographic origin data from filtered signals
    country_counts: dict[str, int] = defaultdict(int)
    for sig in filtered:
        origins = safe_json_list(sig.get("geographic_origin", []))
        for item in origins:
            code = None
            if isinstance(item, dict):
                code = item.get("country_code") or item.get("code") or item.get("country")
            elif isinstance(item, str) and len(item) == 2:
                code = item.upper()
            if code:
                country_counts[code.upper()] += 1

    st.markdown(
        f"""
        <div style="font-size:13px;font-weight:700;color:{COLOR_TEXT};margin-bottom:8px;">
            🗺️ Geographic Origin Map
        </div>
        """,
        unsafe_allow_html=True,
    )

    if country_counts:
        map_df_countries = list(country_counts.keys())
        map_df_values    = list(country_counts.values())

        fig_map = go.Figure(
            go.Choropleth(
                locations=map_df_countries,
                z=map_df_values,
                locationmode="ISO-3166-1-alpha-2",
                colorscale=[
                    [0.0, "#0D1B3E"],
                    [0.3, "#016070"],
                    [0.6, "#028090"],
                    [1.0, "#DC2626"],
                ],
                showscale=True,
                colorbar=dict(
                    title=dict(text="Signals", font=dict(color="#8FA3BF", size=11)),
                    tickfont=dict(color="#8FA3BF", size=10),
                    bgcolor="rgba(13,27,62,0.8)",
                    bordercolor=COLOR_BORDER,
                    len=0.75,
                    thickness=12,
                ),
                hovertemplate="<b>%{location}</b><br>Signals: %{z}<extra></extra>",
            )
        )
        fig_map.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                coastlinecolor=COLOR_BORDER,
                showland=True,
                landcolor="#0a1530",
                showocean=True,
                oceancolor=COLOR_BG,
                showlakes=False,
                showborders=True,
                bordercolor=COLOR_BORDER,
                bgcolor="rgba(0,0,0,0)",
                projection_type="natural earth",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=420,
            font=dict(family="Inter, Segoe UI, sans-serif", color="#8FA3BF"),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.markdown(
            f"""
            <div style="text-align:center; padding:80px 0; color:{COLOR_MUTED};">
                <div style="font-size:42px; margin-bottom:10px;">🗺️</div>
                <div style="font-size:14px; font-weight:600;">No geographic data available</div>
                <div style="font-size:12px; margin-top:6px;">
                    Geographic origin data will appear as signals are processed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Signal table with expandable cards ───────────────────────────────────────
st.markdown(
    f"""
    <div class="ps-section-header">
        <span class="ps-section-title">🧠 Fraud Signal Records</span>
        <span class="ps-section-pill">{total} signals</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not filtered:
    st.markdown(
        f"""
        <div style="text-align:center; padding:60px 0; color:{COLOR_MUTED};">
            <div style="font-size:48px; margin-bottom:12px;">🕵️</div>
            <div style="font-size:16px; font-weight:600;">No signals match your filters</div>
            <div style="font-size:13px; margin-top:6px;">
                Adjust the sidebar filters or run the pipeline to ingest more data.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Table header
    st.markdown(
        f"""
        <div style="overflow-x:auto; border:1px solid {COLOR_BORDER}; border-radius:12px 12px 0 0;">
        <table class="ps-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Typology</th>
                    <th>Severity</th>
                    <th>Detected</th>
                    <th>Confidence</th>
                    <th>Novelty</th>
                </tr>
            </thead>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render each signal row + expander
    for idx, sig in enumerate(filtered, 1):
        typology_key   = sig.get("fraud_typology", "UNKNOWN")
        typology_label = TYPOLOGY_LABELS.get(typology_key, typology_key)
        severity       = sig.get("severity_estimate", "MEDIUM")
        detected_at    = relative_time(sig.get("detected_at", ""))
        conf_pct       = int((sig.get("confidence_score") or 0) * 100)
        nov_score      = sig.get("novelty_score") or 0
        fid            = sig.get("fraud_signal_id", "")

        # Row as HTML
        st.markdown(
            f"""
            <div style="background:{COLOR_SURFACE}; border-left:1px solid {COLOR_BORDER};
                        border-right:1px solid {COLOR_BORDER};
                        border-bottom:1px solid rgba(30,58,95,0.4);">
            <table class="ps-table" style="margin:0;">
                <tbody>
                <tr>
                    <td style="width:36px; color:{COLOR_MUTED}; font-size:11px;">{idx}</td>
                    <td><span class="typology-chip">{typology_label}</span></td>
                    <td>{severity_badge(severity)}</td>
                    <td style="color:{COLOR_MUTED}; font-size:12px; font-style:italic;">{detected_at}</td>
                    <td><span class="conf-pct">{conf_pct}%</span></td>
                    <td style="min-width:120px;">{novelty_bar(nov_score)}</td>
                </tr>
                </tbody>
            </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Expandable detail card
        exp_label = f"📂 {typology_label} — {severity} · {detected_at}"
        with st.expander(exp_label, expanded=False):
            # Full signal from DB for rich data
            full = get_fraud_signal_by_id(fid) or sig

            desc        = full.get("fraud_description") or "—"
            attack_vec  = full.get("attack_vector")      or "—"
            fin_mech    = full.get("financial_mechanism") or "—"
            credibility = full.get("source_credibility")  or "—"
            first_rep   = full.get("first_reported_globally") or "—"

            victim_profile  = full.get("victim_profile", {})
            geo_origin      = safe_json_list(full.get("geographic_origin", []))
            geo_spread      = safe_json_list(full.get("geographic_spread", []))

            col_l, col_r = st.columns([3, 2], gap="large")

            with col_l:
                st.markdown(
                    f"""
                    <div class="detail-card">
                        <div class="detail-label">🕵️ Fraud Description</div>
                        <div class="detail-value">{desc}</div>
                    </div>
                    <div class="detail-card">
                        <div class="detail-label">⚔️ Attack Vector</div>
                        <div class="detail-value">{attack_vec}</div>
                    </div>
                    <div class="detail-card">
                        <div class="detail-label">💸 Financial Mechanism</div>
                        <div class="detail-value">{fin_mech}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_r:
                # Victim profile
                if victim_profile and isinstance(victim_profile, dict):
                    vp_html = "".join(
                        f"<div><span style='color:{COLOR_MUTED};font-size:11px;"
                        f"text-transform:uppercase;'>{k.replace('_',' ')}</span>: "
                        f"<span style='color:{COLOR_TEXT};'>{v}</span></div>"
                        for k, v in victim_profile.items()
                        if v
                    )
                else:
                    vp_html = "<em style='color:#8FA3BF'>No victim profile data</em>"

                # Geo tags
                origin_tags = ""
                for item in geo_origin:
                    code = (
                        item.get("country_code") or item.get("code", "")
                        if isinstance(item, dict) else item
                    )
                    if code:
                        origin_tags += f'<span class="geo-tag">🌐 {code}</span>'
                if not origin_tags:
                    origin_tags = "<em style='color:#8FA3BF'>—</em>"

                spread_tags = ""
                for item in geo_spread:
                    code = (
                        item.get("country_code") or item.get("code", "")
                        if isinstance(item, dict) else item
                    )
                    if code:
                        spread_tags += f'<span class="geo-tag">📍 {code}</span>'
                if not spread_tags:
                    spread_tags = "<em style='color:#8FA3BF'>—</em>"

                st.markdown(
                    f"""
                    <div class="detail-card">
                        <div class="detail-label">👤 Victim Profile</div>
                        <div class="detail-value" style="font-size:12px;">{vp_html}</div>
                    </div>
                    <div class="detail-card">
                        <div class="detail-label">🌍 Geographic Origin</div>
                        <div style="margin-top:4px;">{origin_tags}</div>
                    </div>
                    <div class="detail-card">
                        <div class="detail-label">🗺️ Geographic Spread</div>
                        <div style="margin-top:4px;">{spread_tags}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Score strip
            sev_color = PRIORITY_COLORS.get(severity.upper(), COLOR_TEAL)
            st.markdown(
                f"""
                <div style="display:flex; gap:16px; margin-top:8px; flex-wrap:wrap;">
                    <div style="background:rgba(13,27,62,0.8); border:1px solid {COLOR_BORDER};
                                border-radius:8px; padding:10px 16px; flex:1;">
                        <div class="detail-label">Source Credibility</div>
                        <div style="font-size:15px; font-weight:700; color:{COLOR_TEAL};">
                            {credibility}
                        </div>
                    </div>
                    <div style="background:rgba(13,27,62,0.8); border:1px solid {COLOR_BORDER};
                                border-radius:8px; padding:10px 16px; flex:1;">
                        <div class="detail-label">First Reported Globally</div>
                        <div style="font-size:13px; font-weight:600; color:{COLOR_TEXT};">
                            {first_rep[:10] if first_rep != '—' else '—'}
                        </div>
                    </div>
                    <div style="background:rgba(13,27,62,0.8); border:1px solid {COLOR_BORDER};
                                border-radius:8px; padding:10px 16px; flex:1;">
                        <div class="detail-label">AI Confidence Score</div>
                        <div style="font-size:22px; font-weight:800; color:{COLOR_TEXT};">
                            {conf_pct}<span style="font-size:13px;color:{COLOR_MUTED};">%</span>
                        </div>
                    </div>
                    <div style="background:rgba(13,27,62,0.8); border:1px solid {COLOR_BORDER};
                                border-radius:8px; padding:10px 16px; flex:1;">
                        <div class="detail-label">Novelty Score</div>
                        <div style="font-size:22px; font-weight:800; color:{sev_color};">
                            {int(nov_score * 100)}<span style="font-size:13px;color:{COLOR_MUTED};">%</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Close border
    st.markdown(
        f"<div style='border-bottom:1px solid {COLOR_BORDER}; border-left:1px solid {COLOR_BORDER}; "
        f"border-right:1px solid {COLOR_BORDER}; border-radius:0 0 12px 12px; height:8px;'></div>",
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="margin-top:40px; padding:16px 0; border-top:1px solid {COLOR_BORDER};
                text-align:center; color:{COLOR_MUTED}; font-size:11px; letter-spacing:0.5px;">
        🛡️ PHANTOM SIGNAL &nbsp;·&nbsp; OSInt Early Warning Framework &nbsp;·&nbsp;
        Fraud Intelligence Module &nbsp;·&nbsp;
        <em>Powered by AI-driven signal normalization</em>
    </div>
    """,
    unsafe_allow_html=True,
)
