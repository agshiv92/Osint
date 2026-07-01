"""
Phantom Signal — Page 1: 📡 Live OSInt Feed
Real-time view of raw ingested signals with status badges and source breakdown.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone
from collections import Counter

from data.database import (
    get_raw_signals,
    count_raw_signals_by_status,
    get_raw_signal_count_today,
    get_alerts_count_today,
)
from config import COLOR_BG, COLOR_SURFACE, COLOR_TEAL, COLOR_BORDER, COLOR_TEXT, COLOR_MUTED

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Live Feed · Phantom Signal",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    /* ── Root theme ── */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {COLOR_BG} !important;
        color: {COLOR_TEXT};
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }}
    [data-testid="stSidebar"] {{ background-color: {COLOR_SURFACE} !important; }}
    [data-testid="stHeader"] {{ background: transparent !important; }}

    /* ── Metric cards ── */
    .ps-metric-card {{
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 14px;
        padding: 20px 24px 18px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .ps-metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(2, 128, 144, 0.25);
    }}
    .ps-metric-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, {COLOR_TEAL}, transparent);
        border-radius: 14px 14px 0 0;
    }}
    .ps-metric-label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: {COLOR_MUTED};
        margin-bottom: 8px;
    }}
    .ps-metric-value {{
        font-size: 38px;
        font-weight: 800;
        color: {COLOR_TEXT};
        line-height: 1;
        margin-bottom: 4px;
    }}
    .ps-metric-sub {{
        font-size: 12px;
        color: {COLOR_MUTED};
    }}
    .ps-metric-icon {{
        position: absolute;
        top: 20px; right: 20px;
        font-size: 28px;
        opacity: 0.25;
    }}

    /* ── Status badges ── */
    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    .badge-PENDING    {{ background: rgba(107,114,128,0.2); color: #9CA3AF; border: 1px solid #6B7280; }}
    .badge-NORMALIZED {{ background: rgba(59,130,246,0.2);  color: #60A5FA; border: 1px solid #3B82F6; }}
    .badge-ALERTED    {{ background: rgba(220,38,38,0.25);  color: #FCA5A5; border: 1px solid #DC2626; }}
    .badge-DISCARDED  {{ background: rgba(55,65,81,0.4);    color: #6B7280; border: 1px solid #374151; }}
    .badge-FILTERED   {{ background: rgba(139,92,246,0.2);  color: #C4B5FD; border: 1px solid #8B5CF6; }}

    /* ── Section header ── */
    .ps-section-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 28px 0 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    .ps-section-title {{
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.5px;
        color: {COLOR_TEXT};
    }}
    .ps-section-pill {{
        background: rgba(2,128,144,0.15);
        border: 1px solid {COLOR_TEAL};
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 11px;
        color: {COLOR_TEAL};
        font-weight: 700;
    }}

    /* ── Signal table rows ── */
    .ps-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }}
    .ps-table thead th {{
        background: rgba(13,27,62,0.9);
        color: {COLOR_MUTED};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 10px 14px;
        border-bottom: 1px solid {COLOR_BORDER};
        text-align: left;
    }}
    .ps-table tbody tr {{
        border-bottom: 1px solid rgba(30,58,95,0.5);
        transition: background 0.15s ease;
    }}
    .ps-table tbody tr:hover {{
        background: rgba(2,128,144,0.07);
    }}
    .ps-table tbody td {{
        padding: 10px 14px;
        color: {COLOR_TEXT};
        vertical-align: middle;
    }}
    .source-chip {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
        background: rgba(2,128,144,0.15);
        border: 1px solid rgba(2,128,144,0.4);
        color: {COLOR_TEAL};
    }}
    .time-ago {{
        color: {COLOR_MUTED};
        font-size: 12px;
        font-style: italic;
    }}
    .signal-title {{
        color: {COLOR_TEXT};
        font-weight: 500;
    }}

    /* ── Page header ── */
    .ps-page-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 24px;
        padding: 22px 28px;
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 16px;
        background-image: linear-gradient(135deg, {COLOR_SURFACE} 0%, #0a1530 100%);
    }}
    .ps-page-header-icon {{ font-size: 40px; }}
    .ps-page-header-title {{
        font-size: 24px;
        font-weight: 800;
        color: {COLOR_TEXT};
        margin: 0;
    }}
    .ps-page-header-sub {{
        font-size: 13px;
        color: {COLOR_MUTED};
        margin: 2px 0 0;
    }}
    .ps-live-dot {{
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 0 3px rgba(16,185,129,0.25);
        animation: pulse 2s infinite;
        margin-right: 6px;
    }}
    @keyframes pulse {{
        0%   {{ box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }}
        70%  {{ box-shadow: 0 0 0 8px rgba(16,185,129,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(16,185,129,0); }}
    }}

    /* ── Streamlit overrides ── */
    div[data-testid="metric-container"] {{ display: none; }}
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_TEAL}, #016070);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        padding: 8px 20px;
        letter-spacing: 0.5px;
        transition: opacity 0.2s ease;
    }}
    .stButton > button:hover {{ opacity: 0.85; }}
    div.block-container {{ padding-top: 1.5rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def relative_time(dt_str: str) -> str:
    """Return human-readable relative time from an ISO datetime string."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        s = int(delta.total_seconds())
        if s < 60:
            return f"{s}s ago"
        elif s < 3600:
            return f"{s // 60}m ago"
        elif s < 86400:
            return f"{s // 3600}h ago"
        else:
            return f"{s // 86400}d ago"
    except Exception:
        return dt_str[:16] if dt_str else "—"


def status_badge(status: str) -> str:
    safe = status.upper() if status else "PENDING"
    return f'<span class="badge badge-{safe}">{safe}</span>'


def truncate(text: str, n: int = 60) -> str:
    if not text:
        return "<em style='color:#8FA3BF'>—</em>"
    return text[:n] + "…" if len(text) > n else text

# ── Load data ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_signals():
    return get_raw_signals(limit=50)

@st.cache_data(ttl=30)
def load_status_counts():
    return count_raw_signals_by_status()

@st.cache_data(ttl=30)
def load_today_count():
    return get_raw_signal_count_today()

@st.cache_data(ttl=30)
def load_alerts_today():
    return get_alerts_count_today()


signals      = load_signals()
status_counts = load_status_counts()
today_count  = load_today_count()
alerts_today = load_alerts_today()

normalized_count = status_counts.get("NORMALIZED", 0)
discarded_count  = status_counts.get("DISCARDED", 0)

# ── Page header ───────────────────────────────────────────────────────────────
ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC+8")
st.markdown(
    f"""
    <div class="ps-page-header">
        <div class="ps-page-header-icon">📡</div>
        <div>
            <p class="ps-page-header-title">
                <span class="ps-live-dot"></span>Live OSInt Feed
            </p>
            <p class="ps-page-header-sub">
                Real-time ingestion monitor &nbsp;·&nbsp; Last refreshed: {ts_now}
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Top-row refresh button ────────────────────────────────────────────────────
col_spacer, col_btn_process, col_btn = st.columns([6, 2, 1])
with col_btn_process:
    if st.button("⚡ Process Pending Signals", use_container_width=True, type="primary"):
        with st.spinner("Processing pending signals..."):
            from pipeline.orchestrator import run_orchestrator_batch
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def p_callback(msg, pct):
                status_text.text(msg)
                progress_bar.progress(pct)
                
            run_orchestrator_batch(progress_callback=p_callback, limit=10)
            st.cache_data.clear()
            st.rerun()

with col_btn:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Metric cards ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

metric_cards = [
    (c1, "📥", "Signals Today",   today_count,      "ingested in the last 24 h"),
    (c2, "✅", "Normalized",      normalized_count, "passed Gate-1 filter"),
    (c3, "🚨", "Alerts Generated", alerts_today,    "risk alerts raised today"),
    (c4, "🗑️", "Discarded",       discarded_count,  "below relevance threshold"),
]

for col, icon, label, value, sub in metric_cards:
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

# ── Signal table + Source chart layout ───────────────────────────────────────
st.markdown(
    f"""
    <div class="ps-section-header">
        <span class="ps-section-title">📋 Last 50 Raw Signals</span>
        <span class="ps-section-pill">{len(signals)} records</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_table, col_chart = st.columns([3, 1], gap="large")

with col_table:
    if not signals:
        st.markdown(
            f"""
            <div style="text-align:center; padding:60px 0; color:{COLOR_MUTED};">
                <div style="font-size:48px; margin-bottom:12px;">🌑</div>
                <div style="font-size:16px; font-weight:600;">No signals ingested yet</div>
                <div style="font-size:13px; margin-top:6px;">
                    Run the pipeline to start ingesting OSInt data.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        rows_html = ""
        for s in signals:
            source   = s.get("source_name", "UNKNOWN")
            title    = truncate(s.get("title") or s.get("raw_content", ""), 65)
            ingested = relative_time(s.get("ingested_at", ""))
            status   = s.get("processing_status", "PENDING")
            rows_html += f"""
            <tr>
                <td><span class="source-chip">{source}</span></td>
                <td class="signal-title">{title}</td>
                <td class="time-ago">{ingested}</td>
                <td>{status_badge(status)}</td>
            </tr>
            """

        st.markdown(
            f"""
            <div style="overflow-x:auto; max-height:580px; overflow-y:auto;
                        border: 1px solid {COLOR_BORDER}; border-radius: 12px;">
                <table class="ps-table">
                    <thead>
                        <tr>
                            <th>Source</th>
                            <th>Title / Content</th>
                            <th>Ingested</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_chart:
    st.markdown(
        f"""
        <div class="ps-section-header" style="margin-top:0;">
            <span class="ps-section-title">📊 Source Breakdown</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if signals:
        src_counter = Counter(s.get("source_name", "UNKNOWN") for s in signals)
        sources     = list(src_counter.keys())
        counts      = list(src_counter.values())

        # Sort descending
        pairs  = sorted(zip(counts, sources), reverse=True)
        counts = [p[0] for p in pairs]
        sources = [p[1] for p in pairs]

        bar_colors = [COLOR_TEAL] * len(sources)

        fig = go.Figure(
            go.Bar(
                x=counts,
                y=sources,
                orientation="h",
                marker=dict(
                    color=bar_colors,
                    line=dict(color="rgba(2,128,144,0.3)", width=1),
                ),
                text=counts,
                textposition="outside",
                textfont=dict(color="#8FA3BF", size=11),
                hovertemplate="<b>%{y}</b><br>Signals: %{x}<extra></extra>",
            )
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=30, t=10, b=10),
            height=300,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(30,58,95,0.5)",
                color="#8FA3BF",
                tickfont=dict(size=10),
                zeroline=False,
            ),
            yaxis=dict(
                color="#8FA3BF",
                tickfont=dict(size=11),
                automargin=True,
            ),
            font=dict(family="Inter, Segoe UI, sans-serif", color="#8FA3BF"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Status distribution donut
        st.markdown(
            f"""
            <div class="ps-section-header" style="margin-top:8px;">
                <span class="ps-section-title">🔵 Status Mix</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        status_labels = list(status_counts.keys())
        status_values = list(status_counts.values())
        status_color_map = {
            "PENDING":    "#6B7280",
            "NORMALIZED": "#3B82F6",
            "ALERTED":    "#DC2626",
            "DISCARDED":  "#374151",
            "FILTERED":   "#8B5CF6",
        }
        donut_colors = [status_color_map.get(s, COLOR_TEAL) for s in status_labels]

        fig2 = go.Figure(
            go.Pie(
                labels=status_labels,
                values=status_values,
                hole=0.6,
                marker=dict(colors=donut_colors, line=dict(color=COLOR_BG, width=2)),
                textinfo="percent",
                textfont=dict(size=11, color="#E8EDF5"),
                hovertemplate="<b>%{label}</b><br>%{value} signals (%{percent})<extra></extra>",
            )
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=220,
            showlegend=True,
            legend=dict(
                font=dict(size=10, color="#8FA3BF"),
                bgcolor="rgba(0,0,0,0)",
                orientation="v",
                x=1, y=0.5,
            ),
            font=dict(family="Inter, Segoe UI, sans-serif"),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown(
            f"""
            <div style="text-align:center; padding:40px 0; color:{COLOR_MUTED}; font-size:13px;">
                No data to chart yet.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="margin-top:40px; padding:16px 0; border-top:1px solid {COLOR_BORDER};
                text-align:center; color:{COLOR_MUTED}; font-size:11px; letter-spacing:0.5px;">
        🛡️ PHANTOM SIGNAL &nbsp;·&nbsp; OSInt Early Warning Framework &nbsp;·&nbsp;
        Auto-refreshes on interaction &nbsp;·&nbsp; <em>All data sourced from public intelligence feeds</em>
    </div>
    """,
    unsafe_allow_html=True,
)
