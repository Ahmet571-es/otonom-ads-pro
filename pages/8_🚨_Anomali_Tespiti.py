"""🚨 Anomali Tespiti & Uyarılar - Anomaly Detection"""
import streamlit as st
from database import init_db, fetch_all, update, create_alert, log_action
from automation_engines import AnomalyDetector

init_db()

st.set_page_config(page_title="Anomali Tespiti", page_icon="🚨", layout="wide")
st.markdown('<div class="section-header">🚨 Anomali Tespiti & Uyarı Merkezi</div>', unsafe_allow_html=True)

clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Müşteri eklenmemiş.")
    st.stop()

selected = st.selectbox("Müşteri", [c["name"] for c in clients])
client = next(c for c in clients if c["name"] == selected)
customer_id = client.get("google_ads_id", "")

# ── Run Detection ──
daily = st.session_state.get(f"daily_{customer_id}", [])

st.markdown("### 🔍 Anomali Analizi")
if daily:
    if st.button("🔍 Anomali Tespiti Çalıştır", type="primary"):
        anomalies = AnomalyDetector.detect_anomalies(daily)

        if anomalies:
            st.markdown(f"### ⚠️ {len(anomalies)} Anomali Tespit Edildi")

            for a in anomalies:
                sev = a.get("severity", "warning")
                if sev == "emergency":
                    st.markdown(f"""
                    <div class="alert-critical">
                        🚨 <strong>ACİL: {a.get('message', '')}</strong><br/>
                        <small>Tarih: {a.get('date', '')} | Metrik: {a.get('metric', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                elif sev == "critical":
                    st.markdown(f"""
                    <div class="alert-critical">
                        🔴 <strong>{a.get('message', '')}</strong><br/>
                        <small>Z-Score: {a.get('z_score', '')} | Tarih: {a.get('date', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="alert-warning">
                        🟡 {a.get('message', '')}<br/>
                        <small>Z-Score: {a.get('z_score', '')} | Tarih: {a.get('date', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)

                # Save alert
                create_alert(client["id"], a.get("metric", "unknown"), sev,
                             f"Anomali: {a.get('metric', '')}", a.get("message", ""))

            log_action(client["id"], "anomaly_detection",
                       f"{len(anomalies)} anomali tespit edildi", severity="warning")
        else:
            st.markdown("""
            <div class="alert-success">
                🟢 <strong>Tüm metrikler normal sınırlar içinde!</strong><br/>
                <small>Son 14 günlük veriler analiz edildi, anormal bir durum bulunamadı.</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.warning("Günlük trend verisi yok. Önce Veri Senkronizasyonu yapın.")

# ── Active Alerts ──
st.divider()
st.markdown("### 📋 Aktif Uyarılar")

alerts = fetch_all("alerts", where="client_id = ? AND is_resolved = 0",
                     params=[client["id"]], limit=20)
if alerts:
    for alert in alerts:
        sev = alert.get("severity", "warning")
        icon = {"critical": "🔴", "emergency": "🚨", "warning": "🟡"}.get(sev, "⚪")

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"{icon} **{alert.get('title', '')}** — {alert.get('message', '')} "
                        f"*({alert.get('created_at', '')})*")
        with col2:
            if st.button("✅ Çözüldü", key=f"resolve_{alert['id']}"):
                update("alerts", "is_resolved = 1, resolved_at = datetime('now')",
                       "id = ?", [alert["id"]])
                st.rerun()
else:
    st.success("✅ Aktif uyarı yok.")

# ── Resolved Alerts ──
with st.expander("📜 Çözülmüş Uyarılar"):
    resolved = fetch_all("alerts", where="client_id = ? AND is_resolved = 1",
                          params=[client["id"]], limit=50)
    if resolved:
        for r in resolved:
            st.caption(f"✅ {r.get('title', '')} — Çözüm: {r.get('resolved_at', '')}")
    else:
        st.info("Çözülmüş uyarı yok.")
