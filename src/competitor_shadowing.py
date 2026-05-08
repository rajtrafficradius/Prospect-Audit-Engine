import os
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from playwright.async_api import async_playwright
from dotenv import load_dotenv
try:
    from .usage_tracker import record_openai_usage
except ImportError:  # pragma: no cover - direct script fallback
    from usage_tracker import record_openai_usage

class GapFinding(BaseModel):
    competitor: str = Field(description="The specific competitor domain.")
    what_they_have: str = Field(description="A specific value proposition, feature, or messaging angle they use prominently on their homepage that the prospect lacks.")
    why_it_works: str = Field(description="Why this messaging converts well or builds trust.")
    how_to_beat_it: str = Field(description="The specific counter-strategy the prospect should employ to neutralize this advantage.")

class ShadowingReport(BaseModel):
    overall_gap_summary: str = Field(description="A 1-paragraph brutal summary of how far behind the prospect's messaging is compared to these top competitors.")
    gaps: List[GapFinding] = Field(description="Exactly 3 critical value proposition gaps found across the competitors.")


def _clean_domain(value: str) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("http://") or text.startswith("https://"):
        text = text.split("://", 1)[1]
    return text.split("/", 1)[0].strip()


def build_competitor_shadow_fallback(prospect_text: str, market_intelligence: dict, error_message: str = "") -> dict:
    """Builds a structured fallback report when live competitor extraction is unavailable."""
    prospect = market_intelligence.get("prospect", {}) or {}
    market_competitors = market_intelligence.get("competitors", []) or []
    top_keywords = prospect.get("top_keywords", []) or []
    service_hint = ""
    for item in top_keywords:
        keyword = str((item or {}).get("Keyword") or "").strip()
        if keyword:
            service_hint = keyword
            break
    if not service_hint:
        service_hint = "high-intent local service queries"

    fallback_competitors = []
    for competitor in market_competitors[:3]:
        domain = _clean_domain((competitor or {}).get("domain", ""))
        if domain:
            fallback_competitors.append(
                {
                    "domain": domain,
                    "source": (competitor or {}).get("source", "fallback_market"),
                    "data_status": (competitor or {}).get("data_status", "fallback_sample"),
                }
            )

    labels = [entry["domain"] for entry in fallback_competitors]
    while len(labels) < 3:
        labels.append(["category leaders", "local specialists", "answer-focused competitors"][len(labels)])

    gap_templates = [
        (
            "They present tighter commercial messaging around {service} with stronger local intent alignment.",
            "That clarity helps buyers immediately connect the offer to their need, which improves search relevance and conversion confidence.",
            "Create dedicated service and location pages that lead with Brisbane-specific proof, sharper offer framing, and clearer CTAs around {service}.",
        ),
        (
            "They package trust signals more aggressively through proof, service coverage, and decision-stage FAQs.",
            "This reduces buyer hesitation and gives search engines stronger entity and experience signals for competitive queries.",
            "Expand visible proof points, structured FAQs, and service differentiation blocks so the site answers objections before the quote request stage.",
        ),
        (
            "They likely cover more adjacent informational and comparison topics that support discovery before purchase.",
            "That broader content footprint captures upper-funnel searches and strengthens topical authority across the HVAC journey.",
            "Build supporting guides, maintenance explainers, and comparison pages that connect informational demand back to commercial service pages.",
        ),
    ]

    gaps = []
    for idx, competitor_label in enumerate(labels[:3]):
        what_they_have, why_it_works, how_to_beat_it = gap_templates[idx]
        gaps.append(
            {
                "competitor": competitor_label,
                "what_they_have": what_they_have.format(service=service_hint),
                "why_it_works": why_it_works,
                "how_to_beat_it": how_to_beat_it.format(service=service_hint),
            }
        )

    summary = (
        "Live competitor page extraction was unavailable for this run, so the audit preserved a structured comparison fallback "
        "using available market-intelligence signals instead of dropping the competitive section. "
        "The current gap is not a lack of services; it is weaker commercial framing, thinner trust packaging, and less supporting discovery content "
        "than the competitor set being targeted."
    )

    report = {
        "overall_gap_summary": summary,
        "gaps": gaps,
        "competitors": fallback_competitors,
        "warning": "Competitor shadowing fallback used because live competitor extraction was unavailable.",
        "details": error_message or "Live competitor extraction unavailable",
        "data_status": "fallback_sample",
    }
    return report

async def extract_homepage_text(url: str, p) -> dict:
    """Uses Playwright to grab the fully rendered text of a competitor's homepage."""
    if not url.startswith("http"):
        url = f"https://{url}"
        
    try:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        content = await page.evaluate("() => document.body.innerText")
        await browser.close()
        return {"domain": url, "text": " ".join(content.split())[:3000]} # Limit to 3000 chars for brevity
    except Exception as e:
        print(f"Failed to spy on {url}: {e}")
        return {"domain": url, "text": ""}

async def shadow_competitors_async(prospect_text: str, top_competitors: List[str]) -> dict:
    """Asynchronously scrapes competitor homepages and passes them to GPT-4o for gap analysis."""
    print(f"Shadowing {len(top_competitors)} dynamic competitors natively...")
    
    competitor_data = []
    async with async_playwright() as p:
        tasks = [extract_homepage_text(comp, p) for comp in top_competitors]
        results = await asyncio.gather(*tasks)
        competitor_data = [res for res in results if res["text"]]
        
    if not competitor_data:
        raise ValueError("Failed to extract any text from the dynamic competitors.")
        
    print("Competitor data extracted. Synthesizing Gap Analysis with GPT-4o...")
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    prompt = f"""
    You are an elite Product Marketing & Conversion Specialist.
    We are auditing a prospect's homepage messaging against their top organic competitors.
    
    --- PROSPECT HOMEPAGE COPY ---
    {prospect_text[:3000]}
    
    --- COMPETITOR HOMEPAGE COPY ---
    """
    for comp in competitor_data:
        prompt += f"\n\nCOMPETITOR: {comp['domain']}\nCOPY: {comp['text']}\n"
        
    prompt += """
    \nAnalyze the prospect's copy against the competitors. Identify massive value proposition gaps—what are the competitors claiming, promising, or featuring that the prospect is completely failing to mention?
    Be brutal and highly specific.
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a Senior Competitor Intelligence Analyst."},
            {"role": "user", "content": prompt}
        ],
        response_format=ShadowingReport,
        temperature=0.7
    )
    record_openai_usage(completion, "gpt-4o")
    
    return completion.choices[0].message.parsed.model_dump()

def run_competitor_shadowing(prospect_text: str, market_intelligence: dict) -> dict:
    competitors = market_intelligence.get("competitors", [])
    if not competitors:
        raise ValueError("No competitors found in the market intelligence data.")
        
    # Extract top 3 domains
    top_domains = [c.get("domain") for c in competitors[:3] if c.get("domain")]
    
    if not top_domains:
        raise ValueError("No valid competitor domains found.")
        
    return asyncio.run(shadow_competitors_async(prospect_text, top_domains))

if __name__ == "__main__":
    # Test execution
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    with open(os.path.join(out_dir, "business_analysis.json"), "r") as f:
        bd = json.load(f)
        p_text = bd.get("company_profile", "Prospect Company") # Fallback, ideally we pass actual text
        
    with open(os.path.join(out_dir, "market_intelligence.json"), "r") as f:
        mi = json.load(f)
        
    try:
        report = run_competitor_shadowing(p_text, mi)
        with open(os.path.join(out_dir, "competitor_shadowing.json"), "w") as f:
            json.dump(report, f, indent=2)
        print("Shadowing complete. Results saved.")
    except Exception as e:
        print(f"Error: {e}")
