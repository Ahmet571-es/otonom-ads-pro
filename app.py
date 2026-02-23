"""
╔══════════════════════════════════════════════════════╗
║         OTONOM ADS PRO v4.0 — PREMIUM               ║
║    Google Ads & SEO Otomasyon Platformu              ║
║         Powered by Claude AI                         ║
╚══════════════════════════════════════════════════════╝
"""
import streamlit as st
import json
from datetime import datetime
from config import Config
from database import init_db, fetch_all, fetch_one, count

# ── Initialize ──
init_db()

# ── Page Config ──
st.set_page_config(
    page_title=f"{Config.APP_NAME} v{Config.APP_VERSION}",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium CSS ──
st.markdown("""
<style>
    /* Main app */
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #1A1F2E 100%);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0D1117 0%, #161B22 100%);
        border-right: 1px solid #21262D;
    }

    /* Logo area */
    .logo-container {
        text-align: center;
        padding: 20px 0;
        border-bottom: 1px solid #21262D;
        margin-bottom: 20px;
    }
    .logo-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #4CAF50, #81C784, #A5D6A7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 2px;
    }
    .logo-subtitle {
        font-size: 11px;
        color: #8B949E;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: 4px;
    }
    .logo-version {
        display: inline-block;
        background: linear-gradient(135deg, #1B5E20, #2E7D32);
        color: #A5D6A7;
        font-size: 10px;
        padding: 2px 10px;
        border-radius: 12px;
        margin-top: 8px;
        letter-spacing: 1px;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #161B22 0%, #1A1F2E 100%);
        border: 1px solid #21262D;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .kpi-card:hover {
        border-color: #4CAF50;
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.1);
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #E6EDF3;
    }
    .kpi-label {
        font-size: 12px;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }
    .kpi-delta-up { color: #4CAF50; font-size: 12px; }
    .kpi-delta-down { color: #E53935; font-size: 12px; }

    /* Status badges */
    .badge-active {
        background: #1B5E20; color: #A5D6A7;
        padding: 3px 12px; border-radius: 12px; font-size: 11px;
    }
    .badge-warning {
        background: #E65100; color: #FFE0B2;
        padding: 3px 12px; border-radius: 12px; font-size: 11px;
    }
    .badge-error {
        background: #B71C1C; color: #FFCDD2;
        padding: 3px 12px; border-radius: 12px; font-size: 11px;
    }

    /* Section headers */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #E6EDF3;
        padding: 12px 0 8px 0;
        border-bottom: 2px solid #4CAF50;
        margin-bottom: 16px;
    }

    /* Custom metric cards */
    .metric-row {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }

    /* Alert cards */
    .alert-critical {
        background: linear-gradient(135deg, #1A0000, #2D0000);
        border-left: 4px solid #E53935;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .alert-warning {
        background: linear-gradient(135deg, #1A1200, #2D1E00);
        border-left: 4px solid #FF9800;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .alert-success {
        background: linear-gradient(135deg, #001A00, #002D00);
        border-left: 4px solid #4CAF50;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #161B22;
        border-radius: 8px 8px 0 0;
        border: 1px solid #21262D;
        color: #8B949E;
    }
    .stTabs [aria-selected="true"] {
        background: #1A1F2E;
        border-color: #4CAF50;
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-title">OTONOM ADS PRO</div>
        <div class="logo-subtitle">Premium Otomasyon</div>
        <div class="logo-version">v4.0 PREMIUM</div>
    </div>
    """, unsafe_allow_html=True)

    # Connection status
    api_configured = all([Config.GOOGLE_ADS_DEVELOPER_TOKEN, Config.GOOGLE_ADS_CLIENT_ID,
                          Config.GOOGLE_ADS_CLIENT_SECRET, Config.GOOGLE_ADS_REFRESH_TOKEN])
    ai_configured = bool(Config.ANTHROPIC_API_KEY)

    st.markdown("##### 🔌 Bağlantı Durumu")
    if api_configured:
        st.markdown('<span class="badge-active">● Google Ads API Bağlı</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-error">● Google Ads API Bağlantısız</span>', unsafe_allow_html=True)

    if ai_configured:
        st.markdown('<span class="badge-active">● Claude AI Aktif</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-warning">● Claude AI Yapılandırılmamış</span>', unsafe_allow_html=True)

    st.divider()

    # Client selector
    clients = fetch_all("clients", order_by="name ASC")
    if clients:
        client_names = ["Tüm Müşteriler"] + [c["name"] for c in clients]
        selected = st.selectbox("👤 Müşteri Seçin", client_names)
        if selected != "Tüm Müşteriler":
            st.session_state["selected_client"] = next(c for c in clients if c["name"] == selected)
        else:
            st.session_state.pop("selected_client", None)
    else:
        st.info("Henüz müşteri eklenmemiş. Müşteri Yönetimi sayfasından ekleyin.")

    st.divider()

    # Quick stats
    st.markdown("##### 📊 Platform İstatistikleri")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Müşteri", count("clients"))
        st.metric("Alert", count("alerts", "is_resolved = 0"))
    with col2:
        st.metric("Kampanya", count("campaigns"))
        st.metric("İşlem", count("action_logs"))

    st.divider()
    st.markdown(f"<p style='text-align:center;color:#8B949E;font-size:10px;'>Otonom Ads Pro v{Config.APP_VERSION}<br/>© 2026 Premium Edition</p>", unsafe_allow_html=True)

# ── Main Dashboard ──
st.markdown('<div class="section-header">📊 Ana Dashboard</div>', unsafe_allow_html=True)

# Check configuration
if not api_configured:
    st.warning("⚠️ Google Ads API henüz yapılandırılmamış. Ayarlar sayfasından credentials'larınızı girin.")

    with st.expander("🚀 Hızlı Başlangıç Kılavuzu", expanded=True):
        st.markdown("""
        ### Otonom Ads Pro v4.0'ı kurmak için:

        **Adım 1:** Sol menüden **⚙️ Ayarlar** sayfasına gidin

        **Adım 2:** Google Ads API bilgilerinizi girin:
        - Developer Token
        - OAuth2 Client ID
        - OAuth2 Client Secret
        - Refresh Token (OAuth2 flow ile alınır)
        - MCC Login Customer ID

        **Adım 3:** Anthropic API Key'inizi girin (Claude AI için)

        **Adım 4:** **👥 Müşteri Yönetimi** sayfasından ilk müşterinizi ekleyin

        **Adım 5:** Dashboard'a dönün ve verilerinizi görün!

        ---
        **İhtiyacınız olanlar:**
        - Google Ads MCC hesabı ✅
        - Developer Token (Google Ads API Center'dan)
        - OAuth2 credentials (Google Cloud Console'dan)
        - Anthropic API Key (console.anthropic.com'dan)
        """)

else:
    # Show dashboard with data
    selected_client = st.session_state.get("selected_client")

    if selected_client:
        st.markdown(f"### 🏢 {selected_client['name']}")

        # KPI Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-value">—</div>
                <div class="kpi-label">Gösterim</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-value">—</div>
                <div class="kpi-label">Tıklama</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-value">—</div>
                <div class="kpi-label">Maliyet</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-value">—</div>
                <div class="kpi-label">Dönüşüm</div>
            </div>
            """, unsafe_allow_html=True)
        with col5:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-value">—</div>
                <div class="kpi-label">ROAS</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("📡 Veri çekmek için üst menüden '🔄 Veri Senkronizasyonu' sayfasını kullanın.")
    else:
        # Overview for all clients
        if clients:
            st.markdown("### 📋 Müşteri Özeti")
            for c in clients:
                with st.container():
                    cols = st.columns([3, 2, 2, 1])
                    with cols[0]:
                        st.markdown(f"**{c['name']}** — {c.get('sector', 'N/A')}")
                    with cols[1]:
                        st.markdown(f"Bütçe: {c.get('monthly_budget', 0):,.0f} ₺")
                    with cols[2]:
                        st.markdown(f"Ads ID: {c.get('google_ads_id', 'Yok')}")
                    with cols[3]:
                        status = c.get("google_ads_status", "pending")
                        badge = "badge-active" if status == "active" else "badge-warning"
                        st.markdown(f'<span class="{badge}">{status}</span>', unsafe_allow_html=True)
                    st.divider()
        else:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px;">
                <h2 style="color:#4CAF50;">🚀 Otonom Ads Pro v4.0'a Hoş Geldiniz!</h2>
                <p style="color:#8B949E; font-size:16px;">Premium Google Ads & SEO Otomasyon Platformu</p>
                <br/>
                <p style="color:#E6EDF3;">Başlamak için sol menüden <b>👥 Müşteri Yönetimi</b> sayfasına gidin.</p>
            </div>
            """, unsafe_allow_html=True)

# Recent activity log
recent_logs = fetch_all("action_logs", limit=5)
if recent_logs:
    st.markdown('<div class="section-header">📋 Son İşlemler</div>', unsafe_allow_html=True)
    for log in recent_logs:
        severity = log.get("severity", "info")
        icon = {"info": "🔵", "warning": "🟡", "error": "🔴", "success": "🟢"}.get(severity, "⚪")
        st.markdown(f"{icon} **{log.get('action_type', '')}** — {log.get('description', '')} "
                    f"<small style='color:#8B949E;'>({log.get('created_at', '')})</small>",
                    unsafe_allow_html=True)

# Active alerts
active_alerts = fetch_all("alerts", where="is_resolved = 0", limit=5)
if active_alerts:
    st.markdown('<div class="section-header">🚨 Aktif Uyarılar</div>', unsafe_allow_html=True)
    for alert in active_alerts:
        sev = alert.get("severity", "warning")
        css_class = f"alert-{sev}" if sev in ["critical", "warning"] else "alert-warning"
        st.markdown(f"""
        <div class="{css_class}">
            <strong>{alert.get('title', '')}</strong><br/>
            <small>{alert.get('message', '')}</small>
        </div>
        """, unsafe_allow_html=True)
