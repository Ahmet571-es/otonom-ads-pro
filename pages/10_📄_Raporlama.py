"""📄 Raporlama - Professional PDF Report Generation"""
import streamlit as st
from datetime import datetime
from database import init_db, fetch_all
from report_utils import generate_pdf_report
from automation_engines import AnomalyDetector

init_db()

st.set_page_config(page_title="Raporlama", page_icon="📄", layout="wide")
st.markdown('<div class="section-header">📄 Profesyonel Raporlama</div>', unsafe_allow_html=True)

clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Müşteri eklenmemiş.")
    st.stop()

selected = st.selectbox("Müşteri", [c["name"] for c in clients])
client = next(c for c in clients if c["name"] == selected)
customer_id = client.get("google_ads_id", "")

st.markdown("### 📊 Rapor Oluştur")

col1, col2 = st.columns(2)
with col1:
    report_type = st.selectbox("Rapor Türü", [
        "Aylık Performans Raporu",
        "Haftalık Özet Raporu",
        "Kampanya Detay Raporu",
    ])
with col2:
    report_period = st.selectbox("Dönem", ["Son 7 Gün", "Son 14 Gün", "Son 30 Gün", "Son 60 Gün"])

include_anomalies = st.checkbox("Anomali tespitlerini dahil et", value=True)
include_recommendations = st.checkbox("AI önerilerini dahil et", value=True)

if st.button("📄 PDF Rapor Oluştur", type="primary", use_container_width=True):
    campaigns = st.session_state.get(f"campaigns_{customer_id}", [])
    if not campaigns:
        campaigns = fetch_all("campaigns", where="client_id = ?", params=[client["id"]])

    daily = st.session_state.get(f"daily_{customer_id}", [])
    summary = st.session_state.get(f"summary_{customer_id}")

    if not summary:
        total_imp = sum(c.get("impressions", 0) for c in campaigns)
        total_clicks = sum(c.get("clicks", 0) for c in campaigns)
        total_cost = sum(c.get("cost", 0) for c in campaigns)
        total_conv = sum(c.get("conversions", 0) for c in campaigns)
        summary = {
            "impressions": total_imp,
            "clicks": total_clicks,
            "cost": total_cost,
            "conversions": total_conv,
            "ctr": (total_clicks / total_imp * 100) if total_imp > 0 else 0,
            "avg_cpc": (total_cost / total_clicks) if total_clicks > 0 else 0,
            "cpa": (total_cost / total_conv) if total_conv > 0 else 0,
        }

    anomalies = None
    if include_anomalies and daily:
        anomalies = AnomalyDetector.detect_anomalies(daily)

    with st.spinner("PDF oluşturuluyor..."):
        pdf_buffer = generate_pdf_report(
            client_info={
                "name": client["name"],
                "sector": client.get("sector", ""),
                "website": client.get("website", ""),
                "monthly_budget": client.get("monthly_budget", 0),
            },
            campaigns=campaigns,
            summary=summary,
            anomalies=anomalies,
        )

        filename = f"otonom_ads_pro_{client['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        st.download_button(
            label="⬇️ PDF İndir",
            data=pdf_buffer,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )
        st.success(f"✅ {filename} oluşturuldu!")

# ── Action Log ──
st.divider()
st.markdown("### 📋 İşlem Geçmişi")

logs = fetch_all("action_logs", where="client_id = ?", params=[client["id"]], limit=30)
if logs:
    for log in logs:
        sev = log.get("severity", "info")
        icon = {"info": "🔵", "warning": "🟡", "error": "🔴", "success": "🟢"}.get(sev, "⚪")
        st.markdown(f"{icon} **{log.get('action_type', '')}** — {log.get('description', '')} — *{log.get('created_at', '')}*")
else:
    st.info("İşlem kaydı yok.")
