# PHANTOM SIGNAL — OSInt Early Warning Framework
## PRD Master Document · v1.0
### UOB Group Compliance · Innovation Challenge POC

**Platform:** Google Cloud (Vertex AI, Gemini 1.5 Pro, Cloud Run, BigQuery, GCS)
**Data:** Synthetic / mock data only (POC scope)
**Primary deliverable:** Structured AI-generated Risk Alert Document
**Author:** Project Owner / PM
**Status:** Draft for AI-assisted build

---

## PROJECT PLAN

### Epics & Sprints

| Sprint | Duration | Epic | Deliverable |
|--------|----------|------|-------------|
| Sprint 1 | Week 1–2 | Data Ingestion | OSInt crawler for SPF + MAS + FBI IC3; raw signal store in GCS |
| Sprint 2 | Week 3–4 | Normalization | Gemini-powered extraction → structured FraudSignal schema; BigQuery table |
| Sprint 3 | Week 5–6 | Filtration | 3-gate relevance engine; risk scoring; alert queue |
| Sprint 4 | Week 7–8 | Synthetic Data | Mock customer personas, TM rules, historical loss data generators |
| Sprint 5 | Week 9–10 | Simulation | Customer exposure model; control-gap tester; S$ impact calculator |
| Sprint 6 | Week 11–12 | Alert Document | Gemini-generated structured Risk Alert Document; PDF/JSON output |
| Sprint 7 | Week 13–14 | Intervention Rules | Rule generator; severity-based routing; auto-approve vs human-review split |
| Sprint 8 | Week 15–16 | Demo UI | Streamlit dashboard; end-to-end demo flow; POC submission packaging |

### Phase Gates
- **Phase 1 Gate (Week 8):** Pipeline runs end-to-end on synthetic signals; alert document generated for one fraud type (SMS spoofing)
- **Phase 2 Gate (Week 16):** Full POC with simulation, intervention rules, dashboard, and at least 3 fraud typologies demonstrated

---

## PRD INDEX

| ID | Component | Priority |
|----|-----------|----------|
| PRD-001 | System Architecture & Data Schemas | P0 |
| PRD-002 | OSInt Data Ingestion Agent | P0 |
| PRD-003 | Synthetic Data Generator | P0 |
| PRD-004 | AI Normalization & Schema Layer | P0 |
| PRD-005 | Relevance Filtration Engine (3-Gate) | P0 |
| PRD-006 | Simulation & Impact Modelling Engine | P1 |
| PRD-007 | Risk Alert Document Generator | P0 |
| PRD-008 | Intervention Rules Engine | P1 |
| PRD-009 | Orchestration & Pipeline Management | P1 |
| PRD-010 | Data Storage & Knowledge Base | P0 |
| PRD-011 | Demo Dashboard (Streamlit) | P1 |

---

---

# PRD-001: SYSTEM ARCHITECTURE & DATA SCHEMAS
**Priority:** P0 | **Sprint:** 1

## 1. Objective
Define the canonical data schemas, system boundaries, component interfaces, and technology decisions that all other PRDs reference. This PRD is the single source of truth for data contracts between components.

## 2. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | Gemini 1.5 Pro via Vertex AI | Normalization, classification, alert generation |
| Orchestration | Cloud Composer (Airflow) or Cloud Run Jobs | Pipeline scheduling and task management |
| Raw storage | Google Cloud Storage (GCS) | Raw OSInt HTML/JSON/text blobs |
| Structured store | BigQuery | Processed signals, alert history, mock personas |
| Vector store | Vertex AI Vector Search | Semantic deduplication and similarity matching |
| Compute | Cloud Run | Microservices for each pipeline stage |
| Secrets | Secret Manager | API keys for OSInt sources |
| Delivery | Streamlit on Cloud Run | Demo dashboard |
| Output format | PDF + JSON | Risk Alert Document |

## 3. Core Data Schemas

### 3.1 RawSignal (ingested from OSInt sources)
```json
{
  "signal_id": "uuid-v4",
  "ingested_at": "ISO-8601 timestamp",
  "source_category": "enum: REGULATORY | THREAT_INTEL | OPEN_WEB | DARK_WEB",
  "source_name": "string (e.g. SPF_ADVISORY)",
  "source_url": "string",
  "raw_content": "string (full text)",
  "content_hash": "sha256 (for deduplication)",
  "language": "string (ISO 639-1)",
  "processing_status": "enum: PENDING | NORMALIZED | FILTERED | ALERTED | DISCARDED"
}
```

### 3.2 FraudSignal (output of normalization layer)
```json
{
  "fraud_signal_id": "uuid-v4",
  "raw_signal_id": "uuid-v4 (FK to RawSignal)",
  "detected_at": "ISO-8601 timestamp",
  "fraud_typology": "string (e.g. SMS_SPOOFING | SIM_SWAP | SEXTORTION | DEEPFAKE_CFO | TBML | PHISHING)",
  "fraud_description": "string (2–3 sentence normalized summary)",
  "attack_vector": "string (e.g. Social engineering via SMS link)",
  "victim_profile": {
    "age_range": "string (e.g. 25-40)",
    "customer_segment": "enum: RETAIL | SME | TRADE_FINANCE | CORRESPONDENT_BANKING | MULTIPLE",
    "geography": ["array of ISO country codes"],
    "channel": "enum: MOBILE | INTERNET_BANKING | BRANCH | ATM | MULTIPLE"
  },
  "financial_mechanism": "string (e.g. Credential theft → unauthorized wire transfer)",
  "geographic_origin": ["array of ISO country codes"],
  "geographic_spread": ["array of ISO country codes"],
  "first_reported_globally": "ISO-8601 date (estimated)",
  "severity_estimate": "enum: LOW | MEDIUM | HIGH | CRITICAL",
  "novelty_score": "float 0.0–1.0 (1.0 = completely new typology)",
  "confidence_score": "float 0.0–1.0 (LLM confidence in extraction quality)",
  "source_credibility": "enum: HIGH | MEDIUM | LOW",
  "raw_evidence": "string (key excerpt from raw content)"
}
```

### 3.3 RelevanceAssessment (output of filtration engine)
```json
{
  "assessment_id": "uuid-v4",
  "fraud_signal_id": "uuid-v4 (FK)",
  "assessed_at": "ISO-8601 timestamp",
  "gate1_novelty": {
    "passed": "boolean",
    "existing_tm_rule_match": "boolean",
    "similar_signal_ids": ["array of fraud_signal_ids"],
    "explanation": "string"
  },
  "gate2_customer_exposure": {
    "passed": "boolean",
    "matched_segments": ["array of segment names"],
    "estimated_at_risk_customers": "integer",
    "geographic_overlap": "boolean",
    "channel_overlap": "boolean",
    "explanation": "string"
  },
  "gate3_control_gap": {
    "passed": "boolean",
    "matched_tm_rules": ["array of rule IDs that would catch this"],
    "undetected_percentage": "float 0–100",
    "auth_vulnerability": "boolean",
    "explanation": "string"
  },
  "overall_passed": "boolean (all 3 gates must pass)",
  "composite_risk_score": "float 0.0–100.0",
  "alert_priority": "enum: LOW | MEDIUM | HIGH | CRITICAL",
  "recommended_actions": ["array of action strings"]
}
```

### 3.4 SimulationResult (output of simulation engine)
```json
{
  "simulation_id": "uuid-v4",
  "fraud_signal_id": "uuid-v4 (FK)",
  "run_at": "ISO-8601 timestamp",
  "scenario_name": "string",
  "customer_exposure": {
    "total_at_risk": "integer",
    "by_segment": {"RETAIL": "int", "SME": "int", "TRADE_FINANCE": "int"},
    "by_geography": {"SG": "int", "MY": "int", "TH": "int", "ID": "int"}
  },
  "financial_impact": {
    "baseline_exposure_sgd": "float",
    "with_current_controls_sgd": "float",
    "with_proposed_controls_sgd": "float",
    "methodology": "string"
  },
  "control_gap_analysis": {
    "current_detection_rate_pct": "float",
    "undetected_rate_pct": "float",
    "failing_controls": ["array of control descriptions"]
  },
  "proposed_interventions": [
    {
      "intervention_type": "string",
      "description": "string",
      "estimated_reduction_pct": "float",
      "implementation_effort": "enum: LOW | MEDIUM | HIGH"
    }
  ]
}
```

### 3.5 RiskAlertDocument (primary output)
```json
{
  "alert_id": "uuid-v4",
  "fraud_signal_id": "uuid-v4 (FK)",
  "assessment_id": "uuid-v4 (FK)",
  "simulation_id": "uuid-v4 (FK, optional)",
  "generated_at": "ISO-8601 timestamp",
  "priority": "enum: LOW | MEDIUM | HIGH | CRITICAL",
  "document": {
    "executive_summary": "string (3–4 sentences for leadership)",
    "threat_description": "string (detailed fraud narrative)",
    "uob_relevance": "string (why this matters to UOB specifically)",
    "customer_impact": "string (who is at risk and how many)",
    "financial_exposure": "string (S$ impact narrative)",
    "current_control_gaps": "string (what existing controls miss)",
    "recommended_actions": {
      "immediate": ["array of actions (< 24 hours)"],
      "short_term": ["array of actions (1–7 days)"],
      "strategic": ["array of actions (1–4 weeks)"]
    },
    "intervention_rules": ["array of InterventionRule objects"],
    "simulation_summary": "string (if simulation run)",
    "evidence_sources": ["array of URLs / source names"],
    "confidence_rating": "enum: HIGH | MEDIUM | LOW",
    "analyst_notes": "string (auto-generated caveats)"
  },
  "output_formats": ["PDF", "JSON"],
  "routing": {
    "compliance_team": "boolean",
    "fraud_risk_team": "boolean",
    "tm_analytics_team": "boolean",
    "policy_controls_team": "boolean"
  }
}
```

### 3.6 InterventionRule
```json
{
  "rule_id": "uuid-v4",
  "fraud_signal_id": "uuid-v4 (FK)",
  "rule_type": "enum: TM_DETECTION | CUSTOMER_FRICTION | POLICY_CHANGE | ADVISORY",
  "target_layer": "enum: TRANSACTION_MONITORING | AUTHENTICATION | CUSTOMER_COMMS | POLICY",
  "rule_description": "string",
  "rule_logic": "string (pseudocode or natural language logic)",
  "trigger_conditions": ["array of strings"],
  "expected_impact_pct": "float",
  "deployment_risk": "enum: LOW | MEDIUM | HIGH",
  "approval_required": "boolean",
  "auto_deployable": "boolean"
}
```

### 3.7 MockCustomerPersona (synthetic data)
```json
{
  "persona_id": "uuid-v4",
  "segment": "enum: RETAIL | SME | TRADE_FINANCE | CORRESPONDENT_BANKING",
  "sub_segment": "string",
  "geography": "ISO country code",
  "age_band": "string",
  "digital_channel_usage": "enum: HIGH | MEDIUM | LOW",
  "auth_method": "enum: SMS_OTP | APP_OTP | DEVICE_BOUND | BIOMETRIC",
  "avg_transaction_amount_sgd": "float",
  "monthly_transaction_count": "integer",
  "risk_rating": "enum: LOW | MEDIUM | HIGH",
  "population_count": "integer (synthetic count this persona represents)"
}
```

### 3.8 MockTMRule (synthetic TM rule)
```json
{
  "rule_id": "string",
  "rule_name": "string",
  "fraud_typologies_targeted": ["array of typology strings"],
  "detection_trigger": "string (natural language)",
  "threshold_description": "string",
  "channel_coverage": ["array of channel strings"],
  "estimated_catch_rate_pct": "float",
  "last_updated": "ISO-8601 date",
  "active": "boolean"
}
```

## 4. System Boundaries
- **In scope for POC:** OSInt ingestion from public URLs, normalization, filtration, simulation using synthetic data, risk alert document generation, Streamlit demo
- **Out of scope for POC:** Real UOB data integration, production deployment, MAS regulatory submission, real-time streaming (batch only)

## 5. Acceptance Criteria
- All schemas implemented as Python dataclasses or Pydantic models
- BigQuery tables created from schemas with correct types
- All component PRDs reference this document's schema definitions

---

---

# PRD-002: OSInt DATA INGESTION AGENT
**Priority:** P0 | **Sprint:** 1

## 1. Objective
Build an autonomous crawling agent that fetches raw intelligence from external OSInt sources, deduplicates content, and stores it as RawSignal records in GCS and BigQuery.

## 2. Functional Requirements

### FR-001: Source Coverage (POC Phase 1)
The agent MUST support the following sources at minimum for the POC:
- **SPF Scam Advisories:** `https://www.police.gov.sg/Advisories/Scams` — web crawl, parse HTML
- **MAS News & Circulars:** `https://www.mas.gov.sg/news` — web crawl, parse HTML
- **FBI IC3 Alerts:** `https://www.ic3.gov/Media/News` — web crawl, parse HTML
- **ENISA Publications RSS:** `https://www.enisa.europa.eu/publications` — RSS feed parse
- **AlienVault OTX Pulses:** `https://otx.alienvault.com/api/v1/pulses/subscribed` — REST API (requires API key in Secret Manager)
- **Reddit r/Scams:** `https://www.reddit.com/r/Scams/new.json` — JSON API (no auth needed)

### FR-002: Crawl Scheduling
- Regulatory sources (SPF, MAS, FBI, ENISA): crawl every 6 hours via Cloud Scheduler → Cloud Run Job
- Threat intel feeds (AlienVault OTX): crawl every 1 hour
- Social sources (Reddit): crawl every 2 hours
- Each crawl run must be idempotent — re-crawling must not create duplicate records

### FR-003: Content Extraction
For each source, extract:
- Full text content (strip HTML tags, keep structure)
- Publication date (parse from page metadata, header, or body)
- Source URL (canonical)
- Title / headline
- Any linked PDF content (download and extract text via `pdfplumber`)

### FR-004: Deduplication
- Compute SHA-256 hash of `source_url + publication_date + first_500_chars_of_content`
- Before writing, check BigQuery `raw_signals` table for matching `content_hash`
- If duplicate found: skip write, log as `DUPLICATE_SKIPPED`
- If new: write to GCS (raw blob) + BigQuery (RawSignal record)

### FR-005: GCS Storage Layout
```
gs://{bucket}/raw_signals/
  {YYYY}/{MM}/{DD}/
    {source_category}/
      {signal_id}.json
```

### FR-006: Error Handling
- On HTTP error (4xx, 5xx): retry 3 times with exponential backoff (2s, 4s, 8s)
- On persistent failure: write ERROR record to BigQuery `ingestion_errors` table with source, timestamp, error message
- On rate limit (429): wait 60 seconds, then retry once
- Never crash the entire crawl job on a single source failure — log and continue

### FR-007: Keyword Filtering (pre-normalization noise reduction)
Before writing to BigQuery, apply keyword filter. Only write signals that contain at least ONE of the following keyword groups in their text:
- Group A (fraud types): `fraud`, `scam`, `phishing`, `spoofing`, `sextortion`, `deepfake`, `malware`, `ransomware`, `AML`, `money laundering`, `impersonation`
- Group B (financial): `bank`, `banking`, `financial institution`, `payment`, `transfer`, `account`, `credential`, `OTP`, `wire`
- Group C (impact): `victim`, `loss`, `stolen`, `compromised`, `breach`, `attack`
- Filter logic: (ANY from Group A) AND (ANY from Group B OR ANY from Group C)
- Signals failing this filter: set `processing_status = DISCARDED`, write to BigQuery with reason `PRE_FILTER_KEYWORD`

### FR-008: Volume Guardrails
- Maximum 500 new RawSignal records per crawl run (safety cap)
- If exceeded: log warning, process first 500 by publication date descending, defer rest to next run

## 3. Non-Functional Requirements
- Crawl agent must complete a full run in under 10 minutes for all sources
- Must handle SSL certificate errors gracefully (log and skip, do not crash)
- All API keys stored in Google Secret Manager, never in code or environment variables directly
- Respect `robots.txt` for all web crawls

## 4. Technology
- **Language:** Python 3.11
- **HTTP client:** `httpx` (async) with `tenacity` for retry logic
- **HTML parsing:** `BeautifulSoup4`
- **PDF extraction:** `pdfplumber`
- **RSS parsing:** `feedparser`
- **Compute:** Cloud Run Job (triggered by Cloud Scheduler)
- **Storage:** GCS (`google-cloud-storage`) + BigQuery (`google-cloud-bigquery`)

## 5. Interfaces
- **Output:** Writes to BigQuery table `phantom_signal.raw_signals` and GCS bucket `phantom-signal-raw`
- **Input:** Cloud Scheduler HTTP trigger or manual invocation
- **Logging:** Google Cloud Logging with structured JSON logs

## 6. Acceptance Criteria
- [ ] Crawl runs successfully for all 6 sources without error
- [ ] Deduplication prevents duplicate records across runs
- [ ] Keyword filter rejects >60% of non-fraud content (validated on test set of 50 articles)
- [ ] All errors logged to `ingestion_errors` table without crashing the run
- [ ] A full crawl run completes in <10 minutes
- [ ] Content from SPF Dec 2021 SMS spoofing advisory is correctly ingested when URL is provided

---

---

# PRD-003: SYNTHETIC DATA GENERATOR
**Priority:** P0 | **Sprint:** 4

## 1. Objective
Generate realistic synthetic UOB-like data for customer personas, TM rules, and historical fraud losses. This module replaces real internal data for the POC and must be seeded consistently so demo results are reproducible.

## 2. Functional Requirements

### FR-001: Synthetic Customer Persona Dataset
Generate a dataset of `MockCustomerPersona` records representing UOB Singapore's retail and SME customer base.

**Persona distribution (total synthetic population: 500,000):**

| Segment | Sub-segment | Geography | Count | Auth Method | Avg Txn SGD | Digital Usage |
|---------|-------------|-----------|-------|-------------|-------------|---------------|
| RETAIL | Mass Retail | SG | 180,000 | SMS_OTP | 500 | HIGH |
| RETAIL | Mass Affluent | SG | 60,000 | APP_OTP | 3,000 | HIGH |
| RETAIL | Priority | SG | 15,000 | DEVICE_BOUND | 12,000 | HIGH |
| RETAIL | Mass Retail | MY | 85,000 | SMS_OTP | 800 | MEDIUM |
| RETAIL | Mass Retail | TH | 40,000 | SMS_OTP | 600 | MEDIUM |
| RETAIL | Mass Retail | ID | 55,000 | SMS_OTP | 400 | LOW |
| SME | Small Business | SG | 30,000 | APP_OTP | 8,000 | MEDIUM |
| SME | Mid-Market | SG | 12,000 | DEVICE_BOUND | 45,000 | MEDIUM |
| TRADE_FINANCE | Commodity | SG | 3,000 | DEVICE_BOUND | 250,000 | LOW |
| TRADE_FINANCE | Import/Export | SG | 8,000 | DEVICE_BOUND | 120,000 | LOW |
| CORRESPONDENT_BANKING | International | SG | 2,000 | DEVICE_BOUND | 1,000,000 | LOW |

**Age band distribution (for RETAIL segments):**
- 18–25: 12%
- 26–35: 28%
- 36–45: 25%
- 46–55: 20%
- 56+: 15%

### FR-002: Synthetic TM Rule Dataset
Generate 25 `MockTMRule` records representing UOB's existing transaction monitoring rules.

**Required rules to include (minimum):**

| Rule ID | Rule Name | Targets | Catch Rate % |
|---------|-----------|---------|--------------|
| TM-001 | High-value new payee | Large transfers to first-time payees | 45 |
| TM-002 | Rapid sequential transfers | Multiple transfers in 24h | 62 |
| TM-003 | Crypto exchange detection | Transfers to known crypto platforms | 70 |
| TM-004 | Overseas wire anomaly | Unusual cross-border transfer pattern | 55 |
| TM-005 | Account takeover indicators | Login from new device + immediate transfer | 78 |
| TM-006 | Night-time high-value | Transfers >SGD 5,000 between 10PM–5AM | 35 |
| TM-007 | Structured transactions | Multiple sub-threshold transfers | 60 |
| TM-008 | Gift card purchase pattern | Repeated gift card top-ups | 40 |
| TM-009 | Invoice discrepancy | Trade finance invoices >20% above market | 50 |
| TM-010 | PEP transaction monitoring | Any transfer involving PEP-linked accounts | 90 |

**Remaining 15 rules:** Generate programmatically with random but realistic parameters covering:
- Shell company indicators, smurfing patterns, round-number transactions, geographic anomalies, dormant account reactivation, velocity spikes

### FR-003: Synthetic Historical Fraud Loss Dataset
Generate 500 historical fraud incident records with the following fields:
- `incident_id`, `fraud_typology`, `detection_date`, `loss_amount_sgd`, `customer_segment`, `geography`, `detection_method` (TM rule or manual), `resolution_days`, `was_recovered`, `recovery_amount_sgd`

**Distribution:**
- SMS phishing / spoofing: 35% of incidents
- Investment scams: 20%
- E-commerce fraud: 15%
- Account takeover: 12%
- SIM swap: 8%
- CEO/BEC fraud: 7%
- Other: 3%

**Loss distribution:** Log-normal with mean SGD 4,500, std dev SGD 8,000, cap at SGD 200,000

### FR-004: Seed Consistency
- All generators must accept a `random_seed` parameter (default: `42`)
- Given the same seed, outputs must be identical across runs
- Write generated datasets to BigQuery:
  - `phantom_signal.mock_customer_personas`
  - `phantom_signal.mock_tm_rules`
  - `phantom_signal.mock_fraud_history`
- Also export as CSV to GCS: `gs://phantom-signal-synthetic/`

### FR-005: Fraud Typology Vulnerability Matrix
Generate a `FraudVulnerabilityMatrix` — a lookup table mapping each fraud typology to:
- Which customer segments are vulnerable (Y/N)
- Which auth methods are vulnerable (Y/N)
- Which geographies have highest exposure
- Which existing TM rules (if any) already cover it
- Baseline attack success rate (%)

This matrix is consumed by the Filtration Engine (PRD-005) and Simulation Engine (PRD-006).

## 3. Acceptance Criteria
- [ ] All three datasets generated and written to BigQuery with correct schema
- [ ] Re-running with same seed produces identical outputs
- [ ] Vulnerability matrix covers at minimum 10 fraud typologies
- [ ] Synthetic loss distribution passes a basic sanity check (mean between SGD 3,000–6,000)
- [ ] A query for "SMS spoofing vulnerable retail customers using SMS OTP in Singapore" returns between 150,000–200,000 from the persona dataset

---

---

# PRD-004: AI NORMALIZATION & SCHEMA LAYER
**Priority:** P0 | **Sprint:** 2

## 1. Objective
Use Gemini 1.5 Pro to transform unstructured raw OSInt text into structured `FraudSignal` records. This is the core AI extraction step that turns noise into usable intelligence.

## 2. Functional Requirements

### FR-001: Trigger Condition
- Runs as a Cloud Run Job triggered by completion of ingestion run (Pub/Sub message)
- Processes all `RawSignal` records with `processing_status = PENDING`
- Processes in batches of 20 records per Gemini API call (to manage token costs and rate limits)

### FR-002: Gemini Prompt Specification
The following prompt structure MUST be used. Do not deviate without updating this PRD.

**System prompt:**
```
You are a financial crime intelligence analyst specializing in fraud typology extraction for a major Singapore bank. Your job is to read raw text from regulatory advisories, threat intelligence reports, and news articles, and extract structured fraud intelligence.

You MUST return ONLY valid JSON matching the schema provided. Do not include any explanation, markdown, or preamble. Return null for fields where information is not present in the source text.

The output must be a JSON object matching this schema exactly:
{fraud_signal schema from PRD-001 section 3.2}
```

**User prompt template:**
```
Extract fraud intelligence from the following source text.

SOURCE NAME: {source_name}
SOURCE URL: {source_url}
SOURCE DATE: {ingested_at}

SOURCE TEXT:
{raw_content} (truncated to 8,000 tokens if longer)

Return the structured JSON. Set confidence_score based on how clearly the source text describes a specific fraud. Set novelty_score to 0.9 if this is a new typology not commonly documented, 0.5 if known but evolving, 0.2 if a well-known established fraud type.
```

### FR-003: Response Validation
- Parse Gemini response as JSON
- Validate against `FraudSignal` Pydantic model
- If validation fails: retry once with a "fix this JSON" follow-up prompt
- If second attempt fails: write `NORMALIZATION_FAILED` to BigQuery with raw Gemini output for manual review
- Required fields that must NOT be null: `fraud_typology`, `fraud_description`, `attack_vector`, `geographic_origin`, `severity_estimate`
- If any required field is null after extraction: set `confidence_score < 0.3` and flag for review

### FR-004: Fraud Typology Taxonomy
Gemini must classify each signal into one of the following canonical typologies. If none fit, use `OTHER_EMERGING`:

```python
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
  "OTHER_EMERGING"
]
```

### FR-005: Semantic Deduplication
- After extraction, generate embedding of `fraud_description + attack_vector` using `text-embedding-004` via Vertex AI
- Query Vertex AI Vector Search for nearest neighbours (top 5, cosine similarity threshold 0.92)
- If a match exists above threshold: mark new signal as `DUPLICATE_SEMANTIC`, link to original `fraud_signal_id`, do NOT create new alert
- If no match: upsert embedding into Vector Search index

### FR-006: Batch Processing Rate Control
- Maximum 60 Gemini API calls per minute (respect Vertex AI quota)
- Use `asyncio` with semaphore of size 10 for concurrent Gemini calls
- Log token usage per call to BigQuery `llm_usage_log` table

### FR-007: Output
- Write completed `FraudSignal` to BigQuery table `phantom_signal.fraud_signals`
- Update corresponding `RawSignal.processing_status` to `NORMALIZED`
- Emit Pub/Sub message `fraud-signal-ready` with `fraud_signal_id` payload

## 3. Acceptance Criteria
- [ ] Given the SPF Dec 2021 SMS spoofing advisory text, extraction produces: `fraud_typology = SMS_SPOOFING`, `geographic_origin = ["SG"]`, `victim_profile.auth_method = MULTIPLE`, `severity_estimate = HIGH`, `confidence_score >= 0.8`
- [ ] Semantic dedup correctly links a re-phrased version of the same advisory as DUPLICATE_SEMANTIC
- [ ] Processing 100 pending signals completes in under 5 minutes
- [ ] JSON validation failure rate < 5% on a test set of 50 real advisories
- [ ] All normalized signals have non-null values for all required fields

---

---

# PRD-005: RELEVANCE FILTRATION ENGINE (3-GATE)
**Priority:** P0 | **Sprint:** 3

## 1. Objective
Apply three sequential business-logic gates to each `FraudSignal` to determine whether it is material to UOB. Only signals passing all three gates generate an alert. This is the core intelligence filter.

## 2. Functional Requirements

### FR-001: Trigger Condition
- Listens on Pub/Sub topic `fraud-signal-ready`
- Pulls `FraudSignal` from BigQuery using `fraud_signal_id`
- Runs three gates sequentially — if Gate 1 fails, skip Gates 2 and 3 (short-circuit)

### FR-002: Gate 1 — Novelty Check
**Question: Is this a fraud pattern we haven't already detected and hardened against?**

Logic:
1. Query `mock_tm_rules` table: does any active TM rule list this `fraud_typology` in `fraud_typologies_targeted`?
2. Query `fraud_signals` table: has a signal with same `fraud_typology` + `severity_estimate >= HIGH` been alerted in the last 90 days?
3. Check `novelty_score` from FraudSignal: if < 0.3 (very well-known), weight gate toward fail

**Scoring:**
- TM rule exists AND covers this typology: -40 points
- Similar signal alerted in last 30 days: -30 points
- Similar signal alerted in 31–90 days: -15 points
- novelty_score >= 0.7: +30 points
- novelty_score 0.4–0.69: +10 points
- `source_credibility = HIGH`: +10 points

**Gate 1 threshold:** Score >= 20 points to pass

**Output fields on `gate1_novelty`:**
- `passed`: boolean
- `existing_tm_rule_match`: boolean
- `similar_signal_ids`: list of matching fraud_signal_ids
- `explanation`: 1-sentence human-readable reason

### FR-003: Gate 2 — Customer Exposure Check
**Question: Does this fraud pattern threaten customers UOB actually has?**

Logic:
1. From `FraudSignal.victim_profile.customer_segment`, look up matching `MockCustomerPersona` records
2. From `FraudSignal.victim_profile.geography`, check overlap with UOB's footprint: `[SG, MY, TH, ID, HK, CN, VN]`
3. From `FraudSignal.victim_profile.channel`, check if UOB offers that channel
4. From `FraudVulnerabilityMatrix`, check if this typology targets any UOB customer segment

**Scoring:**
- Segment match (RETAIL): +35 points
- Segment match (SME): +25 points
- Segment match (TRADE_FINANCE or CORRESPONDENT_BANKING): +20 points
- Geography overlap with SG: +30 points
- Geography overlap with MY/TH/ID: +15 points
- Channel: MOBILE or INTERNET_BANKING: +20 points
- `estimated_at_risk_customers > 10,000`: +15 bonus points

**Estimate `at_risk_customers`:**
- Query `mock_customer_personas` filtering on segment + geography + auth_method
- Sum `population_count` of matching personas

**Gate 2 threshold:** Score >= 40 points to pass

### FR-004: Gate 3 — Control Gap Check
**Question: Would our current controls fail to detect or prevent this fraud?**

Logic:
1. Query `mock_tm_rules` for rules covering this typology
2. For matching rules, sum `estimated_catch_rate_pct` weighted by applicability (0.0–1.0)
3. Compute `undetected_pct = 100 - weighted_catch_rate`
4. Check `FraudVulnerabilityMatrix` for `auth_vulnerability` flag matching UOB's prevalent auth method for at-risk segment

**Scoring:**
- `undetected_pct >= 70%`: +50 points
- `undetected_pct 50–69%`: +30 points
- `undetected_pct 30–49%`: +15 points
- `undetected_pct < 30%`: +0 points
- `auth_vulnerability = True` for SMS_OTP (which most retail customers use): +25 points
- No TM rules cover this typology at all: +30 bonus points

**Gate 3 threshold:** Score >= 35 points to pass

### FR-005: Composite Risk Score
If all three gates pass, compute:
```
composite_risk_score = (
  gate1_score * 0.25 +
  gate2_score * 0.40 +
  gate3_score * 0.35
) normalized to 0–100
```

**Alert priority mapping:**
- Score >= 80: CRITICAL
- Score 60–79: HIGH
- Score 40–59: MEDIUM
- Score < 40: LOW (passes filter but low priority)

### FR-006: Failed Gate Handling
- If ANY gate fails: set `overall_passed = False`
- Write `RelevanceAssessment` to BigQuery with `overall_passed = False` and detailed gate explanations
- Update `RawSignal.processing_status = DISCARDED`
- Do NOT emit alert Pub/Sub message
- Log at INFO level (not ERROR — filtering is expected behaviour)

### FR-007: Passed Gate Handling
- Write `RelevanceAssessment` to BigQuery
- Update `RawSignal.processing_status = ALERTED`
- Emit Pub/Sub message `alert-queue` with payload: `{fraud_signal_id, assessment_id, alert_priority}`
- If `alert_priority = CRITICAL`: also trigger immediate Cloud Function notification (email via SendGrid)

## 3. Acceptance Criteria
- [ ] SMS spoofing signal with victim profile RETAIL + SG + SMS_OTP auth passes all three gates with CRITICAL priority
- [ ] A signal about commodity futures fraud with TRADE_FINANCE segment but geography = UK only → fails Gate 2
- [ ] A signal for a typology already covered by TM-001 with catch rate 85% → fails Gate 3
- [ ] A well-known phishing typology alerted 10 days ago → fails Gate 1
- [ ] Composite risk score computation produces deterministic results given same inputs
- [ ] Processing 50 signals through all three gates completes in under 60 seconds

---

---

# PRD-006: SIMULATION & IMPACT MODELLING ENGINE
**Priority:** P1 | **Sprint:** 5

## 1. Objective
Given a `FraudSignal` and `RelevanceAssessment` that passed all three gates, quantify the financial impact to UOB if the fraud hits — and show how proposed interventions reduce that exposure. Output feeds directly into the Risk Alert Document.

## 2. Functional Requirements

### FR-001: Trigger Condition
- Listens on Pub/Sub topic `alert-queue` for `alert_priority = HIGH or CRITICAL` signals
- For MEDIUM and LOW: run simulation on-demand only (not automatic)
- Pulls FraudSignal + RelevanceAssessment from BigQuery

### FR-002: Customer Exposure Calculation
**Step 1 — Base population:**
- Query `mock_customer_personas` filtered by:
  - `segment` matching `FraudSignal.victim_profile.customer_segment`
  - `geography` overlapping `FraudSignal.geographic_spread`
  - `auth_method` marked as vulnerable in `FraudVulnerabilityMatrix`
- Sum `population_count` → `total_at_risk`

**Step 2 — Attack reach adjustment:**
- Apply `attack_reach_factor` based on fraud typology:
  - SMS_SPOOFING: 0.08 (8% of vulnerable population typically reached in a wave)
  - SIM_SWAP: 0.03
  - PHISHING_EMAIL: 0.12
  - SEXTORTION: 0.05
  - DEEPFAKE_CFO_FRAUD: 0.02
  - Default: 0.05
- `estimated_reached = total_at_risk * attack_reach_factor`

**Step 3 — Victim conversion rate:**
- Query `mock_fraud_history` for same typology: compute `actual_victim_rate = count(incidents) / estimated_reached`
- If no history: use typology defaults from `FraudVulnerabilityMatrix`
- `estimated_victims = estimated_reached * victim_conversion_rate`

### FR-003: Financial Impact Calculation

**Baseline exposure (no intervention):**
```python
baseline_exposure_sgd = estimated_victims * avg_loss_per_victim_sgd
```
Where `avg_loss_per_victim_sgd` comes from:
- `mock_fraud_history` mean loss for this typology, or
- Default per typology: SMS_SPOOFING=5500, SIM_SWAP=8000, SEXTORTION=3000, DEEPFAKE_CFO=250000

**With current controls:**
```python
current_catch_rate = gate3_undetected_pct / 100  # inverse
with_current_controls_sgd = baseline_exposure_sgd * (1 - current_catch_rate * 0.7)
# The 0.7 factor accounts for partial prevention (detecting ≠ fully preventing loss)
```

**With proposed interventions:**
- For each proposed intervention (from PRD-008), apply `estimated_reduction_pct`
- Combine reductions (diminishing returns formula):
```python
combined_reduction = 1 - product(1 - r for r in reduction_pcts)
with_proposed_controls_sgd = baseline_exposure_sgd * (1 - combined_reduction)
```

### FR-004: Monte Carlo Sensitivity Analysis
- Run 1,000 iterations varying:
  - `attack_reach_factor`: ±30% random variation (uniform)
  - `victim_conversion_rate`: ±25% random variation (uniform)
  - `avg_loss_per_victim`: log-normal variation (sigma=0.5)
- Report: P10, P50 (median), P90 exposure values for `baseline_exposure_sgd`
- This gives leadership a range rather than a point estimate

### FR-005: Output
- Write `SimulationResult` to BigQuery `phantom_signal.simulations`
- Emit Pub/Sub message `simulation-ready` with `simulation_id` payload
- The simulation summary MUST include: baseline exposure, current-controls exposure, proposed-controls exposure, P10/P50/P90 range, number of customers estimated at risk

## 3. Acceptance Criteria
- [ ] SMS spoofing simulation for SG retail customers: baseline exposure between SGD 8M–20M, current controls SGD 5M–14M, proposed (device binding) SGD 2M–6M
- [ ] Monte Carlo produces a P90 at least 2x the P10 (confirming meaningful uncertainty range)
- [ ] Sextortion simulation correctly targets male 18–35 retail customers using SMS OTP
- [ ] Simulation completes in under 30 seconds per signal
- [ ] Results are deterministic given a fixed `random_seed`

---

---

# PRD-007: RISK ALERT DOCUMENT GENERATOR
**Priority:** P0 | **Sprint:** 6

## 1. Objective
This is the PRIMARY OUTPUT of the entire system. Generate a structured, professional Risk Alert Document using Gemini 1.5 Pro that a compliance officer or fraud expert can immediately act on. Output as both PDF and JSON.

## 2. Functional Requirements

### FR-001: Trigger Condition
- Listens on Pub/Sub: `alert-queue` (for immediate) or `simulation-ready` (after simulation)
- Gathers all context: FraudSignal + RelevanceAssessment + SimulationResult (if available) + InterventionRules (from PRD-008)

### FR-002: Document Structure (MANDATORY)
The generated document MUST contain ALL of the following sections in this order:

**SECTION 1: ALERT HEADER**
- Alert ID, Priority badge (CRITICAL/HIGH/MEDIUM/LOW), Generated timestamp
- Fraud typology (human-readable label), Alert routing (which teams)

**SECTION 2: EXECUTIVE SUMMARY**
- 3–4 sentences ONLY
- Must answer: What is the threat? Who does it affect at UOB? What is the financial exposure? What is the single most important action?
- Tone: Direct, no jargon, suitable for a senior leader who has 30 seconds

**SECTION 3: THREAT INTELLIGENCE BRIEF**
- Full fraud narrative: how the attack works step-by-step
- Global emergence timeline: where and when it first appeared
- Scale of impact globally (numbers from source intelligence)
- Why it is escalating now

**SECTION 4: UOB RELEVANCE ASSESSMENT**
- Gate 1 outcome: novelty justification
- Gate 2 outcome: which UOB customer segments and how many customers estimated at risk
- Gate 3 outcome: which existing TM rules cover this and what % is undetected
- Composite risk score with interpretation

**SECTION 5: FINANCIAL IMPACT SIMULATION**
- Baseline exposure (SGD) if simulation ran, or "Simulation not run — request via portal" if not
- With current controls (SGD)
- With proposed interventions (SGD)
- P10 / P50 / P90 range if Monte Carlo ran
- Clear statement: "UOB's estimated unmitigated exposure is SGD X–Y"

**SECTION 6: RECOMMENDED ACTIONS**
Three sub-sections:
- **Immediate (< 24 hours):** 2–4 specific actions (e.g. "Issue advisory to retail customers via push notification warning of SMS impersonation")
- **Short-term (1–7 days):** 3–5 actions (e.g. "Submit new TM detection scenario to transaction monitoring team for SMS spoofing pattern")
- **Strategic (1–4 weeks):** 2–3 actions (e.g. "Accelerate device binding rollout for retail segment OTP authentication")

**SECTION 7: PROPOSED INTERVENTION RULES**
- List each `InterventionRule` with: type, description, rule logic (plain English), expected impact %, deployment risk, approval required
- Formatted as a numbered list

**SECTION 8: EVIDENCE SOURCES**
- Numbered list of sources with URLs and access dates
- Credibility rating per source

**SECTION 9: ANALYST NOTES & CAVEATS**
- Auto-generated caveats: confidence rating, data limitations (synthetic data disclosure for POC), recommended human review steps
- Always include: "This alert is AI-generated. It must be reviewed by a qualified fraud risk analyst before operational action is taken."

### FR-003: Gemini Prompt for Document Generation

**System prompt:**
```
You are a senior fraud intelligence analyst at a major Singapore bank. You write precise, structured risk intelligence alerts for compliance leadership. Your writing is clear, concise, and action-oriented. You never use vague language. You always quantify impact in SGD where data is available. You write for two audiences simultaneously: a senior executive who reads only the Executive Summary, and a fraud analyst who reads the full document.

You will be given structured data about a fraud signal, a relevance assessment, and a simulation result. Use this data to write a complete Risk Alert Document following the exact section structure provided. Do not invent data not present in the input. If data is missing for a field, say so explicitly.
```

**User prompt template:**
```
Generate a complete Risk Alert Document for the following fraud intelligence.

FRAUD SIGNAL:
{fraud_signal_json}

RELEVANCE ASSESSMENT:
{relevance_assessment_json}

SIMULATION RESULT:
{simulation_result_json or "NOT AVAILABLE"}

INTERVENTION RULES:
{intervention_rules_json}

Write the document in the following section structure:
[Executive Summary] [Threat Intelligence Brief] [UOB Relevance Assessment] [Financial Impact Simulation] [Recommended Actions] [Proposed Intervention Rules] [Evidence Sources] [Analyst Notes & Caveats]

Use clear, professional language. Quantify everything possible. Be specific about which UOB customer segments are affected and why.
```

### FR-004: Quality Validation Rules
Before writing to BigQuery, validate the generated document:
- `executive_summary` length: 50–300 words
- `recommended_actions.immediate` list: 2–5 items (not 0, not 6+)
- `financial_exposure` section must contain at least one SGD figure if simulation was run
- `evidence_sources` must contain at least 1 item
- `analyst_notes` must contain the mandatory human-review disclaimer
- If any check fails: re-generate once; if fails again, write `GENERATION_FAILED` status and alert system admin

### FR-005: PDF Generation
- Use `reportlab` or `weasyprint` to generate PDF
- PDF styling:
  - UOB color palette: navy header (#0D1B3E), teal accents (#028090), white body
  - Priority badge rendered as colored box (CRITICAL=red, HIGH=orange, MEDIUM=amber, LOW=green)
  - Sections separated by thin teal horizontal rules
  - Monospace font for rule logic sections
  - Page header: "RESTRICTED — UOB Group Compliance — Phantom Signal" on every page
  - Page footer: alert ID + generated timestamp + page number
- Max document length: 8 pages for HIGH/CRITICAL, 5 pages for MEDIUM/LOW

### FR-006: Output Storage
- PDF stored in GCS: `gs://phantom-signal-alerts/{YYYY}/{MM}/{DD}/{alert_id}.pdf`
- JSON stored in BigQuery: `phantom_signal.risk_alerts`
- Alert metadata stored in: `phantom_signal.alert_log` (summary row only)
- Signed GCS URL generated (48-hour expiry) for dashboard access

### FR-007: Routing
Based on `alert_priority` and `fraud_typology`, set routing flags:
- CRITICAL + any typology: ALL teams = True
- HIGH + RETAIL: `compliance_team = True`, `fraud_risk_team = True`, `tm_analytics_team = True`
- HIGH + TRADE_FINANCE: `compliance_team = True`, `fraud_risk_team = True`, `policy_controls_team = True`
- MEDIUM: `fraud_risk_team = True` only
- LOW: `tm_analytics_team = True` only

## 3. Acceptance Criteria
- [ ] Alert document generated for SMS spoofing signal contains all 9 mandatory sections
- [ ] Executive summary is 3–4 sentences, mentions SGD exposure figure, names UOB retail customers as affected segment
- [ ] PDF renders correctly: priority badge visible, sections clearly delineated, header/footer on every page
- [ ] Recommended actions contains at least 2 items in each sub-section
- [ ] Mandatory human-review disclaimer present in Analyst Notes
- [ ] Document generation completes in under 45 seconds
- [ ] A non-technical stakeholder reading only the executive summary can understand the threat and the primary action in under 60 seconds (validated by user test in demo)

---

---

# PRD-008: INTERVENTION RULES ENGINE
**Priority:** P1 | **Sprint:** 7

## 1. Objective
Automatically generate specific, deployable intervention rules for each fraud signal that passes filtration. Rules are classified by type, deployment risk, and whether they can be auto-approved or need human review.

## 2. Functional Requirements

### FR-001: Rule Generation via Gemini
For each `RelevanceAssessment` that passes all gates, call Gemini to generate intervention rules.

**System prompt:**
```
You are a fraud controls specialist at a Singapore bank. Your job is to write specific, actionable intervention rules in response to a detected fraud threat. Rules must be concrete enough that a bank's transaction monitoring team or digital banking team can implement them directly. Rules must be categorized by type and include specific trigger conditions.
```

**User prompt template:**
```
Generate intervention rules for the following fraud threat at UOB Singapore.

FRAUD SIGNAL: {fraud_signal_summary}
AT-RISK SEGMENTS: {matched_segments}
UNDETECTED RATE: {undetected_pct}%
PRIMARY VULNERABLE AUTH METHOD: {auth_vulnerability}

Generate rules covering ALL FOUR of these categories (at least 1 rule per category):
1. TM_DETECTION — A new transaction monitoring detection rule
2. CUSTOMER_FRICTION — A friction/challenge to add at a specific customer interaction point
3. POLICY_CHANGE — A policy or procedural change
4. ADVISORY — Customer advisory messaging

For each rule, specify:
- rule_type (from above)
- target_layer
- rule_description (plain English, 1–2 sentences)
- rule_logic (pseudocode or structured natural language IF/THEN)
- trigger_conditions (list of specific conditions)
- expected_impact_pct (realistic estimate, 5–40% range)
- deployment_risk (LOW/MEDIUM/HIGH)
- approval_required (true if changes TM thresholds or customer-facing flows)
- auto_deployable (true only for ADVISORY type with LOW risk)

Return as JSON array of InterventionRule objects.
```

### FR-002: Rule Validation
- Each rule must have non-null: `rule_type`, `rule_description`, `rule_logic`, `trigger_conditions` (at least 1)
- `expected_impact_pct` must be between 1–50 (reject claims > 50% as unrealistic)
- `auto_deployable = true` ONLY allowed if `deployment_risk = LOW` AND `rule_type = ADVISORY`
- Any rule with `approval_required = true` must be flagged in the alert document with "⚠ Requires Head of Fraud Risk sign-off"

### FR-003: Rule Classification Matrix

| Rule Type | Auto-Deployable | Approval Level | Lead Time |
|-----------|-----------------|----------------|-----------|
| TM_DETECTION | Never | Head of TM Analytics | 3–7 days |
| CUSTOMER_FRICTION | Never | Head of Digital Banking | 5–14 days |
| POLICY_CHANGE | Never | CISO + CRO | 14–30 days |
| ADVISORY | If LOW risk | Fraud Risk Manager | <24 hours |

### FR-004: Output
- Write `InterventionRule` records to BigQuery `phantom_signal.intervention_rules`
- Link each rule to `fraud_signal_id` and `assessment_id`
- Rules are included as `SECTION 7` in the Risk Alert Document (PRD-007)

## 3. Acceptance Criteria
- [ ] SMS spoofing signal generates at least 4 rules (1 per type)
- [ ] TM_DETECTION rule for SMS spoofing includes specific trigger: "account login from new device within 6 hours of SIM change event"
- [ ] ADVISORY rule is marked auto_deployable, POLICY_CHANGE rule is not
- [ ] No rule has expected_impact_pct > 50
- [ ] All rules pass validation on first attempt ≥ 80% of the time

---

---

# PRD-009: ORCHESTRATION & PIPELINE MANAGEMENT
**Priority:** P1 | **Sprint:** 3

## 1. Objective
Manage the end-to-end pipeline execution, error recovery, retry logic, and inter-component communication using Google Cloud Pub/Sub and Cloud Composer (Airflow).

## 2. Functional Requirements

### FR-001: Pub/Sub Topics
Create the following Pub/Sub topics:

| Topic | Publisher | Subscriber |
|-------|-----------|------------|
| `ingestion-complete` | Ingestion Agent (PRD-002) | Normalization Layer (PRD-004) |
| `fraud-signal-ready` | Normalization Layer | Filtration Engine (PRD-005) |
| `alert-queue` | Filtration Engine | Simulation Engine (PRD-006), Alert Generator (PRD-007) |
| `simulation-ready` | Simulation Engine | Alert Generator (PRD-007) |
| `alert-generated` | Alert Generator | Dashboard (PRD-011), Notification Service |
| `pipeline-error` | Any component | Error Handler Cloud Function |

### FR-002: Airflow DAG Definition
Create one master DAG `phantom_signal_main` with the following structure:
```
crawl_osint_sources (every 6h)
  → normalize_pending_signals
    → run_filtration_engine
      → [if passed] run_simulation (HIGH/CRITICAL only)
        → generate_alert_document
          → notify_teams
```

Each task must have:
- `retries = 2`
- `retry_delay = timedelta(minutes=5)`
- `execution_timeout = timedelta(minutes=15)`
- On failure: send to `pipeline-error` Pub/Sub topic with task name, run_id, error message

### FR-003: Dead Letter Queue
- All Pub/Sub subscriptions must have Dead Letter Topics configured
- Max delivery attempts: 5
- Dead-lettered messages stored in BigQuery `phantom_signal.dead_letter_log` for manual review

### FR-004: Pipeline Monitoring
- Cloud Monitoring dashboard showing:
  - Signals ingested per hour
  - Signals normalized per hour
  - Pass rate through each gate
  - Alerts generated per day
  - Average end-to-end latency (ingestion → alert document)
- Alert (Cloud Monitoring alert policy) if no new signals ingested in 12 hours

## 3. Acceptance Criteria
- [ ] Full end-to-end pipeline runs without manual intervention from scheduled trigger
- [ ] A deliberate failure in normalization step recovers automatically via retry
- [ ] Dead-letter messages are correctly captured in BigQuery
- [ ] End-to-end latency from signal ingestion to alert PDF generation < 10 minutes for CRITICAL alerts

---

---

# PRD-010: DATA STORAGE & KNOWLEDGE BASE
**Priority:** P0 | **Sprint:** 1

## 1. Objective
Define and create all Google Cloud storage resources required by the system.

## 2. BigQuery Dataset & Tables

**Dataset name:** `phantom_signal`
**Location:** `asia-southeast1` (Singapore)

| Table | Schema Reference | Partition | Clustering |
|-------|-----------------|-----------|------------|
| `raw_signals` | RawSignal (PRD-001 §3.1) | `ingested_at` (DAY) | `source_category`, `processing_status` |
| `fraud_signals` | FraudSignal (PRD-001 §3.2) | `detected_at` (DAY) | `fraud_typology`, `severity_estimate` |
| `relevance_assessments` | RelevanceAssessment (PRD-001 §3.3) | `assessed_at` (DAY) | `overall_passed`, `alert_priority` |
| `simulations` | SimulationResult (PRD-001 §3.4) | `run_at` (DAY) | `fraud_signal_id` |
| `risk_alerts` | RiskAlertDocument (PRD-001 §3.5) | `generated_at` (DAY) | `priority` |
| `intervention_rules` | InterventionRule (PRD-001 §3.6) | `fraud_signal_id` | `rule_type` |
| `mock_customer_personas` | MockCustomerPersona (PRD-001 §3.7) | None | `segment`, `geography` |
| `mock_tm_rules` | MockTMRule (PRD-001 §3.8) | None | `fraud_typologies_targeted` |
| `mock_fraud_history` | (see PRD-003 FR-003) | `detection_date` (MONTH) | `fraud_typology` |
| `ingestion_errors` | error_log schema | `timestamp` (DAY) | `source_name` |
| `llm_usage_log` | usage_log schema | `timestamp` (DAY) | `model_name` |
| `dead_letter_log` | dead_letter schema | `timestamp` (DAY) | `topic` |
| `alert_log` | summary schema | `generated_at` (DAY) | `priority` |

## 3. GCS Buckets

| Bucket | Purpose | Retention |
|--------|---------|-----------|
| `phantom-signal-raw` | Raw OSInt blobs | 90 days |
| `phantom-signal-synthetic` | Synthetic datasets (CSV) | Indefinite |
| `phantom-signal-alerts` | Generated PDFs | 365 days |
| `phantom-signal-embeddings` | Embedding snapshots | 180 days |

## 4. Vertex AI Vector Search
- **Index name:** `fraud-signal-index`
- **Dimensions:** 768 (text-embedding-004 output)
- **Distance measure:** Cosine similarity
- **Algorithm:** Tree-AH (approximate nearest neighbor, suitable for POC scale)
- **Deployed endpoint:** `fraud-signal-endpoint`

## 5. Secret Manager Secrets
| Secret Name | Value |
|-------------|-------|
| `alienvault-otx-api-key` | AlienVault OTX API key |
| `reddit-client-id` | Reddit API client ID |
| `reddit-client-secret` | Reddit API client secret |
| `sendgrid-api-key` | SendGrid API key for notifications |

## 6. Acceptance Criteria
- [ ] All BigQuery tables created with correct schemas and partitioning
- [ ] All GCS buckets created with correct retention policies
- [ ] Vector Search index deployed and queryable
- [ ] All secrets stored in Secret Manager and accessible by Cloud Run service accounts with least-privilege IAM

---

---

# PRD-011: DEMO DASHBOARD (STREAMLIT)
**Priority:** P1 | **Sprint:** 8

## 1. Objective
Build a Streamlit web application that demonstrates the end-to-end POC flow for judges and stakeholders. The dashboard must tell the complete story from "global OSInt signal ingested" to "Risk Alert Document generated" in a single screen session.

## 2. Functional Requirements

### FR-001: Page Structure
The dashboard has 5 pages (Streamlit sidebar navigation):

**Page 1: Live Feed — OSInt Signals**
- Table of last 50 `RawSignal` records: source, title, timestamp, status badge
- Colour-coded status: PENDING (grey), NORMALIZED (blue), ALERTED (red), DISCARDED (light grey)
- "Refresh" button to poll latest records
- Metric cards at top: Total ingested today, Normalized today, Alerts generated today

**Page 2: Fraud Signal Intelligence**
- Table of `FraudSignal` records with filters: typology, severity, date range
- Click on a row → expand card showing full fraud_description, attack_vector, victim_profile, confidence_score
- Bar chart: Fraud signals by typology (last 7 days)
- World map: Geographic origin of signals (using Plotly choropleth)

**Page 3: Relevance Assessment**
- For each signal that went through filtration: show gate results as a 3-step visual
- Gate pass = green tick, fail = red cross, with explanation text
- Composite risk score shown as a gauge chart (0–100)
- Filter by: PASSED ALL / FAILED GATE 1 / FAILED GATE 2 / FAILED GATE 3

**Page 4: Risk Alert Document Viewer**
- Table of generated alerts: alert ID, fraud typology, priority, generated_at, routing
- Click row → show full alert document rendered as structured sections (HTML/markdown)
- "Download PDF" button → downloads signed GCS URL PDF
- Priority badges styled as coloured chips (CRITICAL=red, HIGH=orange, MEDIUM=amber, LOW=green)

**Page 5: Live Demo Mode**
- This page is for the competition presentation
- Input field: "Paste a fraud advisory URL or text"
- "Run Phantom Signal Analysis" button
- Progress bar showing pipeline stages: Ingest → Normalize → Filter (3 gates) → Simulate → Generate Alert
- Each stage lights up green when complete (polling BigQuery/GCS every 3 seconds)
- Final output: rendered alert document in-page + PDF download button
- Pre-loaded demo scenario: SMS spoofing (so it runs instantly if judges are watching)

### FR-002: Pre-loaded Demo Data
For the competition demo, pre-load the following scenarios in BigQuery so they render instantly:
1. **SMS Spoofing** (CRITICAL) — based on OCBC 2021 pattern
2. **Sextortion Surge** (HIGH) — targeting male retail 18–35
3. **Deepfake CFO Fraud** (HIGH) — targeting trade finance

### FR-003: Technical Specs
- Framework: Streamlit 1.35+
- Deploy on: Cloud Run (min 1 instance, to avoid cold start during demo)
- Authentication: None for POC (internal demo only)
- Charts: Plotly (choropleth, gauge, bar)
- Styling: Custom CSS matching Indigo/Teal brand palette
- BigQuery reads: Use `google-cloud-bigquery` with service account credentials
- Responsive: Must render acceptably on a laptop screen (1280x800 minimum)

### FR-004: Performance
- Page 1 (Live Feed): Load in < 3 seconds
- Page 4 (Alert Viewer): Load in < 5 seconds
- Demo Mode pipeline: CRITICAL alert document generated and displayed within 3 minutes of submission
- Pre-loaded demo scenarios: display instantly (< 1 second load)

## 3. Acceptance Criteria
- [ ] All 5 pages render without error
- [ ] Clicking a fraud signal row shows correct detail without page reload
- [ ] PDF download link works and opens the correct alert document
- [ ] Demo Mode runs the full pipeline on the pre-loaded SMS spoofing scenario in under 3 minutes
- [ ] Priority colour badges are correct for all alert levels
- [ ] Dashboard runs on Cloud Run without crashing over a 30-minute continuous session

---

## APPENDIX: ENVIRONMENT SETUP CHECKLIST

```bash
# Google Cloud Project Setup
gcloud projects create phantom-signal-poc
gcloud config set project phantom-signal-poc

# Enable APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable composer.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com

# Service Accounts
gcloud iam service-accounts create phantom-signal-sa \
  --display-name="Phantom Signal Service Account"

# Required roles for SA
gcloud projects add-iam-policy-binding phantom-signal-poc \
  --member="serviceAccount:phantom-signal-sa@phantom-signal-poc.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
gcloud projects add-iam-policy-binding phantom-signal-poc \
  --member="serviceAccount:phantom-signal-sa@phantom-signal-poc.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding phantom-signal-poc \
  --member="serviceAccount:phantom-signal-sa@phantom-signal-poc.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding phantom-signal-poc \
  --member="serviceAccount:phantom-signal-sa@phantom-signal-poc.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding phantom-signal-poc \
  --member="serviceAccount:phantom-signal-sa@phantom-signal-poc.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"
```

---

## APPENDIX: KEY QUESTIONS FOR NEXT REVIEW

These items need Shivam's decision before the relevant PRD can be finalised:

1. **PRD-007 PDF branding:** Should the alert PDF use UOB's official logo and brand colours, or a Phantom Signal custom logo (for competition submission)?

2. **PRD-009 Scheduling:** Should the crawl run on a fixed schedule (every 6 hours) or be event-triggered? For the demo, a manual trigger button in the dashboard may be simpler.

3. **PRD-011 Demo Mode timeout:** Should the live demo pipeline run the full Gemini normalization + simulation in real-time (slower, more impressive), or use the pre-loaded result with a simulated progress bar (faster, more reliable for a competition setting)?

4. **PRD-002 Dark web sources:** IntelX and DarkOwl require paid subscriptions. For the POC, should dark web monitoring be simulated (mock data) or skipped entirely?

5. **PRD-006 Simulation currency:** Financial impact should be in SGD. Should we also show MYR, THB, IDR breakdowns for the regional exposure, or SGD only?

---

*Document version 1.0 — Phantom Signal POC — UOB Innovation Challenge*
*All internal data references use synthetic/mock data only. No real UOB customer data is used in this POC.*
