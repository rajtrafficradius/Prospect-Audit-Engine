import os
import requests
import json
from typing import List, Dict, Any

class SemrushClient:
    """Direct client for SEMrush API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("SEMRUSH_API_KEY")
        if not self.api_key:
            raise ValueError("SEMRUSH_API_KEY is not set.")
        self.base_url = "https://api.semrush.com/"
    
    def _make_request(self, params: dict, endpoint: str = "") -> str:
        """Helper to make SEMrush requests, injects api_key."""
        params["key"] = self.api_key
        url = self.base_url + endpoint
        response = requests.get(url, params=params)
        response.raise_for_status()
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
            # Domain, Rank, Organic Keywords, Organic Traffic, Organic Cost, etc.
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
            "export_columns": "Ph,Po,Pp,Pd,Nq,Cp,Ur,Tr,Tc,Co,Nr,Td,It" # It = Intent
        }
        res = self._make_request(params)
        return self._parse_csv_to_list(res)


def gather_market_intelligence(domain: str, seed_keywords: List[str], brand_variations: List[str] = [], blacklist_terms: List[str] = [], database: str = "us", api_key: str = None) -> dict:
    """Orchestrates pulling the full Market Intelligence payload with strict commercial filtering."""
    client = SemrushClient(api_key=api_key)
    print(f"Gathering Business-First Intelligence for {domain}...")
    
    def is_filtered(text: str, variations: List[str], blacklist: List[str]) -> bool:
        text_lower = text.lower()
        # Filter Branded
        for var in variations:
            if var.lower() in text_lower:
                return True
        # Filter Dynamic Blacklist (from LLM)
        for term in blacklist:
            if term.lower() in text_lower:
                return True
        return False
    
    # 1. Prospect Overview
    prospect_ranks = client.get_domain_ranks(domain, database)
    all_keywords = client.get_domain_organic_with_intent(domain, database, display_limit=100)
    
    # Filter keywords: No Branded, No Blacklisted, Prioritize Commercial/Transactional Intent
    # Intent: 1=Informational, 2=Navigational, 3=Commercial, 4=Transactional
    commercial_keywords = []
    for kw in all_keywords:
        phrase = kw.get("Keyword", "")
        intent = kw.get("Intent", "0")
        
        # 1. Skip if branded or blacklisted
        if is_filtered(phrase, brand_variations, blacklist_terms):
            continue
            
        # 2. Focus on high-intent (Commercial/Transactional)
        # OR specifically matching a seed product keyword
        high_intent = intent in ["3", "4"]
        matches_seed = any(s.lower() in phrase.lower() for s in seed_keywords)
        
        if high_intent or matches_seed:
            commercial_keywords.append(kw)
    
    # Fallback to top keywords if filtering is too aggressive
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
    
    # 2. Competitors
    competitors_raw = client.get_competitors_organic(domain, database, display_limit=15)
    competitors = []
    
    for comp in competitors_raw:
        if len(competitors) >= 5:
            break
            
        c_domain = comp.get("Domain", "")
        
        # Filter Competitors: Skip non-commercial or blacklisted domains
        if is_filtered(c_domain, brand_variations, blacklist_terms):
            print(f" [!] Skipping non-commercial competitor: {c_domain}")
            continue
        
        if c_domain:
            # Get full ranks for competitor
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
            
    # 3. AEO / GEO phrase keyword analysis on provided seed keywords
    all_questions = []
    all_related = []
    
    for seed in seed_keywords[:3]: # Limit to top 3 seeds to manage budget
        questions = client.get_phrase_questions(seed, database, display_limit=15)
        all_questions.extend(questions)
        
        related = client.get_phrase_related(seed, database, display_limit=20)
        all_related.extend(related)
        
    # Prepare the schema output
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
    # For quick testing, supply domain and a seed keyword
    if len(sys.argv) > 2:
        try:
            res = gather_market_intelligence(sys.argv[1], [sys.argv[2]])
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Error: {e}")
