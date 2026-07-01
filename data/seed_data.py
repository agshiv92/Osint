"""
Phantom Signal — Pre-loaded Demo Seed Data
3 complete demo scenarios baked in for instant judge presentation.
No Gemini calls required — all data is pre-generated.
"""
import logging
from datetime import datetime

from data.database import (
    insert_raw_signal, insert_fraud_signal, insert_relevance_assessment,
    insert_simulation, insert_risk_alert, insert_intervention_rules,
    is_seeded, mark_seeded,
)
from utils.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

NOW = "2024-06-15T04:22:00"

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 1 — SMS Spoofing (CRITICAL)
# Based on OCBC 2021 / SPF advisory pattern
# ══════════════════════════════════════════════════════════════════════════════

S1_RAW = {
    "signal_id": "raw-sms-spoofing-001",
    "ingested_at": "2024-06-15T03:10:00",
    "source_category": "REGULATORY",
    "source_name": "SPF_ADVISORY",
    "source_url": "https://www.police.gov.sg/Advisories/Scams/advisory-sms-spoofing-2024",
    "raw_content": (
        "SPF Advisory: Surge in SMS Spoofing Scams Targeting Bank Customers. "
        "Members of public have reported receiving fake SMS messages that appear to come from their banks. "
        "Scammers are spoofing bank SMS sender IDs to trick victims into clicking malicious links that steal credentials. "
        "Over 460 victims reported losing at least S$8.5 million in first half of 2024. "
        "Victims are predominantly retail banking customers using SMS OTP authentication."
    ),
    "content_hash": "abc123sms001",
    "language": "en",
    "processing_status": "ALERTED",
    "title": "SPF: Surge in SMS Spoofing Scams Targeting Bank Customers",
    "publication_date": "2024-06-14",
}

S1_FRAUD = {
    "fraud_signal_id": "fs-sms-spoofing-001",
    "raw_signal_id": "raw-sms-spoofing-001",
    "detected_at": "2024-06-15T03:15:00",
    "fraud_typology": "SMS_SPOOFING",
    "fraud_description": (
        "Fraudsters are spoofing legitimate bank SMS sender IDs to send victims phishing links "
        "that harvest banking credentials. Once credentials are captured, attackers execute "
        "unauthorized transfers to money mule accounts, typically within minutes of compromise. "
        "The attack exploits customer trust in SMS bank notifications and the prevalence of SMS OTP as the primary authentication method."
    ),
    "attack_vector": "SMS phishing via spoofed bank sender ID → credential theft → unauthorized fund transfer",
    "victim_profile": {
        "age_range": "35-65",
        "customer_segment": "RETAIL",
        "geography": ["SG", "MY"],
        "channel": "MOBILE",
    },
    "financial_mechanism": "Credential theft via phishing link → login to IB portal → new payee creation → immediate fund transfer to mule account",
    "geographic_origin": ["SG"],
    "geographic_spread": ["SG", "MY", "TH"],
    "first_reported_globally": "2021-12-01",
    "severity_estimate": "CRITICAL",
    "novelty_score": 0.65,
    "confidence_score": 0.92,
    "source_credibility": "HIGH",
    "raw_evidence": "460 victims reported losing at least S$8.5 million in first half of 2024. Scammers spoofing bank SMS sender IDs.",
}

S1_ASSESSMENT = {
    "assessment_id": "ra-sms-spoofing-001",
    "fraud_signal_id": "fs-sms-spoofing-001",
    "assessed_at": "2024-06-15T03:22:00",
    "gate1_novelty": {
        "passed": True, "score": 72.0, "raw_score": 22.0,
        "existing_tm_rule_match": True,
        "similar_signal_ids": [],
        "explanation": "TM rules partially cover SMS spoofing but evolving attack vector exploits gaps in real-time detection; novelty score 0.65 indicates evolving threat",
        "reasons": [
            "Covered by TM-001, TM-006 but only at 45% and 35% catch rates",
            "No similar HIGH/CRITICAL signal in last 90 days",
            "Moderate-high novelty: attack vector evolving with spoofed sender IDs",
        ],
    },
    "gate2_customer_exposure": {
        "passed": True, "score": 95.0,
        "matched_segments": ["RETAIL"],
        "estimated_at_risk_customers": 180000,
        "geographic_overlap": True,
        "channel_overlap": True,
        "explanation": "✓ RETAIL customers in SG/MY; ~180,000 SMS_OTP users directly at risk",
        "reasons": [
            "Segment match: RETAIL (+35 pts)",
            "Singapore geography overlap (+30 pts)",
            "Channel overlap: MOBILE (+20 pts)",
            "High exposure: 180,000+ at-risk customers (+15 bonus pts)",
        ],
    },
    "gate3_control_gap": {
        "passed": True, "score": 78.0,
        "matched_tm_rules": ["TM-001", "TM-006"],
        "undetected_percentage": 65.5,
        "auth_vulnerability": True,
        "explanation": "✓ 65.5% of attacks undetected by existing TM rules; SMS OTP auth vulnerability: YES",
        "reasons": [
            "Covered by 2 rule(s) with avg catch rate 40%",
            "Significant control gap: 65.5% undetected (+30 pts)",
            "SMS_OTP auth vulnerability exploited by this attack (+25 pts)",
        ],
    },
    "overall_passed": True,
    "composite_risk_score": 84.2,
    "alert_priority": "CRITICAL",
    "recommended_actions": [
        "Issue advisory to 180,000 retail customers via push notification warning of SMS impersonation",
        "Submit new TM detection scenario to transaction monitoring team for SMS spoofing pattern",
        "Accelerate device binding rollout for retail segment OTP authentication",
        "Generate full Risk Alert Document for compliance review",
    ],
}

S1_SIMULATION = {
    "simulation_id": "sim-sms-spoofing-001",
    "fraud_signal_id": "fs-sms-spoofing-001",
    "run_at": "2024-06-15T03:25:00",
    "scenario_name": "SMS Spoofing — Singapore Retail Baseline",
    "customer_exposure": {
        "total_at_risk": 180000,
        "by_segment": {"RETAIL": 180000},
        "by_geography": {"SG": 140000, "MY": 40000},
    },
    "financial_impact": {
        "baseline_exposure_sgd": 14400000.0,
        "with_current_controls_sgd": 9720000.0,
        "with_proposed_controls_sgd": 3240000.0,
        "p10_sgd": 6200000.0,
        "p50_sgd": 12800000.0,
        "p90_sgd": 28500000.0,
        "methodology": (
            "Estimated 2,880 victims (180,000 at-risk × 8% reach factor × 20% conversion). "
            "Avg loss SGD 5,500/victim. Current controls catch 34.5% (partial prevention factor 0.7). "
            "Device binding intervention targets 67% additional reduction."
        ),
    },
    "control_gap_analysis": {
        "current_detection_rate_pct": 34.5,
        "undetected_rate_pct": 65.5,
        "failing_controls": [
            "TM-001 insufficient: only flags new payee transfers, misses credential-theft pre-staging",
            "TM-006 insufficient: night-time rule misses 60% of daytime attacks",
            "No real-time SMS anomaly detection in current stack",
        ],
    },
    "proposed_interventions": [
        {
            "intervention_type": "Device Binding Rollout",
            "description": "Migrate retail SMS_OTP users to device-bound authentication (target 60% of retail base within 90 days)",
            "estimated_reduction_pct": 45.0,
            "implementation_effort": "HIGH",
        },
        {
            "intervention_type": "Real-time SMS Anomaly Detection",
            "description": "Flag and challenge all transactions following SIM change or new device registration events",
            "estimated_reduction_pct": 28.0,
            "implementation_effort": "MEDIUM",
        },
    ],
    "estimated_victims": 2880,
    "victim_rate_pct": 20.0,
    "avg_loss_sgd": 5500.0,
}

S1_RULES = [
    {
        "rule_id": "rule-sms-tm-001",
        "fraud_signal_id": "fs-sms-spoofing-001",
        "rule_type": "TM_DETECTION",
        "target_layer": "TRANSACTION_MONITORING",
        "rule_description": (
            "Detect high-risk transaction sequences following suspicious login events: "
            "new device login + immediate new payee creation + transfer within 2 hours."
        ),
        "rule_logic": (
            "IF new_device_login = TRUE AND new_payee_added WITHIN 24h "
            "AND transfer_amount > SGD 1000 AND time_since_login < 2h "
            "THEN flag as SMS_SPOOFING_RISK with priority REVIEW"
        ),
        "trigger_conditions": [
            "New device login event detected",
            "New payee added within 24 hours of login",
            "Transfer amount > SGD 1,000",
            "Transaction within 2 hours of new device login",
        ],
        "expected_impact_pct": 25.0,
        "deployment_risk": "MEDIUM",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-sms-friction-001",
        "fraud_signal_id": "fs-sms-spoofing-001",
        "rule_type": "CUSTOMER_FRICTION",
        "target_layer": "AUTHENTICATION",
        "rule_description": (
            "Add biometric step-up authentication for retail customers transferring > SGD 2,000 "
            "to payees added within the past 48 hours."
        ),
        "rule_logic": (
            "IF customer_segment = RETAIL AND payee_age < 48h "
            "AND transfer_amount > SGD 2000 "
            "THEN require biometric re-authentication before processing"
        ),
        "trigger_conditions": [
            "Customer segment: RETAIL",
            "Transfer to payee added within 48 hours",
            "Transaction amount > SGD 2,000",
        ],
        "expected_impact_pct": 18.0,
        "deployment_risk": "HIGH",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-sms-policy-001",
        "fraud_signal_id": "fs-sms-spoofing-001",
        "rule_type": "POLICY_CHANGE",
        "target_layer": "POLICY",
        "rule_description": (
            "Establish a mandatory 30-minute cooling-off period for first-time transfers "
            "to new payees exceeding SGD 500 for retail SMS_OTP customers."
        ),
        "rule_logic": (
            "IF customer auth_method = SMS_OTP AND payee_is_new = TRUE "
            "AND transfer_amount > SGD 500 "
            "THEN enforce 30-minute cooling-off; customer can cancel during period"
        ),
        "trigger_conditions": [
            "Auth method: SMS_OTP",
            "First-time payee",
            "Transfer > SGD 500",
        ],
        "expected_impact_pct": 32.0,
        "deployment_risk": "MEDIUM",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-sms-advisory-001",
        "fraud_signal_id": "fs-sms-spoofing-001",
        "rule_type": "ADVISORY",
        "target_layer": "CUSTOMER_COMMS",
        "rule_description": (
            "Issue immediate push notification and in-app alert to all retail customers "
            "warning of active SMS spoofing campaign impersonating UOB."
        ),
        "rule_logic": (
            "IF customer_segment IN [RETAIL] AND geography IN [SG, MY] "
            "THEN send push_notification + in_app_banner + email_advisory WITHIN 24h"
        ),
        "trigger_conditions": [
            "Active SMS spoofing threat confirmed (CRITICAL priority)",
            "Customer segment: RETAIL",
            "Geography: SG, MY",
        ],
        "expected_impact_pct": 12.0,
        "deployment_risk": "LOW",
        "approval_required": False,
        "auto_deployable": True,
    },
]

S1_ALERT = {
    "alert_id": "alert-sms-spoofing-001",
    "fraud_signal_id": "fs-sms-spoofing-001",
    "assessment_id": "ra-sms-spoofing-001",
    "simulation_id": "sim-sms-spoofing-001",
    "generated_at": "2024-06-15T04:00:00",
    "priority": "CRITICAL",
    "document": {
        "executive_summary": (
            "A CRITICAL-priority SMS Spoofing threat has been identified targeting UOB's retail customer base in Singapore and Malaysia. "
            "Approximately 180,000 customers using SMS OTP authentication are directly at risk, with estimated unmitigated financial exposure of SGD 6.2M–28.5M (P10–P90 range). "
            "Current transaction monitoring controls detect only 34.5% of attack instances, leaving a significant operational gap. "
            "Immediate action required: issue customer advisory within 24 hours and accelerate device binding rollout to reduce dependency on vulnerable SMS OTP authentication."
        ),
        "threat_description": (
            "SMS Spoofing attacks exploit telecommunications infrastructure to forge the sender ID of legitimate bank SMS messages. "
            "The attack sequence is: (1) Fraudster spoofs UOB SMS sender ID → (2) Victim receives fake security alert with phishing link → "
            "(3) Victim enters credentials on fake bank portal → (4) Attacker uses stolen credentials to log in via new device → "
            "(5) New payee added and immediate wire transfer executed to money mule account. "
            "This attack pattern was first documented at scale during the OCBC incident (December 2021, Singapore) where 790 victims lost SGD 13.7M. "
            "The SPF has reported a resurgence in 2024 with at least 460 victims and SGD 8.5M in losses in the first half alone. "
            "The attack is escalating because: (a) SMS sender ID spoofing tools are now commercially available, "
            "(b) customers remain highly trusting of SMS notifications, and (c) SMS OTP remains the dominant auth method for retail banking."
        ),
        "uob_relevance": (
            "UOB's retail segment has 180,000+ customers in Singapore using SMS OTP authentication — the primary vulnerable population for this attack. "
            "UOB's existing TM rules (TM-001, TM-006) provide only partial coverage: TM-001 catches 45% of new-payee high-value transfers but misses "
            "the credential-theft pre-staging phase, and TM-006 only covers night-time transactions (60% of attacks occur during business hours). "
            "The composite risk score of 84.2/100 confirms CRITICAL classification. "
            "Without intervention, UOB's estimated exposure is SGD 12.8M (P50) with a worst-case of SGD 28.5M (P90)."
        ),
        "customer_impact": (
            "Primary at-risk population: 180,000 RETAIL customers in Singapore (140,000) and Malaysia (40,000) using SMS OTP authentication. "
            "Age concentration: 35–65 demographic (less digitally aware, higher balance accounts). "
            "Attack reach: approximately 2,880 customers contacted in a typical spoofing wave (8% reach factor). "
            "Expected victims without intervention: ~576 customers (20% conversion rate). "
            "Average loss per victim: SGD 5,500 (based on historical fraud data for this typology)."
        ),
        "financial_exposure": (
            "Baseline exposure (no intervention): SGD 14.4M. "
            "With current TM controls: SGD 9.7M (controls prevent ~32% of losses). "
            "With proposed interventions (device binding + SMS anomaly detection): SGD 3.2M. "
            "Monte Carlo sensitivity analysis (1,000 iterations): P10 = SGD 6.2M, P50 = SGD 12.8M, P90 = SGD 28.5M. "
            "UOB's estimated unmitigated exposure is SGD 6.2M–28.5M. "
            "Proposed intervention package reduces exposure by ~78% to SGD 3.2M."
        ),
        "current_control_gaps": (
            "Three critical control gaps identified: "
            "(1) TM-001 detects new payee transfers but has no visibility into the credential-theft phase preceding the transfer — "
            "attackers can pre-stage payees days in advance; "
            "(2) TM-006 (night-time rule) misses ~60% of SMS spoofing attacks which occur during business hours (9AM–6PM); "
            "(3) No real-time behavioral analytics currently flag the login-from-new-device + immediate-transfer sequence that characterizes this attack. "
            "Overall undetected rate: 65.5% of attacks."
        ),
        "recommended_actions": {
            "immediate": [
                "Issue push notification + in-app advisory to all 180,000 at-risk retail customers warning of active SMS impersonation campaign",
                "Activate enhanced monitoring on all new payee transfers with manual review for transactions > SGD 5,000",
                "Alert fraud operations team: increase staffing for next 72 hours to clear investigation queue",
                "Notify frontline relationship managers and branch staff to escalate any customer reports of suspicious SMS messages",
            ],
            "short_term": [
                "Submit TM detection scenario to analytics team: 'new device login + new payee + transfer within 2h' rule (est. 25% detection improvement)",
                "Implement 30-minute cooling-off period for first-time payee transfers > SGD 500 for SMS OTP customers",
                "Update UOB website and app with specific SMS spoofing guidance and example screenshots",
                "Brief call centre staff on escalation procedure for customers reporting suspicious SMS messages",
                "Coordinate with telco partners on SMS sender ID whitelist enforcement",
            ],
            "strategic": [
                "Accelerate device binding rollout: target 60% of retail base within 90 days (estimated 45% exposure reduction)",
                "Commission vendor assessment for real-time behavioral analytics platform to complement TM rules",
                "Develop formal SMS Spoofing incident response playbook with defined escalation triggers and recovery procedures",
            ],
        },
        "intervention_rules": S1_RULES,
        "simulation_summary": (
            "Monte Carlo simulation (1,000 iterations) over SGD baseline exposure scenarios: "
            "P10 = SGD 6.2M, P50 = SGD 12.8M, P90 = SGD 28.5M. "
            "Proposed device binding rollout + SMS anomaly detection reduces expected loss by ~78% to SGD 3.2M."
        ),
        "evidence_sources": [
            "Singapore Police Force Advisory — SMS Spoofing Surge 2024 (police.gov.sg)",
            "MAS Financial Stability Review 2024 — Digital Banking Fraud Trends",
            "OCBC Phishing Incident Report 2021 — 790 victims, SGD 13.7M losses (MAS case study)",
        ],
        "confidence_rating": "HIGH",
        "analyst_notes": (
            "This alert is AI-generated. It must be reviewed by a qualified fraud risk analyst before operational action is taken. "
            "Financial figures are derived from synthetic customer population data (500,000 persona dataset) and historical fraud simulation. "
            "No real UOB customer data was accessed or used in this analysis. "
            "Data confidence: 92%. "
            "Recommended review steps: (1) Verify current device binding adoption rate against the 180,000 at-risk population estimate; "
            "(2) Confirm TM-001 and TM-006 catch rates with TM Analytics team; "
            "(3) Cross-reference SGD 8.5M SPF-reported loss figure against internal fraud incident data."
        ),
    },
    "routing": {
        "compliance_team": True,
        "fraud_risk_team": True,
        "tm_analytics_team": True,
        "policy_controls_team": True,
    },
    "fraud_typology": "SMS_SPOOFING",
    "composite_score": 84.2,
}

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 2 — Sextortion Surge (HIGH)
# ══════════════════════════════════════════════════════════════════════════════

S2_RAW = {
    "signal_id": "raw-sextortion-001",
    "ingested_at": "2024-06-14T08:30:00",
    "source_category": "REGULATORY",
    "source_name": "FBI_IC3",
    "source_url": "https://www.ic3.gov/Media/News/sextortion-surge-2024",
    "raw_content": (
        "FBI IC3 Alert: Significant surge in financial sextortion targeting males aged 15-35. "
        "Criminals contact victims via social media posing as female peers, solicit explicit images, "
        "then threaten to share images unless immediate payment is made — typically via wire transfer or gift cards. "
        "Over 12,000 victims reported in 2023 with $15M+ in losses. Singapore and Southeast Asia emerging as key target regions."
    ),
    "content_hash": "abc456sext001",
    "language": "en",
    "processing_status": "ALERTED",
    "title": "FBI IC3: Surge in Financial Sextortion Targeting Young Males",
    "publication_date": "2024-06-13",
}

S2_FRAUD = {
    "fraud_signal_id": "fs-sextortion-001",
    "raw_signal_id": "raw-sextortion-001",
    "detected_at": "2024-06-14T08:35:00",
    "fraud_typology": "SEXTORTION",
    "fraud_description": (
        "Organised criminal groups are executing sextortion campaigns targeting young male banking customers. "
        "Fraudsters pose as attractive females on social media platforms, build rapport, solicit explicit imagery, "
        "then immediately pivot to financial extortion threatening public exposure of the images. "
        "Victims are directed to make urgent payments via bank transfer or gift card purchases to avoid 'exposure'."
    ),
    "attack_vector": "Social media honey trap → image solicitation → financial extortion threat → urgent wire transfer / gift card demand",
    "victim_profile": {
        "age_range": "18-35",
        "customer_segment": "RETAIL",
        "geography": ["SG", "TH", "ID", "MY"],
        "channel": "MOBILE",
    },
    "financial_mechanism": "Social engineering → urgency-driven wire transfer to attacker-controlled account or gift card purchase",
    "geographic_origin": ["US", "NG", "PH"],
    "geographic_spread": ["SG", "MY", "TH", "ID", "AU"],
    "first_reported_globally": "2022-01-15",
    "severity_estimate": "HIGH",
    "novelty_score": 0.55,
    "confidence_score": 0.85,
    "source_credibility": "HIGH",
    "raw_evidence": "12,000+ victims in 2023, $15M+ in losses. Singapore and Southeast Asia emerging target regions. Males 15-35 primary victims.",
}

S2_ASSESSMENT = {
    "assessment_id": "ra-sextortion-001",
    "fraud_signal_id": "fs-sextortion-001",
    "assessed_at": "2024-06-14T08:45:00",
    "gate1_novelty": {
        "passed": True, "score": 65.0, "raw_score": 15.0,
        "existing_tm_rule_match": False,
        "similar_signal_ids": [],
        "explanation": "No existing TM rule covers sextortion typology; moderate-high novelty as pattern is emerging in ASEAN region",
        "reasons": [
            "No existing TM rule covers SEXTORTION typology (+30 bonus pts)",
            "No similar signal alerted in last 90 days",
            "Moderate novelty score: 0.55 — known globally but newly surging in ASEAN",
        ],
    },
    "gate2_customer_exposure": {
        "passed": True, "score": 80.0,
        "matched_segments": ["RETAIL"],
        "estimated_at_risk_customers": 67200,
        "geographic_overlap": True,
        "channel_overlap": True,
        "explanation": "✓ RETAIL customers (male 18-35) in SG/TH/ID; ~67,200 at risk",
        "reasons": [
            "Segment match: RETAIL (+35 pts)",
            "ASEAN geography overlap: SG, TH, ID, MY (+15 pts)",
            "Channel overlap: MOBILE (+20 pts)",
            "High exposure: 67,200 at-risk customers (+15 bonus pts)",
        ],
    },
    "gate3_control_gap": {
        "passed": True, "score": 82.0,
        "matched_tm_rules": [],
        "undetected_percentage": 88.0,
        "auth_vulnerability": True,
        "explanation": "✓ 88% of attacks undetected (no TM rules cover sextortion); SMS OTP auth vulnerability: YES",
        "reasons": [
            "No TM rules cover SEXTORTION typology (+30 bonus pts)",
            "Very high control gap: 88% undetected (+50 pts)",
            "SMS_OTP auth vulnerability exploited (+25 pts)",
        ],
    },
    "overall_passed": True,
    "composite_risk_score": 76.5,
    "alert_priority": "HIGH",
    "recommended_actions": [
        "Issue targeted advisory to male retail customers aged 18-35",
        "Deploy gift card purchase monitoring rule (TM-008 enhancement)",
        "Train customer service team to recognize sextortion victim indicators",
    ],
}

S2_SIMULATION = {
    "simulation_id": "sim-sextortion-001",
    "fraud_signal_id": "fs-sextortion-001",
    "run_at": "2024-06-14T08:50:00",
    "scenario_name": "Sextortion — ASEAN Retail Male 18-35 Baseline",
    "customer_exposure": {
        "total_at_risk": 67200,
        "by_segment": {"RETAIL": 67200},
        "by_geography": {"SG": 28800, "MY": 16800, "TH": 12000, "ID": 9600},
    },
    "financial_impact": {
        "baseline_exposure_sgd": 10080000.0,
        "with_current_controls_sgd": 8467200.0,
        "with_proposed_controls_sgd": 3225600.0,
        "p10_sgd": 3200000.0,
        "p50_sgd": 8900000.0,
        "p90_sgd": 22000000.0,
        "methodology": (
            "Estimated 3,360 victims (67,200 at-risk × 5% reach × 100% conversion given urgency tactics). "
            "Avg loss SGD 3,000/victim. Current controls catch ~16% (gift card rule TM-008). "
            "Proposed interventions target 68% additional reduction."
        ),
    },
    "control_gap_analysis": {
        "current_detection_rate_pct": 12.0,
        "undetected_rate_pct": 88.0,
        "failing_controls": [
            "No dedicated TM rule for sextortion pattern",
            "TM-008 (gift card detection) only partially applicable — misses wire transfers",
        ],
    },
    "proposed_interventions": [
        {
            "intervention_type": "Targeted Customer Advisory",
            "description": "Push notification to male RETAIL customers 18-35 warning of sextortion campaigns",
            "estimated_reduction_pct": 20.0,
            "implementation_effort": "LOW",
        },
        {
            "intervention_type": "Urgency Pattern TM Rule",
            "description": "Flag sudden high-value transfers to new overseas payees by customers with no prior international transfer history",
            "estimated_reduction_pct": 35.0,
            "implementation_effort": "MEDIUM",
        },
    ],
    "estimated_victims": 3360,
    "victim_rate_pct": 100.0,
    "avg_loss_sgd": 3000.0,
}

S2_RULES = [
    {
        "rule_id": "rule-sext-tm-001",
        "fraud_signal_id": "fs-sextortion-001",
        "rule_type": "TM_DETECTION",
        "target_layer": "TRANSACTION_MONITORING",
        "rule_description": "Detect sextortion payment pattern: sudden first-time overseas transfer or multiple gift card purchases following social media account activity on registered device.",
        "rule_logic": (
            "IF customer has NO prior overseas_transfer_history AND overseas_transfer > SGD 200 "
            "AND customer_age_band IN [18-25, 26-35] AND time_of_day IN [evening/night] "
            "THEN flag SEXTORTION_RISK"
        ),
        "trigger_conditions": [
            "No prior overseas transfer history",
            "Overseas transfer > SGD 200",
            "Customer age band: 18-35",
            "Transaction during evening or night hours",
        ],
        "expected_impact_pct": 28.0,
        "deployment_risk": "MEDIUM",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-sext-friction-001",
        "fraud_signal_id": "fs-sextortion-001",
        "rule_type": "CUSTOMER_FRICTION",
        "target_layer": "AUTHENTICATION",
        "rule_description": "Implement welfare check pop-up for first-time overseas transfers by customers in the 18-35 demographic, displaying sextortion warning and SafeGuard hotline.",
        "rule_logic": (
            "IF first_overseas_transfer = TRUE AND customer_age IN [18,35] "
            "THEN display welfare_check_modal with sextortion_advisory + scam_helpline before processing"
        ),
        "trigger_conditions": [
            "First-time overseas wire transfer",
            "Customer age 18-35",
            "Transfer initiated via mobile app",
        ],
        "expected_impact_pct": 22.0,
        "deployment_risk": "MEDIUM",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-sext-policy-001",
        "fraud_signal_id": "fs-sextortion-001",
        "rule_type": "POLICY_CHANGE",
        "target_layer": "POLICY",
        "rule_description": "Establish dedicated Sextortion Victim Support Protocol with fast-track transaction reversal process and referral to Police/Samaritans of Singapore.",
        "rule_logic": (
            "IF customer reports sextortion_coercion to call_centre "
            "THEN activate fast_track_reversal_protocol AND provide SPF_report_guidance AND SOS_referral"
        ),
        "trigger_conditions": [
            "Customer self-reports sextortion",
            "Recent transfer to new overseas payee",
        ],
        "expected_impact_pct": 15.0,
        "deployment_risk": "LOW",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-sext-advisory-001",
        "fraud_signal_id": "fs-sextortion-001",
        "rule_type": "ADVISORY",
        "target_layer": "CUSTOMER_COMMS",
        "rule_description": "Issue targeted advisory to male retail customers aged 18-35 warning of sextortion tactics, with guidance to not make any payments and to report to SPF.",
        "rule_logic": (
            "IF customer_segment = RETAIL AND gender_indicator = MALE AND age IN [18,35] "
            "THEN send targeted_advisory via push + email WITHIN 24h"
        ),
        "trigger_conditions": [
            "Customer segment: RETAIL",
            "Age band: 18-35",
            "Geography: SG, MY, TH, ID",
        ],
        "expected_impact_pct": 15.0,
        "deployment_risk": "LOW",
        "approval_required": False,
        "auto_deployable": True,
    },
]

S2_ALERT = {
    "alert_id": "alert-sextortion-001",
    "fraud_signal_id": "fs-sextortion-001",
    "assessment_id": "ra-sextortion-001",
    "simulation_id": "sim-sextortion-001",
    "generated_at": "2024-06-14T09:00:00",
    "priority": "HIGH",
    "document": {
        "executive_summary": (
            "A HIGH-priority Sextortion threat is targeting UOB's male retail customers aged 18–35 across Singapore, Malaysia, Thailand, and Indonesia. "
            "Approximately 67,200 customers are at risk with no existing TM rule coverage — 88% of attacks would currently go undetected. "
            "Baseline financial exposure is estimated at SGD 8.9M (P50), with a worst case of SGD 22M. "
            "Immediate action: issue targeted customer advisory within 24 hours and deploy urgency-pattern TM detection rule."
        ),
        "threat_description": (
            "Sextortion attacks are orchestrated by criminal networks primarily based in West Africa and the Philippines. "
            "The attack sequence: (1) Fraudster creates fake female profile on social media → (2) Targets male users aged 18-35 → "
            "(3) Builds rapport and solicits explicit images/videos → (4) Immediately pivots to extortion: 'pay or I send to your family/employer' → "
            "(5) Victim makes urgent bank transfer or purchases gift cards under duress. "
            "The FBI IC3 reported 12,000+ victims and USD 15M+ in losses globally in 2023. "
            "Singapore and Southeast Asia are now primary growth markets for this fraud, driven by high smartphone penetration "
            "and high-value banking customers in the 18-35 age group."
        ),
        "uob_relevance": (
            "No UOB TM rule currently targets the sextortion pattern. The 88% undetected rate is the highest control gap of any current threat in the alert queue. "
            "UOB's retail customer base includes approximately 67,200 male customers aged 18-35 using mobile banking — "
            "exactly the demographic targeted by this campaign. Composite risk score: 76.5/100 (HIGH)."
        ),
        "customer_impact": (
            "67,200 male retail customers (18-35) in SG/MY/TH/ID estimated at risk. "
            "Attack reach: approximately 3,360 customers contacted per campaign wave (5% reach factor). "
            "Victim conversion rate: near 100% due to extreme urgency and shame-based coercion. "
            "Average loss: SGD 3,000 per victim."
        ),
        "financial_exposure": (
            "Baseline exposure: SGD 10.1M. With current controls: SGD 8.5M (gift card rule provides ~16% coverage). "
            "With proposed interventions: SGD 3.2M. "
            "P10: SGD 3.2M, P50: SGD 8.9M, P90: SGD 22.0M."
        ),
        "current_control_gaps": (
            "No dedicated sextortion TM rule exists. TM-008 (gift card detection) provides limited coverage but misses wire transfer payment method. "
            "No behavioral trigger for 'first overseas transfer by young male customer' pattern. "
            "Overall undetected rate: 88%."
        ),
        "recommended_actions": {
            "immediate": [
                "Issue targeted push notification to 67,200 male retail customers aged 18-35 warning of sextortion campaigns",
                "Activate manual review for all first-time overseas transfers > SGD 200 by customers aged 18-35",
                "Brief call centre staff on sextortion victim support protocol",
            ],
            "short_term": [
                "Submit urgency-pattern TM detection rule: first overseas transfer + young male + night hours",
                "Implement welfare check pop-up for first-time overseas transfers (18-35 demographic)",
                "Coordinate with DBS/OCBC/HSBC for industry-wide alert under MAS Fraud Watch framework",
                "Update SCB SafeGuard app integration with sextortion warning category",
            ],
            "strategic": [
                "Develop formal Sextortion Victim Support Protocol with SPF and Samaritans of Singapore referral pathway",
                "Commission study on social media platform collaboration for fraudulent profile takedown",
            ],
        },
        "intervention_rules": S2_RULES,
        "simulation_summary": "P50 exposure: SGD 8.9M. Proposed advisory + TM rule reduces exposure to SGD 3.2M (68% reduction).",
        "evidence_sources": [
            "FBI Internet Crime Complaint Center (IC3) — Sextortion Alert 2024",
            "Singapore Police Force — Cybercrimes statistics 2023",
            "Interpol — Financial Sextortion Threat Assessment ASEAN 2024",
        ],
        "confidence_rating": "HIGH",
        "analyst_notes": (
            "This alert is AI-generated. It must be reviewed by a qualified fraud risk analyst before operational action is taken. "
            "Age/gender segmentation is derived from synthetic persona dataset and may not reflect actual customer distribution. "
            "Victim conversion rate assumption (100%) is based on FBI IC3 case study data and may vary by geography. "
            "Recommended validation: cross-reference with recent fraud operations case files for sextortion reports."
        ),
    },
    "routing": {
        "compliance_team": True,
        "fraud_risk_team": True,
        "tm_analytics_team": True,
        "policy_controls_team": False,
    },
    "fraud_typology": "SEXTORTION",
    "composite_score": 76.5,
}

# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 3 — Deepfake CFO Fraud (HIGH)
# ══════════════════════════════════════════════════════════════════════════════

S3_RAW = {
    "signal_id": "raw-deepfake-cfo-001",
    "ingested_at": "2024-06-13T14:00:00",
    "source_category": "THREAT_INTEL",
    "source_name": "ENISA",
    "source_url": "https://www.enisa.europa.eu/publications/deepfake-cfo-fraud-2024",
    "raw_content": (
        "ENISA Threat Landscape: AI-Powered Deepfake CEO/CFO Fraud Surging in Asia-Pacific. "
        "Criminal groups are using generative AI to create convincing video and audio deepfakes of executives "
        "to authorize fraudulent wire transfers. A Hong Kong-based multinational lost USD 25M in February 2024 "
        "when an employee was deceived by a deepfake video call appearing to feature the company CFO. "
        "Trade finance and correspondent banking sectors are primary targets due to large transaction values."
    ),
    "content_hash": "abc789deep001",
    "language": "en",
    "processing_status": "ALERTED",
    "title": "ENISA: AI Deepfake CFO Fraud — USD 25M Hong Kong Incident",
    "publication_date": "2024-06-12",
}

S3_FRAUD = {
    "fraud_signal_id": "fs-deepfake-cfo-001",
    "raw_signal_id": "raw-deepfake-cfo-001",
    "detected_at": "2024-06-13T14:10:00",
    "fraud_typology": "DEEPFAKE_CFO_FRAUD",
    "fraud_description": (
        "AI-generated deepfake video and audio technology is being weaponized to impersonate senior corporate executives "
        "during video conference calls, convincing finance employees to authorize large unauthorized wire transfers. "
        "The February 2024 Hong Kong incident — where a multinational lost USD 25M — marks a new phase in sophistication: "
        "real-time deepfake video in a multi-participant call. Trade finance operations handling large cross-border transactions are the primary target."
    ),
    "attack_vector": "AI deepfake video call impersonating CFO/CEO → finance employee authorization → large unauthorized wire transfer",
    "victim_profile": {
        "age_range": "30-55",
        "customer_segment": "TRADE_FINANCE",
        "geography": ["SG", "HK", "CN"],
        "channel": "INTERNET_BANKING",
    },
    "financial_mechanism": "Social engineering via deepfake video call → employee-authorized wire transfer → funds transferred to criminal-controlled account before detection",
    "geographic_origin": ["HK", "CN", "EU"],
    "geographic_spread": ["SG", "HK", "AU", "UK", "US"],
    "first_reported_globally": "2023-06-01",
    "severity_estimate": "HIGH",
    "novelty_score": 0.88,
    "confidence_score": 0.90,
    "source_credibility": "HIGH",
    "raw_evidence": "Hong Kong multinational lost USD 25M (SGD 33.7M) in Feb 2024 via deepfake CFO video call. Employee deceived into authorizing transfer.",
}

S3_ASSESSMENT = {
    "assessment_id": "ra-deepfake-cfo-001",
    "fraud_signal_id": "fs-deepfake-cfo-001",
    "assessed_at": "2024-06-13T14:20:00",
    "gate1_novelty": {
        "passed": True, "score": 88.0, "raw_score": 38.0,
        "existing_tm_rule_match": False,
        "similar_signal_ids": [],
        "explanation": "Very high novelty (0.88): real-time AI deepfake in live video calls is a fundamentally new attack capability with no existing TM coverage",
        "reasons": [
            "No existing TM rule covers DEEPFAKE_CFO_FRAUD typology (+30 bonus pts)",
            "No similar signal alerted in last 90 days",
            "Very high novelty score: 0.88 — real-time deepfake in live calls is genuinely new (+30 pts)",
            "HIGH credibility source (ENISA) (+10 pts)",
        ],
    },
    "gate2_customer_exposure": {
        "passed": True, "score": 65.0,
        "matched_segments": ["TRADE_FINANCE"],
        "estimated_at_risk_customers": 11000,
        "geographic_overlap": True,
        "channel_overlap": True,
        "explanation": "✓ TRADE_FINANCE customers in SG/HK; ~11,000 at risk (lower count but extremely high per-victim loss)",
        "reasons": [
            "Segment match: TRADE_FINANCE (+20 pts)",
            "Singapore/HK geography overlap (+30 pts)",
            "Channel: INTERNET_BANKING overlap (+20 pts)",
        ],
    },
    "gate3_control_gap": {
        "passed": True, "score": 80.0,
        "matched_tm_rules": ["TM-008"],
        "undetected_percentage": 85.0,
        "auth_vulnerability": False,
        "explanation": "✓ 85% undetected; no TM rule specifically targets deepfake-authorized transfers",
        "reasons": [
            "TM-008 provides marginal coverage (15%) via invoice discrepancy detection",
            "Very high control gap: 85% undetected (+50 pts)",
            "No device binding vulnerability (TRADE_FINANCE uses DEVICE_BOUND auth)",
        ],
    },
    "overall_passed": True,
    "composite_risk_score": 73.8,
    "alert_priority": "HIGH",
    "recommended_actions": [
        "Issue advisory to Trade Finance relationship managers on deepfake video call risks",
        "Implement dual-authorisation for all wire transfers > SGD 50,000",
        "Deploy callback verification protocol for high-value approvals",
    ],
}

S3_SIMULATION = {
    "simulation_id": "sim-deepfake-cfo-001",
    "fraud_signal_id": "fs-deepfake-cfo-001",
    "run_at": "2024-06-13T14:25:00",
    "scenario_name": "Deepfake CFO Fraud — Trade Finance SG/HK Baseline",
    "customer_exposure": {
        "total_at_risk": 11000,
        "by_segment": {"TRADE_FINANCE": 11000},
        "by_geography": {"SG": 8000, "HK": 3000},
    },
    "financial_impact": {
        "baseline_exposure_sgd": 55000000.0,
        "with_current_controls_sgd": 51700000.0,
        "with_proposed_controls_sgd": 17600000.0,
        "p10_sgd": 18000000.0,
        "p50_sgd": 47000000.0,
        "p90_sgd": 125000000.0,
        "methodology": (
            "Estimated 220 victims (11,000 at-risk × 2% reach × 100% conversion given sophisticated social engineering). "
            "Avg loss SGD 250,000/victim (trade finance transaction scale). "
            "Current controls catch only 6% (invoice discrepancy rule TM-008). "
            "Dual-authorisation + callback verification targets 68% loss reduction."
        ),
    },
    "control_gap_analysis": {
        "current_detection_rate_pct": 6.0,
        "undetected_rate_pct": 85.0,
        "failing_controls": [
            "No TM rule covers employee-authorized deepfake-instigated transfers",
            "TM-004 (overseas wire anomaly) insufficient: transfers appear legitimate (employee authorized)",
            "Dual-authorisation not currently required for DEVICE_BOUND trade finance customers",
        ],
    },
    "proposed_interventions": [
        {
            "intervention_type": "Dual-Authorisation Policy",
            "description": "Require second approver (Operations Manager level) for all wire transfers > SGD 50,000",
            "estimated_reduction_pct": 55.0,
            "implementation_effort": "MEDIUM",
        },
        {
            "intervention_type": "Callback Verification Protocol",
            "description": "Mandatory callback to pre-registered executive hotline before processing high-value approvals",
            "estimated_reduction_pct": 40.0,
            "implementation_effort": "LOW",
        },
    ],
    "estimated_victims": 220,
    "victim_rate_pct": 100.0,
    "avg_loss_sgd": 250000.0,
}

S3_RULES = [
    {
        "rule_id": "rule-deep-tm-001",
        "fraud_signal_id": "fs-deepfake-cfo-001",
        "rule_type": "TM_DETECTION",
        "target_layer": "TRANSACTION_MONITORING",
        "rule_description": "Flag large wire transfers authorized immediately after video conferencing application activity on the approver's registered device.",
        "rule_logic": (
            "IF wire_transfer > SGD 50000 AND approver_device_has_recent_video_call_activity "
            "AND payee_is_new AND time_since_video_call < 4h "
            "THEN flag DEEPFAKE_CFO_RISK; hold 30 minutes; escalate to Operations Manager"
        ),
        "trigger_conditions": [
            "Wire transfer > SGD 50,000",
            "Approver device shows recent video conferencing activity",
            "Payee is new or unverified",
            "Transfer authorized within 4 hours of video call",
        ],
        "expected_impact_pct": 30.0,
        "deployment_risk": "MEDIUM",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-deep-friction-001",
        "fraud_signal_id": "fs-deepfake-cfo-001",
        "rule_type": "CUSTOMER_FRICTION",
        "target_layer": "AUTHENTICATION",
        "rule_description": "Implement mandatory dual-authorisation for all outward wire transfers exceeding SGD 50,000, requiring separate approval from a second authorised signatory.",
        "rule_logic": (
            "IF transfer_type = OUTWARD_WIRE AND amount > SGD 50000 "
            "THEN require secondary_authorisation from Operations_Manager_or_above; "
            "timeout = 2h; on timeout, reject and notify Compliance"
        ),
        "trigger_conditions": [
            "Outward wire transfer",
            "Amount > SGD 50,000",
            "Trade Finance or SME customer",
        ],
        "expected_impact_pct": 40.0,
        "deployment_risk": "MEDIUM",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-deep-policy-001",
        "fraud_signal_id": "fs-deepfake-cfo-001",
        "rule_type": "POLICY_CHANGE",
        "target_layer": "POLICY",
        "rule_description": "Mandate out-of-band callback verification via pre-registered executive hotline for all wire transfers > SGD 100,000 authorized via digital channels.",
        "rule_logic": (
            "IF transfer_amount > SGD 100000 AND channel IN [INTERNET_BANKING, MOBILE] "
            "THEN operations_team MUST call pre-registered_executive_number to verbally confirm "
            "before processing; record call; retain for 7 years"
        ),
        "trigger_conditions": [
            "Transfer amount > SGD 100,000",
            "Channel: Internet Banking or Mobile",
            "Trade Finance or SME customer",
        ],
        "expected_impact_pct": 35.0,
        "deployment_risk": "LOW",
        "approval_required": True,
        "auto_deployable": False,
    },
    {
        "rule_id": "rule-deep-advisory-001",
        "fraud_signal_id": "fs-deepfake-cfo-001",
        "rule_type": "ADVISORY",
        "target_layer": "CUSTOMER_COMMS",
        "rule_description": "Issue advisory to Trade Finance relationship managers and corporate customers explaining deepfake video call threat and how to verify executive authenticity.",
        "rule_logic": (
            "IF customer_segment IN [TRADE_FINANCE, SME] "
            "THEN send deepfake_advisory to relationship_manager + corporate_finance_contact "
            "with verification_protocol_guide WITHIN 24h"
        ),
        "trigger_conditions": [
            "Customer segment: TRADE_FINANCE, SME",
            "Geography: SG, HK",
            "HIGH or CRITICAL priority threat",
        ],
        "expected_impact_pct": 20.0,
        "deployment_risk": "LOW",
        "approval_required": False,
        "auto_deployable": True,
    },
]

S3_ALERT = {
    "alert_id": "alert-deepfake-cfo-001",
    "fraud_signal_id": "fs-deepfake-cfo-001",
    "assessment_id": "ra-deepfake-cfo-001",
    "simulation_id": "sim-deepfake-cfo-001",
    "generated_at": "2024-06-13T14:45:00",
    "priority": "HIGH",
    "document": {
        "executive_summary": (
            "A HIGH-priority AI Deepfake CFO Fraud threat has been identified, directly relevant to UOB's Trade Finance and SME operations in Singapore and Hong Kong. "
            "The February 2024 Hong Kong incident — USD 25M lost in a single deepfake video call — demonstrates the scale of potential impact for UOB's 11,000 trade finance customers. "
            "Current controls detect only 6% of these attacks, with an estimated unmitigated exposure of SGD 47M (P50) to SGD 125M (P90). "
            "Immediate action: implement dual-authorisation for all wire transfers exceeding SGD 50,000 and issue advisory to Trade Finance relationship managers."
        ),
        "threat_description": (
            "AI-powered deepfake technology has advanced to the point where criminals can generate real-time, convincing video and audio impersonations of corporate executives during live video conference calls. "
            "The attack sequence: (1) Criminal researches target company executives via LinkedIn/public records → "
            "(2) Schedules video call with finance team posing as CFO/CEO → "
            "(3) Uses real-time AI deepfake to appear and sound convincingly as the executive → "
            "(4) Instructs finance employee to process urgent wire transfer → "
            "(5) Funds transferred to criminal-controlled account before detection. "
            "The February 2024 Hong Kong case (USD 25M / SGD 33.7M) involved a multi-participant call with several deepfaked executives, bypassing the social engineering skepticism of a single-participant call. "
            "ENISA identifies Trade Finance, Correspondent Banking, and large SMEs as primary targets due to the scale of authorized transactions."
        ),
        "uob_relevance": (
            "UOB's Trade Finance division processes large cross-border wire transfers — exactly the transaction profile targeted. "
            "Current controls (TM-008: invoice discrepancy detection) provide only 6% coverage against this attack, as the transfers appear legitimate (employee-authorized). "
            "11,000 Trade Finance and SME corporate customers are estimated at risk. "
            "With avg loss potential of SGD 250,000 per incident, even 10 successful attacks would cost SGD 2.5M. "
            "Novelty score: 0.88 — this is a genuinely new threat capability requiring new countermeasures. Composite risk score: 73.8/100 (HIGH)."
        ),
        "customer_impact": (
            "11,000 Trade Finance and SME corporate customers in Singapore (8,000) and Hong Kong (3,000) at risk. "
            "Attack reach: approximately 220 organisations targeted per wave (2% reach factor). "
            "Per-incident loss: SGD 250,000 average (can range to SGD 25M+ for large trade finance transactions). "
            "Victims: finance staff with wire transfer authorization authority."
        ),
        "financial_exposure": (
            "Baseline exposure: SGD 55M. With current controls: SGD 51.7M (invoice anomaly detection provides only 6% coverage). "
            "With proposed interventions (dual-auth + callback): SGD 17.6M. "
            "P10: SGD 18M, P50: SGD 47M, P90: SGD 125M."
        ),
        "current_control_gaps": (
            "Three critical gaps: (1) No TM rule covers employee-authorized deepfake-instigated transfers — "
            "these look identical to legitimate authorized transactions; "
            "(2) TM-004 (overseas wire anomaly) is bypassed because the employee authorization makes the transfer appear routine; "
            "(3) Dual-authorisation is not currently required for DEVICE_BOUND trade finance customers for any transaction size. "
            "Overall undetected rate: 85% — the highest control gap for any corporate segment threat."
        ),
        "recommended_actions": {
            "immediate": [
                "Issue advisory to all Trade Finance relationship managers on deepfake video call threat with HK incident case study",
                "Flag all wire transfers > SGD 100,000 for manual review until dual-authorisation policy is deployed",
                "Brief corporate banking operations team on verification protocol for large-value transfer requests",
            ],
            "short_term": [
                "Implement dual-authorisation for wire transfers > SGD 50,000 (est. 40% exposure reduction)",
                "Establish mandatory callback verification protocol for transfers > SGD 100,000",
                "Deploy TM detection rule: large wire + video call + new payee within 4 hours",
                "Update corporate customer security advisory with deepfake verification guidance",
                "Brief trade finance operations team on how to independently verify executive identity",
            ],
            "strategic": [
                "Commission AI deepfake detection capability assessment (biometric liveness detection on video calls)",
                "Develop formal Deepfake Fraud Incident Response Protocol with CISO and Legal sign-off",
            ],
        },
        "intervention_rules": S3_RULES,
        "simulation_summary": "P50 exposure: SGD 47M. Dual-auth + callback protocol reduces exposure to SGD 17.6M (68% reduction). P90 worst case remains SGD 125M without intervention.",
        "evidence_sources": [
            "ENISA Threat Landscape Report — AI-Powered Financial Fraud 2024",
            "Hong Kong Police Force — February 2024 Deepfake CFO Fraud Case (USD 25M)",
            "FBI Alert AC-000159-MW — Business Email Compromise / Deepfake Evolution",
        ],
        "confidence_rating": "HIGH",
        "analyst_notes": (
            "This alert is AI-generated. It must be reviewed by a qualified fraud risk analyst before operational action is taken. "
            "Financial exposure figures assume USD 25M per major incident as reference point from Hong Kong case; "
            "actual UOB trade finance transaction values may differ. "
            "The P90 scenario (SGD 125M) assumes multiple successful attacks at trade finance transaction scale. "
            "Recommended validation: confirm dual-authorisation status of current Trade Finance wire approval workflows with Operations."
        ),
    },
    "routing": {
        "compliance_team": True,
        "fraud_risk_team": True,
        "tm_analytics_team": False,
        "policy_controls_team": True,
    },
    "fraud_typology": "DEEPFAKE_CFO_FRAUD",
    "composite_score": 73.8,
}


# ══════════════════════════════════════════════════════════════════════════════
# Seed Runner
# ══════════════════════════════════════════════════════════════════════════════

def seed_demo_scenarios():
    """Insert all 3 demo scenarios into the database. Idempotent."""
    if is_seeded("demo_scenarios_v2"):
        logger.info("Demo scenarios already seeded — skipping")
        return

    scenarios = [
        ("SMS Spoofing", S1_RAW, S1_FRAUD, S1_ASSESSMENT, S1_SIMULATION, S1_RULES, S1_ALERT),
        ("Sextortion", S2_RAW, S2_FRAUD, S2_ASSESSMENT, S2_SIMULATION, S2_RULES, S2_ALERT),
        ("Deepfake CFO", S3_RAW, S3_FRAUD, S3_ASSESSMENT, S3_SIMULATION, S3_RULES, S3_ALERT),
    ]

    for name, raw, fraud, assessment, simulation, rules, alert in scenarios:
        logger.info("Seeding scenario: %s", name)
        insert_raw_signal(raw)
        insert_fraud_signal(fraud)
        insert_relevance_assessment(assessment)
        insert_simulation(simulation)
        insert_intervention_rules(rules)
        # Generate PDF
        try:
            pdf_path = generate_pdf(alert, fraud, assessment, simulation)
            alert["pdf_path"] = pdf_path
        except Exception as e:
            logger.warning("PDF generation failed for %s: %s", name, e)
            alert["pdf_path"] = None
        insert_risk_alert(alert)

    mark_seeded("demo_scenarios_v2")
    logger.info("✓ All 3 demo scenarios seeded successfully")
