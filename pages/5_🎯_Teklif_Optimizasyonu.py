"""🎯 Teklif Optimizasyonu - Smart Bid Optimization"""
import streamlit as st
import pandas as pd
from database import init_db, fetch_all, log_action
from automation_engines import BidOptimizer

init_db()

st.set_page_config(page_title="Teklif Optimizasyonu", page_icon="🎯", layout="wide")
st.markdown('<div class="section-header">🎯 Akıllı Teklif Optimizasyonu</div>', unsafe_allow_html=True)

clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Müşteri eklenmemiş.")
    st.stop()

selected = st.selectbox("Müşteri", [c["name"] for c in clients])
client = next(c for c in clients if c["name"] == selected)
customer_id = client.get("google_ads_id", "")

# Get keyword data
keywords = st.session_state.get(f"keywords_{customer_id}", [])
if not keywords:
    st.warning("Anahtar kelime verisi yok. Önce Veri Senkronizasyonu yapın.")
    st.stop()

# ── Config ──
col1, col2 = st.columns(2)
with col1:
    target_cpa = st.number_input("Hedef CPA (₺)", value=float(client.get("target_cpa", 0) or 20), step=1.0)
with col2:
    target_roas = st.number_input("Hedef ROAS", value=float(client.get("target_roas", 0) or 3.0), step=0.1)

# ── Analysis ──
if st.button("🔍 Teklif Analizi Çalıştır", type="primary", use_container_width=True):
    suggestions = BidOptimizer.analyze_keywords(keywords, target_cpa=target_cpa, target_roas=target_roas)

    if suggestions:
        st.markdown(f"### 💡 {len(suggestions)} Teklif Önerisi Bulundu")

        increases = [s for s in suggestions if s["action"] == "increase"]
        decreases = [s for s in suggestions if s["action"] == "decrease"]

        tab1, tab2, tab3 = st.tabs([f"📈 Artırma ({len(increases)})", f"📉 Düşürme ({len(decreases)})", "📊 Tümü"])

        with tab1:
            if increases:
                for s in increases:
                    st.markdown(f"""
                    **📈 {s['keyword']}** ({s['campaign']} → {s['ad_group']})
                    - Mevcut TBM: ₺{s['current_cpc']:.2f} → Önerilen: ₺{s['suggested_cpc']:.2f} ({s['adjustment_pct']:+.1f}%)
                    - {s['conversions']:.0f} dönüşüm, ₺{s['cost']:.2f} harcama, QS: {s['quality_score']}
                    - 💬 {s['reason']}
                    """)
                    st.divider()
            else:
                st.success("Artırılması gereken teklif yok.")

        with tab2:
            if decreases:
                for s in decreases:
                    st.markdown(f"""
                    **📉 {s['keyword']}** ({s['campaign']} → {s['ad_group']})
                    - Mevcut TBM: ₺{s['current_cpc']:.2f} → Önerilen: ₺{s['suggested_cpc']:.2f} ({s['adjustment_pct']:+.1f}%)
                    - {s['conversions']:.0f} dönüşüm, ₺{s['cost']:.2f} harcama, QS: {s['quality_score']}
                    - 💬 {s['reason']}
                    """)
                    st.divider()
            else:
                st.success("Düşürülmesi gereken teklif yok.")

        with tab3:
            df = pd.DataFrame(suggestions)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={
                             "current_cpc": st.column_config.NumberColumn("Mevcut TBM", format="₺%.2f"),
                             "suggested_cpc": st.column_config.NumberColumn("Önerilen TBM", format="₺%.2f"),
                             "adjustment_pct": st.column_config.NumberColumn("Değişim", format="%.1f%%"),
                             "cost": st.column_config.NumberColumn("Maliyet", format="₺%.2f"),
                         })

        # Batch apply
        st.divider()
        st.markdown("### ⚡ Toplu Uygulama")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📈 Tüm Artırmaları Uygula", disabled=len(increases) == 0):
                for s in increases:
                    log_action(client["id"], "bid_increased",
                               f"{s['keyword']}: ₺{s['current_cpc']} → ₺{s['suggested_cpc']}")
                st.success(f"✅ {len(increases)} teklif artırıldı!")
        with col2:
            if st.button("📉 Tüm Düşürmeleri Uygula", disabled=len(decreases) == 0):
                for s in decreases:
                    log_action(client["id"], "bid_decreased",
                               f"{s['keyword']}: ₺{s['current_cpc']} → ₺{s['suggested_cpc']}")
                st.success(f"✅ {len(decreases)} teklif düşürüldü!")
    else:
        st.success("✅ Tüm teklifler optimal seviyede. Değişiklik gerekmiyor.")

# ── Keyword Overview ──
st.divider()
st.markdown("### 🔑 Anahtar Kelime Özeti")
df_kw = pd.DataFrame(keywords)
if not df_kw.empty:
    total_kw = len(df_kw)
    with_qs = df_kw[df_kw.get("quality_score", pd.Series(dtype=int)) > 0] if "quality_score" in df_kw.columns else pd.DataFrame()
    avg_qs = with_qs["quality_score"].mean() if not with_qs.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Toplam Kelime", total_kw)
    with c2:
        st.metric("Ort. QS", f"{avg_qs:.1f}/10")
    with c3:
        zero_conv = len(df_kw[df_kw.get("conversions", pd.Series(dtype=float)) == 0]) if "conversions" in df_kw.columns else 0
        st.metric("Sıfır Dönüşüm", zero_conv)
    with c4:
        total_kw_cost = df_kw["cost"].sum() if "cost" in df_kw.columns else 0
        st.metric("Toplam Maliyet", f"₺{total_kw_cost:,.0f}")
