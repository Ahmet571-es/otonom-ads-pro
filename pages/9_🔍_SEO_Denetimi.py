"""🔍 SEO Denetimi - Advanced Professional SEO Audit & Analysis"""
import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from database import init_db, fetch_all, insert, log_action
from seo_auditor import SEOAuditor
from ai_engine import generate_seo_recommendations
from config import Config

init_db()

st.markdown('<div class="section-header">🔍 Gelişmiş SEO Denetimi & Analizi</div>', unsafe_allow_html=True)
st.caption("Derinlemesine SEO analizi: Meta, İçerik, Anahtar Kelime, Hız, Güvenlik, Rakip Karşılaştırma ve daha fazlası")

clients = fetch_all("clients", order_by="name ASC")

# ── URL INPUT ──
col1, col2 = st.columns([3, 1])
with col1:
    default_url = ""
    selected_client = "Manuel URL Gir"
    if clients:
        selected_client = st.selectbox("Müşteri (opsiyonel)", ["Manuel URL Gir"] + [c["name"] for c in clients])
        if selected_client != "Manuel URL Gir":
            client = next(c for c in clients if c["name"] == selected_client)
            default_url = client.get("website", "")
    url = st.text_input("Site URL", value=default_url, placeholder="https://kralgida.com")

with col2:
    st.markdown("<br/>", unsafe_allow_html=True)
    run_audit = st.button("🔍 SEO Denetimi Başlat", type="primary", use_container_width=True)

# ── COMPETITOR INPUT ──
with st.expander("🏆 Rakip Karşılaştırma (Opsiyonel)"):
    competitor_url = st.text_input("Rakip Site URL", placeholder="https://rakipsite.com")
    run_compare = st.button("📊 Rakiple Karşılaştır")

# ═══════════════════════════════════════════════════════════════════
#  MAIN AUDIT
# ═══════════════════════════════════════════════════════════════════
if run_audit and url:
    with st.spinner("🔍 Site derinlemesine analiz ediliyor... (Bu işlem 30-60 saniye sürebilir)"):
        progress = st.progress(0, text="Meta analizi yapılıyor...")
        auditor = SEOAuditor(url)
        results = auditor.full_audit()
        progress.progress(100, text="Analiz tamamlandı!")

    st.session_state["seo_results"] = results
    st.session_state["seo_auditor"] = auditor

    # ── OVERALL SCORE ──
    score = results.get("overall_score", 0)
    grade = results.get("grade", "?")
    score_color = "#4CAF50" if score >= 70 else "#FF9800" if score >= 40 else "#E53935"

    col_score, col_grade, col_summary = st.columns([2, 1, 2])

    with col_score:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "SEO Puanı", "font": {"color": "#E6EDF3", "size": 20}},
            number={"suffix": "/100", "font": {"color": "#E6EDF3"}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"color": "#8B949E"}},
                "bar": {"color": score_color},
                "steps": [
                    {"range": [0, 40], "color": "rgba(229,57,53,0.2)"},
                    {"range": [40, 70], "color": "rgba(255,152,0,0.2)"},
                    {"range": [70, 100], "color": "rgba(76,175,80,0.2)"},
                ],
            },
        ))
        fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_grade:
        grade_colors = {"A+": "#4CAF50", "A": "#66BB6A", "B": "#FFC107", "C": "#FF9800", "D": "#FF5722", "F": "#E53935"}
        st.markdown(f"""
        <div style="text-align:center; padding:30px;">
            <div style="font-size:80px; font-weight:bold; color:{grade_colors.get(grade, '#999')};">{grade}</div>
            <div style="color:#8B949E; font-size:14px;">SEO Notu</div>
        </div>
        """, unsafe_allow_html=True)

    with col_summary:
        summary = results.get("summary", {})
        st.markdown("### 📊 Özet")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("🔴 Kritik", summary.get("critical_count", 0))
        with c2:
            st.metric("🟡 Uyarı", summary.get("warning_count", 0))
        with c3:
            st.metric("🔵 Bilgi", summary.get("info_count", 0))

        st.metric("📋 Toplam Sorun", summary.get("total_issues", 0))

    # ── SECTION SCORES RADAR ──
    section_scores = results.get("section_scores", {})
    if section_scores:
        labels_map = {
            "meta_analysis": "Meta",
            "heading_structure": "Başlıklar",
            "image_analysis": "Görseller",
            "link_analysis": "Linkler",
            "content_analysis": "İçerik",
            "keyword_analysis": "Anahtar Kelime",
            "technical": "Teknik",
            "security_headers": "Güvenlik",
            "page_speed": "Hız",
            "mobile_friendly": "Mobil",
            "schema_markup": "Schema",
            "social_media": "Sosyal",
            "backlink_indicators": "Backlink",
            "featured_snippet": "Snippet",
            "multi_page": "Çoklu Sayfa",
        }
        labels = [labels_map.get(k, k) for k in section_scores.keys()]
        values = list(section_scores.values())

        fig_radar = go.Figure(data=go.Scatterpolar(
            r=values, theta=labels, fill='toself',
            line=dict(color='#4CAF50'), fillcolor='rgba(76,175,80,0.2)',
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, gridcolor="#30363D"),
                angularaxis=dict(gridcolor="#30363D"),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=False, height=400,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6EDF3"),
            title=dict(text="Kategori Bazlı SEO Performansı", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ── DETAIL TABS ──
    tabs = st.tabs([
        "📋 Tüm Sorunlar", "🏷️ Meta", "📝 İçerik", "🔑 Anahtar Kelimeler",
        "⚡ Teknik & Hız", "🔒 Güvenlik", "📱 Mobil",
        "🔗 Linkler", "🖼️ Görseller", "📐 Schema",
        "📣 Sosyal Medya", "🎯 Snippet", "📄 Çoklu Sayfa",
    ])

    # ── TAB 0: ALL ISSUES ──
    with tabs[0]:
        issues = results.get("issues", [])
        if issues:
            # Category filter
            categories = list(set(i.get("category", "other") for i in issues))
            cat_filter = st.multiselect("Kategori Filtresi", categories, default=categories)
            severity_filter = st.multiselect("Önem Filtresi", ["critical", "warning", "info"], default=["critical", "warning", "info"])

            filtered = [i for i in issues if i.get("category", "other") in cat_filter and i.get("severity", "info") in severity_filter]
            for issue in filtered:
                sev = issue.get("severity", "info")
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(sev, "⚪")
                cat = issue.get("category", "").upper()
                st.markdown(f"{icon} **[{cat}]** {issue.get('message', '')}")
        else:
            st.success("🎉 Sorun bulunamadı!")

    # ── TAB 1: META ──
    with tabs[1]:
        meta = results.get("meta_analysis", {})
        details = meta.get("details", {})
        if details:
            st.markdown(f"**Title:** {details.get('title', 'Yok')}")
            st.progress(min(100, max(0, int(details.get('title_length', 0) / 60 * 100))), text=f"{details.get('title_length', 0)}/60 karakter")

            st.markdown(f"**Meta Description:** {details.get('meta_description', 'Yok')[:150]}")
            st.progress(min(100, max(0, int(details.get('meta_description_length', 0) / 160 * 100))), text=f"{details.get('meta_description_length', 0)}/160 karakter")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Canonical", "✅" if details.get("canonical") else "❌")
            with c2:
                st.metric("Viewport", "✅" if details.get("has_viewport") else "❌")
            with c3:
                st.metric("OG Tags", details.get("og_tags_count", 0))
            with c4:
                st.metric("Dil", details.get("lang", "Yok"))

            if details.get("is_multilingual"):
                st.success(f"🌍 Çok dilli site! {len(details.get('hreflang_tags', []))} dil tespit edildi.")
                for h in details.get("hreflang_tags", []):
                    st.markdown(f"  - `{h['lang']}`: {h['href']}")

            if details.get("og_tags"):
                with st.expander("Open Graph Detayları"):
                    for k, v in details["og_tags"].items():
                        st.markdown(f"**{k}:** {v[:100]}")

    # ── TAB 2: CONTENT ──
    with tabs[2]:
        content = results.get("content_analysis", {})
        headings = results.get("heading_structure", {})

        if content:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Kelime Sayısı", content.get("word_count", 0))
            with c2:
                st.metric("Cümle Sayısı", content.get("sentence_count", 0))
            with c3:
                st.metric("Okunabilirlik", f"{content.get('readability_score', 0)}/100")
            with c4:
                st.metric("Metin/HTML", f"%{content.get('text_html_ratio', 0)}")

            # Readability gauge
            read_score = content.get("readability_score", 0)
            read_color = "#4CAF50" if read_score >= 60 else "#FF9800" if read_score >= 40 else "#E53935"
            st.markdown(f"**Okunabilirlik Skoru:** ", unsafe_allow_html=True)
            st.progress(int(read_score), text=f"{read_score}/100 - {'İyi' if read_score >= 60 else 'Orta' if read_score >= 40 else 'Düşük'}")

        if headings and "headings" in headings:
            st.markdown("### Başlık Yapısı")
            for level, texts in headings["headings"].items():
                if texts:
                    st.markdown(f"**{level.upper()}** ({len(texts)} adet)")
                    for t in texts[:8]:
                        st.markdown(f"  └ {t}")

    # ── TAB 3: KEYWORDS ──
    with tabs[3]:
        kw = results.get("keyword_analysis", {})
        if kw:
            st.markdown("### 🔑 En Çok Kullanılan Anahtar Kelimeler")

            top_kws = kw.get("top_keywords", [])[:15]
            if top_kws:
                kw_data = {"Kelime": [k["keyword"] for k in top_kws],
                           "Tekrar": [k["count"] for k in top_kws],
                           "Yoğunluk %": [k["density"] for k in top_kws]}

                fig_kw = px.bar(kw_data, x="Kelime", y="Tekrar", color="Yoğunluk %",
                                color_continuous_scale="Greens", title="Anahtar Kelime Dağılımı")
                fig_kw.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                     font=dict(color="#E6EDF3"), height=350)
                st.plotly_chart(fig_kw, use_container_width=True)

            # Keyword placement
            placement = kw.get("keyword_placement", [])
            if placement:
                st.markdown("### 📍 Anahtar Kelime Yerleşimi")
                for p in placement:
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"**{p['keyword']}** ({p['count']}x)")
                    with c2:
                        st.markdown(f"Title: {'✅' if p['in_title'] else '❌'}")
                    with c3:
                        st.markdown(f"Meta Desc: {'✅' if p['in_meta_desc'] else '❌'}")
                    with c4:
                        st.markdown(f"H1: {'✅' if p['in_h1'] else '❌'}")

            # Bigrams & Trigrams
            bigrams = kw.get("top_bigrams", [])
            trigrams = kw.get("top_trigrams", [])
            if bigrams:
                st.markdown("### 📝 İki Kelimelik İfadeler")
                for b in bigrams[:7]:
                    st.markdown(f"  - **{b['phrase']}** ({b['count']}x)")
            if trigrams:
                st.markdown("### 📝 Üç Kelimelik İfadeler")
                for t in trigrams[:5]:
                    st.markdown(f"  - **{t['phrase']}** ({t['count']}x)")

    # ── TAB 4: TECHNICAL & SPEED ──
    with tabs[4]:
        tech = results.get("technical", {}).get("details", {})
        speed = results.get("page_speed", {}).get("details", {})

        if tech:
            st.markdown("### ⚡ Teknik Performans")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("HTTP Status", tech.get("status_code", "?"))
            with c2:
                rt = tech.get("total_load_time", 0)
                st.metric("Yüklenme", f"{rt}s", delta=f"{'İyi' if rt < 1.5 else 'Yavaş'}")
            with c3:
                st.metric("Boyut", f"{tech.get('content_size_kb', 0):.0f} KB")
            with c4:
                st.metric("HTTPS", "✅" if tech.get("is_https") else "❌")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Robots.txt", "✅" if tech.get("has_robots_txt") else "❌")
            with c2:
                st.metric("Sitemap", "✅" if tech.get("has_sitemap") else "❌")
            with c3:
                st.metric("Sıkıştırma", tech.get("compression", "Yok"))
            with c4:
                st.metric("Sitemap URL", tech.get("sitemap_url_count", "?"))

            if tech.get("redirect_chain"):
                st.markdown("**Yönlendirme Zinciri:**")
                for i, r in enumerate(tech["redirect_chain"]):
                    st.markdown(f"  {i+1}. {r}")

        if speed:
            st.markdown("### 🚀 Sayfa Hızı Detayları")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("CSS Dosyaları", speed.get("css_files", 0))
            with c2:
                st.metric("JS Dosyaları", speed.get("js_files", 0))
            with c3:
                st.metric("Blocking JS", speed.get("blocking_js", 0))
            with c4:
                st.metric("Toplam Kaynak", speed.get("total_resources", 0))

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Inline CSS", speed.get("inline_css_blocks", 0))
            with c2:
                st.metric("Inline JS", speed.get("inline_js_blocks", 0))
            with c3:
                st.metric("Preload/Prefetch", speed.get("preload_hints", 0))

    # ── TAB 5: SECURITY ──
    with tabs[5]:
        sec = results.get("security_headers", {})
        if sec:
            sec_grade = sec.get("security_grade", "?")
            grade_color = {"A": "#4CAF50", "B": "#66BB6A", "C": "#FF9800", "D": "#FF5722", "F": "#E53935"}.get(sec_grade, "#999")
            st.markdown(f"### 🔒 Güvenlik Notu: <span style='color:{grade_color}; font-size:28px;'>{sec_grade}</span>", unsafe_allow_html=True)

            headers = sec.get("headers", {})
            for header, value in headers.items():
                is_ok = value and value != "Eksik"
                icon = "✅" if is_ok else "❌"
                st.markdown(f"{icon} **{header}:** {value}")

    # ── TAB 6: MOBILE ──
    with tabs[6]:
        mobile = results.get("mobile_friendly", {})
        details = mobile.get("details", {})
        if details:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Viewport", "✅" if details.get("has_viewport") else "❌")
            with c2:
                st.metric("Media Queries", "✅" if details.get("has_media_queries") else "❌")
            with c3:
                st.metric("AMP", "✅" if details.get("has_amp") else "❌")

            for issue in mobile.get("issues", []):
                st.warning(issue.get("message", ""))

    # ── TAB 7: LINKS ──
    with tabs[7]:
        links = results.get("link_analysis", {})
        if links:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("İç Linkler", links.get("internal_count", 0))
            with c2:
                st.metric("Dış Linkler", links.get("external_count", 0))
            with c3:
                st.metric("Dış Domainler", links.get("external_domain_count", 0))
            with c4:
                st.metric("Kırık Link", links.get("broken_link_count", 0))

            broken = links.get("broken_links", [])
            if broken:
                st.markdown("### ❌ Kırık Linkler")
                for bl in broken:
                    st.error(f"**{bl['url']}** → Status: {bl['status']}")

            with st.expander("İç Linkler Detay"):
                for l in links.get("top_internal", [])[:15]:
                    st.markdown(f"  - [{l['anchor'] or 'Boş'}]({l['url']})")

            with st.expander("Dış Linkler Detay"):
                for l in links.get("top_external", [])[:15]:
                    st.markdown(f"  - [{l['anchor'] or l['domain']}]({l['url']})")

    # ── TAB 8: IMAGES ──
    with tabs[8]:
        imgs = results.get("image_analysis", {})
        if imgs:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Toplam Görsel", imgs.get("total", 0))
            with c2:
                st.metric("Alt Eksik", imgs.get("missing_alt", 0))
            with c3:
                st.metric("Alt Kapsam", f"%{imgs.get('alt_coverage', 0)}")
            with c4:
                st.metric("Lazy Load", f"%{imgs.get('lazy_load_coverage', 0)}")

            if imgs.get("missing_dimensions", 0) > 0:
                st.warning(f"⚠️ {imgs['missing_dimensions']} görselde genişlik/yükseklik belirtilmemiş (CLS riski)")

    # ── TAB 9: SCHEMA ──
    with tabs[9]:
        schema = results.get("schema_markup", {})
        if schema:
            st.metric("Schema Bulundu", "✅" if schema.get("has_schema") else "❌")

            if schema.get("json_ld_types"):
                st.markdown("**JSON-LD Tipleri:**")
                for t in schema["json_ld_types"]:
                    st.markdown(f"  - ✅ {t}")

            if schema.get("microdata_types"):
                st.markdown("**Microdata Tipleri:**")
                for t in schema["microdata_types"]:
                    st.markdown(f"  - 📋 {t}")

            if schema.get("raw_schemas"):
                with st.expander("Ham Schema Verisi"):
                    for s in schema["raw_schemas"][:3]:
                        st.json(s)

    # ── TAB 10: SOCIAL ──
    with tabs[10]:
        social = results.get("social_media", {})
        profiles = social.get("profiles", {})
        if profiles:
            st.markdown("### 📣 Tespit Edilen Sosyal Medya Profilleri")
            icons = {"facebook": "📘", "instagram": "📸", "twitter": "🐦", "linkedin": "💼",
                     "youtube": "📺", "tiktok": "🎵", "pinterest": "📌"}
            for platform, handle in profiles.items():
                st.markdown(f"{icons.get(platform, '🔗')} **{platform.title()}:** {handle}")
        else:
            st.warning("Sosyal medya profil bağlantısı bulunamadı.")

    # ── TAB 11: FEATURED SNIPPET ──
    with tabs[11]:
        snippet = results.get("featured_snippet", {})
        readiness = snippet.get("readiness", {})
        if readiness:
            st.markdown("### 🎯 Featured Snippet Hazırlık Durumu")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Listeler", "✅" if readiness.get("has_lists") else "❌")
                st.caption(f"Sıralı: {readiness.get('ordered_lists', 0)}, Sırasız: {readiness.get('unordered_lists', 0)}")
            with c2:
                st.metric("Tablolar", "✅" if readiness.get("has_tables") else "❌")
            with c3:
                st.metric("FAQ/SSS", "✅" if readiness.get("has_faq_content") else "❌")

            if readiness.get("faq_signals"):
                st.info(f"FAQ sinyalleri: {', '.join(readiness['faq_signals'])}")

            st.metric("FAQ Schema", "✅" if readiness.get("has_faq_schema") else "❌")
            st.metric("Tanım Paragrafları (H2+P)", readiness.get("definition_paragraphs", 0))

    # ── TAB 12: MULTI-PAGE ──
    with tabs[12]:
        multi = results.get("multi_page", {})
        if multi:
            st.metric("Taranan Sayfa", multi.get("pages_crawled", 0))

            if multi.get("common_issues"):
                st.markdown("### ⚠️ Ortak Sorunlar")
                for issue in multi["common_issues"]:
                    st.warning(issue)

            if multi.get("page_results"):
                st.markdown("### 📄 Sayfa Detayları")
                for p in multi["page_results"]:
                    status_icon = "✅" if p["status"] == 200 else "❌"
                    title_icon = "✅" if p["has_title"] else "❌"
                    desc_icon = "✅" if p["has_meta_desc"] else "❌"
                    h1_icon = "✅" if p["has_h1"] else "❌"
                    speed_icon = "🟢" if p["load_time"] < 1.5 else "🟡" if p["load_time"] < 3 else "🔴"

                    st.markdown(f"""
                    {status_icon} **{p['title']}** ({p['load_time']}s {speed_icon})
                    <small style='color:#8B949E;'>{p['url']}</small>
                    Title: {title_icon} | Meta Desc: {desc_icon} | H1: {h1_icon}
                    """, unsafe_allow_html=True)
                    st.markdown("---")

    # ── AI SEO RECOMMENDATIONS ──
    st.divider()
    if Config.ANTHROPIC_API_KEY:
        if st.button("🧠 AI ile Derinlemesine SEO Analizi Al", type="primary", use_container_width=True):
            with st.spinner("Claude AI kapsamlı SEO analiz ediyor..."):
                ai_recs = generate_seo_recommendations(url, results)
                st.markdown(ai_recs)

    # ── BACKLINK INDICATORS ──
    with st.expander("🔗 Backlink & Güven Göstergeleri"):
        bl = results.get("backlink_indicators", {})
        indicators = bl.get("indicators", {})
        if indicators:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Tahmini Domain Yaşı", indicators.get("estimated_domain_age", "?"))
            with c2:
                st.metric("Sosyal Varlık", f"{indicators.get('social_presence_count', 0)} platform")
            with c3:
                trust = indicators.get("trust_signals", [])
                st.metric("Güven Sinyali", f"{len(trust)} adet")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Telefon", "✅" if indicators.get("has_phone") else "❌")
            with c2:
                st.metric("E-posta", "✅" if indicators.get("has_email") else "❌")
            with c3:
                st.metric("Adres", "✅" if indicators.get("has_address") else "❌")

            if trust:
                st.info(f"Güven sinyalleri: {', '.join(trust)}")

    # Save audit
    if clients and selected_client != "Manuel URL Gir":
        insert("seo_audits",
               client_id=client["id"], url=url,
               seo_score=score,
               issues=json.dumps(results.get("issues", []), ensure_ascii=False),
               recommendations=json.dumps(results.get("recommendations", []), ensure_ascii=False))
        log_action(client["id"], "seo_audit", f"Gelişmiş SEO denetimi: {score}/100 ({grade})")

# ═══════════════════════════════════════════════════════════════════
#  COMPETITOR COMPARISON
# ═══════════════════════════════════════════════════════════════════
if run_compare and url and competitor_url:
    with st.spinner("🏆 Rakip karşılaştırma yapılıyor..."):
        auditor = st.session_state.get("seo_auditor")
        if not auditor or not auditor.results:
            auditor = SEOAuditor(url)
            auditor.full_audit()

        comparison = auditor.compare_with_competitor(competitor_url)

    st.markdown("## 🏆 Rakip SEO Karşılaştırması")

    # Score comparison
    c1, c2 = st.columns(2)
    with c1:
        your_score = comparison.get("your_score", 0)
        st.markdown(f"### 🟢 Sizin Site: **{your_score}/100**")
        st.caption(url)
    with c2:
        comp_score = comparison.get("competitor_score", 0)
        st.markdown(f"### 🔵 Rakip: **{comp_score}/100**")
        st.caption(competitor_url)

    # Comparison table
    comp_data = comparison.get("comparison", {})
    if comp_data:
        fig_comp = go.Figure()
        metrics = list(comp_data.keys())
        your_vals = [comp_data[m]["yours"] for m in metrics]
        comp_vals = [comp_data[m]["competitor"] for m in metrics]

        fig_comp.add_trace(go.Bar(name="Sizin Site", x=metrics, y=your_vals, marker_color="#4CAF50"))
        fig_comp.add_trace(go.Bar(name="Rakip", x=metrics, y=comp_vals, marker_color="#2196F3"))
        fig_comp.update_layout(
            barmode="group", height=400,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E6EDF3"),
            title="Metrik Karşılaştırması",
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("### 📊 Detaylı Karşılaştırma")
        for metric, data in comp_data.items():
            winner = data["winner"]
            icon = "🟢" if winner == "Siz" else "🔵"
            st.markdown(f"{icon} **{metric}:** Siz: {data['yours']} | Rakip: {data['competitor']} → **{winner} önde**")

# ── AUDIT HISTORY ──
st.divider()
st.markdown("### 📜 Geçmiş Denetimler")
audits = fetch_all("seo_audits", limit=10)
if audits:
    for a in audits:
        st.markdown(f"🔍 **{a.get('url', '')}** — Puan: {a.get('seo_score', 0)}/100 — {a.get('created_at', '')}")
else:
    st.info("Henüz denetim yapılmamış.")
