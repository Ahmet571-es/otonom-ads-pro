"""✅ Onay Merkezi - Approval Center for Automated Actions"""
import streamlit as st
import json
from database import init_db, fetch_all, update, log_action

init_db()

st.set_page_config(page_title="Onay Merkezi", page_icon="✅", layout="wide")
st.markdown('<div class="section-header">✅ Onay Merkezi</div>', unsafe_allow_html=True)

st.caption("Otomasyon motorlarının önerdiği aksiyonları burada onaylayın veya reddedin.")

# ── Pending Approvals ──
pending = fetch_all("approvals", where="status = 'pending'", limit=50)

if pending:
    st.markdown(f"### ⏳ {len(pending)} Bekleyen Onay")

    for item in pending:
        action_type = item.get("action_type", "")
        icon = {
            "negative_keyword": "🚫",
            "bid_change": "🎯",
            "budget_change": "💰",
            "campaign_status": "📋",
        }.get(action_type, "📌")

        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"{icon} **{item.get('title', 'Aksiyon')}**")
                st.caption(item.get("description", ""))

                payload = item.get("payload")
                if payload:
                    try:
                        data = json.loads(payload)
                        st.json(data)
                    except:
                        st.text(payload)

            with col2:
                if st.button("✅ Onayla", key=f"approve_{item['id']}"):
                    update("approvals",
                           "status = 'approved', approved_at = datetime('now')",
                           "id = ?", [item["id"]])
                    log_action(item.get("client_id"), "approval_approved",
                               f"Onaylandı: {item.get('title', '')}")
                    st.rerun()

            with col3:
                if st.button("❌ Reddet", key=f"reject_{item['id']}"):
                    update("approvals",
                           "status = 'rejected', approved_at = datetime('now')",
                           "id = ?", [item["id"]])
                    log_action(item.get("client_id"), "approval_rejected",
                               f"Reddedildi: {item.get('title', '')}")
                    st.rerun()

            st.divider()
else:
    st.success("✅ Bekleyen onay bulunmuyor. Tüm aksiyonlar işlendi.")

# ── History ──
st.divider()
st.markdown("### 📜 Onay Geçmişi")

tab1, tab2 = st.tabs(["✅ Onaylanan", "❌ Reddedilen"])

with tab1:
    approved = fetch_all("approvals", where="status = 'approved'", limit=20)
    if approved:
        for a in approved:
            st.markdown(f"✅ **{a.get('title', '')}** — Onaylandı: {a.get('approved_at', '')}")
    else:
        st.info("Henüz onaylanan aksiyon yok.")

with tab2:
    rejected = fetch_all("approvals", where="status = 'rejected'", limit=20)
    if rejected:
        for r in rejected:
            st.markdown(f"❌ **{r.get('title', '')}** — Reddedildi: {r.get('approved_at', '')}")
    else:
        st.info("Henüz reddedilen aksiyon yok.")
