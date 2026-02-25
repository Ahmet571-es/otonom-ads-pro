"""SEO Audit Module - Advanced Professional SEO Analysis Engine"""
import requests
import json
import re
import time
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from collections import Counter


class SEOAuditor:
    def __init__(self, url):
        self.url = url if url.startswith("http") else f"https://{url}"
        self.domain = urlparse(self.url).netloc
        self.results = {}
        self._page_cache = {}
        self._headers = {"User-Agent": "Mozilla/5.0 (compatible; OtonomAdsBot/4.0; +https://otonomreklam.com)"}

    def _fetch_page(self, url=None):
        target = url or self.url
        if target in self._page_cache:
            return self._page_cache[target]
        try:
            resp = requests.get(target, headers=self._headers, timeout=15, allow_redirects=True)
            self._page_cache[target] = resp
            return resp
        except Exception:
            return None

    def _get_soup(self, url=None):
        resp = self._fetch_page(url)
        if resp:
            return BeautifulSoup(resp.text, "html.parser")
        return None

    # ═══════════════════════════════════════════════════════════════
    #  FULL AUDIT
    # ═══════════════════════════════════════════════════════════════
    def full_audit(self):
        """Run complete advanced SEO audit."""
        self.results = {
            "url": self.url,
            "domain": self.domain,
            "timestamp": datetime.now().isoformat(),
            "meta_analysis": self._analyze_meta(),
            "heading_structure": self._analyze_headings(),
            "image_analysis": self._analyze_images(),
            "link_analysis": self._analyze_links(),
            "content_analysis": self._analyze_content(),
            "keyword_analysis": self._analyze_keywords(),
            "technical": self._analyze_technical(),
            "security_headers": self._analyze_security_headers(),
            "page_speed": self._analyze_page_speed(),
            "mobile_friendly": self._check_mobile(),
            "schema_markup": self._check_schema(),
            "social_media": self._check_social_media(),
            "backlink_indicators": self._analyze_backlink_indicators(),
            "featured_snippet": self._check_featured_snippet_readiness(),
            "multi_page": self._crawl_internal_pages(),
            "overall_score": 0,
            "grade": "",
            "issues": [],
            "recommendations": [],
        }
        self._calculate_score()
        return self.results

    # ═══════════════════════════════════════════════════════════════
    #  1. META ANALYSIS (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_meta(self):
        soup = self._get_soup()
        if not soup:
            return {"error": "Sayfa yüklenemedi", "score": 0, "issues": []}

        result = {"score": 0, "issues": [], "details": {}}

        # Title
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else ""
        result["details"]["title"] = title
        result["details"]["title_length"] = len(title)
        if not title:
            result["issues"].append({"severity": "critical", "category": "meta", "message": "Title etiketi eksik!"})
        elif len(title) < 30:
            result["issues"].append({"severity": "warning", "category": "meta", "message": f"Title çok kısa ({len(title)} karakter). 50-60 karakter önerilir."})
        elif len(title) > 60:
            result["issues"].append({"severity": "warning", "category": "meta", "message": f"Title çok uzun ({len(title)} karakter). 50-60 karakter önerilir."})
        else:
            result["score"] += 10

        # Title keyword check
        if title:
            title_words = len(title.split())
            result["details"]["title_word_count"] = title_words
            if title_words < 3:
                result["issues"].append({"severity": "info", "category": "meta", "message": "Title'da daha fazla anahtar kelime kullanılabilir."})

        # Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
        result["details"]["meta_description"] = desc
        result["details"]["meta_description_length"] = len(desc)
        if not desc:
            result["issues"].append({"severity": "critical", "category": "meta", "message": "Meta description eksik!"})
        elif len(desc) < 120:
            result["issues"].append({"severity": "warning", "category": "meta", "message": f"Meta description kısa ({len(desc)} karakter). 150-160 karakter önerilir."})
        elif len(desc) > 160:
            result["issues"].append({"severity": "warning", "category": "meta", "message": f"Meta description uzun ({len(desc)} karakter). 150-160 karakter önerilir."})
        else:
            result["score"] += 10

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        result["details"]["canonical"] = canonical["href"] if canonical else None
        if not canonical:
            result["issues"].append({"severity": "warning", "category": "meta", "message": "Canonical URL tanımlanmamış."})
        else:
            result["score"] += 3

        # Robots
        robots = soup.find("meta", attrs={"name": "robots"})
        result["details"]["robots"] = robots["content"] if robots and robots.get("content") else "belirtilmemiş"
        if robots and "noindex" in (robots.get("content", "") or "").lower():
            result["issues"].append({"severity": "critical", "category": "meta", "message": "Sayfa noindex olarak işaretli! Google'da görünmez."})

        # Open Graph
        og_tags = {}
        for og in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
            og_tags[og.get("property", "")] = og.get("content", "")
        result["details"]["og_tags"] = og_tags
        result["details"]["og_tags_count"] = len(og_tags)
        if not og_tags:
            result["issues"].append({"severity": "warning", "category": "meta", "message": "Open Graph etiketleri eksik (sosyal medya paylaşımları için)."})
        else:
            result["score"] += 3
            if "og:image" not in og_tags:
                result["issues"].append({"severity": "info", "category": "meta", "message": "og:image eksik. Sosyal paylaşımlarda görsel çıkmaz."})

        # Twitter Card
        twitter_tags = {}
        for tw in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")}):
            twitter_tags[tw.get("name", "")] = tw.get("content", "")
        result["details"]["twitter_tags"] = twitter_tags
        if not twitter_tags:
            result["issues"].append({"severity": "info", "category": "meta", "message": "Twitter Card etiketleri eksik."})
        else:
            result["score"] += 2

        # Viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        result["details"]["has_viewport"] = bool(viewport)
        if not viewport:
            result["issues"].append({"severity": "critical", "category": "meta", "message": "Viewport meta etiketi yok! Mobil uyumluluk sorunu."})
        else:
            result["score"] += 5

        # Language
        html_tag = soup.find("html")
        result["details"]["lang"] = html_tag.get("lang", "") if html_tag else ""
        if not result["details"]["lang"]:
            result["issues"].append({"severity": "warning", "category": "meta", "message": "HTML lang attribute eksik."})
        else:
            result["score"] += 2

        # Hreflang (multi-language support)
        hreflangs = soup.find_all("link", attrs={"rel": "alternate", "hreflang": True})
        result["details"]["hreflang_tags"] = [{
            "lang": h.get("hreflang", ""),
            "href": h.get("href", "")
        } for h in hreflangs]
        if hreflangs:
            result["score"] += 3
            result["details"]["is_multilingual"] = True
        else:
            result["details"]["is_multilingual"] = False

        # Favicon
        favicon = soup.find("link", attrs={"rel": re.compile(r"icon", re.I)})
        result["details"]["has_favicon"] = bool(favicon)
        if not favicon:
            result["issues"].append({"severity": "info", "category": "meta", "message": "Favicon bulunamadı."})

        result["score"] = min(38, result["score"])
        return result

    # ═══════════════════════════════════════════════════════════════
    #  2. HEADING STRUCTURE
    # ═══════════════════════════════════════════════════════════════
    def _analyze_headings(self):
        soup = self._get_soup()
        if not soup:
            return {"error": "Sayfa yüklenemedi", "score": 0, "issues": []}

        result = {"issues": [], "score": 0}
        headings = {}
        for i in range(1, 7):
            tags = soup.find_all(f"h{i}")
            headings[f"h{i}"] = [t.get_text(strip=True)[:100] for t in tags]

        result["headings"] = headings
        result["h1_count"] = len(headings.get("h1", []))
        result["total_headings"] = sum(len(v) for v in headings.values())

        if result["h1_count"] == 0:
            result["issues"].append({"severity": "critical", "category": "heading", "message": "H1 etiketi yok!"})
        elif result["h1_count"] > 1:
            result["issues"].append({"severity": "warning", "category": "heading", "message": f"Birden fazla H1 ({result['h1_count']} adet). Tek H1 önerilir."})
        else:
            result["score"] += 8

        if not headings.get("h2"):
            result["issues"].append({"severity": "warning", "category": "heading", "message": "H2 etiketi yok. İçerik yapısı iyileştirilmeli."})
        else:
            result["score"] += 4

        # Heading hierarchy check
        has_skip = False
        for i in range(1, 5):
            if not headings.get(f"h{i}") and headings.get(f"h{i+1}"):
                has_skip = True
                result["issues"].append({"severity": "info", "category": "heading", "message": f"H{i} atlanmış ama H{i+1} kullanılmış. Hiyerarşi bozuk."})
        if not has_skip and result["total_headings"] >= 3:
            result["score"] += 3

        return result

    # ═══════════════════════════════════════════════════════════════
    #  3. IMAGE ANALYSIS (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_images(self):
        soup = self._get_soup()
        if not soup:
            return {"error": "Sayfa yüklenemedi", "score": 0, "issues": []}

        images = soup.find_all("img")
        result = {"total": len(images), "missing_alt": 0, "missing_dimensions": 0,
                  "lazy_loaded": 0, "large_images": [], "issues": [], "score": 0}

        for img in images:
            alt = img.get("alt", "").strip()
            if not alt:
                result["missing_alt"] += 1

            if not img.get("width") and not img.get("height"):
                if not (img.get("style") and ("width" in img.get("style", "") or "height" in img.get("style", ""))):
                    result["missing_dimensions"] += 1

            if img.get("loading") == "lazy" or img.get("data-src"):
                result["lazy_loaded"] += 1

            src = img.get("src", "") or img.get("data-src", "")
            if src and not src.startswith("data:"):
                result["large_images"].append(src)

        if result["total"] > 0:
            alt_pct = (result["total"] - result["missing_alt"]) / result["total"] * 100
            result["alt_coverage"] = round(alt_pct, 1)
            if result["missing_alt"] > 0:
                result["issues"].append({
                    "severity": "warning", "category": "image",
                    "message": f"{result['missing_alt']}/{result['total']} görselin alt etiketi eksik."
                })
            if alt_pct >= 90:
                result["score"] += 5

            if result["missing_dimensions"] > result["total"] * 0.5:
                result["issues"].append({
                    "severity": "info", "category": "image",
                    "message": f"{result['missing_dimensions']} görselde genişlik/yükseklik tanımlı değil. CLS sorununa neden olabilir."
                })

            lazy_pct = result["lazy_loaded"] / result["total"] * 100 if result["total"] > 0 else 0
            result["lazy_load_coverage"] = round(lazy_pct, 1)
            if result["total"] > 5 and lazy_pct < 50:
                result["issues"].append({
                    "severity": "info", "category": "image",
                    "message": f"Görsellerin sadece %{lazy_pct:.0f}'si lazy load kullanıyor. Sayfa hızı için önerilir."
                })
            elif lazy_pct >= 50:
                result["score"] += 3
        else:
            result["alt_coverage"] = 100
            result["score"] += 5

        result["large_images"] = result["large_images"][:5]
        return result

    # ═══════════════════════════════════════════════════════════════
    #  4. LINK ANALYSIS (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_links(self):
        soup = self._get_soup()
        if not soup:
            return {"error": "Sayfa yüklenemedi", "score": 0, "issues": []}

        links = soup.find_all("a", href=True)
        internal = []
        external = []
        external_domains = set()
        nofollow_count = 0
        broken_candidates = []

        for link in links:
            href = link["href"]
            full_url = urljoin(self.url, href)
            parsed = urlparse(full_url)
            rel = (link.get("rel") or [])
            anchor_text = link.get_text(strip=True)

            if "nofollow" in rel:
                nofollow_count += 1

            if parsed.netloc == self.domain or not parsed.netloc:
                internal.append({"url": full_url, "anchor": anchor_text[:60]})
            elif parsed.scheme in ("http", "https"):
                external.append({"url": full_url, "anchor": anchor_text[:60], "domain": parsed.netloc})
                external_domains.add(parsed.netloc)

            if not anchor_text and not link.find("img"):
                broken_candidates.append({"url": href, "issue": "Boş anchor text"})

        # Check for broken links (sample max 10)
        broken_links = []
        sample_links = [l["url"] for l in internal[:10]]
        for link_url in sample_links:
            try:
                r = requests.head(link_url, headers=self._headers, timeout=5, allow_redirects=True)
                if r.status_code >= 400:
                    broken_links.append({"url": link_url, "status": r.status_code})
            except:
                broken_links.append({"url": link_url, "status": "timeout"})

        result = {
            "internal_count": len(internal),
            "external_count": len(external),
            "external_domains": list(external_domains)[:20],
            "external_domain_count": len(external_domains),
            "nofollow_count": nofollow_count,
            "empty_anchors": len(broken_candidates),
            "broken_links": broken_links[:10],
            "broken_link_count": len(broken_links),
            "top_internal": internal[:15],
            "top_external": external[:15],
            "issues": [],
            "score": 0,
        }

        if len(internal) >= 5:
            result["score"] += 4
        elif len(internal) >= 2:
            result["score"] += 2

        if len(external) >= 1:
            result["score"] += 2

        if len(broken_candidates) > 5:
            result["issues"].append({
                "severity": "warning", "category": "link",
                "message": f"{len(broken_candidates)} boş anchor text tespit edildi."
            })

        if broken_links:
            result["issues"].append({
                "severity": "critical", "category": "link",
                "message": f"{len(broken_links)} kırık link tespit edildi!"
            })

        return result

    # ═══════════════════════════════════════════════════════════════
    #  5. CONTENT ANALYSIS (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_content(self):
        soup = self._get_soup()
        if not soup:
            return {"error": "Sayfa yüklenemedi", "score": 0, "issues": []}

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        words = text.split()
        word_count = len(words)

        # Sentence analysis
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

        # Paragraph analysis
        paragraphs = soup.find_all("p")
        para_texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]

        # Readability score (simplified Flesch for Turkish)
        long_words = sum(1 for w in words if len(w) > 8)
        long_word_pct = (long_words / max(1, word_count)) * 100
        readability = max(0, min(100, 100 - (long_word_pct * 2) - (avg_sentence_length * 1.5)))

        # Text-to-HTML ratio
        resp = self._fetch_page()
        html_size = len(resp.text) if resp else 0
        text_size = len(text)
        text_html_ratio = (text_size / max(1, html_size)) * 100

        result = {
            "word_count": word_count,
            "sentence_count": len(sentences),
            "paragraph_count": len(para_texts),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "long_word_percentage": round(long_word_pct, 1),
            "readability_score": round(readability, 1),
            "text_html_ratio": round(text_html_ratio, 1),
            "issues": [],
            "score": 0,
        }

        if word_count < 300:
            result["issues"].append({"severity": "warning", "category": "content", "message": f"İçerik çok az ({word_count} kelime). 500+ kelime önerilir."})
        elif word_count >= 500:
            result["score"] += 5
        if word_count >= 1000:
            result["score"] += 3

        if text_html_ratio < 10:
            result["issues"].append({"severity": "warning", "category": "content", "message": f"Metin/HTML oranı düşük (%{text_html_ratio:.1f}). Daha fazla içerik eklenmelidir."})
        elif text_html_ratio >= 15:
            result["score"] += 2

        if readability < 40:
            result["issues"].append({"severity": "info", "category": "content", "message": f"İçerik okunabilirliği düşük (Skor: {readability:.0f}/100). Daha kısa cümleler önerilir."})
        elif readability >= 60:
            result["score"] += 2

        return result

    # ═══════════════════════════════════════════════════════════════
    #  6. KEYWORD ANALYSIS (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_keywords(self):
        soup = self._get_soup()
        if not soup:
            return {"score": 0, "issues": []}

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True).lower()
        # Turkish stop words
        stop_words = {
            "bir", "ve", "bu", "da", "de", "ile", "için", "olan", "olarak", "en",
            "çok", "daha", "gibi", "ama", "ancak", "hem", "ya", "veya", "ise",
            "her", "ne", "kadar", "sonra", "önce", "üzere", "biz", "siz", "ben",
            "sen", "onun", "bunu", "şu", "var", "yok", "olan", "den", "dan",
            "the", "and", "for", "that", "this", "with", "are", "was", "were",
            "from", "has", "have", "been", "will", "can", "all", "its", "your",
            "not", "but", "they", "you", "more", "some", "about",
        }

        words = re.findall(r'\b[a-zçğıöşü]{3,}\b', text)
        filtered = [w for w in words if w not in stop_words and len(w) >= 3]
        word_count = len(filtered)

        # Single keywords
        single_freq = Counter(filtered)
        top_keywords = single_freq.most_common(20)

        # Two-word phrases
        bigrams = [f"{filtered[i]} {filtered[i+1]}" for i in range(len(filtered)-1)]
        bigram_freq = Counter(bigrams)
        top_bigrams = bigram_freq.most_common(10)

        # Three-word phrases
        trigrams = [f"{filtered[i]} {filtered[i+1]} {filtered[i+2]}" for i in range(len(filtered)-2)]
        trigram_freq = Counter(trigrams)
        top_trigrams = trigram_freq.most_common(5)

        # Keyword in important elements
        title = (soup.find("title") or type("", (), {"text": ""})()).text if soup.find("title") else ""
        meta_desc = ""
        md = soup.find("meta", attrs={"name": "description"})
        if md and md.get("content"):
            meta_desc = md["content"]
        h1_text = " ".join(h.get_text() for h in soup.find_all("h1"))

        # Check if top keywords appear in title, meta, H1
        keyword_placement = []
        for kw, count in top_keywords[:5]:
            placement = {
                "keyword": kw,
                "count": count,
                "density": round((count / max(1, word_count)) * 100, 2),
                "in_title": kw.lower() in title.lower(),
                "in_meta_desc": kw.lower() in meta_desc.lower(),
                "in_h1": kw.lower() in h1_text.lower(),
            }
            keyword_placement.append(placement)

        result = {
            "total_words_analyzed": word_count,
            "top_keywords": [{"keyword": k, "count": c, "density": round((c/max(1, word_count))*100, 2)} for k, c in top_keywords],
            "top_bigrams": [{"phrase": k, "count": c} for k, c in top_bigrams],
            "top_trigrams": [{"phrase": k, "count": c} for k, c in top_trigrams],
            "keyword_placement": keyword_placement,
            "issues": [],
            "score": 0,
        }

        if top_keywords:
            top_kw = top_keywords[0][0]
            top_density = (top_keywords[0][1] / max(1, word_count)) * 100
            if top_density > 5:
                result["issues"].append({"severity": "warning", "category": "keyword", "message": f"'{top_kw}' anahtar kelime yoğunluğu çok yüksek (%{top_density:.1f}). Keyword stuffing riski."})
            elif top_density >= 1:
                result["score"] += 4

            if keyword_placement:
                kp = keyword_placement[0]
                if not kp["in_title"]:
                    result["issues"].append({"severity": "warning", "category": "keyword", "message": f"En çok kullanılan kelime '{top_kw}' title'da geçmiyor."})
                else:
                    result["score"] += 3
                if not kp["in_h1"]:
                    result["issues"].append({"severity": "info", "category": "keyword", "message": f"En çok kullanılan kelime '{top_kw}' H1'de geçmiyor."})

        return result

    # ═══════════════════════════════════════════════════════════════
    #  7. TECHNICAL ANALYSIS (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_technical(self):
        result = {"issues": [], "score": 0, "details": {}}

        try:
            start = time.time()
            resp = requests.get(self.url, headers=self._headers, timeout=15, allow_redirects=True)
            load_time = time.time() - start

            result["details"]["status_code"] = resp.status_code
            result["details"]["response_time"] = round(resp.elapsed.total_seconds(), 2)
            result["details"]["total_load_time"] = round(load_time, 2)
            result["details"]["content_size_kb"] = round(len(resp.content) / 1024, 1)
            result["details"]["redirect_count"] = len(resp.history)
            result["details"]["is_https"] = resp.url.startswith("https")
            result["details"]["final_url"] = resp.url
            result["details"]["encoding"] = resp.encoding

            # Redirects
            if resp.history:
                result["details"]["redirect_chain"] = [r.url for r in resp.history] + [resp.url]
                if len(resp.history) > 2:
                    result["issues"].append({"severity": "warning", "category": "technical", "message": f"{len(resp.history)} yönlendirme var. Fazla yönlendirme hızı etkiler."})

            # Response time
            if load_time > 3:
                result["issues"].append({"severity": "critical", "category": "technical", "message": f"Sayfa çok yavaş ({load_time:.1f}s). 3s altı önerilir."})
            elif load_time > 1.5:
                result["issues"].append({"severity": "warning", "category": "technical", "message": f"Sayfa yavaş ({load_time:.1f}s). 1.5s altı ideal."})
            else:
                result["score"] += 8

            # HTTPS
            if not result["details"]["is_https"]:
                result["issues"].append({"severity": "critical", "category": "technical", "message": "HTTPS kullanılmıyor! Güvenlik sorunu."})
            else:
                result["score"] += 5

            # Page size
            size_kb = result["details"]["content_size_kb"]
            if size_kb > 3000:
                result["issues"].append({"severity": "warning", "category": "technical", "message": f"Sayfa boyutu çok büyük ({size_kb:.0f} KB). 3MB altı önerilir."})
            elif size_kb < 1500:
                result["score"] += 2

            # Compression
            content_encoding = resp.headers.get("Content-Encoding", "")
            result["details"]["compression"] = content_encoding or "Yok"
            if not content_encoding:
                result["issues"].append({"severity": "warning", "category": "technical", "message": "Gzip/Brotli sıkıştırma aktif değil. Sayfa hızını artırır."})
            else:
                result["score"] += 3

            # Caching
            cache_control = resp.headers.get("Cache-Control", "")
            result["details"]["cache_control"] = cache_control or "Yok"
            if not cache_control:
                result["issues"].append({"severity": "info", "category": "technical", "message": "Cache-Control başlığı yok. Önbellekleme performansı artırır."})
            else:
                result["score"] += 2

            # Robots.txt
            try:
                rr = requests.get(urljoin(self.url, "/robots.txt"), headers=self._headers, timeout=5)
                result["details"]["has_robots_txt"] = rr.status_code == 200
                if rr.status_code == 200:
                    result["details"]["robots_txt_content"] = rr.text[:500]
                    result["score"] += 2
            except:
                result["details"]["has_robots_txt"] = False

            # Sitemap
            try:
                sr = requests.get(urljoin(self.url, "/sitemap.xml"), headers=self._headers, timeout=5)
                result["details"]["has_sitemap"] = sr.status_code == 200
                if sr.status_code == 200:
                    result["score"] += 2
                    # Count URLs in sitemap
                    sitemap_soup = BeautifulSoup(sr.text, "html.parser")
                    sitemap_urls = sitemap_soup.find_all("url")
                    result["details"]["sitemap_url_count"] = len(sitemap_urls)
            except:
                result["details"]["has_sitemap"] = False

            if not result["details"].get("has_sitemap"):
                result["issues"].append({"severity": "warning", "category": "technical", "message": "Sitemap.xml bulunamadı."})
            if not result["details"].get("has_robots_txt"):
                result["issues"].append({"severity": "warning", "category": "technical", "message": "Robots.txt bulunamadı."})

        except Exception as e:
            result["details"]["error"] = str(e)

        return result

    # ═══════════════════════════════════════════════════════════════
    #  8. SECURITY HEADERS (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_security_headers(self):
        resp = self._fetch_page()
        if not resp:
            return {"score": 0, "issues": []}

        headers = resp.headers
        result = {"headers": {}, "issues": [], "score": 0}

        security_checks = {
            "Strict-Transport-Security": {"severity": "warning", "message": "HSTS başlığı eksik. HTTPS zorlaması önerilir."},
            "X-Content-Type-Options": {"severity": "info", "message": "X-Content-Type-Options başlığı eksik."},
            "X-Frame-Options": {"severity": "info", "message": "X-Frame-Options başlığı eksik. Clickjacking koruması önerilir."},
            "Content-Security-Policy": {"severity": "info", "message": "Content-Security-Policy başlığı eksik."},
            "X-XSS-Protection": {"severity": "info", "message": "X-XSS-Protection başlığı eksik."},
        }

        found_count = 0
        for header, check in security_checks.items():
            value = headers.get(header, "")
            result["headers"][header] = value or "Eksik"
            if value:
                found_count += 1
            else:
                result["issues"].append({"severity": check["severity"], "category": "security", "message": check["message"]})

        result["score"] = min(5, found_count)
        result["security_grade"] = "A" if found_count >= 4 else "B" if found_count >= 3 else "C" if found_count >= 2 else "D" if found_count >= 1 else "F"

        # Server header (info leak)
        server = headers.get("Server", "")
        if server:
            result["headers"]["Server"] = server
            result["issues"].append({"severity": "info", "category": "security", "message": f"Server başlığı açık: '{server}'. Gizlenmesi önerilir."})

        return result

    # ═══════════════════════════════════════════════════════════════
    #  9. PAGE SPEED ANALYSIS (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_page_speed(self):
        resp = self._fetch_page()
        if not resp:
            return {"score": 0, "issues": []}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {"issues": [], "score": 0, "details": {}}

        # CSS files
        css_files = soup.find_all("link", attrs={"rel": "stylesheet"})
        result["details"]["css_files"] = len(css_files)
        if len(css_files) > 10:
            result["issues"].append({"severity": "warning", "category": "speed", "message": f"{len(css_files)} CSS dosyası yükleniyor. Birleştirme önerilir."})

        # JS files
        js_files = soup.find_all("script", src=True)
        result["details"]["js_files"] = len(js_files)
        if len(js_files) > 15:
            result["issues"].append({"severity": "warning", "category": "speed", "message": f"{len(js_files)} JavaScript dosyası yükleniyor. Birleştirme önerilir."})

        # Render-blocking resources
        blocking_css = [l for l in css_files if not l.get("media") or l.get("media") == "all"]
        blocking_js = [s for s in js_files if not s.get("async") and not s.get("defer")]
        result["details"]["blocking_css"] = len(blocking_css)
        result["details"]["blocking_js"] = len(blocking_js)

        if len(blocking_js) > 5:
            result["issues"].append({"severity": "warning", "category": "speed", "message": f"{len(blocking_js)} render-blocking JS dosyası. async/defer kullanılmalı."})

        # Inline CSS/JS
        inline_styles = soup.find_all("style")
        inline_scripts = soup.find_all("script", src=False)
        inline_scripts = [s for s in inline_scripts if s.string and len(s.string) > 100]
        result["details"]["inline_css_blocks"] = len(inline_styles)
        result["details"]["inline_js_blocks"] = len(inline_scripts)

        # Total resource estimate
        total_resources = len(css_files) + len(js_files) + len(soup.find_all("img"))
        result["details"]["total_resources"] = total_resources
        if total_resources <= 30:
            result["score"] += 3
        elif total_resources <= 60:
            result["score"] += 1

        # Preload/prefetch
        preloads = soup.find_all("link", attrs={"rel": re.compile(r"preload|prefetch|preconnect")})
        result["details"]["preload_hints"] = len(preloads)
        if preloads:
            result["score"] += 2

        return result

    # ═══════════════════════════════════════════════════════════════
    #  10. MOBILE ANALYSIS (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _check_mobile(self):
        soup = self._get_soup()
        if not soup:
            return {"score": 0, "issues": []}

        result = {"issues": [], "score": 0, "details": {}}

        # Viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        result["details"]["has_viewport"] = bool(viewport)
        if viewport:
            result["details"]["viewport_content"] = viewport.get("content", "")
            result["score"] += 3
        else:
            result["issues"].append({"severity": "critical", "category": "mobile", "message": "Viewport meta etiketi yok!"})

        # Touch icons
        touch_icon = soup.find("link", attrs={"rel": re.compile(r"apple-touch-icon")})
        result["details"]["has_touch_icon"] = bool(touch_icon)

        # Media queries in inline CSS
        styles = soup.find_all("style")
        all_css = " ".join(s.string or "" for s in styles)
        has_media_queries = "@media" in all_css
        result["details"]["has_media_queries"] = has_media_queries
        if has_media_queries:
            result["score"] += 2

        # Fixed widths
        fixed_width_pattern = re.compile(r'width\s*:\s*\d{4,}px')
        if fixed_width_pattern.search(all_css):
            result["issues"].append({"severity": "warning", "category": "mobile", "message": "Çok büyük sabit piksel genişlikleri tespit edildi."})

        # AMP check
        amp_link = soup.find("link", attrs={"rel": "amphtml"})
        result["details"]["has_amp"] = bool(amp_link)

        return result

    # ═══════════════════════════════════════════════════════════════
    #  11. SCHEMA MARKUP (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _check_schema(self):
        soup = self._get_soup()
        if not soup:
            return {"has_schema": False, "types": [], "score": 0, "issues": []}

        schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
        parsed_schemas = []

        for s in schemas:
            try:
                data = json.loads(s.string)
                if isinstance(data, dict):
                    parsed_schemas.append(data)
                elif isinstance(data, list):
                    parsed_schemas.extend(data)
            except:
                pass

        types = [s.get("@type", "Unknown") for s in parsed_schemas]

        # Microdata
        microdata = soup.find_all(attrs={"itemtype": True})
        microdata_types = [m.get("itemtype", "").split("/")[-1] for m in microdata]

        result = {
            "has_schema": len(types) > 0 or len(microdata_types) > 0,
            "json_ld_types": types,
            "microdata_types": microdata_types,
            "schema_count": len(parsed_schemas),
            "raw_schemas": parsed_schemas[:5],
            "issues": [],
            "score": 0,
        }

        recommended = ["Organization", "LocalBusiness", "WebSite", "BreadcrumbList", "Product"]
        if types:
            result["score"] += 4
            missing_recommended = [r for r in recommended if r not in types]
            if missing_recommended:
                result["issues"].append({
                    "severity": "info", "category": "schema",
                    "message": f"Önerilen schema tipleri eksik: {', '.join(missing_recommended[:3])}"
                })
        else:
            result["issues"].append({"severity": "warning", "category": "schema", "message": "JSON-LD yapısal veri bulunamadı. Google zengin sonuçlar için eklenmeli."})

        return result

    # ═══════════════════════════════════════════════════════════════
    #  12. SOCIAL MEDIA CHECK (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _check_social_media(self):
        soup = self._get_soup()
        if not soup:
            return {"score": 0, "issues": [], "profiles": {}}

        result = {"profiles": {}, "issues": [], "score": 0}
        page_text = str(soup)

        social_patterns = {
            "facebook": r'facebook\.com/([a-zA-Z0-9._-]+)',
            "instagram": r'instagram\.com/([a-zA-Z0-9._-]+)',
            "twitter": r'(?:twitter|x)\.com/([a-zA-Z0-9_]+)',
            "linkedin": r'linkedin\.com/(?:company|in)/([a-zA-Z0-9_-]+)',
            "youtube": r'youtube\.com/(?:channel|c|@|user)/([a-zA-Z0-9_-]+)',
            "tiktok": r'tiktok\.com/@([a-zA-Z0-9._-]+)',
            "pinterest": r'pinterest\.com/([a-zA-Z0-9_-]+)',
        }

        found_count = 0
        for platform, pattern in social_patterns.items():
            match = re.search(pattern, page_text)
            if match:
                result["profiles"][platform] = match.group(1)
                found_count += 1

        if found_count >= 3:
            result["score"] += 3
        elif found_count >= 1:
            result["score"] += 1

        if found_count == 0:
            result["issues"].append({"severity": "info", "category": "social", "message": "Sosyal medya profil bağlantısı bulunamadı."})

        return result

    # ═══════════════════════════════════════════════════════════════
    #  13. BACKLINK INDICATORS (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _analyze_backlink_indicators(self):
        """Analyze backlink-related indicators from the page itself."""
        soup = self._get_soup()
        if not soup:
            return {"score": 0, "issues": []}

        result = {"indicators": {}, "issues": [], "score": 0}

        # Check for external trust signals
        page_text = str(soup).lower()

        # SSL certificate (already checked in technical)
        result["indicators"]["has_ssl"] = self.url.startswith("https")

        # Domain age indicator (check copyright year)
        copyright_match = re.search(r'©\s*(\d{4})', str(soup))
        if copyright_match:
            year = int(copyright_match.group(1))
            current_year = datetime.now().year
            domain_age_est = current_year - year
            result["indicators"]["estimated_domain_age"] = f"{domain_age_est} yıl+"
            if domain_age_est >= 3:
                result["score"] += 2

        # External links pointing indicators
        result["indicators"]["external_link_count"] = len(soup.find_all("a", href=re.compile(r'^https?://')))

        # Social proof signals
        social_signals = ["facebook", "instagram", "twitter", "linkedin", "youtube"]
        found_social = sum(1 for s in social_signals if s in page_text)
        result["indicators"]["social_presence_count"] = found_social

        # Trust signals
        trust_keywords = ["sertifika", "certificate", "iso", "fssc", "haccp", "halal", "helal", "kalite", "quality", "award", "ödül"]
        found_trust = [kw for kw in trust_keywords if kw in page_text]
        result["indicators"]["trust_signals"] = found_trust
        if len(found_trust) >= 2:
            result["score"] += 2

        # Contact information completeness
        has_phone = bool(re.search(r'[\+]?[\d\s\-\(\)]{10,}', str(soup)))
        has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(soup)))
        has_address = any(kw in page_text for kw in ["adres", "address", "mahalle", "sokak", "cadde"])
        result["indicators"]["has_phone"] = has_phone
        result["indicators"]["has_email"] = has_email
        result["indicators"]["has_address"] = has_address
        if all([has_phone, has_email, has_address]):
            result["score"] += 2

        if not has_phone and not has_email:
            result["issues"].append({"severity": "warning", "category": "backlink", "message": "İletişim bilgileri eksik. Güven sinyali düşük."})

        return result

    # ═══════════════════════════════════════════════════════════════
    #  14. FEATURED SNIPPET READINESS (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _check_featured_snippet_readiness(self):
        soup = self._get_soup()
        if not soup:
            return {"score": 0, "issues": []}

        result = {"readiness": {}, "issues": [], "score": 0}

        # Lists (ol, ul)
        ordered_lists = soup.find_all("ol")
        unordered_lists = soup.find_all("ul")
        result["readiness"]["has_lists"] = len(ordered_lists) + len(unordered_lists) > 0
        result["readiness"]["ordered_lists"] = len(ordered_lists)
        result["readiness"]["unordered_lists"] = len(unordered_lists)

        # Tables
        tables = soup.find_all("table")
        result["readiness"]["has_tables"] = len(tables) > 0
        result["readiness"]["table_count"] = len(tables)

        # FAQ pattern (question-answer structure)
        text = str(soup).lower()
        faq_patterns = ["sıkça sorulan", "faq", "sss", "sorular", "nasıl", "nedir", "neden"]
        faq_found = [p for p in faq_patterns if p in text]
        result["readiness"]["has_faq_content"] = len(faq_found) > 0
        result["readiness"]["faq_signals"] = faq_found

        # Definition/answer patterns (short paragraphs after headings)
        h2_tags = soup.find_all("h2")
        definition_ready = 0
        for h2 in h2_tags:
            next_p = h2.find_next_sibling("p")
            if next_p:
                p_text = next_p.get_text(strip=True)
                if 40 <= len(p_text) <= 300:
                    definition_ready += 1
        result["readiness"]["definition_paragraphs"] = definition_ready

        # Schema FAQ
        schemas = soup.find_all("script", attrs={"type": "application/ld+json"})
        has_faq_schema = False
        for s in schemas:
            try:
                data = json.loads(s.string)
                if isinstance(data, dict) and data.get("@type") == "FAQPage":
                    has_faq_schema = True
            except:
                pass
        result["readiness"]["has_faq_schema"] = has_faq_schema

        # Score
        if result["readiness"]["has_lists"]:
            result["score"] += 1
        if result["readiness"]["has_tables"]:
            result["score"] += 1
        if result["readiness"]["has_faq_content"]:
            result["score"] += 1
        if definition_ready >= 2:
            result["score"] += 1
        if has_faq_schema:
            result["score"] += 2

        if not result["readiness"]["has_lists"] and not result["readiness"]["has_tables"]:
            result["issues"].append({"severity": "info", "category": "snippet", "message": "Listeler veya tablolar yok. Featured snippet şansı artırılabilir."})
        if not result["readiness"]["has_faq_content"]:
            result["issues"].append({"severity": "info", "category": "snippet", "message": "FAQ/SSS içeriği bulunamadı. Soru-cevap formatı snippet için etkili."})

        return result

    # ═══════════════════════════════════════════════════════════════
    #  15. MULTI-PAGE CRAWL (NEW)
    # ═══════════════════════════════════════════════════════════════
    def _crawl_internal_pages(self, max_pages=5):
        """Crawl key internal pages for common issues."""
        soup = self._get_soup()
        if not soup:
            return {"pages_crawled": 0, "issues": [], "score": 0}

        # Find important internal links
        links = soup.find_all("a", href=True)
        internal_urls = set()
        for link in links:
            href = link["href"]
            full_url = urljoin(self.url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == self.domain and full_url != self.url:
                # Skip anchors, images, assets
                if not any(ext in full_url.lower() for ext in [".jpg", ".png", ".gif", ".pdf", ".css", ".js", "#"]):
                    internal_urls.add(full_url)

        pages_to_crawl = list(internal_urls)[:max_pages]
        result = {"pages_crawled": 0, "page_results": [], "common_issues": [], "issues": [], "score": 0}

        pages_missing_title = 0
        pages_missing_desc = 0
        pages_missing_h1 = 0
        pages_slow = 0

        for page_url in pages_to_crawl:
            try:
                start = time.time()
                resp = requests.get(page_url, headers=self._headers, timeout=10)
                load_time = time.time() - start
                page_soup = BeautifulSoup(resp.text, "html.parser")

                title = page_soup.find("title")
                meta_desc = page_soup.find("meta", attrs={"name": "description"})
                h1 = page_soup.find("h1")

                page_info = {
                    "url": page_url,
                    "status": resp.status_code,
                    "load_time": round(load_time, 2),
                    "has_title": bool(title and title.text.strip()),
                    "title": (title.text.strip()[:60] if title else "Yok"),
                    "has_meta_desc": bool(meta_desc and meta_desc.get("content")),
                    "has_h1": bool(h1),
                }
                result["page_results"].append(page_info)
                result["pages_crawled"] += 1

                if not page_info["has_title"]:
                    pages_missing_title += 1
                if not page_info["has_meta_desc"]:
                    pages_missing_desc += 1
                if not page_info["has_h1"]:
                    pages_missing_h1 += 1
                if load_time > 3:
                    pages_slow += 1

            except:
                pass

        if pages_missing_title > 0:
            result["common_issues"].append(f"{pages_missing_title} iç sayfada title eksik")
        if pages_missing_desc > 0:
            result["common_issues"].append(f"{pages_missing_desc} iç sayfada meta description eksik")
        if pages_missing_h1 > 0:
            result["common_issues"].append(f"{pages_missing_h1} iç sayfada H1 eksik")
        if pages_slow > 0:
            result["common_issues"].append(f"{pages_slow} iç sayfa 3 saniyeden yavaş")

        if result["common_issues"]:
            for issue in result["common_issues"]:
                result["issues"].append({"severity": "warning", "category": "multipage", "message": issue})

        if result["pages_crawled"] > 0 and not result["common_issues"]:
            result["score"] += 3

        return result

    # ═══════════════════════════════════════════════════════════════
    #  COMPETITOR COMPARISON
    # ═══════════════════════════════════════════════════════════════
    def compare_with_competitor(self, competitor_url):
        """Quick SEO comparison with a competitor."""
        competitor = SEOAuditor(competitor_url)
        competitor_results = competitor.full_audit()

        comparison = {
            "your_site": self.url,
            "competitor": competitor_url,
            "your_score": self.results.get("overall_score", 0),
            "competitor_score": competitor_results.get("overall_score", 0),
            "comparison": {},
        }

        # Compare key metrics
        metrics = {
            "SEO Puanı": (self.results.get("overall_score", 0), competitor_results.get("overall_score", 0)),
            "Kelime Sayısı": (
                self.results.get("content_analysis", {}).get("word_count", 0),
                competitor_results.get("content_analysis", {}).get("word_count", 0),
            ),
            "İç Link": (
                self.results.get("link_analysis", {}).get("internal_count", 0),
                competitor_results.get("link_analysis", {}).get("internal_count", 0),
            ),
            "Dış Link": (
                self.results.get("link_analysis", {}).get("external_count", 0),
                competitor_results.get("link_analysis", {}).get("external_count", 0),
            ),
            "Yanıt Süresi": (
                self.results.get("technical", {}).get("details", {}).get("response_time", 0),
                competitor_results.get("technical", {}).get("details", {}).get("response_time", 0),
            ),
            "Görsel Sayısı": (
                self.results.get("image_analysis", {}).get("total", 0),
                competitor_results.get("image_analysis", {}).get("total", 0),
            ),
            "Schema Tipi": (
                len(self.results.get("schema_markup", {}).get("json_ld_types", [])),
                len(competitor_results.get("schema_markup", {}).get("json_ld_types", [])),
            ),
            "Kritik Sorun": (
                sum(1 for i in self.results.get("issues", []) if i.get("severity") == "critical"),
                sum(1 for i in competitor_results.get("issues", []) if i.get("severity") == "critical"),
            ),
        }

        for metric, (yours, theirs) in metrics.items():
            if metric in ("Yanıt Süresi", "Kritik Sorun"):
                winner = "Siz" if yours <= theirs else "Rakip"
            else:
                winner = "Siz" if yours >= theirs else "Rakip"
            comparison["comparison"][metric] = {
                "yours": yours,
                "competitor": theirs,
                "winner": winner,
            }

        return comparison

    # ═══════════════════════════════════════════════════════════════
    #  SCORE CALCULATION (Enhanced)
    # ═══════════════════════════════════════════════════════════════
    def _calculate_score(self):
        total = 0
        all_issues = []

        sections = [
            "meta_analysis", "heading_structure", "image_analysis",
            "link_analysis", "content_analysis", "keyword_analysis",
            "technical", "security_headers", "page_speed",
            "mobile_friendly", "schema_markup", "social_media",
            "backlink_indicators", "featured_snippet", "multi_page",
        ]

        section_scores = {}
        for section in sections:
            data = self.results.get(section, {})
            if isinstance(data, dict):
                score = data.get("score", 0)
                total += score
                section_scores[section] = score
                all_issues.extend(data.get("issues", []))

        self.results["section_scores"] = section_scores
        self.results["overall_score"] = min(100, total)

        # Grade
        score = self.results["overall_score"]
        if score >= 90:
            self.results["grade"] = "A+"
        elif score >= 80:
            self.results["grade"] = "A"
        elif score >= 70:
            self.results["grade"] = "B"
        elif score >= 60:
            self.results["grade"] = "C"
        elif score >= 40:
            self.results["grade"] = "D"
        else:
            self.results["grade"] = "F"

        self.results["issues"] = sorted(
            all_issues,
            key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x.get("severity", "info"), 3)
        )

        # Generate smart recommendations
        recs = []
        critical_count = sum(1 for i in all_issues if i.get("severity") == "critical")
        warning_count = sum(1 for i in all_issues if i.get("severity") == "warning")
        info_count = sum(1 for i in all_issues if i.get("severity") == "info")

        if critical_count > 0:
            recs.append(f"🔴 {critical_count} kritik sorun hemen düzeltilmeli")
        if warning_count > 0:
            recs.append(f"🟡 {warning_count} uyarı dikkat gerektiriyor")
        if info_count > 0:
            recs.append(f"🔵 {info_count} iyileştirme önerisi mevcut")
        if score >= 80:
            recs.append("🟢 Site genel olarak iyi durumda")
        elif score >= 60:
            recs.append("🟠 Site ortalamanın üstünde ama iyileştirme alanları var")
        else:
            recs.append("🔴 Site ciddi SEO iyileştirmelerine ihtiyaç duyuyor")

        self.results["recommendations"] = recs
        self.results["summary"] = {
            "total_issues": len(all_issues),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
        }
