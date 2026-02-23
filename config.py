import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key, default=""):
    """Get secret from Streamlit secrets or environment."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


class Config:
    APP_NAME = "Otonom Ads Pro"
    APP_VERSION = "4.0"
    APP_SUBTITLE = "Premium Google Ads & SEO Otomasyon Platformu"

    # Google Ads API
    GOOGLE_ADS_DEVELOPER_TOKEN = _get_secret("GOOGLE_ADS_DEVELOPER_TOKEN")
    GOOGLE_ADS_CLIENT_ID = _get_secret("GOOGLE_ADS_CLIENT_ID")
    GOOGLE_ADS_CLIENT_SECRET = _get_secret("GOOGLE_ADS_CLIENT_SECRET")
    GOOGLE_ADS_REFRESH_TOKEN = _get_secret("GOOGLE_ADS_REFRESH_TOKEN")
    GOOGLE_ADS_LOGIN_CUSTOMER_ID = _get_secret("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    GOOGLE_ADS_API_VERSION = "v18"

    # Anthropic Claude
    ANTHROPIC_API_KEY = _get_secret("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

    # Database
    DATABASE_PATH = "otonom_ads_pro.db"

    # Automation Thresholds
    BUDGET_OVERSPEND_THRESHOLD = 0.15
    BUDGET_UNDERSPEND_THRESHOLD = 0.25
    BID_MAX_INCREASE = 0.30
    BID_MAX_DECREASE = 0.40
    BID_MIN_CPC = 0.50
    BID_MAX_CPC = 50.0
    ANOMALY_Z_THRESHOLD = 2.5
    CTR_DROP_THRESHOLD = 0.30
    CPA_SPIKE_THRESHOLD = 0.50
    IMPRESSION_DROP_THRESHOLD = 0.40

    # Seasonal Multipliers (Turkey market)
    SEASONAL_MULTIPLIERS = {
        1: 0.90, 2: 0.85, 3: 1.15, 4: 1.10, 5: 1.00,
        6: 0.95, 7: 0.90, 8: 0.90, 9: 1.05, 10: 1.10,
        11: 1.25, 12: 1.30
    }

    OAUTH_SCOPES = ["https://www.googleapis.com/auth/adwords"]
    OAUTH_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
