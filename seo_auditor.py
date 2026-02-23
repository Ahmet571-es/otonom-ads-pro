"""SEO Audit Module - Technical SEO Analysis"""
import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime


class SEOAuditor:
    def __init__(self, url):
        self.url = url if url.startswith("http") else f"https://{url}"
        self.domain = urlparse(self.url).netloc
        self.results = {}

    def full_audit(self):
        """Run complete SEO audit."""
        self.results = {
            "url": self.url,
            "timestamp": datetime.now().isoformat(),
            "meta_analysis": self._analyze_meta(),
            "heading_structure": self._analyze_headings(),
            "image_analysis": self._analyze_images(),
            "link_analysis": self._analyze_links(),
            "content_analysis": self._analyze_content(),
            "technical": self._analyze_technical(),
            "mobile_friendly": self._check_mobile(),
            "schema_markup": self._check_schema(),
            "overall_score": 0,
            "issues": [],
            "recommendations": [],
        }
        self._calculate_score()
        return self.results

    def _fetch_page(self):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; OtonomAdsBot/1.0)"}
            resp = requests.get(self.url, headers=headers, timeout=15, allow_redirects=True)
            return resp
        except Exception as e:
            return None

    def _analyze_meta(self):
        resp = self._fetch_page()
        if not resp:
            return {"error": "Sayfa yüklenemedi"}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {"score": 0, "issues": []}

        # Title
        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else ""
        result["title"] = title
        result["title_length"] = len(title)
        if not title:
            result["issues"].append({"severity": "critical", "message": "Title etiketi eksik!"})
        elif len(title) < 30:
            result["issues"].append({"severity": "warning", "message": f"Title çok kısa ({len(title)} karakter). 50-60 karakter önerilir."})
        elif len(title) > 60:
            result["issues"].append({"severity": "warning", "message": f"Title çok uzun ({len(title)} karakter). 50-60 karakter önerilir."})
        else:
            result["score"] += 15

        # Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
        result["meta_description"] = desc
        result["meta_description_length"] = len(desc)
        if not desc:
            result["issues"].append({"severity": "critical", "message": "Meta description eksik!"})
        elif len(desc) < 120:
            result["issues"].append({"severity": "warning", "message": f"Meta description kısa ({len(desc)} karakter). 150-160 karakter önerilir."})
        elif len(desc) > 160:
            result["issues"].append({"severity": "warning", "message": f"Meta description uzun ({len(desc)} karakter). 150-160 karakter önerilir."})
        else:
            result["score"] += 15

        # Canonical
        canonical = soup.find("link", attrs={"rel": "canonical"})
        result["canonical"] = canonical["href"] if canonical else None
        if not canonical:
            result["issues"].append({"severity": "warning", "message": "Canonical URL tanımlanmamış."})
        else:
            result["score"] += 5

        # Robots
        robots = soup.find("meta", attrs={"name": "robots"})
        result["robots"] = robots["content"] if robots and robots.get("content") else "belirtilmemiş"

        # Open Graph
        og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})
        result["og_tags_count"] = len(og_tags)
        if not og_tags:
            result["issues"].append({"severity": "info", "message": "Open Graph etiketleri eksik (sosyal medya paylaşımları için)."})
        else:
            result["score"] += 5

        # Viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        result["has_viewport"] = bool(viewport)
        if not viewport:
            result["issues"].append({"severity": "critical", "message": "Viewport meta etiketi yok! Mobil uyumluluk sorunu."})
        else:
            result["score"] += 10

        # Language
        html_tag = soup.find("html")
        result["lang"] = html_tag.get("lang", "") if html_tag else ""
        if not result["lang"]:
            result["issues"].append({"severity": "warning", "message": "HTML lang attribute eksik."})

        result["score"] = min(50, result["score"])
        return result

    def _analyze_headings(self):
        resp = self._fetch_page()
        if not resp:
            return {"error": "Sayfa yüklenemedi"}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {"issues": [], "score": 0}

        headings = {}
        for i in range(1, 7):
            tags = soup.find_all(f"h{i}")
            headings[f"h{i}"] = [t.get_text(strip=True)[:80] for t in tags]

        result["headings"] = headings
        result["h1_count"] = len(headings.get("h1", []))

        if result["h1_count"] == 0:
            result["issues"].append({"severity": "critical", "message": "H1 etiketi yok!"})
        elif result["h1_count"] > 1:
            result["issues"].append({"severity": "warning", "message": f"Birden fazla H1 ({result['h1_count']} adet). Tek H1 önerilir."})
        else:
            result["score"] += 15

        if not headings.get("h2"):
            result["issues"].append({"severity": "warning", "message": "H2 etiketi yok. İçerik yapısı iyileştirilmeli."})
        else:
            result["score"] += 10

        return result

    def _analyze_images(self):
        resp = self._fetch_page()
        if not resp:
            return {"error": "Sayfa yüklenemedi"}

        soup = BeautifulSoup(resp.text, "html.parser")
        images = soup.find_all("img")
        result = {"total": len(images), "missing_alt": 0, "issues": [], "score": 0}

        for img in images:
            if not img.get("alt") or not img.get("alt", "").strip():
                result["missing_alt"] += 1

        if result["total"] > 0:
            alt_pct = (result["total"] - result["missing_alt"]) / result["total"] * 100
            result["alt_coverage"] = round(alt_pct, 1)
            if result["missing_alt"] > 0:
                result["issues"].append({
                    "severity": "warning",
                    "message": f"{result['missing_alt']}/{result['total']} görselin alt etiketi eksik."
                })
            if alt_pct > 90:
                result["score"] += 10
        else:
            result["alt_coverage"] = 100
            result["score"] += 10

        return result

    def _analyze_links(self):
        resp = self._fetch_page()
        if not resp:
            return {"error": "Sayfa yüklenemedi"}

        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all("a", href=True)

        internal = []
        external = []
        broken_candidates = []

        for link in links:
            href = link["href"]
            full_url = urljoin(self.url, href)
            parsed = urlparse(full_url)

            if parsed.netloc == self.domain or not parsed.netloc:
                internal.append(full_url)
            else:
                external.append(full_url)

            if not link.get_text(strip=True) and not link.find("img"):
                broken_candidates.append({"url": href, "issue": "Boş anchor text"})

        return {
            "internal_count": len(internal),
            "external_count": len(external),
            "empty_anchors": len(broken_candidates),
            "issues": broken_candidates[:10],
            "score": 10 if len(internal) >= 3 else 5,
        }

    def _analyze_content(self):
        resp = self._fetch_page()
        if not resp:
            return {"error": "Sayfa yüklenemedi"}

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        words = text.split()
        word_count = len(words)

        result = {"word_count": word_count, "issues": [], "score": 0}

        if word_count < 300:
            result["issues"].append({"severity": "warning", "message": f"İçerik çok az ({word_count} kelime). 500+ kelime önerilir."})
        elif word_count >= 500:
            result["score"] += 10

        return result

    def _analyze_technical(self):
        result = {"issues": [], "score": 0}

        try:
            resp = requests.get(self.url, timeout=15, allow_redirects=True)
            result["status_code"] = resp.status_code
            result["response_time"] = round(resp.elapsed.total_seconds(), 2)
            result["content_size_kb"] = round(len(resp.content) / 1024, 1)
            result["redirect_count"] = len(resp.history)
            result["is_https"] = resp.url.startswith("https")

            if resp.elapsed.total_seconds() > 3:
                result["issues"].append({"severity": "critical", "message": f"Sayfa çok yavaş ({resp.elapsed.total_seconds():.1f}s). 3s altı önerilir."})
            elif resp.elapsed.total_seconds() > 1.5:
                result["issues"].append({"severity": "warning", "message": f"Sayfa yavaş ({resp.elapsed.total_seconds():.1f}s). 1.5s altı ideal."})
            else:
                result["score"] += 15

            if not result["is_https"]:
                result["issues"].append({"severity": "critical", "message": "HTTPS kullanılmıyor! Güvenlik sorunu."})
            else:
                result["score"] += 10

            # Check robots.txt
            robots_url = urljoin(self.url, "/robots.txt")
            try:
                rr = requests.get(robots_url, timeout=5)
                result["has_robots_txt"] = rr.status_code == 200
            except:
                result["has_robots_txt"] = False

            # Check sitemap
            sitemap_url = urljoin(self.url, "/sitemap.xml")
            try:
                sr = requests.get(sitemap_url, timeout=5)
                result["has_sitemap"] = sr.status_code == 200
            except:
                result["has_sitemap"] = False

            if not result["has_sitemap"]:
                result["issues"].append({"severity": "warning", "message": "Sitemap.xml bulunamadı."})
            if not result["has_robots_txt"]:
                result["issues"].append({"severity": "warning", "message": "Robots.txt bulunamadı."})

        except Exception as e:
            result["error"] = str(e)

        return result

    def _check_mobile(self):
        resp = self._fetch_page()
        if not resp:
            return {"score": 0, "issues": []}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {"issues": [], "score": 0}

        viewport = soup.find("meta", attrs={"name": "viewport"})
        result["has_viewport"] = bool(viewport)
        if viewport:
            result["score"] += 10

        # Check for fixed width elements
        styles = soup.find_all("style")
        all_css = " ".join(s.string or "" for s in styles)
        if "width:" in all_css and "px" in all_css:
            result["issues"].append({"severity": "info", "message": "Sabit piksel genişlikleri tespit edildi. Responsive tasarım kontrol edin."})

        return result

    def _check_schema(self):
        resp = self._fetch_page()
        if not resp:
            return {"has_schema": False, "types": []}

        soup = BeautifulSoup(resp.text, "html.parser")
        schemas = soup.find_all("script", attrs={"type": "application/ld+json"})

        types = []
        for s in schemas:
            try:
                data = json.loads(s.string)
                if isinstance(data, dict):
                    types.append(data.get("@type", "Unknown"))
                elif isinstance(data, list):
                    for item in data:
                        types.append(item.get("@type", "Unknown"))
            except:
                pass

        return {
            "has_schema": len(types) > 0,
            "types": types,
            "issues": [{"severity": "info", "message": "Schema markup bulunamadı. Yapısal veri eklenmeli."}] if not types else [],
        }

    def _calculate_score(self):
        total = 0
        all_issues = []

        sections = ["meta_analysis", "heading_structure", "image_analysis",
                     "link_analysis", "content_analysis", "technical", "mobile_friendly"]

        for section in sections:
            data = self.results.get(section, {})
            if isinstance(data, dict):
                total += data.get("score", 0)
                all_issues.extend(data.get("issues", []))

        self.results["overall_score"] = min(100, total)
        self.results["issues"] = sorted(all_issues, key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(x.get("severity", "info"), 3))

        # Generate recommendations
        recs = []
        critical_count = sum(1 for i in all_issues if i.get("severity") == "critical")
        warning_count = sum(1 for i in all_issues if i.get("severity") == "warning")

        if critical_count > 0:
            recs.append(f"🔴 {critical_count} kritik sorun hemen düzeltilmeli")
        if warning_count > 0:
            recs.append(f"🟡 {warning_count} uyarı dikkat gerektiriyor")
        if total >= 80:
            recs.append("🟢 Site genel olarak iyi durumda")

        self.results["recommendations"] = recs
