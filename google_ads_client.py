"""Google Ads API Client - OAuth2, Rate Limiting, GAQL Queries"""
import time
import threading
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import Config


class RateLimiter:
    def __init__(self, max_per_minute=60):
        self.max_per_minute = max_per_minute
        self.timestamps = []
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < 60]
            if len(self.timestamps) >= self.max_per_minute:
                wait = 60 - (now - self.timestamps[0])
                time.sleep(max(0, wait))
            self.timestamps.append(time.time())


rate_limiter = RateLimiter(60)


def get_client():
    """Create Google Ads API client from config."""
    if not all([Config.GOOGLE_ADS_DEVELOPER_TOKEN, Config.GOOGLE_ADS_CLIENT_ID,
                Config.GOOGLE_ADS_CLIENT_SECRET, Config.GOOGLE_ADS_REFRESH_TOKEN]):
        return None

    config_dict = {
        "developer_token": Config.GOOGLE_ADS_DEVELOPER_TOKEN,
        "client_id": Config.GOOGLE_ADS_CLIENT_ID,
        "client_secret": Config.GOOGLE_ADS_CLIENT_SECRET,
        "refresh_token": Config.GOOGLE_ADS_REFRESH_TOKEN,
        "use_proto_plus": True,
    }
    if Config.GOOGLE_ADS_LOGIN_CUSTOMER_ID:
        config_dict["login_customer_id"] = Config.GOOGLE_ADS_LOGIN_CUSTOMER_ID

    return GoogleAdsClient.load_from_dict(config_dict)


def execute_query(customer_id, query, client=None):
    """Execute GAQL query with rate limiting and error handling."""
    rate_limiter.acquire()
    if client is None:
        client = get_client()
    if client is None:
        return []

    service = client.get_service("GoogleAdsService")
    cid = str(customer_id).replace("-", "")

    results = []
    try:
        response = service.search_stream(customer_id=cid, query=query)
        for batch in response:
            for row in batch.results:
                results.append(row)
    except GoogleAdsException as ex:
        raise Exception(f"Google Ads API Error: {ex.failure.errors[0].message}")
    return results


def execute_mutate(customer_id, operations, service_name, method_name, client=None):
    """Execute mutate operation with rate limiting."""
    rate_limiter.acquire()
    if client is None:
        client = get_client()
    if client is None:
        raise Exception("Google Ads API yapılandırılmamış")

    service = client.get_service(service_name)
    cid = str(customer_id).replace("-", "")

    try:
        method = getattr(service, method_name)
        response = method(customer_id=cid, operations=operations)
        return response
    except GoogleAdsException as ex:
        raise Exception(f"Mutate Error: {ex.failure.errors[0].message}")


def generate_oauth_url():
    """Generate OAuth2 authorization URL."""
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": Config.GOOGLE_ADS_CLIENT_ID,
                "client_secret": Config.GOOGLE_ADS_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [Config.OAUTH_REDIRECT_URI],
            }
        },
        scopes=Config.OAUTH_SCOPES,
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return auth_url, flow


def exchange_code_for_token(flow, code):
    """Exchange authorization code for refresh token."""
    flow.fetch_token(code=code)
    return flow.credentials.refresh_token


# ── Reporting Functions ──

def get_account_summary(customer_id, days=30):
    """Get account-level summary for last N days."""
    query = f"""
        SELECT
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_per_conversion
        FROM customer
        WHERE segments.date DURING LAST_{days}_DAYS
    """
    rows = execute_query(customer_id, query)
    if not rows:
        return None
    r = rows[0]
    return {
        "impressions": r.metrics.impressions,
        "clicks": r.metrics.clicks,
        "cost": r.metrics.cost_micros / 1_000_000,
        "conversions": r.metrics.conversions,
        "conv_value": r.metrics.conversions_value,
        "ctr": r.metrics.ctr * 100,
        "avg_cpc": r.metrics.average_cpc / 1_000_000,
        "cpa": r.metrics.cost_per_conversion / 1_000_000 if r.metrics.cost_per_conversion else 0,
    }


def get_campaign_performance(customer_id, days=30):
    """Get campaign-level performance data."""
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_per_conversion,
            metrics.search_impression_share
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    rows = execute_query(customer_id, query)
    campaigns = []
    for r in rows:
        campaigns.append({
            "id": r.campaign.id,
            "name": r.campaign.name,
            "status": r.campaign.status.name,
            "type": r.campaign.advertising_channel_type.name,
            "daily_budget": r.campaign_budget.amount_micros / 1_000_000,
            "impressions": r.metrics.impressions,
            "clicks": r.metrics.clicks,
            "cost": r.metrics.cost_micros / 1_000_000,
            "conversions": r.metrics.conversions,
            "conv_value": r.metrics.conversions_value,
            "ctr": round(r.metrics.ctr * 100, 2),
            "avg_cpc": round(r.metrics.average_cpc / 1_000_000, 2),
            "cpa": round(r.metrics.cost_per_conversion / 1_000_000, 2) if r.metrics.cost_per_conversion else 0,
            "impression_share": round(r.metrics.search_impression_share * 100, 1) if r.metrics.search_impression_share else 0,
        })
    return campaigns


def get_daily_performance(customer_id, days=14):
    """Get daily performance trends."""
    query = f"""
        SELECT
            segments.date,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM customer
        WHERE segments.date DURING LAST_{days}_DAYS
        ORDER BY segments.date ASC
    """
    rows = execute_query(customer_id, query)
    return [{
        "date": r.segments.date,
        "impressions": r.metrics.impressions,
        "clicks": r.metrics.clicks,
        "cost": round(r.metrics.cost_micros / 1_000_000, 2),
        "conversions": r.metrics.conversions,
        "ctr": round(r.metrics.ctr * 100, 2),
        "avg_cpc": round(r.metrics.average_cpc / 1_000_000, 2),
    } for r in rows]


def get_keyword_performance(customer_id, campaign_id=None, days=30):
    """Get keyword-level performance."""
    where = f"WHERE segments.date DURING LAST_{days}_DAYS AND ad_group_criterion.status != 'REMOVED'"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"
    query = f"""
        SELECT
            campaign.name,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr,
            metrics.average_cpc
        FROM keyword_view
        {where}
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """
    rows = execute_query(customer_id, query)
    return [{
        "campaign": r.campaign.name,
        "ad_group": r.ad_group.name,
        "keyword": r.ad_group_criterion.keyword.text,
        "match_type": r.ad_group_criterion.keyword.match_type.name,
        "quality_score": r.ad_group_criterion.quality_info.quality_score or 0,
        "impressions": r.metrics.impressions,
        "clicks": r.metrics.clicks,
        "cost": round(r.metrics.cost_micros / 1_000_000, 2),
        "conversions": r.metrics.conversions,
        "ctr": round(r.metrics.ctr * 100, 2),
        "avg_cpc": round(r.metrics.average_cpc / 1_000_000, 2),
    } for r in rows]


def get_search_terms(customer_id, campaign_id=None, days=30, limit=500):
    """Get search terms report for negative keyword mining."""
    where = f"WHERE segments.date DURING LAST_{days}_DAYS"
    if campaign_id:
        where += f" AND campaign.id = {campaign_id}"
    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            search_term_view.search_term,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr
        FROM search_term_view
        {where}
        ORDER BY metrics.cost_micros DESC
        LIMIT {limit}
    """
    rows = execute_query(customer_id, query)
    return [{
        "campaign_id": r.campaign.id,
        "campaign": r.campaign.name,
        "search_term": r.search_term_view.search_term,
        "impressions": r.metrics.impressions,
        "clicks": r.metrics.clicks,
        "cost": round(r.metrics.cost_micros / 1_000_000, 2),
        "conversions": r.metrics.conversions,
        "ctr": round(r.metrics.ctr * 100, 2),
    } for r in rows]


# ── Mutation Functions ──

def create_customer_client(mcc_id, company_name, currency="TRY", time_zone="Europe/Istanbul"):
    """Create a new Google Ads account under MCC."""
    client = get_client()
    if not client:
        raise Exception("API yapılandırılmamış")

    service = client.get_service("CustomerService")
    customer = client.get_type("Customer")
    customer.descriptive_name = company_name
    customer.currency_code = currency
    customer.time_zone = time_zone

    response = service.create_customer_client(
        customer_id=str(mcc_id).replace("-", ""),
        customer_client=customer,
    )
    new_id = response.resource_name.split("/")[-1]
    return new_id


def update_campaign_status(customer_id, campaign_id, status):
    """Update campaign status (ENABLED/PAUSED)."""
    client = get_client()
    service = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    campaign = op.update
    campaign.resource_name = service.campaign_path(str(customer_id).replace("-", ""), campaign_id)
    campaign.status = client.enums.CampaignStatusEnum[status].value
    client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["status"]))
    return execute_mutate(customer_id, [op], "CampaignService", "mutate_campaigns", client)


def update_campaign_budget(customer_id, budget_id, new_amount_micros):
    """Update campaign daily budget."""
    client = get_client()
    service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")
    budget = op.update
    budget.resource_name = service.campaign_budget_path(str(customer_id).replace("-", ""), budget_id)
    budget.amount_micros = int(new_amount_micros)
    client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["amount_micros"]))
    return execute_mutate(customer_id, [op], "CampaignBudgetService", "mutate_campaign_budgets", client)


def add_negative_keywords(customer_id, campaign_id, keywords_list):
    """Add negative keywords to a campaign."""
    client = get_client()
    service = client.get_service("CampaignCriterionService")
    operations = []

    for kw in keywords_list:
        op = client.get_type("CampaignCriterionOperation")
        criterion = op.create
        criterion.campaign = service.campaign_path(str(customer_id).replace("-", ""), campaign_id)
        criterion.negative = True
        criterion.keyword.text = kw["text"]
        match_type = kw.get("match_type", "PHRASE").upper()
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type].value
        operations.append(op)

    if operations:
        return execute_mutate(customer_id, operations, "CampaignCriterionService",
                              "mutate_campaign_criteria", client)
    return None


def update_ad_group_bid(customer_id, ad_group_id, new_cpc_micros):
    """Update ad group CPC bid."""
    client = get_client()
    service = client.get_service("AdGroupService")
    op = client.get_type("AdGroupOperation")
    ad_group = op.update
    ad_group.resource_name = service.ad_group_path(str(customer_id).replace("-", ""), ad_group_id)
    ad_group.cpc_bid_micros = int(new_cpc_micros)
    client.copy_from(op.update_mask, client.get_type("FieldMask")(paths=["cpc_bid_micros"]))
    return execute_mutate(customer_id, [op], "AdGroupService", "mutate_ad_groups", client)


def get_accessible_customers():
    """List all accessible customer IDs under MCC."""
    client = get_client()
    if not client:
        return []
    service = client.get_service("CustomerService")
    response = service.list_accessible_customers()
    return [r.split("/")[-1] for r in response.resource_names]
