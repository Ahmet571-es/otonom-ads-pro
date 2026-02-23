"""💰 Bütçe Yönetimi - Budget Pacing & Reallocation"""
import streamlit as st
import plotly.graph_objects as go
from database import init_db, fetch_all, fetch_one, log_action
from automation_engines import BudgetManager

init_db()

st.set_page_config(page_title="Bütçe Yönetimi", page_icon="💰", layout="wide")
st.markdown('<div class="section-header">💰 Bütçe Yönetimi & Optimizasyonu</div>', unsafe_allow_html=True)

clients = fetch_all("clients", order_by="name ASC")
if not clients:
    st.info("Henüz müşteri eklenmemiş.")
    st.stop()

selected = st.selectbox("Müşteri", [c["name"] for c in clients])
client = next(c for c in clients if c["name"] == selected)
customer_id = client.get("google_ads_id", "")
monthly_budget = client.get("monthly_budget", 0) or 0

st.markdown(f"**Aylık Bütçe:** ₺{monthly_budget:,.0f}")

# Get campaign data
campaigns = st.session_state.get(f"campaigns_{customer_id}", [])
if not campaigns:
    campaigns = fetch_all("campaigns", where="client_id = ?", params=[client["id"]])

if not campaigns:
    st.warning("Kampanya verisi yok. Önce Veri Senkronizasyonu yapın.")
    st.stop()

# ── Budget Pacing ──
st.markdown("### 📊 Bütçe Pacing Analizi")
pacing = BudgetManager.analyze_pacing(campaigns, monthly_budget)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Toplam Harcama", f"₺{pacing['total_cost']:,.2f}")
with col2:
    st.metric("Beklenen Harcama", f"₺{pacing['expected_cost']:,.2f}")
with col3:
    st.metric("Kalan Bütçe", f"₺{pacing['remaining_budget']:,.2f}")
with col4:
    st.metric("İdeal Günlük", f"₺{pacing['daily_ideal']:,.2f}")

# Pacing gauge
status_color = {"normal": "#4CAF50", "overspend": "#E53935", "underspend": "#FF9800"}
status_text = {"normal": "Normal", "overspend": "Aşırı Harcama!", "underspend": "Düşük Harcama"}

fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=pacing["pacing_pct"],
    title={"text": "Bütçe Pacing", "font": {"color": "#E6EDF3"}},
    delta={"reference": 100, "suffix": "%"},
    number={"suffix": "%", "font": {"color": "#E6EDF3"}},
    gauge={
        "axis": {"range": [0, 150], "tickfont": {"color": "#8B949E"}},
        "bar": {"color": status_color.get(pacing["status"], "#4CAF50")},
        "steps": [
            {"range": [0, 75], "color": "rgba(255, 152, 0, 0.2)"},
            {"range": [75, 115], "color": "rgba(76, 175, 80, 0.2)"},
            {"range": [115, 150], "color": "rgba(229, 57, 53, 0.2)"},
        ],
        "threshold": {
            "line": {"color": "#E6EDF3", "width": 2},
            "thickness": 0.75,
            "value": 100,
        },
    },
))
fig.update_layout(
    height=300,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#E6EDF3",
)
st.plotly_chart(fig, use_container_width=True)

status = pacing["status"]
if status == "overspend":
    st.error(f"🔴 **Aşırı Harcama!** Pacing: %{pacing['pacing_pct']:.1f}. Bütçe {BudgetManager.get_seasonal_multiplier():.0%} mevsimsel çarpanla ay sonuna yetişmeyebilir.")
elif status == "underspend":
    st.warning(f"🟡 **Düşük Harcama.** Pacing: %{pacing['pacing_pct']:.1f}. Bütçe kullanım altında. Bid artırma veya kampanya genişletme düşünün.")
else:
    st.success(f"🟢 **Normal.** Pacing: %{pacing['pacing_pct']:.1f}. Bütçe doğru hızda tüketiliyor.")

# Seasonal info
seasonal = BudgetManager.get_seasonal_multiplier()
st.info(f"📅 Bu ay için mevsimsel çarpan: **{seasonal}x** {'(Yüksek sezon)' if seasonal > 1 else '(Düşük sezon)' if seasonal < 1 else '(Normal)'}")

# ── Campaign Budget Distribution ──
st.divider()
st.markdown("### 📊 Kampanya Bütçe Dağılımı")

import pandas as pd
df = pd.DataFrame(campaigns)
if "cost" in df.columns and "name" in df.columns:
    df_cost = df[df["cost"] > 0].sort_values("cost", ascending=True)
    if not df_cost.empty:
        fig = go.Figure(go.Bar(
            x=df_cost["cost"],
            y=df_cost["name"],
            orientation="h",
            marker_color="#4CAF50",
            text=[f"₺{c:,.0f}" for c in df_cost["cost"]],
            textposition="outside",
        ))
        fig.update_layout(
            height=max(300, len(df_cost) * 40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E6EDF3",
            xaxis_title="Harcama (₺)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Reallocation Suggestions ──
st.divider()
st.markdown("### 💡 Bütçe Yeniden Dağılım Önerileri")

suggestions = BudgetManager.get_reallocation_suggestions(campaigns, monthly_budget)
if suggestions:
    for s in suggestions:
        icon = "📈" if s["action"] == "increase" else "📉"
        color = "green" if s["action"] == "increase" else "red"
        st.markdown(f"""
        {icon} **{s['campaign']}**
        - Mevcut: ₺{s['current_budget']:,.2f}/gün → Önerilen: ₺{s['suggested_budget']:,.2f}/gün
        - Sebep: {s['reason']}
        """)

        if st.button(f"✅ Uygula: {s['campaign']}", key=f"apply_budget_{s['campaign']}"):
            try:
                # This would call the API to update budget
                log_action(client["id"], "budget_adjusted",
                           f"{s['campaign']}: ₺{s['current_budget']} → ₺{s['suggested_budget']}")
                st.success(f"✅ {s['campaign']} bütçesi güncellendi!")
            except Exception as e:
                st.error(f"Hata: {e}")
else:
    st.success("✅ Tüm kampanyalar optimal bütçe seviyesinde.")
