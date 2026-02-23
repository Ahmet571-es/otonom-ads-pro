"""📈 Kampanya Performansı - Premium Performance Dashboard"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from database import init_db, fetch_all, fetch_one

init_db()

st.set_page_config(page_title="Kampanya Performansı", page_icon="📈", layout="wide")
st.markdown('<div class="section-header">📈 Kampanya Performansı</div>', unsafe_allow_html=True)

# ── Client Selection ──
clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Henüz müşteri eklenmemiş.")
    st.stop()

client_names = [c["name"] for c in clients]
selected_name = st.selectbox("Müşteri", client_names)
client = next(c for c in clients if c["name"] == selected_name)
customer_id = client.get("google_ads_id", "")

# ── Campaign Data ──
campaigns = fetch_all("campaigns", where="client_id = ?", params=[client["id"]])
snapshots = fetch_all("performance_snapshots", where="client_id = ?",
                       params=[client["id"]], order_by="snapshot_date ASC", limit=90)

# Also check session state for live data
session_campaigns = st.session_state.get(f"campaigns_{customer_id}", [])
session_daily = st.session_state.get(f"daily_{customer_id}", [])

# Use session data if available, otherwise DB
display_campaigns = session_campaigns if session_campaigns else campaigns
display_daily = session_daily if session_daily else snapshots

if not display_campaigns and not display_daily:
    st.warning("Henüz veri yok. Önce Veri Senkronizasyonu sayfasından verileri çekin.")
    st.stop()

# ── KPI Summary ──
if display_campaigns:
    total_impressions = sum(c.get("impressions", 0) for c in display_campaigns)
    total_clicks = sum(c.get("clicks", 0) for c in display_campaigns)
    total_cost = sum(c.get("cost", 0) for c in display_campaigns)
    total_conversions = sum(c.get("conversions", 0) for c in display_campaigns)
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    avg_cpa = (total_cost / total_conversions) if total_conversions > 0 else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Gösterim", f"{total_impressions:,}")
    with c2:
        st.metric("Tıklama", f"{total_clicks:,}")
    with c3:
        st.metric("Maliyet", f"₺{total_cost:,.2f}")
    with c4:
        st.metric("Dönüşüm", f"{total_conversions:.0f}")
    with c5:
        st.metric("CTR", f"%{avg_ctr:.2f}")
    with c6:
        st.metric("CPA", f"₺{avg_cpa:.2f}")

    st.divider()

# ── Tabs ──
tab1, tab2, tab3, tab4 = st.tabs(["📊 Kampanya Tablosu", "📈 Trend Grafikleri", "🎯 Performans Matrisi", "🔑 Anahtar Kelimeler"])

with tab1:
    if display_campaigns:
        df = pd.DataFrame(display_campaigns)
        cols = ["name", "status", "impressions", "clicks", "cost", "conversions", "ctr", "avg_cpc"]
        available = [c for c in cols if c in df.columns]
        if available:
            rename = {"name": "Kampanya", "status": "Durum", "impressions": "Gösterim",
                      "clicks": "Tıklama", "cost": "Maliyet (₺)", "conversions": "Dönüşüm",
                      "ctr": "CTR (%)", "avg_cpc": "Ort. TBM (₺)"}
            display_df = df[available].rename(columns=rename)
            st.dataframe(display_df, use_container_width=True, hide_index=True,
                         column_config={
                             "Maliyet (₺)": st.column_config.NumberColumn(format="₺%.2f"),
                             "Ort. TBM (₺)": st.column_config.NumberColumn(format="₺%.2f"),
                             "CTR (%)": st.column_config.NumberColumn(format="%.2f%%"),
                         })

            # Cost distribution chart
            if "name" in df.columns and "cost" in df.columns:
                fig = px.pie(df[df["cost"] > 0], values="cost", names="name",
                             title="Bütçe Dağılımı",
                             color_discrete_sequence=px.colors.sequential.Greens_r)
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E6EDF3",
                )
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    if display_daily:
        df_daily = pd.DataFrame(display_daily)
        date_col = "date" if "date" in df_daily.columns else "snapshot_date"

        if date_col in df_daily.columns:
            # Multi-metric chart
            fig = make_subplots(rows=2, cols=2,
                                subplot_titles=("Tıklama Trendi", "Maliyet Trendi",
                                                "CTR Trendi", "Dönüşüm Trendi"))

            fig.add_trace(go.Scatter(x=df_daily[date_col], y=df_daily.get("clicks", []),
                                     mode="lines+markers", name="Tıklama",
                                     line=dict(color="#4CAF50", width=2)), row=1, col=1)

            if "cost" in df_daily.columns:
                fig.add_trace(go.Scatter(x=df_daily[date_col], y=df_daily["cost"],
                                         mode="lines+markers", name="Maliyet",
                                         line=dict(color="#FF9800", width=2)), row=1, col=2)

            if "ctr" in df_daily.columns:
                fig.add_trace(go.Scatter(x=df_daily[date_col], y=df_daily["ctr"],
                                         mode="lines+markers", name="CTR",
                                         line=dict(color="#2196F3", width=2)), row=2, col=1)

            if "conversions" in df_daily.columns:
                fig.add_trace(go.Bar(x=df_daily[date_col], y=df_daily["conversions"],
                                     name="Dönüşüm", marker_color="#E91E63"), row=2, col=2)

            fig.update_layout(
                height=600,
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E6EDF3",
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Günlük trend verisi yok. Veri Senkronizasyonu'ndan çekin.")

with tab3:
    if display_campaigns:
        df = pd.DataFrame(display_campaigns)
        if all(c in df.columns for c in ["clicks", "conversions", "cost", "name"]):
            df_filtered = df[df["clicks"] > 0].copy()
            if not df_filtered.empty:
                df_filtered["conv_rate"] = (df_filtered["conversions"] / df_filtered["clicks"] * 100)

                fig = px.scatter(df_filtered, x="cost", y="conv_rate",
                                 size="clicks", color="ctr",
                                 hover_name="name",
                                 labels={"cost": "Maliyet (₺)", "conv_rate": "Dönüşüm Oranı (%)",
                                          "clicks": "Tıklama", "ctr": "CTR (%)"},
                                 title="Kampanya Performans Matrisi",
                                 color_continuous_scale="Greens")
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E6EDF3",
                )
                st.plotly_chart(fig, use_container_width=True)

with tab4:
    keywords = st.session_state.get(f"keywords_{customer_id}", [])
    if keywords:
        df_kw = pd.DataFrame(keywords)
        cols = ["keyword", "match_type", "campaign", "impressions", "clicks", "cost",
                "conversions", "quality_score", "ctr", "avg_cpc"]
        available = [c for c in cols if c in df_kw.columns]

        st.markdown(f"**{len(keywords)} anahtar kelime**")

        # Quality Score distribution
        if "quality_score" in df_kw.columns:
            qs_counts = df_kw[df_kw["quality_score"] > 0]["quality_score"].value_counts().sort_index()
            if not qs_counts.empty:
                fig = px.bar(x=qs_counts.index, y=qs_counts.values,
                             labels={"x": "Kalite Puanı", "y": "Adet"},
                             title="Kalite Puanı Dağılımı",
                             color=qs_counts.values,
                             color_continuous_scale=["#E53935", "#FF9800", "#4CAF50"])
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#E6EDF3",
                )
                st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_kw[available], use_container_width=True, hide_index=True)
    else:
        st.info("Anahtar kelime verisi yok. Veri Senkronizasyonu'ndan çekin.")
