# 🚀 Otonom Ads Pro v4.0 — Premium Edition

## Premium Google Ads & SEO Otomasyon Platformu

**Powered by Claude AI | Streamlit Cloud Ready**

---

## 🌟 Özellikler

### 📊 Google Ads Yönetimi
- **Otomatik Hesap Oluşturma**: MCC altında yeni Google Ads hesabı oluşturma
- **Kampanya Performansı**: Gerçek zamanlı KPI takibi, trend grafikleri, performans matrisi
- **Veri Senkronizasyonu**: Google Ads API ile otomatik veri çekme

### 🎯 Akıllı Optimizasyon
- **Teklif Optimizasyonu**: CPA/ROAS hedefine göre otomatik bid önerileri
- **Bütçe Yönetimi**: Budget pacing, mevsimsel çarpanlar, yeniden dağılım önerileri
- **Negatif Kelime Madenciliği**: Arama terimi analizi ile otomatik negatif kelime tespiti

### 🧠 Claude AI Entegrasyonu
- **Performans Analizi**: Türkçe detaylı AI performans analizi
- **Strateji Oluşturma**: Kapsamlı kampanya stratejisi, KPI hedefleri, aksiyon planı
- **Reklam Metni Üretimi**: AI ile Google Ads uyumlu Türkçe reklam metinleri
- **SEO Önerileri**: AI destekli SEO iyileştirme tavsiyeleri

### 🚨 Anomali Tespiti
- **İstatistiksel Analiz**: Z-score tabanlı anomali tespiti
- **CTR Düşüşü**: Ani CTR düşüşlerini yakalama
- **Sıfır Dönüşüm**: Dönüşüm izleme sorunlarını tespit
- **Uyarı Merkezi**: Tüm uyarıları merkezi yönetim

### 🔍 SEO Denetimi
- **Meta Analizi**: Title, description, canonical, OG tags
- **İçerik Analizi**: Kelime sayısı, heading yapısı, görsel alt etiketleri
- **Teknik SEO**: Sayfa hızı, HTTPS, robots.txt, sitemap
- **Mobil Uyumluluk**: Viewport, responsive kontrol
- **AI SEO Önerileri**: Claude ile detaylı SEO iyileştirme planı

### 📄 Raporlama
- **PDF Rapor**: Profesyonel performans raporları
- **İşlem Geçmişi**: Tüm aksiyonların kaydı
- **Onay Merkezi**: Otomatik aksiyonları onaylama/reddetme

---

## 🚀 Kurulum

### Streamlit Cloud (Önerilen)

1. Bu repo'yu GitHub'a push edin
2. [share.streamlit.io](https://share.streamlit.io) adresinden deploy edin
3. Settings → Secrets bölümüne credentials girin:

```toml
GOOGLE_ADS_DEVELOPER_TOKEN = "your-token"
GOOGLE_ADS_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_ADS_CLIENT_SECRET = "your-secret"
GOOGLE_ADS_REFRESH_TOKEN = "your-refresh-token"
GOOGLE_ADS_LOGIN_CUSTOMER_ID = "1234567890"
ANTHROPIC_API_KEY = "sk-ant-xxxxx"
```

### Yerel Kurulum

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Dosya Yapısı

```
otonom-ads-pro-premium/
├── app.py                          # Ana dashboard
├── config.py                       # Yapılandırma
├── database.py                     # SQLite veritabanı
├── requirements.txt                # Bağımlılıklar
├── .streamlit/config.toml          # Streamlit tema
├── google_ads/
│   └── __init__.py                 # Google Ads API client
├── automation/
│   └── __init__.py                 # Budget, Bid, NegKW, Anomaly
├── ai/
│   └── __init__.py                 # Claude AI Strategy Engine
├── seo/
│   └── __init__.py                 # SEO Audit Module
├── utils/
│   └── __init__.py                 # PDF Reports, Helpers
└── pages/
    ├── 1_👥_Müşteri_Yönetimi.py
    ├── 2_🔄_Veri_Senkronizasyonu.py
    ├── 3_📈_Kampanya_Performansı.py
    ├── 4_💰_Bütçe_Yönetimi.py
    ├── 5_🎯_Teklif_Optimizasyonu.py
    ├── 6_🚫_Negatif_Kelimeler.py
    ├── 7_🧠_AI_Strateji.py
    ├── 8_🚨_Anomali_Tespiti.py
    ├── 9_🔍_SEO_Denetimi.py
    ├── 10_📄_Raporlama.py
    ├── 11_⚙️_Ayarlar.py
    └── 12_✅_Onay_Merkezi.py
```

---

## 🔑 Gerekli Credentials

| Credential | Nereden Alınır |
|---|---|
| Developer Token | Google Ads API Center |
| OAuth2 Client ID | Google Cloud Console |
| OAuth2 Client Secret | Google Cloud Console |
| Refresh Token | Uygulama içi OAuth2 flow |
| MCC Customer ID | Google Ads Manager Account |
| Anthropic API Key | console.anthropic.com |

---

## 📋 Lisans

Bu yazılım özel lisans altındadır. Tüm hakları saklıdır.

**Otonom Ads Pro v4.0 Premium Edition** — © 2026
