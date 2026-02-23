"""🔄 Veri Senkronizasyonu - Google Ads Data Sync"""
import streamlit as st
import json
from datetime import datetime
from config import Config
from database import init_db, fetch_all, fetch_one, insert, update, log_action

init_db()

st.set_page_config(page_title="Veri Senkronizasyonu", page_icon="🔄", layout="wide")
st.markdown('<div class="section-header">🔄 Veri Senkronizasyonu</div>', unsafe_allow_html=True)

# Check API
api_ok = all([Config.GOOGLE_ADS_DEVELOPER_TOKEN, Config.GOOGLE_ADS_CLIENT_ID,
              Config.GOOGLE_ADS_CLIENT_SECRET, Config.GOOGLE_ADS_REFRESH_TOKEN])

if not api_ok:
    st.error("❌ Google Ads API yapılandırılmamış. Önce Ayarlar sayfasından credentials girin.")
    st.stop()

clients = fetch_all("clients", where="google_ads_id IS NOT NULL AND google_ads_id != ''", order_by="name ASC")

if not clients:
    st.warning("Google Ads ID'si olan müşteri bulunamadı. Önce Müşteri Yönetimi'nden ID atayın.")
    st.stop()

# ── Client Selection ──
client_names = [c["name"] for c in clients]
selected_name = st.selectbox("Müşteri Seçin", client_names)
client = next(c for c in clients if c["name"] == selected_name)
customer_id = client["google_ads_id"]

st.info(f"📡 Google Ads Müşteri ID: **{customer_id}**")

# ── Sync Options ──
col1, col2, col3 = st.columns(3)

with col1:
    days = st.selectbox("Veri Dönemi", [7, 14, 30, 60, 90], index=2)

with col2:
    sync_campaigns = st.checkbox("Kampanyalar", value=True)
    sync_keywords = st.checkbox("Anahtar Kelimeler", value=True)

with col3:
    sync_search_terms = st.checkbox("Arama Terimleri", value=True)
    sync_daily = st.checkbox("Günlük Trend", value=True)

# ── Sync Button ──
if st.button("🔄 Verileri Senkronize Et", use_container_width=True, type="primary"):
    try:
        from google_ads_client import (get_account_summary, get_campaign_performance,
                                 get_keyword_performance, get_search_terms,
                                 get_daily_performance)

        progress = st.progress(0)
        status = st.empty()

        # 1. Account Summary
        status.text("📊 Hesap özeti çekiliyor...")
        summary = get_account_summary(customer_id, days)
        progress.progress(20)

        if summary:
            st.session_state[f"summary_{customer_id}"] = summary
            log_action(client["id"], "sync_summary", f"Hesap özeti çekildi ({days} gün)")

        # 2. Campaigns
        campaigns = []
        if sync_campaigns:
            status.text("📋 Kampanya verileri çekiliyor...")
            campaigns = get_campaign_performance(customer_id, days)
            progress.progress(40)

            for camp in campaigns:
                existing = fetch_one("campaigns",
                                     "client_id = ? AND google_campaign_id = ?",
                                     [client["id"], str(camp["id"])])
                if existing:
                    update("campaigns",
                           """name=?, status=?, campaign_type=?, daily_budget=?,
                              impressions=?, clicks=?, cost=?, conversions=?,
                              ctr=?, avg_cpc=?, last_synced=?""",
                           "id=?",
                           [camp["name"], camp["status"], camp["type"], camp["daily_budget"],
                            camp["impressions"], camp["clicks"], camp["cost"], camp["conversions"],
                            camp["ctr"], camp["avg_cpc"], datetime.now().isoformat(), existing["id"]])
                else:
                    insert("campaigns",
                           client_id=client["id"], google_campaign_id=str(camp["id"]),
                           name=camp["name"], status=camp["status"], campaign_type=camp["type"],
                           daily_budget=camp["daily_budget"],
                           impressions=camp["impressions"], clicks=camp["clicks"],
                           cost=camp["cost"], conversions=camp["conversions"],
                           ctr=camp["ctr"], avg_cpc=camp["avg_cpc"],
                           last_synced=datetime.now().isoformat())

            st.session_state[f"campaigns_{customer_id}"] = campaigns
            log_action(client["id"], "sync_campaigns", f"{len(campaigns)} kampanya senkronize edildi")

        # 3. Keywords
        if sync_keywords:
            status.text("🔑 Anahtar kelimeler çekiliyor...")
            keywords = get_keyword_performance(customer_id, days=days)
            progress.progress(60)
            st.session_state[f"keywords_{customer_id}"] = keywords
            log_action(client["id"], "sync_keywords", f"{len(keywords)} anahtar kelime çekildi")

        # 4. Search Terms
        if sync_search_terms:
            status.text("🔍 Arama terimleri çekiliyor...")
            terms = get_search_terms(customer_id, days=days)
            progress.progress(80)
            st.session_state[f"search_terms_{customer_id}"] = terms
            log_action(client["id"], "sync_search_terms", f"{len(terms)} arama terimi çekildi")

        # 5. Daily Data
        if sync_daily:
            status.text("📈 Günlük trend verileri çekiliyor...")
            daily = get_daily_performance(customer_id, days=min(days, 30))
            progress.progress(90)
            st.session_state[f"daily_{customer_id}"] = daily

            # Save snapshots
            for d in daily:
                insert("performance_snapshots",
                       client_id=client["id"], snapshot_date=d["date"],
                       impressions=d["impressions"], clicks=d["clicks"],
                       cost=d["cost"], conversions=d["conversions"],
                       ctr=d["ctr"], avg_cpc=d["avg_cpc"])

        progress.progress(100)
        status.text("")

        # Update client status
        update("clients", "google_ads_status = ?, updated_at = ?", "id = ?",
               ["active", datetime.now().isoformat(), client["id"]])

        st.success(f"""
        ✅ Senkronizasyon tamamlandı!
        - 📊 Hesap özeti: ✓
        - 📋 Kampanyalar: {len(campaigns) if sync_campaigns else 'Atlandı'}
        - 🔑 Anahtar kelimeler: {len(st.session_state.get(f'keywords_{customer_id}', [])) if sync_keywords else 'Atlandı'}
        - 🔍 Arama terimleri: {len(st.session_state.get(f'search_terms_{customer_id}', [])) if sync_search_terms else 'Atlandı'}
        """)

        # Show summary
        if summary:
            st.markdown("### 📊 Hesap Özeti")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Gösterim", f"{summary['impressions']:,}")
            with c2:
                st.metric("Tıklama", f"{summary['clicks']:,}")
            with c3:
                st.metric("Maliyet", f"₺{summary['cost']:,.2f}")
            with c4:
                st.metric("Dönüşüm", f"{summary['conversions']:.0f}")

    except ImportError:
        st.error("google-ads kütüphanesi yüklenmemiş. requirements.txt'i kontrol edin.")
    except Exception as e:
        st.error(f"❌ Senkronizasyon hatası: {str(e)}")
        log_action(client["id"], "sync_error", str(e), severity="error")

# ── Show Cached Data ──
st.divider()
if f"campaigns_{customer_id}" in st.session_state:
    campaigns = st.session_state[f"campaigns_{customer_id}"]
    if campaigns:
        st.markdown("### 📋 Kampanya Verileri (Önbellek)")
        import pandas as pd
        df = pd.DataFrame(campaigns)
        cols_to_show = ["name", "status", "type", "impressions", "clicks", "cost", "conversions", "ctr", "avg_cpc"]
        available = [c for c in cols_to_show if c in df.columns]
        st.dataframe(df[available], use_container_width=True, hide_index=True)

# ── MCC Account List ──
st.divider()
with st.expander("📋 MCC Altındaki Hesaplar"):
    if st.button("Hesapları Listele"):
        try:
            from google_ads_client import get_accessible_customers
            accounts = get_accessible_customers()
            if accounts:
                st.write(f"**{len(accounts)} hesap bulundu:**")
                for acc in accounts:
                    formatted = f"{acc[:3]}-{acc[3:6]}-{acc[6:]}" if len(acc) >= 10 else acc
                    st.code(formatted)
            else:
                st.info("Erişilebilir hesap bulunamadı.")
        except Exception as e:
            st.error(f"Hata: {e}")
