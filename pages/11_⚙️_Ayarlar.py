"""⚙️ Ayarlar - API Configuration & OAuth2 Setup"""
import streamlit as st
import os
from config import Config
from database import init_db

init_db()


st.markdown('<div class="section-header">⚙️ Sistem Ayarları</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔑 Google Ads API", "🤖 Claude AI", "🔐 OAuth2 Flow", "ℹ️ Sistem Bilgisi"])

with tab1:
    st.markdown("### 🔑 Google Ads API Yapılandırması")
    st.caption("Bu bilgiler `.env` dosyasında veya Streamlit Cloud Secrets'da saklanmalıdır.")

    with st.form("google_ads_config"):
        dev_token = st.text_input("Developer Token",
                                   value=Config.GOOGLE_ADS_DEVELOPER_TOKEN or "",
                                   type="password",
                                   help="Google Ads API Center'dan alınır")

        client_id = st.text_input("OAuth2 Client ID",
                                   value=Config.GOOGLE_ADS_CLIENT_ID or "",
                                   help="Google Cloud Console'dan alınır")

        client_secret = st.text_input("OAuth2 Client Secret",
                                       value=Config.GOOGLE_ADS_CLIENT_SECRET or "",
                                       type="password",
                                       help="Google Cloud Console'dan alınır")

        refresh_token = st.text_input("Refresh Token",
                                       value=Config.GOOGLE_ADS_REFRESH_TOKEN or "",
                                       type="password",
                                       help="OAuth2 flow ile alınır (aşağıdaki tab)")

        login_customer_id = st.text_input("MCC Login Customer ID",
                                           value=Config.GOOGLE_ADS_LOGIN_CUSTOMER_ID or "",
                                           help="MCC hesap numarası (tire olmadan)")

        if st.form_submit_button("💾 Kaydet", use_container_width=True):
            # Write to .env file
            env_content = f"""GOOGLE_ADS_DEVELOPER_TOKEN={dev_token}
GOOGLE_ADS_CLIENT_ID={client_id}
GOOGLE_ADS_CLIENT_SECRET={client_secret}
GOOGLE_ADS_REFRESH_TOKEN={refresh_token}
GOOGLE_ADS_LOGIN_CUSTOMER_ID={login_customer_id}
ANTHROPIC_API_KEY={Config.ANTHROPIC_API_KEY}
"""
            try:
                with open(".env", "w") as f:
                    f.write(env_content)
                st.success("✅ Ayarlar kaydedildi! Uygulamayı yeniden başlatın.")
                st.info("⚠️ Streamlit Cloud'da çalışıyorsanız, bu bilgileri Secrets bölümünden girmelisiniz.")
            except Exception as e:
                st.error(f"Hata: {e}")

    # Connection Test
    st.divider()
    if st.button("🧪 Bağlantı Testi"):
        try:
            from google_ads_client import get_client, get_accessible_customers
            client = get_client()
            if client:
                accounts = get_accessible_customers()
                st.success(f"✅ Google Ads API bağlantısı başarılı! {len(accounts)} hesap erişilebilir.")
            else:
                st.error("❌ API client oluşturulamadı. Credentials'ları kontrol edin.")
        except Exception as e:
            st.error(f"❌ Bağlantı hatası: {str(e)}")

with tab2:
    st.markdown("### 🤖 Claude AI Yapılandırması")

    with st.form("ai_config"):
        api_key = st.text_input("Anthropic API Key",
                                 value=Config.ANTHROPIC_API_KEY or "",
                                 type="password",
                                 help="console.anthropic.com'dan alınır")

        model = st.selectbox("Model",
                              ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
                              help="Sonnet daha detaylı, Haiku daha hızlı ve ucuz")

        if st.form_submit_button("💾 Kaydet", use_container_width=True):
            try:
                # Update .env
                env_lines = []
                if os.path.exists(".env"):
                    with open(".env", "r") as f:
                        env_lines = f.readlines()

                new_lines = []
                found_key = False
                for line in env_lines:
                    if line.startswith("ANTHROPIC_API_KEY="):
                        new_lines.append(f"ANTHROPIC_API_KEY={api_key}\n")
                        found_key = True
                    else:
                        new_lines.append(line)
                if not found_key:
                    new_lines.append(f"ANTHROPIC_API_KEY={api_key}\n")

                with open(".env", "w") as f:
                    f.writelines(new_lines)
                st.success("✅ AI ayarları kaydedildi!")
            except Exception as e:
                st.error(f"Hata: {e}")

    # AI Test
    if st.button("🧪 AI Bağlantı Testi"):
        try:
            import anthropic
            api = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY or api_key)
            response = api.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": "Merhaba, test mesajı. Kısa yanıt ver."}]
            )
            st.success(f"✅ Claude AI bağlantısı başarılı! Yanıt: {response.content[0].text}")
        except Exception as e:
            st.error(f"❌ AI bağlantı hatası: {str(e)}")

with tab3:
    st.markdown("### 🔐 OAuth2 Refresh Token Alma")
    st.caption("Google Ads API için refresh token almak üzere OAuth2 consent flow'u başlatın.")

    st.markdown("""
    **Adımlar:**
    1. Aşağıdaki butona tıklayın → Authorization URL oluşturulur
    2. URL'yi tarayıcıda açın → Google hesabınızla giriş yapın
    3. İzin verin → Size bir **authorization code** verilir
    4. Bu kodu aşağıdaki alana yapıştırın
    5. Refresh token otomatik oluşturulur
    """)

    if st.button("🔗 OAuth2 URL Oluştur"):
        try:
            from google_ads_client import generate_oauth_url
            if Config.GOOGLE_ADS_CLIENT_ID and Config.GOOGLE_ADS_CLIENT_SECRET:
                auth_url, flow = generate_oauth_url()
                st.session_state["oauth_flow"] = flow
                st.markdown(f"**Authorization URL:**")
                st.code(auth_url)
                st.info("☝️ Bu URL'yi tarayıcıda açın, giriş yapın ve aldığınız kodu aşağıya girin.")
            else:
                st.error("Client ID ve Client Secret önce girilmelidir.")
        except Exception as e:
            st.error(f"Hata: {e}")

    auth_code = st.text_input("Authorization Code", placeholder="4/0AXxxxxxxx...")
    if st.button("🔄 Refresh Token Al") and auth_code:
        flow = st.session_state.get("oauth_flow")
        if flow:
            try:
                from google_ads_client import exchange_code_for_token
                refresh_token = exchange_code_for_token(flow, auth_code)
                st.success(f"✅ Refresh Token alındı!")
                st.code(refresh_token)
                st.warning("⚠️ Bu token'ı yukarıdaki Google Ads API ayarlarına yapıştırın ve kaydedin!")
            except Exception as e:
                st.error(f"Token alma hatası: {e}")
        else:
            st.error("Önce OAuth2 URL oluşturun.")

with tab4:
    st.markdown("### ℹ️ Sistem Bilgisi")

    st.markdown(f"""
    | Bilgi | Değer |
    |---|---|
    | **Uygulama** | {Config.APP_NAME} v{Config.APP_VERSION} |
    | **Google Ads API** | v{Config.GOOGLE_ADS_API_VERSION} |
    | **AI Model** | {Config.ANTHROPIC_MODEL} |
    | **Veritabanı** | SQLite ({Config.DATABASE_PATH}) |
    | **Platform** | Streamlit Cloud |
    """)

    st.divider()

    st.markdown("### 📋 Streamlit Cloud Secrets Formatı")
    st.caption("Streamlit Cloud'da deploy ederken, Settings → Secrets bölümüne aşağıdaki formatı girin:")
    st.code("""
GOOGLE_ADS_DEVELOPER_TOKEN = "your-developer-token"
GOOGLE_ADS_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_ADS_CLIENT_SECRET = "your-client-secret"
GOOGLE_ADS_REFRESH_TOKEN = "your-refresh-token"
GOOGLE_ADS_LOGIN_CUSTOMER_ID = "1234567890"
ANTHROPIC_API_KEY = "sk-ant-xxxxx"
    """, language="toml")
