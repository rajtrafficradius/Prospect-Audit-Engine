import os
import json
from typing import List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

class RefinementResult(BaseModel):
    relevant_keywords: List[str] = Field(description="Keywords that are strictly relevant to the commercial core of the business.")
    relevant_competitors: List[str] = Field(description="Competitor domains that are actual business rivals, not informational/seasonal noise.")
    justification: str = Field(description="Brief explanation of why certain items were excluded (e.g., 'Removed Christmas countdowns as they are non-commercial noise').")

def refine_intelligence(market_intel: dict, business_analysis: dict, openai_api_key: Optional[str] = None) -> dict:
    """
    Uses LLM to perform a 'Contextual Audit' of the gathered SEMrush data.
    Filters out keywords and competitors that are not aligned with the business's commercial core.
    """
    api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return market_intel # Fallback if no key

    client = OpenAI(api_key=api_key)

    # Prepare data for LLM review
    prospect_keywords = [kw.get("Keyword", "") for kw in market_intel.get("prospect", {}).get("top_keywords", [])]
    aeo_keywords = [kw.get("Keyword", "") for kw in market_intel.get("aeo_indicators", {}).get("top_question_keywords", [])]
    geo_keywords = [kw.get("Keyword", "") for kw in market_intel.get("geo_indicators", {}).get("top_informational_keywords", [])]
    
    competitors = [c.get("domain", "") for c in market_intel.get("competitors", [])]
    
    all_keywords = list(set(prospect_keywords + aeo_keywords + geo_keywords))

    system_prompt = (
        "You are a Senior Strategic Growth Partner. Your task is to perform a Contextual Audit on market data.\n"
        "You must distinguish between 'Commercial Core' (what the business actually sells) and 'Informational/Seasonal Noise' (blogs, countdowns, unrelated generic content).\n"
        "BUSINESS CONTEXT:\n"
        f"Company: {business_analysis.get('company_name')}\n"
        f"Commercial Focus: {business_analysis.get('commercial_intent_focus')}\n"
        f"Exclusion Criteria: {', '.join(business_analysis.get('negative_exclusion_criteria', []))}\n"
        f"Industry: {business_analysis.get('industry')}\n\n"
        "CRITICAL RULES:\n"
        "1. If a keyword is purely informational/seasonal (e.g. 'days until christmas') and doesn't lead to a product sale, mark it IRRELEVANT.\n"
        "2. If a competitor is a blog, news site, or countdown site rather than a commercial entity, mark it IRRELEVANT.\n"
        "3. Only keep high-fidelity, commerce-aligned data."
    )

    user_content = (
        f"KEYWORDS TO REVIEW: {all_keywords}\n"
        f"COMPETITORS TO REVIEW: {competitors}"
    )

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini", # Use mini for speed/cost as this is a classification task
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=RefinementResult,
            temperature=0
        )
        
        refinement = completion.choices[0].message.parsed
        
        # Apply Refinement
        def filter_list(target_list, allowed_items, key_name="Keyword"):
            return [item for item in target_list if item.get(key_name) in allowed_items]

        market_intel["prospect"]["top_keywords"] = filter_list(market_intel["prospect"]["top_keywords"], refinement.relevant_keywords)
        market_intel["aeo_indicators"]["top_question_keywords"] = filter_list(market_intel["aeo_indicators"]["top_question_keywords"], refinement.relevant_keywords)
        market_intel["geo_indicators"]["top_informational_keywords"] = filter_list(market_intel["geo_indicators"]["top_informational_keywords"], refinement.relevant_keywords)
        
        market_intel["competitors"] = [c for c in market_intel["competitors"] if c.get("domain") in refinement.relevant_competitors]
        
        print(f" [+] Contextual Refinement Complete: {refinement.justification}")
        
    except Exception as e:
        print(f" [!] Intelligence Refinement failed: {e}. Proceeding with raw data.")

    return market_intel
