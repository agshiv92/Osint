"""
Phantom Signal — Active Deception & Social Media Module
Proof of Concept (POC) demonstrating active threat engagement (honeypots)
and real-time social media intelligence harvesting for Investment Scams.
"""
import logging
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from utils.gemini_client import call_gemini_flash
from data.database import insert_raw_signal

logger = logging.getLogger(__name__)


def simulate_baiting_chat(chat_history: List[Dict], scam_type: str = "INVESTMENT_SCAM") -> Dict:
    """
    Simulates the next turn of a scambaiting conversation using Gemini AI.
    The goal is for the Decoy Bot (curious victim) to prompt the scammer to reveal a bank account number.
    """
    # System instructions for the simulation
    system_prompt = """You are a dual-persona AI simulation engine for a cybersecurity demonstration.
You are simulating a scambaiting interaction between a Decoy AI Bot ("Victim") and a Financial Scammer ("Scammer").

SCENARIO: INVESTMENT SCAM (High-Yield Crypto/AI Trading Platform Scam in Singapore).
The Scammer claims to represent 'Apex Elite AI Trading' offering 15% guaranteed weekly returns.
The Victim acts as an eager, slightly naive Singaporean investor looking to invest SGD 10,000.

Your task is to generate the NEXT TWO MESSAGES in the chat (one from Victim, one from Scammer).
If the chat history is short (under 2 turns), the Victim asks about how the investment works and how to deposit.
If the chat history is 2 turns or longer, the Victim insists on depositing immediately and asks for the bank account number. The Scammer MUST provide a specific Singapore bank account number (e.g. DBS or UOB account number, payee name, and bank name) to receive the funds.

Return ONLY a valid JSON object matching this schema:
{
  "victim_message": "string (what the decoy bot says)",
  "scammer_message": "string (what the scammer replies)",
  "bank_account_extracted": "string (the bank account number if revealed, else null)",
  "bank_name": "string (name of bank if revealed, else null)",
  "payee_name": "string (name of payee if revealed, else null)"
}"""

    # Prepare chat history context for Gemini
    history_text = ""
    for idx, msg in enumerate(chat_history):
        history_text += f"\n{msg['sender']}: {msg['text']}"
        
    user_prompt = f"""Current Chat History ({len(chat_history)} messages so far):
{history_text or '(Chat just starting. Generate initial introduction from Victim inquiring about the investment ad, and Scammer pitching the guaranteed returns.)'}

Generate the next turn in JSON."""

    try:
        response = call_gemini_flash(system_prompt, user_prompt, expect_json=True)
        if response and isinstance(response, dict):
            return response
    except Exception as e:
        logger.error(f"Error simulating baiting chat with Gemini: {e}")

    # Fallback mock response if Gemini fails or rate limits
    if len(chat_history) < 2:
        return {
            "victim_message": "Hi there! I saw your advertisement on Telegram about the AI Wealth Arbitrage trading. Is it really 15% weekly guaranteed return? I have some savings I want to invest.",
            "scammer_message": "Hello friend! Yes, absolutely. Our AI high-frequency trading bot exploits crypto arbitrage spreads across Asian exchanges. It is 100% risk-free and fully licensed. To start, you just need to open a VIP account with a minimum deposit of SGD 5,000.",
            "bank_account_extracted": None,
            "bank_name": None,
            "payee_name": None
        }
    else:
        return {
            "victim_message": "That sounds amazing! I want to deposit SGD 10,000 to get the VIP bonus right away. Please give me your bank account details so I can do a FAST transfer right now.",
            "scammer_message": "Excellent choice! Please make the FAST transfer of SGD 10,000 to our institutional custody account: \nBank: DBS Bank\nAccount Number: 003-928192-4\nAccount Name: Apex Elite Trading Assets Pte Ltd\n\nSend me the screenshot once done!",
            "bank_account_extracted": "003-928192-4",
            "bank_name": "DBS Bank",
            "payee_name": "Apex Elite Trading Assets Pte Ltd"
        }


def simulate_credential_feeding(phishing_url: str) -> Dict:
    """
    Simulates deploying an automated credential feeder to a suspicious investment phishing portal.
    Submits synthetic credentials and captures the backend server architecture.
    """
    domain = re.sub(r'https?://', '', phishing_url).split('/')[0]
    
    return {
        "phishing_url": phishing_url,
        "domain": domain,
        "hosting_ip": "103.142.55.12",
        "asn": "ASN 45102 (Offshore Secure Server Hosting)",
        "server_location": "Hong Kong / Regional Virtual Subnet",
        "target_mechanism": "Adversary-in-the-Middle (AiTM) Reverse Proxy",
        "exfiltration_endpoint": f"https://api.gateway-secure-route.info/v2/log_creds",
        "fake_credentials_injected": 142,
        "actions_taken": [
            "Generated 142 realistic synthetic Singapore customer profiles",
            "Automated headless browser submission with variable typing cadence",
            "Traced exfiltration API payload back to hosting server IP 103.142.55.12",
            "Added IP and Exfiltration Domain to UOB Web Application Firewall (WAF) blocklist"
        ],
        "confidence_score": 0.98
    }


def scrape_mock_social_media() -> List[Dict]:
    """
    Simulates a real-time feed of scraped social media threat intelligence
    from Telegram scam groups and X (Twitter) security researchers.
    """
    now = datetime.utcnow()
    return [
        {
            "id": "soc-001",
            "source": "TELEGRAM_SCRAPER",
            "author": "t.me/Crypto_Wealth_SG_Group",
            "time": (now - timedelta(minutes=4)).strftime("%H:%M:%S"),
            "content": "⚠️ ALERT FROM SCRAPER: Syndicate admin broadcasting new investment portal link: 'apex-elite-ai-trading.vip'. Offering 20% commission to money mules in Singapore with active UOB or DBS bank accounts.",
            "indicators": ["apex-elite-ai-trading.vip", "UOB mule recruitment", "20% commission"],
            "category": "INVESTMENT_SCAM"
        },
        {
            "id": "soc-002",
            "source": "X_THREAT_FEED",
            "author": "@SG_CyberIntel_Bot",
            "time": (now - timedelta(minutes=14)).strftime("%H:%M:%S"),
            "content": "🚨 New Investment Scam Campaign detected targeting Singapore residents via Instagram ads. Redirects to fake MAS-regulated trading platform 'Vanguard-Quant-AI.com'. Uses PayNow QR codes for deposit.",
            "indicators": ["Vanguard-Quant-AI.com", "Instagram Ad campaign", "PayNow QR spoofing"],
            "category": "INVESTMENT_SCAM"
        },
        {
            "id": "soc-003",
            "source": "TELEGRAM_SCRAPER",
            "author": "t.me/SG_Job_Seekers_Dark",
            "time": (now - timedelta(minutes=28)).strftime("%H:%M:%S"),
            "content": "Looking for active Singapore bank accounts (UOB, OCBC). Paying SGD 800 per day just to receive incoming investment trading deposits. PM @crypto_boss_sg for fast cash.",
            "indicators": ["Mule account solicitation", "@crypto_boss_sg", "SGD 800/day fee"],
            "category": "ACCOUNT_TAKEOVER"
        }
    ]


def ingest_deception_signal(title: str, content: str, source_name: str, url: str = "") -> str:
    """
    Ingests intelligence extracted from Active Deception directly into the Phantom Signal database.
    """
    sig_id = str(uuid.uuid4())
    signal = {
        "signal_id": sig_id,
        "ingested_at": datetime.utcnow().isoformat(),
        "source_category": "ACTIVE_DECEPTION" if "Baiting" in source_name or "Feeder" in source_name else "SOCIAL_MEDIA",
        "source_name": source_name,
        "source_url": url or f"https://phantom-signal.int/deception/{sig_id[:8]}",
        "raw_content": content,
        "title": title,
        "publication_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "language": "en",
        "processing_status": "PENDING",
    }
    insert_raw_signal(signal)
    return sig_id
