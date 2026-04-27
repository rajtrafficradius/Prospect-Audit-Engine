import os
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI
from playwright.async_api import async_playwright
from dotenv import load_dotenv

class GapFinding(BaseModel):
    competitor: str = Field(description="The specific competitor domain.")
    what_they_have: str = Field(description="A specific value proposition, feature, or messaging angle they use prominently on their homepage that the prospect lacks.")
    why_it_works: str = Field(description="Why this messaging converts well or builds trust.")
    how_to_beat_it: str = Field(description="The specific counter-strategy the prospect should employ to neutralize this advantage.")

class ShadowingReport(BaseModel):
    overall_gap_summary: str = Field(description="A 1-paragraph brutal summary of how far behind the prospect's messaging is compared to these top competitors.")
    gaps: List[GapFinding] = Field(description="Exactly 3 critical value proposition gaps found across the competitors.")

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
