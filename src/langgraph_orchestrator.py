import os
import json
import subprocess
import datetime
from typing import TypedDict, List, Optional, Any, Dict, Union
from langgraph.graph import StateGraph, START, END

# Import the existing rigid pipeline phases
try:
    from .scraper import run_scraper
    from .llm_extractor import extract_business_info
    from .vision_cro_agent import analyze_homepage_ui
    from .semrush_client import gather_market_intelligence, SemrushAPIError, generate_semrush_style_fallback
    from .intelligence_refinement import refine_intelligence
    from .competitor_shadowing import run_competitor_shadowing, build_competitor_shadow_fallback
    from .usage_tracker import get_usage_summary
    from .deep_crawler import DeepCrawlerRAG
    from .strategy_synthesizer import synthesize_strategy
except ImportError:  # pragma: no cover - direct script fallback
    from scraper import run_scraper
    from llm_extractor import extract_business_info
    from vision_cro_agent import analyze_homepage_ui
    from semrush_client import gather_market_intelligence, SemrushAPIError, generate_semrush_style_fallback
    from intelligence_refinement import refine_intelligence
    from competitor_shadowing import run_competitor_shadowing, build_competitor_shadow_fallback
    from usage_tracker import get_usage_summary
    from deep_crawler import DeepCrawlerRAG
    from strategy_synthesizer import synthesize_strategy
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from technical_cro_audit import (
    check_robots_txt, 
    check_sitemap, 
    check_homepage_seo, 
    check_ai_bot_access, 
    check_llms_txt, 
    check_schema_and_content_structure, 
    calculate_integrated_scores
)

class AuditState(TypedDict):
    """The central state dictionary bridging everything together."""
    domain: str
    company_name: str
    target_country: str
    output_dir: str
    user_competitors: List[str]
    
    scraped_data: List[dict]
    business_analysis: dict
    cro_assessment: dict
    market_intelligence: dict
    competitor_shadowing: dict
    audit_findings: dict
    rag_ready: bool
    strategy_narrative: dict
    errors: List[str]
    job_id: str


def _safe_read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _text_len(value: Any) -> int:
    return len(str(value or "").strip())


def _artifact_validation_issues(output_dir: str) -> List[str]:
    issues: List[str] = []

    business = _safe_read_json(os.path.join(output_dir, "business_analysis.json"))
    market = _safe_read_json(os.path.join(output_dir, "market_intelligence.json"))
    audit = _safe_read_json(os.path.join(output_dir, "audit_findings.json"))
    cro = _safe_read_json(os.path.join(output_dir, "cro_assessment.json"))
    narrative = _safe_read_json(os.path.join(output_dir, "strategy_narrative.json"))
    shadow = _safe_read_json(os.path.join(output_dir, "competitor_shadowing.json"))
    screenshot_path = os.path.join(output_dir, "homepage_screenshot.png")

    if _text_len(business.get("description")) < 80 or len(business.get("primary_services", []) or []) < 2:
        issues.append("business_analysis.json is missing core business context.")

    prospect = market.get("prospect", {}) or {}
    semrush_state = str(((market.get("availability", {}) or {}).get("semrush") or "")).lower()
    semrush_unavailable = semrush_state in {"unavailable", "fallback_sample"}
    if not semrush_unavailable:
        if not prospect or int(prospect.get("organic_keywords", 0) or 0) <= 0 or int(prospect.get("organic_traffic", 0) or 0) <= 0:
            issues.append("market_intelligence.json is incomplete or missing live market metrics.")
        if len(market.get("competitors", []) or []) < 2:
            issues.append("market_intelligence.json is missing competitor coverage.")

    scorecard = audit.get("scorecard", {}) or {}
    if not scorecard or scorecard.get("overall_score") in (None, "", 0, "0"):
        issues.append("audit_findings.json is incomplete or missing scorecard data.")
    layer_scores = [int(scorecard.get(key, 0) or 0) for key in ("seo_score", "aeo_score", "geo_score")]
    if layer_scores.count(0) == 3:
        issues.append("audit_findings.json contains all-zero SEO/AEO/GEO scores; technical audit likely failed in deployment.")
    error_findings = sum(
        1
        for bucket in ("seo_findings", "aeo_findings", "geo_findings")
        for finding in (audit.get(bucket, []) or [])
        if str((finding or {}).get("current_status", "")).upper() == "ERROR"
    )
    if error_findings >= 2:
        issues.append("audit_findings.json contains transport/access errors from the technical audit.")

    if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
        issues.append("homepage_screenshot.png is missing; CRO screenshot capture failed.")
    if len(cro.get("findings", []) or []) < 3:
        issues.append("cro_assessment.json is incomplete or missing CRO findings.")

    long_fields = [
        narrative.get("executive_summary"),
        narrative.get("company_profile"),
        narrative.get("digital_maturity_assessment"),
        narrative.get("competitive_landscape_analysis"),
    ]
    if any(_text_len(value) < 180 for value in long_fields):
        issues.append("strategy_narrative.json is incomplete or overly thin.")
    if len(narrative.get("content_strategy_roadmap", []) or []) < 3:
        issues.append("strategy_narrative.json is missing roadmap detail.")

    if not semrush_unavailable and len(shadow.get("competitors", []) or []) < 2 and len(shadow.get("gaps", []) or []) < 2:
        issues.append("competitor_shadowing.json is incomplete or missing comparison insights.")

    return issues


def _build_market_intelligence_fallback(state: AuditState, warning_text: str) -> dict:
    clean_domain = state["domain"].replace("https://", "").replace("http://", "").split("/")[0].strip().lower()
    business = state.get("business_analysis", {}) or {}
    service_seeds = business.get("seed_keywords", {}) or {}
    top_keywords = []
    for kw in (service_seeds.get("seo_seeds", []) or [])[:8]:
        text = str(kw or "").strip()
        if text:
            top_keywords.append({"Keyword": text, "Source": "phase_1_seed"})

    competitors = []
    for raw in state.get("user_competitors", [])[:5]:
        domain = str(raw or "").strip().lower()
        if not domain:
            continue
        competitors.append({
            "domain": domain,
            "source": "user",
            "data_status": "unavailable",
        })

    return {
        "prospect": {
            "domain": clean_domain,
            "top_keywords": top_keywords,
            "data_status": "unavailable",
        },
        "competitors": competitors,
        "aeo_indicators": {
            "question_keywords_found": None,
            "top_question_keywords": [],
            "data_status": "unavailable",
        },
        "geo_indicators": {
            "informational_keywords_found": None,
            "top_informational_keywords": [],
            "data_status": "unavailable",
        },
        "availability": {
            "semrush": "unavailable",
            "warning": "Market intelligence data unavailable due to SEMrush API access issue",
            "details": warning_text,
        },
        "warnings": [
            "Market intelligence data unavailable due to SEMrush API access issue",
            warning_text,
        ],
        "user_competitors": state.get("user_competitors", [])[:3],
    }

# -------------------------------------------------------------
# LangGraph Nodes
# -------------------------------------------------------------

def phase_1_extraction_and_vision(state: AuditState):
    print("\n--- [Node] Phase 1 & 1.5: Content Extraction & Vision CRO ---")
    print("[PROGRESS] 10% | Content Extraction & Vision CRO")
    import concurrent.futures
    import json
    import os
    
    scraped = []
    ba = {}
    cro = {}
    
    try:
        def run_scraper_and_synthesis():
            scraped_data = run_scraper(state["domain"], state["output_dir"])
            business_anal = extract_business_info(scraped_data)
            with open(os.path.join(state["output_dir"], "business_analysis.json"), "w") as f:
                json.dump(business_anal, f, indent=2)
            return scraped_data, business_anal
                
        # Scraping first
        scraped, ba = run_scraper_and_synthesis()
        
        # Vision second (since we need the screenshot generated by scraper)
        try:
            screenshot_path = os.path.join(state["output_dir"], "homepage_screenshot.png")
            if os.path.exists(screenshot_path):
                cro = analyze_homepage_ui(screenshot_path)
                with open(os.path.join(state["output_dir"], "cro_assessment.json"), "w") as f:
                    json.dump(cro, f, indent=2)
            else:
                raise FileNotFoundError(f"Screenshot not found at {screenshot_path}.")
        except Exception as e:
            print(f" [!] Vision Error: {e}")
            return {
                "scraped_data": scraped,
                "business_analysis": ba,
                "cro_assessment": cro,
                "errors": [f"Vision CRO Error: {e}"],
            }
            
    except Exception as e:
        print(f" [!] Extraction Phase Error: {e}")
        if not ba:
            ba = {"company_name": state["company_name"], "domain": state["domain"], "seed_keywords": {"seo_seeds": [state["company_name"]]}}
        return {
            "scraped_data": scraped,
            "business_analysis": ba,
            "cro_assessment": cro,
            "errors": [f"Extraction Phase Error: {e}"],
        }

    if not ba or _text_len(ba.get("description")) < 80 or len(ba.get("primary_services", []) or []) < 2:
        return {
            "scraped_data": scraped,
            "business_analysis": ba,
            "cro_assessment": cro,
            "errors": ["Extraction phase produced incomplete business analysis; blocking thin deliverables."],
        }
        
    return {"scraped_data": scraped, "business_analysis": ba, "cro_assessment": cro}

def phase_2_market_intelligence(state: AuditState):
    print("\n--- [Node] Phase 2: High-Quality Market Intelligence ---")
    print("[PROGRESS] 30% | Gathering Deep SEMrush Market Intelligence")
    import json
    import os
    try:
        # Extract highly relevant seeds generated by Phase 1 LLM
        seeds = state.get("business_analysis", {}).get("seed_keywords", {}).get("seo_seeds", [])
        if not seeds:
            # Fallback to company name
            seeds = [state["company_name"]]
            
        print(f"Using deeply targeted seeds: {seeds[:3]}")
        
        # Extract Brand Variations and Blacklist Terms for strict filtering
        ba = state.get("business_analysis") or {}
        entity = ba.get("entity_signals") or {}
        brand_vars = entity.get("brand_name_variations") or []
        blacklist = entity.get("competitor_blacklist_terms") or []
        
        # Ensure domain name is always in brand variations
        clean_domain = state["domain"].replace("https://", "").replace("http://", "").split("/")[0]
        if clean_domain not in brand_vars:
            brand_vars.append(clean_domain)
            
        mi = gather_market_intelligence(
            state["domain"], 
            seeds, 
            brand_variations=brand_vars, 
            blacklist_terms=blacklist, 
            database=state["target_country"]
        )
        mi = merge_user_competitors(mi, state.get("user_competitors", []), state["target_country"])
        
        # New: Contextual Intelligence Refinement (AI Audit)
        mi = refine_intelligence(mi, ba)
        
        with open(os.path.join(state["output_dir"], "market_intelligence.json"), "w") as f:
            json.dump(mi, f, indent=2)
        return {"market_intelligence": mi}
    except SemrushAPIError as e:
        warning = f"Market intelligence data unavailable due to SEMrush API access issue: {e}"
        print(f" [!] {warning}")
        try:
            mi = generate_semrush_style_fallback(
                state["domain"],
                state["company_name"],
                state["target_country"],
                state.get("business_analysis", {}) or {},
                seeds,
                state.get("user_competitors", []) or [],
                str(e),
            )
            mi["availability"] = {
                "semrush": "fallback_sample",
                "warning": "Sample SEMrush-style data used because live SEMrush API was unavailable",
                "details": warning,
            }
            mi["warnings"] = [
                "Sample SEMrush-style data used because live SEMrush API was unavailable",
                warning,
            ]
            mi["user_competitors"] = state.get("user_competitors", [])[:3]
        except Exception as fallback_exc:
            fallback_warning = f"{warning} | fallback_generation={fallback_exc}"
            print(f" [!] SEMrush fallback generation failed: {fallback_exc}")
            mi = _build_market_intelligence_fallback(state, fallback_warning)
        with open(os.path.join(state["output_dir"], "market_intelligence.json"), "w") as f:
            json.dump(mi, f, indent=2)
        return {"market_intelligence": mi}
    except Exception as e:
        warning = f"Market intelligence data unavailable due to SEMrush API access issue: {e}"
        print(f" [!] {warning}")
        try:
            mi = generate_semrush_style_fallback(
                state["domain"],
                state["company_name"],
                state["target_country"],
                state.get("business_analysis", {}) or {},
                seeds,
                state.get("user_competitors", []) or [],
                str(e),
            )
            mi["availability"] = {
                "semrush": "fallback_sample",
                "warning": "Sample SEMrush-style data used because live SEMrush API was unavailable",
                "details": warning,
            }
            mi["warnings"] = [
                "Sample SEMrush-style data used because live SEMrush API was unavailable",
                warning,
            ]
            mi["user_competitors"] = state.get("user_competitors", [])[:3]
        except Exception as fallback_exc:
            fallback_warning = f"{warning} | fallback_generation={fallback_exc}"
            print(f" [!] SEMrush fallback generation failed: {fallback_exc}")
            mi = _build_market_intelligence_fallback(state, fallback_warning)
        with open(os.path.join(state["output_dir"], "market_intelligence.json"), "w") as f:
            json.dump(mi, f, indent=2)
        return {"market_intelligence": mi}

def phase_2_5_competitor_shadow(state: AuditState):
    print("\n--- [Node] Phase 2.5: Dynamic Competitor Shadowing ---")
    print("[PROGRESS] 45% | Shadowing Top Competitors Natively")
    shadow_path = os.path.join(state["output_dir"], "competitor_shadowing.json")
    try:
        if not state.get("market_intelligence") or not state["market_intelligence"].get("competitors"):
            warning = "No market intel or competitors found to shadow. Using structured fallback comparison."
            print(f" [!] Warning: {warning}")
            shadow = build_competitor_shadow_fallback("", state.get("market_intelligence") or {}, warning)
            with open(shadow_path, "w") as f:
                json.dump(shadow, f, indent=2)
            return {"competitor_shadowing": shadow}
            
        p_text = state["scraped_data"][0].get("content", "") if state.get("scraped_data") else ""
        shadow = run_competitor_shadowing(p_text, state["market_intelligence"])
        with open(shadow_path, "w") as f:
            json.dump(shadow, f, indent=2)
        return {"competitor_shadowing": shadow}
    except Exception as e:
        print(f" [!] Shadowing Error: {e}")
        shadow = build_competitor_shadow_fallback(
            state["scraped_data"][0].get("content", "") if state.get("scraped_data") else "",
            state.get("market_intelligence") or {},
            str(e),
        )
        with open(shadow_path, "w") as f:
            json.dump(shadow, f, indent=2)
        return {"competitor_shadowing": shadow}

def phase_3_technical_audit(state: AuditState):
    print("\n--- [Node] Phase 3: Technical Lighthouse & SEO Audit ---")
    print("[PROGRESS] 60% | Running Technical Lighthouse SEO/AEO Audit")
    try:
        d = state["domain"]
        seo_findings = []
        aeo_findings = []
        geo_findings = []
        
        def add_findings(collection, result):
            if isinstance(result, list): collection.extend(result)
            elif result: collection.append(result)
        
        # SEO
        target_url = f"https://{d}" if not d.startswith("http") else d
        add_findings(seo_findings, check_robots_txt(target_url))
        add_findings(seo_findings, check_sitemap(target_url))
        add_findings(seo_findings, check_homepage_seo(target_url))
        
        # AEO
        add_findings(aeo_findings, check_ai_bot_access(target_url))
        add_findings(aeo_findings, check_llms_txt(target_url))
        
        # GEO & AEO
        a_res, g_res = check_schema_and_content_structure(target_url)
        add_findings(aeo_findings, a_res)
        add_findings(geo_findings, g_res)
        
        scores = calculate_integrated_scores(seo_findings, aeo_findings, geo_findings)
        error_findings = [
            f for f in (seo_findings + aeo_findings + geo_findings)
            if str((f or {}).get("current_status", "")).upper() == "ERROR"
        ]
        if len(error_findings) >= 2 or all(int(scores.get(key, 0) or 0) == 0 for key in ("seo_score", "aeo_score", "geo_score")):
            raise ValueError(
                "Technical audit could not retrieve reliable live-site signals. "
                "Detected transport/blocking errors or an all-zero scorecard."
            )
        
        audit = {
            "seo_findings": seo_findings,
            "aeo_findings": aeo_findings,
            "geo_findings": geo_findings,
            "scorecard": scores
        }
        
        with open(os.path.join(state["output_dir"], "audit_findings.json"), "w") as f:
            json.dump(audit, f, indent=2)
        return {"audit_findings": audit}
    except Exception as e:
         return {"errors": [f"Technical Audit Error: {e}"]}

def phase_4_deep_rag(state: AuditState):
    print("\n--- [Node] Phase 4: Constructing Recursive FAISS Index ---")
    print("[PROGRESS] 75% | Constructing Recursive FAISS Vector DB")
    try:
        import asyncio
        rag = DeepCrawlerRAG(state["domain"], state["output_dir"], max_pages=50)
        success = asyncio.run(rag.build_index())
        if success:
            return {"rag_ready": True}
        else:
            print(" [!] Warning: RAG Build Aborted: No relevant content found. Proceeding without RAG.")
            return {"rag_ready": False}
    except Exception as e:
        print(f" [!] RAG Error: {str(e)}")
        return {"rag_ready": False}

def phase_5_strategy_synthesis(state: AuditState):
    print("\n--- [Node] Phase 5: GPT-4o AEO Strategy Synthesis ---")
    print("[PROGRESS] 90% | Synthesizing Final Narrative with GPT-4o")
    try:
        rag = None
        if state.get("rag_ready"):
            rag = DeepCrawlerRAG(state["domain"], state["output_dir"])
            
        narrative = synthesize_strategy(
            state.get("business_analysis", {}),
            state.get("market_intelligence", {}),
            state.get("audit_findings", {}),
            rag_db=rag
        )
        with open(os.path.join(state["output_dir"], "strategy_narrative.json"), "w") as f:
            json.dump(narrative, f, indent=2)
        return {"strategy_narrative": narrative}
    except Exception as e:
        return {"errors": [f"Synthesis Error: {e}"]}

def phase_6_deliverables(state: AuditState):
    print("\n--- [Node] Phase 6: Injecting Dynamic Architecture to Deliverables ---")
    print("[PROGRESS] 98% | Assembling Deliverables (DOCX, XLSX)")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_dir = os.path.join(project_root, "scripts")
    
    # Use venv python if available
    venv_python_win = os.path.join(project_root, "venv", "Scripts", "python.exe")
    venv_python_nix = os.path.join(project_root, "venv", "bin", "python")

    if os.path.exists(venv_python_win):
        python_exe = venv_python_win
    elif os.path.exists(venv_python_nix):
        python_exe = venv_python_nix
    else:
        python_exe = sys.executable

    
    env_vars = os.environ.copy()
    env_vars["OUTPUT_DIR"] = state["output_dir"]
    env_vars["PROSPECT_NAME"] = state["company_name"]
    env_vars["PROSPECT_DOMAIN"] = state["domain"]
    env_vars["PROSPECT_DATE"] = datetime.datetime.now().strftime("%B %d, %Y")
    
    # Ensure these are also in the environment for the sub-scripts to pick up
    os.environ["PROSPECT_NAME"] = state["company_name"]
    os.environ["PROSPECT_DOMAIN"] = state["domain"]
    os.environ["OUTPUT_DIR"] = state["output_dir"]
    
    # 1. GENERATION PHASE
    if "errors" not in state:
        state["errors"] = []

    try:
        validation_issues = _artifact_validation_issues(state["output_dir"])
        if validation_issues:
            raise ValueError(" | ".join(validation_issues))

        subprocess.run([python_exe, os.path.join(script_dir, "create_charts.py")], check=True, env=env_vars, cwd=project_root)
        subprocess.run([python_exe, os.path.join(script_dir, "create_strategy_docx.py")], check=True, env=env_vars, cwd=project_root)
        subprocess.run([python_exe, os.path.join(script_dir, "create_action_plan_xlsx.py")], check=True, env=env_vars, cwd=project_root)
        
        # PPT Generation
        ppt_result = subprocess.run([python_exe, os.path.join(script_dir, "create_presentation_pptx.py"), state["output_dir"], state["company_name"], state["domain"]], env=env_vars, cwd=project_root)
        if ppt_result.returncode != 0:
            err_msg = f"PPT Generation Script failed with return code {ppt_result.returncode}"
            print(f" [!] {err_msg}")
            state["errors"].append(err_msg)
    except Exception as gen_ex:
        print(f" [!] Generation Phase Error: {gen_ex}")
        state["errors"].append(str(gen_ex))
    
    # 2. ARCHIVING PHASE (Run regardless of generation success to preserve what we have)
    try:
        import shutil
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_domain = state["domain"].replace("https://", "").replace("http://", "").replace("/", "_")
        
        # Use job_id (UUID) as the primary handle for the archive folder
        archive_name = state.get("job_id") or f"{timestamp}_{safe_domain}"
        archive_dir = os.path.join(project_root, "output", "archives", archive_name)
        os.makedirs(archive_dir, exist_ok=True)
        
        # Copy trace data (JSONs) first - these are most important for history
        for json_file in ["strategy_narrative.json", "audit_findings.json", "market_intelligence.json", "cro_assessment.json", "business_analysis.json"]:
            src_path = os.path.join(state["output_dir"], json_file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, archive_dir)
        
        # Copy deliverables if they exist
        deliv_dir = os.path.join(state["output_dir"], "deliverables")
        if os.path.exists(deliv_dir):
            for f in os.listdir(deliv_dir):
                shutil.copy2(os.path.join(deliv_dir, f), archive_dir)

        archived_deliverables = {
            "docx": "Strategy_Document.docx" if os.path.exists(os.path.join(archive_dir, "Strategy_Document.docx")) else None,
            "xlsx": "12_Month_Action_Plan.xlsx" if os.path.exists(os.path.join(archive_dir, "12_Month_Action_Plan.xlsx")) else None,
            "pptx": "Master_Presentation.pptx" if os.path.exists(os.path.join(archive_dir, "Master_Presentation.pptx")) else None
        }
        archive_complete = all(archived_deliverables.values())

        # Save metadata for History Vault API
        metadata = {
            "domain": state["domain"],
            "company": state["company_name"],
            "date": env_vars["PROSPECT_DATE"],
            "timestamp": timestamp,
            "archive_id": archive_name,
            "status": "completed" if archive_complete else "partial_failure",
            "usage": get_usage_summary(),
            "deliverables": archived_deliverables
        }
        with open(os.path.join(archive_dir, "metadata.json"), "w") as m_file:
            json.dump(metadata, m_file, indent=2)
            
        print(f" [+] Audit permanently archived in {archive_name} (Status: {metadata['status']})")
    except Exception as arch_ex:
        print(f" [!] Archive System Error: {arch_ex}")
        
    return {"errors": state["errors"]} if state.get("errors") else {}

# -------------------------------------------------------------
# Define LangGraph State Machine
# -------------------------------------------------------------
workflow = StateGraph(AuditState)

workflow.add_node("extraction", phase_1_extraction_and_vision)
workflow.add_node("market_intel", phase_2_market_intelligence)
workflow.add_node("competitor_shadow", phase_2_5_competitor_shadow)
workflow.add_node("technical_audit", phase_3_technical_audit)
workflow.add_node("deep_rag", phase_4_deep_rag)
workflow.add_node("strategy_synthesis", phase_5_strategy_synthesis)
workflow.add_node("deliverables", phase_6_deliverables)

workflow.add_edge(START, "extraction")
workflow.add_edge("extraction", "market_intel")
workflow.add_edge("market_intel", "competitor_shadow")
workflow.add_edge("competitor_shadow", "technical_audit")
workflow.add_edge("technical_audit", "deep_rag")
workflow.add_edge("deep_rag", "strategy_synthesis")
workflow.add_edge("strategy_synthesis", "deliverables")
workflow.add_edge("deliverables", END)

# Compile into an executable AI agent
app = workflow.compile()

def _looks_like_domain(value: str) -> bool:
    text = (value or "").strip().lower()
    return "." in text and " " not in text

def _enrich_competitor_entry(domain: str, database: str) -> Dict[str, Union[str, int]]:
    try:
        try:
            from .semrush_client import SemrushClient
        except ImportError:  # pragma: no cover - direct script fallback
            from semrush_client import SemrushClient
        client = SemrushClient()
        ranks = client.get_domain_ranks(domain, database)
        backlinks = client.get_backlinks_overview(domain)
        return {
            "domain": domain,
            "authority_score": int(ranks.get("Rank", 0)) if ranks else 0,
            "organic_keywords": int(ranks.get("Organic Keywords", 0)) if ranks else 0,
            "organic_traffic": int(ranks.get("Organic Traffic", 0)) if ranks else 0,
            "organic_traffic_value": int(ranks.get("Organic Cost", 0)) if ranks else 0,
            "backlinks": int(backlinks.get("total", 0)) if backlinks else 0,
            "referring_domains": int(backlinks.get("domains_num", 0)) if backlinks else 0,
            "source": "user",
        }
    except Exception as exc:
        print(f" [!] User competitor enrichment failed for {domain}: {exc}")
        return {
            "domain": domain,
            "source": "user",
            "data_status": "unavailable",
        }

def merge_user_competitors(market_intelligence: dict, user_competitors: List[str], database: str) -> dict:
    if not user_competitors:
        return market_intelligence

    existing = market_intelligence.get("competitors", []) or []
    existing_map = {str(item.get("domain", "")).strip().lower(): item for item in existing if item.get("domain")}
    merged: List[dict] = []

    for raw in user_competitors[:3]:
        clean_value = str(raw).strip()
        if not clean_value:
            continue
        domain_key = clean_value.lower()
        if domain_key in existing_map:
            entry = dict(existing_map.pop(domain_key))
            entry["source"] = "user"
            merged.append(entry)
            continue

        if _looks_like_domain(clean_value):
            merged.append(_enrich_competitor_entry(clean_value, database))
        else:
            merged.append({
                "domain": clean_value,
                "authority_score": 0,
                "organic_keywords": 0,
                "organic_traffic": 0,
                "organic_traffic_value": 0,
                "backlinks": 0,
                "referring_domains": 0,
                "source": "user",
            })

    merged.extend(existing)
    market_intelligence["competitors"] = merged[:5]
    market_intelligence["user_competitors"] = user_competitors[:3]
    return market_intelligence

def run_langgraph_pipeline(domain: str, company: str, country: str = "us", custom_out_dir: Optional[str] = None, job_id: Optional[str] = None, competitor_file: Optional[str] = None):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if custom_out_dir:
        out_dir = custom_out_dir
    else:
        out_dir = os.path.join(root_dir, "output")
    
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "charts"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "deliverables"), exist_ok=True)
    
    # Defensively strip any schemas or trailing slashes the user inputted
    clean_domain = domain.replace("https://", "").replace("http://", "").split("/")[0].strip()
    
    # Intelligently assign the SEMrush region database based on TLD if user didn't specify
    if country == "us":
        if clean_domain.endswith(".au") or clean_domain.endswith(".com.au"): country = "au"
        elif clean_domain.endswith(".uk") or clean_domain.endswith(".co.uk"): country = "uk"
        elif clean_domain.endswith(".ca"): country = "ca"
        elif clean_domain.endswith(".nz") or clean_domain.endswith(".co.nz"): country = "nz"
        elif clean_domain.endswith(".in") or clean_domain.endswith(".co.in"): country = "in"
    
    # Initial State Initialization (Ensure Job ID is definitely set)
    # Note: Using a dict as the starting point for LangGraph state
    resolved_job_id = job_id or (out_dir.split("/")[-1] if out_dir and "sessions" in out_dir else f"job_{int(datetime.datetime.now().timestamp())}")
    user_competitors: List[str] = []
    if competitor_file and os.path.exists(competitor_file):
        try:
            with open(competitor_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
                competitors = payload.get("competitors", [])
                if isinstance(competitors, list):
                    user_competitors = [str(item).strip() for item in competitors if str(item).strip()]
        except Exception as exc:
            print(f" [!] Unable to read user competitors file: {exc}")
    
    initial_state = {
        "domain": clean_domain,
        "company_name": company,
        "target_country": country,
        "output_dir": out_dir,
        "user_competitors": user_competitors,
        "scraped_data": [],
        "business_analysis": {},
        "cro_assessment": {},
        "market_intelligence": {},
        "competitor_shadowing": {},
        "audit_findings": {},
        "rag_ready": False,
        "strategy_narrative": {},
        "errors": [],
        "job_id": resolved_job_id
    }
    
    print("============================================================")
    print(f" STARTING LANGGRAPH ORCHESTRATOR: {company} ({domain})")
    print(f" JOB ID: {resolved_job_id}")
    print("============================================================")
    print("[PROGRESS] 5% | Booting Agentic Swarm...")
    
    config = {"recursion_limit": 50}
    
    pipeline_failed = False
    for event in app.stream(initial_state, config):
        for node_name, state_update in event.items():
            if state_update is not None and state_update.get("errors"):
                print(f" [!] Error in {node_name}: {state_update['errors']}")
                pipeline_failed = True
            else:
                print(f" [+] {node_name} completed successfully.")

    deliverables_dir = os.path.join(initial_state["output_dir"], "deliverables")
    required_outputs = [
        os.path.join(deliverables_dir, "Strategy_Document.docx"),
        os.path.join(deliverables_dir, "12_Month_Action_Plan.xlsx"),
        os.path.join(deliverables_dir, "Master_Presentation.pptx"),
    ]
    deliverables_ready = all(os.path.exists(path) for path in required_outputs)

    if deliverables_ready:
        if pipeline_failed:
            print("\n[WARN] Enterprise Pipeline completed with recoverable warnings. All deliverables were generated successfully.")
        else:
            print("\n[SUCCESS] Enterprise Pipeline Run Complete. Review the output/ folder.")
        print("[PROGRESS] 100% | Setup Complete!")
        sys.exit(0)

    if pipeline_failed:
        print("\n [!] Enterprise Pipeline finished with ERRORS. Some deliverables may be missing.")
    else:
        print("\n [!] Enterprise Pipeline finished without generating the full deliverable set.")
    sys.exit(1)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python langgraph_orchestrator.py <domain> <company_name> [target_country] [output_dir] [job_id] [competitor_file]")
        sys.exit(1)
    
    domain = sys.argv[1]
    company = sys.argv[2]
    country = sys.argv[3] if len(sys.argv) > 3 else "us"
    out_dir = sys.argv[4] if len(sys.argv) > 4 else None
    job_id = sys.argv[5] if len(sys.argv) > 5 else None
    competitor_file = sys.argv[6] if len(sys.argv) > 6 else None
    
    run_langgraph_pipeline(domain, company, country, out_dir, job_id, competitor_file)
