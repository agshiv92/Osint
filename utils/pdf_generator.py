"""
Phantom Signal — PDF Generator (PRD-007 FR-005)
Generates styled Risk Alert Document PDFs using reportlab.
"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from config import ALERTS_DIR, COLOR_NAVY, COLOR_TEAL, TYPOLOGY_LABELS

logger = logging.getLogger(__name__)

PRIORITY_PDF_COLORS = {
    "CRITICAL": (0.86, 0.15, 0.15),  # red
    "HIGH":     (0.92, 0.35, 0.04),  # orange
    "MEDIUM":   (0.85, 0.47, 0.04),  # amber
    "LOW":      (0.09, 0.64, 0.25),  # green
}

NAVY  = (0.051, 0.106, 0.243)
TEAL  = (0.008, 0.502, 0.565)
WHITE = (1, 1, 1)
LIGHT_GREY = (0.93, 0.94, 0.96)
DARK_TEXT  = (0.12, 0.17, 0.27)


def _fmt_sgd(v: float) -> str:
    if v >= 1_000_000:
        return f"SGD {v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"SGD {v/1_000:.0f}K"
    return f"SGD {v:,.0f}"


def generate_pdf(
    alert: Dict,
    fraud_signal: Dict,
    assessment: Dict,
    simulation: Optional[Dict] = None,
) -> str:
    """
    Generate a PDF for the given alert. Returns the file path.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
            Table, TableStyle, KeepTogether,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    except ImportError:
        logger.warning("reportlab not available — PDF generation skipped")
        return ""

    alert_id = alert.get("alert_id", str(uuid.uuid4()))
    priority = alert.get("priority", "HIGH")
    doc_content = alert.get("document", {})
    typology = fraud_signal.get("fraud_typology", "UNKNOWN")
    label = TYPOLOGY_LABELS.get(typology, typology)
    generated_at = alert.get("generated_at", datetime.utcnow().isoformat())[:19].replace("T", " ")

    pdf_path = str(ALERTS_DIR / f"{alert_id}.pdf")

    # Colours
    pri_color = colors.Color(*PRIORITY_PDF_COLORS.get(priority, PRIORITY_PDF_COLORS["HIGH"]))
    navy_color = colors.Color(*NAVY)
    teal_color = colors.Color(*TEAL)
    white_color = colors.white
    light_grey = colors.Color(*LIGHT_GREY)
    dark_text = colors.Color(*DARK_TEXT)

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
    )

    # Styles
    styles = getSampleStyleSheet()

    def style(name, **kwargs):
        return ParagraphStyle(name, parent=styles['Normal'], **kwargs)

    h1 = style("H1", fontSize=20, fontName="Helvetica-Bold",
               textColor=white_color, spaceAfter=4, leading=24)
    h2 = style("H2", fontSize=13, fontName="Helvetica-Bold",
               textColor=teal_color, spaceBefore=14, spaceAfter=6)
    h3 = style("H3", fontSize=10, fontName="Helvetica-Bold",
               textColor=dark_text, spaceBefore=8, spaceAfter=4)
    body = style("Body", fontSize=9.5, leading=14, textColor=dark_text,
                 spaceAfter=8, alignment=TA_JUSTIFY)
    bullet = style("Bullet", fontSize=9.5, leading=14, textColor=dark_text,
                   leftIndent=14, spaceAfter=3)
    caption = style("Caption", fontSize=7.5, textColor=colors.grey, spaceAfter=4)
    disclaimer = style("Disclaimer", fontSize=8.5, leading=12,
                       textColor=colors.Color(0.5, 0.3, 0.0),
                       backColor=colors.Color(1, 0.97, 0.88),
                       leftIndent=8, rightIndent=8, borderPadding=6)

    # Page template with header/footer
    story = []

    def add_section_header(title: str):
        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=1.5, color=teal_color))
        story.append(Paragraph(title, h2))

    # ── HEADER BANNER ──────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(
            f'<font color="white"><b>PHANTOM SIGNAL</b></font> &nbsp;'
            f'<font color="#80D4DC" size="9">OSInt Early Warning Framework</font>',
            style("HTitle", fontSize=16, fontName="Helvetica-Bold",
                  textColor=white_color, leading=20)
        ),
        Paragraph(
            f'<font color="white" size="8">RESTRICTED — UOB Group Compliance</font>',
            style("HRight", fontSize=8, textColor=white_color, alignment=1)
        ),
    ]]
    header_table = Table(header_data, colWidths=["70%","30%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), navy_color),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # ── ALERT HEADER ──────────────────────────────────────────────────────────
    badge_data = [[
        Paragraph(
            f'<b>{priority}</b>',
            style("Badge", fontSize=14, fontName="Helvetica-Bold",
                  textColor=white_color, alignment=TA_CENTER)
        ),
        [
            Paragraph(f"<b>{label}</b>",
                      style("AH1", fontSize=15, fontName="Helvetica-Bold", textColor=dark_text)),
            Paragraph(f"Alert ID: {alert_id[:8].upper()}  |  Generated: {generated_at} UTC",
                      style("AH2", fontSize=8, textColor=colors.grey)),
        ]
    ]]
    badge_table = Table(badge_data, colWidths=[2.8*cm, None])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), pri_color),
        ("BACKGROUND", (1, 0), (1, 0), light_grey),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 0.4*cm))

    # Routing
    routing = alert.get("routing", {})
    teams = [k.replace("_"," ").title() for k, v in routing.items() if v]
    if teams:
        story.append(Paragraph(
            f"<b>Routed to:</b> {' · '.join(teams)}",
            style("Route", fontSize=8.5, textColor=dark_text)
        ))
    story.append(Spacer(1, 0.3*cm))

    # ── SECTION 2: EXECUTIVE SUMMARY ─────────────────────────────────────────
    add_section_header("EXECUTIVE SUMMARY")
    exec_sum = doc_content.get("executive_summary", "")
    story.append(Paragraph(exec_sum, body))

    # ── SECTION 3: THREAT INTELLIGENCE BRIEF ──────────────────────────────────
    add_section_header("THREAT INTELLIGENCE BRIEF")
    story.append(Paragraph(doc_content.get("threat_description", ""), body))

    # ── SECTION 4: UOB RELEVANCE ASSESSMENT ──────────────────────────────────
    add_section_header("UOB RELEVANCE ASSESSMENT")

    g1 = assessment.get("gate1_novelty", {})
    g2 = assessment.get("gate2_customer_exposure", {})
    g3 = assessment.get("gate3_control_gap", {})
    score = assessment.get("composite_risk_score", 0.0)

    gate_data = [
        ["Gate", "Result", "Details"],
        ["Gate 1 — Novelty",
         "✓ PASSED" if g1.get("passed") else "✗ FAILED",
         g1.get("explanation","")[:120]],
        ["Gate 2 — Customer Exposure",
         "✓ PASSED" if g2.get("passed") else "✗ FAILED",
         g2.get("explanation","")[:120]],
        ["Gate 3 — Control Gap",
         "✓ PASSED" if g3.get("passed") else "✗ FAILED",
         g3.get("explanation","")[:120]],
    ]

    def gate_result_color(result_text):
        if "PASSED" in result_text:
            return colors.Color(0.09, 0.64, 0.25)
        return colors.Color(0.86, 0.15, 0.15)

    gate_table = Table(gate_data, colWidths=[3.5*cm, 2.5*cm, None])
    gate_style = [
        ("BACKGROUND", (0, 0), (-1, 0), navy_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), white_color),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white_color, light_grey]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for row_idx in range(1, 4):
        result_text = gate_data[row_idx][1]
        c = gate_result_color(result_text)
        gate_style.append(("TEXTCOLOR", (1, row_idx), (1, row_idx), c))
        gate_style.append(("FONTNAME", (1, row_idx), (1, row_idx), "Helvetica-Bold"))

    gate_table.setStyle(TableStyle(gate_style))
    story.append(gate_table)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"<b>Composite Risk Score: {score:.0f}/100 — {priority} Priority</b>",
        style("Score", fontSize=10, fontName="Helvetica-Bold",
              textColor=pri_color, spaceBefore=4)
    ))
    story.append(Paragraph(doc_content.get("uob_relevance",""), body))

    # ── SECTION 5: FINANCIAL IMPACT ───────────────────────────────────────────
    add_section_header("FINANCIAL IMPACT SIMULATION")
    if simulation:
        fi = simulation.get("financial_impact", {})
        impact_data = [
            ["Scenario", "Exposure (SGD)"],
            ["Baseline (no intervention)",
             _fmt_sgd(fi.get("baseline_exposure_sgd", 0))],
            ["With current TM controls",
             _fmt_sgd(fi.get("with_current_controls_sgd", 0))],
            ["With proposed interventions",
             _fmt_sgd(fi.get("with_proposed_controls_sgd", 0))],
            ["P10 (optimistic)", _fmt_sgd(fi.get("p10_sgd", 0))],
            ["P50 (median)", _fmt_sgd(fi.get("p50_sgd", 0))],
            ["P90 (worst case)", _fmt_sgd(fi.get("p90_sgd", 0))],
        ]
        imp_table = Table(impact_data, colWidths=["60%","40%"])
        imp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), white_color),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
            ("TEXTCOLOR", (1, 1), (1, 1), colors.Color(0.8, 0.1, 0.1)),
            ("FONTNAME", (0, 3), (0, 3), "Helvetica-Bold"),
            ("TEXTCOLOR", (1, 3), (1, 3), colors.Color(0.09, 0.64, 0.25)),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white_color, light_grey]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ]))
        story.append(imp_table)
        story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(doc_content.get("financial_exposure",""), body))

    # ── SECTION 6: RECOMMENDED ACTIONS ───────────────────────────────────────
    add_section_header("RECOMMENDED ACTIONS")
    rec = doc_content.get("recommended_actions", {})

    for timing, label_txt in [
        ("immediate", "⚡ Immediate (<24 hours)"),
        ("short_term", "📅 Short-term (1–7 days)"),
        ("strategic", "🎯 Strategic (1–4 weeks)"),
    ]:
        items = rec.get(timing, [])
        if items:
            story.append(Paragraph(label_txt, h3))
            for item in items:
                story.append(Paragraph(f"• {item}", bullet))

    # ── SECTION 7: INTERVENTION RULES ────────────────────────────────────────
    add_section_header("PROPOSED INTERVENTION RULES")

    rules = doc_content.get("intervention_rules", [])
    type_colors = {
        "TM_DETECTION": colors.Color(0.06, 0.35, 0.70),
        "CUSTOMER_FRICTION": colors.Color(0.50, 0.15, 0.70),
        "POLICY_CHANGE": colors.Color(0.80, 0.35, 0.04),
        "ADVISORY": colors.Color(0.09, 0.64, 0.25),
    }
    for i, rule in enumerate(rules, 1):
        rule_type = rule.get("rule_type", "")
        rc = type_colors.get(rule_type, navy_color)
        story.append(Paragraph(
            f'<b>{i}. {rule_type}</b>  '
            f'<font size="8" color="grey">Risk: {rule.get("deployment_risk","?")} · '
            f'Impact: ~{rule.get("expected_impact_pct",10):.0f}% · '
            f'Auto-deployable: {"Yes" if rule.get("auto_deployable") else "No"}</font>',
            style(f"RuleH{i}", fontSize=9.5, fontName="Helvetica-Bold",
                  textColor=rc, spaceBefore=8, spaceAfter=2)
        ))
        story.append(Paragraph(rule.get("rule_description",""), body))
        logic = rule.get("rule_logic","")
        if logic:
            story.append(Paragraph(
                f"<font name='Courier' size='8'>{logic}</font>",
                style("Logic", fontSize=8, fontName="Courier",
                      backColor=light_grey, leftIndent=8, rightIndent=8,
                      borderPadding=4, spaceAfter=4)
            ))
        if rule.get("approval_required"):
            story.append(Paragraph(
                "⚠ Requires Head of Fraud Risk sign-off",
                style("Warn", fontSize=8, textColor=colors.orange)
            ))

    # ── SECTION 8: EVIDENCE SOURCES ──────────────────────────────────────────
    add_section_header("EVIDENCE SOURCES")
    sources = doc_content.get("evidence_sources", [])
    if isinstance(sources, str):
        sources = [sources]
    if not sources:
        sources = [fraud_signal.get("source_credibility",""), fraud_signal.get("raw_evidence","")[:200]]
    for i, src in enumerate(sources, 1):
        if src:
            story.append(Paragraph(f"{i}. {src}", bullet))

    # ── SECTION 9: ANALYST NOTES ─────────────────────────────────────────────
    add_section_header("ANALYST NOTES & CAVEATS")
    story.append(Paragraph(doc_content.get("analyst_notes",""), disclaimer))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=teal_color))
    story.append(Paragraph(
        f"RESTRICTED — UOB Group Compliance — Phantom Signal POC | "
        f"Alert {alert_id[:8].upper()} | {generated_at} UTC",
        style("Footer", fontSize=7, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    logger.info("PDF generated: %s", pdf_path)
    return pdf_path


def read_pdf_bytes(pdf_path: str) -> Optional[bytes]:
    """Read PDF bytes for Streamlit download."""
    try:
        with open(pdf_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error("Failed to read PDF %s: %s", pdf_path, e)
        return None
