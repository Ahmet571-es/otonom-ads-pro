"""🧠 AI Strateji Motoru - Claude Powered Strategy Engine"""
import streamlit as st
import json
from datetime import datetime
from database import init_db, fetch_all, insert, log_action
from ai_engine import generate_strategy, analyze_performance, generate_ad_copy
from config import Config

init_db()

st.set_page_config(page_title="AI Strateji Motoru", page_icon="🧠", layout="wide")
st.markdown('<div class="section-header">🧠 AI Strateji Motoru — Claude Powered</div>', unsafe_allow_html=True)

if not Config.ANTHROPIC_API_KEY:
    st.error("❌ Anthropic API Key yapılandırılmamış. Ayarlar sayfasından girin.")
    st.stop()

clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Müşteri eklenmemiş.")
    st.stop()

selected = st.selectbox("Müşteri", [c["name"] for c in clients])
client = next(c for c in clients if c["name"] == selected)
customer_id = client.get("google_ads_id", "")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Performans Analizi", "🎯 Tam Strateji", "✍️ Reklam Metni Üretici", "📜 Geçmiş Stratejiler"])

with tab1:
    st.markdown("### 📊 Hızlı AI Performans Analizi")
    st.caption("Claude AI mevcut kampanya verilerinizi analiz eder ve Türkçe öneriler sunar.")

    campaigns = st.session_state.get(f"campaigns_{customer_id}", [])
    daily = st.session_state.get(f"daily_{customer_id}", [])

    if not campaigns:
        campaigns = fetch_all("campaigns", where="client_id = ?", params=[client["id"]])

    if not campaigns:
        st.warning("Kampanya verisi yok. Önce Veri Senkronizasyonu yapın.")
    else:
        if st.button("🔍 AI Analiz Başlat", type="primary", key="quick_analysis"):
            with st.spinner("Claude AI analiz ediyor..."):
                result = analyze_performance(
                    {"name": client["name"], "monthly_budget": client.get("monthly_budget", 0)},
                    campaigns, daily
                )
                st.markdown(result)
                log_action(client["id"], "ai_analysis", "AI performans analizi oluşturuldu")

with tab2:
    st.markdown("### 🎯 Kapsamlı AI Strateji Oluşturma")
    st.caption("Claude AI tam kapsamlı strateji, bütçe dağılımı, KPI hedefleri ve haftalık aksiyon planı oluşturur.")

    custom_prompt = st.text_area("Ek Talimatlar (opsiyonel)",
                                  placeholder="Örn: Ramazan ayına özel strateji oluştur, B2B segmentine odaklan...")

    campaigns = st.session_state.get(f"campaigns_{customer_id}", [])
    keywords = st.session_state.get(f"keywords_{customer_id}", [])
    search_terms = st.session_state.get(f"search_terms_{customer_id}", [])

    if st.button("🚀 Tam Strateji Oluştur", type="primary", key="full_strategy"):
        with st.spinner("Claude AI kapsamlı strateji oluşturuyor... (30-60 saniye)"):
            strategy = generate_strategy(
                client_info={
                    "name": client["name"],
                    "sector": client.get("sector", ""),
                    "website": client.get("website", ""),
                    "monthly_budget": client.get("monthly_budget", 0),
                    "products": client.get("products", ""),
                    "target_cpa": client.get("target_cpa"),
                    "target_roas": client.get("target_roas"),
                },
                campaigns=campaigns,
                keywords=keywords,
                search_terms=search_terms,
                custom_prompt=custom_prompt,
            )

            if "error" in strategy:
                st.error(f"Hata: {strategy['error']}")
            else:
                # Analysis
                if strategy.get("analysis"):
                    st.markdown("#### 📋 Durum Analizi")
                    st.markdown(strategy["analysis"])

                # Recommendations
                recs = strategy.get("recommendations", [])
                if recs:
                    st.markdown("#### 💡 Öneriler")
                    for r in recs:
                        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(r.get("priority", ""), "⚪")
                        st.markdown(f"""
                        {priority_icon} **{r.get('title', '')}** [{r.get('category', '')}]
                        {r.get('description', '')}
                        *Beklenen Etki: {r.get('expected_impact', '')}*
                        """)
                        st.divider()

                # KPI Targets
                kpis = strategy.get("kpi_targets", {})
                if kpis:
                    st.markdown("#### 🎯 KPI Hedefleri")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Hedef CPA", f"₺{kpis.get('target_cpa', 0):.2f}")
                    with c2:
                        st.metric("Hedef ROAS", f"{kpis.get('target_roas', 0):.1f}x")
                    with c3:
                        st.metric("Hedef CTR", f"%{kpis.get('target_ctr', 0):.2f}")
                    with c4:
                        st.metric("Dönüşüm Oranı", f"%{kpis.get('target_conv_rate', 0):.2f}")

                # Action Plan
                plan = strategy.get("action_plan", [])
                if plan:
                    st.markdown("#### 📅 Haftalık Aksiyon Planı")
                    for week in plan:
                        st.markdown(f"**Hafta {week.get('week', '?')}:**")
                        for action in week.get("actions", []):
                            st.markdown(f"- {action}")

                # New Keyword Suggestions
                new_kw = strategy.get("new_keyword_suggestions", [])
                if new_kw:
                    st.markdown("#### 🔑 Yeni Anahtar Kelime Önerileri")
                    for kw in new_kw:
                        st.markdown(f"- **{kw.get('keyword', '')}** [{kw.get('match_type', '')}] "
                                    f"— Tahmini TBM: ₺{kw.get('estimated_cpc', 0):.2f} — {kw.get('reason', '')}")

                # Negative Keywords
                neg_kw = strategy.get("negative_keywords", [])
                if neg_kw:
                    st.markdown("#### 🚫 Önerilen Negatif Kelimeler")
                    st.code(", ".join(neg_kw))

                # Save strategy
                meta = strategy.get("_meta", {})
                insert("strategies",
                       client_id=client["id"],
                       title=f"AI Strateji — {datetime.now().strftime('%d.%m.%Y')}",
                       analysis=strategy.get("analysis", ""),
                       recommendations=json.dumps(recs, ensure_ascii=False),
                       budget_allocation=json.dumps(strategy.get("budget_allocation", []), ensure_ascii=False),
                       kpi_targets=json.dumps(kpis, ensure_ascii=False),
                       action_plan=json.dumps(plan, ensure_ascii=False),
                       ai_model=meta.get("model", ""),
                       tokens_used=meta.get("tokens", 0))

                log_action(client["id"], "ai_strategy", "Kapsamlı AI strateji oluşturuldu",
                           details={"tokens": meta.get("tokens", 0)})

                st.success("✅ Strateji oluşturuldu ve kaydedildi!")

with tab3:
    st.markdown("### ✍️ AI Reklam Metni Üretici")

    product_name = st.text_input("Ürün/Hizmet Adı", placeholder="Taze Kadayıf")
    product_desc = st.text_area("Ürün Açıklaması", placeholder="Geleneksel Türk tatlısı, günlük taze üretim...")
    target_audience = st.text_input("Hedef Kitle", placeholder="Tatlıcılar, pastaneler, restoranlar")

    if st.button("✍️ Reklam Metni Oluştur", type="primary") and product_name:
        with st.spinner("Reklam metinleri oluşturuluyor..."):
            ads = generate_ad_copy(product_name, product_desc, target_audience)
            if isinstance(ads, dict) and "error" in ads:
                st.error(ads["error"])
            elif isinstance(ads, list):
                for ad in ads:
                    st.markdown(f"#### Varyant {ad.get('variant', '?')}")
                    st.markdown("**Başlıklar:**")
                    for h in ad.get("headlines", []):
                        char_count = len(h)
                        color = "green" if char_count <= 30 else "red"
                        st.markdown(f"- {h} `({char_count}/30)`")
                    st.markdown("**Açıklamalar:**")
                    for d in ad.get("descriptions", []):
                        char_count = len(d)
                        st.markdown(f"- {d} `({char_count}/90)`")
                    st.caption(f"💬 Strateji: {ad.get('strategy', '')}")
                    st.divider()

with tab4:
    st.markdown("### 📜 Geçmiş Stratejiler")
    strategies = fetch_all("strategies", where="client_id = ?", params=[client["id"]], limit=20)
    if strategies:
        for s in strategies:
            with st.expander(f"📋 {s.get('title', 'Strateji')} — {s.get('created_at', '')}"):
                st.markdown(s.get("analysis", "Analiz yok"))
                if s.get("recommendations"):
                    try:
                        recs = json.loads(s["recommendations"])
                        for r in recs:
                            st.markdown(f"- **{r.get('title', '')}**: {r.get('description', '')}")
                    except:
                        pass
    else:
        st.info("Henüz strateji oluşturulmamış.")
