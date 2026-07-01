"""
Phantom Signal — Monte Carlo Simulation & Impact Modelling (PRD-006)
Quantifies financial exposure to UOB given a fraud signal.
"""
import logging
import random
import uuid
import math
from datetime import datetime
from typing import Dict, List, Optional

from config import (
    ATTACK_REACH_FACTORS, DEFAULT_LOSS_PER_VICTIM,
    RANDOM_SEED, MONTE_CARLO_ITERATIONS,
)
from data.database import (
    get_customer_personas, get_fraud_history_by_typology,
    insert_simulation,
)
from data.synthetic_generator import get_vulnerability_matrix

logger = logging.getLogger(__name__)

_rng = random.Random(RANDOM_SEED)


# ── Step 1: Customer Exposure ─────────────────────────────────────────────────

def _compute_customer_exposure(fraud_signal: Dict) -> Dict:
    typology = fraud_signal.get("fraud_typology", "")
    victim_profile = fraud_signal.get("victim_profile", {})
    segment = victim_profile.get("customer_segment", "RETAIL")
    geos = fraud_signal.get("geographic_spread", []) or fraud_signal.get("geographic_origin", [])
    if not geos:
        geos = ["SG"]
    if isinstance(geos, str):
        geos = [geos]

    vuln_matrix = get_vulnerability_matrix()
    vuln_info = vuln_matrix.get(typology, {})
    vuln_segs = vuln_info.get("vulnerable_segments", [segment])
    vuln_auths = vuln_info.get("vulnerable_auth_methods", ["SMS_OTP"])

    by_segment: Dict[str, int] = {}
    by_geography: Dict[str, int] = {}
    total_at_risk = 0

    uob_geos = ["SG","MY","TH","ID","HK","VN"]
    active_geos = [g for g in geos if g in uob_geos] or ["SG"]

    for seg in vuln_segs:
        seg_total = 0
        for geo in active_geos:
            for auth in vuln_auths:
                personas = get_customer_personas(segment=seg, geography=geo, auth_method=auth)
                count = sum(p.get("population_count", 0) for p in personas)
                by_geography[geo] = by_geography.get(geo, 0) + count
                seg_total += count
        by_segment[seg] = seg_total
        total_at_risk += seg_total

    # Floor: always show at least some exposure
    if total_at_risk == 0:
        total_at_risk = 5_000
        by_segment = {segment: 5_000}
        by_geography = {geos[0]: 5_000}

    return {
        "total_at_risk": total_at_risk,
        "by_segment": by_segment,
        "by_geography": by_geography,
    }


# ── Step 2: Attack Reach & Victim Conversion ──────────────────────────────────

def _compute_estimated_victims(
    typology: str,
    total_at_risk: int,
) -> tuple[int, float]:
    reach_factor = ATTACK_REACH_FACTORS.get(typology, 0.05)
    estimated_reached = int(total_at_risk * reach_factor)

    # Historical victim conversion rate
    history = get_fraud_history_by_typology(typology)
    if history and estimated_reached > 0:
        victim_rate = min(len(history) / max(estimated_reached, 1), 0.30)
    else:
        vuln_matrix = get_vulnerability_matrix()
        vuln_info = vuln_matrix.get(typology, {})
        victim_rate = vuln_info.get("baseline_attack_success_pct", 10.0) / 100.0

    victim_rate = max(0.02, min(victim_rate, 0.30))
    estimated_victims = max(1, int(estimated_reached * victim_rate))
    return estimated_victims, victim_rate


# ── Step 3: Financial Impact ──────────────────────────────────────────────────

def _avg_loss_for_typology(typology: str) -> float:
    history = get_fraud_history_by_typology(typology)
    if history:
        losses = [h.get("loss_amount_sgd", 0) for h in history if h.get("loss_amount_sgd", 0) > 0]
        if losses:
            return sum(losses) / len(losses)
    return DEFAULT_LOSS_PER_VICTIM.get(typology, 4_500.0)


def _compute_financial_impact(
    typology: str,
    estimated_victims: int,
    assessment: Optional[Dict],
) -> Dict:
    avg_loss = _avg_loss_for_typology(typology)
    baseline = estimated_victims * avg_loss

    # With current controls
    undetected_pct = 50.0  # default
    if assessment:
        g3 = assessment.get("gate3_control_gap", {})
        undetected_pct = g3.get("undetected_percentage", 50.0)

    current_catch = (100.0 - undetected_pct) / 100.0
    with_current = baseline * (1.0 - current_catch * 0.7)  # partial prevention factor

    # With proposed controls (estimated 40-65% additional reduction)
    proposed_reduction = _rng.uniform(0.40, 0.65)
    with_proposed = with_current * (1.0 - proposed_reduction)

    methodology = (
        f"Estimated {estimated_victims:,} victims × avg SGD {avg_loss:,.0f} loss. "
        f"Current controls catch {current_catch*100:.0f}% (partial prevention factor 0.7). "
        f"Proposed interventions target additional {proposed_reduction*100:.0f}% reduction."
    )

    return {
        "baseline_exposure_sgd": round(baseline, 0),
        "with_current_controls_sgd": round(with_current, 0),
        "with_proposed_controls_sgd": round(with_proposed, 0),
        "methodology": methodology,
    }


# ── Monte Carlo ───────────────────────────────────────────────────────────────

def _monte_carlo(
    typology: str,
    total_at_risk: int,
    n_iterations: int = MONTE_CARLO_ITERATIONS,
) -> Dict:
    """Run Monte Carlo sensitivity analysis → P10/P50/P90."""
    mc_rng = random.Random(RANDOM_SEED + 1)

    reach_factor_base = ATTACK_REACH_FACTORS.get(typology, 0.05)
    avg_loss_base = _avg_loss_for_typology(typology)
    sigma_loss = math.sqrt(math.log(1 + (avg_loss_base * 0.8 / avg_loss_base) ** 2))
    mu_loss = math.log(avg_loss_base) - sigma_loss**2 / 2

    results = []
    for _ in range(n_iterations):
        reach_factor = reach_factor_base * mc_rng.uniform(0.70, 1.30)
        victim_rate = mc_rng.uniform(0.03, 0.25)
        loss = mc_rng.lognormvariate(mu_loss, sigma_loss)
        loss = min(loss, 500_000)

        victims = max(1, int(total_at_risk * reach_factor * victim_rate))
        exposure = victims * loss
        results.append(exposure)

    results.sort()
    p10 = results[int(n_iterations * 0.10)]
    p50 = results[int(n_iterations * 0.50)]
    p90 = results[int(n_iterations * 0.90)]

    return {
        "p10_sgd": round(p10, 0),
        "p50_sgd": round(p50, 0),
        "p90_sgd": round(p90, 0),
    }


# ── Proposed Interventions ────────────────────────────────────────────────────

INTERVENTION_TEMPLATES = {
    "SMS_SPOOFING": [
        {
            "intervention_type": "Device Binding Rollout",
            "description": "Migrate retail SMS_OTP users to device-bound authentication",
            "estimated_reduction_pct": 45.0,
            "implementation_effort": "HIGH",
        },
        {
            "intervention_type": "Real-time SMS Anomaly Detection",
            "description": "Flag and challenge transactions following SIM change events",
            "estimated_reduction_pct": 28.0,
            "implementation_effort": "MEDIUM",
        },
    ],
    "SEXTORTION": [
        {
            "intervention_type": "Customer Advisory Campaign",
            "description": "Targeted awareness push to male retail customers 18–35",
            "estimated_reduction_pct": 20.0,
            "implementation_effort": "LOW",
        },
        {
            "intervention_type": "Transaction Challenge Rule",
            "description": "OTP challenge for transfers > SGD 500 to new payees by affected demographic",
            "estimated_reduction_pct": 30.0,
            "implementation_effort": "MEDIUM",
        },
    ],
    "DEEPFAKE_CFO_FRAUD": [
        {
            "intervention_type": "Dual-Authorisation Policy",
            "description": "Require second approver for all wire transfers > SGD 50,000",
            "estimated_reduction_pct": 55.0,
            "implementation_effort": "MEDIUM",
        },
        {
            "intervention_type": "Callback Verification Protocol",
            "description": "Mandatory callback to registered number before high-value approvals",
            "estimated_reduction_pct": 40.0,
            "implementation_effort": "LOW",
        },
    ],
}


def _get_proposed_interventions(typology: str) -> List[Dict]:
    templates = INTERVENTION_TEMPLATES.get(typology, [
        {
            "intervention_type": "Enhanced TM Rule",
            "description": f"Deploy new TM detection scenario targeting {typology}",
            "estimated_reduction_pct": 25.0,
            "implementation_effort": "MEDIUM",
        },
        {
            "intervention_type": "Customer Advisory",
            "description": "Issue advisory to at-risk customer segments",
            "estimated_reduction_pct": 15.0,
            "implementation_effort": "LOW",
        },
    ])
    return templates


# ── Control Gap Analysis ───────────────────────────────────────────────────────

def _compute_control_gap(assessment: Optional[Dict]) -> Dict:
    if not assessment:
        return {
            "current_detection_rate_pct": 50.0,
            "undetected_rate_pct": 50.0,
            "failing_controls": ["No assessment available"],
        }
    g3 = assessment.get("gate3_control_gap", {})
    undetected = g3.get("undetected_percentage", 50.0)
    matched_rules = g3.get("matched_tm_rules", [])
    failing = [f"Rule {r} insufficient coverage" for r in matched_rules[:3]]
    if not matched_rules:
        failing = ["No TM rules cover this typology"]

    return {
        "current_detection_rate_pct": round(100.0 - undetected, 1),
        "undetected_rate_pct": round(undetected, 1),
        "failing_controls": failing,
    }


# ── Main Entry: Run Simulation ────────────────────────────────────────────────

def run_simulation(
    fraud_signal: Dict,
    assessment: Optional[Dict] = None,
    scenario_name: str = "Base Scenario",
) -> Dict:
    """
    Run full financial impact simulation for a FraudSignal.
    Returns SimulationResult dict and persists to database.
    """
    typology = fraud_signal.get("fraud_typology", "")
    fraud_signal_id = fraud_signal.get("fraud_signal_id", str(uuid.uuid4()))
    logger.info("Running simulation for %s (%s)", fraud_signal_id, typology)

    # Step 1: Customer exposure
    customer_exposure = _compute_customer_exposure(fraud_signal)
    total_at_risk = customer_exposure["total_at_risk"]

    # Step 2: Victims
    estimated_victims, victim_rate = _compute_estimated_victims(typology, total_at_risk)

    # Step 3: Financial impact
    financial_impact = _compute_financial_impact(typology, estimated_victims, assessment)

    # Step 4: Monte Carlo
    mc = _monte_carlo(typology, total_at_risk)
    financial_impact.update(mc)

    # Step 5: Control gap
    control_gap = _compute_control_gap(assessment)

    # Step 6: Proposed interventions
    proposed_interventions = _get_proposed_interventions(typology)

    simulation = {
        "simulation_id": str(uuid.uuid4()),
        "fraud_signal_id": fraud_signal_id,
        "run_at": datetime.utcnow().isoformat(),
        "scenario_name": scenario_name,
        "customer_exposure": customer_exposure,
        "financial_impact": financial_impact,
        "control_gap_analysis": control_gap,
        "proposed_interventions": proposed_interventions,
        # metadata for display
        "estimated_victims": estimated_victims,
        "victim_rate_pct": round(victim_rate * 100, 1),
        "avg_loss_sgd": round(_avg_loss_for_typology(typology), 0),
    }

    insert_simulation(simulation)
    logger.info(
        "Simulation complete: baseline SGD %.0f (P10=%.0f, P90=%.0f)",
        financial_impact["baseline_exposure_sgd"],
        financial_impact["p10_sgd"],
        financial_impact["p90_sgd"],
    )
    return simulation
