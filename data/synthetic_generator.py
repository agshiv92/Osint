"""
Phantom Signal — Synthetic Data Generator (PRD-003)
Generates reproducible mock customer personas, TM rules, and fraud history.
"""
import random
import uuid
import logging
from datetime import datetime, timedelta

from config import RANDOM_SEED
from data.database import (
    insert_customer_personas, insert_tm_rules, insert_fraud_history,
    is_seeded, mark_seeded,
)

logger = logging.getLogger(__name__)

rng = random.Random(RANDOM_SEED)


# ── Persona Dataset ───────────────────────────────────────────────────────────

PERSONA_SPECS = [
    # segment, sub_segment, geography, auth_method, avg_txn_sgd, digital_usage, population, risk
    ("RETAIL", "Mass Retail",   "SG", "SMS_OTP",      500,    "HIGH",   180_000, "LOW"),
    ("RETAIL", "Mass Affluent", "SG", "APP_OTP",      3_000,  "HIGH",    60_000, "LOW"),
    ("RETAIL", "Priority",      "SG", "DEVICE_BOUND", 12_000, "HIGH",    15_000, "LOW"),
    ("RETAIL", "Mass Retail",   "MY", "SMS_OTP",      800,    "MEDIUM",  85_000, "LOW"),
    ("RETAIL", "Mass Retail",   "TH", "SMS_OTP",      600,    "MEDIUM",  40_000, "LOW"),
    ("RETAIL", "Mass Retail",   "ID", "SMS_OTP",      400,    "LOW",     55_000, "MEDIUM"),
    ("SME",    "Small Business","SG", "APP_OTP",      8_000,  "MEDIUM",  30_000, "MEDIUM"),
    ("SME",    "Mid-Market",    "SG", "DEVICE_BOUND", 45_000, "MEDIUM",  12_000, "MEDIUM"),
    ("TRADE_FINANCE",  "Commodity",    "SG", "DEVICE_BOUND", 250_000, "LOW",  3_000, "HIGH"),
    ("TRADE_FINANCE",  "Import/Export","SG", "DEVICE_BOUND", 120_000, "LOW",  8_000, "HIGH"),
    ("CORRESPONDENT_BANKING", "International", "SG", "DEVICE_BOUND", 1_000_000, "LOW", 2_000, "HIGH"),
]

AGE_BANDS = ["18-25","26-35","36-45","46-55","56+"]
AGE_WEIGHTS = [0.12, 0.28, 0.25, 0.20, 0.15]


def generate_personas() -> list:
    personas = []
    for spec in PERSONA_SPECS:
        segment, sub_seg, geo, auth, avg_txn, digital, pop, risk = spec
        # For retail, add age band breakdown
        if segment == "RETAIL":
            for age, weight in zip(AGE_BANDS, AGE_WEIGHTS):
                personas.append({
                    "persona_id": str(uuid.UUID(int=rng.getrandbits(128))),
                    "segment": segment,
                    "sub_segment": sub_seg,
                    "geography": geo,
                    "age_band": age,
                    "digital_channel_usage": digital,
                    "auth_method": auth,
                    "avg_transaction_amount_sgd": avg_txn * rng.uniform(0.8, 1.2),
                    "monthly_transaction_count": rng.randint(5, 25),
                    "risk_rating": risk,
                    "population_count": int(pop * weight),
                })
        else:
            personas.append({
                "persona_id": str(uuid.UUID(int=rng.getrandbits(128))),
                "segment": segment,
                "sub_segment": sub_seg,
                "geography": geo,
                "age_band": "26-55",
                "digital_channel_usage": digital,
                "auth_method": auth,
                "avg_transaction_amount_sgd": avg_txn,
                "monthly_transaction_count": rng.randint(3, 30),
                "risk_rating": risk,
                "population_count": pop,
            })
    return personas


# ── TM Rules ──────────────────────────────────────────────────────────────────

BASE_TM_RULES = [
    {
        "rule_id": "TM-001", "rule_name": "High-value new payee",
        "fraud_typologies_targeted": ["SMS_SPOOFING","PHISHING_EMAIL","ACCOUNT_TAKEOVER"],
        "detection_trigger": "Large transfers to first-time payees",
        "threshold_description": "Transfer > SGD 5,000 to payee added within 24h",
        "channel_coverage": ["MOBILE","INTERNET_BANKING"],
        "estimated_catch_rate_pct": 45.0,
    },
    {
        "rule_id": "TM-002", "rule_name": "Rapid sequential transfers",
        "fraud_typologies_targeted": ["SMS_SPOOFING","BEC_CEO_FRAUD","E_COMMERCE_FRAUD"],
        "detection_trigger": "Multiple transfers in 24h exceeding threshold",
        "threshold_description": "> 3 transfers totalling > SGD 10,000 in 24h",
        "channel_coverage": ["MOBILE","INTERNET_BANKING","ATM"],
        "estimated_catch_rate_pct": 62.0,
    },
    {
        "rule_id": "TM-003", "rule_name": "Crypto exchange detection",
        "fraud_typologies_targeted": ["INVESTMENT_SCAM","CRYPTO_FRAUD","ROMANCE_SCAM"],
        "detection_trigger": "Transfers to known crypto platforms",
        "threshold_description": "Any transfer to known crypto exchange wallet/platform",
        "channel_coverage": ["MOBILE","INTERNET_BANKING"],
        "estimated_catch_rate_pct": 70.0,
    },
    {
        "rule_id": "TM-004", "rule_name": "Overseas wire anomaly",
        "fraud_typologies_targeted": ["BEC_CEO_FRAUD","TRADE_BASED_MONEY_LAUNDERING"],
        "detection_trigger": "Unusual cross-border transfer pattern",
        "threshold_description": "Overseas wire > 200% of 90-day average",
        "channel_coverage": ["INTERNET_BANKING"],
        "estimated_catch_rate_pct": 55.0,
    },
    {
        "rule_id": "TM-005", "rule_name": "Account takeover indicators",
        "fraud_typologies_targeted": ["ACCOUNT_TAKEOVER","SIM_SWAP","CREDENTIAL_STUFFING"],
        "detection_trigger": "Login from new device + immediate transfer",
        "threshold_description": "New device login followed by transfer within 1h",
        "channel_coverage": ["MOBILE","INTERNET_BANKING"],
        "estimated_catch_rate_pct": 78.0,
    },
    {
        "rule_id": "TM-006", "rule_name": "Night-time high-value",
        "fraud_typologies_targeted": ["SMS_SPOOFING","ACCOUNT_TAKEOVER"],
        "detection_trigger": "Transfers > SGD 5,000 between 10PM–5AM",
        "threshold_description": "High-value transfer during overnight hours",
        "channel_coverage": ["MOBILE","INTERNET_BANKING"],
        "estimated_catch_rate_pct": 35.0,
    },
    {
        "rule_id": "TM-007", "rule_name": "Structured transactions",
        "fraud_typologies_targeted": ["TRADE_BASED_MONEY_LAUNDERING","SYNTHETIC_IDENTITY"],
        "detection_trigger": "Multiple sub-threshold transfers",
        "threshold_description": "> 5 transfers each slightly below SGD 5,000 in 7 days",
        "channel_coverage": ["MOBILE","INTERNET_BANKING","BRANCH"],
        "estimated_catch_rate_pct": 60.0,
    },
    {
        "rule_id": "TM-008", "rule_name": "Gift card purchase pattern",
        "fraud_typologies_targeted": ["INVESTMENT_SCAM","ROMANCE_SCAM","VISHING"],
        "detection_trigger": "Repeated gift card top-ups",
        "threshold_description": "> 3 gift card purchases in 7 days",
        "channel_coverage": ["MOBILE","INTERNET_BANKING"],
        "estimated_catch_rate_pct": 40.0,
    },
    {
        "rule_id": "TM-009", "rule_name": "Invoice discrepancy",
        "fraud_typologies_targeted": ["TRADE_BASED_MONEY_LAUNDERING","BEC_CEO_FRAUD"],
        "detection_trigger": "Trade finance invoices > 20% above market rate",
        "threshold_description": "Invoice value deviates > 20% from market benchmark",
        "channel_coverage": ["INTERNET_BANKING"],
        "estimated_catch_rate_pct": 50.0,
    },
    {
        "rule_id": "TM-010", "rule_name": "PEP transaction monitoring",
        "fraud_typologies_targeted": ["TRADE_BASED_MONEY_LAUNDERING","INSIDER_THREAT"],
        "detection_trigger": "Any transfer involving PEP-linked accounts",
        "threshold_description": "Transaction involving politically exposed persons",
        "channel_coverage": ["MOBILE","INTERNET_BANKING","BRANCH"],
        "estimated_catch_rate_pct": 90.0,
    },
]

ADDITIONAL_RULE_TEMPLATES = [
    ("Dormant account reactivation", ["ACCOUNT_TAKEOVER","SYNTHETIC_IDENTITY"], 45.0),
    ("Shell company transfer", ["TRADE_BASED_MONEY_LAUNDERING"], 38.0),
    ("Round number transfers", ["TRADE_BASED_MONEY_LAUNDERING","E_COMMERCE_FRAUD"], 30.0),
    ("Geographic anomaly", ["ACCOUNT_TAKEOVER","CREDENTIAL_STUFFING"], 52.0),
    ("Velocity spike", ["CREDENTIAL_STUFFING","E_COMMERCE_FRAUD"], 58.0),
    ("High-risk country transfer", ["TRADE_BASED_MONEY_LAUNDERING","BEC_CEO_FRAUD"], 65.0),
    ("Mule account pattern", ["SMS_SPOOFING","INVESTMENT_SCAM"], 42.0),
    ("BEC payment redirect", ["BEC_CEO_FRAUD","DEEPFAKE_CFO_FRAUD"], 55.0),
    ("SIM change + transfer", ["SIM_SWAP","ACCOUNT_TAKEOVER"], 72.0),
    ("Crypto conversion chain", ["RANSOMWARE_FINANCIAL","CRYPTO_FRAUD"], 48.0),
    ("Charity/donation scam", ["INVESTMENT_SCAM","ROMANCE_SCAM"], 28.0),
    ("Payroll diversion", ["BEC_CEO_FRAUD","INSIDER_THREAT"], 35.0),
    ("Trade loan anomaly", ["TRADE_BASED_MONEY_LAUNDERING"], 44.0),
    ("ATM jackpotting attempt", ["ACCOUNT_TAKEOVER"], 80.0),
    ("Synthetic ID opening", ["SYNTHETIC_IDENTITY"], 25.0),
]


def generate_tm_rules() -> list:
    rules = []
    for r in BASE_TM_RULES:
        rules.append({**r, "last_updated": "2024-01-15", "active": True})
    for i, (name, typologies, catch_rate) in enumerate(ADDITIONAL_RULE_TEMPLATES, start=11):
        rules.append({
            "rule_id": f"TM-{i:03d}",
            "rule_name": name,
            "fraud_typologies_targeted": typologies,
            "detection_trigger": f"Automated detection: {name.lower()}",
            "threshold_description": f"Threshold-based detection for {name.lower()} pattern",
            "channel_coverage": rng.sample(["MOBILE","INTERNET_BANKING","BRANCH","ATM"], k=rng.randint(1,3)),
            "estimated_catch_rate_pct": catch_rate + rng.uniform(-5, 5),
            "last_updated": f"2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}",
            "active": True,
        })
    return rules


# ── Fraud History ─────────────────────────────────────────────────────────────

HISTORY_DISTRIBUTION = [
    ("SMS_SPOOFING",     0.35),
    ("INVESTMENT_SCAM",  0.20),
    ("E_COMMERCE_FRAUD", 0.15),
    ("ACCOUNT_TAKEOVER", 0.12),
    ("SIM_SWAP",         0.08),
    ("BEC_CEO_FRAUD",    0.07),
    ("CRYPTO_FRAUD",     0.03),
]

MEAN_LOSS_SGD = 4_500
STD_LOSS_SGD  = 8_000
MAX_LOSS_SGD  = 200_000


def _log_normal_loss() -> float:
    import math
    sigma = 0.8
    mu = math.log(MEAN_LOSS_SGD) - (sigma**2) / 2
    val = rng.lognormvariate(mu, sigma)
    return min(val, MAX_LOSS_SGD)


def generate_fraud_history(n: int = 500) -> list:
    incidents = []
    base_date = datetime(2023, 1, 1)
    typology_weights = [(t, w) for t, w in HISTORY_DISTRIBUTION]
    typologies = [t for t, _ in typology_weights]
    weights = [w for _, w in typology_weights]

    for i in range(n):
        typology = rng.choices(typologies, weights=weights, k=1)[0]
        detection_date = base_date + timedelta(days=rng.randint(0, 500))
        loss = _log_normal_loss()
        recovered = rng.random() < 0.15
        recovery = loss * rng.uniform(0.1, 0.6) if recovered else 0.0
        segment = rng.choices(
            ["RETAIL","SME","TRADE_FINANCE"],
            weights=[0.70, 0.20, 0.10], k=1
        )[0]
        geo = rng.choices(["SG","MY","TH","ID"], weights=[0.60,0.20,0.12,0.08], k=1)[0]
        incidents.append({
            "incident_id": str(uuid.UUID(int=rng.getrandbits(128))),
            "fraud_typology": typology,
            "detection_date": detection_date.strftime("%Y-%m-%d"),
            "loss_amount_sgd": round(loss, 2),
            "customer_segment": segment,
            "geography": geo,
            "detection_method": rng.choice(["TM_RULE","CUSTOMER_REPORT","MANUAL_REVIEW"]),
            "resolution_days": rng.randint(5, 90),
            "was_recovered": recovered,
            "recovery_amount_sgd": round(recovery, 2),
        })
    return incidents


# ── Vulnerability Matrix ──────────────────────────────────────────────────────

VULNERABILITY_MATRIX = {
    "SMS_SPOOFING": {
        "vulnerable_segments": ["RETAIL"],
        "vulnerable_auth_methods": ["SMS_OTP"],
        "highest_exposure_geos": ["SG","MY"],
        "baseline_attack_success_pct": 12.0,
        "tm_rules_covering": ["TM-001","TM-006"],
    },
    "SIM_SWAP": {
        "vulnerable_segments": ["RETAIL"],
        "vulnerable_auth_methods": ["SMS_OTP"],
        "highest_exposure_geos": ["SG","MY","ID"],
        "baseline_attack_success_pct": 8.0,
        "tm_rules_covering": ["TM-005","TM-019"],
    },
    "SEXTORTION": {
        "vulnerable_segments": ["RETAIL"],
        "vulnerable_auth_methods": ["SMS_OTP","APP_OTP"],
        "highest_exposure_geos": ["SG","TH","ID"],
        "baseline_attack_success_pct": 5.0,
        "tm_rules_covering": [],
    },
    "DEEPFAKE_CFO_FRAUD": {
        "vulnerable_segments": ["TRADE_FINANCE","SME"],
        "vulnerable_auth_methods": ["DEVICE_BOUND","APP_OTP"],
        "highest_exposure_geos": ["SG","HK"],
        "baseline_attack_success_pct": 3.0,
        "tm_rules_covering": ["TM-008"],
    },
    "INVESTMENT_SCAM": {
        "vulnerable_segments": ["RETAIL"],
        "vulnerable_auth_methods": ["SMS_OTP","APP_OTP"],
        "highest_exposure_geos": ["SG","MY"],
        "baseline_attack_success_pct": 18.0,
        "tm_rules_covering": ["TM-003","TM-008"],
    },
    "BEC_CEO_FRAUD": {
        "vulnerable_segments": ["SME","TRADE_FINANCE"],
        "vulnerable_auth_methods": ["APP_OTP","DEVICE_BOUND"],
        "highest_exposure_geos": ["SG","HK"],
        "baseline_attack_success_pct": 4.0,
        "tm_rules_covering": ["TM-004","TM-012"],
    },
    "ACCOUNT_TAKEOVER": {
        "vulnerable_segments": ["RETAIL","SME"],
        "vulnerable_auth_methods": ["SMS_OTP"],
        "highest_exposure_geos": ["SG","MY","ID"],
        "baseline_attack_success_pct": 10.0,
        "tm_rules_covering": ["TM-005","TM-006"],
    },
    "PHISHING_EMAIL": {
        "vulnerable_segments": ["RETAIL","SME"],
        "vulnerable_auth_methods": ["SMS_OTP","APP_OTP"],
        "highest_exposure_geos": ["SG","MY"],
        "baseline_attack_success_pct": 14.0,
        "tm_rules_covering": ["TM-001","TM-002"],
    },
    "CRYPTO_FRAUD": {
        "vulnerable_segments": ["RETAIL"],
        "vulnerable_auth_methods": ["SMS_OTP","APP_OTP"],
        "highest_exposure_geos": ["SG"],
        "baseline_attack_success_pct": 8.0,
        "tm_rules_covering": ["TM-003"],
    },
    "ROMANCE_SCAM": {
        "vulnerable_segments": ["RETAIL"],
        "vulnerable_auth_methods": ["SMS_OTP"],
        "highest_exposure_geos": ["SG","MY"],
        "baseline_attack_success_pct": 6.0,
        "tm_rules_covering": ["TM-003","TM-008"],
    },
}


def get_vulnerability_matrix() -> dict:
    return VULNERABILITY_MATRIX


# ── Main Entry Point ──────────────────────────────────────────────────────────

def generate_all_synthetic_data():
    """Generate and persist all synthetic data. Safe to call multiple times."""
    if not is_seeded("synthetic_personas"):
        logger.info("Generating synthetic customer personas...")
        personas = generate_personas()
        insert_customer_personas(personas)
        mark_seeded("synthetic_personas")
        logger.info("Generated %d persona records", len(personas))

    if not is_seeded("synthetic_tm_rules"):
        logger.info("Generating synthetic TM rules...")
        rules = generate_tm_rules()
        insert_tm_rules(rules)
        mark_seeded("synthetic_tm_rules")
        logger.info("Generated %d TM rules", len(rules))

    if not is_seeded("synthetic_fraud_history"):
        logger.info("Generating synthetic fraud history...")
        incidents = generate_fraud_history(500)
        insert_fraud_history(incidents)
        mark_seeded("synthetic_fraud_history")
        logger.info("Generated %d fraud history records", len(incidents))
