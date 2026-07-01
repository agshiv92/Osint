"""
Phantom Signal — Page 6: 🕸️ Active Deception & Social Media POC
Showcases interactive scambaiting honeypots, credential feeding, and live social media scraping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import time
from datetime import datetime

from pipeline.active_deception import (
    simulate_baiting_chat,
    simulate_credential_feeding,
    scrape_mock_social_media,
    ingest_deception_signal,
)
from config import COLOR_BG, COLOR_SURFACE, COLOR_TEAL, COLOR_BORDER, COLOR_TEXT, COLOR_MUTED

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Active Deception POC · Phantom Signal",
    page_icon="🕸️",
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

    /* ── Page header ── */
    .ps-page-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 28px;
        padding: 24px 32px;
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 16px;
        background-image: linear-gradient(135deg, {COLOR_SURFACE} 0%, #081229 100%);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }}
    .ps-page-header-icon {{ font-size: 44px; }}
    .ps-page-header-title {{
        font-size: 26px;
        font-weight: 800;
        color: {COLOR_TEXT};
        margin: 0;
    }}
    .ps-page-header-sub {{
        font-size: 14px;
        color: {COLOR_MUTED};
        margin: 4px 0 0;
    }}
    .ps-live-dot {{
        display: inline-block;
        width: 10px; height: 10px;
        border-radius: 50%;
        background: #F59E0B;
        box-shadow: 0 0 0 3px rgba(245,158,11,0.25);
        animation: pulse 2s infinite;
        margin-right: 8px;
    }}
    @keyframes pulse {{
        0%   {{ box-shadow: 0 0 0 0 rgba(245,158,11,0.4); }}
        70%  {{ box-shadow: 0 0 0 10px rgba(245,158,11,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(245,158,11,0); }}
    }}

    /* ── Chat bubbles ── */
    .chat-container {{
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 20px;
        background: rgba(10, 20, 45, 0.6);
        border: 1px solid {COLOR_BORDER};
        border-radius: 16px;
        margin-bottom: 24px;
        max-height: 500px;
        overflow-y: auto;
    }}
    .chat-bubble {{
        max-width: 75%;
        padding: 14px 20px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.5;
        position: relative;
    }}
    .chat-victim {{
        align-self: flex-start;
        background: rgba(2, 128, 144, 0.2);
        border: 1px solid {COLOR_TEAL};
        color: #E8EDF5;
        border-bottom-left-radius: 4px;
    }}
    .chat-scammer {{
        align-self: flex-end;
        background: rgba(40, 50, 80, 0.7);
        border: 1px solid #4B5563;
        color: #F3F4F6;
        border-bottom-right-radius: 4px;
    }}
    .chat-meta {{
        font-size: 11px;
        font-weight: 700;
        color: {COLOR_MUTED};
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* ── Intelligence Card ── */
    .intel-card {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(13, 27, 62, 0.9) 100%);
        border: 1px solid #10B981;
        border-radius: 16px;
        padding: 24px;
        margin-top: 16px;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.15);
    }}
    .intel-title {{
        color: #10B981;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .intel-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 16px;
    }}
    .intel-item-label {{
        font-size: 11px;
        font-weight: 700;
        color: {COLOR_MUTED};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .intel-item-value {{
        font-size: 16px;
        font-weight: 700;
        color: #E8EDF5;
        margin-top: 4px;
    }}

    /* ── Social Media Card ── */
    .soc-card {{
        background: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease;
    }}
    .soc-card:hover {{
        transform: translateY(-2px);
        border-color: {COLOR_TEAL};
    }}
    .soc-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 12px;
    }}
    .soc-source {{
        background: rgba(59, 130, 246, 0.2);
        color: #60A5FA;
        border: 1px solid #3B82F6;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 10px;
        letter-spacing: 0.5px;
    }}
    .soc-author {{ font-weight: 700; color: #9CA3AF; }}
    .soc-time {{ color: {COLOR_MUTED}; font-style: italic; }}
    .soc-content {{ font-size: 14px; line-height: 1.6; color: #E8EDF5; margin-bottom: 16px; }}
    .soc-indicator-chip {{
        display: inline-block;
        background: rgba(220, 38, 38, 0.2);
        color: #FCA5A5;
        border: 1px solid #DC2626;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }}

    /* ── Streamlit overrides ── */
    .stButton > button {{
        background: linear-gradient(135deg, {COLOR_TEAL}, #016070);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        padding: 8px 20px;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
    }}
    .stButton > button:hover {{ opacity: 0.85; transform: translateY(-1px); }}
    div.block-container {{ padding-top: 1.5rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="ps-page-header">
        <div class="ps-page-header-icon">🕸️</div>
        <div>
            <p class="ps-page-header-title">
                <span class="ps-live-dot"></span>Active Deception & Social Media POC
            </p>
            <p class="ps-page-header-sub">
                Interactive Honeypots & Threat Feeds &nbsp;·&nbsp; <strong>Focus: Investment Scams</strong> &nbsp;·&nbsp; Powered by Gemini AI
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Session State Init ────────────────────────────────────────────────────────
if "bait_chat" not in st.session_state:
    st.session_state.bait_chat = []
if "extracted_mule" not in st.session_state:
    st.session_state.extracted_mule = None
if "feeder_result" not in st.session_state:
    st.session_state.feeder_result = None

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "💬 1. Interactive Baiting Bot (Scam Baiting)", 
    "🎣 2. Phishing Decoy Feeder (Cred Feeding)", 
    "📱 3. Social Media Threat Monitor"
])

# ── TAB 1: Baiting Bot ────────────────────────────────────────────────────────
with tab1:
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h3 style="color: #E8EDF5; font-size: 18px; font-weight: 700; margin-bottom: 6px;">
                💬 Dual-Persona AI Scambaiting Simulation
            </h3>
            <p style="color: #8FA3BF; font-size: 14px; line-height: 1.5;">
                This module acts as an automated honeypot. It deploys an AI Decoy Bot ("Victim") to engage with an online 
                <strong>Investment Scammer</strong> offering fake AI/Crypto arbitrage returns. The bot keeps the scammer engaged 
                until they drop a bank account number (Mule Account) to receive the deposit.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_btn1, col_btn2, col_space = st.columns([3, 2, 5])
    with col_btn1:
        if st.button("⚡ Generate Next Baiting Turn", use_container_width=True, type="primary"):
            with st.spinner("Gemini AI simulating next chat turn..."):
                res = simulate_baiting_chat(st.session_state.bait_chat, "INVESTMENT_SCAM")
                
                # Append victim message
                st.session_state.bait_chat.append({
                    "sender": "🤖 AI Decoy Bot (Victim)",
                    "text": res["victim_message"],
                    "is_victim": True
                })
                # Append scammer message
                st.session_state.bait_chat.append({
                    "sender": "🦹 Syndicate Recruiter (Scammer)",
                    "text": res["scammer_message"],
                    "is_victim": False
                })
                
                if res.get("bank_account_extracted"):
                    st.session_state.extracted_mule = {
                        "account": res["bank_account_extracted"],
                        "bank": res["bank_name"],
                        "payee": res["payee_name"]
                    }
                st.rerun()
                
    with col_btn2:
        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.bait_chat = []
            st.session_state.extracted_mule = None
            st.rerun()

    # Render Chat History
    if not st.session_state.bait_chat:
        st.markdown(
            f"""
            <div style="text-align:center; padding:60px 0; background:rgba(10,20,45,0.4); border:1px solid {COLOR_BORDER}; border-radius:16px; color:{COLOR_MUTED}; margin-top:16px;">
                <div style="font-size:48px; margin-bottom:12px;">💬</div>
                <div style="font-size:16px; font-weight:600;">Chat Simulation Idle</div>
                <div style="font-size:13px; margin-top:6px;">
                    Click <strong>'⚡ Generate Next Baiting Turn'</strong> above to initiate the conversation with the investment scammer.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        chat_html = ""
        for msg in st.session_state.bait_chat:
            bubble_class = "chat-victim" if msg["is_victim"] else "chat-scammer"
            sender_name = msg["sender"]
            text = msg["text"].replace("\n", "<br>")
            chat_html += f"""
            <div class="chat-bubble {bubble_class}">
                <div class="chat-meta">{sender_name}</div>
                <div>{text}</div>
            </div>
            """
        
        st.markdown(
            f"""
            <div class="chat-container">
                {chat_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render Extracted Threat Intel Card
    if st.session_state.extracted_mule:
        mule = st.session_state.extracted_mule
        st.markdown(
            f"""
            <div class="intel-card">
                <div class="intel-title">
                    🎯 Threat Intelligence Extracted: Mule Account Identified!
                </div>
                <p style="color: #8FA3BF; font-size: 13px; margin: 0;">
                    The AI Decoy Bot successfully deceived the scammer into revealing their Singapore deposit clearing account.
                </p>
                <div class="intel-grid">
                    <div>
                        <div class="intel-item-label">Bank Name</div>
                        <div class="intel-item-value">{mule['bank']}</div>
                    </div>
                    <div>
                        <div class="intel-item-label">Account Number</div>
                        <div class="intel-item-value" style="color: #10B981; font-size: 18px;">{mule['account']}</div>
                    </div>
                    <div>
                        <div class="intel-item-label">Beneficiary Name</div>
                        <div class="intel-item-value">{mule['payee']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_push, col_sp = st.columns([3, 7])
        with col_push:
            if st.button("📥 Send Extracted Intel to Live Feed Pipeline", key="push_bait", use_container_width=True, type="primary"):
                content = f"Targeted Investment Scam Mule Account detected via Active Deception Bot.\nBank: {mule['bank']}\nAccount: {mule['account']}\nPayee: {mule['payee']}\nScam Pitch: Apex Elite AI Trading 15% weekly returns."
                sig_id = ingest_deception_signal(
                    title=f"Mule Account Detected: {mule['bank']} ({mule['account']})",
                    content=content,
                    source_name="AI_BAITING_BOT"
                )
                st.success(f"Successfully injected into Phantom Signal engine! (Raw Signal ID: {sig_id})")

# ── TAB 2: Credential Feeder ──────────────────────────────────────────────────
with tab2:
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h3 style="color: #E8EDF5; font-size: 18px; font-weight: 700; margin-bottom: 6px;">
                🎣 Automated Phishing Decoy Feeder
            </h3>
            <p style="color: #8FA3BF; font-size: 14px; line-height: 1.5;">
                When a suspicious investment platform link is identified, Phantom Signal can deploy a <strong>Credential Feeder</strong>. 
                It floods the phishing portal with synthetic, highly realistic bank login credentials, rendering the scammers' stolen data 
                useless while tracing their backend server infrastructure (IP, Hosting ISP, Exfiltration API).
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_url, col_deploy = st.columns([4, 2])
    with col_url:
        phish_input = st.text_input("Target Phishing Portal URL:", value="https://apex-elite-ai-trading.vip/auth/login")
    with col_deploy:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Deploy Credential Feeder & Trace Backend", use_container_width=True, type="primary"):
            progress_bar = st.progress(0)
            status = st.empty()
            
            status.text("Initializing sandboxed headless browser...")
            progress_bar.progress(20)
            time.sleep(0.5)
            
            status.text("Generating 142 synthetic Singapore customer login profiles...")
            progress_bar.progress(50)
            time.sleep(0.8)
            
            status.text("Injecting mock credentials and analyzing reverse proxy routing...")
            progress_bar.progress(85)
            time.sleep(0.8)
            
            status.text("Traced exfiltration API payload! Finalizing IOC report...")
            progress_bar.progress(100)
            time.sleep(0.4)
            status.empty()
            progress_bar.empty()
            
            st.session_state.feeder_result = simulate_credential_feeding(phish_input)

    if st.session_state.feeder_result:
        feed = st.session_state.feeder_result
        actions_html = "".join([f"<li style='margin-bottom: 6px;'>{a}</li>" for a in feed['actions_taken']])
        
        st.markdown(
            f"""
            <div class="intel-card" style="border-color: #3B82F6; background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(13, 27, 62, 0.9) 100%);">
                <div class="intel-title" style="color: #3B82F6;">
                    🛡️ Mission Complete: Backend Infrastructure Infiltrated & Traced
                </div>
                <p style="color: #8FA3BF; font-size: 13px; margin: 0;">
                    Successfully flooded the target phishing portal with <strong>{feed['fake_credentials_injected']} synthetic credential sets</strong>.
                </p>
                <div class="intel-grid">
                    <div>
                        <div class="intel-item-label">Target Domain</div>
                        <div class="intel-item-value">{feed['domain']}</div>
                    </div>
                    <div>
                        <div class="intel-item-label">Backend Hosting IP</div>
                        <div class="intel-item-value" style="color: #3B82F6; font-size: 18px;">{feed['hosting_ip']}</div>
                    </div>
                    <div>
                        <div class="intel-item-label">ASN / ISP Provider</div>
                        <div class="intel-item-value">{feed['asn']}</div>
                    </div>
                    <div>
                        <div class="intel-item-label">Attack Mechanism</div>
                        <div class="intel-item-value">{feed['target_mechanism']}</div>
                    </div>
                </div>
                
                <div style="margin-top: 24px; border-top: 1px solid rgba(59, 130, 246, 0.3); padding-top: 16px;">
                    <div class="intel-item-label">Automated Defense Actions Executed</div>
                    <ul style="color: #E8EDF5; font-size: 13px; margin-top: 8px; padding-left: 20px;">
                        {actions_html}
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_push2, col_sp2 = st.columns([3, 7])
        with col_push2:
            if st.button("📥 Ingest Server IOCs to Live Feed Pipeline", key="push_feed", use_container_width=True, type="primary"):
                content = f"Phishing Server Backend Traced via Credential Feeder.\nDomain: {feed['domain']}\nIP: {feed['hosting_ip']}\nASN: {feed['asn']}\nMechanism: {feed['target_mechanism']}\nExfiltration API: {feed['exfiltration_endpoint']}"
                sig_id = ingest_deception_signal(
                    title=f"Phishing Backend Traced: {feed['domain']} ({feed['hosting_ip']})",
                    content=content,
                    source_name="CREDENTIAL_FEEDER",
                    url=feed['phishing_url']
                )
                st.success(f"Successfully injected into Phantom Signal engine! (Raw Signal ID: {sig_id})")

# ── TAB 3: Social Media Monitor ───────────────────────────────────────────────
with tab3:
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h3 style="color: #E8EDF5; font-size: 18px; font-weight: 700; margin-bottom: 6px;">
                📱 Real-Time Social Media Threat Monitor
            </h3>
            <p style="color: #8FA3BF; font-size: 14px; line-height: 1.5;">
                Continuous ingestion feeds scraping public Telegram fraud channels and X (Twitter) security feeds. 
                This allows Phantom Signal to catch emerging Investment Scam campaigns before official police advisories are published.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    soc_items = scrape_mock_social_media()
    
    for item in soc_items:
        indicators_html = "".join([f"<span class='soc-indicator-chip'>{i}</span>" for i in item['indicators']])
        
        st.markdown(
            f"""
            <div class="soc-card">
                <div class="soc-header">
                    <span class="soc-source">{item['source']}</span>
                    <span class="soc-author">{item['author']}</span>
                    <span class="soc-time">Scraped {item['time']}</span>
                </div>
                <div class="soc-content">
                    {item['content']}
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 11px; font-weight: 700; color: {COLOR_MUTED}; text-transform: uppercase; margin-right: 8px;">Extracted IOCs:</span>
                    {indicators_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col_send, col_rem = st.columns([2, 8])
        with col_send:
            if st.button(f"📥 Send to Phantom Signal Pipeline", key=f"send_{item['id']}", use_container_width=True):
                sig_id = ingest_deception_signal(
                    title=f"Social Media Alert: {item['author']}",
                    content=item['content'],
                    source_name=item['source'],
                )
                st.success(f"Injected! ID: {sig_id}")
        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
