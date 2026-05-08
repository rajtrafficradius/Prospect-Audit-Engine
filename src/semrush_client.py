import os
import requests
import json
from urllib.parse import urlparse
from typing import List, Dict, Any

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from usage_tracker import record_openai_usage


class SemrushAPIError(Exception):
    """Structured SEMrush failure that should not crash the full audit pipeline."""

    def __init__(self, message: str, *, status_code: int = None, category: str = "unknown", details: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.category = category
        self.details = details

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"status={self.status_code}")
        if self.category:
            parts.append(f"category={self.category}")
        if self.details:
            parts.append(f"details={self.details}")
        return " | ".join(parts)


class SemrushKeywordSample(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    keyword: str = Field(alias="Keyword")
    search_volume: int = Field(alias="Search Volume")
    cpc: float = Field(alias="CPC")
    competition: float = Field(alias="Competition")
    intent: str = Field(default="Commercial", alias="Intent")


class SemrushProspectSample(BaseModel):
    domain: str
    authority_score: int
    organic_keywords: int
    organic_traffic: int
    organic_traffic_value: int
    backlinks: int
    referring_domains: int
    top_keywords: List[SemrushKeywordSample]


class SemrushCompetitorSample(BaseModel):
    domain: str
    authority_score: int
    organic_keywords: int
    organic_traffic: int
    organic_traffic_value: int
    backlinks: int
    referring_domains: int
    source: str = "llm_sample"


class SemrushAeoSample(BaseModel):
    question_keywords_found: int
    top_question_keywords: List[SemrushKeywordSample]


class SemrushGeoSample(BaseModel):
    informational_keywords_found: int
    top_informational_keywords: List[SemrushKeywordSample]


class SemrushFallbackPayload(BaseModel):
    prospect: SemrushProspectSample
    competitors: List[SemrushCompetitorSample]
    aeo_indicators: SemrushAeoSample
    geo_indicators: SemrushGeoSample


def _normalize_domain_value(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if "://" in text:
        parsed = urlparse(text)
        text = parsed.netloc or parsed.path
    text = text.split("/")[0].strip().lower()
    return text.removeprefix("www.")


def _ensure_positive_int(value: Any, minimum: int) -> int:
    try:
        return max(minimum, int(round(float(value))))
    except Exception:
        return minimum


def _ensure_float(value: Any, minimum: float) -> float:
    try:
        return max(minimum, float(value))
    except Exception:
        return minimum


def _normalize_keyword_rows(rows: List[dict], fallback_intent: str) -> List[dict]:
    normalized = []
    for row in rows or []:
        keyword = str(row.get("Keyword") or row.get("keyword") or "").strip()
        if not keyword:
            continue
        normalized.append({
            "Keyword": keyword,
            "Search Volume": _ensure_positive_int(row.get("Search Volume"), 40),
            "CPC": round(_ensure_float(row.get("CPC"), 1.2), 2),
            "Competition": round(min(1.0, _ensure_float(row.get("Competition"), 0.25)), 2),
            "Intent": str(row.get("Intent") or fallback_intent),
        })
    return normalized


def _post_process_semrush_fallback(payload: dict, domain: str, user_competitors: List[str]) -> dict:
    data = json.loads(json.dumps(payload))
    prospect = data.get("prospect", {}) or {}
    clean_domain = _normalize_domain_value(domain)
    prospect["domain"] = clean_domain
    prospect["authority_score"] = _ensure_positive_int(prospect.get("authority_score"), 18)
    prospect["organic_keywords"] = _ensure_positive_int(prospect.get("organic_keywords"), 120)
    prospect["organic_traffic"] = _ensure_positive_int(prospect.get("organic_traffic"), 250)
    prospect["organic_traffic_value"] = _ensure_positive_int(prospect.get("organic_traffic_value"), 1200)
    prospect["backlinks"] = _ensure_positive_int(prospect.get("backlinks"), 80)
    prospect["referring_domains"] = _ensure_positive_int(prospect.get("referring_domains"), 25)
    prospect["top_keywords"] = _normalize_keyword_rows(prospect.get("top_keywords", []), "Commercial")
    if not prospect["top_keywords"]:
        base_term = clean_domain.split(".")[0].replace("-", " ")
        prospect["top_keywords"] = [{
            "Keyword": base_term,
            "Search Volume": 120,
            "CPC": 2.2,
            "Competition": 0.38,
            "Intent": "Commercial",
        }]
    prospect["organic_keywords"] = max(prospect["organic_keywords"], len(prospect["top_keywords"]) * 8)

    seen_competitors = set()
    competitors = []
    preferred_domains = [_normalize_domain_value(item) for item in (user_competitors or []) if _normalize_domain_value(item)]
    for entry in data.get("competitors", []) or []:
        comp_domain = _normalize_domain_value(entry.get("domain"))
        if not comp_domain or comp_domain == clean_domain or comp_domain in seen_competitors:
            continue
        seen_competitors.add(comp_domain)
        competitors.append({
            "domain": comp_domain,
            "authority_score": _ensure_positive_int(entry.get("authority_score"), 20),
            "organic_keywords": _ensure_positive_int(entry.get("organic_keywords"), 90),
            "organic_traffic": _ensure_positive_int(entry.get("organic_traffic"), 180),
            "organic_traffic_value": _ensure_positive_int(entry.get("organic_traffic_value"), 900),
            "backlinks": _ensure_positive_int(entry.get("backlinks"), 70),
            "referring_domains": _ensure_positive_int(entry.get("referring_domains"), 22),
            "source": entry.get("source") or ("user" if comp_domain in preferred_domains else "llm_sample"),
        })

    for comp_domain in preferred_domains:
        if comp_domain in seen_competitors or comp_domain == clean_domain:
            continue
        competitors.insert(0, {
            "domain": comp_domain,
            "authority_score": max(20, prospect["authority_score"] - 2),
            "organic_keywords": max(80, int(prospect["organic_keywords"] * 0.8)),
            "organic_traffic": max(160, int(prospect["organic_traffic"] * 0.82)),
            "organic_traffic_value": max(850, int(prospect["organic_traffic_value"] * 0.84)),
            "backlinks": max(60, int(prospect["backlinks"] * 0.78)),
            "referring_domains": max(20, int(prospect["referring_domains"] * 0.8)),
            "source": "user",
        })
        seen_competitors.add(comp_domain)

    data["competitors"] = competitors[:5]

    aeo = data.get("aeo_indicators", {}) or {}
    aeo["top_question_keywords"] = _normalize_keyword_rows(aeo.get("top_question_keywords", []), "Question")
    if not aeo["top_question_keywords"]:
        base_term = clean_domain.split(".")[0].replace("-", " ")
        aeo["top_question_keywords"] = [{
            "Keyword": f"how much does {base_term} cost",
            "Search Volume": 60,
            "CPC": 2.0,
            "Competition": 0.31,
            "Intent": "Question",
        }]
    aeo["question_keywords_found"] = max(_ensure_positive_int(aeo.get("question_keywords_found"), 12), len(aeo["top_question_keywords"]))

    geo = data.get("geo_indicators", {}) or {}
    geo["top_informational_keywords"] = _normalize_keyword_rows(geo.get("top_informational_keywords", []), "Informational")
    if not geo["top_informational_keywords"]:
        base_term = clean_domain.split(".")[0].replace("-", " ")
        geo["top_informational_keywords"] = [{
            "Keyword": f"best {base_term} near me",
            "Search Volume": 90,
            "CPC": 1.8,
            "Competition": 0.28,
            "Intent": "Informational",
        }]
    geo["informational_keywords_found"] = max(_ensure_positive_int(geo.get("informational_keywords_found"), 18), len(geo["top_informational_keywords"]))

    data["prospect"] = prospect
    data["aeo_indicators"] = aeo
    data["geo_indicators"] = geo
    return data


def generate_semrush_style_fallback(
    domain: str,
    company_name: str,
    database: str,
    business_analysis: dict,
    seed_keywords: List[str],
    user_competitors: List[str],
    error_message: str,
    openai_api_key: str = None,
) -> dict:
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    clean_domain = _normalize_domain_value(domain)
    company = str(company_name or business_analysis.get("company_name") or clean_domain).strip()
    services = business_analysis.get("primary_services", []) or []
    commercial_focus = business_analysis.get("commercial_intent_focus") or business_analysis.get("description") or ""
    geography = business_analysis.get("geographic_focus") or database.upper()
    competitor_list = [_normalize_domain_value(item) for item in (user_competitors or []) if _normalize_domain_value(item)]

    system_prompt = (
        "You generate fallback SEMrush-style market intelligence ONLY when the live SEMrush API is unavailable. "
        "Return plausible sample estimates in the exact schema requested. "
        "Rules: no zero metrics, no placeholders, no commentary, no markdown. "
        "Use the prospect business context, target market, and manual competitors. "
        "Competitors must be realistic commercial domains in the same niche. "
        "Prospect top_keywords should be transactional/commercial. "
        "AEO keywords should be question-led answer-engine queries. "
        "GEO keywords should be broader informational or conversational discovery queries. "
        "Keep values internally consistent: prospect totals should be larger than individual keyword rows, "
        "and competitor metrics should be credible relative comparisons."
    )
    user_prompt = (
        f"Prospect company: {company}\n"
        f"Prospect domain: {clean_domain}\n"
        f"Target database/country: {database}\n"
        f"Geographic focus: {geography}\n"
        f"Primary services: {services}\n"
        f"Commercial focus: {commercial_focus}\n"
        f"Seed keywords: {seed_keywords[:8]}\n"
        f"Manual competitors to include if possible: {competitor_list[:5]}\n"
        f"Live SEMrush failure: {error_message}\n"
        "Return 8-12 top prospect keywords, 3-5 competitors, 6-10 AEO question keywords, and 6-10 GEO informational keywords."
    )

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=SemrushFallbackPayload,
        temperature=0.4,
    )
    record_openai_usage(completion, "gpt-4o-mini")
    parsed = completion.choices[0].message.parsed.model_dump(by_alias=True)
    return _post_process_semrush_fallback(parsed, clean_domain, competitor_list)


class SemrushClient:
    """Direct client for SEMrush API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("SEMRUSH_API_KEY")
        if not self.api_key:
            raise ValueError("SEMRUSH_API_KEY is not set.")
        self.base_url = "https://api.semrush.com/"
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            "User-Agent": "TrafficRadiusAudit/1.0 (+https://trafficradius.com.au)",
            "Accept": "*/*",
        })

    def _normalize_domain(self, domain: str) -> str:
        return _normalize_domain_value(domain)

    def get_api_unit_balance(self) -> Dict[str, Any]:
        """Fetches the remaining Standard API units for the current SEMrush key."""
        balance_url = "https://www.semrush.com/users/countapiunits.html"
        try:
            response = self.session.get(balance_url, params={"key": self.api_key}, timeout=20)
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise SemrushAPIError(
                "SEMrush unit balance request timed out",
                category="timeout",
                details=str(exc),
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            body_preview = ""
            if exc.response is not None:
                try:
                    body_preview = " ".join((exc.response.text or "").split())[:220]
                except Exception:
                    body_preview = ""
            raise SemrushAPIError(
                "SEMrush unit balance request failed",
                status_code=status_code,
                category="http",
                details=body_preview or str(exc),
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise SemrushAPIError(
                "SEMrush unit balance request failed",
                category="transport",
                details=str(exc),
            ) from exc

        raw_text = (response.text or "").strip()
        if not raw_text:
            raise SemrushAPIError(
                "SEMrush returned an empty unit balance response",
                category="empty",
            )

        cleaned = raw_text.replace(",", "").strip()
        if not cleaned.isdigit():
            raise SemrushAPIError(
                "SEMrush unit balance response was invalid",
                category="invalid_response",
                details=raw_text[:220],
            )

        remaining_units = int(cleaned)
        return {
            "remaining_units": remaining_units,
            "source": "live",
        }

    def _make_request(self, params: dict, endpoint: str = "") -> str:
        """Helper to make SEMrush requests, injects api_key."""
        params = dict(params)
        params["key"] = self.api_key
        if "domain" in params:
            params["domain"] = self._normalize_domain(params["domain"])
        if "target" in params:
            params["target"] = self._normalize_domain(params["target"])
        url = self.base_url + endpoint
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise SemrushAPIError(
                "SEMrush request timed out",
                category="timeout",
                details=str(exc),
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            body_preview = ""
            if exc.response is not None:
                try:
                    body_preview = " ".join((exc.response.text or "").split())[:220]
                except Exception:
                    body_preview = ""
            if status_code == 403:
                raise SemrushAPIError(
                    "Market intelligence data unavailable due to SEMrush API access issue",
                    status_code=403,
                    category="access",
                    details=body_preview or "SEMrush returned 403 Forbidden",
                ) from exc
            raise SemrushAPIError(
                "SEMrush request failed",
                status_code=status_code,
                category="http",
                details=body_preview or str(exc),
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise SemrushAPIError(
                "SEMrush request failed",
                category="transport",
                details=str(exc),
            ) from exc

        if not response.text or not response.text.strip():
            raise SemrushAPIError(
                "SEMrush returned an empty response",
                category="empty",
                details=f"type={params.get('type')}",
            )
        return response.text

    def _parse_csv_to_list(self, csv_str: str) -> List[Dict[str, str]]:
        """Parses SEMrush semi-colon delimited response into dicts."""
        lines = [line.strip() for line in csv_str.strip().split("\n") if line.strip()]
        if not lines:
            return []

        headers = lines[0].split(";")
        data = []
        for line in lines[1:]:
            parts = line.split(";")
            row = {headers[i]: parts[i] if i < len(parts) else "" for i in range(len(headers))}
            data.append(row)
        return data

    def get_domain_ranks(self, domain: str, database: str = "us") -> dict:
        """Fetches Authority Score, organic traffic, and cost."""
        params = {
            "type": "domain_ranks",
            "domain": domain,
            "database": database
        }
        res = self._make_request(params)
        parsed = self._parse_csv_to_list(res)
        if parsed:
            return parsed[0]
        return {}

    def get_backlinks_overview(self, domain: str) -> dict:
        """Fetches total backlinks and referring domains."""
        params = {
            "type": "backlinks_overview",
            "target": domain,
            "target_type": "root_domain",
            "export_columns": "ascore,total,domains_num"
        }
        res = self._make_request(params, endpoint="analytics/v1/")
        parsed = self._parse_csv_to_list(res)
        if parsed:
            return parsed[0]
        return {}

    def get_domain_organic_keywords(self, domain: str, database: str = "us", display_limit: int = 100) -> List[dict]:
        """Fetches top organic keywords for the given domain."""
        params = {
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": display_limit,
            "export_columns": "Ph,Po,Pp,Pd,Nq,Cp,Ur,Tr,Tc,Co,Nr,Td"
        }
        res = self._make_request(params)
        return self._parse_csv_to_list(res)

    def get_competitors_organic(self, domain: str, database: str = "us", display_limit: int = 5) -> List[dict]:
        """Fetches organic competitors."""
        params = {
            "type": "domain_organic_organic",
            "domain": domain,
            "database": database,
            "display_limit": display_limit,
            "export_columns": "Dn,Cr,Np,Or,Ot,Oc,Ad"
        }
        res = self._make_request(params)
        return self._parse_csv_to_list(res)

    def get_phrase_questions(self, phrase: str, database: str = "us", display_limit: int = 20) -> List[dict]:
        """Fetches question-based keywords for AEO analysis."""
        params = {
            "type": "phrase_questions",
            "phrase": phrase,
            "database": database,
            "display_limit": display_limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td"
        }
        res = self._make_request(params)
        return self._parse_csv_to_list(res)

    def get_phrase_related(self, phrase: str, database: str = "us", display_limit: int = 20) -> List[dict]:
        """Fetches related keywords for GEO/Informational analysis."""
        params = {
            "type": "phrase_related",
            "phrase": phrase,
            "database": database,
            "display_limit": display_limit,
            "export_columns": "Ph,Nq,Cp,Co,Nr,Td"
        }
        res = self._make_request(params)
        return self._parse_csv_to_list(res)

    def get_domain_organic_with_intent(self, domain: str, database: str = "us", display_limit: int = 100) -> List[dict]:
        """Fetches organic keywords with Intent data (It column)."""
        params = {
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": display_limit,
            "export_columns": "Ph,Po,Pp,Pd,Nq,Cp,Ur,Tr,Tc,Co,Nr,Td,It"
        }
        res = self._make_request(params)
        return self._parse_csv_to_list(res)


def gather_market_intelligence(domain: str, seed_keywords: List[str], brand_variations: List[str] = [], blacklist_terms: List[str] = [], database: str = "us", api_key: str = None) -> dict:
    """Orchestrates pulling the full Market Intelligence payload with strict commercial filtering."""
    client = SemrushClient(api_key=api_key)
    print(f"Gathering Business-First Intelligence for {domain}...")

    def is_filtered(text: str, variations: List[str], blacklist: List[str]) -> bool:
        text_lower = text.lower()
        for var in variations:
            if var.lower() in text_lower:
                return True
        for term in blacklist:
            if term.lower() in text_lower:
                return True
        return False

    prospect_ranks = client.get_domain_ranks(domain, database)
    all_keywords = client.get_domain_organic_with_intent(domain, database, display_limit=100)

    commercial_keywords = []
    for kw in all_keywords:
        phrase = kw.get("Keyword", "")
        intent = kw.get("Intent", "0")

        if is_filtered(phrase, brand_variations, blacklist_terms):
            continue

        high_intent = intent in ["3", "4"]
        matches_seed = any(s.lower() in phrase.lower() for s in seed_keywords)

        if high_intent or matches_seed:
            commercial_keywords.append(kw)

    top_keywords = commercial_keywords[:20] if commercial_keywords else all_keywords[:10]
    prospect_backlinks = client.get_backlinks_overview(domain)

    prospect_data = {
        "domain": domain,
        "authority_score": int(prospect_ranks.get("Rank", 0)),
        "organic_keywords": int(prospect_ranks.get("Organic Keywords", 0)),
        "organic_traffic": int(prospect_ranks.get("Organic Traffic", 0)),
        "organic_traffic_value": int(prospect_ranks.get("Organic Cost", 0)),
        "backlinks": int(prospect_backlinks.get("total", 0)),
        "referring_domains": int(prospect_backlinks.get("domains_num", 0)),
        "top_keywords": top_keywords
    }

    competitors_raw = client.get_competitors_organic(domain, database, display_limit=15)
    competitors = []

    for comp in competitors_raw:
        if len(competitors) >= 5:
            break

        c_domain = comp.get("Domain", "")
        if is_filtered(c_domain, brand_variations, blacklist_terms):
            print(f" [!] Skipping non-commercial competitor: {c_domain}")
            continue

        if c_domain:
            c_ranks = client.get_domain_ranks(c_domain, database)
            c_backlinks = client.get_backlinks_overview(c_domain)
            competitors.append({
                "domain": c_domain,
                "authority_score": int(c_ranks.get("Rank", 0)) if c_ranks else 0,
                "organic_keywords": int(c_ranks.get("Organic Keywords", 0)) if c_ranks else 0,
                "organic_traffic": int(c_ranks.get("Organic Traffic", 0)) if c_ranks else 0,
                "organic_traffic_value": int(c_ranks.get("Organic Cost", 0)) if c_ranks else 0,
                "backlinks": int(c_backlinks.get("total", 0)) if c_backlinks else 0,
                "referring_domains": int(c_backlinks.get("domains_num", 0)) if c_backlinks else 0,
            })

    all_questions = []
    all_related = []

    for seed in seed_keywords[:3]:
        questions = client.get_phrase_questions(seed, database, display_limit=15)
        all_questions.extend(questions)

        related = client.get_phrase_related(seed, database, display_limit=20)
        all_related.extend(related)

    market_intelligence = {
        "prospect": prospect_data,
        "competitors": competitors,
        "aeo_indicators": {
            "question_keywords_found": len(all_questions),
            "top_question_keywords": sorted(all_questions, key=lambda x: int(x.get("Search Volume", 0) or 0), reverse=True)[:20]
        },
        "geo_indicators": {
            "informational_keywords_found": len(all_related),
            "top_informational_keywords": sorted(all_related, key=lambda x: int(x.get("Search Volume", 0) or 0), reverse=True)[:20]
        }
    }

    return market_intelligence


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        try:
            res = gather_market_intelligence(sys.argv[1], [sys.argv[2]])
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Error: {e}")
