"""
Automated Report Generator
----------------------------
Renders a professional RCA / Audit PDF report from an agent execution
trace, using ReportLab. This is the "Bonus Feature: Generate RCA PDF
automatically" requirement.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from backend.config import REPORTS_DIR


def generate_rca_report(query: str, ctx_data: dict, filename: str | None = None) -> str:
    filename = filename or f"RCA_Report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = str(REPORTS_DIR / filename)

    doc = SimpleDocTemplate(out_path, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], textColor=colors.HexColor("#0e2a47"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=colors.HexColor("#0e2a47"))
    body = styles["BodyText"]

    story = []
    story.append(Paragraph("Unified Asset & Operations Brain", title_style))
    story.append(Paragraph("Root Cause Analysis / Audit Report", styles["Heading2"]))
    story.append(Paragraph(f"Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}", body))
    story.append(Spacer(1, 0.6*cm))

    story.append(Paragraph("Query", h2))
    story.append(Paragraph(query, body))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Executive Summary (AI-Generated)", h2))
    story.append(Paragraph(ctx_data.get("final_answer", "N/A").replace("\n", "<br/>"), body))
    story.append(Spacer(1, 0.4*cm))

    rca = ctx_data.get("rca")
    if rca:
        story.append(Paragraph("Root Cause Analysis", h2))
        rows = [["Failure Mode", "Occurrences"]] + [[f, str(c)] for f, c in rca.get("recurring_failure_modes", [])]
        if len(rows) > 1:
            t = Table(rows, hAlign="LEFT", colWidths=[9*cm, 4*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0e2a47")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]))
            story.append(t)
        story.append(Spacer(1, 0.4*cm))

    pred = ctx_data.get("prediction")
    if pred:
        story.append(Paragraph("Failure Prediction", h2))
        story.append(Paragraph(
            f"Equipment: {pred.get('equipment')}<br/>"
            f"Risk Score: {pred.get('risk_score')}<br/>"
            f"Remaining Useful Life: {pred.get('remaining_useful_life_days')} days<br/>"
            f"Basis: {pred.get('basis')}", body))
        story.append(Spacer(1, 0.4*cm))

    compliance = ctx_data.get("compliance")
    if compliance:
        story.append(Paragraph("Compliance Check", h2))
        story.append(Paragraph(
            f"Frameworks referenced: {', '.join(compliance.get('frameworks_referenced', [])) or 'None'}<br/>"
            f"Potential gaps: {', '.join(compliance.get('potential_gaps', [])) or 'None'}", body))
        story.append(Spacer(1, 0.4*cm))

    wo = ctx_data.get("work_orders", [])
    if wo:
        story.append(Paragraph("Maintenance History", h2))
        rows = [["Date", "Technician", "Failure Mode", "Downtime (h)"]]
        for w in wo[:12]:
            rows.append([str(w.get("date", "")), str(w.get("technician", "")),
                         str(w.get("failure_mode", "")), str(w.get("downtime_hours", ""))])
        t = Table(rows, hAlign="LEFT", colWidths=[3*cm, 4*cm, 4.5*cm, 2.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0e2a47")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

    trace = ctx_data.get("trace", [])
    if trace:
        story.append(PageBreak())
        story.append(Paragraph("Agent Reasoning Chain (Explainability)", h2))
        for step in trace:
            story.append(Paragraph(f"<b>{step['agent']}:</b> {step['message']}", body))
            story.append(Spacer(1, 0.15*cm))

    doc.build(story)
    return out_path
