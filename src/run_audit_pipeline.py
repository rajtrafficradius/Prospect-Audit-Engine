#!/usr/bin/env python3
import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
from scraper import run_scraper
from llm_extractor import extract_business_info
from semrush_client import gather_market_intelligence
# We can import existing scripts iteratively
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_pipeline(prospect_domain: str, prospect_name: str, database: str = "us"):
    """
    Main entry point for generating the Prospect Audit automatically.
    """
    print(f"\n{'='*60}")
    print(f" STARTING PROSPECT AUDIT: {prospect_name} ({prospect_domain})")
    print(f"{'='*60}\n")
    
    # ---------------------------------------------------------
    # Phase 1: Business Discovery + Structuring
    # ---------------------------------------------------------
    print(">>> Phase 1: Scraping website & extracting business logic...")
    scraped_data = run_scraper(prospect_domain)
    if not scraped_data:
         print("Failed to scrape target domain. Aborting.")
         return
    
    business_analysis = extract_business_info(scraped_data)
    
    # Save Business Analysis JSON
    ba_path = os.path.join(OUTPUT_DIR, "business_analysis.json")
    with open(ba_path, "w") as f:
        json.dump(business_analysis, f, indent=2)
    print(f"Saved: {ba_path}")

    # ---------------------------------------------------------
    # Phase 1.5: Multimodal CRO Vision Assessment
    # ---------------------------------------------------------
    print("\n>>> Phase 1.5: Executing Multimodal Vision Assessment...")
    try:
        from vision_cro_agent import analyze_homepage_ui
        screenshot_path = os.path.join(OUTPUT_DIR, "homepage_screenshot.png")
        cro_assessment = analyze_homepage_ui(screenshot_path)
        cro_path = os.path.join(OUTPUT_DIR, "cro_assessment.json")
        with open(cro_path, "w") as f:
            json.dump(cro_assessment, f, indent=2)
        print(f"Saved: {cro_path}")
    except Exception as e:
        print(f"Skipping Vision Assessment due to Error: {e}")
    
    # ---------------------------------------------------------
    # Phase 2: Market Intelligence
    # ---------------------------------------------------------
    print("\n>>> Phase 2: Gathering Market Intelligence via SEMrush...")
    # Extract SEO seed keywords identified in Phase 1
    seed_keywords = business_analysis.get("seed_keywords", {}).get("seo_seeds", [])
    if not seed_keywords:
        seed_keywords = business_analysis.get("primary_services", [])
        
    market_intelligence = {}
        
    try:
        market_intelligence = gather_market_intelligence(prospect_domain, seed_keywords, database=database)
        mi_path = os.path.join(OUTPUT_DIR, "market_intelligence.json")
        with open(mi_path, "w") as f:
            json.dump(market_intelligence, f, indent=2)
        print(f"Saved: {mi_path}")
    except Exception as e:
         print(f"Skipping Market Intelligence due to API Error: {e}")

    # ---------------------------------------------------------
    # Phase 2.5: Dynamic Competitor Shadowing
    # ---------------------------------------------------------
    print("\n>>> Phase 2.5: Shadowing Top Competitors for Gap Analysis...")
    try:
        from competitor_shadowing import run_competitor_shadowing
        prospect_text = scraped_data[0].get("content", "") if scraped_data else ""
        shadowing_report = run_competitor_shadowing(prospect_text, market_intelligence)
        shadow_path = os.path.join(OUTPUT_DIR, "competitor_shadowing.json")
        with open(shadow_path, "w") as f:
            json.dump(shadowing_report, f, indent=2)
        print(f"Saved: {shadow_path}")
    except Exception as e:
        print(f"Skipping Competitor Shadowing due to Error: {e}")

    # ---------------------------------------------------------
    # Phase 3: Technical Audit
    # ---------------------------------------------------------
    print("\n>>> Phase 3: Executing Technical Audit...")
    # Here we would invoke the existing scripts/technical_cro_audit.py as a module or subprocess
    from technical_cro_audit import check_robots_txt, check_sitemap, check_homepage_seo, check_ai_bot_access, check_llms_txt, check_schema_and_content_structure, calculate_integrated_scores
    
    base_url = f"https://{prospect_domain}"
    seo_findings = []
    aeo_findings = []
    geo_findings = []

    if res := check_robots_txt(base_url): seo_findings.append(res)
    if res := check_sitemap(base_url): seo_findings.append(res)
    seo_findings.extend(check_homepage_seo(base_url))
    
    geo_findings.extend(check_ai_bot_access(base_url))
    geo_findings.append(check_llms_txt(base_url))
    
    a_res, g_res = check_schema_and_content_structure(base_url)
    aeo_findings.extend(a_res)
    geo_findings.extend(g_res)
    
    scores = calculate_integrated_scores(seo_findings, aeo_findings, geo_findings)
    
    audit_findings = {
        "seo_findings": seo_findings,
        "aeo_findings": aeo_findings,
        "geo_findings": geo_findings,
        "scorecard": scores
    }
    
    af_path = os.path.join(OUTPUT_DIR, "audit_findings.json")
    with open(af_path, "w") as f:
        json.dump(audit_findings, f, indent=2)
    print(f"Saved: {af_path}")

    # ---------------------------------------------------------
    # Phase 4: Build Deep RAG Knowledge Base
    # ---------------------------------------------------------
    print("\n>>> Phase 4: Building Deep RAG Knowledge Base (Crawling & Vectorizing)...")
    rag = None
    try:
        from deep_crawler import DeepCrawlerRAG
        import asyncio
        rag = DeepCrawlerRAG(prospect_domain, OUTPUT_DIR, max_pages=50) # limited to 50 for speed
        asyncio.run(rag.build_index())
    except Exception as e:
        print(f"Skipping RAG indexing due to Error: {e}")

    # ---------------------------------------------------------
    # Phase 5: Strategy Synthesis
    # ---------------------------------------------------------
    print("\n>>> Phase 5: Synthesizing AI Narrative (via GPT-4o & RAG)...")
    try:
        from strategy_synthesizer import synthesize_strategy
        strategy_narrative = synthesize_strategy(business_analysis, market_intelligence, audit_findings, rag)
        narrative_path = os.path.join(OUTPUT_DIR, "strategy_narrative.json")
        with open(narrative_path, "w") as f:
            json.dump(strategy_narrative, f, indent=2)
        print(f"Saved: {narrative_path}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Skipping Strategy Synthesis due to Error: {e}")

    # ---------------------------------------------------------
    # Phase 6: Deliverables
    # ---------------------------------------------------------
    print("\n>>> Phase 6: Generative Strategy & Deliverables")
    os.environ["PROSPECT_NAME"] = prospect_name
    os.environ["PROSPECT_DOMAIN"] = prospect_domain
    os.environ["OUTPUT_DIR"] = OUTPUT_DIR
    
    scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    
    import subprocess
    print("Generating charts...")
    subprocess.run([sys.executable, os.path.join(scripts_dir, 'create_charts.py')])
    
    print("Generating Strategy DOCX...")
    subprocess.run([sys.executable, os.path.join(scripts_dir, 'create_strategy_docx.py')])
    
    print("Generating Keyword Action Plan XLSX...")
    subprocess.run([sys.executable, os.path.join(scripts_dir, 'create_keyword_xlsx.py')])
    
    print("Generating Strategy Action Plan XLSX...")
    subprocess.run([sys.executable, os.path.join(scripts_dir, 'create_action_plan_xlsx.py')])

    print("\nPipeline Complete. Deliverables available in the output directory.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 run_audit_pipeline.py <domain> <prospect_name> [database(au/us)]")
        sys.exit(1)
        
    db = sys.argv[3] if len(sys.argv) > 3 else "us"
    run_pipeline(sys.argv[1], sys.argv[2], db)
