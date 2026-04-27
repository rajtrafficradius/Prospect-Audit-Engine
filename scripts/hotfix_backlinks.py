import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.semrush_client import SemrushClient
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.environ.get("OUTPUT_DIR", "/Users/vysakhvijayan/prospect-audit-strategy-seo-geo-aeo (1)/output")
market_path = os.path.join(DATA_DIR, "market_intelligence.json")

def patch_market_intelligence():
    with open(market_path, "r") as f:
        data = json.load(f)
        
    client = SemrushClient()
    
    # Patch Prospect
    prospect_domain = data.get("prospect", {}).get("domain")
    if prospect_domain:
        bl = client.get_backlinks_overview(prospect_domain)
        data["prospect"]["backlinks"] = int(bl.get("total", 0)) if bl else 0
        data["prospect"]["referring_domains"] = int(bl.get("domains_num", 0)) if bl else 0

    # Patch Competitors
    for comp in data.get("competitors", []):
        c_domain = comp.get("domain")
        if c_domain:
            bl = client.get_backlinks_overview(c_domain)
            comp["backlinks"] = int(bl.get("total", 0)) if bl else 0
            comp["referring_domains"] = int(bl.get("domains_num", 0)) if bl else 0

    with open(market_path, "w") as f:
        json.dump(data, f, indent=2)
        
    print("Market Intelligence payload permanently patched with live backlink data!")

if __name__ == "__main__":
    patch_market_intelligence()
