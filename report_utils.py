"""Utility Functions - PDF Reports, Formatting, Helpers"""
import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ── Color Palette ──
COLORS = {
    "primary": "#1B5E20",
    "secondary": "#4CAF50",
    "accent": "#81C784",
    "dark": "#0E1117",
    "text": "#333333",
    "light_bg": "#F5F5F5",
    "white": "#FFFFFF",
    "red": "#E53935",
    "orange": "#FF9800",
    "green": "#43A047",
}


def format_currency(value, symbol="₺"):
    """Format number as Turkish currency."""
    if value is None:
        return f"{symbol}0"
    return f"{symbol}{value:,.2f}"


def format_number(value):
    """Format number with thousands separator."""
    if value is None:
        return "0"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return f"{value:,}"


def format_pct(value):
    """Format as percentage."""
    if value is None:
        return "%0"
    return f"%{value:.2f}"


def severity_emoji(severity):
    """Return emoji for severity level."""
    return {"critical": "🔴", "emergency": "🚨", "warning": "🟡", "info": "🔵", "success": "🟢"}.get(severity, "⚪")


def generate_pdf_report(client_info, campaigns, summary, strategies=None, anomalies=None):
    """Generate professional PDF performance report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"],
                                  fontSize=24, spaceAfter=20,
                                  textColor=HexColor(COLORS["primary"]))
    heading_style = ParagraphStyle("CustomHeading", parent=styles["Heading2"],
                                    fontSize=16, spaceAfter=12,
                                    textColor=HexColor(COLORS["primary"]))
    body_style = ParagraphStyle("CustomBody", parent=styles["Normal"],
                                 fontSize=10, spaceAfter=6)
    small_style = ParagraphStyle("Small", parent=styles["Normal"],
                                  fontSize=8, textColor=HexColor("#888888"))

    elements = []

    # ── Cover ──
    elements.append(Spacer(1, 3 * cm))
    elements.append(Paragraph("OTONOM ADS PRO", title_style))
    elements.append(Paragraph("Google Ads Performans Raporu", heading_style))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph(f"<b>Müşteri:</b> {client_info.get('name', 'N/A')}", body_style))
    elements.append(Paragraph(f"<b>Rapor Tarihi:</b> {datetime.now().strftime('%d.%m.%Y')}", body_style))
    elements.append(Paragraph(f"<b>Sektör:</b> {client_info.get('sector', 'N/A')}", body_style))
    elements.append(Paragraph(f"<b>Aylık Bütçe:</b> {format_currency(client_info.get('monthly_budget', 0))}", body_style))
    elements.append(PageBreak())

    # ── Summary ──
    elements.append(Paragraph("Genel Performans Özeti", heading_style))
    if summary:
        summary_data = [
            ["Metrik", "Değer"],
            ["Gösterim", format_number(summary.get("impressions", 0))],
            ["Tıklama", format_number(summary.get("clicks", 0))],
            ["Maliyet", format_currency(summary.get("cost", 0))],
            ["Dönüşüm", format_number(summary.get("conversions", 0))],
            ["CTR", format_pct(summary.get("ctr", 0))],
            ["Ort. TBM", format_currency(summary.get("avg_cpc", 0))],
            ["CPA", format_currency(summary.get("cpa", 0))],
        ]
        t = Table(summary_data, colWidths=[8 * cm, 8 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(COLORS["primary"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(COLORS["white"])),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor(COLORS["white"]), HexColor(COLORS["light_bg"])]),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
    elements.append(Spacer(1, 1 * cm))

    # ── Campaign Performance ──
    if campaigns:
        elements.append(Paragraph("Kampanya Performansı", heading_style))
        camp_data = [["Kampanya", "Gösterim", "Tıklama", "Maliyet", "Dönüşüm", "CTR", "CPA"]]
        for c in campaigns[:15]:
            name = c.get("name", "")[:30]
            camp_data.append([
                name,
                format_number(c.get("impressions", 0)),
                format_number(c.get("clicks", 0)),
                format_currency(c.get("cost", 0)),
                str(int(c.get("conversions", 0))),
                format_pct(c.get("ctr", 0)),
                format_currency(c.get("cpa", 0)),
            ])
        t = Table(camp_data, colWidths=[5.5*cm, 2*cm, 2*cm, 2.5*cm, 1.8*cm, 1.5*cm, 2*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(COLORS["primary"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor(COLORS["white"])),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor(COLORS["white"]), HexColor(COLORS["light_bg"])]),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 1 * cm))

    # ── Anomalies ──
    if anomalies:
        elements.append(Paragraph("Tespit Edilen Anomaliler", heading_style))
        for a in anomalies:
            sev = severity_emoji(a.get("severity", "info"))
            elements.append(Paragraph(f"{sev} <b>[{a.get('severity','').upper()}]</b> {a.get('message','')}", body_style))
        elements.append(Spacer(1, 1 * cm))

    # ── Footer ──
    elements.append(Spacer(1, 2 * cm))
    elements.append(Paragraph(f"Bu rapor Otonom Ads Pro v{4.0} tarafından otomatik oluşturulmuştur.", small_style))
    elements.append(Paragraph(f"Oluşturma tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", small_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
