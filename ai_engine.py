"""Claude AI Strategy Engine - Premium Turkish Analysis"""
import json
from datetime import datetime
from config import Config

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def generate_strategy(client_info, campaigns=None, keywords=None, search_terms=None, custom_prompt=""):
    """Generate comprehensive AI strategy for a client."""
    if not HAS_ANTHROPIC or not Config.ANTHROPIC_API_KEY:
        return {"error": "Anthropic API yapılandırılmamış"}

    api = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    # Build context
    context = f"""
## Müşteri Bilgileri
- Firma: {client_info.get('name', 'N/A')}
- Sektör: {client_info.get('sector', 'N/A')}
- Website: {client_info.get('website', 'N/A')}
- Aylık Bütçe: {client_info.get('monthly_budget', 0):,.0f} TL
- Ürünler: {client_info.get('products', 'N/A')}
- Hedef CPA: {client_info.get('target_cpa', 'Belirlenmedi')}
- Hedef ROAS: {client_info.get('target_roas', 'Belirlenmedi')}
"""

    if campaigns:
        context += "\n## Mevcut Kampanya Performansı\n"
        for c in campaigns[:10]:
            context += (f"- {c['name']}: {c.get('impressions',0):,} gösterim, "
                        f"{c.get('clicks',0):,} tık, {c.get('cost',0):,.2f} TL maliyet, "
                        f"{c.get('conversions',0):.0f} dönüşüm, CTR: {c.get('ctr',0):.2f}%, "
                        f"Ort. TBM: {c.get('avg_cpc',0):.2f} TL\n")

    if keywords:
        context += "\n## En Çok Harcama Yapan Anahtar Kelimeler (İlk 20)\n"
        for k in keywords[:20]:
            context += (f"- [{k.get('match_type','?')}] \"{k.get('keyword','')}\" → "
                        f"{k.get('clicks',0)} tık, {k.get('cost',0):.2f} TL, "
                        f"{k.get('conversions',0):.0f} dönüşüm, QS: {k.get('quality_score',0)}\n")

    prompt = f"""Sen premium bir Google Ads optimizasyon uzmanısın. Türkçe yanıt ver.

{context}

{f"Ek Talimatlar: {custom_prompt}" if custom_prompt else ""}

Lütfen aşağıdaki JSON formatında kapsamlı bir strateji oluştur:

{{
    "analysis": "Mevcut durumun detaylı analizi (en az 200 kelime)",
    "recommendations": [
        {{
            "priority": "high/medium/low",
            "category": "bidding/budget/keywords/ads/structure",
            "title": "Öneri başlığı",
            "description": "Detaylı açıklama",
            "expected_impact": "Beklenen etki"
        }}
    ],
    "budget_allocation": [
        {{
            "campaign_name": "Kampanya adı",
            "current_budget": 0,
            "suggested_budget": 0,
            "reason": "Neden"
        }}
    ],
    "kpi_targets": {{
        "target_cpa": 0,
        "target_roas": 0,
        "target_ctr": 0,
        "target_conv_rate": 0
    }},
    "negative_keywords": ["önerilen negatif kelimeler"],
    "new_keyword_suggestions": [
        {{
            "keyword": "kelime",
            "match_type": "PHRASE/EXACT",
            "estimated_cpc": 0,
            "reason": "Neden öneriliyor"
        }}
    ],
    "action_plan": [
        {{
            "week": 1,
            "actions": ["Yapılacak işler"]
        }}
    ]
}}

SADECE JSON döndür, başka bir şey yazma."""

    try:
        response = api.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        strategy = json.loads(text)
        strategy["_meta"] = {
            "model": Config.ANTHROPIC_MODEL,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
            "generated_at": datetime.now().isoformat(),
        }
        return strategy
    except json.JSONDecodeError:
        return {"analysis": text, "recommendations": [], "_meta": {"error": "JSON parse hatası"}}
    except Exception as e:
        return {"error": str(e)}


def analyze_performance(client_info, campaigns, daily_data=None):
    """Quick AI performance analysis in Turkish."""
    if not HAS_ANTHROPIC or not Config.ANTHROPIC_API_KEY:
        return "Anthropic API yapılandırılmamış. Lütfen API anahtarınızı ayarlayın."

    api = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    context = f"Firma: {client_info.get('name')}\nBütçe: {client_info.get('monthly_budget',0):,.0f} TL\n\n"
    context += "Kampanya Performansı:\n"
    for c in campaigns[:10]:
        context += (f"• {c['name']}: {c.get('cost',0):,.2f} TL harcama, "
                    f"{c.get('clicks',0)} tık, {c.get('conversions',0):.0f} dönüşüm, "
                    f"CTR {c.get('ctr',0):.2f}%, CPA {c.get('cpa',0):.2f} TL\n")

    if daily_data:
        context += "\nSon 7 Günlük Trend:\n"
        for d in daily_data[-7:]:
            context += f"• {d['date']}: {d.get('cost',0):.2f} TL, {d.get('clicks',0)} tık, {d.get('conversions',0):.0f} dönüşüm\n"

    try:
        response = api.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": f"""Sen bir Google Ads uzmanısın. Türkçe analiz yap.

{context}

Şunları yap:
1. Genel performans değerlendirmesi (kısa ve öz)
2. En önemli 3 sorun
3. Hemen yapılması gereken 3 aksiyon
4. Bütçe kullanım değerlendirmesi

Profesyonel ama anlaşılır bir dil kullan. Markdown formatında yaz."""}],
        )
        return response.content[0].text
    except Exception as e:
        return f"AI analiz hatası: {str(e)}"


def generate_ad_copy(product_name, product_description, target_audience, language="tr"):
    """Generate ad copy suggestions."""
    if not HAS_ANTHROPIC or not Config.ANTHROPIC_API_KEY:
        return {"error": "API yapılandırılmamış"}

    api = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    try:
        response = api.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": f"""Google Ads için Türkçe reklam metinleri oluştur.

Ürün: {product_name}
Açıklama: {product_description}
Hedef Kitle: {target_audience}

3 farklı reklam varyantı oluştur. Her biri için:
- 3 başlık (max 30 karakter)
- 2 açıklama (max 90 karakter)
- 1 strateji notu

JSON formatında döndür:
[{{"variant": "A", "headlines": [...], "descriptions": [...], "strategy": "..."}}]

SADECE JSON döndür."""}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}


def generate_seo_recommendations(url, audit_data):
    """Generate SEO recommendations based on audit data."""
    if not HAS_ANTHROPIC or not Config.ANTHROPIC_API_KEY:
        return "API yapılandırılmamış"

    api = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    try:
        response = api.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": f"""Sen bir SEO uzmanısın. Türkçe yanıt ver.

Site: {url}
Audit Sonuçları:
{json.dumps(audit_data, indent=2, ensure_ascii=False)}

Şunları yap:
1. Teknik SEO değerlendirmesi
2. İçerik optimizasyon önerileri
3. Sayfa hızı iyileştirme tavsiyeleri
4. Mobil uyumluluk analizi
5. Meta tag optimizasyon önerileri
6. Yapısal veri (Schema) önerileri

Markdown formatında, aksiyon odaklı yaz."""}],
        )
        return response.content[0].text
    except Exception as e:
        return f"SEO analiz hatası: {str(e)}"
