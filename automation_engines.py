"""Automation Engines - Budget, Bid, Negative Keyword, Anomaly Detection"""
import json
from datetime import datetime
from config import Config
from database import log_action, create_alert, insert, fetch_all


# ═══════════════════════════════════════════════════════
# BUDGET MANAGER
# ═══════════════════════════════════════════════════════

class BudgetManager:
    @staticmethod
    def analyze_pacing(campaigns, monthly_budget):
        """Analyze budget pacing for all campaigns."""
        today = datetime.now()
        day_of_month = today.day
        days_in_month = 30
        expected_spend_pct = day_of_month / days_in_month

        total_cost = sum(c.get("cost", 0) for c in campaigns)
        expected_cost = monthly_budget * expected_spend_pct
        pacing_pct = (total_cost / expected_cost * 100) if expected_cost > 0 else 0

        status = "normal"
        if pacing_pct > (1 + Config.BUDGET_OVERSPEND_THRESHOLD) * 100:
            status = "overspend"
        elif pacing_pct < (1 - Config.BUDGET_UNDERSPEND_THRESHOLD) * 100 and day_of_month > 14:
            status = "underspend"

        return {
            "total_cost": round(total_cost, 2),
            "expected_cost": round(expected_cost, 2),
            "pacing_pct": round(pacing_pct, 1),
            "remaining_budget": round(monthly_budget - total_cost, 2),
            "daily_ideal": round((monthly_budget - total_cost) / max(1, days_in_month - day_of_month), 2),
            "status": status,
            "day_of_month": day_of_month,
        }

    @staticmethod
    def get_reallocation_suggestions(campaigns, monthly_budget):
        """Suggest budget reallocation based on campaign performance."""
        suggestions = []
        if not campaigns:
            return suggestions

        for c in campaigns:
            score = BudgetManager._performance_score(c)
            current_budget = c.get("daily_budget", 0)

            if score > 0.5 and c.get("impression_share", 0) < 80:
                new_budget = round(current_budget * 1.2, 2)
                suggestions.append({
                    "campaign": c["name"],
                    "action": "increase",
                    "current_budget": current_budget,
                    "suggested_budget": new_budget,
                    "reason": f"Yüksek performans (skor: {score:.1f}), düşük IS ({c.get('impression_share', 0)}%)",
                    "score": score,
                })
            elif score < -0.3:
                new_budget = round(current_budget * 0.8, 2)
                suggestions.append({
                    "campaign": c["name"],
                    "action": "decrease",
                    "current_budget": current_budget,
                    "suggested_budget": new_budget,
                    "reason": f"Düşük performans (skor: {score:.1f})",
                    "score": score,
                })

        return sorted(suggestions, key=lambda x: abs(x["score"]), reverse=True)

    @staticmethod
    def _performance_score(campaign):
        cpa = campaign.get("cpa", 0)
        target_cpa = campaign.get("target_cpa", 0)
        conversions = campaign.get("conversions", 0)

        score = 0.0
        if target_cpa and cpa:
            ratio = cpa / target_cpa
            if ratio < 0.7:
                score += 1.0
            elif ratio < 1.0:
                score += 0.5
            elif ratio > 1.5:
                score -= 1.0
            elif ratio > 1.2:
                score -= 0.5

        if conversions > 10:
            score += 0.3
        elif conversions == 0:
            score -= 0.5

        return max(-1, min(1, score))

    @staticmethod
    def get_seasonal_multiplier():
        month = datetime.now().month
        return Config.SEASONAL_MULTIPLIERS.get(month, 1.0)


# ═══════════════════════════════════════════════════════
# BID OPTIMIZER
# ═══════════════════════════════════════════════════════

class BidOptimizer:
    @staticmethod
    def analyze_keywords(keywords, target_cpa=None, target_roas=None):
        """Analyze keywords and suggest bid adjustments."""
        suggestions = []

        for kw in keywords:
            cost = kw.get("cost", 0)
            conversions = kw.get("conversions", 0)
            clicks = kw.get("clicks", 0)
            current_cpc = kw.get("avg_cpc", 0)
            quality_score = kw.get("quality_score", 0)

            if clicks < 5:
                continue

            action = None
            reason = ""
            adjustment = 0

            kw_cpa = cost / conversions if conversions > 0 else float("inf")

            if target_cpa:
                if kw_cpa > target_cpa * 1.3 and conversions > 0:
                    adjustment = -min(Config.BID_MAX_DECREASE, (kw_cpa - target_cpa) / target_cpa * 0.5)
                    action = "decrease"
                    reason = f"CPA ({kw_cpa:.2f}) hedefin %30+ üstünde ({target_cpa:.2f})"
                elif kw_cpa < target_cpa * 0.7 and conversions >= 3:
                    adjustment = min(Config.BID_MAX_INCREASE, (target_cpa - kw_cpa) / target_cpa * 0.3)
                    action = "increase"
                    reason = f"CPA ({kw_cpa:.2f}) hedefin altında, fırsat var"
                elif conversions == 0 and cost > 20:
                    adjustment = -0.35
                    action = "decrease"
                    reason = f"Sıfır dönüşüm, {cost:.2f} TL harcama"

            if quality_score and quality_score < 4:
                reason += f" | Düşük QS: {quality_score}/10"

            if action:
                new_cpc = max(Config.BID_MIN_CPC, min(Config.BID_MAX_CPC,
                              current_cpc * (1 + adjustment)))
                suggestions.append({
                    "keyword": kw.get("keyword", ""),
                    "campaign": kw.get("campaign", ""),
                    "ad_group": kw.get("ad_group", ""),
                    "current_cpc": round(current_cpc, 2),
                    "suggested_cpc": round(new_cpc, 2),
                    "adjustment_pct": round(adjustment * 100, 1),
                    "action": action,
                    "reason": reason,
                    "conversions": conversions,
                    "cost": cost,
                    "quality_score": quality_score,
                })

        return sorted(suggestions, key=lambda x: abs(x["adjustment_pct"]), reverse=True)


# ═══════════════════════════════════════════════════════
# NEGATIVE KEYWORD MINER
# ═══════════════════════════════════════════════════════

class NegativeKeywordMiner:
    @staticmethod
    def analyze_search_terms(search_terms, target_cpa=None):
        """Analyze search terms and find negative keyword candidates."""
        candidates = []

        for st in search_terms:
            cost = st.get("cost", 0)
            clicks = st.get("clicks", 0)
            conversions = st.get("conversions", 0)
            impressions = st.get("impressions", 0)
            ctr = st.get("ctr", 0)

            reasons = []

            # High cost, zero conversions
            if cost >= 10 and conversions == 0:
                reasons.append(f"Yüksek maliyet ({cost:.2f} TL), sıfır dönüşüm")

            # Many clicks, zero conversions
            if clicks >= 10 and conversions == 0:
                reasons.append(f"Çok tıklama ({clicks}), sıfır dönüşüm")

            # Very low CTR with impressions
            if impressions >= 100 and ctr < 1.0:
                reasons.append(f"Çok düşük CTR ({ctr:.1f}%), {impressions} gösterim")

            # Extreme CPA
            if target_cpa and conversions > 0:
                st_cpa = cost / conversions
                if st_cpa > target_cpa * 3:
                    reasons.append(f"Aşırı CPA ({st_cpa:.2f}), hedefin 3 katı")

            if reasons:
                term = st.get("search_term", "")
                word_count = len(term.split())
                candidates.append({
                    "search_term": term,
                    "campaign": st.get("campaign", ""),
                    "campaign_id": st.get("campaign_id", ""),
                    "impressions": impressions,
                    "clicks": clicks,
                    "cost": cost,
                    "conversions": conversions,
                    "reasons": reasons,
                    "suggested_match": "EXACT" if word_count == 1 else "PHRASE",
                    "priority": "high" if cost >= 20 else "medium" if cost >= 5 else "low",
                    "potential_savings": cost,
                })

        return sorted(candidates, key=lambda x: x["cost"], reverse=True)


# ═══════════════════════════════════════════════════════
# ANOMALY DETECTOR
# ═══════════════════════════════════════════════════════

class AnomalyDetector:
    @staticmethod
    def detect_anomalies(daily_data):
        """Detect performance anomalies using statistical analysis."""
        if len(daily_data) < 7:
            return []

        anomalies = []
        metrics = ["clicks", "impressions", "cost", "ctr", "conversions"]

        for metric in metrics:
            values = [d.get(metric, 0) for d in daily_data]
            if not values or max(values) == 0:
                continue

            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = variance ** 0.5

            if std == 0:
                continue

            latest = values[-1]
            z_score = (latest - mean) / std

            if abs(z_score) > Config.ANOMALY_Z_THRESHOLD:
                direction = "düşüş" if z_score < 0 else "artış"
                anomalies.append({
                    "metric": metric,
                    "latest_value": latest,
                    "mean": round(mean, 2),
                    "std": round(std, 2),
                    "z_score": round(z_score, 2),
                    "direction": direction,
                    "severity": "critical" if abs(z_score) > 3.5 else "warning",
                    "message": f"{metric} metriğinde anormal {direction}: "
                               f"Son değer {latest:.1f}, ortalama {mean:.1f} "
                               f"(Z-score: {z_score:.1f})",
                    "date": daily_data[-1].get("date", ""),
                })

        # Special checks
        latest_day = daily_data[-1] if daily_data else {}
        prev_day = daily_data[-2] if len(daily_data) > 1 else {}

        # CTR sudden drop
        if prev_day.get("ctr", 0) > 0 and latest_day.get("ctr", 0) > 0:
            ctr_change = (latest_day["ctr"] - prev_day["ctr"]) / prev_day["ctr"]
            if ctr_change < -Config.CTR_DROP_THRESHOLD:
                anomalies.append({
                    "metric": "ctr_drop",
                    "severity": "critical",
                    "message": f"CTR bir günde %{abs(ctr_change)*100:.0f} düştü "
                               f"({prev_day['ctr']:.2f}% → {latest_day['ctr']:.2f}%)",
                    "date": latest_day.get("date", ""),
                })

        # Zero conversions after having some
        recent_convs = [d.get("conversions", 0) for d in daily_data[-3:]]
        older_convs = [d.get("conversions", 0) for d in daily_data[-7:-3]]
        if sum(older_convs) > 0 and sum(recent_convs) == 0:
            anomalies.append({
                "metric": "zero_conversions",
                "severity": "emergency",
                "message": "Son 3 gündür sıfır dönüşüm! Dönüşüm izleme veya kampanyaları kontrol edin.",
                "date": latest_day.get("date", ""),
            })

        return anomalies
