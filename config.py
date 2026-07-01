"""
Phantom Signal — App Configuration
All constants, paths, and thresholds referenced across the system.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Base Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ALERTS_DIR = DATA_DIR / "alerts"
RAW_DIR = DATA_DIR / "raw"

for d in [DATA_DIR, ALERTS_DIR, RAW_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Storage ───────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(DATA_DIR, "phantom_signal.db")
FIREBASE_CREDENTIALS = os.path.join(BASE_DIR, "firebase_key.json")

# ── External APIs & Gemini ───────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_FLASH_MODEL = "gemini-2.5-flash"
GEMINI_MAX_CALLS_PER_MINUTE = 60
GEMINI_BATCH_SIZE = 20

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

# ── Brand Colors ─────────────────────────────────────────────────────────────
COLOR_NAVY      = "#0D1B3E"
COLOR_TEAL      = "#028090"
COLOR_TEAL_DARK = "#016070"
COLOR_BG        = "#060D1F"
COLOR_SURFACE   = "#0D1B3E"
COLOR_SURFACE2  = "#112244"
COLOR_BORDER    = "#1E3A5F"
COLOR_TEXT      = "#E8EDF5"
COLOR_MUTED     = "#8FA3BF"

COLOR_CRITICAL  = "#DC2626"
COLOR_HIGH      = "#EA580C"
COLOR_MEDIUM    = "#D97706"
COLOR_LOW       = "#16A34A"

PRIORITY_COLORS = {
    "CRITICAL": COLOR_CRITICAL,
    "HIGH":     COLOR_HIGH,
    "MEDIUM":   COLOR_MEDIUM,
    "LOW":      COLOR_LOW,
}

STATUS_COLORS = {
    "PENDING":    "#6B7280",
    "NORMALIZED": "#3B82F6",
    "FILTERED":   "#8B5CF6",
    "ALERTED":    "#DC2626",
    "DISCARDED":  "#374151",
}

# ── Gate Thresholds ──────────────────────────────────────────────────────────
GATE1_THRESHOLD = 20
GATE2_THRESHOLD = 40
GATE3_THRESHOLD = 35

# ── Priority Score Thresholds ─────────────────────────────────────────────────
PRIORITY_THRESHOLDS = {
    "CRITICAL": 80,
    "HIGH":     60,
    "MEDIUM":   40,
    "LOW":       0,
}

# ── Fraud Typologies ──────────────────────────────────────────────────────────
FRAUD_TYPOLOGIES = [
    "SMS_SPOOFING",
    "SIM_SWAP",
    "PHISHING_EMAIL",
    "VISHING",
    "SEXTORTION",
    "DEEPFAKE_CFO_FRAUD",
    "INVESTMENT_SCAM",
    "ROMANCE_SCAM",
    "ACCOUNT_TAKEOVER",
    "CREDENTIAL_STUFFING",
    "SYNTHETIC_IDENTITY",
    "TRADE_BASED_MONEY_LAUNDERING",
    "BEC_CEO_FRAUD",
    "CRYPTO_FRAUD",
    "E_COMMERCE_FRAUD",
    "INSIDER_THREAT",
    "RANSOMWARE_FINANCIAL",
    "OTHER_EMERGING",
]

TYPOLOGY_LABELS = {
    "SMS_SPOOFING":               "SMS Spoofing",
    "SIM_SWAP":                   "SIM Swap",
    "PHISHING_EMAIL":             "Phishing (Email)",
    "VISHING":                    "Vishing",
    "SEXTORTION":                 "Sextortion",
    "DEEPFAKE_CFO_FRAUD":         "Deepfake CEO Fraud",
    "INVESTMENT_SCAM":            "Investment Scam",
    "ROMANCE_SCAM":               "Romance Scam",
    "ACCOUNT_TAKEOVER":           "Account Takeover",
    "CREDENTIAL_STUFFING":        "Credential Stuffing",
    "SYNTHETIC_IDENTITY":         "Synthetic Identity",
    "TRADE_BASED_MONEY_LAUNDERING": "Trade-Based ML",
    "BEC_CEO_FRAUD":              "BEC / CEO Fraud",
    "CRYPTO_FRAUD":               "Crypto Fraud",
    "E_COMMERCE_FRAUD":           "E-Commerce Fraud",
    "INSIDER_THREAT":             "Insider Threat",
    "RANSOMWARE_FINANCIAL":       "Ransomware (Financial)",
    "OTHER_EMERGING":             "Other / Emerging",
}

# ── Attack Reach Factors ──────────────────────────────────────────────────────
ATTACK_REACH_FACTORS = {
    "SMS_SPOOFING":        0.08,
    "SIM_SWAP":            0.03,
    "PHISHING_EMAIL":      0.12,
    "SEXTORTION":          0.05,
    "DEEPFAKE_CFO_FRAUD":  0.02,
    "VISHING":             0.04,
    "INVESTMENT_SCAM":     0.06,
    "ROMANCE_SCAM":        0.03,
    "ACCOUNT_TAKEOVER":    0.07,
    "CREDENTIAL_STUFFING": 0.10,
    "BEC_CEO_FRAUD":       0.02,
    "CRYPTO_FRAUD":        0.05,
}

# ── Default Loss Per Victim (SGD) ─────────────────────────────────────────────
DEFAULT_LOSS_PER_VICTIM = {
    "SMS_SPOOFING":        5_500,
    "SIM_SWAP":            8_000,
    "SEXTORTION":          3_000,
    "DEEPFAKE_CFO_FRAUD":  250_000,
    "PHISHING_EMAIL":      2_500,
    "VISHING":             4_000,
    "INVESTMENT_SCAM":     25_000,
    "ROMANCE_SCAM":        15_000,
    "ACCOUNT_TAKEOVER":    6_000,
    "BEC_CEO_FRAUD":       180_000,
    "CRYPTO_FRAUD":        12_000,
    "E_COMMERCE_FRAUD":    1_200,
    "CREDENTIAL_STUFFING": 3_500,
}

# ── UOB Geography Footprint ───────────────────────────────────────────────────
UOB_GEOGRAPHIES = ["SG", "MY", "TH", "ID", "HK", "CN", "VN"]

# ── OSInt Sources ─────────────────────────────────────────────────────────────
OSINT_SOURCES = [
    {"name": "NEWSAPI_CYBER", "url": "https://newsapi.org/v2/everything?q=fraud+OR+scam+OR+phishing+OR+cybercrime", "category": "OPEN_WEB"},
    {"name": "BLEEPING_COMPUTER_RSS", "url": "https://www.bleepingcomputer.com/feed/", "category": "OPEN_WEB"},
    {"name": "CYBER_SECURITY_NEWS_RSS", "url": "https://cybersecuritynews.com/feed/", "category": "OPEN_WEB"},
    {"name": "DARK_READING_RSS", "url": "https://www.darkreading.com/rss.xml", "category": "OPEN_WEB"},
    {"name": "SCAMWATCH_AU_RSS", "url": "https://www.scamwatch.gov.au/rss/feed", "category": "REGULATORY"},
    {"name": "SPF_ADVISORY",  "url": "https://www.police.gov.sg/Advisories/Scams",  "category": "REGULATORY"},
    {"name": "MAS_NEWS",      "url": "https://www.mas.gov.sg/news",                  "category": "REGULATORY"},
    {"name": "FBI_IC3",       "url": "https://www.ic3.gov/Media/News",               "category": "REGULATORY"},
    {"name": "ENISA",         "url": "https://www.enisa.europa.eu/publications",      "category": "REGULATORY"},
    {"name": "REDDIT_SCAMS",  "url": "https://www.reddit.com/r/Scams/new.json",      "category": "OPEN_WEB"},
]

# ── Keyword Filter Groups ─────────────────────────────────────────────────────
KEYWORD_GROUP_A = [
    "fraud", "scam", "phishing", "spoofing", "sextortion", "deepfake",
    "malware", "ransomware", "aml", "money laundering", "impersonation",
    "cybercrime", "breach", "hacker", "exploit", "stealer", "vulnerability",
    "trojan", "botnet", "mfa", "bypass", "smishing", "vishing",
]
KEYWORD_GROUP_B = [
    "bank", "banking", "financial", "payment", "transfer", "crypto",
    "account", "credential", "otp", "wire", "money", "fund", "wallet",
]
KEYWORD_GROUP_C = [
    "victim", "loss", "stolen", "compromised", "breach", "attack",
    "target", "threat", "risk", "damage", "extortion", "data",
]

# ── Reproducibility ───────────────────────────────────────────────────────────
RANDOM_SEED = 42
MONTE_CARLO_ITERATIONS = 1000

# ── Demo Scenario IDs (pre-seeded) ────────────────────────────────────────────
DEMO_SCENARIO_SMS     = "demo-sms-spoofing-2024"
DEMO_SCENARIO_SEXT    = "demo-sextortion-2024"
DEMO_SCENARIO_DEEPFAKE= "demo-deepfake-cfo-2024"

APP_TITLE = "Phantom Signal"
APP_SUBTITLE = "OSInt Early Warning Framework"
APP_VERSION = "v1.0 POC"
