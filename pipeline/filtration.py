"""
Phantom Signal — 3-Gate Relevance Filtration Engine (PRD-005)
Sequential gate evaluation determining if a FraudSignal is material to UOB.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config import (
    GATE1_THRESHOLD, GATE2_THRESHOLD, GATE3_THRESHOLD,
    PRIORITY_THRESHOLDS, UOB_GEOGRAPHIES,
)
from data.database import (
    get_tm_rules, get_customer_personas, get_assessment_by_signal,
    get_fraud_signals, insert_relevance_assessment, update_raw_signal_status,
)
from data.synthetic_generator import get_vulnerability_matrix

logger = logging.getLogger(__name__)


# ── Gate 1: Novelty Check ─────────────────────────────────────────────────────

def _gate1_novelty(fraud_signal: Dict) -> Dict:
    """
    Question: Is this a fraud pattern we haven't already detected and hardened against?
    Score >= GATE1_THRESHOLD to pass.
    """
    typology = fraud_signal.get("fraud_typology", "")
    novelty_score = float(fraud_signal.get("novelty_score", 0.5))
    credibility = fraud_signal.get("source_credibility", "MEDIUM")
    fraud_signal_id = fraud_signal.get("fraud_signal_id", "")

    score = 0.0
    existing_tm_rule_match = False
    similar_signal_ids = []
    reasons = []

    # Check TM rules coverage
    tm_rules = get_tm_rules()
    covering_rules = [
        r for r in tm_rules
        if typology in r.get("fraud_typologies_targeted", [])
    ]
    if covering_rules:
        existing_tm_rule_match = True
        score -= 40
        reasons.append(f"Covered by {len(covering_rules)} existing TM rule(s): {', '.join(r['rule_id'] for r in covering_rules[:3])}")
    else:
        score += 30  # bonus: no TM rule coverage at all
        reasons.append("No existing TM rule covers this typology")

    # Check recent similar signals (90-day lookback)
    recent_signals = get_fraud_signals(typology=typology, limit=50)
    cutoff_30 = (datetime.utcnow() - timedelta(days=30)).isoformat()
    cutoff_90 = (datetime.utcnow() - timedelta(days=90)).isoformat()

    recent_30 = [
        s for s in recent_signals
        if s.get("detected_at","") >= cutoff_30
        and s.get("fraud_signal_id") != fraud_signal_id
        and s.get("severity_estimate") in ["HIGH","CRITICAL"]
    ]
    recent_90 = [
        s for s in recent_signals
        if cutoff_30 > s.get("detected_at","") >= cutoff_90
        and s.get("fraud_signal_id") != fraud_signal_id
    ]

    if recent_30:
        score -= 30
        similar_signal_ids = [s["fraud_signal_id"] for s in recent_30[:3]]
        reasons.append(f"Similar HIGH/CRITICAL signal alerted within last 30 days ({len(recent_30)} found)")
    elif recent_90:
        score -= 15
        similar_signal_ids = [s["fraud_signal_id"] for s in recent_90[:3]]
        reasons.append(f"Similar signal alerted in 31–90 day window ({len(recent_90)} found)")
    else:
        reasons.append("No similar signal alerted in last 90 days")

    # Novelty score bonuses
    if novelty_score >= 0.7:
        score += 30
        reasons.append(f"High novelty score ({novelty_score:.2f}) — emerging or novel typology")
    elif novelty_score >= 0.4:
        score += 10
        reasons.append(f"Moderate novelty score ({novelty_score:.2f})")
    else:
        reasons.append(f"Low novelty score ({novelty_score:.2f}) — well-established typology")

    # Source credibility bonus
    if credibility == "HIGH":
        score += 10
        reasons.append("HIGH credibility source (regulatory body)")

    # UOB IOC Match
    iocs = fraud_signal.get("iocs", {})
    bank_accounts = iocs.get("bank_accounts", [])
    has_uob_ioc = False
    for acc in bank_accounts:
        if "UOB" in acc.upper():
            has_uob_ioc = True
            break
            
    if has_uob_ioc:
        score += 50
        reasons.append("Direct UOB IOC Detected (+50 pts override)")

    passed = score >= GATE1_THRESHOLD
    explanation = "; ".join(reasons[:3])

    return {
        "passed": passed,
        "score": max(0.0, min(100.0, score + 50)),  # normalize to 0–100 for display
        "raw_score": score,
        "existing_tm_rule_match": existing_tm_rule_match,
        "similar_signal_ids": similar_signal_ids,
        "explanation": explanation,
        "reasons": reasons,
    }


# ── Gate 2: Customer Exposure Check ──────────────────────────────────────────

def _gate2_customer_exposure(fraud_signal: Dict) -> Dict:
    """
    Question: Does this fraud pattern threaten customers UOB actually has?
    Score >= GATE2_THRESHOLD to pass.
    """
    victim_profile = fraud_signal.get("victim_profile", {})
    segment = victim_profile.get("customer_segment", "RETAIL")
    geos = fraud_signal.get("geographic_spread", []) or fraud_signal.get("geographic_origin", [])
    if isinstance(geos, str):
        geos = [geos]
    channel = victim_profile.get("channel", "MULTIPLE")

    vuln_matrix = get_vulnerability_matrix()
    typology = fraud_signal.get("fraud_typology", "")

    score = 0.0
    matched_segments = []
    at_risk_customers = 0
    geographic_overlap = False
    channel_overlap = False
    reasons = []

    # Segment scoring
    segment_scores = {
        "RETAIL": 35, "MULTIPLE": 30,
        "SME": 25, "TRADE_FINANCE": 20,
        "CORRESPONDENT_BANKING": 20,
    }
    seg_score = segment_scores.get(segment, 10)
    score += seg_score
    matched_segments.append(segment)
    reasons.append(f"Segment match: {segment} (+{seg_score} pts)")

    # UOB IOC Match
    iocs = fraud_signal.get("iocs", {})
    bank_accounts = iocs.get("bank_accounts", [])
    has_uob_ioc = False
    for acc in bank_accounts:
        if "UOB" in acc.upper():
            has_uob_ioc = True
            break
            
    if has_uob_ioc:
        score += 50
        reasons.append("Direct UOB IOC Detected (Bank Account) (+50 pts)")

    # Geography overlap
    sg_overlap = any(g in ["SG"] for g in geos) or not geos
    asean_overlap = any(g in ["MY","TH","ID","HK","VN"] for g in geos)
    uob_overlap = any(g in UOB_GEOGRAPHIES for g in geos)

    if sg_overlap:
        score += 30
        geographic_overlap = True
        reasons.append("Singapore geography overlap (+30 pts)")
    elif asean_overlap:
        score += 15
        geographic_overlap = True
        reasons.append("ASEAN geography overlap (+15 pts)")
    elif uob_overlap:
        score += 5
        geographic_overlap = True
        reasons.append("UOB footprint geography overlap (+5 pts)")
    else:
        reasons.append("No geography overlap with UOB footprint")

    # Channel overlap
    if channel in ["MOBILE", "INTERNET_BANKING", "MULTIPLE"]:
        score += 20
        channel_overlap = True
        reasons.append(f"Channel overlap: {channel} (+20 pts)")

    # Estimate at-risk customers from persona dataset
    vuln_info = vuln_matrix.get(typology, {})
    vuln_auth_methods = vuln_info.get("vulnerable_auth_methods", ["SMS_OTP"])
    vuln_segs = vuln_info.get("vulnerable_segments", [segment])

    total_at_risk = 0
    for seg in vuln_segs:
        for geo in (geos if geos else ["SG"]):
            if geo in UOB_GEOGRAPHIES:
                for auth in vuln_auth_methods:
                    personas = get_customer_personas(segment=seg, geography=geo, auth_method=auth)
                    total_at_risk += sum(p.get("population_count", 0) for p in personas)

    at_risk_customers = max(total_at_risk, 1000)  # minimum floor for display

    if at_risk_customers > 10_000:
        score += 15
        reasons.append(f"High exposure: est. {at_risk_customers:,} customers at risk (+15 bonus pts)")

    passed = score >= GATE2_THRESHOLD
    explanation = f"{'✓' if passed else '✗'} {segment} customers in {'/'.join(geos[:3] or ['SG'])}; ~{at_risk_customers:,} at risk"

    return {
        "passed": passed,
        "score": min(100.0, score),
        "matched_segments": matched_segments,
        "estimated_at_risk_customers": at_risk_customers,
        "geographic_overlap": geographic_overlap,
        "channel_overlap": channel_overlap,
        "explanation": explanation,
        "reasons": reasons,
    }


# ── Gate 3: Control Gap Check ──────────────────────────────────────────────

def _gate3_control_gap(fraud_signal: Dict) -> Dict:
    """
    Question: Would our current controls fail to detect or prevent this fraud?
    Score >= GATE3_THRESHOLD to pass.
    """
    typology = fraud_signal.get("fraud_typology", "")
    victim_profile = fraud_signal.get("victim_profile", {})
    segment = victim_profile.get("customer_segment", "RETAIL")

    tm_rules = get_tm_rules()
    vuln_matrix = get_vulnerability_matrix()
    vuln_info = vuln_matrix.get(typology, {})

    score = 0.0
    matched_rule_ids = []
    reasons = []

    # Find TM rules covering this typology
    covering_rules = [
        r for r in tm_rules
        if typology in r.get("fraud_typologies_targeted", [])
    ]

    if not covering_rules:
        weighted_catch_rate = 0.0
        score += 30  # bonus: no rules at all
        reasons.append("No TM rules cover this fraud typology (+30 bonus pts)")
    else:
        matched_rule_ids = [r["rule_id"] for r in covering_rules]
        # Weighted catch rate: rules covering this typology specifically
        weights = [1.0 / len(covering_rules)] * len(covering_rules)
        weighted_catch_rate = sum(
            r.get("estimated_catch_rate_pct", 50.0) * w
            for r, w in zip(covering_rules, weights)
        )
        reasons.append(f"Covered by {len(covering_rules)} rule(s) with avg catch rate {weighted_catch_rate:.0f}%")

    undetected_pct = 100.0 - weighted_catch_rate if covering_rules else 100.0

    # Score based on undetected %
    if undetected_pct >= 70:
        score += 50
        reasons.append(f"High control gap: {undetected_pct:.0f}% undetected (+50 pts)")
    elif undetected_pct >= 50:
        score += 30
        reasons.append(f"Significant control gap: {undetected_pct:.0f}% undetected (+30 pts)")
    elif undetected_pct >= 30:
        score += 15
        reasons.append(f"Moderate control gap: {undetected_pct:.0f}% undetected (+15 pts)")
    else:
        reasons.append(f"Controls mostly adequate: only {undetected_pct:.0f}% undetected")

    # Auth vulnerability bonus
    vuln_auth = vuln_info.get("vulnerable_auth_methods", [])
    auth_vulnerable = "SMS_OTP" in vuln_auth and segment in ["RETAIL","MULTIPLE"]
    if auth_vulnerable:
        score += 25
        reasons.append("SMS_OTP auth vulnerability exploited by this attack (+25 pts)")

    passed = score >= GATE3_THRESHOLD
    explanation = (
        f"{'✓' if passed else '✗'} {undetected_pct:.0f}% of attacks undetected by existing TM rules; "
        f"auth vulnerability: {'YES' if auth_vulnerable else 'NO'}"
    )

    return {
        "passed": passed,
        "score": min(100.0, score),
        "matched_tm_rules": matched_rule_ids,
        "undetected_percentage": round(undetected_pct, 1),
        "auth_vulnerability": auth_vulnerable,
        "explanation": explanation,
        "reasons": reasons,
    }


# ── Composite Risk Score ───────────────────────────────────────────────────────

def _compute_composite_score(g1: Dict, g2: Dict, g3: Dict) -> float:
    """Weighted composite score per PRD-005 FR-005."""
    score = (
        g1["score"] * 0.25 +
        g2["score"] * 0.40 +
        g3["score"] * 0.35
    )
    return round(min(100.0, max(0.0, score)), 1)


def _score_to_priority(score: float) -> str:
    if score >= PRIORITY_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    elif score >= PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def _build_recommended_actions(fraud_signal: Dict, g1: Dict, g2: Dict, g3: Dict) -> List[str]:
    typology = fraud_signal.get("fraud_typology", "")
    at_risk = g2.get("estimated_at_risk_customers", 0)
    undetected = g3.get("undetected_percentage", 0)
    actions = []
    if g1.get("existing_tm_rule_match"):
        actions.append(f"Review and tune existing TM rules to cover {typology} variants")
    if at_risk > 50_000:
        actions.append(f"Issue advisory to {at_risk:,} at-risk customers via push notification")
    if undetected > 50:
        actions.append(f"Submit new TM detection scenario for {typology} pattern")
    if g3.get("auth_vulnerability"):
        actions.append("Accelerate device binding rollout for SMS_OTP users")
    actions.append("Generate full Risk Alert Document for compliance review")
    return actions


# ── Main Entry: Run Filtration ────────────────────────────────────────────────

def run_filtration(fraud_signal: Dict) -> Dict:
    """
    Run all 3 gates on a FraudSignal dict.
    Returns RelevanceAssessment dict and persists to database.
    """
    fraud_signal_id = fraud_signal.get("fraud_signal_id", str(uuid.uuid4()))
    logger.info("Running filtration for signal %s (%s)",
                fraud_signal_id, fraud_signal.get("fraud_typology",""))

    # Gate 1
    g1 = _gate1_novelty(fraud_signal)
    if not g1["passed"]:
        logger.info("Gate 1 FAILED for %s: %s", fraud_signal_id, g1["explanation"])
        assessment = _build_assessment(fraud_signal_id, g1, None, None, False)
        _persist_assessment(assessment, fraud_signal)
        return assessment

    # Gate 2
    g2 = _gate2_customer_exposure(fraud_signal)
    if not g2["passed"]:
        logger.info("Gate 2 FAILED for %s: %s", fraud_signal_id, g2["explanation"])
        assessment = _build_assessment(fraud_signal_id, g1, g2, None, False)
        _persist_assessment(assessment, fraud_signal)
        return assessment

    # Gate 3
    g3 = _gate3_control_gap(fraud_signal)
    overall_passed = g3["passed"]

    assessment = _build_assessment(fraud_signal_id, g1, g2, g3, overall_passed, fraud_signal)
    _persist_assessment(assessment, fraud_signal)

    if overall_passed:
        logger.info("ALL GATES PASSED for %s — priority: %s, score: %.1f",
                    fraud_signal_id, assessment["alert_priority"], assessment["composite_risk_score"])
    else:
        logger.info("Gate 3 FAILED for %s: %s", fraud_signal_id, g3["explanation"])

    return assessment


def _build_assessment(
    fraud_signal_id: str,
    g1: Dict,
    g2: Optional[Dict],
    g3: Optional[Dict],
    overall_passed: bool,
    fraud_signal: Optional[Dict] = None,
) -> Dict:
    composite = 0.0
    priority = "LOW"
    actions = []

    if g1 and g2 and g3:
        composite = _compute_composite_score(g1, g2, g3)
        priority = _score_to_priority(composite)
        if fraud_signal:
            actions = _build_recommended_actions(fraud_signal, g1, g2, g3)

    _g2 = g2 or {"passed": False, "score": 0.0, "matched_segments": [],
                  "estimated_at_risk_customers": 0, "geographic_overlap": False,
                  "channel_overlap": False, "explanation": "Not evaluated (Gate 1 failed)"}
    _g3 = g3 or {"passed": False, "score": 0.0, "matched_tm_rules": [],
                  "undetected_percentage": 0.0, "auth_vulnerability": False,
                  "explanation": "Not evaluated (Gate 1 or 2 failed)"}

    return {
        "assessment_id": str(uuid.uuid4()),
        "fraud_signal_id": fraud_signal_id,
        "assessed_at": datetime.utcnow().isoformat(),
        "gate1_novelty": g1,
        "gate2_customer_exposure": _g2,
        "gate3_control_gap": _g3,
        "overall_passed": overall_passed,
        "composite_risk_score": composite,
        "alert_priority": priority,
        "recommended_actions": actions,
    }


def _persist_assessment(assessment: Dict, fraud_signal: Optional[Dict] = None):
    insert_relevance_assessment(assessment)
    if fraud_signal:
        status = "ALERTED" if assessment["overall_passed"] else "DISCARDED"
        if fraud_signal.get("raw_signal_id"):
            update_raw_signal_status(fraud_signal["raw_signal_id"], status)
