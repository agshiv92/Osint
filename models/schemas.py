"""
Phantom Signal — Pydantic Data Models
All schemas as defined in PRD-001. Used throughout the pipeline.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────────

class SourceCategory(str, Enum):
    REGULATORY  = "REGULATORY"
    THREAT_INTEL = "THREAT_INTEL"
    OPEN_WEB    = "OPEN_WEB"
    DARK_WEB    = "DARK_WEB"

class ProcessingStatus(str, Enum):
    PENDING    = "PENDING"
    NORMALIZED = "NORMALIZED"
    FILTERED   = "FILTERED"
    ALERTED    = "ALERTED"
    DISCARDED  = "DISCARDED"

class SeverityLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

class CustomerSegment(str, Enum):
    RETAIL                 = "RETAIL"
    SME                    = "SME"
    TRADE_FINANCE          = "TRADE_FINANCE"
    CORRESPONDENT_BANKING  = "CORRESPONDENT_BANKING"
    MULTIPLE               = "MULTIPLE"

class Channel(str, Enum):
    MOBILE           = "MOBILE"
    INTERNET_BANKING = "INTERNET_BANKING"
    BRANCH           = "BRANCH"
    ATM              = "ATM"
    MULTIPLE         = "MULTIPLE"

class CredibilityLevel(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

class AuthMethod(str, Enum):
    SMS_OTP      = "SMS_OTP"
    APP_OTP      = "APP_OTP"
    DEVICE_BOUND = "DEVICE_BOUND"
    BIOMETRIC    = "BIOMETRIC"

class DigitalUsage(str, Enum):
    HIGH   = "HIGH"
    MEDIUM = "MEDIUM"
    LOW    = "LOW"

class RuleType(str, Enum):
    TM_DETECTION      = "TM_DETECTION"
    CUSTOMER_FRICTION = "CUSTOMER_FRICTION"
    POLICY_CHANGE     = "POLICY_CHANGE"
    ADVISORY          = "ADVISORY"

class TargetLayer(str, Enum):
    TRANSACTION_MONITORING = "TRANSACTION_MONITORING"
    AUTHENTICATION         = "AUTHENTICATION"
    CUSTOMER_COMMS         = "CUSTOMER_COMMS"
    POLICY                 = "POLICY"

class DeploymentRisk(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"

class RiskRating(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


# ── PRD-001 §3.1: RawSignal ───────────────────────────────────────────────────

class RawSignal(BaseModel):
    signal_id:          str = Field(default_factory=lambda: str(uuid.uuid4()))
    ingested_at:        str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source_category:    str = "REGULATORY"
    source_name:        str = ""
    source_url:         str = ""
    raw_content:        str = ""
    content_hash:       str = ""
    language:           str = "en"
    processing_status:  str = ProcessingStatus.PENDING
    title:              Optional[str] = None
    publication_date:   Optional[str] = None


# ── PRD-001 §3.2: FraudSignal ─────────────────────────────────────────────────

class VictimProfile(BaseModel):
    age_range:        Optional[str] = None
    customer_segment: str = "RETAIL"
    geography:        List[str] = Field(default_factory=list)
    channel:          str = "MULTIPLE"

class FraudSignal(BaseModel):
    fraud_signal_id:         str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_signal_id:           Optional[str] = None
    detected_at:             str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    fraud_typology:          str = ""
    fraud_description:       str = ""
    attack_vector:           str = ""
    victim_profile:          VictimProfile = Field(default_factory=VictimProfile)
    financial_mechanism:     Optional[str] = None
    geographic_origin:       List[str] = Field(default_factory=list)
    geographic_spread:       List[str] = Field(default_factory=list)
    first_reported_globally: Optional[str] = None
    severity_estimate:       str = "MEDIUM"
    novelty_score:           float = 0.5
    confidence_score:        float = 0.5
    source_credibility:      str = "MEDIUM"
    raw_evidence:            Optional[str] = None


# ── PRD-001 §3.3: RelevanceAssessment ────────────────────────────────────────

class Gate1Result(BaseModel):
    passed:                bool = False
    score:                 float = 0.0
    existing_tm_rule_match: bool = False
    similar_signal_ids:    List[str] = Field(default_factory=list)
    explanation:           str = ""

class Gate2Result(BaseModel):
    passed:                   bool = False
    score:                    float = 0.0
    matched_segments:         List[str] = Field(default_factory=list)
    estimated_at_risk_customers: int = 0
    geographic_overlap:       bool = False
    channel_overlap:          bool = False
    explanation:              str = ""

class Gate3Result(BaseModel):
    passed:               bool = False
    score:                float = 0.0
    matched_tm_rules:     List[str] = Field(default_factory=list)
    undetected_percentage: float = 0.0
    auth_vulnerability:   bool = False
    explanation:          str = ""

class RelevanceAssessment(BaseModel):
    assessment_id:       str = Field(default_factory=lambda: str(uuid.uuid4()))
    fraud_signal_id:     str = ""
    assessed_at:         str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    gate1_novelty:       Gate1Result = Field(default_factory=Gate1Result)
    gate2_customer_exposure: Gate2Result = Field(default_factory=Gate2Result)
    gate3_control_gap:   Gate3Result = Field(default_factory=Gate3Result)
    overall_passed:      bool = False
    composite_risk_score: float = 0.0
    alert_priority:      str = "LOW"
    recommended_actions: List[str] = Field(default_factory=list)


# ── PRD-001 §3.4: SimulationResult ───────────────────────────────────────────

class CustomerExposure(BaseModel):
    total_at_risk:  int = 0
    by_segment:     Dict[str, int] = Field(default_factory=dict)
    by_geography:   Dict[str, int] = Field(default_factory=dict)

class FinancialImpact(BaseModel):
    baseline_exposure_sgd:       float = 0.0
    with_current_controls_sgd:   float = 0.0
    with_proposed_controls_sgd:  float = 0.0
    p10_sgd:                     float = 0.0
    p50_sgd:                     float = 0.0
    p90_sgd:                     float = 0.0
    methodology:                 str = ""

class ControlGapAnalysis(BaseModel):
    current_detection_rate_pct: float = 0.0
    undetected_rate_pct:         float = 0.0
    failing_controls:            List[str] = Field(default_factory=list)

class ProposedIntervention(BaseModel):
    intervention_type:       str = ""
    description:             str = ""
    estimated_reduction_pct: float = 0.0
    implementation_effort:   str = "MEDIUM"

class SimulationResult(BaseModel):
    simulation_id:       str = Field(default_factory=lambda: str(uuid.uuid4()))
    fraud_signal_id:     str = ""
    run_at:              str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    scenario_name:       str = ""
    customer_exposure:   CustomerExposure = Field(default_factory=CustomerExposure)
    financial_impact:    FinancialImpact = Field(default_factory=FinancialImpact)
    control_gap_analysis: ControlGapAnalysis = Field(default_factory=ControlGapAnalysis)
    proposed_interventions: List[ProposedIntervention] = Field(default_factory=list)


# ── PRD-001 §3.5: RiskAlertDocument ──────────────────────────────────────────

class RecommendedActions(BaseModel):
    immediate:   List[str] = Field(default_factory=list)
    short_term:  List[str] = Field(default_factory=list)
    strategic:   List[str] = Field(default_factory=list)

class AlertRouting(BaseModel):
    compliance_team:    bool = False
    fraud_risk_team:    bool = False
    tm_analytics_team:  bool = False
    policy_controls_team: bool = False

class AlertDocument(BaseModel):
    executive_summary:    str = ""
    threat_description:   str = ""
    uob_relevance:        str = ""
    customer_impact:      str = ""
    financial_exposure:   str = ""
    current_control_gaps: str = ""
    recommended_actions:  RecommendedActions = Field(default_factory=RecommendedActions)
    intervention_rules:   List[Dict[str, Any]] = Field(default_factory=list)
    simulation_summary:   str = ""
    evidence_sources:     List[str] = Field(default_factory=list)
    confidence_rating:    str = "MEDIUM"
    analyst_notes:        str = ""

class RiskAlertDocument(BaseModel):
    alert_id:        str = Field(default_factory=lambda: str(uuid.uuid4()))
    fraud_signal_id: str = ""
    assessment_id:   str = ""
    simulation_id:   Optional[str] = None
    generated_at:    str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    priority:        str = "LOW"
    document:        AlertDocument = Field(default_factory=AlertDocument)
    output_formats:  List[str] = Field(default_factory=lambda: ["PDF", "JSON"])
    routing:         AlertRouting = Field(default_factory=AlertRouting)
    pdf_path:        Optional[str] = None


# ── PRD-001 §3.6: InterventionRule ───────────────────────────────────────────

class InterventionRule(BaseModel):
    rule_id:              str = Field(default_factory=lambda: str(uuid.uuid4()))
    fraud_signal_id:      str = ""
    rule_type:            str = "TM_DETECTION"
    target_layer:         str = "TRANSACTION_MONITORING"
    rule_description:     str = ""
    rule_logic:           str = ""
    trigger_conditions:   List[str] = Field(default_factory=list)
    expected_impact_pct:  float = 10.0
    deployment_risk:      str = "MEDIUM"
    approval_required:    bool = True
    auto_deployable:      bool = False


# ── PRD-001 §3.7: MockCustomerPersona ────────────────────────────────────────

class MockCustomerPersona(BaseModel):
    persona_id:                str = Field(default_factory=lambda: str(uuid.uuid4()))
    segment:                   str = "RETAIL"
    sub_segment:               str = ""
    geography:                 str = "SG"
    age_band:                  str = "26-35"
    digital_channel_usage:     str = "HIGH"
    auth_method:               str = "SMS_OTP"
    avg_transaction_amount_sgd: float = 500.0
    monthly_transaction_count: int = 10
    risk_rating:               str = "LOW"
    population_count:          int = 0


# ── PRD-001 §3.8: MockTMRule ─────────────────────────────────────────────────

class MockTMRule(BaseModel):
    rule_id:                    str = ""
    rule_name:                  str = ""
    fraud_typologies_targeted:  List[str] = Field(default_factory=list)
    detection_trigger:          str = ""
    threshold_description:      str = ""
    channel_coverage:           List[str] = Field(default_factory=list)
    estimated_catch_rate_pct:   float = 50.0
    last_updated:               str = ""
    active:                     bool = True
