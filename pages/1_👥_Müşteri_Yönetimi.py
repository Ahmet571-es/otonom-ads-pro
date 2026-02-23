"""👥 Müşteri Yönetimi - Client Management with Auto Account Creation"""
import streamlit as st
import json
from datetime import datetime
from config import Config
from database import init_db, insert, fetch_all, fetch_one, update, delete, log_action

init_db()

st.set_page_config(page_title="Müşteri Yönetimi", page_icon="👥", layout="wide")
st.markdown('<div class="section-header">👥 Müşteri Yönetimi</div>', unsafe_allow_html=True)

# ── New Client Form ──
with st.expander("➕ Yeni Müşteri Ekle", expanded=False):
    with st.form("new_client"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Firma Adı *", placeholder="Kral Gıda")
            sector = st.text_input("Sektör", placeholder="Gıda Üretimi")
            website = st.text_input("Website", placeholder="https://kralgida.com")
            monthly_budget = st.number_input("Aylık Bütçe (₺)", min_value=0.0, step=1000.0, value=40000.0)
        with col2:
            google_ads_id = st.text_input("Google Ads Müşteri ID", placeholder="123-456-7890 (varsa)")
            target_cpa = st.number_input("Hedef CPA (₺)", min_value=0.0, step=1.0, value=0.0)
            target_roas = st.number_input("Hedef ROAS", min_value=0.0, step=0.1, value=0.0)
            products = st.text_area("Ürünler / Hizmetler", placeholder="Kadayıf, Yufka, Börek Hamuru...")
        notes = st.text_area("Notlar", placeholder="Müşteri hakkında önemli notlar...")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            create_account = st.checkbox("🆕 Otomatik Google Ads hesabı oluştur (MCC altında)")
        submitted = st.form_submit_button("💾 Müşteri Kaydet", use_container_width=True)

        if submitted and name:
            client_id = insert("clients",
                               name=name, sector=sector, website=website,
                               monthly_budget=monthly_budget, products=products,
                               google_ads_id=google_ads_id.replace("-", "") if google_ads_id else "",
                               target_cpa=target_cpa if target_cpa > 0 else None,
                               target_roas=target_roas if target_roas > 0 else None,
                               notes=notes)

            log_action(client_id, "client_created", f"Yeni müşteri eklendi: {name}")

            # Auto-create Google Ads account
            if create_account and not google_ads_id:
                try:
                    from google_ads_client import create_customer_client
                    mcc_id = Config.GOOGLE_ADS_LOGIN_CUSTOMER_ID
                    if mcc_id:
                        new_ads_id = create_customer_client(mcc_id, name)
                        update("clients",
                               "google_ads_id = ?, google_ads_status = ?",
                               "id = ?",
                               [new_ads_id, "active", client_id])
                        log_action(client_id, "account_created",
                                   f"Google Ads hesabı oluşturuldu: {new_ads_id}")
                        st.success(f"✅ Müşteri eklendi ve Google Ads hesabı oluşturuldu! ID: {new_ads_id}")
                    else:
                        st.warning("MCC Login Customer ID ayarlanmamış. Ayarlar sayfasından girin.")
                except Exception as e:
                    st.error(f"Hesap oluşturma hatası: {e}")
                    st.success(f"✅ Müşteri eklendi. Google Ads hesabını manuel oluşturabilirsiniz.")
            else:
                st.success(f"✅ {name} başarıyla eklendi!")
            st.rerun()

# ── Client List ──
clients = fetch_all("clients", order_by="name ASC", limit=100)

if clients:
    st.markdown(f"### 📋 Kayıtlı Müşteriler ({len(clients)})")

    for client in clients:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

            with col1:
                st.markdown(f"**{client['name']}**")
                st.caption(f"{client.get('sector', '—')} | {client.get('website', '—')}")

            with col2:
                budget = client.get("monthly_budget", 0) or 0
                st.metric("Aylık Bütçe", f"₺{budget:,.0f}")

            with col3:
                ads_id = client.get("google_ads_id", "")
                if ads_id:
                    formatted = f"{ads_id[:3]}-{ads_id[3:6]}-{ads_id[6:]}" if len(ads_id) >= 10 else ads_id
                    st.markdown(f"🆔 `{formatted}`")
                else:
                    st.markdown("🆔 *Atanmamış*")

            with col4:
                status = client.get("google_ads_status", "pending")
                if status == "active":
                    st.markdown("🟢 Aktif")
                elif status == "pending":
                    st.markdown("🟡 Beklemede")
                else:
                    st.markdown("🔴 Pasif")

            with col5:
                if st.button("🗑️", key=f"del_{client['id']}", help="Müşteriyi sil"):
                    delete("clients", "id = ?", [client["id"]])
                    log_action(client["id"], "client_deleted", f"Müşteri silindi: {client['name']}")
                    st.rerun()

            # Expandable details
            with st.expander(f"📝 {client['name']} Detayları"):
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    new_budget = st.number_input("Bütçe", value=float(client.get("monthly_budget", 0) or 0),
                                                  key=f"budget_{client['id']}")
                    new_ads_id = st.text_input("Ads ID", value=client.get("google_ads_id", ""),
                                                key=f"adsid_{client['id']}")
                with edit_col2:
                    new_cpa = st.number_input("Hedef CPA", value=float(client.get("target_cpa", 0) or 0),
                                              key=f"cpa_{client['id']}")
                    new_roas = st.number_input("Hedef ROAS", value=float(client.get("target_roas", 0) or 0),
                                               key=f"roas_{client['id']}")

                if st.button("💾 Güncelle", key=f"update_{client['id']}"):
                    update("clients",
                           "monthly_budget = ?, google_ads_id = ?, target_cpa = ?, target_roas = ?, updated_at = ?",
                           "id = ?",
                           [new_budget, new_ads_id.replace("-", ""), new_cpa or None, new_roas or None,
                            datetime.now().isoformat(), client["id"]])
                    st.success("✅ Güncellendi!")
                    st.rerun()

            st.divider()
else:
    st.info("Henüz müşteri eklenmemiş. Yukarıdaki formu kullanarak ilk müşterinizi ekleyin.")
