"""🔍 SEO Denetimi - Comprehensive SEO Audit"""
import streamlit as st
import json
import plotly.graph_objects as go
from database import init_db, fetch_all, insert, log_action
from seo_auditor import SEOAuditor
from ai_engine import generate_seo_recommendations
from config import Config

init_db()

st.set_page_config(page_title="SEO Denetimi", page_icon="🔍", layout="wide")
st.markdown('<div class="section-header">🔍 SEO Denetimi & Analizi</div>', unsafe_allow_html=True)

clients = fetch_all("clients", order_by="name ASC")

# URL input
col1, col2 = st.columns([3, 1])
with col1:
    default_url = ""
    if clients:
        selected_client = st.selectbox("Müşteri (opsiyonel)", ["Manuel URL Gir"] + [c["name"] for c in clients])
        if selected_client != "Manuel URL Gir":
            client = next(c for c in clients if c["name"] == selected_client)
            default_url = client.get("website", "")

    url = st.text_input("Site URL", value=default_url, placeholder="https://kralgida.com")

with col2:
    st.markdown("<br/>", unsafe_allow_html=True)
    run_audit = st.button("🔍 SEO Denetimi Başlat", type="primary", use_container_width=True)

if run_audit and url:
    with st.spinner("Site analiz ediliyor..."):
        auditor = SEOAuditor(url)
        results = auditor.full_audit()

    # ── Overall Score ──
    score = results.get("overall_score", 0)
    score_color = "#4CAF50" if score >= 70 else "#FF9800" if score >= 40 else "#E53935"

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

    # ── Issues Summary ──
    issues = results.get("issues", [])
    critical = sum(1 for i in issues if i.get("severity") == "critical")
    warnings = sum(1 for i in issues if i.get("severity") == "warning")
    info = sum(1 for i in issues if i.get("severity") == "info")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("🔴 Kritik", critical)
    with c2:
        st.metric("🟡 Uyarı", warnings)
    with c3:
        st.metric("🔵 Bilgi", info)

    # ── Detail Tabs ──
    tabs = st.tabs(["📋 Tüm Sorunlar", "🏷️ Meta Analizi", "📝 İçerik", "⚡ Teknik", "📱 Mobil", "🔗 Linkler"])

    with tabs[0]:
        if issues:
            for issue in issues:
                sev = issue.get("severity", "info")
                icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(sev, "⚪")
                st.markdown(f"{icon} {issue.get('message', '')}")
        else:
            st.success("Sorun bulunamadı!")

    with tabs[1]:
        meta = results.get("meta_analysis", {})
        if isinstance(meta, dict) and "error" not in meta:
            st.markdown(f"**Title:** {meta.get('title', 'Yok')} ({meta.get('title_length', 0)} karakter)")
            st.markdown(f"**Meta Description:** {meta.get('meta_description', 'Yok')[:100]}... ({meta.get('meta_description_length', 0)} karakter)")
            st.markdown(f"**Canonical:** {meta.get('canonical', 'Yok')}")
            st.markdown(f"**Robots:** {meta.get('robots', 'Belirlenmemiş')}")
            st.markdown(f"**Dil:** {meta.get('lang', 'Belirlenmemiş')}")
            st.markdown(f"**OG Etiketleri:** {meta.get('og_tags_count', 0)} adet")
            st.markdown(f"**Viewport:** {'✅ Var' if meta.get('has_viewport') else '❌ Yok'}")

    with tabs[2]:
        content = results.get("content_analysis", {})
        headings = results.get("heading_structure", {})
        if isinstance(content, dict):
            st.metric("Kelime Sayısı", content.get("word_count", 0))
        if isinstance(headings, dict) and "headings" in headings:
            for level, texts in headings["headings"].items():
                if texts:
                    st.markdown(f"**{level.upper()}** ({len(texts)} adet):")
                    for t in texts[:5]:
                        st.markdown(f"  - {t}")

    with tabs[3]:
        tech = results.get("technical", {})
        if isinstance(tech, dict):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("HTTP Status", tech.get("status_code", "?"))
                st.metric("HTTPS", "✅" if tech.get("is_https") else "❌")
            with c2:
                st.metric("Yanıt Süresi", f"{tech.get('response_time', 0):.2f}s")
                st.metric("Boyut", f"{tech.get('content_size_kb', 0):.0f} KB")
            with c3:
                st.metric("Robots.txt", "✅" if tech.get("has_robots_txt") else "❌")
                st.metric("Sitemap", "✅" if tech.get("has_sitemap") else "❌")

    with tabs[4]:
        mobile = results.get("mobile_friendly", {})
        if isinstance(mobile, dict):
            st.markdown(f"**Viewport Meta:** {'✅ Var' if mobile.get('has_viewport') else '❌ Yok'}")
            for issue in mobile.get("issues", []):
                st.warning(issue.get("message", ""))

    with tabs[5]:
        links = results.get("link_analysis", {})
        if isinstance(links, dict):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("İç Linkler", links.get("internal_count", 0))
            with c2:
                st.metric("Dış Linkler", links.get("external_count", 0))
            with c3:
                st.metric("Boş Anchor", links.get("empty_anchors", 0))

    # ── AI SEO Recommendations ──
    st.divider()
    if Config.ANTHROPIC_API_KEY:
        if st.button("🧠 AI ile SEO Önerileri Al", type="primary"):
            with st.spinner("Claude AI SEO analiz ediyor..."):
                ai_recs = generate_seo_recommendations(url, results)
                st.markdown(ai_recs)

    # Save audit
    if clients and selected_client != "Manuel URL Gir":
        insert("seo_audits",
               client_id=client["id"], url=url,
               seo_score=score,
               issues=json.dumps(issues, ensure_ascii=False),
               recommendations=json.dumps(results.get("recommendations", []), ensure_ascii=False))
        log_action(client["id"], "seo_audit", f"SEO denetimi tamamlandı: Puan {score}/100")

# ── Audit History ──
st.divider()
st.markdown("### 📜 Geçmiş Denetimler")
audits = fetch_all("seo_audits", limit=10)
if audits:
    for a in audits:
        st.markdown(f"🔍 **{a.get('url', '')}** — Puan: {a.get('seo_score', 0)}/100 — {a.get('created_at', '')}")
else:
    st.info("Henüz denetim yapılmamış.")
