"""🚫 Negatif Kelime Madenciliği - Automatic Negative Keyword Mining"""
import streamlit as st
import pandas as pd
from database import init_db, fetch_all, log_action, insert
from automation_engines import NegativeKeywordMiner

init_db()

st.set_page_config(page_title="Negatif Kelime Madenciliği", page_icon="🚫", layout="wide")
st.markdown('<div class="section-header">🚫 Negatif Kelime Madenciliği</div>', unsafe_allow_html=True)

clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Müşteri eklenmemiş.")
    st.stop()

selected = st.selectbox("Müşteri", [c["name"] for c in clients])
client = next(c for c in clients if c["name"] == selected)
customer_id = client.get("google_ads_id", "")

# Get search terms
search_terms = st.session_state.get(f"search_terms_{customer_id}", [])
if not search_terms:
    st.warning("Arama terimi verisi yok. Önce Veri Senkronizasyonu yapın.")
    st.stop()

st.markdown(f"**{len(search_terms)} arama terimi analiz edilecek**")

target_cpa = st.number_input("Hedef CPA (₺)", value=float(client.get("target_cpa", 0) or 20.0), step=1.0)

# ── Analysis ──
if st.button("🔍 Negatif Kelime Analizi Başlat", type="primary", use_container_width=True):
    candidates = NegativeKeywordMiner.analyze_search_terms(search_terms, target_cpa=target_cpa)

    if candidates:
        total_savings = sum(c["potential_savings"] for c in candidates)
        high_priority = [c for c in candidates if c["priority"] == "high"]
        medium_priority = [c for c in candidates if c["priority"] == "medium"]

        st.markdown(f"""
        ### 💡 {len(candidates)} Negatif Kelime Adayı Bulundu
        - 🔴 **Yüksek Öncelik:** {len(high_priority)}
        - 🟡 **Orta Öncelik:** {len(medium_priority)}
        - 💰 **Potansiyel Tasarruf:** ₺{total_savings:,.2f}
        """)

        tab1, tab2, tab3 = st.tabs(["🔴 Yüksek Öncelik", "🟡 Orta Öncelik", "📊 Tümü"])

        with tab1:
            if high_priority:
                for c in high_priority:
                    st.markdown(f"""
                    **🔴 "{c['search_term']}"** — {c['campaign']}
                    - {c['clicks']} tık, ₺{c['cost']:.2f} maliyet, {c['conversions']:.0f} dönüşüm
                    - Önerilen eşleme: `{c['suggested_match']}`
                    - Sebepler: {' | '.join(c['reasons'])}
                    """)

                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("✅ Ekle", key=f"add_neg_{c['search_term'][:20]}"):
                            try:
                                from google_ads_client import add_negative_keywords
                                add_negative_keywords(customer_id, c["campaign_id"],
                                                      [{"text": c["search_term"], "match_type": c["suggested_match"]}])
                                log_action(client["id"], "negative_kw_added",
                                           f"'{c['search_term']}' negatif olarak eklendi")
                                st.success(f"✅ '{c['search_term']}' negatif olarak eklendi!")
                            except Exception as e:
                                st.error(f"Hata: {e}")
                    st.divider()
            else:
                st.success("Yüksek öncelikli negatif kelime yok.")

        with tab2:
            if medium_priority:
                for c in medium_priority[:20]:
                    st.markdown(f"""
                    **🟡 "{c['search_term']}"** — {c['clicks']} tık, ₺{c['cost']:.2f}
                    - {' | '.join(c['reasons'])}
                    """)
            else:
                st.success("Orta öncelikli negatif kelime yok.")

        with tab3:
            df = pd.DataFrame(candidates)
            cols = ["search_term", "campaign", "clicks", "cost", "conversions", "priority", "suggested_match", "potential_savings"]
            available = [c for c in cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True, hide_index=True)

        # Batch apply
        st.divider()
        if high_priority:
            st.markdown("### ⚡ Toplu Ekleme")
            if st.button(f"🚫 Tüm Yüksek Öncelikli ({len(high_priority)}) Negatif Kelimeleri Ekle",
                         type="primary"):
                added = 0
                for c in high_priority:
                    try:
                        from google_ads_client import add_negative_keywords
                        add_negative_keywords(customer_id, c["campaign_id"],
                                              [{"text": c["search_term"], "match_type": c["suggested_match"]}])
                        added += 1
                    except:
                        pass
                log_action(client["id"], "negative_kw_batch",
                           f"{added} negatif kelime toplu eklendi. Potansiyel tasarruf: ₺{total_savings:,.2f}")
                st.success(f"✅ {added}/{len(high_priority)} negatif kelime eklendi! Potansiyel tasarruf: ₺{total_savings:,.2f}")
    else:
        st.success("✅ Arama terimleri temiz! Negatif kelime adayı bulunamadı.")

# ── Existing Negatives ──
st.divider()
st.markdown("### 📋 Mevcut Negatif Kelimeler (Veritabanı)")
existing = fetch_all("keywords", where="is_negative = 1", limit=50)
if existing:
    df = pd.DataFrame(existing)
    st.dataframe(df[["text", "match_type", "created_at"]], use_container_width=True, hide_index=True)
else:
    st.info("Veritabanında kayıtlı negatif kelime yok.")
